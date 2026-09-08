import test from 'node:test';
import assert from 'node:assert/strict';
import { growthEvent } from './growth.js';
import worker from './worker.js';
const request = (body, origin = 'https://promptshield-beta.vercel.app', headers = {}) => new Request('https://redexa.getcertsprint.com/growth-event', { method:'POST', headers:{ Origin:origin, ...headers }, body });
test('only predefined anonymous counters reach storage', async () => {
  const calls = [];
  const env = {GROWTH: {prepare(sql) { return {bind(...args) { return {run: async () => calls.push({sql,args})}; }}; }}};
  assert.equal((await growthEvent(request('demo_result'), env)).status,204);
  assert.deepEqual(calls[0].args.slice(1), ['redaxa','demo_result']);
  for (const body of ['email=someone@example.com', '{"event":"visit","prompt":"secret"}', 'x'.repeat(81)]) {
    assert.ok((await growthEvent(request(body), env)).status >= 400);
  }
  assert.equal((await growthEvent(request('visit','https://unrelated.example'),env)).status,403);
  assert.equal((await growthEvent(request('visit',undefined,{'DNT':'1'}),env)).status,204);
  assert.equal(calls.length,1);
});
test('missing database fails without counting a success', async () => {
  assert.equal((await growthEvent(request('visit'),{})).status,503);
});
test('setup guide and client script are public and support HEAD', async () => {
  for (const path of ['/getting-started','/growth.js']) {
    const response=await worker.fetch(new Request('https://redexa.getcertsprint.com'+path),{});
    assert.equal(response.status,200);
    const head=await worker.fetch(new Request('https://redexa.getcertsprint.com'+path,{method:'HEAD'}),{});
    assert.equal(await head.text(),'');
  }
  const home=await (await worker.fetch(new Request('https://redexa.getcertsprint.com/'),{})).text();
  assert.match(home,/Redexa-Social-1.9.3-Setup.exe/);
  assert.match(home,/href="\/getting-started"/);
});
