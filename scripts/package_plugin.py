"""Package the plugin into the source zip Fab expects.

Fab distributes code plugins as source and Epic compiles them. One zip per
engine version, since the target engine is recorded inside the .uplugin.
"""

import argparse
import json
import shutil
import zipfile
from pathlib import Path

# build leftovers and tooling droppings, none of which may reach Fab
EXCLUDED_DIRECTORIES = frozenset(
    {
        "Binaries",
        "Intermediate",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".idea",
        ".vscode",
    }
)
EXCLUDED_SUFFIXES = (".pyc", ".pyo")
EXCLUDED_NAMES = frozenset({".DS_Store", "Thumbs.db"})


def parse_version(version: str) -> tuple[int, int, int]:
    """Split "major.minor.patch" into its numeric parts

    Raises:
        ValueError: not three dot-separated non-negative integers
    """
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Expected a major.minor.patch version, got {version!r}")

    try:
        major, minor, patch = (int(part) for part in parts)
    except ValueError as exc:
        raise ValueError(f"Version parts must be integers, got {version!r}") from exc

    if major < 0 or minor < 0 or patch < 0:
        raise ValueError(f"Version parts must not be negative, got {version!r}")

    return major, minor, patch


def version_code(version: str) -> int:
    """Pack a version string into the integer .uplugin "Version" field

    Unreal wants an increasing build number there, so parts are packed two
    digits each: 1.2.0 -> 10200, preserving order.

    Raises:
        ValueError: malformed, or a part too large to pack
    """
    major, minor, patch = parse_version(version)
    if minor > 99 or patch > 99:
        raise ValueError(
            f"Minor and patch must each be below 100 to pack into a version "
            f"code, got {version!r}"
        )

    return major * 10000 + minor * 100 + patch


def is_excluded(path: Path) -> bool:
    """Check whether a plugin-relative path must stay out of the artifact"""
    if EXCLUDED_DIRECTORIES.intersection(path.parts):
        return True

    return path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES


def stamp_uplugin(uplugin_path: Path, version: str, engine_version: str) -> dict:
    """Write the release version and target engine into a .uplugin in place

    Raises:
        ValueError: the version is malformed
    """
    descriptor = json.loads(uplugin_path.read_text(encoding="utf-8"))

    descriptor["Version"] = version_code(version)
    descriptor["VersionName"] = version
    descriptor["EngineVersion"] = engine_version

    uplugin_path.write_text(
        json.dumps(descriptor, indent="\t") + "\n", encoding="utf-8"
    )

    return descriptor


def stage_plugin(plugin_dir: Path, staging_dir: Path) -> Path:
    """Copy the plugin into a staging directory, minus everything excluded"""
    staged = staging_dir / plugin_dir.name
    shutil.rmtree(staged, ignore_errors=True)

    for source in sorted(plugin_dir.rglob("*")):
        relative = source.relative_to(plugin_dir)
        if is_excluded(relative):
            continue

        target = staged / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    return staged


def write_zip(staged_plugin: Path, zip_path: Path) -> Path:
    """Zip a staged plugin with the plugin folder at the archive root"""
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(staged_plugin.rglob("*")):
            if source.is_file():
                arcname = Path(staged_plugin.name) / source.relative_to(staged_plugin)
                archive.write(source, arcname.as_posix())

    return zip_path


def package(
    plugin_dir: Path, output_dir: Path, version: str, engine_version: str
) -> Path:
    """Build one release zip for a single engine version

    Raises:
        FileNotFoundError: the plugin directory has no .uplugin
    """
    uplugin_files = list(plugin_dir.glob("*.uplugin"))
    if not uplugin_files:
        raise FileNotFoundError(f"No .uplugin found in {plugin_dir}")

    staged = stage_plugin(plugin_dir, output_dir / "staging")
    stamp_uplugin(staged / uplugin_files[0].name, version, engine_version)

    zip_path = output_dir / f"{plugin_dir.name}-{version}-UE{engine_version}.zip"

    return write_zip(staged, zip_path)


def main() -> None:
    """Package the plugin for every requested engine version"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", required=True, help='e.g. "1.2.0"')
    parser.add_argument(
        "--engine-versions",
        required=True,
        help='comma separated, e.g. "5.6,5.7"',
    )
    args = parser.parse_args()

    engine_versions = [part.strip() for part in args.engine_versions.split(",")]
    for engine_version in filter(None, engine_versions):
        zip_path = package(
            args.plugin_dir, args.output_dir, args.version, engine_version
        )
        print(f"wrote {zip_path}")


if __name__ == "__main__":
    main()
