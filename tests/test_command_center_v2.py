import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from migrate_command_center_state_v1_to_v2 import migrate,STATES
class MigrationTests(unittest.TestCase):
 def test_v1_v2_deterministic_non_destructive(self):
  v1=json.loads(__import__('subprocess').check_output(['git','show','ffae7b31e3cd7f86428ab4811245cabe0eed7a9c:site/command-center/state.json'],cwd=ROOT));before=copy.deepcopy(v1);out=migrate(v1)
  self.assertEqual(v1,before);self.assertEqual(migrate(out),out);self.assertEqual(out['public_application_data']['book_change_proposals']['states'],STATES);self.assertEqual(out['schedules'],v1['schedules'])
  schema=json.loads((ROOT/'schemas/command-center-state.schema.json').read_text());self.assertEqual([x['properties']['schema_version']['const'] for x in schema['oneOf']],['1.0.0','2.0.0'])
 def test_rejects_unknown_schema(self):
  with self.assertRaises(ValueError):migrate({'schema_version':'3.0.0'})

if __name__=="__main__":unittest.main()
