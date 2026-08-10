import sys
import types

import pytest


@pytest.fixture
def fake_pydevd(monkeypatch):
    """Insert a fake pydevd module tree into sys.modules"""
    modules = {
        "pydevd": types.ModuleType("pydevd"),
        "pydevd_pycharm": types.ModuleType("pydevd_pycharm"),
        "_pydevd_bundle": types.ModuleType("_pydevd_bundle"),
        "_pydev_bundle": types.ModuleType("_pydev_bundle"),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    return modules


@pytest.fixture
def wrapped_streams(monkeypatch):
    """Put sys into the state pydevd leaves behind after a connect"""
    unreal_stdout = types.SimpleNamespace(name="unreal stdout")
    unreal_stderr = types.SimpleNamespace(name="unreal stderr")

    monkeypatch.setattr(sys, "stdout", types.SimpleNamespace(name="pydevd wrapper"))
    monkeypatch.setattr(sys, "stderr", types.SimpleNamespace(name="pydevd wrapper"))

    # set directly: the code deletes these, and monkeypatch teardown would fail
    pydevd_attributes = {
        "_pydevd_out_buffer_": object(),
        "_pydevd_err_buffer_": object(),
        "stdout_original": unreal_stdout,
        "stderr_original": unreal_stderr,
    }
    for attribute, value in pydevd_attributes.items():
        setattr(sys, attribute, value)

    yield unreal_stdout, unreal_stderr

    for attribute in pydevd_attributes:
        if hasattr(sys, attribute):
            delattr(sys, attribute)


def test_restore_streams_wrapped_expects_unreal_streams_back(wrapped_streams):
    # Arrange
    from pycharmremotedebug.session import restore_streams

    unreal_stdout, unreal_stderr = wrapped_streams

    # Act
    restored = restore_streams()

    # Assert
    assert restored == 2
    assert sys.stdout is unreal_stdout
    assert sys.stderr is unreal_stderr


def test_restore_streams_wrapped_expects_guard_attributes_cleared(wrapped_streams):
    # Arrange - the guards make the next settrace() skip rewiring
    from pycharmremotedebug.session import restore_streams

    # Act
    restore_streams()

    # Assert
    for attribute in (
        "_pydevd_out_buffer_",
        "_pydevd_err_buffer_",
        "stdout_original",
        "stderr_original",
    ):
        assert not hasattr(sys, attribute)


def test_restore_streams_never_wrapped_expects_streams_untouched():
    # Arrange
    from pycharmremotedebug.session import restore_streams

    for attribute in ("_pydevd_out_buffer_", "_pydevd_err_buffer_"):
        if hasattr(sys, attribute):
            delattr(sys, attribute)
    before_stdout, before_stderr = sys.stdout, sys.stderr

    # Act
    restored = restore_streams()

    # Assert
    assert restored == 0
    assert sys.stdout is before_stdout
    assert sys.stderr is before_stderr


def test_purge_stale_pydevd_disconnected_expects_streams_restored(
    fake_pydevd, wrapped_streams
):
    # Arrange
    from pycharmremotedebug.session import purge_stale_pydevd

    fake_pydevd["pydevd"].get_global_debugger = lambda: None
    unreal_stdout, unreal_stderr = wrapped_streams

    # Act
    purge_stale_pydevd()

    # Assert
    assert sys.stdout is unreal_stdout
    assert sys.stderr is unreal_stderr


def test_purge_stale_pydevd_connected_expects_streams_left_wrapped(
    fake_pydevd, wrapped_streams
):
    # Arrange - a live session keeps its streams on the debugger
    from pycharmremotedebug.session import purge_stale_pydevd

    fake_pydevd["pydevd"].get_global_debugger = lambda: object()
    wrapper_stdout = sys.stdout

    # Act
    purge_stale_pydevd()

    # Assert
    assert sys.stdout is wrapper_stdout
    assert hasattr(sys, "_pydevd_out_buffer_")


def test_is_connected_pydevd_not_imported_expects_false():
    # Arrange
    from pycharmremotedebug.session import is_connected

    sys.modules.pop("pydevd", None)

    # Act / Assert
    assert is_connected() is False


def test_is_connected_live_debugger_expects_true(fake_pydevd):
    # Arrange
    from pycharmremotedebug.session import is_connected

    fake_pydevd["pydevd"].get_global_debugger = lambda: object()

    # Act / Assert
    assert is_connected() is True


def test_is_connected_after_stoptrace_expects_false(fake_pydevd):
    # Arrange - stoptrace() disposes the debugger but leaves the latch True
    from pycharmremotedebug.session import is_connected

    fake_pydevd["pydevd"].get_global_debugger = lambda: None
    fake_pydevd["pydevd"].connected = True

    # Act / Assert
    assert is_connected() is False


def test_is_connected_no_global_debugger_api_expects_false(fake_pydevd):
    # Arrange - unrecognised pydevd reads as disconnected, never via the latch
    from pycharmremotedebug.session import is_connected

    fake_pydevd["pydevd"].connected = True

    # Act / Assert
    assert is_connected() is False


def test_purge_stale_pydevd_disconnected_expects_modules_removed(fake_pydevd):
    # Arrange
    from pycharmremotedebug.session import purge_stale_pydevd

    fake_pydevd["pydevd"].get_global_debugger = lambda: None

    # Act
    purged = purge_stale_pydevd()

    # Assert
    assert purged == len(fake_pydevd)
    for name in fake_pydevd:
        assert name not in sys.modules


def test_purge_stale_pydevd_connected_expects_no_purge(fake_pydevd):
    # Arrange
    from pycharmremotedebug.session import purge_stale_pydevd

    fake_pydevd["pydevd"].get_global_debugger = lambda: object()

    # Act
    purged = purge_stale_pydevd()

    # Assert
    assert purged == 0
    for name in fake_pydevd:
        assert name in sys.modules
