CREATE TABLE IF NOT EXISTS devices (
    id          TEXT PRIMARY KEY,
    last_seen   INTEGER NOT NULL,
    fw_version  TEXT
);

CREATE TABLE IF NOT EXISTS readings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id    TEXT NOT NULL REFERENCES devices(id),
    ts           INTEGER NOT NULL,
    ph           REAL,
    ec_us        REAL,
    temp_c       REAL,
    humidity_pct REAL,
    lux          REAL,
    soil_pct     REAL,
    motion       INTEGER,
    water_level  REAL,
    probe_temp_c REAL,
    vbus_mv      INTEGER,
    UNIQUE(device_id, ts)
);

CREATE INDEX IF NOT EXISTS idx_readings_device_ts ON readings(device_id, ts);

CREATE TABLE IF NOT EXISTS device_config (
    device_id      TEXT PRIMARY KEY REFERENCES devices(id),
    relay_schedule TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS commands (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id  TEXT NOT NULL REFERENCES devices(id),
    action     TEXT NOT NULL,
    duration_s INTEGER,
    relay      INTEGER NOT NULL DEFAULT 1,   -- on-board relay: 1 = K1 (GP10), 2 = K2 (GP15)
    created_at INTEGER NOT NULL,
    acked_at   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_commands_device_pending ON commands(device_id, acked_at, created_at);
