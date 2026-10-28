"""Discover only known entities when their datapoints arrive, exactly once."""
from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN


def setup_dynamic_entities(hass, entry, add_entities, factory):
    seen = set()
    for props in hass.data[DOMAIN][entry.entry_id][CONF_DISCOVERED_DEVICES].values():
        coordinator = props[CONF_COORDINATOR]
        def discover(coordinator=coordinator):
            pending = []
            for entity in factory(coordinator):
                key = entity.unique_id
                if key not in seen:
                    seen.add(key)
                    pending.append(entity)
            if pending:
                add_entities(pending)
        entry.async_on_unload(coordinator.async_add_listener(discover))
        discover()
