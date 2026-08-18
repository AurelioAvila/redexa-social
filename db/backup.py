"""
Copie di sicurezza del database dell'utente.

Il database contiene cose che l'utente non puo' ricostruire da solo: gli
account collegati (ogni ripristino significa rifare tutti gli accessi
OAuth), la licenza pagata, le credenziali delle app proprie, lo storico dei
numeri. Perderlo non e' un fastidio, e' la fine dei suoi dati.

Due regole non negoziabili:

  1. Il backup usa l'API di copia di SQLite, non una copia del file. Con WAL
     attivo le ultime transazioni possono trovarsi nel file -wal e non
     ancora nel .db principale: copiare solo il .db le perderebbe, in
     silenzio e proprio nel momento in cui il backup serve di piu'.

  2. I backup stanno accanto ai DATI, non accanto al programma. La cartella
     del programma viene sostituita interamente ad ogni aggiornamento: un
     backup li' dentro sparirebbe esattamente quando serve.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os
import sqlite3
import time

from .connection import connect

# Quanti tenerne. Tre coprono l'errore che ci si accorge subito e quello che
# si scopre due aggiornamenti dopo, senza far crescere la cartella senza fine.
KEEP = 3

PREFIX = "cache-"
SUFFIX = ".db"


def backups_dir(db_path: str) -> str:
    """Sottocartella accanto al database, creata se manca."""
    path = os.path.join(os.path.dirname(os.path.abspath(db_path)), "backups")
    os.makedirs(path, exist_ok=True)
    return path


def create(db_path: str, label: str = "") -> str:
    """Copia coerente del database. Restituisce il percorso del backup.

    label finisce nel nome del file e serve a capire, guardando la cartella,
    perche' quel backup esiste (es. "pre-migration-2", "pre-update-1.4.0").
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = f"-{label}" if label else ""
    dest = os.path.join(backups_dir(db_path), f"{PREFIX}{stamp}{suffix}{SUFFIX}")

    source = connect(db_path)
    try:
        target = sqlite3.connect(dest)
        try:
            # API di copia di SQLite: coerente anche a database in uso e
            # anche con transazioni ancora nel file -wal.
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()

    prune(db_path)
    return dest


def existing(db_path: str) -> list[str]:
    """Backup presenti, dal piu' recente al piu' vecchio."""
    directory = backups_dir(db_path)
    found = [
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.startswith(PREFIX) and name.endswith(SUFFIX)
    ]
    return sorted(found, key=os.path.getmtime, reverse=True)


def prune(db_path: str, keep: int = KEEP) -> list[str]:
    """Elimina i backup oltre i piu' recenti. Restituisce quelli rimossi."""
    removed = []
    for path in existing(db_path)[keep:]:
        try:
            os.remove(path)
            removed.append(path)
        except OSError:
            # Un backup che non si riesce a cancellare (file aperto da un
            # antivirus, permessi) non e' un motivo per far fallire
            # l'operazione che lo ha generato.
            pass
    return removed


def restore(backup_path: str, db_path: str) -> None:
    """Riporta il database allo stato del backup indicato.

    Anche qui si passa dall'API di SQLite invece di sovrascrivere il file:
    se esistono un -wal e uno -shm rimasti indietro, una sovrascrittura
    grezza lascerebbe il database in uno stato incoerente.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(backup_path)

    source = sqlite3.connect(backup_path)
    try:
        target = connect(db_path)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
