"""Database engine and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base para modelos ORM
Base = declarative_base()


def get_database_url() -> str:
    """Obtém DATABASE_URL e corrige prefixo postgres:// para postgresql://."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL não encontrada. Configure no arquivo .env ou variável de ambiente."
        )
    # Fix para Heroku/Neon que pode retornar postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def create_db_engine():
    """Cria engine com pool conservador e SSL para PostgreSQL."""
    url = get_database_url()

    # Pool pequeno para ambientes com limites de conexão
    # pool_pre_ping detecta conexões mortas
    engine = create_engine(
        url,
        pool_size=2,
        max_overflow=3,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recicla conexões a cada hora
        connect_args={"sslmode": "require"} if url.startswith("postgresql://") else {},
        echo=False,  # Mudar para True para debug SQL
    )
    return engine


# Engine global (criada na importação)
engine = create_db_engine()

# SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para FastAPI: retorna sessão DB e fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cria todas as tabelas (usado no bootstrap da API)."""
    Base.metadata.create_all(bind=engine)
