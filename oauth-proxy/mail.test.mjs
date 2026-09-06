import assert from 'node:assert/strict';
import { test } from 'node:test';
import { sendResetCode, sendWelcome, sendPasswordChanged } from './mail.js';

const request = (body = { to: 'audit@example.invalid', code: '123456', name: '<Test>' }) =>
  new Request('https://example.invalid/', { method: 'POST', body: JSON.stringify(body) });
const env = () => ({ RESEND_API_KEY: 'mock', LICENSES: { get: async () => null, put: async () => {} } });

for (const handler of [sendResetCode, sendWelcome, sendPasswordChanged]) {
  test(`${handler.name} reports provider failure without exposing its response`, async () => {
    const previous = globalThis.fetch;
    try {
      globalThis.fetch = async () => new Response('private provider details', { status: 503 });
      const response = await handler(env(), request());
      assert.equal(response.status, 503);
      assert.deepEqual(await response.json(), { error: 'email_unavailable' });
      const missing = await handler({ ...env(), RESEND_API_KEY: '' }, request());
      assert.equal(missing.status, 503);
    } finally { globalThis.fetch = previous; }
  });
  test(`${handler.name} sends branded HTML and text and reports acceptance`, async () => {
    const previous = globalThis.fetch;
    try {
      globalThis.fetch = async (_url, options) => {
        const payload = JSON.parse(options.body);
        assert.match(payload.subject, /Redexa Social/);
        assert.match(payload.html, /<html lang="en">/);
        assert.ok(payload.text);
        assert.doesNotMatch(payload.html, /<Test>|Nothing is uploaded/);
        assert.doesNotMatch(payload.text, /nothing is uploaded/i);
        assert.ok(options.signal);
        return new Response('{}', { status: 200 });
      };
      const response = await handler(env(), request());
      assert.equal(response.status, 200);
      assert.deepEqual(await response.json(), { ok: true, accepted: true });
    } finally { globalThis.fetch = previous; }
  });
  test(`${handler.name} rejects null JSON`, async () => {
    assert.equal((await handler(env(), request(null))).status, 400);
  });
}
