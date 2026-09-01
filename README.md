<p align="center">
  <img src="icon_preview.png" width="144" alt="Social Dashboard icon">
</p>

<h1 align="center">Social Dashboard</h1>

<p align="center">
  <strong>Every account. One calm, private workspace.</strong><br>
  See what is growing, what needs attention and when your content performs best — without juggling a dozen tabs.
</p>

<p align="center">
  <a href="https://github.com/AurelioAvila/social-dashboard/releases/latest"><img src="https://img.shields.io/badge/Download-Windows%2010%2F11-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Download for Windows"></a>
  <img src="https://img.shields.io/badge/Data-local%20first-22C55E?style=for-the-badge&logo=shield&logoColor=white" alt="Local-first data">
  <a href="https://github.com/AurelioAvila/social-dashboard/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-Proprietary-B33A3A?style=for-the-badge" alt="Proprietary License"></a>
</p>

<p align="center"><sub>Like the privacy-first approach? ⭐ Star the repository to follow releases and help more creators discover it.</sub></p>

<p align="center">
  <a href="https://buy.stripe.com/28E3cvdoZdzTdRiedY9Ve00"><img src="https://img.shields.io/badge/%E2%98%95%20Buy%20me%20a%20coffee-one--off%2C%20no%20account-FF5500?style=flat-square&labelColor=1c1c1c" alt="Buy me a coffee — a one-off tip, no account and nothing to cancel" height="20"></a>
</p>

## [⬇ Download the latest version](https://github.com/AurelioAvila/social-dashboard/releases/latest)

Not code-signed yet, so Windows SmartScreen shows a warning on first run —
click **More info** → **Run anyway**. Details in [Installation](#installation) below.

## What it does

- **Single overview** of YouTube, Instagram, TikTok and X, with trends over time
- **Analytics** that answer "what's working and when should I post": top
  content and a 24-hour chart of the best posting windows
- **Diagnostics** that go beyond "is the API responding": flags accounts
  stalled for too many days, content with zero views, and access problems,
  each with a concrete next step
- **Automatic insights** computed locally from your own data — no AI calls,
  no extra cost
- **CSV export** of the collected data
- 9 themes, 6 languages (IT/EN/ES/FR/DE/JA)

## Designed around your data

- 📈 **See the signal** — spot your strongest content and the best publishing windows across platforms.
- 🔒 **Keep control** — tokens and account permissions stay on your computer, not on a central analytics server.
- ✦ **Act with confidence** — diagnostics turn stale accounts, zero-view content and access issues into clear next steps.

## Privacy

Account permissions stay **only on your computer**, in a local database next
to the application. Nothing goes through an external server: the app talks
directly to each platform's API.

Access tokens and any developer-app secrets you enter are encrypted at rest
using Windows DPAPI, tied to your Windows account. If the database file is
copied to another machine or opened under a different Windows account, those
credentials cannot be decrypted and the affected accounts simply show as
needing to be reconnected — the rest of your data stays readable.

To be precise about what that does and doesn't cover: it protects against
the database file being taken elsewhere (a stray backup, a synced folder, a
resold computer, another account on the same PC). It does **not** protect
against malicious software running as you on your own machine, which could
ask Windows to decrypt exactly as the app does. No local encryption can
prevent that.

The only external calls are the OAuth token exchange for Instagram/TikTok,
routed through a minimal proxy that only forwards the authorization code —
it never sees or stores your data.

## Installation

Download the latest release, extract the ZIP and launch
`Social Dashboard.exe`. No install, no configuration.

On first launch Windows may show a SmartScreen warning because the
executable isn't digitally signed: "More info" → "Run anyway".

The app checks once a day whether a newer release exists and shows a small
banner if so; it never downloads or installs anything on its own, the
banner just opens the release page for you to grab manually.

## Connecting accounts

Open **Connect account**, press the platform button, sign in. The app only
requests **read-only** access to your statistics.

Availability by platform:

| Platform | Status |
|---|---|
| YouTube | Direct connection |
| Instagram | Coming soon, or connect now with your own app |
| TikTok | Coming soon, or connect now with your own app |
| X | Read metrics don't exist on the free API tier |

### Connect Instagram or TikTok right now

Both platforms require their own review before an app may connect *other*
people's accounts, and Instagram additionally requires Meta business
verification. Neither review is needed to connect the account of whoever
registered the app: Instagram allows it in Development mode, TikTok through a
Sandbox.

So there is a way to skip the wait entirely. Press **Connect**, and when the
"coming soon" notice appears choose **Connect it now**: a step-by-step guide
walks you through registering your own app — about ten minutes, once. The
credentials never leave your computer, and the redirect address is already
published, so there is no website for you to set up.

When the platform review is approved this becomes unnecessary, and existing
connections keep working either way.

## Development

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python desktop_app.py
```

To work on backend/frontend only, without the native window:

```bash
python -m uvicorn app:app --port 8787 --reload
```

Manual configuration (optional) is done by copying `.env.example` to `.env`.
Not needed for normal use: accounts are connected from within the app.

### OAuth app credentials (for people distributing the app)

One-click login for Instagram/TikTok/YouTube requires the product's own app
credentials, not the end user's. Copy `brand.example.py` to `brand.py` and
fill in the values created on the respective developer portals:

- **Instagram**: [developers.facebook.com/apps](https://developers.facebook.com/apps) →
  create an app → add the "Manage messages and content on Instagram" use
  case → find the App ID and App Secret under the Instagram Login
  configuration, and set the redirect URL
- **TikTok**: [developers.tiktok.com/apps](https://developers.tiktok.com/apps) →
  create an app → add "Login Kit" → request the `video.list` scope

`brand.py` **must never be committed**: once filled in it contains real
secrets. It's already excluded via `.gitignore`.

Instagram and TikTok additionally require a **token exchange proxy** so the
client secret never ships inside the executable — see
[oauth-proxy/README.md](oauth-proxy/README.md).

### Building the executable

```bash
pyinstaller --noconfirm "Social Dashboard.spec"
```

The result lands in `dist/Social Dashboard/`. `.env`, `cache.db` and
`brand.py` are not part of the build and must never be distributed as
source — only the credentials from `brand.py` end up compiled into the
executable itself (with the confidential Instagram/TikTok secrets kept out
via the proxy — run `python check_release.py --dist` to verify before
distributing).

### Modes

`APP_MODE` distinguishes the public build from the personal one:

- `customer` (default) — social platforms only
- `personal` — also includes the personal modules

The default is deliberately `customer`: a build distributed by mistake
without the variable set never exposes the personal modules.

## Structure

```
app.py            FastAPI API and refresh orchestration
connections.py    Account linking via OAuth
own_app.py        Credentials of an app registered by the user
platforms/        One adapter per platform
diagnostics.py    Automated checks (no AI calls)
analytics.py      Locally computed statistics
trends.py         Historical series and trends
auth.py           Local registration and login
billing.py        Plans and Stripe checkout
static/           UI (HTML/CSS/JS, no framework)
```

## License

Proprietary — all rights reserved, see [LICENSE](LICENSE). This applies
from the first release after v1.4.0 onward. Versions up to and including
v1.4.0 remain available under the MIT License they were originally
published under: see the
[v1.4.0 LICENSE](https://github.com/AurelioAvila/social-dashboard/blob/v1.4.0/LICENSE).
