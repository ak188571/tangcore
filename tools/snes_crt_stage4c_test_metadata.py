"""Temporary metadata guards on workspace-only substitute cards; no device access."""
from pathlib import Path
import importlib.util,json,struct,unittest,zlib
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=module('base_guards',HERE/'test_deploy.py');m=module('metadata_guards',HERE/'metadata.py')
d=base.d;k=d.k;m.d=d;m.k=k

def record(kind,generation,value):
    data=bytearray(b'CRT1'+bytes([1,2,kind,0]))
    data+=struct.pack('<IQ',0x232bb5b8,2097152)+bytes([value,0,0,0])+struct.pack('<I',generation)
    return bytes(data)+struct.pack('<I',zlib.crc32(data)&0xffffffff)

class MetadataGuards(unittest.TestCase):
    tearDown=base.DeploymentGuards.tearDown
    save=base.DeploymentGuards.save
    reload=base.DeploymentGuards.reload
    def setUp(self):
        base.DeploymentGuards.setUp(self)
        fixture=d.image('titles_fixture').read_bytes()
        original=b''.join(line.rstrip(b'\r\n').rsplit(b'\t',1)[0]+line[len(line.rstrip(b'\r\n')):] for line in fixture.splitlines(keepends=True))
        for name,data in [(m.T,original),(m.A,record(0,3,27)),(m.B,record(0,2,23))]:
            for parent in [self.card,self.session/'sd']:
                p=parent/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            self.state['sd']['files'][name]=d.file_entry(self.card/name)
        self.state.update(flash_installed={'verified':True},sd_installed={'files':dict(self.state['sd']['files'])})
        self.save();self.args.snapshot=str(self.root/'capture')
    def install(self):m.install(self.args);self.state=self.reload()
    def reset_saved(self):self.install();(self.card/m.B).write_bytes(record(1,4,0))
    def test_metadata_install_preserves_every_record_title_and_attribute(self):
        original=(self.card/m.T).read_bytes();before={name:d.file_entry(self.card/name) for name in self.state['sd']['files']}
        d.set_attrs(self.card/m.T,d.attrs(self.card/m.T)|1)
        self.state['sd']['files'][m.T]=d.file_entry(self.card/m.T);self.state['sd_installed']['files'][m.T]=d.file_entry(self.card/m.T);self.save()
        self.install();self.assertEqual(d.attrs(self.card/m.T),self.state['sd']['files'][m.T]['attributes'])
        fixture=(self.card/m.T).read_bytes()
        self.assertEqual(b''.join(line.rstrip(b'\r\n').rsplit(b'\t',1)[0]+line[len(line.rstrip(b'\r\n')):] for line in fixture.splitlines(keepends=True)),original)
        for name,row in before.items():
            if name!=m.T:self.assertEqual(d.file_entry(self.card/name),row)
        self.assertEqual((self.card/m.D).read_bytes(),b'system\tcrt_v1\r\nsnes\t1:3:2\r\n')
    def test_existing_defaults_refused_without_overwrite(self):
        (self.card/m.D).write_bytes(b'user-defaults');original=(self.card/m.T).read_bytes()
        with self.assertRaises(RuntimeError):self.install()
        self.assertEqual((self.card/m.D).read_bytes(),b'user-defaults');self.assertEqual((self.card/m.T).read_bytes(),original)
    def test_changed_titles_refused_before_default_creation(self):
        (self.card/m.T).write_bytes(b'changed')
        with self.assertRaises(RuntimeError):self.install()
        self.assertFalse((self.card/m.D).exists())
    def test_corrupt_backup_refused_before_writes(self):
        (self.session/'sd'/m.T).write_bytes(b'corrupt')
        with self.assertRaisesRegex(RuntimeError,'backup corrupted'):self.install()
        self.assertFalse((self.card/m.D).exists())
    def test_verified_firmware_required(self):
        self.state.pop('flash_installed');self.save()
        with self.assertRaisesRegex(RuntimeError,'Verified S4c firmware'):self.install()
        self.assertFalse((self.card/m.D).exists())
    def test_s4b_invariance_required(self):
        self.state['s4b_sd_audit_passed']=False;self.save()
        with self.assertRaisesRegex(RuntimeError,'S4b SD audit'):self.install()
        self.assertFalse((self.card/m.D).exists())
    def test_duplicate_install_refused(self):
        self.install()
        with self.assertRaisesRegex(RuntimeError,'already started'):self.install()
    def test_reset_audit_restores_original_metadata_and_keeps_actual_records(self):
        self.reset_saved();m.audit_restore(self.args)
        self.assertEqual((self.card/m.T).read_bytes(),(self.session/'sd'/m.T).read_bytes());self.assertFalse((self.card/m.D).exists())
        self.assertEqual((self.card/m.A).read_bytes(),record(0,3,27));self.assertEqual((self.card/m.B).read_bytes(),record(1,4,0))
        state=self.reload();self.assertIn('metadata_restored',state)
        self.args.snapshot=str(self.root/'cold');m.audit_clean(self.args)
        self.assertEqual(d.file_entry(self.card/m.B),state['metadata_restored']['files'][m.B])
    def test_changed_fixture_refused_and_observed_snapshot_preserved(self):
        self.reset_saved();(self.card/m.D).write_bytes(b'user-change')
        with self.assertRaisesRegex(RuntimeError,'fixture changed'):m.audit_restore(self.args)
        self.assertEqual((Path(self.args.snapshot)/'sd'/m.D).read_bytes(),b'user-change');self.assertEqual((self.card/m.D).read_bytes(),b'user-change')
        self.assertEqual((self.card/m.T).read_bytes(),d.image('titles_fixture').read_bytes())
    def test_unknown_record_or_duplicate_generation_refused(self):
        self.reset_saved();(self.card/m.B).write_bytes(record(1,5,0))
        with self.assertRaisesRegex(RuntimeError,'generation differs'):m.audit_restore(self.args)
        self.assertTrue((self.card/m.D).exists());self.assertNotIn('metadata_restore_started',self.reload())
    def test_reset_crc_error_refused(self):
        self.reset_saved();data=bytearray(record(1,4,0));data[-1]^=1;(self.card/m.B).write_bytes(data)
        with self.assertRaisesRegex(RuntimeError,'CRC differs'):m.audit_restore(self.args)
        self.assertTrue((self.card/m.D).exists())
    def test_other_user_file_change_refused_before_restoration(self):
        self.reset_saved();(self.card/'nes/titles.csv').write_bytes(b'user-change')
        with self.assertRaisesRegex(RuntimeError,'Unrelated'):m.audit_restore(self.args)
        self.assertTrue((self.card/m.D).exists());self.assertEqual((self.card/'nes/titles.csv').read_bytes(),b'user-change')
    def test_prior_user_slot_change_refused(self):
        self.reset_saved();(self.card/m.A).write_bytes(record(0,3,29))
        with self.assertRaisesRegex(RuntimeError,'Unrelated'):m.audit_restore(self.args)
        self.assertTrue((self.card/m.D).exists())
    def test_user_kind_refused_instead_of_reset(self):
        self.reset_saved();(self.card/m.B).write_bytes(record(0,4,0))
        with self.assertRaisesRegex(RuntimeError,'kind differs'):m.audit_restore(self.args)
        self.assertTrue((self.card/m.D).exists())
    def test_clean_audit_preserves_drift_for_inspection(self):
        self.reset_saved();m.audit_restore(self.args);(self.card/'nes/titles.csv').write_bytes(b'drift')
        self.args.snapshot=str(self.root/'cold')
        with self.assertRaisesRegex(RuntimeError,'SD changed'):m.audit_clean(self.args)
        self.assertEqual((Path(self.args.snapshot)/'sd/nes/titles.csv').read_bytes(),b'drift')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MetadataGuards))
    (HERE/'metadata-test-results.json').write_text(json.dumps(dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),passed=result.wasSuccessful(),device_access=False,storage_media_written=False),indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
