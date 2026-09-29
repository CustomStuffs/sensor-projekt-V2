"""lightsleep power manager."""

import machine
import time


def sleep(duration_s, relays=(), pir_pin_num=11):
    """
    Sleep for duration_s. Wakes early whenever an active relay's on-time runs out,
    switches it off, and sleeps the remainder. Returns True if woken by PIR.
    """
    pir = machine.Pin(pir_pin_num, machine.Pin.IN)
    pir.irq(trigger=machine.Pin.IRQ_RISING)

    relays = list(relays)
    left_ms = duration_s * 1000
    while left_ms > 0:
        due = [r.remaining_ms() for r in relays if r.remaining_ms() is not None]
        step = min(due + [left_ms])
        if step > 0:                       # never lightsleep(0): relay already due, just tick
            _do_sleep(step)
        left_ms -= step
        for r in relays:
            r.tick()
    return bool(pir.value())


def _do_sleep(ms):
    try:
        machine.lightsleep(int(ms))
    except Exception as e:
        print("lightsleep unavailable, falling back to time.sleep:", e)
        time.sleep(ms / 1000)


def uptime_ms():
    return time.ticks_ms()
