"""Synthetic railway timetable API; not for actual passenger or train operations."""
import os
import time
from datetime import datetime, timezone
from typing import Literal

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

MODE = os.getenv("APP_MODE", "modern")
INSTANCE = os.getenv("APP_INSTANCE", "legacy-1")
PROVIDER_URL = os.getenv("PROVIDER_URL", "http://localhost:8001")

app = FastAPI(title="KAI Synthetic Reliability Lab", version="1.0.0")
REQUESTS = Counter("demo_http_requests_total", "HTTP requests", ["mode", "path", "status"])
DURATIONS = Histogram("demo_request_duration_seconds", "Duration of HTTP requests", ["mode", "path"],
                      buckets=[.01, .025, .05, .1, .2, .5, 1, 2, 5])
JOURNEYS = Counter("demo_journey_results_total", "Journey search outcomes", ["mode", "outcome"])

# A bundled *demo-only* snapshot makes degradation visible even if the provider dies.
# An actual timetable must have a freshness policy, provenance and integrity checks.
STALE_SNAPSHOT = [
    {"train": "DEMO-101", "departure": "08:00", "arrival": "11:15"},
    {"train": "DEMO-205", "departure": "13:20", "arrival": "16:40"},
]
recent_good_snapshot = None
recent_good_at = None


@app.middleware("http")
async def record_requests(request: Request, call_next):
    path = "/search" if request.url.path == "/search" else "other"
    start = time.monotonic()
    status = "500"
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        REQUESTS.labels(MODE, path, status).inc()
        DURATIONS.labels(MODE, path).observe(time.monotonic() - start)


@app.get("/healthz")
def healthz():
    return {"status": "alive", "instance": INSTANCE}


@app.get("/readyz")
def readyz():
    # Deliberately tests ability to serve, not the external provider.
    # An app offering degraded responses can remain ready during provider failure.
    return {"status": "ready", "instance": INSTANCE}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/search")
async def search(origin: str = "Jakarta", destination: str = "Bandung"):
    global recent_good_snapshot, recent_good_at
    # Baseline waits on the dependency; modern limits the wait to 300ms.
    timeout = 3.0 if MODE == "legacy" else 0.30
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream = await client.get(f"{PROVIDER_URL}/timetable")
            upstream.raise_for_status()
            journeys = upstream.json()["journeys"]
        recent_good_snapshot = journeys
        recent_good_at = datetime.now(timezone.utc).isoformat()
        JOURNEYS.labels(MODE, "good").inc()
        return {
            "origin": origin, "destination": destination,
            "journeys": journeys, "outcome": "good", "source": "live-demo-provider",
            "instance": INSTANCE, "observed_at_utc": recent_good_at,
            "message": "Synthetic data only. Never use for travel decisions."
        }
    except (httpx.HTTPError, ValueError, KeyError):
        if MODE == "legacy":
            JOURNEYS.labels(MODE, "unavailable").inc()
            return JSONResponse(status_code=503, content={
                "outcome": "unavailable", "message": "Demo timetable provider unavailable",
                "instance": INSTANCE
            })
        # Modernized read-only endpoint: explicitly flag stale information.
        # This counts as DEGRADED, *not* a successful user-journey SLI event.
        JOURNEYS.labels(MODE, "degraded").inc()
        return JSONResponse(status_code=200, headers={"X-Demo-Outcome": "degraded"}, content={
            "origin": origin, "destination": destination,
            "journeys": recent_good_snapshot or STALE_SNAPSHOT,
            "outcome": "degraded",
            "source": "last-successful-demo-snapshot" if recent_good_snapshot else "bundled-demo-snapshot",
            "snapshot_time_utc": recent_good_at,
            "instance": INSTANCE,
            "warning": "Stale information: not valid for booking, seat inventory, safety or operations."
        })
