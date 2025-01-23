# SolarEdge EV Charger (Australia) - Home Assistant Integration

A custom component for Home Assistant to integrate **SolarEdge EV Charger (AU)** devices using the local Protobuf status endpoint.

## Features

- Discovers and polls the charger for car status, charger status, power (W or kW), energy (Wh or kWh), and any errors.
- Allows configuration of polling interval and unit system (W/Wh or kW/kWh).
- Automatically groups sensors under one device in Home Assistant.
- Short, lowercased states for easy automation (`"charging"`, `"connected"`, etc.).

## Installation

1. Copy or clone this repository into your Home Assistant `custom_components` folder:
   
   `<config_directory>/custom_components/solaredge_ev_charger_au`
   
2. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & Services → + Add Integration**.
2. Search for **"SolarEdge EV Charger (Australia)"**.
3. Enter the charger's IP address or hostname, and set a polling interval (in seconds).

## Options

After installation, open the **Options** flow to:
- Edit the IP or scanning interval.
- Choose **Watts/Watt-hours** (W/Wh) or **Kilowatts/Kilowatt-hours** (kW/kWh) for displayed values.

## Known Limitations

- The `icon` field in custom integrations doesn't affect the displayed icon in the UI.
- The integration is fully local but requires the EV Charger’s web endpoint (`/web/v1/status`) to be accessible.

## Support

- Please open issues in this repo if you encounter bugs or have feature requests.
- Code owners: [@niktest](https://github.com/niktest/solaredge_ev_charger_au)

## Available Sensors

1. **`solaredge_ev_charger_car_status`**
   - **Description**: Reflects the car's connection and charging state.
   - **Possible States**: `disconnected`, `connected`, `charging`, `rfid`, `undefined`.


2. **`solaredge_ev_charger_charger_status`**
   - **Description**: Reflects the EV charger's operational state.
   - **Possible States**: `ready`, `initializing`, `active`, `boost`, `excess_pv`, `off`, `error`.


3. **`solaredge_ev_charger_charge_power`**
   - **Description**: Displays the current charging power.
   - **Units**: Watts (W) or Kilowatts (kW).


4. **`solaredge_ev_charger_session_energy`**
   - **Description**: Total energy delivered during the current charging session.
   - **Units**: Watt-hours (Wh) or Kilowatt-hours (kWh).


5. **`solaredge_ev_charger_error`**
   - **Description**: Provides error details (code and subsystem).


6. **`solaredge_ev_charger_charger_sn`**
   - **Description**: Serial number of the EV charger.


7. **`solaredge_ev_charger_inverter_sn`**
   - **Description**: Serial number of the inverter, if connected.

## Home Assistant Sensors

You can find all entities created by this integration in Home Assistant under **Settings → Devices & Services → Entities**.

### Example Entity List
- `solaredge_ev_charger_car_status`
- `solaredge_ev_charger_charger_status`
- `solaredge_ev_charger_charge_power`
- `solaredge_ev_charger_session_energy`
- `solaredge_ev_charger_error`
- `solaredge_ev_charger_charger_sn`
- `solaredge_ev_charger_inverter_sn`
