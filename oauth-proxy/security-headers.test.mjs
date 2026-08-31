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
  assert.match(response.headers.get('content-security-policy-report-only'), /frame-ancestors 'none'/);
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
