"""Smoke tests for the package shell."""

import pybravia_connect


def test_version() -> None:
    assert isinstance(pybravia_connect.__version__, str)
    assert pybravia_connect.__version__


def test_public_exports() -> None:
    assert pybravia_connect.BraviaConnectClient is not None
    assert pybravia_connect.DEFAULT_THEATRE_PORT == 55051
