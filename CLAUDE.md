# Sensor Hub — Master Agent

Outdoor environmental monitoring system based on Raspberry Pi Pico W. Four independent subprojects, each with its own CLAUDE.md. Work inside a subproject without touching others.

## System Data Flow

```
Pico W (MicroPython)
  └─ POST JSON ──► RPi FastAPI server (port 8080)
                      └─ SQLite DB
                      └─ Static files ──► Browser dashboard
```

## Subproject Ownership

| Folder | Owns | Must not touch |
|--------|------|----------------|
| `hardware/` | PCB schematic, BOM, KiCad files | any code |
| `firmware/` | MicroPython source, tools scripts | server/, dashboard/ |
| `server/` | FastAPI app, SQLite schema | firmware/, dashboard/src/ |
| `dashboard/` | HTML/JS/CSS frontend | server/, firmware/ |

**Rule: never change an API endpoint shape without updating `firmware/CLAUDE.md`, `server/CLAUDE.md`, and `dashboard/CLAUDE.md` in the same session.**

---

## API Contract (single source of truth)

### POST /api/time — time sync, Pico W calls before every upload
```json
Request:  { "device_id": "pico_001", "uptime_ms": 123456 }
Response: {
  "unix_ts": 1748000000,
  "config": {
    "interval_s": 1800,
    "relay_schedule": [
      { "time": "08:00", "duration_s": 600, "days": ["mon","wed","fri"], "skip_if": null }
    ]
  }
}
```
`relay_schedule` is an empty array if no schedule is saved. `skip_if` is null or `{ "sensor": "soil_pct", "op": ">=", "value": 60 }`.

### POST /api/readings — sensor data upload
```json
Request: {
  "device_id": "pico_001",
  "fw": "1.0.0",
  "vbus_mv": 4850,
  "readings": [{
    "ts": 1748000000,
    "ph": 6.8,
    "ec_us": 1250,
    "temp_c": 22.5,
    "humidity_pct": 65.2,
    "lux": 850,
    "soil_pct": 45,
    "motion": false,
    "water_level": 0.0
  }]
}
Response: { "ok": true, "stored": 1 }
```
All sensor fields are nullable (null if sensor not connected). Duplicate (device_id + ts) rows silently ignored.

### GET /api/commands?device_id=pico_001 — Pico W polls after each upload
```json
Response: { "commands": [{ "id": 42, "action": "relay_on", "duration_s": 300 }] }
```

### POST /api/commands/42/ack — Pico W acknowledges executed command
```json
Response: { "ok": true }
```

### POST /api/commands — dashboard posts manual relay command
```json
Request:  { "device_id": "pico_001", "action": "relay_on", "duration_s": 300 }
Response: { "id": 42, "queued": true }
```
`action` values: `"relay_on"` | `"relay_off"`

### GET /api/schedule/{device_id} — dashboard fetches saved schedule
```json
Response: { "schedule": [{ "time": "08:00", "duration_s": 600, "days": ["mon","wed","fri"], "skip_if": null }] }
```

### POST /api/schedule/{device_id} — dashboard saves schedule
```json
Request:  { "schedule": [{ "time": "08:00", "duration_s": 600, "days": ["mon","wed","fri"], "skip_if": null }] }
Response: { "ok": true }
```
Replaces the full schedule for that device. Firmware receives it on the next `POST /api/time`.

### GET /api/readings?device_id=pico_001&from=TS&to=TS&limit=500
```json
Response: { "readings": [...], "total": 142 }
```

### GET /api/devices
```json
Response: { "devices": [{ "id": "pico_001", "last_seen": 1748000000, "fw": "1.0.0" }] }
```

---

## Stack Summary

- **Firmware**: MicroPython 1.28+ on Pico W (`RPI_PICO_W` build)
- **Server**: FastAPI + uvicorn + aiosqlite, runs on Raspberry Pi
- **Remote access**: Tailscale VPN — no auth layer needed, no port forwarding
- **Dashboard**: Vanilla HTML/JS, served as static files by the FastAPI server
- **Relay**: Auto rules (config.json) + manual override from dashboard (command queue)
- **Data**: Append-only SQLite, forever, multi-device from the start

## PCB Note

An empty V1 KiCad skeleton exists at `PCB/V1 pico sensorhub/` (KiCad 10). The active design lives in `hardware/kicad/`. Use `hardware/docs/schematic.md` as the source of truth for all electrical connections.
