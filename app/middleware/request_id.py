import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request.
    
    The request ID is added to:
    1. Request state as request.state.request_id
    2. Response headers as X-Request-ID
    3. Logging context for correlation
    """
    
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Get request ID from header or generate a new one
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Add request ID to logging context
        logger_adapter = logging.LoggerAdapter(
            logger, {"request_id": request_id}
        )
        logger_adapter.info(f"Request started: {request.method} {request.url.path}")
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[self.header_name] = request_id
        
        logger_adapter.info(f"Request completed: {request.method} {request.url.path} - {response.status_code}")
        
        return response