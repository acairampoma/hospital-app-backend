# Hospital App Backend

FastAPI backend para sistema hospitalario con arquitectura de microservicios.

## Stack Tecnológico

- **Framework**: FastAPI
- **Database**: PostgreSQL (Railway)
- **ORM**: SQLAlchemy (Async)
- **Authentication**: JWT + Refresh Tokens
- **Security**: Bcrypt

## Características

- 🔐 Autenticación JWT con refresh tokens
- 👥 Gestión de usuarios médicos
- 📋 Catálogos médicos y vademécum
- 💊 Sistema de prescripciones médicas
- 📝 Notas médicas con soporte de audio
- 🧪 Órdenes médicas (laboratorio, imagenología)
- 🏥 Gestión de camas hospitalarias
- ⚡ Conexiones 100% async no bloqueantes

## Instalación

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Crear archivo `.env`:

```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Ejecución

```bash
# Desarrollo
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Documentación API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estructura del Proyecto

```
hospital-app-back/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── usuarios.py
│   │       ├── catalogos.py
│   │       ├── recetas.py
│   │       ├── notas.py
│   │       ├── ordenes.py
│   │       └── listas.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── database.py
├── main.py
├── requirements.txt
└── .env
```

## Licencia

Proprietary - Hospital System