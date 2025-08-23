from fastapi import APIRouter
from app.api.v1 import auth, usuarios, catalogos, recetas, notas, ordenes, listas, upload

api_router = APIRouter()

# Registrar todas las rutas de la API v1
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["Users Management"])
api_router.include_router(catalogos.router, prefix="/catalogos", tags=["Catalogs & Medications"])
api_router.include_router(recetas.router, prefix="/recetas", tags=["Medical Prescriptions"])
api_router.include_router(notas.router, prefix="/notas", tags=["Medical Notes"])
api_router.include_router(ordenes.router, prefix="/ordenes", tags=["Medical Orders"])
api_router.include_router(listas.router, prefix="/listas", tags=["Hospital Lists & Beds"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload & Registration"])

# Endpoint principal de salud de la API
@api_router.get("/health", tags=["Health Check"])
async def api_health():
    """Health check general de la API Hospital"""
    
    return {
        "status": "UP",
        "service": "Hospital Management API",
        "version": "1.0.0",
        "modules": {
            "auth": "Authentication & Authorization",
            "usuarios": "Medical Users Management", 
            "catalogos": "Medical Catalogs & Medications",
            "recetas": "Medical Prescriptions",
            "notas": "Medical Notes & Documentation",
            "ordenes": "Medical Orders (Lab, Imaging, etc)",
            "listas": "Hospital Lists & Bed Management"
        },
        "features": [
            "JWT Authentication with Refresh Tokens",
            "Medical Staff Management",
            "Medical Catalogs & Drug Vademecum", 
            "Digital Prescription System",
            "Medical Notes with Audio/PDF Support",
            "Medical Orders Management",
            "Hospital Bed & Patient Assignment",
            "Statistics & Reporting",
            "Hospital Structure Management"
        ],
        "database": "PostgreSQL with AsyncPG (Non-blocking)",
        "architecture": "Clean Architecture with Service Layer",
        "documentation": "/docs (Swagger UI) | /redoc (ReDoc)"
    }