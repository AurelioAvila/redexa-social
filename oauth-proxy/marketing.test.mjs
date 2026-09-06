import assert from 'node:assert/strict';
import test from 'node:test';
import worker from './worker.js';

test('public HEAD mirrors GET status and headers without a body', async () => {
  for (const path of ['/', '/weekly-social-media-review', '/robots.txt', '/sitemap.xml']) {
    const url = 'https://redexa.getcertsprint.com' + path;
    const get = await worker.fetch(new Request(url), {});
    const head = await worker.fetch(new Request(url, { method: 'HEAD' }), {});
    assert.equal(get.status, 200);
    assert.equal(head.status, get.status);
    assert.equal(head.headers.get('content-type'), get.headers.get('content-type'));
    assert.equal(await head.text(), '');
  }
});

test('old domain keeps the canonical redirect for HEAD', async () => {
  const response = await worker.fetch(new Request('https://socialdashboard.getcertsprint.com/', { method: 'HEAD' }), {});
  assert.equal(response.status, 301);
  assert.equal(response.headers.get('location'), 'https://redexa.getcertsprint.com/');
});

test('HEAD cannot invoke account or payment handlers', async () => {
  for (const path of ['/checkout', '/exchange', '/license/claim', '/stripe/webhook']) {
    const response = await worker.fetch(new Request('https://redexa.getcertsprint.com' + path, { method: 'HEAD' }), {});
    assert.equal(response.status, 405);
  }
});

test('home links the guide and sitemap advertises its canonical URL', async () => {
  const html = await (await worker.fetch(new Request('https://redexa.getcertsprint.com/'), {})).text();
  assert.match(html, /href="\/weekly-social-media-review"/);
  const sitemap = await (await worker.fetch(new Request('https://redexa.getcertsprint.com/sitemap.xml'), {})).text();
  assert.match(sitemap, /<loc>https:\/\/redexa.getcertsprint.com\/weekly-social-media-review<\/loc>/);
});

