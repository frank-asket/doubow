from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from db.session import init_models
from dependencies import rate_limit_key
from error_handlers import register_exception_handlers
from routers import (
    agents,
    applications,
    approvals,
    auth,
    autopilot,
    integrations_google,
    integrations_linkedin,
    jobs,
    prep,
    resume,
    telemetry,
    users,
    webhooks,
)
from services.observability import setup_observability
from services.metrics import metrics_middleware, metrics_response

setup_observability()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup/shutdown hooks live here once DB + Redis are wired.
    await init_models()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.middleware("http")(metrics_middleware)
limiter = Limiter(key_func=rate_limit_key, default_limits=["240/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Local dev (any port) + Vercel preview/production hostnames (*.vercel.app).
    # Production canonical origin is also in settings.cors_origins; regex covers branch previews.
    allow_origin_regex=(
        r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|host\.docker\.internal)(:\d+)?$"
        r"|^https://[a-z0-9]([a-z0-9-]*[a-z0-9])?\.vercel\.app$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["system"])
@limiter.exempt
async def healthcheck(_request: Request) -> dict[str, str]:
    """Liveness: process is up (no dependency checks — safe for frequent kube/docker probes)."""
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
@limiter.exempt
async def readiness(_request: Request) -> JSONResponse:
    """Readiness: Postgres required; Redis reported as ok or degraded (cache/Celery optional)."""
    from services.health_checks import gather_readiness

    body, status_code = await gather_readiness()
    return JSONResponse(content=body, status_code=status_code)


@app.get("/metrics", tags=["system"])
@limiter.exempt
async def metrics(_request: Request):
    return metrics_response()


API_PREFIX = "/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(integrations_google.router, prefix=API_PREFIX)
app.include_router(integrations_linkedin.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(resume.router, prefix=API_PREFIX)
app.include_router(jobs.router, prefix=API_PREFIX)
app.include_router(applications.router, prefix=API_PREFIX)
app.include_router(autopilot.router, prefix=API_PREFIX)
app.include_router(approvals.router, prefix=API_PREFIX)
app.include_router(prep.router, prefix=API_PREFIX)
app.include_router(agents.router, prefix=API_PREFIX)
app.include_router(telemetry.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
