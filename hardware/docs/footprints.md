# KiCad Footprint Reference

Map every BOM line to its KiCad library footprint before starting schematic entry.
Checked against the KiCad **10.0** standard libraries (Sep 2026).
All footprints assigned. Project footprints: `sensor_hub:VEML7700_TT`.
Flags: ⚠ = verify against datasheet before placing; ✗ = DNP v1; **TBD** = not in the KiCad library, project footprint still to be drawn.

Project libraries live next to the project: `kicad/sensor_hub.kicad_sym` (symbols). A project footprint library `kicad/sensor_hub.pretty` will be added for the TBD footprints.

---

## ICs

| Ref | Part | Package | KiCad symbol | KiCad footprint |
|-----|------|---------|--------------|-----------------|
| U1 | Pico WH (SC0919) on sockets | 2× 1×20 THT, 2.54 mm | `MCU_Module:RaspberryPi_Pico_W` | `Module:RaspberryPi_Pico_Common_THT` |
| U2 | ADS1115IDGSR | VSSOP-10 | `Analog_ADC:ADS1115IDGS` | `Package_SO:MSOP-10_3x3mm_P0.5mm` |
| U3 ✗ | LMP91200SD/NOPB | ⚠ open | ⚠ none in KiCad 10 | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` ⚠ |
| U4 | AD8603ARTZ-R2 | TSOT-23-5 | `Amplifier_Operational:AD8603` | `Package_TO_SOT_SMD:TSOT-23-5` (KiCad symbol default) ⚠ |
| U5 | AP2112K-3.3TRG1 | SOT-23-5 | `Regulator_Linear:AP2112K-3.3` | `Package_TO_SOT_SMD:SOT-23-5` |
| U6 | VEML7700-TT | 4-pin, top view | `sensor_hub:VEML7700` (project) | `sensor_hub:VEML7700_TT` (project) |

**U2 note**: DGS suffix = VSSOP-10 (3×3 mm, 0.5 mm pitch). KiCad 10 names this land pattern `MSOP-10_3x3mm_P0.5mm` (same footprint).

**U3 note**: DNP in v1 and slated for replacement by AD5933. KiCad 10 has no LMP91200 symbol, and the package in the old docs (SOIC-14) is unconfirmed — decide whether to keep U3 on the v1 board at all before layout.

**U4 note**: the BOM description said SC70-5; the KiCad AD8603 symbol defaults to TSOT-23-5, which is now used. Confirm against ADI's ordering guide before ordering.

**U6 note**: pinout 1 = SCL, 2 = VDD, 3 = GND, 4 = SDA and pad pattern (4 × 0.7 × 1.6 mm, pitch 1.27 mm, "Top View" layout) taken from Vishay datasheet 84286 Rev. 1.8, p. 1 and p. 10. Pin 1 is marked with a silk dot. The body outline on F.Fab is approximate — the datasheet gives no body-to-pad offset for top-view mounting; check against a real part before placing it near other parts.

---

## Discretes

| Ref | Part | Package | KiCad footprint |
|-----|------|---------|-----------------|
| D1 | BAV99 | SOT-23 | `Package_TO_SOT_SMD:SOT-23` |
| D2, D3 | 1N4148W | SOD-123 | `Diode_SMD:D_SOD-123` |
| Q1, Q3 | BC817-40 | SOT-23 | `Package_TO_SOT_SMD:SOT-23` |
| Q2 | BSS84PXUMA1 | SOT-23 | `Package_TO_SOT_SMD:SOT-23` |
| K1, K2 | Omron G2RL-1-E DC5 | THT relay | `Relay_THT:Relay_SPDT_Omron_G2RL-1-E` (symbol `Relay:G2RL-1-E`) |

**K1/K2 note**: both symbol and footprint are in the KiCad 10 library. Confirm coil pins and COM/NO/NC pin numbers against the Omron datasheet before routing. Add the 2 mm isolation slot (Edge.Cuts) between coil and contact pins on the board.

---

## Passives

| Ref | Value | Package | KiCad footprint |
|-----|-------|---------|-----------------|
| R1–R3, R5–R11, R17, R18 | various | 0603 | `Resistor_SMD:R_0603_1608Metric` |
| R4 | — | — | intentionally unused |
| R15–R16 ✗ | 10 kΩ DNP | 0603 | same — place footprint, do not populate |
| R19–R20 | 100 Ω snubber | 1206 | `Resistor_SMD:R_1206_3216Metric` |
| C1–C2, C6–C12 | 100 nF | 0603 | `Capacitor_SMD:C_0603_1608Metric` |
| C3–C5 ✗ | 100 nF DNP | 0603 | same — place footprint, do not populate |
| C13–C16 | 10 µF | 0805 | `Capacitor_SMD:C_0805_2012Metric` |
| C17–C18 | 1 µF | 0603 | `Capacitor_SMD:C_0603_1608Metric` |
| C19–C20 | 100 nF X2 film | THT box 13×6 mm, 10 mm pitch | `Capacitor_THT:C_Rect_L13.0mm_W6.0mm_P10.00mm_FKS3_FKP3_MKS4` ⚠ verify body size of chosen part |

---

## Connectors

| Ref | Part | Type | KiCad footprint |
|-----|------|------|-----------------|
| J1 | Amphenol 031-6575 | RA BNC | `Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal` (symbol `Connector:Conn_Coaxial`) |
| J2–J6 | Wago 2601-1103 | THT 3-pole 3.5 mm (SELV sensors W1–W5) | `TerminalBlock_WAGO:TerminalBlock_WAGO_2601-1103_1x03_P3.50mm_Horizontal` |
| J7, J10 | Wago 236-403 | THT 3-pole 5 mm, mains (W6/W7), 24 A IEC / 300 V UL | `TerminalBlock_WAGO:TerminalBlock_WAGO_236-403_1x03_P5.00mm_45Degree` |
| J8 | Phoenix PT 1.5/4-3.5-H | THT 4-pin 3.5 mm | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal` |
| J9 | Phoenix PT 1.5/2-5-H | THT 2-pin 5 mm | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-5.0-H_1x02_P5.00mm_Horizontal` |
| HDR1 | PEC04SAAN | 2.54 mm 1×4 | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` |
| J11 | — (DNP, holes only) | 2.54 mm 2×8 | `Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical` |
