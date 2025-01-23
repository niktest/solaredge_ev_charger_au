import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_SYSTEM,
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_SYSTEM,
    UNIT_SYSTEM_W,
    UNIT_SYSTEM_KW,
)


class SolarEdgeEVChargerAUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolarEdge EV Charger (Australia)."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SolarEdgeEVChargerAUOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial (user) step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="SolarEdge EV Charger (AU)",
                data={
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                },
            )

        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            # The user sets the interval in seconds
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)


class SolarEdgeEVChargerAUOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the EV Charger: poll interval, units, etc."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Current settings, fall back if none exist
        current_host = self.config_entry.data.get(CONF_HOST, DEFAULT_HOST)
        current_interval = self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        current_unit_system = self.config_entry.options.get(CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM)

        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default=current_host): str,
            vol.Required(CONF_SCAN_INTERVAL, default=current_interval): int,
            vol.Required(
                CONF_UNIT_SYSTEM,
                default=current_unit_system
            ): vol.In({
                UNIT_SYSTEM_W:  "Watts / Watt-hours (W, Wh)",
                UNIT_SYSTEM_KW: "Kilowatts / Kilowatt-hours (kW, kWh)"
            })
        })

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
