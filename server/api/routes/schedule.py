import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from storage.database import get_db

router = APIRouter()


class ScheduleCondition(BaseModel):
    sensor: str
    op: str
    value: float


class ScheduleSlot(BaseModel):
    time: str
    duration_s: int
    days: list[str]
    skip_if: Optional[ScheduleCondition] = None


class ScheduleSaveRequest(BaseModel):
    schedule: list[ScheduleSlot]


@router.get("/api/schedule/{device_id}")
async def get_schedule(device_id: str):
    db = await get_db()
    async with db.execute(
        "SELECT relay_schedule FROM device_config WHERE device_id = ?", (device_id,)
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return {"schedule": []}
    return {"schedule": json.loads(row["relay_schedule"])}


@router.post("/api/schedule/{device_id}")
async def save_schedule(device_id: str, body: ScheduleSaveRequest):
    db = await get_db()
    await db.execute(
        "INSERT INTO device_config(device_id, relay_schedule) VALUES(?, ?)"
        " ON CONFLICT(device_id) DO UPDATE SET relay_schedule=excluded.relay_schedule",
        (device_id, json.dumps([s.model_dump() for s in body.schedule]))
    )
    await db.commit()
    return {"ok": True}
