from pydantic import BaseModel
from typing import Literal, Optional


class TimeSyncRequest(BaseModel):
    device_id: str
    uptime_ms: int


class TimeSyncResponse(BaseModel):
    unix_ts: int
    config: dict


class SensorReading(BaseModel):
    ts: int
    ph: Optional[float] = None
    ec_us: Optional[float] = None
    temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    lux: Optional[float] = None
    soil_pct: Optional[float] = None
    motion: Optional[bool] = None
    water_level: Optional[float] = None


class ReadingsUpload(BaseModel):
    device_id: str
    fw: str
    vbus_mv: Optional[int] = None
    readings: list[SensorReading]


class ReadingsUploadResponse(BaseModel):
    ok: bool
    stored: int


class CommandRequest(BaseModel):
    device_id: str
    action: Literal["relay_on", "relay_off"]
    duration_s: Optional[int] = None


class CommandResponse(BaseModel):
    id: int
    queued: bool


class CommandItem(BaseModel):
    id: int
    action: str
    duration_s: Optional[int] = None


class CommandListResponse(BaseModel):
    commands: list[CommandItem]


class AckResponse(BaseModel):
    ok: bool


class DeviceItem(BaseModel):
    id: str
    last_seen: int
    fw: Optional[str] = None


class DeviceListResponse(BaseModel):
    devices: list[DeviceItem]
