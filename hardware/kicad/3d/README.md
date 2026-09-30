# 3D models (not in git)

KiCad ships no 3D models for these parts, and the vendor models may not be
redistributed (vendor terms of use), so the STEP files are `.gitignore`d.
Download them once into this folder under exactly these names;
`tools/place_pcb.py` points the footprints at `${KIPRJMOD}/3d/<name>` and
sets rotation/offset for each.

| File name | Part | Used by | Source (format: STEP AP214) |
|---|---|---|---|
| `Wago_2601-1102.step` | Wago 2601-1102 | J9 | wago.com → product → CAD (partcommunity); entry "2601-1102 bis 2601-1112", pick 1102 |
| `Wago_2601-1103.step` | Wago 2601-1103 | J2–J6 | same entry, pick 1103 (not the colour-coded 2601-1103/987-100) |
| `Wago_2601-1104.step` | Wago 2601-1104 | J8 | same entry, pick 1104 |
| `Wago_236-403.step` | Wago 236-403 | J7, J10 | wago.com → 236-403 → CAD |
| `Omron_G2RL-14-E.step` | Omron G2RL-14-E DC5 | K1, K2 | TraceParts / omron.com (the sealed -14-E; same body and pins as the -1-E we fit) |
| `TE_BNC_1-1478035-0.step` | TE 1-1478035-0 | J1 | te.com → 1-1478035-0 → Customer View Model `…3d_stp.zip` |

Only the model files matter for the 3D view and the enclosure design; Gerbers
and the JLCPCB files do not depend on them.
