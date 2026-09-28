const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/app.js'), 'utf8');
const render = source.slice(source.indexOf('function renderDiagnosticChannels('), source.indexOf('// Match the backend list'));
const elements = new Map();
const document = {
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, { classList: { toggle() {} }, querySelectorAll: () => [] });
    return elements.get(id);
  },
  querySelectorAll: () => [],
};
const run = new Function('document', 'connectionsData', 'diag', `
  const t = key => key, esc = String, icon = () => '', activePlatforms = () => ['youtube'];
  const CONNECT_META = {youtube:{name:'YouTube',ico:''}}, DIAG_ICONS = {};
  const NUDGE_CODES = new Set(['diag_no_account']), INFORMATIONAL_CODES = new Set();
  const diagField = (i, field) => i[field] || '', platformStatusMap = () => ({}), statusDotClass = () => '';
  let lastDiag = null, diagFilter = 'all';
  ${render}
  renderDiagnostics(diag);
`);
run(document, {connections:[]}, {score:null, issues:[{platform:'youtube', code:'diag_no_account', severity:'yellow'}]});
assert.equal(elements.get('diag-badge').textContent, 0);
assert.equal(elements.get('health-panel').hidden, true);
assert.match(elements.get('diagnostic-channels').innerHTML, /connect_not_linked/);
run(document, {connections:[{platform:'youtube',needs_reauth:true}]}, {score:null, issues:[{platform:'youtube',code:'expired',severity:'red',title:'Expired access'}]});
assert.equal(elements.get('diag-badge').textContent, 1);
assert.equal(elements.get('health-panel').hidden, false);
assert.match(elements.get('diagnostics-list').innerHTML, /Expired access/);
assert.match(elements.get('diagnostic-channels').innerHTML, /data-channel-target="connections"/);
console.log('Setup nudges stay separate; failed connections stay actionable.');
