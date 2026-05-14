import json
import time
from fastapi import APIRouter
from api.models import TimeSyncRequest, TimeSyncResponse
from config.settings import POLL_INTERVAL_S
from storage.database import get_db

router = APIRouter()


@router.post("/api/time", response_model=TimeSyncResponse)
async def post_time(req: TimeSyncRequest):
    db = await get_db()
    now = int(time.time())
    await db.execute(
        "INSERT INTO devices(id, last_seen) VALUES(?, ?)"
        " ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen",
        (req.device_id, now)
    )
    await db.commit()

    async with db.execute(
        "SELECT relay_schedule FROM device_config WHERE device_id = ?", (req.device_id,)
    ) as cur:
        row = await cur.fetchone()
    schedule = json.loads(row["relay_schedule"]) if row else []

    return TimeSyncResponse(
        unix_ts=now,
        config={"interval_s": POLL_INTERVAL_S, "relay_schedule": schedule}
    )
