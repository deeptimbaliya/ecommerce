# app/core/middleware.py
import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import setup_logger

logger = setup_logger("app.middleware")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate unique ID for this request
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"[request_id={request_id}]"
        )

        try:
            response = await call_next(request)
            duration = (time.time() - start_time) * 1000  # ms

            # Log response
            logger.info(
                f"← {request.method} {request.url.path} "
                f"status={response.status_code} "
                f"duration={duration:.1f}ms "
                f"[request_id={request_id}]"
            )
            return response

        except Exception as exc:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"FAILED after {duration:.1f}ms "
                f"[request_id={request_id}]: {exc}",
                exc_info=True
            )
            raise