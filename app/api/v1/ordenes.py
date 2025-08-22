from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.orden import (
    OrdenCabCreate, OrdenCabUpdate, OrdenCompletaResponse,
    OrdenDetCreate, OrdenDetUpdate, OrdenCabResponse,
    OrdenesListResponse, OrdenSearchResponse
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services.orden_service import OrdenService
from app.core.security import get_current_user_id
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=ApiResponse[OrdenCompletaResponse], status_code=status.HTTP_201_CREATED)
async def crear_orden(
    orden_data: OrdenCabCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Crear nueva orden médica"""
    
    try:
        orden = await OrdenService.crear_orden(db, orden_data, current_user_id)
        
        # Convertir detalles
        detalles_response = []
        for detalle in orden.detalles:
            detalles_response.append({
                "id": detalle.id,
                "tipo_orden": detalle.tipo_orden,
                "codigo_examen": detalle.codigo_examen,
                "nombre_examen": detalle.nombre_examen,
                "categoria": detalle.categoria,
                "subcategoria": detalle.subcategoria,
                "urgente": detalle.urgente,
                "observaciones": detalle.observaciones,
                "indicaciones_especiales": detalle.indicaciones_especiales,
                "ayuno_requerido": detalle.ayuno_requerido,
                "horas_ayuno": detalle.horas_ayuno,
                "estado": detalle.estado,
                "fecha_programada": detalle.fecha_programada
            })
        
        orden_response = OrdenCompletaResponse(
            id=orden.id,
            numero_orden=orden.numero_orden,
            tipo_origen=orden.tipo_origen,
            origen_id=orden.origen_id,
            paciente_id=orden.paciente_id,
            paciente_nombre=orden.paciente_nombre,
            paciente_documento=orden.paciente_documento,
            diagnostico_principal=orden.diagnostico_principal,
            justificacion_clinica=orden.justificacion_clinica,
            observaciones_generales=orden.observaciones_generales,
            fecha_solicitud=orden.fecha_solicitud,
            creado_por=orden.creado_por,
            medico_nombre=orden.medico_nombre,
            medico_especialidad=orden.medico_especialidad,
            medico_colegiatura=orden.medico_colegiatura,
            estado=orden.estado,
            prioridad=orden.prioridad,
            created_at=orden.created_at,
            updated_at=orden.updated_at,
            detalles=detalles_response
        )
        
        return ApiResponse.success_response(
            data=orden_response,
            message=f"Orden médica {orden.numero_orden} creada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ApiResponse[OrdenesListResponse])
async def obtener_ordenes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tipo_origen: Optional[str] = Query(None),
    origen_id: Optional[int] = Query(None),
    paciente_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener órdenes médicas con filtros"""
    
    try:
        result = await OrdenService.obtener_ordenes_paginado(
            db=db,
            page=page,
            size=size,
            medico_id=current_user_id,
            tipo_origen=tipo_origen,
            origen_id=origen_id,
            paciente_id=paciente_id,
            estado=estado,
            prioridad=prioridad,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
        
        ordenes_response = [
            OrdenCabResponse(
                id=orden.id,
                numero_orden=orden.numero_orden,
                tipo_origen=orden.tipo_origen,
                origen_id=orden.origen_id,
                paciente_id=orden.paciente_id,
                paciente_nombre=orden.paciente_nombre,
                paciente_documento=orden.paciente_documento,
                diagnostico_principal=orden.diagnostico_principal,
                justificacion_clinica=orden.justificacion_clinica,
                observaciones_generales=orden.observaciones_generales,
                fecha_solicitud=orden.fecha_solicitud,
                creado_por=orden.creado_por,
                medico_nombre=orden.medico_nombre,
                medico_especialidad=orden.medico_especialidad,
                medico_colegiatura=orden.medico_colegiatura,
                estado=orden.estado,
                prioridad=orden.prioridad,
                created_at=orden.created_at,
                updated_at=orden.updated_at,
                total_examenes=len(orden.detalles) if hasattr(orden, 'detalles') else 0
            )
            for orden in result["ordenes"]
        ]
        
        list_response = OrdenesListResponse(
            ordenes=ordenes_response,
            total=result["total"],
            page=page,
            size=size,
            total_pages=result["total_pages"]
        )
        
        return ApiResponse.success_response(
            data=list_response,
            message=f"Obtenidas {len(ordenes_response)} órdenes médicas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{orden_id}", response_model=ApiResponse[OrdenCompletaResponse])
async def obtener_orden_por_id(
    orden_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener orden médica completa por ID"""
    
    try:
        orden = await OrdenService.obtener_orden_por_id(db, orden_id)
        if not orden:
            raise HTTPException(status_code=404, detail="Orden médica no encontrada")
        
        # Convertir detalles
        detalles_response = []
        for detalle in orden.detalles:
            detalles_response.append({
                "id": detalle.id,
                "tipo_orden": detalle.tipo_orden,
                "codigo_examen": detalle.codigo_examen,
                "nombre_examen": detalle.nombre_examen,
                "categoria": detalle.categoria,
                "subcategoria": detalle.subcategoria,
                "urgente": detalle.urgente,
                "observaciones": detalle.observaciones,
                "indicaciones_especiales": detalle.indicaciones_especiales,
                "ayuno_requerido": detalle.ayuno_requerido,
                "horas_ayuno": detalle.horas_ayuno,
                "estado": detalle.estado,
                "fecha_programada": detalle.fecha_programada
            })
        
        orden_response = OrdenCompletaResponse(
            id=orden.id,
            numero_orden=orden.numero_orden,
            tipo_origen=orden.tipo_origen,
            origen_id=orden.origen_id,
            paciente_id=orden.paciente_id,
            paciente_nombre=orden.paciente_nombre,
            paciente_documento=orden.paciente_documento,
            diagnostico_principal=orden.diagnostico_principal,
            justificacion_clinica=orden.justificacion_clinica,
            observaciones_generales=orden.observaciones_generales,
            fecha_solicitud=orden.fecha_solicitud,
            creado_por=orden.creado_por,
            medico_nombre=orden.medico_nombre,
            medico_especialidad=orden.medico_especialidad,
            medico_colegiatura=orden.medico_colegiatura,
            estado=orden.estado,
            prioridad=orden.prioridad,
            created_at=orden.created_at,
            updated_at=orden.updated_at,
            detalles=detalles_response
        )
        
        return ApiResponse.success_response(
            data=orden_response,
            message="Orden médica obtenida exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/numero/{numero_orden}", response_model=ApiResponse[OrdenCompletaResponse])
async def obtener_orden_por_numero(
    numero_orden: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Obtener orden médica por número"""
    
    try:
        orden = await OrdenService.obtener_orden_por_numero(db, numero_orden)
        if not orden:
            raise HTTPException(status_code=404, detail="Orden médica no encontrada")
        
        # Convertir detalles
        detalles_response = []
        for detalle in orden.detalles:
            detalles_response.append({
                "id": detalle.id,
                "tipo_orden": detalle.tipo_orden,
                "codigo_examen": detalle.codigo_examen,
                "nombre_examen": detalle.nombre_examen,
                "categoria": detalle.categoria,
                "subcategoria": detalle.subcategoria,
                "urgente": detalle.urgente,
                "observaciones": detalle.observaciones,
                "indicaciones_especiales": detalle.indicaciones_especiales,
                "ayuno_requerido": detalle.ayuno_requerido,
                "horas_ayuno": detalle.horas_ayuno,
                "estado": detalle.estado,
                "fecha_programada": detalle.fecha_programada
            })
        
        orden_response = OrdenCompletaResponse(
            id=orden.id,
            numero_orden=orden.numero_orden,
            tipo_origen=orden.tipo_origen,
            origen_id=orden.origen_id,
            paciente_id=orden.paciente_id,
            paciente_nombre=orden.paciente_nombre,
            paciente_documento=orden.paciente_documento,
            diagnostico_principal=orden.diagnostico_principal,
            justificacion_clinica=orden.justificacion_clinica,
            observaciones_generales=orden.observaciones_generales,
            fecha_solicitud=orden.fecha_solicitud,
            creado_por=orden.creado_por,
            medico_nombre=orden.medico_nombre,
            medico_especialidad=orden.medico_especialidad,
            medico_colegiatura=orden.medico_colegiatura,
            estado=orden.estado,
            prioridad=orden.prioridad,
            created_at=orden.created_at,
            updated_at=orden.updated_at,
            detalles=detalles_response
        )
        
        return ApiResponse.success_response(
            data=orden_response,
            message=f"Orden {numero_orden} obtenida exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{orden_id}", response_model=ApiResponse[OrdenCompletaResponse])
async def actualizar_orden(
    orden_id: int,
    orden_data: OrdenCabUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """✏️ Actualizar orden médica"""
    
    try:
        orden = await OrdenService.actualizar_orden(db, orden_id, orden_data, current_user_id)
        
        # Recargar con detalles
        orden_completa = await OrdenService.obtener_orden_por_id(db, orden.id)
        
        # Convertir detalles
        detalles_response = []
        for detalle in orden_completa.detalles:
            detalles_response.append({
                "id": detalle.id,
                "tipo_orden": detalle.tipo_orden,
                "codigo_examen": detalle.codigo_examen,
                "nombre_examen": detalle.nombre_examen,
                "categoria": detalle.categoria,
                "subcategoria": detalle.subcategoria,
                "urgente": detalle.urgente,
                "observaciones": detalle.observaciones,
                "indicaciones_especiales": detalle.indicaciones_especiales,
                "ayuno_requerido": detalle.ayuno_requerido,
                "horas_ayuno": detalle.horas_ayuno,
                "estado": detalle.estado,
                "fecha_programada": detalle.fecha_programada
            })
        
        orden_response = OrdenCompletaResponse(
            id=orden_completa.id,
            numero_orden=orden_completa.numero_orden,
            tipo_origen=orden_completa.tipo_origen,
            origen_id=orden_completa.origen_id,
            paciente_id=orden_completa.paciente_id,
            paciente_nombre=orden_completa.paciente_nombre,
            paciente_documento=orden_completa.paciente_documento,
            diagnostico_principal=orden_completa.diagnostico_principal,
            justificacion_clinica=orden_completa.justificacion_clinica,
            observaciones_generales=orden_completa.observaciones_generales,
            fecha_solicitud=orden_completa.fecha_solicitud,
            creado_por=orden_completa.creado_por,
            medico_nombre=orden_completa.medico_nombre,
            medico_especialidad=orden_completa.medico_especialidad,
            medico_colegiatura=orden_completa.medico_colegiatura,
            estado=orden_completa.estado,
            prioridad=orden_completa.prioridad,
            created_at=orden_completa.created_at,
            updated_at=orden_completa.updated_at,
            detalles=detalles_response
        )
        
        return ApiResponse.success_response(
            data=orden_response,
            message="Orden médica actualizada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{orden_id}/estado", response_model=ApiResponse[OrdenCabResponse])
async def cambiar_estado_orden(
    orden_id: int,
    nuevo_estado: str = Query(..., regex="^(01|02|03|04|05)$"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔄 Cambiar estado de orden (01:Pendiente, 02:Programada, 03:En Proceso, 04:Completada, 05:Cancelada)"""
    
    try:
        orden = await OrdenService.cambiar_estado_orden(db, orden_id, nuevo_estado, current_user_id)
        
        orden_response = OrdenCabResponse(
            id=orden.id,
            numero_orden=orden.numero_orden,
            tipo_origen=orden.tipo_origen,
            origen_id=orden.origen_id,
            paciente_id=orden.paciente_id,
            paciente_nombre=orden.paciente_nombre,
            paciente_documento=orden.paciente_documento,
            diagnostico_principal=orden.diagnostico_principal,
            justificacion_clinica=orden.justificacion_clinica,
            observaciones_generales=orden.observaciones_generales,
            fecha_solicitud=orden.fecha_solicitud,
            creado_por=orden.creado_por,
            medico_nombre=orden.medico_nombre,
            medico_especialidad=orden.medico_especialidad,
            medico_colegiatura=orden.medico_colegiatura,
            estado=orden.estado,
            prioridad=orden.prioridad,
            created_at=orden.created_at,
            updated_at=orden.updated_at,
            total_examenes=0
        )
        
        estados_desc = {
            "01": "Pendiente",
            "02": "Programada", 
            "03": "En Proceso",
            "04": "Completada",
            "05": "Cancelada"
        }
        
        return ApiResponse.success_response(
            data=orden_response,
            message=f"Orden cambiada a estado: {estados_desc.get(nuevo_estado, nuevo_estado)}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/paciente/{paciente_id}/historial", response_model=ApiResponse[List[OrdenCabResponse]])
async def obtener_historial_ordenes_paciente(
    paciente_id: int,
    tipo_orden: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """👤 Obtener historial de órdenes médicas de un paciente"""
    
    try:
        ordenes = await OrdenService.obtener_ordenes_por_paciente(db, paciente_id, tipo_orden, limit)
        
        ordenes_response = [
            OrdenCabResponse(
                id=orden.id,
                numero_orden=orden.numero_orden,
                tipo_origen=orden.tipo_origen,
                origen_id=orden.origen_id,
                paciente_id=orden.paciente_id,
                paciente_nombre=orden.paciente_nombre,
                paciente_documento=orden.paciente_documento,
                diagnostico_principal=orden.diagnostico_principal,
                justificacion_clinica=orden.justificacion_clinica,
                observaciones_generales=orden.observaciones_generales,
                fecha_solicitud=orden.fecha_solicitud,
                creado_por=orden.creado_por,
                medico_nombre=orden.medico_nombre,
                medico_especialidad=orden.medico_especialidad,
                medico_colegiatura=orden.medico_colegiatura,
                estado=orden.estado,
                prioridad=orden.prioridad,
                created_at=orden.created_at,
                updated_at=orden.updated_at,
                total_examenes=len(orden.detalles) if hasattr(orden, 'detalles') else 0
            )
            for orden in ordenes
        ]
        
        return ApiResponse.success_response(
            data=ordenes_response,
            message=f"Historial de {len(ordenes_response)} órdenes del paciente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/origen/{tipo_origen}/{origen_id}", response_model=ApiResponse[List[OrdenCabResponse]])
async def obtener_ordenes_por_origen(
    tipo_origen: str,
    origen_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener órdenes por origen (consulta, hospitalización, etc.)"""
    
    try:
        ordenes = await OrdenService.obtener_ordenes_por_origen(db, tipo_origen, origen_id)
        
        ordenes_response = [
            OrdenCabResponse(
                id=orden.id,
                numero_orden=orden.numero_orden,
                tipo_origen=orden.tipo_origen,
                origen_id=orden.origen_id,
                paciente_id=orden.paciente_id,
                paciente_nombre=orden.paciente_nombre,
                paciente_documento=orden.paciente_documento,
                diagnostico_principal=orden.diagnostico_principal,
                justificacion_clinica=orden.justificacion_clinica,
                observaciones_generales=orden.observaciones_generales,
                fecha_solicitud=orden.fecha_solicitud,
                creado_por=orden.creado_por,
                medico_nombre=orden.medico_nombre,
                medico_especialidad=orden.medico_especialidad,
                medico_colegiatura=orden.medico_colegiatura,
                estado=orden.estado,
                prioridad=orden.prioridad,
                created_at=orden.created_at,
                updated_at=orden.updated_at,
                total_examenes=len(orden.detalles) if hasattr(orden, 'detalles') else 0
            )
            for orden in ordenes
        ]
        
        return ApiResponse.success_response(
            data=ordenes_response,
            message=f"Obtenidas {len(ordenes_response)} órdenes para {tipo_origen}:{origen_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/examenes/tipos", response_model=ApiResponse[List[dict]])
async def obtener_tipos_examenes(
    categoria: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔬 Obtener tipos de exámenes médicos disponibles"""
    
    try:
        tipos = await OrdenService.obtener_tipos_examenes_disponibles(db, categoria)
        
        return ApiResponse.success_response(
            data=tipos,
            message=f"Obtenidos {len(tipos)} tipos de exámenes"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search/examenes", response_model=ApiResponse[List[dict]])
async def buscar_examenes(
    q: str = Query(..., min_length=2),
    categoria: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Buscar exámenes médicos por nombre o código"""
    
    try:
        examenes = await OrdenService.buscar_examenes_disponibles(db, q, categoria, limit)
        
        return ApiResponse.success_response(
            data=examenes,
            message=f"Encontrados {len(examenes)} exámenes"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/medico", response_model=ApiResponse[dict])
async def obtener_estadisticas_ordenes_medico(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📊 Obtener estadísticas de órdenes del médico actual"""
    
    try:
        stats = await OrdenService.obtener_estadisticas_medico(db, current_user_id)
        
        return ApiResponse.success_response(
            data=stats,
            message="Estadísticas de órdenes obtenidas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/examenes/mas-solicitados", response_model=ApiResponse[List[dict]])
async def obtener_examenes_mas_solicitados(
    limite: int = Query(10, ge=1, le=50),
    categoria: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔬 Obtener exámenes más solicitados globalmente"""
    
    try:
        examenes = await OrdenService.obtener_examenes_mas_solicitados(db, limite, categoria)
        
        return ApiResponse.success_response(
            data=examenes,
            message=f"Top {len(examenes)} exámenes más solicitados"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", response_model=ApiResponse[dict])
async def ordenes_health():
    """💚 Health check del módulo de órdenes médicas"""
    
    health_data = {
        "status": "UP",
        "module": "Medical Orders",
        "version": "1.0.0",
        "timestamp": datetime.now(),
        "features": [
            "Medical Order Management",
            "Laboratory Orders",
            "Imaging Orders", 
            "Procedure Orders",
            "Priority Management",
            "State Tracking",
            "Patient History",
            "Order Statistics",
            "Examination Search",
            "Auto-numbering System"
        ],
        "endpoints": [
            "POST /ordenes/",
            "GET /ordenes/",
            "GET /ordenes/{id}",
            "GET /ordenes/numero/{numero}",
            "PUT /ordenes/{id}",
            "PUT /ordenes/{id}/estado",
            "GET /ordenes/paciente/{id}/historial",
            "GET /ordenes/origen/{tipo}/{id}",
            "GET /ordenes/examenes/tipos",
            "GET /ordenes/search/examenes",
            "GET /ordenes/stats/medico",
            "GET /ordenes/examenes/mas-solicitados"
        ],
        "order_types": [
            "LABORATORIO",
            "IMAGEN",
            "PROCEDIMIENTO",
            "INTERCONSULTA",
            "TERAPIA"
        ],
        "priorities": [
            "RUTINA",
            "URGENTE", 
            "EMERGENCIA"
        ],
        "states": [
            "01: Pendiente",
            "02: Programada",
            "03: En Proceso",
            "04: Completada", 
            "05: Cancelada"
        ]
    }
    
    return ApiResponse.success_response(
        data=health_data,
        message="Módulo de órdenes médicas operativo"
    )