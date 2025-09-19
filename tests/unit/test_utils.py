import sys

import pytest


def test_get_plugin_config_expects_plugin_config_path(mocker):
    # Arrange
    from pycharmdebug.utils import get_plugin_config
    mocker.patch(
        "unreal.PluginBlueprintLibrary.get_plugin_base_dir",
        return_value="/foo/bar"
    )
    mocker.patch("pathlib.Path.exists", return_value=True)

    # Act
    result = get_plugin_config()

    # Assert
    assert result.as_posix() == "/foo/bar/Config/tool_config.json"


def test_get_plugin_config_create_on_fail_expects_plugin_config_created(mocker):
    # Arrange
    from pycharmdebug.utils import get_plugin_config
    mocker.patch(
        "unreal.PluginBlueprintLibrary.get_plugin_base_dir",
        return_value="/foo/bar"
    )
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocked_path_touch = mocker.patch("pathlib.Path.touch")

    # Act
    get_plugin_config(create_on_fail=True)

    # Assert
    mocked_path_touch.assert_called_once()


def test_get_plugin_config_plugin_config_not_found_expects_raises_PyCharmDebugRuntimeError(mocker):
    # Arrange
    from pycharmdebug.utils import get_plugin_config
    from pycharmdebug.exceptions import PyCharmDebugRuntimeError

    mocker.patch(
        "pycharmdebug.utils.PluginBlueprintLibrary.get_plugin_base_dir",
        return_value=None
    )

    # Act
    with pytest.raises(PyCharmDebugRuntimeError) as _ex:
        get_plugin_config()

    # Assert
    assert "Failed to resolve plugin root directory" in str(_ex)


def test_get_debug_port_expects_42(mocker):
    # Arrange
    from pycharmdebug.utils import get_debug_port
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"port_number": 42})
    mocker.patch("pycharmdebug.utils.get_plugin_config")

    # Act
    result = get_debug_port()

    # Assert
    assert result == 42


def test_get_debug_port_plugin_config_not_found_expects_fallback_to_default_port(mocker):
    # Arrange
    from pycharmdebug.utils import (
        get_debug_port,
        DEFAULT_PORT_NUMBER
    )
    mocker.patch("builtins.open")
    mocker.patch(
        "pycharmdebug.utils.get_plugin_config",
        return_value=None
    )

    # Act
    result = get_debug_port()

    # Assert
    assert result == DEFAULT_PORT_NUMBER


def test_get_debug_port_config_entry_empty_expects_fallback_to_default_port(mocker):
    # Arrange
    from pycharmdebug.utils import (
        get_debug_port,
        DEFAULT_PORT_NUMBER,
    )
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={})
    mocker.patch("pycharmdebug.utils.get_plugin_config")

    # Act
    result = get_debug_port()

    # Assert
    assert result == DEFAULT_PORT_NUMBER


def test_get_debug_port_config_entry_is_none_expects_fallback_to_default_port(mocker):
    # Arrange
    from pycharmdebug.utils import (
        get_debug_port,
        DEFAULT_PORT_NUMBER,
    )
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"port_number": None})
    mocker.patch("pycharmdebug.utils.get_plugin_config")

    # Act
    result = get_debug_port()

    # Assert
    assert result == DEFAULT_PORT_NUMBER


def test_set_debug_port_expects_42_dumped_true_returned(mocker):
    # Arrange
    from pycharmdebug.utils import (
        set_debug_port,
        DEFAULT_PORT_NUMBER,
    )
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"port_number": DEFAULT_PORT_NUMBER})
    mock_dump = mocker.patch("json.dump")
    mocker.patch("pycharmdebug.utils.get_plugin_config")

    # Act
    result = set_debug_port(42)

    # Assert
    mock_dump.assert_called_once_with(
        {"port_number": 42}, mocker.ANY, indent=4
    )
    assert result is True


def test_set_debug_port_existing_data_in_config_expects_existing_data_maintained(mocker):
    # Arrange
    from pycharmdebug.utils import (
        set_debug_port,
        DEFAULT_PORT_NUMBER,
    )
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"port_number": DEFAULT_PORT_NUMBER, "foo": "bar"})
    mock_dump = mocker.patch("json.dump")
    mocker.patch("pycharmdebug.utils.get_plugin_config")

    # Act
    result = set_debug_port(42)

    # Assert
    mock_dump.assert_called_once_with(
        {"port_number": 42,  "foo": "bar"}, mocker.ANY, indent=4
    )
    assert result is True



def test_set_debug_port_incorrect_type_expects_raises_PyCharmDebugTypeError(mocker):
    # Arrange
    from pycharmdebug.exceptions import PyCharmDebugTypeError
    from pycharmdebug.utils import set_debug_port
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"port_number": 5678, "debug_egg": "/foo/bar.egg"})
    mocker.patch("pycharmdebug.utils.get_plugin_config")

    # Act
    with pytest.raises(PyCharmDebugTypeError) as _ex:
        set_debug_port("foo")

    # Assert
    assert "Port must be an integer" in str(_ex)


def test_set_debug_port_higher_than_max_expects_raises_PyCharmDebugRuntimeError(mocker):
    # Arrange
    from pycharmdebug.exceptions import PyCharmDebugRuntimeError
    from pycharmdebug.utils import (
        set_debug_port,
        DEFAULT_PORT_NUMBER,
        MAX_PORT_NUMBER,
    )
    mocker.patch("builtins.open")
    mocker.patch(
        "json.load",
        return_value={"port_number": DEFAULT_PORT_NUMBER, "debug_egg": "/foo/bar.egg"}
    )

    # Act
    with pytest.raises(PyCharmDebugRuntimeError) as _ex:
        set_debug_port(MAX_PORT_NUMBER+1)

    # Assert
    assert "Port must be between 0 and 65535" in str(_ex)


def test_set_debug_port_lower_than_min_expects_raises_PyCharmDebugRuntimeError(mocker):
    # Arrange
    from pycharmdebug.exceptions import PyCharmDebugRuntimeError
    from pycharmdebug.utils import (
        set_debug_port,
        DEFAULT_PORT_NUMBER,
        MIN_PORT_NUMBER,
    )

    mocker.patch("builtins.open")
    mocker.patch(
        "json.load",
        return_value={"port_number": DEFAULT_PORT_NUMBER, "debug_egg": "/foo/bar.egg"}
    )

    # Act
    with pytest.raises(PyCharmDebugRuntimeError) as _ex:
        set_debug_port(MIN_PORT_NUMBER-1)

    # Assert
    assert "Port must be between 0 and 65535" in str(_ex)



def test_set_debug_port_no_plugin_config_exists_expects_true_42_dumped_and_file_created(mocker):
    # Arrange
    from pycharmdebug.utils import set_debug_port
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={})
    mocked_dump = mocker.patch("json.dump")
    mocked_path_touch = mocker.patch("pathlib.Path.touch")

    # Act
    result = set_debug_port(42)

    # Assert
    mocked_dump.assert_called_once_with({"port_number": 42}, mocker.ANY, indent=4)
    mocked_path_touch.assert_called_once()
    assert result is True


def test_set_debug_port_plugin_config_is_none_and_fails_to_create_expects_false(mocker):
    # Arrange
    from pycharmdebug.utils import (
        set_debug_port,
        DEFAULT_PORT_NUMBER,
    )
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"port_number": DEFAULT_PORT_NUMBER})
    mock_dump = mocker.patch("json.dump")
    mocker.patch("pycharmdebug.utils.get_plugin_config", return_value=None)

    # Act
    result = set_debug_port(42)

    # Assert
    assert result is False


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="This test is specific to Windows.")
def test_find_system_dbg_egg_expects_path_to_egg(mocker):
    # Arrange
    from pycharmdebug.utils import find_system_dbg_egg
    mocker.patch("os.environ.get", return_value="/foo/bar/bin;")
    mocker.patch("pathlib.Path.is_dir", return_value=True)
    mocker.patch("pathlib.Path.is_file", return_value=True)

    # Act
    result = find_system_dbg_egg()

    # Assert
    assert result == "/foo/bar/debug-eggs/pydevd-pycharm.egg"


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="This test is specific to Windows.")
def test_find_system_dbg_egg_windows_cant_resolve_pycharm_installation_raises_PyCharmDebugRuntimeError(mocker):
    # Arrange
    from pycharmdebug.utils import find_system_dbg_egg
    from pycharmdebug.exceptions import PyCharmDebugRuntimeError
    mocker.patch("os.environ.get", return_value=None)


    # Act
    with pytest.raises(PyCharmDebugRuntimeError) as _ex:
        find_system_dbg_egg()

    # Assert
    assert "PyCharm installation not found" in str(_ex)


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="This test is specific to Windows.")
def test_find_system_dbg_egg_cant_resolve_pycharm_bin_dir_expects_raises_PyCharmDebugRuntimeError(mocker):
    # Arrange
    from pycharmdebug.utils import find_system_dbg_egg
    from pycharmdebug.exceptions import PyCharmDebugRuntimeError

    mocker.patch("os.environ.get", return_value="/foo/bar/bin;")
    mocker.patch("pathlib.Path.is_dir", return_value=False)

    # Act
    with pytest.raises(PyCharmDebugRuntimeError) as _ex:
        find_system_dbg_egg()

    # Assert

    assert "PyCharm bin path not found" in str(_ex)


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="This test is specific to Windows.")
def test_find_system_dbg_egg_cant_resolve_debug_egg_file_expects_raises_PyCharmDebugRuntimeError(mocker):
    # Arrange
    from pycharmdebug.utils import find_system_dbg_egg
    from pycharmdebug.exceptions import PyCharmDebugRuntimeError

    mocker.patch("os.environ.get", return_value="/foo/bar/bin;")
    mocker.patch("pathlib.Path.is_dir", return_value=True)
    mocker.patch("pathlib.Path.is_file", return_value=False)

    # Act
    with pytest.raises(PyCharmDebugRuntimeError) as _ex:
        find_system_dbg_egg()

    # Assert
    assert "System debug egg not found" in str(_ex)


def test_get_debug_egg_exists_in_config_expects_config_value_mocked_find_system_dbg_egg_not_called(mocker):
    # Arrange
    from pycharmdebug.utils import get_debug_egg
    mocker.patch("builtins.open")
    mocker.patch("pycharmdebug.utils.get_plugin_config")
    mocker.patch("json.load", return_value={"debug_egg": "/foo/bar/pydevd-pycharm.egg"})
    mocked_find_system_dbg_egg = mocker.patch(
        "pycharmdebug.utils.find_system_dbg_egg"
    )
    mocker.patch("pathlib.Path.is_file", return_value=True)

    # Act
    result = get_debug_egg()

    # Assert
    assert result == "/foo/bar/pydevd-pycharm.egg"
    mocked_find_system_dbg_egg.assert_not_called()


def test_get_debug_egg_serialized_data_is_empty_string_expects_empty_string_returned(mocker):
    # Arrange
    from pycharmdebug.utils import get_debug_egg
    mocker.patch("builtins.open")
    mocker.patch("pycharmdebug.utils.get_plugin_config")
    mocker.patch("json.load", return_value={"debug_egg": ""})
    mocker.patch("pathlib.Path.is_file", return_value=True)

    # Act
    result = get_debug_egg()

    # Assert
    assert result == ""


def test_get_debug_egg_serialized_data_is_invalid_expects_PyCharmDebugRuntimeError_raised(mocker):
    # Arrange
    from pycharmdebug.utils import get_debug_egg
    from pycharmdebug.exceptions import PyCharmDebugRuntimeError

    mocker.patch("builtins.open")
    mocker.patch("pycharmdebug.utils.get_plugin_config")
    mocker.patch("json.load", return_value={"debug_egg": "blah"})

    # Act
    with pytest.raises(PyCharmDebugRuntimeError) as _ex:
        get_debug_egg()

    # Assert
    assert "No valid debug_egg location saved in the config" in str(_ex)



def test_set_debug_egg_expects_path_dumped_and_returns_true(mocker):
    # Arrange
    from pycharmdebug.utils import set_debug_egg
    mocker.patch("pycharmdebug.utils.get_plugin_config")
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={})
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocked_dump = mocker.patch("json.dump")

    # Act
    result = set_debug_egg("/foo/bar/pydevd-pycharm.egg")

    # Assert
    assert result is True
    mocked_dump.assert_called_once_with(
        {"debug_egg": "/foo/bar/pydevd-pycharm.egg"}, mocker.ANY, indent=4)


def test_set_debug_egg_invalid_egg_file_expects_raises_PyCharmDebugTypeError(mocker):
    # Arrange
    from pycharmdebug.utils import set_debug_egg
    from pycharmdebug.exceptions import PyCharmDebugTypeError

    mocker.patch("pycharmdebug.utils.get_plugin_config")
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={})

    # Act
    with pytest.raises(PyCharmDebugTypeError) as _ex:
        set_debug_egg("/foo/bar/pydevd-pycharm.foo")

    # Assert
    assert "Invalid egg file" in str(_ex)


def test_set_debug_egg_config_doesnt_exist_gets_created_and_value_dumped_returns_true(mocker):
    # Arrange
    from pycharmdebug.utils import set_debug_egg
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={})
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocked_path_touch = mocker.patch("pathlib.Path.touch")
    mocked_dump = mocker.patch("json.dump")

    # Act
    result = set_debug_egg("/foo/bar/pydevd-pycharm.egg")

    # Assert
    assert result is True
    mocked_dump.assert_called_once_with(
        {"debug_egg": "/foo/bar/pydevd-pycharm.egg"}, mocker.ANY, indent=4)
    mocked_path_touch.assert_called_once()



def test_set_debug_egg_config_has_other_data_expects_other_data_maintained(mocker):
    # Arrange
    from pycharmdebug.utils import set_debug_egg
    mocker.patch("pycharmdebug.utils.get_plugin_config")
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"foo": "bar"})
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocked_dump = mocker.patch("json.dump")

    # Act
    result = set_debug_egg("/foo/bar/pydevd-pycharm.egg")

    # Assert
    assert result is True
    mocked_dump.assert_called_once_with(
        {
            "foo": "bar",
            "debug_egg": "/foo/bar/pydevd-pycharm.egg"
        },
        mocker.ANY,
        indent=4
    )


def test_set_debug_egg_empty_string_set_expects_empty_string_serialized(mocker):
    # Arrange
    from pycharmdebug.utils import set_debug_egg
    mocker.patch("pycharmdebug.utils.get_plugin_config")
    mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"debug_egg": "foo"})
    mocked_dump = mocker.patch("json.dump")

    # Act
    result = set_debug_egg("")

    # Assert
    assert result is True
    mocked_dump.assert_called_once_with({"debug_egg": ""}, mocker.ANY,indent=4)


def test_set_debug_egg_no_config_found_expects_PyCharmDebugRuntimeError(mocker):
    # Arrange
    from pycharmdebug.utils import set_debug_egg
    from pycharmdebug.exceptions import PyCharmDebugRuntimeError

    mocker.patch("pycharmdebug.utils.get_plugin_config", return_value=None)

    # Act
    with pytest.raises(PyCharmDebugRuntimeError) as _ex:
        set_debug_egg("foo")

    # Assert
    assert "Failed to find or create plugin config" in str(_ex)
