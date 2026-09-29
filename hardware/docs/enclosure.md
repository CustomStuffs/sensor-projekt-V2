# Enclosure & Weatherproofing

---

## Primary Recommendation: Hammond 1554T2GYCL

| Attribute | Value |
|-----------|-------|
| Part number | 1554T2GYCL |
| External dimensions | 115 × 65 × 40 mm |
| Material | Polycarbonate (PC) |
| IP rating | **IP67** (1 m submersion) |
| Lid | Clear polycarbonate |
| Color | Light grey body |
| PCB standoffs | 4× M3 brass inserts, 3 mm height |
| Approx. CHF | 8–12 (Distrelec / Conrad) |
| Screws | 4× M3 × 10 mm stainless |

The clear lid lets you see the status LED without drilling.

**Alternative**: Bopla Euromas II EM 220 F (IP65, 122 × 72 × 55 mm, ABS, more depth for wiring).

---

## Cable Entries

| Entry | Part | IP rating | Cable dia. | Qty | Notes |
|-------|------|-----------|-----------|-----|-------|
| Wago sensor cables | Wiska ClikPlug M16 | IP68 | 4–8 mm | 5 | One per sensor port W1–W5 (J2–J6) |
| NTC probe cable (J8) | Wiska ClikPlug M16 | IP68 | 4–8 mm | 1 | 2 wires used in v1 (EC wires unused); M20 if a 4-wire EC probe cable is kept for v2 |
| USB-C power | Bulgin PX0441/B/4M00 | IP68 | Panel mount | 1 | 5V input feedthrough |
| pH BNC external | Amphenol 31-221-RFX | IP67 | Panel mount | 1 | External probe connector |
| Relay mains cables (W6, W7) | Wiska ClikPlug M20 | IP68 | 8–14 mm | 2 | 230 VAC load cables; enter on the MAINS side of the box, away from sensor glands |

**Mains wiring inside the enclosure**: keep 230 VAC load cables on the MAINS side of the box, tied down so a loose conductor cannot reach the SELV side of the PCB. Double-insulated cable (sheath stripped only as far as needed at W6/W7). If the enclosure has any metal parts (e.g. mounting plate), they must be earthed by the electrician.

**⚠ Enclosure size**: the PCB is now **100 × 100 mm**; the Hammond 1554T2GYCL (115 × 65 × 40 mm external) above does **not** fit it, neither does the Bopla EM 220 F. The plan (see `pcb_guidelines.md`) is a 3D-printed enclosure; a bought box needs ≥ ~110 × 110 mm inside and ≥ ~25 mm clear height above the board.

---

## PCB Envelope (for the enclosure design)

Heights above the top of the PCB, from the vendor 3D models (`kicad/3d/`):

| Part | Where on the board | Height |
|------|--------------------|--------|
| BNC J1 (pH) | left edge, y 44–60, opening points out of the left edge | ≈ 19.2 mm (tallest) |
| Relays K1/K2 | right half, x 67–80 | 15.7 mm |
| Wago 2601 (J2–J6, J8, J9) | bottom edge row + J9 at the top edge | ≈ 15.1 mm, orange levers reach ~0.8 mm past the board edge |
| Pico WH on sockets | centre, USB-C at the top edge (x ≈ 40) | ≈ 8.5 mm socket + Pico + USB plug |
| Wago 236-403 (W6/W7) | right edge, y 15–51 | 12.7 mm |
| X2 caps C19/C20 | left of the relays | box 13 × 6 mm, check the fitted part |

- **Board mounting**: 4× M3 holes H1–H4 at (3.5, 3.5), (3.5, 96.5), (96.5, 96.5), (96.5, 3.5) mm from the top-left corner.
- **Wire entries**: all sensor terminals (J8, J2–J6) open toward the bottom edge, J9 (5 V) toward the top edge, W6/W7 (mains) toward the right edge — put the glands on those walls and keep the mains glands on the right wall only.
- **Light sensor window**: U6 (VEML7700) is at (45.0, 73.45) mm. A light pipe (acrylic/PMMA rod, ≈ 5–6 mm) runs from just above U6 (≤ 0.5 mm gap) straight up to a window/hole in the lid. Its 3D-printed holder screws to the board through 3× M2 holes H5 (45.0, 66.45), H6 (38.94, 76.95), H7 (51.06, 76.95); the holder base needs a recess for U6 (2.35 mm high) and C9 (3.2 mm below U6). Seal the rod in the lid (silicone or O-ring) and keep it opaque around the sides so only the window collects light.

---

## BNC Panel Mount

The PCB uses a right-angle PCB-mount BNC (TE 1-1478035-0) at the left board edge for internal connection. The external BNC on the enclosure wall is a separate panel-mount connector connected via a short RG174 coaxial pigtail (50–100 mm).

1. Drill a 10 mm hole in the enclosure wall at the BNC position
2. Insert panel-mount BNC (Amphenol 31-221-RFX), secure with lock nut and washer
3. Solder a 75–100 mm RG174 pigtail: center conductor to PCB BNC center pin, shield to PCB BNC shell / VREF_MID trace
4. Apply silicone sealant around the BNC nut on the outside

---

## Gore-Tex Vent Plug (mandatory for outdoor use)

**Part**: Wiska VMK 16 or equivalent IP67-rated vent plug.

**Why**: a fully sealed IP67 enclosure experiences pressure/temperature cycling outdoors. Without a vent, warm air inside the enclosure during the day creates condensation when it cools at night. The Gore-Tex membrane passes water vapor but not liquid water — preventing internal condensation without compromising weather protection.

Install one vent plug in the bottom face of the enclosure (lowest point for drainage if any moisture enters).

---

## Assembly Notes

1. Drill all holes using a step drill bit in polycarbonate — avoid twist drills (crack risk)
2. Install cable glands hand-tight, then 1/4 turn with pliers — do not overtighten
3. Apply silicone sealant (neutral cure, not acetic acid cure) around:
   - PCB standoff mounting screws
   - BNC lock nut
   - USB-C panel connector
4. Route sensor cables with a drip loop before entering cable glands (prevents water tracking)
5. Lid torque: finger-tight + 1/4 turn — overtightening cracks polycarbonate lid
6. Supplied gasket is replaceable; check condition annually if unit is in direct rain exposure
7. Label cable glands with UV-stable vinyl labels or permanent marker (sensor type)

---

## Mounting

Mount on a stake, post, or bracket using M3/M4 stainless bolts through the enclosure wall or base. Avoid mounting flat against a wall — leave at least 10 mm air gap behind for heat dissipation.

Orientation: BNC connector side toward the nearest sheltered location (garden wall, planter edge) to protect the pH probe connection from direct rain impact.
