from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RecetaCab(Base):
    """💊 Modelo Receta Cabecera - Compatible con microservicio-receta"""
    __tablename__ = "receta_cab"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    numero_receta = Column(String(20), unique=True, index=True, nullable=False)
    
    # Origen de la receta
    tipo_origen = Column(String(10), nullable=False, index=True)  # HOS, CON, EME
    origen_id = Column(Integer, nullable=False, index=True)       # ID hospitalización, consulta, etc.
    
    # Información del paciente
    paciente_id = Column(Integer, index=True)
    paciente_nombre = Column(String(200))
    paciente_documento = Column(String(20))
    
    # Información médica
    diagnostico_principal = Column(Text)
    indicaciones_generales = Column(Text)
    
    # Control de la receta
    estado = Column(String(2), default="01", nullable=False)  # 01=Activa, 02=Despachada, 03=Vencida, 04=Anulada
    fecha_vencimiento = Column(DateTime(timezone=True))
    
    # Información del médico
    creado_por = Column(Integer, ForeignKey("users.id"), nullable=False)
    medico_nombre = Column(String(200))
    medico_colegiatura = Column(String(50))
    
    # Firma digital
    firmada = Column(Boolean, default=False)
    fecha_firma = Column(DateTime(timezone=True))
    hash_firma = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    medico = relationship("User", foreign_keys=[creado_por])
    detalles = relationship("RecetaDet", back_populates="receta", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RecetaCab(numero='{self.numero_receta}', paciente='{self.paciente_nombre}')>"
    
    @property
    def estado_descripcion(self) -> str:
        """Descripción del estado"""
        estados = {
            "01": "Activa",
            "02": "Despachada", 
            "03": "Vencida",
            "04": "Anulada"
        }
        return estados.get(self.estado, "Desconocido")

class RecetaDet(Base):
    """💊 Modelo Receta Detalle - Medicamentos prescritos"""
    __tablename__ = "receta_det"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(Integer, ForeignKey("receta_cab.id"), nullable=False)
    
    # Información del medicamento
    medicamento_id = Column(Integer, ForeignKey("medicamentos_vademecum.id"))
    medicamento_codigo = Column(String(20))
    medicamento_nombre = Column(String(200), nullable=False)
    
    # Prescripción
    cantidad = Column(Integer, nullable=False)           # Cantidad a dispensar
    unidad = Column(String(20), default="UNIDAD")       # UNIDAD, FRASCO, CAJA, etc.
    posologia = Column(Text)                            # Indicaciones de uso
    duracion_tratamiento = Column(String(50))           # "7 días", "2 semanas", etc.
    
    # Control
    cantidad_despachada = Column(Integer, default=0)
    despachado = Column(Boolean, default=False)
    fecha_despacho = Column(DateTime(timezone=True))
    
    # Observaciones
    observaciones = Column(Text)
    sustituible = Column(Boolean, default=True)         # Se puede sustituir por genérico
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    receta = relationship("RecetaCab", back_populates="detalles")
    medicamento = relationship("MedicamentoVademecum")
    
    def __repr__(self):
        return f"<RecetaDet(medicamento='{self.medicamento_nombre}', cantidad={self.cantidad})>"
    
    @property
    def prescripcion_completa(self) -> str:
        """Descripción completa de la prescripción"""
        desc = f"{self.medicamento_nombre} - {self.cantidad} {self.unidad}"
        if self.posologia:
            desc += f" - {self.posologia}"
        return desc