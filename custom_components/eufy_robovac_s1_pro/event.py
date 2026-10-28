"""Optional captured-packet events. Disabled by default to avoid Recorder churn."""
from homeassistant.components.event import EventEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN


async def async_setup_entry(hass, entry, add_entities):
    add_entities([ProtocolEvent(p[CONF_COORDINATOR]) for p in
        hass.data[DOMAIN][entry.entry_id][CONF_DISCOVERED_DEVICES].values()])


class ProtocolEvent(CoordinatorEntity, EventEntity):
    _attr_name = "Protocol event"
    _attr_has_entity_name = True
    _attr_event_types = ["incoming", "outgoing"]
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.tuya_client.device_id}_protocol_event"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.tuya_client.device_id)}}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(self.coordinator.trace.subscribe(self._on_packet))

    def _on_packet(self, row):
        if row is not None:
            self._trigger_event(row["direction"], row)
            self.async_write_ha_state()
