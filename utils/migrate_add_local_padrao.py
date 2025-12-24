"""Migration: Adiciona campo local_padrao à tabela alunos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine

def migrate():
    """Adiciona coluna local_padrao."""
    print("🔄 Adicionando coluna local_padrao à tabela alunos...")

    try:
        with engine.connect() as conn:
            # Verifica se coluna já existe
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='alunos' AND column_name='local_padrao'
            """))

            if result.fetchone():
                print("⚠️  Coluna local_padrao já existe. Nada a fazer.")
                return

            # Adiciona coluna
            conn.execute(text("""
                ALTER TABLE alunos
                ADD COLUMN local_padrao VARCHAR(500)
            """))
            conn.commit()

            print("✅ Coluna local_padrao adicionada com sucesso!")

    except Exception as e:
        print(f"❌ Erro na migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
