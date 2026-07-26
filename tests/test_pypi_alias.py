"""Validate bravia-connect PyPI alias metadata stays pinned to __version__."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pybravia_connect

ROOT = Path(__file__).resolve().parents[1]
BUILD_ALIAS = ROOT / "tools" / "build_pypi_alias.py"


def test_pypi_alias_metadata_matches_version() -> None:
    result = subprocess.run(
        [sys.executable, str(BUILD_ALIAS), "--check-only"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert pybravia_connect.__version__ in result.stdout
    assert "bravia-connect" in result.stdout
