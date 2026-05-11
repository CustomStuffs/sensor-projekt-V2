#!/usr/bin/env python3
"""
Generate KiCad 8 schematic skeleton for Pico W Sensor Hub.

Writes hardware/kicad/sensor_hub.kicad_sch with every BOM component
placed, footprints set, and DNP flags applied.  lib_symbols is left
empty intentionally — KiCad resolves symbols on first open:

    Tools > Update Symbols from Library   (say "yes" to all)

Then wire connections following hardware/docs/schematic.md.
Two symbols may need a manual library search:
  U3  LMP91200  — try Sensor:LMP91200 or create generic IC (DNP anyway)
  U6  VEML7700  — try Sensor_Optical:VEML7700 or create generic 6-pin IC

Usage:
    python3 hardware/tools/generate_schematic.py
"""

import hashlib
import uuid
from pathlib import Path

HERE   = Path(__file__).parent
OUTPUT = HERE.parent / "kicad" / "sensor_hub.kicad_sch"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid(seed: str) -> str:
    """Deterministic UUID-v4-shaped string from a seed (reproducible output)."""
    raw = hashlib.md5(seed.encode()).digest()
    return str(uuid.UUID(bytes=raw))


def sym(lib_id, ref, value, footprint, x, y, angle=0, dnp=False, datasheet="~"):
    """Return a symbol instance block."""
    d   = "yes" if dnp else "no"
    rx  = round(x + 2.54, 2)
    ry  = round(y - 2.54, 2)
    vx  = round(x + 2.54, 2)
    vy  = round(y + 2.54, 2)
    return (
        f'\t(symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {angle}) (unit 1)\n'
        f'\t\t(in_bom yes) (on_board yes) (dnp {d})\n'
        f'\t\t(uuid "{_uid(ref)}")\n'
        f'\t\t(property "Reference" "{ref}" (at {rx} {ry} {angle})\n'
        f'\t\t\t(effects (font (size 1.27 1.27)))\n'
        f'\t\t)\n'
        f'\t\t(property "Value" "{value}" (at {vx} {vy} {angle})\n'
        f'\t\t\t(effects (font (size 1.27 1.27)))\n'
        f'\t\t)\n'
        f'\t\t(property "Footprint" "{footprint}" (at {x:.2f} {y:.2f} {angle})\n'
        f'\t\t\t(effects (font (size 1.27 1.27)) hide)\n'
        f'\t\t)\n'
        f'\t\t(property "Datasheet" "{datasheet}" (at {x:.2f} {y:.2f} {angle})\n'
        f'\t\t\t(effects (font (size 1.27 1.27)) hide)\n'
        f'\t\t)\n'
        f'\t)'
    )


def note(text, x, y, bold=False):
    """Floating text annotation on the schematic."""
    style = " bold" if bold else ""
    return (
        f'\t(text "{text}" (at {x:.2f} {y:.2f} 0)\n'
        f'\t\t(effects (font (size 1.5 1.5){style}))\n'
        f'\t\t(uuid "{_uid("txt_" + text[:20] + str(x))}")\n'
        f'\t)'
    )


# ---------------------------------------------------------------------------
# Footprint shortcuts
# ---------------------------------------------------------------------------
R      = "Resistor_SMD:R_0603_1608Metric"
C_0603 = "Capacitor_SMD:C_0603_1608Metric"
C_0805 = "Capacitor_SMD:C_0805_2012Metric"
SOT23  = "Package_TO_SOT_SMD:SOT-23"
SOT235 = "Package_TO_SOT_SMD:SOT-23-5"

# ---------------------------------------------------------------------------
# Component list  —  A3 sheet (420 × 297 mm)
# Zones: Analog x=18-115 | EC(DNP) x=125-188 | Digital x=200-330
#        PIR x=338-368 | Relay x=373-418 | Connectors y=228-258
# Spacing: passives ~18 mm apart, ICs ~30 mm, Pico W isolated at right
# ---------------------------------------------------------------------------
COMPONENTS = [

    # ── ANALOG ZONE ──────────────────────────────────────────────────────────
    sym("Connector_Coaxial:BNC_Jack",
        "J1", "5-1634500-1",
        "Connector_Coaxial:BNC_TE-Connectivity_1-1634500-1_Horizontal",
        18, 75),

    sym("Device:R", "R1", "10M",  R, 42, 68),
    sym("Device:R", "R2", "10M",  R, 42, 88),

    sym("Diode:BAV99",          "D1", "BAV99",          SOT23,  65, 75),
    sym("Amplifier_Operational:AD8603", "U4", "AD8603ARTZ-R2", SOT235, 92, 75),
    sym("Device:C", "C2", "100nF", C_0603, 115, 68),   # AD8603 VS+

    # VREF divider + AD8603 summing node (100 kΩ × 4 per BOM)
    sym("Device:R", "R3", "100k", R, 48, 115),
    sym("Device:R", "R4", "100k", R, 70, 115),
    sym("Device:R", "R5", "100k", R, 48, 133),
    sym("Device:R", "R6", "100k", R, 70, 133),
    sym("Device:C", "C1", "100nF", C_0603, 95, 120),   # VREF_MID filter

    # LDO + bulk caps
    sym("Regulator_Linear:AP2112K-3.3", "U5", "AP2112K-3.3TRG1", SOT235, 35, 168),
    sym("Device:C", "C14", "10uF",  C_0805, 18,  180),
    sym("Device:C", "C15", "10uF",  C_0805, 38,  180),
    sym("Device:C", "C17", "1uF",   C_0603, 58,  180),
    sym("Device:C", "C18", "1uF",   C_0603, 78,  180),

    # ── EC ZONE  (all DNP v1) ─────────────────────────────────────────────────
    sym("Sensor:LMP91200",
        "U3", "LMP91200SD/NOPB",
        "Package_SO:SOIC-14_3.9x8.65mm_P1.27mm",
        155, 168, dnp=True),

    sym("Device:R", "R15", "10k", R,       125, 155, dnp=True),
    sym("Device:R", "R16", "10k", R,       125, 173, dnp=True),
    sym("Device:C", "C3",  "100nF", C_0603, 140, 155, dnp=True),
    sym("Device:C", "C4",  "100nF", C_0603, 140, 173, dnp=True),
    sym("Device:C", "C5",  "100nF", C_0603, 168, 145, dnp=True),

    # ── DIGITAL ZONE ──────────────────────────────────────────────────────────
    sym("Sensor_Optical:VEML7700",
        "U6", "VEML7700-TT",
        "Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.65mm_EP0.7x1.6mm",
        205, 52),
    sym("Device:C", "C9", "100nF", C_0603, 228, 52),   # VEML VCC

    sym("Analog_ADC:ADS1115xDGS",
        "U2", "ADS1115IDGSR",
        "Package_SO:VSSOP-10_3x3mm_P0.5mm",
        205, 108),
    sym("Device:R", "R10", "4k7", R,       192, 80),   # I2C SDA pullup
    sym("Device:R", "R11", "4k7", R,       215, 80),   # I2C SCL pullup
    sym("Device:C", "C7",  "100nF", C_0603, 192, 120), # ADS VDD
    sym("Device:C", "C8",  "100nF", C_0603, 215, 120), # ADS AVDD
    sym("Device:C", "C6",  "100nF", C_0603, 240, 120), # NTC AIN1 anti-alias

    # Misc 10 kΩ: NTC pullup, DHT pullup, PIR pullup, SPI-idle × 4
    sym("Device:R", "R7",  "10k", R, 205, 188),
    sym("Device:R", "R19", "10k", R, 223, 188),
    sym("Device:R", "R20", "10k", R, 241, 188),
    sym("Device:R", "R21", "10k", R, 259, 188),
    sym("Device:R", "R22", "10k", R, 277, 188),

    # Pico W — placed right of ADS1115, plenty of clearance
    sym("MCU_RaspberryPi_RP2040:RaspberryPi_PicoW",
        "U1", "PicoW",
        "MicrocontrollerBoard:RaspberryPi_PicoW",
        305, 138),
    sym("Device:C", "C13", "10uF",  C_0805, 258, 60),
    sym("Device:C", "C11", "100nF", C_0603, 275, 60),
    sym("Device:C", "C12", "100nF", C_0603, 292, 60),

    # ── PIR POWER GATE ────────────────────────────────────────────────────────
    sym("Transistor_FET:BSS84",
        "Q2", "BSS84PXUMA1",
        SOT23,
        350, 128),
    sym("Device:R", "R17", "10k", R, 338, 112),        # gate pullup

    # ── RELAY ZONE ────────────────────────────────────────────────────────────
    sym("Device:D",          "D2", "1N4148W",       "Diode_SMD:D_SOD-123", 380, 65),
    sym("Device:Relay_SPDT", "K1", "SRD-05VDC-SL-C",
        "Relay_THT:Relay_SPDT_Songle_SRD-xxVDC-SL-C", 400, 95),
    sym("Transistor_BJT:BC817", "Q1", "BC817-40",   SOT23,  373, 118),
    sym("Device:R", "R8",  "1k", R, 358, 118),         # relay base drive
    sym("Device:R", "R12", "1k", R, 373, 138),
    sym("Device:R", "R13", "1k", R, 390, 138),
    sym("Device:R", "R14", "1k", R, 407, 138),
    sym("Device:C", "C16", "10uF",  C_0805, 415, 80),
    sym("Device:C", "C10", "100nF", C_0603, 415, 100),

    # ── CONNECTORS  (45 mm spacing) ───────────────────────────────────────────
    sym("Connector_Generic:Conn_01x03", "J2", "Wago-DS18B20",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        18, 248),
    sym("Connector_Generic:Conn_01x03", "J3", "Wago-DHT22",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        63, 248),
    sym("Connector_Generic:Conn_01x03", "J4", "Wago-PIR",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        108, 248),
    sym("Connector_Generic:Conn_01x03", "J5", "Wago-GP16",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        153, 248),
    sym("Connector_Generic:Conn_01x03", "J6", "Wago-GP17",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        198, 248),
    sym("Connector_Generic:Conn_01x03", "J7", "Wago-Relay",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        398, 248),

    sym("Connector_Generic:Conn_01x04", "J8", "Phoenix-EC4pin",
        "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5_4-3,5-H_1x04_P3.50mm_Horizontal",
        150, 228),
    sym("Connector_Generic:Conn_01x02", "J9", "Phoenix-Power",
        "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5_2-5,0-H_1x02_P5.00mm_Horizontal",
        298, 248),
    sym("Connector_Generic:Conn_01x04", "HDR1", "Debug-UART",
        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        253, 248),
]

NOTES = [
    note("ANALOG ZONE",                                        18,  40, bold=True),
    note("EC ZONE  (DNP v1 — AD5933 redesign for v2)",        125, 138, bold=True),
    note("DIGITAL ZONE",                                       200,  35, bold=True),
    note("PIR GATE",                                           334,  95, bold=True),
    note("RELAY ZONE",                                         368,  45, bold=True),
    note("CONNECTORS",                                          18, 232, bold=True),
    note("After opening: Tools > Update Symbols from Library",  18, 270),
    note("Wire per hardware/docs/schematic.md",                 18, 278),
    note("U3 (LMP91200) + U6 (VEML7700) may need manual symbol search", 18, 286),
]

# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

HEADER = """\
(kicad_sch
\t(version 20231120)
\t(generator "eeschema")
\t(generator_version "8.0")
\t(uuid "{sch_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "Pico W Sensor Hub")
\t\t(rev "V1.0")
\t\t(date "2026-05-11")
\t\t(company "sensor_projekt_V2")
\t\t(comment 1 "Wire per hardware/docs/schematic.md")
\t\t(comment 2 "Run Tools > Update Symbols from Library after opening")
\t\t(comment 3 "EC section (U3 R15 R16 C3-C5) is DNP v1")
\t)
\t(lib_symbols)"""

FOOTER = """\
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
\t(embedded_fonts no)
)"""


def generate(output: Path) -> None:
    blocks = [HEADER.format(sch_uuid=_uid("sensor_hub_top_level_sch"))]
    blocks += NOTES
    blocks += COMPONENTS
    blocks.append(FOOTER)
    output.write_text("\n".join(blocks) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(f"  {len(COMPONENTS)} components")
    print()
    print("Next steps:")
    print("  1. Open hardware/kicad/sensor_hub.kicad_pro in KiCad 8")
    print("  2. Tools > Update Symbols from Library  (accept all)")
    print("  3. Wire connections per hardware/docs/schematic.md")
    print("  4. Tools > Annotate Schematic  (if any ? refs remain)")
    print("  5. Inspect > ERC  (fix errors before moving to PCB editor)")


if __name__ == "__main__":
    generate(OUTPUT)
