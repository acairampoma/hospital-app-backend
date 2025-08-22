from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# 💊 RECETA DETALLE SCHEMAS

class RecetaDetBase(BaseModel):
    """Base schema para detalle de receta"""
    medicamento_codigo: str
    medicamento_nombre: str
    cantidad: int
    unidad: str = "UNIDAD"
    posologia: Optional[str] = None
    duracion_tratamiento: Optional[str] = None
    
    @validator('cantidad')
    def validate_cantidad(cls, v):
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        if v > 2:  # Regla de negocio del monorepo
            raise ValueError('La cantidad máxima es 2 unidades por medicamento')
        return v

class RecetaDetCreate(RecetaDetBase):
    """Create detalle receta"""
    medicamento_id: Optional[int] = None
    observaciones: Optional[str] = None
    sustituible: bool = True

class RecetaDetUpdate(BaseModel):
    """Update detalle receta"""
    cantidad: Optional[int] = None
    posologia: Optional[str] = None
    duracion_tratamiento: Optional[str] = None
    observaciones: Optional[str] = None
    
    @validator('cantidad')
    def validate_cantidad(cls, v):
        if v is not None and v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        if v is not None and v > 2:
            raise ValueError('La cantidad máxima es 2 unidades por medicamento')
        return v

class RecetaDetResponse(RecetaDetBase):
    """Response detalle receta"""
    id: int
    medicamento_id: Optional[int] = None
    observaciones: Optional[str] = None
    sustituible: bool = True
    cantidad_despachada: int = 0
    despachado: bool = False
    fecha_despacho: Optional[datetime] = None
    created_at: datetime
    
    # Propiedades calculadas
    prescripcion_completa: str = ""
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        desc = f"{self.medicamento_nombre} - {self.cantidad} {self.unidad}"
        if self.posologia:
            desc += f" - {self.posologia}"
        self.prescripcion_completa = desc

# 💊 RECETA CABECERA SCHEMAS

class RecetaCabBase(BaseModel):
    """Base schema para cabecera de receta"""
    tipo_origen: str  # HOS, CON, EME
    origen_id: int
    diagnostico_principal: Optional[str] = None
    indicaciones_generales: Optional[str] = None
    
    @validator('tipo_origen')
    def validate_tipo_origen(cls, v):
        if v not in ['HOS', 'CON', 'EME']:
            raise ValueError('Tipo origen debe ser HOS, CON o EME')
        return v

class RecetaCabCreate(RecetaCabBase):
    """Create receta cabecera"""
    paciente_id: int
    paciente_nombre: str
    paciente_documento: str
    fecha_vencimiento: Optional[datetime] = None
    detalles: List[RecetaDetCreate] = []
    
    @validator('detalles')
    def validate_detalles(cls, v):
        if not v or len(v) == 0:
            raise ValueError('La receta debe tener al menos un medicamento')
        if len(v) > 10:  # Regla de negocio del monorepo
            raise ValueError('Máximo 10 medicamentos por receta')
        return v

class RecetaCabUpdate(BaseModel):
    """Update receta cabecera"""
    diagnostico_principal: Optional[str] = None
    indicaciones_generales: Optional[str] = None
    fecha_vencimiento: Optional[datetime] = None

class RecetaCabResponse(RecetaCabBase):
    """Response cabecera receta"""
    id: int
    numero_receta: str
    paciente_id: int
    paciente_nombre: str
    paciente_documento: str
    estado: str = "01"  # 01=Activa, 02=Despachada, 03=Vencida, 04=Anulada
    fecha_vencimiento: Optional[datetime] = None
    
    # Información del médico
    creado_por: int
    medico_nombre: Optional[str] = None
    medico_colegiatura: Optional[str] = None
    
    # Firma digital
    firmada: bool = False
    fecha_firma: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Propiedades calculadas
    estado_descripcion: str = ""
    puede_editarse: bool = True
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        estados = {
            "01": "Activa",
            "02": "Despachada",
            "03": "Vencida", 
            "04": "Anulada"
        }
        self.estado_descripcion = estados.get(self.estado, "Desconocido")
        self.puede_editarse = self.estado == "01" and not self.firmada

# 💊 RECETA COMPLETA SCHEMAS

class RecetaCompletaResponse(RecetaCabResponse):
    """Response receta completa con detalles"""
    detalles: List[RecetaDetResponse] = []
    total_medicamentos: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_medicamentos = len(self.detalles)

# 💊 REQUESTS ESPECÍFICOS

class CambiarEstadoRecetaRequest(BaseModel):
    """Request para cambiar estado de receta"""
    nuevo_estado: str
    medico_id: int
    observaciones: Optional[str] = None
    
    @validator('nuevo_estado')
    def validate_estado(cls, v):
        if v not in ['01', '02', '03', '04']:
            raise ValueError('Estado debe ser 01, 02, 03 o 04')
        return v

class BuscarRecetasRequest(BaseModel):
    """Request para búsqueda de recetas"""
    tipo_origen: Optional[str] = None
    origen_id: Optional[int] = None
    paciente_id: Optional[int] = None
    medico_id: Optional[int] = None
    estado: Optional[str] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None

# 📊 ESTADÍSTICAS SCHEMAS

class EstadisticasMedicoResponse(BaseModel):
    """Estadísticas de recetas por médico"""
    medico_id: int
    medico_nombre: str
    total_recetas: int
    recetas_activas: int
    recetas_despachadas: int
    medicamentos_mas_prescritos: List[dict] = []
    periodo_analizado: str = ""

class MedicamentoMasPrescrito(BaseModel):
    """Medicamento más prescrito"""
    medicamento_nombre: str
    total_prescripciones: int
    porcentaje: float

class EstadisticasGeneralesResponse(BaseModel):
    """Estadísticas generales de recetas"""
    total_recetas: int
    recetas_por_estado: dict = {}
    medicamentos_mas_prescritos: List[MedicamentoMasPrescrito] = []
    promedio_medicamentos_por_receta: float = 0.0

class RecetasListResponse(BaseModel):
    """Response para lista paginada de recetas"""
    recetas: List[RecetaCabResponse]
    total: int
    page: int
    size: int
    total_pages: int

class RecetaSearchResponse(BaseModel):
    """Response para búsqueda de recetas"""
    id: int
    numero_receta: str
    paciente_nombre: str
    paciente_documento: str
    estado: str
    estado_descripcion: str
    diagnostico_principal: Optional[str] = None
    total_medicamentos: int = 0
    medico_nombre: Optional[str] = None
    created_at: datetime