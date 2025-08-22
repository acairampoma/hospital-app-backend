from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.nota import (
    NotaCreate, NotaUpdate, NotaResponse, NotaCompletaResponse,
    NotasListResponse, NotaSearchResponse
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services.nota_service import NotaService
from app.core.security import get_current_user_id
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=ApiResponse[NotaResponse], status_code=status.HTTP_201_CREATED)
async def crear_nota(
    nota_data: NotaCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📝 Crear nueva nota médica"""
    
    try:
        nota = await NotaService.crear_nota(db, nota_data, current_user_id)
        
        nota_response = NotaResponse(
            id=nota.id,
            numero_nota=nota.numero_nota,
            tipo_nota=nota.tipo_nota,
            tipo_origen=nota.tipo_origen,
            origen_id=nota.origen_id,
            paciente_id=nota.paciente_id,
            paciente_nombre=nota.paciente_nombre,
            paciente_documento=nota.paciente_documento,
            titulo=nota.titulo,
            contenido_texto=nota.contenido_texto,
            estado=nota.estado,
            fecha_nota=nota.fecha_nota,
            creado_por=nota.creado_por,
            medico_nombre=nota.medico_nombre,
            medico_especialidad=nota.medico_especialidad,
            medico_colegiatura=nota.medico_colegiatura,
            confidencial=nota.confidencial,
            created_at=nota.created_at,
            updated_at=nota.updated_at,
            tiene_audio=bool(nota.audio_path),
            tiene_pdf=bool(nota.pdf_path)
        )
        
        return ApiResponse.success_response(
            data=nota_response,
            message=f"Nota médica {nota.numero_nota} creada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ApiResponse[NotasListResponse])
async def obtener_notas(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tipo_nota: Optional[str] = Query(None),
    tipo_origen: Optional[str] = Query(None),
    origen_id: Optional[int] = Query(None),
    paciente_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    confidencial: Optional[bool] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener notas médicas con filtros"""
    
    try:
        result = await NotaService.obtener_notas_paginado(
            db=db,
            page=page,
            size=size,
            medico_id=current_user_id,
            tipo_nota=tipo_nota,
            tipo_origen=tipo_origen,
            origen_id=origen_id,
            paciente_id=paciente_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            confidencial=confidencial
        )
        
        notas_response = [
            NotaResponse(
                id=nota.id,
                numero_nota=nota.numero_nota,
                tipo_nota=nota.tipo_nota,
                tipo_origen=nota.tipo_origen,
                origen_id=nota.origen_id,
                paciente_id=nota.paciente_id,
                paciente_nombre=nota.paciente_nombre,
                paciente_documento=nota.paciente_documento,
                titulo=nota.titulo,
                contenido_texto=nota.contenido_texto,
                estado=nota.estado,
                fecha_nota=nota.fecha_nota,
                creado_por=nota.creado_por,
                medico_nombre=nota.medico_nombre,
                medico_especialidad=nota.medico_especialidad,
                medico_colegiatura=nota.medico_colegiatura,
                confidencial=nota.confidencial,
                created_at=nota.created_at,
                updated_at=nota.updated_at,
                tiene_audio=bool(nota.audio_path),
                tiene_pdf=bool(nota.pdf_path)
            )
            for nota in result["notas"]
        ]
        
        list_response = NotasListResponse(
            notas=notas_response,
            total=result["total"],
            page=page,
            size=size,
            total_pages=result["total_pages"]
        )
        
        return ApiResponse.success_response(
            data=list_response,
            message=f"Obtenidas {len(notas_response)} notas médicas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{nota_id}", response_model=ApiResponse[NotaCompletaResponse])
async def obtener_nota_por_id(
    nota_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📝 Obtener nota médica completa por ID"""
    
    try:
        nota = await NotaService.obtener_nota_por_id(db, nota_id, current_user_id)
        if not nota:
            raise HTTPException(status_code=404, detail="Nota médica no encontrada")
        
        nota_response = NotaCompletaResponse(
            id=nota.id,
            numero_nota=nota.numero_nota,
            tipo_nota=nota.tipo_nota,
            tipo_origen=nota.tipo_origen,
            origen_id=nota.origen_id,
            paciente_id=nota.paciente_id,
            paciente_nombre=nota.paciente_nombre,
            paciente_documento=nota.paciente_documento,
            titulo=nota.titulo,
            contenido_texto=nota.contenido_texto,
            contenido_html=nota.contenido_html,
            metadata_adicional=nota.metadata_adicional,
            estado=nota.estado,
            fecha_nota=nota.fecha_nota,
            creado_por=nota.creado_por,
            medico_nombre=nota.medico_nombre,
            medico_especialidad=nota.medico_especialidad,
            medico_colegiatura=nota.medico_colegiatura,
            confidencial=nota.confidencial,
            audio_path=nota.audio_path,
            pdf_path=nota.pdf_path,
            created_at=nota.created_at,
            updated_at=nota.updated_at
        )
        
        return ApiResponse.success_response(
            data=nota_response,
            message="Nota médica obtenida exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/numero/{numero_nota}", response_model=ApiResponse[NotaCompletaResponse])
async def obtener_nota_por_numero(
    numero_nota: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Obtener nota médica por número"""
    
    try:
        nota = await NotaService.obtener_nota_por_numero(db, numero_nota, current_user_id)
        if not nota:
            raise HTTPException(status_code=404, detail="Nota médica no encontrada")
        
        nota_response = NotaCompletaResponse(
            id=nota.id,
            numero_nota=nota.numero_nota,
            tipo_nota=nota.tipo_nota,
            tipo_origen=nota.tipo_origen,
            origen_id=nota.origen_id,
            paciente_id=nota.paciente_id,
            paciente_nombre=nota.paciente_nombre,
            paciente_documento=nota.paciente_documento,
            titulo=nota.titulo,
            contenido_texto=nota.contenido_texto,
            contenido_html=nota.contenido_html,
            metadata_adicional=nota.metadata_adicional,
            estado=nota.estado,
            fecha_nota=nota.fecha_nota,
            creado_por=nota.creado_por,
            medico_nombre=nota.medico_nombre,
            medico_especialidad=nota.medico_especialidad,
            medico_colegiatura=nota.medico_colegiatura,
            confidencial=nota.confidencial,
            audio_path=nota.audio_path,
            pdf_path=nota.pdf_path,
            created_at=nota.created_at,
            updated_at=nota.updated_at
        )
        
        return ApiResponse.success_response(
            data=nota_response,
            message=f"Nota {numero_nota} obtenida exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{nota_id}", response_model=ApiResponse[NotaResponse])
async def actualizar_nota(
    nota_id: int,
    nota_data: NotaUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """✏️ Actualizar nota médica"""
    
    try:
        nota = await NotaService.actualizar_nota(db, nota_id, nota_data, current_user_id)
        
        nota_response = NotaResponse(
            id=nota.id,
            numero_nota=nota.numero_nota,
            tipo_nota=nota.tipo_nota,
            tipo_origen=nota.tipo_origen,
            origen_id=nota.origen_id,
            paciente_id=nota.paciente_id,
            paciente_nombre=nota.paciente_nombre,
            paciente_documento=nota.paciente_documento,
            titulo=nota.titulo,
            contenido_texto=nota.contenido_texto,
            estado=nota.estado,
            fecha_nota=nota.fecha_nota,
            creado_por=nota.creado_por,
            medico_nombre=nota.medico_nombre,
            medico_especialidad=nota.medico_especialidad,
            medico_colegiatura=nota.medico_colegiatura,
            confidencial=nota.confidencial,
            created_at=nota.created_at,
            updated_at=nota.updated_at,
            tiene_audio=bool(nota.audio_path),
            tiene_pdf=bool(nota.pdf_path)
        )
        
        return ApiResponse.success_response(
            data=nota_response,
            message="Nota médica actualizada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{nota_id}/estado", response_model=ApiResponse[NotaResponse])
async def cambiar_estado_nota(
    nota_id: int,
    nuevo_estado: str = Query(..., regex="^(01|02|03)$"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔄 Cambiar estado de nota (01:Borrador, 02:Finalizada, 03:Archivada)"""
    
    try:
        nota = await NotaService.cambiar_estado_nota(db, nota_id, nuevo_estado, current_user_id)
        
        nota_response = NotaResponse(
            id=nota.id,
            numero_nota=nota.numero_nota,
            tipo_nota=nota.tipo_nota,
            tipo_origen=nota.tipo_origen,
            origen_id=nota.origen_id,
            paciente_id=nota.paciente_id,
            paciente_nombre=nota.paciente_nombre,
            paciente_documento=nota.paciente_documento,
            titulo=nota.titulo,
            contenido_texto=nota.contenido_texto,
            estado=nota.estado,
            fecha_nota=nota.fecha_nota,
            creado_por=nota.creado_por,
            medico_nombre=nota.medico_nombre,
            medico_especialidad=nota.medico_especialidad,
            medico_colegiatura=nota.medico_colegiatura,
            confidencial=nota.confidencial,
            created_at=nota.created_at,
            updated_at=nota.updated_at,
            tiene_audio=bool(nota.audio_path),
            tiene_pdf=bool(nota.pdf_path)
        )
        
        estados_desc = {"01": "Borrador", "02": "Finalizada", "03": "Archivada"}
        
        return ApiResponse.success_response(
            data=nota_response,
            message=f"Nota cambiada a estado: {estados_desc.get(nuevo_estado, nuevo_estado)}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{nota_id}/audio", response_model=ApiResponse[MessageResponse])
async def subir_audio_nota(
    nota_id: int,
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🎤 Subir archivo de audio a nota médica"""
    
    try:
        # Validar tipo de archivo
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos de audio")
        
        # Validar tamaño (máximo 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo de audio no puede exceder 10MB")
        
        audio_path = await NotaService.guardar_audio_nota(db, nota_id, file, current_user_id)
        
        message_response = MessageResponse(
            message=f"Audio guardado exitosamente en: {audio_path}",
            success=True
        )
        
        return ApiResponse.success_response(
            data=message_response,
            message="Audio subido exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{nota_id}/pdf", response_model=ApiResponse[MessageResponse])
async def generar_pdf_nota(
    nota_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📄 Generar PDF de nota médica"""
    
    try:
        pdf_path = await NotaService.generar_pdf_nota(db, nota_id, current_user_id)
        
        message_response = MessageResponse(
            message=f"PDF generado exitosamente en: {pdf_path}",
            success=True
        )
        
        return ApiResponse.success_response(
            data=message_response,
            message="PDF generado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/paciente/{paciente_id}/historial", response_model=ApiResponse[List[NotaResponse]])
async def obtener_historial_notas_paciente(
    paciente_id: int,
    tipo_nota: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """👤 Obtener historial de notas médicas de un paciente"""
    
    try:
        notas = await NotaService.obtener_notas_por_paciente(db, paciente_id, tipo_nota, limit, current_user_id)
        
        notas_response = [
            NotaResponse(
                id=nota.id,
                numero_nota=nota.numero_nota,
                tipo_nota=nota.tipo_nota,
                tipo_origen=nota.tipo_origen,
                origen_id=nota.origen_id,
                paciente_id=nota.paciente_id,
                paciente_nombre=nota.paciente_nombre,
                paciente_documento=nota.paciente_documento,
                titulo=nota.titulo,
                contenido_texto=nota.contenido_texto,
                estado=nota.estado,
                fecha_nota=nota.fecha_nota,
                creado_por=nota.creado_por,
                medico_nombre=nota.medico_nombre,
                medico_especialidad=nota.medico_especialidad,
                medico_colegiatura=nota.medico_colegiatura,
                confidencial=nota.confidencial,
                created_at=nota.created_at,
                updated_at=nota.updated_at,
                tiene_audio=bool(nota.audio_path),
                tiene_pdf=bool(nota.pdf_path)
            )
            for nota in notas
        ]
        
        return ApiResponse.success_response(
            data=notas_response,
            message=f"Historial de {len(notas_response)} notas del paciente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/origen/{tipo_origen}/{origen_id}", response_model=ApiResponse[List[NotaResponse]])
async def obtener_notas_por_origen(
    tipo_origen: str,
    origen_id: int,
    tipo_nota: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏥 Obtener notas por origen (consulta, hospitalización, etc.)"""
    
    try:
        notas = await NotaService.obtener_notas_por_origen(db, tipo_origen, origen_id, tipo_nota, current_user_id)
        
        notas_response = [
            NotaResponse(
                id=nota.id,
                numero_nota=nota.numero_nota,
                tipo_nota=nota.tipo_nota,
                tipo_origen=nota.tipo_origen,
                origen_id=nota.origen_id,
                paciente_id=nota.paciente_id,
                paciente_nombre=nota.paciente_nombre,
                paciente_documento=nota.paciente_documento,
                titulo=nota.titulo,
                contenido_texto=nota.contenido_texto,
                estado=nota.estado,
                fecha_nota=nota.fecha_nota,
                creado_por=nota.creado_por,
                medico_nombre=nota.medico_nombre,
                medico_especialidad=nota.medico_especialidad,
                medico_colegiatura=nota.medico_colegiatura,
                confidencial=nota.confidencial,
                created_at=nota.created_at,
                updated_at=nota.updated_at,
                tiene_audio=bool(nota.audio_path),
                tiene_pdf=bool(nota.pdf_path)
            )
            for nota in notas
        ]
        
        return ApiResponse.success_response(
            data=notas_response,
            message=f"Obtenidas {len(notas_response)} notas para {tipo_origen}:{origen_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search/texto", response_model=ApiResponse[List[NotaSearchResponse]])
async def buscar_notas_por_texto(
    q: str = Query(..., min_length=3),
    tipo_nota: Optional[str] = Query(None),
    paciente_id: Optional[int] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Buscar notas médicas por contenido de texto"""
    
    try:
        notas = await NotaService.buscar_notas_por_texto(
            db, q, current_user_id, tipo_nota, paciente_id, fecha_desde, fecha_hasta, limit
        )
        
        search_response = [
            NotaSearchResponse(
                id=nota.id,
                numero_nota=nota.numero_nota,
                tipo_nota=nota.tipo_nota,
                titulo=nota.titulo,
                contenido_texto=nota.contenido_texto[:200] + "..." if len(nota.contenido_texto) > 200 else nota.contenido_texto,
                paciente_nombre=nota.paciente_nombre,
                fecha_nota=nota.fecha_nota,
                estado=nota.estado
            )
            for nota in notas
        ]
        
        return ApiResponse.success_response(
            data=search_response,
            message=f"Encontradas {len(search_response)} notas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tipos/list", response_model=ApiResponse[List[dict]])
async def obtener_tipos_nota(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener tipos de nota médica disponibles"""
    
    try:
        tipos = await NotaService.obtener_tipos_nota_disponibles(db)
        
        return ApiResponse.success_response(
            data=tipos,
            message=f"Obtenidos {len(tipos)} tipos de nota"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/resumen", response_model=ApiResponse[dict])
async def obtener_estadisticas_notas(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📊 Obtener estadísticas de notas del médico actual"""
    
    try:
        stats = await NotaService.obtener_estadisticas_medico(db, current_user_id)
        
        return ApiResponse.success_response(
            data=stats,
            message="Estadísticas de notas obtenidas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", response_model=ApiResponse[dict])
async def notas_health():
    """💚 Health check del módulo de notas médicas"""
    
    health_data = {
        "status": "UP",
        "module": "Medical Notes",
        "version": "1.0.0",
        "timestamp": datetime.now(),
        "features": [
            "Medical Notes Management",
            "Audio Recording Support",
            "PDF Generation",
            "Text Search",
            "Patient History",
            "Confidentiality Control",
            "Multiple Note Types",
            "State Management",
            "Rich Content Support"
        ],
        "endpoints": [
            "POST /notas/",
            "GET /notas/",
            "GET /notas/{id}",
            "GET /notas/numero/{numero}",
            "PUT /notas/{id}",
            "PUT /notas/{id}/estado",
            "POST /notas/{id}/audio",
            "POST /notas/{id}/pdf",
            "GET /notas/paciente/{id}/historial",
            "GET /notas/origen/{tipo}/{id}",
            "GET /notas/search/texto",
            "GET /notas/tipos/list",
            "GET /notas/stats/resumen"
        ],
        "note_types": [
            "EVOLUCION",
            "ANAMNESIS",
            "EXAMEN_FISICO", 
            "DIAGNOSTICO",
            "PLAN_TRATAMIENTO",
            "INTERCONSULTA",
            "EPICRISIS",
            "PROCEDIMIENTO"
        ],
        "states": [
            "01: Borrador",
            "02: Finalizada", 
            "03: Archivada"
        ]
    }
    
    return ApiResponse.success_response(
        data=health_data,
        message="Módulo de notas médicas operativo"
    )