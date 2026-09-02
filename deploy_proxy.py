"""
Deploy the OAuth and licensing proxy in one operation.

After `wrangler login`, this publishes the Worker, uploads secrets from
brand.py, writes the deployed URL back to brand.py, and removes the two
confidential client secrets from the distributable build.

    wrangler login          # authenticate your account once
    python deploy_proxy.py

Afterwards, `python check_release.py` must report a clean build.

Secrets are sent to Wrangler through stdin, never through command-line
arguments, so they do not appear in shell history or process listings.

Stripe keys never belong in brand.py, the repository, or the build. Upload
them separately once with:

    python deploy_proxy.py --stripe

Upload the Resend key, used for licensing email, the same way:

    python deploy_proxy.py --resend

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROXY_DIR = ROOT / "oauth-proxy"
BRAND = ROOT / "brand.py"

# Name in brand.py -> secret name in the Worker.
SECRETS = {
    "INSTAGRAM_APP_ID": "INSTAGRAM_APP_ID",
    "INSTAGRAM_APP_SECRET": "INSTAGRAM_APP_SECRET",
    "TIKTOK_CLIENT_KEY": "TIKTOK_CLIENT_KEY",
    "TIKTOK_CLIENT_SECRET": "TIKTOK_CLIENT_SECRET",
}

# Only these values are cleared from brand.py. Google documents the installed
# app client secret as non-confidential, so it remains available to the build.
TO_CLEAR = ("INSTAGRAM_APP_SECRET", "TIKTOK_CLIENT_SECRET")
NPX = shutil.which("npx.cmd" if sys.platform == "win32" else "npx") or "npx"


def run(args, **kw):
    # Wrangler prints Unicode; force UTF-8 instead of relying on the Windows
    # code page. Commands are passed as an argument list without a shell.
    return subprocess.run(args, cwd=PROXY_DIR, text=True, capture_output=True,
                          encoding="utf-8", errors="replace", **kw)


def check_login() -> bool:
    out = run([NPX, "wrangler", "whoami"])
    combined = (out.stdout or "") + (out.stderr or "")
    return "not authenticated" not in combined.lower()


def deploy() -> str | None:
    print("Publishing the Worker...")
    out = run([NPX, "wrangler", "deploy"])
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
            continue
        res = subprocess.run(
            [NPX, "wrangler", "secret", "put", worker_name],
            cwd=PROXY_DIR, input=value, text=True, capture_output=True,
            encoding="utf-8", errors="replace",
        )
        if res.returncode != 0:
            ok = False
    return ok


def update_brand(url: str) -> None:
    text = BRAND.read_text(encoding="utf-8")
    text = re.sub(r'^OAUTH_PROXY_URL = ".*"$', f'OAUTH_PROXY_URL = "{url}"',
                  text, count=1, flags=re.M)
    for name in TO_CLEAR:
        text = re.sub(rf'^{name} = ".*"$', f'{name} = ""', text, count=1, flags=re.M)
    BRAND.write_text(text, encoding="utf-8")
    print(f"brand.py updated: proxy active; {', '.join(TO_CLEAR)} cleared.")


def push_stripe_keys() -> int:
    """Upload Stripe keys directly to the Worker without storing them locally."""
    import getpass

    print("Stripe keys (dashboard.stripe.com).")
    print("They will not be stored on this computer; they go directly to the Worker.\n")

    entries = [
        ("STRIPE_SECRET_KEY",
         "Secret key (Developers > API keys; starts with sk_live_ or sk_test_): "),
        ("STRIPE_WEBHOOK_SECRET",
         "Webhook signing secret (Developers > Webhooks > your endpoint; starts with whsec_): "),
    ]

    for name, prompt in entries:
        value = getpass.getpass(prompt).strip()
        if not value:
            print(f"  {name}: skipped (empty)")
            continue
        res = subprocess.run(
            [NPX, "wrangler", "secret", "put", name],
            cwd=PROXY_DIR, input=value, text=True, capture_output=True,
            encoding="utf-8", errors="replace",
        )
        print(f"  {name}: {'uploaded' if res.returncode == 0 else 'ERROR'}")
        if res.returncode != 0:
            print((res.stderr or "")[-300:])
            return 1

    print("\nDone. The Stripe webhook must point to:")
    print("  <URL del Worker>/stripe/webhook")
    print("subscribed to these five events:")
    for evento in ("checkout.session.completed", "customer.subscription.deleted",
                   "invoice.payment_failed", "invoice.paid",
                   "customer.subscription.updated"):
        print(f"  - {evento}")
    # The last two are what bring a licence back after a failed payment
    # recovers. Without them the key stays dead while Stripe goes on billing.
    print("  (the last two restore a licence after a recovered payment —")
    print("   without them a suspended key never comes back)")
    return 0


def push_resend_key() -> int:
    """Upload the Resend API key used to deliver a backup copy of each license."""
    import getpass

    print("Resend API key (resend.com/api-keys).")
    print("It will not be stored on this computer; it goes directly to the Worker.\n")

    value = getpass.getpass("Resend API key (starts with re_): ").strip()
    if not value:
        print("  RESEND_API_KEY: skipped (empty)")
        return 0

    res = subprocess.run(
        [NPX, "wrangler", "secret", "put", "RESEND_API_KEY"],
        cwd=PROXY_DIR, input=value, text=True, capture_output=True,
        encoding="utf-8", errors="replace",
    )
    print(f"  RESEND_API_KEY: {'uploaded' if res.returncode == 0 else 'ERROR'}")
    if res.returncode != 0:
        print((res.stderr or "")[-300:])
        return 1

    print("\nDone. Verify the sender domain (licenses@mail.getcertsprint.com)")
    print("at resend.com/domains before sending email.")
    return 0


def main() -> int:
    if "--stripe" in sys.argv:
        if not check_login():
            print("You are not authenticated with Cloudflare. Run: wrangler login")
            return 1
        return push_stripe_keys()

    if "--resend" in sys.argv:
        if not check_login():
            print("You are not authenticated with Cloudflare. Run: wrangler login")
            return 1
        return push_resend_key()

    if not check_login():
        print("You are not authenticated with Cloudflare.\n"
              "Run:  wrangler login\n"
              "(this opens your account in a browser and is only required once)")
        return 1

    if not push_secrets():
        print("\nSecret upload failed; deployment stopped.")
        return 1

    url = deploy()
    if not url:
        print("\nDeployment failed; brand.py was not changed.")
        return 1

    update_brand(url)
    print(f"\nDone. Proxy active at {url}")
    print("Rebuild the app and verify it with:  python check_release.py --dist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
