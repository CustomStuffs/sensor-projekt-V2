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
    for t in [TR[i] for i in range(len(TR))]: b.Delete(t)
    for z in zones():
        if z.GetZoneName().startswith(("TEMP_", "GND", "GUARD")): b.Delete(z)

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

    # ── 3V3_ANA: leave U2 pin 8 thin (0.5 mm pitch), then Power width to C7 ─────
    u2, c7 = pad("U2", "8"), pad("C7", "1")
    track([u2, (u2[0] + 1.2, u2[1])], "/3V3_ANA", 0.25)
    track([(u2[0] + 1.2, u2[1]), (u2[0] + 1.2 + (c7[1] - u2[1]), c7[1]), c7], "/3V3_ANA", 0.5)

    # ── spare GPIO U1 -> J11: down the 1.2 mm gap between the antenna keepout (x 46.8)
    # and the right pin row, two lanes per layer, then straight to J11 under the Pico.
    # Leaves the channel right of the Pico to the autorouter (pins 21-25 escape there).
    # Per layer: upper Pico pin = inner lane = upper run, dropping further left, so
    # nothing crosses.
    j = {n: pad("J11", n) for n in ("7", "8", "9", "10", "12")}
    mid = lambda a, c: (a + c) / 2
    for layer, pairs in ((pcbnew.B_Cu, (("27", "8", "/GP21", j["8"][0]),
                                        ("26", "7", "/GP20", mid(j["8"][0], j["10"][0])))),
                         (pcbnew.F_Cu, (("31", "10", "/GP26", j["10"][0]),
                                        ("29", "9", "/GP22", mid(j["10"][0], j["12"][0]))))):
        for i, (up, jp, nm, drop_x) in enumerate(pairs):
            s, e = pad("U1", up), j[jp]
            lane, run = 47.2 + 0.43 * i, 56.0 + 0.45 * i       # U1's own antenna keepout ends at x 46.99
            pts = [s, (lane, s[1]), (lane, run), (drop_x, run), (drop_x, e[1])]
            if drop_x != e[0]: pts.append(e)
            track(pts, nm, 0.25, layer)

    # ── guard pour on B.Cu needs its own connection to PH_BUF (U4 pin 4) ──────
    u4p4 = pad("U4", "4"); gv = (u4p4[0] + 1.26, u4p4[1])
    track([u4p4, gv], "/PH_BUF", 0.25)
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(*gv)); v.SetWidth(MM(0.8)); v.SetDrill(MM(0.4))
    v.SetNet(net("/PH_BUF")); v.SetLocked(True); b.Add(v)

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

elif stage == "fixclear":
    # Freerouting rounds geometry and now and then lands a few µm under a clearance. Take
    # those violations from a kicad-cli JSON DRC report (argv[2]) and make the offending
    # tracks 0.01 mm narrower (never below 0.2 mm); the routing itself does not change.
    import json, re
    rep = json.load(open(DSN))
    uuids = set()
    for v in rep.get("violations", []):
        m = re.search(r"clearance ([\d.]+) mm; actual ([\d.]+) mm", v.get("description", ""))
        if v.get("type") != "clearance" or not m or float(m.group(1)) - float(m.group(2)) > 0.01:
            continue
        uuids |= {it["uuid"] for it in v.get("items", []) if it.get("description", "").startswith("Track")}
    TR = b.Tracks(); n = 0
    for t in [TR[i] for i in range(len(TR))]:
        if t.m_Uuid.AsString() in uuids and t.GetWidth() >= MM(0.21):
            t.SetWidth(t.GetWidth() - MM(0.01)); n += 1
    if n:
        pcbnew.ZONE_FILLER(b).Fill(zones()); b.Save(F)
    print("fixclear: narrowed %d track(s)" % n)

else:  # finish
    TR = b.Tracks()                                # before any zone access: that breaks TRACKS wrappers
    for t in [TR[i] for i in range(len(TR))]:
        if t.GetClass() == "PCB_TRACK" and t.GetWidth() < MM(0.2): t.SetWidth(MM(0.2))
    # Freerouting leaves vias/stubs that connect on one side only: strip them (signal nets only;
    # vias on pour nets are stitching). Repeat until nothing more dangles.
    POUR = {"/GND", "/GND_ANA", "/PH_BUF"}
    tol = MM(0.01)
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads(): pads.setdefault(p.GetNetname(), []).append(p)
    removed = 0
    while True:
        TR = b.Tracks(); items = [TR[i] for i in range(len(TR))]
        segs = [x for x in items if x.GetClass() == "PCB_TRACK"]
        vias = [x for x in items if x.GetClass() == "PCB_VIA"]
        def hit(pt, n, layer, skip):
            if any(p.IsOnLayer(layer) and p.HitTest(pt, tol) for p in pads.get(n, [])): return True
            if any(v is not skip and v.GetNetname() == n and v.HitTest(pt, tol) for v in vias): return True
            return any(s is not skip and s.GetNetname() == n and s.GetLayer() == layer and s.HitTest(pt, tol) for s in segs)
        dead = [v for v in vias if v.GetNetname() not in POUR and not v.IsLocked()
                and not all(hit(v.GetPosition(), v.GetNetname(), L, v) for L in (pcbnew.F_Cu, pcbnew.B_Cu))]
        dead += [s for s in segs if s.GetNetname() not in POUR and not s.IsLocked()
                 and not all(hit(pt, s.GetNetname(), s.GetLayer(), s) for pt in (s.GetStart(), s.GetEnd()))]
        if not dead: break
        for x in dead: b.Delete(x)
        removed += len(dead)
    print("removed dangling vias/stubs:", removed)

    for z in zones():
        if z.GetZoneName().startswith(("TEMP_", "GND", "GUARD")): b.Delete(z)   # rerunnable
    board = rectpts(0.3, 0.3, 99.7, 99.7)
    ana = rectpts(0.3, 11.0, 27.6, 77.5)          # analog column: LDO out, ADC, pH, NTC
    guard = rectpts(15.8, 45.0, 28.2, 51.2)       # around R1 / D1 / U4 (+ NODE_A)
    for L in (pcbnew.F_Cu, pcbnew.B_Cu):
        poly_zone("GND", "/GND", L, board, 0)
        poly_zone("GND_ANA", "/GND_ANA", L, ana, 1)
        poly_zone("GUARD_PH", "/PH_BUF", L, guard, 2, clearance=0.3)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(zones())

    # Exposed guard on F.Cu (NODE_A side): solder mask absorbs moisture and leaks, bare
    # (ENIG) guard copper does not. Opening = guard fill shrunk by 0.1 mm, so the mask
    # still covers the clearance gaps, NODE_A and every foreign pad/track.
    DR = b.Drawings()
    for d in [DR[i] for i in range(len(DR))]:
        if d.GetLayer() == pcbnew.F_Mask: b.Delete(d)
    for z in zones():
        if z.GetZoneName() == "GUARD_PH" and z.GetLayer() == pcbnew.F_Cu:
            fill = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(pcbnew.F_Cu))
            fill.Deflate(MM(0.1), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MM(0.005))
            silk = pcbnew.SHAPE_POLY_SET()                 # keep mask under footprint silkscreen
            for f in b.GetFootprints():
                GI = f.GraphicalItems()
                texts = [t for t in (f.Reference(), f.Value()) if t.IsVisible()]
                for g in [GI[i] for i in range(len(GI))] + texts:
                    if g.GetLayer() == pcbnew.F_SilkS:
                        g.TransformShapeToPolygon(silk, pcbnew.F_SilkS, MM(0.15), MM(0.005), pcbnew.ERROR_OUTSIDE)
            fill.BooleanSubtract(silk)
            fill.Simplify()
            for i in range(fill.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(fill.Outline(i))
                for h in range(fill.HoleCount(i)): one.AddHole(fill.Hole(i, h))
                one.thisown = False
                s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_POLY); s.SetPolyShape(one)
                s.SetFilled(True); s.SetWidth(0); s.SetLayer(pcbnew.F_Mask); b.Add(s)
            print("guard mask openings:", fill.OutlineCount())
    b.Save(F)
    print("post done")
