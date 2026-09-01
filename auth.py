"""
Registrazione/login locali per la dashboard.

Le password non vengono mai salvate in chiaro: si conserva solo un hash
PBKDF2-HMAC-SHA256 con salt casuale per utente (200k iterazioni), e i
confronti usano compare_digest per non essere vulnerabili a timing attack.
I token di sessione sono casuali a 256 bit e in tabella se ne salva solo
lo SHA-256: chi legge il database non puo' impersonare una sessione attiva.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import datetime
import hashlib
import hmac
import re
import secrets
import sqlite3
import time

import cache
import db

PBKDF2_ITERATIONS = 200_000
SESSION_TTL_SECONDS = 30 * 24 * 3600  # 30 giorni
RESET_CODE_TTL_SECONDS = 15 * 60
RESET_MAX_ATTEMPTS = 5
MIN_PASSWORD_LENGTH = 8
MIN_AGE_YEARS = 13  # soglia minima comune per servizi social (es. GDPR/COPPA)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
BIRTH_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class AuthError(Exception):
    """Errore lato utente (credenziali/validazione) - il chiamante lo mappa
    su un 400/401 invece che su un 500.

    Il messaggio e' un codice, non una frase: l'interfaccia esiste in sei
    lingue e il testo va scritto in quella scelta dall'utente. La traduzione
    vive nel catalogo del frontend."""


def _conn() -> sqlite3.Connection:
    conn = db.connect(cache.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL DEFAULT '',
            password_salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            plan TEXT NOT NULL DEFAULT 'free',
            created_at INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)
    # Un solo codice attivo per email (INSERT OR REPLACE su un nuovo invio):
    # chiederne un secondo invalida il primo, cosi' un vecchio codice
    # rimasto in una casella di posta non resta utilizzabile all'infinito.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            email TEXT PRIMARY KEY,
            code_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Migrazione soft per database creati prima dell'aggiunta di nome/
    # cognome/data di nascita - stesso pattern gia' usato in cache.py per
    # la colonna 'scope' degli insight, cosi' gli account gia' registrati
    # non si rompono quando l'app viene aggiornata.
    cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    for col, ddl in (
        ("first_name", "ALTER TABLE users ADD COLUMN first_name TEXT NOT NULL DEFAULT ''"),
        ("last_name", "ALTER TABLE users ADD COLUMN last_name TEXT NOT NULL DEFAULT ''"),
        ("birth_date", "ALTER TABLE users ADD COLUMN birth_date TEXT"),
    ):
        if col not in cols:
            conn.execute(ddl)
    return conn


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def password_strength(password: str) -> dict:
    """Punteggio 0-4 basato su lunghezza e varieta' di caratteri - usato dal
    frontend per la barra di robustezza. Volutamente semplice e prevedibile:
    non blocca nulla, informa soltanto."""
    if not password:
        return {"score": 0, "label": "vuota"}
    score = 0
    if len(password) >= MIN_PASSWORD_LENGTH:
        score += 1
    if len(password) >= 12:
        score += 1
    classes = sum(bool(re.search(p, password)) for p in (r"[a-z]", r"[A-Z]", r"\d", r"[^\w\s]"))
    if classes >= 3:
        score += 1
    if classes >= 4 and len(password) >= 10:
        score += 1
    labels = ["debole", "debole", "media", "buona", "ottima"]
    return {"score": score, "label": labels[score]}


def _row_to_user(row) -> dict:
    return {
        "id": row[0], "email": row[1], "name": row[2], "plan": row[3], "created_at": row[4],
        "first_name": row[5], "last_name": row[6], "birth_date": row[7],
    }


def _validate_birth_date(birth_date: str) -> str:
    birth_date = (birth_date or "").strip()
    if not BIRTH_DATE_RE.match(birth_date):
        raise AuthError("err_birth_invalid")
    try:
        parsed = datetime.date.fromisoformat(birth_date)
    except ValueError:
        raise AuthError("err_birth_invalid")
    today = datetime.date.today()
    if parsed > today:
        raise AuthError("err_birth_date_future")
    age = today.year - parsed.year - ((today.month, today.day) < (parsed.month, parsed.day))
    if age < MIN_AGE_YEARS:
        raise AuthError("err_birth_too_young")
    if age > 120:
        raise AuthError("err_birth_invalid")
    return birth_date


def register(email: str, password: str, password_confirm: str, first_name: str, last_name: str, birth_date: str) -> dict:
    email = (email or "").strip().lower()
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()

    if not EMAIL_RE.match(email):
        raise AuthError("err_email_invalid")
    if not first_name:
        raise AuthError("err_first_name_required")
    if not last_name:
        raise AuthError("err_last_name_required")
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise AuthError("err_password_short")
    if password != password_confirm:
        raise AuthError("err_password_mismatch")
    birth_date = _validate_birth_date(birth_date)

    salt = secrets.token_bytes(16)
    pw_hash = _hash_password(password, salt)
    full_name = f"{first_name} {last_name}".strip()

    conn = _conn()
    try:
        cur = conn.execute(
            """INSERT INTO users (email, name, first_name, last_name, birth_date, password_salt, password_hash, plan, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'free', ?)""",
            (email, full_name, first_name, last_name, birth_date, salt, pw_hash, int(time.time())),
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise AuthError("err_email_taken")
    finally:
        conn.close()

    return _issue_session(user_id)


def login(email: str, password: str) -> dict:
    email = (email or "").strip().lower()
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT id, password_salt, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    # Anche quando l'utente non esiste si esegue comunque un hash fittizio:
    # cosi' il tempo di risposta non rivela quali email sono registrate.
    if not row:
        _hash_password(password or "", b"\x00" * 16)
        raise AuthError("err_bad_credentials")

    user_id, salt, stored_hash = row
    if not hmac.compare_digest(_hash_password(password or "", salt), stored_hash):
        raise AuthError("err_bad_credentials")

    return _issue_session(user_id)


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def request_password_reset(email: str) -> str | None:
    """Genera un codice a 6 cifre e lo salva con scadenza, solo se l'email
    e' davvero registrata. Il codice va mandato via email dal chiamante -
    qui non si spedisce nulla, cosi' questa funzione resta testabile senza
    rete. Restituisce None se l'email non esiste: il chiamante risponde
    comunque "ok" in entrambi i casi (vedi login sopra per lo stesso motivo:
    non rivelare quali email sono registrate)."""
    email = (email or "").strip().lower()
    conn = _conn()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not row:
            return None
        code = f"{secrets.randbelow(1_000_000):06d}"
        now = int(time.time())
        conn.execute(
            """INSERT INTO password_resets (email, code_hash, created_at, expires_at, attempts)
               VALUES (?, ?, ?, ?, 0)
               ON CONFLICT(email) DO UPDATE SET
                 code_hash = excluded.code_hash, created_at = excluded.created_at,
                 expires_at = excluded.expires_at, attempts = 0""",
            (email, _hash_code(code), now, now + RESET_CODE_TTL_SECONDS),
        )
        conn.commit()
        return code
    finally:
        conn.close()


def reset_password(email: str, code: str, new_password: str, new_password_confirm: str) -> dict:
    email = (email or "").strip().lower()
    if len(new_password or "") < MIN_PASSWORD_LENGTH:
        raise AuthError("err_password_short")
    if new_password != new_password_confirm:
        raise AuthError("err_password_mismatch")

    conn = _conn()
    try:
        row = conn.execute(
            "SELECT code_hash, expires_at, attempts FROM password_resets WHERE email = ?", (email,)
        ).fetchone()
        if not row:
            raise AuthError("err_reset_invalid")
        code_hash, expires_at, attempts = row
        # Troppi tentativi sbagliati sullo stesso codice: si tratta come
        # scaduto invece di continuare a farlo provare a indovinare.
        if attempts >= RESET_MAX_ATTEMPTS:
            raise AuthError("err_reset_too_many")
        if time.time() > expires_at:
            raise AuthError("err_reset_expired")
        if not hmac.compare_digest(_hash_code(code or ""), code_hash):
            conn.execute("UPDATE password_resets SET attempts = attempts + 1 WHERE email = ?", (email,))
            conn.commit()
            raise AuthError("err_reset_invalid")

        user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            raise AuthError("err_reset_invalid")
        salt = secrets.token_bytes(16)
        pw_hash = _hash_password(new_password, salt)
        conn.execute("UPDATE users SET password_salt = ?, password_hash = ? WHERE id = ?", (salt, pw_hash, user[0]))
        # Ogni sessione aperta decade insieme alla vecchia password. Senza
        # questo, un token rubato sopravviveva al reset: cambiare la password
        # non serviva a riprendersi l'account, che e' l'unica ragione per cui
        # si fa un reset.
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user[0],))
        # Il codice e' a uso singolo: resta valido solo per il tentativo che
        # lo ha appena consumato con successo.
        conn.execute("DELETE FROM password_resets WHERE email = ?", (email,))
        conn.commit()
        return _issue_session(user[0])
    finally:
        conn.close()


def _issue_session(user_id: int) -> dict:
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_hash_token(token), user_id, now, now + SESSION_TTL_SECONDS),
        )
        # Pulizia opportunistica delle sessioni gia' scadute, cosi' la tabella
        # non cresce all'infinito senza bisogno di un job dedicato.
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        conn.commit()
        row = conn.execute(
            "SELECT id, email, name, plan, created_at, first_name, last_name, birth_date FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()
    return {"token": token, "user": _row_to_user(row)}


def user_for_token(token: str) -> dict | None:
    if not token:
        return None
    conn = _conn()
    try:
        row = conn.execute(
            """SELECT u.id, u.email, u.name, u.plan, u.created_at, u.first_name, u.last_name, u.birth_date
               FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > ?""",
            (_hash_token(token), int(time.time())),
        ).fetchone()
    finally:
        conn.close()
    return _row_to_user(row) if row else None


def logout(token: str) -> None:
    if not token:
        return
    conn = _conn()
    try:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))
        conn.commit()
    finally:
        conn.close()


def set_plan(user_id: int, plan: str) -> None:
    conn = _conn()
    try:
        conn.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))
        conn.commit()
    finally:
        conn.close()
