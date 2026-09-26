// Run: node tests/test_ui_requests.cjs (no browser or dependencies needed).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const userFunction = source.slice(source.indexOf('async function loadUser()'), source.indexOf('// ---------- License ----------'));
const refreshFunction = source.slice(source.indexOf('async function refreshAll()'), source.indexOf('btnRefresh.addEventListener("click", refreshAll)'));
const snapshotFunction = source.slice(source.indexOf('async function loadSnapshot()'), source.indexOf('function setProgress('));

function context(fetch) {
  const messages = [], progress = [], removed = [];
  const classes = {add() {}, remove() {}};
  const sandbox = {
    fetch, AbortSignal, currentUser: {name: 'Existing user'},
    authToken: () => 'stored-token', authHeaders: () => ({}),
    localStorage: {removeItem: key => removed.push(key)}, renderUser() {}, renderAll() {},
    t: key => key, toast: (text, kind) => messages.push({text, kind}),
    btnRefresh: {disabled: false, classList: classes}, progressWrap: {classList: classes},
    lastRefreshEl: {}, setProgress: value => progress.push(value), sleep: async () => {},
    console: {error() {}}, messages, progress, removed,
  };
  vm.createContext(sandbox);
  vm.runInContext(userFunction + snapshotFunction + refreshFunction, sandbox);
  return sandbox;
}
const response = (status, body) => ({status, ok: status >= 200 && status < 300, json: async () => body});

(async () => {
  for (const failure of [async () => response(500), async () => { throw Error('offline'); }]) {
    const ctx = context(failure);
    await ctx.loadUser();
    assert.equal(ctx.currentUser.name, 'Existing user');
    assert.equal(ctx.removed.length, 0);
    assert.equal(ctx.messages[0].kind, 'err');
  }
  const expired = context(async () => response(401));
  await expired.loadUser();
  assert.equal(expired.currentUser, null);
  assert.deepEqual(expired.removed, ['dashboard-token']);

  for (const mode of ['start-error', 'poll-error', 'still-running', 'snapshot-error', 'invalid-status', 'success']) {
    const ctx = context(async url => {
      if (url === '/api/refresh') return response(mode === 'start-error' ? 500 : 200, {});
      if (url === '/api/snapshot') return response(mode === 'snapshot-error' ? 500 : 200, {});
      if (mode === 'poll-error') throw Error('offline');
      return response(200, mode === 'invalid-status' ? {} : {
        running: mode === 'still-running', done_units: 2, total_units: 2,
      });
    });
    await ctx.refreshAll();
    assert.equal(ctx.messages.at(-1).kind, mode === 'success' ? 'ok' : 'err', mode);
    assert.equal(ctx.btnRefresh.disabled, false, mode);
    if (['start-error', 'poll-error', 'still-running', 'invalid-status'].includes(mode)) {
      assert(!ctx.progress.includes(100), mode);
    }
  }
  console.log('Account and refresh request regressions passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
