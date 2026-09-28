const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/app.js'), 'utf8');
const load = source.slice(source.indexOf('async function loadSnapshot()'), source.indexOf('\nfunction setProgress'));
const refresh = source.slice(source.indexOf('async function refreshAll()'), source.indexOf('\nbtnRefresh.addEventListener'));
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const run = new AsyncFunction('assert', `
  const elements = new Map();
  const document = {getElementById(id) {
    if (!elements.has(id)) elements.set(id, {innerHTML:'saved rows', dataset:{}, attrs:{}, setAttribute(k,v){this.attrs[k]=v}});
    return elements.get(id);
  }};
  const t = key => key, esc = String, authHeaders = () => ({});
  let currentSnapshot = {}, failure = false, requests = 0;
  const fetch = async () => {
    requests++;
    if (failure) throw new Error('network failure');
    assert.equal(document.getElementById('overview-grid').attrs['aria-busy'], 'true');
    assert.match(document.getElementById('overview-grid').innerHTML, /skeleton-row/);
    return {ok:true,json:async()=>({loaded:true})};
  };
  const renderAll = snapshot => {currentSnapshot=snapshot; ['overview-grid','top-posts-list','diagnostic-channels'].forEach(id=>document.getElementById(id).innerHTML='real rows');};
  ${load}
  await loadSnapshot();
  assert.equal(document.getElementById('overview-grid').innerHTML, 'real rows');
  assert.equal(document.getElementById('overview-grid').attrs['aria-busy'], 'false');
  failure=true;
  await assert.rejects(loadSnapshot(), /network failure/);
  assert.equal(document.getElementById('overview-grid').innerHTML, 'real rows');
  currentSnapshot={};
  await assert.rejects(loadSnapshot(), /network failure/);
  assert.match(document.getElementById('overview-grid').innerHTML, /footer_error/);
  assert.doesNotMatch(document.getElementById('overview-grid').innerHTML, /skeleton-row/);
  assert.equal(document.getElementById('overview-grid').attrs['aria-busy'], 'false');
  const btnRefresh={disabled:false,attrs:{},setAttribute(k,v){this.attrs[k]=v},classList:{add(){},remove(){}}};
  const progressWrap={classList:{add(){},remove(){}}}, lastRefreshEl={};
  const setProgress=()=>{}, toast=()=>{}, console={error(){}}, sleep=async()=>{};
  ${refresh}
  await refreshAll();
  assert.equal(btnRefresh.disabled, false);
  assert.equal(btnRefresh.attrs['aria-busy'], 'false');
  assert.equal(document.getElementById('refresh-button-label').textContent, 'btn_refresh');
  assert.equal(lastRefreshEl.textContent, 'footer_error');
  btnRefresh.disabled=true;
  const before=requests;
  await refreshAll();
  assert.equal(requests,before);
`);
run(assert).then(()=>console.log('Loading restores controls on failure, preserves prior data and blocks duplicate refresh.'));
