"""
Desktop unit tests for pH, EC, and soil calibration math.
Run with: python3 firmware/tests/test_calibration.py
No hardware required.
"""

import sys
import os
import math
import types

# ── Stub MicroPython-only modules before any firmware import ──────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

class _FakeADC:
    """machine.ADC stand-in: every pin returns _FakeADC.count."""
    count = 0
    def __init__(self, pin): pass
    def read_u16(self): return _FakeADC.count

_machine = types.ModuleType("machine")
_machine.Pin = object
_machine.ADC = _FakeADC
sys.modules.setdefault("machine", _machine)

_micropython = types.ModuleType("micropython")
_micropython.const = lambda x: x
sys.modules.setdefault("micropython", _micropython)

import time as _time
if not hasattr(_time, "sleep_ms"):
    _time.sleep_ms = lambda ms: None   # no-op on desktop

# ── Import actual sensor modules ──────────────────────────────────────────────

import sensors.ph as ph_sensor
import sensors.ec as ec_sensor
import sensors.soil as soil_sensor
import sensors.probe_temp as probe_temp_sensor
import sensors.light as light_sensor

# ── Mock hardware objects ─────────────────────────────────────────────────────

class MockADS:
    """Returns preset voltages / raw counts per channel."""
    def __init__(self, voltages=None, raw_counts=None):
        if isinstance(voltages, (int, float)):
            voltages = {ch: voltages for ch in range(4)}
        self._v = voltages or {}
        self._r = raw_counts or {}

    def read_voltage(self, channel, fsr=2.048):
        self.last_fsr = fsr
        return self._v.get(channel, 0.0)

    def read_raw(self, channel):
        return self._r.get(channel, 0)


class MockPWM:
    def duty_u16(self, val): pass


class MockLMP:
    pass


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_ph_calibration():
    cal = {"v_at_ph4": 1.855, "v_at_ph7": 1.650}

    assert ph_sensor.read(MockADS(1.650), cal) == 7.00, "pH 7 at v_at_ph7"
    assert ph_sensor.read(MockADS(1.855), cal) == 4.00, "pH 4 at v_at_ph4"

    mid_v = (cal["v_at_ph4"] + cal["v_at_ph7"]) / 2
    mid_ph = ph_sensor.read(MockADS(mid_v), cal)
    assert abs(mid_ph - 5.5) < 0.05, f"pH midpoint off: {mid_ph}"

    assert ph_sensor.read(MockADS(3.3), cal) == 0.0,  "high voltage → pH clamped to 0"
    assert ph_sensor.read(MockADS(0.0), cal) == 14.0, "low voltage → pH clamped to 14"

    bad_cal = {"v_at_ph4": 1.65, "v_at_ph7": 1.65}
    assert ph_sensor.read(MockADS(1.65), bad_cal) is None, "degenerate cal → None"

    print("PASS  test_ph_calibration")


def test_ec_ntc():
    # At 25 °C, NTC = R0; divider with 3.3 V supply → V = 1.65 V
    t = ec_sensor._ntc_temp_c(MockADS(voltages={1: 1.65}), 3.3)
    assert t is not None and abs(t - 25.0) < 0.5, f"NTC 25 °C: got {t}"

    assert ec_sensor._ntc_temp_c(MockADS(voltages={1: 0.0}), 3.3) is None, "zero V → None"
    assert ec_sensor._ntc_temp_c(MockADS(voltages={1: 3.3}), 3.3) is None, "rail V → None"

    print("PASS  test_ec_ntc")


def test_ec_temp_compensation():
    cal = {"cell_constant": 1.0, "ref_voltage": 1.65, "ref_temp_c": 25.0}

    # At 35 °C, raw conductance is ~20 % high; compensation must recover the ref value.
    # Reverse-engineer the AIN3 voltage that yields ec_raw = 1413 * 1.2.
    ec_raw_35 = 1413.0 * 1.2
    v_diff = ec_raw_35 * ec_sensor.tia_gain / 1e6 if hasattr(ec_sensor, "tia_gain") \
             else ec_raw_35 * 35000.0 / 1e6
    v_out = cal["ref_voltage"] + v_diff

    # NTC voltage at 35 °C from Steinhart-Hart (matches ec.py constants)
    r_ntc_35 = ec_sensor._NTC_R0 * math.exp(
        ec_sensor._NTC_B * (1 / 308.15 - 1 / 298.15))
    v_ntc_35 = ec_sensor._NTC_VCC * r_ntc_35 / (r_ntc_35 + ec_sensor._PULLUP_R)

    ads = MockADS(voltages={3: v_out, 1: v_ntc_35})
    result = ec_sensor.read(ads, MockLMP(), cal, MockPWM(), MockPWM())
    assert result is not None and abs(result - 1413.0) < 2.0, \
        f"EC temp compensation at 35 °C: got {result}"

    print("PASS  test_ec_temp_compensation")


def test_soil_calibration():
    cal = {"dry_count": 26000, "wet_count": 13000}
    cfg = {"adc_pin": 26}

    def soil(count):
        _FakeADC.count = count
        return soil_sensor.read(cfg, cal)

    assert soil(26000) == 0.0,   "dry = 0 %"
    assert soil(13000) == 100.0, "wet = 100 %"
    assert abs(soil((26000 + 13000) // 2) - 50.0) < 0.1, "midpoint ~50 %"
    assert soil(30000) == 0.0,   "over-range → 0 %"
    assert soil(5000) == 100.0,  "under-range → 100 %"

    _FakeADC.count = 20000
    assert soil_sensor.read(cfg, {"dry_count": 20000, "wet_count": 20000}) is None, \
        "degenerate cal → None"

    print("PASS  test_soil_calibration")


def test_probe_temp():
    cal = {"ntc_r0": 10000, "ntc_b": 3950}

    # 25 °C: NTC = pull-up = 10 k → node at half of 3.3 V
    ads = MockADS(voltages={1: 1.65})
    assert probe_temp_sensor.read(ads, cal) == 25.0
    assert ads.last_fsr == 4.096, "NTC must be read on the ±4.096 V range"

    # 5 °C: NTC ≈ 25.3 k → node ≈ 2.37 V, above the old ±2.048 V range
    r5 = 10000 * math.exp(3950 * (1 / 278.15 - 1 / 298.15))
    v5 = 3.3 * r5 / (r5 + 10000)
    assert v5 > 2.048
    assert abs(probe_temp_sensor.read(MockADS(voltages={1: v5}), cal) - 5.0) < 0.1

    assert probe_temp_sensor.read(MockADS(voltages={1: 3.3}), cal) is None, "open probe → None"
    assert probe_temp_sensor.read(MockADS(voltages={1: 0.0}), cal) is None, "short → None"
    print("PASS  test_probe_temp")


def test_light_scaling():
    assert abs(light_sensor._LUX_COEFF - 2.1504) < 1e-9, "gain 1/8, IT 25 ms = 2.1504 lux/count"
    assert abs(light_sensor._correct(100) - 100.2) < 1, "correction ~1:1 at low lux"
    assert light_sensor._correct(50000) > 50000, "correction raises high readings"
    print("PASS  test_light_scaling")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    failures = 0
    tests = [test_ph_calibration, test_ec_ntc, test_ec_temp_compensation,
             test_soil_calibration, test_probe_temp, test_light_scaling]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failures += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {e}")
            failures += 1

    if failures:
        sys.exit(1)
    print(f"\n{len(tests)}/{len(tests)} tests passed.")
