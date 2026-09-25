import {hash,canonical,validateRevision} from './safety.mjs';
export const rows=async(stmt)=>(await stmt.all()).results||[];
export async function listRecords(db,family){return (await rows(db.prepare('SELECT payload FROM cc_records WHERE family=? ORDER BY edition DESC,id').bind(family))).map(x=>JSON.parse(x.payload));}
export async function getRecord(db,id){const r=(await rows(db.prepare('SELECT payload FROM cc_records WHERE id=?').bind(id)))[0];if(!r)return null;const record=JSON.parse(r.payload);const history=(await rows(db.prepare('SELECT payload FROM cc_revisions WHERE parent_id=? ORDER BY revision').bind(id))).map(x=>JSON.parse(x.payload));const last=history.at(-1);return {...record,...(last?{status:last.status,notes:last.notes,priority:last.priority,revision:last.revision}:{}),history:[...(record.history||[]),...history]};}
export async function importRecords(db,records,migrationId){
 const old=(await rows(db.prepare('SELECT payload FROM cc_migrations WHERE id=?').bind(migrationId)))[0];if(old)return {...JSON.parse(old.payload),replay:true};
 let inserted=0,duplicates=0,conflicts=0;const existingMap=new Map((await rows(db.prepare('SELECT id,digest FROM cc_records'))).map(r=>[r.id,r.digest]));const before=existingMap.size;
 for(let i=0;i<records.length;i+=40){const chunk=records.slice(i,i+40),digests=await Promise.all(chunk.map(hash));
  const existing=chunk.map(r=>existingMap.has(r.id)?[{digest:existingMap.get(r.id)}]:[]);
  for(let n=0;n<chunk.length;n++){if(existing[n].length){if(existing[n][0].digest===digests[n])duplicates++;else conflicts++;}else inserted++;}
  await db.batch(chunk.map((r,n)=>db.prepare('INSERT INTO cc_records(id,family,edition,payload,digest,imported_at) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(r.id,r.family,r.edition_date??null,JSON.stringify(r),digests[n],new Date().toISOString())));
 }
 const expected=records.map(r=>r.id).sort(),actual=await rows(db.prepare('SELECT id,digest FROM cc_records ORDER BY id'));
 const actualMap=new Map(actual.map(r=>[r.id,r.digest]));const missing=expected.filter(id=>!actualMap.has(id));
 const expectedDigests=await Promise.all(records.map(hash));const verified=records.filter((r,i)=>actualMap.get(r.id)===expectedDigests[i]).length;if(missing.length)throw new Error('Migration read-back failed');
 const receipt={migration_id:migrationId,source_count:records.length,destination_before:before,destination_after:actual.length,inserted,duplicates,conflicts,excluded:0,read_back:{status:'passed',ids_checksum:await hash(expected),record_count:expected.length,payload_digests_verified:verified,conflicted_payloads:records.length-verified},completed_at:new Date().toISOString()};
 await db.prepare('INSERT INTO cc_migrations(id,payload,completed_at) VALUES(?,?,?) ON CONFLICT(id) DO NOTHING').bind(migrationId,JSON.stringify(receipt),receipt.completed_at).run();return receipt;
}
export async function rateLimit(db,network,now=Date.now()){
 const day=Math.floor(now/86400000),short=Math.floor(now/300000),key=await hash('cc:'+day+':'+network);
 const keys=[`${key}:short:${short}`,`${key}:day:${day}`];
 await db.prepare('DELETE FROM cc_rate_buckets WHERE expires_at<?').bind(now).run();
 const result=await db.batch(keys.map((k,i)=>db.prepare('INSERT INTO cc_rate_buckets(bucket,count,expires_at) VALUES(?,1,?) ON CONFLICT(bucket) DO UPDATE SET count=count+1 RETURNING count').bind(k,now+(i?86400000:300000))));
 return result.every((x,i)=>(x.results?.[0]?.count||0)<=(i?100:10));
}
export async function appendRevision(db,id,input,network,verifyEvidence){
 const record=await getRecord(db,id);if(!record)return {status:404,error:'Record not found'};
 let body;try{body=validateRevision(input,record.family);}catch(e){return {status:400,error:e.message};}
 const requestDigest=await hash({id,body}),key=await hash(body.idempotency_key);
 const prior=(await rows(db.prepare('SELECT request_digest,payload FROM cc_revisions WHERE request_key=?').bind(key)))[0];
 if(prior)return prior.request_digest===requestDigest?{status:200,revision:JSON.parse(prior.payload),idempotent:true,read_back:true}:{status:409,error:'Idempotency key reused with different content'};
 if((record.revision||0)!==body.base_revision)return {status:409,error:'Revision conflict',current_revision:record.revision||0};
 if(body.status==='Applied'&&!(await verifyEvidence(record,body.application_evidence)))return {status:400,error:'Applied requires a verified change affecting the proposal target'};
 if(!(await rateLimit(db,network)))return {status:429,error:'Review limit reached; try later'};
 const event={revision_id:`${id}:r${body.base_revision+1}`,parent_id:id,revision:body.base_revision+1,previous_revision:body.base_revision,status:body.status,notes:body.notes,priority:body.priority??null,actor_kind:'anonymous',created_at:new Date().toISOString(),edition_date:record.edition_date,run_id:record.run_id??null,attempt_id:record.attempt_id??null,source_sha:record.source_sha??null,artifact_id:record.artifact_id??null,provenance:record.provenance,application_evidence:body.status==='Applied'?body.application_evidence:null};
 try{
  await db.prepare('INSERT INTO cc_revisions(parent_id,revision,request_key,request_digest,payload,created_at) SELECT ?,?,?,?,?,? WHERE COALESCE((SELECT MAX(revision) FROM cc_revisions WHERE parent_id=?),?)=?').bind(id,event.revision,key,requestDigest,JSON.stringify(event),event.created_at,id,record.revision||0,body.base_revision).run();
 }catch{return {status:409,error:'Concurrent revision or idempotency conflict'};}
 const saved=(await rows(db.prepare('SELECT payload FROM cc_revisions WHERE request_key=?').bind(key)))[0];
 if(!saved)return {status:409,error:'Revision conflict'};
 return {status:201,revision:JSON.parse(saved.payload),read_back:true};
}
export async function saveSnapshot(db,state){const id='cc-snapshot:'+state.executive.edition_date+':'+await hash(state);await db.prepare('INSERT INTO cc_snapshots(id,edition,source_sha,payload,verified_at) VALUES(?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(id,state.executive.edition_date,state.source.main_sha,JSON.stringify(state),new Date().toISOString()).run();const saved=(await rows(db.prepare('SELECT payload FROM cc_snapshots WHERE id=?').bind(id)))[0];if(!saved||canonical(JSON.parse(saved.payload))!==canonical(state))throw new Error('Snapshot read-back failed');return {id,read_back:true};}
export async function lastSnapshot(db){const r=(await rows(db.prepare('SELECT payload,verified_at FROM cc_snapshots ORDER BY verified_at DESC LIMIT 1')))[0];return r?{snapshot:JSON.parse(r.payload),verified_at:r.verified_at}:null;}
