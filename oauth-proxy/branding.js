/**
 * Home page, privacy policy and terms of service, served from here rather
 * than from GitHub Pages.
 *
 * Copyright (c) 2026 Aurelio Avila. All rights reserved.
 *
 * Why not aurelioavila.github.io: that domain is not ours — it is a shared
 * subdomain of github.io — so Google Cloud's branding verification cannot
 * confirm that the homepage "belongs" to whoever runs the OAuth project. A
 * real domain, with DNS under our control, fixes that at the root. Adding a
 * custom domain to GitHub Pages would have risked redirecting the Instagram
 * and TikTok OAuth callback pages too, which are already registered at that
 * exact URL — which is why these pages live here, on the Worker, instead.
 */
import { FAVICON_B64, ICON_512_B64, SCREENSHOT_B64 } from './assets.js';

const STYLE = `
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1a1a1a; }
  h1 { font-size: 1.6em; }
  h2 { font-size: 1.15em; margin-top: 2em; }
  code { background: #f2f2f2; padding: 2px 6px; border-radius: 4px; }
  footer { margin-top: 3em; font-size: 0.9em; color: #666; }
`;

// Palette e screenshot ripresi 1:1 dal tema "Ocean" dell'app (static/style.css):
// is what someone actually sees when they open Social Dashboard, not a
// separate theme invented for the website.
const HOME_STYLE = `
  :root {
    --bg: #071620; --panel: #0d2434; --panel-line: rgba(94,230,255,0.14);
    --text: #eaf6fb; --muted: #8fa8b3; --accent: #38bdf8; --accent2: #34d399;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: "Inter", -apple-system, Segoe UI, Roboto, sans-serif;
    line-height: 1.6;
  }
  a { color: var(--accent); }
  .wrap { max-width: 1080px; margin: 0 auto; padding: 0 24px; }
  header.site { display: flex; align-items: center; justify-content: space-between; padding: 22px 0; }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.05em; }
  .brand img { width: 28px; height: 28px; border-radius: 7px; }
  nav.site a { color: var(--muted); text-decoration: none; margin-left: 26px; font-size: 0.92em; }
  nav.site a:hover { color: var(--text); }
  .hero { padding: 56px 0 40px; text-align: center; }
  .eyebrow {
    font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 12.5px;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent2);
    display: inline-flex; align-items: center; gap: 8px; margin-bottom: 18px;
  }
  .eyebrow .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--accent2); box-shadow: 0 0 10px 1px color-mix(in srgb, var(--accent2) 70%, transparent); }
  h1 { font-size: 2.6em; font-weight: 800; letter-spacing: -0.02em; margin: 0 auto 18px; max-width: 720px; }
  h1 em { font-style: normal; color: var(--accent); }
  .sub { color: var(--muted); font-size: 1.15em; max-width: 560px; margin: 0 auto 32px; }
  .cta-row { display: flex; justify-content: center; gap: 14px; flex-wrap: wrap; }
  .btn { display: inline-flex; align-items: center; gap: 8px; padding: 13px 24px; border-radius: 11px; font-weight: 700; font-size: 0.98em; text-decoration: none; }
  .btn.primary { background: var(--accent); color: #04141d; }
  .btn.ghost { background: rgba(255,255,255,0.06); color: var(--text); border: 1px solid var(--panel-line); }
  .fineprint { margin-top: 16px; color: var(--muted); font-size: 0.85em; font-family: "JetBrains Mono", ui-monospace, monospace; }
  .shot { margin: 48px 0; border-radius: 16px; overflow: hidden; border: 1px solid var(--panel-line); box-shadow: 0 40px 90px rgba(0,0,0,0.45); }
  .shot img { display: block; width: 100%; height: auto; }
  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin: 20px 0 56px; }
  .card {
    background: var(--panel); border: 1px solid var(--panel-line); border-radius: 14px; padding: 22px;
  }
  .card .glyph { width: 34px; height: 34px; border-radius: 9px; background: linear-gradient(135deg, var(--accent), var(--accent2)); margin-bottom: 14px; }
  .card h3 { margin: 0 0 8px; font-size: 1.02em; }
  .card p { margin: 0; color: var(--muted); font-size: 0.92em; }
  .trust { background: var(--panel); border: 1px solid var(--panel-line); border-radius: 16px; padding: 32px; margin: 0 0 56px; }
  .trust h2 { margin-top: 0; font-size: 1.3em; }
  .trust p { color: var(--muted); max-width: 720px; }
  .platforms { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin: 0 0 60px; }
  .platforms span {
    font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 12.5px;
    padding: 8px 16px; border-radius: 999px; background: rgba(255,255,255,0.05); border: 1px solid var(--panel-line); color: var(--muted);
  }
  footer.site { border-top: 1px solid var(--panel-line); padding: 28px 0 50px; color: var(--muted); font-size: 0.88em; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
  footer.site a { color: var(--muted); text-decoration: underline; }
  @media (max-width: 720px) {
    .grid { grid-template-columns: 1fr; }
    h1 { font-size: 2em; }
  }
`;

function html(body) {
  return new Response(body, { headers: { 'content-type': 'text/html; charset=utf-8' } });
}

function png(base64) {
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  return new Response(bytes, { headers: { 'content-type': 'image/png', 'cache-control': 'public, max-age=604800' } });
}

export function faviconAsset() {
  return png(FAVICON_B64);
}

export function iconAsset() {
  return png(ICON_512_B64);
}

export function screenshotAsset() {
  return png(SCREENSHOT_B64);
}

export function robotsTxt() {
  return new Response('User-agent: *\nAllow: /\n\nSitemap: https://socialdashboard.getcertsprint.com/sitemap.xml\n', { headers: { 'content-type': 'text/plain; charset=utf-8' } });
}

export function sitemapXml() {
  const urls = ['', 'privacy', 'terms', 'data-deletion'].map((p) => `  <url><loc>https://socialdashboard.getcertsprint.com/${p}</loc></url>`).join('\n');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`, { headers: { 'content-type': 'application/xml; charset=utf-8' } });
}

const DESCRIPTION = 'Social Dashboard brings your YouTube, Instagram, TikTok and X stats into one calm, private window. Free, local-first, no account required.';
const DOWNLOAD_URL = 'https://github.com/AurelioAvila/social-dashboard/releases/latest';

export function homePage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="icon" href="/favicon.png" type="image/png">
<meta name="application-name" content="Social Dashboard">
<meta name="description" content="${DESCRIPTION}">
<link rel="canonical" href="https://socialdashboard.getcertsprint.com/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Social Dashboard">
<meta property="og:title" content="Social Dashboard — every account, one calm window">
<meta property="og:description" content="${DESCRIPTION}">
<meta property="og:image" content="https://socialdashboard.getcertsprint.com/screenshot.png">
<meta property="og:url" content="https://socialdashboard.getcertsprint.com/">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Social Dashboard">
<meta name="twitter:description" content="${DESCRIPTION}">
<meta name="twitter:image" content="https://socialdashboard.getcertsprint.com/screenshot.png">
<script type="application/ld+json">${JSON.stringify({
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Social Dashboard',
  operatingSystem: 'Windows 10, Windows 11',
  applicationCategory: 'BusinessApplication',
  offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
  description: DESCRIPTION,
  url: 'https://socialdashboard.getcertsprint.com/',
})}</script>
<title>Social Dashboard — every account, one calm window</title>
<style>${HOME_STYLE}</style></head><body>
<div class="wrap">
  <header class="site">
    <div class="brand"><img src="/icon.png" alt=""><span>Social Dashboard</span></div>
    <nav class="site">
      <a href="#features">Features</a>
      <a href="#privacy">Privacy</a>
      <a href="https://github.com/AurelioAvila/social-dashboard">GitHub</a>
    </nav>
  </header>

  <section class="hero">
    <p class="eyebrow"><span class="dot"></span>Free · Windows 10/11</p>
    <h1>Every account. <em>One calm</em>, private workspace.</h1>
    <p class="sub">See what's growing, what needs attention and when your content performs
    best across YouTube, Instagram, TikTok and X — without juggling a dozen tabs.</p>
    <div class="cta-row">
      <a class="btn primary" href="${DOWNLOAD_URL}">⬇ Download for Windows</a>
      <a class="btn ghost" href="#features">See what it does</a>
    </div>
    <p class="fineprint">No account, no cloud sync, no credit card — your tokens never leave your PC</p>
  </section>

  <div class="shot"><img src="/screenshot.png" alt="Social Dashboard overview screen, showing total audience, recent views, interactions and per-platform breakdowns" loading="lazy"></div>

  <section id="features" class="grid">
    <div class="card">
      <div class="glyph"></div>
      <h3>Single overview</h3>
      <p>YouTube, Instagram, TikTok and X side by side, with trends over time instead of four separate apps.</p>
    </div>
    <div class="card">
      <div class="glyph"></div>
      <h3>Analytics that answer "what's working"</h3>
      <p>Top-performing content and a 24-hour chart of your best posting windows, per platform.</p>
    </div>
    <div class="card">
      <div class="glyph"></div>
      <h3>Diagnostics, not just numbers</h3>
      <p>Flags stalled accounts, zero-view content and access problems — each with a concrete next step.</p>
    </div>
    <div class="card">
      <div class="glyph"></div>
      <h3>Automatic insights</h3>
      <p>Computed locally from your own data. No AI calls, no extra cost, nothing sent anywhere.</p>
    </div>
    <div class="card">
      <div class="glyph"></div>
      <h3>CSV export</h3>
      <p>Take the collected data with you — spreadsheets, reports, whatever you need it for.</p>
    </div>
    <div class="card">
      <div class="glyph"></div>
      <h3>9 themes, 6 languages</h3>
      <p>IT, EN, ES, FR, DE, JA — and a theme that actually matches how you like your desktop to look.</p>
    </div>
  </section>

  <section id="privacy" class="trust">
    <h2>Your data stays on your computer</h2>
    <p>Account permissions and every statistic Social Dashboard shows live in a local database next to
    the app — never on a server we run. The app talks directly to each platform's official API using a
    token you grant yourself, and you can revoke it at any time from that platform's own security
    settings. Read the full <a href="/privacy">privacy policy</a>.</p>
  </section>

  <div class="platforms">
    <span>YouTube</span><span>Instagram</span><span>TikTok</span><span>X</span>
  </div>

  <footer class="site">
    <span>© 2026 Aurelio Avila. All rights reserved.</span>
    <span><a href="/privacy">Privacy policy</a> · <a href="/terms">Terms of service</a> · <a href="/data-deletion">Data deletion</a> · <a href="https://github.com/AurelioAvila/social-dashboard">Source on GitHub</a></span>
  </footer>
</div>
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

export function dataDeletionPage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Social Dashboard — Data Deletion Instructions</title><style>${STYLE}</style></head><body>
<h1>Data Deletion Instructions — Social Dashboard</h1>
<p>Last updated: August 28, 2026.</p>

<p>Social Dashboard is a local-first desktop application: it does not have a
server that stores your account data, so there is nothing on our side to
delete on request. Everything the app knows about your accounts — access
tokens, statistics, content history — lives only in a SQLite database on
your own computer. Deleting it is something you do directly, in full
control, without waiting on us.</p>

<h2>Delete a single connected account</h2>
<ol>
  <li>Open Social Dashboard.</li>
  <li>Go to the "Link account" screen.</li>
  <li>Choose the account you want to remove and select <strong>Unlink</strong>.</li>
</ol>
<p>The corresponding access token is deleted immediately from the local
database. Nothing is sent to us — there is nothing for us to receive.</p>

<h2>Delete everything the app has stored</h2>
<ul>
  <li>Uninstall Social Dashboard through Windows' usual "Apps" settings, which
  removes the app's local data folder along with it; or</li>
  <li>Manually delete the <code>cache.db</code> file in the app's data
  folder, which holds every token and every piece of collected data.</li>
</ul>

<h2>Revoke access from the platform directly</h2>
<p>Because tokens live only on your device, the platforms themselves are the
authoritative place to confirm access has been cut. You can revoke Social
Dashboard's access at any time from the security settings of
<a href="https://myaccount.google.com/permissions">YouTube (Google)</a>,
<a href="https://accountscenter.instagram.com/">Instagram (Meta)</a>,
<a href="https://www.tiktok.com/setting/manage-account-and-permissions">TikTok</a>
or X — this works whether or not the app is still installed.</p>

<h2>Contact</h2>
<p>Questions about this process can be opened as an issue on
<a href="https://github.com/AurelioAvila/social-dashboard/issues">GitHub</a>.</p>

<footer>Social Dashboard</footer>
</body></html>`);
}
