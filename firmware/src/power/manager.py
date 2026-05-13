"""lightsleep power manager."""

import machine
import time


def sleep(duration_s, relay=None, pir_pin_num=11):
    """
    Sleep for duration_s. If relay is active and expires sooner, wakes early
    to turn it off then sleeps the remainder. Returns True if woken by PIR.
    """
    pir = machine.Pin(pir_pin_num, machine.Pin.IN)
    pir.irq(trigger=machine.Pin.IRQ_RISING)

    if relay is not None:
        rem_ms = relay.remaining_ms()
        if rem_ms is not None and rem_ms < duration_s * 1000:
            _do_sleep(rem_ms)
            relay.tick()
            rest_ms = duration_s * 1000 - rem_ms
            if rest_ms > 0:
                _do_sleep(rest_ms)
            return bool(pir.value())

    _do_sleep(duration_s * 1000)
    return bool(pir.value())


def _do_sleep(ms):
    try:
        machine.lightsleep(int(ms))
    except Exception:
        time.sleep_ms(int(ms))


def uptime_ms():
    return time.ticks_ms()
