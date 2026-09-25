// Local QA adapter only. Production uses the Site's D1 binding.
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
export function localDB(){
 const db=new DatabaseSync(':memory:');
 const dir=fileURLToPath(new URL('./drizzle/',import.meta.url));
 for(const file of readdirSync(dir).filter(x=>x.endsWith('.sql')).sort())db.exec(readFileSync(dir+'/'+file,'utf8'));
 const prepare=(sql,values=[])=>({
  bind(...args){return prepare(sql,args);},
  all(){return {results:db.prepare(sql).all(...values)};},
  run(){return db.prepare(sql).run(...values);},
  execute(){return /(^\s*SELECT|RETURNING)/i.test(sql)?this.all():{results:[],meta:this.run()};}
 });
 return {prepare,batch(statements){db.exec('BEGIN');try{const result=statements.map(s=>s.execute());db.exec('COMMIT');return result;}catch(error){db.exec('ROLLBACK');throw error;}},close(){db.close();}};
}
