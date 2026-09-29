"""
Desktop unit tests for two-relay control (rules, schedule, commands, sleep wake-ups).
Run with: python3 firmware/tests/test_relays.py
No hardware required.
"""

import sys
import os
import time
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ── Stub MicroPython-only modules ─────────────────────────────────────────────

class _Pin:
    IN, OUT, IRQ_RISING = 0, 1, 1
    def __init__(self, *a, **k): self._v = k.get("value", 0)
    def value(self, v=None):
        if v is None: return self._v
        self._v = v
    def irq(self, **k): pass

_machine = types.ModuleType("machine")
_machine.Pin = _Pin
_machine.lightsleep = lambda ms: None
sys.modules["machine"] = _machine

from automation.rules import evaluate, evaluate_schedule
import automation.rules as rules_mod
from automation.control import handle_relays
import power.manager as power

# ── Fakes ─────────────────────────────────────────────────────────────────────

class FakeRelay:
    def __init__(self, remaining=None):
        self.log = []
        self._remaining = remaining
    def on(self, duration_s):  self.log.append(("on", duration_s))
    def off(self):             self.log.append(("off",)); self._remaining = None
    def remaining_ms(self):    return self._remaining
    def tick(self):
        if self._remaining == 0: self.off()


def ts_at(hh, mm):
    """Unix ts for today hh:mm local time (weekday irrelevant: slots use all days)."""
    lt = time.localtime()
    return int(time.mktime((lt[0], lt[1], lt[2], hh, mm, 0, lt[6], lt[7], -1)))


RULES = [
    {"sensor": "soil_pct", "op": ">=", "value": 60, "action": "relay_off"},               # relay 1 (default)
    {"sensor": "soil_pct", "op": "<",  "value": 30, "action": "relay_on", "duration_s": 300},
    {"sensor": "lux", "op": "<", "value": 100, "action": "relay_on", "duration_s": 120, "relay": 2},
    {"sensor": "lux", "op": ">=", "value": 500, "action": "relay_off", "relay": 2},
]

# ── Tests ─────────────────────────────────────────────────────────────────────

def test_rules_per_relay():
    r = {"soil_pct": 20, "lux": 50}
    assert evaluate(RULES, r)["duration_s"] == 300, "relay 1 = rules without 'relay'"
    assert evaluate(RULES, r, relay=2)["duration_s"] == 120
    assert evaluate(RULES, {"soil_pct": 70, "lux": 900}, relay=2)["action"] == "relay_off"
    assert evaluate(RULES, {"soil_pct": 40, "lux": 300}, relay=2) is None
    print("PASS  rules_per_relay")


def test_schedule_both_relays_fire():
    rules_mod._last_fired.clear()
    sched = [{"time": "08:00", "duration_s": 600},
             {"time": "08:00", "duration_s": 90, "relay": 2}]
    hits = evaluate_schedule(sched, {}, ts_at(8, 5))
    assert sorted((h["relay"], h["duration_s"]) for h in hits) == [(1, 600), (2, 90)], hits
    assert evaluate_schedule(sched, {}, ts_at(8, 10)) == [], "no double fire in the same window"
    print("PASS  schedule_both_relays_fire")


def test_schedule_one_per_relay():
    rules_mod._last_fired.clear()
    sched = [{"time": "08:00", "duration_s": 600}, {"time": "08:10", "duration_s": 30}]
    hits = evaluate_schedule(sched, {}, ts_at(8, 15))
    assert hits == [{"relay": 1, "action": "relay_on", "duration_s": 600}], hits
    hits = evaluate_schedule(sched, {}, ts_at(8, 20))
    assert hits == [{"relay": 1, "action": "relay_on", "duration_s": 30}], "second slot stays due"
    print("PASS  schedule_one_per_relay")


def test_command_targets_one_relay_only():
    rules_mod._last_fired.clear()
    k1, k2 = FakeRelay(), FakeRelay()
    cfg = {"relay_rules": RULES, "relay_schedule": []}
    ack = handle_relays([{"id": 7, "action": "relay_off", "relay": 1}], {1: k1, 2: k2},
                        {"soil_pct": 20, "lux": 50}, cfg)
    assert ack == 7
    assert k1.log == [("off",)], "command wins over relay 1's rule"
    assert k2.log == [("on", 120)], "relay 2 automation still runs"
    print("PASS  command_targets_one_relay_only")


def test_legacy_command_and_unknown_relay():
    k1, k2 = FakeRelay(), FakeRelay()
    cfg = {"relay_rules": [], "relay_schedule": []}
    assert handle_relays([{"id": 1, "action": "relay_on", "duration_s": 45}], {1: k1, 2: k2}, {}, cfg) == 1
    assert k1.log == [("on", 45)] and k2.log == [], "command without 'relay' = relay 1"
    k1, k2 = FakeRelay(), FakeRelay()
    assert handle_relays([{"id": 2, "action": "relay_on", "relay": 3}], {1: k1, 2: k2}, {}, cfg) == 2
    assert k1.log == [] and k2.log == [], "unknown relay ignored but acked"
    k1 = FakeRelay()
    handle_relays([{"id": 3, "action": "relay_on", "duration_s": None}], {1: k1}, {}, cfg)
    assert k1.log == [("on", 60)], "missing duration falls back to 60 s"
    print("PASS  legacy_command_and_unknown_relay")


def test_schedule_beats_rules_per_relay():
    rules_mod._last_fired.clear()
    k1, k2 = FakeRelay(), FakeRelay()
    cfg = {"relay_rules": RULES, "relay_schedule": [{"time": "08:00", "duration_s": 90, "relay": 2}]}
    handle_relays([], {1: k1, 2: k2}, {"ts": ts_at(8, 1), "soil_pct": 70, "lux": 900}, cfg)
    assert k2.log == [("on", 90)], "schedule wins over relay 2's off rule this cycle"
    assert k1.log == [("off",)], "relay 1 still follows its rules"
    print("PASS  schedule_beats_rules_per_relay")


def test_sleep_wakes_for_each_relay():
    slept = []
    power._do_sleep = lambda ms: slept.append(ms)

    class Countdown(FakeRelay):
        def __init__(self, ms): super().__init__(ms)
        def remaining_ms(self):
            if self._remaining is None: return None
            return max(0, self._remaining - sum(slept))

        def tick(self):
            if self.remaining_ms() == 0: self.off()

    a, b = Countdown(10_000), Countdown(25_000)
    power.sleep(60, relays=[a, b])
    assert slept == [10_000, 15_000, 35_000], slept
    assert a.log == [("off",)] and b.log == [("off",)]
    slept.clear()
    power.sleep(5, relays=[])
    assert slept == [5_000]
    print("PASS  sleep_wakes_for_each_relay")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [test_rules_per_relay, test_schedule_both_relays_fire, test_schedule_one_per_relay,
             test_command_targets_one_relay_only, test_legacy_command_and_unknown_relay,
             test_schedule_beats_rules_per_relay, test_sleep_wakes_for_each_relay]
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
