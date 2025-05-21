import logging
import struct
import binascii
from datetime import timedelta
from enum import Enum

import aiohttp
from google.protobuf.internal.decoder import _DecodeVarint
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CarStatus(Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    CHARGING_CAR = 2
    RFID_REQ = 3
    UNDEFINED = 4

    def label(self) -> str:
        """Return a short, lowercase state for Home Assistant."""
        if self is CarStatus.DISCONNECTED:
            return "disconnected"
        elif self is CarStatus.CONNECTED:
            return "connected"
        elif self is CarStatus.CHARGING_CAR:
            return "charging"
        elif self is CarStatus.RFID_REQ:
            return "rfid"
        elif self is CarStatus.UNDEFINED:
            return "undefined"
        return f"unknown_{self.value}"

class ChargerStatus(Enum):
    READY = 0
    INITIALIZING = 1
    CHARGING = 2
    CHARGING_BOOST = 3
    CHARGING_EXCESS_PV = 4
    OFF = 5
    ERROR = 6

    def label(self) -> str:
        """Return a short, lowercase state for Home Assistant."""
        if self is ChargerStatus.READY:
            return "ready"
        elif self is ChargerStatus.INITIALIZING:
            return "initializing"
        elif self is ChargerStatus.CHARGING:
            return "active"
        elif self is ChargerStatus.CHARGING_BOOST:
            return "boost"
        elif self is ChargerStatus.CHARGING_EXCESS_PV:
            return "excess_pv"
        elif self is ChargerStatus.OFF:
            return "off"
        elif self is ChargerStatus.ERROR:
            return "error"
        return f"unknown_{self.value}"


def decode_ansi_string(raw_bytes: bytes) -> str:
    """Decode a string from ANSI-latin-1, removing control chars."""
    text = raw_bytes.decode("latin-1", errors="replace")
    return ''.join(ch for ch in text if ch >= ' ' and ch != '\x7f')


def skip_field(buf: bytes, pos: int, wire_type: int) -> int:
    if wire_type == 0:
        _, pos = _DecodeVarint(buf, pos)  # varint
    elif wire_type == 1:
        pos += 8  # 64-bit
    elif wire_type == 2:
        length, pos = _DecodeVarint(buf, pos)
        pos += length
    elif wire_type == 5:
        pos += 4  # 32-bit
    else:
        _LOGGER.error(f"Unknown wire type {wire_type}")
        raise RuntimeError(f"Unknown wire type {wire_type}")
    return pos


def parse_evse(buf: bytes, start: int = 0, end: int = None) -> dict:
    """Parse the EVSE submessage."""
    if end is None:
        end = len(buf)
    pos = start

    evse = {
        "carStatus": None,
        "chargerStatus": None,
        "chargePower": None,
        "sessionEnergy": None,
        "errorCode": None,
        "subsystem": None,
        "sn": None
    }

    _LOGGER.debug(f"Starting EVSE message parsing at position {start}, length {end - start} bytes")

    try:
        while pos < end:
            tag, pos = _DecodeVarint(buf, pos)
            field_number = tag >> 3
            wire_type = tag & 7

            _LOGGER.debug(f"EVSE field: #{field_number}, wire_type: {wire_type}, position: {pos}")

            if field_number == 1 and wire_type == 0:
                val, pos = _DecodeVarint(buf, pos)
                evse["carStatus"] = val
                _LOGGER.debug(f"Parsed carStatus: {val} (enum: {CarStatus(val).name if val in [e.value for e in CarStatus] else 'UNKNOWN'})")
            elif field_number == 2 and wire_type == 0:
                val, pos = _DecodeVarint(buf, pos)
                evse["chargerStatus"] = val
                _LOGGER.debug(f"Parsed chargerStatus: {val} (enum: {ChargerStatus(val).name if val in [e.value for e in ChargerStatus] else 'UNKNOWN'})")
            elif field_number == 3 and wire_type == 5:
                evse["chargePower"] = struct.unpack('<f', buf[pos:pos + 4])[0]
                _LOGGER.debug(f"Parsed chargePower: {evse['chargePower']} W")
                pos += 4
            elif field_number == 4 and wire_type == 5:
                evse["sessionEnergy"] = struct.unpack('<f', buf[pos:pos + 4])[0]
                _LOGGER.debug(f"Parsed sessionEnergy: {evse['sessionEnergy']} Wh")
                pos += 4
            elif field_number == 5 and wire_type == 0:
                val, pos = _DecodeVarint(buf, pos)
                evse["errorCode"] = val
                _LOGGER.debug(f"Parsed errorCode: {val}")
            elif field_number == 6 and wire_type == 0:
                val, pos = _DecodeVarint(buf, pos)
                evse["subsystem"] = val
                _LOGGER.debug(f"Parsed subsystem: {val}")
            elif field_number == 7 and wire_type == 2:
                length, pos = _DecodeVarint(buf, pos)
                evse["sn"] = decode_ansi_string(buf[pos:pos + length])
                _LOGGER.debug(f"Parsed EVSE sn: {evse['sn']}")
                pos += length
            else:
                old_pos = pos
                pos = skip_field(buf, pos, wire_type)
                _LOGGER.debug(f"Skipped unknown field {field_number} (wire_type={wire_type}), advanced {pos - old_pos} bytes")

    except Exception as e:
        _LOGGER.error(f"Error parsing EVSE message: {e}")
        _LOGGER.debug(f"EVSE parse buffer: {binascii.hexlify(buf[start:end])}")
        # Return partial results, if any

    _LOGGER.debug(f"Completed EVSE parsing with results: {evse}")
    return evse


def parse_status(buf: bytes) -> dict:
    """Parse top-level status, including an 'evse' sub-message."""
    status = {"sn": None, "evse": None}
    pos = 0
    end = len(buf)

    _LOGGER.debug(f"Starting protobuf parsing, buffer size: {len(buf)} bytes")
    _LOGGER.debug(f"Buffer hex dump: {binascii.hexlify(buf)}")

    try:
        while pos < end:
            tag, pos = _DecodeVarint(buf, pos)
            field_number = tag >> 3
            wire_type = tag & 7

            _LOGGER.debug(f"Top-level field: #{field_number}, wire_type: {wire_type}, position: {pos}")

            if field_number == 1 and wire_type == 2:
                length, pos = _DecodeVarint(buf, pos)
                status["sn"] = decode_ansi_string(buf[pos:pos + length])
                _LOGGER.debug(f"Parsed inverter sn: {status['sn']}")
                pos += length
            elif field_number == 38 and wire_type == 2:
                length, pos = _DecodeVarint(buf, pos)
                sub_end = pos + length
                _LOGGER.debug(f"Found EVSE submessage at position {pos}, length {length}")
                status["evse"] = parse_evse(buf, pos, sub_end)
                pos = sub_end
            else:
                old_pos = pos
                pos = skip_field(buf, pos, wire_type)
                _LOGGER.debug(f"Skipped unknown field {field_number} (wire_type={wire_type}), advanced {pos - old_pos} bytes")
    except Exception as e:
        _LOGGER.error(f"Error parsing top-level status: {e}")
        _LOGGER.debug(f"Full buffer hex dump: {binascii.hexlify(buf)}")
        # Return partial results, if any

    _LOGGER.debug(f"Completed status parsing with results: {status}")
    return status


def parse_and_format(status: dict) -> dict:
    """Convert raw status dict into short, lowercased results for Home Assistant."""
    inverter_sn = status.get("sn") or "N/A"
    evse = status.get("evse") or {}

    _LOGGER.debug(f"Formatting status data: {status}")

    # Car status
    raw_car_status = evse.get("carStatus")
    if raw_car_status is not None:
        try:
            car_enum = CarStatus(raw_car_status)
            car_status_text = car_enum.label()  # e.g., "charging"
            _LOGGER.debug(f"Formatted car status: {raw_car_status} -> {car_status_text}")
        except ValueError:
            car_status_text = f"unknown_{raw_car_status}"
            _LOGGER.warning(f"Unknown car status value: {raw_car_status}")
    else:
        car_status_text = "n/a"
        _LOGGER.debug("No car status found in data")

    # Charger status
    raw_charger_status = evse.get("chargerStatus")
    if raw_charger_status is not None:
        try:
            ch_enum = ChargerStatus(raw_charger_status)
            charger_status_text = ch_enum.label()
            _LOGGER.debug(f"Formatted charger status: {raw_charger_status} -> {charger_status_text}")
        except ValueError:
            charger_status_text = f"unknown_{raw_charger_status}"
            _LOGGER.warning(f"Unknown charger status value: {raw_charger_status}")
    else:
        charger_status_text = "n/a"
        _LOGGER.debug("No charger status found in data")

    charge_power = evse.get("chargePower")
    if charge_power is not None:
        _LOGGER.debug(f"Charge power: {charge_power} W")
    else:
        _LOGGER.debug("No charge power found in data")

    session_energy = evse.get("sessionEnergy")
    if session_energy is not None:
        _LOGGER.debug(f"Session energy: {session_energy} Wh")
    else:
        _LOGGER.debug("No session energy found in data")

    # Error, if any
    error_msg = ""
    subsystem = evse.get("subsystem")
    error_code = evse.get("errorCode")
    if subsystem is not None and error_code is not None and error_code != 0:
        error_msg = f"Error code={error_code}, subsystem={subsystem}"
        _LOGGER.debug(f"Error detected: {error_msg}")

    charger_sn = evse.get("sn") or ""
    if charger_sn:
        _LOGGER.debug(f"Charger SN: {charger_sn}")
    else:
        _LOGGER.debug("No charger SN found in data")

    formatted_result = {
        "inverter_sn": inverter_sn,
        "car_status": car_status_text,
        "charger_status": charger_status_text,
        "charge_power": charge_power,
        "session_energy": session_energy,
        "error": error_msg,
        "charger_sn": charger_sn
    }

    _LOGGER.debug(f"Final formatted result: {formatted_result}")
    return formatted_result


class SolarEdgeEVChargerAUDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from the EV Charger (AU) endpoint."""

    def __init__(self, hass: HomeAssistant, host: str, scan_interval: int):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self._last_raw_data = None  # Store the last raw data received
        _LOGGER.debug(f"Initialized coordinator with host={host}, scan_interval={scan_interval}s")

    async def _async_update_data(self) -> dict:
        """Perform actual async fetch using aiohttp."""
        return await self._fetch_data()

    async def _fetch_data(self) -> dict:
        """Load status from the charger, parse it."""
        url = f"http://{self.host}/web/v1/status"
        _LOGGER.debug(f"Fetching data from: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    _LOGGER.debug(f"HTTP response status: {resp.status}")
                    resp.raise_for_status()
                    raw_data = await resp.read()
                    _LOGGER.debug(f"Received {len(raw_data)} bytes of raw data")

                    # Store the raw data for diagnostics
                    self._last_raw_data = raw_data

            parsed = parse_status(raw_data)
            formatted = parse_and_format(parsed)
            return formatted

        except aiohttp.ClientError as err:
            error_msg = f"Connection error fetching data from {url}: {err}"
            _LOGGER.error(error_msg)
            raise UpdateFailed(error_msg)
        except Exception as err:
            error_msg = f"Error fetching/parsing data from {url}: {type(err).__name__}: {err}"
            _LOGGER.error(error_msg)
            _LOGGER.debug(f"Exception details:", exc_info=True)
            raise UpdateFailed(error_msg)