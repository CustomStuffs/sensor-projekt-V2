#!/usr/bin/env python3
"""
pico_tool.py — Machine Pico UART bridge controller

Commands
--------
  monitor              Stream Project Pico debug output live (also accepts RESET / SEND:)
  reset                Hard-reset Project Pico via relay (100 ms)
  flash <file.py>      Copy a file to Project Pico via its USB port — requires explicit confirmation

Auto-detection
--------------
All connected Pico devices (VID=0x2E8A, PID=0x0005) are listed.
If exactly one is found it is used automatically as the Machine Pico.
With multiple devices the --port flag or an interactive prompt selects it.
"""

import sys
import time
import argparse
import subprocess
import threading
from pathlib import Path

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial not installed.  Run: pip install pyserial")
    sys.exit(1)

# Raspberry Pi Foundation VID, MicroPython CDC PID
_PICO_VID = 0x2E8A
_PICO_PID = 0x0005
_BAUD     = 115200


# ── Port detection ────────────────────────────────────────────────────────────

def find_pico_ports() -> list[tuple[str, str]]:
    """Return [(port, description)] for every connected MicroPython Pico."""
    return [
        (p.device, p.description)
        for p in serial.tools.list_ports.comports()
        if p.vid == _PICO_VID and p.pid == _PICO_PID
    ]


def pick_machine_port(explicit: str | None = None) -> str:
    """Resolve which serial port is the Machine Pico."""
    if explicit:
        return explicit

    ports = find_pico_ports()

    if not ports:
        print("ERROR: No MicroPython Pico found (VID=0x2E8A PID=0x0005).")
        print("  → Check USB cable and that Machine Pico runs MicroPython firmware.")
        sys.exit(1)

    if len(ports) == 1:
        port, desc = ports[0]
        print(f"[auto] Machine Pico: {port}  ({desc})")
        return port

    print("Multiple Pico devices found:")
    for i, (port, desc) in enumerate(ports):
        print(f"  [{i}] {port}  {desc}")
    try:
        idx = int(input("Select Machine Pico index: ").strip())
        return ports[idx][0]
    except (ValueError, IndexError):
        print("Invalid selection.")
        sys.exit(1)


def _open(port: str) -> serial.Serial:
    s = serial.Serial(port, _BAUD, timeout=0.1, dsrdtr=False, rtscts=False)
    s.dtr = False
    return s


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_monitor(port: str) -> None:
    """
    Bidirectional monitor: Project Pico output → terminal, keyboard → Machine Pico.
    Type RESET or SEND:<text> and press Enter while monitoring.
    Ctrl-C exits.
    """
    interactive = sys.stdin.isatty()
    print(f"[monitor] {port} @ {_BAUD} baud — Ctrl-C to stop")
    if interactive:
        print("[monitor] type  RESET  or  SEND:<text>  to interact\n")
    else:
        print("[monitor] read-only (no TTY)\n")

    running = True

    def _read_loop(ser: serial.Serial) -> None:
        while running:
            try:
                data = ser.read(256)
                if data:
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
            except Exception:
                break

    with _open(port) as ser:
        reader = threading.Thread(target=_read_loop, args=(ser,), daemon=True)
        reader.start()
        try:
            if interactive:
                while True:
                    line = input()
                    ser.write((line + "\r\n").encode())
            else:
                reader.join()   # non-TTY: just stream until Ctrl-C
        except (KeyboardInterrupt, EOFError):
            running = False
            print("\n[monitor] stopped")


def cmd_reset(port: str) -> None:
    """Send RESET command; print bridge confirmation line."""
    with _open(port) as ser:
        ser.write(b"RESET\r\n")
        time.sleep(0.4)
        resp = ser.read(512)
    print(resp.decode("utf-8", "replace").strip() or "[reset] (no response)")


def cmd_flash(port: str, file_path: str) -> None:
    """
    Flash a .py file to the Project Pico via its own USB port.

    Requires:
    - Project Pico ALSO connected via USB (for mpremote access)
    - mpremote installed: pip install mpremote

    Flow: confirm → RESET via relay → mpremote on Project Pico USB within boot.py 5 s window
    """
    fp = Path(file_path)
    if not fp.exists():
        print(f"ERROR: file not found: {fp}")
        sys.exit(1)

    # Find Project Pico port (any Pico that isn't the Machine Pico)
    all_ports = [p for p, _ in find_pico_ports()]
    project_ports = [p for p in all_ports if p != port]

    if not project_ports:
        print("ERROR: Cannot find Project Pico's USB port.")
        print("  → Make sure Project Pico is also connected via USB.")
        print("  → If both show up on the same port, use --port to specify Machine Pico.")
        sys.exit(1)

    project_port = project_ports[0]

    # ── Confirmation gate ─────────────────────────────────────────────────────
    print()
    print("┌── FLASH SUMMARY ───────────────────────────────────────┐")
    print(f"│  File         : {fp.name:<42}│")
    print(f"│  Machine Pico : {port:<42}│")
    print(f"│  Project Pico : {project_port:<42}│")
    print(f"│  Destination  : :{fp.name:<41}│")
    print("└────────────────────────────────────────────────────────┘")
    print()
    answer = input("Type 'yes' to confirm flash: ").strip().lower()
    if answer != "yes":
        print("Aborted.")
        return

    # ── Reset → flash within boot.py 5 s window ──────────────────────────────
    # boot.py holds the USB REPL open for 5 s after every hard reset.
    # USB re-enumeration takes ~0.5-1 s, so we have ~4 s to hit the window.
    # Three attempts at t≈1s, t≈2.5s, t≈4s cover the window regardless of timing.
    # "resume" skips mpremote's own Ctrl-D so it doesn't trigger another boot cycle.
    print("[flash] Sending RESET to Project Pico...")
    with _open(port) as ser:
        ser.write(b"RESET\r\n")

    dest = f":{fp.name}"
    cmd  = ["mpremote", "connect", project_port, "resume", "cp", str(fp), dest]

    for attempt, delay in enumerate([1.0, 1.5, 1.5], start=1):
        print(f"[flash] waiting {delay:.0f}s then attempt {attempt}/3 (t={sum([1.0,1.5,1.5][:attempt]):.1f}s after reset)...")
        time.sleep(delay)
        print(f"[flash] attempt {attempt}/3: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        except subprocess.TimeoutExpired:
            print(f"[flash] attempt {attempt} timed out")
            continue
        if result.returncode == 0:
            print(f"[flash] OK — {fp.name} copied to Project Pico")
            return
        err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "no output"
        print(f"[flash] attempt {attempt} failed: {err}")

    print("[flash] all attempts failed — try running within 5 s of a manual replug")
    sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pico_tool",
        description="Machine Pico UART bridge controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--port", "-p",
        metavar="PORT",
        help="Override serial port for Machine Pico (skips auto-detect)",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("monitor", help="Stream live UART output (interactive)")
    sub.add_parser("reset",   help="Hard-reset Project Pico via relay")

    fl = sub.add_parser("flash", help="Flash a .py file to Project Pico")
    fl.add_argument("file", help=".py file to copy")

    args = parser.parse_args()
    port = pick_machine_port(args.port)

    if args.cmd == "monitor":
        cmd_monitor(port)
    elif args.cmd == "reset":
        cmd_reset(port)
    elif args.cmd == "flash":
        cmd_flash(port, args.file)


if __name__ == "__main__":
    main()
