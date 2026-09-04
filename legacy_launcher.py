"""Compatibility launcher for shortcuts created before the Redexa rebrand."""

import ctypes
import os
import subprocess
import sys


def main() -> int:
    target = os.path.join(os.path.dirname(sys.executable), "Redexa Social.exe")
    if not os.path.exists(target):
        ctypes.windll.user32.MessageBoxW(
            None,
            "Redexa Social.exe is missing. Download the latest release to repair the installation.",
            "Redexa Social",
            0x10,
        )
        return 1
    subprocess.Popen([target, *sys.argv[1:]], cwd=os.path.dirname(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
