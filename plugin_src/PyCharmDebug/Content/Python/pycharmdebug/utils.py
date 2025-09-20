import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

from unreal import (
    PluginBlueprintLibrary,
    log_error,
)

from .exceptions import (
    PyCharmDebugRuntimeError,
    PyCharmDebugTypeError,
)


DEFAULT_PORT_NUMBER = 5678
MIN_PORT_NUMBER = 0
MAX_PORT_NUMBER = 65535  # unsigned 16-bit integer range for port numbers
PLUGIN_NAME = "PyCharmDebug"
RELATIVE_CONFIG_PATH = "Config/tool_config.json"


def get_plugin_config(create_on_fail=False) -> Path:
    """Get the path to the tool config file

    Args:
        create_on_fail (bool): If the lookup fails, create the config file,
        defaults to False

    Returns:
        str: The path to the tool config file

    Raises:
        PyCharmDebugRuntimeError:
            Failed to resolve plugin root directory
            Failed to resolve plugin config
    """
    plugin_root = PluginBlueprintLibrary.get_plugin_base_dir(PLUGIN_NAME)
    if plugin_root is None:
        raise PyCharmDebugRuntimeError("Failed to resolve plugin root directory")

    resolved_plugin_config = Path(plugin_root).joinpath(RELATIVE_CONFIG_PATH)

    if resolved_plugin_config.exists() is False:
        if create_on_fail:
            resolved_plugin_config.touch()
        else:
            raise PyCharmDebugRuntimeError("Failed to resolve plugin config")

    return resolved_plugin_config


def get_debug_port() -> int:
    """Get the port number from the config file

    Returns:
        int: The port number
    """
    plugin_config = get_plugin_config()

    if plugin_config is None:
        return DEFAULT_PORT_NUMBER

    with open(plugin_config.as_posix(), "r", encoding="utf-8") as file:
        data = json.load(file)

    port_number = data.get("port_number", DEFAULT_PORT_NUMBER)
    if port_number is None:
        # port number key is present but value is None, default to 5678
        port_number = DEFAULT_PORT_NUMBER

    return port_number


def set_debug_port(port: int) -> bool:
    """Set the port number in the config

    Args:
        port (int): The port number to set

    Raises:
        PyCharmDebugTypeError:
            Port must be an integer
        PyCharmDebugRuntimeError:
            Port must be between 0 and 65535
    """
    if isinstance(port, int) is False:
        raise PyCharmDebugTypeError("Port must be an integer")

    if port < MIN_PORT_NUMBER or port > MAX_PORT_NUMBER:
        raise PyCharmDebugRuntimeError("Port must be between 0 and 65535")

    plugin_config = get_plugin_config(create_on_fail=True)

    if plugin_config is None:
        return False  # failed to find or create plugin config

    with open(plugin_config.as_posix(), "r", encoding="utf-8") as file:
        data: dict = json.load(file)

    data["port_number"] = port

    with open(plugin_config.as_posix(), "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    return True


def find_system_dbg_egg() -> str:
    """Attempt to find the debug egg from the system PyCharm installation

    Returns:
        str: Path to the PyCharm installation debug egg or None

    Raises:
        PyCharmDebugRuntimeError:
            PyCharm installation not found
            PyCharm bin path not found
            System debug egg not found
    """
    pycharm_installation_path = resolve_os_specific_pycharm_path()
    if not pycharm_installation_path or not pycharm_installation_path.is_dir():
        raise PyCharmDebugRuntimeError("PyCharm installation not found")

    egg_path: Path = pycharm_installation_path.joinpath("debug-eggs/pydevd-pycharm.egg")

    if not egg_path.is_file():
        raise PyCharmDebugRuntimeError("System debug egg not found")

    return egg_path.as_posix()


def resolve_os_specific_pycharm_path() -> Optional[Path]:
    """Attempt to resolve the OS specific PyCharm installation path

    Returns:
        Path: PyCharm installation path or None
    """
    if sys.platform.startswith("win"):
        pycharm_bin_dir = os.environ.get("PyCharm")
        if not pycharm_bin_dir:
            return None
        return Path(pycharm_bin_dir.split(";")[0]).parent

    if sys.platform.startswith("darwin"):  # macOS
        try:
            output = subprocess.check_output(
                ["mdfind", "kMDItemCFBundleIdentifier == 'com.jetbrains.pycharm'"],
                text=True,
            ).strip()
            return (
                Path(output.split("\n", maxsplit=1)[0]) / "Contents" if output else None
            )

        except Exception:  # pylint: disable=broad-exception-caught
            log_error("Failed to import pydevd_pycharm")

    if sys.platform.startswith("linux"):
        log_error("Linux")
        return None

    log_error(f"Unknown: {sys.platform}")

    return None


def get_debug_egg() -> str:
    """Get the debug egg location from the config file.

    Returns:
        str: Path to the debug egg or empty string if not set

    Raises:
        PyCharmDebugRuntimeError
            No debug egg set
    """
    plugin_config = get_plugin_config()

    data = {}
    if plugin_config:
        with open(plugin_config.as_posix(), "r", encoding="utf-8") as file:
            data = json.load(file)

    serialized_egg = str(data.get("debug_egg"))

    if serialized_egg == "":
        return serialized_egg

    egg_path = Path(serialized_egg)
    if egg_path.is_file() is False or egg_path.name != "pydevd-pycharm.egg":
        raise PyCharmDebugRuntimeError(
            "No valid debug_egg location saved in the config, please either enter "
            "one manually in the dialog box, or click 'Find installed' to try "
            "and resolve from a system PyCharm installation"
        )

    return egg_path.as_posix()


def set_debug_egg(location: str) -> bool:
    """Set the debug egg location in the config file

    Args:
        location (str): The location of the debug egg

    Returns:
        bool: True if the operation was successful
    """
    plugin_config = get_plugin_config(create_on_fail=True)

    if plugin_config is None:
        raise PyCharmDebugRuntimeError("Failed to find or create plugin config")

    with open(plugin_config.as_posix(), "r", encoding="utf-8") as file:
        data: dict = json.load(file)

    if location == "":  # allow user to clear the path
        data["debug_egg"] = location

    else:
        location = location.strip('"')
        egg_path = Path(location)
        if egg_path.is_file() is False or egg_path.name != "pydevd-pycharm.egg":
            raise PyCharmDebugTypeError(f"Invalid egg file: {egg_path.as_posix()}")

        data["debug_egg"] = egg_path.as_posix()

    with open(plugin_config.as_posix(), "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    return True
