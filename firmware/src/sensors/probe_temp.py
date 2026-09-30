"""
NTC probe temperature on J8 pins 3/4 → ADS1115 AIN1.

Divider: R7 10 kΩ from 3V3_ANA to the node, NTC from the node to GND_ANA.
Read on the ±4.096 V range: a 10 k NTC below ~14 °C puts the node above 2.048 V.
"""

import math

_PULLUP_R = 10000.0   # R7
_NTC_VCC  = 3.3       # 3V3_ANA


def ntc_temp_c(v, r0=10000.0, b=3950.0, vcc=_NTC_VCC, pullup=_PULLUP_R):
    """Convert the divider voltage to °C (B-parameter equation), None if out of range."""
    if v <= 0 or v >= vcc:
        return None   # open probe (v ≈ vcc) or short (v ≈ 0)
    r_ntc = pullup * v / (vcc - v)
    try:
        temp_k = 1.0 / (math.log(r_ntc / r0) / b + 1.0 / 298.15)
    except (ZeroDivisionError, ValueError):
        return None
    return round(temp_k - 273.15, 1)


def read(ads, cal, channel=1):
    """
    Return probe temperature in °C (float) or None on error.
    cal = calibration.probe_temp block: { "ntc_r0": float, "ntc_b": float }
    """
    try:
        v = ads.read_voltage(channel, fsr=4.096)
    except Exception:
        return None
    return ntc_temp_c(v, r0=cal["ntc_r0"], b=cal["ntc_b"])
