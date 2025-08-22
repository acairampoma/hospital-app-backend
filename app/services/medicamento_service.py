from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from app.models.catalogos import MedicamentoVademecum
from app.schemas.catalogos import (
    MedicamentoCreate, MedicamentoUpdate
)
from app.core.exceptions import NotFoundError, ValidationException, BusinessRuleException
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class MedicamentoService:
    """💊 Servicio de Medicamentos Vademécum - Compatible con MedicamentoController Java"""
    
    # ===== CONSULTAS PRINCIPALES =====
    
    @staticmethod
    async def obtener_medicamento_por_id(db: AsyncSession, medicamento_id: int) -> Optional[MedicamentoVademecum]:
        """Obtener medicamento por ID"""
        result = await db.execute(
            select(MedicamentoVademecum).where(MedicamentoVademecum.id == medicamento_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_medicamento_por_codigo(db: AsyncSession, codigo: str) -> Optional[MedicamentoVademecum]:
        """Obtener medicamento por código"""
        result = await db.execute(
            select(MedicamentoVademecum).where(MedicamentoVademecum.codigo == codigo.upper())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_medicamentos_paginado(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        categoria: Optional[str] = None,
        forma_farmaceutica: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Obtener medicamentos con paginación y filtros"""
        
        query = select(MedicamentoVademecum)
        
        # Aplicar filtros
        filters = []
        if search:
            search_filter = or_(
                MedicamentoVademecum.nombre_comercial.ilike(f"%{search}%"),
                MedicamentoVademecum.nombre_generico.ilike(f"%{search}%"),
                MedicamentoVademecum.principio_activo.ilike(f"%{search}%"),
                MedicamentoVademecum.codigo.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if categoria:
            filters.append(MedicamentoVademecum.categoria_terapeutica == categoria)
        
        if forma_farmaceutica:
            filters.append(MedicamentoVademecum.forma_farmaceutica == forma_farmaceutica)
        
        if activo is not None:
            filters.append(MedicamentoVademecum.activo == activo)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Contar total
        count_query = select(func.count()).select_from(MedicamentoVademecum)
        if filters:
            count_query = count_query.where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Aplicar paginación y ordenamiento
        offset = (page - 1) * size
        query = query.order_by(asc(MedicamentoVademecum.nombre_comercial)).offset(offset).limit(size)
        
        result = await db.execute(query)
        medicamentos = result.scalars().all()
        
        return {
            "medicamentos": medicamentos,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size
        }
    
    # ===== OPERACIONES CRUD =====
    
    @staticmethod
    async def crear_medicamento(
        db: AsyncSession,
        medicamento_data: MedicamentoCreate,
        usuario_id: int
    ) -> MedicamentoVademecum:
        """Crear nuevo medicamento en vademécum"""
        
        # Validar que no existe medicamento con el mismo código
        existing = await MedicamentoService.obtener_medicamento_por_codigo(db, medicamento_data.codigo)
        if existing:
            raise BusinessRuleException(f"Ya existe un medicamento con código: {medicamento_data.codigo}")
        
        # Crear medicamento
        db_medicamento = MedicamentoVademecum(
            codigo=medicamento_data.codigo.upper(),
            nombre_comercial=medicamento_data.nombre_comercial,
            nombre_generico=medicamento_data.nombre_generico,
            principio_activo=medicamento_data.principio_activo,
            concentracion=medicamento_data.concentracion,
            forma_farmaceutica=medicamento_data.forma_farmaceutica,
            presentacion=medicamento_data.presentacion,
            laboratorio=medicamento_data.laboratorio,
            codigo_atc=medicamento_data.codigo_atc,
            categoria_terapeutica=medicamento_data.categoria_terapeutica,
            requiere_receta=medicamento_data.requiere_receta,
            precio_referencial=medicamento_data.precio_referencial,
            observaciones=medicamento_data.observaciones,
            activo=medicamento_data.activo
        )
        
        db.add(db_medicamento)
        await db.commit()
        await db.refresh(db_medicamento)
        
        return db_medicamento
    
    @staticmethod
    async def actualizar_medicamento(
        db: AsyncSession,
        medicamento_id: int,
        medicamento_data: MedicamentoUpdate,
        usuario_id: int
    ) -> MedicamentoVademecum:
        """Actualizar medicamento existente"""
        
        medicamento = await MedicamentoService.obtener_medicamento_por_id(db, medicamento_id)
        if not medicamento:
            raise NotFoundError(f"Medicamento no encontrado con ID: {medicamento_id}")
        
        # Validar código único si se está cambiando
        if medicamento_data.codigo and medicamento_data.codigo.upper() != medicamento.codigo:
            existing = await MedicamentoService.obtener_medicamento_por_codigo(db, medicamento_data.codigo)
            if existing:
                raise BusinessRuleException(f"Ya existe un medicamento con código: {medicamento_data.codigo}")
        
        # Actualizar campos
        update_data = medicamento_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "codigo" and value:
                value = value.upper()
            setattr(medicamento, field, value)
        
        await db.commit()
        await db.refresh(medicamento)
        
        return medicamento
    
    @staticmethod
    async def eliminar_medicamento(db: AsyncSession, medicamento_id: int, usuario_id: int) -> bool:
        """Eliminar medicamento (desactivar)"""
        
        medicamento = await MedicamentoService.obtener_medicamento_por_id(db, medicamento_id)
        if not medicamento:
            raise NotFoundError(f"Medicamento no encontrado con ID: {medicamento_id}")
        
        # Soft delete - solo desactivar
        medicamento.activo = False
        
        await db.commit()
        
        return True
    
    # ===== BÚSQUEDAS ESPECÍFICAS =====
    
    @staticmethod
    async def buscar_medicamentos(
        db: AsyncSession,
        busqueda: str,
        categoria: Optional[str] = None,
        forma_farmaceutica: Optional[str] = None,
        limit: int = 20
    ) -> List[MedicamentoVademecum]:
        """Buscar medicamentos por múltiples criterios"""
        
        query = select(MedicamentoVademecum).where(MedicamentoVademecum.activo == True)
        
        # Filtro de búsqueda principal
        search_filters = [
            MedicamentoVademecum.nombre_comercial.ilike(f"%{busqueda}%"),
            MedicamentoVademecum.nombre_generico.ilike(f"%{busqueda}%"),
            MedicamentoVademecum.principio_activo.ilike(f"%{busqueda}%"),
            MedicamentoVademecum.codigo.ilike(f"%{busqueda}%")
        ]
        
        query = query.where(or_(*search_filters))
        
        # Filtros adicionales
        if categoria:
            query = query.where(MedicamentoVademecum.categoria_terapeutica == categoria)
        
        if forma_farmaceutica:
            query = query.where(MedicamentoVademecum.forma_farmaceutica == forma_farmaceutica)
        
        # Ordenar por relevancia (nombre comercial primero)
        query = query.order_by(asc(MedicamentoVademecum.nombre_comercial)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def buscar_por_principio_activo(
        db: AsyncSession,
        principio_activo: str,
        limit: int = 10
    ) -> List[MedicamentoVademecum]:
        """Buscar medicamentos por principio activo"""
        
        result = await db.execute(
            select(MedicamentoVademecum)
            .where(and_(
                MedicamentoVademecum.principio_activo.ilike(f"%{principio_activo}%"),
                MedicamentoVademecum.activo == True
            ))
            .order_by(asc(MedicamentoVademecum.nombre_comercial))
            .limit(limit)
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def buscar_por_laboratorio(
        db: AsyncSession,
        laboratorio: str,
        limit: int = 50
    ) -> List[MedicamentoVademecum]:
        """Buscar medicamentos por laboratorio"""
        
        result = await db.execute(
            select(MedicamentoVademecum)
            .where(and_(
                MedicamentoVademecum.laboratorio.ilike(f"%{laboratorio}%"),
                MedicamentoVademecum.activo == True
            ))
            .order_by(asc(MedicamentoVademecum.nombre_comercial))
            .limit(limit)
        )
        
        return result.scalars().all()
    
    # ===== CATÁLOGOS Y LISTAS =====
    
    @staticmethod
    async def obtener_categorias_terapeuticas(db: AsyncSession) -> List[Dict[str, Any]]:
        """Obtener lista de categorías terapéuticas"""
        
        result = await db.execute(
            select(
                MedicamentoVademecum.categoria_terapeutica,
                func.count(MedicamentoVademecum.id).label('total')
            )
            .where(and_(
                MedicamentoVademecum.categoria_terapeutica.isnot(None),
                MedicamentoVademecum.activo == True
            ))
            .group_by(MedicamentoVademecum.categoria_terapeutica)
            .order_by(asc(MedicamentoVademecum.categoria_terapeutica))
        )
        
        return [
            {"categoria": categoria, "total_medicamentos": total}
            for categoria, total in result.all()
        ]
    
    @staticmethod
    async def obtener_formas_farmaceuticas(db: AsyncSession) -> List[Dict[str, Any]]:
        """Obtener lista de formas farmacéuticas"""
        
        result = await db.execute(
            select(
                MedicamentoVademecum.forma_farmaceutica,
                func.count(MedicamentoVademecum.id).label('total')
            )
            .where(and_(
                MedicamentoVademecum.forma_farmaceutica.isnot(None),
                MedicamentoVademecum.activo == True
            ))
            .group_by(MedicamentoVademecum.forma_farmaceutica)
            .order_by(asc(MedicamentoVademecum.forma_farmaceutica))
        )
        
        return [
            {"forma_farmaceutica": forma, "total_medicamentos": total}
            for forma, total in result.all()
        ]
    
    @staticmethod
    async def obtener_laboratorios(db: AsyncSession) -> List[Dict[str, Any]]:
        """Obtener lista de laboratorios"""
        
        result = await db.execute(
            select(
                MedicamentoVademecum.laboratorio,
                func.count(MedicamentoVademecum.id).label('total')
            )
            .where(and_(
                MedicamentoVademecum.laboratorio.isnot(None),
                MedicamentoVademecum.activo == True
            ))
            .group_by(MedicamentoVademecum.laboratorio)
            .order_by(asc(MedicamentoVademecum.laboratorio))
        )
        
        return [
            {"laboratorio": laboratorio, "total_medicamentos": total}
            for laboratorio, total in result.all()
        ]
    
    # ===== ESTADÍSTICAS =====
    
    @staticmethod
    async def obtener_estadisticas_generales(db: AsyncSession) -> Dict[str, Any]:
        """Obtener estadísticas generales de medicamentos"""
        
        # Total de medicamentos
        total_result = await db.execute(
            select(func.count(MedicamentoVademecum.id))
        )
        total_medicamentos = total_result.scalar()
        
        # Medicamentos activos
        activos_result = await db.execute(
            select(func.count(MedicamentoVademecum.id))
            .where(MedicamentoVademecum.activo == True)
        )
        activos = activos_result.scalar()
        
        # Que requieren receta
        receta_result = await db.execute(
            select(func.count(MedicamentoVademecum.id))
            .where(and_(
                MedicamentoVademecum.requiere_receta == True,
                MedicamentoVademecum.activo == True
            ))
        )
        requieren_receta = receta_result.scalar()
        
        # Precio promedio
        precio_result = await db.execute(
            select(func.avg(MedicamentoVademecum.precio_referencial))
            .where(and_(
                MedicamentoVademecum.precio_referencial.isnot(None),
                MedicamentoVademecum.activo == True
            ))
        )
        precio_promedio = precio_result.scalar()
        
        # Top 5 categorías
        categorias_result = await db.execute(
            select(
                MedicamentoVademecum.categoria_terapeutica,
                func.count(MedicamentoVademecum.id).label('total')
            )
            .where(and_(
                MedicamentoVademecum.categoria_terapeutica.isnot(None),
                MedicamentoVademecum.activo == True
            ))
            .group_by(MedicamentoVademecum.categoria_terapeutica)
            .order_by(desc('total'))
            .limit(5)
        )
        
        top_categorias = [
            {"categoria": cat, "total": total}
            for cat, total in categorias_result.all()
        ]
        
        return {
            "total_medicamentos": total_medicamentos,
            "medicamentos_activos": activos,
            "medicamentos_inactivos": total_medicamentos - activos,
            "requieren_receta": requieren_receta,
            "venta_libre": activos - requieren_receta,
            "precio_promedio": float(precio_promedio) if precio_promedio else 0.0,
            "top_categorias": top_categorias
        }
    
    # ===== VALIDACIONES =====
    
    @staticmethod
    async def validar_medicamento_disponible(
        db: AsyncSession,
        medicamento_id: Optional[int] = None,
        codigo: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validar si un medicamento está disponible"""
        
        if medicamento_id:
            medicamento = await MedicamentoService.obtener_medicamento_por_id(db, medicamento_id)
        elif codigo:
            medicamento = await MedicamentoService.obtener_medicamento_por_codigo(db, codigo)
        else:
            raise ValidationException("Se requiere ID o código del medicamento")
        
        if not medicamento:
            return {
                "disponible": False,
                "motivo": "Medicamento no encontrado",
                "medicamento": None
            }
        
        if not medicamento.activo:
            return {
                "disponible": False,
                "motivo": "Medicamento inactivo",
                "medicamento": {
                    "id": medicamento.id,
                    "codigo": medicamento.codigo,
                    "nombre": medicamento.nombre_comercial
                }
            }
        
        return {
            "disponible": True,
            "motivo": "Medicamento disponible",
            "medicamento": {
                "id": medicamento.id,
                "codigo": medicamento.codigo,
                "nombre": medicamento.nombre_comercial,
                "requiere_receta": medicamento.requiere_receta,
                "precio": float(medicamento.precio_referencial) if medicamento.precio_referencial else None
            }
        }