/**
 * Token exchange proxy for Redexa Social.
 *
 * Copyright (c) 2026 Aurelio Avila. All rights reserved.
 *
 * Why it exists: Instagram and TikTok require the client secret to turn an
 * OAuth `code` into a token. Compiling that secret into a distributed
 * executable means handing it to everyone who downloads the app — unpacking
 * the binary is enough to read it back in the clear. Meta forbids this
 * explicitly for its own app secret.
 *
 * Here the secrets are Worker environment variables and never leave the
 * server: the app sends the `code` and gets the token back.
 *
 * Deployment: see README.md in this folder.
 *
 * Endpoints:
 *   POST /exchange {platform, code, redirect_uri}  -> {access_token, ...}
 *   POST /refresh  {platform, refresh_token}       -> {access_token, scope}
 *
 * Licence issuing (licensing.js) lives here too, for the same reason: the
 * Stripe secret key cannot sit in a distributed executable, and a local app
 * cannot decide for itself who has paid.
 *   POST /checkout        -> a payment URL
 *   POST /stripe/webhook  -> the licence is issued
 *   GET  /license/claim   -> the page where the customer reads their key
 *   POST /license/verify  -> the app unlocks the plan
 */
import { createCheckout, handleWebhook, verifyLicense, claimPage, createBillingPortal } from './licensing.js';
import { sendPasswordChanged, sendResetCode, sendWelcome } from './mail.js';
import { homePage, privacyPage, termsPage, dataDeletionPage, faviconAsset, iconAsset, screenshotAsset, robotsTxt, sitemapXml } from './branding.js';

const JSON_HEADERS = { 'content-type': 'application/json' };

const SECURITY_HEADERS = {
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
  // Begin in report-only mode so platform review pages and payment return
  // flows can be observed before the policy is made blocking.
  'Content-Security-Policy-Report-Only': [
    "default-src 'none'",
    "base-uri 'none'",
    "frame-ancestors 'none'",
    "form-action 'self' https://checkout.stripe.com",
    "img-src 'self' data:",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    'font-src https://fonts.gstatic.com',
    "script-src 'self' 'unsafe-inline'",
    "connect-src 'self'",
  ].join('; '),
};

function withSecurityHeaders(response) {
  const secured = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
    secured.headers.set(name, value);
  }
  return secured;
}

// The only return addresses this proxy accepts for the OAuth code exchange.
// They are the static GitHub Pages registered in the Meta and TikTok apps:
// any other value cannot have come from one of our logins.
const ALLOWED_REDIRECTS = new Set([
  'https://aurelioavila.github.io/social-dashboard/instagram-callback',
  'https://aurelioavila.github.io/social-dashboard/tiktok-callback',
]);

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
}

/** The platform's raw body is not passed back to the client: it may carry
 *  details the app has no use for. Only a useful message is returned. */
function fail(message, status = 400) {
  return json({ error: message }, status);
}

async function instagramExchange(env, code, redirectUri) {
  const short = await fetch('https://api.instagram.com/oauth/access_token', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: env.INSTAGRAM_APP_ID,
      client_secret: env.INSTAGRAM_APP_SECRET,
      grant_type: 'authorization_code',
      redirect_uri: redirectUri,
      code,
    }),
  });
  if (!short.ok) return fail('instagram_code_rejected', 400);
  const shortData = await short.json();

  // The short-lived token lasts an hour, so it is swapped straight away for
  // the sixty-day one.
  const longUrl = new URL('https://graph.instagram.com/access_token');
  longUrl.searchParams.set('grant_type', 'ig_exchange_token');
  longUrl.searchParams.set('client_secret', env.INSTAGRAM_APP_SECRET);
  longUrl.searchParams.set('access_token', shortData.access_token);
  const long = await fetch(longUrl);
  if (!long.ok) return fail('instagram_token_exchange_failed', 400);
  const longData = await long.json();

  return json({ access_token: longData.access_token, expires_in: longData.expires_in });
}

async function tiktokToken(env, params) {
  const resp = await fetch('https://open.tiktokapis.com/v2/oauth/token/', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_key: env.TIKTOK_CLIENT_KEY,
      client_secret: env.TIKTOK_CLIENT_SECRET,
      ...params,
    }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok || !data.access_token) return fail('tiktok_request_rejected', 400);
  // Only what the app needs is returned.
  return json({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    open_id: data.open_id,
    scope: data.scope,
    expires_in: data.expires_in,
  });
}

async function handleRequest(request, env) {
    const url = new URL(request.url);
    const action = url.pathname.replace(/^\/+|\/+$/g, '');

    // --- Pagine pubbliche (branding, verifica OAuth) --------------------
    // Served from here rather than GitHub Pages — see the comment in
    // branding.js for why. They answer both on the workers.dev domain and on
    // any custom domain attached to this Worker.
    if (request.method === 'GET') {
      if (action === '') return homePage();
      if (action === 'privacy') return privacyPage();
      if (action === 'terms') return termsPage();
      if (action === 'data-deletion') return dataDeletionPage();
      if (action === 'favicon.png') return faviconAsset();
      if (action === 'icon.png') return iconAsset();
      if (action === 'screenshot.png') return screenshotAsset();
      if (action === 'robots.txt') return robotsTxt();
      if (action === 'sitemap.xml') return sitemapXml();
      // TikTok's URL-prefix ownership check for the Login Kit app review -
      // the exact filename and content TikTok generated when verifying
      // socialdashboard.getcertsprint.com as this app's Web/Desktop URL.
      if (action === 'tiktokJlrPTn3QSB0uMIqRXZRBk2qpis7pA8e9.txt') {
        return new Response('tiktok-developers-site-verification=JlrPTn3QSB0uMIqRXZRBk2qpis7pA8e9\n', {
          headers: { 'content-type': 'text/plain; charset=utf-8' },
        });
      }
    }

    // --- Licenze -------------------------------------------------------
    // Before the token exchange: these are the only endpoints that accept GET
    // (the claim page) and that read the raw body — Stripe's signature is
    // computed over the exact bytes, not over re-serialised JSON.
    if (action === 'license/claim') {
      if (request.method !== 'GET') return fail('method_not_allowed', 405);
      return claimPage(env, url);
    }

    if (action === 'license/cancelled') {
      // The same destination for a cancelled payment and for someone leaving
      // the subscription portal: in both cases nothing happened that needs
      // this page to stay open.
      return new Response(
        '<!doctype html><meta charset="utf-8"><title>Redexa Social</title>' +
          '<style>body{margin:0;min-height:100vh;display:flex;align-items:center;' +
          'justify-content:center;background:#0f1115;color:#e8eaf0;font:16px system-ui}</style>' +
          '<div>You can close this tab and go back to Redexa Social.</div>',
        { headers: { 'content-type': 'text/html; charset=utf-8' } }
      );
    }

    // --- Transactional email (local account, not licences) -------------
    if (action === 'mail/reset-code' && request.method === 'POST') {
      return sendResetCode(env, request);
    }
    if (action === 'mail/welcome' && request.method === 'POST') {
      return sendWelcome(env, request);
    }
    if (action === 'mail/password-changed' && request.method === 'POST') {
      return sendPasswordChanged(env, request);
    }

    if (action === 'stripe/webhook') {
      if (request.method !== 'POST') return fail('method_not_allowed', 405);
      return handleWebhook(env, request);
    }

    if (request.method !== 'POST') return fail('method_not_allowed', 405);

    let body;
    try {
      body = await request.json();
    } catch {
      return fail('bad_request', 400);
    }

    if (action === 'checkout') return createCheckout(env, body);
    if (action === 'license/verify') return verifyLicense(env, body);
    if (action === 'billing/portal') return createBillingPortal(env, body);

    // --- OAuth token exchange ------------------------------------------
    const platform = body.platform;
    if (platform !== 'instagram' && platform !== 'tiktok') {
      return fail('platform_unsupported', 400);
    }

    if (action === 'exchange') {
      if (!body.code || !body.redirect_uri) return fail('missing_params', 400);
      // The redirect has to be one of ours. This endpoint exchanges a code
      // using OUR client secret: accepting any address would turn it into a
      // public service that converts any code from our app into a token, for
      // anyone who manages to get hold of one.
      if (!ALLOWED_REDIRECTS.has(String(body.redirect_uri).trim())) {
        return fail('redirect_not_allowed', 400);
      }
      if (platform === 'instagram') {
        return instagramExchange(env, body.code, body.redirect_uri);
      }
      return tiktokToken(env, {
        code: body.code,
        grant_type: 'authorization_code',
        redirect_uri: body.redirect_uri,
      });
    }

    if (action === 'refresh') {
      if (!body.refresh_token) return fail('missing_params', 400);
      // Instagram refreshes the long-lived token without a secret, so the app
      // does that itself; only TikTok needs this.
      if (platform !== 'tiktok') return fail('refresh_not_needed', 400);
      return tiktokToken(env, {
        grant_type: 'refresh_token',
        refresh_token: body.refresh_token,
      });
    }

    return fail('unknown_endpoint', 404);
}

export default {
  async fetch(request, env) {
    return withSecurityHeaders(await handleRequest(request, env));
  },
};
