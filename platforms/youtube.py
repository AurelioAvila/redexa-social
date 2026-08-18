"""
Legge statistiche pubbliche (subscriberCount, viewCount, videoCount) per
ogni canale YouTube elencato in YT_CHANNELS (formato "Nome:PREFIX,..."),
riusando lo stesso pattern OAuth di solofounded-bot/src/analytics.py.
Serve solo lo scope youtube.readonly gia' autorizzato sui refresh token
esistenti - niente YouTube Analytics API.
"""
import os
import time
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _service_from_creds(refresh_token: str, client_id: str, client_secret: str, scopes: list[str]):
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
    return build("youtube", "v3", credentials=creds)


def _service_for(prefix: str):
    # Alcuni refresh token esistenti sono stati generati con uno scope diverso
    # (es. solo youtube.upload, o il full "youtube") - il refresh fallisce con
    # invalid_scope se qui si richiede uno scope non concesso in origine.
    # Override per canale via {PREFIX}_YOUTUBE_SCOPE nel .env se serve.
    scope = os.environ.get(f"{prefix}_YOUTUBE_SCOPE", "https://www.googleapis.com/auth/youtube.readonly")
    return _service_from_creds(
        os.environ[f"{prefix}_YOUTUBE_REFRESH_TOKEN"],
        os.environ[f"{prefix}_YOUTUBE_CLIENT_ID"],
        os.environ[f"{prefix}_YOUTUBE_CLIENT_SECRET"],
        scope.split(),
    )


def _parse_channels() -> list[tuple[str, str]]:
    raw = os.environ.get("YT_CHANNELS", "")
    out = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        name, prefix = entry.split(":", 1)
        out.append((name.strip(), prefix.strip()))
    return out


def _sources() -> list[dict]:
    """Canali da leggere: quelli configurati a mano nel .env piu' quelli
    collegati con "Collega account" (login OAuth). Le due strade convivono,
    cosi' una configurazione manuale gia' esistente non smette di funzionare
    quando si inizia a usare il collegamento automatico."""
    sources = [{"name": name, "prefix": prefix, "kind": "env"} for name, prefix in _parse_channels()]

    import connections
    for conn in connections.list_connections("youtube"):
        data = conn["data"]
        sources.append({
            "name": conn["account_name"],
            "kind": "oauth",
            "connection_id": conn["id"],
            "refresh_token": data["refresh_token"],
            "client_id": data["client_id"],
            "client_secret": data["client_secret"],
            "scopes": data.get("scopes") or ["https://www.googleapis.com/auth/youtube.readonly"],
        })
    return sources


def count_units() -> int:
    """Numero di canali configurati - usato per un progresso di refresh
    granulare (un'unita' di lavoro per canale, non uno per l'intera
    piattaforma) invece di un'unica barra a scatti su 5 voci totali."""
    return len(_sources())


def _fetch_channel(source: dict) -> dict:
    """Un tentativo di lettura per un singolo canale - isolato in una
    funzione cosi' fetch_stats puo' ritentarlo una volta in caso di errore
    transitorio (es. hiccup momentaneo del token endpoint di Google durante
    il refresh in parallelo di piu' canali/piattaforme contemporaneamente)."""
    if source["kind"] == "oauth":
        youtube = _service_from_creds(
            source["refresh_token"], source["client_id"], source["client_secret"], source["scopes"]
        )
    else:
        youtube = _service_for(source["prefix"])
    name = source["name"]
    resp = youtube.channels().list(part="statistics,snippet", mine=True).execute()
    item = resp["items"][0]
    stats = item["statistics"]

    recent_views = 0
    recent_videos = []
    try:
        uploads = youtube.channels().list(part="contentDetails", mine=True).execute()
        playlist_id = uploads["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        items = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=10).execute()
        video_ids = [i["contentDetails"]["videoId"] for i in items["items"]]
        if video_ids:
            videos = youtube.videos().list(part="statistics,snippet", id=",".join(video_ids)).execute()
            for v in videos["items"]:
                views = int(v["statistics"].get("viewCount", 0))
                recent_views += views
                published = v["snippet"].get("publishedAt")
                hour = None
                if published:
                    try:
                        hour = datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(timezone.utc).hour
                    except Exception:
                        hour = None
                recent_videos.append({
                    "title": v["snippet"].get("title", ""),
                    "published": published,
                    "publish_hour_utc": hour,
                    "views": views,
                    "likes": int(v["statistics"].get("likeCount", 0)),
                    "comments": int(v["statistics"].get("commentCount", 0)),
                })
    except Exception:
        pass

    return {
        "name": name,
        "title": item["snippet"]["title"],
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "recent_views_last10": recent_views,
        "recent_videos": recent_videos,
        "source": source["kind"],
        "ok": True,
    }


def fetch_stats(on_item=None) -> dict:
    channels_out = []
    errors = []
    for source in _sources():
        name = source["name"]
        last_exc = None
        result = None
        # Fino a 3 tentativi con backoff crescente - assorbe hiccup
        # transitori del token endpoint di Google quando piu' canali/
        # piattaforme fanno refresh OAuth in parallelo (osservato in pratica
        # sull'exe compilato anche se non riproducibile isolatamente),
        # invece di marcare subito il canale come in errore dopo un solo
        # fallimento momentaneo.
        for attempt, backoff in enumerate((0, 2, 5)):
            if backoff:
                time.sleep(backoff)
            try:
                result = _fetch_channel(source)
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
        if result is not None:
            channels_out.append(result)
        else:
            errors.append(f"{name}: {last_exc}")
            channels_out.append({"name": name, "ok": False, "error": str(last_exc), "source": source["kind"]})
        if on_item:
            on_item()

    return {"platform": "youtube", "channels": channels_out, "errors": errors}
