"""Health check router for the API."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    """Health check endpoint.

    This endpoint is used to check if the API is running.

    Returns:
        A dictionary with status information.
    """
    return {"status": "ok", "service": "we-upload-api"}


@router.get("/health/db")
def db_health_check(db: Session = Depends(get_db)) -> dict:
    """Database health check endpoint.

    This endpoint checks if the database connection is working.

    Args:
        db: Database session dependency.

    Returns:
        A dictionary with database connection status.
    """
    # Execute a simple query to check database connectivity
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
