"""
Confronto con account pubblici scelti dall'utente.

Copyright (c) 2026 Aurelio Avila. All rights reserved.

A cosa serve, e in cosa e' diverso da benchmarks.py: quella tabella dice
com'e' l'engagement medio di chi ha un pubblico della tua dimensione sulla
tua piattaforma. E' un riferimento di settore, buono per capire se un
numero e' alto o basso in assoluto. Non dice pero' come stai rispetto a
chi fa esattamente la tua stessa cosa, che e' la domanda che uno si fa
davvero. Tre canali scelti a mano rispondono a quella.

Perche' e' compatibile con un prodotto local-first: si leggono SOLO dati
che quei canali pubblicano gia' a chiunque apra la loro pagina - iscritti,
visualizzazioni totali, numero di video. La chiamata parte dal computer
dell'utente con le credenziali che ha gia' collegato per i suoi canali, e
il risultato resta sul suo disco. Nessun dato dell'utente esce, nessun
servizio nostro vede chi sta guardando chi.

Perche' solo YouTube, per ora: e' l'unica delle quattro piattaforme dove
leggere le statistiche pubbliche di un account altrui e' una chiamata
prevista e consentita dall'API. Instagram lo permetterebbe con
business_discovery, ma solo da un account Business e solo verso account
Business, quindi fallirebbe per la maggior parte delle coppie. TikTok e X
non lo permettono affatto. La UI dice quale piattaforma si puo'
confrontare e quale no, invece di mostrare un riquadro vuoto che sembra
rotto.
"""
import json
import re
import sqlite3
import time

import cache
import db

# Quanti se ne possono seguire. Il limite non e' tecnico: e' che un
# confronto con venti canali torna a essere una tabella da leggere invece
# di una risposta. Tre e' il numero di concorrenti che una persona ha
# davvero in testa.
MAX_RIVALS = 3

# Le forme in cui si incolla un canale: handle, URL della pagina, o l'id
# grezzo. Si accettano tutte perche' l'utente incolla quello che ha, e
# chiedergli di estrarre l'handle da un URL e' un compito nostro.
_HANDLE = re.compile(r"^@?([A-Za-z0-9._-]{3,30})$")
_URL_HANDLE = re.compile(r"youtube\.com/@([A-Za-z0-9._-]{3,30})")
_URL_CHANNEL = re.compile(r"youtube\.com/channel/(UC[A-Za-z0-9_-]{20,})")


class RivalError(Exception):
    """Errore che ha senso mostrare all'utente cosi' com'e'."""


def _conn() -> sqlite3.Connection:
    conn = db.connect(cache.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            -- Come lo ha scritto l'utente, per poterglielo rimostrare uguale.
            handle TEXT NOT NULL,
            -- Risolto alla prima lettura riuscita; e' la chiave stabile,
            -- perche' un handle si puo' cambiare mentre l'id no.
            channel_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            -- Ultima lettura riuscita, come JSON. Si conserva perche' il
            -- confronto deve poter comparire anche offline, con la data
            -- accanto, invece di sparire.
            data TEXT NOT NULL DEFAULT '{}',
            fetched_at INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            UNIQUE(platform, handle)
        )
    """)
    return conn


def parse_handle(raw: str) -> str:
    """Estrae l'handle o l'id da quello che l'utente ha incollato.

    Solleva RivalError con un messaggio leggibile invece di restituire
    None: chi chiama deve dirlo all'utente, non tirare avanti in silenzio.
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
        # ORDER BY created_at, id: due canali aggiunti nello stesso secondo
        # hanno lo stesso created_at, e senza un secondo criterio l'elenco
        # cambierebbe ordine da solo fra un caricamento e l'altro.
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
            # Una riga rovinata non deve far sparire l'intera sezione, come
            # gia' si fa in cache.py.
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
    """Le statistiche che il canale pubblica gia' a chiunque.

    `part` chiede deliberatamente solo statistics e snippet: sono i due
    blocchi pubblici. Non si chiede nulla che richieda di essere il
    proprietario del canale, perche' non lo siamo e non deve sembrare che
    lo siamo.
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
    # Un canale puo' nascondere il numero di iscritti. In quel caso l'API
    # manda hiddenSubscriberCount: si registra come None, non come zero -
    # zero direbbe "non ha iscritti", che e' una cosa diversa e falsa.
    nascosti = bool(stats.get("hiddenSubscriberCount"))
    return {
        "channel_id": item.get("id", ""),
        "title": item.get("snippet", {}).get("title", ""),
        "subscribers": None if nascosti else int(stats.get("subscriberCount", 0) or 0),
        "total_views": int(stats.get("viewCount", 0) or 0),
        "video_count": int(stats.get("videoCount", 0) or 0),
    }


def refresh(platform: str = "youtube") -> dict:
    """Rilegge tutti i canali seguiti. Un fallimento su uno non ferma gli altri.

    Le credenziali sono quelle che l'utente ha gia' collegato per i suoi
    canali: leggere dati pubblici non richiede altro, e non si chiede
    all'utente un secondo collegamento per una cosa che il primo copre.
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
    """Un errore dell'API ridotto a qualcosa che si puo' mostrare.

    Le eccezioni di googleapiclient portano dentro l'URL completo della
    richiesta, che contiene la chiave. Non deve finire ne' a schermo ne'
    in un log.
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
    """Il posizionamento: i tuoi canali e quelli seguiti, sulla stessa scala.

    Restituisce None quando non c'e' niente da dire - nessun rivale
    seguito, o nessuna lettura ancora riuscita. Una sezione che compare
    vuota e' peggio di una che non compare.
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

    # Le medie per video sono il confronto che regge fra account di
    # dimensioni diverse: il totale premia solo chi pubblica da piu' tempo.
    def per_video(riga: dict) -> float:
        video = riga.get("video_count") or 0
        return round((riga.get("total_views") or 0) / video, 1) if video else 0.0

    tutti = miei + loro
    for riga in tutti:
        riga["views_per_video"] = per_video(riga)

    # La posizione si calcola solo sui canali che dichiarano gli iscritti:
    # includere chi li nasconde come "zero" lo metterebbe ultimo per una
    # scelta di privacy, che non e' un risultato.
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
