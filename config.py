"""
Product configuration: it separates the personal build from the one that goes
out to customers.

CertSprint is a personal module (an audit of one specific repository): in
"customer" mode it must not even appear in the interface, or whoever downloads
the app finds a section that has nothing to do with them and that they cannot
use.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os

# Piattaforme social, sempre disponibili a tutti.
CORE_PLATFORMS = ["youtube", "instagram", "tiktok"]

# X does not expose read metrics on the free tier of its APIs: connecting it
# would produce no data at all. Showing it with a "Connect" button destined to
# fail promises a feature we cannot deliver, so it stays out of the
# distributed build. It reappears in personal mode (for development) or by
# forcing SHOW_X=1.
UNAVAILABLE_PLATFORMS = ["x"]

# Personal modules: visible only in the personal build, and only when configured.
PERSONAL_PLATFORMS = ["certsprint"]


def app_mode() -> str:
    """'personal' or 'customer'. A cautious default of customer, so a build
    shipped by mistake without APP_MODE hides the personal modules rather than
    showing them to everyone."""
    mode = (os.environ.get("APP_MODE") or "").strip().lower()
    return mode if mode in ("personal", "customer") else "customer"


def is_personal() -> bool:
    return app_mode() == "personal"


def enabled_platforms() -> list[str]:
    platforms = list(CORE_PLATFORMS)
    if is_personal() or os.environ.get("SHOW_X"):
        platforms += UNAVAILABLE_PLATFORMS
    if is_personal():
        for name in PERSONAL_PLATFORMS:
            if name == "certsprint" and not os.environ.get("CERTSPRINT_PUBLIC_URL"):
                continue  # modulo personale non configurato: si salta
            platforms.append(name)
    return platforms


def public_config() -> dict:
    """Configuration the frontend can read to hide sections and adjust its
    wording, rather than having to guess at either."""
    return {
        "mode": app_mode(),
        "platforms": enabled_platforms(),
        "personal": is_personal(),
    }
