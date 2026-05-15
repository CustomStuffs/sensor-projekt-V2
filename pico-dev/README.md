# Pico UART Debug Bridge

Two-Pico setup: **Machine Pico** (USB→PC) acts as a relay-reset + UART bridge
for the **Project Pico** (running the real firmware, never overwritten directly).

## Hardware

| Machine Pico | → | Project Pico |
|---|---|---|
| GPIO 4 (UART1 TX) | → | GPIO 1 (UART0 RX) |
| GPIO 5 (UART1 RX) | ← | GPIO 0 (UART0 TX) |
| GND | — | GND |
| GPIO 15 → Relay IN | | Relay COM → RUN pin, NO → GND |

Relay active-LOW: pulling GPIO 15 low closes the relay, which pulls RUN to GND
and resets the Project Pico.

## Quick Start

### 1. Flash the Machine Pico

Connect **only** the Machine Pico via USB.  Hold BOOTSEL, plug in → drag
`machine_pico/main.py` on using Thonny or mpremote:

```bash
mpremote connect /dev/ttyACM0 cp machine_pico/main.py :main.py
```

After reboot the Machine Pico prints `[bridge] ready …` on USB serial.

### 2. Install PC tool dependencies

```bash
pip install -r tools/requirements.txt
```

### 3. Use pico_tool.py

```bash
# Stream all Project Pico output live (also lets you type RESET / SEND:)
python tools/pico_tool.py monitor

# Hard-reset Project Pico via relay
python tools/pico_tool.py reset

# Copy a file to Project Pico (requires confirmation + Project Pico USB connected)
python tools/pico_tool.py flash firmware/src/main.py

# Force a specific port (skips auto-detect)
python tools/pico_tool.py --port /dev/ttyACM1 monitor
```

### 4. Add UART debug output to Project Pico (optional)

Copy `project_pico/uart_debug.py` to the Project Pico:

```bash
mpremote connect /dev/ttyACMx cp project_pico/uart_debug.py :uart_debug.py
```

Then make `uart_debug` the **first import** in `main.py`:

```python
import uart_debug   # must be first — mirrors all print() to UART

# ... rest of your firmware unchanged
```

All `print()` calls are now mirrored to UART0 and will appear in `pico_tool.py monitor`.
Call `uart_debug.tick()` once per loop iteration for a 10 s heartbeat.

## Command Protocol (Machine Pico ↔ PC)

These are the raw commands the Machine Pico understands over its USB serial.
`pico_tool.py` sends them automatically; you can also type them in monitor mode.

| Command | Effect |
|---|---|
| `RESET` | Closes relay 100 ms → Project Pico RUN → GND → hard reset |
| `SEND:<text>` | Sends `<text>\r\n` to Project Pico via UART |

## Flash Workflow (how `flash` works internally)

1. Confirms with user before touching anything
2. Sends `RESET` to Machine Pico (relay fires, Project Pico reboots)
3. Waits 2 s for MicroPython REPL to come up on Project Pico
4. Runs `mpremote connect <project-port> cp <file> :<file>` to copy the file

**Requirement**: the Project Pico must also be connected via USB during flashing
so mpremote can reach its filesystem.
