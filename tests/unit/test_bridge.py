import sys
import types
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _mock_settings(mocker, pycharm_path="", port_number=5678, host="localhost"):
    """Build a mock PyCharmRemoteDebugSettings default object and patch
    bridge._get_settings() to return it"""
    mock_settings = mocker.MagicMock()

    def get_editor_property(name):
        if name == "py_charm_path":  # Unreal splits PyCharmPath as Py|Charm|Path
            return mocker.MagicMock(file_path=pycharm_path)
        if name == "port_number":
            return port_number
        if name == "host":
            return host
        raise AssertionError(f"unexpected property lookup: {name}")

    mock_settings.get_editor_property.side_effect = get_editor_property
    mocker.patch("pycharmremotedebug.bridge._get_settings", return_value=mock_settings)
    return mock_settings


def _make_windows_install(root, egg=True):
    """Build a <install>/bin/pycharm64.exe layout, returning the executable"""
    executable = root / "PyCharm 2025.1" / "bin" / "pycharm64.exe"
    executable.parent.mkdir(parents=True)
    executable.touch()

    if egg:
        egg_dir = root / "PyCharm 2025.1" / "debug-eggs"
        egg_dir.mkdir()
        (egg_dir / "pydevd-pycharm.egg").touch()

    return executable


def _make_macos_install(root, egg=True):
    """Build a PyCharm.app bundle layout, returning the bundle path"""
    bundle = root / "PyCharm.app"
    executable = bundle / "Contents" / "MacOS" / "pycharm"
    executable.parent.mkdir(parents=True)
    executable.touch()

    if egg:
        egg_dir = bundle / "Contents" / "debug-eggs"
        egg_dir.mkdir()
        (egg_dir / "pydevd-pycharm.egg").touch()

    return bundle


@pytest.fixture
def fake_pydevd_pycharm(monkeypatch):
    """Insert a fake pydevd_pycharm module so connect() can 'import' it"""
    module = types.ModuleType("pydevd_pycharm")
    module.settrace = MagicMock()
    monkeypatch.setitem(sys.modules, "pydevd_pycharm", module)
    return module


def test_find_debug_egg_windows_layout_expects_egg_returned(tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    executable = _make_windows_install(tmp_path)

    # Act
    result = bridge._find_debug_egg(executable)

    # Assert
    assert result == executable.parent.parent / "debug-eggs" / "pydevd-pycharm.egg"


def test_find_debug_egg_macos_bundle_expects_egg_returned(tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    bundle = _make_macos_install(tmp_path)

    # Act - macOS dialogs hand back the bundle, not the binary
    result = bridge._find_debug_egg(bundle)

    # Assert
    assert result == bundle / "Contents" / "debug-eggs" / "pydevd-pycharm.egg"


def test_find_debug_egg_macos_binary_expects_egg_returned(tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    bundle = _make_macos_install(tmp_path)
    executable = bundle / "Contents" / "MacOS" / "pycharm"

    # Act
    result = bridge._find_debug_egg(executable)

    # Assert
    assert result == bundle / "Contents" / "debug-eggs" / "pydevd-pycharm.egg"


def test_find_debug_egg_no_egg_in_install_expects_none_returned(tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    executable = _make_windows_install(tmp_path, egg=False)

    # Act
    result = bridge._find_debug_egg(executable)

    # Assert
    assert result is None


def test_find_debug_egg_egg_above_search_depth_expects_none_returned(tmp_path):
    # Arrange - an egg too far above the executable must not match
    from pycharmremotedebug import bridge

    executable = tmp_path / "a" / "b" / "c" / "d" / "pycharm64.exe"
    executable.parent.mkdir(parents=True)
    executable.touch()
    egg_dir = tmp_path / "debug-eggs"
    egg_dir.mkdir()
    (egg_dir / "pydevd-pycharm.egg").touch()

    # Act
    result = bridge._find_debug_egg(executable)

    # Assert
    assert result is None


def test_get_debug_egg_empty_path_expects_PyCharmRemoteDebugRuntimeError_raised(mocker):
    # Arrange
    from pycharmremotedebug import bridge
    from pycharmremotedebug.exceptions import PyCharmRemoteDebugRuntimeError

    _mock_settings(mocker, pycharm_path="")

    # Act / Assert
    with pytest.raises(PyCharmRemoteDebugRuntimeError) as _ex:
        bridge._get_debug_egg()

    assert "No PyCharm location saved in Project Settings" in str(_ex)


def test_get_debug_egg_unknown_property_expects_PyCharmRemoteDebugRuntimeError_raised(
    mocker,
):
    # Arrange - stale plugin binary: unknown name raises a bare Exception
    from pycharmremotedebug import bridge
    from pycharmremotedebug.exceptions import PyCharmRemoteDebugRuntimeError

    mock_settings = mocker.MagicMock()
    mock_settings.get_editor_property.side_effect = Exception(
        "Failed to find property 'py_charm_path'"
    )
    mocker.patch("pycharmremotedebug.bridge._get_settings", return_value=mock_settings)

    # Act / Assert
    with pytest.raises(PyCharmRemoteDebugRuntimeError) as _ex:
        bridge._get_debug_egg()

    assert "rebuild the plugin" in str(_ex)


def test_get_debug_egg_missing_path_expects_PyCharmRemoteDebugRuntimeError_raised(
    mocker, tmp_path
):
    # Arrange
    from pycharmremotedebug import bridge
    from pycharmremotedebug.exceptions import PyCharmRemoteDebugRuntimeError

    missing = tmp_path / "pycharm64.exe"  # never created
    _mock_settings(mocker, pycharm_path=missing.as_posix())

    # Act / Assert
    with pytest.raises(PyCharmRemoteDebugRuntimeError) as _ex:
        bridge._get_debug_egg()

    assert "does not exist" in str(_ex)


def test_get_debug_egg_install_without_egg_expects_PyCharmRemoteDebugRuntimeError_raised(
    mocker, tmp_path
):
    # Arrange
    from pycharmremotedebug import bridge
    from pycharmremotedebug.exceptions import PyCharmRemoteDebugRuntimeError

    executable = _make_windows_install(tmp_path, egg=False)
    _mock_settings(mocker, pycharm_path=executable.as_posix())

    # Act / Assert
    with pytest.raises(PyCharmRemoteDebugRuntimeError) as _ex:
        bridge._get_debug_egg()

    assert "debug-eggs/pydevd-pycharm.egg" in str(_ex)


def test_get_debug_egg_valid_install_expects_egg_path_returned(mocker, tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    executable = _make_windows_install(tmp_path)
    _mock_settings(mocker, pycharm_path=executable.as_posix())

    # Act
    result = bridge._get_debug_egg()

    # Assert
    expected = executable.parent.parent / "debug-eggs" / "pydevd-pycharm.egg"
    assert result == expected.as_posix()


def test_resolve_config_path_absolute_expects_unreal_not_consulted(mocker, tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    result = bridge._resolve_config_path(tmp_path.as_posix())

    # Assert
    assert result == tmp_path
    mock_unreal.Paths.convert_relative_path_to_full.assert_not_called()


def test_resolve_config_path_relative_expects_expanded_via_unreal(mocker, tmp_path):
    # Arrange - the picker stores off-root picks relative to the engine root
    from pycharmremotedebug import bridge

    relative = "../../../../Applications/PyCharm.app"
    expanded = (tmp_path / "Applications" / "PyCharm.app").as_posix()

    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")
    mock_unreal.Paths.convert_relative_path_to_full.return_value = expanded

    # Act
    result = bridge._resolve_config_path(relative)

    # Assert
    assert result == Path(expanded)
    mock_unreal.Paths.convert_relative_path_to_full.assert_called_once_with(relative)


def test_get_debug_egg_relative_path_expects_egg_resolved(mocker, tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    bundle = _make_macos_install(tmp_path)
    _mock_settings(mocker, pycharm_path="../../../../Applications/PyCharm.app")

    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")
    mock_unreal.Paths.convert_relative_path_to_full.return_value = bundle.as_posix()

    # Act
    result = bridge._get_debug_egg()

    # Assert
    expected = bundle / "Contents" / "debug-eggs" / "pydevd-pycharm.egg"
    assert result == expected.as_posix()


def _make_egg(tmp_path, name="pydevd-pycharm.egg"):
    """Build a zip egg holding the native pieces that cannot load from an
    archive, returning its path"""
    egg_path = tmp_path / name
    with zipfile.ZipFile(egg_path, "w") as archive:
        archive.writestr("pydevd.py", "connected = False\n")
        archive.writestr("pydevd_attach_to_process/attach.dylib", b"\xcf\xfa\xed\xfe")

    return egg_path


def test_unpack_egg_expects_native_helper_on_disk(mocker, tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    egg_path = _make_egg(tmp_path)
    mocker.patch(
        "pycharmremotedebug.bridge._resolve_config_path",
        return_value=tmp_path / "Intermediate",
    )
    mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    result = bridge._unpack_egg(egg_path)

    # Assert - the dylib must be a real file, not a zip member
    assert result.is_dir()
    assert (result / "pydevd_attach_to_process" / "attach.dylib").is_file()


def test_unpack_egg_already_unpacked_expects_no_re_extract(mocker, tmp_path):
    # Arrange
    from pycharmremotedebug import bridge

    egg_path = _make_egg(tmp_path)
    mocker.patch(
        "pycharmremotedebug.bridge._resolve_config_path",
        return_value=tmp_path / "Intermediate",
    )
    mocker.patch("pycharmremotedebug.bridge.unreal")

    first = bridge._unpack_egg(egg_path)
    marker = first / "marker.txt"
    marker.touch()

    # Act
    second = bridge._unpack_egg(egg_path)

    # Assert
    assert second == first
    assert marker.is_file()


def test_unpack_egg_corrupt_expects_egg_path_returned(mocker, tmp_path):
    # Arrange - a corrupt egg must degrade, not raise
    from pycharmremotedebug import bridge

    egg_path = tmp_path / "pydevd-pycharm.egg"
    egg_path.write_bytes(b"not a zip")
    mocker.patch(
        "pycharmremotedebug.bridge._resolve_config_path",
        return_value=tmp_path / "Intermediate",
    )
    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    result = bridge._unpack_egg(egg_path)

    # Assert
    assert result == egg_path
    mock_unreal.log_warning.assert_called_once()


def test_unpack_egg_updated_pycharm_expects_new_directory(mocker, tmp_path):
    # Arrange - an updated egg must not reuse the unpacked copy
    from pycharmremotedebug import bridge

    egg_path = _make_egg(tmp_path)
    mocker.patch(
        "pycharmremotedebug.bridge._resolve_config_path",
        return_value=tmp_path / "Intermediate",
    )
    mocker.patch("pycharmremotedebug.bridge.unreal")

    first = bridge._unpack_egg(egg_path)

    with zipfile.ZipFile(egg_path, "w") as archive:
        archive.writestr("pydevd.py", "connected = False\n# newer build\n")

    # Act
    second = bridge._unpack_egg(egg_path)

    # Assert
    assert second != first


def test_route_pydevd_info_logging_expects_info_sent_to_unreal_log(mocker, monkeypatch):
    # Arrange
    from pycharmremotedebug import bridge

    pydev_log = types.ModuleType("pydev_log")
    pydev_log.info = MagicMock()
    pydev_log.error = MagicMock()
    original_error = pydev_log.error

    bundle = types.ModuleType("_pydev_bundle")
    bundle.pydev_log = pydev_log
    monkeypatch.setitem(sys.modules, "_pydev_bundle", bundle)
    monkeypatch.setitem(sys.modules, "_pydev_bundle.pydev_log", pydev_log)

    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    bridge._route_pydevd_info_logging()
    pydev_log.info("Connected to: <socket ...>")

    # Assert
    mock_unreal.log.assert_called_once_with("[pydevd] Connected to: <socket ...>")
    assert pydev_log.error is original_error  # errors must stay errors


def test_route_pydevd_info_logging_no_pydevd_expects_no_raise(mocker, monkeypatch):
    # Arrange - _pydev_bundle is absent outside a live session
    from pycharmremotedebug import bridge

    monkeypatch.delitem(sys.modules, "_pydev_bundle", raising=False)
    mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act / Assert - must not raise
    bridge._route_pydevd_info_logging()


def test_notify_error_expects_logged_and_shown_as_failure(mocker):
    # Arrange
    from pycharmremotedebug import bridge

    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    bridge._notify("no PyCharm path", is_error=True)

    # Assert
    mock_unreal.log_error.assert_called_once_with("no PyCharm path")
    mock_unreal.PyCharmRemoteDebugNotifications.show_notification.assert_called_once_with(
        "no PyCharm path", True
    )


def test_notify_stale_binary_expects_no_raise(mocker):
    # Arrange - a plugin binary predating the notification class
    from pycharmremotedebug import bridge

    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")
    mock_unreal.PyCharmRemoteDebugNotifications.show_notification.side_effect = (
        AttributeError("no attribute 'show_notification'")
    )

    # Act / Assert - must not raise, and the outcome still reaches the log
    bridge._notify("connected")

    mock_unreal.log.assert_called_once_with("connected")
    mock_unreal.log_warning.assert_called_once()


def test_connect_already_connected_expects_no_op(mocker):
    # Arrange
    from pycharmremotedebug import bridge

    mocker.patch("pycharmremotedebug.bridge.is_connected", return_value=True)
    mock_get_debug_egg = mocker.patch("pycharmremotedebug.bridge._get_debug_egg")

    # Act
    bridge.connect()

    # Assert
    mock_get_debug_egg.assert_not_called()


def test_connect_invalid_egg_expects_error_logged_and_settrace_not_called(
    mocker, fake_pydevd_pycharm
):
    # Arrange
    from pycharmremotedebug import bridge
    from pycharmremotedebug.exceptions import PyCharmRemoteDebugRuntimeError

    mocker.patch("pycharmremotedebug.bridge.is_connected", return_value=False)
    mocker.patch(
        "pycharmremotedebug.bridge._get_debug_egg",
        side_effect=PyCharmRemoteDebugRuntimeError("bad egg"),
    )
    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    bridge.connect()

    # Assert
    mock_unreal.log_error.assert_called_once_with("bad egg")
    fake_pydevd_pycharm.settrace.assert_not_called()


def test_connect_valid_egg_expects_settrace_called(
    mocker, tmp_path, fake_pydevd_pycharm
):
    # Arrange
    from pycharmremotedebug import bridge

    egg_path = tmp_path / "pydevd-pycharm.egg"
    egg_path.touch()

    mocker.patch("pycharmremotedebug.bridge.is_connected", return_value=False)
    mocker.patch("pycharmremotedebug.bridge.purge_stale_pydevd")
    mocker.patch(
        "pycharmremotedebug.bridge._get_debug_egg", return_value=egg_path.as_posix()
    )
    _mock_settings(mocker, port_number=5678, host="localhost")
    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    bridge.connect()

    # Assert
    fake_pydevd_pycharm.settrace.assert_called_once_with(
        "localhost",
        port=5678,
        stdoutToServer=True,
        stderrToServer=True,
    )
    mock_unreal.log.assert_called_once_with("Connected to PyCharm debugger")
    assert egg_path.as_posix() in sys.path
    sys.path.remove(egg_path.as_posix())


def test_connect_custom_host_expects_settrace_called_with_host(
    mocker, tmp_path, fake_pydevd_pycharm
):
    # Arrange
    from pycharmremotedebug import bridge

    egg_path = tmp_path / "pydevd-pycharm.egg"
    egg_path.touch()

    mocker.patch("pycharmremotedebug.bridge.is_connected", return_value=False)
    mocker.patch("pycharmremotedebug.bridge.purge_stale_pydevd")
    mocker.patch(
        "pycharmremotedebug.bridge._get_debug_egg", return_value=egg_path.as_posix()
    )
    _mock_settings(mocker, port_number=9999, host="192.168.1.50")
    mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    bridge.connect()

    # Assert
    fake_pydevd_pycharm.settrace.assert_called_once_with(
        "192.168.1.50",
        port=9999,
        stdoutToServer=True,
        stderrToServer=True,
    )
    sys.path.remove(egg_path.as_posix())


def test_disconnect_not_connected_expects_no_op(mocker):
    # Arrange
    from pycharmremotedebug import bridge

    mocker.patch("pycharmremotedebug.bridge.is_connected", return_value=False)
    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    bridge.disconnect()

    # Assert
    mock_unreal.log.assert_called_once_with(
        "Not connected to PyCharm debugger, nothing to do"
    )


def test_disconnect_connected_expects_stoptrace_called(mocker, monkeypatch):
    # Arrange
    from pycharmremotedebug import bridge

    fake_pydevd = types.ModuleType("pydevd")
    fake_pydevd.stoptrace = mocker.MagicMock()
    monkeypatch.setitem(sys.modules, "pydevd", fake_pydevd)

    mocker.patch("pycharmremotedebug.bridge.is_connected", return_value=True)
    mock_unreal = mocker.patch("pycharmremotedebug.bridge.unreal")

    # Act
    bridge.disconnect()

    # Assert
    fake_pydevd.stoptrace.assert_called_once()
    mock_unreal.log.assert_called_once_with("Disconnected from PyCharm debugger")
