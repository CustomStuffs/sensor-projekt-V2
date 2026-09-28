"""First-pass board setup for sensor_hub.kicad_pcb (KiCad 10 pcbnew API).
Outline 100x100, mounting holes, isolation slots, rule areas, zone-based placement.
Board coordinates: (0,0) = top-left board corner = page (OX, OY)."""
import pcbnew

import sys
F = sys.argv[1] if len(sys.argv) > 1 else "hardware/kicad/sensor_hub.kicad_pcb"
b = pcbnew.LoadBoard(F)
MM = pcbnew.FromMM
OX, OY, W, H = 40.0, 40.0, 100.0, 100.0
def FP(ref):
    for f in b.GetFootprints():
        if f.GetReference() == ref: return f
    raise KeyError(ref)
P = lambda x, y: pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))

# ── clean previous generated items (idempotent) ─────────────────────────────
DR = b.Drawings()
for d in [DR[i] for i in range(len(DR))]:
    if d.GetLayer() in (pcbnew.Edge_Cuts,) or (d.GetLayer() == pcbnew.F_SilkS and d.GetClass() == "PCB_TEXT"):   # Drawings() yields plain BOARD_ITEMs
        b.Delete(d)
for z in list(b.Zones()):
    b.Delete(z)
for f in list(b.GetFootprints()):
    if f.GetReference() in ("H1", "H2", "H3", "H4"):
        b.Delete(f)

def rect(x0, y0, x1, y1, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(P(x0, y0)); s.SetEnd(P(x1, y1)); s.SetLayer(layer); s.SetWidth(MM(w)); b.Add(s)

rect(0, 0, W, H)                                  # board outline
rect(62.0, 11.0, 84.0, 13.0)                      # isolation slot under K1: coil (top) | contacts
rect(62.0, 53.3, 84.0, 55.3)                      # isolation slot under K2: contacts | coil (bottom)

# ── footprint swaps (keep nets / UUID path; schematic carries the same footprint) ──
def swap(ref, lib, name, value, fallback_pad=None):
    old = FP(ref)
    if old.GetFPIDAsString() == "%s:%s" % (lib, name): return
    new = pcbnew.FootprintLoad("/usr/share/kicad/footprints/%s.pretty" % lib, name)
    new.SetFPID(pcbnew.LIB_ID(lib, name))
    new.SetReference(ref); new.SetValue(value); new.SetPath(old.GetPath())
    new.GetField(pcbnew.FIELD_T_DESCRIPTION).SetText(old.GetField(pcbnew.FIELD_T_DESCRIPTION).GetText())
    nets = {p.GetNumber(): p.GetNet() for p in old.Pads()}
    b.Add(new)
    for p in new.Pads():
        p.SetNet(nets.get(p.GetNumber()) or nets.get(fallback_pad))
    b.Delete(old)
swap("J1", "Connector_Coaxial", "BNC_TEConnectivity_1478035_Horizontal", "1-1478035-0", "2")   # all shell pads = shield
# push-in instead of screw terminals, same Wago 2601 family as the sensor ports
swap("J8", "TerminalBlock_WAGO", "TerminalBlock_WAGO_2601-1104_1x04_P3.50mm_Horizontal", "Wago-EC4pin")
swap("J9", "TerminalBlock_WAGO", "TerminalBlock_WAGO_2601-1102_1x02_P3.50mm_Horizontal", "Wago-Power")

# ── manufacturer 3D models (KiCad ships none for these). The STEP files are NOT in git
# (vendor terms): download them into kicad/3d/, see kicad/3d/README.md. All vendor models
# are Y-up; offsets put their pin 1 on the footprint's pad 1 (pins read from the STEP files).
def model(ref, name, off, rot=(-90, 0, 90)):          # KiCad angles are clockwise-positive
    m = pcbnew.FP_3DMODEL(); m.m_Filename = "${KIPRJMOD}/3d/" + name
    m.m_Offset = pcbnew.VECTOR3D(*off); m.m_Rotation = pcbnew.VECTOR3D(*rot); m.m_Scale = pcbnew.VECTOR3D(1, 1, 1)
    ms = FP(ref).Models(); ms.clear(); ms.push_back(m)
model("J9", "Wago_2601-1102.step", (4.56, 0.08, 0))
for r in ("J2", "J3", "J4", "J5", "J6"):
    model(r, "Wago_2601-1103.step", (8.06, 0.08, 0))
model("J8", "Wago_2601-1104.step", (11.56, 0.08, 0))
for r in ("J7", "J10"):
    model(r, "Wago_236-403.step", (13.1, 0, 0))
for r in ("K1", "K2"):
    model(r, "Omron_G2RL-14-E.step", (3.75, -12.2, 0))       # -14-E = sealed -1-E, same body/pins
model("J1", "TE_BNC_1-1478035-0.step", (0, 16.9, 13.1), (-90, 0, 180))   # housing base at model y=-13.1

# ── mounting holes (M3, no copper) ─────────────────────────────────────────
for i, (x, y) in enumerate([(3.5, 3.5), (3.5, 96.5), (96.5, 96.5), (96.5, 3.5)], 1):
    h = pcbnew.FootprintLoad("/usr/share/kicad/footprints/MountingHole.pretty", "MountingHole_3.2mm_M3")
    h.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
    h.SetReference("H%d" % i); h.SetPosition(P(x, y)); h.SetBoardOnly(True); h.SetExcludedFromBOM(True); b.Add(h)

# ── placement helpers ──────────────────────────────────────────────────────
def crt(f):
    c = f.GetCourtyard(pcbnew.F_CrtYd)
    return c.BBox() if not c.IsEmpty() else f.GetBoundingBox(False)

def tl(ref, rot, x, y):
    """courtyard top-left at board (x, y)"""
    f = FP(ref); f.SetOrientationDegrees(rot)
    f.SetPosition(P(0, 0)); bb = crt(f)
    f.Move(pcbnew.VECTOR2I(P(x, y).x - bb.GetLeft(), P(x, y).y - bb.GetTop()))

def ctr(ref, rot, x, y):
    """courtyard centre at board (x, y)"""
    f = FP(ref); f.SetOrientationDegrees(rot)
    f.SetPosition(P(0, 0)); bb = crt(f)
    f.Move(pcbnew.VECTOR2I(P(x, y).x - bb.GetCenter().x, P(x, y).y - bb.GetCenter().y))

# POWER (top left) — J9 wire entry toward top edge
tl("J9", 180, 8.5, 0.3)
for ref, x in (("C13", 4), ("C11", 8), ("C14", 12), ("C17", 16), ("C8", 20)):
    ctr(ref, 90, x, 17.8)
ctr("U5", 0, 12, 23)
for ref, x in (("C15", 4), ("C18", 8), ("C12", 12)):
    ctr(ref, 90, x, 28.3)
ctr("R10", 90, 23, 5); ctr("R11", 90, 26, 5)           # I2C pull-ups near Pico GP2/GP3
ctr("U6", 0, 21.5, 24.5); ctr("C9", 0, 21.5, 28.5)       # light sensor
# ADC
ctr("U2", 0, 12, 34); ctr("C7", 90, 18.5, 34); ctr("C16", 90, 22.5, 34); ctr("NT1", 0, 12, 38.5)
# pH FRONT-END (BNC at left edge, opening to -x)
bnc = FP("J1"); bnc.SetOrientationDegrees(90)
bnc.SetPosition(P(7.6, 52))                             # housing front face on the board edge
ctr("R1", 0, 19, 47); ctr("D1", 0, 19, 51.5); ctr("U4", 0, 24.5, 49); ctr("C2", 90, 25, 54)
ctr("R2", 90, 17, 57); ctr("R3", 90, 20.5, 57); ctr("C1", 90, 24, 58.5)
# NTC + EC (DNP) above J8
for ref, x in (("R7", 9), ("C6", 12.5), ("R15", 16), ("C3", 19.5), ("R16", 23), ("C4", 26.5), ("C5", 30)):
    ctr(ref, 90, x, 72)
# MCU (USB end at top edge)
u1 = FP("U1"); u1.SetOrientationDegrees(0); u1.SetPosition(P(31, 4))
tl("J11", 90, 29.5, 57.5)
tl("HDR1", 90, 66, 68)
# RELAYS: MAINS band in the middle, coils in SELV strips above (K1) and below (K2).
# Contact rows line up with the terminal rows -> straight mains tracks.
def at(ref, rot, x, y):
    f = FP(ref); f.SetOrientationDegrees(rot); f.SetPosition(P(x, y))
at("K1", 0, 70, 4)          # A1 (70,4) A2 (77.5,4); NC y19, COM y24, NO y29
at("K2", 180, 77.5, 62.3)   # A1 (77.5,62.3) A2 (70,62.3); NO y37.3, COM y42.3, NC y47.3
at("J7", 90, 90.5, 29)      # pin1 NO y29, pin2 COM y24, pin3 NC y19 (wire entry right edge)
at("J10", 90, 90.5, 47.3)   # pin1 NC y47.3, pin2 COM y42.3, pin3 NO y37.3
at("C19", 270, 61.5, 19)    # pad1 SNUB (61.5,19), pad2 K1_NO (61.5,29)
at("C20", 90, 61.5, 47.3)   # pad1 SNUB (61.5,47.3), pad2 K2_NO (61.5,37.3)
ctr("R19", 90, 66, 24)      # pad1 K1_COM below, pad2 SNUB above
ctr("R20", 270, 66, 44)     # pad1 K2_COM above, pad2 SNUB below
# relay drivers: K1 in the top SELV strip, K2 in the bottom SELV strip
ctr("C10", 90, 53.5, 5); ctr("Q1", 0, 58, 4); ctr("R8", 0, 58, 8.5); ctr("D2", 0, 63.5, 4)
ctr("Q3", 0, 58, 62); ctr("R18", 0, 58, 66); ctr("D3", 0, 63.5, 62.3)
# SENSOR PORTS along bottom edge (wire entry toward bottom edge)
for ref, x in (("J2", 23.8), ("J3", 37.5), ("J4", 51.2), ("J5", 64.9), ("J6", 78.6)):
    tl(ref, 0, x, 84.2)
tl("J8", 0, 7.0, 84.2)                            # same row/depth as J2-J6, clear of H2
ctr("R5", 0, 30, 80.5); ctr("R6", 0, 43.5, 80.5); ctr("R9", 0, 55, 80.5)
ctr("Q2", 0, 61, 78); ctr("R17", 0, 61, 74)

# terminal pin -> net (matches the schematic after the W6/W7 re-mapping)
NETS = {n: b.FindNet(n) for n in ("/K1_NO", "/K1_COM", "/K1_NC", "/K2_NC", "/K2_COM", "/K2_NO")}
for ref, m in (("J7", {"1": "/K1_NO", "2": "/K1_COM", "3": "/K1_NC"}), ("J10", {"1": "/K2_NC", "2": "/K2_COM", "3": "/K2_NO"})):
    for pd in FP(ref).Pads():
        pd.SetNet(NETS[m[pd.GetNumber()]])

# ── rule areas ─────────────────────────────────────────────────────────────
def rule_area(name, x0, y0, x1, y1, no_pour=True, no_vias=True, no_tracks=False):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    z.SetDoNotAllowZoneFills(no_pour); z.SetDoNotAllowVias(no_vias); z.SetDoNotAllowTracks(no_tracks)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    o = z.Outline(); o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(P(x, y).x, P(x, y).y)
    b.Add(z)
rule_area("MAINS_keepout", 57.5, 13.0, 100, 53.3)            # no pour, no vias in MAINS band
rule_area("PicoW_antenna_keepout", 33.0, 42, 46.8, 55.5, no_tracks=True)   # antenna end of Pico W, between the pin rows only

# ── silkscreen labels ──────────────────────────────────────────────────────
def silk(t, x, y, size=1.2, rot=0):
    s = pcbnew.PCB_TEXT(b); s.SetText(t); s.SetPosition(P(x, y)); s.SetLayer(pcbnew.F_SilkS)
    s.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); s.SetTextThickness(MM(size * 0.15))
    s.SetTextAngleDegrees(rot); b.Add(s)
for t, x in (("W1 DS18B20", 30.4), ("W2 DHT22", 44.1), ("W3 PIR", 57.8), ("W4 GP16", 71.5), ("W5 GP17", 85.2)):
    silk(t, x, 86.3, 1.0)                        # inside the terminal outline, above the pins
silk("EC  W Y R B", 15.3, 86.3, 1.0)                # inside the J8 outline, like W1-W5
silk("W6 RELAY1", 92.5, 13.9, 1.0); silk("W7 RELAY2", 92.5, 52.1, 1.0)
for t_, y_ in (("NC", 19), ("COM", 24), ("NO", 29), ("NO", 37.3), ("COM", 42.3), ("NC", 47.3)):
    silk(t_, 81.5, y_, 0.9)                      # on the (masked) mains track it names
silk("! 230 VAC max 5 A", 73.5, 33.2, 1.2)
silk("PH", 3, 43, 1.2); silk("5V IN", 5.2, 11.0, 1.0)
silk("Sensor Hub V2.0  2026-09", 80, 74, 1.2)

# reference fields that would land on neighbours
def ref_at(ref, x, y, rot, size=None):
    r = FP(ref).Reference(); r.SetPosition(P(x, y)); r.SetTextAngleDegrees(rot)
    if size: r.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); r.SetTextThickness(MM(size * 0.15))
ref_at("C19", 57.25, 24.0, 90)                   # left of the cap, like C20
ref_at("R19", 66.0, 20.9, 0, 0.8)                # no room beside R19 (C19 | K1 outline)
ref_at("R20", 66.0, 47.1, 0, 0.8)
ref_at("J9", 19.8, 8.0, 90)                      # beside the (deep) Wago, not on the cap row below

b.Save(F)
print("saved")
