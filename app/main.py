"""Main application module for the We-Upload API."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.init_db import create_first_superuser, init_db
from app.routers import files, health, login, users

# Initialize logging first
setup_logging()
logger = logging.getLogger(__name__)

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
    logger.info("Starting application initialization")

    # Initialize database and create tables if they don't exist
    init_db()

    # Create initial superuser if configured
    if settings.FIRST_SUPERUSER:
        create_first_superuser()

    logger.info("Application initialization complete")


if __name__ == "__main__":
    import uvicorn

    # Uvicorn is an ASGI server implementation that serves as the interface between
    # our FastAPI application and HTTP clients. It handles HTTP connections, request parsing,
    # and response delivery with high performance. We use it here to run our application
    # directly when this file is executed as a script.
    uvicorn.run(
        "app.main:app",  # Path to the app object in the format "module:attribute"
        host="0.0.0.0",  # Bind to all network interfaces
        port=8000,  # Port to listen on
        reload=settings.DEBUG,  # Auto-reload on code changes when in debug mode
        log_level="info",  # Set logging verbosity
    )
