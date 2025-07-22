from fastapi import HTTPException, status


# Base exceptions
class CliporaAIException(Exception):
    """Base exception for CliporaAI application"""

    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


# Authentication & Authorization exceptions
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class TokenExpiredError(CliporaAIException):
    """Raised when authentication token has expired"""

    pass
