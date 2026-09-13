import assert from 'node:assert/strict';
import test from 'node:test';

import worker from './worker.js';

test('public responses include the security baseline', async () => {
  const response = await worker.fetch(
    new Request('https://redexa.getcertsprint.com/'),
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
    new Request('https://redexa.getcertsprint.com/health'),
    {},
  );
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: 'ok', service: 'redexa-social' });
});

test('error responses receive the same security baseline', async () => {
  // Two shapes of error, because they are now produced by two different
  // paths: a missing page is a 404 built by the branding module, and a wrong
  // method on a real endpoint is a 405 built by fail(). Both are wrapped by
  // withSecurityHeaders, and this is the test that keeps it that way - the
  // 404 was added later and could easily have been returned around it.
  const cases = [
    ['https://redexa.getcertsprint.com/unknown', 'GET', 404],
    ['https://redexa.getcertsprint.com/checkout', 'GET', 405],
  ];

  for (const [url, method, status] of cases) {
    const response = await worker.fetch(new Request(url, { method }), {});
    assert.equal(response.status, status, `${method} ${url}`);
    assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
    assert.equal(response.headers.get('referrer-policy'), 'strict-origin-when-cross-origin');
  }
});
