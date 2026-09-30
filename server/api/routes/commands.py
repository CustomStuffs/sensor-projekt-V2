import time
from fastapi import APIRouter
from api.models import CommandRequest, CommandResponse, CommandListResponse, AckResponse
from storage.database import get_db

router = APIRouter()


@router.post("/api/commands", response_model=CommandResponse)
async def post_command(req: CommandRequest):
    db = await get_db()
    now = int(time.time())
    await db.execute(
        "INSERT INTO devices(id, last_seen) VALUES(?, ?)"
        " ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen",
        (req.device_id, now)
    )
    async with db.execute(
        "INSERT INTO commands(device_id, action, duration_s, relay, created_at)"
        " VALUES(?, ?, ?, ?, ?)",
        (req.device_id, req.action, req.duration_s, req.relay, now)
    ) as cur:
        cmd_id = cur.lastrowid
    await db.commit()
    return CommandResponse(id=cmd_id, queued=True)


@router.get("/api/commands", response_model=CommandListResponse)
async def get_commands(device_id: str):
    db = await get_db()
    async with db.execute(
        "SELECT id, action, duration_s, relay FROM commands"
        " WHERE device_id = ? AND acked_at IS NULL ORDER BY created_at ASC",
        (device_id,)
    ) as cur:
        rows = await cur.fetchall()
    return CommandListResponse(commands=[dict(r) for r in rows])


@router.post("/api/commands/{cmd_id}/ack", response_model=AckResponse)
async def ack_command(cmd_id: int):
    db = await get_db()
    now = int(time.time())
    await db.execute(
        "UPDATE commands SET acked_at = ? WHERE id = ?", (now, cmd_id)
    )
    await db.commit()
    return AckResponse(ok=True)
