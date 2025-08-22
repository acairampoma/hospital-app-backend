from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import SecurityService
from app.core.exceptions import NotFoundError, ValidationException
from typing import List, Optional

class UserService:
    """👥 Servicio de Usuarios - Compatible con UserController Java"""
    
    @staticmethod
    async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtener todos los usuarios"""
        result = await db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Obtener usuario por ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError(f"Usuario no encontrado con ID: {user_id}")
            
        return user
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Obtener usuario por username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Crear nuevo usuario"""
        
        # Verificar email único
        existing_email = await UserService.get_user_by_email(db, user_data.email)
        if existing_email:
            raise ValidationException("El email ya está registrado")
        
        # Verificar username único
        existing_username = await UserService.get_user_by_username(db, user_data.username)
        if existing_username:
            raise ValidationException("El username ya está en uso")
        
        # Crear usuario
        hashed_password = SecurityService.get_password_hash(user_data.password)
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            nombre_completo=user_data.nombre_completo,
            telefono=user_data.telefono,
            especialidad=user_data.especialidad,
            colegiatura=user_data.colegiatura,
            cargo=user_data.cargo,
            is_active=True,
            enabled=True,
            is_verified=True
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> User:
        """Actualizar usuario"""
        
        # Obtener usuario existente
        user = await UserService.get_user_by_id(db, user_id)
        
        # Verificar email único si se está cambiando
        if user_data.email and user_data.email != user.email:
            existing_email = await UserService.get_user_by_email(db, user_data.email)
            if existing_email:
                raise ValidationException("El email ya está registrado")
            user.email = user_data.email
        
        # Verificar username único si se está cambiando
        if user_data.username and user_data.username != user.username:
            existing_username = await UserService.get_user_by_username(db, user_data.username)
            if existing_username:
                raise ValidationException("El username ya está en uso")
            user.username = user_data.username
        
        # Actualizar campos
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field not in ['email', 'username']:  # Ya procesados arriba
                setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Eliminar usuario (soft delete)"""
        user = await UserService.get_user_by_id(db, user_id)
        
        # Soft delete
        user.is_active = False
        user.enabled = False
        
        await db.commit()
        return True
    
    @staticmethod
    async def get_enabled_users(db: AsyncSession) -> List[User]:
        """Obtener usuarios habilitados"""
        result = await db.execute(
            select(User)
            .where(and_(User.enabled == True, User.is_active == True))
            .order_by(User.nombre_completo)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_medicos(db: AsyncSession) -> List[User]:
        """Obtener todos los médicos (usuarios con especialidad)"""
        result = await db.execute(
            select(User)
            .where(and_(
                User.is_active == True,
                User.enabled == True,
                User.especialidad.isnot(None),
                User.colegiatura.isnot(None)
            ))
            .order_by(User.especialidad, User.nombre_completo)
        )
        return result.scalars().all()
    
    @staticmethod
    async def search_users(db: AsyncSession, query: str) -> List[User]:
        """Buscar usuarios por nombre, username o email"""
        search_term = f"%{query}%"
        
        result = await db.execute(
            select(User)
            .where(and_(
                User.is_active == True,
                or_(
                    User.nombre_completo.ilike(search_term),
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.especialidad.ilike(search_term)
                )
            ))
            .order_by(User.nombre_completo)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_users_by_specialty(db: AsyncSession, especialidad: str) -> List[User]:
        """Obtener usuarios por especialidad"""
        result = await db.execute(
            select(User)
            .where(and_(
                User.is_active == True,
                User.especialidad.ilike(f"%{especialidad}%")
            ))
            .order_by(User.nombre_completo)
        )
        return result.scalars().all()
    
    @staticmethod
    async def toggle_user_status(db: AsyncSession, user_id: int) -> User:
        """Cambiar estado habilitado/deshabilitado del usuario"""
        user = await UserService.get_user_by_id(db, user_id)
        
        user.enabled = not user.enabled
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_count(db: AsyncSession) -> dict:
        """Obtener conteos de usuarios"""
        total_result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
        total = total_result.scalar()
        
        enabled_result = await db.execute(
            select(func.count(User.id))
            .where(and_(User.is_active == True, User.enabled == True))
        )
        enabled = enabled_result.scalar()
        
        medicos_result = await db.execute(
            select(func.count(User.id))
            .where(and_(
                User.is_active == True,
                User.especialidad.isnot(None),
                User.colegiatura.isnot(None)
            ))
        )
        medicos = medicos_result.scalar()
        
        return {
            "total": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "medicos": medicos
        }
    
    @staticmethod
    async def validate_medico(db: AsyncSession, user_id: int) -> bool:
        """Validar que el usuario sea un médico válido"""
        user = await UserService.get_user_by_id(db, user_id)
        
        return bool(
            user and 
            user.is_active and 
            user.enabled and 
            user.especialidad and 
            user.colegiatura
        )