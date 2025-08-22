from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# 🚀 CONEXIÓN ASYNC NO BLOQUEANTE - asyncpg
# Convertir URL a async (postgresql+asyncpg)
async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Crear async engine
async_engine = create_async_engine(
    async_database_url,
    # Configuración optimizada ASYNC
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,  # True para debug SQL
    future=True
)

# Crear AsyncSessionLocal
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# Base para modelos
Base = declarative_base()

# 🔗 Dependency ASYNC para obtener sesión de BD
async def get_db():
    """Obtener sesión ASYNC de base de datos"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 🏥 Función para inicializar BD
def init_db():
    """Inicializar base de datos - crear tablas si no existen"""
    # Importar todos los modelos para que SQLAlchemy los registre
    from app.models import user, catalogos, receta, nota, orden, lista
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas de BD inicializadas correctamente")