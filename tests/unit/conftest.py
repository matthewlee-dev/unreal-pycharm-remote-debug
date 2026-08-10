import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def mock_unreal(monkeypatch):
    unreal_mock = MagicMock()
    monkeypatch.setitem(__import__("sys").modules, "unreal", unreal_mock)
    return unreal_mock
