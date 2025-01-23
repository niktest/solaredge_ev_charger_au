from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarEdgeEVChargerAUDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SolarEdge EV Charger sensors from a config entry."""
    coordinator: SolarEdgeEVChargerAUDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "car_status",
            "SolarEdge EV Charger - Car Status",
            "Indicates the connection and charging state of the car.",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "charger_status",
            "SolarEdge EV Charger - Charger Status",
            "Represents the operational state of the EV charger.",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "charge_power",
            "SolarEdge EV Charger - Charge Power",
            "Real-time power delivered to the car (in W or kW).",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "session_energy",
            "SolarEdge EV Charger - Session Energy",
            "Total energy delivered in the current session (in Wh or kWh).",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "error",
            "SolarEdge EV Charger - Error",
            "Detailed error information (code and subsystem).",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "charger_sn",
            "SolarEdge EV Charger - Serial Number",
            "The unique serial number of the EV charger hardware.",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "inverter_sn",
            "SolarEdge EV Charger - Inverter Serial Number",
            "The unique serial number of the connected solar inverter.",
        ),
    ]

    async_add_entities(sensors)


class SolarEdgeEVChargerSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SolarEdge EV Charger sensor."""

    def __init__(
        self,
        coordinator: SolarEdgeEVChargerAUDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        description: str,
    ) -> None:
        """Initialize the SolarEdge EV Charger sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._description = description

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self):
        """Return the sensor state attributes."""
        return {"description": self._description}
