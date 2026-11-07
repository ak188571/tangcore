"""Temporary-fixture guards on PC substitute cards only."""
from pathlib import Path
import importlib.util,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=module('load_info_base',HERE/'test_deploy.py');m=module('load_info_metadata',HERE/'metadata.py')
d=base.d;k=d.k;m.d=d;m.k=k
from osd2_load_info_fixtures import record

class FixtureGuards(unittest.TestCase):
    tearDown=base.DeploymentGuards.tearDown
    save=base.DeploymentGuards.save
    reload=base.DeploymentGuards.reload
    def setUp(self):
        base.DeploymentGuards.setUp(self)
        for name,data in [(m.A,record(1,7,0)),(m.B,record(0,6,1)),('snes/titles.csv','name\ttitle\r\ngame.sfc\t日本語\r\n'.encode())]:
            for root in (self.card,self.session/'sd'):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            self.state['sd']['files'][name]=d.file_entry(self.card/name)
        self.state.update(flash_installed={'verified':True},sd_installed={'files':dict(self.state['sd']['files'])})
        self.save();self.n=0
    def transition(self,operation):
        self.args.operation=operation;self.args.snapshot=str(self.root/('snapshot-'+str(self.n)));self.n+=1
        m.run(self.args);self.state=self.reload()
    def contents(self):return {n:d.file_entry(p) for n,p in k.user_files(self.card).items()}
    def test_full_cycle_restores_actual_records_and_all_unrelated_bytes_attributes(self):
        before=self.contents()
        for phase in ('system','global','errors','original','audit'):self.transition(phase)
        self.assertEqual(self.contents(),before)
        self.assertEqual((self.card/m.A).read_bytes(),record(1,7,0))
        self.assertEqual((self.card/m.B).read_bytes(),record(0,6,1))
        self.assertFalse((self.card/m.D).exists())
    def test_wrong_order_refused_before_writes(self):
        before=self.contents()
        with self.assertRaisesRegex(RuntimeError,'phase order'):self.transition('global')
        self.assertEqual(self.contents(),before)
    def test_verified_firmware_required(self):
        self.state.pop('flash_installed');self.save();before=self.contents()
        with self.assertRaisesRegex(RuntimeError,'Verified firmware'):self.transition('system')
        self.assertEqual(self.contents(),before)
    def test_fresh_baseline_audit_required(self):
        self.state['compact_sd_audit_passed']=False;self.save();before=self.contents()
        with self.assertRaisesRegex(RuntimeError,'fresh baseline'):self.transition('system')
        self.assertEqual(self.contents(),before)
    def test_existing_defaults_preserved(self):
        (self.card/m.D).write_bytes(b'actual user defaults');before=self.contents()
        with self.assertRaisesRegex(RuntimeError,'SD content'):self.transition('system')
        self.assertEqual(self.contents(),before)
    def test_corrupt_actual_backup_refused(self):
        (self.session/'sd'/m.A).write_bytes(b'broken');before=self.contents()
        with self.assertRaisesRegex(RuntimeError,'backup corrupted'):self.transition('system')
        self.assertEqual(self.contents(),before)
    def test_unknown_user_save_preserved_instead_of_restored(self):
        self.transition('system');(self.card/m.B).write_bytes(record(0,8,31));before=self.contents()
        for op in ('global','recover-original'):
            with self.assertRaises(RuntimeError):self.transition(op)
            self.assertEqual(self.contents(),before)
        self.assertTrue((self.root/'snapshot-1/sd'/m.B).exists())
    def test_changed_unrelated_titles_refused(self):
        self.transition('system');(self.card/'snes/titles.csv').write_bytes(b'user title change');before=self.contents()
        with self.assertRaisesRegex(RuntimeError,'SD content'):self.transition('global')
        self.assertEqual(self.contents(),before)
    def test_attribute_drift_refused(self):
        self.transition('system');p=self.card/m.B;d.set_attrs(p,d.attrs(p)|2);before=self.contents()
        with self.assertRaises(RuntimeError):self.transition('global')
        self.assertEqual(self.contents(),before)
    def test_partial_known_transition_recoverable_and_unknown_never_overwritten(self):
        before=self.contents();real=m.write_bytes;calls=0
        def interrupted(*args):
            nonlocal calls
            real(*args);calls+=1
            if calls==1:raise RuntimeError('Simulated interruption')
        with patch.object(m,'write_bytes',side_effect=interrupted):
            with self.assertRaisesRegex(RuntimeError,'Simulated interruption'):self.transition('system')
        with self.assertRaisesRegex(RuntimeError,'Incomplete transition'):self.transition('global')
        self.transition('recover-original');self.assertEqual(self.contents(),before)
    def test_duplicate_system_refused(self):
        self.transition('system');before=self.contents()
        with self.assertRaisesRegex(RuntimeError,'phase order'):self.transition('system')
        self.assertEqual(self.contents(),before)
    def test_audit_cannot_skip_fixture_restoration(self):
        self.transition('system');before=self.contents()
        with self.assertRaisesRegex(RuntimeError,'Restore original'):self.transition('audit')
        self.assertEqual(self.contents(),before)

if __name__=='__main__':unittest.main(verbosity=2)
