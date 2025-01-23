DOMAIN = "solaredge_ev_charger_au"

CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"

# Let users choose which unit system to display
CONF_UNIT_SYSTEM = "unit_system"

UNIT_SYSTEM_W = "w_wh"       # Display raw W and Wh
UNIT_SYSTEM_KW = "kw_kwh"    # Display kW and kWh

DEFAULT_HOST = "192.168.0.138"

# NOTE: This is in seconds
DEFAULT_SCAN_INTERVAL = 30

# Default if user does not pick anything in Options
DEFAULT_UNIT_SYSTEM = UNIT_SYSTEM_KW
