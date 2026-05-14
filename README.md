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

| Sensor | Chip / interface | Measures |
|--------|-----------------|----------|
| Temperature | DS18B20, 1-Wire (GP8) | °C |
| Humidity | DHT22, GP9 | % RH + °C fallback |
| pH | ADS1115 ADC (I2C, GP2/3) | pH 0–14 |
| EC | LMP91200, SPI (GP4–7) | µS/cm |
| Light | BH1750 / VEML7700, I2C (GP2/3) | lux |
| Soil moisture | Capacitive, ADC (GP26–28) | % |
| Motion | PIR, GP11 (also wake IRQ) | boolean |
| Water level | Float switch, GP16 | float |

All sensor fields are nullable — unconnected sensors send `null`.

## Relay

- **Auto rules**: threshold-based (e.g. water when soil < 30 %) configured in `firmware/src/config.json`
- **Schedule**: time-based rules, also in `config.json`
- **Manual override**: one-click from the dashboard, queued via server command API

## Repo layout

```
firmware/   MicroPython source + flash/dev tools
server/     FastAPI app, SQLite schema, systemd unit
dashboard/  Vanilla HTML/JS/CSS frontend
hardware/   KiCad schematic + BOM
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
