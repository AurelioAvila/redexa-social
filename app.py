"""
Server locale dell'applicazione: espone le API che l'interfaccia consuma e
tiene insieme raccolta dati, analisi, diagnostica, licenze e aggiornamenti.

Ascolta solo su 127.0.0.1 e non e' un servizio web: nasce e muore con la
finestra dell'app. Le difese contro CSRF e DNS rebinding sono comunque
necessarie e sono spiegate poco piu' sotto, dove sono implementate.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os
import sys
import threading
import time
import webbrowser

from dotenv import load_dotenv

# In un .exe compilato (PyInstaller) i file bundlati finiscono in una cartella
# temporanea (_MEIPASS) che sparisce ad ogni riavvio - .env e il database
# devono invece restare accanto all'eseguibile vero, altrimenti si perde la
# configurazione e lo storico ad ogni apertura.
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

app = FastAPI(title="Social Stats Dashboard")


# ------------------------------------------------- difesa del server locale
#
# Il server ascolta su 127.0.0.1, ma "solo locale" non vuol dire "solo la
# nostra finestra": qualsiasi pagina web aperta nel browser mentre l'app gira
# puo' parlare con questa porta. Due attacchi reali, verificati entrambi
# prima di scrivere questa difesa:
#
#   1. CSRF. Una POST senza corpo JSON e' una "richiesta semplice": il
#      browser la manda cross-origin senza chiedere permesso al server.
#      Bastava una pagina malevola aperta in un'altra scheda per svuotare
#      lo storico (/api/cache/clear) o togliere la licenza attivata
#      (/api/license/remove). La risposta l'attaccante non la legge, ma il
#      danno e' gia' fatto.
#
#   2. DNS rebinding. L'header Host non veniva controllato: un dominio che
#      dopo qualche secondo punta a 127.0.0.1 diventa "stessa origine" per
#      il browser, e da li' si leggono le risposte - cioe' le statistiche
#      private del cliente.
#
# Il controllo sull'Origin scatta solo sui metodi che cambiano qualcosa, e
# solo quando l'header c'e': un browser lo manda sempre in una POST
# cross-origin, mentre una richiesta locale legittima (la finestra dell'app,
# uno script dell'utente) o non lo manda o lo manda uguale al nostro.
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _host_only(value: str) -> str:
    """Nome host senza porta. Gli indirizzi IPv6 arrivano fra parentesi
    quadre ("[::1]:8787"), quindi non basta tagliare sull'ultimo due punti."""
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

# Le piattaforme attive dipendono dalla modalita' (personale o cliente):
# i moduli personali come CertSprint non esistono nella build distribuita.
PLATFORM_NAMES = config.enabled_platforms()
_module_cache = {}


def _get_module(name: str):
    """Import pigro: le librerie delle singole piattaforme (in particolare
    google-api-python-client per YouTube) sono pesanti da caricare - farlo
    solo quando serve davvero (al primo refresh) invece che all'avvio
    dell'app taglia parecchio il tempo di apertura della finestra.

    NB: import statici dentro funzioni (non importlib con stringa dinamica)
    - PyInstaller analizza l'AST e li rileva comunque per bundlarli, mentre
    un importlib.import_module(f"...") gli resta invisibile e il modulo
    finisce per mancare nell'eseguibile compilato."""
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
    """Dati piu' recenti gia' salvati - nessuna chiamata esterna, per un
    caricamento istantaneo e a costo zero ogni volta che si apre l'app.

    Storico e fasce orarie consigliate sono funzioni Pro: vengono tolte dalla
    risposta, non solo nascoste dall'interfaccia."""
    import insights
    import plans

    plan = _current_plan(authorization)
    out = {}
    for platform in PLATFORM_NAMES:
        out[platform] = cache.latest_snapshot(platform)
    # Le osservazioni sono aritmetica sui dati gia' in memoria: costano
    # nulla, quindi arrivano insieme allo snapshot invece di dietro a un
    # pulsante che l'utente deve sapere di dover premere.
    out["insights"] = {p: insights.generate_insights(out, platform=p) for p in PLATFORM_NAMES}
    # L'analisi va calcolata prima: la diagnostica la usa per i controlli di
    # strategia (engagement contro i valori di settore, risonanza, squilibrio
    # fra piattaforme) invece di limitarsi a dire se le API rispondono.
    out["analytics"] = analytics.compute_analytics(out)
    out["diagnostics"] = diagnostics.run_diagnostics(out, out["analytics"])
    out["trends"] = trends.compute_trends() if plans.allows(plan, "history") else {}
    if not plans.allows(plan, "best_hours"):
        out["analytics"]["best_hours"] = []
        out["analytics"]["hours_locked"] = True

    fetch_times = [out[p]["fetched_at"] for p in PLATFORM_NAMES if out.get(p) and out[p].get("fetched_at")]
    out["analytics"]["last_refresh_at"] = max(fetch_times) if fetch_times else None
    out["entitlements"] = plans.public_entitlements(plan)
    return out


def _on_unit_done():
    # `+= 1` su un valore condiviso e' una read-modify-write, non
    # un'operazione atomica: con piu' thread di refresh in parallelo due
    # incrementi possono sovrapporsi e perdersi, facendo fermare la barra
    # sotto il 100%. Serve il lock esplicito.
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
    """Tutte le piattaforme in parallelo (non una alla volta) - il tempo
    totale resta quello della piu' lenta, non la somma di tutte. Il
    progresso e' granulare per singola unita' di lavoro (un canale YouTube,
    un account Instagram, un controllo CertSprint, ...) invece che per
    piattaforma intera, cosi' la barra avanza in modo continuo invece di
    stare ferma su 5 grandi blocchi."""
    threads = [threading.Thread(target=_refresh_one, args=(name,)) for name in PLATFORM_NAMES]
    for t in threads:
        t.start()
        # Piccolo sfasamento tra l'avvio di una piattaforma e la successiva -
        # evita che tutte le richieste OAuth/HTTP partano nello stesso istante
        # esatto, riducendo la probabilita' di errori intermittenti osservati
        # lato server (es. invalid_scope spurio) quando piu' token endpoint
        # vengono colpiti in un burst perfettamente simultaneo.
        time.sleep(0.4)
    for t in threads:
        t.join()
    _refresh_state["running"] = False


@app.post("/api/refresh")
def refresh_all():
    """Avvia il refresh in background e ritorna subito - il progresso reale
    si legge da /api/refresh/status, cosi' la barra di caricamento riflette
    il lavoro vero invece di una stima finta."""
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
    """Analisi della piattaforma calcolata dal codice: istantanea e gratuita,
    quindi non serve piu' ne' cache ne' un pulsante che la chieda - viene
    gia' inclusa in /api/snapshot. L'endpoint resta per compatibilita'."""
    if platform not in PLATFORM_NAMES:
        raise HTTPException(404, f"Unknown platform: {platform}")

    import insights
    snap = cache.latest_snapshot(platform)
    return {"generated_at": int(time.time()), "items": insights.generate_insights({platform: snap}, platform=platform)}


# ---------------------------------------------------------------- config

@app.get("/api/config")
def get_config():
    """Il frontend usa questo per sapere quali sezioni mostrare, invece di
    avere l'elenco delle piattaforme scritto a mano in due posti diversi."""
    return config.public_config()


@app.get("/api/version")
def get_version():
    """Non scarica ne' installa nulla: dice solo se su GitHub c'e' una
    release piu' recente di questa, cosi' il frontend puo' mostrare un
    avviso con il link alla pagina di download."""
    import version
    return version.status()


@app.get("/api/update/check")
def update_check(force: bool = False):
    """C'e' un aggiornamento? Non scarica e non installa niente.

    Se questa copia e' gestita da winget, risponde dicendolo: due
    meccanismi che sostituiscono gli stessi file lascerebbero
    l'installazione in uno stato che nessuno dei due sa piu' riparare.
    """
    from updater import runner

    return runner.check(force=force)


@app.post("/api/update/install")
def update_install():
    """Scarica, verifica firma e impronta, salva il database e avvia il
    processo che sostituisce i file.

    Ritorna subito: da qui in poi e' l'updater esterno a comandare, e
    l'applicazione viene chiusa da lui.
    """
    from updater import runner

    try:
        preparato = runner.prepare()
        return runner.apply(preparato)
    except runner.UpdateError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/update/postpone")
def update_postpone(payload: dict = Body(default={})):
    """"Ricordamelo piu' tardi" oppure "salta questa versione".

    Saltare vale solo per gli aggiornamenti non critici: uno obbligatorio
    torna a proporsi comunque.
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
    """Passaggio volontario al canale di prova: chi non lo sceglie non vede
    mai una versione beta."""
    from updater import runner

    try:
        runner.set_channel(str(payload.get("channel", "")))
    except runner.UpdateError as exc:
        raise HTTPException(400, str(exc))
    return {"ok": True, "channel": runner.channel()}


@app.post("/api/cache/clear")
def clear_cache():
    """Svuota tutto cio' che si ricalcola da solo con un refresh (statistiche,
    osservazioni, cache di diagnostica). Non tocca connessioni, licenza ne'
    le app registrate dal cliente: sono configurazione, non cache, e un
    pulsante "pulisci" non deve poterle cancellare per sbaglio."""
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
        # Motivo per ogni piattaforma non collegabile: credenziali assenti
        # nella build oppure limite della piattaforma stessa.
        "unavailable": {p: r for p, r in reasons.items() if r},
        "connectable": list(connections.CONNECTORS.keys()),
        "guided": list(connections.GUIDED.keys()),
        # Come si collega ciascuna: "oneclick" (basta il bottone),
        # "guided" (serve un incolla), "unavailable".
        "modes": {p: connections.connect_mode(p) for p in platforms},
        # Piattaforme per cui il cliente puo' registrare un'app propria e
        # collegarsi senza attendere la nostra revisione, con lo stato di
        # quelle gia' configurate.
        "own_app": {p: own_app.status(p) for p in own_app.SUPPORTED},
    }


@app.post("/api/connections/connect/{platform}")
def connect_platform(platform: str, authorization: str | None = Header(default=None)):
    """Avvia il login OAuth: apre il browser sulla pagina della piattaforma
    e attende il ritorno su 127.0.0.1. Torna subito, il progresso si legge
    da /api/connections/status.

    Il numero di account collegabili dipende dal piano, e il controllo sta
    qui: nasconderlo solo nell'interfaccia non sarebbe un limite."""
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


@app.post("/api/connections/cancel")
def connect_cancel():
    """Sblocca un collegamento rimasto appeso (finestra chiusa, login mai
    completato) senza dover aspettare la scadenza o riavviare l'app."""
    import connections
    return connections.cancel_connect()


@app.get("/api/connections/authorize/{platform}")
def connection_authorize_url(platform: str):
    """URL da aprire per autorizzare Instagram/TikTok: non accettano un
    redirect su 127.0.0.1, quindi il ritorno va incollato a mano una volta."""
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


# --------------------------------------------------- "usa la tua app"
# Instagram e TikTok aprono l'accesso senza revisione a chi collega il
# proprio account tramite un'app registrata da se'. Vedi own_app.py.

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
    """Torna alla nostra app. Le connessioni gia' create restano: sono state
    autorizzate con le credenziali del cliente e continuano a funzionare
    finche' non le scollega lui."""
    import own_app
    return own_app.clear(platform)


# ---------------------------------------------------------------- account

def _token_from_header(authorization: str | None) -> str:
    if not authorization:
        return ""
    parts = authorization.split(None, 1)
    return parts[1].strip() if len(parts) == 2 and parts[0].lower() == "bearer" else ""


def _current_plan(authorization: str | None) -> str:
    """Piano valido per questa richiesta.

    La fonte e' la licenza verificata online: il piano non puo' dipendere da
    un database che sta sul computer di chi deve pagare. Il campo `plan`
    dell'utente resta come scorciatoia amministrativa (account interni), e
    fra i due vince il piu' generoso - cosi' una licenza attiva funziona
    anche senza aver effettuato l'accesso."""
    import auth
    import licensing
    import plans

    user = auth.user_for_token(_token_from_header(authorization))
    account_plan = plans.normalize(user.get("plan") if user else None)
    license_plan = licensing.current_plan()

    rank = {plans.FREE: 0, plans.PRO: 1, plans.STUDIO: 2}
    return account_plan if rank.get(account_plan, 0) >= rank.get(license_plan, 0) else license_plan


@app.post("/api/auth/register")
def auth_register(request: Request, payload: dict = Body(...)):
    import auth
    import rate_limit
    rate_limit.enforce(f"register:{request.client.host}", max_attempts=5, window_seconds=3600)
    try:
        return auth.register(
            payload.get("email", ""),
            payload.get("password", ""),
            payload.get("password_confirm", ""),
            payload.get("first_name", ""),
            payload.get("last_name", ""),
            payload.get("birth_date", ""),
        )
    except auth.AuthError as exc:
        raise HTTPException(400, str(exc))


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
    """Valutazione della robustezza calcolata lato server per restare
    coerente con le regole di registrazione, senza mai salvare nulla."""
    import auth
    return auth.password_strength(payload.get("password", ""))


# ---------------------------------------------------------------- pagamenti

@app.get("/api/billing/plans")
def billing_plans():
    import billing
    return billing.list_plans()


@app.post("/api/billing/checkout")
def billing_checkout(payload: dict = Body(...), authorization: str | None = Header(default=None)):
    """Apre il pagamento. Ne' i dati della carta ne' la chiave segreta di
    Stripe passano da qui: la sessione la crea il servizio, che e' anche
    l'unico a poter stabilire chi ha pagato."""
    import auth
    import billing

    user = auth.user_for_token(_token_from_header(authorization))
    return billing.start_checkout(
        payload.get("plan_id", ""),
        payload.get("billing_cycle", "monthly"),
        user["email"] if user else "",
    )


# ---------------------------------------------------------------- licenze

@app.on_event("startup")
def _migrate_database_on_start():
    """Porta lo schema del database all'ultima versione, prima che qualsiasi
    altra cosa lo tocchi.

    Non e' in un thread di proposito: deve finire prima che le rotte
    comincino a leggere e scrivere. E' quasi sempre istantaneo (quando non
    c'e' niente da migrare non fa nulla), e se fallisce il database viene
    riportato com'era da solo.

    Un fallimento qui non impedisce l'avvio: l'app parte comunque con lo
    schema precedente, che e' comunque funzionante, invece di lasciare
    l'utente davanti a una finestra che non si apre.
    """
    import logging

    import cache
    import db

    try:
        esito = db.ensure_current(cache.DB_PATH)
        if esito["applied"]:
            logging.info("database migrato: %s -> %s (%s)",
                         esito["from"], esito["to"], ", ".join(esito["applied"]))
    except Exception:
        logging.exception("database migration failed; continuing with the previous schema")


@app.on_event("startup")
def _license_recheck_on_start():
    """Ricontrolla la licenza in sottofondo a ogni avvio, cosi' una revoca
    (rimborso, abbonamento disdetto) ha effetto entro un giorno. In un thread
    separato: se il servizio e' lento, la finestra si apre lo stesso."""
    import licensing

    threading.Thread(target=licensing.refresh_if_due, daemon=True).start()


@app.get("/api/license")
def license_status():
    import licensing
    return licensing.status()


@app.post("/api/license/activate")
def license_activate(payload: dict = Body(...)):
    """Attiva la chiave ricevuta dopo il pagamento."""
    import licensing
    return licensing.activate(payload.get("key", ""))


@app.post("/api/license/remove")
def license_remove():
    """Stacca la licenza da questa installazione, per spostarla su un altro
    computer senza doverne chiedere una nuova."""
    import licensing
    licensing.clear()
    return {"ok": True}


@app.post("/api/license/portal")
def license_portal():
    """URL del portale clienti Stripe, dove l'abbonamento si disdice
    davvero (non solo si stacca da questo computer). Apribile nel browser
    di sistema, non nella webview dell'app: e' Stripe che deve autenticare
    il cliente, non noi."""
    import licensing
    result = licensing.billing_portal_url()
    if not result.get("ok"):
        raise HTTPException(400, result.get("code", "license_service_unavailable"))
    return result


# ---------------------------------------------------------------- export

@app.get("/api/export.csv", response_class=PlainTextResponse)
def export_csv(authorization: str | None = Header(default=None)):
    """Esporta i dati dell'ultimo snapshot in CSV, per aprirli in Excel o
    incrociarli con altri fogli senza doverli ricopiare a mano.

    Funzione Pro: il controllo e' qui, non solo sul pulsante."""
    import csv
    import io

    import plans

    if not plans.allows(_current_plan(authorization), "csv_export"):
        raise HTTPException(403, "plan_feature_locked")

    buf = io.StringIO()
    writer = csv.writer(buf)
    # Il CSV lo apre il cliente in Excel: le intestazioni sono testo
    # visibile, non nomi interni, e vanno nella lingua del prodotto.
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
    """L'app gira sempre dallo stesso host:porta anche dopo un aggiornamento,
    quindi il browser incorporato puo' continuare a servire una versione
    vecchia di style.css/app.js dalla propria cache locale invece di
    ricontrollarla - un rebuild non basterebbe a far vedere le modifiche.
    No-cache forza una richiesta condizionale ad ogni avvio: costa
    pochissimo (file piccoli, tutto in locale) e garantisce che l'interfaccia
    mostrata sia sempre quella dell'ultima build installata."""

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
