# KiCad Footprint Reference

Map every BOM line to its KiCad library footprint before starting schematic entry.
Checked against the KiCad **10.0** standard libraries (Sep 2026).
All footprints assigned. J1 was changed from Amphenol 031-6575 (an isolated BNC whose footprint splits shield and shell into separate pads) to TE 1-1478035-0 (all shield pads = pad 2). Project footprints: `sensor_hub:VEML7700_TT`.
Flags: ⚠ = verify against datasheet before placing; ✗ = DNP v1; **TBD** = not in the KiCad library, project footprint still to be drawn.

Project libraries live next to the project: `kicad/sensor_hub.kicad_sym` (symbols). A project footprint library `kicad/sensor_hub.pretty` will be added for the TBD footprints.

---

## ICs

| Ref | Part | Package | KiCad symbol | KiCad footprint |
|-----|------|---------|--------------|-----------------|
| U1 | Pico WH (SC0919) on sockets | 2× 1×20 THT, 2.54 mm | `MCU_Module:RaspberryPi_Pico_W` | `Module:RaspberryPi_Pico_Common_THT` |
| U2 | ADS1115IDGSR | VSSOP-10 | `Analog_ADC:ADS1115IDGS` | `Package_SO:MSOP-10_3x3mm_P0.5mm` |
| U4 | AD8603AUJZ | TSOT-23-5 | `Amplifier_Operational:AD8603` | `Package_TO_SOT_SMD:TSOT-23-5` |
| U5 | AP2112K-3.3TRG1 | SOT-23-5 | `Regulator_Linear:AP2112K-3.3` | `Package_TO_SOT_SMD:SOT-23-5` |
| U6 | VEML7700-TT | 4-pin, top view | `sensor_hub:VEML7700` (project) | `sensor_hub:VEML7700_TT` (project) |

**U2 note**: DGS suffix = VSSOP-10 (3×3 mm, 0.5 mm pitch). KiCad 10 names this land pattern `MSOP-10_3x3mm_P0.5mm` (same footprint).

**U3 / R15 / R16 / C3–C5**: EC front-end (LMP91200) removed from v1 (Sep 2026); designators retired.

**U4 note**: TSOT-23-5 = order code AD8603AUJZ (JLCPCB/LCSC C14937, AD8603AUJZ-REEL7). The old BOM entry "AD8603ARTZ-R2" is not a valid ADI part number.

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
| R19–R20 | 100 Ω snubber | 1206 | `Resistor_SMD:R_1206_3216Metric` |
| C1–C2, C6–C12 | 100 nF | 0603 | `Capacitor_SMD:C_0603_1608Metric` |
| C13–C16 | 10 µF | 0805 | `Capacitor_SMD:C_0805_2012Metric` |
| C17–C18 | 1 µF | 0603 | `Capacitor_SMD:C_0603_1608Metric` |
| C19–C20 | 100 nF X2 film | THT box 13×6 mm, 10 mm pitch | `Capacitor_THT:C_Rect_L13.0mm_W6.0mm_P10.00mm_FKS3_FKP3_MKS4` ⚠ verify body size of chosen part |

---

## Connectors

| Ref | Part | Type | KiCad footprint |
|-----|------|------|-----------------|
| J1 | TE 1-1478035-0 | RA BNC, 4 pins (1 = center, all others = shield) | `Connector_Coaxial:BNC_TEConnectivity_1478035_Horizontal` (symbol `Connector:Conn_Coaxial`) |
| J2–J6 | Wago 2601-1103 | THT 3-pole 3.5 mm (SELV sensors W1–W5) | `TerminalBlock_WAGO:TerminalBlock_WAGO_2601-1103_1x03_P3.50mm_Horizontal` |
| J7, J10 | Wago 236-403 | THT 3-pole 5 mm, mains (W6/W7), 24 A IEC / 300 V UL | `TerminalBlock_WAGO:TerminalBlock_WAGO_236-403_1x03_P5.00mm_45Degree` |
| J8 | Wago 2601-1104 | THT 4-pole push-in 3.5 mm | `TerminalBlock_WAGO:TerminalBlock_WAGO_2601-1104_1x04_P3.50mm_Horizontal` |
| J9 | Wago 2601-1102 | THT 2-pole push-in 3.5 mm | `TerminalBlock_WAGO:TerminalBlock_WAGO_2601-1102_1x02_P3.50mm_Horizontal` |
| HDR1 | PEC04SAAN | 2.54 mm 1×4 | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` |
| J11 | — (DNP, holes only) | 2.54 mm 2×8 | `Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical` |

---

## Mechanical

| Ref | Part | KiCad footprint | Notes |
|-----|------|-----------------|-------|
| H1–H4 | M3 board mounting | `MountingHole:MountingHole_3.2mm_M3` | corners, no copper |
| H5–H7 | M2 light-pipe holder | `MountingHole:MountingHole_2.2mm_M2` | around U6 on r = 7 mm, no copper, reference hidden |

## 3D models

KiCad has no 3D models for the Wago terminals (2601-1102/-1103/-1104, 236-403), the G2RL relay (SPDT) and the TE BNC. `tools/place_pcb.py` points those footprints at vendor STEP files in `kicad/3d/` (with rotation/offset worked out from the pin positions in the STEP data). The STEP files are not in git (vendor terms, public repo) — download list in `kicad/3d/README.md`. U6 (VEML7700, project footprint) has no 3D model yet.
