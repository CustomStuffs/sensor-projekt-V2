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
# Component list   (ref, lib_id, value, footprint, x, y, angle, dnp)
# Coordinates in mm on A3 sheet (420 x 297).
# Zones: Analog x=15-95 | EC(DNP) x=95-165 | Digital x=165-280
#        PIR-gate x=255-285 | Relay x=295-385 | Connectors y=215-260
# ---------------------------------------------------------------------------
COMPONENTS = [

    # ── ANALOG ZONE ─────────────────────────────────────────────────────────
    sym("Connector_Coaxial:BNC_Jack",
        "J1", "5-1634500-1",
        "Connector_Coaxial:BNC_TE-Connectivity_1-1634500-1_Horizontal",
        15, 65),

    sym("Device:R", "R1", "10M", R, 35, 58),
    sym("Device:R", "R2", "10M", R, 35, 72),   # 2nd 10 MΩ per BOM qty=2

    sym("Diode:BAV99",
        "D1", "BAV99",
        SOT23,
        52, 65),

    sym("Amplifier_Operational:AD8603",
        "U4", "AD8603ARTZ-R2",
        SOT235,
        75, 65),

    sym("Regulator_Linear:AP2112K-3.3",
        "U5", "AP2112K-3.3TRG1",
        SOT235,
        35, 108),

    # VREF divider + AD8603 summing (100 kΩ × 4 per BOM)
    sym("Device:R", "R3", "100k", R, 52, 90),
    sym("Device:R", "R4", "100k", R, 67, 90),
    sym("Device:R", "R5", "100k", R, 52, 102),  # BOM qty 4 → extra 100k
    sym("Device:R", "R6", "100k", R, 67, 102),

    sym("Device:C", "C1",  "100nF", C_0603, 83, 90),   # VREF_MID filter
    sym("Device:C", "C2",  "100nF", C_0603, 83, 65),   # AD8603 VS+
    sym("Device:C", "C14", "10uF",  C_0805, 22, 118),  # AP2112K bulk in
    sym("Device:C", "C15", "10uF",  C_0805, 37, 118),  # AP2112K bulk out
    sym("Device:C", "C17", "1uF",   C_0603, 52, 118),  # AP2112K out stab
    sym("Device:C", "C18", "1uF",   C_0603, 65, 118),  # AP2112K in stab

    # ── EC ZONE  (all DNP v1) ────────────────────────────────────────────────
    sym("Sensor:LMP91200",   # search manually if missing; DNP anyway
        "U3", "LMP91200SD/NOPB",
        "Package_SO:SOIC-14_3.9x8.65mm_P1.27mm",
        118, 152, dnp=True),

    sym("Device:R", "R15", "10k", R,  95, 143, dnp=True),  # EC PWM RC A
    sym("Device:R", "R16", "10k", R,  95, 157, dnp=True),  # EC PWM RC B
    sym("Device:C", "C3",  "100nF", C_0603, 106, 143, dnp=True),
    sym("Device:C", "C4",  "100nF", C_0603, 106, 157, dnp=True),
    sym("Device:C", "C5",  "100nF", C_0603, 130, 140, dnp=True),  # LMP VDD

    # ── DIGITAL ZONE ────────────────────────────────────────────────────────
    sym("Analog_ADC:ADS1115xDGS",
        "U2", "ADS1115IDGSR",
        "Package_SO:VSSOP-10_3x3mm_P0.5mm",
        150, 78),

    sym("Sensor_Optical:VEML7700",  # search manually if missing
        "U6", "VEML7700-TT",
        "Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.65mm_EP0.7x1.6mm",
        150, 44),

    sym("Device:R", "R10", "4k7", R, 140, 58),  # I2C SDA pullup
    sym("Device:R", "R11", "4k7", R, 155, 58),  # I2C SCL pullup

    sym("Device:C", "C6",  "100nF", C_0603, 168, 90),  # NTC AIN1 anti-alias
    sym("Device:C", "C7",  "100nF", C_0603, 140, 85),  # ADS1115 VDD decouple
    sym("Device:C", "C8",  "100nF", C_0603, 154, 85),  # ADS1115 AVDD decouple
    sym("Device:C", "C9",  "100nF", C_0603, 164, 44),  # VEML7700 VCC decouple

    sym("MCU_RaspberryPi_RP2040:RaspberryPi_PicoW",
        "U1", "PicoW",
        "MicrocontrollerBoard:RaspberryPi_PicoW",
        225, 130),

    sym("Device:C", "C11", "100nF", C_0603, 203, 58),  # Pico VSYS decouple
    sym("Device:C", "C12", "100nF", C_0603, 217, 58),
    sym("Device:C", "C13", "10uF",  C_0805, 190, 58),  # Pico VSYS bulk

    # 10 kΩ misc: NTC pullup, DHT pullup, PIR pullup, SPI-idle (7 total)
    # R7 reused for NTC pullup; R5-R6 already used above for 100k;
    # BOM R5-R9 group (10k, qty 7) mapped to R7 + R19-R24 here to avoid clash
    sym("Device:R", "R7",  "10k", R, 192, 148),  # NTC pullup (3V3_ANA → AIN1)
    sym("Device:R", "R19", "10k", R, 206, 148),  # DHT22 data pullup
    sym("Device:R", "R20", "10k", R, 220, 148),  # PIR data pullup
    sym("Device:R", "R21", "10k", R, 234, 148),  # SPI idle / misc
    sym("Device:R", "R22", "10k", R, 248, 148),  # spare (BOM qty 7 = 5 above + R7 + R17)

    # ── PIR POWER GATE ───────────────────────────────────────────────────────
    sym("Transistor_FET:BSS84",
        "Q2", "BSS84PXUMA1",
        SOT23,
        268, 90),

    sym("Device:R", "R17", "10k", R, 258, 78),  # gate pullup to 3V3_DIG

    # ── RELAY ZONE ───────────────────────────────────────────────────────────
    sym("Device:Relay_SPDT",
        "K1", "SRD-05VDC-SL-C",
        "Relay_THT:Relay_SPDT_Songle_SRD-xxVDC-SL-C",
        338, 72),

    sym("Transistor_BJT:BC817",
        "Q1", "BC817-40",
        SOT23,
        312, 92),

    sym("Device:D",
        "D2", "1N4148W",
        "Diode_SMD:D_SOD-123",
        322, 57),

    sym("Device:R", "R8",  "1k", R, 298, 92),   # relay base drive
    sym("Device:R", "R12", "1k", R, 312, 107),  # misc 1k
    sym("Device:R", "R13", "1k", R, 326, 107),
    sym("Device:R", "R14", "1k", R, 340, 107),

    sym("Device:C", "C10", "100nF", C_0603, 355, 90),  # relay zone decouple
    sym("Device:C", "C16", "10uF",  C_0805, 355, 72),  # relay VSYS bulk

    # ── CONNECTORS ───────────────────────────────────────────────────────────
    sym("Connector_Generic:Conn_01x03", "J2", "Wago-DS18B20",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        18, 240),
    sym("Connector_Generic:Conn_01x03", "J3", "Wago-DHT22",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        52, 240),
    sym("Connector_Generic:Conn_01x03", "J4", "Wago-PIR",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        86, 240),
    sym("Connector_Generic:Conn_01x03", "J5", "Wago-GP16",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        120, 240),
    sym("Connector_Generic:Conn_01x03", "J6", "Wago-GP17",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        154, 240),
    sym("Connector_Generic:Conn_01x03", "J7", "Wago-Relay",
        "TerminalBlock_Wago:TerminalBlock_Wago_2060-453_1x03_P5.00mm_Horizontal",
        338, 240),

    sym("Connector_Generic:Conn_01x04", "J8", "Phoenix-EC4pin",
        "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5_4-3,5-H_1x04_P3.50mm_Horizontal",
        115, 215),

    sym("Connector_Generic:Conn_01x02", "J9", "Phoenix-Power",
        "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5_2-5,0-H_1x02_P5.00mm_Horizontal",
        255, 240),

    sym("Connector_Generic:Conn_01x04", "HDR1", "Debug-UART",
        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        220, 240),
]

NOTES = [
    note("ANALOG ZONE", 15, 26, bold=True),
    note("EC ZONE  (DNP v1 — see schematic.md for v2 AD5933 plan)", 93, 126, bold=True),
    note("DIGITAL ZONE", 148, 26, bold=True),
    note("PIR GATE", 252, 68, bold=True),
    note("RELAY ZONE", 293, 42, bold=True),
    note("CONNECTORS", 15, 225, bold=True),
    note("After opening: Tools > Update Symbols from Library", 15, 270),
    note("Wire per hardware/docs/schematic.md", 15, 276),
    note("U3 (LMP91200) + U6 (VEML7700) may need manual symbol search", 15, 282),
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
