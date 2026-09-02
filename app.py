"""
The application's local server: it exposes the APIs the interface consumes and
holds together data collection, analysis, diagnostics, licensing and updates.

It listens on 127.0.0.1 only and is not a web service: it is born and dies
with the app window. The defences against CSRF and DNS rebinding are needed
anyway, and are explained a little further down, where they are implemented.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os
import sys
import threading
import time
import webbrowser
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# In a compiled .exe (PyInstaller) the bundled files land in a temporary
# folder (_MEIPASS) that disappears on every restart - the .env and the
# database have to stay beside the real executable instead, or the
# configuration and the history are lost every time the app opens.
APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_DIR, ".env"))

from fastapi import Body, FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

import analytics
import cache
import config
import diagnostics
import trends

@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Prepare persistent state before serving requests.

    Database migration remains synchronous by design: routes must not access a
    partially migrated schema. A failed migration is rolled back and logged,
    while license refresh remains best-effort and runs in the background so it
    cannot delay the desktop window.
    """
    import logging

    import licensing
    import db

    try:
        result = db.ensure_current(cache.DB_PATH)
        if result["applied"]:
            logging.info(
                "database migrated: %s -> %s (%s)",
                result["from"],
                result["to"],
                ", ".join(result["applied"]),
            )
    except Exception:
        logging.exception(
            "database migration failed; continuing with the previous schema"
        )

    threading.Thread(target=licensing.refresh_if_due, daemon=True).start()
    yield


app = FastAPI(title="Social Stats Dashboard", lifespan=_lifespan)


# ------------------------------------------------- local server defences
#
# The server listens on 127.0.0.1, but "local only" does not mean "our window
# only": any web page open in the browser while the app is running can talk to
# this port. Two real attacks, both verified before this defence was written:
#
#   1. CSRF. A POST with no JSON body is a "simple request": the browser sends
#      it cross-origin without asking the server for permission. A malicious
#      page open in another tab was enough to wipe the history
#      (/api/cache/clear) or remove the activated licence
#      (/api/license/remove). The attacker never reads the response, but the
#      damage is already done.
#
#   2. DNS rebinding. The Host header was not checked: a domain that points at
#      127.0.0.1 after a few seconds becomes "same origin" to the browser, and
#      from there the responses can be read - which is to say the customer's
#      private statistics.
#
# The Origin check fires only on the methods that change something, and only
# when the header is present: a browser always sends it on a cross-origin
# POST, while a legitimate local request (the app window, a script of the
# user's own) either omits it or sends ours.
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _host_only(value: str) -> str:
    """The host name without the port. IPv6 addresses arrive in square
    brackets ("[::1]:8787"), so cutting at the last colon is not enough."""
    raw = (value or "").strip()
    if raw.startswith("["):
        end = raw.find("]")
        return raw[1:end] if end != -1 else ""
    return raw.rsplit(":", 1)[0] if ":" in raw else raw


@app.middleware("http")
async def _local_only_guard(request, call_next):
    from fastapi.responses import JSONResponse

    if _host_only(request.headers.get("host", "")) not in LOCAL_HOSTS:
        return JSONResponse({"error": "bad_host"}, status_code=400)

    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlparse
            if (urlparse(origin).hostname or "") not in LOCAL_HOSTS:
                return JSONResponse({"error": "bad_origin"}, status_code=403)

    return await call_next(request)

# Which platforms are active depends on the mode (personal or customer): the
# personal modules such as CertSprint do not exist in the distributed build.
PLATFORM_NAMES = config.enabled_platforms()
_module_cache = {}


def _get_module(name: str):
    """Lazy import: the individual platform libraries (google-api-python-client
    for YouTube in particular) are heavy to load - doing it only when it is
    genuinely needed (at the first refresh) rather than at app startup cuts a
    good deal off the time before the window appears.

    Note: static imports inside functions, not importlib with a dynamic
    string - PyInstaller walks the AST and finds these to bundle them, while
    an importlib.import_module(f"...") stays invisible to it and the module
    ends up missing from the compiled executable."""
    if name in _module_cache:
        return _module_cache[name]

    if name == "youtube":
        from platforms import youtube as mod
    elif name == "instagram":
        from platforms import instagram as mod
    elif name == "tiktok":
        from platforms import tiktok as mod
    elif name == "x":
        from platforms import x as mod
    elif name == "certsprint":
        from platforms import certsprint as mod
    else:
        raise ValueError(f"Piattaforma sconosciuta: {name}")

    _module_cache[name] = mod
    return mod


_refresh_state = {"running": False, "done": [], "done_units": 0, "total_units": len(PLATFORM_NAMES)}
_refresh_lock = threading.Lock()
_units_lock = threading.Lock()


@app.get("/api/snapshot")
def get_snapshot(authorization: str | None = Header(default=None)):
    """The most recent data already stored - no external calls, so opening the
    app loads instantly and costs nothing.

    History and suggested posting windows are Pro features: they are stripped
    from the response, not merely hidden by the interface."""
    import insights
    import plans

    plan = _current_plan(authorization)
    out = {}
    for platform in PLATFORM_NAMES:
        out[platform] = cache.latest_snapshot(platform)
    # The observations are arithmetic over data already in memory: they cost
    # nothing, so they arrive with the snapshot rather than behind a button
    # the user has to know to press.
    out["insights"] = {p: insights.generate_insights(out, platform=p) for p in PLATFORM_NAMES}
    # The analysis has to be computed first: diagnostics uses it for the
    # strategy checks (engagement against industry figures, resonance,
    # imbalance across platforms) rather than only saying whether the APIs
    # answer.
    out["analytics"] = analytics.compute_analytics(out)
    out["diagnostics"] = diagnostics.run_diagnostics(out, out["analytics"])
    out["trends"] = trends.compute_trends() if plans.allows(plan, "history") else {}
    # Computed from data already read, no calls: it arrives with the
    # snapshot the way the observations do, rather than behind a button.
    if plans.allows(plan, "rivals"):
        import rivals
        out["rivals"] = rivals.compare(out)
    else:
        out["rivals"] = None
    if not plans.allows(plan, "best_hours"):
        out["analytics"]["best_hours"] = []
        out["analytics"]["hours_locked"] = True

    fetch_times = [out[p]["fetched_at"] for p in PLATFORM_NAMES if out.get(p) and out[p].get("fetched_at")]
    out["analytics"]["last_refresh_at"] = max(fetch_times) if fetch_times else None
    out["entitlements"] = plans.public_entitlements(plan)
    return out


def _on_unit_done():
    # `+= 1` on a shared value is a read-modify-write, not an atomic
    # operation: with several refresh threads running in parallel two
    # increments can overlap and one is lost, leaving the bar stuck below
    # 100%. The explicit lock is needed.
    with _units_lock:
        _refresh_state["done_units"] += 1


def _refresh_one(name: str):
    module = _get_module(name)
    try:
        data = module.fetch_stats(on_item=_on_unit_done)
    except Exception as exc:
        data = {"platform": name, "ok": False, "error": str(exc)}
        _on_unit_done()
    cache.save_snapshot(name, data)
    _refresh_state["done"].append(name)


def _refresh_worker():
    """Every platform in parallel, not one at a time - the total stays the
    time of the slowest rather than the sum of all of them. Progress is
    tracked per unit of work (one YouTube channel, one Instagram account, one
    CertSprint check, and so on) instead of per whole platform, so the bar
    advances continuously rather than sitting still across 5 large blocks."""
    threads = [threading.Thread(target=_refresh_one, args=(name,)) for name in PLATFORM_NAMES]
    for t in threads:
        t.start()
        # A small stagger between starting one platform and the next -
        # keeps every OAuth/HTTP request from leaving at the same instant,
        # which reduces the intermittent server-side errors seen in practice
        # (a spurious invalid_scope, for one) when several token endpoints
        # are hit in a perfectly simultaneous burst.
        time.sleep(0.4)
    for t in threads:
        t.join()
    _refresh_state["running"] = False


@app.post("/api/refresh")
def refresh_all():
    """Starts the refresh in the background and returns immediately - the real
    progress is read from /api/refresh/status, so the loading bar reflects
    actual work rather than an invented estimate."""
    with _refresh_lock:
        if _refresh_state["running"]:
            return dict(_refresh_state)
        total_units = 0
        for name in PLATFORM_NAMES:
            try:
                total_units += _get_module(name).count_units()
            except Exception:
                total_units += 1
        _refresh_state["running"] = True
        _refresh_state["done"] = []
        _refresh_state["done_units"] = 0
        _refresh_state["total_units"] = max(total_units, 1)
        threading.Thread(target=_refresh_worker, daemon=True).start()
    return dict(_refresh_state)


@app.get("/api/refresh/status")
def refresh_status():
    return {**_refresh_state, "done_count": len(_refresh_state["done"])}


@app.post("/api/insights/{platform}")
def get_platform_insights(platform: str):
    """Platform analysis computed in code: instant and free, so it needs
    neither a cache nor a button to ask for it - it is already included in
    /api/snapshot. The endpoint stays for compatibility."""
    if platform not in PLATFORM_NAMES:
        raise HTTPException(404, f"Unknown platform: {platform}")

    import insights
    snap = cache.latest_snapshot(platform)
    return {"generated_at": int(time.time()), "items": insights.generate_insights({platform: snap}, platform=platform)}


# ---------------------------------------------------------------- config

@app.get("/api/config")
def get_config():
    """The frontend uses this to know which sections to show, rather than
    keeping the list of platforms written by hand in two places."""
    return config.public_config()


@app.get("/api/version")
def get_version():
    """Downloads and installs nothing: it only says whether GitHub has a
    release newer than this one, so the frontend can show a notice with a link
    to the download page."""
    import version
    return version.status()


@app.get("/api/update/check")
def update_check(force: bool = False):
    """Is there an update? Nothing is downloaded and nothing is installed.

    If this copy is managed by winget, it says so: two mechanisms replacing
    the same files would leave the installation in a state neither of them
    knows how to repair.
    """
    from updater import runner

    return runner.check(force=force)


@app.post("/api/update/install")
def update_install():
    """Downloads, verifies signature and digest, saves the database and starts
    the process that replaces the files.

    Returns immediately: from here on the external updater is in charge, and
    it is what closes the application.
    """
    from updater import runner

    from updater import manifest as manifest_module

    try:
        preparato = runner.prepare()
        return runner.apply(preparato)
    # The manifest can refuse an update (not a newer version, signature,
    # channel) and ManifestError is not an UpdateError: without this branch it
    # came out as a 500, and the interface said "installation failed" where
    # the reason was simply that there was nothing to install.
    except (runner.UpdateError, manifest_module.ManifestError) as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/update/postpone")
def update_postpone(payload: dict = Body(default={})):
    """"Remind me later", or "skip this version".

    Skipping applies only to non-critical updates: a mandatory one comes back
    regardless.
    """
    from updater import runner

    if payload.get("skip_version"):
        runner.skip_version(str(payload["skip_version"]))
    else:
        runner.snooze(int(payload.get("hours", 24)))
    return {"ok": True}


@app.get("/api/update/channel")
def update_channel_get():
    from updater import runner

    return {"channel": runner.channel()}


@app.post("/api/update/channel")
def update_channel_set(payload: dict = Body(...)):
    """Opting in to the test channel: anyone who does not choose it never sees
    a beta version."""
    from updater import runner

    try:
        runner.set_channel(str(payload.get("channel", "")))
    except runner.UpdateError as exc:
        raise HTTPException(400, str(exc))
    return {"ok": True, "channel": runner.channel()}


@app.post("/api/cache/clear")
def clear_cache():
    """Empties everything a refresh recomputes on its own (statistics,
    observations, the diagnostics cache). It does not touch connections, the
    licence, or the apps the customer registered: those are configuration
    rather than cache, and a "clear" button must not be able to lose them by
    accident."""
    cache.clear_all()
    return {"ok": True}


# ------------------------------------------------------------ connessioni

@app.get("/api/connections")
def get_connections():
    import connections
    import own_app
    platforms = list(connections.CONNECTORS) + list(connections.GUIDED) + list(connections.UNAVAILABLE)
    platforms = list(dict.fromkeys(platforms))
    reasons = {p: connections.unavailable_reason(p) for p in platforms}
    return {
        "connections": connections.public_connections(),
        # The reason each unconnectable platform is unconnectable: no
        # credentials in the build, or a limit of the platform itself.
        "unavailable": {p: r for p, r in reasons.items() if r},
        "connectable": list(connections.CONNECTORS.keys()),
        "guided": list(connections.GUIDED.keys()),
        # How each one connects: "oneclick" (the button is enough),
        # "guided" (a paste is needed), "unavailable".
        "modes": {p: connections.connect_mode(p) for p in platforms},
        # Platforms where the customer can register an app of their own and
        # connect without waiting on our review, with the state of the ones
        # already configured.
        "own_app": {p: own_app.status(p) for p in own_app.SUPPORTED},
    }


@app.post("/api/connections/connect/{platform}")
def connect_platform(platform: str, authorization: str | None = Header(default=None)):
    """Starts the OAuth sign-in: opens the browser on the platform's page and
    waits for the return to 127.0.0.1. Returns immediately; progress is read
    from /api/connections/status.

    How many accounts can be connected depends on the plan, and the check
    lives here: hiding it in the interface alone would not be a limit."""
    import connections
    import plans

    plan = _current_plan(authorization)
    limit = plans.max_accounts(plan)
    if limit is not None and len(connections.public_connections()) >= limit:
        return {"ok": False, "code": "plan_account_limit", "limit": limit, "plan": plan,
                "message": "plan_account_limit"}
    return connections.start_connect(platform)


@app.get("/api/connections/status")
def connect_status():
    import connections
    return connections.connect_status()


@app.get("/api/rivals")
def rivals_list(authorization: str | None = Header(default=None)):
    """Who is being followed, with the last successful read.

    Not behind the plan: knowing who you added and when it was last read has
    to stay visible even after a subscription lapses, or the data you entered
    looks as though it disappeared.

    The numbers are, though. `stats` holds the subscriber, view and video
    counts — the comparison itself, which is the thing the plan sells. This
    route handed the whole blob over on any plan while /api/snapshot was
    carefully setting `rivals: None` for Free, so the paid answer was
    available at a different URL. Only the payload is withheld: the handles,
    the titles and the last-read dates still come back, which is what this
    endpoint exists for."""
    import plans
    import rivals

    seguiti = rivals.list_rivals()
    if not plans.allows(_current_plan(authorization), "rivals"):
        seguiti = [{**r, "stats": {}} for r in seguiti]
    return {"rivals": seguiti, "max": rivals.MAX_RIVALS}


@app.post("/api/rivals")
def rivals_add(payload: dict = Body(...), authorization: str | None = Header(default=None)):
    import plans
    import rivals
    if not plans.allows(_current_plan(authorization), "rivals"):
        raise HTTPException(402, "plan_required")
    try:
        return rivals.add_rival(payload.get("handle", ""))
    except rivals.RivalError as errore:
        raise HTTPException(400, str(errore))


@app.delete("/api/rivals/{rival_id}")
def rivals_delete(rival_id: int):
    """Removing does not require the plan: someone who stopped paying must
    still be able to delete what they entered."""
    import rivals
    rivals.remove_rival(rival_id)
    return {"ok": True}


@app.post("/api/rivals/refresh")
def rivals_refresh(authorization: str | None = Header(default=None)):
    """Re-reads the public statistics of the followed channels.

    Deliberately separate from the general refresh: it spends YouTube API
    quota and the main screen does not need it, so it runs when the user looks
    at the comparison rather than every time the app opens."""
    import plans
    import rivals
    if not plans.allows(_current_plan(authorization), "rivals"):
        raise HTTPException(402, "plan_required")
    try:
        return rivals.refresh()
    except rivals.RivalError as errore:
        raise HTTPException(400, str(errore))


@app.post("/api/connections/cancel")
def connect_cancel():
    """Frees a connection left hanging (window closed, sign-in never finished)
    without waiting out the expiry or restarting the app."""
    import connections
    return connections.cancel_connect()


@app.get("/api/connections/authorize/{platform}")
def connection_authorize_url(platform: str):
    """The URL to open to authorize Instagram or TikTok: neither accepts a
    redirect to 127.0.0.1, so the return has to be pasted by hand once."""
    import connections
    return connections.authorize_url(platform)


@app.post("/api/connections/finish/{platform}")
def connection_finish(platform: str, payload: dict = Body(...)):
    import connections
    return connections.finish_guided(platform, payload.get("pasted", ""))


@app.delete("/api/connections/{connection_id}")
def remove_connection(connection_id: int):
    import connections
    connections.delete_connection(connection_id)
    return {"ok": True}


# --------------------------------------------------- "use your own app"
# Instagram and TikTok open access without a review to anyone connecting their
# own account through an app they registered themselves. See own_app.py.

@app.get("/api/own-app/{platform}")
def own_app_status(platform: str):
    import own_app
    return own_app.status(platform)


@app.post("/api/own-app/{platform}")
def own_app_save(platform: str, payload: dict = Body(...)):
    import own_app
    return own_app.save(platform, payload.get("client_id", ""), payload.get("client_secret", ""))


@app.delete("/api/own-app/{platform}")
def own_app_clear(platform: str):
    """Switches back to our app. Connections already made stay: they were
    authorized with the customer's own credentials and go on working until the
    customer disconnects them."""
    import own_app
    return own_app.clear(platform)


# ---------------------------------------------------------------- account

def _token_from_header(authorization: str | None) -> str:
    if not authorization:
        return ""
    parts = authorization.split(None, 1)
    return parts[1].strip() if len(parts) == 2 and parts[0].lower() == "bearer" else ""


def _current_plan(authorization: str | None) -> str:
    """The plan in force for this request: the licence verified online, and
    nothing else.

    This used to take the more generous of the licence and `users.plan`, on
    the stated grounds that the second was "an administrative shortcut for
    internal accounts". It was not one. `auth.set_plan` is the only thing that
    writes that column and it has no callers, so the value was never anything
    but the 'free' default the schema gives it — while sitting in cache.db, on
    the customer's own disk, outside the DPAPI protection that covers
    connection tokens. One UPDATE turned on history, best hours, rivals, CSV
    export and the ten-account cap, with the licence still saying 'free'.

    Which is the opposite of what the old docstring here promised: the plan
    cannot depend on a database sitting on the computer of the person who is
    supposed to pay. Now it doesn't."""
    import licensing

    return licensing.current_plan()


@app.post("/api/auth/register")
def auth_register(request: Request, payload: dict = Body(...)):
    import auth
    import rate_limit
    rate_limit.enforce(f"register:{request.client.host}", max_attempts=5, window_seconds=3600)
    try:
        session = auth.register(
            payload.get("email", ""),
            payload.get("password", ""),
            payload.get("password_confirm", ""),
            payload.get("first_name", ""),
            payload.get("last_name", ""),
            payload.get("birth_date", ""),
        )
    except auth.AuthError as exc:
        raise HTTPException(400, str(exc))
    import mail
    mail.send_welcome(payload.get("email", "").strip().lower(), payload.get("first_name", ""))
    return session


@app.post("/api/auth/forgot-password")
def auth_forgot_password(request: Request, payload: dict = Body(...)):
    import auth
    import mail
    import rate_limit
    rate_limit.enforce(f"forgot:{request.client.host}", max_attempts=5, window_seconds=3600)
    email = payload.get("email", "").strip().lower()
    code = auth.request_password_reset(email)
    if code:
        mail.send_reset_code(email, code)
    # The same response whether the address exists or not, or this endpoint
    # becomes a way to find out who is registered.
    return {"ok": True}


@app.post("/api/auth/reset-password")
def auth_reset_password(request: Request, payload: dict = Body(...)):
    import auth
    import mail
    import rate_limit
    rate_limit.enforce(f"reset:{request.client.host}", max_attempts=10, window_seconds=3600)
    try:
        session = auth.reset_password(
            payload.get("email", ""),
            payload.get("code", ""),
            payload.get("password", ""),
            payload.get("password_confirm", ""),
        )
    except auth.AuthError as exc:
        raise HTTPException(400, str(exc))
    # After the change, never before: the notice has to describe something
    # that actually happened. mail never raises, so a successful reset cannot
    # turn into an error because the email did not go out.
    user = session.get("user") or {}
    mail.send_password_changed(user.get("email", ""), user.get("first_name", ""))
    return session


@app.post("/api/auth/login")
def auth_login(request: Request, payload: dict = Body(...)):
    import auth
    import rate_limit
    rate_limit.enforce(f"login:{request.client.host}", max_attempts=10, window_seconds=300)
    try:
        return auth.login(payload.get("email", ""), payload.get("password", ""))
    except auth.AuthError as exc:
        raise HTTPException(401, str(exc))


@app.post("/api/auth/logout")
def auth_logout(authorization: str | None = Header(default=None)):
    import auth
    auth.logout(_token_from_header(authorization))
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(authorization: str | None = Header(default=None)):
    import auth
    user = auth.user_for_token(_token_from_header(authorization))
    if not user:
        raise HTTPException(401, "err_session_expired")
    return {"user": user}


@app.post("/api/auth/password-strength")
def auth_password_strength(payload: dict = Body(...)):
    """Strength scored on the server so it stays consistent with the
    registration rules, storing nothing at any point."""
    import auth
    return auth.password_strength(payload.get("password", ""))


# ---------------------------------------------------------------- pagamenti

@app.get("/api/billing/plans")
def billing_plans():
    import billing
    return billing.list_plans()


@app.post("/api/billing/checkout")
def billing_checkout(payload: dict = Body(...), authorization: str | None = Header(default=None)):
    """Opens the payment. Neither the card details nor the Stripe secret key
    pass through here: the session is created by the service, which is also
    the only thing that can establish who paid."""
    import auth
    import billing

    user = auth.user_for_token(_token_from_header(authorization))
    return billing.start_checkout(
        payload.get("plan_id", ""),
        payload.get("billing_cycle", "monthly"),
        user["email"] if user else "",
    )


# ---------------------------------------------------------------- licenze

@app.get("/api/license")
def license_status():
    import licensing
    return licensing.status()


@app.post("/api/license/activate")
def license_activate(payload: dict = Body(...)):
    """Activates the key issued after payment."""
    import licensing
    return licensing.activate(payload.get("key", ""))


@app.post("/api/license/remove")
def license_remove():
    """Detaches the licence from this installation, so it can move to another
    computer without asking for a new one."""
    import licensing
    licensing.clear()
    return {"ok": True}


@app.post("/api/license/portal")
def license_portal():
    """The Stripe customer-portal URL, where a subscription is genuinely
    cancelled rather than merely detached from this computer. Opened in the
    system browser, not the app's webview: authenticating the customer is
    Stripe's job, not ours."""
    import licensing
    result = licensing.billing_portal_url()
    if not result.get("ok"):
        raise HTTPException(400, result.get("code", "license_service_unavailable"))
    return result


# ---------------------------------------------------------------- export

@app.get("/api/export.csv", response_class=PlainTextResponse)
def export_csv(authorization: str | None = Header(default=None)):
    """Exports the latest snapshot as CSV, to open in Excel or cross-reference
    against other sheets without copying anything out by hand.

    A Pro feature: the check is here, not only on the button."""
    import csv
    import io

    import plans

    if not plans.allows(_current_plan(authorization), "csv_export"):
        raise HTTPException(403, "plan_feature_locked")

    buf = io.StringIO()
    writer = csv.writer(buf)
    # The customer opens this CSV in Excel: the headers are visible text,
    # not internal names, and belong in the product's language.
    writer.writerow(["platform", "account", "metric", "value"])

    yt = cache.latest_snapshot("youtube") or {}
    for c in yt.get("channels", []):
        if not c.get("ok"):
            continue
        for key in ("subscribers", "total_views", "video_count", "recent_views_last10"):
            writer.writerow(["youtube", c.get("name", ""), key, c.get(key, 0)])

    ig = cache.latest_snapshot("instagram") or {}
    for a in ig.get("accounts", []):
        if not a.get("ok"):
            continue
        writer.writerow(["instagram", a.get("name", ""), "followers", a.get("followers", 0)])
        for key, val in (a.get("totals_last_n") or {}).items():
            writer.writerow(["instagram", a.get("name", ""), key, val])

    tt = cache.latest_snapshot("tiktok") or {}
    for a in tt.get("accounts", []):
        if not a.get("ok"):
            continue
        for key, val in (a.get("totals_last_n") or {}).items():
            writer.writerow(["tiktok", a.get("name", ""), key, val])

    return PlainTextResponse(
        buf.getvalue(),
        headers={"Content-Disposition": 'attachment; filename="social-dashboard.csv"'},
        media_type="text/csv",
    )


class _NoCacheStaticFiles(StaticFiles):
    """The app always runs from the same host:port, updates included, so the
    embedded browser can go on serving an old style.css or app.js out of its
    own cache instead of revalidating - a rebuild alone would not be enough to
    make changes visible. No-cache forces a conditional request at every
    startup: it costs very little (small files, all local) and guarantees the
    interface shown is the one from the latest installed build."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


app.mount("/", _NoCacheStaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    def _open_browser():
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8787")

    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8787)
