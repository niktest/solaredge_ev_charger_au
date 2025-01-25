from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get

from .const import DOMAIN

# Fields to redact to ensure sensitive information is not exposed
TO_REDACT = {"host"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """
    Return diagnostics for a config entry.

    This includes configuration data, fetched data from the coordinator,
    and associated device information.
    """
    # Validate coordinator presence
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not coordinator:
        return {
            "error": "Coordinator data not found. Ensure the integration is correctly set up."
        }

    # Fetch configuration data and redact sensitive fields
    config_data = async_redact_data(entry.data, TO_REDACT)

    # Fetch and format data from the coordinator
    coordinator_data = coordinator.data or {}
    coordinator_data_formatted = {
        "charger_sn": coordinator_data.get("charger_sn", "unknown"),
        "inverter_sn": coordinator_data.get("inverter_sn", "unknown"),
        "car_status": coordinator_data.get("car_status", "unknown"),
        "charger_status": coordinator_data.get("charger_status", "unknown"),
        "charge_power": coordinator_data.get("charge_power", "n/a"),
        "session_energy": coordinator_data.get("session_energy", "n/a"),
        "error_message": coordinator_data.get("error", "No errors reported"),
    }

    # Fetch associated devices
    device_registry = async_get(hass)
    associated_devices = [
        dict(
            id=device.id,
            name=device.name,
            model=device.model,
            manufacturer=device.manufacturer,
            serial_number=device.serial_number
        )
        for device in device_registry.devices.values()
        if entry.entry_id in device.config_entries
    ]

    # Return structured diagnostic data
    return {
        "config_entry": config_data,
        "coordinator_data": coordinator_data_formatted,
        "devices": associated_devices,
    }