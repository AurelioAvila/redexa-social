import assert from 'node:assert/strict';
import test from 'node:test';
import worker from './worker.js';
import { readFileSync, existsSync } from 'node:fs';

test('legal pages and their GitHub Pages copies share one canonical URL', async () => {
  for (const slug of ['pricing', 'privacy', 'terms', 'data-deletion',
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
      // The overview shot has always been JPEG bytes under a .png address.
      // The declared type has to match the bytes, because an og:image is
      // fetched by crawlers that trust the header rather than sniffing.
      assert.equal(response.headers.get('content-type'), 'image/jpeg');
    }
  }
});

test('the shipped version in the home page schema is the one version.py declares', async () => {
  // softwareVersion is a second copy of a number that lives in version.py,
  // and a second copy is a number that drifts. This is the check that makes
  // the drift fail a release instead of shipping quietly.
  const declared = readFileSync(new URL('../version.py', import.meta.url), 'utf8')
    .match(/^APP_VERSION = "([^"]+)"/m)[1];
  for (const html of [await (await worker.fetch(new Request('https://redexa.getcertsprint.com/'), {})).text(),
    readFileSync(new URL('../docs/index.html', import.meta.url), 'utf8')]) {
    const schema = JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
    assert.equal(schema.softwareVersion, declared);
  }
});

/** PLANS in licensing.js is the table createCheckout bills, so it is the only
 *  place a price may come from. Read as text rather than imported: the docs/
 *  copies are static files that cannot import anything, and they have to be
 *  held to the same number. */
const planCents = () => {
  const plans = readFileSync(new URL('./licensing.js', import.meta.url), 'utf8')
    .match(/const PLANS = \{([\s\S]*?)\};/)[1];
  return (plan, cycle) => Number(plans.match(new RegExp(`${plan}:[^}]*${cycle}: (\\d+)`))[1]);
};

const pricedPages = async () => [
  await (await worker.fetch(new Request('https://redexa.getcertsprint.com/pricing'), {})).text(),
  readFileSync(new URL('../docs/pricing.html', import.meta.url), 'utf8'),
];

test('the prices in the page schema are the prices licensing.js charges', async () => {
  // The schema said 12 and 39 EUR a month while the page and the checkout
  // said 7.99 and 10.99. Structured data is a price quote to a search engine,
  // so it has to come from the table createCheckout actually bills.
  const cents = planCents();
  for (const html of [await (await worker.fetch(new Request('https://redexa.getcertsprint.com/'), {})).text(),
    readFileSync(new URL('../docs/index.html', import.meta.url), 'utf8'),
    ...await pricedPages()]) {
    const schema = JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
    const priced = new Map(schema.offers.map((offer) => [offer.name, offer.price]));
    for (const [plan, name] of [['pro', 'Pro'], ['studio', 'Studio']]) {
      for (const cycle of ['monthly', 'yearly']) {
        assert.equal(priced.get(`${name} ${cycle}`), (cents(plan, cycle) / 100).toFixed(2));
      }
    }
    // Ratings and reviews are never invented here, however tempting the
    // rich-result star is: there is nothing to average.
    assert.ok(!('aggregateRating' in schema) && !('review' in schema));
  }
});

test('the pricing page prints the amounts and the saving licensing.js implies', async () => {
  // The visible numbers are the ones somebody decides on; the schema is only
  // what a crawler reads. Both come off PLANS, and the yearly saving is
  // arithmetic on it rather than a round number somebody liked the look of -
  // a "save 50%" that the table does not actually give is a false price.
  const cents = planCents();
  for (const html of await pricedPages()) {
    for (const plan of ['pro', 'studio']) {
      const monthly = cents(plan, 'monthly');
      const yearly = cents(plan, 'yearly');
      for (const amount of [monthly, yearly, monthly * 12, monthly * 12 - yearly]) {
        assert.ok(html.includes(`€${(amount / 100).toFixed(2)}`),
          `${plan}: the page never says €${(amount / 100).toFixed(2)}`);
      }
    }
    // The limits the server actually applies: DEVICE_LIMITS in licensing.js,
    // ENTITLEMENTS in plans.py, MAX_RIVALS in rivals.py. A pricing page that
    // promises more accounts than the API hands out is a refund request.
    assert.match(html, /Up to 3 computers on one key/);
    assert.match(html, /Up to 5 computers on one key/);
    assert.match(html, /up to 3 public channels/);
    // Nothing to average, so nothing is claimed.
    assert.doesNotMatch(html, /aggregateRating|"review"/);
    // The register the rest of the site keeps: local-first is not offline.
    assert.doesNotMatch(html, /never leaves your computer/);
    assert.match(html, /licence records[\s\S]{0,80}are stored remotely/);
  }
});

test('every public page has a title that fits a result and a description that fills one', async () => {
  for (const slug of ['', 'getting-started', 'pricing', 'privacy', 'terms', 'data-deletion',
    'local-first-social-media-analytics', 'youtube-analytics-dashboard',
    'multi-platform-creator-analytics', 'weekly-social-media-review']) {
    const html = await (await worker.fetch(new Request(`https://redexa.getcertsprint.com/${slug}`), {})).text();
    const title = html.match(/<title>([^<]+)<\/title>/)[1];
    assert.ok(title.length <= 60, `/${slug} title is ${title.length} chars: ${title}`);
    const description = html.match(/<meta name="description" content="([^"]+)">/)[1];
    assert.ok(description.length >= 140 && description.length <= 160,
      `/${slug} description is ${description.length} chars`);
    assert.equal((html.match(/<h1[\s>]/g) || []).length, 1, `/${slug} must have exactly one h1`);
    assert.match(html, /<meta property="og:image" content="[^"]+">/);
  }
});

test('pages that exist to finish a payment or a login do not compete in search', async () => {
  for (const path of ['/license/claim', '/license/cancelled']) {
    const response = await worker.fetch(new Request('https://redexa.getcertsprint.com' + path), {});
    assert.equal(response.status, 200, path);
    assert.match(await response.text(), /<meta name="robots" content="noindex, nofollow">/, path);
  }
});

test('the sitemap dates every URL it lists', async () => {
  const xml = await (await worker.fetch(new Request('https://redexa.getcertsprint.com/sitemap.xml'), {})).text();
  const locs = (xml.match(/<loc>/g) || []).length;
  assert.equal((xml.match(/<lastmod>\d{4}-\d{2}-\d{2}<\/lastmod>/g) || []).length, locs);
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
  assert.equal(image.headers.get('content-type'), 'image/jpeg');
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


test('an unknown page is a 404, not a 405 about the method', async () => {
  // Every unmatched GET used to fall through to the API branch and answer
  // 405 with a JSON body. A crawler reads that as "wrong method" rather than
  // "no such page", so nothing ever left the index cleanly - and the same
  // fallthrough is why Search Console's file check could never pass.
  //
  // /pricing was one of the three addresses here, because at the time it was
  // genuinely missing. It is a real page now, so it moved to the assertion
  // below and /pricing/plans took its place: the guarantee under test is that
  // an address with no page answers 404, not that this particular address is
  // missing, and a path nested under the new route also proves the route is
  // an exact match rather than a prefix that swallows everything beneath it.
  for (const path of ['/this/does/not/exist', '/pricing/plans', '/some.old.page.html']) {
    const response = await worker.fetch(new Request(`https://redexa.getcertsprint.com${path}`), {});
    assert.equal(response.status, 404, `${path} should be 404`);
    assert.match(response.headers.get('content-type') ?? '', /text\/html/);
    const html = await response.text();
    assert.match(html, /<meta name="robots" content="noindex">/);
  }
  const pricing = await worker.fetch(new Request('https://redexa.getcertsprint.com/pricing'), {});
  assert.equal(pricing.status, 200);
  assert.doesNotMatch(await pricing.text(), /<meta name="robots" content="noindex">/);
});

test('a non-GET method with no matching route still says method not allowed', async () => {
  // The 404 is only for reads. A DELETE to the API surface is genuinely a
  // method problem and must not start claiming the endpoint does not exist.
  const response = await worker.fetch(
    new Request('https://redexa.getcertsprint.com/some/api/thing', { method: 'DELETE' }), {});
  assert.equal(response.status, 405);
});

test('the Search Console verification file is served with the exact body Google expects', async () => {
  // The file has been in docs/ since the site was on GitHub Pages; on this
  // Worker nothing served it, so the property was never verified.
  const name = 'googleafbc03dac8bce67a.html';
  const response = await worker.fetch(new Request(`https://redexa.getcertsprint.com/${name}`), {});
  assert.equal(response.status, 200);
  const body = await response.text();
  assert.equal(body.trim(), `google-site-verification: ${name}`);
  if (existsSync(new URL(`../docs/${name}`, import.meta.url))) {
    assert.equal(body.trim(), readFileSync(new URL(`../docs/${name}`, import.meta.url), 'utf8').trim());
  }
});

test('the pricing buttons open a checkout instead of a download', async () => {
  // Until now the only way to give this product money was to install it
  // first and find the upgrade screen inside: every pricing button, on all
  // three plans, pointed at the .exe.
  const home = await (await worker.fetch(new Request('https://redexa.getcertsprint.com/'), {})).text();
  assert.match(home, /data-checkout="pro"/);
  assert.match(home, /data-checkout="studio"/);
  // Free is still a download, because free is a download.
  const freeCard = home.slice(home.indexOf('<h3>Free</h3>'), home.indexOf('<h3>Pro</h3>'));
  assert.match(freeCard, /releases\/latest/);
  assert.doesNotMatch(freeCard, /data-checkout/);
});

test('every price on the page carries both cycles, and the discount is stated correctly', async () => {
  const home = await (await worker.fetch(new Request('https://redexa.getcertsprint.com/'), {})).text();
  for (const [monthly, yearly] of [['€7.99', '€49.99'], ['€10.99', '€69.99']]) {
    assert.ok(home.includes(`data-monthly="${monthly}" data-yearly="${yearly}"`), `${monthly}/${yearly} missing`);
  }
  // 49.99 against 95.88 is 47.9% off, 69.99 against 131.88 is 46.9%. "2
  // months free" described the old prices and would now understate the offer,
  // which is still a wrong number on a price page.
  assert.match(home, /Save 47%/);
  assert.doesNotMatch(home, /2 months free/);
});

test('the page says who handles VAT', async () => {
  const home = await (await worker.fetch(new Request('https://redexa.getcertsprint.com/'), {})).text();
  assert.match(home, /Stripe determines and collects it at checkout/);
});
