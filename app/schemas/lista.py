from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class EstadoCama(str, Enum):
    """Estados de la cama"""
    DISPONIBLE = "DISPONIBLE"
    OCUPADA = "OCUPADA"
    MANTENIMIENTO = "MANTENIMIENTO"
    LIMPIEZA = "LIMPIEZA"

class TipoCama(str, Enum):
    """Tipos de cama"""
    GENERAL = "GENERAL"
    UCI = "UCI"
    PEDIATRICA = "PEDIATRICA"
    MATERNIDAD = "MATERNIDAD"
    CIRUGIA = "CIRUGIA"

# 🏥 PACIENTE POR CAMA SCHEMAS

class PacientePorCamaBase(BaseModel):
    """Base schema para paciente por cama"""
    numero_cama: str
    piso: Optional[str] = None
    ala: Optional[str] = None
    servicio: Optional[str] = None
    habitacion: Optional[str] = None
    tipo_cama: Optional[TipoCama] = TipoCama.GENERAL
    
    @validator('numero_cama')
    def validate_numero_cama(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Número de cama es requerido')
        return v.strip().upper()

class PacientePorCamaCreate(PacientePorCamaBase):
    """Create paciente por cama"""
    tiene_oxigeno: bool = False
    tiene_monitor: bool = False
    aislamiento: bool = False
    observaciones: Optional[str] = None

class PacientePorCamaUpdate(BaseModel):
    """Update paciente por cama"""
    estado_cama: Optional[EstadoCama] = None
    piso: Optional[str] = None
    ala: Optional[str] = None
    servicio: Optional[str] = None
    habitacion: Optional[str] = None
    tiene_oxigeno: Optional[bool] = None
    tiene_monitor: Optional[bool] = None
    aislamiento: Optional[bool] = None
    observaciones: Optional[str] = None

class PacientePorCamaResponse(PacientePorCamaBase):
    """Response paciente por cama"""
    id: int
    ocupada: bool = False
    estado_cama: EstadoCama = EstadoCama.DISPONIBLE
    
    # Información del paciente (si está ocupada)
    paciente_id: Optional[int] = None
    paciente_nombre: Optional[str] = None
    paciente_documento: Optional[str] = None
    paciente_telefono: Optional[str] = None
    
    # Información de hospitalización
    hospitalizacion_id: Optional[int] = None
    numero_cuenta: Optional[str] = None
    fecha_ingreso: Optional[datetime] = None
    fecha_egreso_programada: Optional[datetime] = None
    
    # Información médica
    medico_tratante: Optional[str] = None
    especialidad: Optional[str] = None
    diagnostico_principal: Optional[str] = None
    
    # Características
    tiene_oxigeno: bool = False
    tiene_monitor: bool = False
    aislamiento: bool = False
    equipos_asignados: Optional[Dict[str, Any]] = None
    
    # Información adicional
    observaciones: Optional[str] = None
    restricciones: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    fecha_ultimo_cambio: Optional[datetime] = None
    
    # Propiedades calculadas
    descripcion_cama: str = ""
    info_paciente: str = ""
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # Calcular descripción de cama
        desc = f"Cama {self.numero_cama}"
        if self.habitacion:
            desc += f" - Hab. {self.habitacion}"
        if self.servicio:
            desc += f" ({self.servicio})"
        self.descripcion_cama = desc
        
        # Información del paciente
        if not self.ocupada or not self.paciente_nombre:
            self.info_paciente = "Cama disponible"
        else:
            self.info_paciente = f"{self.paciente_nombre} - {self.paciente_documento}"

# 🏥 REQUESTS ESPECÍFICOS

class OcuparCamaRequest(BaseModel):
    """Request para ocupar cama"""
    paciente_id: int
    paciente_nombre: str
    paciente_documento: str
    paciente_telefono: Optional[str] = None
    hospitalizacion_id: int
    numero_cuenta: str
    fecha_ingreso: Optional[datetime] = None
    fecha_egreso_programada: Optional[datetime] = None
    medico_tratante: str
    especialidad: Optional[str] = None
    diagnostico_principal: Optional[str] = None

class LiberarCamaRequest(BaseModel):
    """Request para liberar cama"""
    motivo: Optional[str] = None
    fecha_egreso: Optional[datetime] = None

class BuscarCamasRequest(BaseModel):
    """Request para búsqueda de camas"""
    estado: Optional[EstadoCama] = None
    tipo_cama: Optional[TipoCama] = None
    servicio: Optional[str] = None
    piso: Optional[str] = None
    ocupada: Optional[bool] = None
    medico_tratante: Optional[str] = None
    tiene_oxigeno: Optional[bool] = None
    tiene_monitor: Optional[bool] = None

class RangoCamasRequest(BaseModel):
    """Request para obtener rango de camas"""
    start: str
    end: str
    
    @validator('start', 'end')
    def validate_bed_numbers(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Número de cama es requerido')
        return v.strip().upper()

# 🏥 ESTRUCTURA HOSPITAL SCHEMAS

class EstructuraHospitalBase(BaseModel):
    """Base schema para estructura hospital"""
    hospital_id: int
    nombre_hospital: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    director: Optional[str] = None

class EstructuraHospitalCreate(EstructuraHospitalBase):
    """Create estructura hospital"""
    total_camas: int = 0
    numero_pisos: Optional[int] = None
    numero_habitaciones: Optional[int] = None
    nivel_hospital: Optional[str] = None  # I, II, III, IV
    categoria: Optional[str] = None       # PUBLICO, PRIVADO, MIXTO

class EstructuraHospitalUpdate(BaseModel):
    """Update estructura hospital"""
    nombre_hospital: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    director: Optional[str] = None
    total_camas: Optional[int] = None
    numero_pisos: Optional[int] = None
    numero_habitaciones: Optional[int] = None
    activo: Optional[bool] = None

class EstructuraHospitalResponse(EstructuraHospitalBase):
    """Response estructura hospital"""
    id: int
    
    # Capacidad
    total_camas: int = 0
    camas_disponibles: int = 0
    camas_ocupadas: int = 0
    camas_mantenimiento: int = 0
    
    # Servicios y especialidades
    servicios: Optional[List[str]] = []
    especialidades: Optional[List[str]] = []
    
    # Estructura física
    numero_pisos: Optional[int] = None
    numero_habitaciones: Optional[int] = None
    
    # Tipos de cama
    camas_generales: int = 0
    camas_uci: int = 0
    camas_pediatricas: int = 0
    camas_maternidad: int = 0
    camas_cirugia: int = 0
    
    # Equipamiento
    tiene_laboratorio: bool = False
    tiene_imagenologia: bool = False
    tiene_farmacia: bool = False
    tiene_emergencia: bool = False
    
    # Estado
    activo: bool = True
    nivel_hospital: Optional[str] = None
    categoria: Optional[str] = None
    
    # Horarios
    horario_atencion: Optional[Dict[str, Any]] = None
    observaciones: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Propiedades calculadas
    porcentaje_ocupacion: float = 0.0
    info_capacidad: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # Calcular porcentaje de ocupación
        if self.total_camas > 0:
            self.porcentaje_ocupacion = (self.camas_ocupadas / self.total_camas) * 100
        else:
            self.porcentaje_ocupacion = 0.0
            
        # Info de capacidad
        self.info_capacidad = {
            "total": self.total_camas,
            "disponibles": self.camas_disponibles,
            "ocupadas": self.camas_ocupadas,
            "mantenimiento": self.camas_mantenimiento,
            "porcentaje_ocupacion": self.porcentaje_ocupacion
        }

# 📊 ESTADÍSTICAS SCHEMAS

class EstadisticasOcupacionResponse(BaseModel):
    """Estadísticas de ocupación de camas"""
    total_camas: int
    camas_ocupadas: int
    camas_disponibles: int
    camas_mantenimiento: int
    camas_limpieza: int
    porcentaje_ocupacion: float
    porcentaje_disponibilidad: float
    
    # Por tipo de cama
    ocupacion_por_tipo: Dict[str, Dict[str, int]] = {}
    
    # Por servicio
    ocupacion_por_servicio: Dict[str, Dict[str, int]] = {}
    
    # Tendencias
    ocupacion_ultima_semana: List[Dict[str, Any]] = []

class ConteosCamasResponse(BaseModel):
    """Conteos de camas por estado"""
    total: int
    disponible: int
    ocupada: int
    mantenimiento: int
    limpieza: int

class PorcentajesOcupacionResponse(BaseModel):
    """Porcentajes de ocupación"""
    ocupacion: float
    disponibilidad: float
    mantenimiento: float
    limpieza: float

class EstadisticasDisponibilidadResponse(BaseModel):
    """Estadísticas detalladas de disponibilidad"""
    resumen_general: ConteosCamasResponse
    porcentajes: PorcentajesOcupacionResponse
    por_tipo_cama: Dict[str, ConteosCamasResponse] = {}
    por_servicio: Dict[str, ConteosCamasResponse] = {}
    por_piso: Dict[str, ConteosCamasResponse] = {}
    
    # Información adicional
    camas_con_equipamiento: Dict[str, int] = {}  # oxigeno, monitor, etc.
    tiempo_promedio_estadia: Optional[float] = None  # En días
    rotacion_camas_dia: Optional[float] = None

# ===== SCHEMAS ADICIONALES PARA SERVICIOS =====

class MovimientoCamaCreate(BaseModel):
    """Schema para crear movimiento de cama"""
    cama_id: int
    paciente_id: int
    nombre_paciente: str
    documento: str
    fecha_ingreso: Optional[datetime] = None
    motivo_ingreso: str
    observaciones: Optional[str] = None

class MovimientoCamaResponse(BaseModel):
    """Response para movimiento de cama"""
    id: int
    cama_id: int
    paciente_id: int
    nombre_paciente: str
    documento: str
    fecha_ingreso: datetime
    fecha_salida: Optional[datetime] = None
    dias_estancia: Optional[int] = None
    motivo_ingreso: str
    motivo_salida: Optional[str] = None
    observaciones: Optional[str] = None
    creado_por: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AsignacionCamaRequest(BaseModel):
    """Request para asignar paciente a cama"""
    paciente_id: int
    nombre_paciente: str
    documento: str
    fecha_ingreso: Optional[datetime] = None
    motivo_ingreso: str
    observaciones: Optional[str] = None

class CambioServicioRequest(BaseModel):
    """Request para cambio de servicio"""
    nueva_cama_id: int
    motivo_cambio: str
    observaciones: Optional[str] = None

class CamasListResponse(BaseModel):
    """Response para lista de camas"""
    camas: List[PacientePorCamaResponse]
    total: int
    estadisticas: Dict[str, Any]

class CamaDisponibilidadResponse(BaseModel):
    """Response para disponibilidad de camas"""
    servicio: str
    unidad: str
    total_camas: int
    ocupadas: int
    disponibles: int
    en_mantenimiento: int
    porcentaje_ocupacion: float

class EstructuraCompleta(BaseModel):
    """Estructura completa del hospital"""
    servicios: List[Dict[str, Any]]
    total_servicios: int
    total_unidades: int
    total_camas: int