"""
Automatic updates: checking, signature verification, installation.

The process that actually replaces the files lives in updater_bin/, kept
separate on purpose: on Windows a running executable cannot overwrite
itself.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
from . import install_kind, manifest, runner, signature

__all__ = ["manifest", "signature", "install_kind", "runner"]
