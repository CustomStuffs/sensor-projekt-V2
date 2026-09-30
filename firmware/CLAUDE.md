# Firmware Agent

> **Scope: `firmware/` only. Do not read, modify, or suggest changes to files outside this directory.**

MicroPython firmware for Raspberry Pi Pico W. This subproject owns everything that runs on the device.

## Tooling (always use these, never raw mpremote commands ad-hoc)

| Script | When to use |
|--------|------------|
| `tools/setup.sh` | First time — installs mpremote, checks device |
| `tools/mount.sh` | **Daily dev loop** — mounts src/ on device, edit locally, Ctrl-D to reload |
| `tools/flash.sh` | Release build — copies all files to device |
| `tools/repl.sh` | Interactive REPL / inspect device state |
| `tools/monitor.sh` | Watch serial output (minicom, 115200 baud) |
| `tools/reset.sh` | Soft-reset device |

Full workflow documentation: `docs/WORKFLOW.md`

## MicroPython Version

**1.28+ required.** This project uses the **Pico W (RP2040)**. Use the `RPI_PICO_W` build — not the generic RP2040 build (no WiFi) and not the Pico 2 W build.

Download page: https://micropython.org/download/RPI_PICO_W/  
Latest stable: https://micropython.org/resources/firmware/RPI_PICO_W-20260406-v1.28.0.uf2

Flash: hold BOOTSEL, plug USB, release, drag `.uf2` onto the `RPI-RP2` drive.  
Confirm chip: the `INDEX.HTM` on the bootloader drive should redirect to `raspberrypi.com/device/RP2?version=...` (RP2040). If it says RP2350 you have a Pico 2 W and need the `RPI_PICO2_W` build instead.

## GPIO Pinout

Source: `hardware/docs/schematic.md` (v1 board).

| GPIO | Net | Connected to |
|------|-----|-------------|
| GP0 | UART0 TX | Debug header HDR1 pin 1 |
| GP1 | UART0 RX | Debug header HDR1 pin 2 |
| GP2 | I2C1 SDA | ADS1115 (0x48) + VEML7700 (0x10); 4.7 kΩ pull-up R10 |
| GP3 | I2C1 SCL | ADS1115 + VEML7700; 4.7 kΩ pull-up R11 |
| GP4–GP7 | free | J11 solder holes 1–4; reserved for a v2 EC front-end. Not connected to anything on the v1 board — the LMP91200 SPI code in firmware has no hardware |
| GP8 | 1-Wire | DS18B20, Wago W1 (J2); 4.7 kΩ pull-up R5 |
| GP9 | DHT_DATA | DHT22, Wago W2 (J3); 10 kΩ pull-up R6 |
| GP10 | RELAY1_DRV | K1 via Q1 (BC817) + 1 kΩ R8 |
| GP11 | PIR_OUT | PIR output + wake IRQ, Wago W3 (J4); 10 kΩ pull-up R9 |
| GP12 | PIR_EN_N | PIR power gate Q2 (BSS84): LOW = PIR on; R17 pulls it off at boot |
| GP13, GP14 | not connected | were the EC excitation PWM outputs; EC is not on the v1 board |
| GP15 | RELAY2_DRV | K2 via Q3 (BC817) + 1 kΩ R18 |
| GP16 | W4_SIG | Wago W4 (J5), generic digital (e.g. float switch) |
| GP17 | W5_SIG | Wago W5 (J6), generic digital |
| GP18–GP22 | free | J11 solder holes 5–9 |
| GP26–GP28 | free, ADC0–2 | J11 solder holes 10–12 (0–3.3 V analog, e.g. capacitive soil sensor on GP26) |
| RUN | RUN | J11 hole 13 |

**Pico W LED**: `Pin("LED", Pin.OUT)` — NOT `Pin(25)`.

## Source Layout

```
src/
├── main.py              # scheduler loop — DO NOT put blocking code here
├── config.json          # user config (WiFi, server URL, intervals, relay rules)
├── sensors/             # one file per sensor, all return float | None
├── drivers/             # low-level hardware (I2C, SPI register access)
├── communication/       # WiFi, HTTP, time sync
├── storage/             # ringbuffer persisted to flash
├── power/               # lightsleep + wake IRQ
└── automation/          # relay rules + schedule (rules.py), per-relay control (control.py)
```

## API Contract (firmware side)

The Pico W calls these endpoints in order each cycle:
1. `POST /api/time` → get unix timestamp + config update
2. `POST /api/readings` → upload buffered readings
3. `GET /api/commands` → fetch any pending relay commands
4. `POST /api/commands/{id}/ack` → acknowledge executed commands

Full shapes: see root `CLAUDE.md`.

## Relays (K1 = relay 1 on GP10, K2 = relay 2 on GP15)

- Both relays have the same safety timeout (`relay.max_on_duration_s`); `power.sleep()` wakes early for whichever relay's on-time ends first.
- Commands, schedule slots and `relay_rules` entries take an optional `"relay": 1 | 2`; without it they drive relay 1, so existing configs, schedules and commands are unchanged.
- Priority **per relay**: server command > schedule > sensor rules. A command for relay 1 does not stop relay 2's rules or schedule in the same cycle. One server command per cycle (acked on the next upload).
- Example rule for relay 2 in `config.json`: `{ "sensor": "lux", "op": "<", "value": 100, "action": "relay_on", "duration_s": 600, "relay": 2 }`
- Server and dashboard send `relay` in commands and schedule slots (see root `CLAUDE.md` → API contract).
- Tests: `python3 firmware/tests/test_relays.py` (desktop, no hardware).

## Power Budget

| State | Current | Duration per 30-min cycle |
|-------|---------|--------------------------|
| Lightsleep | 0.30 mA | ~1745 s |
| Sensing (all sensors) | 25 mA | ~25 s |
| PIR (powered while motion is enabled) | < 0.1 mA | continuous |
| WiFi active | 80 mA | ~15 s |
| **Average** | **~1.2 mA** | |

10,000 mAh power bank → ~6–11 months depending on WiFi conditions.

## Calibration

**pH** (2-point): use pH 4.0 and pH 7.0 buffer solutions. Record mV at each point. Update `ph_cal` in config.json.

**EC** (needs an EC front-end — not on the v1 board, keep `ec` disabled): use 1413 µS/cm standard solution. Set `ec_gain` in config.json to normalize reading.

**Soil moisture**: `dry_count` = raw ADC count in dry air; `wet_count` = raw count in water. Update `calibration.soil` in config.json.

**Probe temperature** (NTC on J8, ADS1115 AIN1): set `sensors.probe_temp.enabled`; `calibration.probe_temp` holds the NTC's R25 (`ntc_r0`) and B value (`ntc_b`) from its datasheet.

## Rules

- No blocking delay longer than 2 s in the main loop
- Every sensor read must return `None` on error, never raise
- config.json is the only user-editable file — all tunables go here
- Desktop tests (no hardware): `python3 firmware/tests/test_calibration.py`, `test_relays.py`, `test_motion.py`
