const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const count = source.slice(source.indexOf('function countAccounts('), source.indexOf('/** A summary tile.'));
const render = source.slice(source.indexOf('function renderOverview('), source.indexOf("/** The period's best content"));
const elements = new Map();
for (const id of ['overview-grid','overview-sub','overview-empty','hero-tiles','overview-platforms-heading','btn-export']) {
  elements.set(id, { hidden: false, classList: { toggle(key, hidden) { this[key] = hidden; } } });
}
const document = { getElementById: id => elements.get(id) };
let tileRenders = 0;
function check(snapshot, connections) {
  new Function('document','connectionsData','t','activePlatforms','platformStatusMap','renderHeroTiles','renderTopContent',count + render + ';return renderOverview;')(
    document, connections, key => key, () => [], () => ({}), () => tileRenders++, () => {}
  )(snapshot);
}
check({}, { connections: [] });
assert.equal(elements.get('overview-empty').hidden, false, 'new users get a connection guide');
assert.equal(elements.get('hero-tiles').classList.hidden, true, 'missing data must not look like zero performance');
assert.equal(tileRenders, 0);
check({}, { connections: [{ platform: 'youtube' }] });
assert.equal(elements.get('overview-empty').hidden, true, 'a linked account waiting for refresh is not a new user');
check({ youtube: { channels: [{ ok: false }] } }, null);
assert.equal(elements.get('overview-empty').hidden, true, 'account errors must not show first-account onboarding');
assert.equal(elements.get('overview-grid').classList.hidden, false, 'account status remains visible');
check({ youtube: { channels: [{ ok: true }] } }, null);
assert.equal(elements.get('hero-tiles').classList.hidden, false);
assert.equal(tileRenders, 1);
console.log('Overview guides new users without showing fabricated zero metrics; linked and failed accounts keep their status.');
