/**
 * Transactional email that has nothing to do with a licence: the password
 * reset code and the welcome message on registration. The same Resend key the
 * licences already use (licensing.js), kept in a separate file because these
 * are conceptually different messages — they concern the local account that
 * auth.py manages, not a Stripe purchase.
 *
 * Copyright (c) 2026 Aurelio Avila. All rights reserved.
 */
const MAIL_FROM = 'Social Dashboard <noreply@mail.getcertsprint.com>';
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/;

function fail(message, status = 400) {
  return new Response(JSON.stringify({ error: message }), { status, headers: { 'content-type': 'application/json' } });
}

function ok() {
  return new Response(JSON.stringify({ ok: true }), { headers: { 'content-type': 'application/json' } });
}

/** A fixed window in KV: N sends per address per hour. The precision of a
 *  real rate limiter is not needed here; this only has to stop a public
 *  endpoint from becoming a way to spam any mailbox at will. */
async function underLimit(env, address, max) {
  const bucket = `mailrate:${address}:${Math.floor(Date.now() / 3600000)}`;
  const current = parseInt((await env.LICENSES.get(bucket)) || '0', 10);
  if (current >= max) return false;
  await env.LICENSES.put(bucket, String(current + 1), { expirationTtl: 3700 });
  return true;
}

async function send(env, to, subject, html) {
  if (!env.RESEND_API_KEY || !to) return false;
  try {
    const resp = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { authorization: `Bearer ${env.RESEND_API_KEY}`, 'content-type': 'application/json' },
      body: JSON.stringify({ from: MAIL_FROM, to, subject, html }),
    });
    return resp.ok;
  } catch {
    return false;
  }
}

function shell(title, bodyHtml) {
  return `<!doctype html><html><body style="margin:0;background:#09090b;color:#e8eaf0;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;padding:32px 16px">
<div style="max-width:480px;margin:0 auto;background:#12131a;border:1px solid #262b36;border-radius:16px;padding:28px">
<h1 style="font-size:18px;margin:0 0 6px">${title}</h1>
${bodyHtml}
</div></body></html>`;
}

export async function sendResetCode(env, request) {
  const body = await request.json().catch(() => ({}));
  const to = String(body.to || '').trim().toLowerCase();
  const code = String(body.code || '').trim();
  if (!EMAIL_RE.test(to) || !/^\d{6}$/.test(code)) return fail('bad_request');
  if (!(await underLimit(env, to, 5))) return fail('rate_limited', 429);
  await send(env, to, 'Your Social Dashboard reset code', shell('Reset your password',
    `<p style="color:#9aa3b2;font-size:13.5px;margin:0 0 18px">Enter this code in Social Dashboard to choose a new password. It expires in 15 minutes.</p>
<div style="font:700 26px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.1em;background:#09090b;border:1px solid #3a4152;border-radius:12px;padding:14px;text-align:center">${code}</div>
<p style="color:#6f7787;font-size:12.5px;margin:18px 0 0">Didn't ask for this? You can ignore this email — your password stays unchanged.</p>`));
  return ok();
}

export async function sendWelcome(env, request) {
  const body = await request.json().catch(() => ({}));
  const to = String(body.to || '').trim().toLowerCase();
  const name = String(body.name || '').trim().slice(0, 80);
  if (!EMAIL_RE.test(to)) return fail('bad_request');
  if (!(await underLimit(env, to, 3))) return fail('rate_limited', 429);
  await send(env, to, 'Welcome to Social Dashboard', shell(`Welcome${name ? ', ' + name : ''}`,
    `<p style="color:#9aa3b2;font-size:13.5px;margin:0">Your account is ready. Link your first account from the app and press Refresh to see everything in one place.</p>`));
  return ok();
}
