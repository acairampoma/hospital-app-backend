from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TipoNota(str, Enum):
    """Tipos de nota médica"""
    EVOLUCION = "01"
    INTERCONSULTA = "02"

class EstadoNota(str, Enum):
    """Estados de la nota"""
    BORRADOR = "BORRADOR"
    FINALIZADA = "FINALIZADA"

# 📝 NOTA SCHEMAS

class NotaBase(BaseModel):
    """Base schema para notas"""
    hospitalizacion_id: int
    numero_cuenta: Optional[str] = None
    tipo_nota: TipoNota
    contenido_nota: str
    observaciones: Optional[str] = None
    
    @validator('contenido_nota')
    def validate_contenido(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('El contenido de la nota debe tener al menos 10 caracteres')
        return v.strip()

class NotaCreate(NotaBase):
    """Create nota schema"""
    paciente_id: Optional[int] = None
    paciente_nombre: Optional[str] = None

class NotaUpdate(BaseModel):
    """Update nota schema"""
    contenido_nota: Optional[str] = None
    observaciones: Optional[str] = None
    
    @validator('contenido_nota')
    def validate_contenido(cls, v):
        if v is not None and len(v.strip()) < 10:
            raise ValueError('El contenido de la nota debe tener al menos 10 caracteres')
        return v.strip() if v else None

class NotaResponse(NotaBase):
    """Response nota básica"""
    id: int
    paciente_id: Optional[int] = None
    paciente_nombre: Optional[str] = None
    estado: EstadoNota = EstadoNota.BORRADOR
    
    # Información del médico
    creado_por: int
    medico_nombre: Optional[str] = None
    medico_especialidad: Optional[str] = None
    medico_colegiatura: Optional[str] = None
    
    # Control de audio
    tiene_audio: bool = False
    archivo_audio: Optional[str] = None
    
    # Firma digital
    firmada: bool = False
    fecha_firma: Optional[datetime] = None
    
    # Control de versiones
    version: int = 1
    es_version_actual: bool = True
    
    # Timestamps
    creado_en: datetime
    actualizado_en: Optional[datetime] = None
    finalizado_en: Optional[datetime] = None
    
    # Propiedades calculadas
    tipo_nota_descripcion: str = ""
    puede_editarse: bool = True
    resumen_contenido: str = ""
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # Calcular propiedades
        tipos = {"01": "Evolución", "02": "Interconsulta"}
        self.tipo_nota_descripcion = tipos.get(self.tipo_nota, "Desconocido")
        self.puede_editarse = self.estado == EstadoNota.BORRADOR and not self.firmada
        
        # Resumen del contenido
        if len(self.contenido_nota) <= 100:
            self.resumen_contenido = self.contenido_nota
        else:
            self.resumen_contenido = self.contenido_nota[:97] + "..."

class NotaCompletaResponse(NotaResponse):
    """Response nota completa con todos los campos"""
    transcripcion_automatica: Optional[str] = None
    hash_firma: Optional[str] = None

# 📝 REQUESTS ESPECÍFICOS

class FinalizarNotaRequest(BaseModel):
    """Request para finalizar nota"""
    medico_id: int
    observaciones_finales: Optional[str] = None

class BuscarNotasRequest(BaseModel):
    """Request para búsqueda de notas"""
    hospitalizacion_id: Optional[int] = None
    numero_cuenta: Optional[str] = None
    paciente_id: Optional[int] = None
    medico_id: Optional[int] = None
    tipo_nota: Optional[TipoNota] = None
    estado: Optional[EstadoNota] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None

class ValidarCreacionNotaRequest(BaseModel):
    """Request para validar si se puede crear nota"""
    medico_id: int
    hospitalizacion_id: int

class ValidarCreacionNotaResponse(BaseModel):
    """Response de validación de creación"""
    puede_crear: bool
    medico_id: int
    hospitalizacion_id: int
    razon: str = "Sin restricciones"

# 🔊 AUDIO SCHEMAS

class AudioNotaRequest(BaseModel):
    """Request para manejar audio de nota"""
    medico_id: int

class AudioNotaResponse(BaseModel):
    """Response de audio de nota"""
    nota_id: int
    tiene_audio: bool
    audio_eliminado: Optional[bool] = None
    mensaje: str

class VerificarAudioResponse(BaseModel):
    """Response para verificar audio"""
    nota_id: int
    tiene_audio: bool

# 📄 PDF SCHEMAS

class GenerarPdfRequest(BaseModel):
    """Request para generar PDF"""
    nota_id: Optional[int] = None
    hospitalizacion_id: Optional[int] = None
    incluir_firma: bool = True
    incluir_transcripcion: bool = False

# 📊 ESTADÍSTICAS SCHEMAS

class EstadisticasNotaResponse(BaseModel):
    """Estadísticas de notas por hospitalización"""
    hospitalizacion_id: int
    total_notas: int
    notas_borrador: int
    notas_finalizadas: int
    notas_con_audio: int
    notas_firmadas: int
    tipos_nota: dict = {}  # {tipo: cantidad}
    medicos_participantes: List[dict] = []  # [{nombre, total_notas}]
    ultima_nota: Optional[datetime] = None
    
class EstadisticasMedicoNotasResponse(BaseModel):
    """Estadísticas de notas por médico"""
    medico_id: int
    medico_nombre: str
    periodo_desde: datetime
    periodo_hasta: datetime
    total_notas: int
    notas_por_tipo: dict = {}
    notas_por_estado: dict = {}
    promedio_notas_por_dia: float = 0.0

class NotasListResponse(BaseModel):
    """Response para lista paginada de notas"""
    notas: List[NotaResponse]
    total: int
    page: int
    size: int
    total_pages: int

class NotaSearchResponse(BaseModel):
    """Response para búsqueda de notas"""
    id: int
    hospitalizacion_id: int
    numero_cuenta: Optional[str] = None
    tipo_nota: TipoNota
    tipo_nota_descripcion: str
    estado: EstadoNota
    paciente_nombre: Optional[str] = None
    medico_nombre: Optional[str] = None
    resumen_contenido: str
    tiene_audio: bool = False
    firmada: bool = False
    creado_en: datetime