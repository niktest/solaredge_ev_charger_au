import aiohttp
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
from .coordinator import parse_status, parse_and_format


class SolarEdgeEVChargerAUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolarEdge EV Charger (Australia)."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SolarEdgeEVChargerAUOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step where user inputs IP and poll interval."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            scan_interval = user_input[CONF_SCAN_INTERVAL]

            # Attempt a connection test to fetch the top-level inverter SN
            try:
                inverter_sn = await self._async_test_connection(host)
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                if inverter_sn:
                    # Set unique_id to the inverter's S/N so we avoid duplicates
                    await self.async_set_unique_id(inverter_sn)
                    self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"SolarEdge EV Charger (AU) - {host}",
                    data={
                        CONF_HOST: host,
                        CONF_SCAN_INTERVAL: scan_interval
                    }
                )

        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def _async_test_connection(self, host: str):
        """Attempt to fetch and parse device status, returning the inverter SN."""
        url = f"http://{host}/web/v1/status"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                resp.raise_for_status()
                raw_data = await resp.read()

        # Try parsing it
        parsed = parse_status(raw_data)
        display = parse_and_format(parsed)
        # return top-level inverter SN as unique ID
        return display.get("inverter_sn")


class SolarEdgeEVChargerAUOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for changing scan interval, units, etc."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Current settings, fallback if none exist
        current_interval = self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        current_unit_system = self.config_entry.options.get(CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM)
        current_host = self.config_entry.data.get(CONF_HOST, DEFAULT_HOST)

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
