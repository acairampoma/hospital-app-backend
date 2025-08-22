from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    nombre_completo: Optional[str] = None
    telefono: Optional[str] = None
    especialidad: Optional[str] = None
    colegiatura: Optional[str] = None
    cargo: Optional[str] = None

class UserCreate(UserBase):
    """Create user schema"""
    password: str

class UserUpdate(BaseModel):
    """Update user schema"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    nombre_completo: Optional[str] = None
    telefono: Optional[str] = None
    especialidad: Optional[str] = None
    colegiatura: Optional[str] = None
    cargo: Optional[str] = None
    enabled: Optional[bool] = None

class UserResponse(BaseModel):
    """User response schema - Compatible con UserController Java"""
    id: int
    username: str
    email: str
    nombre_completo: Optional[str] = None
    especialidad: Optional[str] = None
    colegiatura: Optional[str] = None
    enabled: bool = True
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    
    # Propiedades calculadas
    is_medico: bool = False
    display_name: str = ""
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # Calcular propiedades
        self.is_medico = bool(self.especialidad and self.colegiatura)
        self.display_name = self.nombre_completo or self.username

class UserSearchResponse(BaseModel):
    """Response para búsqueda de usuarios"""
    id: int
    nombre_completo: Optional[str] = None
    especialidad: Optional[str] = None
    colegiatura: Optional[str] = None
    cargo: Optional[str] = None

class UserListResponse(BaseModel):
    """Response para lista paginada de usuarios"""
    users: list[UserResponse]
    total: int
    page: int
    size: int
    total_pages: int

class ChangePasswordRequest(BaseModel):
    """Request para cambio de contraseña"""
    current_password: str
    new_password: str

class MedicoInfo(BaseModel):
    """Información básica de médico para otros schemas"""
    id: int
    nombre_completo: str
    especialidad: Optional[str] = None
    colegiatura: Optional[str] = None