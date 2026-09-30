#!/usr/bin/env bash
# Full routing run: hand-routed MAINS/NODE_A -> Freerouting -> pours -> DRC.
# Run from the repo root:  hardware/tools/autoroute.sh
# Java 25 + Freerouting 2.4.1 are cached in ~/.cache/sensor-hub-tools (not system-wide).
set -euo pipefail
C="${XDG_CACHE_HOME:-$HOME/.cache}/sensor-hub-tools"; W="$(mktemp -d)"; mkdir -p "$C"
if ! ls "$C"/jdk-25*/bin/java >/dev/null 2>&1; then
  curl -sL "https://api.adoptium.net/v3/binary/latest/25/ga/linux/x64/jre/hotspot/normal/eclipse" | tar xz -C "$C"
fi
[ -f "$C/freerouting-2.4.1.jar" ] || curl -sL -o "$C/freerouting-2.4.1.jar" \
  https://github.com/freerouting/freerouting/releases/download/v2.4.1/freerouting-2.4.1.jar
JAVA=$(ls "$C"/jdk-25*/bin/java | head -1)
T=hardware/tools
step() {  # run a route_pcb.py stage; on failure show the error and stop
  python3 $T/route_pcb.py "$1" "$W/board.dsn" "$W/board.ses" > "$W/$1.log" 2>&1 \
    || { grep -v "PROPERTY_ENUM\|memory leak" "$W/$1.log" | tail -8; echo "route_pcb.py $1 failed (exit $?)"; exit 1; }
  grep -E "done|import|removed" "$W/$1.log"
}
step pre
"$JAVA" -Djava.awt.headless=true -jar "$C/freerouting-2.4.1.jar" -de "$W/board.dsn" -do "$W/board.ses" \
  -mp 30 -mt 4 --gui.enabled=false > "$W/freerouting.log" 2>&1
grep -E "^  Net '" "$W/freerouting.log" || true
step post
kicad-cli pcb drc --format json --severity-error -o "$W/drc.json" hardware/kicad/sensor_hub.kicad_pcb >/dev/null 2>&1 || true
python3 $T/route_pcb.py fixclear "$W/drc.json" x 2>&1 | grep -E "fixclear|Error|Trace" || true
kicad-cli pcb drc --severity-error --severity-warning -o "$W/drc.rpt" hardware/kicad/sensor_hub.kicad_pcb >/dev/null 2>&1 || true
grep -oE "^\[[a-z_]+\]" "$W/drc.rpt" | sort | uniq -c | sort -rn
echo "logs + DRC report: $W"
