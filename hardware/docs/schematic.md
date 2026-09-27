# Schematic — Pico W Sensor Hub

Use this as the reference for KiCad entry. Every connection in `bom.csv` traces back here.

**Design decision (Aug 2026):** Minimum two on-board relays (K1 + K2). The board must support at least two independent actuator channels (pump, valve, etc.) without external modules. Future variants can add more relays; this is the baseline.

**Also required:** Guard ring on the pH high-Z node + RC snubbers on both relay contact sets for EMC.

**Connector decision:** Both relay contact sets use mains-rated Wago 3-pin connectors (W6 = Relay 1, W7 = Relay 2) at the bottom-right corner, inside the MAINS zone and separated from sensor ports W1–W5. No separate screw terminals next to the relays.

**Mains decision (Sep 2026):** Relay contacts are rated for **230 VAC, 5 A per channel** (anything up to 48 V DC is covered too). Relays are Omron G2RL-1-E with reinforced coil–contact insulation. All relay contact nets belong to the `MAINS` netclass and need ≥ 8 mm creepage/clearance to every other net — see `pcb_guidelines.md` → Relay Zone Rules.

---

## System Block Diagram

```
USB-C 5V (power bank)
│
├─ VSYS ──────────────────────────────── Pico W VSYS
│                                         K1 + K2 coil (+)
│                                         AP2112K IN ── AP2112K OUT (Analog 3V3) ─── ADS1115, AD8603, VREF divider, NTC pullup
│
└─ Pico W 3V3(OUT)
     └─ Digital 3V3 ─── VEML7700, DS18B20, DHT22, PIR, LMP91200, pull-ups

(AP2112K is fed from VSYS, not from 3V3_DIG — a 3.3 V LDO cannot regulate from a 3.3 V input.)

I2C Bus (GP2/GP3, 4.7kΩ pullups to 3V3_DIG)
  ├── ADS1115  addr 0x48 (ADDR pin → GND)
  └── VEML7700 addr 0x10 (fixed; no ADDR pin)

SPI Bus (GP4/GP5/GP6/GP7)
  └── LMP91200 (EC analog frontend)

1-Wire (GP8, 4.7kΩ pullup to 3V3_DIG)
  └── DS18B20 temperature sensor (Wago port 1)

GPIO direct:
  GP9  ── DHT22 data (Wago port 2, 10kΩ pullup)
  GP10 ── Relay 1 driver (→ Q1 BC817 base)
  GP11 ── PIR output (Wago port 3, 10kΩ pullup, wake IRQ)
  GP12 ── PIR MOSFET gate (power gate for PIR)
  GP13 ── EC excitation PWM A → RC filter → LMP91200
  GP14 ── EC excitation PWM B (complement) → RC filter → LMP91200
  GP15 ── Relay 2 driver (→ Q3 BC817 base)
  GP16 ── Wago port 4 signal (generic)
  GP17 ── Wago port 5 signal (generic)
```

---

## Net List

### Power Nets

| Net | Source | Destinations |
|-----|--------|-------------|
| VSYS | USB-C VBUS | Pico W VSYS, K1 coil (+), K2 coil (+), AP2112K VIN |
| 3V3_DIG | Pico W 3V3(OUT) | VEML7700 VCC, DS18B20 VDD, DHT22 VDD, LMP91200 VDD, BC817 pull, I2C pullup tops |
| 3V3_ANA | AP2112K VOUT | ADS1115 VDD+AVDD, AD8603 VS+, VREF_TOP (pH divider), NTC pullup top |
| GND_DIG | Pico W GND | All digital IC GND, Q1/Q3 emitters, K1/K2 coil (–) via collectors |
| GND_ANA | ADS1115 AGND | AD8603 VS–, pH divider bottom, NTC low side |
| VREF_MID | pH divider midpoint | BNC shield, AD8603 IN– via 100kΩ, C_vref 100nF to GND_ANA |

Single-point AGND/DGND join at the ADS1115 GND pin, implemented as net tie **NT1** (GND_ANA ↔ GND). Optional: replace with 0Ω link or ferrite bead.
The AP2112K (U5) GND and its input caps C14/C17/C8 sit on GND_ANA; the VSYS entry caps C13/C11 sit on GND.
Pico W AGND (pin 33) is tied to GND (Pico ADC unused). KiCad ERC flags this as "power output to power output" — expected, can be excluded.

---

## pH Analog Frontend + Guard Ring

```
BNC_CENTER ──── R1(10MΩ) ──── NODE_A ──── AD8603 IN+
                                │
                             BAV99 (SOT-23)
                                │ Pin3 (common) = NODE_A
                                │ Pin1 (anode)  → GND_ANA
                                │ Pin2 (cathode) → 3V3_ANA

3V3_ANA ── R2(100kΩ) ── NODE_VREF ── R3(100kΩ) ── GND_ANA
                              │
                           C1(100nF) → GND_ANA      [filter cap]

AD8603 OUT ──── AD8603 IN– (direct, unity-gain voltage follower)
AD8603 OUT ──── ADS1115 AIN0

BNC_SHIELD ──── NODE_VREF   (reference electrode biased at 1.65V)

AD8603 VS+  ──── 3V3_ANA + C2(100nF) to GND_ANA
AD8603 VS–  ──── GND_ANA
```

**Design decision (Sep 2026):** the former R4 (100 kΩ from NODE_VREF to AD8603 IN–) is removed. With IN– tied to OUT it only injected a small error current into the output. The reference offset comes from the BNC shield sitting on NODE_VREF. Reference R4 is intentionally unused.

**Transfer function**: pH electrode output ±414 mV (pH 0–14 at 25°C) is offset by VREF = 1.65V.
ADS1115 AIN0 sees 1.236V (pH 0) to 2.064V (pH 14). Use ±2.048V PGA setting.

### Guard-Ring Implementation (mandatory)

NODE_A (the net between R1 and AD8603 IN+) is a high-impedance node. Any surface leakage on the PCB corrupts the pH reading.

**Layout rule:**
- Surround the entire NODE_A trace with a continuous copper guard ring on **both** top and bottom layers.
- Connect the guard ring **only** to AD8603 OUT (the unity-gain buffered output).
- Do **not** connect the guard to GND or to any other net.
- Keep the guard ring as close as practical to the NODE_A trace (typically 0.2–0.5 mm gap).
- No other traces may cross the guarded area without a keep-out.

This makes the potential difference between NODE_A and the surrounding copper almost zero → leakage current becomes negligible.

---

## EC Analog Frontend (LMP91200)

> **DNP v1** — LMP91200 is EOL/unavailable (May 2026). U3 + R15 + R16 + C3 + C4 + C5
> are all DNP. J8 pins 1–2 (WE/RE) are unconnected. J8 pins 3–4 (NTC) remain active.
> Footprint retained; plan is AD5933 impedance converter for v2.

```
GP13 (PWM A) ── R15(10kΩ) ── C3(100nF) to GND ── LMP91200 excitation IN+
GP14 (PWM B) ── R16(10kΩ) ── C4(100nF) to GND ── LMP91200 excitation IN–

LMP91200 ── SPI ── Pico W (GP4 MISO, GP5 MOSI, GP6 SCK, GP7 CS)
LMP91200 VDD ──── 3V3_DIG + C5(100nF) to GND_DIG
LMP91200 GND ──── GND_DIG

EC 4-wire terminal (J8, Phoenix Contact 4-pin):
  Pin 1 (White) ── LMP91200 Working Electrode (WE)
  Pin 2 (Yellow) ── LMP91200 Reference Electrode (RE)
  Pin 3 (Red)   ── NTC thermistor signal → NODE_NTC
  Pin 4 (Black) ── NTC GND → GND_ANA
```

### NTC Thermistor Divider

```
3V3_ANA ── R7(10kΩ) ── NODE_NTC ── J8 Pin3 (NTC hot side)
                           │
                        C6(100nF) to GND_ANA    [anti-alias]
                           │
                        ADS1115 AIN1

J8 Pin4 (NTC GND) ── GND_ANA
```

---

## ADS1115 Channel Assignments

| Channel | Signal | Sensor |
|---------|--------|--------|
| AIN0 | pH buffer output (AD8603 OUT) | pH electrode |
| AIN1 | NTC divider (NODE_NTC) | EC sensor temperature |
| AIN2 | Soil moisture analog out (Wago port 4 or 5) | Capacitive soil sensor |
| AIN3 | Spare | — |

ADS1115 I2C address: 0x48 (ADDR pin → GND_DIG)

---

## Relay Drivers + Contact EMC Snubbers (two channels)

Both relays are SPDT PCB-mount **Omron G2RL-1-E DC5** (5 V coil ≈ 80 mA from VSYS, contacts 16 A 250 VAC, 5 kVAC reinforced coil–contact insulation). Do not substitute a relay with only basic coil–contact insulation (e.g. Songle SRD series) — the SELV side connects to probes in water. Contact nets (COM/NO/NC, snubber midpoints, W6/W7) are in netclass `MAINS`: ≥ 8 mm creepage and clearance to any coil, logic or sensor net.

### Relay 1 (K1) — GP10

```
GP10 ── R8(1kΩ) ── Q1(BC817) BASE
Q1 EMITTER ──────── GND_DIG
Q1 COLLECTOR ─┬──── K1 coil (–)
              └──── D2(1N4148) cathode
K1 coil (+) ──┴──── D2(1N4148) anode ──── VSYS

K1 COM ─── W6 (Wago 6) pin 1
K1 NO  ─── W6 (Wago 6) pin 2
K1 NC  ─── W6 (Wago 6) pin 3

# Contact EMC snubber (across the switched path)
K1 COM ── R19(100Ω) ── C19(100nF) ── K1 NO
```

### Relay 2 (K2) — GP15

```
GP15 ── R18(1kΩ) ── Q3(BC817) BASE
Q3 EMITTER ──────── GND_DIG
Q3 COLLECTOR ─┬──── K2 coil (–)
              └──── D3(1N4148) cathode
K2 coil (+) ──┴──── D3(1N4148) anode ──── VSYS

K2 COM ─── W7 (Wago 7) pin 1
K2 NO  ─── W7 (Wago 7) pin 2
K2 NC  ─── W7 (Wago 7) pin 3

# Contact EMC snubber
K2 COM ── R20(100Ω) ── C20(100nF) ── K2 NO
```

**Snubber notes:**
- Series RC across COM–NO suppresses arcing and EMI when switching inductive loads (pumps, solenoids, valves).
- C19/C20 are **X2-rated film capacitors (100 nF, 275 VAC)** because the contacts may switch 230 VAC. R19/R20 are 1206 (≥ 200 V working voltage), not 0603.
- Place the snubber components as close as possible to the relay contact pins, inside the MAINS zone.
- At 230 V / 50 Hz the snubber passes ≈ 7 mA with the contact open. For LED lamps or small contactor coils that react to this, leave that channel's snubber unpopulated.
- Each channel must be protected upstream by a fuse/MCB ≤ 6 A (installation side).

---

## Wago / Terminal Ports

| Port | Pin 1 | Pin 2 | Pin 3 | Default sensor / function |
|------|-------|-------|-------|---------------------------|
| W1 (J2) | 3V3_DIG | GND_DIG | GP8 (1-Wire) | DS18B20 temperature |
| W2 (J3) | 3V3_DIG | GND_DIG | GP9 (DHT data) | DHT22 temp+humidity |
| W3 (J4) | 3V3_DIG | GND_DIG | GP11 (PIR out) | PIR motion |
| W4 (J5) | 3V3_DIG | GND_DIG | GP16 | Generic / soil moisture signal |
| W5 (J6) | 3V3_DIG | GND_DIG | GP17 | Generic |
| W6 (J7) | K1 COM | K1 NO | K1 NC | Relay 1 SPDT contacts — **MAINS, 230 VAC / 5 A** |
| W7 (J10) | K2 COM | K2 NO | K2 NC | Relay 2 SPDT contacts — **MAINS, 230 VAC / 5 A** |
| J8      | WE | RE | NTC+ | NTC– | EC 4-wire sensor |

All actuator and sensor connections use push-in Wago terminals for a consistent interface. W1–W5 are SELV sensor ports (Wago 2601-1103, 3.5 mm); W6/W7 are mains-rated 3-pole THT terminals (Wago 236-403, 5 mm, 2.5 mm²) in the separate MAINS zone.

**PIR power gate**: Q2 (BSS84, SOT-23 P-channel MOSFET) controlled by GP12 switches the 3V3 supply to the PIR on Wago port 3. This avoids the 50–65 mA PIR standby current during sleep.
- Source → 3V3_DIG, Drain → PIR VCC (Wago port 3 pin 1), Gate → GP12
- R17 (10 kΩ) pulls gate to 3V3_DIG so FET is OFF (PIR off) when GP12 is floating at boot
- GP12 LOW = Vgs −3.3 V = FET ON; GP12 HIGH = Vgs 0 V = FET OFF

---

## Decoupling Summary

| Location | Cap value | Refs | Notes |
|----------|-----------|------|-------|
| VSYS entry (J9) | 10 µF + 100 nF | C13 + C11 | Before anything else |
| AP2112K input (VSYS) | 10 µF + 1 µF + 100 nF | C14 + C17 + C8 | |
| AP2112K output (3V3_ANA) | 10 µF + 1 µF + 100 nF | C15 + C18 + C12 | Per datasheet |
| ADS1115 VDD | 10 µF + 100 nF | C16 + C7 | AVDD and VDD pins |
| AD8603 VS+ | 100 nF | C2 | Within 0.5 mm of pin |
| VEML7700 VDD | 100 nF | C9 | |
| LMP91200 VDD | 100 nF | C5 (DNP) | |
| VREF_MID | 100 nF to GND_ANA | C1 | Filters virtual mid-rail |
| NTC node | 100 nF to GND_ANA | C6 | Anti-alias |
| Relay coils (VSYS at K1/K2) | 100 nF | C10 | Local decoupling next to the coils |
| BC817 collector traces | — | — | No cap; keep traces short |
| Relay contact snubbers | 100 nF X2 | C19 / C20 | Across COM–NO of each relay, series with R19 / R20 100 Ω |

---

## Reference Designators (master list)

Single source for every reference. KiCad schematic, `bom.csv` and `footprints.md` must match this table.

| Ref | Value | Function |
|-----|-------|----------|
| U1 | Pico W | MCU module |
| U2 | ADS1115IDGSR | 16-bit ADC, I2C 0x48 |
| U3 | LMP91200 | EC front-end — **DNP v1** |
| U4 | AD8603 | pH unity-gain buffer |
| U5 | AP2112K-3.3 | 3V3_ANA LDO, input from VSYS |
| U6 | VEML7700 | Ambient light, I2C 0x10 |
| J1 | BNC | pH probe input (shield → NODE_VREF) |
| J2–J6 | Wago 3-pin | Sensor ports W1–W5 (SELV) |
| J7 | Wago 3-pole mains | W6 = Relay 1 COM/NO/NC |
| J8 | Phoenix 4-pin | EC probe (pins 3–4 NTC active in v1) |
| J9 | Phoenix 2-pin | VSYS + GND input |
| J10 | Wago 3-pole mains | W7 = Relay 2 COM/NO/NC |
| HDR1 | 1×4 header | Debug UART0 (GP0 TX, GP1 RX, GND, 3V3) |
| K1, K2 | G2RL-1-E DC5 | Relays 1 and 2 |
| Q1, Q3 | BC817-40 | Relay 1 / Relay 2 coil drivers |
| Q2 | BSS84 | PIR power gate |
| D1 | BAV99 | pH input clamp (pin 3 common → NODE_A) |
| NT1 | Net tie | Single-point join GND_ANA ↔ GND at ADS1115 |
| D2, D3 | 1N4148W | Relay 1 / Relay 2 flyback |
| R1 | 10 MΩ | pH series input (BNC center → NODE_A) |
| R2, R3 | 100 kΩ | VREF divider top / bottom |
| R4 | — | Intentionally unused (removed Sep 2026) |
| R5 | 4.7 kΩ | 1-Wire pull-up GP8 → 3V3_DIG |
| R6 | 10 kΩ | DHT22 pull-up GP9 → 3V3_DIG |
| R7 | 10 kΩ | NTC pull-up 3V3_ANA → NODE_NTC |
| R8 | 1 kΩ | Q1 base (GP10) |
| R9 | 10 kΩ | PIR output pull-up GP11 → 3V3_DIG |
| R10, R11 | 4.7 kΩ | I2C pull-ups SDA/SCL → 3V3_DIG |
| R15, R16 | 10 kΩ | EC PWM RC filter — **DNP v1** |
| R17 | 10 kΩ | Q2 gate pull-up |
| R18 | 1 kΩ | Q3 base (GP15) |
| R19, R20 | 100 Ω 1206 | Relay 1 / Relay 2 snubber |
| C1–C20 | see Decoupling Summary | C3, C4, C5 DNP v1 |
