"""
Comparison against public accounts the user picks.

Copyright (c) 2026 Aurelio Avila. All rights reserved.

What it is for, and how it differs from benchmarks.py: that table says what
average engagement looks like for an audience of your size on your platform.
It is an industry reference, good for telling whether a number is high or low
in absolute terms. What it does not say is how you are doing against the
people doing exactly what you do, which is the question anyone actually asks.
Three hand-picked channels answer that one.

Why this fits a local-first product: it reads ONLY data those channels already
publish to anyone who opens their page - subscribers, total views, video
count. The call goes out from the user's own computer with the credentials
they already connected for their own channels, and the result stays on their
disk. No user data leaves, and no service of ours sees who is watching whom.

Why YouTube only, for now: it is the one platform of the four where reading
another account's public statistics is a call the API provides for and
permits. Instagram would allow it through business_discovery, but only from a
Business account and only towards Business accounts, so it would fail for most
pairs. TikTok and X do not allow it at all. The UI says which platform can be
compared and which cannot, rather than showing an empty panel that looks
broken.
"""
import json
import re
import sqlite3
import time

import cache
import db

# How many can be followed. The limit is not technical: a comparison against
# twenty channels goes back to being a table to read rather than an answer.
# Three is the number of competitors a person actually holds in their head.
MAX_RIVALS = 3

# The shapes a channel gets pasted in: a handle, the page URL, or the raw
# id. All of them are accepted because people paste what they have, and
# pulling the handle out of a URL is our job, not theirs.
_HANDLE = re.compile(r"^@?([A-Za-z0-9._-]{3,30})$")
_URL_HANDLE = re.compile(r"youtube\.com/@([A-Za-z0-9._-]{3,30})")
_URL_CHANNEL = re.compile(r"youtube\.com/channel/(UC[A-Za-z0-9_-]{20,})")


class RivalError(Exception):
    """An error that makes sense shown to the user exactly as it is."""


def _conn() -> sqlite3.Connection:
    conn = db.connect(cache.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            -- As the user typed it, so it can be shown back unchanged.
            handle TEXT NOT NULL,
            -- Resolved on the first successful read; this is the stable
            -- key, because a handle can be changed and an id cannot.
            channel_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            -- The last successful read, as JSON. Kept so the comparison
            -- can still be shown offline, with its date beside it, rather
            -- than disappearing.
            data TEXT NOT NULL DEFAULT '{}',
            fetched_at INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            UNIQUE(platform, handle)
        )
    """)
    return conn


def parse_handle(raw: str) -> str:
    """Pulls the handle or the id out of whatever the user pasted.

    Raises RivalError with a readable message rather than returning None: the
    caller has to tell the user, not carry on quietly.
    """
    testo = (raw or "").strip()
    if not testo:
        raise RivalError("empty")
    trovato = _URL_CHANNEL.search(testo)
    if trovato:
        return trovato.group(1)
    trovato = _URL_HANDLE.search(testo)
    if trovato:
        return "@" + trovato.group(1)
    if testo.startswith("UC") and re.fullmatch(r"UC[A-Za-z0-9_-]{20,}", testo):
        return testo
    trovato = _HANDLE.match(testo)
    if trovato:
        return "@" + trovato.group(1)
    raise RivalError("bad_handle")


def list_rivals(platform: str = "youtube") -> list[dict]:
    conn = _conn()
    try:
        # ORDER BY created_at, id: two channels added in the same second
        # share a created_at, and with no second key the list would reorder
        # itself between one load and the next.
        righe = conn.execute(
            "SELECT id, handle, channel_id, title, data, fetched_at "
            "FROM rivals WHERE platform = ? ORDER BY created_at, id",
            (platform,),
        ).fetchall()
    finally:
        conn.close()
    out = []
    for rid, handle, channel_id, title, data, fetched_at in righe:
        try:
            stats = json.loads(data) if data else {}
        except (ValueError, TypeError):
            # One spoiled row must not take the whole section with it, the
            # same way cache.py already handles this.
            stats = {}
        out.append({
            "id": rid,
            "handle": handle,
            "channel_id": channel_id,
            "title": title or handle,
            "stats": stats,
            "fetched_at": fetched_at,
        })
    return out


def add_rival(raw_handle: str, platform: str = "youtube") -> dict:
    if platform != "youtube":
        raise RivalError("platform_unsupported")
    handle = parse_handle(raw_handle)
    conn = _conn()
    try:
        quanti = conn.execute(
            "SELECT COUNT(*) FROM rivals WHERE platform = ?", (platform,)
        ).fetchone()[0]
        if quanti >= MAX_RIVALS:
            raise RivalError("too_many")
        try:
            conn.execute(
                "INSERT INTO rivals (platform, handle, created_at) VALUES (?, ?, ?)",
                (platform, handle, int(time.time())),
            )
        except sqlite3.IntegrityError:
            raise RivalError("already_tracked")
        conn.commit()
    finally:
        conn.close()
    return {"handle": handle}


def remove_rival(rival_id: int) -> None:
    conn = _conn()
    try:
        conn.execute("DELETE FROM rivals WHERE id = ?", (rival_id,))
        conn.commit()
    finally:
        conn.close()


def _public_channel(youtube, handle: str) -> dict:
    """The statistics the channel already publishes to everyone.

    `part` deliberately asks for statistics and snippet only: those are the
    two public blocks. Nothing is requested that would require owning the
    channel, because we do not, and it must not look as though we do.
    """
    if handle.startswith("@"):
        resp = youtube.channels().list(part="statistics,snippet", forHandle=handle).execute()
    else:
        resp = youtube.channels().list(part="statistics,snippet", id=handle).execute()
    items = resp.get("items") or []
    if not items:
        raise RivalError("not_found")
    item = items[0]
    stats = item.get("statistics", {})
    # A channel can hide its subscriber count. The API sends
    # hiddenSubscriberCount in that case: record it as None, not zero - zero
    # would say "has no subscribers", which is a different thing and false.
    nascosti = bool(stats.get("hiddenSubscriberCount"))
    return {
        "channel_id": item.get("id", ""),
        "title": item.get("snippet", {}).get("title", ""),
        "subscribers": None if nascosti else int(stats.get("subscriberCount", 0) or 0),
        "total_views": int(stats.get("viewCount", 0) or 0),
        "video_count": int(stats.get("videoCount", 0) or 0),
    }


def refresh(platform: str = "youtube") -> dict:
    """Re-reads every followed channel. One failure does not stop the rest.

    The credentials are the ones the user already connected for their own
    channels: reading public data needs nothing more, and nobody is asked for
    a second connection to cover what the first one already does.
    """
    seguiti = list_rivals(platform)
    if not seguiti:
        return {"updated": 0, "errors": []}

    import platforms.youtube as yt

    sorgenti = yt._sources()
    if not sorgenti:
        raise RivalError("no_credentials")
    sorgente = sorgenti[0]
    if sorgente["kind"] == "oauth":
        youtube = yt._service_from_creds(
            sorgente["refresh_token"], sorgente["client_id"],
            sorgente["client_secret"], sorgente["scopes"],
        )
    else:
        youtube = yt._service_for(sorgente["prefix"])

    aggiornati = 0
    errori = []
    conn = _conn()
    try:
        for rivale in seguiti:
            try:
                dati = _public_channel(youtube, rivale["handle"])
            except RivalError as errore:
                errori.append({"handle": rivale["handle"], "error": str(errore)})
                continue
            except Exception as errore:
                errori.append({"handle": rivale["handle"], "error": _leggibile(errore)})
                continue
            conn.execute(
                "UPDATE rivals SET channel_id = ?, title = ?, data = ?, fetched_at = ? WHERE id = ?",
                (dati["channel_id"], dati["title"], json.dumps(dati), int(time.time()), rivale["id"]),
            )
            aggiornati += 1
        conn.commit()
    finally:
        conn.close()
    return {"updated": aggiornati, "errors": errori}


def _leggibile(errore: Exception) -> str:
    """An API error reduced to something that can be shown.

    googleapiclient's exceptions carry the full request URL inside them, and
    that URL contains the key. It must reach neither the screen nor a log.
    """
    testo = str(errore)
    if "quota" in testo.lower():
        return "quota"
    if "403" in testo:
        return "forbidden"
    if "404" in testo:
        return "not_found"
    return "fetch_failed"


def compare(snapshot: dict, platform: str = "youtube") -> dict | None:
    """The standings: your channels and the followed ones, on one scale.

    Returns None when there is nothing to say - no rivals followed, or no
    successful read yet. A section that shows up empty is worse than one that
    does not show up.
    """
    seguiti = [r for r in list_rivals(platform) if r["stats"]]
    if not seguiti:
        return None

    import analytics

    miei = []
    for canale in analytics._lista((snapshot.get(platform) or {}).get("channels")):
        if not isinstance(canale, dict):
            continue
        miei.append({
            "title": canale.get("title") or canale.get("name") or "",
            "subscribers": int(analytics._num(canale.get("subscribers"))),
            "total_views": int(analytics._num(canale.get("total_views"))),
            "video_count": int(analytics._num(canale.get("video_count"))),
            "mine": True,
        })
    if not miei:
        return None

    loro = [{
        "title": r["title"],
        "handle": r["handle"],
        "subscribers": r["stats"].get("subscribers"),
        "total_views": int(r["stats"].get("total_views") or 0),
        "video_count": int(r["stats"].get("video_count") or 0),
        "fetched_at": r["fetched_at"],
        "mine": False,
    } for r in seguiti]

    # Per-video averages are the comparison that holds up between accounts
    # of different sizes: totals only reward whoever has been publishing
    # longest.
    def per_video(riga: dict) -> float:
        video = riga.get("video_count") or 0
        return round((riga.get("total_views") or 0) / video, 1) if video else 0.0

    tutti = miei + loro
    for riga in tutti:
        riga["views_per_video"] = per_video(riga)

    # The ranking is computed only over channels that publish their
    # subscriber count: counting a hidden one as "zero" would put it last for
    # making a privacy choice, which is not a result.
    con_iscritti = [r for r in tutti if isinstance(r.get("subscribers"), int)]
    con_iscritti.sort(key=lambda r: r["subscribers"], reverse=True)
    posizione = None
    for indice, riga in enumerate(con_iscritti, start=1):
        if riga.get("mine"):
            posizione = indice
            break

    return {
        "platform": platform,
        "rows": sorted(tutti, key=lambda r: r.get("subscribers") or -1, reverse=True),
        "rank": posizione,
        "ranked_of": len(con_iscritti) if posizione else 0,
        "hidden_subscribers": any(r.get("subscribers") is None for r in tutti),
    }
