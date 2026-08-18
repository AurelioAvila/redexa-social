"""
Deploy del servizio (proxy OAuth + licenze) in un colpo solo.

Fa tutto quello che serve dopo `wrangler login`: pubblica il Worker, ci
carica i segreti leggendoli da brand.py, scrive l'URL in brand.py e svuota
i due client secret confidenziali dalla build.

    wrangler login          # una volta sola, autentica il TUO account
    python deploy_proxy.py

Al termine `python check_release.py` deve dire che la build e' pulita.

I segreti passano allo stdin di wrangler, non sulla riga di comando: cosi'
non finiscono nella cronologia della shell ne' nell'elenco dei processi.

Le chiavi di Stripe non stanno in brand.py (non devono nemmeno sfiorare il
repository o la build): si caricano a parte, una volta sola, con

    python deploy_proxy.py --stripe

Stessa cosa per la chiave di Resend (manda l'email con la chiave di
licenza):

    python deploy_proxy.py --resend
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROXY_DIR = ROOT / "oauth-proxy"
BRAND = ROOT / "brand.py"

# Nome in brand.py -> nome del segreto sul Worker.
SECRETS = {
    "INSTAGRAM_APP_ID": "INSTAGRAM_APP_ID",
    "INSTAGRAM_APP_SECRET": "INSTAGRAM_APP_SECRET",
    "TIKTOK_CLIENT_KEY": "TIKTOK_CLIENT_KEY",
    "TIKTOK_CLIENT_SECRET": "TIKTOK_CLIENT_SECRET",
}

# Solo questi vanno svuotati da brand.py: il secret di Google resta, per le
# "installed app" Google lo documenta come non confidenziale.
TO_CLEAR = ("INSTAGRAM_APP_SECRET", "TIKTOK_CLIENT_SECRET")


def run(args, **kw):
    # encoding esplicito: wrangler stampa emoji, e con la codepage di default
    # di Windows la lettura dell'output fallirebbe.
    return subprocess.run(args, cwd=PROXY_DIR, text=True, capture_output=True,
                          encoding="utf-8", errors="replace", **kw)


def check_login() -> bool:
    out = run(["npx", "wrangler", "whoami"], shell=True)
    combined = (out.stdout or "") + (out.stderr or "")
    return "not authenticated" not in combined.lower()


def deploy() -> str | None:
    print("Pubblico il Worker...")
    out = run(["npx", "wrangler", "deploy"], shell=True)
    text = (out.stdout or "") + (out.stderr or "")
    print(text.strip()[-800:])
    if out.returncode != 0:
        return None
    match = re.search(r"https://[a-z0-9.\-]+\.workers\.dev", text)
    return match.group(0) if match else None


def push_secrets() -> bool:
    sys.path.insert(0, str(ROOT))
    import brand

    ok = True
    for brand_name, worker_name in SECRETS.items():
        value = (brand.get(brand_name) or "").strip()
        if not value:
            print(f"  {brand_name}: vuoto in brand.py, salto")
            continue
        res = subprocess.run(
            ["npx", "wrangler", "secret", "put", worker_name],
            cwd=PROXY_DIR, input=value, text=True, capture_output=True, shell=True,
            encoding="utf-8", errors="replace",
        )
        if res.returncode == 0:
            print(f"  {worker_name}: caricato")
        else:
            ok = False
            print(f"  {worker_name}: ERRORE\n{(res.stderr or '')[-300:]}")
    return ok


def update_brand(url: str) -> None:
    text = BRAND.read_text(encoding="utf-8")
    text = re.sub(r'^OAUTH_PROXY_URL = ".*"$', f'OAUTH_PROXY_URL = "{url}"',
                  text, count=1, flags=re.M)
    for name in TO_CLEAR:
        text = re.sub(rf'^{name} = ".*"$', f'{name} = ""', text, count=1, flags=re.M)
    BRAND.write_text(text, encoding="utf-8")
    print(f"brand.py aggiornato: proxy attivo, {', '.join(TO_CLEAR)} svuotati.")


def push_stripe_keys() -> int:
    """Carica le chiavi di Stripe sul Worker. Si chiedono qui e non si
    scrivono da nessuna parte: restano solo nel Worker, che e' l'unico posto
    dove possono stare senza finire in un eseguibile distribuito."""
    import getpass

    print("Chiavi di Stripe (dashboard.stripe.com).")
    print("Non verranno salvate su questo computer: vanno direttamente al Worker.\n")

    entries = [
        ("STRIPE_SECRET_KEY",
         "Secret key (Developers > API keys, inizia con sk_live_ o sk_test_): "),
        ("STRIPE_WEBHOOK_SECRET",
         "Webhook signing secret (Developers > Webhooks > il tuo endpoint, inizia con whsec_): "),
    ]

    for name, prompt in entries:
        value = getpass.getpass(prompt).strip()
        if not value:
            print(f"  {name}: saltato (vuoto)")
            continue
        res = subprocess.run(
            ["npx", "wrangler", "secret", "put", name],
            cwd=PROXY_DIR, input=value, text=True, capture_output=True, shell=True,
            encoding="utf-8", errors="replace",
        )
        print(f"  {name}: {'caricato' if res.returncode == 0 else 'ERRORE'}")
        if res.returncode != 0:
            print((res.stderr or "")[-300:])
            return 1

    print("\nFatto. Ricorda che il webhook su Stripe deve puntare a:")
    print("  <URL del Worker>/stripe/webhook")
    print("con gli eventi: checkout.session.completed,")
    print("               customer.subscription.deleted, invoice.payment_failed")
    return 0


def push_resend_key() -> int:
    """Carica la chiave API di Resend: senza questa, la chiave di licenza
    resta visibile solo sulla pagina di atterraggio dopo il pagamento, con
    nessuna copia di riserva se il cliente chiude la scheda troppo presto."""
    import getpass

    print("Chiave API di Resend (resend.com/api-keys).")
    print("Non verra' salvata su questo computer: va direttamente al Worker.\n")

    value = getpass.getpass("Resend API key (inizia con re_): ").strip()
    if not value:
        print("  RESEND_API_KEY: saltato (vuoto)")
        return 0

    res = subprocess.run(
        ["npx", "wrangler", "secret", "put", "RESEND_API_KEY"],
        cwd=PROXY_DIR, input=value, text=True, capture_output=True, shell=True,
        encoding="utf-8", errors="replace",
    )
    print(f"  RESEND_API_KEY: {'caricata' if res.returncode == 0 else 'ERRORE'}")
    if res.returncode != 0:
        print((res.stderr or "")[-300:])
        return 1

    print("\nFatto. Il dominio mittente (licenses@mail.getcertsprint.com) deve")
    print("essere verificato su resend.com/domains prima che le email partano.")
    return 0


def main() -> int:
    if "--stripe" in sys.argv:
        if not check_login():
            print("Non sei autenticato su Cloudflare. Esegui prima: wrangler login")
            return 1
        return push_stripe_keys()

    if "--resend" in sys.argv:
        if not check_login():
            print("Non sei autenticato su Cloudflare. Esegui prima: wrangler login")
            return 1
        return push_resend_key()

    if not check_login():
        print("Non sei autenticato su Cloudflare.\n"
              "Esegui prima:  wrangler login\n"
              "(apre il browser sul tuo account, serve una volta sola)")
        return 1

    if not push_secrets():
        print("\nCaricamento dei segreti fallito: non proseguo.")
        return 1

    url = deploy()
    if not url:
        print("\nDeploy fallito: brand.py non e' stato toccato.")
        return 1

    update_brand(url)
    print(f"\nFatto. Proxy attivo su {url}")
    print("Ora ricompila l'app e verifica con:  python check_release.py --dist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
