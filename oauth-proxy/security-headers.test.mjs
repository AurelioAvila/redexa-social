import assert from 'node:assert/strict';
import test from 'node:test';

import worker from './worker.js';

test('public responses include the security baseline', async () => {
  const response = await worker.fetch(
    new Request('https://socialdashboard.getcertsprint.com/'),
    {},
  );

  assert.equal(response.status, 200);
  assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
  assert.equal(response.headers.get('x-frame-options'), 'DENY');
  assert.match(response.headers.get('strict-transport-security'), /max-age=31536000/);
  assert.match(response.headers.get('content-security-policy'), /frame-ancestors 'none'/);
  assert.equal(response.headers.get('content-security-policy-report-only'), null);
});

test('health endpoint exposes only a minimal service status', async () => {
  const response = await worker.fetch(
    new Request('https://socialdashboard.getcertsprint.com/health'),
    {},
  );
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: 'ok', service: 'redexa-social' });
});

test('API errors receive the same security baseline', async () => {
  const response = await worker.fetch(
    new Request('https://socialdashboard.getcertsprint.com/unknown'),
    {},
  );

  assert.equal(response.status, 405);
  assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
  assert.equal(response.headers.get('referrer-policy'), 'strict-origin-when-cross-origin');
});
