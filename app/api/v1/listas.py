from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.lista import (
    PacientePorCamaResponse, CamasListResponse, CamaDisponibilidadResponse,
    EstructuraHospitalResponse, EstructuraCompleta,
    MovimientoCamaCreate, MovimientoCamaResponse,
    AsignacionCamaRequest, CambioServicioRequest
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services.lista_service import ListaService
from app.core.security import get_current_user_id
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()

# ===== ENDPOINTS DE GESTIÓN DE CAMAS =====

@router.get("/camas", response_model=ApiResponse[Dict[str, Any]])
async def obtener_listado_camas(
    servicio: Optional[str] = Query(None),
    unidad: Optional[str] = Query(None),
    disponible: Optional[bool] = Query(None),
    tipo_cama: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🛏️ Obtener listado de camas con filtros"""
    
    try:
        camas = await ListaService.obtener_camas_con_filtros(
            db, servicio, unidad, disponible, tipo_cama
        )
        
        # Estadísticas
        total_camas = len(camas)
        camas_ocupadas = sum(1 for c in camas if c['ocupada'])
        camas_disponibles = total_camas - camas_ocupadas
        
        return ApiResponse.success_response(
            data={
                "camas": camas,
                "total": total_camas,
                "estadisticas": {
                    "total_camas": total_camas,
                    "ocupadas": camas_ocupadas,
                    "disponibles": camas_disponibles,
                    "porcentaje_ocupacion": round(
                        (camas_ocupadas / total_camas * 100) if total_camas > 0 else 0, 2
                    )
                }
            },
            message="Listado de camas obtenido exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener listado de camas: {str(e)}"
        )

@router.get("/camas/disponibilidad", response_model=ApiResponse[List[Dict[str, Any]]])
async def obtener_disponibilidad_camas(
    servicio: Optional[str] = Query(None),
    unidad: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📊 Obtener disponibilidad de camas por servicio/unidad"""
    
    try:
        disponibilidad = await ListaService.obtener_disponibilidad_por_servicio(
            db, servicio, unidad
        )
        
        return ApiResponse.success_response(
            data=disponibilidad,
            message="Disponibilidad obtenida exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener disponibilidad: {str(e)}"
        )

@router.get("/camas/{cama_id}/historial", response_model=ApiResponse[Dict[str, Any]])
async def obtener_historial_cama(
    cama_id: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener historial de ocupación de una cama"""
    
    # Por ahora retornamos datos simulados
    return ApiResponse.success_response(
        data={
            "cama_id": cama_id,
            "historial": [],
            "mensaje": "Funcionalidad en desarrollo"
        },
        message="Historial de cama obtenido"
    )

@router.post("/camas/{cama_id}/asignar", response_model=ApiResponse[Dict[str, Any]])
async def asignar_paciente_cama(
    cama_id: str,
    asignacion: AsignacionCamaRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """👤 Asignar paciente a cama"""
    
    try:
        resultado = await ListaService.asignar_paciente_a_cama(
            db, cama_id, asignacion.dict()
        )
        
        return ApiResponse.success_response(
            data=resultado,
            message="Paciente asignado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al asignar paciente: {str(e)}"
        )

@router.post("/camas/{cama_id}/liberar", response_model=ApiResponse[Dict[str, Any]])
async def liberar_cama(
    cama_id: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔓 Liberar cama (dar de alta al paciente)"""
    
    try:
        resultado = await ListaService.liberar_cama(db, cama_id)
        
        return ApiResponse.success_response(
            data=resultado,
            message="Cama liberada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al liberar cama: {str(e)}"
        )

@router.post("/pacientes/{paciente_id}/cambiar-servicio", response_model=ApiResponse[Dict[str, Any]])
async def cambiar_servicio_paciente(
    paciente_id: int,
    cambio: CambioServicioRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔄 Cambiar paciente a otro servicio/cama"""
    
    # Por ahora retornamos datos simulados
    return ApiResponse.success_response(
        data={
            "paciente_id": paciente_id,
            "nueva_cama": cambio.nueva_cama_id,
            "mensaje": "Funcionalidad en desarrollo"
        },
        message="Cambio de servicio realizado"
    )

# ===== ENDPOINTS DE ESTRUCTURA HOSPITALARIA =====

@router.get("/estructura", response_model=ApiResponse[Dict[str, Any]])
async def obtener_estructura_hospital(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener estructura completa del hospital"""
    
    try:
        estructura = await ListaService.obtener_estructura_completa(db)
        
        return ApiResponse.success_response(
            data=estructura,
            message="Estructura del hospital obtenida exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estructura: {str(e)}"
        )

@router.get("/estructura/servicios", response_model=ApiResponse[List[Dict[str, Any]]])
async def obtener_servicios_medicos(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener lista de servicios médicos"""
    
    try:
        servicios = await ListaService.obtener_servicios_medicos(db)
        
        return ApiResponse.success_response(
            data=servicios,
            message="Servicios médicos obtenidos exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servicios: {str(e)}"
        )

@router.get("/estructura/servicio/{servicio}/unidades", response_model=ApiResponse[List[Dict[str, Any]]])
async def obtener_unidades_servicio(
    servicio: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener unidades de un servicio específico"""
    
    try:
        unidades = await ListaService.obtener_unidades_por_servicio(db, servicio)
        
        return ApiResponse.success_response(
            data=unidades,
            message=f"Unidades del servicio {servicio} obtenidas exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener unidades: {str(e)}"
        )

# ===== ENDPOINTS DE REPORTES =====

@router.get("/reportes/ocupacion", response_model=ApiResponse[Dict[str, Any]])
async def reporte_ocupacion(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📊 Reporte de ocupación de camas"""
    
    try:
        reporte = await ListaService.obtener_reporte_ocupacion(db)
        
        return ApiResponse.success_response(
            data=reporte,
            message="Reporte de ocupación generado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar reporte: {str(e)}"
        )

@router.get("/reportes/movimientos", response_model=ApiResponse[Dict[str, Any]])
async def reporte_movimientos(
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📊 Reporte de movimientos de camas"""
    
    # Por ahora retornamos datos simulados
    return ApiResponse.success_response(
        data={
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "movimientos": [],
            "mensaje": "Funcionalidad en desarrollo"
        },
        message="Reporte de movimientos generado"
    )

# ===== ENDPOINTS DE BÚSQUEDA =====

@router.get("/search/pacientes", response_model=ApiResponse[List[Dict[str, Any]]])
async def buscar_pacientes(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Buscar pacientes hospitalizados"""
    
    try:
        pacientes = await ListaService.buscar_pacientes_hospitalizados(db, q)
        
        return ApiResponse.success_response(
            data=pacientes,
            message=f"Se encontraron {len(pacientes)} pacientes"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
        )

# ===== HEALTH CHECK =====

@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def health_check():
    """🏥 Health check del módulo de listas y camas"""
    
    return ApiResponse.success_response(
        data={
            "status": "UP",
            "module": "Listas y Gestión de Camas",
            "version": "1.0.0",
            "endpoints": {
                "camas": "Gestión de camas hospitalarias",
                "estructura": "Estructura del hospital",
                "reportes": "Reportes de ocupación",
                "search": "Búsqueda de pacientes"
            },
            "features": [
                "✅ Listado de camas con filtros",
                "✅ Disponibilidad por servicio",
                "✅ Asignación de pacientes",
                "✅ Estructura hospitalaria",
                "✅ Reportes de ocupación",
                "✅ Búsqueda de pacientes"
            ]
        },
        message="Módulo de listas funcionando correctamente"
    )