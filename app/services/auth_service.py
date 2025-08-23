from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.schemas.user import UserResponse
from app.core.security import SecurityService
from app.core.exceptions import AuthenticationException, ValidationException
from typing import Optional

class AuthService:
    """🔐 Servicio de Autenticación - Patrón galloapp_backend"""
    
    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserRegister) -> User:
        """Registrar nuevo usuario médico"""
        
        # Verificar si el email ya existe
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValidationException("El email ya está registrado")
        
        # Verificar si el username ya existe
        result = await db.execute(select(User).where(User.username == user_data.username))
        existing_username = result.scalar_one_or_none()
        
        if existing_username:
            raise ValidationException("El username ya está en uso")
        
        # Crear usuario con hash de password
        hashed_password = SecurityService.get_password_hash(user_data.password)
        
        # Preparar datos profesionales para JSONB
        # Primero usar datos_profesional si viene completo
        if hasattr(user_data, 'datos_profesional') and user_data.datos_profesional:
            datos_profesional = user_data.datos_profesional
        else:
            # Si no, construirlo desde campos individuales
            datos_profesional = {}
            if user_data.especialidad:
                datos_profesional['especialidad'] = user_data.especialidad
            if user_data.colegiatura:
                datos_profesional['colegiatura'] = user_data.colegiatura
            if user_data.cargo:
                datos_profesional['cargo'] = user_data.cargo
            if user_data.telefono:
                datos_profesional['telefono'] = user_data.telefono
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password,  # Cambié a password
            first_name=user_data.first_name if hasattr(user_data, 'first_name') else (user_data.nombre_completo.split()[0] if user_data.nombre_completo else None),
            last_name=user_data.last_name if hasattr(user_data, 'last_name') else (" ".join(user_data.nombre_completo.split()[1:]) if user_data.nombre_completo and len(user_data.nombre_completo.split()) > 1 else None),
            datos_profesional=datos_profesional if datos_profesional else None,
            enabled=True,
            account_non_expired=True,
            account_non_locked=True,
            credentials_non_expired=True
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        """Autenticar usuario"""
        
        # Buscar usuario por email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationException("Credenciales inválidas")
        
        if not user.is_active:
            raise AuthenticationException("Usuario inactivo")
            
        if not user.enabled:
            raise AuthenticationException("Usuario deshabilitado")
        
        # Verificar password
        if not SecurityService.verify_password(password, user.password):
            raise AuthenticationException("Credenciales inválidas")
        
        # Actualizar último login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Obtener usuario por ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_refresh_token(db: AsyncSession, user_id: int, refresh_token: Optional[str]):
        """Actualizar refresh token del usuario"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            user.refresh_token = refresh_token
            await db.commit()
    
    @staticmethod
    async def verify_refresh_token(db: AsyncSession, refresh_token: str) -> User:
        """Verificar refresh token"""
        result = await db.execute(select(User).where(User.refresh_token == refresh_token))
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationException("Refresh token inválido")
            
        return user
    
    @staticmethod
    async def change_password(db: AsyncSession, user_id: int, current_password: str, new_password: str) -> bool:
        """Cambiar contraseña del usuario"""
        
        # Obtener usuario
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationException("Usuario no encontrado")
        
        # Verificar contraseña actual
        if not SecurityService.verify_password(current_password, user.password_hash):
            raise AuthenticationException("Contraseña actual incorrecta")
        
        # Hashear nueva contraseña y actualizar
        user.password_hash = SecurityService.get_password_hash(new_password)
        # Invalidar refresh token para forzar re-login
        user.refresh_token = None
        
        await db.commit()
        return True
    
    @staticmethod
    async def logout_user(db: AsyncSession, user_id: int) -> bool:
        """Logout del usuario - limpiar refresh token"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            user.refresh_token = None
            await db.commit()
            return True
            
        return False
    
    @staticmethod
    def create_tokens_for_user(user: User) -> dict:
        """Crear tokens JWT para usuario"""
        access_token = SecurityService.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = SecurityService.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def validate_medico_permissions(db: AsyncSession, user_id: int) -> bool:
        """Validar que el usuario sea médico"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
            
        # Un médico debe tener especialidad y colegiatura
        return bool(user.especialidad and user.colegiatura)
    
    @staticmethod
    async def get_medico_info(db: AsyncSession, user_id: int) -> dict:
        """Obtener información básica del médico"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return {}
        
        return {
            "id": user.id,
            "nombre_completo": user.nombre_completo or user.username,
            "especialidad": user.especialidad,
            "colegiatura": user.colegiatura,
            "cargo": user.cargo
        }
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Obtener usuario por username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def reset_password(db: AsyncSession, user_id: int, new_password: str) -> bool:
        """Resetear contraseña de usuario"""
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Hash nueva contraseña
            hashed_password = SecurityService.get_password_hash(new_password)
            user.password = hashed_password
            user.updated_at = datetime.utcnow()
            
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            raise AuthenticationException(f"Error reseteando contraseña: {str(e)}")