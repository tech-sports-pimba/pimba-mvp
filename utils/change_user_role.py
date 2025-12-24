"""Script para alterar role de um usuário."""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.database import SessionLocal
from core.models import User, Personal
from core.enums import UserRole

def list_users():
    """Lista todos os usuários."""
    db = SessionLocal()
    try:
        users = db.query(User).all()

        print("\n📋 Usuários cadastrados:\n")
        print(f"{'ID':<5} {'Email':<30} {'Nome':<25} {'Role':<10} {'Ativo'}")
        print("-" * 95)

        for user in users:
            ativo = "✅" if user.ativo else "❌"
            print(f"{user.id:<5} {user.email:<30} {user.nome:<25} {user.role.value:<10} {ativo}")

        print()
        return users
    finally:
        db.close()


def change_user_role(user_id: int, new_role: str):
    """Altera o role de um usuário."""
    db = SessionLocal()
    try:
        # Busca usuário
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            print(f"❌ Usuário com ID {user_id} não encontrado!")
            return

        # Valida role
        try:
            role_enum = UserRole(new_role.lower())
        except ValueError:
            print(f"❌ Role inválido: {new_role}")
            print(f"   Roles válidos: admin, personal, aluno")
            return

        old_role = user.role.value
        user.role = role_enum

        # Se virar personal, cria registro Personal se não existir
        if role_enum == UserRole.PERSONAL:
            existing_personal = db.query(Personal).filter(Personal.user_id == user.id).first()
            if not existing_personal:
                personal = Personal(
                    user_id=user.id,
                    telefone="",
                    especializacao="",
                )
                db.add(personal)
                db.flush()
                print(f"✅ Registro Personal criado automaticamente (ID: {personal.id})")

        db.commit()

        print(f"\n✅ Role alterado com sucesso!")
        print(f"   Usuário: {user.nome} ({user.email})")
        print(f"   {old_role} → {role_enum.value}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Gerenciador de Roles de Usuários\n")

    # Lista usuários
    users = list_users()

    if not users:
        print("❌ Nenhum usuário cadastrado!")
        sys.exit(1)

    # Pega input do usuário
    try:
        user_id = int(input("Digite o ID do usuário: "))

        print("\nRoles disponíveis:")
        print("  - admin     (Administrador do sistema)")
        print("  - personal  (Personal Trainer)")
        print("  - aluno     (Aluno/Cliente)")

        new_role = input("\nDigite o novo role: ").strip().lower()

        # Confirma
        confirm = input(f"\n⚠️  Confirma alteração para '{new_role}'? (s/n): ").lower()

        if confirm == 's':
            change_user_role(user_id, new_role)
        else:
            print("❌ Operação cancelada")

    except ValueError:
        print("❌ ID inválido!")
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada")
    except Exception as e:
        print(f"❌ Erro: {e}")
