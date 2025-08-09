from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to each response.
    
    Adds the following headers:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - X-XSS-Protection: 1; mode=block
    - Content-Security-Policy: default-src 'self'
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        hsts_max_age: int = 31536000,
        include_subdomains: bool = True
    ):
        super().__init__(app)
        self.hsts_value = f"max-age={hsts_max_age}"
        if include_subdomains:
            self.hsts_value += "; includeSubDomains"
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = self.hsts_value
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response