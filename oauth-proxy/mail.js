/**
 * Transactional email that has nothing to do with a licence: the password
 * reset code, the welcome message on registration, and the notice sent after
 * a password actually changes. The same Resend key the licences already use
 * (licensing.js), kept in a separate file because these are conceptually
 * different messages — they concern the local account that auth.py manages,
 * not a Stripe purchase.
 *
 * The chrome and the way out to Resend both live in email-layout.js, shared
 * with licensing.js, so a customer who gets a welcome and a licence key sees
 * one product rather than two.
 *
 * Copyright (c) 2026 Aurelio Avila. All rights reserved.
 */
import { codeBlock, firstName, layout, paragraph, sendMail } from './email-layout.js';

const MAIL_FROM = 'Redexa Social <noreply@mail.getcertsprint.com>';
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/;
const SITE = 'https://redexa.getcertsprint.com';

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

async function allowMailRequest(env, request, address, perAddress) {
  const ip = request.headers.get('cf-connecting-ip') || 'unknown';
  return (await underLimit(env, `address:${address}`, perAddress))
    && (await underLimit(env, `ip:${ip}`, 20));
}

const send = (env, to, subject, html, text) =>
  sendMail(env, { from: MAIL_FROM, to, subject, html, text });

/** Reads and validates the shared part of every request: these endpoints are
 *  public, so nothing past this point may assume a well-formed body. */
async function recipient(request) {
  const body = await request.json().catch(() => ({}));
  return {
    body,
    to: String(body.to || '').trim().toLowerCase(),
    name: String(body.name || '').trim().slice(0, 80),
  };
}

export async function sendResetCode(env, request) {
  const { body, to } = await recipient(request);
  const code = String(body.code || '').trim();
  if (!EMAIL_RE.test(to) || !/^\d{6}$/.test(code)) return fail('bad_request');
  if (!(await allowMailRequest(env, request, to, 5))) return fail('rate_limited', 429);
  await send(
    env,
    to,
    'Your Redexa Social reset code',
    layout({
      preview: `${code} is your Redexa Social reset code`,
      eyebrow: 'Account recovery',
      heading: 'Reset your password.',
      body: paragraph('Enter this code in Redexa Social to choose a new password. It expires in 15 minutes.')
        + codeBlock(code, { spaced: true })
        + paragraph("Didn't ask for this? You can ignore this email — your password stays unchanged."),
      footer: 'This is a security email about your Redexa Social account. We will never ask you for your password.',
    }),
    `Your Redexa Social reset code is ${code}. It expires in 15 minutes.\n\nDidn't ask for this? You can ignore this email — your password stays unchanged.`,
  );
  return ok();
}

export async function sendWelcome(env, request) {
  const { to, name } = await recipient(request);
  if (!EMAIL_RE.test(to)) return fail('bad_request');
  if (!(await allowMailRequest(env, request, to, 3))) return fail('rate_limited', 429);
  const greeting = firstName(name);
  await send(
    env,
    to,
    'Your Redexa Social account is ready',
    layout({
      preview: 'Your Redexa Social account is ready',
      eyebrow: 'Account ready',
      heading: `You're set up, ${greeting}.`,
      body: paragraph('Link your first account from the app and press Refresh to see everything in one place.')
        + `<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:22px 0;background:#061a26;border:1px solid #1b3d52;border-radius:12px"><tr><td style="padding:18px;color:#8fa8b3;font-size:14px;line-height:1.8">&#10003; &nbsp;Connect YouTube, Instagram, TikTok and X<br>&#10003; &nbsp;See every account in one window<br>&#10003; &nbsp;Find your best time to post from your own history</td></tr></table>`
        + paragraph('Your data stays on this computer. Nothing is uploaded, and there is no account of yours on our servers to lose.'),
      cta: { label: 'Read the setup guide', url: SITE },
    }),
    `You're set up, ${greeting}.\n\nLink your first account from the app and press Refresh to see everything in one place.\n\nYour data stays on this computer — nothing is uploaded.\n\nSetup guide: ${SITE}`,
  );
  return ok();
}

/**
 * Sent after a password actually changed, not when one was requested.
 *
 * Carries no link and no code on purpose: whoever reads this already holds
 * the new password, so a "wasn't me" button here would be the exact shape an
 * attacker would forge. The instruction is to open the app, which cannot be
 * phished from an inbox.
 */
export async function sendPasswordChanged(env, request) {
  const { to, name } = await recipient(request);
  if (!EMAIL_RE.test(to)) return fail('bad_request');
  if (!(await allowMailRequest(env, request, to, 5))) return fail('rate_limited', 429);
  const greeting = firstName(name);
  const when = new Date().toUTCString();
  await send(
    env,
    to,
    'Your Redexa Social password was changed',
    layout({
      preview: 'The password on your Redexa Social account was changed',
      eyebrow: 'Security notice',
      heading: 'Your password was changed.',
      body: paragraph(`Hi ${greeting}, the password on your Redexa Social account was changed on ${when}. Any session that was open has been signed out.`)
        + `<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:22px 0;background:#061a26;border:1px solid #1b3d52;border-radius:12px"><tr><td style="padding:18px;color:#8fa8b3;font-size:14px;line-height:1.7">If this was you, nothing else is needed.<br>If it was not, whoever did it had access to this computer — change the password again from the app and check who can reach the machine.</td></tr></table>`
        + paragraph('We will never ask you for your password by email.'),
      footer: 'This security notice is sent every time the password changes and cannot be turned off.',
    }),
    `Hi ${greeting},\n\nThe password on your Redexa Social account was changed on ${when}. Any session that was open has been signed out.\n\nIf this was you, nothing else is needed. If it was not, whoever did it had access to this computer — change the password again from the app and check who can reach the machine.\n\nWe will never ask you for your password by email.`,
  );
  return ok();
}
