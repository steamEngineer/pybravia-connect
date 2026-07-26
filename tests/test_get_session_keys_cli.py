"""Tests for tools/get_session_keys.py helpers."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "tools"))

from get_session_keys import extract_ssh_app_redirect_from_har, main  # noqa: E402

SSH_APP = "ssh-app://signin?code=abc123&state=state456"


def test_extract_ssh_app_redirect_from_har(tmp_path: Path) -> None:
    har = {
        "log": {
            "entries": [
                {
                    "request": {"url": "https://example.com/"},
                    "response": {"headers": [{"name": "Location", "value": SSH_APP}]},
                }
            ]
        }
    }
    path = tmp_path / "capture.har"
    path.write_text(json.dumps(har), encoding="utf-8")
    assert extract_ssh_app_redirect_from_har(path) == SSH_APP


def test_extract_ssh_app_redirect_from_har_missing(tmp_path: Path) -> None:
    har = {"log": {"entries": []}}
    path = tmp_path / "empty.har"
    path.write_text(json.dumps(har), encoding="utf-8")
    with pytest.raises(ValueError, match="No ssh-app://"):
        extract_ssh_app_redirect_from_har(path)


def test_cli_help() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
