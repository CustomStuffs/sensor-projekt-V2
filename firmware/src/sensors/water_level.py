"""Float switch on Wago W4 (J5): GP16, internal pull-up.

Wiring: the switch's two wires go to W4 pin 2 (GND) and pin 3 (GP16); pin 1 stays empty.
Contact closed pulls GP16 LOW = water present. Mount (or flip) the float so the
contact closes when the tank has water. Any open-collector / open-drain level
sensor that pulls LOW on liquid works the same way.
Returns 1.0 if water present, 0.0 if dry, None on error.
"""

from machine import Pin


def read(cfg):
    """cfg = sensors.water_level block from config.json (needs "pin")."""
    try:
        p = Pin(cfg.get("pin", 16), Pin.IN, Pin.PULL_UP)
        return 0.0 if p.value() else 1.0
    except Exception:
        return None
