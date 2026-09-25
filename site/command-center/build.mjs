import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
fs.writeFileSync('records.json',gunzipSync(fs.readFileSync('records.json.gz')));
const types={'index.html':'text/html; charset=utf-8','cc.css':'text/css; charset=utf-8','cc.js':'application/javascript; charset=utf-8','explorer.js':'application/javascript; charset=utf-8','state.json':'application/json; charset=utf-8','guide.html':'text/html; charset=utf-8','coverage.json':'application/json; charset=utf-8'};
const assets=Object.fromEntries(Object.entries(types).filter(([name])=>fs.existsSync('./'+name)).map(([name,type])=>['/'+name,{type,body:fs.readFileSync('./'+name,'utf8')}]));
fs.mkdirSync('dist/server',{recursive:true});fs.writeFileSync('dist/server/assets.mjs','export const assets='+JSON.stringify(assets)+';\n');
fs.writeFileSync('dist/server/data.mjs','export const seedRecords='+fs.readFileSync('./records.json','utf8')+';\nexport const importManifest='+fs.readFileSync('./import-manifest.json','utf8')+';\nexport const template='+fs.readFileSync('./state.json','utf8')+';\n');
for(const name of ['safety','store','analytics','projection','live','components'])fs.copyFileSync('./'+name+'.mjs','dist/server/'+name+'.mjs');
fs.copyFileSync('./worker.mjs','dist/server/index.js');
