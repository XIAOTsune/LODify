from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "blender_manifest.toml"
INIT_PATH = ROOT / "__init__.py"
VERSION_RE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"\s*$')
BL_INFO_VERSION_RE = re.compile(
    r'(?m)^\s*"version"\s*:\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*$'
)
BUILD_PATHS_RE = re.compile(r"(?ms)^\[build\]\s*paths\s*=\s*\[(.*?)\]")
WHEELS_RE = re.compile(r"(?ms)^wheels\s*=\s*\[(.*?)\]")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def fail(message: str) -> None:
    raise SystemExit(f"Release build failed: {message}")


def toml_strings(value: str, label: str) -> list[str]:
    strings = re.findall(r'"([^"\\]*)"', value)
    remainder = re.sub(r'"[^"\\]*"|[\s,]', "", value)
    if remainder:
        fail(f"unsupported syntax in manifest {label}")
    return strings


def read_manifest() -> tuple[str, list[str], list[str]]:
    if not MANIFEST_PATH.is_file():
        fail("blender_manifest.toml is missing")

    manifest = MANIFEST_PATH.read_text(encoding="utf-8")
    root_table = manifest.split("\n[", maxsplit=1)[0]
    version_match = VERSION_RE.search(root_table)
    paths_match = BUILD_PATHS_RE.search(manifest)
    wheels_match = WHEELS_RE.search(root_table)
    if not version_match or not paths_match or not wheels_match:
        fail("manifest must define version, wheels, and [build].paths")

    version = version_match.group(1)
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"expected a stable semantic version, got {version!r}")
    paths = toml_strings(paths_match.group(1), "build.paths")
    wheels = [item.removeprefix("./") for item in toml_strings(wheels_match.group(1), "wheels")]
    if not paths:
        fail("manifest [build].paths is empty")
    return version, paths, wheels


def collect_files(paths: list[str]) -> list[Path]:
    files: set[Path] = set()
    for item in paths:
        path = (ROOT / item).resolve()
        if ROOT not in path.parents:
            fail(f"build path escapes the project: {item}")
        if not path.exists():
            fail(f"build path does not exist: {item}")
        candidates = [path] if path.is_file() else sorted(path.rglob("*"))
        for candidate in candidates:
            if candidate.is_symlink():
                fail(f"symbolic links are not supported: {candidate.relative_to(ROOT)}")
            if candidate.is_file():
                relative = candidate.relative_to(ROOT)
                if "__pycache__" in relative.parts or candidate.suffix == ".pyc":
                    continue
                files.add(candidate)

    if not files:
        fail("build paths contain no files")
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def validate_sources(version: str, files: list[Path], wheels: list[str]) -> None:
    if not INIT_PATH.is_file():
        fail("__init__.py is missing")
    init_text = INIT_PATH.read_text(encoding="utf-8")
    match = BL_INFO_VERSION_RE.search(init_text)
    expected = tuple(int(part) for part in version.split("."))
    actual = tuple(int(part) for part in match.groups()) if match else None
    if actual != expected:
        fail(f"bl_info version {actual!r} does not match manifest version {version}")

    packaged_paths = {path.relative_to(ROOT).as_posix() for path in files}
    for required in ("__init__.py", "blender_manifest.toml"):
        if required not in packaged_paths:
            fail(f"manifest build.paths does not include {required}")
    for wheel in wheels:
        if wheel not in packaged_paths:
            fail(f"manifest wheel is missing from build.paths: {wheel}")
        if not (ROOT / wheel).is_file():
            fail(f"manifest wheel does not exist: {wheel}")


def write_archive(output_path: Path, files: list[Path]) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_path.parent, suffix=".tmp", delete=False) as temporary:
        temporary_path = Path(temporary.name)

    try:
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for source in files:
                relative_path = source.relative_to(ROOT).as_posix()
                info = zipfile.ZipInfo(relative_path, date_time=ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

        with zipfile.ZipFile(temporary_path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                fail(f"archive integrity check failed at {bad_member}")
            names = set(archive.namelist())
            for required in ("__init__.py", "blender_manifest.toml", "operators/__init__.py", "ui/__init__.py"):
                if required not in names:
                    fail(f"archive is missing required file: {required}")

        digest = hashlib.sha256(temporary_path.read_bytes()).hexdigest()
        os.replace(temporary_path, output_path)
        return digest
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Blender-installable LODify release zip.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist",
        help="directory for the zip and SHA-256 sidecar (default: dist)",
    )
    args = parser.parse_args()

    version, paths, wheels = read_manifest()
    files = collect_files(paths)
    validate_sources(version, files, wheels)

    output_path = args.output_dir.resolve() / f"LODifyv{version}.zip"
    digest = write_archive(output_path, files)
    checksum_path = output_path.with_suffix(output_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {output_path.name}\n", encoding="ascii")

    print(f"Package: {output_path}")
    print(f"Files: {len(files)}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
