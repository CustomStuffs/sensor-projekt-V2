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
| Wago sensor cables | Wiska ClikPlug M16 | IP68 | 4–8 mm | 5 | One per Wago port 1–5 |
| EC sensor cable | Wiska ClikPlug M20 | IP68 | 8–14 mm | 1 | Thicker 4-wire cable |
| USB-C power | Bulgin PX0441/B/4M00 | IP68 | Panel mount | 1 | 5V input feedthrough |
| pH BNC external | Amphenol 31-221-RFX | IP67 | Panel mount | 1 | External probe connector |
| Relay mains cables (W6, W7) | Wiska ClikPlug M20 | IP68 | 8–14 mm | 2 | 230 VAC load cables; enter on the MAINS side of the box, away from sensor glands |

**Mains wiring inside the enclosure**: keep 230 VAC load cables on the MAINS side of the box, tied down so a loose conductor cannot reach the SELV side of the PCB. Double-insulated cable (sheath stripped only as far as needed at W6/W7). If the enclosure has any metal parts (e.g. mounting plate), they must be earthed by the electrician.

**⚠ Enclosure size**: the Hammond 1554T2GYCL (115 × 65 mm external) is smaller than the 100 × 80 mm PCB — re-check enclosure choice before finalising the board outline.

---

## BNC Panel Mount

The PCB uses a right-angle PCB-mount BNC for internal connection. The external BNC on the enclosure wall is a separate panel-mount connector connected via a short RG174 coaxial pigtail (50–100 mm).

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
