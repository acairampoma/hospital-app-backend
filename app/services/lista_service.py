from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, and_, or_, desc
from app.core.exceptions import NotFoundError, ValidationException, BusinessRuleException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

class ListaService:
    """🏏️ Servicio de Listas y Gestión de Camas - Compatible con vistas PostgreSQL"""
    
    # ===== GESTIÓN DE CAMAS =====
    
    @staticmethod
    async def obtener_camas_con_filtros(
        db: AsyncSession,
        servicio: Optional[str] = None,
        unidad: Optional[str] = None,
        disponible: Optional[bool] = None,
        tipo_cama: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtener camas desde vista_pacientes_por_cama"""
        
        # Query básica para obtener solo las camas con pacientes reales
        query = """
            SELECT 
                bed_number,
                patient_data
            FROM vista_pacientes_por_cama
            WHERE patient_data IS NOT NULL 
            AND patient_data::text != 'null'
        """
        
        result = await db.execute(text(query))
        camas_con_pacientes = result.fetchall()
        
        # También obtener estructura completa para camas disponibles
        estructura_query = """
            SELECT estructura_completa 
            FROM vista_estructura_hospital 
            LIMIT 1
        """
        estructura_result = await db.execute(text(estructura_query))
        estructura = estructura_result.fetchone()
        
        if not estructura:
            return []
        
        estructura_json = estructura[0] if isinstance(estructura[0], dict) else json.loads(estructura[0])
        
        # Procesar todas las camas del hospital
        todas_camas = []
        camas_ocupadas = {row[0]: row[1] for row in camas_con_pacientes}
        
        for floor in estructura_json.get('floors', []):
            especialidad = floor.get('specialty', '')
            piso = floor.get('floor_number', 0)
            
            # Filtrar por servicio si se especifica
            if servicio and servicio.lower() not in especialidad.lower():
                continue
            
            for wing_key, wing_data in floor.get('wings', {}).items():
                ala = wing_data.get('wing_code', '')
                
                # Filtrar por unidad/ala si se especifica
                if unidad and unidad.lower() not in ala.lower():
                    continue
                
                for bed in wing_data.get('beds', []):
                    bed_number = bed.get('bed_number', '')
                    status = bed.get('status', 'available')
                    
                    # Filtrar por disponibilidad
                    is_occupied = bed_number in camas_ocupadas
                    if disponible is not None:
                        if disponible and is_occupied:
                            continue
                        if not disponible and not is_occupied:
                            continue
                    
                    cama_info = {
                        "numero_cama": bed_number,
                        "piso": piso,
                        "ala": ala,
                        "servicio": especialidad,
                        "estado": status,
                        "ocupada": is_occupied,
                        "genero_preferido": bed.get('gender', 'M'),
                        "paciente": None
                    }
                    
                    # Si está ocupada, agregar info del paciente
                    if is_occupied and bed_number in camas_ocupadas:
                        patient_data = camas_ocupadas[bed_number]
                        if patient_data:
                            cama_info["paciente"] = {
                                "paciente_id": patient_data.get('paciente_id'),
                                "nombre": patient_data.get('personal_info', {}).get('fullname'),
                                "documento": patient_data.get('personal_info', {}).get('dni'),
                                "fecha_ingreso": patient_data.get('fecha_ingreso'),
                                "diagnostico": patient_data.get('medical_info', {}).get('primary_diagnosis'),
                                "medico": patient_data.get('medical_info', {}).get('attending_physician')
                            }
                    
                    todas_camas.append(cama_info)
        
        return todas_camas
    
    @staticmethod
    async def obtener_disponibilidad_por_servicio(
        db: AsyncSession,
        servicio: Optional[str] = None,
        unidad: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtener disponibilidad de camas por servicio/unidad"""
        
        # Obtener todas las camas
        todas_camas = await ListaService.obtener_camas_con_filtros(
            db, servicio, unidad
        )
        
        # Agrupar por servicio
        disponibilidad = {}
        for cama in todas_camas:
            key = cama['servicio']
            
            if key not in disponibilidad:
                disponibilidad[key] = {
                    "servicio": cama['servicio'],
                    "total_camas": 0,
                    "camas_disponibles": 0,
                    "camas_ocupadas": 0,
                    "porcentaje_ocupacion": 0.0,
                    "pisos": set()
                }
            
            disponibilidad[key]["total_camas"] += 1
            disponibilidad[key]["pisos"].add(cama['piso'])
            
            if cama['ocupada']:
                disponibilidad[key]["camas_ocupadas"] += 1
            else:
                disponibilidad[key]["camas_disponibles"] += 1
        
        # Calcular porcentajes y formatear
        resultado = []
        for key, data in disponibilidad.items():
            data["pisos"] = sorted(list(data["pisos"]))
            if data["total_camas"] > 0:
                data["porcentaje_ocupacion"] = round(
                    (data["camas_ocupadas"] / data["total_camas"]) * 100, 2
                )
            resultado.append(data)
        
        return sorted(resultado, key=lambda x: x["servicio"])
    
    @staticmethod
    async def obtener_estructura_completa(db: AsyncSession) -> Dict[str, Any]:
        """Obtener estructura completa del hospital desde la vista"""
        
        query = """
            SELECT estructura_completa 
            FROM vista_estructura_hospital 
            LIMIT 1
        """
        
        result = await db.execute(text(query))
        estructura = result.fetchone()
        
        if not estructura:
            raise NotFoundError("No se encontró la estructura del hospital")
        
        # Retornar el JSON directamente
        return estructura[0] if isinstance(estructura[0], dict) else json.loads(estructura[0])
    
    @staticmethod
    async def obtener_servicios_medicos(db: AsyncSession) -> List[Dict[str, Any]]:
        """Obtener lista de servicios médicos únicos"""
        
        estructura = await ListaService.obtener_estructura_completa(db)
        
        servicios = []
        servicios_unicos = set()
        
        for floor in estructura.get('floors', []):
            especialidad = floor.get('specialty', '')
            if especialidad and especialidad not in servicios_unicos:
                servicios_unicos.add(especialidad)
                servicios.append({
                    "id": floor.get('floor_number'),
                    "nombre": especialidad,
                    "codigo": floor.get('specialty_code', ''),
                    "piso": floor.get('floor_number'),
                    "jefe_departamento": floor.get('department_head', ''),
                    "extension": floor.get('phone_extension', ''),
                    "color": floor.get('color_theme', '#000000'),
                    "icono": floor.get('icon', 'fas fa-hospital')
                })
        
        return sorted(servicios, key=lambda x: x["piso"])
    
    @staticmethod
    async def obtener_unidades_por_servicio(
        db: AsyncSession, 
        servicio: str
    ) -> List[Dict[str, Any]]:
        """Obtener unidades/alas de un servicio específico"""
        
        estructura = await ListaService.obtener_estructura_completa(db)
        
        unidades = []
        for floor in estructura.get('floors', []):
            if servicio.lower() in floor.get('specialty', '').lower():
                for wing_key, wing_data in floor.get('wings', {}).items():
                    unidades.append({
                        "codigo": wing_data.get('wing_code', ''),
                        "nombre": wing_data.get('name', ''),
                        "tipo": wing_key,
                        "total_camas": len(wing_data.get('beds', [])),
                        "piso": floor.get('floor_number')
                    })
        
        return sorted(unidades, key=lambda x: x["codigo"])
    
    @staticmethod
    async def buscar_pacientes_hospitalizados(
        db: AsyncSession,
        termino_busqueda: str
    ) -> List[Dict[str, Any]]:
        """Buscar pacientes hospitalizados por nombre o documento"""
        
        query = """
            SELECT 
                bed_number,
                patient_data
            FROM vista_pacientes_por_cama
            WHERE patient_data IS NOT NULL
            AND patient_data::text != 'null'
        """
        
        result = await db.execute(text(query))
        pacientes = result.fetchall()
        
        resultado = []
        termino = termino_busqueda.lower()
        
        for bed_number, patient_data in pacientes:
            if patient_data:
                personal_info = patient_data.get('personal_info', {})
                nombre = personal_info.get('fullname', '').lower()
                documento = personal_info.get('dni', '').lower()
                
                if termino in nombre or termino in documento:
                    resultado.append({
                        "paciente_id": patient_data.get('paciente_id'),
                        "nombre": personal_info.get('fullname'),
                        "documento": personal_info.get('dni'),
                        "cama": bed_number,
                        "fecha_ingreso": patient_data.get('fecha_ingreso'),
                        "diagnostico": patient_data.get('medical_info', {}).get('primary_diagnosis'),
                        "medico": patient_data.get('medical_info', {}).get('attending_physician'),
                        "especialidad": patient_data.get('medical_info', {}).get('attending_physician')
                    })
        
        return resultado
    
    @staticmethod
    async def obtener_reporte_ocupacion(db: AsyncSession) -> Dict[str, Any]:
        """Generar reporte de ocupación del hospital"""
        
        # Obtener todas las camas
        todas_camas = await ListaService.obtener_camas_con_filtros(db)
        
        total_camas = len(todas_camas)
        camas_ocupadas = sum(1 for c in todas_camas if c['ocupada'])
        camas_disponibles = total_camas - camas_ocupadas
        
        # Estadísticas por servicio
        por_servicio = {}
        for cama in todas_camas:
            servicio = cama['servicio']
            if servicio not in por_servicio:
                por_servicio[servicio] = {
                    'total': 0,
                    'ocupadas': 0,
                    'disponibles': 0
                }
            
            por_servicio[servicio]['total'] += 1
            if cama['ocupada']:
                por_servicio[servicio]['ocupadas'] += 1
            else:
                por_servicio[servicio]['disponibles'] += 1
        
        # Calcular porcentajes
        for servicio in por_servicio:
            total = por_servicio[servicio]['total']
            ocupadas = por_servicio[servicio]['ocupadas']
            por_servicio[servicio]['porcentaje_ocupacion'] = round(
                (ocupadas / total * 100) if total > 0 else 0, 2
            )
        
        return {
            "resumen_general": {
                "total_camas": total_camas,
                "camas_ocupadas": camas_ocupadas,
                "camas_disponibles": camas_disponibles,
                "porcentaje_ocupacion": round(
                    (camas_ocupadas / total_camas * 100) if total_camas > 0 else 0, 2
                )
            },
            "por_servicio": por_servicio,
            "fecha_reporte": datetime.now().isoformat()
        }
    
    @staticmethod
    async def asignar_paciente_a_cama(
        db: AsyncSession,
        cama_id: str,
        datos_paciente: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Asignar un paciente a una cama (simulado - requiere implementación real)"""
        
        # Esta función requeriría actualizar las tablas reales
        # Por ahora retornamos una respuesta simulada
        return {
            "success": True,
            "message": f"Paciente asignado a cama {cama_id}",
            "cama": cama_id,
            "paciente": datos_paciente
        }
    
    @staticmethod
    async def liberar_cama(
        db: AsyncSession,
        cama_id: str
    ) -> Dict[str, Any]:
        """Liberar una cama (simulado - requiere implementación real)"""
        
        # Esta función requeriría actualizar las tablas reales
        # Por ahora retornamos una respuesta simulada
        return {
            "success": True,
            "message": f"Cama {cama_id} liberada correctamente",
            "cama": cama_id
        }