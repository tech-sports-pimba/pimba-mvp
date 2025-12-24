"""Script para criar tabela de sessões."""
from dotenv import load_dotenv
load_dotenv()

from core.database import engine
from core.models import Base, Session

# Cria apenas a tabela sessions
Base.metadata.create_all(bind=engine, tables=[Session.__table__])
print('✅ Tabela sessions criada com sucesso!')
