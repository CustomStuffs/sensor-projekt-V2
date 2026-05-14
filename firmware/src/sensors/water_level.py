"""IR optical liquid level sensor (e.g. FS-IR1901D) on a digital GPIO pin.

Wiring: power from VBUS (5V), signal wire to cfg["pin"] with PULL_UP.
NPN open-collector output: pulled LOW when liquid detected, HIGH in air.
Returns 1.0 if liquid present, 0.0 if dry, None on error.
"""

from machine import Pin


def read(cfg):
    """cfg = sensors.water_level block from config.json (needs "pin")."""
    try:
        p = Pin(cfg.get("pin", 16), Pin.IN, Pin.PULL_UP)
        return 0.0 if p.value() else 1.0
    except Exception:
        return None
