"""Sistema de sessão multi-tenant usando session ID na URL.

Cada browser/aba terá um session_id único na query string que identifica sua sessão.
Sem JavaScript, sem cookies, sem timing issues.
"""
import streamlit as st
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from utils.session_manager import save_session, clear_session

# Diretório para sessões
SESSION_DIR = Path(".sessions")
SESSION_DIR.mkdir(exist_ok=True)

SESSION_EXPIRY_DAYS = 7


def _get_or_create_session_id() -> str:
    """
    Obtém session_id da URL ou cria um novo.
    O session_id fica persistente na URL durante toda a sessão.
    """
    # Tenta pegar da URL
    if "sid" in st.query_params:
        return st.query_params["sid"]

    # Se não tem, cria novo e adiciona na URL
    new_sid = uuid.uuid4().hex[:16]  # 16 chars é suficiente
    st.query_params["sid"] = new_sid

    return new_sid


def _get_session_file(session_id: str) -> Path:
    """Retorna path do arquivo de sessão."""
    return SESSION_DIR / f"sess_{session_id}.json"


def save_auth_url_session(auth_token: str, user_info: dict):
    """
    Salva autenticação usando session_id da URL.
    """
    # Salva na sessão Streamlit normal
    save_session(auth_token, user_info)

    # Obtém session_id (cria se necessário)
    session_id = _get_or_create_session_id()

    # Salva no arquivo
    session_data = {
        "token": auth_token,
        "user": user_info,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)).isoformat()
    }

    session_file = _get_session_file(session_id)
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)


def restore_auth_url_session() -> bool:
    """
    Tenta restaurar sessão usando session_id da URL.
    Retorna True se restaurou com sucesso.
    """
    # Se já está autenticado, não faz nada
    if st.session_state.get("authenticated", False):
        return True

    # Se não tem session_id na URL, não há sessão para restaurar
    if "sid" not in st.query_params:
        return False

    session_id = st.query_params["sid"]
    session_file = _get_session_file(session_id)

    # Verifica se arquivo existe
    if not session_file.exists():
        return False

    try:
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        # Verifica expiração
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.now() > expires_at:
            # Sessão expirada, remove arquivo
            session_file.unlink()
            return False

        # Restaura sessão
        save_session(session_data["token"], session_data["user"])

        return True
    except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError):
        # Arquivo corrompido ou não encontrado, tenta remover
        if session_file.exists():
            session_file.unlink()
        return False


def clear_auth_url_session():
    """Remove autenticação persistente."""
    # Limpa sessão Streamlit
    clear_session()

    # Remove arquivo se existir
    if "sid" in st.query_params:
        session_id = st.query_params["sid"]
        session_file = _get_session_file(session_id)
        if session_file.exists():
            session_file.unlink()

    # Remove session_id da URL
    if "sid" in st.query_params:
        del st.query_params["sid"]


def cleanup_expired_sessions():
    """Remove sessões expiradas do diretório."""
    if not SESSION_DIR.exists():
        return

    now = datetime.now()
    for session_file in SESSION_DIR.glob("sess_*.json"):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)

            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if now > expires_at:
                session_file.unlink()
        except:
            # Arquivo corrompido, remove
            session_file.unlink()
