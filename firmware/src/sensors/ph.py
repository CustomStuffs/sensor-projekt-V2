"""pH sensor — ADS1115 AIN0, 2-point linear calibration."""


def read(ads, cal, channel=0):
    """
    Return pH float or None on error.
    cal = { "v_at_ph4": float, "v_at_ph7": float }
    """
    try:
        v = ads.read_voltage(channel)
    except Exception:
        return None

    v4 = cal["v_at_ph4"]
    v7 = cal["v_at_ph7"]
    if v4 == v7:
        return None

    slope = (7.0 - 4.0) / (v7 - v4)
    ph = 7.0 + slope * (v - v7)
    ph = max(0.0, min(14.0, ph))
    return round(ph, 2)
