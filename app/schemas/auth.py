from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

# 🔐 AUTH SCHEMAS - Patrón galloapp_backend

class UserLogin(BaseModel):
    """Login request"""
    email: EmailStr  # Cambié de username a email
    password: str

class UserRegister(BaseModel):
    """Registro de usuario médico"""
    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nombre_completo: Optional[str] = None  # Para compatibilidad
    telefono: Optional[str] = None
    datos_profesional: Optional[dict] = None  # Para JSONB
    
    # Campos médicos
    especialidad: Optional[str] = None
    colegiatura: Optional[str] = None
    cargo: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password debe tener al menos 8 caracteres')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username debe tener al menos 3 caracteres')
        return v

class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutos

class TokenRefresh(BaseModel):
    """Refresh token request"""
    refresh_token: str

class ChangePassword(BaseModel):
    """Cambio de contraseña"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Nueva password debe tener al menos 8 caracteres')
        return v

class LoginResponse(BaseModel):
    """Response completo de login"""
    user: "UserResponse"
    token: Token
    message: str = "Login exitoso"
    login_success: bool = True

class RegisterResponse(BaseModel):
    """Response completo de registro"""
    user: "UserResponse"
    message: str = "Usuario registrado exitosamente"

class LogoutResponse(BaseModel):
    """Response de logout"""
    message: str = "Logout exitoso"
    success: bool = True

# Forward references
from app.schemas.user import UserResponse
LoginResponse.model_rebuild()
RegisterResponse.model_rebuild()