from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import _FlowResultT

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


def generate_config_schema(step_id: str, user_input: dict[str, Any]) -> vol.Schema:
    """Generate config flow or repair schema."""
    schema: dict[vol.Marker, Any] = {}

    if step_id in ["reconfigure", "confirm", "user"]:
        schema |= {
            vol.Required(
                CONF_HOST,
                default=user_input.get(CONF_HOST, DEFAULT_HOST)
            ): str}

        schema |= {
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ): vol.All(int, vol.Range(min=1, max=3600))
        }

    if step_id == "reconfigure":
        schema |= {
            vol.Required(
                CONF_UNIT_SYSTEM,
                default=user_input.get(CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM)
            ): vol.In({
                UNIT_SYSTEM_W: "Watts / Watt-hours (W, Wh)",
                UNIT_SYSTEM_KW: "Kilowatts / Kilowatt-hours (kW, kWh)"
            })
        }

    return vol.Schema(schema)


async def _async_test_connection(host: str):
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


class SolarEdgeEVChargerAUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolarEdge EV Charger (Australia)."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SolarEdgeEVChargerAUOptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        """Handle the initial step where user inputs IP and poll interval."""
        errors = {}

        if user_input is not None:
            # Attempt a connection test to fetch the top-level inverter SN
            try:
                host = user_input.get(CONF_HOST, DEFAULT_HOST)
                inverter_sn = await _async_test_connection(host)
            except Exception:
                errors[CONF_HOST] = "Unable to connect. Please check the IP address."
            else:
                if inverter_sn:
                    # Set unique_id to the inverter's S/N so we avoid duplicates
                    await self.async_set_unique_id(inverter_sn)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"SolarEdge EV Charger (AU) - {host}",
                        data=user_input
                    )
        else:
            user_input = {
                CONF_HOST: DEFAULT_HOST,
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            }

        return self.async_show_form(
            step_id="user",
            data_schema=generate_config_schema("user", user_input),
            errors=errors
        )


class SolarEdgeEVChargerAUOptionsFlowHandler(OptionsFlow):
    """Handle options flow for changing scan interval, units, etc."""

    async def async_step_init(
            self, user_input: dict[str, Any] | None = None
    ) -> _FlowResultT:
        errors = {}
        if user_input is not None:
            # Attempt a connection test to fetch the top-level inverter SN
            try:
                await _async_test_connection(user_input.get(CONF_HOST, DEFAULT_HOST))
            except Exception:
                errors[CONF_HOST] = "Unable to connect. Please check the IP address."
            else:
                return self.async_create_entry(title="", data=user_input)
        else:
            user_input = {
                CONF_SCAN_INTERVAL: self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
                CONF_UNIT_SYSTEM: self.config_entry.options.get(
                    CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM
                ),
                CONF_HOST: self.config_entry.options.get(
                    CONF_HOST, DEFAULT_HOST
                )
            }

        return self.async_show_form(
            step_id="init",
            data_schema=generate_config_schema("reconfigure", user_input),
            errors=errors
        )
