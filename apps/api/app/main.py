"""REGIQ API — FastAPI application entry point."""

from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.mongodb import close_mongo, connect_mongo

# fastapi-limiter is optional in development environments; import defensively
try:
    from fastapi_limiter import FastAPILimiter  # type: ignore

    _LIMITER_AVAILABLE = True
except Exception:
    FastAPILimiter = None  # type: ignore
    _LIMITER_AVAILABLE = False

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_connection = redis.from_url(settings.redis_url, encoding="utf8")
    if _LIMITER_AVAILABLE and FastAPILimiter is not None:
        try:
            await FastAPILimiter.init(redis_connection)
        except Exception:
            pass

    await connect_mongo()

    yield

    # Shutdown
    await close_mongo()
    await redis_connection.close()


app = FastAPI(
    title="REGIQ API",
    description="AI-Powered Regression Intelligence Platform — REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health check ──────────────────────────────────────────


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "regiq-api", "version": "1.0.0"}


# ── Routers ───────────────────────────────────────────────

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.audit import router as audit_router
from app.api.v1.tests import router as tests_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.changes import router as changes_router
from app.api.v1.dashboard import router as dashboard_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(api_keys_router, prefix="/api/v1/api-keys", tags=["API Keys"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit Logs"])
app.include_router(tests_router, prefix="/api/v1/tests", tags=["Test Repository"])
app.include_router(integrations_router, prefix="/api/v1/integrations", tags=["Integrations"])
app.include_router(changes_router, prefix="/api/v1/changes", tags=["Change Management"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
