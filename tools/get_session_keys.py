#!/usr/bin/env python3
"""Deprecated path — prefer ``bravia-connect-keys`` after pip install."""

from pybravia_connect.cli.get_session_keys import main

if __name__ == "__main__":
    raise SystemExit(main())
