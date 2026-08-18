import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise AI Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev port
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]
    
    # AI / LLM Configuration
    DEFAULT_MODEL: str = "gpt-4o-mini"
    LLM_PROVIDER: str = "openai"  # Options: 'openai', 'mock'
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./enterprise_assistant.db")
    DEFAULT_CLIENT_ID: str = os.getenv("DEFAULT_CLIENT_ID", "default-client")

    # Qdrant Vector DB Configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = "enterprise_knowledge"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Auth0 Configuration
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
    AUTH0_AUDIENCE: str = os.getenv("AUTH0_AUDIENCE", "")
    AUTH0_ALGORITHMS: List[str] = ["RS256"]
    
    # Bypass / Mock Auth settings for local development
    BYPASS_AUTH: bool = os.getenv("BYPASS_AUTH", "true").lower() == "true"


    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
