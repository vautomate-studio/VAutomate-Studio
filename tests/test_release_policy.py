"""Production safeguards using synthetic attestations in temporary directories only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

path=Path(__file__).resolve().parents[1]/'tools/release_policy.py';spec=importlib.util.spec_from_file_location('release_policy',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ReleasePolicyTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);source=self.root/'custom_components/vautomate_studio';source.mkdir(parents=True);(source/'fixture.py').write_text('INERT = True\n');native=self.root/'android/app/src';native.mkdir(parents=True);(native/'Fixture.java').write_text('class Fixture {}\n')
    def tearDown(self):self.temp.cleanup()
    def record(self,**changes):
        value={'schema':1,'gate':'approved_hardware_matrix','release_version':'fixture-version','runtime_sha256':module.runtime_digest(self.root),'status':'passed','reviewed_by':'Synthetic test reviewer','tested_at':'2020-01-01T00:00:00Z','checks':[{'name':'Inert test only','status':'passed'}],'scope':'physical_devices',**changes};content=json.dumps(value).encode();(self.root/'record.json').write_bytes(content);return {'evidence':'record.json','evidence_sha256':hashlib.sha256(content).hexdigest()}
    def test_correctly_bound_fixture_record_is_parseable(self):self.assertEqual(module.attestation(self.root,self.record(),'approved_hardware_matrix','fixture-version')['status'],'passed')
    def test_old_version_wrong_gate_and_synthetic_scope_are_rejected(self):
        for changes in [{'release_version':'old'},{'gate':'wrong'},{'scope':'synthetic'},{'scope':'operational_review'},{'status':'pending'},{'reviewed_by':''},{'tested_at':'2100-01-01T00:00:00Z'},{'tested_at':'2020-01-01'},{'checks':[]},{'checks':[{'name':'incomplete','status':'failed'}]}]:
            with self.assertRaises(ValueError):module.attestation(self.root,self.record(**changes),'approved_hardware_matrix','fixture-version')
    def test_missing_or_mismatched_hash_cannot_pass(self):
        record=self.record();record.pop('evidence_sha256')
        with self.assertRaises(ValueError):module.attestation(self.root,record,'approved_hardware_matrix','fixture-version')
        record=self.record();(self.root/'record.json').write_text('{}')
        with self.assertRaises(ValueError):module.attestation(self.root,record,'approved_hardware_matrix','fixture-version')
    def test_escaping_paths_and_non_json_evidence_rejected(self):
        for relative in ['../outside.json',str(self.root/'absolute.json'),'',None]:
            with self.assertRaises(ValueError):module.read(self.root,relative)
        (self.root/'record.json').write_text('not json')
        with self.assertRaises(ValueError):module.read(self.root,'record.json')
    def test_removing_gates_does_not_enable_production(self):
        missing=module.audit(self.root,{'version':'fixture-version','required_acceptance':{},'certified_core_versions':['*']});self.assertEqual(sum('gate removed' in m for m in missing),len(module.REQUIRED_GATES));self.assertTrue(any('hardware' in m.lower() for m in missing))
    def test_same_release_name_with_changed_runtime_requires_new_acceptance(self):
        record=self.record();(self.root/'custom_components/vautomate_studio/fixture.py').write_text('INERT = "changed"\n')
        with self.assertRaises(ValueError):module.attestation(self.root,record,'approved_hardware_matrix','fixture-version')
