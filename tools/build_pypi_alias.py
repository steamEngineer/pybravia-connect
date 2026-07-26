#!/usr/bin/env python3
"""Build PyPI alias wheels/sdists into dist/.

Reads ``__version__`` from ``src/pybravia_connect/__init__.py`` and generates
dependency-only packages that pin ``pybravia-connect==<version>``. No importable
code — install names only; import remains ``pybravia_connect``.
"""

from __future__ import annotations

import argparse
import email
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
INIT_PATH = ROOT / "src" / "pybravia_connect" / "__init__.py"
ALIASES = ("bravia-connect", "bravaconnect")
CANONICAL_NAME = "pybravia-connect"

_VERSION_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.M)


def read_version() -> str:
    text = INIT_PATH.read_text(encoding="utf-8")
    match = _VERSION_RE.search(text)
    if match is None:
        raise SystemExit(f"Could not find __version__ in {INIT_PATH}")
    return match.group(1)


def normalized_prefix(name: str) -> str:
    """PEP 503-ish filename prefix: hyphens become underscores."""
    return name.replace("-", "_")


def alias_readme(name: str) -> Path:
    path = ROOT / "alias" / name / "README.md"
    if not path.is_file():
        raise SystemExit(f"Missing alias README: {path}")
    return path


def write_alias_project(project_dir: Path, *, name: str, version: str) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(alias_readme(name), project_dir / "README.md")
    pyproject = f"""\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "{version}"
description = "PyPI alias for {CANONICAL_NAME} (same library; import pybravia_connect)"
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [{{ name = "steamEngineer" }}]
dependencies = ["{CANONICAL_NAME}=={version}"]

[project.optional-dependencies]
crypto = ["{CANONICAL_NAME}[crypto]=={version}"]

[project.urls]
Homepage = "https://github.com/steamEngineer/pybravia-connect"
Repository = "https://github.com/steamEngineer/pybravia-connect"
Issues = "https://github.com/steamEngineer/pybravia-connect/issues"

[tool.hatch.build.targets.wheel]
bypass-selection = true

[tool.hatch.build.targets.sdist]
include = ["README.md", "pyproject.toml"]
"""
    (project_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")


def collect_alias_artifacts(outdir: Path, name: str) -> list[Path]:
    prefixes = (name, normalized_prefix(name))
    found = sorted(
        p
        for p in outdir.iterdir()
        if any(p.name.startswith(f"{prefix}-") for prefix in prefixes)
    )
    if not found:
        raise SystemExit(f"No alias artifacts for {name!r} in {outdir}")
    return found


def build_alias(*, name: str, outdir: Path, version: str) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{normalized_prefix(name)}-alias-") as tmp:
        project_dir = Path(tmp) / "alias"
        write_alias_project(project_dir, name=name, version=version)
        subprocess.run(
            [sys.executable, "-m", "build", "--outdir", str(outdir.resolve())],
            cwd=project_dir,
            check=True,
        )
    return collect_alias_artifacts(outdir, name)


def assert_alias_metadata(wheel: Path, *, name: str, version: str) -> None:
    with ZipFile(wheel) as zf:
        meta_name = next(n for n in zf.namelist() if n.endswith(".dist-info/METADATA"))
        msg = email.message_from_bytes(zf.read(meta_name))
    if msg["Name"] != name:
        raise SystemExit(f"Alias Name={msg['Name']!r}, expected {name!r}")
    if msg["Version"] != version:
        raise SystemExit(f"Alias Version={msg['Version']!r}, expected {version!r}")
    requires = msg.get_all("Requires-Dist") or []
    expected_pin = f"{CANONICAL_NAME}=={version}"
    if not any(r.split(";")[0].strip() == expected_pin for r in requires):
        raise SystemExit(
            f"Alias {name!r} missing Requires-Dist {expected_pin!r}; got {requires!r}"
        )


def build_all_aliases(*, outdir: Path, version: str) -> list[Path]:
    all_artifacts: list[Path] = []
    for name in ALIASES:
        artifacts = build_alias(name=name, outdir=outdir, version=version)
        wheel = next(p for p in artifacts if p.suffix == ".whl")
        assert_alias_metadata(wheel, name=name, version=version)
        all_artifacts.extend(artifacts)
    return all_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "dist",
        help="Directory for built artifacts (default: dist/)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Build to a temp dir and validate metadata; do not write outdir",
    )
    args = parser.parse_args(argv)
    version = read_version()
    if args.check_only:
        with tempfile.TemporaryDirectory(prefix="pypi-alias-check-") as tmp:
            build_all_aliases(outdir=Path(tmp), version=version)
        for name in ALIASES:
            print(f"OK: {name}=={version} -> {CANONICAL_NAME}=={version}")
        return 0

    artifacts = build_all_aliases(outdir=args.outdir, version=version)
    for path in artifacts:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
