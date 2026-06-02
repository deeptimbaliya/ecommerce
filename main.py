from fastapi import FastAPI, Request
import app.core.cloudinary
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.user import router as user_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.core.middleware import RequestLoggingMiddleware
from app.core.logger import setup_logger
from app.core.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings

logger = setup_logger(__name__)


app = FastAPI(
    title="Ecommerce API",
    version="1.0.0",
    description="Ecommerce REST API with versioned endpoints",
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware) 

# ── Register routers ──────────────────────────────────────────────
app.include_router(user_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(health_router, prefix="/api/v1")

# ── Global exception handlers ────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    logger.warning(f"404 Not Found: {request.method} {request.url}")
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Resource not found",
            "path": str(request.url),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"422 Validation Error: {request.method} {request.url}")
    # Sanitize errors: convert non-serializable objects (e.g. ValueError) to strings
    clean_errors = []
    for err in exc.errors():
        clean_err = {
            "type": err.get("type"),
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "input": err.get("input"),
        }
        clean_errors.append(clean_err)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "errors": clean_errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"500 Unhandled Exception: {request.method} {request.url} — {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
        },
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(
        f"Rate limit exceeded: {request.method} {request.url.path} "
        f"from IP {get_remote_address(request)}"
    )
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": "Please wait before trying again"
        }
    )


# ── Root health check ────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"success": True, "message": "Ecommerce API is running"}
