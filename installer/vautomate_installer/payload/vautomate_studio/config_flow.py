"""One independent commercial service per home. Read-only by default."""
from homeassistant import config_entries
from homeassistant.core import callback
try:
    import probatio as vol
except ImportError:
    import voluptuous as vol
from . import DOMAIN


class StudioConfigFlow(config_entries.ConfigFlow,domain=DOMAIN):
    VERSION=1
    async def async_step_user(self,user_input=None):
        self._async_abort_entries_match()
        if user_input is not None:return self.async_create_entry(title="VAutomate Studio",data={})
        return self.async_show_form(step_id="user",data_schema=vol.Schema({}))
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):return StudioOptionsFlow()


class StudioOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self,user_input=None):
        if user_input is not None:return self.async_create_entry(title="",data=user_input)
        return self.async_show_form(step_id="init",data_schema=vol.Schema({vol.Optional("allow_evaluation_controls",default=self.config_entry.options.get("allow_evaluation_controls",False)):bool}))
