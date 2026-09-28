const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/app.js'), 'utf8');
const load = source.slice(source.indexOf('async function loadUpdateCheck()'), source.indexOf('// Fallback for winget/source builds'));
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
new AsyncFunction('assert', `
  let response, opened = 0, passive = 0, _updateInfo = null;
  const banner = {dataset:{},querySelector:()=>({}),classList:{remove(){}}};
  const document = {getElementById:()=>banner};
  const t = key => key;
  const fetch = async (url, options) => {
    assert.equal(url, '/api/update/check');
    assert.equal(options, undefined, 'Startup must never request installation');
    return {json:async()=>response};
  };
  const openUpdateModal = () => { opened++; };
  const loadPassiveUpdateNotice = () => { passive++; };
  ${load}
  for (const reason of ['postponed','skipped','no_update']) {
    response={available:false,reason}; await loadUpdateCheck();
    assert.equal(opened,0);
  }
  response={managed_externally:true}; await loadUpdateCheck();
  assert.equal(opened,0); assert.equal(passive,1);
  response={available:true,version:'1.10.7'}; await loadUpdateCheck();
  assert.equal(opened,1); assert.equal(_updateInfo.version,'1.10.7');
  assert.equal(banner.dataset.mode,'install');
`)(assert).then(()=>console.log('Startup opens only an available internal update and never installs automatically.'));
