from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class HospitalizacionNota(Base):
    """📝 Modelo Nota de Hospitalización - Compatible con microservicio-notas"""
    __tablename__ = "hospitalizacion_notas"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    hospitalizacion_id = Column(Integer, nullable=False, index=True)
    numero_cuenta = Column(String(20), index=True)
    
    # Información del paciente
    paciente_id = Column(Integer, index=True)
    paciente_nombre = Column(String(200))
    
    # Tipo de nota
    tipo_nota = Column(String(2), nullable=False, index=True)  # 01=Evolución, 02=Interconsulta
    
    # Contenido de la nota
    contenido_nota = Column(Text, nullable=False)
    observaciones = Column(Text)
    
    # Estado de la nota
    estado = Column(String(10), default="BORRADOR", nullable=False)  # BORRADOR, FINALIZADA
    
    # Información del médico
    creado_por = Column(Integer, ForeignKey("users.id"), nullable=False)
    medico_nombre = Column(String(200))
    medico_especialidad = Column(String(100))
    medico_colegiatura = Column(String(50))
    
    # Audio y transcripción
    tiene_audio = Column(Boolean, default=False)
    archivo_audio = Column(String(255))        # Path o URL del archivo de audio
    audio_data = Column(LargeBinary)           # Datos binarios del audio (opcional)
    transcripcion_automatica = Column(Text)    # Transcripción del audio
    
    # Firma digital
    firmada = Column(Boolean, default=False)
    fecha_firma = Column(DateTime(timezone=True))
    hash_firma = Column(String(255))
    firma_digital_data = Column(LargeBinary)   # Datos de la firma
    
    # Control de versiones
    version = Column(Integer, default=1)
    es_version_actual = Column(Boolean, default=True)
    nota_original_id = Column(Integer, ForeignKey("hospitalizacion_notas.id"))
    
    # Timestamps
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    finalizado_en = Column(DateTime(timezone=True))
    
    # Relaciones
    medico = relationship("User", foreign_keys=[creado_por])
    nota_original = relationship("HospitalizacionNota", remote_side=[id])
    
    def __repr__(self):
        return f"<HospitalizacionNota(id={self.id}, paciente='{self.paciente_nombre}', tipo='{self.tipo_nota}')>"
    
    @property
    def tipo_nota_descripcion(self) -> str:
        """Descripción del tipo de nota"""
        tipos = {
            "01": "Evolución",
            "02": "Interconsulta"
        }
        return tipos.get(self.tipo_nota, "Desconocido")
    
    @property
    def puede_editarse(self) -> bool:
        """Verificar si la nota puede editarse"""
        return self.estado == "BORRADOR" and not self.firmada
    
    @property
    def resumen_contenido(self) -> str:
        """Resumen del contenido para listados"""
        if len(self.contenido_nota) <= 100:
            return self.contenido_nota
        return self.contenido_nota[:97] + "..."
    
    def finalizar_nota(self):
        """Finalizar la nota (cambiar estado)"""
        self.estado = "FINALIZADA"
        self.finalizado_en = func.now()
        
    def firmar_nota(self, hash_firma: str):
        """Firmar digitalmente la nota"""
        self.firmada = True
        self.fecha_firma = func.now()
        self.hash_firma = hash_firma