import binascii
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get
import logging

from .const import DOMAIN
from .coordinator import parse_status

_LOGGER = logging.getLogger(__name__)

# Fields to redact to ensure sensitive information is not exposed
TO_REDACT = {"host"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """
    Return diagnostics for a config entry.

    This includes configuration data, fetched data from the coordinator,
    associated device information, and raw binary buffer data.
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

    # Add raw binary buffer data if available
    raw_buffer_data = {}
    try:
        if hasattr(coordinator, "_last_raw_data"):
            raw_data = coordinator._last_raw_data
            raw_buffer_data = {
                "buffer_hex": binascii.hexlify(raw_data).decode("ascii"),
                "buffer_length": len(raw_data),
                "parse_attempt": parse_status(raw_data)
            }
        else:
            raw_buffer_data = {
                "info": "Raw buffer data not available. The coordinator doesn't store the last raw data."
            }
    except Exception as e:
        _LOGGER.error(f"Error processing raw buffer data for diagnostics: {e}")
        raw_buffer_data = {
            "error": f"Failed to process raw buffer data: {str(e)}"
        }

    # Return structured diagnostic data
    return {
        "config_entry": config_data,
        "coordinator_data": coordinator_data_formatted,
        "devices": associated_devices,
        "raw_buffer_data": raw_buffer_data,
    }