"""
Un unico posto dove si aprono connessioni al database.

Prima ogni modulo apriva la sua con sqlite3.connect() e basta, quindi le
impostazioni che contano non erano attive da nessuna parte:

  journal_mode=WAL   Senza, un lettore e uno scrittore contemporanei si
                     bloccano a vicenda. L'app legge dall'interfaccia mentre
                     il thread di aggiornamento scrive: e' esattamente il
                     caso che WAL risolve. E' un'impostazione permanente,
                     scritta nel file una volta sola.

  busy_timeout       Senza, una scrittura che trova il database occupato
                     fallisce subito con "database is locked" invece di
                     aspettare il mezzo secondo che serve.

Questo modulo non importa cache di proposito: il percorso arriva da fuori.
Cosi' resta usabile dall'updater, che gira in un processo separato dove
l'app non e' nemmeno caricata.
"""
import sqlite3

# Quanto aspettare prima di dichiarare il database occupato. Cinque secondi
# sono molto piu' del necessario per le scritture di questa app, e molto
# meno di quanto un utente consideri "bloccato".
BUSY_TIMEOUT_MS = 5000


def connect(db_path: str) -> sqlite3.Connection:
    """Connessione con le impostazioni giuste gia' applicate."""
    conn = sqlite3.connect(db_path, timeout=BUSY_TIMEOUT_MS / 1000)
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    # WAL e' persistente: una volta impostato resta nel file. Riapplicarlo
    # ad ogni connessione non costa nulla e copre i database creati prima.
    # Su filesystem che non lo supportano (alcune condivisioni di rete)
    # SQLite rifiuta il cambio: in quel caso si resta in journal classico,
    # che funziona lo stesso, invece di impedire l'avvio dell'app.
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.DatabaseError:
        pass
    return conn
