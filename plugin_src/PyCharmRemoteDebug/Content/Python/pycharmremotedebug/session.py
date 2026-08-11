"""pydevd connection-state helpers.

pydevd is one-shot: stoptrace() leaves state behind that breaks the next
settrace(). Unreal's interpreter lives for the whole editor session, so we
clear that state ourselves - both sys.modules entries and the stream
wrapping pydevd installs on the sys module itself.
"""

import sys

from unreal import log

# module prefixes owned by the debug egg, all purged together on reconnect
PYDEVD_MODULE_PREFIXES = ("pydevd", "_pydevd", "_pydev_", "pydev_ipython")

# (guard attribute, stream, saved original). pydevd installs these behind
# `if not hasattr(sys, <guard>)` and never removes them, so leaving them set
# makes the next settrace() skip rewiring and use a writer bound to the
# disposed PyDB.
PYDEVD_IO_ATTRIBUTES = (
    ("_pydevd_out_buffer_", "stdout", "stdout_original"),
    ("_pydevd_err_buffer_", "stderr", "stderr_original"),
)


def is_connected() -> bool:
    """Check if pydevd currently reports a live connection to PyCharm"""
    pydevd = sys.modules.get("pydevd")
    if pydevd is None:
        return False

    # not pydevd.connected: that is a one-way latch settrace() sets and
    # stoptrace() never clears. stoptrace() does dispose the global debugger.
    get_global_debugger = getattr(pydevd, "get_global_debugger", None)
    if get_global_debugger is None:
        return False

    return get_global_debugger() is not None


def restore_streams() -> int:
    """Hand sys.stdout/sys.stderr back to Unreal, undoing pydevd's wrapping

    Returns:
        int: The number of streams restored
    """
    restored = 0
    for guard_attribute, stream_name, original_name in PYDEVD_IO_ATTRIBUTES:
        if not hasattr(sys, guard_attribute):
            continue

        # restore before dropping the bookkeeping, so a failure here cannot
        # leave sys.stdout on a dead writer
        original = getattr(sys, original_name, None)
        if original is not None:
            setattr(sys, stream_name, original)
            delattr(sys, original_name)

        delattr(sys, guard_attribute)
        restored += 1

    if restored:
        log(f"Restored {restored} stream(s) wrapped by pydevd")

    return restored


def purge_stale_pydevd() -> int:
    """Clear leftover pydevd modules and stream wrapping, unless still connected

    Returns:
        int: The number of modules purged
    """
    if is_connected():
        return 0

    restore_streams()

    stale = [name for name in sys.modules if name.startswith(PYDEVD_MODULE_PREFIXES)]
    for name in stale:
        del sys.modules[name]

    if stale:
        log(f"Purged {len(stale)} stale pydevd modules before reconnect")

    return len(stale)
