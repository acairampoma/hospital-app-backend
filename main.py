from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import cloudinary

# 🗄️ Importar modelos ANTES que los routers
from app.models import *  # Importa todos los modelos

# Importar configuración
from app.core.config import settings

# Importar router principal
from app.api.v1 import api_router

# 📸 Configurar Cloudinary GLOBAL (credenciales correctas del galloapp)
cloudinary.config(
    cloud_name="dz4czc3en",
    api_key="455285241939111", 
    api_secret="1uzQrkFD1Rbj8vPOClFBUEIwBn0"
)

# 🏥 HOSPITAL APP BACKEND - REPLICANDO MONOREPO JAVA
app = FastAPI(
    title="Hospital Management System API",
    description="🏥 Sistema hospitalario completo - FastAPI version del monorepo Java",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 REGISTRAR ROUTER PRINCIPAL CON TODOS LOS ENDPOINTS
app.include_router(api_router, prefix="/api/v1")

# 🚀 HEALTH CHECK GLOBAL
@app.get("/health")
async def health_check():
    """🏥 Health check del sistema hospitalario"""
    return {
        "status": "UP",
        "system": "Hospital Management System",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "microservices_replicated": [
            "✅ microservicio-usuarios",
            "✅ microservicio-catalogos", 
            "✅ microservicio-receta",
            "✅ microservicio-notas",
            "✅ microservicio-orden",
            "✅ microservicio-listas"
        ],
        "endpoints_count": "120+",
        "architecture": "FastAPI Monolith replicating Java Microservices"
    }

# 📊 INFO GENERAL
@app.get("/info")
async def system_info():
    """📊 Información completa del sistema"""
    return {
        "name": "Hospital Management System",
        "description": "🏥 Sistema hospitalario completo replicando monorepo Java",
        "version": "1.0.0",
        "framework": "FastAPI",
        "database": "PostgreSQL bd_hdigital",
        "original_architecture": "Spring Boot 3.2.5 + Java 17 Microservices",
        "replicated_services": {
            "oauth2": "Replicado como /api/v1/auth",
            "usuarios": "Replicado como /api/v1/usuarios", 
            "catalogos": "Replicado como /api/v1/catalogos",
            "receta": "Replicado como /api/v1/recetas",
            "notas": "Replicado como /api/v1/notas",
            "orden": "Replicado como /api/v1/ordenes",
            "listas": "Replicado como /api/v1/listas"
        },
        "features": [
            "🔐 JWT Authentication + Refresh Tokens",
            "👥 User Management",
            "🔍 Medical Catalogs Search",
            "💊 Prescription Management",
            "📝 Medical Notes with PDF",
            "📋 Medical Orders & Exams",
            "🏥 Hospital Structure & Beds",
            "📊 Statistics & Reports"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )