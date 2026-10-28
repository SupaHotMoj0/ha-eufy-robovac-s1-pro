"""Bounded metadata-only observation; never retain arbitrary payload values."""
from collections import deque
from copy import deepcopy
from itertools import islice
import logging
from datetime import datetime, timezone
import time


class ProtocolTrace:
    def __init__(self, capacity=200, clock=time.monotonic):
        self._rows = deque(maxlen=capacity)
        self._clock = clock
        self._until = 0
        self._listeners = set()
        self._sequence = 0
        self.rx = self.tx = 0
        self.seen_dps = set()
        self.last_rx = None

    @property
    def enabled(self):
        return self._clock() < self._until

    def set_enabled(self, enabled):
        self._until = self._clock() + 600 if enabled else 0
        self._notify(None)

    def clear(self):
        self._rows.clear()
        self._notify(None)

    def subscribe(self, callback):
        self._listeners.add(callback)
        return lambda: self._listeners.discard(callback)

    def _notify(self, row):
        for callback in tuple(self._listeners):
            try:
                callback(deepcopy(row))
            except Exception:
                logging.getLogger(__name__).warning("Trace listener failed; details omitted")

    def record(self, direction, command, payload, outcome="observed"):
        if direction not in ("incoming", "outgoing"):
            raise ValueError("Invalid packet direction")
        now = datetime.now(timezone.utc).isoformat()
        if direction == "incoming":
            self.rx += 1
            self.last_rx = now
        else:
            self.tx += 1
        dps = payload.get("dps", {}) if isinstance(payload, dict) else {}
        if not isinstance(dps, dict):
            dps = {}
        fields = {}
        for key, value in islice(dps.items(), 128):
            key = str(key)
            if not key.isascii() or not key.isdigit() or not 1 <= len(key) <= 5:
                continue
            if len(self.seen_dps) < 256:
                self.seen_dps.add(key)
            if isinstance(value, bool):
                kind = "bool"
            elif isinstance(value, (int, float)):
                kind = "number"
            elif isinstance(value, str):
                kind = "string"
            elif isinstance(value, (bytes, bytearray)):
                kind = "bytes"
            elif value is None:
                kind = "null"
            else:
                kind = "container"
            fields[key] = {"type": kind}
            labels = {"8": "battery", "9": "fan_speed", "111": "volume",
                      "152": "cleaning_command", "153": "robot_status",
                      "154": "cleaning_mode", "156": "auto_return",
                      "167": "cleaning_statistics", "168": "consumable_statistics"}
            if key in labels:
                fields[key]["meaning"] = labels[key]
            if key == "152" and isinstance(value, str):
                actions = {"AA==": "start", "AggO": "cleaning", "AggN": "pause", "AggG": "return_to_base"}
                fields[key]["known_action"] = actions.get(value, "unrecognized")
            if isinstance(value, (str, bytes, bytearray, list, dict)):
                fields[key]["length"] = len(value)
        row = None
        if self.enabled:
            self._sequence += 1
            row = {"sequence": self._sequence, "time": now, "direction": direction,
                   "command": command if type(command) is int and 0 <= command <= 65535 else None,
                   "datapoints": fields, "outcome": "write_failed" if outcome == "write_failed" else "observed"}
            self._rows.append(row)
        self._notify(row)

    def snapshot(self):
        return {"enabled": self.enabled, "capacity": self._rows.maxlen,
                "rx": self.rx, "tx": self.tx, "last_rx": self.last_rx,
                "seen_dps": sorted(self.seen_dps, key=int), "rows": deepcopy(list(self._rows))}
