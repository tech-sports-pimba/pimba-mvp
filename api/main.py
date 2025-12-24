"""FastAPI app principal."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_db
from auth.firebase_auth import initialize_firebase
from api.routers import auth, users, alunos
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pimba API",
    description="API multi-tenant para gestão de personal trainers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (API interna, mas permite acesso do Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: permite tudo. Produção: restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Inicializa serviços no startup."""
    logger.info("🚀 Iniciando Pimba API...")

    # Inicializa Firebase Admin SDK
    try:
        initialize_firebase()
    except Exception as e:
        logger.error(f"❌ Falha ao inicializar Firebase: {e}")
        # Continue mesmo com erro - permitir desenvolvimento sem Firebase configurado
        # Em produção, considere fazer raise aqui

    # Cria tabelas no banco (MVP: create_all. Produção: usar Alembic migrations)
    try:
        init_db()
        logger.info("✅ Database inicializado")
    except Exception as e:
        logger.error(f"❌ Falha ao inicializar database: {e}")
        raise


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "pimba-api",
        "version": "0.1.0"
    }


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(alunos.router)

logger.info("✅ Pimba API carregada com sucesso")
