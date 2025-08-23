from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PacientePorCama(Base):
    """🏥 Modelo Paciente por Cama - Compatible con microservicio-listas"""
    __tablename__ = "pacientes_por_cama"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    numero_cama = Column(String(10), unique=True, index=True, nullable=False)
    
    # Información del paciente (si está ocupada)
    paciente_id = Column(Integer, index=True)
    paciente_nombre = Column(String(200))
    paciente_documento = Column(String(20), index=True)
    paciente_telefono = Column(String(20))
    
    # Estado de la cama
    ocupada = Column(Boolean, default=False, nullable=False)
    estado_cama = Column(String(20), default="DISPONIBLE")  # DISPONIBLE, OCUPADA, MANTENIMIENTO, LIMPIEZA
    
    # Información de hospitalización
    hospitalizacion_id = Column(Integer, index=True)
    numero_cuenta = Column(String(20), index=True)
    fecha_ingreso = Column(DateTime(timezone=True))
    fecha_egreso_programada = Column(DateTime(timezone=True))
    
    # Información médica básica
    medico_tratante = Column(String(200))
    especialidad = Column(String(100))
    diagnostico_principal = Column(Text)
    
    # Ubicación en el hospital
    piso = Column(String(10))
    ala = Column(String(50))
    servicio = Column(String(100))
    habitacion = Column(String(10))
    
    # Relación con estructura hospital
    estructura_id = Column(Integer, ForeignKey("estructura_hospital.id"))
    estructura = relationship("EstructuraHospital", back_populates="pacientes_por_cama")
    
    # Características de la cama
    tipo_cama = Column(String(50))              # GENERAL, UCI, PEDIATRICA, etc.
    tiene_oxigeno = Column(Boolean, default=False)
    tiene_monitor = Column(Boolean, default=False)
    aislamiento = Column(Boolean, default=False)
    
    # Información adicional
    observaciones = Column(Text)
    restricciones = Column(Text)
    equipos_asignados = Column(JSON)            # Lista de equipos médicos
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    fecha_ultimo_cambio = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<PacientePorCama(cama='{self.numero_cama}', ocupada={self.ocupada})>"
    
    @property
    def descripcion_cama(self) -> str:
        """Descripción completa de la cama"""
        desc = f"Cama {self.numero_cama}"
        if self.habitacion:
            desc += f" - Hab. {self.habitacion}"
        if self.servicio:
            desc += f" ({self.servicio})"
        return desc
    
    @property
    def info_paciente(self) -> str:
        """Información del paciente si está ocupada"""
        if not self.ocupada or not self.paciente_nombre:
            return "Cama disponible"
        return f"{self.paciente_nombre} - {self.paciente_documento}"
    
    def liberar_cama(self):
        """Liberar la cama"""
        self.ocupada = False
        self.estado_cama = "DISPONIBLE"
        self.paciente_id = None
        self.paciente_nombre = None
        self.paciente_documento = None
        self.hospitalizacion_id = None
        self.numero_cuenta = None
        self.fecha_ingreso = None
        self.medico_tratante = None
        self.diagnostico_principal = None
        self.fecha_ultimo_cambio = func.now()
    
    def ocupar_cama(self, paciente_data: dict):
        """Ocupar la cama con un paciente"""
        self.ocupada = True
        self.estado_cama = "OCUPADA"
        self.paciente_id = paciente_data.get("paciente_id")
        self.paciente_nombre = paciente_data.get("paciente_nombre")
        self.paciente_documento = paciente_data.get("paciente_documento")
        self.hospitalizacion_id = paciente_data.get("hospitalizacion_id")
        self.numero_cuenta = paciente_data.get("numero_cuenta")
        self.fecha_ingreso = paciente_data.get("fecha_ingreso", func.now())
        self.medico_tratante = paciente_data.get("medico_tratante")
        self.diagnostico_principal = paciente_data.get("diagnostico_principal")
        self.fecha_ultimo_cambio = func.now()

class EstructuraHospital(Base):
    """🏥 Modelo Estructura Hospital - Configuración hospitalaria"""
    __tablename__ = "estructura_hospital"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, unique=True, index=True, nullable=False)
    nombre_hospital = Column(String(200), nullable=False)
    
    # Información del hospital
    direccion = Column(Text)
    telefono = Column(String(20))
    email = Column(String(100))
    director = Column(String(200))
    
    # Capacidad y estructura
    total_camas = Column(Integer, default=0)
    camas_disponibles = Column(Integer, default=0)
    camas_ocupadas = Column(Integer, default=0)
    camas_mantenimiento = Column(Integer, default=0)
    
    # Servicios disponibles
    servicios = Column(JSON)                    # Lista de servicios médicos
    especialidades = Column(JSON)               # Lista de especialidades
    
    # Estructura física
    numero_pisos = Column(Integer)
    numero_habitaciones = Column(Integer)
    
    # Configuración por tipos de cama
    camas_generales = Column(Integer, default=0)
    camas_uci = Column(Integer, default=0)
    camas_pediatricas = Column(Integer, default=0)
    camas_maternidad = Column(Integer, default=0)
    camas_cirugia = Column(Integer, default=0)
    
    # Equipamiento
    tiene_laboratorio = Column(Boolean, default=False)
    tiene_imagenologia = Column(Boolean, default=False)
    tiene_farmacia = Column(Boolean, default=False)
    tiene_emergencia = Column(Boolean, default=False)
    
    # Estado del hospital
    activo = Column(Boolean, default=True, nullable=False)
    nivel_hospital = Column(String(20))         # I, II, III, IV
    categoria = Column(String(50))              # PUBLICO, PRIVADO, MIXTO
    
    # Información adicional
    horario_atencion = Column(JSON)             # Horarios de atención
    observaciones = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relación con pacientes por cama
    pacientes_por_cama = relationship("PacientePorCama", back_populates="estructura", lazy="select")
    
    def __repr__(self):
        return f"<EstructuraHospital(id={self.hospital_id}, nombre='{self.nombre_hospital}')>"
    
    @property
    def porcentaje_ocupacion(self) -> float:
        """Porcentaje de ocupación del hospital"""
        if self.total_camas == 0:
            return 0.0
        return (self.camas_ocupadas / self.total_camas) * 100
    
    @property
    def info_capacidad(self) -> dict:
        """Información de capacidad resumida"""
        return {
            "total": self.total_camas,
            "disponibles": self.camas_disponibles,
            "ocupadas": self.camas_ocupadas,
            "mantenimiento": self.camas_mantenimiento,
            "porcentaje_ocupacion": self.porcentaje_ocupacion
        }
    
    def actualizar_conteos_camas(self):
        """Actualizar conteos de camas basado en datos reales"""
        # Este método se ejecutaría con una query a PacientePorCama
        # para sincronizar los conteos
        pass