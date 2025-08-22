from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from app.models.lista import PacientePorCama, EstructuraHospital
from app.models.user import User
from app.schemas.lista import (
    MovimientoCamaCreate, AsignacionCamaRequest, CambioServicioRequest
)
from app.core.exceptions import NotFoundError, ValidationException, BusinessRuleException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

class ListaService:
    """🛏️ Servicio de Listas y Gestión de Camas - Compatible con ListaController Java"""
    
    # ===== GESTIÓN DE CAMAS =====
    
    @staticmethod
    async def obtener_camas_con_filtros(
        db: AsyncSession,
        servicio: Optional[str] = None,
        unidad: Optional[str] = None,
        disponible: Optional[bool] = None,
        tipo_cama: Optional[str] = None
    ) -> List[EstructuraHospital]:
        """Obtener camas con filtros opcionales"""
        
        query = select(EstructuraHospital).options(
            selectinload(EstructuraHospital.pacientes_por_cama)
        )
        
        filters = []
        if servicio:
            filters.append(EstructuraHospital.servicio == servicio)
        if unidad:
            filters.append(EstructuraHospital.unidad == unidad)
        if tipo_cama:
            filters.append(EstructuraHospital.tipo_cama == tipo_cama)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(EstructuraHospital.servicio, EstructuraHospital.unidad, EstructuraHospital.numero_cama)
        
        result = await db.execute(query)
        camas = result.scalars().unique().all()
        
        # Filtrar por disponibilidad si se especifica
        if disponible is not None:
            camas_filtradas = []
            for cama in camas:
                cama_disponible = True
                if cama.pacientes_por_cama:
                    # Verificar si hay paciente activo
                    for paciente in cama.pacientes_por_cama:
                        if paciente.fecha_salida is None:
                            cama_disponible = False
                            break
                
                if disponible == cama_disponible:
                    camas_filtradas.append(cama)
            
            return camas_filtradas
        
        return camas
    
    @staticmethod
    async def obtener_disponibilidad_por_servicio(
        db: AsyncSession,
        servicio: Optional[str] = None,
        unidad: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtener disponibilidad de camas por servicio/unidad"""
        
        query = select(EstructuraHospital).options(
            selectinload(EstructuraHospital.pacientes_por_cama)
        )
        
        filters = []
        if servicio:
            filters.append(EstructuraHospital.servicio == servicio)
        if unidad:
            filters.append(EstructuraHospital.unidad == unidad)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await db.execute(query)
        camas = result.scalars().unique().all()
        
        # Agrupar por servicio/unidad
        disponibilidad = {}
        for cama in camas:
            key = f"{cama.servicio}_{cama.unidad}"
            
            if key not in disponibilidad:
                disponibilidad[key] = {
                    "servicio": cama.servicio,
                    "unidad": cama.unidad,
                    "total_camas": 0,
                    "ocupadas": 0,
                    "disponibles": 0,
                    "en_mantenimiento": 0
                }
            
            disponibilidad[key]["total_camas"] += 1
            
            # Verificar ocupación
            cama_ocupada = False
            if cama.pacientes_por_cama:
                for paciente in cama.pacientes_por_cama:
                    if paciente.fecha_salida is None:
                        cama_ocupada = True
                        break
            
            if cama_ocupada:
                disponibilidad[key]["ocupadas"] += 1
            elif cama.estado_cama == "MANTENIMIENTO":
                disponibilidad[key]["en_mantenimiento"] += 1
            else:
                disponibilidad[key]["disponibles"] += 1
        
        # Calcular porcentajes
        resultado = []
        for item in disponibilidad.values():
            if item["total_camas"] > 0:
                item["porcentaje_ocupacion"] = round(
                    (item["ocupadas"] / item["total_camas"]) * 100, 2
                )
            else:
                item["porcentaje_ocupacion"] = 0
            resultado.append(item)
        
        return resultado
    
    @staticmethod
    async def asignar_paciente_cama(
        db: AsyncSession,
        movimiento_data: MovimientoCamaCreate,
        usuario_id: int
    ) -> PacientePorCama:
        """Asignar paciente a una cama"""
        
        # Validar que la cama existe
        result = await db.execute(
            select(EstructuraHospital).where(EstructuraHospital.id == movimiento_data.cama_id)
        )
        cama = result.scalar_one_or_none()
        
        if not cama:
            raise NotFoundError(f"Cama no encontrada con ID: {movimiento_data.cama_id}")
        
        # Validar que la cama está disponible
        result = await db.execute(
            select(PacientePorCama)
            .where(and_(
                PacientePorCama.cama_id == movimiento_data.cama_id,
                PacientePorCama.fecha_salida.is_(None)
            ))
        )
        paciente_actual = result.scalar_one_or_none()
        
        if paciente_actual:
            raise BusinessRuleException("La cama ya está ocupada")
        
        # Crear asignación
        db_movimiento = PacientePorCama(
            cama_id=movimiento_data.cama_id,
            paciente_id=movimiento_data.paciente_id,
            nombre_paciente=movimiento_data.nombre_paciente,
            documento=movimiento_data.documento,
            fecha_ingreso=movimiento_data.fecha_ingreso or datetime.utcnow(),
            motivo_ingreso=movimiento_data.motivo_ingreso,
            observaciones=movimiento_data.observaciones,
            creado_por=usuario_id
        )
        
        # Actualizar estado de cama
        cama.estado_cama = "OCUPADA"
        
        db.add(db_movimiento)
        await db.commit()
        await db.refresh(db_movimiento)
        
        # Calcular días de estancia
        db_movimiento.dias_estancia = 0
        
        return db_movimiento
    
    @staticmethod
    async def liberar_cama(
        db: AsyncSession,
        cama_id: int,
        motivo_salida: str,
        observaciones: Optional[str],
        usuario_id: int
    ) -> bool:
        """Liberar cama (dar de alta al paciente)"""
        
        # Buscar paciente actual en la cama
        result = await db.execute(
            select(PacientePorCama)
            .where(and_(
                PacientePorCama.cama_id == cama_id,
                PacientePorCama.fecha_salida.is_(None)
            ))
        )
        paciente_cama = result.scalar_one_or_none()
        
        if not paciente_cama:
            raise NotFoundError("No hay paciente en esta cama")
        
        # Actualizar registro de salida
        paciente_cama.fecha_salida = datetime.utcnow()
        paciente_cama.motivo_salida = motivo_salida
        
        if observaciones:
            paciente_cama.observaciones = (paciente_cama.observaciones or "") + f" | SALIDA: {observaciones}"
        
        # Calcular días de estancia
        dias = (paciente_cama.fecha_salida - paciente_cama.fecha_ingreso).days
        paciente_cama.dias_estancia = max(1, dias)  # Mínimo 1 día
        
        # Actualizar estado de cama
        result = await db.execute(
            select(EstructuraHospital).where(EstructuraHospital.id == cama_id)
        )
        cama = result.scalar_one_or_none()
        
        if cama:
            cama.estado_cama = "LIMPIEZA"  # Requiere limpieza antes de estar disponible
        
        await db.commit()
        
        return True
    
    @staticmethod
    async def cambiar_servicio_paciente(
        db: AsyncSession,
        paciente_id: int,
        nueva_cama_id: int,
        motivo_cambio: str,
        observaciones: Optional[str],
        usuario_id: int
    ) -> PacientePorCama:
        """Cambiar paciente a otra cama/servicio"""
        
        # Buscar asignación actual del paciente
        result = await db.execute(
            select(PacientePorCama)
            .where(and_(
                PacientePorCama.paciente_id == paciente_id,
                PacientePorCama.fecha_salida.is_(None)
            ))
        )
        asignacion_actual = result.scalar_one_or_none()
        
        if not asignacion_actual:
            raise NotFoundError("Paciente no está hospitalizado actualmente")
        
        # Liberar cama actual
        await ListaService.liberar_cama(
            db, 
            asignacion_actual.cama_id,
            f"TRASLADO: {motivo_cambio}",
            observaciones,
            usuario_id
        )
        
        # Asignar nueva cama
        nueva_asignacion = MovimientoCamaCreate(
            cama_id=nueva_cama_id,
            paciente_id=paciente_id,
            nombre_paciente=asignacion_actual.nombre_paciente,
            documento=asignacion_actual.documento,
            fecha_ingreso=datetime.utcnow(),
            motivo_ingreso=f"TRASLADO: {motivo_cambio}",
            observaciones=observaciones
        )
        
        return await ListaService.asignar_paciente_cama(db, nueva_asignacion, usuario_id)
    
    @staticmethod
    async def obtener_historial_cama(
        db: AsyncSession,
        cama_id: int,
        limite: int = 20
    ) -> List[PacientePorCama]:
        """Obtener historial de ocupación de una cama"""
        
        result = await db.execute(
            select(PacientePorCama)
            .where(PacientePorCama.cama_id == cama_id)
            .order_by(desc(PacientePorCama.fecha_ingreso))
            .limit(limite)
        )
        
        return result.scalars().all()
    
    # ===== ESTRUCTURA HOSPITALARIA =====
    
    @staticmethod
    async def obtener_estructura_hospital(
        db: AsyncSession,
        incluir_camas: bool = False
    ) -> Dict[str, Any]:
        """Obtener estructura completa del hospital"""
        
        # Obtener todos los servicios únicos
        servicios_result = await db.execute(
            select(EstructuraHospital.servicio).distinct()
        )
        servicios = servicios_result.scalars().all()
        
        estructura = {"servicios": [], "total_camas": 0}
        
        for servicio in servicios:
            # Obtener unidades del servicio
            unidades_result = await db.execute(
                select(EstructuraHospital.unidad).distinct()
                .where(EstructuraHospital.servicio == servicio)
            )
            unidades = unidades_result.scalars().all()
            
            servicio_data = {
                "servicio": servicio,
                "unidades": []
            }
            
            for unidad in unidades:
                unidad_data = {"unidad": unidad}
                
                if incluir_camas:
                    # Obtener camas de la unidad
                    camas_result = await db.execute(
                        select(EstructuraHospital)
                        .where(and_(
                            EstructuraHospital.servicio == servicio,
                            EstructuraHospital.unidad == unidad
                        ))
                        .order_by(EstructuraHospital.numero_cama)
                    )
                    camas = camas_result.scalars().all()
                    
                    unidad_data["camas"] = [
                        {
                            "id": cama.id,
                            "codigo": cama.codigo_cama,
                            "numero": cama.numero_cama,
                            "tipo": cama.tipo_cama,
                            "estado": cama.estado_cama
                        }
                        for cama in camas
                    ]
                    unidad_data["total_camas"] = len(camas)
                    estructura["total_camas"] += len(camas)
                
                servicio_data["unidades"].append(unidad_data)
            
            estructura["servicios"].append(servicio_data)
        
        return estructura
    
    @staticmethod
    async def obtener_servicios(
        db: AsyncSession,
        activo: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtener lista de servicios médicos"""
        
        query = select(EstructuraHospital.servicio, func.count(EstructuraHospital.id).label('total_camas'))
        
        if activo:
            query = query.where(EstructuraHospital.activa == True)
        
        query = query.group_by(EstructuraHospital.servicio)
        
        result = await db.execute(query)
        
        return [
            {"servicio": servicio, "total_camas": total}
            for servicio, total in result.all()
        ]
    
    @staticmethod
    async def obtener_unidades_por_servicio(
        db: AsyncSession,
        servicio: str,
        activo: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtener unidades de un servicio específico"""
        
        query = select(
            EstructuraHospital.unidad,
            func.count(EstructuraHospital.id).label('total_camas')
        ).where(EstructuraHospital.servicio == servicio)
        
        if activo:
            query = query.where(EstructuraHospital.activa == True)
        
        query = query.group_by(EstructuraHospital.unidad)
        
        result = await db.execute(query)
        
        return [
            {"unidad": unidad, "total_camas": total}
            for unidad, total in result.all()
        ]
    
    # ===== REPORTES Y ESTADÍSTICAS =====
    
    @staticmethod
    async def generar_reporte_ocupacion(
        db: AsyncSession,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        servicio: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generar reporte de ocupación de camas"""
        
        query = select(PacientePorCama).options(
            selectinload(PacientePorCama.cama)
        )
        
        filters = []
        if fecha_desde:
            filters.append(PacientePorCama.fecha_ingreso >= datetime.fromisoformat(fecha_desde))
        if fecha_hasta:
            filters.append(or_(
                PacientePorCama.fecha_salida <= datetime.fromisoformat(fecha_hasta),
                PacientePorCama.fecha_salida.is_(None)
            ))
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await db.execute(query)
        movimientos = result.scalars().all()
        
        # Filtrar por servicio si se especifica
        if servicio:
            movimientos = [m for m in movimientos if m.cama and m.cama.servicio == servicio]
        
        # Calcular estadísticas
        total_ingresos = len(movimientos)
        total_altas = len([m for m in movimientos if m.fecha_salida])
        pacientes_actuales = len([m for m in movimientos if not m.fecha_salida])
        
        # Promedio de estancia
        estancias = [m.dias_estancia for m in movimientos if m.dias_estancia]
        promedio_estancia = sum(estancias) / len(estancias) if estancias else 0
        
        return {
            "periodo": {
                "desde": fecha_desde or "inicio",
                "hasta": fecha_hasta or "actual"
            },
            "servicio": servicio or "todos",
            "total_ingresos": total_ingresos,
            "total_altas": total_altas,
            "pacientes_actuales": pacientes_actuales,
            "promedio_estancia_dias": round(promedio_estancia, 2)
        }
    
    @staticmethod
    async def obtener_movimientos_camas(
        db: AsyncSession,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        servicio: Optional[str] = None,
        tipo_movimiento: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> Dict[str, Any]:
        """Obtener movimientos de camas con paginación"""
        
        query = select(PacientePorCama).options(
            selectinload(PacientePorCama.cama)
        )
        
        filters = []
        if fecha_desde:
            filters.append(PacientePorCama.fecha_ingreso >= datetime.fromisoformat(fecha_desde))
        if fecha_hasta:
            filters.append(PacientePorCama.fecha_ingreso <= datetime.fromisoformat(fecha_hasta))
        
        if tipo_movimiento == "INGRESO":
            filters.append(PacientePorCama.fecha_salida.is_(None))
        elif tipo_movimiento == "ALTA":
            filters.append(PacientePorCama.fecha_salida.isnot(None))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Contar total
        count_query = select(func.count()).select_from(PacientePorCama)
        if filters:
            count_query = count_query.where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Aplicar paginación
        offset = (page - 1) * size
        query = query.order_by(desc(PacientePorCama.fecha_ingreso)).offset(offset).limit(size)
        
        result = await db.execute(query)
        movimientos = result.scalars().all()
        
        # Filtrar por servicio si se especifica
        if servicio:
            movimientos = [m for m in movimientos if m.cama and m.cama.servicio == servicio]
        
        return {
            "movimientos": movimientos,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size
        }
    
    @staticmethod
    async def buscar_pacientes_hospitalizados(
        db: AsyncSession,
        busqueda: str,
        servicio: Optional[str] = None,
        limit: int = 20
    ) -> List[PacientePorCama]:
        """Buscar pacientes hospitalizados"""
        
        query = select(PacientePorCama).options(
            selectinload(PacientePorCama.cama)
        ).where(
            and_(
                PacientePorCama.fecha_salida.is_(None),
                or_(
                    PacientePorCama.nombre_paciente.ilike(f"%{busqueda}%"),
                    PacientePorCama.documento.ilike(f"%{busqueda}%")
                )
            )
        ).limit(limit)
        
        result = await db.execute(query)
        pacientes = result.scalars().all()
        
        # Filtrar por servicio si se especifica
        if servicio:
            pacientes = [p for p in pacientes if p.cama and p.cama.servicio == servicio]
        
        return pacientes