from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct
from app.models.catalogos import Catalogo, MedicamentoVademecum
from app.schemas.catalogo import (
    CatalogoCreate, CatalogoUpdate, CatalogoResponse,
    MedicamentoCreate, MedicamentoUpdate, MedicamentoResponse,
    CatalogoSearchRequest, MedicamentoSearchRequest
)
from app.core.exceptions import NotFoundError, ValidationException
from typing import List, Optional

class CatalogoService:
    """🔍 Servicio de Catálogos - Compatible con CatalogosController Java"""
    
    # ===== BÚSQUEDAS GENERALES =====
    
    @staticmethod
    async def buscar_por_termino(db: AsyncSession, termino: str) -> List[Catalogo]:
        """Búsqueda general por término"""
        search_term = f"%{termino}%"
        
        result = await db.execute(
            select(Catalogo)
            .where(and_(
                Catalogo.activo == True,
                or_(
                    Catalogo.codigo.ilike(search_term),
                    Catalogo.descripcion.ilike(search_term),
                    Catalogo.categoria.ilike(search_term)
                )
            ))
            .order_by(Catalogo.codigo)
            .limit(50)
        )
        return result.scalars().all()
    
    @staticmethod
    async def buscar_por_codigo_exacto(db: AsyncSession, codigo: str) -> Optional[Catalogo]:
        """Búsqueda por código exacto"""
        result = await db.execute(
            select(Catalogo)
            .where(and_(
                Catalogo.codigo == codigo.upper(),
                Catalogo.activo == True
            ))
        )
        return result.scalar_one_or_none()
    
    # ===== BÚSQUEDAS POR TIPO =====
    
    @staticmethod
    async def buscar_examenes(db: AsyncSession, termino: str) -> List[Catalogo]:
        """Buscar exámenes médicos"""
        search_term = f"%{termino}%"
        
        result = await db.execute(
            select(Catalogo)
            .where(and_(
                Catalogo.tabla_origen == "EXA",
                Catalogo.activo == True,
                or_(
                    Catalogo.descripcion.ilike(search_term),
                    Catalogo.codigo.ilike(search_term)
                )
            ))
            .order_by(Catalogo.descripcion)
        )
        return result.scalars().all()
    
    @staticmethod
    async def buscar_medicamentos_catalogo(db: AsyncSession, termino: str) -> List[Catalogo]:
        """Buscar medicamentos en catálogos generales"""
        search_term = f"%{termino}%"
        
        result = await db.execute(
            select(Catalogo)
            .where(and_(
                Catalogo.tabla_origen == "MED",
                Catalogo.activo == True,
                or_(
                    Catalogo.descripcion.ilike(search_term),
                    Catalogo.codigo.ilike(search_term)
                )
            ))
            .order_by(Catalogo.descripcion)
        )
        return result.scalars().all()
    
    @staticmethod
    async def buscar_catalogos_maestros(db: AsyncSession, termino: str) -> List[Catalogo]:
        """Buscar en catálogos maestros"""
        search_term = f"%{termino}%"
        
        result = await db.execute(
            select(Catalogo)
            .where(and_(
                Catalogo.tabla_origen == "CAT",
                Catalogo.activo == True,
                or_(
                    Catalogo.descripcion.ilike(search_term),
                    Catalogo.codigo.ilike(search_term)
                )
            ))
            .order_by(Catalogo.categoria, Catalogo.descripcion)
        )
        return result.scalars().all()
    
    # ===== BÚSQUEDAS POR CATEGORÍA =====
    
    @staticmethod
    async def buscar_por_categoria(db: AsyncSession, categoria: str) -> List[Catalogo]:
        """Buscar por categoría"""
        result = await db.execute(
            select(Catalogo)
            .where(and_(
                Catalogo.categoria.ilike(f"%{categoria}%"),
                Catalogo.activo == True
            ))
            .order_by(Catalogo.descripcion)
        )
        return result.scalars().all()
    
    @staticmethod
    async def buscar_en_tabla_especifica(db: AsyncSession, tabla_codigo: str, termino: Optional[str] = None) -> List[Catalogo]:
        """Buscar en tabla específica"""
        query = select(Catalogo).where(and_(
            Catalogo.tabla_origen == tabla_codigo.upper(),
            Catalogo.activo == True
        ))
        
        if termino:
            search_term = f"%{termino}%"
            query = query.where(or_(
                Catalogo.descripcion.ilike(search_term),
                Catalogo.codigo.ilike(search_term)
            ))
        
        query = query.order_by(Catalogo.codigo)
        result = await db.execute(query)
        return result.scalars().all()
    
    # ===== LISTADOS COMPLETOS =====
    
    @staticmethod
    async def obtener_todos_los_examenes(db: AsyncSession) -> List[Catalogo]:
        """Obtener todos los exámenes"""
        result = await db.execute(
            select(Catalogo)
            .where(and_(
                Catalogo.tabla_origen == "EXA",
                Catalogo.activo == True
            ))
            .order_by(Catalogo.categoria, Catalogo.descripcion)
        )
        return result.scalars().all()
    
    @staticmethod
    async def obtener_todos_los_medicamentos_catalogo(db: AsyncSession) -> List[Catalogo]:
        """Obtener todos los medicamentos del catálogo"""
        result = await db.execute(
            select(Catalogo)
            .where(and_(
                Catalogo.tabla_origen == "MED",
                Catalogo.activo == True
            ))
            .order_by(Catalogo.descripcion)
        )
        return result.scalars().all()
    
    @staticmethod
    async def obtener_todas_las_categorias(db: AsyncSession) -> List[str]:
        """Obtener todas las categorías disponibles"""
        result = await db.execute(
            select(distinct(Catalogo.categoria))
            .where(and_(
                Catalogo.categoria.isnot(None),
                Catalogo.activo == True
            ))
            .order_by(Catalogo.categoria)
        )
        return [cat for cat in result.scalars().all() if cat]
    
    @staticmethod
    async def obtener_tipos_de_tabla(db: AsyncSession) -> List[str]:
        """Obtener tipos de tabla disponibles"""
        result = await db.execute(
            select(distinct(Catalogo.tabla_origen))
            .where(and_(
                Catalogo.tabla_origen.isnot(None),
                Catalogo.activo == True
            ))
            .order_by(Catalogo.tabla_origen)
        )
        return [tipo for tipo in result.scalars().all() if tipo]
    
    # ===== CRUD CATÁLOGOS =====
    
    @staticmethod
    async def crear_catalogo(db: AsyncSession, catalogo_data: CatalogoCreate) -> Catalogo:
        """Crear nuevo catálogo"""
        # Verificar código único
        existing = await CatalogoService.buscar_por_codigo_exacto(db, catalogo_data.codigo)
        if existing:
            raise ValidationException(f"Ya existe un catálogo con código: {catalogo_data.codigo}")
        
        db_catalogo = Catalogo(**catalogo_data.model_dump())
        db_catalogo.codigo = db_catalogo.codigo.upper()
        
        db.add(db_catalogo)
        await db.commit()
        await db.refresh(db_catalogo)
        
        return db_catalogo
    
    @staticmethod
    async def actualizar_catalogo(db: AsyncSession, catalogo_id: int, catalogo_data: CatalogoUpdate) -> Catalogo:
        """Actualizar catálogo"""
        result = await db.execute(select(Catalogo).where(Catalogo.id == catalogo_id))
        catalogo = result.scalar_one_or_none()
        
        if not catalogo:
            raise NotFoundError(f"Catálogo no encontrado con ID: {catalogo_id}")
        
        # Actualizar campos
        update_data = catalogo_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(catalogo, field, value)
        
        await db.commit()
        await db.refresh(catalogo)
        
        return catalogo


# ===== MEDICAMENTO VADEMÉCUM SERVICE =====

class MedicamentoService:
    """💊 Servicio de Medicamentos Vademécum"""
    
    @staticmethod
    async def buscar_medicamentos(db: AsyncSession, termino: Optional[str] = None, categoria: Optional[str] = None) -> List[MedicamentoVademecum]:
        """Buscar medicamentos en vademécum"""
        query = select(MedicamentoVademecum).where(MedicamentoVademecum.activo == True)
        
        if termino:
            search_term = f"%{termino}%"
            query = query.where(or_(
                MedicamentoVademecum.nombre_comercial.ilike(search_term),
                MedicamentoVademecum.nombre_generico.ilike(search_term),
                MedicamentoVademecum.codigo.ilike(search_term)
            ))
        
        if categoria:
            query = query.where(MedicamentoVademecum.categoria_terapeutica.ilike(f"%{categoria}%"))
        
        query = query.order_by(MedicamentoVademecum.nombre_comercial).limit(50)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def obtener_medicamento_por_id(db: AsyncSession, medicamento_id: int) -> Optional[MedicamentoVademecum]:
        """Obtener medicamento por ID"""
        result = await db.execute(select(MedicamentoVademecum).where(MedicamentoVademecum.id == medicamento_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_medicamento_por_codigo(db: AsyncSession, codigo: str) -> Optional[MedicamentoVademecum]:
        """Obtener medicamento por código"""
        result = await db.execute(
            select(MedicamentoVademecum)
            .where(and_(
                MedicamentoVademecum.codigo == codigo.upper(),
                MedicamentoVademecum.activo == True
            ))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_categorias_medicamentos(db: AsyncSession) -> List[str]:
        """Obtener categorías terapéuticas"""
        result = await db.execute(
            select(distinct(MedicamentoVademecum.categoria_terapeutica))
            .where(and_(
                MedicamentoVademecum.categoria_terapeutica.isnot(None),
                MedicamentoVademecum.activo == True
            ))
            .order_by(MedicamentoVademecum.categoria_terapeutica)
        )
        return [cat for cat in result.scalars().all() if cat]
    
    @staticmethod
    async def crear_medicamento(db: AsyncSession, medicamento_data: MedicamentoCreate) -> MedicamentoVademecum:
        """Crear nuevo medicamento"""
        # Verificar código único
        existing = await MedicamentoService.obtener_medicamento_por_codigo(db, medicamento_data.codigo)
        if existing:
            raise ValidationException(f"Ya existe un medicamento con código: {medicamento_data.codigo}")
        
        db_medicamento = MedicamentoVademecum(**medicamento_data.model_dump())
        db_medicamento.codigo = db_medicamento.codigo.upper()
        
        db.add(db_medicamento)
        await db.commit()
        await db.refresh(db_medicamento)
        
        return db_medicamento
    
    @staticmethod
    async def actualizar_medicamento(db: AsyncSession, medicamento_id: int, medicamento_data: MedicamentoUpdate) -> MedicamentoVademecum:
        """Actualizar medicamento"""
        medicamento = await MedicamentoService.obtener_medicamento_por_id(db, medicamento_id)
        
        if not medicamento:
            raise NotFoundError(f"Medicamento no encontrado con ID: {medicamento_id}")
        
        # Actualizar campos
        update_data = medicamento_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(medicamento, field, value)
        
        await db.commit()
        await db.refresh(medicamento)
        
        return medicamento