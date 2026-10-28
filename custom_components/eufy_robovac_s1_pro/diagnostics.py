"""Allowlisted metadata only: never dump config entries or raw datapoints."""
from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN


async def async_get_config_entry_diagnostics(hass, entry):
    devices = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get(CONF_DISCOVERED_DEVICES, {})
    return {"format_version": 1, "robots": [
        {"robot": index, "last_update_success": props[CONF_COORDINATOR].last_update_success,
         "trace": props[CONF_COORDINATOR].trace.snapshot()}
        for index, props in enumerate(devices.values(), 1)
    ]}
