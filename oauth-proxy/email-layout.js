/**
 * The one layout every Redexa Social email uses.
 *
 * There used to be three: one shell in mail.js, one hand-written block in
 * licensing.js, and one bare fragment for the owner notice. They drifted —
 * different backgrounds, different card borders, no header, no footer — so a
 * customer who received both the welcome and the licence key saw two
 * products. This file is the only place any of that is decided.
 *
 * The palette is the app's own "Ocean" theme (static/style.css), so the mail
 * looks like the window it is talking about rather than a separate brand.
 *
 * Copyright (c) 2026 Aurelio Avila. All rights reserved.
 */

const BG = '#071620';
const PANEL = '#0d2434';
const INSET = '#061a26';
const LINE = '#1b3d52';
const TEXT = '#eaf6fb';
const MUTED = '#8fa8b3';
const FAINT = '#6d8794';
const ACCENT = '#38bdf8';

const SITE = 'https://redexa.getcertsprint.com';

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[character]));
}

/** First name only. A form gives us whatever the person typed, so this also
 *  caps the length — a greeting is not a place to render 200 characters. */
export function firstName(name) {
  return String(name || '').trim().split(/\s+/)[0].slice(0, 40) || 'there';
}

export function paragraph(text) {
  return `<p style="margin:0 0 16px;color:${MUTED};font-size:15px;line-height:1.7">${escapeHtml(text)}</p>`;
}

/** A monospace block for a code or a licence key. `break` matters for keys,
 *  which are long enough to overflow a phone otherwise. */
export function codeBlock(value, { spaced = false } = {}) {
  return `<div style="margin:22px 0;padding:16px;background:${INSET};border:1px solid ${LINE};border-radius:12px;color:${ACCENT};font:700 ${spaced ? '26px' : '18px'}/1.4 ui-monospace,SFMono-Regular,Consolas,monospace;${spaced ? 'letter-spacing:.14em;' : 'letter-spacing:.03em;word-break:break-all;'}text-align:center">${escapeHtml(value)}</div>`;
}

/**
 * Wraps a body in the shared chrome: preheader, header, eyebrow, heading,
 * optional button, footer.
 *
 * Tables and inline styles throughout, not because the markup is nicer that
 * way but because Outlook ignores most of everything else.
 */
export function layout({ preview, eyebrow, heading, body, cta, footer = 'This is a transactional email about your Redexa Social account.' }) {
  const button = cta
    ? `<table role="presentation" cellspacing="0" cellpadding="0" style="margin:26px 0 6px"><tr><td style="border-radius:10px;background:${ACCENT}"><a href="${escapeHtml(cta.url)}" style="display:inline-block;padding:13px 22px;color:#04202e;font-size:15px;font-weight:700;text-decoration:none">${escapeHtml(cta.label)} &nbsp;&rarr;</a></td></tr></table>`
    : '';
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${escapeHtml(preview)}</title></head><body style="margin:0;padding:0;background:${BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:${TEXT}">`
    + `<div style="display:none;max-height:0;overflow:hidden;opacity:0">${escapeHtml(preview)}</div>`
    + `<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:${BG}"><tr><td align="center" style="padding:24px 14px">`
    + `<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:${PANEL};border:1px solid ${LINE};border-radius:18px;overflow:hidden">`
    + `<tr><td style="height:4px;background:${ACCENT}"></td></tr>`
    + `<tr><td style="padding:22px 30px 18px;border-bottom:1px solid ${LINE}"><table role="presentation" cellspacing="0" cellpadding="0"><tr><td align="center" style="width:32px;height:32px;border-radius:9px;background:${ACCENT};color:#04202e;font-size:13px;font-weight:900">R</td><td style="padding-left:11px"><a href="${SITE}" style="color:${TEXT};font-size:19px;font-weight:800;text-decoration:none;letter-spacing:-.3px">Redexa Social</a></td></tr></table></td></tr>`
    + `<tr><td style="padding:30px">`
    + `<table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 15px"><tr><td style="padding:6px 11px;border:1px solid #235268;border-radius:999px;background:#0a2b3a;color:${ACCENT};font-size:10px;font-weight:800;letter-spacing:1.3px;text-transform:uppercase">${escapeHtml(eyebrow)}</td></tr></table>`
    + `<h1 style="margin:0 0 16px;color:${TEXT};font-size:25px;line-height:1.22;letter-spacing:-.5px">${escapeHtml(heading)}</h1>${body}${button}`
    + `</td></tr>`
    + `<tr><td style="padding:18px 30px;background:${INSET};border-top:1px solid ${LINE}"><p style="margin:0 0 7px;color:${MUTED};font-size:12px;line-height:1.6">${escapeHtml(footer)}</p><p style="margin:0;color:${FAINT};font-size:11px;line-height:1.5">Redexa Social &nbsp;&middot;&nbsp; <a href="${SITE}" style="color:${MUTED}">Website</a> &nbsp;&middot;&nbsp; <a href="${SITE}/privacy" style="color:${MUTED}">Privacy</a> &nbsp;&middot;&nbsp; <a href="${SITE}/terms" style="color:${MUTED}">Terms</a></p></td></tr>`
    + `</table></td></tr></table></body></html>`;
}

/**
 * The single way out to Resend.
 *
 * Never throws and never rejects: every caller is either a Stripe webhook —
 * which Stripe would retry in full if this failed — or a best-effort notice
 * attached to an action that has already succeeded.
 *
 * `text` is not optional by accident. HTML-only mail scores worse with spam
 * filters, and these are the messages that must not land in spam.
 */
export async function sendMail(env, { from, to, subject, html, text }) {
  if (!env.RESEND_API_KEY || !to) return false;
  try {
    const resp = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        authorization: `Bearer ${env.RESEND_API_KEY}`,
        'content-type': 'application/json',
      },
      body: JSON.stringify({ from, to, subject, html, text }),
    });
    if (!resp.ok) {
      console.log('resend send failed', resp.status, (await resp.text()).slice(0, 300));
      return false;
    }
    return true;
  } catch (err) {
    console.log('resend send threw', String(err).slice(0, 300));
    return false;
  }
}
