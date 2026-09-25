#!/usr/bin/env python3
"""Build sanitized, provenance-bearing import input. Never writes legacy/reader sources."""
import argparse,json,hashlib,re,datetime
from pathlib import Path
DENY={'email','email_address','ip','ip_address','session_id','ballot','operation','owner_email','account_id','account_user_id','user_id','authorization','cookie','token','api_key','password','secret','visitor_id','client_id','customer_id','subscriber_id','phone','phone_number','address','postal_address','billing','payment','account','site_project_id','site_version_id','deployment_id','prompt','generation_prompt','internal_prompt'}
SENSITIVE=re.compile(r'(?:sk-[a-zA-Z0-9_-]{16,}|gh[pousr]_[a-zA-Z0-9]{16,}|github_pat_[a-zA-Z0-9_]+|Bearer\s+[\w.-]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}|\b\d{3}-\d{2}-\d{4}\b)')
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def clean(x,counts):
 if isinstance(x,dict):
  out={}
  for k,v in x.items():
   if k.lower() in DENY:counts['fields']+=1;continue
   out[k]=clean(v,counts)
  return out
 if isinstance(x,list):return [clean(v,counts) for v in x]
 if isinstance(x,str) and SENSITIVE.search(x):counts['fields']+=1;return '[excluded sensitive field]'
 return x
def dateof(d,path=''):
 for k in ['edition_date','brief_date','date','day','edition','edition_id','snapshot_date']:
  m=re.search(r'20\d\d-\d\d-\d\d',str(d.get(k,'')))
  if m:return m[0]
 m=re.search(r'20\d\d-\d\d-\d\d',str(d.get('details',{}).get('edition_id',''))+' '+path);return m[0] if m else None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--imports',required=True);ap.add_argument('--canonical',required=True);ap.add_argument('--old-source',required=True);ap.add_argument('--reader-source',required=True);a=ap.parse_args();root=Path(__file__).resolve().parents[1];legacy=root/'legacy_snapshot';records={};counts={'fields':0,'excluded_records':0,'duplicates':0,'conflicts':0};now=(json.loads((root/'site/command-center/import-manifest.json').read_text()).get('prepared_at') if (root/'site/command-center/import-manifest.json').exists() else datetime.datetime.now(datetime.timezone.utc).isoformat());sources=[]
 legacysha='4ac06268048a3241d2ecaa5ce7c2638266500d75';newsha='4a0faf7bc3637bab7d27ee95bfa0dc542e0f958c'
 def add(family,d,ref,sha,identity=None,date=None,**extra):
  if not isinstance(d,dict):d={'value':d}
  safe=clean(d,counts);rid=identity or f'{family}:{digest([ref,safe])[:24]}'
  rec={'id':rid,'family':family,'edition_date':date or dateof(d,ref),'run_id':d.get('run_id'),'attempt_id':d.get('attempt_id'),'stage_id':d.get('produced_by_stage'),'source_sha':sha,'artifact_id':d.get('artifact_id'),'artifact_digest':d.get('content_digest') or 'sha256:'+digest(d),'observed_at':d.get('observed_at') or d.get('generated_at') or d.get('updated_at') or now,'availability':{'status':'available','reason':None},'provenance':[{'source_ref':ref,'source_type':'migration','observed_at':now}],'title':d.get('title') or d.get('headline') or d.get('item_title') or d.get('name') or str(ref).split('/')[-1],'data':safe,**extra}
  if rid in records:
   if records[rid]['data']==safe:counts['duplicates']+=1
   else:counts['conflicts']+=1;rid+=':observation:'+digest(safe)[:12];rec['id']=rid;rec['availability']={'status':'conflict','reason':'multiple_source_observations'}
  records[rid]=rec
 def file_records(p,ref,sha):
  try:
   ds=[json.loads(line) for line in p.read_text().splitlines() if line.strip()] if p.suffix=='.jsonl' else [json.loads(p.read_text())]
  except Exception:counts['excluded_records']+=1;return
  path=str(p);family=next((v for k,v in [('watchlist','watchlist-history'),('media-','media'),('candidates','candidates'),('discovery','candidates'),('story-memory','story-memory'),('editorial/videos','media'),('editorial/podcasts','media'),('media-preflight','media'),('image-quality','images'),('/images/','images'),('watchlist','watchlist-history'),('source-reliability','sources'),('accessibility','accessibility'),('/qa','qa'),('ledgers','corrections'),('editorial-learning','learning'),('editorial-feedback','learning'),('/trends/','trends'),('/analytics/','feedback'),('/attempts/','usage'),('/efficiency/','usage'),('/publication/','publication'),('/releases/','publication'),('command-center','incidents'),('/operations/','components'),('/editions/','editions')] if k in path),'evidence')
  for d in ds:
   add(family,d,ref,sha)
   if isinstance(d,dict) and isinstance(d.get('candidates'),list) and '/editorial/candidates/' in path:
    for row in d['candidates']:add('candidate',row,ref,sha,identity=row.get('candidate_id'),date=dateof(d,path))
   if family=='editions' and isinstance(d,dict):
    for row in d.get('stories',[]):add('stories',row,ref,sha,identity=row.get('story_id'),date=dateof(d,path))
 for p in sorted((legacy/'_records').rglob('*')):
  if p.suffix in ['.json','.jsonl'] and not any(x in str(p) for x in ['generation-prompts','personal-feedback']):file_records(p,'https://github.com/gttome/Daily-AI-Brief/blob/'+legacysha+'/'+str(p.relative_to(legacy)),legacysha)
 for p in sorted((legacy/'_data/story-memory').glob('*.json')):file_records(p,'https://github.com/gttome/Daily-AI-Brief/blob/'+legacysha+'/'+str(p.relative_to(legacy)),legacysha)
 for name,family in [('source-registry.json','sources'),('watchlist-source-state.json','sources'),('book-reading.json','books')]:
  p=legacy/'_data'/name;add(family,json.loads(p.read_text()),'https://github.com/gttome/Daily-AI-Brief/blob/'+legacysha+'/'+str(p.relative_to(legacy)),legacysha)
 for p in sorted((legacy/'_data/editions').glob('*.json')):file_records(p,'https://github.com/gttome/Daily-AI-Brief/blob/'+legacysha+'/'+str(p.relative_to(legacy)),legacysha)
 can=Path(a.canonical)
 for base in ['.state/manual/2026-09-24__production','.runtime-source/_records','.runtime-source/_data/editions']:
  for p in sorted((can/base).rglob('*.json')):
   if p.name=='lease.json':continue
   ref='https://github.com/gttome/New-Daily-AI-Brief/actions/runs/36051784007/artifacts/10829999743#'+str(p.relative_to(can));file_records(p,ref,newsha)
   d=json.loads(p.read_text())
   if '/evidence-packets/' in str(p):
    packet={**d.get('data',{}),'selected':True,'selection_rationale':'Selected in the locked canonical discovery artifact; detailed evidence preserved','evidence_class':d.get('data',{}).get('provenance',{}).get('source_reliability','publisher_authored')}
    add('candidate',packet,ref,newsha,identity=d.get('candidate_id'),date='2026-09-24')
   if p.name in ['discovery-metrics.json','build-metrics.json']:
    add('usage',{'metrics':d,'measurement_boundary':'canonical-build-instrumentation (excludes external preparation)','attempt_id':'36051784007:'+p.stem},ref,newsha,date='2026-09-24',run_id='36051784007')
   if d.get('status')=='locked' and d.get('artifact_id'):
    add('canonical',d,ref,newsha,identity=d['artifact_id'],date=d['edition_date'])
    if d.get('artifact_type')=='discovery':
     for c in d.get('data',{}).get('candidates',[]):add('candidate',c,ref,newsha,identity=c.get('candidate_id') or c.get('id'),date=d['edition_date'])
 # Full structured latest edition copied from actual validated canonical artifact.
 current=json.loads((can/'.runtime-source/_data/editions/2026-09-24.json').read_text());add('editions',current,'https://github.com/gttome/New-Daily-AI-Brief/actions/runs/36051784007/artifacts/10829999743',newsha,identity='edition:2026-09-24')
 reader=Path(a.reader_source)
 for name,family,key in [('watchlist.json','watchlist','topics'),('early-signal-sources.json','channels','channels'),('watchlist-sources.json','sources','sources')]:
  d=json.loads((reader/'out/data'/name).read_text());items=d.get(key,[]);items=[{'source_id':k,**v} for k,v in items.items()] if isinstance(items,dict) else items
  for row in items:add(family,row,'https://ndaib.gtome.chatgpt.site/data/'+name,'55b8d93ec53601ea2f1d6c84ce00089f24a8527d',identity=str(row.get('topic_id') or row.get('id') or '') or None,date=dateof(d),revision=0)
 for p in sorted(Path(a.imports).glob('*.json')):
  name=p.stem
  if name=='prepared-receipt':continue
  if any(name=='legacy-'+t for t in ['rating_totals','event_totals','event_days','audience_totals']):continue
  doc=json.loads(p.read_text());sources.append({'source':name,'rows_received':len(doc.get('rows',[])),'remaining_offset':doc.get('remaining_offset'),'truncated_values':doc.get('model_projection',{}).get('truncated_values',0)})
  for row in doc.get('rows',[]):
   ref='legacy-runtime:'+name;family='evidence';d=row;extra={};ident=None
   if 'book_reviews' in name:
    try:d={**json.loads(row['suggestion']),'notes':row['notes'],'proof':row['proof']};hist=json.loads(row['history'])
    except Exception:counts['excluded_records']+=1;continue
    family='book-proposals';ident=row['id'];extra={'status':row['status'],'revision':row['revision'],'notes':clean(row['notes'],counts),'history':clean(hist,counts),'title':d.get('title'), 'application_evidence_availability':'available' if row.get('proof') else 'incomplete'}
   elif 'book_evaluation' in name:
    family='proposal-evaluations'
    try:d={**row,'evaluation':json.loads(row['evaluation'])}
    except Exception:counts['excluded_records']+=1;continue
   elif 'book_import' in name:family='migration-source-receipts'
   elif 'maintenance' in name:family='retention'
   elif 'edition_usage' in name or 'private_snapshots' in name:
    try:d=json.loads(row['payload'])
    except Exception:counts['excluded_records']+=1;continue
    family='usage' if 'usage' in name else 'snapshots';ident='usage:'+row['attempt_id'] if 'usage' in name else None
   elif 'reader_comments' in name:family='comments';ident=str(row.get('id') or '') or None;extra={'status':row.get('review_state','Pending review'),'notes':clean(row.get('notes',''),counts),'revision':0}
   elif 'watchlist_review' in name:family='watchlist-reviews'
   elif 'rating_totals' in name:family='ratings'
   elif 'event_days' in name:family='event-days'
   elif 'event_totals' in name:family='events'
   elif 'audience_totals' in name:
    family='audience'
    try:d={**row,'dimensions':json.loads(row['dimensions'])}
    except Exception:counts['excluded_records']+=1;continue
   elif 'audience_metadata' in name:family='audience-metadata'
   elif name=='reader-reader_feedback':family='native-feedback'
   elif 'watchlist_ballots' in name:family='watchlist-interest'
   add(family,d,ref,None,identity=ident,**extra)
 recovery=Path(a.old_source)/'private-evidence/september-21-22-evaluations.json'
 if recovery.exists():
  for d in json.loads(recovery.read_text()).get('evaluations',[]):add('proposal-evaluations',d,'old-sites-source:ff0ed5f4ca8fd97696f4043dc5a18cc48de7180c/private-evidence/september-21-22-evaluations.json','ff0ed5f4ca8fd97696f4043dc5a18cc48de7180c',identity=d['id'])
 out=root/'site/command-center';(out/'records.json').write_text(json.dumps(list(records.values()),separators=(',',':'))+'\n');receipt={'prepared_at':now,'record_count':len(records),'families':{f:sum(r['family']==f for r in records.values()) for f in sorted({r['family'] for r in records.values()})},'exclusions':counts,'sources':sources,'source_sha':newsha,'canonical_run':36051784007,'canonical_artifact':10829999743,'read_back':'pending deployed import'};(out/'import-manifest.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
