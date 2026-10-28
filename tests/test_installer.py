from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

project=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('studio_installer',project/'installer/vautomate_installer/installer.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class API:
    def __init__(self):
        self.calls=[];self.installed=False;self.fail_check=0;self.checks=0;self.version='2026.10.4'
    def request(self,method,route,body=None):
        self.calls.append((method,route,deepcopy(body)))
        if route=='/core/api/vautomate_studio/v1/health':return {'bridge_version':getattr(self,'running_version','test'),'api_version':1,'initialized':True}
        if route=='/core/info':return {'version':self.version}
        if route=='/core/check':
            self.checks+=1
            if self.checks==self.fail_check:raise module.InstallError('Configuration check failed')
            return {}
        if route=='/core/restart':
            if hasattr(self,'component_parent'):
                assert all(not item.name.startswith('.') for item in self.component_parent.iterdir()), 'Temporary manifests must not enter HA component discovery'
            return {}
        if route.endswith('/entry'):return [{'domain':'vautomate_studio','state':'loaded'}] if self.installed else []
        if route.endswith('/flow'):return {'type':'form','step_id':'user','flow_id':'a'*32}
        if route.endswith('/flow/'+'a'*32):self.installed=True;return {'type':'create_entry'}
        raise AssertionError(route)


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.config=self.root/'home';self.config.mkdir()
        (self.config/'configuration.yaml').write_text('ORIGINAL HOME CONFIG')
        (self.config/'.storage').mkdir();(self.config/'.storage/auth').write_text('NEVER_TOUCH')
        self.bundle=self.root/'bundle';self.payload=self.bundle/'payload/vautomate_studio';self.payload.mkdir(parents=True)
        (self.payload/'__init__.py').write_text('NEW_COMPONENT')
        self.manifest={'version':'test','production_ready':False,'files':{'vautomate_studio/__init__.py':hashlib.sha256(b'NEW_COMPONENT').hexdigest()}}
        self.write_manifest();self.api=API()
        self.api.component_parent=self.config/'custom_components'
        self.installer=module.Installer(self.bundle,self.config,self.root/'private',self.api,sleep=lambda _:None)
    def write_manifest(self):
        (self.bundle/'payload.json').write_text(json.dumps(self.manifest))
    def run_install(self):return self.installer.install(allow_candidate=True,backup_confirmed=True)
    def test_rejects_unapproved_candidate_before_any_server_write(self):
        with self.assertRaises(module.InstallError):self.installer.install(backup_confirmed=True)
        self.assertEqual(self.api.calls,[])
    def test_requires_backup_confirmation(self):
        with self.assertRaises(module.InstallError):self.installer.install(allow_candidate=True)
        self.assertEqual(self.api.calls,[])
    def test_checksum_failure_leaves_home_untouched(self):
        (self.payload/'__init__.py').write_text('TAMPERED')
        with self.assertRaises(module.InstallError):self.run_install()
        self.assertFalse((self.config/'custom_components').exists());self.assertEqual(self.api.calls,[])
    def test_extra_payload_file_rejected(self):
        (self.payload/'extra.py').write_text('UNEXPECTED')
        with self.assertRaises(module.InstallError):self.run_install()
    def test_unknown_core_rejected(self):
        self.api.version='2027.1.0'
        with self.assertRaises(module.InstallError):self.run_install()
        self.assertFalse(any(method=='POST' for method,_,_ in self.api.calls))
    def test_install_preserves_configuration_and_authentication(self):
        result=self.run_install()
        self.assertEqual(result['phase'],'ready_for_onboarding')
        self.assertFalse(result['controls_enabled_automatically'])
        self.assertEqual((self.config/'configuration.yaml').read_text(),'ORIGINAL HOME CONFIG')
        self.assertEqual((self.config/'.storage/auth').read_text(),'NEVER_TOUCH')
        self.assertEqual((self.config/'custom_components/vautomate_studio/__init__.py').read_text(),'NEW_COMPONENT')
    def test_repeat_install_does_not_restart_or_duplicate_entry(self):
        self.run_install();self.api.calls=[]
        self.run_install()
        self.assertFalse(any(route=='/core/restart' or '/flow' in route for _,route,_ in self.api.calls))
    def test_failed_configuration_check_restores_prior_component(self):
        old=self.config/'custom_components/vautomate_studio';old.mkdir(parents=True);(old/'__init__.py').write_text('OLD_COMPONENT')
        self.api.fail_check=2
        with self.assertRaises(module.InstallError):self.run_install()
        self.assertEqual((old/'__init__.py').read_text(),'OLD_COMPONENT')
        self.assertFalse(any(route=='/core/restart' for _,route,_ in self.api.calls))
        self.assertEqual(json.loads((self.root/'private/install-status.json').read_text())['phase'],'needs_installer_attention')
    def test_existing_component_snapshot_survives_success(self):
        old=self.config/'custom_components/vautomate_studio';old.mkdir(parents=True);(old/'__init__.py').write_text('OLD_COMPONENT')
        result=self.run_install()
        backup=self.root/'private/component-backups'/result['component_backup']/'__init__.py'
        self.assertEqual(backup.read_text(),'OLD_COMPONENT')
    def test_concurrent_or_interrupted_install_requires_review(self):
        data=self.root/'private';data.mkdir();(data/'install.lock').write_text('')
        with self.assertRaises(module.InstallError):self.run_install()
        self.assertTrue((data/'install.lock').exists())
        self.assertFalse(any(method=='POST' for method,_,_ in self.api.calls))
    def test_old_runtime_cannot_be_mistaken_for_success(self):
        self.api.running_version='old-release'
        with self.assertRaises(module.InstallError):self.run_install()
        self.assertEqual(json.loads((self.root/'private/install-status.json').read_text())['phase'],'needs_installer_attention')


if __name__=='__main__':unittest.main()
