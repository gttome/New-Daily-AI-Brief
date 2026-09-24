// NDAIB-owned feedback; no calls or writes to the legacy production service.
const metrics=new Set(['share_initiations','views','retention_30s','source_clicks','permanent_page_clicks','worth_watching_clicks']);
const choices=new Set(['very_interested','somewhat_interested','not_interested']);
const uuid=s=>typeof s==='string'&&/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(s);
const json=(value,status=200)=>Response.json(value,{status,headers:{'cache-control':'no-store','x-content-type-options':'nosniff'}});
const bad=(message,status=400)=>json({recorded:false,error:message},status);
export function createReaderWorker(registry){
 const items=new Set(registry.items),topics=new Set(registry.topics);
 async function handle(request,env){
  const url=new URL(request.url),path=url.pathname;
  if(!path.startsWith('/api/'))return env.ASSETS?env.ASSETS.fetch(request):new Response('Not found',{status:404});
  if(!['/api/ratings','/api/events','/api/comments','/api/watchlist','/api/subscriptions'].includes(path))return bad('Not found',404);
  if(path==='/api/subscriptions')return request.method==='GET'?json({available:false}):bad('Use RSS or calendar subscription',503);
  if(!['GET','POST'].includes(request.method))return bad('Method not allowed',405);
  if(!env.DB)return bad('Feedback storage unavailable',503);
  // Comments have no public read endpoint. The Site owner reviews them through D1.
  if(request.method==='GET'){
   if(path==='/api/comments')return bad('Method not allowed',405);
   if(path==='/api/watchlist'){
    const rows=await env.DB.prepare('SELECT topic AS topic_id,choice,COUNT(*) AS count FROM reader_watchlist_ballots GROUP BY topic,choice').all();
    return json({totals:rows.results});
   }
   const edition=url.searchParams.get('brief_date'),item=url.searchParams.get('item_id');
   if(!items.has(edition+'|'+item))return bad('Unknown published item',404);
   const kind=path==='/api/ratings'?'rating':'event';
   const rows=await env.DB.prepare('SELECT value,COUNT(*) AS count FROM reader_feedback WHERE edition=? AND item=? AND kind=? GROUP BY value').bind(edition,item,kind).all();
   return json({totals:Object.fromEntries(rows.results.map(r=>[r.value,r.count]))});
  }
  const origin=request.headers.get('origin');
  if(origin!=='https://ndaib.gtome.chatgpt.site' && !(origin===url.origin&&['localhost','127.0.0.1','terminal.local'].includes(url.hostname)))return bad('Origin not allowed',403);
  if(request.headers.get('sec-fetch-site')==='cross-site')return bad('Origin not allowed',403);
  if(!request.headers.get('content-type')?.startsWith('application/json'))return bad('JSON required',415);
  const stream=request.body?.getReader();let chunks=[],size=0;
  if(!stream)return bad('Body required');
  while(true){const {done,value}=await stream.read();if(done)break;size+=value.length;if(size>8192){await stream.cancel();return bad('Request too large',413);}chunks.push(value);}
  let body;try{const bytes=new Uint8Array(size);let offset=0;for(const part of chunks){bytes.set(part,offset);offset+=part.length;}body=JSON.parse(new TextDecoder().decode(bytes));}catch{return bad('Invalid JSON');}
  if(!body||typeof body!=='object'||Array.isArray(body))return bad('Object required');
  const now=Date.now();
  if(path==='/api/watchlist'){
   const {topic_id:topic,ballot,choice,revision}=body;
   if(!topics.has(topic)||!uuid(ballot)||!choices.has(choice)||!Number.isSafeInteger(revision)||revision<1||revision>1000000)return bad('Invalid vote');
   const result=await env.DB.batch([
    env.DB.prepare('INSERT INTO reader_watchlist_ballots(topic,ballot,choice,revision,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(topic,ballot) DO UPDATE SET choice=excluded.choice,revision=excluded.revision,updated_at=excluded.updated_at WHERE excluded.revision>reader_watchlist_ballots.revision').bind(topic,ballot,choice,revision,now),
    env.DB.prepare('SELECT choice,revision FROM reader_watchlist_ballots WHERE topic=? AND ballot=?').bind(topic,ballot)
   ]);
   const saved=result[1].results[0];
   if(saved.revision===revision&&saved.choice!==choice)return bad('Revision already used',409);
   return json({recorded:true,...saved});
  }
  const {brief_date:edition,item_id:item}=body,operation=request.headers.get('x-operation-id');
  if(!items.has(edition+'|'+item))return bad('Unknown published item',404);
  if(!uuid(operation))return bad('Operation ID required');
  if(path==='/api/comments'){
   if(typeof body.body!=='string'||!body.body.trim()||body.body.trim().length>1000)return bad('Comment must be 1–1000 characters');
   const comment=body.body.trim();
   const result=await env.DB.batch([
    env.DB.prepare('DELETE FROM reader_comments WHERE created_at<?').bind(now-90*86400000),
    env.DB.prepare('INSERT INTO reader_comments(operation,edition,item,body,created_at) VALUES(?,?,?,?,?) ON CONFLICT(operation) DO NOTHING').bind(operation,edition,item,comment,now),
    env.DB.prepare('SELECT edition,item,body FROM reader_comments WHERE operation=?').bind(operation)
   ]);
   const saved=result[2].results[0];
   if(saved.edition!==edition||saved.item!==item||saved.body!==comment)return bad('Operation ID already used',409);
   return json({recorded:true});
  }
  const kind=path==='/api/ratings'?'rating':'event';
  const aliases={most_useful:5,useful:4,neutral:3,not_useful:1};
  const rating=aliases[body.rating]??body.rating;
  if(kind==='rating'&&(!Number.isInteger(rating)||rating<1||rating>5))return bad('Rating must be 1–5');
  if(kind==='event'&&!metrics.has(body.metric))return bad('Invalid metric');
  const value=kind==='rating'?String(rating):body.metric;
  const result=await env.DB.batch([
   env.DB.prepare('INSERT INTO reader_feedback(operation,kind,edition,item,value,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(operation) DO NOTHING').bind(operation,kind,edition,item,value,now),
   env.DB.prepare('SELECT kind,edition,item,value FROM reader_feedback WHERE operation=?').bind(operation),
   env.DB.prepare('SELECT COUNT(*) AS count FROM reader_feedback WHERE edition=? AND item=? AND kind=? AND value=?').bind(edition,item,kind,value)
  ]);
  const saved=result[1].results[0];
  if(saved.kind!==kind||saved.edition!==edition||saved.item!==item||saved.value!==value)return bad('Operation ID already used',409);
  return json({recorded:true,count:result[2].results[0].count});
 }
 return {async fetch(request,env){try{return await handle(request,env);}catch{return bad('Feedback temporarily unavailable',503);}}};
}
