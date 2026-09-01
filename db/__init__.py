"""
Database access: connections, schema versioning, backups.

Deliberately independent of the rest of the app (it imports neither cache nor
anything else): the database path always arrives from outside, so the updater
too — which runs in a separate process where the app is not loaded — can use
it to put the data somewhere safe before replacing the files.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
from . import backup
from .connection import connect
from .migrations import LATEST, current_version, ensure_current

__all__ = ["connect", "ensure_current", "current_version", "LATEST", "backup"]
