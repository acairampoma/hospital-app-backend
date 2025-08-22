from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.receta import (
    RecetaCabCreate, RecetaCabUpdate, RecetaCompletaResponse,
    RecetaDetCreate, RecetaDetUpdate, RecetaCabResponse,
    RecetasListResponse, RecetaSearchResponse
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services.receta_service import RecetaService
from app.core.security import get_current_user_id
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=ApiResponse[RecetaCompletaResponse], status_code=status.HTTP_201_CREATED)
async def crear_receta(
    receta_data: RecetaCabCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """💊 Crear nueva receta médica"""
    
    try:
        receta = await RecetaService.crear_receta(db, receta_data, current_user_id)
        
        # Convertir detalles
        detalles_response = []
        for detalle in receta.detalles:
            detalles_response.append({
                "id": detalle.id,
                "medicamento_id": detalle.medicamento_id,
                "medicamento_codigo": detalle.medicamento_codigo,
                "medicamento_nombre": detalle.medicamento_nombre,
                "cantidad": detalle.cantidad,
                "unidad": detalle.unidad,
                "posologia": detalle.posologia,
                "duracion_tratamiento": detalle.duracion_tratamiento,
                "observaciones": detalle.observaciones,
                "sustituible": detalle.sustituible
            })
        
        receta_response = RecetaCompletaResponse(
            id=receta.id,
            numero_receta=receta.numero_receta,
            tipo_origen=receta.tipo_origen,
            origen_id=receta.origen_id,
            paciente_id=receta.paciente_id,
            paciente_nombre=receta.paciente_nombre,
            paciente_documento=receta.paciente_documento,
            diagnostico_principal=receta.diagnostico_principal,
            indicaciones_generales=receta.indicaciones_generales,
            fecha_vencimiento=receta.fecha_vencimiento,
            creado_por=receta.creado_por,
            medico_nombre=receta.medico_nombre,
            medico_colegiatura=receta.medico_colegiatura,
            estado=receta.estado,
            firmada=receta.firmada,
            fecha_firma=receta.fecha_firma,
            hash_firma=receta.hash_firma,
            created_at=receta.created_at,
            updated_at=receta.updated_at,
            detalles=detalles_response
        )
        
        return ApiResponse.success_response(
            data=receta_response,
            message=f"Receta {receta.numero_receta} creada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ApiResponse[RecetasListResponse])
async def obtener_recetas(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    paciente_id: Optional[int] = Query(None),
    tipo_origen: Optional[str] = Query(None),
    origen_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener recetas médicas con filtros"""
    
    try:
        # Si no se especifica filtro, obtener las del médico actual
        if not any([paciente_id, tipo_origen, origen_id]):
            recetas = await RecetaService.obtener_recetas_por_medico(
                db, current_user_id, page, size, estado, fecha_desde, fecha_hasta
            )
        elif tipo_origen and origen_id:
            recetas_list = await RecetaService.obtener_recetas_por_origen(db, tipo_origen, origen_id)
            # Aplicar paginación manual para consistencia
            start = (page - 1) * size
            end = start + size
            recetas = {
                "recetas": recetas_list[start:end],
                "total": len(recetas_list),
                "total_pages": (len(recetas_list) + size - 1) // size
            }
        elif paciente_id:
            recetas_list = await RecetaService.obtener_recetas_por_paciente(db, paciente_id)
            # Aplicar paginación manual
            start = (page - 1) * size
            end = start + size
            recetas = {
                "recetas": recetas_list[start:end],
                "total": len(recetas_list),
                "total_pages": (len(recetas_list) + size - 1) // size
            }
        else:
            recetas = {"recetas": [], "total": 0, "total_pages": 0}
        
        recetas_response = [
            RecetaCabResponse(
                id=receta.id,
                numero_receta=receta.numero_receta,
                tipo_origen=receta.tipo_origen,
                origen_id=receta.origen_id,
                paciente_id=receta.paciente_id,
                paciente_nombre=receta.paciente_nombre,
                paciente_documento=receta.paciente_documento,
                diagnostico_principal=receta.diagnostico_principal,
                indicaciones_generales=receta.indicaciones_generales,
                fecha_vencimiento=receta.fecha_vencimiento,
                creado_por=receta.creado_por,
                medico_nombre=receta.medico_nombre,
                medico_colegiatura=receta.medico_colegiatura,
                estado=receta.estado,
                firmada=receta.firmada,
                fecha_firma=receta.fecha_firma,
                hash_firma=receta.hash_firma,
                created_at=receta.created_at,
                updated_at=receta.updated_at,
                total_medicamentos=len(receta.detalles) if hasattr(receta, 'detalles') else 0
            )
            for receta in recetas["recetas"]
        ]
        
        list_response = RecetasListResponse(
            recetas=recetas_response,
            total=recetas["total"],
            page=page,
            size=size,
            total_pages=recetas["total_pages"]
        )
        
        return ApiResponse.success_response(
            data=list_response,
            message=f"Obtenidas {len(recetas_response)} recetas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{receta_id}", response_model=ApiResponse[RecetaCompletaResponse])
async def obtener_receta_por_id(
    receta_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """💊 Obtener receta completa por ID"""
    
    try:
        receta = await RecetaService.obtener_receta_por_id(db, receta_id)
        if not receta:
            raise HTTPException(status_code=404, detail="Receta no encontrada")
        
        # Convertir detalles
        detalles_response = []
        for detalle in receta.detalles:
            detalles_response.append({
                "id": detalle.id,
                "medicamento_id": detalle.medicamento_id,
                "medicamento_codigo": detalle.medicamento_codigo,
                "medicamento_nombre": detalle.medicamento_nombre,
                "cantidad": detalle.cantidad,
                "unidad": detalle.unidad,
                "posologia": detalle.posologia,
                "duracion_tratamiento": detalle.duracion_tratamiento,
                "observaciones": detalle.observaciones,
                "sustituible": detalle.sustituible
            })
        
        receta_response = RecetaCompletaResponse(
            id=receta.id,
            numero_receta=receta.numero_receta,
            tipo_origen=receta.tipo_origen,
            origen_id=receta.origen_id,
            paciente_id=receta.paciente_id,
            paciente_nombre=receta.paciente_nombre,
            paciente_documento=receta.paciente_documento,
            diagnostico_principal=receta.diagnostico_principal,
            indicaciones_generales=receta.indicaciones_generales,
            fecha_vencimiento=receta.fecha_vencimiento,
            creado_por=receta.creado_por,
            medico_nombre=receta.medico_nombre,
            medico_colegiatura=receta.medico_colegiatura,
            estado=receta.estado,
            firmada=receta.firmada,
            fecha_firma=receta.fecha_firma,
            hash_firma=receta.hash_firma,
            created_at=receta.created_at,
            updated_at=receta.updated_at,
            detalles=detalles_response
        )
        
        return ApiResponse.success_response(
            data=receta_response,
            message="Receta obtenida exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/numero/{numero_receta}", response_model=ApiResponse[RecetaCompletaResponse])
async def obtener_receta_por_numero(
    numero_receta: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Obtener receta por número de receta"""
    
    try:
        receta = await RecetaService.obtener_receta_por_numero(db, numero_receta)
        if not receta:
            raise HTTPException(status_code=404, detail="Receta no encontrada")
        
        # Convertir detalles
        detalles_response = []
        for detalle in receta.detalles:
            detalles_response.append({
                "id": detalle.id,
                "medicamento_id": detalle.medicamento_id,
                "medicamento_codigo": detalle.medicamento_codigo,
                "medicamento_nombre": detalle.medicamento_nombre,
                "cantidad": detalle.cantidad,
                "unidad": detalle.unidad,
                "posologia": detalle.posologia,
                "duracion_tratamiento": detalle.duracion_tratamiento,
                "observaciones": detalle.observaciones,
                "sustituible": detalle.sustituible
            })
        
        receta_response = RecetaCompletaResponse(
            id=receta.id,
            numero_receta=receta.numero_receta,
            tipo_origen=receta.tipo_origen,
            origen_id=receta.origen_id,
            paciente_id=receta.paciente_id,
            paciente_nombre=receta.paciente_nombre,
            paciente_documento=receta.paciente_documento,
            diagnostico_principal=receta.diagnostico_principal,
            indicaciones_generales=receta.indicaciones_generales,
            fecha_vencimiento=receta.fecha_vencimiento,
            creado_por=receta.creado_por,
            medico_nombre=receta.medico_nombre,
            medico_colegiatura=receta.medico_colegiatura,
            estado=receta.estado,
            firmada=receta.firmada,
            fecha_firma=receta.fecha_firma,
            hash_firma=receta.hash_firma,
            created_at=receta.created_at,
            updated_at=receta.updated_at,
            detalles=detalles_response
        )
        
        return ApiResponse.success_response(
            data=receta_response,
            message=f"Receta {numero_receta} obtenida"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{receta_id}", response_model=ApiResponse[RecetaCompletaResponse])
async def actualizar_receta(
    receta_id: int,
    receta_data: RecetaCabUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """✏️ Actualizar receta médica"""
    
    try:
        receta = await RecetaService.actualizar_receta(db, receta_id, receta_data, current_user_id)
        
        # Recargar con detalles
        receta_completa = await RecetaService.obtener_receta_por_id(db, receta.id)
        
        # Convertir detalles
        detalles_response = []
        for detalle in receta_completa.detalles:
            detalles_response.append({
                "id": detalle.id,
                "medicamento_id": detalle.medicamento_id,
                "medicamento_codigo": detalle.medicamento_codigo,
                "medicamento_nombre": detalle.medicamento_nombre,
                "cantidad": detalle.cantidad,
                "unidad": detalle.unidad,
                "posologia": detalle.posologia,
                "duracion_tratamiento": detalle.duracion_tratamiento,
                "observaciones": detalle.observaciones,
                "sustituible": detalle.sustituible
            })
        
        receta_response = RecetaCompletaResponse(
            id=receta_completa.id,
            numero_receta=receta_completa.numero_receta,
            tipo_origen=receta_completa.tipo_origen,
            origen_id=receta_completa.origen_id,
            paciente_id=receta_completa.paciente_id,
            paciente_nombre=receta_completa.paciente_nombre,
            paciente_documento=receta_completa.paciente_documento,
            diagnostico_principal=receta_completa.diagnostico_principal,
            indicaciones_generales=receta_completa.indicaciones_generales,
            fecha_vencimiento=receta_completa.fecha_vencimiento,
            creado_por=receta_completa.creado_por,
            medico_nombre=receta_completa.medico_nombre,
            medico_colegiatura=receta_completa.medico_colegiatura,
            estado=receta_completa.estado,
            firmada=receta_completa.firmada,
            fecha_firma=receta_completa.fecha_firma,
            hash_firma=receta_completa.hash_firma,
            created_at=receta_completa.created_at,
            updated_at=receta_completa.updated_at,
            detalles=detalles_response
        )
        
        return ApiResponse.success_response(
            data=receta_response,
            message="Receta actualizada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{receta_id}/estado", response_model=ApiResponse[RecetaCabResponse])
async def cambiar_estado_receta(
    receta_id: int,
    nuevo_estado: str = Query(..., regex="^(01|02|03|04)$"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔄 Cambiar estado de receta (01:Activa, 02:Despachada, 03:Vencida, 04:Anulada)"""
    
    try:
        receta = await RecetaService.cambiar_estado_receta(db, receta_id, nuevo_estado, current_user_id)
        
        receta_response = RecetaCabResponse(
            id=receta.id,
            numero_receta=receta.numero_receta,
            tipo_origen=receta.tipo_origen,
            origen_id=receta.origen_id,
            paciente_id=receta.paciente_id,
            paciente_nombre=receta.paciente_nombre,
            paciente_documento=receta.paciente_documento,
            diagnostico_principal=receta.diagnostico_principal,
            indicaciones_generales=receta.indicaciones_generales,
            fecha_vencimiento=receta.fecha_vencimiento,
            creado_por=receta.creado_por,
            medico_nombre=receta.medico_nombre,
            medico_colegiatura=receta.medico_colegiatura,
            estado=receta.estado,
            firmada=receta.firmada,
            fecha_firma=receta.fecha_firma,
            hash_firma=receta.hash_firma,
            created_at=receta.created_at,
            updated_at=receta.updated_at,
            total_medicamentos=0
        )
        
        estados_desc = {"01": "Activa", "02": "Despachada", "03": "Vencida", "04": "Anulada"}
        
        return ApiResponse.success_response(
            data=receta_response,
            message=f"Receta cambiada a estado: {estados_desc.get(nuevo_estado, nuevo_estado)}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/paciente/{paciente_id}/historial", response_model=ApiResponse[List[RecetaCabResponse]])
async def obtener_historial_recetas_paciente(
    paciente_id: int,
    limit: int = Query(50, ge=1, le=100),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """👤 Obtener historial de recetas de un paciente"""
    
    try:
        recetas = await RecetaService.obtener_recetas_por_paciente(db, paciente_id)
        
        # Limitar resultados
        recetas_limitadas = recetas[:limit] if len(recetas) > limit else recetas
        
        recetas_response = [
            RecetaCabResponse(
                id=receta.id,
                numero_receta=receta.numero_receta,
                tipo_origen=receta.tipo_origen,
                origen_id=receta.origen_id,
                paciente_id=receta.paciente_id,
                paciente_nombre=receta.paciente_nombre,
                paciente_documento=receta.paciente_documento,
                diagnostico_principal=receta.diagnostico_principal,
                indicaciones_generales=receta.indicaciones_generales,
                fecha_vencimiento=receta.fecha_vencimiento,
                creado_por=receta.creado_por,
                medico_nombre=receta.medico_nombre,
                medico_colegiatura=receta.medico_colegiatura,
                estado=receta.estado,
                firmada=receta.firmada,
                fecha_firma=receta.fecha_firma,
                hash_firma=receta.hash_firma,
                created_at=receta.created_at,
                updated_at=receta.updated_at,
                total_medicamentos=len(receta.detalles) if hasattr(receta, 'detalles') else 0
            )
            for receta in recetas_limitadas
        ]
        
        return ApiResponse.success_response(
            data=recetas_response,
            message=f"Historial de {len(recetas_response)} recetas del paciente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/origen/{tipo_origen}/{origen_id}", response_model=ApiResponse[List[RecetaCabResponse]])
async def obtener_recetas_por_origen(
    tipo_origen: str,
    origen_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener recetas por origen (consulta, hospitalización, etc.)"""
    
    try:
        recetas = await RecetaService.obtener_recetas_por_origen(db, tipo_origen, origen_id)
        
        recetas_response = [
            RecetaCabResponse(
                id=receta.id,
                numero_receta=receta.numero_receta,
                tipo_origen=receta.tipo_origen,
                origen_id=receta.origen_id,
                paciente_id=receta.paciente_id,
                paciente_nombre=receta.paciente_nombre,
                paciente_documento=receta.paciente_documento,
                diagnostico_principal=receta.diagnostico_principal,
                indicaciones_generales=receta.indicaciones_generales,
                fecha_vencimiento=receta.fecha_vencimiento,
                creado_por=receta.creado_por,
                medico_nombre=receta.medico_nombre,
                medico_colegiatura=receta.medico_colegiatura,
                estado=receta.estado,
                firmada=receta.firmada,
                fecha_firma=receta.fecha_firma,
                hash_firma=receta.hash_firma,
                created_at=receta.created_at,
                updated_at=receta.updated_at,
                total_medicamentos=len(receta.detalles) if hasattr(receta, 'detalles') else 0
            )
            for receta in recetas
        ]
        
        return ApiResponse.success_response(
            data=recetas_response,
            message=f"Obtenidas {len(recetas_response)} recetas para {tipo_origen}:{origen_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/medico", response_model=ApiResponse[dict])
async def obtener_estadisticas_medico(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📊 Obtener estadísticas de recetas del médico actual"""
    
    try:
        stats = await RecetaService.obtener_estadisticas_medico(db, current_user_id)
        
        return ApiResponse.success_response(
            data=stats,
            message="Estadísticas de recetas obtenidas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/medicamentos-mas-prescritos", response_model=ApiResponse[List[dict]])
async def obtener_medicamentos_mas_prescritos(
    limite: int = Query(10, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """💊 Obtener medicamentos más prescritos globalmente"""
    
    try:
        medicamentos = await RecetaService.obtener_medicamentos_mas_prescritos(db, limite)
        
        return ApiResponse.success_response(
            data=medicamentos,
            message=f"Top {len(medicamentos)} medicamentos más prescritos"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", response_model=ApiResponse[dict])
async def recetas_health():
    """💚 Health check del módulo de recetas"""
    
    health_data = {
        "status": "UP",
        "module": "Medical Prescriptions",
        "version": "1.0.0",
        "timestamp": datetime.now(),
        "features": [
            "Prescription Management",
            "Digital Signature Support",
            "Medical Validation Rules",
            "Prescription Status Control",
            "Patient Prescription History",
            "Prescription Statistics",
            "Auto-numbering System",
            "Expiration Control"
        ],
        "endpoints": [
            "POST /recetas/",
            "GET /recetas/",
            "GET /recetas/{id}",
            "GET /recetas/numero/{numero}",
            "PUT /recetas/{id}",
            "PUT /recetas/{id}/estado",
            "GET /recetas/paciente/{id}/historial",
            "GET /recetas/origen/{tipo}/{id}",
            "GET /recetas/stats/medico",
            "GET /recetas/stats/medicamentos-mas-prescritos"
        ],
        "business_rules": [
            "Máximo 10 medicamentos por receta",
            "Solo médicos pueden crear recetas",
            "Una receta activa por paciente por día",
            "Auto-firma para recetas simples (≤3 medicamentos)",
            "Validación de transiciones de estado",
            "Control de modificaciones por tiempo"
        ]
    }
    
    return ApiResponse.success_response(
        data=health_data,
        message="Módulo de recetas operativo"
    )