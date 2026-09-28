"""Routing for sensor_hub.kicad_pcb.  usage: route_pcb.py pre|post <dsn> <ses> [board]
stage 'pre'  : clear tracks, hand-route MAINS + NODE_A, add temp keepout, export DSN
stage 'post' : import SES, remove temp keepout, add GND / GND_ANA / guard zones, fill, save"""
import sys, pcbnew

F = sys.argv[4] if len(sys.argv) > 4 else "hardware/kicad/sensor_hub.kicad_pcb"
DSN, SES = sys.argv[2], sys.argv[3]
stage = sys.argv[1]
b = pcbnew.LoadBoard(F)
MM = pcbnew.FromMM
OX = OY = 40.0
P = lambda x, y: pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))

def FP(ref):
    for f in b.GetFootprints():
        if f.GetReference() == ref: return f
    raise KeyError(ref)

def pad(ref, num, near=None):
    """pad position in board coords; for duplicated pad numbers pick the one nearest `near`"""
    ps = [p for p in FP(ref).Pads() if p.GetNumber() == num]
    xy = [(pcbnew.ToMM(p.GetPosition().x) - OX, pcbnew.ToMM(p.GetPosition().y) - OY) for p in ps]
    if near: xy.sort(key=lambda q: (q[0] - near[0]) ** 2 + (q[1] - near[1]) ** 2)
    return xy[0]

def net(name): return b.FindNet(name)

def track(pts, netname, w, layer=pcbnew.F_Cu, locked=True):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(x0, y0)); t.SetEnd(P(x1, y1))
        t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(net(netname)); t.SetLocked(locked); b.Add(t)

def poly_zone(name, netname, layer, pts, prio, clearance=0.3, keepout=False, tracks_ok=False):
    z = pcbnew.ZONE(b); z.SetZoneName(name); z.SetLayer(pcbnew.F_Cu if layer is None else layer)
    if keepout:
        z.SetIsRuleArea(True); z.SetDoNotAllowTracks(not tracks_ok); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    else:
        z.SetNet(net(netname)); z.SetAssignedPriority(prio)
        z.SetLocalClearance(MM(clearance)); z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.4)); z.SetThermalReliefSpokeWidth(MM(0.5))
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in pts: ch.Append(P(x, y).x, P(x, y).y)
    ch.SetClosed(True)
    o = pcbnew.SHAPE_POLY_SET(); o.AddOutline(ch); o.thisown = False; z.SetOutline(o)   # zone owns it
    b.Add(z)
    return z

def rectpts(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def zones():
    return [b.Zones()[i] for i in range(len(b.Zones()))] if not isinstance(b.Zones(), tuple) else list(b.Zones())

if stage == "pre":
    TR = b.Tracks()
    for t in [TR[i] for i in range(len(TR))]: b.Remove(t)
    for z in zones():
        if z.GetZoneName().startswith(("TEMP_", "GND", "GUARD")): b.Remove(z)

    # antenna keepout only between the pin rows (was over the pads -> pins 15-26 unroutable)
    for z in zones():
        if z.GetZoneName() == "PicoW_antenna_keepout":
            bb = z.GetBoundingBox(); y0 = pcbnew.ToMM(bb.GetTop()) - OY; y1 = pcbnew.ToMM(bb.GetBottom()) - OY
            ch = pcbnew.SHAPE_LINE_CHAIN()
            for x, y in rectpts(33.0, y0, 46.8, y1): ch.Append(P(x, y).x, P(x, y).y)
            ch.SetClosed(True)
            o = pcbnew.SHAPE_POLY_SET(); o.AddOutline(ch); o.thisown = False; z.SetOutline(o)   # zone owns it

    # ── MAINS: straight rows relay -> terminal, 3 mm; snubber links 0.8-1.0 mm ──
    for K, J, rows in (("K1", "J7", (("11", "2", "/K1_COM"), ("12", "3", "/K1_NC"), ("14", "1", "/K1_NO"))),
                       ("K2", "J10", (("11", "2", "/K2_COM"), ("12", "1", "/K2_NC"), ("14", "3", "/K2_NO")))):
        for kp, jp, n in rows:
            a = pad(K, kp, (69, 0)); c = pad(K, kp, (78, 0)); y = a[1]
            j1 = pad(J, jp, (90, y)); j2 = pad(J, jp, (96, y))
            a = pad(K, kp, (69, y)); c = pad(K, kp, (78, y))
            track([a, c, j1, j2], n, 3.0)
    # K1 snubber: R19 1 = COM, 2 = SNUB ; C19 1 = SNUB, 2 = NO
    track([pad("R19", "1"), pad("K1", "11", (69, 24))], "/K1_COM", 0.8)
    track([pad("R19", "2"), pad("C19", "1")], "/K1_SNUB", 0.8)
    track([pad("C19", "2"), pad("K1", "14", (69, 29))], "/K1_NO", 1.0)
    # K2 snubber
    track([pad("R20", "1"), pad("K2", "11", (69, 42))], "/K2_COM", 0.8)
    track([pad("R20", "2"), pad("C20", "1")], "/K2_SNUB", 0.8)
    track([pad("C20", "2"), pad("K2", "14", (69, 37))], "/K2_NO", 1.0)

    # ── NODE_A: short, direct, inside the future guard pour ─────────────────
    r1, d1, u4 = pad("R1", "2"), pad("D1", "3"), pad("U4", "3")
    knee = (r1[0], u4[1])                          # straight down from R1, then across to U4 +IN
    track([r1, knee, u4], "/NODE_A", 0.25)
    track([knee, d1], "/NODE_A", 0.25)

    # ── temporary track keepouts for the autorouter ─────────────────────────
    # MAINS band + 8 mm margin (SELV copper must stay >= 8 mm from MAINS copper)
    poly_zone("TEMP_MAINS", None, None, rectpts(52.6, 10.3, 100, 56.0), 0, keepout=True)

    pcbnew.ExportSpecctraDSN(b, DSN)
    b.Save(F)
    print("pre done")

elif stage == "post":
    # SES import leaves pcbnew's SWIG wrappers unusable for the rest of the process,
    # so only import + save here and do the rest in a fresh interpreter ('finish')
    ok = pcbnew.ImportSpecctraSES(b, SES)
    print("SES import:", ok)
    b.Save(F)
    import subprocess
    sys.exit(subprocess.call([sys.executable, __file__, "finish", DSN, SES, F]))

else:  # finish
    TR = b.Tracks()                                # before any zone access: that breaks TRACKS wrappers
    for t in [TR[i] for i in range(len(TR))]:
        if t.GetClass() == "PCB_TRACK" and t.GetWidth() < MM(0.2): t.SetWidth(MM(0.2))
    for z in zones():
        if z.GetZoneName().startswith("TEMP_"): b.Remove(z)
    board = rectpts(0.3, 0.3, 99.7, 99.7)
    ana = rectpts(0.3, 11.0, 27.6, 77.5)          # analog column: LDO out, ADC, pH, NTC
    guard = rectpts(15.8, 45.0, 28.2, 51.2)       # around R1 / D1 / U4 (+ NODE_A)
    for L in (pcbnew.F_Cu, pcbnew.B_Cu):
        poly_zone("GND", "/GND", L, board, 0)
        poly_zone("GND_ANA", "/GND_ANA", L, ana, 1)
        poly_zone("GUARD_PH", "/PH_BUF", L, guard, 2, clearance=0.3)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(zones())
    b.Save(F)
    print("post done")
