"""
uart_debug.py — Drop-in UART mirror for Project Pico.
Import this FIRST in main.py.  After import, every print() call is
automatically duplicated to UART0 (TX=GPIO0, RX=GPIO1) so the Machine
Pico bridge can forward it to the PC.

Works around MicroPython RP2350 limitation: sys.stdout is read-only and
os.dupterm only has one slot (index 0 = USB CDC, must not replace it).
Solution: replace builtins.print with a wrapper that writes to both.
"""
import machine
import builtins
import utime

_uart = machine.UART(0, baudrate=115200, tx=machine.Pin(0), rx=machine.Pin(1))

_HEARTBEAT_INTERVAL_MS = 10_000
_last_hb = utime.ticks_ms()

_orig_print = builtins.print


def _mirrored_print(*args, **kwargs):
    _orig_print(*args, **kwargs)
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    msg = sep.join(str(a) for a in args) + end
    try:
        _uart.write(msg.encode("utf-8"))
    except Exception:
        pass


builtins.print = _mirrored_print


def tick():
    """Call once per main-loop iteration for a periodic heartbeat over UART."""
    global _last_hb
    now = utime.ticks_ms()
    if utime.ticks_diff(now, _last_hb) >= _HEARTBEAT_INTERVAL_MS:
        _uart.write("[hb] uptime_ms={}\r\n".format(now).encode())
        _last_hb = now


def send_raw(msg):
    """Write directly to UART without going through print()."""
    _uart.write((msg if msg.endswith("\r\n") else msg + "\r\n").encode())
