"""Relay rule evaluation: sensor threshold rules and time-based daily schedule."""

import time

_OPS = {
    "<":  lambda a, b: a < b,
    ">":  lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
}

_DAY_MAP = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

# Tracks last-fired unix timestamp per schedule entry index to avoid double-firing.
_last_fired = {}


def evaluate(rules, reading):
    """
    Check sensor threshold rules against the latest reading dict.
    Returns the first matching rule dict or None.
    Rule shape: { "sensor", "op", "value", "action", "duration_s" }
    """
    for rule in rules:
        val = reading.get(rule["sensor"])
        if val is None:
            continue
        op_fn = _OPS.get(rule["op"])
        if op_fn and op_fn(val, rule["value"]):
            return rule
    return None


def evaluate_schedule(schedule, reading, current_ts):
    """
    Check each time-based schedule entry against the current time.
    Fires on the first cycle after the scheduled time (within a 29-minute window).
    Returns {"action": "relay_on", "duration_s": N} or None.

    Slot shape: { "time": "HH:MM", "duration_s": int, "days": [...], "skip_if": {sensor, op, value} | null }
    """
    lt = time.localtime(current_ts)
    current_min = lt[3] * 60 + lt[4]
    weekday = lt[6]

    for i, slot in enumerate(schedule):
        # Day-of-week check
        allowed_days = [_DAY_MAP[d] for d in slot.get("days", list(_DAY_MAP.keys()))]
        if weekday not in allowed_days:
            continue

        # Time window: fire on the first cycle in the 29 minutes after scheduled time
        h, m = slot["time"].split(":")
        sched_min = int(h) * 60 + int(m)
        delta = current_min - sched_min
        if delta < 0 or delta >= 29:
            continue

        # Avoid double-firing within the same window
        window_start_ts = current_ts - delta * 60
        if _last_fired.get(i, 0) >= window_start_ts:
            continue

        # Sensor condition: skip if condition is met
        skip_if = slot.get("skip_if")
        if skip_if:
            val = reading.get(skip_if["sensor"])
            op_fn = _OPS.get(skip_if["op"])
            if val is not None and op_fn and op_fn(val, skip_if["value"]):
                continue

        _last_fired[i] = current_ts
        return {"action": "relay_on", "duration_s": slot["duration_s"]}

    return None
