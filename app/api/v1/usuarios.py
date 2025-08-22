from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserSearchResponse,
    ChangePasswordRequest, UserListResponse
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services.user_service import UserService
from app.core.security import get_current_user_id, get_current_user
from app.models.user import User
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    user_data: UserCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """👤 Crear nuevo usuario médico"""
    
    try:
        user = await UserService.crear_usuario(db, user_data, current_user_id)
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
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
        
        return ApiResponse.success_response(
            data=user_response,
            message="Usuario médico creado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ApiResponse[UserListResponse])
async def obtener_usuarios(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    especialidad: Optional[str] = Query(None),
    cargo: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener lista de usuarios médicos con filtros"""
    
    try:
        result = await UserService.obtener_usuarios_paginado(
            db=db,
            page=page,
            size=size,
            search=search,
            especialidad=especialidad,
            cargo=cargo,
            enabled=enabled
        )
        
        users_response = [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
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
            for user in result["users"]
        ]
        
        list_response = UserListResponse(
            users=users_response,
            total=result["total"],
            page=page,
            size=size,
            total_pages=result["total_pages"]
        )
        
        return ApiResponse.success_response(
            data=list_response,
            message=f"Obtenidos {len(users_response)} usuarios"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def obtener_usuario_por_id(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """👤 Obtener usuario por ID"""
    
    try:
        user = await UserService.obtener_usuario_por_id(db, user_id)
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
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
        
        return ApiResponse.success_response(
            data=user_response,
            message="Usuario obtenido exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def actualizar_usuario(
    user_id: int,
    user_data: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """✏️ Actualizar usuario médico"""
    
    try:
        user = await UserService.actualizar_usuario(db, user_id, user_data, current_user_id)
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
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
        
        return ApiResponse.success_response(
            data=user_response,
            message="Usuario actualizado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}", response_model=ApiResponse[MessageResponse])
async def eliminar_usuario(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🗑️ Eliminar usuario (soft delete)"""
    
    try:
        success = await UserService.eliminar_usuario(db, user_id, current_user_id)
        
        if success:
            message_response = MessageResponse(
                message="Usuario eliminado exitosamente",
                success=True
            )
            
            return ApiResponse.success_response(
                data=message_response,
                message="Usuario eliminado"
            )
        else:
            raise HTTPException(status_code=400, detail="Error eliminando usuario")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/toggle-status", response_model=ApiResponse[UserResponse])
async def cambiar_estado_usuario(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔄 Activar/Desactivar usuario"""
    
    try:
        user = await UserService.cambiar_estado_usuario(db, user_id, current_user_id)
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
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
        
        estado = "activado" if user.enabled else "desactivado"
        
        return ApiResponse.success_response(
            data=user_response,
            message=f"Usuario {estado} exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search/medicos", response_model=ApiResponse[List[UserSearchResponse]])
async def buscar_medicos(
    q: str = Query(..., min_length=2),
    especialidad: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Buscar médicos por nombre, especialidad o colegiatura"""
    
    try:
        medicos = await UserService.buscar_medicos(db, q, especialidad)
        
        search_response = [
            UserSearchResponse(
                id=medico.id,
                nombre_completo=medico.nombre_completo or medico.username,
                especialidad=medico.especialidad,
                colegiatura=medico.colegiatura,
                cargo=medico.cargo
            )
            for medico in medicos
        ]
        
        return ApiResponse.success_response(
            data=search_response,
            message=f"Encontrados {len(search_response)} médicos"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/validate/{colegiatura}", response_model=ApiResponse[dict])
async def validar_colegiatura(
    colegiatura: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """✅ Validar si número de colegiatura está disponible"""
    
    try:
        disponible = await UserService.validar_colegiatura_disponible(db, colegiatura)
        
        result = {
            "colegiatura": colegiatura,
            "disponible": disponible,
            "mensaje": "Colegiatura disponible" if disponible else "Colegiatura ya registrada"
        }
        
        return ApiResponse.success_response(
            data=result,
            message="Validación completada"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/especialidades/list", response_model=ApiResponse[List[dict]])
async def obtener_especialidades(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener lista de especialidades médicas"""
    
    try:
        especialidades = await UserService.obtener_especialidades_activas(db)
        
        return ApiResponse.success_response(
            data=especialidades,
            message=f"Obtenidas {len(especialidades)} especialidades"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/resumen", response_model=ApiResponse[dict])
async def obtener_estadisticas_usuarios(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📊 Obtener estadísticas generales de usuarios"""
    
    try:
        stats = await UserService.obtener_estadisticas_usuarios(db)
        
        return ApiResponse.success_response(
            data=stats,
            message="Estadísticas obtenidas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/reset-password", response_model=ApiResponse[MessageResponse])
async def resetear_password_usuario(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔑 Resetear contraseña de usuario"""
    
    try:
        nueva_password = await UserService.resetear_password_usuario(db, user_id, current_user_id)
        
        message_response = MessageResponse(
            message=f"Contraseña reseteada. Nueva contraseña temporal: {nueva_password}",
            success=True
        )
        
        return ApiResponse.success_response(
            data=message_response,
            message="Contraseña reseteada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", response_model=ApiResponse[dict])
async def usuarios_health():
    """💚 Health check del módulo de usuarios"""
    
    health_data = {
        "status": "UP",
        "module": "Users Management",
        "version": "1.0.0",
        "timestamp": datetime.now(),
        "features": [
            "User CRUD Operations",
            "Medical Professional Management",
            "User Search and Filtering",
            "Specialties Management",
            "Password Reset",
            "User Statistics"
        ],
        "endpoints": [
            "POST /users/",
            "GET /users/",
            "GET /users/{user_id}",
            "PUT /users/{user_id}",
            "DELETE /users/{user_id}",
            "PUT /users/{user_id}/toggle-status",
            "GET /users/search/medicos",
            "GET /users/validate/{colegiatura}",
            "GET /users/especialidades/list",
            "GET /users/stats/resumen",
            "PUT /users/{user_id}/reset-password"
        ]
    }
    
    return ApiResponse.success_response(
        data=health_data,
        message="Módulo de usuarios operativo"
    )