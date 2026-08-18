"""
"Usa la tua app": credenziali di un'app Meta o TikTok registrata dal cliente.

Perche' esiste. Instagram e TikTok distinguono due situazioni:

  - un'app che collega account di *altre* persone, e allora pretendono la
    revisione della piattaforma (per Instagram anche la verifica aziendale
    di Meta, che richiede documenti di un'attivita' registrata);
  - un'app che collega l'account di *chi l'ha creata*, e allora non serve
    nessuna revisione: Instagram lo consente in Development mode a chi ha
    un ruolo sull'app, TikTok tramite la Sandbox.

La seconda e' esattamente la situazione del cliente che vuole vedere i
propri numeri. Registrando la sua app in dieci minuti collega il proprio
account subito, senza aspettare l'approvazione della nostra. Non e' un
aggiramento: e' l'uso previsto da entrambe le piattaforme.

Le credenziali restano su questo computer e non passano mai dal proxy: e'
il cliente a custodire il proprio segreto, quindi lo scambio del token
avviene in locale (vedi connections.using_proxy).

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import re
import sqlite3
import time

import cache
import db
import secrets_store

# Piattaforme per cui il cliente puo' registrare un'app propria.
SUPPORTED = ("instagram", "tiktok")

# Controlli di formato sulle credenziali.
#
# Non sono un vezzo: quasi tutti gli errori reali sono copia-incolla
# sbagliati (campi invertiti, incollato a meta', spazi invisibili presi
# insieme al valore). Accorgersene qui produce un messaggio preciso subito,
# invece di un login che fallisce dopo tre schermate senza spiegare perche'.
# Volutamente larghi: devono scartare l'errore evidente, non indovinare il
# formato futuro delle piattaforme.
FORMATS = {
    "instagram": {
        "client_id": (r"^\d{10,25}$", "ownapp_bad_ig_id"),
        "client_secret": (r"^[A-Za-z0-9]{20,64}$", "ownapp_bad_ig_secret"),
    },
    "tiktok": {
        # Il prefisso "sbaw" e' quello delle chiavi Sandbox, ed e' il caso
        # normale qui: e' la Sandbox a permettere di leggere i propri dati
        # senza App Review. Accettare solo "aw" avrebbe respinto proprio le
        # credenziali che questo flusso e' fatto per usare.
        "client_id": (r"^(sb)?aw[A-Za-z0-9]{8,30}$", "ownapp_bad_tt_key"),
        "client_secret": (r"^[A-Za-z0-9]{20,80}$", "ownapp_bad_tt_secret"),
    },
}


def _conn() -> sqlite3.Connection:
    conn = db.connect(cache.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS own_apps (
            platform TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    return conn


def get(platform: str) -> dict | None:
    """Credenziali salvate per questa piattaforma, se ce ne sono."""
    if platform not in SUPPORTED:
        return None
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT client_id, client_secret, created_at FROM own_apps WHERE platform = ?",
            (platform,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None

    import logging

    import secrets_store

    try:
        segreto = secrets_store.unprotect(row[1])
    except secrets_store.SecretUnavailable:
        # Database arrivato da un altro computer o account Windows: le
        # credenziali ci sono ma non sono utilizzabili qui. Meglio dire
        # "non configurata" e far rifare la procedura guidata, che passare
        # un segreto illeggibile alla piattaforma e farsi rifiutare il login
        # con un errore incomprensibile.
        logging.warning("Credenziali dell'app %s non decifrabili su questo "
                        "account Windows: vanno reinserite", platform)
        return None

    return {"client_id": row[0], "client_secret": segreto, "created_at": row[2]}


def configured(platform: str) -> bool:
    return get(platform) is not None


def redirect_uri(platform: str) -> str:
    """L'indirizzo di ritorno che il cliente deve registrare nella propria
    app. E' lo stesso della nostra: una pagina statica su GitHub Pages che
    esiste gia', cosi' non deve pubblicare nessun sito."""
    import brand
    return brand.get("INSTAGRAM_REDIRECT_URI" if platform == "instagram" else "TIKTOK_REDIRECT_URI")


def check_format(platform: str, client_id: str, client_secret: str) -> str | None:
    """Codice dell'errore di formato, oppure None se i valori sono plausibili."""
    rules = FORMATS.get(platform)
    if not rules:
        return "ownapp_unsupported"
    values = {"client_id": client_id, "client_secret": client_secret}
    for field, (pattern, code) in rules.items():
        if not re.match(pattern, values[field] or ""):
            return code
    return None


def _verify_tiktok(key: str, secret: str) -> str | None:
    """Chiede a TikTok se la coppia esiste davvero.

    TikTok rilascia un token "client_credentials" alle sole app valide, ed
    e' una chiamata senza effetti collaterali: costa nulla e trasforma un
    errore che sarebbe emerso a login gia' iniziato in un messaggio chiaro
    mentre il cliente ha ancora la pagina delle credenziali aperta.

    Un problema di rete non deve bloccare il salvataggio: in quel caso non
    si dichiara nulla e sara' il collegamento vero a dire come e' andata.
    """
    import requests
    try:
        resp = requests.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"client_key": key, "client_secret": secret,
                  "grant_type": "client_credentials"},
            timeout=15,
        )
    except Exception:
        return None
    if resp.ok and "access_token" in resp.json():
        return None
    print(f"[own-app] tiktok rejected credentials: {resp.text[:200]}")
    return "ownapp_tt_refused"


def save(platform: str, client_id: str, client_secret: str) -> dict:
    """Valida e memorizza. Restituisce {"ok": True} o un codice di errore."""
    if platform not in SUPPORTED:
        return {"ok": False, "message": "ownapp_unsupported"}

    client_id = (client_id or "").strip()
    client_secret = (client_secret or "").strip()
    if not client_id or not client_secret:
        return {"ok": False, "message": "ownapp_missing"}

    bad = check_format(platform, client_id, client_secret)
    if bad:
        return {"ok": False, "message": bad}

    if platform == "tiktok":
        refused = _verify_tiktok(client_id, client_secret)
        if refused:
            return {"ok": False, "message": refused}

    conn = _conn()
    try:
        conn.execute(
            """INSERT INTO own_apps (platform, client_id, client_secret, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(platform) DO UPDATE SET
                 client_id = excluded.client_id,
                 client_secret = excluded.client_secret,
                 created_at = excluded.created_at""",
            (platform, client_id, secrets_store.protect(client_secret), int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


def clear(platform: str) -> dict:
    conn = _conn()
    try:
        conn.execute("DELETE FROM own_apps WHERE platform = ?", (platform,))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


def status(platform: str) -> dict:
    """Cosa mostrare nell'interfaccia. Il segreto non esce mai di qui: del
    client id basta la coda per far riconoscere al cliente quale app ha
    collegato senza esporre altro."""
    saved = get(platform)
    return {
        "platform": platform,
        "supported": platform in SUPPORTED,
        "configured": bool(saved),
        "client_id_hint": ("…" + saved["client_id"][-4:]) if saved else "",
        "redirect_uri": redirect_uri(platform),
    }
