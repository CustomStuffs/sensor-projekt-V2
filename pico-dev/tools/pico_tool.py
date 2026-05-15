#!/usr/bin/env python3
"""
pico_tool.py — Machine Pico UART bridge controller

Commands
--------
  monitor              Stream Project Pico debug output live (also accepts RESET / SEND:)
  reset                Hard-reset Project Pico via relay (100 ms)
  flash <file.py>      Copy a file to Project Pico — requires explicit confirmation

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
    return serial.Serial(port, _BAUD, timeout=0.1)


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_monitor(port: str) -> None:
    """
    Bidirectional monitor: Project Pico output → terminal, keyboard → Machine Pico.
    Type RESET or SEND:<text> and press Enter while monitoring.
    Ctrl-C exits.
    """
    print(f"[monitor] {port} @ {_BAUD} baud — Ctrl-C to stop")
    print("[monitor] type  RESET  or  SEND:<text>  to interact\n")

    running = True

    def _read_loop(ser: serial.Serial) -> None:
        while running:
            data = ser.read(256)
            if data:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

    with _open(port) as ser:
        reader = threading.Thread(target=_read_loop, args=(ser,), daemon=True)
        reader.start()
        try:
            while True:
                line = input()               # blocks until user presses Enter
                ser.write((line + "\r\n").encode())
        except KeyboardInterrupt:
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
    Flash a .py file to the Project Pico.

    Requires:
    - Project Pico ALSO connected via USB (for mpremote access)
    - mpremote installed: pip install mpremote

    Flow: confirm → RESET via relay → 2 s pause → mpremote copy
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

    # ── Reset → pause → flash ─────────────────────────────────────────────────
    print("[flash] Sending RESET to Project Pico...")
    with _open(port) as ser:
        ser.write(b"RESET\r\n")

    print("[flash] Waiting 2 s for REPL to come up...")
    time.sleep(2)

    dest = f":{fp.name}"
    cmd  = ["mpremote", "connect", project_port, "cp", str(fp), dest]
    print(f"[flash] {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[flash] OK — {fp.name} copied to {project_port}")
        if result.stdout:
            print(result.stdout.strip())
    else:
        print("[flash] FAILED")
        if result.stderr:
            print(result.stderr.strip())
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
