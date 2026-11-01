"""Run inside an official isolated HA container; does not contact a home server."""
import importlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from homeassistant.const import __version__
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntityFeature
bridge=importlib.import_module('custom_components.vautomate_studio')
flow=importlib.import_module('custom_components.vautomate_studio.config_flow')
assert int(CoverEntityFeature.SET_POSITION)==4
assert int(FanEntityFeature.SET_SPEED)==1
assert int(MediaPlayerEntityFeature.SELECT_SOURCE)==2048
assert int(AlarmControlPanelEntityFeature.ARM_AWAY)==2
assert bridge.StaticPathConfig and flow.StudioConfigFlow
assert bridge.studio_request
from homeassistant.components.backup.manager import BackupManager,NewBackup
from homeassistant.components.backup.models import AgentBackup,Folder
import inspect
assert 'backup_job_id' in NewBackup.__dataclass_fields__
assert {'include_all_addons','include_database','include_folders','include_homeassistant','password','agent_ids'} <= set(inspect.signature(BackupManager.async_initiate_backup).parameters)
assert {'restore_addons','restore_database','restore_folders','restore_homeassistant'} <= set(inspect.signature(BackupManager.async_restore_backup).parameters)
assert {'backup_id','size','protected','addons','folders','homeassistant_included'} <= set(AgentBackup.__dataclass_fields__)
from homeassistant.auth import AuthManager
from homeassistant.auth.const import GROUP_ID_READ_ONLY
from homeassistant.auth.providers.homeassistant import HassAuthProvider,async_get_provider
assert GROUP_ID_READ_ONLY=='system-read-only'
assert {'group_ids','local_only'} <= set(inspect.signature(AuthManager.async_create_user).parameters)
assert {'is_active','group_ids','local_only'} <= set(inspect.signature(AuthManager.async_update_user).parameters)
assert callable(AuthManager.async_remove_refresh_token) and callable(HassAuthProvider.async_change_password) and callable(async_get_provider)
from homeassistant.components import mqtt
from homeassistant.helpers import device_registry,entity_registry
assert callable(mqtt.is_connected) and callable(mqtt.async_subscribe) and callable(mqtt.async_publish)
assert 'retain' in inspect.signature(mqtt.async_publish).parameters
assert callable(device_registry.async_get) and callable(entity_registry.async_get)
assert bridge.HAPairing and bridge.Pairing and bridge.HAIntegrations and bridge.IntegrationSetup
print('API import and feature contract passed on Core',__version__)
print('This is a source/API smoke test. Full HAOS, update, restore and device tests remain separate gates.')
