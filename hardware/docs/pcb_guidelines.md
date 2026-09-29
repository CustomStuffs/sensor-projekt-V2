# PCB Layout Guidelines

Board: **100 × 100 mm** (was 100 × 80; enlarged Sep 2026 to fit the 8 mm MAINS separation and the socketed Pico WH — still inside the ≤ 100 × 100 mm low-cost fab tier), 2-layer FR4 1.6 mm, ENIG finish, 1 oz copper both layers. Enclosure is 3D-printed to fit.

**Design rules live in the project:** net classes in `kicad/sensor_hub.kicad_pro` (Default 0.25/0.15, Power 0.5, VSYS 0.8, MAINS 3.0 mm tracks) and custom rules in `kicad/sensor_hub.kicad_dru` (MAINS ↔ SELV 8 mm clearance + creepage + hole clearance, MAINS K1 ↔ K2 4 mm, same channel 1.5 mm). Rule areas on the board: `MAINS_keepout` (no pour, no vias), `PicoW_antenna_keepout` (no pour, no tracks; only between the Pico pin rows, x 33.0–46.8). Pours: `GND` (both layers), `GND_ANA` (analog column), `GUARD_PH` (PH_BUF, around the pH input). Custom DRC rule: socket/header GND pins (U1, J11) may use one thermal spoke per layer.

**Design decision (Sep 2026): relay contacts are rated for 230 VAC mains.** Anything up to 48 V DC is covered by the same layout. The board is therefore split into a **SELV side** (everything low-voltage, including the pH and NTC probes that sit in water) and a **MAINS zone** (relay contacts, snubbers, W6/W7). The two are separated by **reinforced insulation**.

**Hard requirements:**
- Two on-board relays (K1 + K2) with reinforced coil-to-contact insulation (Omron G2RL-1-E)
- **8 mm creepage and clearance** between any mains copper and any SELV copper, on both layers
- Routed isolation slot between the MAINS zone and the SELV side
- Guard pour on the pH high-Z node (NODE_A), driven by the AD8603 output
- RC snubbers on both relay contact sets (COM–NO), X2 capacitors
- Both relay contacts use mains-rated Wago connectors in the MAINS zone (W6 = RELAY1, W7 = RELAY2), physically separated from sensor ports W1–W5

---

## Zone Map

```
  x=0                                                                          x=100 mm
  ┌──────────────────────────────────────────────────────────────────────────────┐ y=0
  │(H1)  [J9 5V IN]  R10/R11  ┌──────────────┐  Q1 D2 ┌── K1 coil ──┐          (H4)│
  │                          │              │   R8  │  ═══slot═══ │               │
  │ C13 C11 C14 C17 C8       │  RASPBERRY   │       │ C19 R19     │  ┌────────┐   │
  │ U5 (LDO)                 │   PI PICO WH │       │  K1 contacts│══│ W6 (J7)│   │
  │ C15 C18 C12              │  on sockets  │       │  NC/COM/NO  │  └────────┘   │
  │ U2 (ADS1115) C7 C16      │              │ MAINS │ ! 230 VAC   │     MAINS     │
  │  ANALOG                  │  USB at top  │ ZONE  │  K2 contacts│  ┌────────┐   │
  │[BNC J1]  R1 D1 U4 ◄guard │ antenna end ▼│ ≥8 mm │ C20 R20     │══│ W7(J10)│   │
  │ (pH, left edge)  R2 R3 C1│  (keepout)   │       │  ═══slot═══ │  └────────┘   │
  │                          └──────────────┘  Q3 D3└── K2 coil ──┘               │
  │                          [J11 spare-GPIO holes]   R18                         │
  │                              (H5)                     [HDR1 UART]             │
  │  R7 C6 (NTC)           (H6) [U6] (H7)  ◄ light pipe       R17 Q2              │
  │                               C9                  Sensor Hub V2.0             │
  │                  R5          R6          R9                                   │
  │ ┌──J8──┐┌──J2──┐┌──J3──┐┌──J4──┐┌──J5──┐┌──J6──┐                              │
  │ │EC/NTC││ W1   ││ W2   ││ W3   ││ W4   ││ W5   │    all SELV, wire entry ↓   │
  │(H2)────┘└──────┘└──────┘└──────┘└──────┘└──────┘                         (H3) │
  └──────────────────────────────────────────────────────────────────────────────┘ y=100
```

Schematic only, not to scale — `kicad/sensor_hub.kicad_pcb` is the reference (placement comes from `tools/place_pcb.py`). Coordinates in this document are board mm from the top-left corner, y pointing down.

The relay bodies straddle the SELV/MAINS boundary: coil pins on the SELV side (K1 at the top edge, K2 at the bottom of the relay block), contact pins in the MAINS zone, with a 2 mm isolation slot under each relay body between them. The contact rows line up with the W6/W7 terminal rows so every mains track is a straight 3 mm run.

---

## Analog Zone Rules + Guard Ring

1. **No GND pour under the pH front-end**: under AD8603, R1 (10 MΩ), D1 (BAV99) and the NODE_A trace there is no GND/GND_ANA pour on either layer — the guard pour below takes its place. No digital signal routing in this area.

2. **Guard pour on NODE_A (mandatory)** — zone `GUARD_PH`, net PH_BUF, both layers, x 15.8–28.2 / y 45.0–51.2, priority above GND_ANA:
   - NODE_A (R1 → AD8603 IN+ and D1) is hand-routed short and sits inside the guard with 0.3 mm clearance.
   - The guard is driven **only** by AD8603 OUT (PH_BUF, unity-gain buffered). The bottom-layer guard is stitched to PH_BUF with one via next to U4 pin 4.
   - Do **not** connect the guard to GND or any other net.
   - Top-side guard copper is **exposed** (F.Mask opening = guard fill shrunk 0.1 mm, minus footprint silkscreen, generated by `route_pcb.py`): solder mask absorbs moisture, bare ENIG does not. NODE_A and all other copper stay masked. Clean flux off this area after assembly (IPA).
   - Purpose: potential difference ≈ 0 → surface leakage from nearby 3V3_ANA/GND_ANA copper ends on the guard, not on NODE_A. Outdoors an unguarded 10 GΩ surface path to 3V3 would already mean ≈ 1 pH of drift.

3. **VREF filter**: place C1 (100 nF on VREF_MID) directly at the divider midpoint node, not at the op-amp pin.

4. **Ground plane**: GND_ANA pour on both layers over the analog column (x 0.3–27.6, y 11–77.5), GND pour everywhere else. The two meet at a single point: net tie NT1 next to the ADS1115 (no 0 Ω link or ferrite needed).

5. **BNC connector**: right-angle mount at left board edge. The board edge should align with the enclosure wall knockout. Leave 3 mm clearance between BNC body and any component.

6. **AP2112K (U5)**: top-left, below J9, at the boundary between analog and digital zones. Its output connects to 3V3_ANA pour. Input from VSYS (5 V) — a 3.3 V LDO cannot regulate from 3V3_DIG.

---

## Digital Zone Rules

7. **Pico WH on sockets**: U1 uses `Module:RaspberryPi_Pico_Common_THT` (2 × 20 THT, 1 mm drill) for two 1×20 female headers, so a Pico WH (pre-soldered headers) plugs in and can be swapped. Stack height ≈ 8.5 mm socket + Pico — plan the 3D-printed enclosure for it. Keep the Pico W antenna end (opposite the USB connector) pointing away from the MAINS zone, with no copper pour and no traces under the antenna area on either layer.

7a. **J11 spare-GPIO breakout**: 2×8 holes at 2.54 mm (no part fitted) next to U1, carrying GP4–GP7, GP18–GP22, GP26–GP28, RUN, 3V3_DIG and 2× GND. Keep traces short; GP26–28 are ADC-capable (0–3.3 V only). SELV side only.

8. **ADS1115**: place at the analog/digital boundary. AGND pad connects to GND_ANA; VDD connects to 3V3_ANA; SDA/SCL to GND_DIG. 100 nF decoupling within 0.5 mm of VDD pin.

9. **EC front-end**: removed in v1 (LMP91200 EOL); GP4–GP7 stay free on J11 for the v2 AD5933.

10. **VEML7700 (U6) + light pipe**: U6 sits in the digital area below J11 (centre x 45 / y 73.45 mm) so a light pipe (acrylic rod) can run straight up to a window in the lid. Three M2 holes (H5–H7, r = 7 mm, one above, two diagonally below U6) take a 3D-printed light-pipe holder; M2 screws from below into the print (or M2 heat-set inserts). Keep the holder area free of tall parts. C9 (100 nF) directly below U6, inside the hole triangle. I2C address fixed at 0x10.

11. **I2C pullups**: R10 and R11 (4.7 kΩ) sit next to the Pico W GP2/GP3 pins (top, left of U1), not at the sensor end.

---

## Relay Zone Rules (230 VAC mains, two relays + EMC snubbers)

The insulation between MAINS and SELV must be **reinforced** because the SELV side connects to probes immersed in water and to touchable sensor wiring. Figures below follow IEC 60664-1 for 250 V, pollution degree 3 (outdoor enclosure, condensation possible), FR4 material group IIIa, overvoltage category II/III.

12. **Relays (K1 + K2)**: Omron G2RL-1-E (5 V coil, 16 A, 5 kVAC coil–contact, reinforced). Place at the right side so each relay's **coil pins sit on the SELV side and its contact pins sit in the MAINS zone**. Do not substitute a relay with only basic coil–contact insulation (e.g. Songle SRD series).

13. **SELV ↔ MAINS separation (reinforced)**:
    - **≥ 8.0 mm creepage** (along the board surface) and **≥ 8.0 mm clearance** (through air) between any mains net (K1/K2 COM, NO, NC, snubber nodes, W6/W7 pins) and any SELV net (coil, VSYS, GND, logic, sensors) — on **both** layers.
    - Measure from pad/trace edge to pad/trace edge, including THT pads on the opposite layer.
    - Use a KiCad **netclass `MAINS`** with a custom DRC rule (8 mm clearance to all other netclasses) so the DRC enforces this automatically.

14. **Isolation slot**: route a **2 mm wide slot** (Edge.Cuts) under each relay body between its coil pins and contact pins, and continue it along the MAINS/SELV boundary as far as the layout allows. A slot ≥ 1.5 mm wide counts as an air gap for creepage at pollution degree 3. The slot does not replace the 8 mm — it adds margin.

15. **MAINS zone keepout**:
    - No GND pour, no copper pour of any kind, and no vias on either layer in the MAINS zone, except the mains traces themselves.
    - No SELV trace may enter or cross under the MAINS zone on any layer.
    - No mounting hole with a metal screw inside or within 8 mm of the MAINS zone.
    - Silkscreen a hatched border and a ⚠ 230 V warning symbol around the MAINS zone.

16. **Between the two mains channels**: ≥ 4 mm between K1 circuit copper and K2 circuit copper (they may be fed from different circuits or phases). Between COM, NO and NC of the same relay (functional insulation, 230 V across an open contact): ≥ 3 mm wherever the relay footprint allows.

17. **Flyback diodes**: place D2 (1N4148W) directly across K1 coil pads and D3 directly across K2 coil pads. Cathode toward VSYS. SELV side only.

18. **Drivers**: Q1 (BC817) for K1 adjacent to K1 coil pins; Q3 (BC817) for K2 adjacent to K2 coil pins. Base resistors R8 and R18 (1 kΩ) within 3 mm of the respective base pads. G2RL coil draws ≈ 80 mA at 5 V — within BC817 rating.

19. **Contact EMC snubbers (mandatory)**:
    - R19 (100 Ω, 1206) + C19 (100 nF **X2** film, 275 VAC) in series across K1 COM–NO
    - R20 (100 Ω, 1206) + C20 (100 nF **X2** film, 275 VAC) in series across K2 COM–NO
    - Place as close as possible to the relay contact pins, entirely inside the MAINS zone.
    - Purpose: suppress arcing and EMI when switching inductive loads (pumps, solenoids, valves).
    - Note: at 230 V / 50 Hz a 100 nF snubber passes ≈ 7 mA with the contact **open**. This can make LED lamps glow or small contactor coils hum, and the NO terminal is never truly dead while COM is live. For such loads, leave R19/C19 (or R20/C20) unpopulated. Always isolate the supply before working on the load.

20. **Contact connectors**: W6 (K1) and W7 (K2) are 3-pole, mains-rated, THT PCB terminals for up to 2.5 mm² wire (Wago 236-403, 24 A IEC / 300 V 15 A UL). They sit at the **right board edge** (J7 at y 15–33, J10 at y 33–51), level with the relay contact rows, inside the MAINS zone and far from the SELV terminals along the bottom edge. Pin order follows the straight tracks: **W6 (J7) 1 = NO, 2 = COM, 3 = NC; W7 (J10) 1 = NC, 2 = COM, 3 = NO** (K2 is rotated 180°). Labels NC/COM/NO are printed on the tracks next to each terminal.

21. **External protection**: each relay channel must be protected upstream by a fuse or MCB rated ≤ 6 A (installation side, done by the electrician). The board traces are sized for 5 A continuous.

---

## Power Entry

22. J9 (VSYS + GND, Wago 2601-1102 push-in) at the top-left board edge, on the SELV side, far from the MAINS zone. Route VSYS as a 0.8 mm wide trace or polygon from J9 to Pico W VSYS and both relay coils. Add 10 µF + 100 nF directly at J9.

23. AP2112K input/output both need 10 µF + 100 nF. Place caps within 2 mm of IC pads.

---

## Trace Widths

Widths as set in the project (netclass default width; board minimum 0.2 mm, clearance 0.15 mm):

| Net type | Netclass | Width |
|----------|----------|-------|
| Signal (logic, I2C, 1-Wire) | Default | 0.25 mm (0.24 mm where `fixclear` trimmed a Freerouting track) |
| Power (3V3_DIG, 3V3_ANA, GND) | Power | 0.5 mm (0.25 mm only for the first 1.2 mm off U2 pin 8, 0.5 mm pitch) |
| VSYS | VSYS | 0.8 mm |
| Relay contacts / mains (COM, NO, NC → W6/W7) | MAINS | **3.0 mm** (5 A continuous, 1 oz, ≈ 10 °C rise) |
| Snubber branch (R19/C19, R20/C20) | MAINS | 0.8–1.0 mm (hand-routed) |
| pH analog (NODE_A) | Default | 0.25 mm inside the guard pour |

Mains traces: keep them as short as possible (relay pin → Wago pin). Where 3.0 mm does not fit between pads, run the same trace on both layers in parallel and stitch at the THT pads rather than necking down.

---

## Silkscreen

All labels are generated by `tools/place_pcb.py`:

- Sensor terminals, above each terminal (the Wago bodies cover their own outline): `J2  W1 DS18B20`, `J3  W2 DHT22`, `J4  W3 PIR`, `J5  W4 GP16`, `J6  W5 GP17`; the separate J2–J6 reference fields are hidden.
- NTC terminal: `J8  EC  W Y R B` (W/Y unused in v1, R = NTC+, B = NTC–).
- Power: `5V IN` next to J9.
- Mains: `W6 RELAY1` / `W7 RELAY2` beside the terminals, `NC` / `COM` / `NO` on each mains track, `! 230 VAC max 5 A` between the relays.
- BNC: `PH`. Board name and date: `Sensor Hub V2.0  2026-09`.
- Not done yet: hatched border + ⚠ symbol around the MAINS zone (optional, the text warning is there).

---

## Manufacturing Checklist (before ordering)

- [ ] DRC passes with 0 errors (including the `MAINS` netclass 8 mm rule) — `hardware/tools/autoroute.sh` prints the summary; only the 12 `silk_edge_clearance` warnings (edge-mounted terminals) are expected
- [ ] Minimum trace/space ≥ 0.2 mm / 0.15 mm
- [ ] Minimum via drill ≥ 0.3 mm
- [ ] BNC, relay and Wago footprints match physical parts (print 1:1 and test-fit)
- [ ] ≥ 8 mm creepage and clearance between MAINS zone and SELV copper, both layers
- [ ] 2 mm isolation slot under each relay and along the MAINS/SELV boundary (in Edge.Cuts)
- [ ] No pour, vias or SELV traces inside the MAINS zone
- [ ] Mains traces ≥ 3.0 mm wide
- [ ] Guard pour present on both layers, connected only to AD8603 OUT (PH_BUF), top side exposed
- [ ] Snubbers (R19/C19 and R20/C20) placed close to relay contacts; C19/C20 are X2 rated
- [ ] Five sensor Wagos (W1–W5) on the SELV side; W6/W7 inside the MAINS zone
- [ ] 4× M3 mounting holes H1–H4 in the corners (3.2 mm, no copper), none within 8 mm of the MAINS zone
- [ ] 3× M2 light-pipe holder holes H5–H7 around U6 (2.2 mm, no copper)
- [ ] Order files regenerated: `python3 hardware/tools/jlc_export.py` → `fab/gerbers.zip` (all layers incl. paste + drill), `fab/bom_jlc.csv`, `fab/cpl_jlc.csv`
- [ ] Part orientation checked in the JLCPCB placement preview (U2, U4, U5, U6, D1–D3, Q1–Q3)
- [ ] Mains side reviewed by the electrician before first power-up
