# KiCad Footprint Reference

Map every BOM line to its KiCad library footprint before starting schematic entry.
Checked against the KiCad **10.0** standard libraries (Sep 2026).
Flags: ⚠ = verify against datasheet before placing; ✗ = DNP v1; **TBD** = not in the KiCad library, project footprint still to be drawn.

Project libraries live next to the project: `kicad/sensor_hub.kicad_sym` (symbols). A project footprint library `kicad/sensor_hub.pretty` will be added for the TBD footprints.

---

## ICs

| Ref | Part | Package | KiCad symbol | KiCad footprint |
|-----|------|---------|--------------|-----------------|
| U1 | Pico W SC0918 | Castellated | `MCU_Module:RaspberryPi_Pico_W` | `Module:RaspberryPi_Pico_W_SMD` |
| U2 | ADS1115IDGSR | VSSOP-10 | `Analog_ADC:ADS1115IDGS` | `Package_SO:MSOP-10_3x3mm_P0.5mm` |
| U3 ✗ | LMP91200SD/NOPB | ⚠ open | ⚠ none in KiCad 10 | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` ⚠ |
| U4 | AD8603ARTZ-R2 | SC70-5 | `Amplifier_Operational:AD8603` | `Package_TO_SOT_SMD:SOT-23-5` ⚠ |
| U5 | AP2112K-3.3TRG1 | SOT-23-5 | `Regulator_Linear:AP2112K-3.3` | `Package_TO_SOT_SMD:SOT-23-5` |
| U6 | VEML7700-TT | 4-pin 6.8×2.35 mm ⚠ | `sensor_hub:VEML7700` (project) | **TBD** |

**U2 note**: DGS suffix = VSSOP-10 (3×3 mm, 0.5 mm pitch). KiCad 10 names this land pattern `MSOP-10_3x3mm_P0.5mm` (same footprint).

**U3 note**: DNP in v1 and slated for replacement by AD5933. KiCad 10 has no LMP91200 symbol, and the package in the old docs (SOIC-14) is unconfirmed — decide whether to keep U3 on the v1 board at all before layout.

**U4 note**: the BOM description says SC70-5 but the footprint is SOT-23-5. Confirm the AD8603ARTZ package in ADI's ordering guide and use `Package_TO_SOT_SMD:SOT-23-5` or `Package_TO_SOT_SMD:SOT-353_SC-70-5` accordingly.

**U6 note**: the old docs listed a 2×2 mm ODFN-6. The VEML7700-TT is believed to be a 4-pin 6.8 × 2.35 mm package (the 2×2 mm variant is the VEML6030). The project symbol uses 1 = SCL, 2 = VDD, 3 = GND, 4 = SDA — **verify pin numbers and package against the Vishay datasheet** before drawing the footprint.

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
| C19–C20 | 100 nF X2 film | THT box | `Capacitor_THT:C_Rect_*` matching the chosen X2 part's pitch — **TBD** until part chosen |

---

## Connectors

| Ref | Part | Type | KiCad footprint |
|-----|------|------|-----------------|
| J1 | TE 5-1634500-1 | RA BNC | **TBD** — not in KiCad 10. Library alternatives: `Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal`, `BNC_TEConnectivity_1478035_Horizontal` (symbol `Connector:Conn_Coaxial`) |
| J2–J6 | Wago 2060-453 | 3-pin (SELV sensors W1–W5) | **TBD** — not in KiCad 10 |
| J7, J10 | Wago 2604-1103 | THT 3-pole 5 mm, mains (W6/W7) | **TBD** — not in KiCad 10. Library alternative: `TerminalBlock_WAGO:TerminalBlock_WAGO_236-403_1x03_P5.00mm_45Degree` if the 236 series ratings fit ⚠ |
| J8 | Phoenix PT 1.5/4-3.5-H | THT 4-pin 3.5 mm | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal` |
| J9 | Phoenix PT 1.5/2-5-H | THT 2-pin 5 mm | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-5.0-H_1x02_P5.00mm_Horizontal` |
| HDR1 | PEC04SAAN | 2.54 mm 1×4 | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` |
