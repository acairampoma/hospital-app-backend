from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class OrdenCab(Base):
    """📋 Modelo Orden Cabecera - Compatible con microservicio-orden"""
    __tablename__ = "orden_cab"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    numero_orden = Column(String(20), unique=True, index=True, nullable=False)
    
    # Información del origen
    hospitalizacion_id = Column(Integer, nullable=False, index=True)
    numero_cuenta = Column(String(20), index=True)
    
    # Información del paciente
    paciente_id = Column(Integer, index=True)
    paciente_nombre = Column(String(200))
    paciente_documento = Column(String(20))
    
    # Tipo de orden
    tipo_orden = Column(String(2), nullable=False, index=True)  # 01=Laboratorio, 02=Imagenología, 03=Procedimiento
    
    # Información clínica
    diagnostico = Column(Text)
    indicaciones_clinicas = Column(Text)
    observaciones = Column(Text)
    
    # Estado de la orden
    estado = Column(String(10), default="PENDIENTE", nullable=False)  # PENDIENTE, PROCESANDO, COMPLETADA, CANCELADA
    prioridad = Column(String(10), default="NORMAL")  # URGENTE, NORMAL, BAJA
    
    # Información del médico solicitante
    creado_por = Column(Integer, ForeignKey("users.id"), nullable=False)
    medico_nombre = Column(String(200))
    medico_especialidad = Column(String(100))
    medico_colegiatura = Column(String(50))
    
    # Fechas de procesamiento
    fecha_solicitada = Column(DateTime(timezone=True))
    fecha_programada = Column(DateTime(timezone=True))
    fecha_completada = Column(DateTime(timezone=True))
    
    # Información del servicio ejecutor
    servicio_destino = Column(String(100))     # Laboratorio, Radiología, etc.
    profesional_ejecutor = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    medico = relationship("User", foreign_keys=[creado_por])
    examenes = relationship("OrdenDet", back_populates="orden", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<OrdenCab(numero='{self.numero_orden}', paciente='{self.paciente_nombre}')>"
    
    @property
    def tipo_orden_descripcion(self) -> str:
        """Descripción del tipo de orden"""
        tipos = {
            "01": "Laboratorio",
            "02": "Imagenología", 
            "03": "Procedimiento",
            "04": "Interconsulta"
        }
        return tipos.get(self.tipo_orden, "Desconocido")
    
    @property
    def puede_editarse(self) -> bool:
        """Verificar si la orden puede editarse"""
        return self.estado in ["PENDIENTE", "PROCESANDO"]
    
    @property
    def total_examenes(self) -> int:
        """Total de exámenes en la orden"""
        return len(self.examenes)

class OrdenDet(Base):
    """📋 Modelo Orden Detalle - Exámenes/Procedimientos solicitados"""
    __tablename__ = "orden_det"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("orden_cab.id"), nullable=False)
    
    # Información del examen/procedimiento
    examen_id = Column(Integer, ForeignKey("catalogos.id"))
    examen_codigo = Column(String(20))
    examen_nombre = Column(String(200), nullable=False)
    examen_categoria = Column(String(100))
    
    # Especificaciones del examen
    especificaciones = Column(Text)             # Instrucciones específicas
    preparacion_requerida = Column(Text)        # Preparación del paciente
    
    # Estado del examen
    estado = Column(String(10), default="PENDIENTE", nullable=False)  # PENDIENTE, EN_PROCESO, COMPLETADO, CANCELADO
    
    # Resultados
    resultado = Column(Text)                    # Resultado textual
    valor_numerico = Column(Numeric(10, 3))     # Valor numérico si aplica
    unidad_medida = Column(String(20))          # mg/dl, U/L, etc.
    valor_referencia = Column(String(100))      # Rangos normales
    interpretacion = Column(Text)               # Interpretación del resultado
    
    # Información del procesamiento
    fecha_toma_muestra = Column(DateTime(timezone=True))
    fecha_resultado = Column(DateTime(timezone=True))
    profesional_responsable = Column(String(200))
    
    # Archivos adjuntos (imágenes, PDFs)
    archivo_resultado = Column(String(255))     # Path del archivo
    tipo_archivo = Column(String(20))           # PDF, JPG, DICOM, etc.
    
    # Control de calidad
    validado = Column(Boolean, default=False)
    fecha_validacion = Column(DateTime(timezone=True))
    validado_por = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    orden = relationship("OrdenCab", back_populates="examenes")
    examen_catalogo = relationship("Catalogo")
    
    def __repr__(self):
        return f"<OrdenDet(examen='{self.examen_nombre}', estado='{self.estado}')>"
    
    @property
    def tiene_resultado(self) -> bool:
        """Verificar si el examen tiene resultado"""
        return self.resultado is not None or self.valor_numerico is not None
    
    @property
    def resultado_completo(self) -> str:
        """Resultado completo formateado"""
        if self.valor_numerico is not None:
            resultado = f"{self.valor_numerico}"
            if self.unidad_medida:
                resultado += f" {self.unidad_medida}"
            if self.valor_referencia:
                resultado += f" (Ref: {self.valor_referencia})"
            return resultado
        return self.resultado or "Sin resultado"