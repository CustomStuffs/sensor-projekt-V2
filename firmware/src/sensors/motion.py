"""
PIR motion sensor on GP11, powered through Q2 (BSS84, P-channel) on GP12.

GP12 LOW = PIR powered, HIGH = off; R17 keeps it off while GP12 floats at boot.
While motion is enabled the PIR stays powered (AM312 / HC-SR501 idle current is
well under 0.1 mA) and an IRQ latches every rising edge on GP11, so a reading
reports "motion since the last reading" instead of a short scan window. The
edge also wakes the Pico from lightsleep. Edges during the PIR's warm-up after
power-on are ignored.
"""

from machine import Pin
import time

_pir = None
_ready_at = None
_seen = False


def _on_edge(pin):
    global _seen
    if time.ticks_diff(time.ticks_ms(), _ready_at) >= 0:
        _seen = True


def start(pir_pin_num=11, gate_pin_num=12, warmup_s=60):
    """Power the PIR and arm the edge latch. Call once at boot."""
    global _pir, _ready_at, _seen
    Pin(gate_pin_num, Pin.OUT, value=0)   # LOW = Q2 on = PIR powered
    _pir = Pin(pir_pin_num, Pin.IN)
    _ready_at = time.ticks_add(time.ticks_ms(), warmup_s * 1000)
    _seen = False
    _pir.irq(trigger=Pin.IRQ_RISING, handler=_on_edge)


def read():
    """
    Return True if motion was seen since the last read, False if not,
    None while the PIR is still warming up or start() was not called.
    """
    global _seen
    if _pir is None or time.ticks_diff(time.ticks_ms(), _ready_at) < 0:
        return None
    try:
        detected = _seen or bool(_pir.value())
        _seen = False
        return detected
    except Exception:
        return None
