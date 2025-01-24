from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_HOST, CONF_SCAN_INTERVAL
from .coordinator import SolarEdgeEVChargerAUDataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryNotReady

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """For YAML-based setups (unused)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Create and set up a config entry (integration instance)."""
    host = entry.data[CONF_HOST]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, 30)

    coordinator = SolarEdgeEVChargerAUDataUpdateCoordinator(
        hass=hass,
        host=host,
        scan_interval=scan_interval
    )

    # Try initial refresh
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
