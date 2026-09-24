import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createReaderWorker} from './worker.mjs';
import {localDB} from './local-db.mjs';
const date='2026-09-23',item='dab-podcast-2026-09-23-second',origin='https://ndaib.gtome.chatgpt.site';
function harness(){
 const DB=localDB(),worker=createReaderWorker({items:[date+'|'+item],topics:['topic-one']});
 const call=(path,body,operation=crypto.randomUUID(),extra={})=>worker.fetch(new Request(origin+'/api/'+path,body===undefined?{}:{method:'POST',headers:{origin,'content-type':'application/json','x-operation-id':operation,...extra},body:JSON.stringify(body)}),{DB});
 return {DB,call};
}
test('both podcast-shaped IDs use the same canonical item contract; retries count once',async()=>{
 const {DB,call}=harness(),id=crypto.randomUUID(),body={brief_date:date,item_id:item,rating:5};
 assert.equal((await call('ratings',body,id)).status,200);
 assert.equal((await call('ratings',body,id)).status,200);
 assert.equal((await call('ratings',{...body,rating:1},id)).status,409);
 assert.deepEqual((await (await call('ratings?brief_date='+date+'&item_id='+item)).json()).totals,{'5':1});
 DB.close();
});
test('unknown items, cross-origin writes, invalid JSON shapes and unbounded values fail closed',async()=>{
 const {DB,call}=harness(),body={brief_date:date,item_id:item,rating:3};
 assert.equal((await call('ratings',body,crypto.randomUUID(),{origin:'https://evil.example'})).status,403);
 assert.equal((await call('ratings',{...body,item_id:'unknown'})).status,404);
 assert.equal((await call('ratings',{...body,rating:6})).status,400);
 assert.equal((await call('ratings',[],crypto.randomUUID())).status,400);
 assert.equal((await call('comments',{...body,body:'x'.repeat(9000)})).status,413);
 assert.equal((await call('ratings',body,'not-an-operation')).status,400);
 DB.close();
});
test('share and reading events are persisted once, without accepting arbitrary metric names',async()=>{
 const {DB,call}=harness(),operation=crypto.randomUUID(),body={brief_date:date,item_id:item,metric:'share_initiations'};
 await call('events',body,operation);await call('events',body,operation);
 assert.deepEqual((await (await call('events?brief_date='+date+'&item_id='+item)).json()).totals,{share_initiations:1});
 assert.equal((await call('events',{...body,metric:'arbitrary'})).status,400);
 DB.close();
});
test('private comments are retained, retried once, never exposed by GET, and expired rows are purged',async()=>{
 const {DB,call}=harness(),operation=crypto.randomUUID(),body={brief_date:date,item_id:item,body:'Local QA only'};
 DB.prepare('INSERT INTO reader_comments VALUES(?,?,?,?,?)').bind('old',date,item,'expired',Date.now()-91*86400000).run();
 await call('comments',body,operation);await call('comments',body,operation);
 assert.equal((await call('comments')).status,405);
 assert.equal(DB.prepare('SELECT COUNT(*) AS n FROM reader_comments').all().results[0].n,1);
 assert.equal((await call('comments',{...body,body:'changed'},operation)).status,409);
 DB.close();
});
test('watchlist revisions support changing a vote; stale retries cannot restore old choices',async()=>{
 const {DB,call}=harness(),body={topic_id:'topic-one',ballot:crypto.randomUUID(),choice:'very_interested',revision:1};
 await call('watchlist',body);await call('watchlist',body);
 await call('watchlist',{...body,choice:'not_interested',revision:2});
 const stale=await (await call('watchlist',body)).json();assert.equal(stale.choice,'not_interested');assert.equal(stale.revision,2);
 assert.equal((await call('watchlist',{...body,choice:'somewhat_interested',revision:2})).status,409);
 assert.deepEqual((await (await call('watchlist')).json()).totals,[{topic_id:'topic-one',choice:'not_interested',count:1}]);
 DB.close();
});
test('email subscription is not advertised without a configured provider',async()=>{
 const {DB,call}=harness();assert.deepEqual(await (await call('subscriptions')).json(),{available:false});DB.close();
});
