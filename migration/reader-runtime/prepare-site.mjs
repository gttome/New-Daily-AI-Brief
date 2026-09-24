// Packaging only: consumes the already reviewed canonical reader output.
// This does not discover, select, generate, or publish an edition.
import {cp,mkdir,readFile,rm,writeFile} from 'node:fs/promises';
const expected='appgprj_6ab087e80a888191abb0f806118aa194';
const existing=JSON.parse(await readFile('.openai/hosting.json','utf8'));
const incoming=JSON.parse(await readFile('out.runtime/hosting.json','utf8'));
if(existing.project_id!==expected||incoming.project_id!==expected)throw Error('Existing ndaib identity required');
await writeFile('.openai/hosting.json',JSON.stringify(incoming,null,2)+'\n');
await cp('out.runtime/drizzle','drizzle',{recursive:true});
await rm('dist',{recursive:true,force:true});
await mkdir('dist/.openai',{recursive:true});
await cp('out','dist/client',{recursive:true});
await cp('out.runtime/server','dist/server',{recursive:true});
await cp('drizzle','dist/.openai/drizzle',{recursive:true});
await cp('.openai/hosting.json','dist/.openai/hosting.json');
const worker=await import(new URL('../out.runtime/server/index.js',import.meta.url));
if(typeof worker.default?.fetch!=='function')throw Error('Worker fetch export missing');
console.log('Packaged reviewed reader with NDAIB-owned feedback');
