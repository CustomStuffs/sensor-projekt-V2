# Server Agent

> **Scope: `server/` only. Do not read, modify, or suggest changes to files outside this directory.**

FastAPI backend running on Raspberry Pi. Receives data from Pico W devices and serves the dashboard.

## Stack

- **FastAPI** + **uvicorn** (async HTTP server)
- **aiosqlite** (async SQLite driver)
- **Pydantic v2** (request/response validation)

## Run

```bash
cd server
pip install fastapi uvicorn aiosqlite pydantic
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

For production (systemd service on RPi):
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

## Remote Access (Tailscale)

No auth layer needed — Tailscale provides network-level security. Install:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Dashboard is then reachable at `http://<tailscale-ip>:8080` from any Tailscale-connected device.

## File Layout

```
server/
├── api/
│   ├── main.py          # FastAPI app, mounts routes, serves dashboard/ as static files
│   ├── models.py        # Pydantic models — all request/response shapes defined here
│   └── routes/
│       ├── readings.py  # POST /api/readings, GET /api/readings
│       ├── time_sync.py # POST /api/time
│       └── commands.py  # POST /api/commands, GET /api/commands, POST /api/commands/{id}/ack
├── storage/
│   ├── database.py      # aiosqlite connection pool + query helpers
│   └── schema.sql       # table definitions (run once on startup)
└── config/
    └── settings.py      # port, DB path, dashboard static path
```

## DB Schema Summary

- `devices` — one row per device_id, updated on each contact
- `readings` — append-only, UNIQUE(device_id, ts) enforces idempotency
- `commands` — pending/acked relay commands; acked_at=NULL means pending; `relay` = 1 | 2 (on-board relay, default 1; added by the migration in `storage/database.py` for existing DBs)
- `device_config.relay_schedule` — JSON list of schedule slots, each with an optional `relay` (1 | 2, validated by `ScheduleSlot`)

Full schema: `storage/schema.sql`

## API Contract (server side)

All endpoints and their exact JSON shapes are in the root `CLAUDE.md`. The server must:
- Respond to `POST /api/time` before accepting readings (Pico W depends on ordering)
- Silently ignore duplicate readings (same device_id + ts)
- Return pending commands on `GET /api/commands` (acked_at IS NULL)
- Mark commands delivered when `POST /api/commands/{id}/ack` is called

## Static Files

`api/main.py` mounts `../dashboard/` as static files at `/`. So `GET /` serves `dashboard/index.html` and `GET /src/api.js` serves `dashboard/src/api.js`.

## Rules

- Do not break API endpoint shapes without updating `firmware/CLAUDE.md` and `dashboard/CLAUDE.md`
- All DB writes are idempotent — Pico W retries on failure and the server must handle it
- Never store secrets in settings.py — no auth is intentional (Tailscale handles it)
