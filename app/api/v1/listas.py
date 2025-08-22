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
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# ===== ENDPOINTS DE GESTIÓN DE CAMAS =====

@router.get("/camas", response_model=ApiResponse[CamasListResponse])
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
        
        camas_response = []
        for cama in camas:
            # Obtener paciente actual si existe
            paciente_actual = None
            if cama.pacientes_por_cama:
                for paciente_cama in cama.pacientes_por_cama:
                    if paciente_cama.fecha_salida is None:  # Paciente activo
                        paciente_actual = {
                            "paciente_id": paciente_cama.paciente_id,
                            "nombre_paciente": paciente_cama.nombre_paciente,
                            "documento": paciente_cama.documento,
                            "fecha_ingreso": paciente_cama.fecha_ingreso,
                            "dias_estancia": paciente_cama.dias_estancia
                        }
                        break
            
            camas_response.append(PacientePorCamaResponse(
                id=cama.id,
                codigo_cama=cama.codigo_cama,
                numero_cama=cama.numero_cama,
                servicio=cama.servicio,
                unidad=cama.unidad,
                piso=cama.piso,
                tipo_cama=cama.tipo_cama,
                estado_cama=cama.estado_cama,
                observaciones=cama.observaciones,
                activa=cama.activa,
                paciente_actual=paciente_actual
            ))
        
        list_response = CamasListResponse(
            camas=camas_response,
            total=len(camas_response),
            estadisticas={
                "total_camas": len(camas_response),
                "ocupadas": len([c for c in camas_response if c.paciente_actual]),
                "disponibles": len([c for c in camas_response if not c.paciente_actual and c.estado_cama == "DISPONIBLE"]),
                "en_mantenimiento": len([c for c in camas_response if c.estado_cama == "MANTENIMIENTO"]),
                "bloqueadas": len([c for c in camas_response if c.estado_cama == "BLOQUEADA"])
            }
        )
        
        return ApiResponse.success_response(
            data=list_response,
            message=f"Obtenidas {len(camas_response)} camas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/camas/disponibilidad", response_model=ApiResponse[List[CamaDisponibilidadResponse]])
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
        
        disponibilidad_response = [
            CamaDisponibilidadResponse(
                servicio=item["servicio"],
                unidad=item["unidad"],
                total_camas=item["total_camas"],
                ocupadas=item["ocupadas"],
                disponibles=item["disponibles"],
                en_mantenimiento=item["en_mantenimiento"],
                porcentaje_ocupacion=item["porcentaje_ocupacion"]
            )
            for item in disponibilidad
        ]
        
        return ApiResponse.success_response(
            data=disponibilidad_response,
            message=f"Disponibilidad de {len(disponibilidad_response)} servicios/unidades"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/camas/{cama_id}/historial", response_model=ApiResponse[List[dict]])
async def obtener_historial_cama(
    cama_id: int,
    limite: int = Query(20, ge=1, le=100),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📝 Obtener historial de ocupación de una cama"""
    
    try:
        historial = await ListaService.obtener_historial_cama(db, cama_id, limite)
        
        historial_response = []
        for registro in historial:
            historial_response.append({
                "id": registro.id,
                "paciente_id": registro.paciente_id,
                "nombre_paciente": registro.nombre_paciente,
                "documento": registro.documento,
                "fecha_ingreso": registro.fecha_ingreso,
                "fecha_salida": registro.fecha_salida,
                "dias_estancia": registro.dias_estancia,
                "motivo_ingreso": registro.motivo_ingreso,
                "observaciones": registro.observaciones
            })
        
        return ApiResponse.success_response(
            data=historial_response,
            message=f"Historial de {len(historial_response)} registros"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/camas/{cama_id}/asignar", response_model=ApiResponse[MovimientoCamaResponse])
async def asignar_paciente_a_cama(
    cama_id: int,
    asignacion_data: AsignacionCamaRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """👤 Asignar paciente a cama"""
    
    try:
        movimiento_data = MovimientoCamaCreate(
            cama_id=cama_id,
            paciente_id=asignacion_data.paciente_id,
            nombre_paciente=asignacion_data.nombre_paciente,
            documento=asignacion_data.documento,
            fecha_ingreso=asignacion_data.fecha_ingreso or datetime.utcnow(),
            motivo_ingreso=asignacion_data.motivo_ingreso,
            observaciones=asignacion_data.observaciones
        )
        
        movimiento = await ListaService.asignar_paciente_cama(db, movimiento_data, current_user_id)
        
        movimiento_response = MovimientoCamaResponse(
            id=movimiento.id,
            cama_id=movimiento.cama_id,
            paciente_id=movimiento.paciente_id,
            nombre_paciente=movimiento.nombre_paciente,
            documento=movimiento.documento,
            fecha_ingreso=movimiento.fecha_ingreso,
            fecha_salida=movimiento.fecha_salida,
            dias_estancia=movimiento.dias_estancia,
            motivo_ingreso=movimiento.motivo_ingreso,
            motivo_salida=movimiento.motivo_salida,
            observaciones=movimiento.observaciones,
            creado_por=movimiento.creado_por,
            created_at=movimiento.created_at
        )
        
        return ApiResponse.success_response(
            data=movimiento_response,
            message="Paciente asignado a cama exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/camas/{cama_id}/liberar", response_model=ApiResponse[MessageResponse])
async def liberar_cama(
    cama_id: int,
    motivo_salida: str = Query(...),
    observaciones: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🚪 Liberar cama (dar de alta al paciente)"""
    
    try:
        success = await ListaService.liberar_cama(db, cama_id, motivo_salida, observaciones, current_user_id)
        
        if success:
            message_response = MessageResponse(
                message="Cama liberada exitosamente",
                success=True
            )
            
            return ApiResponse.success_response(
                data=message_response,
                message="Cama liberada"
            )
        else:
            raise HTTPException(status_code=400, detail="Error liberando cama")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pacientes/{paciente_id}/cambiar-servicio", response_model=ApiResponse[MovimientoCamaResponse])
async def cambiar_servicio_paciente(
    paciente_id: int,
    cambio_data: CambioServicioRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔄 Cambiar paciente a otro servicio/cama"""
    
    try:
        movimiento = await ListaService.cambiar_servicio_paciente(
            db, paciente_id, cambio_data.nueva_cama_id, cambio_data.motivo_cambio, 
            cambio_data.observaciones, current_user_id
        )
        
        movimiento_response = MovimientoCamaResponse(
            id=movimiento.id,
            cama_id=movimiento.cama_id,
            paciente_id=movimiento.paciente_id,
            nombre_paciente=movimiento.nombre_paciente,
            documento=movimiento.documento,
            fecha_ingreso=movimiento.fecha_ingreso,
            fecha_salida=movimiento.fecha_salida,
            dias_estancia=movimiento.dias_estancia,
            motivo_ingreso=movimiento.motivo_ingreso,
            motivo_salida=movimiento.motivo_salida,
            observaciones=movimiento.observaciones,
            creado_por=movimiento.creado_por,
            created_at=movimiento.created_at
        )
        
        return ApiResponse.success_response(
            data=movimiento_response,
            message="Paciente cambiado de servicio exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===== ENDPOINTS DE ESTRUCTURA HOSPITALARIA =====

@router.get("/estructura", response_model=ApiResponse[EstructuraCompleta])
async def obtener_estructura_hospital(
    incluir_camas: bool = Query(False),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener estructura completa del hospital"""
    
    try:
        estructura = await ListaService.obtener_estructura_hospital(db, incluir_camas)
        
        estructura_response = EstructuraCompleta(
            servicios=estructura["servicios"],
            total_servicios=len(estructura["servicios"]),
            total_unidades=sum(len(servicio["unidades"]) for servicio in estructura["servicios"]),
            total_camas=estructura.get("total_camas", 0) if incluir_camas else 0
        )
        
        return ApiResponse.success_response(
            data=estructura_response,
            message="Estructura hospitalaria obtenida"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/estructura/servicios", response_model=ApiResponse[List[dict]])
async def obtener_servicios(
    activo: bool = Query(True),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener lista de servicios médicos"""
    
    try:
        servicios = await ListaService.obtener_servicios(db, activo)
        
        return ApiResponse.success_response(
            data=servicios,
            message=f"Obtenidos {len(servicios)} servicios"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/estructura/servicio/{servicio}/unidades", response_model=ApiResponse[List[dict]])
async def obtener_unidades_por_servicio(
    servicio: str,
    activo: bool = Query(True),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener unidades de un servicio específico"""
    
    try:
        unidades = await ListaService.obtener_unidades_por_servicio(db, servicio, activo)
        
        return ApiResponse.success_response(
            data=unidades,
            message=f"Obtenidas {len(unidades)} unidades para el servicio {servicio}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===== ENDPOINTS DE REPORTES Y ESTADÍSTICAS =====

@router.get("/reportes/ocupacion", response_model=ApiResponse[dict])
async def reporte_ocupacion_camas(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    servicio: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📊 Reporte de ocupación de camas"""
    
    try:
        reporte = await ListaService.generar_reporte_ocupacion(
            db, fecha_desde, fecha_hasta, servicio
        )
        
        return ApiResponse.success_response(
            data=reporte,
            message="Reporte de ocupación generado"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reportes/movimientos", response_model=ApiResponse[List[dict]])
async def reporte_movimientos_camas(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    servicio: Optional[str] = Query(None),
    tipo_movimiento: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📝 Reporte de movimientos de camas"""
    
    try:
        movimientos = await ListaService.obtener_movimientos_camas(
            db, fecha_desde, fecha_hasta, servicio, tipo_movimiento, page, size
        )
        
        movimientos_response = []
        for mov in movimientos["movimientos"]:
            movimientos_response.append({
                "id": mov.id,
                "cama_codigo": mov.cama.codigo_cama if mov.cama else None,
                "servicio": mov.cama.servicio if mov.cama else None,
                "unidad": mov.cama.unidad if mov.cama else None,
                "paciente_id": mov.paciente_id,
                "nombre_paciente": mov.nombre_paciente,
                "documento": mov.documento,
                "fecha_ingreso": mov.fecha_ingreso,
                "fecha_salida": mov.fecha_salida,
                "dias_estancia": mov.dias_estancia,
                "motivo_ingreso": mov.motivo_ingreso,
                "motivo_salida": mov.motivo_salida,
                "tipo_movimiento": "ALTA" if mov.fecha_salida else "INGRESO",
                "created_at": mov.created_at
            })
        
        return ApiResponse.success_response(
            data={
                "movimientos": movimientos_response,
                "total": movimientos["total"],
                "page": page,
                "size": size,
                "total_pages": movimientos["total_pages"]
            },
            message=f"Obtenidos {len(movimientos_response)} movimientos"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search/pacientes", response_model=ApiResponse[List[dict]])
async def buscar_pacientes_hospitalizados(
    q: str = Query(..., min_length=2),
    servicio: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Buscar pacientes hospitalizados"""
    
    try:
        pacientes = await ListaService.buscar_pacientes_hospitalizados(db, q, servicio, limit)
        
        pacientes_response = []
        for paciente in pacientes:
            pacientes_response.append({
                "paciente_id": paciente.paciente_id,
                "nombre_paciente": paciente.nombre_paciente,
                "documento": paciente.documento,
                "cama_codigo": paciente.cama.codigo_cama if paciente.cama else None,
                "servicio": paciente.cama.servicio if paciente.cama else None,
                "unidad": paciente.cama.unidad if paciente.cama else None,
                "fecha_ingreso": paciente.fecha_ingreso,
                "dias_estancia": paciente.dias_estancia,
                "motivo_ingreso": paciente.motivo_ingreso
            })
        
        return ApiResponse.success_response(
            data=pacientes_response,
            message=f"Encontrados {len(pacientes_response)} pacientes"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", response_model=ApiResponse[dict])
async def listas_health():
    """💚 Health check del módulo de listas y camas"""
    
    health_data = {
        "status": "UP",
        "module": "Hospital Lists & Bed Management",
        "version": "1.0.0",
        "timestamp": datetime.now(),
        "features": [
            "Bed Management",
            "Patient Assignment",
            "Service Transfers",
            "Bed Availability Tracking",
            "Hospital Structure Management",
            "Occupancy Reports",
            "Movement History",
            "Patient Search",
            "Statistics & Analytics"
        ],
        "endpoints": [
            "GET /listas/camas",
            "GET /listas/camas/disponibilidad",
            "GET /listas/camas/{id}/historial",
            "POST /listas/camas/{id}/asignar",
            "POST /listas/camas/{id}/liberar",
            "POST /listas/pacientes/{id}/cambiar-servicio",
            "GET /listas/estructura",
            "GET /listas/estructura/servicios",
            "GET /listas/estructura/servicio/{servicio}/unidades",
            "GET /listas/reportes/ocupacion",
            "GET /listas/reportes/movimientos",
            "GET /listas/search/pacientes"
        ],
        "bed_states": [
            "DISPONIBLE",
            "OCUPADA",
            "MANTENIMIENTO",
            "BLOQUEADA",
            "LIMPIEZA"
        ],
        "movement_types": [
            "INGRESO",
            "ALTA",
            "TRASLADO",
            "CAMBIO_SERVICIO"
        ]
    }
    
    return ApiResponse.success_response(
        data=health_data,
        message="Módulo de listas y camas operativo"
    )