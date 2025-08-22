from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List, Any
from datetime import datetime

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """🔥 Response wrapper - Compatible con monorepo Java"""
    success: bool = True
    message: str
    data: Optional[T] = None
    timestamp: datetime = datetime.now()
    
    @classmethod
    def success_response(cls, data: T, message: str = "Success") -> "ApiResponse[T]":
        return cls(success=True, message=message, data=data)
    
    @classmethod 
    def error_response(cls, message: str, data: Optional[T] = None) -> "ApiResponse[T]":
        return cls(success=False, message=message, data=data)

class PaginatedResponse(BaseModel, Generic[T]):
    """📄 Respuesta paginada"""
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 10
    pages: int = 1
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int = 1, page_size: int = 10) -> "PaginatedResponse[T]":
        pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )

class HealthResponse(BaseModel):
    """💚 Health check response"""
    status: str = "UP"
    microservicio: str
    version: str = "1.0.0"
    timestamp: datetime = datetime.now()
    endpoints_disponibles: List[str] = []
    
class MessageResponse(BaseModel):
    """💬 Simple message response"""
    message: str
    success: bool = True
    
class ValidationError(BaseModel):
    """❌ Error de validación"""
    field: str
    message: str
    value: Any = None