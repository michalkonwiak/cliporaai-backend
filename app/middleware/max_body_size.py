import logging
import json
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


logger = logging.getLogger(__name__)

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """
    Middleware that limits the size of the request body.
    
    If the Content-Length header exceeds the maximum size, the request is rejected
    with a 413 Payload Too Large response.
    """
    
    def __init__(self, app: ASGIApp, max_size_mb: int = 100):
        super().__init__(app)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        logger.info(f"MaxBodySizeMiddleware initialized with limit of {max_size_mb}MB ({self.max_size_bytes} bytes)")
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        content_length = request.headers.get("content-length")
        
        # If Content-Length header is present, check it against the limit
        if content_length:
            try:
                content_length_int = int(content_length)
                if content_length_int > self.max_size_bytes:
                    logger.warning(f"Request body too large: {content_length} bytes (max: {self.max_size_bytes})")
                    return Response(
                        status_code=413,
                        content=json.dumps({"detail": f"Request body too large. Maximum size is {self.max_size_bytes} bytes."}),
                        media_type="application/json"
                    )
            except ValueError:
                pass
        
        return await call_next(request)