"""JLCPCB fabrication + SMD assembly files for sensor_hub.kicad_pcb.
Run from the repo root:  python3 hardware/tools/jlc_export.py
Writes hardware/fab/: gerbers.zip (Gerbers + drill), bom_jlc.csv, cpl_jlc.csv.

Only SMD parts are assembled by JLCPCB; THT parts (Pico sockets, relays, Wago
terminals, BNC, X2 caps, UART header) are hand-soldered. DNP parts are skipped.
LCSC numbers checked against JLCPCB stock on 2026-09-28."""
import csv, os, subprocess, sys, tempfile, zipfile
from collections import defaultdict
import pcbnew

F = "hardware/kicad/sensor_hub.kicad_pcb"
OUT = "hardware/fab"

# (value, footprint name) -> LCSC part number.  "base" = JLC basic part (no setup fee)
LCSC = {
    ("100nF", "C_0603_1608Metric"): "C14663",          # base  CC0603KRX7R9BB104 50V X7R
    ("1uF", "C_0603_1608Metric"): "C15849",            # base  CL10A105KB8NNNC 50V X5R
    ("10uF", "C_0805_2012Metric"): "C15850",           # base  CL21A106KAYNNNE 25V X5R
    ("10M", "R_0603_1608Metric"): "C7250",             # base  0603WAF1005T5E 1%
    ("100k", "R_0603_1608Metric"): "C25803",           # base  0603WAF1003T5E 1%
    ("10k", "R_0603_1608Metric"): "C25804",            # base  0603WAF1002T5E 1%
    ("4k7", "R_0603_1608Metric"): "C23162",            # base  0603WAF4701T5E 1%
    ("1k", "R_0603_1608Metric"): "C21190",             # base  0603WAF1001T5E 1%
    ("100R", "R_1206_3216Metric"): "C17901",           # base  1206W4F1000T5E 200 V
    ("BAV99", "SOT-23"): "C2500",                      # base  BAV99,215
    ("1N4148W", "D_SOD-123"): "C81598",                # base
    ("BC817-40", "SOT-23"): "C52801",                  # ext   BC817-40,215 (Nexperia)
    ("BSS84PXUMA1", "SOT-23"): "C152212",              # ext   BSS84PH6327 (same Infineon die)
    ("ADS1115IDGSR", "MSOP-10_3x3mm_P0.5mm"): "C37593",  # ext
    ("AD8603AUJZ", "TSOT-23-5"): "C14937",             # ext   AD8603AUJZ-REEL7
    ("AP2112K-3.3TRG1", "SOT-23-5"): "C51118",         # ext
    ("VEML7700-TT", "VEML7700_TT"): "C1850416",        # ext
}

b = pcbnew.LoadBoard(F)
os.makedirs(OUT, exist_ok=True)

smd = []
for f in b.GetFootprints():
    if not f.GetAttributes() & pcbnew.FP_SMD or f.IsDNP() or f.IsExcludedFromBOM():
        continue
    key = (f.GetValue(), str(f.GetFPID().GetLibItemName()))
    if key not in LCSC:
        sys.exit("no LCSC part for %s %s" % (f.GetReference(), key))
    smd.append((f, key))

# ── BOM: Comment, Designator, Footprint, LCSC Part # ──────────────────────────
groups = defaultdict(list)
for f, key in smd:
    groups[key].append(f.GetReference())
nat = lambda r: (r.rstrip("0123456789"), int(r[len(r.rstrip("0123456789")):] or 0))
with open(os.path.join(OUT, "bom_jlc.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for key in sorted(groups, key=lambda k: nat(sorted(groups[k], key=nat)[0])):
        w.writerow([key[0], ",".join(sorted(groups[key], key=nat)), key[1], LCSC[key]])

# ── CPL: Designator, Mid X, Mid Y, Layer, Rotation (KiCad pos convention, Y up) ──
with open(os.path.join(OUT, "cpl_jlc.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for f, _ in sorted(smd, key=lambda s: nat(s[0].GetReference())):
        p = f.GetPosition()
        w.writerow([f.GetReference(), "%.4fmm" % pcbnew.ToMM(p.x), "%.4fmm" % -pcbnew.ToMM(p.y),
                    "Top" if f.GetLayer() == pcbnew.F_Cu else "Bottom", "%g" % (f.GetOrientationDegrees() % 360)])

# ── Gerbers + drill -> gerbers.zip ────────────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    layers = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
    subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--layers", layers, "--subtract-soldermask",
                    "-o", tmp + "/", F], check=True, capture_output=True)
    subprocess.run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th",
                    "--generate-map", "--map-format", "gerberx2", "-o", tmp + "/", F], check=True, capture_output=True)
    with zipfile.ZipFile(os.path.join(OUT, "gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(os.listdir(tmp)):
            z.write(os.path.join(tmp, n), n)
        names = z.namelist()

print("SMD parts: %d in %d BOM lines" % (len(smd), len(groups)))
print("gerbers.zip:", ", ".join(names))
