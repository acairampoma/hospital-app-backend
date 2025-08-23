from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import (
    UserLogin, UserRegister, TokenRefresh, ChangePassword,
    LoginResponse, RegisterResponse, Token, LogoutResponse
)
from app.schemas.user import UserResponse
from app.schemas.common import ApiResponse, MessageResponse
from app.services.auth_service import AuthService
from app.core.security import get_current_user_id, get_current_user
from app.core.config import settings
from app.models.user import User
from datetime import datetime

router = APIRouter()

@router.post("/register", response_model=ApiResponse[RegisterResponse], status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """🔐 Registrar nuevo usuario médico"""
    
    try:
        # Registrar usuario
        user = await AuthService.register_user(db, user_data)
        
        # Crear response
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            nombre_completo=user.nombre_completo,
            especialidad=user.especialidad,
            colegiatura=user.colegiatura,
            enabled=user.enabled,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        register_response = RegisterResponse(
            user=user_response,
            message=f"Usuario médico {user.email} registrado exitosamente"
        )
        
        return ApiResponse.success_response(
            data=register_response,
            message="Registro exitoso"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """🔐 Login de usuario médico"""
    
    try:
        # Autenticar usuario
        user = await AuthService.authenticate_user(db, user_data.username, user_data.password)
        
        # Crear tokens
        tokens = AuthService.create_tokens_for_user(user)
        
        # Guardar refresh token
        await AuthService.update_refresh_token(db, user.id, tokens["refresh_token"])
        
        # Crear responses
        token_response = Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            nombre_completo=user.nombre_completo,
            especialidad=user.especialidad,
            colegiatura=user.colegiatura,
            enabled=user.enabled,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        login_response = LoginResponse(
            user=user_response,
            token=token_response,
            message=f"Bienvenido Dr(a). {user.nombre_completo or user.username}",
            login_success=True
        )
        
        return ApiResponse.success_response(
            data=login_response,
            message="Login exitoso"
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/refresh", response_model=ApiResponse[Token])
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """🔄 Renovar access token"""
    
    try:
        # Verificar refresh token
        user = await AuthService.verify_refresh_token(db, token_data.refresh_token)
        
        # Crear nuevo access token
        tokens = AuthService.create_tokens_for_user(user)
        
        token_response = Token(
            access_token=tokens["access_token"],
            refresh_token=token_data.refresh_token,  # Mantener el mismo refresh
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return ApiResponse.success_response(
            data=token_response,
            message="Token renovado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """👤 Obtener información del usuario actual"""
    
    user_response = UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        nombre_completo=current_user.nombre_completo,
        especialidad=current_user.especialidad,
        colegiatura=current_user.colegiatura,
        cargo=current_user.cargo,
        telefono=current_user.telefono,
        enabled=current_user.enabled,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )
    
    return ApiResponse.success_response(
        data=user_response,
        message="Información de usuario obtenida"
    )

@router.post("/logout", response_model=ApiResponse[LogoutResponse])
async def logout(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🚪 Logout del usuario"""
    
    try:
        # Limpiar refresh token
        success = await AuthService.logout_user(db, current_user_id)
        
        if success:
            logout_response = LogoutResponse(
                message="Sesión cerrada exitosamente",
                success=True
            )
            
            return ApiResponse.success_response(
                data=logout_response,
                message="Logout exitoso"
            )
        else:
            raise HTTPException(status_code=400, detail="Error en logout")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/change-password", response_model=ApiResponse[MessageResponse])
async def change_password(
    password_data: ChangePassword,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔐 Cambiar contraseña del usuario"""
    
    try:
        success = await AuthService.change_password(
            db, 
            current_user_id, 
            password_data.current_password, 
            password_data.new_password
        )
        
        if success:
            message_response = MessageResponse(
                message="Contraseña cambiada exitosamente",
                success=True
            )
            
            return ApiResponse.success_response(
                data=message_response,
                message="Contraseña actualizada"
            )
        else:
            raise HTTPException(status_code=400, detail="Error cambiando contraseña")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/validate-medico", response_model=ApiResponse[dict])
async def validate_medico(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """👨‍⚕️ Validar si el usuario es médico"""
    
    try:
        is_medico = await AuthService.validate_medico_permissions(db, current_user_id)
        medico_info = await AuthService.get_medico_info(db, current_user_id)
        
        result = {
            "is_medico": is_medico,
            "medico_info": medico_info,
            "permissions": {
                "puede_crear_recetas": is_medico,
                "puede_crear_notas": is_medico,
                "puede_crear_ordenes": is_medico
            }
        }
        
        return ApiResponse.success_response(
            data=result,
            message="Validación médica completada"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", response_model=ApiResponse[dict])
async def auth_health():
    """💚 Health check del módulo de autenticación"""
    
    health_data = {
        "status": "UP",
        "module": "Authentication",
        "version": "1.0.0",
        "timestamp": datetime.now(),
        "features": [
            "JWT Authentication",
            "Refresh Token Support",
            "Medical User Registration",
            "Password Management",
            "Medical Permissions Validation"
        ],
        "endpoints": [
            "POST /auth/register",
            "POST /auth/login", 
            "POST /auth/refresh",
            "GET /auth/me",
            "POST /auth/logout",
            "PUT /auth/change-password",
            "GET /auth/validate-medico"
        ]
    }
    
    return ApiResponse.success_response(
        data=health_data,
        message="Módulo de autenticación operativo"
    )