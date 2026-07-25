"""Smoke tests for the package shell."""

import pybravia_connect


def test_version() -> None:
    assert pybravia_connect.__version__ == "0.0.0"
