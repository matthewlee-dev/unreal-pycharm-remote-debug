import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, (Path(__file__).resolve().parents[2] / "scripts").as_posix())


def _make_plugin(root, name="PyCharmRemoteDebug"):
    """Build a plugin directory carrying the leftovers a real one has"""
    plugin_dir = root / name
    (plugin_dir / "Source" / name / "Private").mkdir(parents=True)
    (plugin_dir / "Content" / "Python" / "pycharmremotedebug").mkdir(parents=True)

    (plugin_dir / f"{name}.uplugin").write_text(
        json.dumps({"Version": 1, "VersionName": "1", "EngineVersion": "5.7.0"}),
        encoding="utf-8",
    )
    (plugin_dir / "Source" / name / "Private" / "Module.cpp").write_text("// code")
    (plugin_dir / "Content" / "Python" / "pycharmremotedebug" / "bridge.py").write_text(
        "x=1"
    )

    # must not reach Fab
    (plugin_dir / "Binaries" / "Mac").mkdir(parents=True)
    (plugin_dir / "Binaries" / "Mac" / "plugin.dylib").write_text("binary")
    (plugin_dir / "Intermediate" / "Build").mkdir(parents=True)
    (plugin_dir / "Intermediate" / "Build" / "gen.cpp").write_text("generated")
    (plugin_dir / "Content" / ".DS_Store").write_text("finder")
    (
        plugin_dir / "Content" / "Python" / "pycharmremotedebug" / "bridge.pyc"
    ).write_text("b")

    return plugin_dir


def test_version_code_expects_parts_packed():
    # Arrange
    from package_plugin import version_code

    # Act / Assert
    assert version_code("1.2.0") == 10200
    assert version_code("0.0.1") == 1
    assert version_code("2.10.30") == 21030


def test_version_code_expects_ordering_preserved():
    # Arrange - Version is an increasing build number
    from package_plugin import version_code

    # Act / Assert
    assert version_code("1.2.0") < version_code("1.2.1") < version_code("1.3.0")
    assert version_code("1.3.0") < version_code("2.0.0")


@pytest.mark.parametrize("version", ["1.2", "1.2.0.1", "1.two.0", "", "-1.0.0"])
def test_version_code_malformed_expects_ValueError_raised(version):
    # Arrange
    from package_plugin import version_code

    # Act / Assert
    with pytest.raises(ValueError):
        version_code(version)


def test_version_code_part_too_large_expects_ValueError_raised():
    # Arrange - 100 would collide with the next place value
    from package_plugin import version_code

    # Act / Assert
    with pytest.raises(ValueError) as _ex:
        version_code("1.100.0")

    assert "below 100" in str(_ex)


@pytest.mark.parametrize(
    "engine_version,expected",
    [("5.6", "5.6.0"), ("5.6.0", "5.6.0"), ("5.6.1", "5.6.1"), ("5.10", "5.10.0")],
)
def test_engine_version_string_expects_three_components(engine_version, expected):
    # Arrange - Unreal warns on launch for anything it cannot parse
    from package_plugin import engine_version_string

    # Act
    result = engine_version_string(engine_version)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "engine_version", ["5", "5.6.0.1", "5.six", "", "-5.6", "5.-6"]
)
def test_engine_version_string_malformed_expects_ValueError_raised(engine_version):
    # Arrange
    from package_plugin import engine_version_string

    # Act / Assert
    with pytest.raises(ValueError):
        engine_version_string(engine_version)


def test_stamp_uplugin_expects_version_fields_written(tmp_path):
    # Arrange
    from package_plugin import stamp_uplugin

    uplugin = tmp_path / "PyCharmRemoteDebug.uplugin"
    uplugin.write_text(
        json.dumps({"Version": 1, "VersionName": "1", "FriendlyName": "x"})
    )

    # Act
    stamp_uplugin(uplugin, "1.2.0", "5.6")

    # Assert
    descriptor = json.loads(uplugin.read_text())
    assert descriptor["Version"] == 10200
    assert descriptor["VersionName"] == "1.2.0"
    assert descriptor["EngineVersion"] == "5.6.0"  # Unreal cannot parse "5.6"
    assert descriptor["FriendlyName"] == "x"  # untouched fields survive


def test_package_expects_build_output_excluded(tmp_path):
    # Arrange
    from package_plugin import package

    plugin_dir = _make_plugin(tmp_path / "src")

    # Act
    zip_path = package(plugin_dir, tmp_path / "out", "1.2.0", "5.7")

    # Assert
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()

    assert not [n for n in names if "Binaries" in n or "Intermediate" in n]
    assert not [n for n in names if n.endswith(".DS_Store") or n.endswith(".pyc")]


def test_package_expects_plugin_folder_at_archive_root(tmp_path):
    # Arrange - Fab expects the plugin folder at the top level
    from package_plugin import package

    plugin_dir = _make_plugin(tmp_path / "src")

    # Act
    zip_path = package(plugin_dir, tmp_path / "out", "1.2.0", "5.7")

    # Assert
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()

    assert "PyCharmRemoteDebug/PyCharmRemoteDebug.uplugin" in names
    assert all(name.startswith("PyCharmRemoteDebug/") for name in names)


def test_package_expects_source_and_content_kept(tmp_path):
    # Arrange
    from package_plugin import package

    plugin_dir = _make_plugin(tmp_path / "src")

    # Act
    zip_path = package(plugin_dir, tmp_path / "out", "1.2.0", "5.7")

    # Assert
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()

    assert "PyCharmRemoteDebug/Source/PyCharmRemoteDebug/Private/Module.cpp" in names
    assert "PyCharmRemoteDebug/Content/Python/pycharmremotedebug/bridge.py" in names


def test_package_expects_stamped_uplugin_in_zip(tmp_path):
    # Arrange
    from package_plugin import package

    plugin_dir = _make_plugin(tmp_path / "src")

    # Act
    zip_path = package(plugin_dir, tmp_path / "out", "1.2.0", "5.6")

    # Assert
    with zipfile.ZipFile(zip_path) as archive:
        descriptor = json.loads(
            archive.read("PyCharmRemoteDebug/PyCharmRemoteDebug.uplugin")
        )

    assert descriptor["VersionName"] == "1.2.0"
    assert descriptor["EngineVersion"] == "5.6.0"  # Unreal cannot parse "5.6"


def test_package_expects_source_uplugin_untouched(tmp_path):
    # Arrange - stamping must happen on the staged copy, never the repo
    from package_plugin import package

    plugin_dir = _make_plugin(tmp_path / "src")
    before = (plugin_dir / "PyCharmRemoteDebug.uplugin").read_text()

    # Act
    package(plugin_dir, tmp_path / "out", "1.2.0", "5.6")

    # Assert
    assert (plugin_dir / "PyCharmRemoteDebug.uplugin").read_text() == before


def test_package_expects_zip_named_for_version_and_engine(tmp_path):
    # Arrange
    from package_plugin import package

    plugin_dir = _make_plugin(tmp_path / "src")

    # Act
    zip_path = package(plugin_dir, tmp_path / "out", "1.2.0", "5.7")

    # Assert
    assert zip_path.name == "PyCharmRemoteDebug-1.2.0-UE5.7.zip"


def test_package_no_uplugin_expects_FileNotFoundError_raised(tmp_path):
    # Arrange
    from package_plugin import package

    plugin_dir = tmp_path / "src" / "NotAPlugin"
    plugin_dir.mkdir(parents=True)

    # Act / Assert
    with pytest.raises(FileNotFoundError):
        package(plugin_dir, tmp_path / "out", "1.2.0", "5.7")


def test_package_twice_expects_no_leftovers_from_first_run(tmp_path):
    # Arrange - staging is reused between engine versions in one workflow run
    from package_plugin import package

    plugin_dir = _make_plugin(tmp_path / "src")
    package(plugin_dir, tmp_path / "out", "1.2.0", "5.6")
    (plugin_dir / "Content" / "Python" / "pycharmremotedebug" / "bridge.py").unlink()

    # Act
    zip_path = package(plugin_dir, tmp_path / "out", "1.2.0", "5.7")

    # Assert
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()

    assert "PyCharmRemoteDebug/Content/Python/pycharmremotedebug/bridge.py" not in names
