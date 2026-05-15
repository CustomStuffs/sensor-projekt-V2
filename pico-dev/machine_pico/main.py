"""
Machine Pico — UART bridge + relay controller
Wiring: UART1 TX=GPIO4 → Project Pico RX=GPIO1
        UART1 RX=GPIO5 ← Project Pico TX=GPIO0
        GPIO15 → Relay IN  (LOW = relay closed = RUN pulled to GND = reset)

Commands (normal mode):
  RESET         — pulse relay 100 ms → hard-reset Project Pico
  SEND:<text>   — write <text>\\r\\n to Project Pico via UART
  BRIDGE        — enter transparent passthrough mode (USB ↔ UART1)

Bridge mode:
  All USB bytes are forwarded to UART1 and vice versa with no processing.
  This lets mpremote (or any tool) talk directly to the Project Pico's
  UART0 REPL. Exit by sending 5× Ctrl-C in a row.
"""
import machine
import utime
import sys
import uselect
import micropython

BAUD     = 115200
RESET_MS = 100

uart  = machine.UART(1, baudrate=BAUD, tx=machine.Pin(4), rx=machine.Pin(5))
relay = machine.Pin(15, machine.Pin.OUT, value=1)

_poll = uselect.poll()
_poll.register(sys.stdin, uselect.POLLIN)


def relay_reset(ms=RESET_MS):
    relay.value(0)
    utime.sleep_ms(ms)
    relay.value(1)


def usb_write(msg):
    sys.stdout.write(msg)


# ── Bridge mode ───────────────────────────────────────────────────────────────

def run_bridge():
    """
    Transparent USB↔UART passthrough. mpremote can connect to this port and
    talk directly to the Project Pico's UART0 REPL (Pico W default primary
    REPL stream). Exit: send 5× Ctrl-C in a row.
    """
    usb_write("[bridge] BRIDGE MODE — 5x Ctrl-C to exit\r\n")

    # Disable MicroPython's own Ctrl-C interrupt so we can forward \x03 raw.
    micropython.kbd_intr(-1)

    exit_count = 0

    try:
        while True:
            # UART → USB: forward Project Pico output
            n = uart.any()
            if n:
                chunk = uart.read(n)
                # latin-1: lossless 1-to-1 byte↔char mapping for raw bytes
                sys.stdout.write(chunk.decode("latin-1"))

            # USB → UART: forward mpremote / tool input
            if _poll.poll(0):
                ch = sys.stdin.read(1)
                uart.write(ch.encode("latin-1"))

                if ch == "\x03":          # Ctrl-C
                    exit_count += 1
                    if exit_count >= 5:
                        break
                else:
                    exit_count = 0

            utime.sleep_ms(1)
    finally:
        micropython.kbd_intr(3)           # re-enable Ctrl-C
        usb_write("\r\n[bridge] bridge mode ended\r\n")


# ── Normal command mode ───────────────────────────────────────────────────────

usb_write("[bridge] ready — RESET | SEND:<text> | BRIDGE\r\n")

_cmd_buf = ""

while True:
    # Forward Project Pico UART output → USB
    n = uart.any()
    if n:
        chunk = uart.read(n)
        usb_write(chunk.decode("utf-8", "replace"))

    # Read USB commands (non-blocking)
    if _poll.poll(0):
        ch = sys.stdin.read(1)

        if ch in ("\r", "\n"):
            cmd = _cmd_buf.strip()
            _cmd_buf = ""

            if not cmd:
                pass

            elif cmd == "RESET":
                relay_reset()
                usb_write("[bridge] RESET sent\r\n")

            elif cmd.startswith("SEND:"):
                payload = cmd[5:]
                uart.write(payload + "\r\n")
                usb_write("[bridge] TX: " + payload + "\r\n")

            elif cmd == "BRIDGE":
                run_bridge()

            else:
                usb_write("[bridge] unknown: " + cmd + "\r\n")

        else:
            _cmd_buf += ch

    utime.sleep_ms(1)
