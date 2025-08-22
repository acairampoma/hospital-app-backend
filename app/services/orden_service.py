from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from app.models.orden import OrdenCab, OrdenDet
from app.models.user import User
from app.schemas.orden import (
    OrdenCabCreate, OrdenCabUpdate, OrdenDetCreate, OrdenDetUpdate
)
from app.core.exceptions import NotFoundError, ValidationException, BusinessRuleException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

class OrdenService:
    """📋 Servicio de Órdenes Médicas - Compatible con OrdenController Java"""
    
    # ===== CONSULTAS PRINCIPALES =====
    
    @staticmethod
    async def obtener_orden_por_id(db: AsyncSession, orden_id: int) -> Optional[OrdenCab]:
        """Obtener orden por ID con detalles"""
        result = await db.execute(
            select(OrdenCab)
            .options(selectinload(OrdenCab.detalles))
            .where(OrdenCab.id == orden_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_orden_por_numero(db: AsyncSession, numero_orden: str) -> Optional[OrdenCab]:
        """Obtener orden por número"""
        result = await db.execute(
            select(OrdenCab)
            .options(selectinload(OrdenCab.detalles))
            .where(OrdenCab.numero_orden == numero_orden)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_ordenes_por_origen(db: AsyncSession, tipo_origen: str, origen_id: int) -> List[OrdenCab]:
        """Obtener órdenes por tipo de origen y origen ID"""
        result = await db.execute(
            select(OrdenCab)
            .options(selectinload(OrdenCab.detalles))
            .where(and_(
                OrdenCab.tipo_origen == tipo_origen,
                OrdenCab.origen_id == origen_id
            ))
            .order_by(desc(OrdenCab.created_at))
        )
        return result.scalars().all()
    
    @staticmethod
    async def obtener_ordenes_por_paciente(
        db: AsyncSession, 
        paciente_id: int, 
        tipo_orden: Optional[str] = None,
        limit: int = 50
    ) -> List[OrdenCab]:
        """Obtener órdenes de un paciente con filtros opcionales"""
        query = select(OrdenCab).options(selectinload(OrdenCab.detalles))
        query = query.where(OrdenCab.paciente_id == paciente_id)
        
        if tipo_orden:
            # Filtrar por tipo en los detalles
            query = query.join(OrdenDet).where(OrdenDet.tipo_orden == tipo_orden)
        
        query = query.order_by(desc(OrdenCab.created_at)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    # ===== OPERACIONES CRUD =====
    
    @staticmethod
    async def crear_orden(db: AsyncSession, orden_data: OrdenCabCreate, medico_id: int) -> OrdenCab:
        """Crear nueva orden médica con transacción atómica"""
        
        # Validar reglas de negocio
        await OrdenService._validar_creacion_orden(db, orden_data, medico_id)
        
        # Obtener información del médico
        medico_info = await OrdenService._obtener_info_medico(db, medico_id)
        
        # Generar número de orden único
        numero_orden = await OrdenService._generar_numero_orden(db, orden_data.detalles[0].tipo_orden if orden_data.detalles else "GEN")
        
        # Crear cabecera de orden
        db_orden = OrdenCab(
            numero_orden=numero_orden,
            tipo_origen=orden_data.tipo_origen,
            origen_id=orden_data.origen_id,
            paciente_id=orden_data.paciente_id,
            paciente_nombre=orden_data.paciente_nombre,
            paciente_documento=orden_data.paciente_documento,
            diagnostico_principal=orden_data.diagnostico_principal,
            justificacion_clinica=orden_data.justificacion_clinica,
            observaciones_generales=orden_data.observaciones_generales,
            fecha_solicitud=orden_data.fecha_solicitud or datetime.utcnow(),
            creado_por=medico_id,
            medico_nombre=medico_info["nombre_completo"],
            medico_especialidad=medico_info["especialidad"],
            medico_colegiatura=medico_info["colegiatura"],
            estado="01",  # Pendiente
            prioridad=orden_data.prioridad or "RUTINA"
        )
        
        db.add(db_orden)
        await db.flush()  # Para obtener el ID
        
        # Crear detalles de exámenes
        for detalle_data in orden_data.detalles:
            await OrdenService._crear_detalle_orden(db, db_orden.id, detalle_data)
        
        await db.commit()
        await db.refresh(db_orden)
        
        # Cargar detalles
        result = await db.execute(
            select(OrdenCab)
            .options(selectinload(OrdenCab.detalles))
            .where(OrdenCab.id == db_orden.id)
        )
        return result.scalar_one()
    
    @staticmethod
    async def actualizar_orden(db: AsyncSession, orden_id: int, orden_data: OrdenCabUpdate, medico_id: int) -> OrdenCab:
        """Actualizar orden existente"""
        
        # Obtener orden
        orden = await OrdenService.obtener_orden_por_id(db, orden_id)
        if not orden:
            raise NotFoundError(f"Orden no encontrada con ID: {orden_id}")
        
        # Validar permisos de modificación
        await OrdenService._validar_modificacion_orden(db, orden, medico_id)
        
        # Actualizar campos
        update_data = orden_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != "detalles":  # Los detalles se manejan separadamente
                setattr(orden, field, value)
        
        await db.commit()
        await db.refresh(orden)
        
        return orden
    
    @staticmethod
    async def cambiar_estado_orden(db: AsyncSession, orden_id: int, nuevo_estado: str, medico_id: int) -> OrdenCab:
        """Cambiar estado de orden médica"""
        
        orden = await OrdenService.obtener_orden_por_id(db, orden_id)
        if not orden:
            raise NotFoundError(f"Orden no encontrada con ID: {orden_id}")
        
        # Validar transición de estado
        await OrdenService._validar_cambio_estado(db, orden, nuevo_estado, medico_id)
        
        orden.estado = nuevo_estado
        
        # Si se completa, actualizar fecha de finalización en detalles
        if nuevo_estado == "04":  # Completada
            for detalle in orden.detalles:
                detalle.estado = "COMPLETADO"
        
        await db.commit()
        await db.refresh(orden)
        
        return orden
    
    # ===== CONSULTAS PAGINADAS Y FILTRADAS =====
    
    @staticmethod
    async def obtener_ordenes_paginado(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        medico_id: Optional[int] = None,
        tipo_origen: Optional[str] = None,
        origen_id: Optional[int] = None,
        paciente_id: Optional[int] = None,
        estado: Optional[str] = None,
        prioridad: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtener órdenes con paginación y filtros"""
        
        query = select(OrdenCab).options(selectinload(OrdenCab.detalles))
        
        # Aplicar filtros
        filters = []
        if medico_id:
            filters.append(OrdenCab.creado_por == medico_id)
        if tipo_origen:
            filters.append(OrdenCab.tipo_origen == tipo_origen)
        if origen_id:
            filters.append(OrdenCab.origen_id == origen_id)
        if paciente_id:
            filters.append(OrdenCab.paciente_id == paciente_id)
        if estado:
            filters.append(OrdenCab.estado == estado)
        if prioridad:
            filters.append(OrdenCab.prioridad == prioridad)
        if fecha_desde:
            filters.append(OrdenCab.fecha_solicitud >= datetime.fromisoformat(fecha_desde))
        if fecha_hasta:
            filters.append(OrdenCab.fecha_solicitud <= datetime.fromisoformat(fecha_hasta))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Contar total
        count_query = select(func.count()).select_from(OrdenCab)
        if filters:
            count_query = count_query.where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Aplicar paginación
        offset = (page - 1) * size
        query = query.order_by(desc(OrdenCab.created_at)).offset(offset).limit(size)
        
        result = await db.execute(query)
        ordenes = result.scalars().unique().all()
        
        return {
            "ordenes": ordenes,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size
        }
    
    # ===== ESTADÍSTICAS =====
    
    @staticmethod
    async def obtener_estadisticas_medico(db: AsyncSession, medico_id: int) -> Dict[str, Any]:
        """Obtener estadísticas de órdenes por médico"""
        
        # Total de órdenes
        total_result = await db.execute(
            select(func.count(OrdenCab.id)).where(OrdenCab.creado_por == medico_id)
        )
        total_ordenes = total_result.scalar()
        
        # Órdenes por estado
        estados_result = await db.execute(
            select(OrdenCab.estado, func.count(OrdenCab.id))
            .where(OrdenCab.creado_por == medico_id)
            .group_by(OrdenCab.estado)
        )
        
        ordenes_por_estado = {}
        for estado, count in estados_result.all():
            estado_desc = {
                "01": "Pendientes",
                "02": "Programadas",
                "03": "En Proceso",
                "04": "Completadas",
                "05": "Canceladas"
            }
            ordenes_por_estado[estado_desc.get(estado, estado)] = count
        
        # Órdenes por prioridad
        prioridad_result = await db.execute(
            select(OrdenCab.prioridad, func.count(OrdenCab.id))
            .where(OrdenCab.creado_por == medico_id)
            .group_by(OrdenCab.prioridad)
        )
        
        ordenes_por_prioridad = {
            prioridad: count for prioridad, count in prioridad_result.all()
        }
        
        return {
            "medico_id": medico_id,
            "total_ordenes": total_ordenes,
            "ordenes_por_estado": ordenes_por_estado,
            "ordenes_por_prioridad": ordenes_por_prioridad
        }
    
    @staticmethod
    async def obtener_examenes_mas_solicitados(
        db: AsyncSession, 
        limite: int = 10,
        categoria: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtener exámenes más solicitados"""
        
        query = select(
            OrdenDet.nombre_examen,
            OrdenDet.categoria,
            func.count(OrdenDet.id).label('total')
        ).group_by(OrdenDet.nombre_examen, OrdenDet.categoria)
        
        if categoria:
            query = query.where(OrdenDet.categoria == categoria)
        
        query = query.order_by(desc('total')).limit(limite)
        
        result = await db.execute(query)
        
        return [
            {
                "examen": nombre,
                "categoria": cat,
                "total_solicitudes": total
            }
            for nombre, cat, total in result.all()
        ]
    
    # ===== BÚSQUEDAS =====
    
    @staticmethod
    async def buscar_examenes_disponibles(
        db: AsyncSession,
        busqueda: str,
        categoria: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Buscar exámenes disponibles en el catálogo"""
        
        # Esta función debería buscar en un catálogo de exámenes
        # Por ahora devolvemos ejemplos estáticos
        examenes = [
            {"codigo": "LAB001", "nombre": "Hemograma Completo", "categoria": "LABORATORIO"},
            {"codigo": "LAB002", "nombre": "Glucosa", "categoria": "LABORATORIO"},
            {"codigo": "IMG001", "nombre": "Radiografía de Tórax", "categoria": "IMAGEN"},
            {"codigo": "IMG002", "nombre": "Ecografía Abdominal", "categoria": "IMAGEN"},
        ]
        
        # Filtrar por búsqueda
        resultados = [
            e for e in examenes 
            if busqueda.lower() in e["nombre"].lower() or busqueda.lower() in e["codigo"].lower()
        ]
        
        if categoria:
            resultados = [e for e in resultados if e["categoria"] == categoria]
        
        return resultados[:limit]
    
    @staticmethod
    async def obtener_tipos_examenes_disponibles(
        db: AsyncSession,
        categoria: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtener tipos de exámenes disponibles"""
        
        tipos = [
            {"tipo": "LABORATORIO", "descripcion": "Exámenes de Laboratorio", "count": 150},
            {"tipo": "IMAGEN", "descripcion": "Estudios de Imagen", "count": 80},
            {"tipo": "PROCEDIMIENTO", "descripcion": "Procedimientos Médicos", "count": 45},
            {"tipo": "INTERCONSULTA", "descripcion": "Interconsultas", "count": 30},
            {"tipo": "TERAPIA", "descripcion": "Terapias", "count": 25}
        ]
        
        if categoria:
            tipos = [t for t in tipos if t["tipo"] == categoria]
        
        return tipos
    
    # ===== MÉTODOS PRIVADOS =====
    
    @staticmethod
    async def _validar_creacion_orden(db: AsyncSession, orden_data: OrdenCabCreate, medico_id: int):
        """Validar reglas de negocio para creación"""
        
        # Validar médico
        result = await db.execute(select(User).where(User.id == medico_id))
        medico = result.scalar_one_or_none()
        
        if not medico or not medico.especialidad:
            raise BusinessRuleException("Solo médicos pueden crear órdenes")
        
        # Validar no orden duplicada mismo día para mismo tipo
        if orden_data.detalles:
            hoy = datetime.utcnow().date()
            for detalle in orden_data.detalles:
                result = await db.execute(
                    select(func.count(OrdenDet.id))
                    .join(OrdenCab)
                    .where(and_(
                        OrdenCab.paciente_id == orden_data.paciente_id,
                        OrdenDet.tipo_orden == detalle.tipo_orden,
                        OrdenDet.codigo_examen == detalle.codigo_examen,
                        func.date(OrdenCab.created_at) == hoy
                    ))
                )
                
                if result.scalar() > 0:
                    raise BusinessRuleException(
                        f"Ya existe una orden de {detalle.nombre_examen} para este paciente hoy"
                    )
        
        # Validar cantidad de exámenes (máximo 20 por orden)
        if len(orden_data.detalles) > 20:
            raise BusinessRuleException("Máximo 20 exámenes por orden")
        
        if len(orden_data.detalles) == 0:
            raise BusinessRuleException("La orden debe tener al menos un examen")
    
    @staticmethod
    async def _crear_detalle_orden(db: AsyncSession, orden_id: int, detalle_data: OrdenDetCreate):
        """Crear detalle de orden"""
        
        db_detalle = OrdenDet(
            orden_id=orden_id,
            tipo_orden=detalle_data.tipo_orden,
            codigo_examen=detalle_data.codigo_examen,
            nombre_examen=detalle_data.nombre_examen,
            categoria=detalle_data.categoria,
            subcategoria=detalle_data.subcategoria,
            urgente=detalle_data.urgente,
            observaciones=detalle_data.observaciones,
            indicaciones_especiales=detalle_data.indicaciones_especiales,
            ayuno_requerido=detalle_data.ayuno_requerido,
            horas_ayuno=detalle_data.horas_ayuno,
            estado="PENDIENTE",
            fecha_programada=detalle_data.fecha_programada
        )
        
        db.add(db_detalle)
    
    @staticmethod
    async def _obtener_info_medico(db: AsyncSession, medico_id: int) -> Dict[str, Any]:
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
    async def _generar_numero_orden(db: AsyncSession, tipo_orden: str) -> str:
        """Generar número único de orden"""
        fecha_actual = datetime.utcnow().strftime("%Y%m%d")
        
        # Prefijo según tipo
        prefijos = {
            "LABORATORIO": "LAB",
            "IMAGEN": "IMG",
            "PROCEDIMIENTO": "PRO",
            "INTERCONSULTA": "INT",
            "TERAPIA": "TER"
        }
        prefijo = prefijos.get(tipo_orden, "ORD")
        
        # Contar órdenes del día
        result = await db.execute(
            select(func.count(OrdenCab.id))
            .where(func.date(OrdenCab.created_at) == datetime.utcnow().date())
        )
        secuencial = result.scalar() + 1
        
        return f"{prefijo}{fecha_actual}{secuencial:04d}"
    
    @staticmethod
    async def _validar_modificacion_orden(db: AsyncSession, orden: OrdenCab, medico_id: int):
        """Validar que se puede modificar la orden"""
        
        # Solo el médico creador puede modificar (o admin)
        if orden.creado_por != medico_id:
            raise BusinessRuleException("Solo el médico creador puede modificar la orden")
        
        # Solo órdenes pendientes o programadas
        if orden.estado not in ["01", "02"]:
            raise BusinessRuleException("Solo se pueden modificar órdenes pendientes o programadas")
    
    @staticmethod
    async def _validar_cambio_estado(db: AsyncSession, orden: OrdenCab, nuevo_estado: str, medico_id: int):
        """Validar cambio de estado de orden"""
        
        # Validar transiciones válidas
        transiciones_validas = {
            "01": ["02", "03", "05"],  # Pendiente -> Programada, En Proceso, Cancelada
            "02": ["03", "05"],        # Programada -> En Proceso, Cancelada
            "03": ["04", "05"],        # En Proceso -> Completada, Cancelada
            "04": [],                  # Completada -> No puede cambiar
            "05": []                   # Cancelada -> No puede cambiar
        }
        
        if nuevo_estado not in transiciones_validas.get(orden.estado, []):
            raise BusinessRuleException(f"Transición no válida de {orden.estado} a {nuevo_estado}")