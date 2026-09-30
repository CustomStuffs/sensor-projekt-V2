"""lightsleep power manager."""

import machine
import time


def sleep(duration_s, relays=()):
    """
    Sleep for duration_s. Wakes early whenever an active relay's on-time runs out,
    switches it off, and sleeps the remainder. A pin IRQ (the PIR latch in
    sensors/motion.py) can end a lightsleep early; the time actually slept is
    counted, so the loop just sleeps the rest.
    """
    relays = list(relays)
    left_ms = duration_s * 1000
    while left_ms > 0:
        due = [r.remaining_ms() for r in relays if r.remaining_ms() is not None]
        step = min(due + [left_ms])
        slept = step
        if step > 0:                       # never lightsleep(0): relay already due, just tick
            slept = _do_sleep(step)
            if slept is None:
                slept = step
        left_ms -= slept
        for r in relays:
            r.tick()


def _do_sleep(ms):
    """Sleep up to ms; returns the milliseconds actually slept (less on an IRQ wake)."""
    t0 = time.ticks_ms()
    try:
        machine.lightsleep(int(ms))
    except Exception as e:
        print("lightsleep unavailable, falling back to time.sleep:", e)
        time.sleep(ms / 1000)
    return max(0, time.ticks_diff(time.ticks_ms(), t0))


def uptime_ms():
    return time.ticks_ms()
