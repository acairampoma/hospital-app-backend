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
    
    # 📧 Email Configuration (opcional para notificaciones)
    SMTP_HOST: str = config("SMTP_HOST", default="")
    SMTP_PORT: int = config("SMTP_PORT", default=587, cast=int)
    SMTP_USER: str = config("SMTP_USER", default="")
    SMTP_PASSWORD: str = config("SMTP_PASSWORD", default="")

settings = Settings()