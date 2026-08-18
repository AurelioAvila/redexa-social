"""
Controllo da eseguire PRIMA di distribuire una build.

Verifica due cose che, se sbagliate, non si notano finche' non e' troppo
tardi: che nell'eseguibile non finiscano credenziali confidenziali, e che il
proxy di scambio token sia configurato.

    python check_release.py            # controlla la configurazione
    python check_release.py --dist     # controlla anche il binario compilato

Esce con codice 1 se qualcosa non va, cosi' puo' essere messo in una
pipeline e bloccare una distribuzione sbagliata.
"""
import os
import sys
import zlib

# Il secret di Google e' escluso apposta: per le "installed app" Google lo
# documenta come non confidenziale. Questi due invece lo sono davvero.
CONFIDENTIAL = ("INSTAGRAM_APP_SECRET", "TIKTOK_CLIENT_SECRET")

DIST_EXE = os.path.join("dist", "Social Dashboard", "Social Dashboard.exe")


def check_config() -> list[str]:
    problems = []
    try:
        import brand
    except Exception as exc:
        return [f"brand.py non importabile: {exc}"]

    proxy = (brand.get("OAUTH_PROXY_URL") or "").strip()
    embedded = [name for name in CONFIDENTIAL if (brand.get(name) or "").strip()]

    if not proxy:
        problems.append(
            "OAUTH_PROXY_URL non configurato: senza proxy i client secret "
            "vengono compilati nell'eseguibile e sono leggibili da chiunque "
            "lo scarichi (vedi oauth-proxy/README.md)."
        )
    if embedded:
        problems.append(
            "Credenziali confidenziali presenti in brand.py e destinate a "
            "finire nella build: " + ", ".join(embedded) + ". Con il proxy "
            "attivo vanno svuotate."
        )
    return problems


def _decompressed_blobs(data: bytes):
    """Ricostruisce i blocchi zlib dentro il binario: e' quello che farebbe
    chi vuole estrarre le stringhe da un eseguibile PyInstaller."""
    i = 0
    while i < len(data) - 1:
        if data[i] == 0x78:
            try:
                yield zlib.decompressobj().decompress(data[i:i + 400_000])
            except Exception:
                pass
        i += 1


def check_binary() -> list[str]:
    if not os.path.exists(DIST_EXE):
        return [f"Eseguibile non trovato ({DIST_EXE}): compila prima di controllare."]

    try:
        import brand
    except Exception:
        return ["brand.py non importabile: impossibile sapere cosa cercare."]

    wanted = {}
    for name in CONFIDENTIAL:
        value = (brand.get(name) or "").strip()
        if value:
            wanted[name] = value.encode()
    if not wanted:
        return []

    blob = open(DIST_EXE, "rb").read()
    found = set()
    for chunk in _decompressed_blobs(blob):
        for name, needle in wanted.items():
            if needle in chunk:
                found.add(name)
        if len(found) == len(wanted):
            break

    return [
        f"{name} e' estraibile dall'eseguibile distribuito."
        for name in sorted(found)
    ]


def _version_reminder() -> None:
    """Il controllo aggiornamenti (version.py) confronta APP_VERSION con
    l'ultimo tag pubblicato su GitHub: se questa build ha lo stesso numero
    della release gia' pubblicata, ogni cliente gia' aggiornato vedrebbe
    "aggiornamento disponibile" all'infinito. Non blocca (un tag locale non
    ancora pushato e' normale), ma lo ricorda ad ogni controllo."""
    try:
        import subprocess
        import version
        tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
        current_tag = tag.lstrip("vV")
        if current_tag and current_tag == version.APP_VERSION:
            print(f"Promemoria: APP_VERSION ({version.APP_VERSION}) e' uguale "
                  f"all'ultimo tag git ({tag}). Se questa e' una nuova release, "
                  "alza APP_VERSION in version.py prima di pubblicarla.")
    except Exception:
        pass  # git assente o nessun tag: nessun promemoria, non e' un errore


def main() -> int:
    problems = check_config()
    if "--dist" in sys.argv:
        problems += check_binary()

    _version_reminder()

    if problems:
        print("Controllo NON superato:\n")
        for p in problems:
            print(f"  - {p}")
        print("\nNon distribuire questa build finche' i punti sopra non sono risolti.")
        return 1

    print("Controllo superato: nessuna credenziale confidenziale nella build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
