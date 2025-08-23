"""
🚀 API Endpoints para Upload y Registro Completo
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse, MessageResponse
from app.schemas.user import UserResponse
from app.services.cloudinary_service import cloudinary_service
from app.services.email_service import email_service
from app.services.auth_service import AuthService
from typing import Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register-with-photo", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register_user_with_photo(
    # Datos básicos
    firstName: str = Form(..., description="Nombre"),
    lastName: str = Form(..., description="Apellido"),
    email: str = Form(..., description="Email"),
    username: str = Form(..., description="Usuario"),
    password: str = Form(..., description="Contraseña"),
    
    # Datos profesionales (opcional)
    especialidad: Optional[str] = Form(None, description="Especialidad médica"),
    colegiatura: Optional[str] = Form(None, description="Número de colegiatura"),
    telefono: Optional[str] = Form(None, description="Teléfono"),
    cargo: Optional[str] = Form(None, description="Cargo"),
    
    # Foto de perfil (opcional)
    photo: Optional[UploadFile] = File(None, description="Foto de perfil"),
    
    db: AsyncSession = Depends(get_db)
):
    """
    🎯 Registro completo con foto y email de bienvenida
    """
    try:
        logger.info(f"🔄 Iniciando registro para: {email}")
        
        # 1. Verificar si el usuario ya existe
        existing_user = await AuthService.get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=400, 
                detail="Email ya registrado"
            )
        
        existing_username = await AuthService.get_user_by_username(db, username)
        if existing_username:
            raise HTTPException(
                status_code=400, 
                detail="Usuario ya existe"
            )
        
        # 2. Subir foto a Cloudinary si se proporciona
        photo_url = None
        if photo and photo.size > 0:
            logger.info(f"📷 Subiendo foto para {username}")
            
            # Validar tipo de archivo
            if not photo.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail="Solo se permiten archivos de imagen"
                )
            
            # Validar tamaño (5MB máximo)
            if photo.size > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="Archivo muy grande. Máximo 5MB"
                )
            
            # Subir a Cloudinary
            photo_content = await photo.read()
            upload_result = await cloudinary_service.upload_avatar(
                file_content=photo_content,
                filename=photo.filename or "avatar.jpg",
                user_id=username
            )
            
            if upload_result["success"]:
                photo_url = upload_result["url"]
                logger.info(f"✅ Foto subida: {photo_url}")
            else:
                logger.warning(f"⚠️ Error subiendo foto: {upload_result['message']}")
        
        # 3. Preparar datos profesionales para JSONB
        datos_profesional = {}
        if especialidad:
            datos_profesional["especialidad"] = especialidad
        if colegiatura:
            datos_profesional["colegiatura"] = colegiatura
        if telefono:
            datos_profesional["telefono"] = telefono
        if cargo:
            datos_profesional["cargo"] = cargo
        if photo_url:
            datos_profesional["foto_url"] = photo_url
        
        # 4. Crear usuario en la base de datos
        from app.schemas.auth import UserRegister
        user_data = UserRegister(
            username=username,
            email=email,
            password=password,
            first_name=firstName,
            last_name=lastName,
            datos_profesional=datos_profesional if datos_profesional else None
        )
        
        user = await AuthService.register_user(db, user_data)
        
        # 5. Enviar email de bienvenida (asíncrono)
        try:
            await email_service.send_welcome_email(
                email=email,
                name=f"{firstName} {lastName}",
                username=username
            )
            logger.info(f"✅ Email de bienvenida enviado a {email}")
        except Exception as e:
            logger.warning(f"⚠️ Error enviando email de bienvenida: {str(e)}")
        
        # 6. Crear response
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            nombre_completo=user.nombre_completo,
            especialidad=user.especialidad,
            colegiatura=user.colegiatura,
            cargo=user.cargo,
            telefono=user.telefono,
            enabled=user.enabled,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        logger.info(f"✅ Usuario registrado exitosamente: {username}")
        
        return ApiResponse.success_response(
            data=user_response,
            message=f"Usuario {firstName} {lastName} registrado exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en registro: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/send-recovery-code", response_model=ApiResponse[dict])
async def send_recovery_code(
    email: str = Form(..., description="Email del usuario"),
    db: AsyncSession = Depends(get_db)
):
    """
    🔐 Enviar código de recuperación por email
    """
    try:
        # 1. Verificar que el email existe
        user = await AuthService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Email no registrado en el sistema"
            )
        
        # 2. Enviar código por SendGrid
        result = await email_service.send_recovery_code(
            email=email,
            name=user.nombre_completo or user.username
        )
        
        if result["success"]:
            # TODO: Guardar código en caché/DB con expiración
            logger.info(f"✅ Código de recuperación enviado a {email}")
            
            return ApiResponse.success_response(
                data={
                    "email": email,
                    "code_sent": True,
                    "message": "Código enviado correctamente"
                },
                message="Código de recuperación enviado"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result["message"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error enviando código: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.post("/verify-recovery-code", response_model=ApiResponse[dict])
async def verify_recovery_code(
    email: str = Form(..., description="Email del usuario"),
    code: str = Form(..., description="Código de recuperación"),
    new_password: str = Form(..., description="Nueva contraseña"),
    db: AsyncSession = Depends(get_db)
):
    """
    🔐 Verificar código y cambiar contraseña
    """
    try:
        # TODO: Verificar código desde caché/DB
        # Por ahora solo simulamos la verificación
        
        user = await AuthService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Cambiar contraseña
        success = await AuthService.reset_password(db, user.id, new_password)
        
        if success:
            return ApiResponse.success_response(
                data={
                    "email": email,
                    "password_reset": True,
                    "message": "Contraseña actualizada correctamente"
                },
                message="Contraseña cambiada exitosamente"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Error cambiando contraseña"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error verificando código: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.get("/health", response_model=ApiResponse[dict])
async def upload_health():
    """💚 Health check del módulo de upload"""
    
    health_data = {
        "status": "UP",
        "module": "Upload & Registration",
        "version": "1.0.0",
        "timestamp": datetime.now(),
        "features": [
            "Cloudinary Image Upload",
            "SendGrid Email Service",
            "Complete User Registration",
            "Password Recovery"
        ],
        "endpoints": [
            "POST /upload/register-with-photo",
            "POST /upload/send-recovery-code",
            "POST /upload/verify-recovery-code"
        ]
    }
    
    return ApiResponse.success_response(
        data=health_data,
        message="Módulo de upload operativo"
    )