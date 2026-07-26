#!/usr/bin/env python3
"""Build the bravia-connect PyPI alias wheel/sdist into dist/.

Reads ``__version__`` from ``src/pybravia_connect/__init__.py`` and generates a
dependency-only package that pins ``pybravia-connect==<version>``. No importable
code — install name only; import remains ``pybravia_connect``.
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
ALIAS_README = ROOT / "alias" / "bravia-connect" / "README.md"
ALIAS_NAME = "bravia-connect"
CANONICAL_NAME = "pybravia-connect"

_VERSION_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.M)


def read_version() -> str:
    text = INIT_PATH.read_text(encoding="utf-8")
    match = _VERSION_RE.search(text)
    if match is None:
        raise SystemExit(f"Could not find __version__ in {INIT_PATH}")
    return match.group(1)


def write_alias_project(project_dir: Path, version: str) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ALIAS_README, project_dir / "README.md")
    pyproject = f"""\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{ALIAS_NAME}"
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


def build_alias(*, outdir: Path, version: str) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bravia-connect-alias-") as tmp:
        project_dir = Path(tmp) / "alias"
        write_alias_project(project_dir, version)
        subprocess.run(
            [sys.executable, "-m", "build", "--outdir", str(outdir.resolve())],
            cwd=project_dir,
            check=True,
        )
    # Wheel uses normalized underscores; sdist keeps the project name with hyphens.
    unique = sorted(
        p
        for p in outdir.iterdir()
        if p.name.startswith("bravia_connect") or p.name.startswith("bravia-connect")
    )
    if not unique:
        raise SystemExit(f"No alias artifacts found in {outdir}")
    return unique


def assert_alias_metadata(wheel: Path, version: str) -> None:
    with ZipFile(wheel) as zf:
        meta_name = next(n for n in zf.namelist() if n.endswith(".dist-info/METADATA"))
        msg = email.message_from_bytes(zf.read(meta_name))
    if msg["Name"] != ALIAS_NAME:
        raise SystemExit(f"Alias Name={msg['Name']!r}, expected {ALIAS_NAME!r}")
    if msg["Version"] != version:
        raise SystemExit(f"Alias Version={msg['Version']!r}, expected {version!r}")
    requires = msg.get_all("Requires-Dist") or []
    expected_pin = f"{CANONICAL_NAME}=={version}"
    if not any(r.split(";")[0].strip() == expected_pin for r in requires):
        raise SystemExit(
            f"Alias missing Requires-Dist {expected_pin!r}; got {requires!r}"
        )


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
        with tempfile.TemporaryDirectory(prefix="bravia-connect-alias-check-") as tmp:
            artifacts = build_alias(outdir=Path(tmp), version=version)
            wheel = next(p for p in artifacts if p.suffix == ".whl")
            assert_alias_metadata(wheel, version)
        print(f"OK: {ALIAS_NAME}=={version} -> {CANONICAL_NAME}=={version}")
        return 0

    artifacts = build_alias(outdir=args.outdir, version=version)
    wheel = next(p for p in artifacts if p.suffix == ".whl")
    assert_alias_metadata(wheel, version)
    for path in artifacts:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
