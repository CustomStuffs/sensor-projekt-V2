# Hardware Agent

> **Scope: `hardware/` only. Do not read, modify, or suggest changes to files outside this directory.**

PCB design for the Pico W sensor hub. This subproject owns all electrical design. No firmware or server code here.

## What's in this folder

| Path | Purpose |
|------|---------|
| `docs/schematic.md` | **Source of truth** for all electrical connections (ASCII schematic + netlist table) |
| `docs/bom.csv` | Bill of materials — part numbers, quantities, CHF prices |
| `docs/pcb_guidelines.md` | Layout rules: analog zone, relay clearance, ground plane |
| `docs/enclosure.md` | Enclosure selection, cable glands, vent plug |
| `kicad/sensor_hub.*` | KiCad 10 project files — draw schematic manually using schematic.md as reference |

An empty V1 skeleton also exists at `../PCB/V1 pico sensorhub/` (historical, ignore).

## Key Design Constraints

### Two relays (hard minimum)
- The board **must** carry two independent on-board SPDT relays (K1 + K2).
- Purpose: allow at least two actuator channels (pump, valve, etc.) without external modules.
- Future board variants may add more relays; two is the baseline that must never be omitted.
- Drivers: GP10 → K1, GP15 → K2. Each has its own BC817 + 1N4148 flyback.

### Analog zone (bottom-left PCB quadrant)
- Copper pour keepout on both layers under AD8603, the 10 MΩ input resistor (R1) and BAV99
- AD8603 is a plain unity-gain follower (IN– tied to OUT); no resistor from VREF to IN–
- Route the high-impedance node (between 10 MΩ and AD8603 IN+) with a guard ring tied to AD8603 output — this eliminates PCB surface leakage that corrupts pH readings
- Single-point AGND/DGND join at ADS1115 AGND pin
- Separate 3V3_ANA pour fed by AP2112K LDO from VSYS (isolated from digital 3V3)
- Reference designators: `docs/schematic.md` → "Reference Designators (master list)" is authoritative

### Relay zone / MAINS zone (right board side, 230 VAC)
- Relay contacts are rated for 230 VAC, 5 A per channel (covers ≤ 48 V DC too)
- Relays: Omron G2RL-1-E DC5 — reinforced coil–contact insulation; never substitute a basic-insulation relay (e.g. Songle SRD)
- **8 mm creepage and clearance** between any mains net and any SELV net, both layers; enforce with a `MAINS` netclass DRC rule
- 2 mm routed isolation slot between relay coil and contact pins and along the MAINS/SELV boundary
- No pour, vias or SELV traces in the MAINS zone; mains traces ≥ 3.0 mm
- Snubbers use X2 capacitors and 1206 resistors; W6/W7 are mains-rated THT terminals inside the MAINS zone
- 1N4148 flyback diode directly across each relay coil pads
- Relay coils driven from VSYS (5V), not 3V3

### BNC connector (left board edge)
- Right-angle PCB-mount BNC at board edge
- 10 MΩ input resistor + BAV99 ESD protection before op-amp
- BNC shield connects to VREF (1.65V virtual mid-rail), NOT to GND — this shifts the pH electrode's ±414 mV output into the ADS1115's positive input range

### General
- 2-layer FR4, 1.6 mm, ENIG finish recommended
- 100 nF decoupling within 0.5 mm of every IC VCC pin
- 10 µF bulk at VSYS entry, AP2112K output, ADS1115 VDD

## BOM Update Process

1. Edit `docs/bom.csv` — one row per component
2. Verify every part in the BOM appears in `docs/schematic.md` netlist
3. Update component values in KiCad schematic to match

## KiCad Note

The `kicad/` skeleton files are in KiCad 10 format. Draw the schematic manually using `docs/schematic.md` as reference. Do not try to auto-generate KiCad XML — draw it in the KiCad application.

## Scripts (`tools/`, run from the repo root)

- `wire_sch.py` — net labels / no-connects on every schematic pin (net table at the top). Idempotent.
- `place_pcb.py` — outline, holes, isolation slots, rule areas, footprint placement. Idempotent; resets tracks' surroundings, not tracks.
- `route_pcb.py` + `autoroute.sh` — hand-routed MAINS + NODE_A, Freerouting for the rest, GND / GND_ANA / guard pours. Java 25 + Freerouting 2.4.1 are cached in `~/.cache/sensor-hub-tools`.
- pcbnew (KiCad 10.0.6) Python quirks: iterate `b.Tracks()` / `b.Drawings()` by index (their iterators are broken); give a `SHAPE_POLY_SET` to `ZONE.SetOutline()` with `thisown = False`, otherwise saving segfaults and truncates the board file; do nothing but save after `ImportSpecctraSES` (it breaks the wrappers for the rest of the process).
