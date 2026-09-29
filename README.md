# Sensor Hub

Outdoor environmental monitoring system built on a Raspberry Pi Pico W. Sensors are read every 30 minutes, uploaded over WiFi to a FastAPI server running on a Raspberry Pi, and displayed in a browser dashboard.

## System overview

```
Pico W (MicroPython)
  └─ POST JSON ──► RPi FastAPI server (port 8080)
                      └─ SQLite DB
                      └─ Static files ──► Browser dashboard
```

Remote access via Tailscale VPN — no port forwarding, no auth layer needed.

## Sensors

| Sensor | Chip / interface | Board connection | Measures |
|--------|-----------------|------------------|----------|
| Temperature | DS18B20, 1-Wire (GP8) | W1 (J2) | °C |
| Humidity | DHT22, GP9 | W2 (J3) | % RH + °C fallback |
| pH | AD8603 buffer → ADS1115 AIN0 (I2C, GP2/3) | BNC (J1), guarded input | pH 0–14 |
| Light | VEML7700, I2C (GP2/3) | on the board, under a light pipe to the lid | lux |
| Soil moisture | Capacitive, Pico ADC (GP26) | J11 solder holes (GP26–28) | % |
| Motion | PIR, GP11 (also wake IRQ), power-gated by GP12 | W3 (J4) | boolean |
| Water level | Float switch, GP16 | W4 (J5) | float |
| Probe temperature | NTC → ADS1115 AIN1 | J8 pins 3/4 | °C (for compensation) |
| EC | **not on the v1 board** (LMP91200 is EOL; firmware driver exists, keep `ec` disabled) | — | µS/cm |

All sensor fields are nullable — unconnected sensors send `null`.

## Relays (two on-board channels)

The PCB carries **two independent SPDT relays** (K1 on GP10, K2 on GP15), rated 230 VAC / 5 A with reinforced insulation to the sensor side, as a hard minimum. Local sensor rules can drive either relay (`"relay": 2` in a rule); dashboard commands and schedules reach relay 1 until the server API carries a relay number. This allows two simultaneous actuator channels (e.g. pump + valve) without external modules. Future board variants can add more relays.

- **Auto rules**: threshold-based (e.g. water when soil < 30 %) configured in `firmware/src/config.json`
- **Schedule**: time-based rules, also in `config.json`
- **Manual override**: one-click from the dashboard, queued via server command API

## Repo layout

```
firmware/   MicroPython source + flash/dev tools
server/     FastAPI app, SQLite schema, systemd unit
dashboard/  Vanilla HTML/JS/CSS frontend
hardware/   KiCad project + generation scripts, BOM, JLCPCB order files
```

Each folder has its own `CLAUDE.md` with subproject-specific rules.

## Getting started

### Firmware

Requires MicroPython 1.28+ (`RPI_PICO_W` build).

```bash
cd firmware
bash tools/setup.sh          # install mpremote, check device
cp src/config.json.example src/config.json   # fill in WiFi + server URL
bash tools/flash.sh          # copy all files to device
bash tools/monitor.sh        # watch serial output
```

For daily development, use the mount workflow instead of reflashing:

```bash
bash tools/mount.sh   # edits in src/ take effect on Ctrl-D
```

### Server

```bash
cd server
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

Or run as a systemd service:

```bash
sudo cp sensor_hub.service /etc/systemd/system/
sudo systemctl enable --now sensor_hub
```

### Dashboard

Served as static files by the FastAPI server — no build step. Open `http://<pi-ip>:8080` in a browser.

### Hardware

100 × 100 mm, 2-layer PCB (`hardware/kicad/`), generated and routed by the scripts in `hardware/tools/`. JLCPCB fabricates the board and places all SMD parts (`hardware/fab/`, regenerate with `python3 hardware/tools/jlc_export.py`); the through-hole parts — Pico WH sockets, relays, Wago push-in terminals, BNC, X2 capacitors, UART header — are hand-soldered. Details: `hardware/CLAUDE.md` and `hardware/docs/`.

## Pico W hardware notes

- **VSYS ADC**: use `ADC(29)` (GPIO29), not `ADC(3)`. On Pico W, GPIO29 is the VSYS/3 voltage divider. `ADC(3)` reads GPIO3 (I2C SCL) and gives garbage.
- **VSYS measurement timing**: read VSYS *before* `wlan.active(True)` — GPIO29 is shared with the WiFi SPI bus and returns wrong values while the radio is up.
- **Lightsleep after WiFi**: `machine.lightsleep(ms)` can fail silently on Pico W after WiFi use. The firmware falls back to `time.sleep()` automatically and logs when this happens.
- **Serial monitor**: uses `mpremote` (`bash tools/monitor.sh`), not minicom. On immutable distros (Bazzite/Silverblue), minicom is not available.
- **Flashing**: the device enters lightsleep ~30 s after boot, making `mpremote` unreachable. Flash immediately after plugging in USB, or interrupt via REPL first.

## Power budget (battery operation)

| State | Current |
|-------|---------|
| Lightsleep | 0.30 mA |
| Sensing (all sensors) | 25 mA |
| WiFi active | 80 mA |
| **Average (30 min cycle)** | **~1.2 mA** |

A 10 000 mAh power bank lasts roughly 6–11 months.

## License

MIT
