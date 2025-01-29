from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_UNIT_SYSTEM, UNIT_SYSTEM_KW
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
            "SolarEdge EV Charger Car Status",
            "Indicates the connection and charging state of the car.",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "charger_status",
            "SolarEdge EV Charger Charger Status",
            "Represents the operational state of the EV charger.",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "charge_power",
            "SolarEdge EV Charger Charge Power",
            "Real-time power delivered to the car.",
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "session_energy",
            "SolarEdge EV Charger Session Energy",
            "Total energy delivered in the current session.",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL,
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "error",
            "SolarEdge EV Charger Error",
            "Detailed error information (code and subsystem).",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "charger_sn",
            "SolarEdge EV Charger Serial Number",
            "The unique serial number of the EV charger hardware.",
        ),
        SolarEdgeEVChargerSensor(
            coordinator,
            entry,
            "inverter_sn",
            "SolarEdge EV Charger Inverter Serial Number",
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
            device_class: SensorDeviceClass | None = None,
            state_class: SensorStateClass | None = None,
    ) -> None:
        """Initialize the SolarEdge EV Charger sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._description = description
        self._unit_system = entry.options.get(CONF_UNIT_SYSTEM, UNIT_SYSTEM_KW)

        # Set attributes for Energy Dashboard compatibility
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._key)

        # Adjust units for session_energy and charge_power
        if self._key == "charge_power" and value is not None:
            return round(value / 1000, 2) if self._unit_system == UNIT_SYSTEM_KW else round(value, 2)
        if self._key == "session_energy" and value is not None:
            return round(value / 1000, 2) if self._unit_system == UNIT_SYSTEM_KW else round(value, 2)

        return value

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement for the sensor."""
        if self._key == "charge_power":
            return "kW" if self._unit_system == UNIT_SYSTEM_KW else "W"
        if self._key == "session_energy":
            return "kWh" if self._unit_system == UNIT_SYSTEM_KW else "Wh"
        return None

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return {"description": self._description}

    @property
    def device_info(self):
        """Return device information for grouping into an area."""
        charger_sn = self.coordinator.data.get("charger_sn", "unknown_charger_sn")
        inverter_sn = self.coordinator.data.get("inverter_sn", "unknown_inverter_sn")

        return dict(
            identifiers={(DOMAIN, f"{charger_sn}_{inverter_sn}")},
            name="SolarEdge EV Charger",
            manufacturer="SolarEdge",
            model="EV Charger AU",
            serial_number = charger_sn,
        )
