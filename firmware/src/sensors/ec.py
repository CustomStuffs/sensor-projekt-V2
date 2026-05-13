"""
EC sensor — LMP91200 AFE + ADS1115 AIN1 (NTC temp compensation).

Excitation: complementary PWM on GP13/GP14, RC-filtered (10kΩ + 100nF).
NTC divider on ADS1115 AIN1: 10kΩ pull-up to 3V3_ANA, NTC to GND.
Temperature compensation: 2% per °C relative to ref_temp_c.
"""

import math
import time


_NTC_R0   = 10000.0   # NTC nominal resistance at 25 °C
_NTC_B    = 3950.0    # NTC B-constant
_PULLUP_R = 10000.0   # pull-up resistor
_NTC_VCC  = 3.3       # NTC pull-up rail (3V3_ANA), distinct from LMP ref (1.65 V)


def _ntc_temp_c(ads, ref_voltage):
    """Read NTC on AIN1 and return temperature in °C, or None on error."""
    try:
        v_ntc = ads.read_voltage(1)
    except Exception:
        return None
    if v_ntc <= 0 or v_ntc >= ref_voltage:
        return None
    r_ntc = _PULLUP_R * v_ntc / (ref_voltage - v_ntc)
    try:
        temp_k = 1.0 / (math.log(r_ntc / _NTC_R0) / _NTC_B + 1.0 / 298.15)
    except (ZeroDivisionError, ValueError):
        return None
    return round(temp_k - 273.15, 1)


def read(ads, lmp, cal, pwm_a, pwm_b):
    """
    Return EC in µS/cm (float) or None on error.
    pwm_a / pwm_b: machine.PWM objects already configured for AC excitation.
    cal = { "cell_constant": float, "ref_voltage": float, "ref_temp_c": float }
    """
    try:
        pwm_a.duty_u16(32768)
        pwm_b.duty_u16(32768)
        time.sleep_ms(10)   # let RC filter (10kΩ + 100nF, τ=1ms) settle
        v_out = ads.read_voltage(3)
    except Exception:
        return None
    finally:
        pwm_a.duty_u16(0)
        pwm_b.duty_u16(0)

    ref_v = cal["ref_voltage"]
    cell_k = cal["cell_constant"]
    ref_t = cal["ref_temp_c"]

    v_diff = abs(v_out - ref_v)
    if v_diff < 1e-6:
        return None

    # Raw conductance from TIA: G = V_diff / (TIA_gain * excitation_amplitude)
    # With TIA gain = 35 kΩ and 1.65 V reference, normalise to cell constant.
    tia_gain = 35000.0
    ec_raw = (v_diff / tia_gain) * cell_k * 1e6   # µS/cm

    temp_c = _ntc_temp_c(ads, _NTC_VCC)
    if temp_c is not None:
        # Linear temp compensation: 2% per °C
        ec_raw = ec_raw / (1.0 + 0.02 * (temp_c - ref_t))

    return round(ec_raw, 1)
