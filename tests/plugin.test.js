import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { registerTools, invoke } from '../src/tools.js';

test('registration is inert, optional, matches manifest; real Python bridge works', async () => {
  const root = await mkdtemp(join(tmpdir(), 'radar-test-'));
  try {
    const registered=[];
    registerTools({ pluginConfig: { dataRoot:root }, registerTool: (tool,opts)=>registered.push({tool,opts}) });
    const manifest=JSON.parse(await readFile(new URL('../openclaw.plugin.json',import.meta.url)));
    assert.deepEqual(registered.map(x=>x.tool.name),manifest.contracts.tools);
    assert.ok(registered.every(x=>x.opts.optional));
    const result=await registered[0].tool.execute('test',{});
    assert.equal(result.details.items,0);
    assert.equal(result.details.dossier_count,0);
  } finally { await rm(root,{recursive:true,force:true}); }
});
test('no arbitrary command or relative runtime', () => {
  assert.throws(()=>invoke({dataRoot:'/tmp'},'status; echo injected'), /Unsupported/);
  assert.throws(()=>invoke({dataRoot:'relative'},'status'), /absolute/);
});
