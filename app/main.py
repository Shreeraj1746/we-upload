"""Main application module for the We-Upload API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.init_db import create_first_superuser
from app.routers import files, health, login, users

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-User File Upload & Sharing Backend API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(login.router, tags=["login"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])


@app.on_event("startup")
async def startup_event() -> None:
    """Execute actions on application startup.

    This function is called when the FastAPI application starts. It's used for
    initializing resources, database connections, and executing startup tasks.
    """
    # Create initial superuser if configured
    if settings.FIRST_SUPERUSER:
        create_first_superuser()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
