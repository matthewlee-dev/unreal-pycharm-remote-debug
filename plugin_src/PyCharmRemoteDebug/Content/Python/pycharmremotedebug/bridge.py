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


def _get_settings() -> "unreal.PyCharmRemoteDebugSettings":
    """Get the PyCharmRemoteDebugSettings default object"""
    return unreal.get_default_object(unreal.PyCharmRemoteDebugSettings)


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

    if serialized_path == "":
        raise PyCharmRemoteDebugRuntimeError(
            "No PyCharm location saved in Project Settings, please enter the "
            "path to your PyCharm executable (PyCharm.app/Contents/MacOS/pycharm "
            "on macOS)"
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
        unreal.log("Already connected to PyCharm debugger, ignoring")
        return

    try:
        dbg_egg = _get_debug_egg()
    except PyCharmRemoteDebugRuntimeError as exc:
        unreal.log_error(str(exc))
        return

    dbg_path = _unpack_egg(Path(dbg_egg)).as_posix()
    if dbg_path not in sys.path:
        sys.path.append(dbg_path)

    # stoptrace() leaves state that breaks the next settrace()
    purge_stale_pydevd()

    try:
        import pydevd_pycharm
    except ImportError:
        unreal.log_error("Failed to import pydevd_pycharm")
        return

    _route_pydevd_info_logging()

    settings = _get_settings()
    host = settings.get_editor_property("host")
    port = settings.get_editor_property("port_number")
    try:
        try:
            pydevd_pycharm.settrace(
                host,
                port=port,
                stdoutToServer=True,
                stderrToServer=True,
            )
        except TypeError:  # new versions of pydevd_pycharm moved to snake case
            pydevd_pycharm.settrace(
                host,
                port=port,
                stdout_to_server=True,
                stderr_to_server=True,
            )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        unreal.log_error(
            f"Failed to connect to PyCharm debug server on {host}:{port} "
            f"- is the Debug Server running in PyCharm? ({exc})"
        )
        return
    unreal.log("Connected to PyCharm debugger")


def disconnect() -> None:
    """Disconnect from the PyCharm debugger"""
    if not is_connected():
        unreal.log("Not connected to PyCharm debugger, nothing to do")
        return

    import pydevd  # pylint: disable=import-error  # provided by the debug egg

    pydevd.stoptrace()
    unreal.log("Disconnected from PyCharm debugger")
