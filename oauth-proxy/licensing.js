/**
 * Licences: purchase, issue and verification.
 *
 * Copyright (c) 2026 Aurelio Avila. All rights reserved.
 *
 * Why this lives here and not in the app: the Stripe secret key cannot sit
 * inside a distributed executable — it can be read straight back out of the
 * binary — and an app running only on the customer's computer cannot decide
 * for itself who has paid, since the record of who owns what would be sitting
 * on the machine of the person who is supposed to pay.
 *
 * The flow:
 *   1. the app calls POST /checkout        -> a Stripe payment URL
 *   2. the customer pays on Stripe's page
 *   3. Stripe calls POST /stripe/webhook   -> the key is issued here and the
 *      email is sent with Resend
 *   4. the customer lands on GET /license/claim -> their key is shown
 *   5. the app calls POST /license/verify  -> the plan is unlocked
 *
 * Keys live in KV (the LICENSES namespace), indexed both by key and by Stripe
 * session id, which is what step 4 looks them up by.
 *
 * The email is not a nicety. Step 4's page is only reached if the customer's
 * browser stays open through Stripe's redirect: close the tab a moment too
 * early, or lose the network right then, and the key would be gone with no
 * second way to recover it. A failed send must not block the key from being
 * issued, though, nor make Stripe retry the webhook — so it is attempted,
 * the outcome is recorded, and the landing page says honestly what happened
 * instead of promising a Stripe receipt that will never contain the key.
 */
import { codeBlock, layout, paragraph, sendMail } from './email-layout.js';

const JSON_HEADERS = { 'content-type': 'application/json' };

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
}

/** The client gets a code, not a sentence: the app exists in six languages
 *  and the wording has to be written in the one the user chose. */
function fail(code, status = 400) {
  return json({ error: code }, status);
}

// I prezzi stanno sul server: se stessero nell'app, chi la modifica potrebbe
// have a zero-euro payment session generated for themselves.
const PLANS = {
  pro: { name: 'Pro', monthly: 1200, yearly: 12000 },
  studio: { name: 'Studio', monthly: 3900, yearly: 39000 },
};

// How many distinct installations one key may activate. Studio is meant for
// agencies working from several machines, so it is given more room.
const DEVICE_LIMITS = { pro: 3, studio: 5 };

// No visually ambiguous characters: no 0/O, no 1/I/L. A key misread and
// retyped by hand is an avoidable support request.
const KEY_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';

function newLicenseKey(plan) {
  let out = '';
  const unbiasedLimit = 256 - (256 % KEY_ALPHABET.length);
  for (let i = 0; i < 16;) {
    const byte = crypto.getRandomValues(new Uint8Array(1))[0];
    if (byte >= unbiasedLimit) continue;
    if (i > 0 && i % 4 === 0) out += '-';
    out += KEY_ALPHABET[byte % KEY_ALPHABET.length];
    i += 1;
  }
  return `SD-${plan.toUpperCase()}-${out}`;
}

/**
 * Checks that the request genuinely came from Stripe.
 *
 * Without this, anyone could call the endpoint and have a licence issued to
 * them for free: this is the point where who has paid is decided.
 */
async function verifyStripeSignature(rawBody, header, secret) {
  if (!header || !secret) return false;

  const parts = Object.fromEntries(
    header.split(',').map((p) => p.split('=').map((s) => s.trim()))
  );
  const timestamp = parts.t;
  const expected = parts.v1;
  if (!timestamp || !expected) return false;

  // A valid but old signature is not enough: with no time window, anyone who
  // intercepted a request could replay it forever.
  const age = Math.abs(Date.now() / 1000 - Number(timestamp));
  if (!Number.isFinite(age) || age > 300) return false;

  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const sig = await crypto.subtle.sign(
    'HMAC',
    key,
    new TextEncoder().encode(`${timestamp}.${rawBody}`)
  );
  const computed = [...new Uint8Array(sig)]
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  // Constant-time comparison: an ordinary one stops at the first differing
  // character, which lets an attacker measure how close a guess came.
  if (computed.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < computed.length; i++) {
    diff |= computed.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return diff === 0;
}

/** Creates the payment session. The app sends only the plan and the billing
 *  cycle; the amount and the currency are the server's decision. */
export async function createCheckout(env, body) {
  const plan = PLANS[body.plan];
  if (!plan) return fail('plan_unknown');
  if (!env.STRIPE_SECRET_KEY) return fail('checkout_unavailable', 503);

  const yearly = body.cycle === 'yearly';
  const amount = yearly ? plan.yearly : plan.monthly;
  // The return URLs are ours (env.PUBLIC_URL), never the ones sent by the
  // client. An origin used to be built here from body.return_to as well: it
  // was used nowhere, but it was enough to blow the endpoint up with a 500
  // when the value was not a valid URL — and it would have become an open
  // redirect the day anyone actually used it.
  const self = env.PUBLIC_URL || '';

  const form = new URLSearchParams({
    mode: 'subscription',
    'line_items[0][quantity]': '1',
    'line_items[0][price_data][currency]': 'eur',
    'line_items[0][price_data][unit_amount]': String(amount),
    'line_items[0][price_data][recurring][interval]': yearly ? 'year' : 'month',
    'line_items[0][price_data][product_data][name]': `Social Dashboard ${plan.name}`,
    // Required by the Stripe account, which has automatic tax enabled: with
    // no tax code on the product the session is rejected.
    // txcd_10103001 = remotely accessed SaaS software, no physical medium.
    'line_items[0][price_data][product_data][tax_code]': 'txcd_10103001',
    'metadata[plan]': body.plan,
    // The key is claimed from here: the page shows it large and copyable.
    success_url: `${self}/license/claim?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${self}/license/cancelled`,
    // Shows the "promotion code" field on Stripe's payment page. Without it a
    // promotion code created in the dashboard has nowhere to be typed, and the
    // session would refuse it even though the code exists and is valid.
    allow_promotion_codes: 'true',
  });
  if (body.email) form.set('customer_email', body.email);

  const resp = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      'content-type': 'application/x-www-form-urlencoded',
    },
    body: form,
  });
  if (!resp.ok) {
    console.log('stripe checkout failed', resp.status, (await resp.text()).slice(0, 300));
    return fail('checkout_failed', 502);
  }
  const data = await resp.json();
  return json({ url: data.url });
}

// The key email is sent from here. A dedicated subdomain rather than the
// main domain, so that if the sending reputation were to suffer — bounces,
// spam reports — it would not drag another product down with it.
//
// The domain itself is wrong and configurable for that reason: it belongs to
// CertSprint, so a Social Dashboard customer currently receives their licence
// from a product they have never heard of. Set LICENSE_FROM to a Social
// Dashboard address once one exists.
const DEFAULT_LICENSE_FROM = 'Social Dashboard <licenses@mail.getcertsprint.com>';
const licenseFrom = (env) => env.LICENSE_FROM || DEFAULT_LICENSE_FROM;

// Where a sale is announced. Defaults to the owner's own address so the
// notification works before anything is configured; override with OWNER_INBOX.
const ownerInbox = (env) => env.OWNER_INBOX || 'canadesino91@gmail.com';

const SITE = 'https://socialdashboard.getcertsprint.com';

function licenseEmailHtml(plan, key) {
  const planName = PLANS[plan]?.name || plan;
  return layout({
    preview: `Your Social Dashboard ${planName} license key`,
    eyebrow: 'Payment complete',
    heading: 'Your license key is ready.',
    body: paragraph(`Your ${planName} license for Social Dashboard is active.`)
      + codeBlock(key)
      + paragraph(`Paste this key into Social Dashboard under "Your account" to activate ${planName}. Keep this email — it is the only copy sent to you.`)
      + paragraph('Stripe sends the payment receipt separately; this email is the key itself.'),
    footer: 'This email carries the license you just bought. Store it somewhere you can find again.',
  });
}

/** The plain-text twin of the licence email. The key has to survive a client
 *  that strips HTML — losing it there would mean losing the purchase. */
function licenseEmailText(plan, key) {
  const planName = PLANS[plan]?.name || plan;
  return `Your Social Dashboard ${planName} license is active.

License key: ${key}

Paste it into Social Dashboard under "Your account" to activate ${planName}. Keep this email - it is the only copy sent to you. Stripe sends the payment receipt separately.`;
}

/**
 * Tells the owner a sale happened.
 *
 * Nothing did this before: a licence was issued, the customer was emailed,
 * and the person selling found out only by looking at Stripe. Best-effort in
 * the same way as the customer's email — this must never be the reason a
 * webhook fails and Stripe retries it.
 */
async function notifyOwnerOfSale(env, { plan, email, key }) {
  const name = PLANS[plan]?.name || plan;
  const html = `<p>Someone just bought Social Dashboard.</p>
     <p><strong>Plan:</strong> ${escapeHtml(name)}<br>
        <strong>Account:</strong> ${escapeHtml(email || '(no address given to Stripe)')}<br>
        <strong>Licence:</strong> ${escapeHtml(key)}</p>
     <p>Stripe has the payment; this is only the heads-up.</p>`;
  const text = `Someone just bought Social Dashboard.

Plan: ${name}
Account: ${email || '(no address given to Stripe)'}
Licence: ${key}

Stripe has the payment; this is only the heads-up.`;
  return sendWithResend(env, ownerInbox(env), `New Social Dashboard sale — ${name}`, html, text);
}

/** One way out to Resend, shared by the customer's key email, the owner's
 *  sale notice and the revocation notice. Never throws: a failure here must
 *  not fail the webhook, which Stripe would then retry, nor stop the key
 *  from existing and being reachable from the landing page. Returns whether
 *  it actually went. */
async function sendWithResend(env, to, subject, html, text) {
  return sendMail(env, { from: licenseFrom(env), to, subject, html, text });
}

/** Sends the key to the customer. */
async function sendLicenseEmail(env, to, plan, key) {
  return sendWithResend(
    env,
    to,
    'Your Social Dashboard license key',
    licenseEmailHtml(plan, key),
    licenseEmailText(plan, key),
  );
}

/**
 * Tells the customer their licence stopped working, and why.
 *
 * Until this existed, `subscription.deleted` and `invoice.payment_failed`
 * flipped the key to inactive and told nobody: the app simply stopped
 * unlocking one day. Someone whose card expired reads that as the product
 * breaking, and asks their bank rather than us — a chargeback instead of a
 * card update. The two cases are deliberately worded differently, because a
 * failed payment is recoverable and a cancellation is a choice.
 */
async function notifyLicenceRevoked(env, { to, plan, reason }) {
  const planName = PLANS[plan]?.name || plan;
  const failed = reason === 'payment_failed';
  const heading = failed ? 'Your payment did not go through.' : 'Your subscription has ended.';
  const explain = failed
    ? `We could not charge the card on your Social Dashboard ${planName} subscription, so the license is inactive for now. Updating the card restores it — the key you already have starts working again, and nothing on your computer was touched.`
    : `Your Social Dashboard ${planName} subscription has ended, so the license is now inactive. Subscribing again reactivates it.`;
  return sendWithResend(
    env,
    to,
    failed ? 'Your Social Dashboard payment failed' : 'Your Social Dashboard subscription has ended',
    layout({
      preview: failed ? 'Your Social Dashboard license is inactive after a failed payment' : 'Your Social Dashboard license is now inactive',
      eyebrow: failed ? 'Payment failed' : 'Subscription ended',
      heading,
      body: paragraph(explain)
        + paragraph('Your data has not been deleted. It never left your computer in the first place, so it is all still there when you come back.'),
      cta: { label: failed ? 'Update your card' : 'Subscribe again', url: SITE },
      footer: 'This email is sent when a Social Dashboard license changes state. Stripe handles the payment itself.',
    }),
    `${heading}

${explain}

Your data has not been deleted — it never left your computer.

${SITE}`,
  );
}

/** Stripe confirms the payment; the licence is created here. */
export async function handleWebhook(env, request) {
  const raw = await request.text();
  const ok = await verifyStripeSignature(
    raw,
    request.headers.get('stripe-signature'),
    env.STRIPE_WEBHOOK_SECRET
  );
  if (!ok) return fail('bad_signature', 400);

  const event = JSON.parse(raw);
  const obj = event.data?.object || {};

  if (event.type === 'checkout.session.completed') {
    const plan = obj.metadata?.plan;
    if (!PLANS[plan]) return json({ received: true });

    const key = newLicenseKey(plan);
    const email = obj.customer_email || obj.customer_details?.email || '';
    const record = {
      key,
      plan,
      email,
      customer: obj.customer || '',
      subscription: obj.subscription || '',
      status: 'active',
      issued_at: Date.now(),
      email_sent: false,
    };
    if (email) {
      record.email_sent = await sendLicenseEmail(env, email, plan, key);
    }
    // The owner used to learn about a sale only by going to look at Stripe.
    // Deliberately not awaited into the record: whether the heads-up arrived
    // is of no interest to the customer or to the landing page.
    await notifyOwnerOfSale(env, { plan, email, key });
    await env.LICENSES.put(`key:${key}`, JSON.stringify(record));
    // Indexed by session id as well: this is what the page that shows the
    // customer their key immediately after payment looks up.
    await env.LICENSES.put(`session:${obj.id}`, key, { expirationTtl: 60 * 60 * 24 * 30 });
    if (record.subscription) {
      await env.LICENSES.put(`sub:${record.subscription}`, key);
    }
    return json({ received: true });
  }

  // Back to paying. Stripe fires invoice.payment_failed on the *first* failed
  // attempt, then retries the invoice for days, and the revocation email tells
  // the customer to update their card in the portal — so recovery is the
  // normal outcome, not the rare one. Neither the retry succeeding nor the new
  // card reached this handler: only checkout.session.completed ever set a
  // licence back to active, so a customer whose payment recovered went on
  // being billed with a dead key until somebody edited KV by hand.
  //
  // invoice.paid is itself the evidence of payment. For subscription.updated
  // Stripe's own status is the authority: active and trialing entitle, and
  // anything else (past_due, unpaid, incomplete) does not. Note this does not
  // move the plan — rec.plan comes from the checkout metadata, so a tier
  // change made inside the portal is still not reflected anywhere.
  if (event.type === 'invoice.paid' || event.type === 'customer.subscription.updated') {
    const subId = event.type === 'invoice.paid' ? obj.subscription : obj.id;
    const entitled = event.type === 'invoice.paid'
      || obj.status === 'active' || obj.status === 'trialing';
    const key = subId && (await env.LICENSES.get(`sub:${subId}`));
    if (key) {
      const rec = await env.LICENSES.get(`key:${key}`, 'json');
      if (rec) {
        rec.status = entitled ? 'active' : 'inactive';
        if (entitled) delete rec.revoked_at;
        else rec.revoked_at = Date.now();
        await env.LICENSES.put(`key:${key}`, JSON.stringify(rec));
      }
    }
    // No email either way. The app rechecks on its own and starts working
    // again; a customer who has just fixed their card does not need a second
    // message about it, and one who is still past_due already got the first.
    return json({ received: true });
  }

  // Subscription ended or payment failed: the licence stops being valid.
  if (event.type === 'customer.subscription.deleted' || event.type === 'invoice.payment_failed') {
    const subId = event.type === 'invoice.payment_failed' ? obj.subscription : obj.id;
    const key = subId && (await env.LICENSES.get(`sub:${subId}`));
    if (key) {
      const rec = await env.LICENSES.get(`key:${key}`, 'json');
      if (rec) {
        // Only on the way out of "active". Stripe retries a failed invoice
        // several times over a week and fires the event each time; without
        // this the customer would be told four times that the same payment
        // failed, which reads as broken rather than helpful.
        const wasActive = rec.status === 'active';
        rec.status = 'inactive';
        rec.revoked_at = Date.now();
        await env.LICENSES.put(`key:${key}`, JSON.stringify(rec));
        if (wasActive && rec.email) {
          // Best-effort, like every other send here: Stripe must not retry
          // the whole webhook because a notice did not go out.
          await notifyLicenceRevoked(env, {
            to: rec.email,
            plan: rec.plan,
            reason: event.type === 'invoice.payment_failed' ? 'payment_failed' : 'cancelled',
          });
        }
      }
    }
    return json({ received: true });
  }

  return json({ received: true });
}

/** The app asks whether a key is valid and what it unlocks. */
export async function verifyLicense(env, body) {
  const key = String(body.key || '').trim().toUpperCase();
  if (!key) return fail('license_missing');
  // A key that does not have our shape cannot exist in KV, so it is answered
  // immediately rather than looked up. It also keeps long or strange values
  // away from KV, where they would fail the read with a 500 instead of a
  // plain "invalid key".
  if (!/^SD-[A-Z]+-[A-Z0-9-]{4,40}$/.test(key)) {
    return json({ valid: false, reason: 'license_not_found' });
  }

  const rec = await env.LICENSES.get(`key:${key}`, 'json');
  if (!rec) return json({ valid: false, reason: 'license_not_found' });
  if (rec.status !== 'active') return json({ valid: false, reason: 'license_inactive' });

  // Counts how many distinct installations are using this key, so that one
  // key paid for once does not become shareable with any number of people.
  // It is not meant to stop someone who rebuilds the app with the check
  // removed — that stays possible for anyone who reads the source, open
  // licence or not — but it does stop a single key from carrying dozens of
  // independent activations.
  const deviceId = typeof body.device_id === 'string' ? body.device_id.trim().slice(0, 128) : '';
  if (deviceId) {
    if (!Array.isArray(rec.devices)) {
      // A key issued before this check existed: the first device to turn up
      // is recorded, rather than penalising someone who had already
      // activated it legitimately.
      rec.devices = [deviceId];
      await env.LICENSES.put(`key:${key}`, JSON.stringify(rec));
    } else if (!rec.devices.includes(deviceId)) {
      if (!body.register) {
        // A background check must never be able to add a device on its own:
        // if this one was never explicitly activated, it has to go back and
        // do that before the plan is unlocked.
        return json({ valid: false, reason: 'license_reactivate_needed' });
      }
      const limit = DEVICE_LIMITS[rec.plan] || 1;
      if (rec.devices.length >= limit) {
        return json({ valid: false, reason: 'license_device_limit', limit });
      }
      rec.devices.push(deviceId);
      await env.LICENSES.put(`key:${key}`, JSON.stringify(rec));
    }
  }

  return json({ valid: true, plan: rec.plan, email: rec.email, issued_at: rec.issued_at });
}

/** Opens Stripe's customer portal, which is where someone can actually
 *  cancel, change their payment method or read their invoices. Cancellation
 *  is deliberately not reimplemented here: the portal Stripe hosts is already
 *  what subscription rules — such as cancelling being as easy as signing up —
 *  expect to find. */
export async function createBillingPortal(env, body) {
  const key = String(body.key || '').trim().toUpperCase();
  if (!key) return fail('license_missing');
  // The same shape verifyLicense requires: a key that cannot exist should not
  // reach KV at all.
  if (!/^SD-[A-Z]+-[A-Z0-9-]{4,40}$/.test(key)) return fail('license_not_found');
  if (!env.STRIPE_SECRET_KEY) return fail('checkout_unavailable', 503);

  const rec = await env.LICENSES.get(`key:${key}`, 'json');
  // The same message for a key that does not exist and for one with no Stripe
  // customer behind it, such as a key issued by hand: someone guessing keys is
  // given no way to tell the two apart.
  if (!rec || !rec.customer) return fail('license_not_found');

  const self = env.PUBLIC_URL || '';
  const form = new URLSearchParams({
    customer: rec.customer,
    return_url: `${self}/license/cancelled`,
  });
  const resp = await fetch('https://api.stripe.com/v1/billing_portal/sessions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      'content-type': 'application/x-www-form-urlencoded',
    },
    body: form,
  });
  if (!resp.ok) {
    console.log('stripe portal failed', resp.status, (await resp.text()).slice(0, 300));
    return fail('checkout_failed', 502);
  }
  const data = await resp.json();
  return json({ url: data.url });
}

/** Neutralises text that ends up inside the HTML. The address comes from
 *  Stripe, which validates it, but a third-party value written into a page
 *  unfiltered is a door left open for nothing: closing it costs one line. */
function escapeHtml(value) {
  return String(value == null ? '' : value).replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
  );
}

function page(title, bodyHtml) {
  return new Response(
    `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title}</title><style>
:root{color-scheme:dark}
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
 background:#0f1115;color:#e8eaf0;font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;padding:24px}
.card{max-width:520px;width:100%;background:#171a21;border:1px solid #262b36;
 border-radius:18px;padding:32px;text-align:center}
h1{font-size:20px;margin:0 0 8px}
p{color:#9aa3b2;font-size:14px;margin:0 0 20px}
.key{font:700 20px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.04em;
 background:#0f1115;border:1px solid #3a4152;border-radius:12px;padding:16px;
 word-break:break-all;user-select:all;margin-bottom:16px}
button{background:linear-gradient(135deg,#6d8cff,#9d7bff);color:#0f1115;border:0;
 border-radius:10px;padding:12px 22px;font:700 14px system-ui;cursor:pointer}
.hint{font-size:13px;color:#6f7787;margin-top:18px}
</style></head><body><div class="card">${bodyHtml}</div></body></html>`,
    { headers: { 'content-type': 'text/html; charset=utf-8' } }
  );
}

/** The landing page after payment: it shows the key to paste into the app.
 *  This is the only moment the customer sees it, so it has to be impossible
 *  to get wrong. */
export async function claimPage(env, url) {
  const sessionId = url.searchParams.get('session_id');
  if (!sessionId) {
    return page('Social Dashboard', '<h1>Missing session</h1><p>No payment session was provided.</p>');
  }

  // The webhook and the browser's return are two parallel races: if the key
  // is not there yet, the page retries on its own instead of telling the
  // customer that something went wrong.
  const key = await env.LICENSES.get(`session:${sessionId}`);
  if (!key) {
    return new Response(
      `<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="2">
<title>Activating…</title><style>body{margin:0;min-height:100vh;display:flex;align-items:center;
justify-content:center;background:#0f1115;color:#e8eaf0;font:16px system-ui}</style>
<div>Activating your license…</div>`,
      { headers: { 'content-type': 'text/html; charset=utf-8' } }
    );
  }

  // The send status is the real one, recorded by the webhook: no copy is
  // promised by email unless one actually went out — no address given to
  // Stripe, Resend not configured, or the send failed.
  const rec = await env.LICENSES.get(`key:${key}`, 'json');
  const hint = rec?.email_sent
    ? `A copy was also emailed to ${escapeHtml(rec.email)}.`
    : 'This is the only copy of your key — no email is sent, so keep it somewhere safe before leaving this page.';

  return page(
    'Your license key',
    `<h1>Payment complete</h1>
<p>Copy this key and paste it into Social Dashboard under <strong>Your account</strong>.</p>
<div class="key" id="k">${key}</div>
<button onclick="navigator.clipboard.writeText(document.getElementById('k').textContent.trim());this.textContent='Copied'">Copy key</button>
<div class="hint">${hint}</div>`
  );
}

export { fail, json };
