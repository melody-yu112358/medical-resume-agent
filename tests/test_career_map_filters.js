const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const {runInNewContext} = require('node:vm');
const source = readFileSync(resolve(__dirname, '../src/medical_career_agent/assets/career_map_filters.js'), 'utf8');

function setup(hasForm = true) {
  const handlers = {}, status = {setAttribute(k,v) {this[k]=v;}, removeAttribute(k) {delete this[k];}};
  const button = {hidden:false};
  const form = {querySelector:() => button, addEventListener:(k,f) => {handlers[k]=f;},
    requestSubmit() {this.submitted=(this.submitted || 0)+1;}};
  const location = {pathname:'/', reload() {this.reloaded=true;}};
  runInNewContext(source, {document:{querySelector:() => hasForm ? form : null, getElementById:() => status},
    window:{location, addEventListener:(k,f) => {handlers[k]=f;}}});
  return {handlers, status, button, form, location};
}

test('checking and unchecking submit immediately with visible pending state', () => {
  const ctx = setup();
  assert.equal(ctx.button.hidden,true);
  for (const checked of [true,false]) {
    ctx.handlers.change({target:{type:'checkbox', checked, closest:() => ({id:'facet-lifecycle_stages'})}});
  }
  assert.equal(ctx.form.submitted,2);
  assert.equal(ctx.form.action,'/#facet-lifecycle_stages');
  assert.equal(ctx.status['aria-busy'],'true');
  assert.match(ctx.status.textContent,/正在更新/);
});

test('non-filter changes do not submit and non-catalog pages are safe', () => {
  const ctx = setup();
  ctx.handlers.change({target:{type:'select-one'}});
  assert.equal(ctx.form.submitted,undefined);
  assert.doesNotThrow(() => setup(false));
});

test('back-forward cache restores authoritative URL state instead of stale selections', () => {
  const ctx = setup();
  ctx.handlers.pageshow({persisted:true});
  assert.equal(ctx.location.reloaded,true);
  ctx.handlers.pageshow({persisted:false});
  assert.match(ctx.status.textContent,/立即更新/);
});
