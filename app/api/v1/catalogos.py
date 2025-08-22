from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.catalogos import (
    CatalogoResponse, CatalogoCreate, CatalogoUpdate,
    MedicamentoVademecumResponse, MedicamentoCreate, MedicamentoUpdate,
    CatalogosListResponse, MedicamentosListResponse,
    CatalogoSearchResponse, MedicamentoSearchResponse
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services.catalogo_service import CatalogoService
from app.services.medicamento_service import MedicamentoService
from app.core.security import get_current_user_id
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# ===== ENDPOINTS DE CATÁLOGOS =====

@router.get("/tipos", response_model=ApiResponse[List[dict]])
async def obtener_tipos_catalogo(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener tipos de catálogo disponibles"""
    
    try:
        tipos = await CatalogoService.obtener_tipos_catalogo(db)
        
        return ApiResponse.success_response(
            data=tipos,
            message=f"Obtenidos {len(tipos)} tipos de catálogo"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tipo_catalogo}", response_model=ApiResponse[CatalogosListResponse])
async def obtener_catalogo_por_tipo(
    tipo_catalogo: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener catálogo por tipo con paginación"""
    
    try:
        result = await CatalogoService.obtener_catalogo_paginado(
            db=db,
            tipo_catalogo=tipo_catalogo,
            page=page,
            size=size,
            search=search,
            enabled=enabled
        )
        
        catalogos_response = [
            CatalogoResponse(
                id=catalogo.id,
                tipo_catalogo=catalogo.tipo_catalogo,
                codigo=catalogo.codigo,
                descripcion=catalogo.descripcion,
                descripcion_corta=catalogo.descripcion_corta,
                valor1=catalogo.valor1,
                valor2=catalogo.valor2,
                valor3=catalogo.valor3,
                orden=catalogo.orden,
                enabled=catalogo.enabled,
                created_at=catalogo.created_at,
                updated_at=catalogo.updated_at
            )
            for catalogo in result["catalogos"]
        ]
        
        list_response = CatalogosListResponse(
            catalogos=catalogos_response,
            total=result["total"],
            page=page,
            size=size,
            total_pages=result["total_pages"],
            tipo_catalogo=tipo_catalogo
        )
        
        return ApiResponse.success_response(
            data=list_response,
            message=f"Obtenidos {len(catalogos_response)} elementos del catálogo {tipo_catalogo}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tipo_catalogo}/{catalogo_id}", response_model=ApiResponse[CatalogoResponse])
async def obtener_catalogo_por_id(
    tipo_catalogo: str,
    catalogo_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """📋 Obtener elemento de catálogo por ID"""
    
    try:
        catalogo = await CatalogoService.obtener_catalogo_por_id(db, catalogo_id, tipo_catalogo)
        
        catalogo_response = CatalogoResponse(
            id=catalogo.id,
            tipo_catalogo=catalogo.tipo_catalogo,
            codigo=catalogo.codigo,
            descripcion=catalogo.descripcion,
            descripcion_corta=catalogo.descripcion_corta,
            valor1=catalogo.valor1,
            valor2=catalogo.valor2,
            valor3=catalogo.valor3,
            orden=catalogo.orden,
            enabled=catalogo.enabled,
            created_at=catalogo.created_at,
            updated_at=catalogo.updated_at
        )
        
        return ApiResponse.success_response(
            data=catalogo_response,
            message="Elemento de catálogo obtenido"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{tipo_catalogo}", response_model=ApiResponse[CatalogoResponse], status_code=status.HTTP_201_CREATED)
async def crear_catalogo(
    tipo_catalogo: str,
    catalogo_data: CatalogoCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """➕ Crear nuevo elemento de catálogo"""
    
    try:
        catalogo = await CatalogoService.crear_catalogo(db, tipo_catalogo, catalogo_data, current_user_id)
        
        catalogo_response = CatalogoResponse(
            id=catalogo.id,
            tipo_catalogo=catalogo.tipo_catalogo,
            codigo=catalogo.codigo,
            descripcion=catalogo.descripcion,
            descripcion_corta=catalogo.descripcion_corta,
            valor1=catalogo.valor1,
            valor2=catalogo.valor2,
            valor3=catalogo.valor3,
            orden=catalogo.orden,
            enabled=catalogo.enabled,
            created_at=catalogo.created_at,
            updated_at=catalogo.updated_at
        )
        
        return ApiResponse.success_response(
            data=catalogo_response,
            message="Elemento de catálogo creado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{tipo_catalogo}/{catalogo_id}", response_model=ApiResponse[CatalogoResponse])
async def actualizar_catalogo(
    tipo_catalogo: str,
    catalogo_id: int,
    catalogo_data: CatalogoUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """✏️ Actualizar elemento de catálogo"""
    
    try:
        catalogo = await CatalogoService.actualizar_catalogo(db, catalogo_id, catalogo_data, current_user_id)
        
        catalogo_response = CatalogoResponse(
            id=catalogo.id,
            tipo_catalogo=catalogo.tipo_catalogo,
            codigo=catalogo.codigo,
            descripcion=catalogo.descripcion,
            descripcion_corta=catalogo.descripcion_corta,
            valor1=catalogo.valor1,
            valor2=catalogo.valor2,
            valor3=catalogo.valor3,
            orden=catalogo.orden,
            enabled=catalogo.enabled,
            created_at=catalogo.created_at,
            updated_at=catalogo.updated_at
        )
        
        return ApiResponse.success_response(
            data=catalogo_response,
            message="Elemento de catálogo actualizado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{tipo_catalogo}/{catalogo_id}", response_model=ApiResponse[MessageResponse])
async def eliminar_catalogo(
    tipo_catalogo: str,
    catalogo_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🗑️ Eliminar elemento de catálogo"""
    
    try:
        success = await CatalogoService.eliminar_catalogo(db, catalogo_id, current_user_id)
        
        if success:
            message_response = MessageResponse(
                message="Elemento de catálogo eliminado exitosamente",
                success=True
            )
            
            return ApiResponse.success_response(
                data=message_response,
                message="Elemento eliminado"
            )
        else:
            raise HTTPException(status_code=400, detail="Error eliminando elemento")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search/{tipo_catalogo}", response_model=ApiResponse[List[CatalogoSearchResponse]])
async def buscar_en_catalogo(
    tipo_catalogo: str,
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Buscar en catálogo por descripción o código"""
    
    try:
        catalogos = await CatalogoService.buscar_en_catalogo(db, tipo_catalogo, q, limit)
        
        search_response = [
            CatalogoSearchResponse(
                id=catalogo.id,
                codigo=catalogo.codigo,
                descripcion=catalogo.descripcion,
                descripcion_corta=catalogo.descripcion_corta
            )
            for catalogo in catalogos
        ]
        
        return ApiResponse.success_response(
            data=search_response,
            message=f"Encontrados {len(search_response)} elementos"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===== ENDPOINTS DE MEDICAMENTOS VADEMÉCUM =====

@router.get("/medicamentos/", response_model=ApiResponse[MedicamentosListResponse])
async def obtener_medicamentos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    forma_farmaceutica: Optional[str] = Query(None),
    activo: Optional[bool] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """💊 Obtener medicamentos del vademécum con filtros"""
    
    try:
        result = await MedicamentoService.obtener_medicamentos_paginado(
            db=db,
            page=page,
            size=size,
            search=search,
            categoria=categoria,
            forma_farmaceutica=forma_farmaceutica,
            activo=activo
        )
        
        medicamentos_response = [
            MedicamentoVademecumResponse(
                id=med.id,
                codigo=med.codigo,
                nombre_comercial=med.nombre_comercial,
                nombre_generico=med.nombre_generico,
                principio_activo=med.principio_activo,
                concentracion=med.concentracion,
                forma_farmaceutica=med.forma_farmaceutica,
                presentacion=med.presentacion,
                laboratorio=med.laboratorio,
                codigo_atc=med.codigo_atc,
                categoria_terapeutica=med.categoria_terapeutica,
                requiere_receta=med.requiere_receta,
                precio_referencial=med.precio_referencial,
                observaciones=med.observaciones,
                activo=med.activo,
                created_at=med.created_at,
                updated_at=med.updated_at
            )
            for med in result["medicamentos"]
        ]
        
        list_response = MedicamentosListResponse(
            medicamentos=medicamentos_response,
            total=result["total"],
            page=page,
            size=size,
            total_pages=result["total_pages"]
        )
        
        return ApiResponse.success_response(
            data=list_response,
            message=f"Obtenidos {len(medicamentos_response)} medicamentos"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/medicamentos/{medicamento_id}", response_model=ApiResponse[MedicamentoVademecumResponse])
async def obtener_medicamento_por_id(
    medicamento_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """💊 Obtener medicamento por ID"""
    
    try:
        medicamento = await MedicamentoService.obtener_medicamento_por_id(db, medicamento_id)
        
        medicamento_response = MedicamentoVademecumResponse(
            id=medicamento.id,
            codigo=medicamento.codigo,
            nombre_comercial=medicamento.nombre_comercial,
            nombre_generico=medicamento.nombre_generico,
            principio_activo=medicamento.principio_activo,
            concentracion=medicamento.concentracion,
            forma_farmaceutica=medicamento.forma_farmaceutica,
            presentacion=medicamento.presentacion,
            laboratorio=medicamento.laboratorio,
            codigo_atc=medicamento.codigo_atc,
            categoria_terapeutica=medicamento.categoria_terapeutica,
            requiere_receta=medicamento.requiere_receta,
            precio_referencial=medicamento.precio_referencial,
            observaciones=medicamento.observaciones,
            activo=medicamento.activo,
            created_at=medicamento.created_at,
            updated_at=medicamento.updated_at
        )
        
        return ApiResponse.success_response(
            data=medicamento_response,
            message="Medicamento obtenido exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/medicamentos/", response_model=ApiResponse[MedicamentoVademecumResponse], status_code=status.HTTP_201_CREATED)
async def crear_medicamento(
    medicamento_data: MedicamentoCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """➕ Crear nuevo medicamento en vademécum"""
    
    try:
        medicamento = await MedicamentoService.crear_medicamento(db, medicamento_data, current_user_id)
        
        medicamento_response = MedicamentoVademecumResponse(
            id=medicamento.id,
            codigo=medicamento.codigo,
            nombre_comercial=medicamento.nombre_comercial,
            nombre_generico=medicamento.nombre_generico,
            principio_activo=medicamento.principio_activo,
            concentracion=medicamento.concentracion,
            forma_farmaceutica=medicamento.forma_farmaceutica,
            presentacion=medicamento.presentacion,
            laboratorio=medicamento.laboratorio,
            codigo_atc=medicamento.codigo_atc,
            categoria_terapeutica=medicamento.categoria_terapeutica,
            requiere_receta=medicamento.requiere_receta,
            precio_referencial=medicamento.precio_referencial,
            observaciones=medicamento.observaciones,
            activo=medicamento.activo,
            created_at=medicamento.created_at,
            updated_at=medicamento.updated_at
        )
        
        return ApiResponse.success_response(
            data=medicamento_response,
            message="Medicamento creado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/medicamentos/{medicamento_id}", response_model=ApiResponse[MedicamentoVademecumResponse])
async def actualizar_medicamento(
    medicamento_id: int,
    medicamento_data: MedicamentoUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """✏️ Actualizar medicamento del vademécum"""
    
    try:
        medicamento = await MedicamentoService.actualizar_medicamento(db, medicamento_id, medicamento_data, current_user_id)
        
        medicamento_response = MedicamentoVademecumResponse(
            id=medicamento.id,
            codigo=medicamento.codigo,
            nombre_comercial=medicamento.nombre_comercial,
            nombre_generico=medicamento.nombre_generico,
            principio_activo=medicamento.principio_activo,
            concentracion=medicamento.concentracion,
            forma_farmaceutica=medicamento.forma_farmaceutica,
            presentacion=medicamento.presentacion,
            laboratorio=medicamento.laboratorio,
            codigo_atc=medicamento.codigo_atc,
            categoria_terapeutica=medicamento.categoria_terapeutica,
            requiere_receta=medicamento.requiere_receta,
            precio_referencial=medicamento.precio_referencial,
            observaciones=medicamento.observaciones,
            activo=medicamento.activo,
            created_at=medicamento.created_at,
            updated_at=medicamento.updated_at
        )
        
        return ApiResponse.success_response(
            data=medicamento_response,
            message="Medicamento actualizado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/medicamentos/search/query", response_model=ApiResponse[List[MedicamentoSearchResponse]])
async def buscar_medicamentos(
    q: str = Query(..., min_length=2),
    categoria: Optional[str] = Query(None),
    forma_farmaceutica: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🔍 Buscar medicamentos por nombre, principio activo o código"""
    
    try:
        medicamentos = await MedicamentoService.buscar_medicamentos(
            db, q, categoria, forma_farmaceutica, limit
        )
        
        search_response = [
            MedicamentoSearchResponse(
                id=med.id,
                codigo=med.codigo,
                nombre_comercial=med.nombre_comercial,
                nombre_generico=med.nombre_generico,
                principio_activo=med.principio_activo,
                concentracion=med.concentracion,
                forma_farmaceutica=med.forma_farmaceutica,
                presentacion=med.presentacion,
                laboratorio=med.laboratorio,
                precio_referencial=med.precio_referencial
            )
            for med in medicamentos
        ]
        
        return ApiResponse.success_response(
            data=search_response,
            message=f"Encontrados {len(search_response)} medicamentos"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/medicamentos/categorias/list", response_model=ApiResponse[List[dict]])
async def obtener_categorias_medicamentos(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """🏷️ Obtener categorías terapéuticas de medicamentos"""
    
    try:
        categorias = await MedicamentoService.obtener_categorias_terapeuticas(db)
        
        return ApiResponse.success_response(
            data=categorias,
            message=f"Obtenidas {len(categorias)} categorías"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/medicamentos/formas/list", response_model=ApiResponse[List[dict]])
async def obtener_formas_farmaceuticas(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """💊 Obtener formas farmacéuticas disponibles"""
    
    try:
        formas = await MedicamentoService.obtener_formas_farmaceuticas(db)
        
        return ApiResponse.success_response(
            data=formas,
            message=f"Obtenidas {len(formas)} formas farmacéuticas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", response_model=ApiResponse[dict])
async def catalogos_health():
    """💚 Health check del módulo de catálogos"""
    
    health_data = {
        "status": "UP",
        "module": "Catalogs & Medications",
        "version": "1.0.0",
        "timestamp": datetime.now(),
        "features": [
            "Medical Catalogs Management",
            "Medication Vademecum",
            "Therapeutic Categories",
            "Pharmaceutical Forms",
            "Advanced Search",
            "Catalog Types Management"
        ],
        "endpoints": [
            "GET /catalogos/tipos",
            "GET /catalogos/{tipo_catalogo}",
            "POST /catalogos/{tipo_catalogo}",
            "PUT /catalogos/{tipo_catalogo}/{id}",
            "DELETE /catalogos/{tipo_catalogo}/{id}",
            "GET /catalogos/search/{tipo_catalogo}",
            "GET /catalogos/medicamentos/",
            "POST /catalogos/medicamentos/",
            "PUT /catalogos/medicamentos/{id}",
            "GET /catalogos/medicamentos/search/query",
            "GET /catalogos/medicamentos/categorias/list",
            "GET /catalogos/medicamentos/formas/list"
        ]
    }
    
    return ApiResponse.success_response(
        data=health_data,
        message="Módulo de catálogos operativo"
    )