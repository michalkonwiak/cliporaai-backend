import logging
from typing import List, Optional, Union, cast, Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """Model for a single error detail."""
    loc: List[Union[str, int]] = Field(..., description="Location of the error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ErrorResponse(BaseModel):
    """Unified error response model."""
    status_code: int = Field(..., description="HTTP status code")
    detail: Union[str, List[ErrorDetail]] = Field(..., description="Error details")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
    request_id: Optional[str] = Field(None, description="Request ID for correlation")


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom exception handler for validation errors.
    
    Args:
        request: The request that caused the exception
        exc: The validation exception
        
    Returns:
        A JSON response with a unified error format
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={"request_id": request_id} if request_id else {}
    )
    
    error_response = ErrorResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=cast(List[ErrorDetail], exc.errors()),
        error_code=None,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(exclude_none=True)
    )



def setup_error_handlers(app: FastAPI) -> None:
    """
    Register custom exception handlers with the FastAPI app.
    
    Args:
        app: The FastAPI application
    """
    app.add_exception_handler(RequestValidationError, cast(Any, validation_exception_handler))