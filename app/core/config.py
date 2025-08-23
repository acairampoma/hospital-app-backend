from decouple import config
from typing import List

class Settings:
    # 🔐 JWT Configuration
    SECRET_KEY: str = config("SECRET_KEY", default="hospital-super-secret-key-development")
    ALGORITHM: str = "HS256" 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 🗄️ Database - Railway PostgreSQL (misma estrategia que galloapp_backend)
    DATABASE_URL: str = config(
        "DATABASE_URL",
        default="postgresql://postgres:QzlJMZtbYmqOxVSspnQAICcTDjkgOqMG@switchback.proxy.rlwy.net:43095/railway"
    )
    
    # 🌐 CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 🔄 Environment
    ENVIRONMENT: str = config("ENVIRONMENT", default="local")
    
    # 🏥 Hospital Configuration
    HOSPITAL_NAME: str = config("HOSPITAL_NAME", default="Hospital Digital")
    HOSPITAL_VERSION: str = "1.0.0"
    
    # 📄 PDF Configuration
    PDF_OUTPUT_PATH: str = config("PDF_OUTPUT_PATH", default="./temp_pdfs/")
    
    # 📧 SendGrid Configuration
    SENDGRID_API_KEY: str = config("SENDGRID_API_KEY", default="")
    SENDGRID_FROM_EMAIL: str = config("SENDGRID_FROM_EMAIL", default="noreply@hospital.com")
    SENDGRID_FROM_NAME: str = config("SENDGRID_FROM_NAME", default="IA Medical Solutions")
    
    # 📷 Cloudinary - Configurado directo sin env vars (como galloapp)

settings = Settings()