"""Configurações do sistema via variáveis de ambiente."""
from pydantic_settings import BaseSettings
from pydantic import Field
import json
import os


class Settings(BaseSettings):
    """Configurações da aplicação."""

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    # Firebase
    FIREBASE_SERVICE_ACCOUNT_KEY: str = Field(
        ...,
        description="Firebase service account JSON (string ou path)"
    )

    # API
    API_HOST: str = Field(default="127.0.0.1", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    SECRET_KEY: str = Field(..., description="Secret key for security")

    # Flags
    DEBUG: bool = Field(default=False, description="Debug mode")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }

    @property
    def firebase_credentials(self) -> dict:
        """
        Parse Firebase credentials.
        Suporta:
        - JSON string direto
        - Caminho para arquivo JSON
        """
        key = self.FIREBASE_SERVICE_ACCOUNT_KEY

        # Tenta parsear como JSON string
        try:
            return json.loads(key)
        except json.JSONDecodeError:
            pass

        # Se não for JSON, assume que é path para arquivo
        if os.path.exists(key):
            with open(key, 'r') as f:
                return json.load(f)

        raise ValueError(
            "FIREBASE_SERVICE_ACCOUNT_KEY deve ser um JSON válido ou caminho para arquivo JSON"
        )


# Instância global de settings
settings = Settings()
