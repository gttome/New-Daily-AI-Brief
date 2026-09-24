from __future__ import annotations
import argparse, json
from pathlib import Path
from new_daily_ai_brief import start_daily_brief

STAGES={
 'editorial_fixture_root':'editorial',
 'build_fixture_root':'build',
 'pre_release_fixture_root':'pre_release',
 'render_fixture_root':'render',
 'release_fixture_root':'release',
 'evaluation_fixture_root':'evaluation',
 'operations_fixture_root':'operations',
 'completion_fixture_root':'completion',
}

def main():
 p=argparse.ArgumentParser();p.add_argument('--date',required=True);p.add_argument('--mode',choices=['production','shadow','synthetic'],default='production');p.add_argument('--input-package',required=True);p.add_argument('--state-dir',default='.state/manual');a=p.parse_args()
 root=Path(a.input_package)/a.date
 missing=[name for name in STAGES.values() if not (root/name).is_dir()]
 if missing:
  raise SystemExit('fail-closed: canonical input package is incomplete for '+a.date+': '+', '.join(missing))
 kwargs={key:root/sub for key,sub in STAGES.items()}
 result=start_daily_brief(edition_date=a.date,mode=a.mode,state_root=Path(a.state_dir),owner='manual-github-operator',**kwargs)
 print(json.dumps(result,indent=2,sort_keys=True))
 return 0
if __name__=='__main__': raise SystemExit(main())
