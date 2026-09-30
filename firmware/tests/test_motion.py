"""
Desktop unit tests for the PIR motion latch (power gate polarity, warm-up, edge latch).
Run with: python3 firmware/tests/test_motion.py
No hardware required.
"""

import sys
import os
import time
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ── Stub MicroPython-only modules ─────────────────────────────────────────────

_now = [0]
time.ticks_ms = lambda: _now[0]
time.ticks_add = lambda t, d: t + d
time.ticks_diff = lambda a, b: a - b

class _Pin:
    IN, OUT, IRQ_RISING = 0, 1, 1
    pins = {}
    def __init__(self, num, mode=None, value=None):
        self.num, self._v, self.handler = num, value if value is not None else 0, None
        _Pin.pins[num] = self
    def value(self, v=None):
        if v is None: return self._v
        self._v = v
    def irq(self, trigger=None, handler=None):
        self.handler = handler

_machine = types.ModuleType("machine")
_machine.Pin = _Pin
sys.modules["machine"] = _machine

import sensors.motion as motion


def edge():
    """Simulate one PIR pulse: rising edge fires the IRQ, then the output drops."""
    pir = _Pin.pins[11]
    pir.value(1); pir.handler(pir); pir.value(0)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_not_started():
    assert motion.read() is None
    print("PASS  not_started")


def test_gate_low_powers_pir():
    _now[0] = 0
    motion.start(warmup_s=60)
    assert _Pin.pins[12].value() == 0, "GP12 LOW = Q2 (P-channel) on = PIR powered"
    assert _Pin.pins[11].handler is not None, "edge IRQ armed"
    print("PASS  gate_low_powers_pir")


def test_warmup_ignored():
    _now[0] = 0
    motion.start(warmup_s=60)
    _now[0] = 30_000
    edge()
    assert motion.read() is None, "still warming up"
    _now[0] = 60_000
    assert motion.read() is False, "edge during warm-up is not latched"
    print("PASS  warmup_ignored")


def test_latch_and_clear():
    _now[0] = 0
    motion.start(warmup_s=60)
    _now[0] = 100_000
    edge()
    _now[0] = 1_900_000
    assert motion.read() is True, "edge between readings is reported"
    assert motion.read() is False, "latch clears after a read"
    _Pin.pins[11].value(1)
    assert motion.read() is True, "output still high at read time counts"
    print("PASS  latch_and_clear")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [test_not_started, test_gate_low_powers_pir, test_warmup_ignored, test_latch_and_clear]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failures += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
            failures += 1
    if failures:
        sys.exit(1)
    print(f"\n{len(tests)}/{len(tests)} tests passed.")
