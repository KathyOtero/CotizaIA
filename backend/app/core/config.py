import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "CotizaAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Base de datos
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://cotiza_admin:cotiza_password123@localhost:5432/cotizaai"
    )
    
    # Seguridad
    JWT_SECRET: str = os.getenv("JWT_SECRET", "cotizaai-super-secret-key-development-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 día
    
    # Proveedor LLM en capa gratuita
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Reglas de negocio por defecto
    MARGEN_MINIMO_DEFAULT: float = 25.0  # 25% de margen mínimo configurable
    IVA_DEFAULT: float = 19.0           # 19% IVA Colombia

settings = Settings()
