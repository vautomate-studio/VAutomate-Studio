"""Adapter shape tests with inert HA models; live HAOS tests are separate evidence."""
from enum import StrEnum
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_engine import ProductError

class Folder(StrEnum):
    SHARE='share'

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/ha_backups.py'
spec=importlib.util.spec_from_file_location('studio_product.ha_backups',path)
module=importlib.util.module_from_spec(spec)
with patch.dict(sys.modules,{'aiohttp':SimpleNamespace(web=SimpleNamespace(FileResponse=lambda **v:v)),
    'homeassistant.components.backup.const':SimpleNamespace(DATA_MANAGER='backup'),
    'homeassistant.components.backup.models':SimpleNamespace(Folder=Folder)}):
    spec.loader.exec_module(module)

class Agent:
    domain='hassio';unique_id='local'
    def __init__(self):self.reads=0
    async def async_list_backups(self):self.reads+=1;return [item()]
    async def async_get_backup(self,identity):self.reads+=1;return item()
    async def async_download_backup(self,identity):
        async def stream():yield b'encrypted'
        return stream()

def item():return SimpleNamespace(backup_id='ab1234',name='Saved home',date='2026-10-29T10:00:00Z',size=9,protected=True,homeassistant_included=True,database_included=True,homeassistant_version='2026.10.4',addons=[SimpleNamespace(slug='radio',name='Home radio',version='1')],folders=[Folder.SHARE])

class Manager:
    state='idle';last_action_event=None;local_backup_agents={}
    def __init__(self):
        self.backup_agents={'hassio.local':Agent(),'cloud.remote':Agent()};self.backup_agents['cloud.remote'].domain='cloud';self.known_backups={};self.create_options=None;self.restore_options=None
    async def async_initiate_backup(self,**options):self.create_options=options;return SimpleNamespace(backup_job_id='job1234')
    async def async_restore_backup(self,identity,**options):self.restore_options=options

class HABackupTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager=Manager();self.adapter=module.HABackups(SimpleNamespace(data={'backup':self.manager},config=SimpleNamespace(components={'hassio'})))
    async def test_supervisor_local_agent_is_usable_without_filesystem_access(self):
        self.assertEqual(self.adapter.local(),'hassio.local');status=await self.adapter.status();self.assertTrue(status['can_create']);self.assertEqual(len(status['backups']),1);self.assertEqual(self.manager.backup_agents['cloud.remote'].reads,0)
    async def test_creation_covers_actual_haos_apps_database_folders_and_returns_job_identity(self):
        self.assertEqual(await self.adapter.create('Home copy','PRIVATE'),'job1234');options=self.manager.create_options;self.assertTrue(options['include_all_addons']);self.assertTrue(options['include_database']);self.assertEqual(options['agent_ids'],['hassio.local']);self.assertEqual(options['include_folders'],[Folder.SHARE])
    async def test_restore_passes_explicit_saved_app_and_folder_selection(self):
        backup=await self.adapter.details('ab1234');await self.adapter.restore(backup,'PRIVATE');options=self.manager.restore_options;self.assertEqual(options['restore_addons'],['radio']);self.assertEqual(options['restore_folders'],[Folder.SHARE]);self.assertTrue(options['restore_database'])
    async def test_haos_export_streams_ciphertext_without_loading_archive_in_memory(self):
        export=await self.adapter.export('ab1234');self.assertEqual(export['headers']['Cache-Control'],'no-store');self.assertEqual(export['headers']['Content-Length'],'9');self.assertEqual([data async for data in export['stream']],[b'encrypted']);self.assertEqual(self.manager.backup_agents['cloud.remote'].reads,0)
    async def test_missing_local_agent_has_no_create_capability(self):
        del self.manager.backup_agents['hassio.local'];self.assertIsNone(self.adapter.local());self.assertFalse((await self.adapter.status())['can_create'])
    async def test_agent_error_is_redacted_in_status(self):
        async def fail():raise RuntimeError('PRIVATE networkkey and password')
        self.manager.backup_agents['hassio.local'].async_list_backups=fail;status=await self.adapter.status();self.assertTrue(status['storage_attention']);self.assertFalse(status['can_create']);self.assertNotIn('PRIVATE',str(status))
