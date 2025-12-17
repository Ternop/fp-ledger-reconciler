from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.api.routes import router
from app.core.logging import get_logger

LOG = get_logger("fp-ledger")
REQ_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQ_LAT = Histogram("http_request_latency_seconds", "Latency", ["method", "path"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOG.info("starting")
    yield
    LOG.info("stopping")


app = FastAPI(title="FP Ledger Reconciler", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.middleware("http")
async def metrics_mw(request: Request, call_next):
    path = request.url.path
    method = request.method
    start = time.time()
    try:
        resp = await call_next(request)
        return resp
    finally:
        dur = time.time() - start
        status = getattr(locals().get("resp", None), "status_code", 500)
        # avoid high-cardinality labels: keep path as-is for this small demo
        REQ_COUNT.labels(method=method, path=path, status=str(status)).inc()
        REQ_LAT.labels(method=method, path=path).observe(dur)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/metrics")
def metrics():
    return JSONResponse(content=generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
