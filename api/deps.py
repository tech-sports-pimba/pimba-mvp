"""Dependencies da API FastAPI."""
from core.database import get_db

# Re-exporta get_db para uso nos routers
__all__ = ["get_db"]
