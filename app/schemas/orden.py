from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class TipoOrden(str, Enum):
    """Tipos de orden médica"""
    LABORATORIO = "01"
    IMAGENOLOGIA = "02"
    PROCEDIMIENTO = "03"
    INTERCONSULTA = "04"

class EstadoOrden(str, Enum):
    """Estados de la orden"""
    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"

class PrioridadOrden(str, Enum):
    """Prioridades de orden"""
    URGENTE = "URGENTE"
    NORMAL = "NORMAL"
    BAJA = "BAJA"

class EstadoExamen(str, Enum):
    """Estados del examen"""
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"

# 📋 ORDEN DETALLE (EXÁMENES) SCHEMAS

class OrdenDetBase(BaseModel):
    """Base schema para detalle de orden"""
    examen_codigo: str
    examen_nombre: str
    examen_categoria: Optional[str] = None
    especificaciones: Optional[str] = None
    preparacion_requerida: Optional[str] = None

class OrdenDetCreate(OrdenDetBase):
    """Create examen schema"""
    examen_id: Optional[int] = None

class OrdenDetUpdate(BaseModel):
    """Update examen schema"""
    especificaciones: Optional[str] = None
    resultado: Optional[str] = None
    valor_numerico: Optional[Decimal] = None
    unidad_medida: Optional[str] = None
    valor_referencia: Optional[str] = None
    interpretacion: Optional[str] = None
    estado: Optional[EstadoExamen] = None

class OrdenDetResponse(OrdenDetBase):
    """Response examen"""
    id: int
    orden_id: int
    examen_id: Optional[int] = None
    estado: EstadoExamen = EstadoExamen.PENDIENTE
    
    # Resultados
    resultado: Optional[str] = None
    valor_numerico: Optional[Decimal] = None
    unidad_medida: Optional[str] = None
    valor_referencia: Optional[str] = None
    interpretacion: Optional[str] = None
    
    # Procesamiento
    fecha_toma_muestra: Optional[datetime] = None
    fecha_resultado: Optional[datetime] = None
    profesional_responsable: Optional[str] = None
    
    # Archivos
    archivo_resultado: Optional[str] = None
    tipo_archivo: Optional[str] = None
    
    # Control de calidad
    validado: bool = False
    fecha_validacion: Optional[datetime] = None
    validado_por: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Propiedades calculadas
    tiene_resultado: bool = False
    resultado_completo: str = "Sin resultado"
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # Calcular si tiene resultado
        self.tiene_resultado = bool(self.resultado or self.valor_numerico)
        
        # Formatear resultado completo
        if self.valor_numerico is not None:
            resultado = f"{self.valor_numerico}"
            if self.unidad_medida:
                resultado += f" {self.unidad_medida}"
            if self.valor_referencia:
                resultado += f" (Ref: {self.valor_referencia})"
            self.resultado_completo = resultado
        elif self.resultado:
            self.resultado_completo = self.resultado

# 📋 ORDEN CABECERA SCHEMAS

class OrdenCabBase(BaseModel):
    """Base schema para orden cabecera"""
    hospitalizacion_id: int
    numero_cuenta: Optional[str] = None
    tipo_orden: TipoOrden
    diagnostico: Optional[str] = None
    indicaciones_clinicas: Optional[str] = None
    observaciones: Optional[str] = None
    prioridad: PrioridadOrden = PrioridadOrden.NORMAL

class OrdenCabCreate(OrdenCabBase):
    """Create orden cabecera"""
    paciente_id: int
    paciente_nombre: str
    paciente_documento: str
    paciente_edad: Optional[int] = None
    paciente_genero: Optional[str] = None  # M/F
    paciente_cama: Optional[str] = None
    paciente_sala: Optional[str] = None
    medico_nombre: Optional[str] = None
    fecha_solicitada: Optional[datetime] = None
    servicio_destino: Optional[str] = None
    examenes: List[OrdenDetCreate] = []
    
    @validator('examenes')
    def validate_examenes(cls, v):
        if not v or len(v) == 0:
            raise ValueError('La orden debe tener al menos un examen')
        return v

class OrdenCabUpdate(BaseModel):
    """Update orden cabecera"""
    diagnostico: Optional[str] = None
    indicaciones_clinicas: Optional[str] = None
    observaciones: Optional[str] = None
    prioridad: Optional[PrioridadOrden] = None
    estado: Optional[EstadoOrden] = None
    fecha_programada: Optional[datetime] = None
    servicio_destino: Optional[str] = None

class OrdenCabResponse(OrdenCabBase):
    """Response orden cabecera"""
    id: int
    numero_orden: str
    paciente_id: int
    paciente_nombre: str
    paciente_documento: str
    estado: EstadoOrden = EstadoOrden.PENDIENTE
    
    # Información del médico
    creado_por: int
    medico_nombre: Optional[str] = None
    medico_especialidad: Optional[str] = None
    medico_colegiatura: Optional[str] = None
    
    # Fechas
    fecha_solicitada: Optional[datetime] = None
    fecha_programada: Optional[datetime] = None
    fecha_completada: Optional[datetime] = None
    
    # Servicio ejecutor
    servicio_destino: Optional[str] = None
    profesional_ejecutor: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Propiedades calculadas
    tipo_orden_descripcion: str = ""
    puede_editarse: bool = True
    total_examenes: int = 0
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # Calcular propiedades
        tipos = {
            "01": "Laboratorio",
            "02": "Imagenología",
            "03": "Procedimiento", 
            "04": "Interconsulta"
        }
        self.tipo_orden_descripcion = tipos.get(self.tipo_orden, "Desconocido")
        self.puede_editarse = self.estado in [EstadoOrden.PENDIENTE, EstadoOrden.PROCESANDO]

class OrdenCompletaResponse(OrdenCabResponse):
    """Response orden completa con examenes"""
    examenes: List[OrdenDetResponse] = []
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_examenes = len(self.examenes)

# 📋 REQUESTS ESPECÍFICOS

class CambiarEstadoOrdenRequest(BaseModel):
    """Request para cambiar estado de orden"""
    nuevo_estado: EstadoOrden
    medico_id: int
    observaciones: Optional[str] = None

class ValidarCreacionOrdenRequest(BaseModel):
    """Request para validar creación de orden"""
    medico_id: int
    hospitalizacion_id: int

class ValidarCreacionOrdenResponse(BaseModel):
    """Response de validación de creación"""
    puede_crear: bool
    medico_id: int
    hospitalizacion_id: int
    razon: str = "Sin restricciones"
    ordenes_pendientes: int = 0

class BuscarOrdenesRequest(BaseModel):
    """Request para búsqueda de órdenes"""
    hospitalizacion_id: Optional[int] = None
    numero_cuenta: Optional[str] = None
    paciente_id: Optional[int] = None
    medico_id: Optional[int] = None
    tipo_orden: Optional[TipoOrden] = None
    estado: Optional[EstadoOrden] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None

# 🔬 EXÁMENES ESPECÍFICOS

class AgregarExamenRequest(BaseModel):
    """Request para agregar examen a orden"""
    examen_codigo: str
    examen_nombre: str
    examen_categoria: Optional[str] = None
    especificaciones: Optional[str] = None
    preparacion_requerida: Optional[str] = None

class ActualizarResultadoExamenRequest(BaseModel):
    """Request para actualizar resultado de examen"""
    resultado: Optional[str] = None
    valor_numerico: Optional[Decimal] = None
    unidad_medida: Optional[str] = None
    valor_referencia: Optional[str] = None
    interpretacion: Optional[str] = None
    profesional_responsable: Optional[str] = None
    validado: bool = False

# 📊 ESTADÍSTICAS SCHEMAS

class EstadisticasOrdenesResponse(BaseModel):
    """Estadísticas de órdenes por hospitalización"""
    hospitalizacion_id: int
    total_ordenes: int
    ordenes_por_estado: dict = {}  # {estado: cantidad}
    ordenes_por_tipo: dict = {}    # {tipo: cantidad}
    total_examenes: int
    examenes_completados: int
    examenes_pendientes: int
    ultima_orden: Optional[datetime] = None

class EstadisticasMedicoOrdenesResponse(BaseModel):
    """Estadísticas de órdenes por médico"""
    medico_id: int
    medico_nombre: str
    periodo_desde: datetime
    periodo_hasta: datetime
    total_ordenes: int
    ordenes_por_tipo: dict = {}
    ordenes_por_estado: dict = {}
    examenes_mas_solicitados: List[dict] = []
    promedio_ordenes_por_dia: float = 0.0

class ExamenMasSolicitado(BaseModel):
    """Examen más solicitado"""
    examen_nombre: str
    total_solicitudes: int
    porcentaje: float

class EstadisticasGeneralesOrdenesResponse(BaseModel):
    """Estadísticas generales de órdenes"""
    total_ordenes: int
    ordenes_por_estado: dict = {}
    ordenes_por_tipo: dict = {}
    examenes_mas_solicitados: List[ExamenMasSolicitado] = []
    tiempo_promedio_procesamiento: Optional[float] = None  # En horas

class OrdenesListResponse(BaseModel):
    """Response para lista paginada de órdenes"""
    ordenes: List[OrdenCabResponse]
    total: int
    page: int
    size: int
    total_pages: int

class OrdenSearchResponse(BaseModel):
    """Response para búsqueda de órdenes"""
    id: int
    numero_orden: str
    tipo_orden: TipoOrden
    tipo_orden_descripcion: str
    estado: EstadoOrden
    paciente_nombre: str
    paciente_documento: str
    medico_nombre: Optional[str] = None
    total_examenes: int = 0
    prioridad: PrioridadOrden
    created_at: datetime