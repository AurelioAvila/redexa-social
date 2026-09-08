import assert from 'node:assert/strict';
import test from 'node:test';
import worker from './worker.js';
import { readFileSync, existsSync } from 'node:fs';

test('legal pages and their GitHub Pages copies share one canonical URL', async () => {
  for (const slug of ['privacy', 'terms', 'data-deletion',
    'local-first-social-media-analytics', 'youtube-analytics-dashboard',
    'multi-platform-creator-analytics', 'weekly-social-media-review']) {
    const url = `https://redexa.getcertsprint.com/${slug}`;
    const response = await worker.fetch(new Request(url), {});
    assert.equal(response.status, 200);
    const copies = [await response.text(), readFileSync(new URL(`../docs/${slug}.html`, import.meta.url), 'utf8')];
    for (const html of copies) {
      assert.equal((html.match(/rel="canonical"/g) || []).length, 1);
      assert.ok(html.includes(`<link rel="canonical" href="${url}">`));
      assert.match(html, /<meta name="description" content="[^"]+">/);
    }
  }
});

test('both landing pages agree on metadata, platform limits and paid features', async () => {
  const live = await (await worker.fetch(new Request('https://redexa.getcertsprint.com/'), {})).text();
  const pages = readFileSync(new URL('../docs/index.html', import.meta.url), 'utf8');
  const description = (html) => html.match(/<meta name="description" content="([^"]+)">/)[1];
  assert.equal(description(live), description(pages));
  for (const html of [live, pages]) {
    assert.match(html, /Instagram and TikTok currently require your own developer app/);
    assert.match(html, /X shows credential status only; X analytics are not available/);
    assert.match(html, /Export collected data to spreadsheets and reports with Pro or Studio/);
    assert.match(html, /License records are stored remotely/);
    assert.doesNotMatch(html, /Your tokens stay on your PC/);
    const schema = JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
    assert.equal(schema.description, description(html));
    assert.equal(schema.url, 'https://redexa.getcertsprint.com/');
    for (const match of html.matchAll(/<meta (?:property="og:image"|name="twitter:image") content="([^"]+)"/g)) {
      const response = await worker.fetch(new Request(match[1]), {});
      assert.equal(response.status, 200);
      assert.equal(response.headers.get('content-type'), 'image/png');
    }
  }
});

test('both sitemaps list the same successful canonical URLs', async () => {
  const xml = await (await worker.fetch(new Request('https://redexa.getcertsprint.com/sitemap.xml'), {})).text();
  const copy = readFileSync(new URL('../docs/sitemap.xml', import.meta.url), 'utf8');
  const urls = (text) => [...text.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]).sort();
  assert.deepEqual(urls(copy), urls(xml));
  for (const url of urls(xml)) {
    const response = await worker.fetch(new Request(url), {});
    assert.equal(response.status, 200, url);
    assert.ok((await response.text()).includes(`<link rel="canonical" href="${url}">`));
  }
});

test('legacy public document URLs redirect for GET and HEAD', async () => {
  for (const slug of ['local-first-social-media-analytics', 'youtube-analytics-dashboard',
    'multi-platform-creator-analytics', 'weekly-social-media-review']) {
    for (const method of ['GET', 'HEAD']) {
      const response = await worker.fetch(new Request(`https://redexa.getcertsprint.com/${slug}.html`, { method }), {});
      assert.equal(response.status, 301);
      assert.equal(response.headers.get('location'), `https://redexa.getcertsprint.com/${slug}`);
    }
    const copy = readFileSync(new URL(`../docs/${slug}.html`, import.meta.url), 'utf8');
    assert.doesNotMatch(copy, /href="\/"/); // Would escape the GitHub Pages project path.
  }
  const image = await worker.fetch(new Request('https://redexa.getcertsprint.com/screenshots/overview.png'), {});
  assert.equal(image.status, 200);
  assert.equal(image.headers.get('content-type'), 'image/png');
});

test('GitHub Pages callback documents remain static and unredirected', () => {
  assert.equal(existsSync(new URL('../docs/CNAME', import.meta.url)), false);
  for (const platform of ['instagram', 'tiktok']) {
    const html = readFileSync(new URL(`../docs/${platform}-callback.html`, import.meta.url), 'utf8');
    assert.match(html, /<meta name="robots" content="noindex">/);
    assert.doesNotMatch(html, /<script|http-equiv=["']refresh/i);
  }
});

test('OAuth exchange and refresh keep their POST routes on all configured hosts', async (t) => {
  let calls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url: String(url), body: options?.body });
    return Response.json({ access_token: 'test-token', refresh_token: 'test-refresh', expires_in: 3600 });
  });
  for (const host of ['redexa.getcertsprint.com', 'socialdashboard.getcertsprint.com',
    'social-dashboard-oauth.canadesino91.workers.dev']) {
    for (const platform of ['instagram', 'tiktok']) {
      calls = [];
      const redirect = `https://aurelioavila.github.io/social-dashboard/${platform}-callback`;
      const response = await worker.fetch(new Request(`https://${host}/exchange`, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ platform, code: 'test-code', redirect_uri: redirect }),
      }), {});
      assert.equal(response.status, 200);
      assert.equal(response.headers.get('location'), null);
      assert.equal(calls[0].body.get('redirect_uri'), redirect);
      assert.equal((await response.json()).access_token, 'test-token');
    }
    const refresh = await worker.fetch(new Request(`https://${host}/refresh`, {
      method: 'POST', body: JSON.stringify({ platform: 'tiktok', refresh_token: 'test-refresh' }),
    }), {});
    assert.equal(refresh.status, 200);
  }
  calls = [];
  const rejected = await worker.fetch(new Request('https://redexa.getcertsprint.com/exchange', {
    method: 'POST', body: JSON.stringify({ platform: 'tiktok', code: 'test-code', redirect_uri: 'https://example.com/callback' }),
  }), {});
  assert.equal(rejected.status, 400);
  assert.equal(calls.length, 0);
});

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

