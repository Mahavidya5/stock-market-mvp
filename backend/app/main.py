import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import models  # noqa: F401  (register tables)
from .config import settings
from .database import Base, engine
from .market.base import ProviderError
from .market.service import get_provider
from .routers import alerts, market, notifications, stocks, watchlist
from .scheduler import run_forever

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    p = get_provider()
    log.info("Started with data mode=%s provider=%s db=%s", p.data_mode, p.name, engine.dialect.name)
    task = asyncio.create_task(run_forever())
    yield
    task.cancel()


app = FastAPI(title="NSE Stock Market Dashboard", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(ProviderError)
async def provider_error_handler(_: Request, exc: ProviderError):
    log.warning("Provider error [%s]: %s", exc.code, exc)
    headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc), "code": exc.code}, headers=headers)


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health")
def health():
    p = get_provider()
    return {"status": "ok", "data_mode": p.data_mode, "provider": p.name, "database": engine.dialect.name}


for r in (market.router, stocks.router, watchlist.router, alerts.router, notifications.router):
    app.include_router(r)
