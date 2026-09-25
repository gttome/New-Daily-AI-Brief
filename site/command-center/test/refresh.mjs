import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import worker,{publishedEdition,refresh} from '../dist/server/index.js';
const snapshot=JSON.parse(fs.readFileSync('./state.json','utf8'));
const feed={items:[{title:'New story',url:'https://ndaib.gtome.chatgpt.site/stories/2026-09-24/new/'},{title:'Old story',url:'https://ndaib.gtome.chatgpt.site/stories/2026-09-23/old/'},{title:'Wrong host',url:'https://example.org/stories/2099-01-01/no/'}]};
test('published edition uses only canonical reader URLs and newest date',()=>{
 const p=publishedEdition(feed);assert.equal(p.date,'2026-09-24');assert.equal(p.stories,1);assert.equal(p.items.length,1);
 assert.throws(()=>publishedEdition({items:[]}));
});
test('one unavailable source does not suppress published reader or snapshot',async()=>{
 const original=globalThis.fetch;
 globalThis.fetch=async url=>{if(url.includes('feed.json'))return Response.json(feed);if(url.includes('raw.githubusercontent'))return Response.json(snapshot);throw Error('unavailable');};
 try{const r=await refresh();assert.equal(r.published.date,'2026-09-24');assert.equal(r.snapshot.executive.edition_date,'2026-09-24');assert.equal(r.errors.length,6);assert.ok(r.checked_at);}finally{globalThis.fetch=original;}
});
test('total source failure never generates a success timestamp',async()=>{
 const original=globalThis.fetch;globalThis.fetch=async()=>{throw Error('offline')};
 try{const r=await refresh();assert.equal(r.checked_at,null);assert.equal(r.errors.length,7);}finally{globalThis.fetch=original;}
});
test('endpoint refuses writes and unknown paths',async()=>{
 assert.equal((await worker.fetch(new Request('https://test/api/refresh',{method:'POST'}))).status,405);
 assert.equal((await worker.fetch(new Request('https://test/api/anything'))).status,404);
 assert.equal((await worker.fetch(new Request('https://test/'))).status,200);
});
test('Refresh refetches edition state on every click; rejects regressions and unsafe schedule state',async()=>{
 const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',className:'',insertAdjacentHTML(){},addEventListener(){}});return nodes.get(id)};
 let calls=0;const next=structuredClone(snapshot);next.executive.edition_date='2026-09-24';next.snapshot_generated_at='2026-09-25T00:00:00Z';
 const context=vm.createContext({document:{getElementById:node,querySelectorAll:()=>[],querySelector:()=>null},AbortSignal,fetch:async url=>{if(url==='state.json')return Response.json(snapshot);calls++;return Response.json({snapshot:calls===1?snapshot:next,published:publishedEdition(feed),errors:[]});}});
 context.URL=URL;context.Date=Date;const js=fs.readFileSync('./cc.js','utf8').replace('$("refresh").addEventListener("click",refreshAll);refreshAll();','');vm.runInContext(js,context);
 await vm.runInContext('refreshAll()',context);await vm.runInContext('refreshAll()',context);
 assert.equal(calls>=2,true);assert.equal(vm.runInContext('snapshot.executive.edition_date',context),'2026-09-24');
 context.older=snapshot;assert.equal(vm.runInContext('chooseSnapshot(snapshot,older).executive.edition_date',context),'2026-09-24');
 const unsafe=structuredClone(next);unsafe.schedules.creation_permitted=true;context.unsafe=unsafe;assert.equal(vm.runInContext('validSnapshot(unsafe)',context),false);
 assert.equal(node('refresh').disabled,false);assert.match(node('published-status').innerHTML,/2026-09-24/);
});
