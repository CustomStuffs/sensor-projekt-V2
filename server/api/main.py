"""
FastAPI app. Serves the API and the dashboard as static files.

Run:
    cd server
    uvicorn api.main:app --host 0.0.0.0 --port 8080

Or via systemd — see server/CLAUDE.md for the unit file snippet.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from api.routes import time_sync, readings, commands, schedule
from storage.database import close_db
from config.settings import DASHBOARD_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()


app = FastAPI(title="Sensor Hub", lifespan=lifespan)

app.include_router(time_sync.router)
app.include_router(readings.router)
app.include_router(commands.router)
app.include_router(schedule.router)

# Serve dashboard static files at root — must come after API routes
_dash = os.path.abspath(DASHBOARD_DIR)
if os.path.isdir(_dash):
    app.mount("/", StaticFiles(directory=_dash, html=True), name="dashboard")
