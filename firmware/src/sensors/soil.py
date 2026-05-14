"""Resistive soil moisture sensor on a Pico ADC pin (default GP26)."""

from machine import ADC


def read(cfg, cal):
    """
    Return soil moisture as percentage (0-100) or None on error.
    cfg = sensors.soil block from config.json  (needs "adc_pin")
    cal = calibration.soil block               (needs "dry_count", "wet_count")
    Higher raw count = drier (high resistance = high voltage at ADC pin).
    """
    try:
        raw = ADC(cfg.get("adc_pin", 26)).read_u16()
    except Exception:
        return None

    dry = cal["dry_count"]
    wet = cal["wet_count"]
    if dry == wet:
        return None

    pct = (dry - raw) / (dry - wet) * 100.0
    return round(max(0.0, min(100.0, pct)), 1)
