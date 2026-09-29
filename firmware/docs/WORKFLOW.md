# Pico W Firmware Development Workflow

## One-Time Setup

### 1. Flash MicroPython to the Pico W

1. Hold the **BOOTSEL** button on the Pico W while plugging in USB.
2. The device appears as a USB drive named `RPI-RP2`.
3. Download the latest MicroPython UF2 for **Pico W** (not the generic RP2040 build):
   `https://micropython.org/download/RPI_PICO_W/`
   (Current stable: v1.28.0 — `RPI_PICO_W-20241025-v1.28.0.uf2`)
4. Drag the UF2 file onto the `RPI-RP2` drive.
5. The Pico W reboots automatically. MicroPython is now running.

### 2. Install dev tools

```bash
./tools/setup.sh
```

This installs `mpremote` and checks that `/dev/ttyACM0` is detected.

---

## Daily Development Loop

Use `mount.sh` — it mounts your local `src/` directory on the device without copying files. Edit normally in your editor; press Ctrl-D in the mpremote terminal to reload.

```bash
./tools/mount.sh
```

Inside the mpremote session:
- **Ctrl-D** — soft-reset and re-run `main.py` (picks up your latest edits instantly)
- **Ctrl-X** — exit mpremote cleanly

> **WARNING — filesystem corruption bug (MicroPython issue #10898)**
> After pressing Ctrl-D, wait for the `>>>` prompt before pressing Ctrl-C.
> Pressing Ctrl-C immediately after Ctrl-D triggers a known bug that can corrupt
> the entire Pico W filesystem. If that happens, re-flash MicroPython via BOOTSEL.

---

## Inspecting the Device

Open a REPL to run snippets, check sensor values, or poke at module state:

```bash
./tools/repl.sh
```

Useful REPL snippets:

```python
# Check config
import json
with open('config.json') as f: print(json.load(f))

# Read temperature manually
from drivers.ads1115 import ADS1115
from machine import I2C, Pin
i2c = I2C(1, sda=Pin(2), scl=Pin(3))
adc = ADS1115(i2c)
print(adc.read(0))   # AIN0 = pH buffer output

# Check WiFi
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print(wlan.scan())
```

---

## Monitoring Serial Output

Watch `print()` output from `main.py` without entering the REPL:

```bash
./tools/monitor.sh             # uses /dev/ttyACM0
./tools/monitor.sh /dev/ttyACM1   # if ACM0 is wrong
```

Exit: **Ctrl-A then X**.

---

## Resetting the Device

Soft-reset (reruns `main.py`, same as Ctrl-D in the REPL):

```bash
./tools/reset.sh
```

---

## Deploying a Release Build

When development is done, copy all files to device flash (no more live mount):

```bash
./tools/flash.sh
```

This runs `mpremote cp -r src/ :` then `mpremote reset`. After reset the device runs standalone without a USB connection.

---

## Calibration Procedures

### pH (2-point calibration)

1. Edit `config.json` → `calibration.ph`:

```json
"ph": {
  "v_at_ph4": 1.855,
  "v_at_ph7": 1.650
}
```

2. Measure the actual ADS1115 voltage for each buffer solution:
   - pH 4.01 buffer → record voltage as `v_at_ph4`
   - pH 7.00 buffer → record voltage as `v_at_ph7`
3. The slope is `(7 - 4) / (v_at_ph7 - v_at_ph4)` — pH increases as voltage decreases.

### EC (1-point calibration)

> Needs an EC front-end, which the v1 board does not have (LMP91200 removed, EOL). Keep `sensors.ec.enabled = false` on v1 hardware.

1. Use 1413 µS/cm standard solution at a known temperature (25 °C ideal).
2. Edit `config.json` → `calibration.ec`:

```json
"ec": {
  "cell_constant": 1.0,
  "ref_voltage": 1.65,
  "ref_temp_c": 25.0
}
```

3. Adjust `cell_constant` until the reported value matches 1413 µS/cm.

### Soil moisture (2-point calibration)

1. Read raw ADC count in dry air → `dry_count`
2. Submerge sensor in water → `wet_count`
3. Edit `config.json` → `calibration.soil`:

```json
"soil": {
  "dry_count": 26000,
  "wet_count": 13000
}
```

---

## Running Desktop Unit Tests

The calibration math can be tested on any desktop Python (no hardware needed):

```bash
python3 firmware/tests/test_calibration.py
```

---

## Recovering a Boot-Looping Pico

If `main.py` crashes before the REPL loads and the device is stuck in a crash loop:

1. Hold **BOOTSEL**, plug in USB → `RPI-RP2` drive appears.
2. Flash the same MicroPython UF2 again.
3. This overwrites the filesystem — your code is gone. Re-flash with `./tools/flash.sh`.

To avoid this: always test new code changes in the REPL (`./tools/repl.sh`) before writing to `main.py`.

---

## GPIO Pinout Reference

Source: `hardware/docs/schematic.md` (v1 board).

| GPIO | Function | Notes |
|------|----------|-------|
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
| GP15 | RELAY2_DRV | K2 via Q3 (BC817) + 1 kΩ R18 (not driven by the firmware yet) |
| GP16 | W4_SIG | Wago W4 (J5), generic digital (e.g. float switch) |
| GP17 | W5_SIG | Wago W5 (J6), generic digital |
| GP18–GP22 | free | J11 solder holes 5–9 |
| GP26–GP28 | free, ADC0–2 | J11 solder holes 10–12 (0–3.3 V analog, e.g. capacitive soil sensor on GP26) |
| RUN | RUN | J11 hole 13 |
