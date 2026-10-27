"""Deliberately faulty dependency. Administrative controls MUST remain localhost-only."""
import asyncio
import os
import secrets
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="Synthetic Timetable Provider")
state = {"mode": "healthy"}
ADMIN_KEY = os.environ.get("DEMO_ADMIN_KEY", "")

@app.get("/timetable")
async def timetable():
    if state["mode"] == "slow":
        await asyncio.sleep(1.5)
    if state["mode"] == "down":
        raise HTTPException(status_code=503, detail="Simulated downstream outage")
    return {"journeys": [
        {"train": "DEMO-101", "departure": "08:05", "arrival": "11:20"},
        {"train": "DEMO-205", "departure": "13:20", "arrival": "16:40"}
    ]}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/admin/mode/{mode}")
def set_mode(mode: str, x_demo_key: str | None = Header(default=None)):
    if not ADMIN_KEY or not x_demo_key or not secrets.compare_digest(x_demo_key, ADMIN_KEY):
        raise HTTPException(status_code=403, detail="Forbidden")
    if mode not in ("healthy", "slow", "down"):
        raise HTTPException(status_code=400, detail="Mode must be healthy, slow, or down")
    state["mode"] = mode
    return {"provider_mode": mode}
