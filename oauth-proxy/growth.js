// Counts actions, not people. Never persist IPs, URLs, prompts or account IDs.
const origins = new Map([
  ['https://redexa.getcertsprint.com', 'redexa'],
  ['https://promptshield-beta.vercel.app', 'redaxa'],
]);
// An event not named here is rejected with a 400 and recorded nowhere, so a
// new data-growth attribute on a button is only half the work.
const events = new Set(['visit', 'demo_result', 'demo_copy', 'scan_success', 'trial_gate',
  'extension_click', 'download_click', 'guide_view', 'feedback_success',
  'feedback_connection', 'feedback_value', 'feedback_return', 'verification',
  'checkout_start_pro', 'checkout_start_studio']);

export async function growthEvent(request, env) {
  const origin = request.headers.get('Origin');
  const product = origins.get(origin);
  const headers = { 'Cache-Control': 'no-store', 'Vary': 'Origin' };
  if (!product) return new Response(null, { status: 403, headers });
  headers['Access-Control-Allow-Origin'] = origin;
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: { ...headers,
      'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': 'Content-Type' } });
  }
  if (request.method !== 'POST') return new Response(null, { status: 405, headers });
  if (request.headers.get('DNT') === '1' || request.headers.get('Sec-GPC') === '1') {
    return new Response(null, { status: 204, headers });
  }
  // Limit even chunked bodies without reading arbitrary user data into memory.
  const reader = request.body?.getReader();
  if (!reader) return new Response(null, { status: 400, headers });
  let size = 0, value = '';
  const decoder = new TextDecoder();
  while (true) {
    const chunk = await reader.read();
    if (chunk.done) break;
    size += chunk.value.byteLength;
    if (size > 80) { await reader.cancel(); return new Response(null, { status: 413, headers }); }
    value += decoder.decode(chunk.value, { stream: true });
  }
  value += decoder.decode();
  if (!events.has(value)) return new Response(null, { status: 400, headers });
  if (!env.GROWTH) return new Response(null, { status: 503, headers });
  try {
    await env.GROWTH.prepare('INSERT INTO growth_daily(day,product,event,count) VALUES(?,?,?,1) ON CONFLICT(day,product,event) DO UPDATE SET count = MIN(count + 1, 100000)')
      .bind(new Date().toISOString().slice(0, 10), product, value).run();
    return new Response(null, { status: 204, headers });
  } catch { return new Response(null, { status: 503, headers }); }
}

export const growthScript = `(() => {
  if (location.hostname !== 'redexa.getcertsprint.com') return;
  const sent = new Set();
  function track(event) {
    if (navigator.doNotTrack === '1' || navigator.globalPrivacyControl || sent.has(event)) return Promise.resolve(false);
    sent.add(event);
    return fetch('https://redexa.getcertsprint.com/growth-event', {method:'POST', body:event, credentials:'omit', referrerPolicy:'no-referrer', keepalive:true})
      .then(r => { if (!r.ok) sent.delete(event); return r.ok; }).catch(() => { sent.delete(event); return false; });
  }
  window.trackGrowth = track;
  if (location.pathname === '/') track('visit');
  if (location.pathname === '/getting-started') track('guide_view');
  // Monthly / yearly on the pricing section. Every amount and every unit
  // carries both values as data attributes, so the switch is a text swap and
  // the page needs no request to change what it shows. Nothing here decides
  // what is charged: the checkout builds its own price_data from the Worker's
  // plan table, and these two must be kept in step by hand.
  let cycle = 'monthly';
  const cycleButtons = Array.from(document.querySelectorAll('.cycle-btn'));
  if (cycleButtons.length) {
    const applyCycle = (next) => {
      cycle = next;
      const cycleValue = next;
      for (const el of document.querySelectorAll('[data-monthly][data-yearly]')) {
        el.textContent = cycleValue === 'yearly' ? el.dataset.yearly : el.dataset.monthly;
      }
      for (const button of cycleButtons) {
        const on = button.dataset.cycle === cycleValue;
        button.classList.toggle('on', on);
        button.setAttribute('aria-pressed', String(on));
      }
    };
    for (const button of cycleButtons) {
      button.addEventListener('click', () => { applyCycle(button.dataset.cycle); });
    }
  }

  // The pricing buttons used to be download links: the only way to give this
  // product money was to install it first and find the upgrade screen inside.
  // They now open Stripe, which is also what settles VAT - the amount and the
  // currency are decided server-side by the Worker's plan table, and the
  // client sends nothing but which plan and which cycle.
  document.addEventListener('click', async (e) => {
    const buy = e.target.closest('[data-checkout]');
    if (!buy) return;
    const errorBox = document.getElementById('checkout-error');
    if (errorBox) errorBox.textContent = '';
    const label = buy.textContent;
    buy.disabled = true;
    buy.textContent = 'Opening checkout...';
    try {
      const resp = await fetch('/checkout', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ plan: buy.dataset.checkout, cycle }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || !data.url) throw new Error(data.error || 'checkout_failed');
      location.href = data.url;
      return;
    } catch {
      // Never strand somebody who wants to pay: say what happened and leave
      // the download, which is still a real way to start.
      if (errorBox) {
        errorBox.textContent = 'Checkout could not be opened. Please try again, or download the app and upgrade from inside it.';
      }
      buy.disabled = false;
      buy.textContent = label;
    }
  });

  document.addEventListener('click', async e => {
    const target = e.target.closest('[data-growth]');
    if (!target) return;
    const ok = await track(target.dataset.growth);
    if (target.tagName === 'BUTTON') {
      document.getElementById('feedback-status').textContent = ok ? 'Thank you. Your anonymous response was recorded.' : 'Your response was not recorded. Please try again, or check your privacy settings.';
      if (ok) target.disabled = true;
    }
  });
})();`;
