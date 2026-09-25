#!/usr/bin/env python3
"""Non-destructive deterministic Command Center access-schema migration."""
import argparse,copy,hashlib,json
from pathlib import Path
STATES=['Pending review','Approved','Rejected','Proposed','Accepted','Applied','Deferred','Dismissed']
def migrate(source):
 if source.get('schema_version')=='2.0.0': return copy.deepcopy(source)
 if source.get('schema_version')!='1.0.0':raise ValueError('unsupported source schema')
 d=copy.deepcopy(source);d['schema_version']='2.0.0'
 d['privacy'].update(surface='public-command-center',application_data_classification='public',contains_payment_account_details=False,contains_third_party_identifying_information=False)
 d['legacy_import_source']=d.pop('private_owner_data',{})
 d['public_application_data']={'transport':'Sites D1','values_public':True,'review_writes':{'anonymous_allowed':True,'append_only_history':True,'revision_protection':True,'idempotency':True,'rate_limited':True},'usage_history':{'dedupe_key':'attempt_id + measurement_boundary','estimated_values_allowed':False},'book_change_proposals':{'states':STATES,'dedupe_key':'stable proposal ID','prior_owner_decisions_preserved':True}}
 d['command_center_site'].update(public_access=True,requires_owner_sign_in=False,publication_state='public_release_candidate',live_url='https://npccs.gtome.chatgpt.site')
 d['data_domains'].pop('private_owner_only',None);d['data_domains']['public_application_records']={'status':'runtime_required','current_source':'Sites D1'}
 return d
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();
 if Path(a.source).resolve()==Path(a.output).resolve():raise ValueError('Migration requires a separate output; source must be preserved')
 source=Path(a.source).read_bytes();out=json.dumps(migrate(json.loads(source)),indent=2)+'\n';Path(a.output).write_text(out);print(json.dumps({'source_sha256':hashlib.sha256(source).hexdigest(),'output_sha256':hashlib.sha256(out.encode()).hexdigest(),'source_preserved':Path(a.source)!=Path(a.output)}))
