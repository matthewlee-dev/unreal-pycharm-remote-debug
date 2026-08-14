"""Bridge called by the C++ menu actions.

settrace() patches the interpreter it runs in, so it must run here rather than
in C++. The menu module calls connect()/disconnect() via IPythonScriptPlugin.
"""

import shutil
import sys
import zipfile
from pathlib import Path

import unreal

from .exceptions import PyCharmRemoteDebugRuntimeError
from .session import is_connected, purge_stale_pydevd

EGG_FILENAME = "pydevd-pycharm.egg"
EGG_DIRNAME = "debug-eggs"

# every JetBrains layout puts the executable two levels under debug-eggs/
MAX_SEARCH_DEPTH = 2

# Unreal snake-cases UPROPERTY names by camel-case break: PyCharmPath -> Py|Charm|Path
PYCHARM_PATH_PROPERTY = "py_charm_path"

# 0 is what a cleared port field commits, and it connects nowhere
PORT_MIN = 1
PORT_MAX = 65535

DEFAULT_HOST = "localhost"


def _get_settings() -> "unreal.PyCharmRemoteDebugSettings":
    """Get the PyCharmRemoteDebugSettings default object"""
    return unreal.get_default_object(unreal.PyCharmRemoteDebugSettings)


def _notify(message: str, is_error: bool = False) -> None:
    """Log an outcome and show it as an editor notification

    The menu entries give no feedback of their own, so a log-only outcome reads
    as "Connect did nothing".

    Args:
        message (str): Text to log and show
        is_error (bool): Show the failure toast, which links to the settings
    """
    if is_error:
        unreal.log_error(message)
    else:
        unreal.log(message)

    try:
        unreal.PyCharmRemoteDebugNotifications.show_notification(message, is_error)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # a stale plugin binary predating the class - the log line still stands
        unreal.log_warning(f"Could not show an editor notification ({exc})")


def _find_debug_egg(pycharm_path: Path) -> Path | None:
    """Find the debug egg shipped alongside a PyCharm executable or .app bundle

    Args:
        pycharm_path (Path): PyCharm executable, or PyCharm.app

    Returns:
        Path | None: The egg, or None if not found
    """
    for root in (pycharm_path, *pycharm_path.parents[:MAX_SEARCH_DEPTH]):
        candidates = (
            root / EGG_DIRNAME / EGG_FILENAME,
            # macOS dialogs hand back PyCharm.app; its egg sits under Contents/
            root / "Contents" / EGG_DIRNAME / EGG_FILENAME,
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate

    return None


def _resolve_config_path(serialized_path: str) -> Path:
    """Expand a path as stored by Unreal's file picker into an absolute one

    The picker stores anything outside the engine root relative to it, so
    "/Applications/PyCharm.app" comes back as "../../../../Applications/...".
    unreal.Paths reverses that; the process CWD cannot be trusted to.

    Args:
        serialized_path (str): Path as read from Project Settings

    Returns:
        Path: The absolute path
    """
    path = Path(serialized_path)
    if path.is_absolute():
        return path

    return Path(unreal.Paths.convert_relative_path_to_full(serialized_path))


def _unpacked_egg_dir(egg_path: Path) -> Path:
    """Where an egg unpacks to, keyed on size+mtime so an update re-extracts"""
    stats = egg_path.stat()
    cache_root = _resolve_config_path(unreal.Paths.project_intermediate_dir())

    return (
        cache_root
        / "PyCharmRemoteDebug"
        / f"pydevd-{stats.st_size}-{int(stats.st_mtime)}"
    )


def _unpack_egg(egg_path: Path) -> Path:
    """Unpack the debug egg to a real directory, once per egg

    The egg is a zip, and pydevd's native pieces cannot be dlopen'd from inside
    one: attach.dylib (traces threads created in C++) and the cython accelerator.

    Args:
        egg_path (Path): Path to the debug egg

    Returns:
        Path: Directory for sys.path, or the egg itself if unpacking failed
    """
    unpacked = _unpacked_egg_dir(egg_path)
    if unpacked.is_dir():
        return unpacked

    # extract then rename, so an interrupted run leaves nothing usable-looking
    staging = unpacked.with_name(f"{unpacked.name}.partial")
    try:
        shutil.rmtree(staging, ignore_errors=True)
        with zipfile.ZipFile(egg_path) as archive:
            archive.extractall(staging)
        staging.replace(unpacked)
    except (OSError, zipfile.BadZipFile) as exc:
        shutil.rmtree(staging, ignore_errors=True)
        unreal.log_warning(
            f"Could not unpack {egg_path.name} ({exc}), falling back to the egg "
            "itself - pydevd will run without its native helpers"
        )
        return egg_path

    unreal.log(f"Unpacked {egg_path.name} to {unpacked.as_posix()}")

    return unpacked


def _get_debug_egg() -> str:
    """Resolve the debug egg from the PyCharm location set in Project Settings

    Returns:
        str: Path to the debug egg

    Raises:
        PyCharmRemoteDebugRuntimeError: property missing, unset, non-existent
            path, or no egg alongside it
    """
    try:
        serialized_path = (
            _get_settings().get_editor_property(PYCHARM_PATH_PROPERTY).file_path
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # bare Exception on unknown name - in practice, a stale plugin binary
        raise PyCharmRemoteDebugRuntimeError(
            f"Could not read '{PYCHARM_PATH_PROPERTY}' from the PyCharm Remote Debug "
            f"settings ({exc}) - rebuild the plugin so the editor picks up the "
            "current settings class"
        ) from exc

    # None would reach Path() and raise TypeError past connect()'s handler
    serialized_path = "" if serialized_path is None else str(serialized_path).strip()
    if not serialized_path:
        raise PyCharmRemoteDebugRuntimeError(
            "No PyCharm location saved in Project Settings, please enter the "
            "path to your PyCharm executable"
        )

    pycharm_path = _resolve_config_path(serialized_path)
    if not pycharm_path.exists():
        raise PyCharmRemoteDebugRuntimeError(
            "PyCharm location saved in Project Settings does not exist: "
            f"{serialized_path}"
        )

    egg_path = _find_debug_egg(pycharm_path)
    if egg_path is None:
        raise PyCharmRemoteDebugRuntimeError(
            f"Found no {EGG_DIRNAME}/{EGG_FILENAME} near {serialized_path} - check "
            "the path points at PyCharm Professional, the debug egg does not ship "
            "with Community Edition"
        )

    return egg_path.as_posix()


def _get_endpoint() -> tuple[str, int]:
    """Resolve the debug server host and port from Project Settings

    Guarded because settrace() waits on the game thread with no timeout: an
    empty host flips pydevd into server mode, blocking in accept() forever.

    Returns:
        tuple[str, int]: Host and port to hand settrace()

    Raises:
        PyCharmRemoteDebugRuntimeError: host unset, or port unset/out of range
    """
    settings = _get_settings()

    # str() alone would turn None into the literal hostname "None"
    raw_host = settings.get_editor_property("host")
    host = "" if raw_host is None else str(raw_host).strip()
    if not host:
        raise PyCharmRemoteDebugRuntimeError(
            "No debug host saved in Project Settings, please enter the host the "
            f'PyCharm debug server listens on ("{DEFAULT_HOST}" when PyCharm runs '
            "on this machine)"
        )

    try:
        port = int(settings.get_editor_property("port_number"))
    except (TypeError, ValueError) as exc:
        raise PyCharmRemoteDebugRuntimeError(
            "Could not read the debug port from Project Settings "
            f"({exc}), please enter the port of your PyCharm Python Debug Server"
        ) from exc

    if not PORT_MIN <= port <= PORT_MAX:
        raise PyCharmRemoteDebugRuntimeError(
            f"Debug port {port} saved in Project Settings is not a connectable "
            "port, please enter the port of your PyCharm Python Debug Server "
            f"({PORT_MIN}-{PORT_MAX})"
        )

    return host, port


def _route_pydevd_info_logging() -> None:
    """Send pydevd's info lines to the Unreal log rather than stderr

    pydev_log.info() writes to stderr ungated, and Unreal tags all stderr as
    "LogPython: Error", so "Connected to: <socket>" reads as a failure. warn and
    error keep the stderr path. Redone per connect - the purge drops _pydev_bundle.
    """
    try:
        from _pydev_bundle import pydev_log  # type: ignore[import-not-found]
    except ImportError:
        return

    def _info(message: str) -> None:
        unreal.log(f"[pydevd] {message}")

    pydev_log.info = _info


def connect() -> None:
    """Connect to the PyCharm debugger, via the host, port and egg configured
    in Project Settings > Plugins > PyCharm Remote Debug"""
    if is_connected():
        _notify("Already connected to PyCharm debugger, ignoring")
        return

    try:
        dbg_egg = _get_debug_egg()
        host, port = _get_endpoint()
    except PyCharmRemoteDebugRuntimeError as exc:
        _notify(str(exc), is_error=True)
        return

    dbg_path = _unpack_egg(Path(dbg_egg)).as_posix()
    if dbg_path not in sys.path:
        sys.path.append(dbg_path)

    # stoptrace() leaves state that breaks the next settrace()
    purge_stale_pydevd()

    try:
        import pydevd_pycharm
    except ImportError:
        _notify("Failed to import pydevd_pycharm from the debug egg", is_error=True)
        return

    _route_pydevd_info_logging()

    try:
        try:
            pydevd_pycharm.settrace(
                host,
                port=port,
                suspend=False,
                stdoutToServer=True,
                stderrToServer=True,
            )
        except TypeError:  # new versions of pydevd_pycharm moved to snake case
            pydevd_pycharm.settrace(
                host,
                port=port,
                suspend=False,
                stdout_to_server=True,
                stderr_to_server=True,
            )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        _notify(
            f"Failed to connect to PyCharm debug server on {host}:{port} "
            f"- is the Debug Server running in PyCharm? ({exc})",
            is_error=True,
        )
        return
    _notify("Connected to PyCharm debugger")


def disconnect() -> None:
    """Disconnect from the PyCharm debugger"""
    if not is_connected():
        _notify("Not connected to PyCharm debugger, nothing to do")
        return

    import pydevd  # pylint: disable=import-error  # provided by the debug egg

    pydevd.stoptrace()
    _notify("Disconnected from PyCharm debugger")
