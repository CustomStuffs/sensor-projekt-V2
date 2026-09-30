# Hardware Agent

> **Scope: `hardware/` only. Do not read, modify, or suggest changes to files outside this directory.**

PCB design for the Pico W sensor hub. This subproject owns all electrical design. No firmware or server code here.

## What's in this folder

| Path | Purpose |
|------|---------|
| `docs/schematic.md` | **Source of truth** for all electrical connections (ASCII schematic + netlist table) |
| `docs/bom.csv` | Bill of materials — part numbers, quantities, CHF prices |
| `docs/pcb_guidelines.md` | Layout rules: analog zone, relay clearance, ground plane |
| `docs/enclosure.md` | Enclosure, cable glands, vent plug, PCB envelope (heights, wire entries, light-pipe window) |
| `docs/footprints.md` | Footprint + 3D model per part |
| `kicad/sensor_hub.*` | KiCad 10 project — generated/maintained by `tools/` (see KiCad Note) |
| `kicad/3d/` | Vendor STEP models (not in git; download list in `kicad/3d/README.md`) |
| `tools/` | Schematic wiring, placement, routing and JLCPCB export scripts |
| `fab/` | JLCPCB order files: `gerbers.zip`, `bom_jlc.csv`, `cpl_jlc.csv` (regenerate with `tools/jlc_export.py`) |

An empty V1 skeleton also exists at `../PCB/V1 pico sensorhub/` (historical, ignore).

## Key Design Constraints

### Two relays (hard minimum)
- The board **must** carry two independent on-board SPDT relays (K1 + K2).
- Purpose: allow at least two actuator channels (pump, valve, etc.) without external modules.
- Future board variants may add more relays; two is the baseline that must never be omitted.
- Drivers: GP10 → K1, GP15 → K2. Each has its own BC817 + 1N4148 flyback.

### Analog zone (left column: LDO, ADS1115, pH front-end next to the BNC)
- No GND / GND_ANA pour under AD8603, the 10 MΩ input resistor (R1) and BAV99 — instead a guard pour `GUARD_PH` on both layers, net PH_BUF (AD8603 output), priority above GND_ANA
- AD8603 is a plain unity-gain follower (IN– tied to OUT); no resistor from VREF to IN–
- Route the high-impedance node (between 10 MΩ and AD8603 IN+) inside that guard — it sits at ~ the node's own voltage, so surface leakage from nearby 3V3_ANA / GND_ANA copper ends on the guard instead of NODE_A (outdoor humidity: an unguarded 10 GΩ surface path to 3V3 would be ~1 pH of drift)
- Top-side guard copper is exposed (F.Mask opening = guard fill shrunk 0.1 mm, minus footprint silkscreen): solder mask absorbs moisture and leaks, bare ENIG guard copper doesn't. NODE_A and all foreign copper stay masked. Keep the area flux-free after assembly (IPA clean)
- Single-point AGND/DGND join: net tie NT1 next to the ADS1115
- Separate 3V3_ANA pour fed by AP2112K LDO from VSYS (isolated from digital 3V3)
- Reference designators: `docs/schematic.md` → "Reference Designators (master list)" is authoritative

### Relay zone / MAINS zone (right half, 230 VAC)
- Relay contacts are rated for 230 VAC, 5 A per channel (covers ≤ 48 V DC too)
- Relays: Omron G2RL-1-E DC5 — reinforced coil–contact insulation; never substitute a basic-insulation relay (e.g. Songle SRD)
- **8 mm creepage and clearance** between any mains net and any SELV net, both layers; enforce with a `MAINS` netclass DRC rule
- 2 mm routed isolation slot between relay coil and contact pins and along the MAINS/SELV boundary
- No pour, vias or SELV traces in the MAINS zone; mains traces ≥ 3.0 mm
- Snubbers use X2 capacitors and 1206 resistors; W6/W7 are mains-rated THT terminals (Wago 236-403) at the right edge inside the MAINS zone
- Terminal pin order follows the straight mains tracks: W6 (J7) 1 = NO, 2 = COM, 3 = NC; W7 (J10) 1 = NC, 2 = COM, 3 = NO
- 1N4148 flyback diode directly across each relay coil pads
- Relay coils driven from VSYS (5V), not 3V3

### BNC connector (left board edge)
- Right-angle PCB-mount BNC at board edge
- 10 MΩ input resistor + BAV99 ESD protection before op-amp
- BNC shield connects to VREF (1.65V virtual mid-rail), NOT to GND — this shifts the pH electrode's ±414 mV output into the ADS1115's positive input range

### Terminals, light sensor, EC
- Every wire connection is a Wago push-in terminal: 2601 family (3.5 mm) for all SELV ports incl. J8 (NTC) and J9 (5 V in), 236-403 for mains. No screw terminals.
- U6 (VEML7700) sits under a light pipe at (45.0, 73.45) mm with three M2 holder holes H5–H7 (r = 7 mm). Keep that area free of tall parts.
- EC measurement is not in v1: the LMP91200 front-end (U3, R15, R16, C3, C4, C5) was removed; those designators are retired. GP13/GP14 are unused, GP4–GP7 stay free on J11 for a v2 AD5933.

### General
- 2-layer FR4, 1.6 mm, ENIG finish recommended
- 100 nF decoupling within 0.5 mm of every IC VCC pin
- 10 µF bulk at VSYS entry, AP2112K output, ADS1115 VDD

## BOM Update Process

1. Edit `docs/bom.csv` — one row per component
2. Verify every part in the BOM appears in `docs/schematic.md` netlist
3. Update component values in KiCad schematic to match

## KiCad Note

The `kicad/` files are KiCad 10 format and are generated/maintained by the scripts in `tools/` (see below), with `docs/schematic.md` as the source of truth for connections. Change the scripts and rerun them rather than hand-editing the generated parts; close the board in KiCad first, the scripts overwrite the file. Manual tweaks in the KiCad application are fine for anything the scripts don't own, but a rerun of `place_pcb.py` / `autoroute.sh` will reset placement, zones, labels and tracks.

## Scripts (`tools/`, run from the repo root)

- `wire_sch.py` — net labels / no-connects on every schematic pin (net table at the top). Idempotent.
- `place_pcb.py` — outline, holes (H1–H7), isolation slots, rule areas, footprint swaps and placement, silkscreen labels, 3D model links. Idempotent; recreates all zones, leaves tracks alone, so rerun `autoroute.sh` (or `route_pcb.py finish x x` if only labels moved) afterwards. Optional arg: board file path (for testing on a copy).
- `route_pcb.py` + `autoroute.sh` — hand-routed MAINS, NODE_A, 3V3_ANA at U2 and the J11 spare GPIOs, Freerouting for the rest (~1-25 min), dangling-via cleanup, `fixclear` (trims tracks Freerouting leaves a few µm under the clearance by 0.01 mm), GND / GND_ANA / guard pours, exposed-guard mask opening. Don't add clearance margin for the Freerouting export instead: it chokes the 0.5 mm-pitch U2 and the J11 gaps. After only moving labels: `place_pcb.py`, then `route_pcb.py finish x x` to rebuild the pours. Java 25 + Freerouting 2.4.1 are cached in `~/.cache/sensor-hub-tools`.
- `jlc_export.py` — JLCPCB order files in `fab/`: `gerbers.zip`, `bom_jlc.csv`, `cpl_jlc.csv`. JLCPCB assembles only the SMD parts (top side); all THT parts are hand-soldered. LCSC numbers live in the script (keyed by value + footprint) and in the `lcsc` column of `docs/bom.csv`; a new SMD part without an entry stops the export. Check part orientation in JLCPCB's placement preview before ordering (SOT-23, SOT-23-5, MSOP-10, SOD-123, VEML7700).
- pcbnew (KiCad 10.0.6) Python quirks: iterate `b.Tracks()` / `b.Drawings()` by index (their iterators are broken) and test items with `GetClass()`, not `isinstance` (they come back as plain `BOARD_ITEM`); use `b.Delete()`, not `b.Remove()` (segfaults on filled boards); give a `SHAPE_POLY_SET` to `ZONE.SetOutline()` with `thisown = False`, otherwise saving segfaults and truncates the board file; do nothing but save after `ImportSpecctraSES` (it breaks the wrappers for the rest of the process).
