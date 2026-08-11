from pathlib import Path
import sys

import pytest


@pytest.fixture(scope="session", autouse=True)
def add_root_to_sys_path():
    root_dir = (
        Path(__file__).resolve().parents[1]
        / "plugin_src"
        / "PyCharmRemoteDebug"
        / "Content"
        / "Python"
    )
    sys.path.insert(0, root_dir.as_posix())
