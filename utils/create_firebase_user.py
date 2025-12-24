"""Cria usuário de teste no Firebase Authentication."""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import auth, credentials
from config.settings import settings

# Inicializa Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.firebase_credentials)
    firebase_admin.initialize_app(cred)

def create_user(email: str, password: str, display_name: str):
    """Cria usuário no Firebase Authentication."""
    try:
        # Verifica se usuário já existe
        try:
            existing_user = auth.get_user_by_email(email)
            print(f"⚠️  Usuário '{email}' já existe!")
            print(f"   UID: {existing_user.uid}")
            return existing_user
        except auth.UserNotFoundError:
            pass

        # Cria novo usuário
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=True  # Marca como verificado
        )

        print(f"✅ Usuário criado com sucesso!")
        print(f"   Email: {email}")
        print(f"   UID: {user.uid}")
        print(f"   Nome: {display_name}")

        return user

    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return None


if __name__ == "__main__":
    print("🔐 Criando usuário de teste no Firebase...\n")

    # Cria personal de teste
    create_user(
        email="personal@pimba.com",
        password="senha123",
        display_name="Personal Trainer"
    )

    print("\n💡 Use estas credenciais para fazer login:")
    print("   Email: personal@pimba.com")
    print("   Senha: senha123")
