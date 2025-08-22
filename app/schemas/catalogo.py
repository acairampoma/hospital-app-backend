from pydantic import BaseModel, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class CatalogoBase(BaseModel):
    """Base schema para catálogos"""
    codigo: str
    descripcion: str
    tabla_origen: Optional[str] = None
    categoria: Optional[str] = None
    tipo: Optional[str] = None
    activo: bool = True

class CatalogoCreate(CatalogoBase):
    """Create catálogo schema"""
    pass

class CatalogoUpdate(BaseModel):
    """Update catálogo schema"""
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    tipo: Optional[str] = None
    activo: Optional[bool] = None

class CatalogoResponse(CatalogoBase):
    """Catálogo response - Compatible con CatalogosController"""
    id: int
    valor_numerico: Optional[Decimal] = None
    campo_extra1: Optional[str] = None
    campo_extra2: Optional[str] = None
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CatalogoSearchRequest(BaseModel):
    """Request de búsqueda en catálogos"""
    q: str  # Término de búsqueda
    tabla_origen: Optional[str] = None
    categoria: Optional[str] = None
    activo: bool = True
    
    @validator('q')
    def validate_search_term(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El término de búsqueda debe tener al menos 2 caracteres')
        return v.strip()

# 💊 MEDICAMENTO VADEMÉCUM SCHEMAS

class MedicamentoBase(BaseModel):
    """Base schema para medicamentos"""
    codigo: str
    nombre_comercial: str
    nombre_generico: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    concentracion: Optional[str] = None
    laboratorio: Optional[str] = None
    categoria_terapeutica: Optional[str] = None

class MedicamentoCreate(MedicamentoBase):
    """Create medicamento schema"""
    indicaciones: Optional[str] = None
    contraindicaciones: Optional[str] = None
    posologia: Optional[str] = None
    requiere_receta: bool = True
    controlado: bool = False

class MedicamentoUpdate(BaseModel):
    """Update medicamento schema"""
    nombre_comercial: Optional[str] = None
    nombre_generico: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    concentracion: Optional[str] = None
    laboratorio: Optional[str] = None
    categoria_terapeutica: Optional[str] = None
    indicaciones: Optional[str] = None
    contraindicaciones: Optional[str] = None
    posologia: Optional[str] = None
    precio_referencial: Optional[Decimal] = None
    stock_disponible: Optional[int] = None
    activo: Optional[bool] = None

class MedicamentoResponse(MedicamentoBase):
    """Medicamento response"""
    id: int
    indicaciones: Optional[str] = None
    contraindicaciones: Optional[str] = None
    posologia: Optional[str] = None
    requiere_receta: bool = True
    controlado: bool = False
    activo: bool = True
    precio_referencial: Optional[Decimal] = None
    stock_disponible: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Propiedades calculadas
    descripcion_completa: str = ""
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # Calcular descripción completa
        desc = self.nombre_comercial
        if self.concentracion:
            desc += f" {self.concentracion}"
        if self.forma_farmaceutica:
            desc += f" ({self.forma_farmaceutica})"
        self.descripcion_completa = desc

class MedicamentoSearchRequest(BaseModel):
    """Request de búsqueda de medicamentos"""
    q: Optional[str] = None
    categoria: Optional[str] = None
    laboratorio: Optional[str] = None
    requiere_receta: Optional[bool] = None
    activo: bool = True
    
    @validator('q')
    def validate_search_term(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('El término de búsqueda debe tener al menos 2 caracteres')
        return v.strip() if v else None

# 📊 RESPONSES DE ESTADÍSTICAS

class CategoriaStats(BaseModel):
    """Estadísticas por categoría"""
    categoria: str
    total: int
    activos: int

class CatalogoStatsResponse(BaseModel):
    """Estadísticas generales de catálogos"""
    total_catalogos: int
    total_medicamentos: int
    categorias_disponibles: int
    tipos_tabla: List[str]
    stats_por_categoria: List[CategoriaStats]