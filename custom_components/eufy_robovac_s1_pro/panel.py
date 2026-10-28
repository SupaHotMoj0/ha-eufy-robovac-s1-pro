"""Authenticated admin-only inspector; no arbitrary protocol-write endpoint."""
import asyncio
from pathlib import Path
import voluptuous as vol
from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback
from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN

PANEL_PATH = "eufy-s1-pro-inspector"
STATIC_PATH = "/eufy_s1_pro_inspector_static"


def _coordinators(hass):
    for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
        if isinstance(entry_data, dict):
            for index, props in enumerate(entry_data.get(CONF_DISCOVERED_DEVICES, {}).values(), 1):
                yield f"{entry_id}:{index}", props[CONF_COORDINATOR]


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/inspector"})
@websocket_api.require_admin
@callback
def ws_inspector(hass, connection, msg):
    connection.send_result(msg["id"], {"robots": [
        {"id": key, "label": f"S1 Pro {index}", "trace": coord.trace.snapshot(),
         "connected": coord.last_update_success}
        for index, (key, coord) in enumerate(_coordinators(hass), 1)
    ]})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/capture",
    vol.Required("robot"): str, vol.Required("action"): vol.In(["start", "stop", "clear"])})
@websocket_api.require_admin
@callback
def ws_capture(hass, connection, msg):
    coordinator = dict(_coordinators(hass)).get(msg["robot"])
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "Robot is not loaded")
        return
    if msg["action"] == "clear":
        coordinator.trace.clear()
    else:
        coordinator.set_capture(msg["action"] == "start")
    connection.send_result(msg["id"], {"ok": True})


async def async_setup_panel(hass):
    lock = hass.data.setdefault(f"{DOMAIN}_panel_lock", asyncio.Lock())
    async with lock:
        key = f"{DOMAIN}_inspector_registered"
        if hass.data.get(key):
            return
        if not hass.data.get(f"{DOMAIN}_inspector_paths"):
            await hass.http.async_register_static_paths([
                StaticPathConfig(STATIC_PATH, str(Path(__file__).parent / "frontend"), cache_headers=False)
            ])
            hass.data[f"{DOMAIN}_inspector_paths"] = True
        if not hass.data.get(f"{DOMAIN}_inspector_ws"):
            websocket_api.async_register_command(hass, ws_inspector)
            websocket_api.async_register_command(hass, ws_capture)
            hass.data[f"{DOMAIN}_inspector_ws"] = True
        await panel_custom.async_register_panel(
            hass, webcomponent_name="eufy-s1-pro-inspector", frontend_url_path=PANEL_PATH,
            sidebar_title="S1 Pro Inspector", sidebar_icon="mdi:robot-vacuum",
            module_url=f"{STATIC_PATH}/inspector.js", require_admin=True,
        )
        hass.data[key] = True
