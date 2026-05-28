#!/usr/bin/env python3
"""
Flash Machine Pico firmware (boot.py + main.py).

Usage:
  Unplug the Machine Pico, then run this script, then replug.
  The script waits for the device, then copies files within the 4 s boot window.
"""
import sys
import time
import subprocess
from pathlib import Path

PORT   = "/dev/ttyACM1"
SRC    = Path(__file__).parent.parent / "machine_pico"
FILES  = ["boot.py", "main.py"]


def wait_for_port(port: str, timeout: float = 30.0) -> bool:
    import serial.tools.list_ports
    deadline = time.time() + timeout
    print(f"Waiting for {port} (replug Machine Pico now)…")
    while time.time() < deadline:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if port in ports:
            return True
        time.sleep(0.05)
    return False


def flash_file(port: str, src: Path, dest: str) -> bool:
    cmd = ["mpremote", "connect", port, "resume", "cp", str(src), dest]
    print(f"  {src.name} → {dest}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        err = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "no output"
        print(f"  FAILED: {err}")
    return r.returncode == 0


def main():
    if not wait_for_port(PORT):
        print("ERROR: timed out waiting for Machine Pico")
        sys.exit(1)

    print(f"Found {PORT} — flashing within boot window…")
    time.sleep(0.6)   # let USB enumerate

    ok = True
    for fname in FILES:
        fp = SRC / fname
        if not fp.exists():
            print(f"  SKIP {fname} (not found)")
            continue
        ok &= flash_file(PORT, fp, f":{fname}")

    if ok:
        print("\nDone — replug to start bridge firmware.")
    else:
        print("\nSome files failed — try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
