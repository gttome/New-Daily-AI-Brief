// Supervised preview only; no dev code is included in the production Worker.
import {defineConfig} from 'vite';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createReaderWorker} from './worker.mjs';
import {localDB} from './local-db.mjs';
export default defineConfig({
 root:resolve(process.cwd(),'out'),appType:'mpa',
 server:{host:'0.0.0.0',port:4173,strictPort:true,allowedHosts:['terminal.local']},
 plugins:[{name:'ndaib-feedback-preview',transformIndexHtml(html){return html.replaceAll('https://ndaib.gtome.chatgpt.site/','/').replace('<head>','<head><script>if(!crypto.randomUUID)crypto.randomUUID=()=>"10000000-1000-4000-8000-100000000000".replace(/[018]/g,c=>(c^crypto.getRandomValues(new Uint8Array(1))[0]&15>>c/4).toString(16));</script>');},configureServer(server){
  const registry=JSON.parse(readFileSync(resolve(process.cwd(),'out.runtime/registry.json'),'utf8'));
  const worker=createReaderWorker(registry),DB=localDB();
  server.middlewares.use(async(req,res,next)=>{
   if(req.url.startsWith('/__qa_mobile')){
    const path=new URL(req.url,'http://localhost').searchParams.get('path')||'/';
    if(!/^\/[a-zA-Z0-9_/-]*$/.test(path)){res.writeHead(400);res.end();return;}
    res.setHeader('content-type','text/html');
    res.end('<!doctype html><html><head><title>NDAIB 390px responsive QA</title></head><body style="margin:0;background:#ddd;display:flex;justify-content:center"><output id="qa-metrics" style="position:fixed;left:12px;top:20px;width:220px;overflow-wrap:anywhere"></output><iframe title="390px reader viewport" src="'+path+'" style="width:390px;height:900px;border:0;background:white"></iframe><script>const f=document.querySelector("iframe");setInterval(()=>{const d=f.contentDocument;if(!d)return;document.querySelector("output").textContent=JSON.stringify({viewport:f.contentWindow.innerWidth,scrollWidth:d.documentElement.scrollWidth,images:[...d.images].map(i=>({loaded:i.complete&&i.naturalWidth>0,width:Math.round(i.getBoundingClientRect().width)}))});},300);</script></body></html>');return;
   }
   if(!req.url.startsWith('/api/'))return next();
   try{
    const init={method:req.method,headers:req.headers};
    if(!['GET','HEAD'].includes(req.method)){init.body=req;init.duplex='half';}
    const response=await worker.fetch(new Request('http://'+req.headers.host+req.url,init),{DB});
    res.writeHead(response.status,Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
   }catch{res.writeHead(500);res.end('Preview request failed');}
  });
 }}]
});
