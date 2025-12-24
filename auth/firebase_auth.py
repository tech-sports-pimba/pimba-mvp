"""Inicialização e utilities do Firebase Admin SDK."""
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Flag para garantir inicialização única
_firebase_initialized = False


def initialize_firebase():
    """
    Inicializa Firebase Admin SDK.
    Chamado no startup da API.
    """
    global _firebase_initialized

    if _firebase_initialized:
        logger.info("Firebase já inicializado, pulando...")
        return

    try:
        cred_dict = settings.firebase_credentials
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("✅ Firebase Admin SDK inicializado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Firebase: {e}")
        raise


def verify_firebase_token(id_token: str) -> dict:
    """
    Verifica Firebase ID token e retorna decoded token.

    Args:
        id_token: Token JWT do Firebase Auth

    Returns:
        dict: Decoded token com uid, email, etc

    Raises:
        ValueError: Se token for inválido
    """
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.warning(f"Token inválido: {e}")
        raise ValueError(f"Token Firebase inválido: {e}")


def get_firebase_user(uid: str) -> dict:
    """
    Busca usuário no Firebase por UID.

    Args:
        uid: Firebase UID

    Returns:
        dict: User record do Firebase

    Raises:
        ValueError: Se usuário não existir
    """
    try:
        user = firebase_auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "email_verified": user.email_verified,
        }
    except Exception as e:
        logger.warning(f"Usuário {uid} não encontrado: {e}")
        raise ValueError(f"Usuário não encontrado: {e}")


def create_firebase_user(email: str, password: str, display_name: str = None) -> dict:
    """
    Cria novo usuário no Firebase Auth.
    (Usado para criar personals/admins via admin panel)

    Args:
        email: Email do usuário
        password: Senha
        display_name: Nome opcional

    Returns:
        dict: User record criado
    """
    try:
        user = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
        )
        logger.info(f"✅ Usuário Firebase criado: {user.uid} ({email})")
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
        }
    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário Firebase: {e}")
        raise ValueError(f"Erro ao criar usuário: {e}")
