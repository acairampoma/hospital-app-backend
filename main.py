from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
import cloudinary
from datetime import datetime

# 🗄️ Importar modelos ANTES que los routers
from app.models import *  # Importa todos los modelos

# Importar configuración
from app.core.config import settings

# Importar router principal
from app.api.v1 import api_router

# Importar servicios para templates
from app.database import get_db
from app.services.auth_service import AuthService

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

# 🎨 CONFIGURAR ARCHIVOS ESTÁTICOS Y TEMPLATES
app.mount("/static", StaticFiles(directory="../front/hospital-app/static"), name="static")
templates = Jinja2Templates(directory="../front/hospital-app/templates")

# 🔥 REGISTRAR ROUTER PRINCIPAL CON TODOS LOS ENDPOINTS
app.include_router(api_router, prefix="/api/v1")

# 🔐 RUTAS DE TEMPLATES - MÓDULO SEGURIDAD ÉPICO
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """🔐 Página de Login con datos dinámicos"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "sistema": {
            "nombre": "IA Medical Solutions",
            "version": "1.0.0",
            "año": datetime.now().year,
            "demo_user": "admin",
            "demo_pass": "123456"
        }
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: AsyncSession = Depends(get_db)):
    """🏥 Dashboard con datos del doctor"""
    try:
        # TODO: Obtener user_id del token JWT
        user_id = 1  # Temporal para desarrollo
        
        # Obtener datos del usuario directamente del servicio
        user = await AuthService.get_user_by_id(db, user_id)
        
        if not user:
            # Redireccionar a login si no hay usuario
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Sesión expirada. Por favor inicia sesión nuevamente."
            })
        
        # Estadísticas del dashboard
        estadisticas = {
            "pacientes_hoy": 25,
            "citas_pendientes": 8,
            "consultas_completadas": 12,
            "pacientes_nuevos": 5
        }
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "doctor": {
                "id": user.id,
                "nombre_completo": user.nombre_completo or f"{user.first_name} {user.last_name}",
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "especialidad": user.especialidad,
                "colegiatura": user.colegiatura,
                "cargo": user.cargo,
                "telefono": user.telefono,
                "foto_url": user.datos_profesional.get('foto_url') if user.datos_profesional else None,
                "is_medico": bool(user.especialidad and user.colegiatura)
            },
            "estadisticas": estadisticas,
            "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
            "hora_actual": datetime.now().strftime("%H:%M")
        })
        
    except Exception as e:
        # En caso de error, mostrar login
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Error cargando datos. Por favor intenta nuevamente."
        })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """📝 Página de Registro con especialidades dinámicas"""
    especialidades = [
        "Medicina General",
        "Cardiología", 
        "Neurología",
        "Pediatría",
        "Traumatología",
        "Ginecología",
        "Urología",
        "Dermatología",
        "Psiquiatría",
        "Oncología"
    ]
    
    return templates.TemplateResponse("register.html", {
        "request": request,
        "especialidades": especialidades,
        "año_actual": datetime.now().year
    })

@app.get("/perfil", response_class=HTMLResponse)  
async def perfil_page(request: Request, db: AsyncSession = Depends(get_db)):
    """👤 Página de Perfil del usuario"""
    try:
        # TODO: Obtener user_id del token JWT  
        user_id = 1  # Temporal
        
        user = await AuthService.get_user_by_id(db, user_id)
        
        if not user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Sesión expirada"
            })
        
        return templates.TemplateResponse("perfil.html", {
            "request": request,
            "usuario": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "nombre_completo": user.nombre_completo,
                "especialidad": user.especialidad,
                "colegiatura": user.colegiatura,
                "cargo": user.cargo,
                "telefono": user.telefono,
                "foto_url": user.datos_profesional.get('foto_url') if user.datos_profesional else None,
                "created_at": user.created_at.strftime("%d/%m/%Y") if user.created_at else None,
                "last_login": user.last_login.strftime("%d/%m/%Y %H:%M") if user.last_login else "Nunca"
            }
        })
        
    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Error cargando perfil"
        })

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