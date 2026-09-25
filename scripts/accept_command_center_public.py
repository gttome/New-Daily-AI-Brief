"""Bounded anonymous acceptance; never dispatches a production workflow."""
import argparse,json,uuid,urllib.request,urllib.error,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--url',default='https://npccs.gtome.chatgpt.site');p.add_argument('--output',required=True);p.add_argument('--write-probe',action='store_true');a=p.parse_args();checks=[]
def request(path,method='GET',body=None):
 req=urllib.request.Request(a.url+path,method=method,headers={'Accept':'application/json','Origin':a.url,'Content-Type':'application/json','User-Agent':'Command-Center-Acceptance/1.0'},data=json.dumps(body).encode() if body is not None else None)
 try:
  with urllib.request.urlopen(req,timeout=25) as r:status=r.status;raw=r.read()
 except urllib.error.HTTPError as e:status=e.code;raw=e.read()
 try:data=json.loads(raw)
 except Exception:data={'response_excerpt':raw[:128].decode(errors='replace')}
 checks.append({'path':path,'method':method,'status':status});return status,data
report={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'anonymous':True,'credentials_used':False,'checks':checks,'production_dispatch_performed':False}
try:
 status,health=request('/api/cc/v1/health');report['health']=health
 if status!=200:raise RuntimeError('Public read blocked: '+str(status)+' '+str(health))
 for area in ['editions','candidates','media','book-proposals','watchlist','sources','qa','incidents','usage','feedback','learning','audience','components','automation','evidence']:
  status,data=request('/api/cc/v1/'+area+'?limit=1');assert status==200,(area,status)
 status,state=request('/api/cc/v1/state');assert status==200;report['identity']=state['identity'];report['snapshot_persistence']=state.get('persistence')
 for path in ['/api/cc/v1/dispatch','/api/cc/v1/force-replace','/api/cc/v1/publish']:
  status,_=request(path,'POST',{});assert status in [404,405]
 if a.write_probe:
  status,data=request('/api/cc/v1/book-proposals?status=Pending%20review&limit=100');record=next(r for r in data['records'] if r['family']=='book-proposals' and len(r.get('notes',''))<3000)
  body={'base_revision':record.get('revision',0),'idempotency_key':str(uuid.uuid4()),'status':record['status'],'notes':record.get('notes','')+'\nAnonymous persistence acceptance probe. No production or editorial action requested.'};path='/api/cc/v1/book-proposals/'+urllib.parse.quote(record['id'],safe='')+'/revisions'
  status,saved=request(path,'POST',body);assert status==201,saved;report['public_write_revision']=saved['revision']['revision_id'];assert saved['revision']['actor_kind']=='anonymous';assert saved['read_back']
  status,replay=request(path,'POST',body);assert status==200 and replay['idempotent']
  status,conflict=request(path,'POST',{**body,'idempotency_key':str(uuid.uuid4())});assert status==409
  status,read=request('/api/cc/v1/evidence?id='+urllib.parse.quote(record['id'],safe=''));assert read['record']['revision']==saved['revision']['revision'];report['write_read_back']=True
 report['result']='PASS'
except Exception as e:report.update(result='BLOCKED_OR_FAILED',reason=str(e))
Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'result':report['result'],'checks':len(checks),'reason':report.get('reason')}))
raise SystemExit(0 if report['result']=='PASS' else 1)
