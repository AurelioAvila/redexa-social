"""
How this copy was installed, and who has the right to update it.

The concrete problem: installing with `winget install` produces a package
winget considers its own and upgrades with `winget upgrade`. If the internal
updater replaced the files as well, the two would contend for the same folder
— winget would find a version other than the one it has on record, and the
user an inconsistent installation neither of them knows how to repair.

The rule: if someone else installed it, someone else updates it. The app says
so and gets out of the way.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os
import sys

PORTABLE = "portable"      # a zip the user unpacked: ours to update
WINGET = "winget"          # managed by winget: updated with winget upgrade
DEVELOPMENT = "development"  # run from source: nothing is updated

# winget puts "portable" packages under here, and creates the shortcuts in a
# neighbouring Links folder.
_WINGET_MARKERS = (
    os.path.join("microsoft", "winget", "packages"),
    os.path.join("microsoft", "winget", "links"),
)


def app_directory() -> str:
    """The folder holding the installed application."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def detect(executable_path: str | None = None) -> str:
    path = (executable_path or getattr(sys, "executable", "") or "").lower()

    if not getattr(sys, "frozen", False) and executable_path is None:
        return DEVELOPMENT
    if any(marker in path for marker in _WINGET_MARKERS):
        return WINGET
    return PORTABLE


def can_self_update(kind: str | None = None) -> bool:
    return (kind or detect()) == PORTABLE


def explain(kind: str | None = None) -> str:
    """Message code to display, translated by the interface."""
    current = kind or detect()
    if current == WINGET:
        return "update_managed_by_winget"
    if current == DEVELOPMENT:
        return "update_running_from_source"
    return ""
