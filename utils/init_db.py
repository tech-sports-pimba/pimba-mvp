"""Inicializa o banco de dados criando todas as tabelas."""
import sys
from pathlib import Path

# Adiciona o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# IMPORTANTE: Carregar .env ANTES de importar qualquer módulo
from dotenv import load_dotenv
load_dotenv()

from core.database import engine, Base
from core.models import User, Personal, Aluno, Agendamento, FichaTreino, Exercicio, Pagamento, RegistroEvolucao


def init_db():
    """Cria todas as tabelas no banco de dados."""
    print("🔧 Inicializando banco de dados...")
    print(f"📊 Conectando em: {engine.url}")

    try:
        # Cria todas as tabelas
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")

        # Lista as tabelas criadas
        print("\n📋 Tabelas criadas:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")

    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        raise


if __name__ == "__main__":
    init_db()
