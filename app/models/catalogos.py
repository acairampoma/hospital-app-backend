from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Catalogo(Base):
    """🔍 Modelo Catálogo - Compatible con microservicio-catalogos"""
    __tablename__ = "catalogos"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False)
    descripcion = Column(Text, nullable=False)
    
    # Clasificación
    tabla_origen = Column(String(50), index=True)  # EXA, MED, CAT, etc.
    categoria = Column(String(100), index=True)
    tipo = Column(String(50), index=True)
    
    # Estado
    activo = Column(Boolean, default=True, nullable=False)
    
    # Campos adicionales para flexibilidad
    valor_numerico = Column(Numeric(10, 2))
    campo_extra1 = Column(String(100))
    campo_extra2 = Column(String(100))
    observaciones = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Catalogo(codigo='{self.codigo}', descripcion='{self.descripcion}')>"

class MedicamentoVademecum(Base):
    """💊 Modelo Medicamento Vademécum - Para recetas"""
    __tablename__ = "medicamentos_vademecum"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False)
    nombre_comercial = Column(String(200), nullable=False, index=True)
    nombre_generico = Column(String(200), index=True)
    
    # Clasificación médica
    forma_farmaceutica = Column(String(100))  # Tableta, jarabe, ampolla, etc.
    concentracion = Column(String(100))       # 500mg, 250mg/5ml, etc.
    laboratorio = Column(String(100))
    categoria_terapeutica = Column(String(150), index=True)
    
    # Información clínica
    indicaciones = Column(Text)
    contraindicaciones = Column(Text)
    posologia = Column(Text)                  # Dosis recomendada
    
    # Control
    requiere_receta = Column(Boolean, default=True)
    controlado = Column(Boolean, default=False)  # Medicamento controlado
    activo = Column(Boolean, default=True, nullable=False)
    
    # Información adicional
    precio_referencial = Column(Numeric(10, 2))
    stock_disponible = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Medicamento(codigo='{self.codigo}', nombre='{self.nombre_comercial}')>"
    
    @property
    def descripcion_completa(self) -> str:
        """Descripción completa del medicamento"""
        desc = self.nombre_comercial
        if self.concentracion:
            desc += f" {self.concentracion}"
        if self.forma_farmaceutica:
            desc += f" ({self.forma_farmaceutica})"
        return desc