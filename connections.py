"""
"Connect account": replaces hand-editing a client id, secret and refresh
token into the .env with an ordinary OAuth sign-in.

The user clicks "Connect YouTube", the browser opens on Google's page, they
authorize, and the token finds its own way back. It uses the "installed app"
flow (redirect to 127.0.0.1 on an ephemeral port), the one Google intends for
desktop applications: no public server to expose, no tokens to copy and paste.

Connections live in cache.db and are read by the platform adapters alongside
any that are already present in the .env, so an existing manual setup keeps
working.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import logging
import os
import secrets
import sqlite3
import threading
import time

import cache
import db

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# State of the connection in progress: the OAuth flow blocks until the user
# finishes signing in inside the browser, so it runs on a thread and the
# frontend follows its progress by polling (same shape as the refresh).
#
# started_at is what keeps this from wedging: if an earlier attempt died badly
# (window closed in a way that raises nothing, thread left hanging), then with
# no expiry the state would sit at "running" forever and every later
# connection would be turned away with "a connection is already in progress".
_connect_state = {"running": False, "platform": None, "error": None, "done": False,
                  "account": None, "started_at": 0}
_connect_lock = threading.RLock()

# Bumped on every new attempt (start_connect) and on every cancellation: the
# thread doing the connecting carries the value it read at startup and checks
# it again before writing its final result. If the user cancelled in the
# meantime (or a new attempt started), the generation number has changed and
# the late write is discarded rather than overwriting a "cancelled" state with
# a "done" that no longer means anything.
_connect_gen = 0

# Past this, a connection still marked "in progress" is treated as abandoned:
# longer than a real sign-in needs, short enough that nobody is left waiting
# on something that is never coming back.
CONNECT_STALE_SECONDS = 330


def _connect_is_active() -> bool:
    """True only when a connection is genuinely alive, not left over."""
    with _connect_lock:
        if not _connect_state["running"]:
            return False
        if time.time() - (_connect_state.get("started_at") or 0) > CONNECT_STALE_SECONDS:
            _connect_state["running"] = False
            _connect_state["error"] = _connect_state["error"] or "connect_timeout"
            return False
        return True


def cancel_connect() -> dict:
    """Cancel the connection in progress, so nobody has to wait out the
    expiry after closing the window or changing their mind. Bumps the
    generation number so the now-orphaned thread can no longer write a late
    result over this reset."""
    global _connect_gen
    with _connect_lock:
        _connect_gen += 1
        _connect_state.update({"running": False, "done": False, "error": None, "account": None})
    return {"ok": True}


def _conn() -> sqlite3.Connection:
    conn = db.connect(cache.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            account_name TEXT NOT NULL,
            account_id TEXT,
            data TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            -- '' finche' l'accesso funziona; il motivo dell'ultimo fallimento
            -- di autenticazione altrimenti (vedi mark_auth_failed).
            auth_state TEXT NOT NULL DEFAULT '',
            auth_checked_at INTEGER NOT NULL DEFAULT 0,
            UNIQUE(platform, account_id)
        )
    """)
    return conn


_CAMPI = ("id, platform, account_name, account_id, data, created_at, "
          "auth_state, auth_checked_at")


def _rows(platform: str | None = None) -> list[tuple]:
    conn = _conn()
    try:
        if platform:
            return conn.execute(
                f"SELECT {_CAMPI} FROM connections WHERE platform = ? ORDER BY created_at",
                (platform,),
            ).fetchall()
        return conn.execute(
            f"SELECT {_CAMPI} FROM connections ORDER BY platform, created_at"
        ).fetchall()
    finally:
        conn.close()


# The reasons an authorization stops being valid. These are the only cases
# where asking the user to reconnect makes sense: a timeout or a 500 from the
# platform says nothing about the token, and flagging the account for those
# would send someone through a sign-in again over a temporary outage that
# clears up on its own.
_AUTH_FAILURE_NEEDLES = (
    "invalid_grant", "expired", "revoked", "invalid_token", "token has been",
    "unauthorized", "401", "invalid_scope", "oauthexception",
)


def is_auth_failure(errore) -> bool:
    """Is this error saying a fresh authorization is needed, or is it just
    passing trouble?

    Takes anything and coerces it to text: the errors come from three
    different libraries and are not always strings (an exception, bytes from
    an HTTP response, a numeric code). Asking the caller to convert means
    someone eventually forgets, and this function decides whether to send a
    user through a sign-in again - not the place to raise a TypeError.
    """
    if errore is None:
        return False
    if isinstance(errore, bytes):
        errore = errore.decode("utf-8", "replace")
    basso = str(errore).lower()
    return any(n in basso for n in _AUTH_FAILURE_NEEDLES)


def mark_auth_failed(connection_id: int, motivo: str) -> None:
    """Record that this account is unusable until someone signs in again.
    Deletes nothing: the token may become valid again (a successful refresh
    clears the state), and removing the connection would take the history
    already gathered for that account with it."""
    conn = _conn()
    try:
        conn.execute(
            "UPDATE connections SET auth_state = ?, auth_checked_at = ? WHERE id = ?",
            (str(motivo or "expired")[:200], int(time.time()), connection_id),
        )
        conn.commit()
    finally:
        conn.close()


def record_fetch_outcome(connection_id, errore=None) -> None:
    """The single place where platform adapters report how it went.

    It lives here rather than inside each adapter because the rule for what
    counts as "needs signing in again" has to be one rule: if every platform
    decided for itself, sooner or later one of them would flag an account
    over a network timeout and the user would be redoing a sign-in that was
    working perfectly well.

    No connection_id = an account configured from the .env rather than the
    database (personal use): there is no row to update.
    """
    if not connection_id:
        return
    try:
        if errore is None:
            mark_auth_ok(connection_id)
        elif is_auth_failure(str(errore)):
            mark_auth_failed(connection_id, str(errore))
    except Exception:
        # Recording the state is a bonus: if it fails (database busy, disk
        # full) the refresh still has to return the data it already
        # gathered, not die over an incidental write.
        logging.warning("authentication state was not updated", exc_info=True)


def mark_auth_ok(connection_id: int) -> None:
    """The refresh worked: the account goes back to normal. Writes only when
    there was genuinely something to clear, so a successful update touches
    the database not at all."""
    conn = _conn()
    try:
        conn.execute(
            "UPDATE connections SET auth_state = '', auth_checked_at = ? "
            "WHERE id = ? AND auth_state != ''",
            (int(time.time()), connection_id),
        )
        conn.commit()
    finally:
        conn.close()


def list_connections(platform: str | None = None) -> list[dict]:
    """The usable accounts, tokens included.

    Rows that cannot be decrypted are skipped: that happens when the database
    came from another computer or another Windows account, which is exactly
    what the encryption is there to prevent. To whoever reads this list (the
    platform adapters) that account simply is not there, as though it were
    disconnected - better than an error halfway through a refresh. The
    interface still shows it, marked, through public_connections.
    """
    import logging

    import secrets_store

    risultato = []
    for r in _rows(platform):
        try:
            dati = json.loads(secrets_store.unprotect(r[4]))
        except secrets_store.SecretUnavailable:
            logging.warning(
                "%s credentials cannot be decrypted by this Windows account; "
                "reconnect the account", r[1]
            )
            continue
        risultato.append(
            {"id": r[0], "platform": r[1], "account_name": r[2], "account_id": r[3],
             "data": dati, "created_at": r[5], "auth_state": r[6]}
        )
    return risultato


def public_connections() -> list[dict]:
    """Like list_connections but without the tokens: this is the version that
    is allowed to reach the frontend.

    It also includes the accounts that cannot be decrypted, marked "locked",
    so the user sees that they exist and need reconnecting instead of
    watching them vanish with no explanation.
    """
    import secrets_store

    pubblici = []
    for r in _rows():
        voce = {"id": r[0], "platform": r[1], "account_name": r[2],
                "account_id": r[3], "created_at": r[5]}
        # The authorization expired or was revoked: the account still reads
        # as connected but is good for nothing until it is redone. Without
        # this the interface showed it as active while diagnostics said the
        # opposite, and the two screens contradicted each other.
        if r[6]:
            voce["needs_reauth"] = True
            voce["auth_checked_at"] = r[7]
        try:
            secrets_store.unprotect(r[4])
        except secrets_store.SecretUnavailable:
            voce["locked"] = True
        pubblici.append(voce)
    return pubblici


def _connection_exists(platform: str, account_id: str) -> bool:
    """Whether this exact account is already stored, which is what tells a
    reconnection apart from a new account."""
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM connections WHERE platform = ? AND account_id = ?",
            (platform, str(account_id)),
        ).fetchone()
    finally:
        conn.close()
    return row is not None


class PlanAccountLimit(Exception):
    """Raised instead of storing an account the plan does not allow."""

    def __init__(self, limit: int):
        super().__init__("plan_account_limit")
        self.limit = limit


def save_connection(platform: str, account_name: str, account_id: str, data: dict) -> None:
    import secrets_store

    # The account limit is enforced here, where every path converges, not at
    # the routes. /api/connections/connect checked it; the guided paste flow
    # that Instagram and TikTok need did not, and it reaches this same
    # function — so a Free account, capped at one, could add as many as it
    # liked by using the flow those two platforms already require.
    #
    # Asking licensing directly rather than taking the plan as an argument:
    # since the licence became the only source, the plan is a fact about the
    # installation, not about the request, and there is no header to plumb
    # through. A caller cannot forget to pass it.
    #
    # Reconnecting an account already stored is never refused: the statement
    # below is an upsert, and someone re-authorising an existing account is
    # not adding one.
    import licensing
    import plans

    limit = plans.max_accounts(licensing.current_plan())
    if limit is not None and not _connection_exists(platform, account_id):
        if len(public_connections()) >= limit:
            raise PlanAccountLimit(limit)

    # Tokens never touch the disk in the clear: they are encrypted here, not
    # in some later tidy-up pass that might never run.
    cifrati = secrets_store.protect(json.dumps(data))

    conn = _conn()
    try:
        conn.execute(
            """INSERT INTO connections (platform, account_name, account_id, data, created_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(platform, account_id) DO UPDATE SET
                 account_name = excluded.account_name,
                 data = excluded.data,
                 created_at = excluded.created_at,
                 -- Reconnecting means new credentials, so any earlier
                 -- "needs reconnecting" no longer holds. Without this the
                 -- warning would have stayed up until the first successful
                 -- refresh — precisely while the user had just done the
                 -- thing it asked for.
                 auth_state = '',
                 auth_checked_at = 0""",
            (platform, account_name, account_id, cifrati, int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()


def delete_connection(connection_id: int) -> None:
    conn = _conn()
    try:
        row = conn.execute("SELECT platform FROM connections WHERE id = ?", (connection_id,)).fetchone()
        conn.execute("DELETE FROM connections WHERE id = ?", (connection_id,))
        conn.commit()
    finally:
        conn.close()

    # If no account is left on this platform, the last-seen numbers belong to
    # nobody: without this they stayed in the cache and the dashboard went on
    # showing them as though they were still true, until someone pressed
    # Refresh by hand.
    if row and not list_connections(row[0]):
        cache.clear_snapshot(row[0])


def _google_client() -> tuple[str, str] | None:
    """Credentials of the OAuth app used for the Google sign-in.

    In a distributed build these are the application's own (for desktop apps
    Google does not treat the secret as a real secret). A client already
    present in the .env is accepted too, so this is usable straight away
    without registering another one."""
    import brand
    if brand.configured("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"):
        return brand.get("GOOGLE_CLIENT_ID"), brand.get("GOOGLE_CLIENT_SECRET")

    client_id = os.environ.get("OAUTH_GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("OAUTH_GOOGLE_CLIENT_SECRET")
    if client_id and client_secret:
        return client_id, client_secret

    # Last resort, development only: reuse whatever *_YOUTUBE_CLIENT_ID and
    # _SECRET pair already sits in the .env.
    #
    # Outside the personal build this fallback MUST NOT exist. It has already
    # done damage: during development it masked the fact that GOOGLE_CLIENT_ID
    # in brand.py was empty (the credentials were coming from a different
    # project in the .env), so YouTube looked connectable while in the
    # distributed build it was not. And on someone else's computer it would
    # use that person's credentials without telling them.
    import config
    if config.is_personal():
        for key, value in os.environ.items():
            if key.endswith("_YOUTUBE_CLIENT_ID") and value:
                secret = os.environ.get(key.replace("_CLIENT_ID", "_CLIENT_SECRET"))
                if secret:
                    return value, secret
    return None


def connect_status() -> dict:
    return dict(_connect_state)


def _connect_youtube() -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds_pair = _google_client()
    if not creds_pair:
        raise RuntimeError("connect_no_google_app")
    client_id, client_secret = creds_pair

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=YOUTUBE_SCOPES,
    )
    # port=0 => free port picked by the system; Google accepts any port on
    # 127.0.0.1 for clients of the "Desktop app" type.
    # select_account is what makes connecting more than one channel possible:
    # without it Google silently reuses the account already signed in inside
    # the browser, and you end up reconnecting the same one every time.
    creds = flow.run_local_server(port=0, prompt="consent select_account", open_browser=True)

    service = build("youtube", "v3", credentials=creds)
    resp = service.channels().list(part="snippet", mine=True).execute()
    item = resp["items"][0]
    channel_id = item["id"]
    channel_name = item["snippet"]["title"]

    save_connection("youtube", channel_name, channel_id, {
        "refresh_token": creds.refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": YOUTUBE_SCOPES,
    })
    _connect_state["account"] = channel_name


CONNECTORS = {"youtube": _connect_youtube}


# ---------------------------------------------------------------------------
# Instagram and TikTok: guided connection
#
# Neither accepts a redirect to 127.0.0.1 (they insist on an HTTPS URL), so
# the automatic YouTube-style sign-in is not possible without a public
# endpoint. The guided flow still reduces the whole thing to: open the link,
# authorize, paste the URL you landed on. One paste instead of three variables
# typed by hand into the .env for every account.
# ---------------------------------------------------------------------------

def _oauth_window_available() -> bool:
    """True when the app's native window is available and the sign-in can be
    opened inside it. In the executable it always is; running the server on
    its own (development) it is not, and we fall back to the paste flow."""
    try:
        import webview
        return bool(webview.windows)
    except Exception:
        return False


def _connect_in_window(auth_url: str, redirect_uri: str, title: str, timeout: int = 300) -> str:
    """Open the sign-in inside an app window and intercept the redirect.

    This is what turns connecting into a single click: Instagram and TikTok
    insist on an HTTPS redirect (no 127.0.0.1), but that page does not
    actually have to exist - it is enough to notice the window navigating to
    it and read the code out of the URL before it even loads. No token to
    paste, nothing for the user to configure.
    """
    import webview

    window = webview.create_window(title, auth_url, width=520, height=720)
    result = {}

    # Closing the window does not always make get_current_url() fail: on some
    # backends it keeps returning the last URL, and the loop stayed up until
    # the timeout, holding the state at "connection in progress". The closed
    # event is the signal that can be trusted.
    closed = threading.Event()
    try:
        window.events.closed += closed.set
    except Exception:
        pass

    from urllib.parse import urlparse

    auth_host = urlparse(auth_url).netloc

    deadline = time.time() + timeout
    while time.time() < deadline:
        if closed.is_set():
            break
        time.sleep(0.35)
        try:
            current = window.get_current_url()
        except Exception:
            break  # finestra chiusa dall'utente
        if not current:
            continue
        # An exact prefix match is not enough: if the landing page is a web
        # application, its router rewrites the URL (with no HTTP redirect)
        # before the polling notices, and the code was lost while we hung on
        # until the timeout. The moment we are off the sign-in domain and
        # there is a `code`, it is ours.
        if current.startswith(redirect_uri):
            result["url"] = current
            break
        if "code=" in current and urlparse(current).netloc != auth_host:
            result["url"] = current
            break

    if not closed.is_set():
        try:
            window.destroy()
        except Exception:
            pass

    if "url" not in result:
        raise RuntimeError("connect_window_closed")
    if "error" in result["url"] and "code=" not in result["url"]:
        raise RuntimeError("connect_denied")
    # Returns the whole URL, not just the code: the caller has to be able to
    # check the state as well before trusting the code.
    return result["url"]


def _state_from(raw: str) -> str:
    """The state parameter of the return URL, if it carries one."""
    raw = (raw or "").strip()
    if "state=" not in raw:
        return ""
    value = raw.split("state=", 1)[1].split("&", 1)[0].split("#", 1)[0]
    try:
        from urllib.parse import unquote
        value = unquote(value)
    except Exception:
        pass
    return value


def _clean_code(raw: str) -> str:
    """Accepts either the bare code or the whole return URL, from which it
    pulls the code parameter. Instagram appends '#_' to the code: it has to
    come off or the token exchange fails."""
    raw = (raw or "").strip()
    if not raw:
        raise RuntimeError("guided_paste_needed")
    if "code=" in raw:
        raw = raw.split("code=", 1)[1].split("&", 1)[0]
    raw = raw.split("#", 1)[0]
    try:
        from urllib.parse import unquote
        raw = unquote(raw)
    except Exception:
        pass
    if not raw:
        raise RuntimeError("connect_code_not_found")
    return raw


# These two values go straight into the interface. They are codes rather than
# sentences because the text has to be written in the language the user chose:
# a phrase decided here would keep that wording even with the app set to
# another language (which is exactly what happened with "X does not expose the
# statistics...").
NOT_SET = "unavail_not_configured"


def _env_pair(id_suffix: str, secret_suffix: str) -> tuple[str, str] | None:
    """Find an id/secret pair already in the .env under any prefix (for
    example SOLOFOUNDED_TIKTOK_CLIENT_KEY). Saves asking again for
    credentials the user has already configured elsewhere."""
    for key, value in os.environ.items():
        if key.endswith(id_suffix) and value:
            secret = os.environ.get(key[: -len(id_suffix)] + secret_suffix)
            if secret:
                return value, secret
    return None


# ---------------------------------------------------------------------------
# Token exchange through the proxy
#
# Instagram and TikTok require the client secret to turn a `code` into a
# token. Compiling it into the executable means handing it to everyone who
# downloads the app: unpacking the binary is enough to read it back in the
# clear (verified). Meta says so explicitly - the app secret must never go
# into distributed code.
#
# With OAUTH_PROXY_URL set, the exchange happens on an endpoint of ours that
# keeps the secrets, and none of them end up in the build. Without it we fall
# back to the historical behaviour: useful in development, not advisable for
# anything shipped.
# ---------------------------------------------------------------------------

def proxy_url() -> str:
    import brand
    return (brand.get("OAUTH_PROXY_URL") or "").rstrip("/")


def using_proxy(platform: str | None = None) -> bool:
    """The proxy keeps *our* secrets. If the customer registered an app of
    their own, the secret is theirs and lives only on this computer: the
    token exchange has to happen locally, or the proxy would try to sign it
    with credentials that have nothing to do with it."""
    if platform:
        import own_app
        if own_app.configured(platform):
            return False
    return bool(proxy_url())


def proxy_call(action: str, payload: dict) -> dict:
    import requests

    base = proxy_url()
    if not base:
        raise RuntimeError("proxy_not_configured")
    resp = requests.post(f"{base}/{action}", json=payload, timeout=30)
    if not resp.ok:
        # The raw text stays in the logs for debugging; the user gets only a
        # code, so the message follows the language chosen in the app.
        print(f"[oauth-proxy] {resp.status_code}: {resp.text[:200]}")
        raise RuntimeError("connect_proxy_http_error")
    data = resp.json()
    if data.get("error"):
        print(f"[oauth-proxy] rejected: {str(data['error'])[:200]}")
        raise RuntimeError("connect_proxy_rejected")
    return data


def _instagram_app() -> tuple[str, str, str]:
    """(app_id, secret, redirect). With the proxy active the secret is not in
    the build and stays empty: only the endpoint doing the exchange needs
    it."""
    import brand
    import own_app
    redirect = brand.get("INSTAGRAM_REDIRECT_URI")

    # The customer's own registered app wins: it is what lets them connect
    # their account without waiting on our platform review, so if it is there
    # at all it is because they want it used.
    mine = own_app.get("instagram")
    if mine:
        return mine["client_id"], mine["client_secret"], redirect

    app_id = brand.get("INSTAGRAM_APP_ID")
    secret = brand.get("INSTAGRAM_APP_SECRET")
    if not (app_id and secret):
        found = _env_pair("_IG_APP_ID", "_IG_APP_SECRET")
        if found:
            app_id, secret = found
    required = (app_id, redirect) if using_proxy() else (app_id, secret, redirect)
    if not all(required):
        raise RuntimeError(NOT_SET)
    return app_id, secret, redirect


def _tiktok_app() -> tuple[str, str, str]:
    """(client_key, secret, redirect). See _instagram_app about the secret."""
    import brand
    import own_app
    redirect = brand.get("TIKTOK_REDIRECT_URI")

    mine = own_app.get("tiktok")  # vedi _instagram_app
    if mine:
        return mine["client_id"], mine["client_secret"], redirect

    key = brand.get("TIKTOK_CLIENT_KEY")
    secret = brand.get("TIKTOK_CLIENT_SECRET")
    if not (key and secret):
        found = _env_pair("_TIKTOK_CLIENT_KEY", "_TIKTOK_CLIENT_SECRET")
        if found:
            key, secret = found
    required = (key, redirect) if using_proxy() else (key, secret, redirect)
    if not all(required):
        raise RuntimeError(NOT_SET)
    return key, secret, redirect


APP_CHECKS = {"instagram": _instagram_app, "tiktok": _tiktok_app, "youtube": lambda: _google_client() or (_ for _ in ()).throw(RuntimeError(NOT_SET))}


def credentials_ready(platform: str) -> bool:
    """Are this platform's app credentials available? Used to avoid showing a
    button that would lead into a dead end."""
    check = APP_CHECKS.get(platform)
    if not check:
        return False
    try:
        check()
        return True
    except Exception:
        return False


# OAuth `state` does exactly one job: recognizing that the code coming back
# belongs to the request we made. It was being generated and then thrown away,
# which made it decorative - in the manual-paste flow, convincing someone to
# paste the return URL of a *different* account was enough to attach that
# account to their dashboard.
#
# Only the most recent one per platform is kept: connections happen one at a
# time (_connect_is_active already enforces that), so nothing is left to clean
# up.
_pending_state: dict[str, str] = {}


def _remember_state(platform: str) -> str:
    value = secrets.token_urlsafe(24)
    _pending_state[platform] = value
    return value


def _check_state(platform: str, returned: str) -> None:
    """Consume the expected state. A return with no state is not accepted when
    we asked for one: that would be the same as never having sent it."""
    expected = _pending_state.pop(platform, None)
    if not expected:
        raise RuntimeError("connect_state_missing")
    if not returned or not secrets.compare_digest(expected, returned):
        raise RuntimeError("connect_state_mismatch")


def authorize_url(platform: str) -> dict:
    """The URL to open in the browser to authorize the account."""
    from urllib.parse import urlencode

    if coming_soon(platform):
        return {"ok": False, "message": "connect_coming_soon"}

    try:
        # force_reauth / disable_auto_auth: the app window keeps the
        # platform's cookies, so without these parameters the second
        # connection skips sign-in and consent and silently reconnects the
        # same account. They are what makes "connect another account"
        # actually do that.
        if platform == "instagram":
            app_id, _, redirect = _instagram_app()
            params = {
                "client_id": app_id,
                "redirect_uri": redirect,
                "response_type": "code",
                "scope": "instagram_business_basic,instagram_business_manage_insights",
                "force_reauth": "true",
                "state": _remember_state("instagram"),
            }
            return {"ok": True, "url": "https://www.instagram.com/oauth/authorize?" + urlencode(params)}

        if platform == "tiktok":
            key, _, redirect = _tiktok_app()
            params = {
                "client_key": key,
                "scope": "user.info.basic,user.info.stats,video.list",
                "response_type": "code",
                "redirect_uri": redirect,
                "state": _remember_state("tiktok"),
                "disable_auto_auth": "1",
            }
            return {"ok": True, "url": "https://www.tiktok.com/v2/auth/authorize/?" + urlencode(params)}
    except RuntimeError:
        return {"ok": False, "message": "connect_configuration_error"}

    return {"ok": False, "message": "connect_guided_unavailable"}


def _finish_instagram(code: str) -> str:
    import requests

    app_id, app_secret, redirect = _instagram_app()

    if using_proxy("instagram"):
        # The secret is not in this build: code -> long-lived token happens
        # on the endpoint that keeps it.
        long_token = proxy_call("exchange", {
            "platform": "instagram", "code": code, "redirect_uri": redirect,
        })["access_token"]
    else:
        token_resp = requests.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": app_id,
                "client_secret": app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect,
                "code": code,
            },
            timeout=30,
        )
        if not token_resp.ok:
            print(f"[instagram] token rejected: {token_resp.text[:200]}")
            raise RuntimeError("connect_instagram_rejected")
        short = token_resp.json()

        # The short token lasts an hour: swap it for the 60-day one straight
        # away, or the connection stops working almost immediately.
        long_resp = requests.get(
            "https://graph.instagram.com/access_token",
            params={"grant_type": "ig_exchange_token", "client_secret": app_secret,
                    "access_token": short["access_token"]},
            timeout=30,
        )
        if not long_resp.ok:
            print(f"[instagram] long-token exchange failed: {long_resp.text[:200]}")
            raise RuntimeError("connect_token_exchange_failed")
        long_token = long_resp.json()["access_token"]

    me = requests.get(
        "https://graph.instagram.com/v21.0/me",
        params={"fields": "id,username"},
        headers={"Authorization": f"Bearer {long_token}"},
        timeout=30,
    )
    me.raise_for_status()
    info = me.json()
    username = info.get("username") or "Instagram"

    save_connection("instagram", username, str(info["id"]), {
        "access_token": long_token, "user_id": str(info["id"]), "api_kind": "instagram",
    })
    return username


def _finish_tiktok(code: str) -> str:
    import requests

    key, secret, redirect = _tiktok_app()

    if using_proxy("tiktok"):
        data = proxy_call("exchange", {
            "platform": "tiktok", "code": code, "redirect_uri": redirect,
        })
    else:
        resp = requests.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_key": key, "client_secret": secret,
                "code": code, "grant_type": "authorization_code", "redirect_uri": redirect,
            },
            timeout=30,
        )
        if not resp.ok:
            print(f"[tiktok] token rejected: {resp.text[:200]}")
            raise RuntimeError("connect_tiktok_rejected")
        data = resp.json()
    if "access_token" not in data:
        print(f"[tiktok] unexpected response: {str(data)[:200]}")
        raise RuntimeError("connect_tiktok_unexpected")

    # If 'video.list' is missing the sign-in still succeeded: throwing the
    # connection away would leave the user with no connected account and no
    # idea why. Save it anyway and record the granted scope - diagnostics is
    # what explains that the permission has not been approved, in a translated
    # message rather than a blunt error at sign-in time.
    granted = data.get("scope", "")

    username = "TikTok"
    try:
        info = requests.get(
            "https://open.tiktokapis.com/v2/user/info/",
            headers={"Authorization": f"Bearer {data['access_token']}"},
            params={"fields": "display_name"},
            timeout=30,
        )
        if info.ok:
            username = info.json().get("data", {}).get("user", {}).get("display_name") or username
    except Exception:
        pass

    # With the proxy the secret is not stored locally either: refreshing the
    # token will go through the endpoint that keeps it as well.
    stored = {"refresh_token": data["refresh_token"], "client_key": key, "granted_scope": granted}
    if using_proxy("tiktok"):
        stored["via_proxy"] = True
    else:
        stored["client_secret"] = secret
    save_connection("tiktok", username, str(data.get("open_id", username)), stored)
    return username


GUIDED = {"instagram": _finish_instagram, "tiktok": _finish_tiktok}

REDIRECT_GETTERS = {
    "instagram": lambda: _instagram_app()[2],
    "tiktok": lambda: _tiktok_app()[2],
}

WINDOW_TITLES = {"instagram": "Connect Instagram", "tiktok": "Connect TikTok"}


def _connect_oneclick(platform: str) -> None:
    """One-click sign-in inside the app window, for the platforms that will
    not accept a redirect to 127.0.0.1."""
    info = authorize_url(platform)
    if not info.get("ok"):
        raise RuntimeError(info.get("message", "connect_guided_unavailable"))

    returned = _connect_in_window(
        info["url"], REDIRECT_GETTERS[platform](), WINDOW_TITLES.get(platform, "Connect account")
    )
    _check_state(platform, _state_from(returned))
    _connect_state["account"] = GUIDED[platform](_clean_code(returned))


def finish_guided(platform: str, pasted: str) -> dict:
    if coming_soon(platform):
        return {"ok": False, "message": "connect_coming_soon"}
    finisher = GUIDED.get(platform)
    if not finisher:
        return {"ok": False, "message": "connect_guided_unavailable"}
    try:
        # What arrives here was pasted by hand: this is the point where
        # someone could be talked into pasting another account's return URL.
        # The state has to be checked before the code is exchanged, and that
        # is why the whole address is needed rather than just the code.
        _check_state(platform, _state_from(pasted))
        account = finisher(_clean_code(pasted))
        return {"ok": True, "account": account}
    except PlanAccountLimit as limit:
        # Not a failure to connect: the authorisation worked and the plan is
        # what refused it. Reported as itself so the interface can say so and
        # offer the upgrade, instead of showing "could not connect" for an
        # account that connected perfectly well.
        return {"ok": False, "message": "plan_account_limit", "limit": limit.limit}
    except Exception:
        # Everything else collapses into one message, which is its own small
        # problem: a state mismatch, a rejected code and a dropped connection
        # are indistinguishable here and to the logs. Logged now, at least,
        # so the reason survives even though the message does not.
        logging.exception("guided connect failed for %s", platform)
        return {"ok": False, "message": "connect_failed"}


def connect_mode(platform: str) -> str:
    """How this platform connects, so the frontend shows a single button when
    one click is enough and the manual steps only when they cannot be
    avoided.

    If the app credentials are missing it reports "unavailable" up front:
    better to say so than to let someone press a button that is going to
    fail."""
    if coming_soon(platform):
        return "coming_soon"
    if platform in UNAVAILABLE:
        return "unavailable"
    if not credentials_ready(platform):
        return "unavailable"
    if platform in CONNECTORS:
        return "oneclick"
    if platform in GUIDED:
        return "oneclick" if _oauth_window_available() else "guided"
    return "unsupported"


def unavailable_reason(platform: str) -> str | None:
    """A readable reason why a platform cannot be connected."""
    if platform in UNAVAILABLE:
        return UNAVAILABLE[platform]
    if platform in (set(CONNECTORS) | set(GUIDED)) and not credentials_ready(platform):
        return NOT_SET
    return None


# Platforms with no possible connection at all. Same rule here: a code, not a
# sentence (see the comment on NOT_SET).
UNAVAILABLE = {
    "x": "unavail_x_no_read_api",
}

# Instagram and TikTok have their credentials ready but are not yet
# connectable for an ordinary customer: Instagram needs Meta's business
# verification (blocked, the paperwork is missing) and TikTok has been in
# review since 2026-08-04. Rather than letting someone attempt a sign-in that
# jams silently on Instagram (account is not a tester) or connects with no
# data on TikTok (video.list not granted), we say "coming soon" up front.
# Take a platform out of here as soon as its review is approved.
COMING_SOON = {"instagram", "tiktok"}


def coming_soon(platform: str) -> bool:
    """"Coming soon" is about *our* app waiting on approval. Anyone who
    registered their own is waiting on nobody: for them the connection is
    available now, which is precisely why they registered it."""
    if platform not in COMING_SOON:
        return False
    import own_app
    return not own_app.configured(platform)


def start_connect(platform: str) -> dict:
    if coming_soon(platform):
        return {"ok": False, "message": "connect_coming_soon"}
    if platform in UNAVAILABLE:
        return {"ok": False, "message": UNAVAILABLE[platform]}

    if platform in CONNECTORS:
        runner = CONNECTORS[platform]
    elif platform in GUIDED and _oauth_window_available():
        runner = lambda: _connect_oneclick(platform)
    else:
        return {"ok": False, "message": "connect_platform_unsupported"}

    global _connect_gen
    with _connect_lock:
        if _connect_is_active():
            return {"ok": False, "message": "connect_already_running"}
        _connect_gen += 1
        my_gen = _connect_gen
        _connect_state.update({"running": True, "platform": platform, "error": None,
                               "done": False, "account": None, "started_at": time.time()})

    def worker():
        try:
            runner()
            result = ("done", None)
        except Exception as exc:
            result = ("error", str(exc))
        with _connect_lock:
            # If the user cancelled in the meantime (or a new attempt
            # started), the generation number no longer matches: this thread
            # is orphaned now and must not overwrite the state.
            if _connect_gen != my_gen:
                return
            if result[0] == "done":
                _connect_state["done"] = True
            else:
                _connect_state["error"] = result[1]
            _connect_state["running"] = False

    threading.Thread(target=worker, daemon=True).start()
    return {"ok": True}
