from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# ===== SCHEMAS DE CATÁLOGOS =====

class CatalogoBase(BaseModel):
    """Base schema para catálogos"""
    codigo: str
    descripcion: str
    descripcion_corta: Optional[str] = None
    valor1: Optional[str] = None
    valor2: Optional[str] = None
    valor3: Optional[str] = None
    orden: Optional[int] = None
    enabled: bool = True

    @validator('codigo')
    def validate_codigo(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Código es requerido')
        return v.strip().upper()

    @validator('descripcion')
    def validate_descripcion(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Descripción es requerida')
        return v.strip()

class CatalogoCreate(CatalogoBase):
    """Create schema para catálogos"""
    pass

class CatalogoUpdate(BaseModel):
    """Update schema para catálogos"""
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    descripcion_corta: Optional[str] = None
    valor1: Optional[str] = None
    valor2: Optional[str] = None
    valor3: Optional[str] = None
    orden: Optional[int] = None
    enabled: Optional[bool] = None

class CatalogoResponse(CatalogoBase):
    """Response schema para catálogos"""
    id: int
    tipo_catalogo: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CatalogoSearchResponse(BaseModel):
    """Response para búsqueda de catálogos"""
    id: int
    codigo: str
    descripcion: str
    descripcion_corta: Optional[str] = None

class CatalogosListResponse(BaseModel):
    """Response para lista paginada de catálogos"""
    catalogos: List[CatalogoResponse]
    total: int
    page: int
    size: int
    total_pages: int
    tipo_catalogo: str

# ===== SCHEMAS DE MEDICAMENTOS VADEMÉCUM =====

class MedicamentoVademecumBase(BaseModel):
    """Base schema para medicamentos vademécum"""
    codigo: str
    nombre_comercial: str
    nombre_generico: Optional[str] = None
    principio_activo: Optional[str] = None
    concentracion: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    presentacion: Optional[str] = None
    laboratorio: Optional[str] = None
    codigo_atc: Optional[str] = None
    categoria_terapeutica: Optional[str] = None
    requiere_receta: bool = True
    precio_referencial: Optional[Decimal] = None
    observaciones: Optional[str] = None
    activo: bool = True

    @validator('codigo')
    def validate_codigo(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Código es requerido')
        return v.strip().upper()

    @validator('nombre_comercial')
    def validate_nombre_comercial(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Nombre comercial es requerido')
        return v.strip()

    @validator('precio_referencial')
    def validate_precio(cls, v):
        if v is not None and v < 0:
            raise ValueError('El precio no puede ser negativo')
        return v

class MedicamentoCreate(MedicamentoVademecumBase):
    """Create schema para medicamentos"""
    pass

class MedicamentoUpdate(BaseModel):
    """Update schema para medicamentos"""
    codigo: Optional[str] = None
    nombre_comercial: Optional[str] = None
    nombre_generico: Optional[str] = None
    principio_activo: Optional[str] = None
    concentracion: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    presentacion: Optional[str] = None
    laboratorio: Optional[str] = None
    codigo_atc: Optional[str] = None
    categoria_terapeutica: Optional[str] = None
    requiere_receta: Optional[bool] = None
    precio_referencial: Optional[Decimal] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None

class MedicamentoVademecumResponse(MedicamentoVademecumBase):
    """Response schema para medicamentos vademécum"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Propiedades calculadas
    descripcion_completa: str = ""
    precio_formateado: str = ""

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        # Descripción completa
        desc = self.nombre_comercial
        if self.concentracion:
            desc += f" {self.concentracion}"
        if self.forma_farmaceutica:
            desc += f" - {self.forma_farmaceutica}"
        if self.presentacion:
            desc += f" ({self.presentacion})"
        self.descripcion_completa = desc

        # Precio formateado
        if self.precio_referencial:
            self.precio_formateado = f"S/ {self.precio_referencial:.2f}"
        else:
            self.precio_formateado = "Precio no disponible"

class MedicamentoSearchResponse(BaseModel):
    """Response para búsqueda de medicamentos"""
    id: int
    codigo: str
    nombre_comercial: str
    nombre_generico: Optional[str] = None
    principio_activo: Optional[str] = None
    concentracion: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    presentacion: Optional[str] = None
    laboratorio: Optional[str] = None
    precio_referencial: Optional[Decimal] = None

class MedicamentosListResponse(BaseModel):
    """Response para lista paginada de medicamentos"""
    medicamentos: List[MedicamentoVademecumResponse]
    total: int
    page: int
    size: int
    total_pages: int

# ===== SCHEMAS PARA BÚSQUEDAS Y FILTROS =====

class CatalogoFiltros(BaseModel):
    """Filtros para búsqueda de catálogos"""
    tipo_catalogo: Optional[str] = None
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    enabled: Optional[bool] = None
    orden_min: Optional[int] = None
    orden_max: Optional[int] = None

class MedicamentoFiltros(BaseModel):
    """Filtros para búsqueda de medicamentos"""
    nombre: Optional[str] = None
    principio_activo: Optional[str] = None
    laboratorio: Optional[str] = None
    categoria_terapeutica: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    requiere_receta: Optional[bool] = None
    precio_min: Optional[Decimal] = None
    precio_max: Optional[Decimal] = None
    activo: Optional[bool] = None

# ===== SCHEMAS PARA ESTADÍSTICAS =====

class EstadisticasCatalogo(BaseModel):
    """Estadísticas de catálogos"""
    total_tipos: int
    total_elementos: int
    elementos_activos: int
    elementos_inactivos: int
    tipos_mas_usados: List[Dict[str, Any]]

class EstadisticasMedicamentos(BaseModel):
    """Estadísticas de medicamentos"""
    total_medicamentos: int
    medicamentos_activos: int
    medicamentos_inactivos: int
    por_categoria: Dict[str, int]
    por_forma_farmaceutica: Dict[str, int]
    por_laboratorio: Dict[str, int]
    requieren_receta: int
    no_requieren_receta: int
    precio_promedio: Optional[Decimal] = None
    precio_maximo: Optional[Decimal] = None
    precio_minimo: Optional[Decimal] = None

# ===== SCHEMAS PARA OPERACIONES MASIVAS =====

class CatalogoImportItem(BaseModel):
    """Item para importación masiva de catálogos"""
    tipo_catalogo: str
    codigo: str
    descripcion: str
    descripcion_corta: Optional[str] = None
    valor1: Optional[str] = None
    valor2: Optional[str] = None
    valor3: Optional[str] = None
    orden: Optional[int] = None

class MedicamentoImportItem(BaseModel):
    """Item para importación masiva de medicamentos"""
    codigo: str
    nombre_comercial: str
    nombre_generico: Optional[str] = None
    principio_activo: Optional[str] = None
    concentracion: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    presentacion: Optional[str] = None
    laboratorio: Optional[str] = None
    codigo_atc: Optional[str] = None
    categoria_terapeutica: Optional[str] = None
    requiere_receta: bool = True
    precio_referencial: Optional[Decimal] = None

class ImportacionResponse(BaseModel):
    """Response para importaciones masivas"""
    total_procesados: int
    exitosos: int
    fallidos: int
    errores: List[str]
    advertencias: List[str]
    tiempo_procesamiento: float

# ===== SCHEMAS DE VALIDACIÓN =====

class ValidacionMedicamento(BaseModel):
    """Validación de medicamento"""
    medicamento_id: int
    codigo: str
    nombre: str
    disponible: bool
    activo: bool
    requiere_receta: bool
    observaciones: Optional[str] = None

class ValidacionCatalogo(BaseModel):
    """Validación de elemento de catálogo"""
    catalogo_id: int
    tipo_catalogo: str
    codigo: str
    descripcion: str
    activo: bool
    orden: Optional[int] = None