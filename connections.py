"""
"Collega account": sostituisce la configurazione manuale di client id,
secret e refresh token dentro il .env con un normale login OAuth.

L'utente clicca "Collega YouTube", si apre il browser sulla pagina di
Google, autorizza, e il token torna indietro da solo. Funziona con il
flusso "installed app" (redirect su 127.0.0.1 con porta effimera), lo
stesso che Google prevede per le applicazioni desktop: nessun server
pubblico da esporre, nessun copia-incolla di token.

Le connessioni vivono in cache.db e vengono lette dagli adapter delle
piattaforme insieme a quelle eventualmente gia' presenti nel .env, cosi'
una configurazione manuale esistente continua a funzionare.

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

# Stato del collegamento in corso: il flusso OAuth blocca finche' l'utente
# non completa il login nel browser, quindi gira in un thread e il frontend
# ne segue l'avanzamento in polling (stessa logica del refresh).
#
# started_at serve a non restare bloccati: se un tentativo precedente e'
# morto male (finestra chiusa in un modo che non solleva eccezioni, thread
# appeso), senza scadenza lo stato resterebbe "running" e ogni collegamento
# successivo verrebbe respinto con "C'e' gia' un collegamento in corso".
_connect_state = {"running": False, "platform": None, "error": None, "done": False,
                  "account": None, "started_at": 0}
_connect_lock = threading.RLock()

# Incrementato a ogni nuovo tentativo (start_connect) e a ogni cancellazione:
# il thread di collegamento in corso porta con se' il valore letto all'avvio
# e lo ricontrolla prima di scrivere il risultato finale. Se nel frattempo
# l'utente ha annullato (o e' partito un nuovo tentativo), il generation
# number e' cambiato e la scrittura tardiva viene scartata invece di
# sovrascrivere uno stato "cancelled" con un "done" che non ha piu' senso.
_connect_gen = 0

# Oltre questo tempo un collegamento "in corso" e' considerato abbandonato:
# e' piu' del tempo che serve a un login reale, ma abbastanza poco da non
# lasciare l'utente bloccato ad aspettare.
CONNECT_STALE_SECONDS = 330


def _connect_is_active() -> bool:
    """True solo se c'e' davvero un collegamento vivo, non un residuo."""
    with _connect_lock:
        if not _connect_state["running"]:
            return False
        if time.time() - (_connect_state.get("started_at") or 0) > CONNECT_STALE_SECONDS:
            _connect_state["running"] = False
            _connect_state["error"] = _connect_state["error"] or "connect_timeout"
            return False
        return True


def cancel_connect() -> dict:
    """Annulla il collegamento in corso, cosi' l'utente non deve aspettare
    la scadenza se ha chiuso la finestra o ha cambiato idea. Incrementa il
    generation number cosi' che il thread ormai orfano non possa piu'
    scrivere un risultato tardivo sopra questo reset."""
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


# Motivi per cui un accesso smette di valere. Sono gli unici casi in cui ha
# senso chiedere all'utente di ricollegare: un timeout o un errore 500 della
# piattaforma non dicono niente sul token, e marcare l'account per quelli
# vorrebbe dire mandare l'utente a rifare l'accesso per un disservizio
# temporaneo che si risolve da solo.
_AUTH_FAILURE_NEEDLES = (
    "invalid_grant", "expired", "revoked", "invalid_token", "token has been",
    "unauthorized", "401", "invalid_scope", "oauthexception",
)


def is_auth_failure(errore) -> bool:
    """L'errore dice che serve una nuova autorizzazione, o e' solo un
    problema passeggero?

    Accetta qualsiasi cosa e la porta a testo: gli errori arrivano da tre
    librerie diverse e non sempre sono stringhe (un'eccezione, dei byte da
    una risposta HTTP, un codice numerico). Chiedere al chiamante di
    convertire significa che prima o poi qualcuno se ne dimentica, e questa
    funzione decide se mandare l'utente a rifare un accesso: non e' il posto
    dove sollevare un TypeError.
    """
    if errore is None:
        return False
    if isinstance(errore, bytes):
        errore = errore.decode("utf-8", "replace")
    basso = str(errore).lower()
    return any(n in basso for n in _AUTH_FAILURE_NEEDLES)


def mark_auth_failed(connection_id: int, motivo: str) -> None:
    """Annota che questo account non e' piu' utilizzabile senza un nuovo
    accesso. Non cancella niente: il token potrebbe tornare valido (un
    rinnovo riuscito ripulisce lo stato) e cancellare la connessione
    porterebbe via anche lo storico gia' raccolto per quell'account."""
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
    """Punto unico dove gli adapter delle piattaforme dicono com'e' andata.

    Sta qui e non dentro i singoli adapter perche' la regola su cosa conta
    come "accesso da rifare" deve essere una sola: se ogni piattaforma
    decidesse per conto suo, prima o poi una marcherebbe l'account per un
    timeout di rete e l'utente si troverebbe a rifare un accesso che
    funzionava benissimo.

    connection_id assente = account configurato da .env e non dal database
    (uso personale): non c'e' nessuna riga da aggiornare.
    """
    if not connection_id:
        return
    try:
        if errore is None:
            mark_auth_ok(connection_id)
        elif is_auth_failure(str(errore)):
            mark_auth_failed(connection_id, str(errore))
    except Exception:
        # Annotare lo stato e' un di piu': se fallisce (database occupato,
        # disco pieno) l'aggiornamento deve comunque restituire i dati che
        # ha gia' raccolto, non morire per una scrittura accessoria.
        logging.warning("authentication state was not updated", exc_info=True)


def mark_auth_ok(connection_id: int) -> None:
    """Il rinnovo e' andato a buon fine: l'account torna normale. Scrive solo
    se c'era davvero qualcosa da azzerare, cosi' un aggiornamento riuscito
    non tocca il database per niente."""
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
    """Gli account utilizzabili, token compresi.

    Le righe che non si riescono a decifrare vengono saltate: succede
    quando il database arriva da un altro computer o da un altro account
    Windows, ed e' esattamente cio' che la cifratura deve impedire. Per chi
    legge questa lista (gli adapter delle piattaforme) quell'account
    semplicemente non c'e', come se fosse scollegato - meglio di un errore
    a meta' aggiornamento. L'interfaccia lo mostra comunque, contrassegnato,
    tramite public_connections.
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
    """Come list_connections ma senza i token: questa e' la versione che
    puo' uscire verso il frontend.

    Include anche gli account non decifrabili, con "locked": cosi' l'utente
    vede che ci sono e che vanno ricollegati, invece di vederli sparire
    senza spiegazione.
    """
    import secrets_store

    pubblici = []
    for r in _rows():
        voce = {"id": r[0], "platform": r[1], "account_name": r[2],
                "account_id": r[3], "created_at": r[5]}
        # L'accesso e' scaduto o e' stato revocato: l'account risulta ancora
        # collegato ma non serve a niente finche' non lo si rifa'. Senza
        # questo l'interfaccia lo mostrava attivo mentre la diagnostica
        # diceva l'opposto, e le due schermate si contraddicevano.
        if r[6]:
            voce["needs_reauth"] = True
            voce["auth_checked_at"] = r[7]
        try:
            secrets_store.unprotect(r[4])
        except secrets_store.SecretUnavailable:
            voce["locked"] = True
        pubblici.append(voce)
    return pubblici


def save_connection(platform: str, account_name: str, account_id: str, data: dict) -> None:
    import secrets_store

    # I token non toccano mai il disco in chiaro: si cifrano qui, non in una
    # ripulitura successiva che potrebbe non arrivare mai.
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
                 -- Ricollegare significa credenziali nuove: l'eventuale
                 -- "da ricollegare" di prima non vale piu'. Senza questo
                 -- l'avviso sarebbe rimasto fino al primo aggiornamento
                 -- riuscito, proprio mentre l'utente ha appena fatto quello
                 -- che gli veniva chiesto.
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

    # Se non resta piu' nessun account di questa piattaforma, i numeri
    # visti l'ultima volta non sono piu' di nessuno: senza questo restavano
    # in cache e la dashboard continuava a mostrarli come se fossero
    # ancora veri, finche' l'utente non premeva Refresh a mano.
    if row and not list_connections(row[0]):
        cache.clear_snapshot(row[0])


def _google_client() -> tuple[str, str] | None:
    """Credenziali dell'app OAuth usate per il login Google.

    In una build distribuita sono quelle dell'applicazione (per le desktop
    app Google non considera il secret una vera credenziale segreta). Qui
    si accetta anche un client gia' presente nel .env, cosi' la funzione e'
    utilizzabile subito senza doverne registrare un altro."""
    import brand
    if brand.configured("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"):
        return brand.get("GOOGLE_CLIENT_ID"), brand.get("GOOGLE_CLIENT_SECRET")

    client_id = os.environ.get("OAUTH_GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("OAUTH_GOOGLE_CLIENT_SECRET")
    if client_id and client_secret:
        return client_id, client_secret

    # Ultima spiaggia, solo in sviluppo: riusa una qualsiasi coppia
    # *_YOUTUBE_CLIENT_ID/_SECRET gia' presente nel .env.
    #
    # Fuori dalla build personale questo fallback NON deve esistere. Ha gia'
    # fatto danni: durante lo sviluppo mascherava il fatto che GOOGLE_CLIENT_ID
    # in brand.py fosse vuoto (le credenziali arrivavano da un altro progetto
    # nel .env), quindi YouTube sembrava collegabile mentre nella build
    # distribuita non lo era. E su un computer altrui userebbe le credenziali
    # di quella persona senza dirglielo.
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
    # port=0 => porta libera scelta dal sistema; Google accetta qualunque
    # porta su 127.0.0.1 per i client di tipo "Desktop app".
    # select_account e' quello che rende possibile collegare piu' canali:
    # senza, Google riusa in silenzio l'account gia' loggato nel browser e
    # si finisce per ricollegare sempre lo stesso.
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
# Instagram e TikTok: collegamento guidato
#
# Nessuna delle due accetta un redirect su 127.0.0.1 (pretendono un URL
# HTTPS), quindi il login automatico in stile YouTube non e' possibile senza
# un endpoint pubblico. Il flusso guidato riduce comunque tutto a: apri il
# link, autorizza, incolla l'URL su cui sei atterrato. Un solo incolla al
# posto di tre variabili da scrivere a mano nel .env per ogni account.
# ---------------------------------------------------------------------------

def _oauth_window_available() -> bool:
    """True se la finestra nativa dell'app e' attiva e possiamo aprirci
    dentro il login. Nell'eseguibile lo e' sempre; avviando solo il server
    (sviluppo) no, e allora si ricade sul flusso con incolla."""
    try:
        import webview
        return bool(webview.windows)
    except Exception:
        return False


def _connect_in_window(auth_url: str, redirect_uri: str, title: str, timeout: int = 300) -> str:
    """Apre il login dentro una finestra dell'app e intercetta il redirect.

    E' questo che rende il collegamento un solo clic: Instagram e TikTok
    pretendono un redirect HTTPS (niente 127.0.0.1), ma non serve che quella
    pagina esista davvero - basta accorgersi che la finestra ci sta
    navigando sopra e leggere il codice dall'URL prima ancora che carichi.
    Nessun token da incollare, nessuna configurazione lato utente.
    """
    import webview

    window = webview.create_window(title, auth_url, width=520, height=720)
    result = {}

    # Chiudere la finestra non sempre fa fallire get_current_url(): su alcuni
    # backend continua a restituire l'ultimo URL, e il ciclo restava in piedi
    # fino al timeout tenendo lo stato bloccato su "collegamento in corso".
    # L'evento closed e' il segnale attendibile.
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
        # Il confronto esatto sul prefisso non basta: se la pagina di
        # atterraggio e' un'applicazione web, il suo router riscrive l'URL
        # (senza redirect HTTP) prima che il polling se ne accorga, e il
        # codice andava perso restando appesi fino al timeout. Appena
        # siamo fuori dal dominio di login e c'e' un `code`, e' il nostro.
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
    # Torna l'URL intero, non il solo codice: chi chiama deve poter
    # verificare anche lo state prima di fidarsi del codice.
    return result["url"]


def _state_from(raw: str) -> str:
    """Il parametro state dell'URL di ritorno, se c'e'."""
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
    """Accetta sia il codice nudo sia l'intero URL di ritorno, da cui estrae
    il parametro code. Instagram accoda '#_' al codice: va tolto o lo
    scambio del token fallisce."""
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


# Questi due valori finiscono dritti nell'interfaccia. Sono codici e non
# frasi perche' il testo va scritto nella lingua scelta dall'utente: una
# stringa italiana decisa qui resterebbe italiana anche con l'app in
# inglese (era esattamente il caso di "X non espone le statistiche...").
NOT_SET = "unavail_not_configured"


def _env_pair(id_suffix: str, secret_suffix: str) -> tuple[str, str] | None:
    """Recupera una coppia id/secret gia' presente nel .env con un prefisso
    qualsiasi (es. SOLOFOUNDED_TIKTOK_CLIENT_KEY). Evita di richiedere di
    nuovo credenziali che l'utente ha gia' configurato altrove."""
    for key, value in os.environ.items():
        if key.endswith(id_suffix) and value:
            secret = os.environ.get(key[: -len(id_suffix)] + secret_suffix)
            if secret:
                return value, secret
    return None


# ---------------------------------------------------------------------------
# Scambio del token tramite proxy
#
# Instagram e TikTok pretendono il client secret per trasformare il `code` in
# un token. Compilarlo dentro l'eseguibile significa consegnarlo a chiunque
# scarichi l'app: basta decomprimere il binario per rileggerlo in chiaro
# (verificato). Meta lo dice esplicitamente: l'app secret non va mai messo in
# codice distribuito.
#
# Con OAUTH_PROXY_URL configurato lo scambio avviene su un endpoint nostro che
# custodisce i segreti, e nella build non ne finisce nessuno. Senza, si ricade
# sul comportamento storico (utile in sviluppo, sconsigliato per distribuire).
# ---------------------------------------------------------------------------

def proxy_url() -> str:
    import brand
    return (brand.get("OAUTH_PROXY_URL") or "").rstrip("/")


def using_proxy(platform: str | None = None) -> bool:
    """Il proxy custodisce i *nostri* segreti. Se il cliente ha registrato
    un'app propria il segreto e' suo e sta solo su questo computer: lo
    scambio del token deve avvenire in locale, altrimenti il proxy tenterebbe
    di firmarlo con credenziali che non c'entrano nulla."""
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
        # Il testo grezzo resta nei log per il debug; all'utente arriva solo
        # un codice, cosi' il messaggio segue la lingua scelta nell'app.
        print(f"[oauth-proxy] {resp.status_code}: {resp.text[:200]}")
        raise RuntimeError("connect_proxy_http_error")
    data = resp.json()
    if data.get("error"):
        print(f"[oauth-proxy] rejected: {str(data['error'])[:200]}")
        raise RuntimeError("connect_proxy_rejected")
    return data


def _instagram_app() -> tuple[str, str, str]:
    """(app_id, secret, redirect). Con il proxy attivo il secret non e' nella
    build e resta vuoto: serve solo all'endpoint che fa lo scambio."""
    import brand
    import own_app
    redirect = brand.get("INSTAGRAM_REDIRECT_URI")

    # L'app registrata dal cliente ha la precedenza: e' quella che gli
    # permette di collegare il proprio account senza attendere la nostra
    # revisione, quindi se c'e' e' perche' vuole usare quella.
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
    """(client_key, secret, redirect). Vedi _instagram_app per il secret."""
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
    """Le credenziali dell'app per questa piattaforma sono disponibili?
    Serve a non mostrare un pulsante che porterebbe a un vicolo cieco."""
    check = APP_CHECKS.get(platform)
    if not check:
        return False
    try:
        check()
        return True
    except Exception:
        return False


# Lo `state` di OAuth serve a una cosa sola: riconoscere che il codice che
# torna indietro appartiene alla richiesta che abbiamo fatto noi. Veniva
# generato e poi buttato via, il che lo rendeva decorativo: nel flusso con
# incolla manuale bastava convincere qualcuno a incollare l'URL di ritorno di
# un *altro* account per agganciare quell'account alla sua dashboard.
#
# Si tiene solo l'ultimo per piattaforma: i collegamenti sono uno alla volta
# (lo impone gia' _connect_is_active) e cosi' non resta nulla da ripulire.
_pending_state: dict[str, str] = {}


def _remember_state(platform: str) -> str:
    value = secrets.token_urlsafe(24)
    _pending_state[platform] = value
    return value


def _check_state(platform: str, returned: str) -> None:
    """Consuma lo state atteso. Non si accetta un ritorno senza state quando
    ne avevamo chiesto uno: sarebbe come non averlo mai messo."""
    expected = _pending_state.pop(platform, None)
    if not expected:
        raise RuntimeError("connect_state_missing")
    if not returned or not secrets.compare_digest(expected, returned):
        raise RuntimeError("connect_state_mismatch")


def authorize_url(platform: str) -> dict:
    """URL da aprire nel browser per autorizzare l'account."""
    from urllib.parse import urlencode

    if coming_soon(platform):
        return {"ok": False, "message": "connect_coming_soon"}

    try:
        # force_reauth / disable_auto_auth: la finestra dell'app conserva i
        # cookie della piattaforma, quindi senza questi parametri il secondo
        # collegamento salta login e consenso e ricollega in silenzio lo
        # stesso account. Sono loro a rendere possibile "collega un altro
        # account" davvero.
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
        # Il secret non e' in questa build: code -> token a lunga durata
        # avviene sull'endpoint che lo custodisce.
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

        # Il token breve dura un'ora: si scambia subito con quello a 60 giorni,
        # altrimenti il collegamento smetterebbe di funzionare quasi subito.
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

    # Se manca 'video.list' il login e' comunque riuscito: buttare via la
    # connessione lascerebbe l'utente senza account collegato e senza capire
    # perche'. Si salva lo stesso e si annota lo scope concesso - sara' la
    # diagnostica a spiegare che manca l'approvazione del permesso, con un
    # messaggio tradotto invece di un errore secco al momento del login.
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

    # Col proxy il secret non viene salvato nemmeno in locale: il rinnovo del
    # token passera' anch'esso dall'endpoint che lo custodisce.
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
    """Login a un clic dentro la finestra dell'app, per le piattaforme che
    non accettano un redirect su 127.0.0.1."""
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
        # Qui arriva un valore incollato a mano: e' il punto in cui qualcuno
        # potrebbe essere convinto a incollare l'URL di ritorno di un altro
        # account. Lo state va verificato prima di scambiare il codice, e
        # per questo serve l'indirizzo intero, non il solo codice.
        _check_state(platform, _state_from(pasted))
        account = finisher(_clean_code(pasted))
        return {"ok": True, "account": account}
    except Exception:
        return {"ok": False, "message": "connect_failed"}


def connect_mode(platform: str) -> str:
    """Come si collega questa piattaforma, cosi' il frontend mostra un solo
    bottone quando basta un clic e i passaggi manuali solo se indispensabili.

    Se le credenziali dell'app non ci sono, si dichiara "unavailable" fin
    da subito: meglio dirlo prima che far premere un pulsante destinato a
    fallire."""
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
    """Motivo leggibile per cui una piattaforma non e' collegabile."""
    if platform in UNAVAILABLE:
        return UNAVAILABLE[platform]
    if platform in (set(CONNECTORS) | set(GUIDED)) and not credentials_ready(platform):
        return NOT_SET
    return None


# Piattaforme senza alcun collegamento possibile. Anche qui: codice, non
# frase (vedi il commento su NOT_SET).
UNAVAILABLE = {
    "x": "unavail_x_no_read_api",
}

# Instagram e TikTok hanno le credenziali pronte ma non sono ancora
# collegabili per un cliente qualsiasi: Instagram richiede la verifica
# aziendale di Meta (bloccata, manca la documentazione), TikTok e' in
# revisione dal 2026-08-04. Anziche' far provare un accesso che per
# Instagram si inceppa in silenzio (account non tester) o per TikTok si
# collega senza dati (manca video.list), si dichiara subito "in arrivo".
# Togliere una piattaforma da qui appena la sua revisione viene approvata.
COMING_SOON = {"instagram", "tiktok"}


def coming_soon(platform: str) -> bool:
    """"In arrivo" riguarda la *nostra* app in attesa di approvazione. Chi ha
    registrato la propria non sta aspettando nessuno: per lui il collegamento
    e' disponibile subito, ed e' proprio il motivo per cui l'ha registrata."""
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
            # Se nel frattempo l'utente ha annullato (o e' partito un nuovo
            # tentativo), il generation number non combacia piu': questo
            # thread e' ormai orfano e non deve sovrascrivere lo stato.
            if _connect_gen != my_gen:
                return
            if result[0] == "done":
                _connect_state["done"] = True
            else:
                _connect_state["error"] = result[1]
            _connect_state["running"] = False

    threading.Thread(target=worker, daemon=True).start()
    return {"ok": True}
