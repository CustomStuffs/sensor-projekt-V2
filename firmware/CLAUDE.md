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

| GPIO | Net | Connected to |
|------|-----|-------------|
| GP0 | UART_TX | Debug header |
| GP1 | UART_RX | Debug header |
| GP2 | I2C1_SDA | ADS1115 + BH1750 |
| GP3 | I2C1_SCL | ADS1115 + BH1750 |
| GP4 | SPI0_MISO | LMP91200 |
| GP5 | SPI0_MOSI | LMP91200 |
| GP6 | SPI0_SCK | LMP91200 |
| GP7 | SPI0_CS | LMP91200 (active low) |
| GP8 | 1-Wire | DS18B20 (Wago port 1) |
| GP9 | DHT_DATA | DHT22 (Wago port 2) |
| GP10 | RELAY_DRV | BC817 NPN base via 1 kΩ |
| GP11 | PIR_IN | PIR output + wake IRQ (Wago port 3) |
| GP12 | PIR_MOSFET | PIR power gate (saves 50–65 mA when off) |
| GP13 | EC_PWM_A | EC excitation, 1–5 kHz |
| GP14 | EC_PWM_B | EC excitation complement |
| GP15 | (spare) | Was BH1750 ADDR; VEML7700 has no ADDR pin |
| GP16 | WAGO4 | Generic (Wago port 4) |
| GP17 | WAGO5 | Generic (Wago port 5) |
| GP26 | ADC0 | Spare analog |
| GP27 | ADC1 | Spare analog |
| GP28 | ADC2 | Spare analog |

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
└── automation/          # relay rule evaluation
```

## API Contract (firmware side)

The Pico W calls these endpoints in order each cycle:
1. `POST /api/time` → get unix timestamp + config update
2. `POST /api/readings` → upload buffered readings
3. `GET /api/commands` → fetch any pending relay commands
4. `POST /api/commands/{id}/ack` → acknowledge executed commands

Full shapes: see root `CLAUDE.md`.

## Power Budget

| State | Current | Duration per 30-min cycle |
|-------|---------|--------------------------|
| Lightsleep | 0.30 mA | ~1745 s |
| Sensing (all sensors) | 25 mA | ~25 s |
| PIR warm-up | 65 mA | ~5 s |
| WiFi active | 80 mA | ~15 s |
| **Average** | **~1.2 mA** | |

10,000 mAh power bank → ~6–11 months depending on WiFi conditions.

## Calibration

**pH** (2-point): use pH 4.0 and pH 7.0 buffer solutions. Record mV at each point. Update `ph_cal` in config.json.

**EC**: use 1413 µS/cm standard solution. Set `ec_gain` in config.json to normalize reading.

**Soil moisture**: `dry_mv` = reading in dry air; `wet_mv` = reading in water. Update in config.json.

## Rules

- No blocking delay longer than 2 s in the main loop
- Every sensor read must return `None` on error, never raise
- config.json is the only user-editable file — all tunables go here
