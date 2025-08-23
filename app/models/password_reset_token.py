from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.database import Base

class PasswordResetToken(Base):
    """🔐 Modelo para tokens de recuperación de contraseña"""
    
    __tablename__ = "password_reset_tokens"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relación con el modelo User
    user = relationship("User", back_populates="password_reset_tokens")
    
    def __repr__(self):
        return f"<PasswordResetToken(email={self.email}, token={self.token}, used={self.used})>"
    
    def is_expired(self):
        """Verificar si el token ha expirado"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Verificar si el token es válido (no usado y no expirado)"""
        return not self.used and not self.is_expired()
    
    @classmethod
    def generate_token(cls):
        """Generar código de 6 dígitos"""
        import random
        return str(random.randint(100000, 999999))
    
    @classmethod
    def create_token(cls, user_id: int, email: str):
        """Crear nuevo token con expiración de 15 minutos"""
        token = cls.generate_token()
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        return cls(
            user_id=user_id,
            email=email,
            token=token,
            expires_at=expires_at
        )