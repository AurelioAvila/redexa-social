"""
Storage locale (SQLite) dell'ultimo snapshot per piattaforma + storico per
i grafici trend. Nessuna chiamata di rete qui: solo lettura/scrittura
locale, cosi' riaprire l'app non genera traffico ne' costo.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import os
import sqlite3
import sys
import time
import db

# cache.db contiene le connessioni account dell'utente (YouTube/Instagram/
# TikTok): deve sopravvivere a reinstallazioni e rebuild dell'exe, quindi non
# puo' stare accanto all'eseguibile (quella cartella viene ricreata da zero
# a ogni build/installer, cancellando tutto). Va in una cartella utente
# stabile fuori dalla cartella dell'app.
if getattr(sys, "frozen", False):
    DATA_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "SocialDashboard")
    os.makedirs(DATA_DIR, exist_ok=True)
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATA_DIR, "cache.db")

# Migrazione una tantum: se un'installazione precedente aveva il db accanto
# all'exe, spostalo nella nuova posizione stabile invece di perdere i dati.
if getattr(sys, "frozen", False) and not os.path.exists(DB_PATH):
    _legacy_path = os.path.join(os.path.dirname(sys.executable), "cache.db")
    if os.path.exists(_legacy_path):
        import shutil
        shutil.move(_legacy_path, DB_PATH)


def _conn():
    conn = db.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            platform TEXT,
            fetched_at INTEGER,
            data TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL DEFAULT 'all',
            generated_at INTEGER,
            based_on_fetch_at INTEGER,
            text TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kv_cache (
            key TEXT PRIMARY KEY,
            saved_at INTEGER,
            data TEXT
        )
    """)
    # migrazione soft per db creati prima dell'aggiunta della colonna scope
    cols = [r[1] for r in conn.execute("PRAGMA table_info(insights)").fetchall()]
    if "scope" not in cols:
        conn.execute("ALTER TABLE insights ADD COLUMN scope TEXT NOT NULL DEFAULT 'all'")
    return conn


def _leggi_json(grezzo: str, contesto: str) -> dict | None:
    """Legge una riga salvata da noi, senza far morire l'app se e' rovinata.

    Sono dati che scrive l'applicazione stessa, quindi normalmente sono
    validi. Ma una scrittura interrotta a meta' (mancanza di corrente,
    errore del disco) lascerebbe una riga illeggibile, e senza questo
    l'eccezione risalirebbe fino alla pagina principale: la dashboard
    resterebbe rotta ad ogni apertura, senza che l'utente possa capire
    perche' ne' rimediare.

    Saltare il dato guasto significa al massimo un numero mancante, che il
    prossimo Aggiorna rimette a posto.
    """
    import logging

    try:
        return json.loads(grezzo)
    except (ValueError, TypeError):
        logging.warning("stored data is unreadable (%s); ignoring it until "
                        "the next refresh", contesto)
        return None


def kv_set(key: str, data: dict) -> None:
    """Cache generica chiave/valore su disco (usata es. da certsprint.py per
    npm audit/eslint) - sopravvive al riavvio dell'app, a differenza di un
    semplice dict in memoria che si azzera ad ogni apertura."""
    conn = _conn()
    try:
        conn.execute("INSERT OR REPLACE INTO kv_cache (key, saved_at, data) VALUES (?, ?, ?)",
                     (key, int(time.time()), json.dumps(data)))
        conn.commit()
    finally:
        conn.close()


def kv_get(key: str, max_age_seconds: int) -> dict | None:
    conn = _conn()
    try:
        row = conn.execute("SELECT saved_at, data FROM kv_cache WHERE key = ?", (key,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    saved_at, data = row
    if time.time() - saved_at > max_age_seconds:
        return None
    return _leggi_json(data, contesto=f"kv_cache[{key}]")


def save_snapshot(platform: str, data: dict) -> None:
    conn = _conn()
    try:
        conn.execute("INSERT INTO snapshots (platform, fetched_at, data) VALUES (?, ?, ?)",
                     (platform, int(time.time()), json.dumps(data)))
        conn.commit()
    finally:
        conn.close()


def latest_snapshot(platform: str) -> dict | None:
    conn = _conn()
    try:
        # rowid come spareggio: fetched_at ha risoluzione al secondo, quindi
        # due salvataggi ravvicinati (due click su Aggiorna) finiscono a pari
        # merito e senza questo SQLite restituiva il piu' VECCHIO dei due -
        # i numeri sembravano tornare indietro dopo un aggiornamento.
        row = conn.execute(
            "SELECT fetched_at, data FROM snapshots WHERE platform = ?"
            " ORDER BY fetched_at DESC, rowid DESC LIMIT 1",
            (platform,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    dati = _leggi_json(row[1], contesto=f"snapshot {platform}")
    if dati is None:
        return None
    return {"fetched_at": row[0], **dati}


def device_id() -> str:
    """Identificativo anonimo e permanente di questa installazione, usato
    solo per contare quanti dispositivi diversi stanno usando la stessa
    chiave di licenza. Vive in una tabella propria, non in kv_cache: deve
    sopravvivere a "Clear cached data", altrimenti ogni pulizia farebbe
    sembrare l'installazione un dispositivo nuovo agli occhi del Worker,
    consumando un'attivazione in piu' per niente."""
    import secrets

    conn = _conn()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS device (id TEXT PRIMARY KEY)")
        row = conn.execute("SELECT id FROM device LIMIT 1").fetchone()
        if row:
            return row[0]
        new_id = secrets.token_hex(16)
        conn.execute("INSERT INTO device (id) VALUES (?)", (new_id,))
        conn.commit()
        return new_id
    finally:
        conn.close()


def clear_snapshot(platform: str) -> None:
    """Cancella tutto lo storico salvato di una piattaforma - non solo
    l'ultimo snapshot. Serve quando non resta piu' nessun account collegato:
    senza questo, Overview continuerebbe a mostrare i numeri dell'ultimo
    account scollegato finche' l'utente non preme Refresh a mano, il che
    sembra un dato reale invece che una cache mai svuotata."""
    conn = _conn()
    try:
        conn.execute("DELETE FROM snapshots WHERE platform = ?", (platform,))
        conn.commit()
    finally:
        conn.close()


def clear_all() -> None:
    """Svuota tutto cio' che e' ricalcolabile con un refresh: snapshot,
    osservazioni, cache generica. Non tocca connessioni, licenza o le app
    proprie del cliente - quelle sono configurazione, non cache, e cancellarle
    per sbaglio da un pulsante "pulisci cache" sarebbe una sorpresa brutta."""
    conn = _conn()
    try:
        conn.execute("DELETE FROM snapshots")
        conn.execute("DELETE FROM insights")
        conn.execute("DELETE FROM kv_cache")
        conn.commit()
    finally:
        conn.close()


def history(platform: str, limit: int = 30) -> list[dict]:
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT fetched_at, data FROM snapshots WHERE platform = ?"
            " ORDER BY fetched_at DESC, rowid DESC LIMIT ?",
            (platform, limit),
        ).fetchall()
    finally:
        conn.close()
    storico = []
    for r in reversed(rows):
        dati = _leggi_json(r[1], contesto=f"storico {platform}")
        if dati is not None:
            storico.append({"fetched_at": r[0], **dati})
    return storico


def save_insight(text: str, based_on_fetch_at: int, scope: str = "all") -> None:
    conn = _conn()
    try:
        conn.execute("INSERT INTO insights (scope, generated_at, based_on_fetch_at, text) VALUES (?, ?, ?, ?)",
                     (scope, int(time.time()), based_on_fetch_at, text))
        conn.commit()
    finally:
        conn.close()


def latest_insight(scope: str = "all") -> dict | None:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT generated_at, based_on_fetch_at, text FROM insights WHERE scope = ?"
            " ORDER BY generated_at DESC, rowid DESC LIMIT 1",
            (scope,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {"generated_at": row[0], "based_on_fetch_at": row[1], "text": row[2]}
