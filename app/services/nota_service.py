from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update
from app.models.nota import HospitalizacionNota
from app.models.user import User
from app.schemas.nota import (
    NotaCreate, NotaUpdate, NotaResponse,
    TipoNota, EstadoNota
)
from app.core.exceptions import NotFoundError, ValidationException, BusinessRuleException, MedicoPermissionException
from typing import List, Optional
from datetime import datetime, timedelta
import hashlib
import os

class NotaService:
    """📝 Servicio de Notas - Compatible con HospitalizacionNotaController Java"""
    
    # ===== VALIDACIÓN CRÍTICA =====
    
    @staticmethod
    async def puede_crear_nota(db: AsyncSession, medico_id: int, hospitalizacion_id: int) -> dict:
        """Verificar si un médico puede crear una nueva nota"""
        
        # Validar que es médico
        if not await NotaService._validar_es_medico(db, medico_id):
            return {
                "puede_crear": False,
                "razon": "Usuario no es médico válido"
            }
        
        # Verificar si ya tiene una nota en borrador
        result = await db.execute(
            select(func.count(HospitalizacionNota.id))
            .where(and_(
                HospitalizacionNota.creado_por == medico_id,
                HospitalizacionNota.hospitalizacion_id == hospitalizacion_id,
                HospitalizacionNota.estado == EstadoNota.BORRADOR
            ))
        )
        
        notas_borrador = result.scalar()
        
        return {
            "puede_crear": notas_borrador == 0,
            "medico_id": medico_id,
            "hospitalizacion_id": hospitalizacion_id,
            "razon": "Sin restricciones" if notas_borrador == 0 else "Ya tiene una nota en borrador"
        }
    
    # ===== CONSULTAR NOTAS =====
    
    @staticmethod
    async def obtener_notas_por_hospitalizacion(db: AsyncSession, hospitalizacion_id: int, estado: Optional[str] = None) -> List[HospitalizacionNota]:
        """Obtener todas las notas de una hospitalización"""
        query = select(HospitalizacionNota).where(HospitalizacionNota.hospitalizacion_id == hospitalizacion_id)
        
        if estado and estado.lower() != "todas":
            if estado.lower() == "borrador":
                query = query.where(HospitalizacionNota.estado == EstadoNota.BORRADOR)
            elif estado.lower() == "finalizada":
                query = query.where(HospitalizacionNota.estado == EstadoNota.FINALIZADA)
        
        query = query.order_by(desc(HospitalizacionNota.creado_en))
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def obtener_notas_borrador(db: AsyncSession, hospitalizacion_id: int) -> List[HospitalizacionNota]:
        """Obtener solo notas en borrador"""
        result = await db.execute(
            select(HospitalizacionNota)
            .where(and_(
                HospitalizacionNota.hospitalizacion_id == hospitalizacion_id,
                HospitalizacionNota.estado == EstadoNota.BORRADOR
            ))
            .order_by(desc(HospitalizacionNota.creado_en))
        )
        return result.scalars().all()
    
    @staticmethod
    async def obtener_notas_finalizadas(db: AsyncSession, hospitalizacion_id: int) -> List[HospitalizacionNota]:
        """Obtener solo notas finalizadas"""
        result = await db.execute(
            select(HospitalizacionNota)
            .where(and_(
                HospitalizacionNota.hospitalizacion_id == hospitalizacion_id,
                HospitalizacionNota.estado == EstadoNota.FINALIZADA
            ))
            .order_by(desc(HospitalizacionNota.finalizado_en))
        )
        return result.scalars().all()
    
    @staticmethod
    async def obtener_nota_por_id(db: AsyncSession, nota_id: int) -> Optional[HospitalizacionNota]:
        """Obtener nota específica por ID"""
        result = await db.execute(
            select(HospitalizacionNota)
            .where(HospitalizacionNota.id == nota_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def buscar_por_numero_cuenta(db: AsyncSession, numero_cuenta: str) -> List[HospitalizacionNota]:
        """Buscar notas por número de cuenta"""
        result = await db.execute(
            select(HospitalizacionNota)
            .where(HospitalizacionNota.numero_cuenta == numero_cuenta)
            .order_by(desc(HospitalizacionNota.creado_en))
        )
        return result.scalars().all()
    
    @staticmethod
    async def buscar_por_tipo(db: AsyncSession, hospitalizacion_id: int, tipo_nota: str) -> List[HospitalizacionNota]:
        """Buscar notas por tipo en una hospitalización"""
        result = await db.execute(
            select(HospitalizacionNota)
            .where(and_(
                HospitalizacionNota.hospitalizacion_id == hospitalizacion_id,
                HospitalizacionNota.tipo_nota == tipo_nota
            ))
            .order_by(desc(HospitalizacionNota.creado_en))
        )
        return result.scalars().all()
    
    @staticmethod
    async def buscar_por_medico_y_fechas(db: AsyncSession, medico_id: int, fecha_inicio: datetime, fecha_fin: datetime) -> List[HospitalizacionNota]:
        """Buscar notas de un médico en rango de fechas"""
        result = await db.execute(
            select(HospitalizacionNota)
            .where(and_(
                HospitalizacionNota.creado_por == medico_id,
                HospitalizacionNota.creado_en >= fecha_inicio,
                HospitalizacionNota.creado_en <= fecha_fin
            ))
            .order_by(desc(HospitalizacionNota.creado_en))
        )
        return result.scalars().all()
    
    # ===== CRUD INTELIGENTE =====
    
    @staticmethod
    async def crear_nota(db: AsyncSession, nota_data: NotaCreate, medico_id: int) -> HospitalizacionNota:
        """Crear nueva nota con auto-limpieza"""
        
        # Validar permisos
        validacion = await NotaService.puede_crear_nota(db, medico_id, nota_data.hospitalizacion_id)
        if not validacion["puede_crear"]:
            raise BusinessRuleException(validacion["razon"])
        
        # Obtener información del médico
        medico_info = await NotaService._obtener_info_medico(db, medico_id)
        
        # Crear nota
        db_nota = HospitalizacionNota(
            hospitalizacion_id=nota_data.hospitalizacion_id,
            numero_cuenta=nota_data.numero_cuenta,
            paciente_id=nota_data.paciente_id,
            paciente_nombre=nota_data.paciente_nombre,
            tipo_nota=nota_data.tipo_nota,
            contenido_nota=nota_data.contenido_nota,
            observaciones=nota_data.observaciones,
            estado=EstadoNota.BORRADOR,
            creado_por=medico_id,
            medico_nombre=medico_info["nombre_completo"],
            medico_especialidad=medico_info["especialidad"],
            medico_colegiatura=medico_info["colegiatura"],
            creado_en=datetime.utcnow()
        )
        
        db.add(db_nota)
        await db.commit()
        await db.refresh(db_nota)
        
        # Auto-limpieza de notas antiguas en borrador
        await NotaService._auto_limpiar_borradores_antiguos(db, medico_id)
        
        return db_nota
    
    @staticmethod
    async def actualizar_nota(db: AsyncSession, nota_id: int, nota_data: NotaUpdate, medico_id: int) -> HospitalizacionNota:
        """Actualizar nota existente"""
        
        nota = await NotaService.obtener_nota_por_id(db, nota_id)
        if not nota:
            raise NotFoundError(f"Nota no encontrada con ID: {nota_id}")
        
        # Validar permisos de edición
        await NotaService._validar_permisos_edicion(db, nota, medico_id)
        
        # Actualizar campos
        update_data = nota_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(nota, field, value)
        
        nota.actualizado_en = datetime.utcnow()
        
        await db.commit()
        await db.refresh(nota)
        
        return nota
    
    @staticmethod
    async def finalizar_nota(db: AsyncSession, nota_id: int, medico_id: int) -> HospitalizacionNota:
        """Finalizar nota (borrador → finalizada)"""
        
        nota = await NotaService.obtener_nota_por_id(db, nota_id)
        if not nota:
            raise NotFoundError(f"Nota no encontrada con ID: {nota_id}")
        
        # Validar permisos
        if nota.creado_por != medico_id:
            raise MedicoPermissionException("Solo el médico creador puede finalizar la nota")
        
        if nota.estado != EstadoNota.BORRADOR:
            raise BusinessRuleException("Solo se pueden finalizar notas en borrador")
        
        # Finalizar nota
        nota.estado = EstadoNota.FINALIZADA
        nota.finalizado_en = datetime.utcnow()
        nota.actualizado_en = datetime.utcnow()
        
        await db.commit()
        await db.refresh(nota)
        
        return nota
    
    @staticmethod
    async def eliminar_nota(db: AsyncSession, nota_id: int, medico_id: int) -> bool:
        """Eliminar nota"""
        
        nota = await NotaService.obtener_nota_por_id(db, nota_id)
        if not nota:
            raise NotFoundError(f"Nota no encontrada con ID: {nota_id}")
        
        # Validar permisos
        if nota.creado_por != medico_id:
            raise MedicoPermissionException("Solo el médico creador puede eliminar la nota")
        
        if nota.estado == EstadoNota.FINALIZADA and nota.firmada:
            raise BusinessRuleException("No se pueden eliminar notas finalizadas y firmadas")
        
        await db.delete(nota)
        await db.commit()
        
        return True
    
    # ===== GESTIÓN DE AUDIO =====
    
    @staticmethod
    async def eliminar_audio_nota(db: AsyncSession, nota_id: int, medico_id: int) -> bool:
        """Eliminar audio de una nota específica"""
        
        nota = await NotaService.obtener_nota_por_id(db, nota_id)
        if not nota:
            raise NotFoundError(f"Nota no encontrada con ID: {nota_id}")
        
        # Validar permisos
        if nota.creado_por != medico_id:
            raise MedicoPermissionException("Solo el médico creador puede eliminar el audio")
        
        if not nota.tiene_audio:
            return False  # No tiene audio para eliminar
        
        # Eliminar archivo físico si existe
        if nota.archivo_audio and os.path.exists(nota.archivo_audio):
            try:
                os.remove(nota.archivo_audio)
            except Exception:
                pass  # Ignorar errores de eliminación de archivo
        
        # Limpiar datos de audio
        nota.tiene_audio = False
        nota.archivo_audio = None
        nota.audio_data = None
        nota.transcripcion_automatica = None
        nota.actualizado_en = datetime.utcnow()
        
        await db.commit()
        
        return True
    
    @staticmethod
    async def tiene_audio_disponible(db: AsyncSession, nota_id: int) -> bool:
        """Verificar si una nota tiene audio disponible"""
        nota = await NotaService.obtener_nota_por_id(db, nota_id)
        return nota.tiene_audio if nota else False
    
    # ===== ESTADÍSTICAS =====
    
    @staticmethod
    async def obtener_estadisticas_hospitalizacion(db: AsyncSession, hospitalizacion_id: int) -> dict:
        """Obtener estadísticas de una hospitalización"""
        
        # Total de notas
        total_result = await db.execute(
            select(func.count(HospitalizacionNota.id))
            .where(HospitalizacionNota.hospitalizacion_id == hospitalizacion_id)
        )
        total_notas = total_result.scalar()
        
        # Notas por estado
        estados_result = await db.execute(
            select(HospitalizacionNota.estado, func.count(HospitalizacionNota.id))
            .where(HospitalizacionNota.hospitalizacion_id == hospitalizacion_id)
            .group_by(HospitalizacionNota.estado)
        )
        
        notas_por_estado = {estado: count for estado, count in estados_result.all()}
        
        # Notas con audio
        audio_result = await db.execute(
            select(func.count(HospitalizacionNota.id))
            .where(and_(
                HospitalizacionNota.hospitalizacion_id == hospitalizacion_id,
                HospitalizacionNota.tiene_audio == True
            ))
        )
        notas_con_audio = audio_result.scalar()
        
        # Notas firmadas
        firmadas_result = await db.execute(
            select(func.count(HospitalizacionNota.id))
            .where(and_(
                HospitalizacionNota.hospitalizacion_id == hospitalizacion_id,
                HospitalizacionNota.firmada == True
            ))
        )
        notas_firmadas = firmadas_result.scalar()
        
        # Médicos participantes
        medicos_result = await db.execute(
            select(
                HospitalizacionNota.medico_nombre,
                func.count(HospitalizacionNota.id).label('total_notas')
            )
            .where(HospitalizacionNota.hospitalizacion_id == hospitalizacion_id)
            .group_by(HospitalizacionNota.medico_nombre)
            .order_by(desc('total_notas'))
        )
        
        medicos_participantes = [
            {"nombre": nombre, "total_notas": total}
            for nombre, total in medicos_result.all()
        ]
        
        return {
            "hospitalizacion_id": hospitalizacion_id,
            "total_notas": total_notas,
            "notas_por_estado": notas_por_estado,
            "notas_con_audio": notas_con_audio,
            "notas_firmadas": notas_firmadas,
            "medicos_participantes": medicos_participantes
        }
    
    # ===== GENERACIÓN DE PDF =====
    
    @staticmethod
    async def generar_pdf_nota(db: AsyncSession, nota_id: int) -> bytes:
        """Generar PDF de una nota específica"""
        nota = await NotaService.obtener_nota_por_id(db, nota_id)
        if not nota:
            raise NotFoundError(f"Nota no encontrada con ID: {nota_id}")
        
        # Aquí iría la lógica de generación de PDF
        # Por ahora retornamos un placeholder
        pdf_content = f"""
        NOTA MÉDICA - {nota.tipo_nota_descripcion}
        
        Paciente: {nota.paciente_nombre}
        Número de Cuenta: {nota.numero_cuenta}
        Fecha: {nota.creado_en.strftime('%d/%m/%Y %H:%M')}
        
        Médico: {nota.medico_nombre}
        Especialidad: {nota.medico_especialidad}
        
        CONTENIDO:
        {nota.contenido_nota}
        
        {"FIRMADA DIGITALMENTE" if nota.firmada else "SIN FIRMA"}
        """.encode('utf-8')
        
        return pdf_content
    
    @staticmethod
    async def generar_pdf_consolidado(db: AsyncSession, hospitalizacion_id: int) -> bytes:
        """Generar PDF consolidado de una hospitalización"""
        notas = await NotaService.obtener_notas_finalizadas(db, hospitalizacion_id)
        
        if not notas:
            raise NotFoundError("No hay notas finalizadas para esta hospitalización")
        
        # Aquí iría la lógica de generación de PDF consolidado
        pdf_content = f"""
        REPORTE CONSOLIDADO DE NOTAS
        Hospitalización ID: {hospitalizacion_id}
        
        Total de Notas: {len(notas)}
        Fecha de Generación: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}
        
        {"=" * 50}
        """.encode('utf-8')
        
        return pdf_content
    
    # ===== MÉTODOS PRIVADOS =====
    
    @staticmethod
    async def _validar_es_medico(db: AsyncSession, user_id: int) -> bool:
        """Validar que el usuario es médico"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        return bool(user and user.especialidad and user.colegiatura and user.is_active)
    
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
    async def _validar_permisos_edicion(db: AsyncSession, nota: HospitalizacionNota, medico_id: int):
        """Validar permisos para editar nota"""
        
        if nota.creado_por != medico_id:
            raise MedicoPermissionException("Solo el médico creador puede editar la nota")
        
        if nota.estado != EstadoNota.BORRADOR:
            raise BusinessRuleException("Solo se pueden editar notas en borrador")
        
        if nota.firmada:
            raise BusinessRuleException("No se pueden editar notas firmadas")
    
    @staticmethod
    async def _auto_limpiar_borradores_antiguos(db: AsyncSession, medico_id: int):
        """Auto-limpieza de notas en borrador muy antiguas"""
        
        # Eliminar borradores sin actividad de más de 7 días
        fecha_limite = datetime.utcnow() - timedelta(days=7)
        
        await db.execute(
            update(HospitalizacionNota)
            .where(and_(
                HospitalizacionNota.creado_por == medico_id,
                HospitalizacionNota.estado == EstadoNota.BORRADOR,
                HospitalizacionNota.actualizado_en < fecha_limite
            ))
            .values(estado="ELIMINADA")  # Soft delete
        )
        
        await db.commit()