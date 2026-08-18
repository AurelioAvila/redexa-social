/**
 * Home page, privacy policy e termini di servizio, serviti da qui invece
 * che da GitHub Pages.
 *
 * Perche' non su aurelioavila.github.io: quel dominio non e' di nostra
 * proprieta' (e' un sottodominio condiviso di github.io), quindi la
 * verifica del branding di Google Cloud non riesce a confermare che
 * l'homepage "appartiene" a chi gestisce il progetto OAuth. Un dominio
 * vero (socialdashboard.getcertsprint.com, DNS sotto il nostro controllo)
 * risolve il problema alla radice. Aggiungere un dominio personalizzato a
 * GitHub Pages avrebbe rischiato di reindirizzare anche le pagine di
 * callback OAuth di Instagram/TikTok, gia' registrate su quell'URL esatto -
 * per questo le pagine vivono qui, sul Worker, invece.
 */

const STYLE = `
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1a1a1a; }
  h1 { font-size: 1.6em; }
  h2 { font-size: 1.15em; margin-top: 2em; }
  code { background: #f2f2f2; padding: 2px 6px; border-radius: 4px; }
  footer { margin-top: 3em; font-size: 0.9em; color: #666; }
`;

function html(body) {
  return new Response(body, { headers: { 'content-type': 'text/html; charset=utf-8' } });
}

export function homePage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="application-name" content="Social Dashboard">
<meta name="description" content="Social Dashboard is a free Windows desktop application that brings together your YouTube, Instagram and TikTok statistics in a single window.">
<meta property="og:site_name" content="Social Dashboard">
<meta property="og:title" content="Social Dashboard">
<meta property="og:description" content="Social Dashboard is a free Windows desktop application that brings together your YouTube, Instagram and TikTok statistics in a single window.">
<title>Social Dashboard</title><style>${STYLE}</style></head><body>
<h1>Social Dashboard</h1>
<p><strong>Social Dashboard</strong> is a free Windows desktop application that brings
together your YouTube, Instagram and TikTok statistics in a single window.
Connect your accounts, press Refresh, and see follower counts, views and
trends without opening each platform separately.</p>
<p>All the data it shows comes directly from the official API of each
platform, using an access token you grant yourself. The app runs locally
on your computer: your statistics and your login credentials are never
sent to any server we operate.</p>
<ul>
  <li><a href="/privacy">Privacy policy</a></li>
  <li><a href="/terms">Terms of service</a></li>
</ul>
<footer>© 2026 Aurelio Avila. All rights reserved.</footer>
</body></html>`);
}

export function privacyPage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Social Dashboard — Privacy Policy</title><style>${STYLE}</style></head><body>
<h1>Privacy Policy — Social Dashboard</h1>
<p>Last updated: August 18, 2026.</p>

<p>Social Dashboard is a desktop application that shows the statistics of
your YouTube, Instagram, TikTok and X accounts in a single window. This
page explains what data is handled and how.</p>

<h2>Where your data lives</h2>
<p>All the data the app collects — access tokens, statistics, content
history — stays <strong>exclusively on your computer</strong>, in a local
SQLite database next to the executable. There is no Social Dashboard server
that receives or stores this data: the app talks directly to the official
YouTube, Instagram, TikTok and X APIs using your own credentials.</p>

<h2>What is requested from each platform</h2>
<p>When you link an account, the app only requests <strong>read-only</strong>
access to the public statistics of your profile (e.g. subscriber/follower
count, views, the list of published content). The app never posts, edits or
deletes anything on your behalf.</p>

<h2>Nothing leaves your computer</h2>
<p>Every statistic, chart and observation shown in the app is computed
locally, on your machine, from the data already collected. No external
service — AI or otherwise — ever receives your statistics or your content.
The only network requests the app makes are the ones needed to read your
own accounts from the platforms' own APIs, to check for app updates, and
to verify a licence key for paid plans.</p>

<h2>How to delete your data</h2>
<p>You can unlink an account at any time from the "Link account" screen: the
corresponding token is deleted immediately from the local database. To
delete everything, remove the <code>cache.db</code> file in the app's data
folder, or uninstall the app.</p>

<h2>Revoking access from the platform</h2>
<p>You can also revoke Social Dashboard's access to your accounts directly
from the security settings of YouTube (Google), Instagram (Meta), TikTok or
X, at any time.</p>

<h2>Contact</h2>
<p>For questions about this policy, open an issue on
<a href="https://github.com/AurelioAvila/social-dashboard/issues">GitHub</a>.</p>

<footer>Social Dashboard</footer>
</body></html>`);
}

export function termsPage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Social Dashboard — Terms of Service</title><style>${STYLE}</style></head><body>
<h1>Terms of Service — Social Dashboard</h1>
<p>Last updated: August 18, 2026.</p>

<p>These terms govern the use of Social Dashboard, a desktop application
that shows the statistics of your social accounts (YouTube, Instagram,
TikTok, X) in a single window. By using the app, you accept the following.</p>

<h2>What the app does</h2>
<p>Social Dashboard reads, with your authorization, the public statistics of
your social accounts through the official APIs of the respective platforms,
and displays them locally. The app doesn't publish content, doesn't change
account settings, and doesn't share your data with third parties, except as
described in the <a href="/privacy">privacy policy</a>.</p>

<h2>Accounts and connections</h2>
<p>You're responsible for keeping your social account credentials
confidential. You can link and unlink accounts at any time from the app.
Social Dashboard is not affiliated with YouTube, Instagram, TikTok or X:
these are third-party platforms subject to their own terms, which remain in
effect in addition to these.</p>

<h2>Permitted use</h2>
<p>The app is intended for personal monitoring of your own accounts. You may
not use it to access accounts that don't belong to you without
authorization, or for unlawful purposes.</p>

<h2>No warranty</h2>
<p>The app is provided "as is". The statistics shown depend on the
availability and accuracy of the data returned by third-party platform
APIs: we don't guarantee they are always accurate, complete, or available
in real time.</p>

<h2>Subscription</h2>
<p>Some features may require a paid subscription, handled through a
third-party payment provider. You can cancel your subscription at any time
from the app's settings.</p>

<h2>Ownership and license</h2>
<p>Social Dashboard and its source code are proprietary and © 2026 Aurelio
Avila. Downloading and running the application does not grant any right to
copy, modify, decompile, redistribute or resell it. Versions up to and
including v1.4.0 were published under the MIT License and remain available
under that license as originally granted; this clause applies from the
first version released after v1.4.0 onward. See the
<a href="https://github.com/AurelioAvila/social-dashboard/blob/master/LICENSE">LICENSE</a>
for the full terms.</p>

<h2>Changes</h2>
<p>These terms may be updated; the version in effect is always the one
published at this address.</p>

<h2>Contact</h2>
<p>For questions about these terms, open an issue on
<a href="https://github.com/AurelioAvila/social-dashboard/issues">GitHub</a>.</p>

<footer>Social Dashboard</footer>
</body></html>`);
}
