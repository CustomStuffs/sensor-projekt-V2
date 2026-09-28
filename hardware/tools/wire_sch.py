"""Wire sensor_hub.kicad_sch per docs/schematic.md: short stub + net label on every pin,
no-connect flags on unused pins, net tie GND_ANA<->GND at the ADS1115, PWR_FLAGs.
Idempotent: removes previously generated wires/labels/no_connects/flags first."""
import re, uuid

F = "hardware/kicad/sensor_hub.kicad_sch"
s = open(F).read()
U = lambda: str(uuid.uuid4())
G = 2.54
snap = lambda v: round(round(v / G) * G, 4)
fmt = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')

# ── Nets (ref -> {pin: net}); "NC" = no-connect flag ─────────────────────────
N = {}
def c(ref, **pins): N[ref] = {k.lstrip('p'): v for k, v in pins.items()}
def two(ref, a, b): N[ref] = {"1": a, "2": b}

# Power
two("J9", "VSYS", "GND")
for r in ("C13", "C11"): two(r, "VSYS", "GND")
for r in ("C14", "C17", "C8"): two(r, "VSYS", "GND_ANA")
c("U5", p1="VSYS", p3="VSYS", p2="GND_ANA", p4="NC", p5="3V3_ANA")
for r in ("C15", "C18", "C12"): two(r, "3V3_ANA", "GND_ANA")
# pH front-end
two("J1", "PH_IN", "VREF_MID")                       # 1 = center, 2 = shield
two("R1", "PH_IN", "NODE_A")
c("D1", p1="GND_ANA", p2="3V3_ANA", p3="NODE_A")     # BAV99: 3 = common node
c("U4", p3="NODE_A", p4="PH_BUF", p1="PH_BUF", p5="3V3_ANA", p2="GND_ANA")
two("C2", "3V3_ANA", "GND_ANA")
two("R2", "3V3_ANA", "VREF_MID")
two("R3", "VREF_MID", "GND_ANA")
two("C1", "VREF_MID", "GND_ANA")
# NTC + EC (EC DNP)
c("J8", p1="NC", p2="NC", p3="NODE_NTC", p4="GND_ANA")
two("R7", "3V3_ANA", "NODE_NTC")
two("C6", "NODE_NTC", "GND_ANA")
two("R15", "EC_PWM_A", "EC_EXC_A"); two("C3", "EC_EXC_A", "GND")
two("R16", "EC_PWM_B", "EC_EXC_B"); two("C4", "EC_EXC_B", "GND")
two("C5", "3V3_DIG", "GND")
# ADC + light + I2C
c("U2", p8="3V3_ANA", p3="GND_ANA", p1="GND_ANA", p2="NC", p4="PH_BUF", p5="NODE_NTC",
  p6="NC", p7="NC", p9="I2C_SDA", p10="I2C_SCL")
two("C16", "3V3_ANA", "GND_ANA"); two("C7", "3V3_ANA", "GND_ANA")
c("U6", p2="3V3_DIG", p3="GND", p1="I2C_SCL", p4="I2C_SDA")
two("C9", "3V3_DIG", "GND")
two("R10", "3V3_DIG", "I2C_SDA"); two("R11", "3V3_DIG", "I2C_SCL")
two("NT1", "GND_ANA", "GND")                         # single-point AGND/DGND join
# MCU
gp = {0: "UART_TX", 1: "UART_RX", 2: "I2C_SDA", 3: "I2C_SCL", 4: "GP4", 5: "GP5",
      6: "GP6", 7: "GP7", 8: "ONEWIRE", 9: "DHT_DATA", 10: "RELAY1_DRV", 11: "PIR_OUT",
      12: "PIR_EN_N", 13: "EC_PWM_A", 14: "EC_PWM_B", 15: "RELAY2_DRV", 16: "W4_SIG", 17: "W5_SIG"}
PICO_GP_PIN = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 16,
               13: 17, 14: 19, 15: 20, 16: 21, 17: 22, 18: 24, 19: 25, 20: 26, 21: 27, 22: 29,
               26: 31, 27: 32, 28: 34}
gp.update({g: "GP%d" % g for g in (18, 19, 20, 21, 22, 26, 27, 28)})   # spare GPIOs -> J11 breakout
u1 = {str(PICO_GP_PIN[g]): gp.get(g, "NC") for g in PICO_GP_PIN}
u1.update({"39": "VSYS", "40": "NC", "36": "3V3_DIG", "3": "GND", "33": "GND",
           "35": "NC", "30": "RUN", "37": "NC"})
u1.update({p: "GND" for p in ("8", "13", "18", "23", "28", "38")})   # stacked GND pins
N["U1"] = u1
c("HDR1", p1="UART_TX", p2="UART_RX", p3="GND", p4="3V3_DIG")
# J11: solder-hole breakout for spare Pico pins (no part fitted)
N["J11"] = {str(i + 1): n for i, n in enumerate(["GP4", "GP5", "GP6", "GP7", "GP18", "GP19", "GP20", "GP21",
                                                  "GP22", "GP26", "GP27", "GP28", "RUN", "3V3_DIG", "GND", "GND"])}
# Sensor ports + pull-ups + PIR gate
c("J2", p1="3V3_DIG", p2="GND", p3="ONEWIRE");   two("R5", "3V3_DIG", "ONEWIRE")
c("J3", p1="3V3_DIG", p2="GND", p3="DHT_DATA");  two("R6", "3V3_DIG", "DHT_DATA")
c("J4", p1="PIR_VCC", p2="GND", p3="PIR_OUT");   two("R9", "3V3_DIG", "PIR_OUT")
c("Q2", p1="PIR_EN_N", p2="3V3_DIG", p3="PIR_VCC"); two("R17", "3V3_DIG", "PIR_EN_N")
c("J5", p1="3V3_DIG", p2="GND", p3="W4_SIG")
c("J6", p1="3V3_DIG", p2="GND", p3="W5_SIG")
# Relays (G2RL: A1/A2 coil, 11 COM, 12 NC, 14 NO)
two("C10", "VSYS", "GND")
for k, q, rb, d, rs, cs, j, drv in (("1", "Q1", "R8", "D2", "R19", "C19", "J7", "RELAY1_DRV"),
                                     ("2", "Q3", "R18", "D3", "R20", "C20", "J10", "RELAY2_DRV")):
    K = "K" + k
    two(rb, drv, f"{q}_B")
    c(q, p1=f"{q}_B", p2="GND", p3=f"{K}_COIL")
    two(d, "VSYS", f"{K}_COIL")                      # 1 = K to VSYS, 2 = A to collector
    N[K] = {"A1": "VSYS", "A2": f"{K}_COIL", "11": f"{K}_COM", "12": f"{K}_NC", "14": f"{K}_NO"}
    two(rs, f"{K}_COM", f"{K}_SNUB"); two(cs, f"{K}_SNUB", f"{K}_NO")
    # terminal pin order follows the board geometry (straight mains tracks):
    # J7 (W6): 1 = NO, 2 = COM, 3 = NC   |   J10 (W7): 1 = NC, 2 = COM, 3 = NO
    if K == "K1": c(j, p1=f"{K}_NO", p2=f"{K}_COM", p3=f"{K}_NC")
    else:         c(j, p1=f"{K}_NC", p2=f"{K}_COM", p3=f"{K}_NO")
c("#FLG01", p1="VSYS"); c("#FLG02", p1="GND_ANA")

# ── Placement tweaks so labels have room (left blocks +10 mm etc.) ──────────
POS = {"J9": (35, 45), "C13": (48, 48), "C11": (56, 48), "C14": (66, 48), "C17": (74, 48), "C8": (82, 48),
       "U5": (100, 45), "C15": (125, 48), "C18": (133, 48), "C12": (141, 48),
       "#FLG01": (152, 40), "#FLG02": (165, 40),
       "J1": (35, 90), "R1": (50, 90), "D1": (80, 100), "U4": (110, 90), "C2": (130, 85),
       "R2": (45, 128), "R3": (58, 128), "C1": (71, 128),
       "J8": (35, 175), "R7": (52, 175), "C6": (64, 175), "R15": (85, 175), "C3": (97, 175),
       "R16": (109, 175), "C4": (121, 175), "U3": (115, 195), "C5": (135, 175),
       "C16": (205, 50), "C7": (213, 50), "C9": (260, 50), "NT1": (190, 82), "R10": (220, 88), "R11": (230, 88),
       "J2": (35, 245), "R5": (50, 235), "J3": (75, 245), "R6": (90, 235), "J4": (115, 245),
       "R9": (130, 235), "Q2": (155, 225), "R17": (182, 212), "J5": (190, 245), "J6": (220, 245),
       "R8": (278, 85), "R18": (278, 160), "J11": (250, 165)}

SYM = re.compile(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\).*?\n\t\)(?=\n)', re.S)
ref_of = lambda b: re.search(r'\(property "Reference" "([^"]*)"', b).group(1)

def move(b, x, y):
    ox, oy = map(float, re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+) ', b).groups())
    dx, dy = x - ox, y - oy
    return re.sub(r'\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)',
                  lambda m: '(at %s %s%s)' % (fmt(float(m.group(1)) + dx), fmt(float(m.group(2)) + dy), m.group(3) or ''), b)

# Drop previous generated content (idempotency)
s = SYM.sub(lambda m: "" if ref_of(m.group(0)) in ("NT1", "#FLG01", "#FLG02", "J11") else m.group(0), s)
for kw in ("wire", "label", "no_connect", "junction"):
    s = re.sub(r'\n\t\(%s\b.*?\n\t\)(?=\n)' % kw, "", s, flags=re.S)

# Embed library symbols for NetTie_2 / PWR_FLAG
def embed(libfile, name, libname):
    global s
    if '(symbol "%s:%s"' % (libname, name) in s: return
    t = open('/usr/share/kicad/symbols/%s.kicad_sym' % libfile).read()
    i = t.index('\t(symbol "%s"' % name); j = t.index('\n\t(symbol "', i + 5)
    blk = t[i:j].replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (libname, name), 1)
    blk = "\n".join("\t" + l for l in blk.split("\n"))
    k = s.index("\t(lib_symbols") + len("\t(lib_symbols")
    s = s[:k] + "\n" + blk + s[k:]
embed("Device", "NetTie_2", "Device")
embed("power", "PWR_FLAG", "power")
embed("Connector_Generic", "Conn_02x08_Odd_Even", "Connector_Generic")

# Clone R8 as template for the new symbols
tmpl = next(m.group(0) for m in SYM.finditer(s) if ref_of(m.group(0)) == "R8")
def newsym(lib_id, ref, value, fp, pins, x, y, in_bom="yes", on_board="yes", dnp="no"):
    b = re.sub(r'\(lib_id "[^"]+"\)', '(lib_id "%s")' % lib_id, tmpl, count=1)
    b = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % U(), b)
    for k, v in (("Reference", ref), ("Value", value), ("Footprint", fp), ("Description", "")):
        b = re.sub(r'(\(property "%s" )"[^"]*"' % k, lambda m: m.group(1) + '"%s"' % v, b, count=1)
    b = re.sub(r'\(reference "[^"]*"\)', '(reference "%s")' % ref, b)
    b = re.sub(r'\(in_bom \w+\)', '(in_bom %s)' % in_bom, b, count=1)
    b = re.sub(r'\(on_board \w+\)', '(on_board %s)' % on_board, b, count=1)
    b = re.sub(r'\(dnp \w+\)', '(dnp %s)' % dnp, b, count=1)
    b = re.sub(r'\n\t\t\(pin "[^"]+"\n\t\t\t\(uuid "[^"]+"\)\n\t\t\)', "", b)
    pinblk = "".join('\n\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)' % (p, U()) for p in pins)
    b = b.replace("\n\t\t(instances", pinblk + "\n\t\t(instances", 1)
    X0, Y0 = map(float, re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+) ', b).groups())
    flag = lib_id.startswith("power:")
    lay = {"Reference": (0, -2.54, flag), "Value": (0, -5.08 if flag else 2.54, not flag)}
    def prop(m):
        k = m.group(1); dx, dy, hide = lay.get(k, (0, 0, True))
        body = re.sub(r'\(at [-\d.]+ [-\d.]+ [-\d.]+\)', '(at %s %s 0)' % (fmt(X0 + dx), fmt(Y0 + dy)), m.group(2), count=1)
        body = re.sub(r'\n\t\t\t\(hide yes\)', '', body)
        if hide: body = body.replace(')', ')\n\t\t\t(hide yes)', 1)
        return '(property "%s"%s' % (k, body)
    b = re.sub(r'\(property "(\w+)"(.*?)(?=\n\t\t\(property|\n\t\t\(pin|\n\t\t\(instances)', prop, b, flags=re.S)
    return move(b, x, y)
extra = [newsym("Device:NetTie_2", "NT1", "NetTie_2", "NetTie:NetTie-2_SMD_Pad0.5mm", ["1", "2"], 0, 0, "no"),
         newsym("power:PWR_FLAG", "#FLG01", "PWR_FLAG", "", ["1"], 0, 0, "no", "no"),
         newsym("power:PWR_FLAG", "#FLG02", "PWR_FLAG", "", ["1"], 0, 0, "no", "no"),
         newsym("Connector_Generic:Conn_02x08_Odd_Even", "J11", "Spare-GPIO", "Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical",
                [str(i) for i in range(1, 17)], 0, 0, "no", "yes", "yes")]
anchor = "\n\t(sheet_instances"
s = s.replace(anchor, "".join(extra) + anchor, 1)

# Footprint changes: Pico WH on sockets, VEML7700 project footprint
FP_SET = {"U1": "Module:RaspberryPi_Pico_Common_THT", "U6": "sensor_hub:VEML7700_TT", "U1v": "Pico WH"}
def setfp(m):
    b = m.group(0); r = ref_of(b)
    if r in FP_SET:
        b = re.sub(r'(\(property "Footprint" )"[^"]*"', lambda x: x.group(1) + '"%s"' % FP_SET[r], b, count=1)
    if r == "U1":
        b = re.sub(r'(\(property "Value" )"[^"]*"', lambda x: x.group(1) + '"%s"' % FP_SET["U1v"], b, count=1)
    return b
s = SYM.sub(setfp, s)

# Apply positions
def place(m):
    b = m.group(0); r = ref_of(b)
    return move(b, snap(POS[r][0]), snap(POS[r][1])) if r in POS else b
s = SYM.sub(place, s)

# ── Pin geometry from the embedded library cache ────────────────────────────
lib = s[s.index('\t(lib_symbols'):]; lib = lib[:lib.index('\n\t)\n')]
PINS = {}
for m in re.finditer(r'\n\t\t\(symbol "([^"]+)"(.*?)(?=\n\t\t\(symbol "|\Z)', lib, re.S):
    PINS[m.group(1)] = {p[3]: (float(p[0]), float(p[1]), int(p[2])) for p in re.findall(
        r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "([^"]*)"', m.group(2), re.S)}

out, used = [], set()
OUTDIR = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}     # stub direction in sheet coords
LBLANG = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}
seen_pts = set()
for m in SYM.finditer(s):
    b = m.group(0); r = ref_of(b)
    if r not in N: continue
    lid = re.search(r'\(lib_id "([^"]+)"\)', b).group(1)
    X, Y = map(float, re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+) ', b).groups())
    for pin, net in N[r].items():
        px, py, ang = PINS[lid][pin]
        P = (round(X + px, 4), round(Y - py, 4))
        if P in seen_pts: used.add((r, pin)); continue          # stacked pins (Pico GND)
        seen_pts.add(P); used.add((r, pin))
        if net == "NC":
            out.append('\n\t(no_connect (at %s %s) (uuid "%s"))' % (fmt(P[0]), fmt(P[1]), U())); continue
        d = OUTDIR[ang]; Q = (round(P[0] + G * d[0], 4), round(P[1] + G * d[1], 4))
        out.append('\n\t(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))'
                   % (fmt(P[0]), fmt(P[1]), fmt(Q[0]), fmt(Q[1]), U()))
        a = LBLANG[d]
        just = "left bottom" if a in (0, 90) else "right bottom"
        out.append('\n\t(label "%s" (at %s %s %d) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s"))'
                   % (net, fmt(Q[0]), fmt(Q[1]), a, just, U()))

# every pin of every wired symbol must be covered
for m in SYM.finditer(s):
    b = m.group(0); r = ref_of(b)
    if r not in N: continue
    lid = re.search(r'\(lib_id "([^"]+)"\)', b).group(1)
    missing = [p for p in PINS[lid] if (r, p) not in used]
    assert not missing, (r, missing)
unwired = sorted({ref_of(m.group(0)) for m in SYM.finditer(s)} - set(N))
s = s.replace(anchor, "".join(out) + anchor, 1)
open(F, "w").write(s)
print("labels/wires/nc:", len(out), "unwired symbols:", unwired)
