import time
from fastapi import APIRouter, Query
from typing import Optional
from api.models import ReadingsUpload, ReadingsUploadResponse
from storage.database import get_db

router = APIRouter()


@router.post("/api/readings", response_model=ReadingsUploadResponse)
async def post_readings(upload: ReadingsUpload):
    db = await get_db()
    now = int(time.time())

    await db.execute(
        "INSERT INTO devices(id, last_seen, fw_version) VALUES(?, ?, ?)"
        " ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen, fw_version=excluded.fw_version",
        (upload.device_id, now, upload.fw)
    )

    stored = 0
    for r in upload.readings:
        cur = await db.execute(
            """INSERT OR IGNORE INTO readings
               (device_id, ts, ph, ec_us, temp_c, humidity_pct, lux, soil_pct, motion, water_level, vbus_mv)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (upload.device_id, r.ts, r.ph, r.ec_us, r.temp_c,
             r.humidity_pct, r.lux, r.soil_pct,
             int(r.motion) if r.motion is not None else None,
             r.water_level, upload.vbus_mv)
        )
        stored += cur.rowcount

    await db.commit()
    return ReadingsUploadResponse(ok=True, stored=stored)


@router.get("/api/readings")
async def get_readings(
    device_id: str,
    from_ts: Optional[int] = Query(None, alias="from"),
    to_ts: Optional[int] = Query(None, alias="to"),
    limit: int = Query(500, le=2000),
):
    db = await get_db()
    conditions = ["device_id = ?"]
    params: list = [device_id]

    if from_ts is not None:
        conditions.append("ts >= ?")
        params.append(from_ts)
    if to_ts is not None:
        conditions.append("ts <= ?")
        params.append(to_ts)

    where = " AND ".join(conditions)
    params.append(limit)

    async with db.execute(
        f"SELECT * FROM readings WHERE {where} ORDER BY ts DESC LIMIT ?", params
    ) as cur:
        rows = await cur.fetchall()

    async with db.execute(
        f"SELECT COUNT(*) FROM readings WHERE {where}", params[:-1]
    ) as cur:
        total = (await cur.fetchone())[0]

    return {"readings": [dict(r) for r in rows], "total": total}


@router.get("/api/devices")
async def get_devices():
    db = await get_db()
    async with db.execute(
        "SELECT id, last_seen, fw_version as fw FROM devices ORDER BY last_seen DESC"
    ) as cur:
        rows = await cur.fetchall()
    return {"devices": [dict(r) for r in rows]}
