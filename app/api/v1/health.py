from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.logger import setup_logger

router = APIRouter(tags=["Health"])
logger = setup_logger(__name__)

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    Returns 200 if app + DB are healthy.
    Returns 503 if something is wrong.
    """
    health = {
        "status": "healthy",
        "app": "ok",
        "database": "ok",
    }

    # Check DB connection
    try:
        db.execute(text("SELECT 1"))
        logger.debug("Health check: DB ok")
    except Exception as e:
        logger.error(f"Health check: DB failed: {e}")
        health["status"] = "unhealthy"
        health["database"] = "error"
        return JSONResponse(status_code=503, content=health)

    return health