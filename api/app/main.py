from fastapi import FastAPI
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_connection = redis.from_url("redis://localhost:6379", encoding="utf8")
    await FastAPILimiter.init(redis_connection)
    yield
    await redis_connection.close()

app = FastAPI(
    title="REGIQ API",
    description="Backend API for REGIQ Platform",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "api"
    }

# Include routers here later
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.audit import router as audit_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(api_keys_router, prefix="/api/v1/api-keys", tags=["API Keys"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit Logs"])

