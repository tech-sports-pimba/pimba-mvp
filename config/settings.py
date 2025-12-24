"""Configurações do sistema via variáveis de ambiente."""
from pydantic_settings import BaseSettings
from pydantic import Field
import json
import os


def _get_from_streamlit_secrets(key: str, default=None):
    """
    Tenta obter valor de st.secrets (Streamlit Cloud).
    Se não estiver disponível, retorna o default.
    """
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return default


class Settings(BaseSettings):
    """Configurações da aplicação."""

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    # Firebase
    FIREBASE_SERVICE_ACCOUNT_KEY: str = Field(
        ...,
        description="Firebase service account JSON (string ou path)"
    )
    FIREBASE_WEB_CONFIG: str = Field(
        default="",
        description="Firebase Web SDK config JSON (opcional, para modo produção)"
    )

    # API
    API_HOST: str = Field(default="127.0.0.1", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    SECRET_KEY: str = Field(..., description="Secret key for security")

    # Flags
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Credenciais de desenvolvimento (apenas quando DEBUG=True)
    DEV_ADMIN_UID: str = Field(default="dev-mock-uid-admin")
    DEV_ADMIN_EMAIL: str = Field(default="admin@pimba.com")
    DEV_ADMIN_NAME: str = Field(default="Admin")
    DEV_ADMIN_TOKEN: str = Field(default="dev-mock-token")

    DEV_PERSONAL_UID: str = Field(default="dev-mock-uid-personal")
    DEV_PERSONAL_EMAIL: str = Field(default="personal@pimba.com")
    DEV_PERSONAL_NAME: str = Field(default="Personal Trainer")
    DEV_PERSONAL_TOKEN: str = Field(default="dev-mock-token-personal")
    DEV_PERSONAL_ID: int = Field(default=1)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignora variáveis extras no .env
    }

    def __init__(self, **kwargs):
        """
        Inicializa Settings.
        Prioridade: kwargs > st.secrets > .env > defaults
        """
        # Tenta carregar de st.secrets primeiro (Streamlit Cloud)
        streamlit_values = {}
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                # Pega todos os valores de secrets
                for key in ['DATABASE_URL', 'FIREBASE_SERVICE_ACCOUNT_KEY', 'FIREBASE_WEB_CONFIG',
                           'SECRET_KEY', 'API_HOST', 'API_PORT', 'DEBUG']:
                    if key in st.secrets:
                        streamlit_values[key] = st.secrets[key]
        except:
            pass

        # Merge: kwargs sobrescreve st.secrets
        merged_values = {**streamlit_values, **kwargs}
        super().__init__(**merged_values)

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
