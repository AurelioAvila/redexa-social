"""
OAuth app credentials for the product.

These belong to the application, not the end user: they're compiled into
the executable once, so whoever downloads the dashboard doesn't have to
register anything anywhere. They press "Link", sign in to their account,
done.

For desktop applications the "client secret" isn't a truly confidential
credential - Google and the other platforms explicitly design for this kind
of client, which can't keep secrets. The rule still holds not to reuse
personal bot credentials here.

Every value can be overridden by .env with the same name, useful in
development without having to recompile.

--------------------------------------------------------------------------
HOW TO USE IT: copy this file to brand.py (which stays out of git, see
.gitignore) and fill in the values with your own app's credentials.
brand.py must NEVER be committed: once filled in, it holds real secrets.
--------------------------------------------------------------------------
"""
import os

# --- Google / YouTube -------------------------------------------------
GOOGLE_CLIENT_ID = ""
GOOGLE_CLIENT_SECRET = ""

# --- Instagram (Meta) -------------------------------------------------
# The redirect must be an HTTPS URL registered on the Meta app. The page
# doesn't actually need to exist: login happens inside the app's own
# window, which intercepts the redirect before it loads.
INSTAGRAM_APP_ID = ""
INSTAGRAM_APP_SECRET = ""
INSTAGRAM_REDIRECT_URI = ""

# Endpoint that holds the client secrets instead of the executable: with
# this set, the two *_SECRET values below stay empty and never end up in
# the build. See oauth-proxy/README.md.
OAUTH_PROXY_URL = ""

# --- TikTok -----------------------------------------------------------
TIKTOK_CLIENT_KEY = ""
TIKTOK_CLIENT_SECRET = ""
TIKTOK_REDIRECT_URI = ""


def get(name: str) -> str:
    """Value from .env if present, otherwise the one compiled into the app."""
    return os.environ.get(name) or globals().get(name, "") or ""


def configured(*names: str) -> bool:
    return all(get(n) for n in names)
