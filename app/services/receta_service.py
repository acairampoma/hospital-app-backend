from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from app.models.receta import RecetaCab, RecetaDet
from app.models.catalogos import MedicamentoVademecum
from app.models.user import User
from app.schemas.receta import (
    RecetaCabCreate, RecetaCabUpdate, RecetaCompletaResponse,
    RecetaDetCreate, RecetaDetUpdate
)
from app.core.exceptions import NotFoundError, ValidationException, BusinessRuleException
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

class RecetaService:
    """💊 Servicio de Recetas - Compatible con RecetaController Java"""
    
    # ===== CONSULTAS PRINCIPALES =====
    
    @staticmethod
    async def obtener_recetas_por_origen(db: AsyncSession, tipo_origen: str, origen_id: int) -> List[RecetaCab]:
        """Obtener recetas por tipo de origen y origen ID"""
        result = await db.execute(
            select(RecetaCab)
            .options(selectinload(RecetaCab.detalles))
            .where(and_(
                RecetaCab.tipo_origen == tipo_origen,
                RecetaCab.origen_id == origen_id
            ))
            .order_by(desc(RecetaCab.created_at))
        )
        return result.scalars().all()
    
    @staticmethod
    async def obtener_receta_por_id(db: AsyncSession, receta_id: int) -> Optional[RecetaCab]:
        """Obtener receta por ID con detalles"""
        result = await db.execute(
            select(RecetaCab)
            .options(selectinload(RecetaCab.detalles))
            .where(RecetaCab.id == receta_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_receta_por_numero(db: AsyncSession, numero_receta: str) -> Optional[RecetaCab]:
        """Obtener receta por número"""
        result = await db.execute(
            select(RecetaCab)
            .options(selectinload(RecetaCab.detalles))
            .where(RecetaCab.numero_receta == numero_receta)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_recetas_por_paciente(db: AsyncSession, paciente_id: int) -> List[RecetaCab]:
        """Obtener todas las recetas de un paciente"""
        result = await db.execute(
            select(RecetaCab)
            .options(selectinload(RecetaCab.detalles))
            .where(RecetaCab.paciente_id == paciente_id)
            .order_by(desc(RecetaCab.created_at))
        )
        return result.scalars().all()
    
    # ===== OPERACIONES CRUD =====
    
    @staticmethod
    async def crear_receta(db: AsyncSession, receta_data: RecetaCabCreate, medico_id: int) -> RecetaCab:
        """Crear nueva receta con transacción atómica"""
        
        # Validar reglas de negocio
        await RecetaService._validar_creacion_receta(db, receta_data, medico_id)
        
        # Obtener información del médico
        medico_info = await RecetaService._obtener_info_medico(db, medico_id)
        
        # Generar número de receta único
        numero_receta = await RecetaService._generar_numero_receta(db)
        
        # Calcular fecha de vencimiento (30 días por defecto)
        fecha_vencimiento = receta_data.fecha_vencimiento or (datetime.utcnow() + timedelta(days=30))
        
        # Crear cabecera de receta
        db_receta = RecetaCab(
            numero_receta=numero_receta,
            tipo_origen=receta_data.tipo_origen,
            origen_id=receta_data.origen_id,
            paciente_id=receta_data.paciente_id,
            paciente_nombre=receta_data.paciente_nombre,
            paciente_documento=receta_data.paciente_documento,
            diagnostico_principal=receta_data.diagnostico_principal,
            indicaciones_generales=receta_data.indicaciones_generales,
            fecha_vencimiento=fecha_vencimiento,
            creado_por=medico_id,
            medico_nombre=medico_info["nombre_completo"],
            medico_colegiatura=medico_info["colegiatura"],
            estado="01"  # Activa
        )
        
        db.add(db_receta)
        await db.flush()  # Para obtener el ID
        
        # Crear detalles de medicamentos
        for detalle_data in receta_data.detalles:
            await RecetaService._crear_detalle_receta(db, db_receta.id, detalle_data)
        
        # Auto-firma si cumple condiciones
        if await RecetaService._debe_auto_firmarse(db, db_receta):
            db_receta.firmada = True
            db_receta.fecha_firma = datetime.utcnow()
            db_receta.hash_firma = RecetaService._generar_hash_firma(db_receta)
        
        await db.commit()
        await db.refresh(db_receta)
        
        # Cargar detalles
        result = await db.execute(
            select(RecetaCab)
            .options(selectinload(RecetaCab.detalles))
            .where(RecetaCab.id == db_receta.id)
        )
        return result.scalar_one()
    
    @staticmethod
    async def actualizar_receta(db: AsyncSession, receta_id: int, receta_data: RecetaCabUpdate, medico_id: int) -> RecetaCab:
        """Actualizar receta existente"""
        
        # Obtener receta
        receta = await RecetaService.obtener_receta_por_id(db, receta_id)
        if not receta:
            raise NotFoundError(f"Receta no encontrada con ID: {receta_id}")
        
        # Validar permisos de modificación
        await RecetaService._validar_modificacion_receta(db, receta, medico_id)
        
        # Actualizar campos
        update_data = receta_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(receta, field, value)
        
        await db.commit()
        await db.refresh(receta)
        
        return receta
    
    @staticmethod
    async def cambiar_estado_receta(db: AsyncSession, receta_id: int, nuevo_estado: str, medico_id: int) -> RecetaCab:
        """Cambiar estado de receta"""
        
        receta = await RecetaService.obtener_receta_por_id(db, receta_id)
        if not receta:
            raise NotFoundError(f"Receta no encontrada con ID: {receta_id}")
        
        # Validar transición de estado
        await RecetaService._validar_cambio_estado(db, receta, nuevo_estado, medico_id)
        
        receta.estado = nuevo_estado
        
        # Si se anula, limpiar firma
        if nuevo_estado == "04":  # Anulada
            receta.firmada = False
            receta.fecha_firma = None
            receta.hash_firma = None
        
        await db.commit()
        await db.refresh(receta)
        
        return receta
    
    # ===== ESTADÍSTICAS =====
    
    @staticmethod
    async def obtener_estadisticas_medico(db: AsyncSession, medico_id: int) -> dict:
        """Obtener estadísticas de recetas por médico"""
        
        # Total de recetas
        total_result = await db.execute(
            select(func.count(RecetaCab.id)).where(RecetaCab.creado_por == medico_id)
        )
        total_recetas = total_result.scalar()
        
        # Recetas por estado
        estados_result = await db.execute(
            select(RecetaCab.estado, func.count(RecetaCab.id))
            .where(RecetaCab.creado_por == medico_id)
            .group_by(RecetaCab.estado)
        )
        
        recetas_por_estado = {}
        for estado, count in estados_result.all():
            estado_desc = {"01": "Activas", "02": "Despachadas", "03": "Vencidas", "04": "Anuladas"}
            recetas_por_estado[estado_desc.get(estado, estado)] = count
        
        # Medicamentos más prescritos
        medicamentos_result = await db.execute(
            select(RecetaDet.medicamento_nombre, func.count(RecetaDet.id).label('total'))
            .join(RecetaCab, RecetaDet.receta_id == RecetaCab.id)
            .where(RecetaCab.creado_por == medico_id)
            .group_by(RecetaDet.medicamento_nombre)
            .order_by(desc('total'))
            .limit(10)
        )
        
        medicamentos_mas_prescritos = [
            {"medicamento": med, "total": total}
            for med, total in medicamentos_result.all()
        ]
        
        return {
            "medico_id": medico_id,
            "total_recetas": total_recetas,
            "recetas_por_estado": recetas_por_estado,
            "medicamentos_mas_prescritos": medicamentos_mas_prescritos
        }
    
    @staticmethod
    async def obtener_medicamentos_mas_prescritos(db: AsyncSession, limite: int = 10) -> List[dict]:
        """Obtener medicamentos más prescritos globalmente"""
        
        result = await db.execute(
            select(RecetaDet.medicamento_nombre, func.count(RecetaDet.id).label('total'))
            .group_by(RecetaDet.medicamento_nombre)
            .order_by(desc('total'))
            .limit(limite)
        )
        
        return [
            {"medicamento": med, "total_prescripciones": total}
            for med, total in result.all()
        ]
    
    # ===== MÉTODOS PRIVADOS =====
    
    @staticmethod
    async def _validar_creacion_receta(db: AsyncSession, receta_data: RecetaCabCreate, medico_id: int):
        """Validar reglas de negocio para creación"""
        
        # Validar médico
        result = await db.execute(select(User).where(User.id == medico_id))
        medico = result.scalar_one_or_none()
        
        if not medico or not medico.especialidad or not medico.colegiatura:
            raise BusinessRuleException("Solo médicos pueden crear recetas")
        
        # Validar no receta duplicada mismo día
        hoy = datetime.utcnow().date()
        result = await db.execute(
            select(func.count(RecetaCab.id))
            .where(and_(
                RecetaCab.tipo_origen == receta_data.tipo_origen,
                RecetaCab.origen_id == receta_data.origen_id,
                RecetaCab.paciente_id == receta_data.paciente_id,
                func.date(RecetaCab.created_at) == hoy,
                RecetaCab.estado.in_(["01", "02"])  # Activa o Despachada
            ))
        )
        
        if result.scalar() > 0:
            raise BusinessRuleException("Ya existe una receta activa para este paciente hoy")
        
        # Validar cantidad de medicamentos (máximo 10)
        if len(receta_data.detalles) > 10:
            raise BusinessRuleException("Máximo 10 medicamentos por receta")
        
        if len(receta_data.detalles) == 0:
            raise BusinessRuleException("La receta debe tener al menos un medicamento")
    
    @staticmethod
    async def _crear_detalle_receta(db: AsyncSession, receta_id: int, detalle_data: RecetaDetCreate):
        """Crear detalle de receta"""
        
        # Buscar medicamento en vademécum si se proporciona código
        medicamento_info = {}
        if detalle_data.medicamento_codigo and not detalle_data.medicamento_id:
            result = await db.execute(
                select(MedicamentoVademecum)
                .where(MedicamentoVademecum.codigo == detalle_data.medicamento_codigo)
            )
            medicamento = result.scalar_one_or_none()
            if medicamento:
                medicamento_info = {
                    "medicamento_id": medicamento.id,
                    "medicamento_nombre": medicamento.nombre_comercial
                }
        
        db_detalle = RecetaDet(
            receta_id=receta_id,
            medicamento_id=medicamento_info.get("medicamento_id") or detalle_data.medicamento_id,
            medicamento_codigo=detalle_data.medicamento_codigo,
            medicamento_nombre=medicamento_info.get("medicamento_nombre") or detalle_data.medicamento_nombre,
            cantidad=detalle_data.cantidad,
            unidad=detalle_data.unidad,
            posologia=detalle_data.posologia,
            duracion_tratamiento=detalle_data.duracion_tratamiento,
            observaciones=detalle_data.observaciones,
            sustituible=detalle_data.sustituible
        )
        
        db.add(db_detalle)
    
    @staticmethod
    async def _obtener_info_medico(db: AsyncSession, medico_id: int) -> dict:
        """Obtener información del médico"""
        result = await db.execute(select(User).where(User.id == medico_id))
        medico = result.scalar_one_or_none()
        
        if not medico:
            raise NotFoundError(f"Médico no encontrado con ID: {medico_id}")
        
        return {
            "nombre_completo": medico.nombre_completo or medico.username,
            "especialidad": medico.especialidad,
            "colegiatura": medico.colegiatura
        }
    
    @staticmethod
    async def _generar_numero_receta(db: AsyncSession) -> str:
        """Generar número único de receta"""
        fecha_actual = datetime.utcnow().strftime("%Y%m%d")
        
        # Contar recetas del día
        result = await db.execute(
            select(func.count(RecetaCab.id))
            .where(func.date(RecetaCab.created_at) == datetime.utcnow().date())
        )
        secuencial = result.scalar() + 1
        
        return f"RX{fecha_actual}{secuencial:04d}"
    
    @staticmethod
    async def _validar_modificacion_receta(db: AsyncSession, receta: RecetaCab, medico_id: int):
        """Validar que se puede modificar la receta"""
        
        # Solo el médico creador puede modificar
        if receta.creado_por != medico_id:
            raise BusinessRuleException("Solo el médico creador puede modificar la receta")
        
        # Solo recetas activas
        if receta.estado != "01":
            raise BusinessRuleException("Solo se pueden modificar recetas activas")
        
        # Solo hasta 24h antes del vencimiento
        if receta.fecha_vencimiento:
            limite_modificacion = receta.fecha_vencimiento - timedelta(days=1)
            if datetime.utcnow() > limite_modificacion:
                raise BusinessRuleException("No se puede modificar la receta tan cerca del vencimiento")
    
    @staticmethod
    async def _validar_cambio_estado(db: AsyncSession, receta: RecetaCab, nuevo_estado: str, medico_id: int):
        """Validar cambio de estado de receta"""
        
        # Solo el médico creador puede cambiar estado
        if receta.creado_por != medico_id:
            raise BusinessRuleException("Solo el médico creador puede cambiar el estado")
        
        # Validar transiciones válidas
        transiciones_validas = {
            "01": ["02", "04"],  # Activa -> Despachada, Anulada
            "02": ["04"],        # Despachada -> Anulada
            "03": ["04"],        # Vencida -> Anulada
        }
        
        if nuevo_estado not in transiciones_validas.get(receta.estado, []):
            raise BusinessRuleException(f"Transición no válida de {receta.estado} a {nuevo_estado}")
    
    @staticmethod
    async def _debe_auto_firmarse(db: AsyncSession, receta: RecetaCab) -> bool:
        """Determinar si la receta debe auto-firmarse"""
        # Lógica de auto-firma (simplificada)
        return len(receta.detalles) <= 3  # Auto-firmar recetas simples
    
    @staticmethod
    def _generar_hash_firma(receta: RecetaCab) -> str:
        """Generar hash de firma digital"""
        data = f"{receta.numero_receta}:{receta.creado_por}:{datetime.utcnow().isoformat()}"
        return str(hash(data))  # Simplificado - en producción usar SHA256