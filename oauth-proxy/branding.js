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

// The website and application share the same Redexa Social visual language.
const HOME_STYLE = `
  :root {
    --bg: #f5f8ff; --panel: #ffffff; --line: #dce5f5;
    --text: #09142f; --muted: #5d6b85; --accent: #145cff; --soft: #eaf0ff; --green: #168b49;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body { margin:0; background:linear-gradient(180deg,#fff 0,#f5f8ff 28%,#fff 100%); color:var(--text); font-family:"Inter",-apple-system,Segoe UI,Roboto,sans-serif; line-height:1.55; }
  a { color: var(--accent); }
  .wrap { max-width:1180px; margin:0 auto; padding:0 28px; }
  header.site { display:flex; align-items:center; justify-content:space-between; padding:22px 0; }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.05em; }
  .brand img { width:32px; height:32px; border-radius:9px; }
  nav.site a { color:var(--muted); text-decoration:none; margin-left:26px; font-size:.92em; font-weight:600; }
  nav.site a:hover { color: var(--text); }
  .hero { display:grid; grid-template-columns:.92fr 1.08fr; align-items:center; gap:54px; padding:72px 0 58px; }
  .eyebrow { font:600 12px "JetBrains Mono",monospace; letter-spacing:.11em; text-transform:uppercase; color:var(--green); margin:0 0 18px; }
  h1 { font-size:clamp(42px,5vw,68px); line-height:1.02; font-weight:800; letter-spacing:-.045em; margin:0 0 22px; }
  h1 em { font-style: normal; color: var(--accent); }
  .sub { color:var(--muted); font-size:1.14em; max-width:570px; margin:0 0 30px; }
  .cta-row { display:flex; gap:12px; flex-wrap:wrap; }
  .btn { display:inline-flex; align-items:center; padding:13px 22px; border-radius:10px; font-weight:700; text-decoration:none; transition:.18s ease; }
  .btn:hover { transform:translateY(-2px); }
  .btn.primary { background:var(--accent); color:#fff; box-shadow:0 14px 30px rgba(20,92,255,.24); }
  .btn.ghost { background:var(--panel); color:var(--text); border:1px solid var(--line); }
  .fineprint { margin-top:18px; color:var(--muted); font:500 12px "JetBrains Mono",monospace; }
  .shot { border-radius:20px; overflow:hidden; border:1px solid var(--line); box-shadow:0 32px 70px rgba(34,60,120,.20); transform:rotate(1deg); background:#fff; }
  .shot img { display: block; width: 100%; height: auto; }
  .proof { display:grid; grid-template-columns:repeat(4,1fr); border:1px solid var(--line); border-radius:16px; background:#fff; margin:22px 0 84px; overflow:hidden; }
  .proof div { padding:20px; text-align:center; border-right:1px solid var(--line); font-size:13px; color:var(--muted); }
  .proof div:last-child { border:0; } .proof strong { display:block; color:var(--text); font-size:16px; }
  .section-head { max-width:680px; margin:0 0 30px; } .section-head h2 { font-size:clamp(30px,4vw,46px); line-height:1.08; letter-spacing:-.035em; margin:0 0 12px; }
  .section-head p,.card p,.trust p,.price p { color:var(--muted); }
  .grid { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; margin:0 0 90px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:26px; }
  .card .number { color:var(--accent); font:700 12px "JetBrains Mono",monospace; }
  .card h3 { margin:28px 0 8px; font-size:1.06em; } .card p { margin:0; font-size:.92em; }
  .trust { display:grid; grid-template-columns:1fr 1fr; gap:36px; background:#0b1735; color:white; border-radius:22px; padding:46px; margin:0 0 90px; }
  .trust h2 { margin:0; font-size:2em; line-height:1.15; } .trust p { color:#b9c6df; margin:0; }
  .pricing { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; margin:0 0 90px; }
  .price { background:#fff; border:1px solid var(--line); border-radius:16px; padding:27px; } .price.featured { border:2px solid var(--accent); box-shadow:0 18px 40px rgba(20,92,255,.12); }
  .price h3 { margin:0 0 7px; } .amount { font-size:32px; font-weight:800; letter-spacing:-.03em; margin:20px 0 4px; } .amount small { font-size:13px; color:var(--muted); font-weight:500; }
  .price ul { padding-left:18px; color:var(--muted); min-height:116px; }
  .final { text-align:center; background:var(--soft); border-radius:22px; padding:54px 24px; margin-bottom:72px; } .final h2 { font-size:36px; margin:0 0 12px; }
  footer.site { border-top:1px solid var(--line); padding:28px 0 50px; color:var(--muted); font-size:.88em; display:flex; justify-content:space-between; flex-wrap:wrap; gap:12px; }
  footer.site a { color: var(--muted); text-decoration: underline; }
  @media (max-width:800px) { nav.site a:not(:last-child){display:none}.hero,.trust{grid-template-columns:1fr}.hero{padding-top:40px}.shot{transform:none}.grid,.pricing{grid-template-columns:1fr}.proof{grid-template-columns:1fr 1fr}.proof div:nth-child(2){border-right:0} }
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
  return new Response('User-agent: *\nAllow: /\n\nSitemap: https://redexa.getcertsprint.com/sitemap.xml\n', { headers: { 'content-type': 'text/plain; charset=utf-8' } });
}

export function sitemapXml() {
  const urls = ['', 'privacy', 'terms', 'data-deletion', 'local-first-social-media-analytics', 'youtube-analytics-dashboard', 'multi-platform-creator-analytics'].map((p) => `  <url><loc>https://redexa.getcertsprint.com/${p}</loc></url>`).join('\n');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`, { headers: { 'content-type': 'application/xml; charset=utf-8' } });
}

const DESCRIPTION = 'Redexa Social turns YouTube, Instagram, TikTok and X metrics into clear next steps in a private Windows workspace.';
const DOWNLOAD_URL = 'https://github.com/AurelioAvila/social-dashboard/releases/latest';

export function homePage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="icon" href="/icon.png?v=191" type="image/png">
<link rel="apple-touch-icon" href="/icon.png?v=191">
<meta name="application-name" content="Redexa Social">
<meta name="description" content="${DESCRIPTION}">
<link rel="canonical" href="https://redexa.getcertsprint.com/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Redexa Social">
<meta property="og:title" content="Redexa Social — turn scattered metrics into your next move">
<meta property="og:description" content="${DESCRIPTION}">
<meta property="og:image" content="https://redexa.getcertsprint.com/redexa-social-overview.png?v=191">
<meta property="og:image:width" content="1280"><meta property="og:image:height" content="720">
<meta property="og:url" content="https://redexa.getcertsprint.com/">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Redexa Social — your creator command center">
<meta name="twitter:description" content="${DESCRIPTION}">
<meta name="twitter:image" content="https://redexa.getcertsprint.com/redexa-social-overview.png?v=191">
<script type="application/ld+json">${JSON.stringify({
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Redexa Social',
  operatingSystem: 'Windows 10, Windows 11',
  applicationCategory: 'BusinessApplication',
  downloadUrl: DOWNLOAD_URL,
  offers: [
    { '@type': 'Offer', name: 'Free', price: '0', priceCurrency: 'EUR' },
    { '@type': 'Offer', name: 'Pro monthly', price: '12', priceCurrency: 'EUR' },
    { '@type': 'Offer', name: 'Studio monthly', price: '39', priceCurrency: 'EUR' },
  ],
  description: DESCRIPTION,
  url: 'https://redexa.getcertsprint.com/',
})}</script>
<title>Redexa Social — Private Social Analytics for Windows</title>
<style>${HOME_STYLE}</style></head><body>
<div class="wrap">
  <header class="site">
    <div class="brand"><img src="/icon.png" alt=""><span>Redexa Social</span></div>
    <nav class="site">
      <a href="#features">Features</a>
      <a href="#privacy">Privacy</a>
      <a href="https://github.com/AurelioAvila/social-dashboard">GitHub</a>
    </nav>
  </header>

  <section class="hero">
    <div><p class="eyebrow">Private by design · Built for Windows</p>
    <h1>Your audience is talking. <em>See the signal.</em></h1>
    <p class="sub">Redexa Social brings YouTube, Instagram, TikTok and X into one focused workspace, then shows you where to act next.</p>
    <div class="cta-row">
      <a class="btn primary" href="${DOWNLOAD_URL}">Download for Windows</a>
      <a class="btn ghost" href="#features">Explore features</a>
    </div>
    <p class="fineprint">Local-first storage · Read-only access · Your tokens stay on your PC</p>
    </div><div class="shot"><img src="/screenshot.png" alt="Redexa Social overview showing total audience, recent views, interactions and per-platform performance"></div>
  </section>

  <section class="proof" aria-label="Product highlights"><div><strong>4 platforms</strong>One private workspace</div><div><strong>Read-only</strong>No posting permissions</div><div><strong>Local-first</strong>Analytics stay on your PC</div><div><strong>Free to start</strong>Upgrade only when ready</div></section>

  <div class="section-head"><p class="eyebrow">Clarity over clutter</p><h2>Everything you need to make the next post count.</h2><p>Stop switching tabs and guessing. Redexa turns scattered performance data into a practical daily workflow.</p></div>

  <section id="features" class="grid">
    <div class="card">
      <span class="number">01 / OVERVIEW</span>
      <h3>Single overview</h3>
      <p>YouTube, Instagram, TikTok and X side by side, with trends over time instead of four separate apps.</p>
    </div>
    <div class="card">
      <span class="number">02 / TIMING</span>
      <h3>Analytics that answer "what's working"</h3>
      <p>Top-performing content and a 24-hour chart of your best posting windows, per platform.</p>
    </div>
    <div class="card">
      <span class="number">03 / HEALTH</span>
      <h3>Diagnostics, not just numbers</h3>
      <p>Flags stalled accounts, zero-view content and access problems — each with a concrete next step.</p>
    </div>
    <div class="card">
      <span class="number">04 / INSIGHTS</span>
      <h3>Automatic insights</h3>
      <p>Computed locally from your own data. No AI calls, no extra cost, nothing sent anywhere.</p>
    </div>
    <div class="card">
      <span class="number">05 / EXPORT</span>
      <h3>CSV export</h3>
      <p>Take the collected data with you — spreadsheets, reports, whatever you need it for.</p>
    </div>
    <div class="card">
      <span class="number">06 / YOUR WAY</span>
      <h3>9 themes, 6 languages</h3>
      <p>English, Spanish, French, German, Italian and Japanese, plus nine themes for your workspace.</p>
    </div>
  </section>

  <section id="privacy" class="trust">
    <h2>Useful analytics without becoming the product.</h2>
    <p>Statistics and account permissions are stored in your Windows app-data folder, not in a central analytics cloud. Redexa talks directly to official platform APIs; only the Instagram and TikTok token exchange passes through a minimal proxy, without storing your analytics. <a href="/privacy">Read the privacy policy.</a></p>
  </section>

  <div class="section-head" id="pricing"><p class="eyebrow">Simple plans</p><h2>Start free. Scale when the workflow proves itself.</h2></div>
  <section class="pricing"><div class="price"><h3>Free</h3><p>Learn the workflow with one connected account.</p><div class="amount">€0</div><ul><li>One account</li><li>Core overview</li><li>Local storage</li></ul><a class="btn ghost" href="${DOWNLOAD_URL}">Download free</a></div><div class="price featured"><h3>Pro</h3><p>For creators building a repeatable publishing system.</p><div class="amount">€12 <small>/ month</small></div><ul><li>Up to three accounts</li><li>Full history and exports</li><li>Advanced insights</li></ul><a class="btn primary" href="${DOWNLOAD_URL}">Get Redexa Social</a></div><div class="price"><h3>Studio</h3><p>For teams managing a wider portfolio.</p><div class="amount">€39 <small>/ month</small></div><ul><li>Up to ten accounts</li><li>Everything in Pro</li><li>Built for multi-brand work</li></ul><a class="btn ghost" href="${DOWNLOAD_URL}">Download the app</a></div></section>

  <section class="final"><h2>Make your next move obvious.</h2><p>Bring your channels together and find the signal behind the numbers.</p><a class="btn primary" href="${DOWNLOAD_URL}">Download Redexa Social</a></section>

  <footer class="site">
    <span>© 2026 Aurelio Avila. All rights reserved.</span>
    <span><a href="/privacy">Privacy policy</a> · <a href="/terms">Terms of service</a> · <a href="/data-deletion">Data deletion</a> · <a href="https://github.com/AurelioAvila/social-dashboard">Source on GitHub</a></span>
  </footer>
</div>
</body></html>`);
}

function guidePage({ slug, label, title, description, paragraphs }) {
  const canonical = `https://redexa.getcertsprint.com/${slug}`;
  const article = paragraphs.map(({ heading, body }) => `<section><h2>${heading}</h2><p>${body}</p></section>`).join('');
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title} | Redexa Social</title><meta name="description" content="${description}"><link rel="canonical" href="${canonical}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Redexa Social"><meta property="og:title" content="${title}"><meta property="og:description" content="${description}"><meta property="og:url" content="${canonical}"><meta property="og:image" content="https://redexa.getcertsprint.com/redexa-social-overview.png?v=191">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${title}"><meta name="twitter:description" content="${description}"><meta name="twitter:image" content="https://redexa.getcertsprint.com/redexa-social-overview.png?v=191">
<link rel="icon" href="/icon.png?v=191"><style>${HOME_STYLE}.article{max-width:820px;margin:72px auto 100px}.article h1{font-size:clamp(40px,6vw,64px)}.article section{margin:48px 0}.article section h2{font-size:25px}.article section p{color:var(--muted);font-size:17px}.article .shot{margin:42px 0;transform:none}</style></head><body><div class="wrap"><header class="site"><a class="brand" href="/"><img src="/icon.png?v=191" alt=""><span>Redexa Social</span></a><nav class="site"><a href="/#features">Features</a><a href="/#pricing">Pricing</a><a href="${DOWNLOAD_URL}">Download</a></nav></header><main class="article"><p class="eyebrow">${label}</p><h1>${title}</h1><p class="sub">${description}</p><div class="cta-row"><a class="btn primary" href="${DOWNLOAD_URL}">Download for Windows</a><a class="btn ghost" href="/">Explore Redexa Social</a></div><div class="shot"><img src="/redexa-social-overview.png?v=191" alt="Redexa Social creator analytics workspace"></div>${article}</main><footer class="site"><span>© 2026 Aurelio Avila.</span><span><a href="/privacy">Privacy</a> · <a href="/terms">Terms</a> · <a href="https://github.com/AurelioAvila/social-dashboard">GitHub</a></span></footer></div></body></html>`);
}

export const localFirstPage = () => guidePage({
  slug: 'local-first-social-media-analytics', label: 'LOCAL-FIRST ANALYTICS',
  title: 'Social media analytics without surrendering your data',
  description: 'A private Windows analytics workspace that keeps creator metrics and encrypted credentials on your computer.',
  paragraphs: [
    { heading: 'Your workspace, not another data silo', body: 'Redexa Social stores account statistics, history and insights locally. It does not upload your analytics to a central Redexa database.' },
    { heading: 'Official, read-only connections', body: 'Connect supported accounts through official platform APIs with read-only permissions. Redexa cannot publish, edit or delete your content.' },
    { heading: 'Clarity without cloud lock-in', body: 'Review trends, diagnostics and publishing-time suggestions in one desktop workspace, then export your data when you need it elsewhere.' },
  ],
});

export const youtubeAnalyticsPage = () => guidePage({
  slug: 'youtube-analytics-dashboard', label: 'YOUTUBE ANALYTICS FOR WINDOWS',
  title: 'Understand YouTube performance from one focused dashboard',
  description: 'Track channel growth, recent views and top content in a private creator analytics workspace for Windows.',
  paragraphs: [
    { heading: 'See the signal faster', body: 'Bring subscriber growth, views and recent content into a clean overview designed for daily decisions instead of endless reporting tabs.' },
    { heading: 'Find stronger publishing windows', body: 'Use your own channel history to understand when content performs best and where consistency starts to slip.' },
    { heading: 'Keep platform access under control', body: 'Google authorization stays read-only, credentials are encrypted with Windows DPAPI, and access can be revoked from your Google account at any time.' },
  ],
});

export const multiPlatformPage = () => guidePage({
  slug: 'multi-platform-creator-analytics', label: 'CROSS-PLATFORM CREATOR ANALYTICS',
  title: 'Bring every channel into one creator command center',
  description: 'Compare YouTube, Instagram, TikTok and X performance without juggling separate analytics tabs.',
  paragraphs: [
    { heading: 'One consistent view', body: 'Redexa Social normalizes the signals that matter across supported platforms while preserving the context of each individual network.' },
    { heading: 'Diagnostics with a next step', body: 'Spot stale accounts, authorization problems and unusual performance drops, then see a concrete action instead of a vague warning.' },
    { heading: 'Built to grow with your portfolio', body: 'Start with one account, then move to Pro or Studio when you need deeper history, exports and more connected brands.' },
  ],
});

export function privacyPage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Redexa Social — Privacy Policy</title><style>${STYLE}</style></head><body>
<h1>Privacy Policy — Redexa Social</h1>
<p>Last updated: August 18, 2026.</p>

<p>Redexa Social is a desktop application that shows the statistics of
your YouTube, Instagram, TikTok and X accounts in a single window. This
page explains what data is handled and how.</p>

<h2>Where your data lives</h2>
  <p>All the data the app collects — access tokens, statistics, content
history — stays <strong>exclusively on your computer</strong>, in a local
SQLite database under <code>%APPDATA%\RedexaSocial</code>. Existing installations are migrated automatically. There is no Redexa Social server
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
<p>You can also revoke Redexa Social's access to your accounts directly
from the security settings of YouTube (Google), Instagram (Meta), TikTok or
X, at any time.</p>

<h2>Contact</h2>
<p>For questions about this policy, open an issue on
<a href="https://github.com/AurelioAvila/social-dashboard/issues">GitHub</a>.</p>

<footer>Redexa Social</footer>
</body></html>`);
}

export function termsPage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Redexa Social — Terms of Service</title><style>${STYLE}</style></head><body>
<h1>Terms of Service — Redexa Social</h1>
<p>Last updated: August 18, 2026.</p>

<p>These terms govern the use of Redexa Social, a desktop application
that shows the statistics of your social accounts (YouTube, Instagram,
TikTok, X) in a single window. By using the app, you accept the following.</p>

<h2>What the app does</h2>
<p>Redexa Social reads, with your authorization, the public statistics of
your social accounts through the official APIs of the respective platforms,
and displays them locally. The app doesn't publish content, doesn't change
account settings, and doesn't share your data with third parties, except as
described in the <a href="/privacy">privacy policy</a>.</p>

<h2>Accounts and connections</h2>
<p>You're responsible for keeping your social account credentials
confidential. You can link and unlink accounts at any time from the app.
Redexa Social is not affiliated with YouTube, Instagram, TikTok or X:
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
<p>Redexa Social and its source code are proprietary and © 2026 Aurelio
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

<footer>Redexa Social</footer>
</body></html>`);
}

export function dataDeletionPage() {
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Redexa Social — Data Deletion Instructions</title><style>${STYLE}</style></head><body>
<h1>Data Deletion Instructions — Redexa Social</h1>
<p>Last updated: August 28, 2026.</p>

<p>Redexa Social is a local-first desktop application: it does not have a
server that stores your account data, so there is nothing on our side to
delete on request. Everything the app knows about your accounts — access
tokens, statistics, content history — lives only in a SQLite database on
your own computer. Deleting it is something you do directly, in full
control, without waiting on us.</p>

<h2>Delete a single connected account</h2>
<ol>
  <li>Open Redexa Social.</li>
  <li>Go to the "Link account" screen.</li>
  <li>Choose the account you want to remove and select <strong>Unlink</strong>.</li>
</ol>
<p>The corresponding access token is deleted immediately from the local
database. Nothing is sent to us — there is nothing for us to receive.</p>

<h2>Delete everything the app has stored</h2>
<ul>
  <li>Uninstall Redexa Social through Windows' usual "Apps" settings, which
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

<footer>Redexa Social</footer>
</body></html>`);
}
