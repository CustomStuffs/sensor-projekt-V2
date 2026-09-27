# PCB Layout Guidelines

Board: 100 × 80 mm, 2-layer FR4 1.6 mm, ENIG finish, 1 oz copper both layers.

**Design decision (Sep 2026): relay contacts are rated for 230 VAC mains.** Anything up to 48 V DC is covered by the same layout. The board is therefore split into a **SELV side** (everything low-voltage, including the pH/EC probes that sit in water) and a **MAINS zone** (relay contacts, snubbers, W6/W7). The two are separated by **reinforced insulation**.

**Hard requirements:**
- Two on-board relays (K1 + K2) with reinforced coil-to-contact insulation (Omron G2RL-1-E)
- **8 mm creepage and clearance** between any mains copper and any SELV copper, on both layers
- Routed isolation slot between the MAINS zone and the SELV side
- Guard ring on the pH high-Z node (NODE_A)
- RC snubbers on both relay contact sets (COM–NO), X2 capacitors
- Both relay contacts use mains-rated Wago connectors in the MAINS zone (W6 = RELAY1, W7 = RELAY2), physically separated from sensor ports W1–W5

---

## Zone Map

```
┌──────────────────────────────────────────────────────────────────────┐
│  100 mm × 80 mm — TOP VIEW                        [J9 VSYS in]       │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────────────────┐ ║ ┌──────────┐ │
│  │  ANALOG ZONE    │  │       DIGITAL ZONE          │ ║ │  MAINS   │ │
│  │  (keepout +     │  │                             │ ║ │  ZONE    │ │
│  │   Guard Ring)   │  │  ┌───────────────────────┐  │ ║ │          │ │
│  │                 │  │  │  RASPBERRY PI PICO W  │  │ ║ │ K1 cont. │ │
│  │  [BNC]──[10MΩ]  │  │  └───────────────────────┘  │ ║ │ K2 cont. │ │
│  │     │           │  │                             │ ║ │          │ │
│  │  [BAV99]        │  │  [ADS1115]   [VEML7700]     │ ║ │ R19/C19  │ │
│  │     │           │  │                             │ ║ │ R20/C20  │ │
│  │  [AD8603]       │  │  [LMP91200]  [AP2112K]      │ ║ │          │ │
│  │     │           │  │                             │ ║ │          │ │
│  │  [VREF divider] │  │  [Q1/Q3 + D2/D3 + K coils]──╫─╫─┤ (relay   │ │
│  │                 │  │                             │ ║ │  bodies  │ │
│  └────────┬────────┘  └─────────────────────────────┘ ║ │  bridge  │ │
│  AGND─────┘ (single-point join at ADS1115 AGND)       ║ │  slot)   │ │
│                                                   slot║ │          │ │
│  ╔══╦══╦══╦══╦══╗  ╔══╗                    ≥ 8 mm ║ │ ╔════╦════╗│ │
│  ║W1║W2║W3║W4║W5║  ║J8║                           ║ │ ║ W6 ║ W7 ║│ │
│  ╚══╩══╩══╩══╩══╝  ╚══╝                           ║ │ ╚════╩════╝│ │
│  [HDR1 debug 1×4]   SELV side                     ║ └──────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

The relay bodies straddle the SELV/MAINS boundary: coil pins on the SELV side, contact pins in the MAINS zone, with the isolation slot running between them under the relay body.

---

## Analog Zone Rules + Guard Ring

1. **Keepout**: copper pour prohibition on both layers under AD8603, R1 (10 MΩ), D1 (BAV99), and NODE_A trace. No digital signal routing allowed in this zone.

2. **Guard Ring on NODE_A (mandatory)**:
   - Surround the entire NODE_A net (trace from R1 to AD8603 IN+) with a continuous copper ring on **both** top and bottom layers.
   - Connect the guard ring **only** to AD8603 OUT (unity-gain buffered output).
   - Do **not** connect the guard to GND or any other net.
   - Typical gap between NODE_A and guard: 0.2–0.5 mm.
   - No other traces may cross the guarded area.
   - Purpose: potential difference ≈ 0 → surface leakage current becomes negligible. Critical for accurate pH readings.

3. **VREF filter**: place C1 (100 nF on VREF_MID) directly at the divider midpoint node, not at the op-amp pin.

4. **Ground plane**: solid GND_ANA pour in analog zone (bottom layer). Join to GND_DIG pour at a single point — the ADS1115 AGND pad. Use a 0 Ω link or ferrite bead at the join.

5. **BNC connector**: right-angle mount at left board edge. The board edge should align with the enclosure wall knockout. Leave 3 mm clearance between BNC body and any component.

6. **AP2112K**: place at the boundary between analog and digital zones. Its output connects to 3V3_ANA pour. Input from VSYS (5 V) — a 3.3 V LDO cannot regulate from 3V3_DIG.

---

## Digital Zone Rules

7. **Pico WH on sockets**: U1 uses `Module:RaspberryPi_Pico_Common_THT` (2 × 20 THT, 1 mm drill) for two 1×20 female headers, so a Pico WH (pre-soldered headers) plugs in and can be swapped. Stack height ≈ 8.5 mm socket + Pico — plan the 3D-printed enclosure for it. Keep the Pico W antenna end (opposite the USB connector) pointing away from the MAINS zone, with no copper pour and no traces under the antenna area on either layer.

7a. **J11 spare-GPIO breakout**: 2×8 holes at 2.54 mm (no part fitted) next to U1, carrying GP4–GP7, GP18–GP22, GP26–GP28, RUN, 3V3_DIG and 2× GND. Keep traces short; GP26–28 are ADC-capable (0–3.3 V only). SELV side only.

8. **ADS1115**: place at the analog/digital boundary. AGND pad connects to GND_ANA; VDD connects to 3V3_ANA; SDA/SCL to GND_DIG. 100 nF decoupling within 0.5 mm of VDD pin.

9. **LMP91200**: place near J8 (EC terminal). SPI traces (GP4–GP7) route as a bundle, away from analog zone. Keep SPI trace lengths within 10 mm of each other.

10. **VEML7700**: near ADS1115 (shares I2C bus). Place 100 nF decoupling at VCC pin. No ADDR pin — I2C address fixed at 0x10.

11. **I2C pullups**: place R10 and R11 (4.7 kΩ) close to Pico W GP2/GP3 pads, not at the sensor end.

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

20. **Contact connectors**: W6 (K1) and W7 (K2) are 3-pole, mains-rated, THT PCB terminals for up to 2.5 mm² wire (Wago 236-403, 24 A IEC / 300 V 15 A UL). Place them at the **bottom-right corner inside the MAINS zone**, ≥ 8 mm from W5/J8 and any other SELV connector. Pin order: 1 = COM, 2 = NO, 3 = NC.

21. **External protection**: each relay channel must be protected upstream by a fuse or MCB rated ≤ 6 A (installation side, done by the electrician). The board traces are sized for 5 A continuous.

---

## Power Entry

22. J9 (VSYS + GND screw terminal) at the top-right board edge, on the SELV side, ≥ 8 mm from the MAINS zone. Route VSYS as a 0.8 mm wide trace or polygon from J9 to Pico W VSYS and both relay coils. Add 10 µF + 100 nF directly at J9.

23. AP2112K input/output both need 10 µF + 100 nF. Place caps within 2 mm of IC pads.

---

## Trace Widths

| Net type | Minimum width |
|----------|--------------|
| Signal (logic, SPI, I2C) | 0.15 mm |
| Power (3V3_DIG, 3V3_ANA) | 0.3 mm |
| VSYS | 0.8 mm |
| Relay coil (VSYS → coil → Q collector) | 0.5 mm |
| Relay contacts / mains (COM, NO, NC → W6/W7) | **3.0 mm** (5 A continuous, 1 oz, ≈ 10 °C rise) |
| Snubber branch (R19/C19, R20/C20) | 0.5 mm |
| pH analog (NODE_A) | 0.15 mm with guard ring |

Mains traces: keep them as short as possible (relay pin → Wago pin). Where 3.0 mm does not fit between pads, run the same trace on both layers in parallel and stitch at the THT pads rather than necking down.

---

## Silkscreen

Label all sensor Wago connectors:  
W1=DS18B20, W2=DHT22, W3=PIR, W4=GP16, W5=GP17.  
Label mains connectors: W6=RELAY1 (COM/NO/NC), W7=RELAY2 (COM/NO/NC), plus "230 VAC max 5 A".  
Hatched border + ⚠ high-voltage symbol around the MAINS zone.  
Label BNC connector: PH (pH probe).  
Label EC terminal: EC (W=White, Y=Yellow, R=NTC+, B=NTC–).  
Mark board version and date on silkscreen.

---

## Manufacturing Checklist (before ordering)

- [ ] DRC passes with 0 errors (including the `MAINS` netclass 8 mm rule)
- [ ] Minimum trace/space ≥ 0.15 mm / 0.15 mm
- [ ] Minimum via drill ≥ 0.3 mm
- [ ] BNC, relay and Wago footprints match physical parts (print 1:1 and test-fit)
- [ ] ≥ 8 mm creepage and clearance between MAINS zone and SELV copper, both layers
- [ ] 2 mm isolation slot under each relay and along the MAINS/SELV boundary (in Edge.Cuts)
- [ ] No pour, vias or SELV traces inside the MAINS zone
- [ ] Mains traces ≥ 3.0 mm wide
- [ ] Guard ring present and connected only to AD8603 OUT
- [ ] Snubbers (R19/C19 and R20/C20) placed close to relay contacts; C19/C20 are X2 rated
- [ ] Five sensor Wagos (W1–W5) on the SELV side; W6/W7 inside the MAINS zone
- [ ] 4× M3 mounting holes (3.2 mm drill, no copper pad), none within 8 mm of the MAINS zone
- [ ] Gerbers exported: F.Cu, B.Cu, F.Mask, B.Mask, F.SilkS, Edge.Cuts (including slots), Drill
- [ ] Mains side reviewed by the electrician before first power-up
