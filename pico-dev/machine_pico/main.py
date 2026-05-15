"""
Machine Pico — UART bridge + relay controller
Wiring: UART1 TX=GPIO4 → Project Pico RX=GPIO1
        UART1 RX=GPIO5 ← Project Pico TX=GPIO0
        GPIO15 → Relay IN  (LOW = relay closed = RUN pulled to GND = reset)
"""
import machine
import utime
import sys
import uselect

BAUD       = 115200
RESET_MS   = 100    # how long to hold RUN low

# UART1 talks to Project Pico
uart  = machine.UART(1, baudrate=BAUD, tx=machine.Pin(4), rx=machine.Pin(5))

# Relay: HIGH = open (idle), LOW = closed (pulls RUN → GND → reset)
relay = machine.Pin(15, machine.Pin.OUT, value=1)

# Non-blocking stdin polling
_poll = uselect.poll()
_poll.register(sys.stdin, uselect.POLLIN)


def relay_reset(ms=RESET_MS):
    relay.value(0)
    utime.sleep_ms(ms)
    relay.value(1)


def usb_write(msg):
    sys.stdout.write(msg)


usb_write("[bridge] ready — commands: RESET | SEND:<text>\r\n")

_cmd_buf = ""

while True:
    # ── Forward Project Pico UART output → USB ──────────────────────────────
    n = uart.any()
    if n:
        chunk = uart.read(n)
        # Decode as UTF-8; replace any garbage bytes rather than crashing
        usb_write(chunk.decode("utf-8", "replace"))

    # ── Read commands from USB (non-blocking) ───────────────────────────────
    if _poll.poll(0):
        ch = sys.stdin.read(1)

        if ch in ("\r", "\n"):
            cmd = _cmd_buf.strip()
            _cmd_buf = ""

            if not cmd:
                pass  # ignore blank lines

            elif cmd == "RESET":
                relay_reset()
                usb_write("[bridge] RESET sent\r\n")

            elif cmd.startswith("SEND:"):
                payload = cmd[5:]
                uart.write(payload + "\r\n")
                usb_write("[bridge] TX: " + payload + "\r\n")

            else:
                usb_write("[bridge] unknown cmd: " + cmd + "\r\n")

        else:
            _cmd_buf += ch

    utime.sleep_ms(1)
