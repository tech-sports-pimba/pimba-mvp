"""Script para popular banco de dados com dados de teste."""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.database import SessionLocal
from core.models import User, Personal, Aluno
from core.enums import UserRole
from config.settings import settings
from datetime import date, datetime
import sys

def seed_database():
    """Popula banco com dados de teste."""
    db = SessionLocal()

    try:
        print("🌱 Iniciando seed do banco de dados...")

        # 1. Criar usuário Personal de teste
        print("\n👨‍💼 Criando Personal de teste...")

        # Verifica se já existe
        existing_user = db.query(User).filter(User.email == settings.DEV_PERSONAL_EMAIL).first()
        if existing_user:
            print(f"⚠️  Personal '{settings.DEV_PERSONAL_EMAIL}' já existe. Pulando...")
            personal = db.query(Personal).filter(Personal.user_id == existing_user.id).first()
        else:
            # Cria User
            user = User(
                firebase_uid=settings.DEV_PERSONAL_UID,
                email=settings.DEV_PERSONAL_EMAIL,
                nome=settings.DEV_PERSONAL_NAME,
                role=UserRole.PERSONAL,
                ativo=True,
            )
            db.add(user)
            db.flush()

            # Cria Personal
            personal = Personal(
                user_id=user.id,
                telefone="+55 11 98765-4321",
                especializacao="Funcional e Musculação",
                bio="Personal trainer com 10 anos de experiência em treinamento funcional e musculação."
            )
            db.add(personal)
            db.flush()

            print(f"✅ Personal criado: {user.nome} (ID: {personal.id})")

        # 2. Criar alunos de teste
        print("\n👥 Criando alunos de teste...")

        alunos_teste = [
            {
                "nome": "João Silva",
                "email": "joao@exemplo.com",
                "telefone": "+55 11 91111-1111",
                "data_nascimento": date(1990, 5, 15),
                "objetivo": "Perder peso e ganhar massa muscular",
                "ativo": True,
            },
            {
                "nome": "Maria Santos",
                "email": "maria@exemplo.com",
                "telefone": "+55 11 92222-2222",
                "data_nascimento": date(1985, 8, 22),
                "objetivo": "Melhorar condicionamento físico",
                "ativo": True,
            },
            {
                "nome": "Pedro Oliveira",
                "email": "pedro@exemplo.com",
                "telefone": "+55 11 93333-3333",
                "data_nascimento": date(1995, 3, 10),
                "objetivo": "Ganhar massa muscular",
                "ativo": True,
            },
            {
                "nome": "Ana Costa",
                "email": "ana@exemplo.com",
                "telefone": "+55 11 94444-4444",
                "data_nascimento": date(1988, 11, 5),
                "objetivo": "Emagrecimento e definição",
                "ativo": True,
            },
            {
                "nome": "Carlos Souza",
                "email": "carlos@exemplo.com",
                "telefone": "+55 11 95555-5555",
                "data_nascimento": date(1992, 7, 18),
                "objetivo": "Hipertrofia",
                "ativo": False,  # Um inativo para teste
            },
        ]

        alunos_criados = 0
        for aluno_data in alunos_teste:
            # Verifica se já existe
            existing = db.query(Aluno).filter(
                Aluno.email == aluno_data["email"],
                Aluno.personal_id == personal.id
            ).first()

            if existing:
                print(f"⚠️  Aluno '{aluno_data['nome']}' já existe. Pulando...")
                continue

            aluno = Aluno(
                personal_id=personal.id,
                **aluno_data
            )
            db.add(aluno)
            alunos_criados += 1
            print(f"✅ Aluno criado: {aluno_data['nome']}")

        db.commit()

        print(f"\n🎉 Seed concluído com sucesso!")
        print(f"   - {alunos_criados} aluno(s) criado(s)")
        print(f"   - Personal ID: {personal.id}")
        print(f"\n💡 Modo Desenvolvimento (DEBUG=True):")
        print(f"   - Clique em 'Personal' na tela de login")
        print(f"   - Email: {settings.DEV_PERSONAL_EMAIL}")

    except Exception as e:
        print(f"\n❌ Erro ao fazer seed: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
