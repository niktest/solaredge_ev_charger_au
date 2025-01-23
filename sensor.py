from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, 
    CONF_UNIT_SYSTEM,
    UNIT_SYSTEM_W,
    UNIT_SYSTEM_KW,
    DEFAULT_UNIT_SYSTEM,
)
from .coordinator import SolarEdgeEVChargerAUDataUpdateCoordinator


SENSOR_TYPES = [
    # data_key,         base_name,         device_class,           state_class
    ("car_status",       "car_status",      None,                   None),
    ("charger_status",   "charger_status",  None,                   None),
    ("charge_power",     "charge_power",    SensorDeviceClass.POWER,SensorStateClass.MEASUREMENT),
    ("session_energy",   "session_energy",  SensorDeviceClass.ENERGY,SensorStateClass.MEASUREMENT),
    ("error",            "error",           None,                   None),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Set up the SolarEdge EV Charger (AU) sensors."""
    coordinator: SolarEdgeEVChargerAUDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Retrieve user's desired unit system from entry.options
    unit_system = entry.options.get(CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM)

    entities = []
    for (data_key, base_name, device_class, state_class) in SENSOR_TYPES:
        entities.append(
            SolarEdgeEVChargerAUSensor(
                coordinator=coordinator,
                config_entry=entry,
                data_key=data_key,
                base_name=base_name,
                device_class=device_class,
                state_class=state_class,
                user_unit_system=unit_system,
            )
        )

    async_add_entities(entities, update_before_add=True)


class SolarEdgeEVChargerAUSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing data from the EV Charger."""

    def __init__(
        self,
        coordinator: SolarEdgeEVChargerAUDataUpdateCoordinator,
        config_entry: ConfigEntry,
        data_key: str,
        base_name: str,
        device_class: str | None,
        state_class: str | None,
        user_unit_system: str,
    ):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._data_key = data_key
        self._user_unit_system = user_unit_system
        self._attr_device_class = device_class
        self._attr_state_class = state_class

        # ----- Rename Entities Here -----
        # Prefix the sensor's display name with "solaredge_ev_charger_"
        self._attr_name = f"solaredge_ev_charger_{base_name}"

        # Use both the entry_id and data_key to ensure unique IDs
        self._attr_unique_id = f"{config_entry.entry_id}-{data_key}"

        # Decide displayed units based on user's preference
        if data_key == "charge_power":
            # raw is W
            self._attr_native_unit_of_measurement = (
                "W" if user_unit_system == UNIT_SYSTEM_W else "kW"
            )
        elif data_key == "session_energy":
            # raw is Wh
            self._attr_native_unit_of_measurement = (
                "Wh" if user_unit_system == UNIT_SYSTEM_W else "kWh"
            )
        else:
            self._attr_native_unit_of_measurement = None

    @property
    def native_value(self):
        """Return the sensor value, with optional conversion."""
        data = self.coordinator.data
        if not data:
            return None

        raw_value = data.get(self._data_key)
        if raw_value is None:
            return None

        # If user wants raw W/Wh, just return that.
        if self._user_unit_system == UNIT_SYSTEM_W:
            if isinstance(raw_value, float):
                return round(raw_value, 2)
            return raw_value

        # If user chose kW/kWh, convert from W->kW or Wh->kWh
        if self._data_key == "charge_power":
            return round(raw_value / 1000.0, 3)
        elif self._data_key == "session_energy":
            return round(raw_value / 1000.0, 3)

        # For statuses or error, no conversion needed
        return raw_value

    @property
    def extra_state_attributes(self):
        """Expose additional attributes, e.g. serial numbers."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "inverter_serial_number": data.get("inverter_sn"),
            "ev_charger_serial_number": data.get("charger_sn"),
        }

    @property
    def should_poll(self) -> bool:
        """Disable polling; updates come from coordinator."""
        return False
