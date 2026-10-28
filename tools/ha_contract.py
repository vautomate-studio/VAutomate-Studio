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
print('API import and feature contract passed on Core',__version__)
print('This is a source/API smoke test. Full HAOS, update, restore and device tests remain separate gates.')
