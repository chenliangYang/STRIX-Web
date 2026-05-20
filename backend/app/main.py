"""STRIX Web Backend Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, auth, tasks, whitelists, dashboard, users, audit_logs, runs, websockets, results
from app.core.config import get_settings
from app.core.errors import StrixWebException
from app.core.logging import setup_logging

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(StrixWebException)
async def strix_web_exception_handler(
    request: Request,
    exc: StrixWebException,
) -> JSONResponse:
    """Handle custom exceptions."""
    # Map exception codes to HTTP status codes
    status_code = 200
    if exc.code >= 40100 and exc.code < 40200:
        status_code = 401
    elif exc.code >= 40300 and exc.code < 40400:
        status_code = 403
    elif exc.code >= 40400 and exc.code < 40500:
        status_code = 404
    elif exc.code >= 40900 and exc.code < 41000:
        status_code = 409
    elif exc.code >= 50000:
        status_code = 500

    return JSONResponse(
        status_code=status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data,
        },
    )


# Include routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(tasks.router, prefix=settings.api_prefix)
app.include_router(runs.router, prefix=settings.api_prefix)
app.include_router(runs.task_runs_router, prefix=settings.api_prefix)
app.include_router(whitelists.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(audit_logs.router, prefix=settings.api_prefix)
app.include_router(results.router, prefix=settings.api_prefix)
app.include_router(websockets.router)  # No prefix for WebSocket routes


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "name": settings.app_name,
            "version": "0.1.0",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
