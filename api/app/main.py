from fastapi import FastAPI

app = FastAPI(
    title="REGIQ API",
    description="Backend API for REGIQ Platform",
    version="1.0.0"
)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "api"
    }

# Include routers here later
# app.include_router(auth.router, prefix="/api/v1/auth")
