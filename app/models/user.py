from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """👥 Modelo Usuario - Compatible con tabla existente"""
    __tablename__ = "users"
    
    # Campos básicos - coinciden con tu tabla
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # Cambié de password_hash a password
    
    # Campos de tu tabla
    first_name = Column(String(100))
    last_name = Column(String(100))
    enabled = Column(Boolean, default=True, nullable=False)
    account_non_expired = Column(Boolean, default=True, nullable=False)
    account_non_locked = Column(Boolean, default=True, nullable=False)
    credentials_non_expired = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0)
    datos_profesional = Column(JSONB)  # Para datos médicos
    
    # Timestamps - coinciden con tu tabla
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    # 🏥 Propiedades calculadas
    @property
    def is_active(self) -> bool:
        """Usuario activo si enabled=True y account_non_locked=True"""
        return self.enabled and self.account_non_locked
    
    @property
    def nombre_completo(self) -> str:
        """Nombre completo calculado desde first_name y last_name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username
    
    @property
    def is_medico(self) -> bool:
        """Verificar si el usuario es médico basado en datos_profesional"""
        if self.datos_profesional:
            return self.datos_profesional.get('especialidad') is not None
        return False
    
    @property
    def especialidad(self) -> str:
        """Especialidad médica desde datos_profesional"""
        if self.datos_profesional:
            return self.datos_profesional.get('especialidad')
        return None
    
    @property
    def colegiatura(self) -> str:
        """Número de colegiatura desde datos_profesional"""
        if self.datos_profesional:
            return self.datos_profesional.get('colegiatura')
        return None
    
    @property
    def cargo(self) -> str:
        """Cargo desde datos_profesional"""
        if self.datos_profesional:
            return self.datos_profesional.get('cargo')
        return None
    
    @property
    def telefono(self) -> str:
        """Teléfono desde datos_profesional"""
        if self.datos_profesional:
            return self.datos_profesional.get('telefono')
        return None