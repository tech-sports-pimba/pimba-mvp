"""Script para adicionar admin ao banco de dados."""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.database import SessionLocal
from core.models import User
from core.enums import UserRole

def add_admin():
    """Adiciona ou atualiza usuário admin."""
    db = SessionLocal()

    try:
        print("👨‍💼 Adicionando admin ao banco de dados...")

        # Dados do admin Firebase
        firebase_uid = "aZCDWf9GH5WgWakXYEosE1N4QKM2"
        email = "admin@pimba.com"
        nome = "Admin"

        # Verifica se já existe
        existing_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

        if existing_user:
            print(f"⚠️  Usuário com firebase_uid já existe: {existing_user.email}")
            print(f"   Atualizando dados...")

            existing_user.email = email
            existing_user.nome = nome
            existing_user.role = UserRole.ADMIN
            existing_user.ativo = True

            print(f"✅ Admin atualizado: {nome} ({email})")
        else:
            # Verifica se existe com mesmo email
            existing_by_email = db.query(User).filter(User.email == email).first()

            if existing_by_email:
                print(f"⚠️  Usuário com email já existe: {existing_by_email.email}")
                print(f"   Atualizando firebase_uid...")

                existing_by_email.firebase_uid = firebase_uid
                existing_by_email.nome = nome
                existing_by_email.role = UserRole.ADMIN
                existing_by_email.ativo = True

                print(f"✅ Admin atualizado: {nome} ({email})")
            else:
                # Cria novo User
                user = User(
                    firebase_uid=firebase_uid,
                    email=email,
                    nome=nome,
                    role=UserRole.ADMIN,
                    ativo=True,
                )
                db.add(user)
                print(f"✅ Admin criado: {nome} ({email})")

        db.commit()

        print(f"\n🎉 Admin configurado com sucesso!")
        print(f"\n💡 Credenciais para login:")
        print(f"   Email: {email}")
        print(f"   Senha: abc456")
        print(f"   Firebase UID: {firebase_uid}")

    except Exception as e:
        print(f"\n❌ Erro ao adicionar admin: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    add_admin()
