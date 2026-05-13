"""Relay driver with mandatory safety timeout."""

from machine import Pin
import time

_DEFAULT_MAX_S = 600


class Relay:
    def __init__(self, pin_num, max_on_s=_DEFAULT_MAX_S):
        self._pin = Pin(pin_num, Pin.OUT, value=0)
        self._max_on_ms = max_on_s * 1000
        self._on_at = None
        self._duration_ms = 0

    def on(self, duration_s):
        """Energise relay for at most min(duration_s, max_on_s) seconds. Non-blocking."""
        self._duration_ms = min(duration_s * 1000, self._max_on_ms)
        self._pin.value(1)
        self._on_at = time.ticks_ms()

    def off(self):
        self._pin.value(0)
        self._on_at = None

    def tick(self):
        """Turn off if the requested duration has elapsed. Call from main loop."""
        if self._on_at is not None:
            if time.ticks_diff(time.ticks_ms(), self._on_at) >= self._duration_ms:
                self.off()

    def remaining_ms(self):
        """Milliseconds until auto-off, or None if relay is off."""
        if self._on_at is None:
            return None
        elapsed = time.ticks_diff(time.ticks_ms(), self._on_at)
        return max(0, self._duration_ms - elapsed)

    @property
    def is_on(self):
        return bool(self._pin.value())
