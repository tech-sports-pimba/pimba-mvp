"""Sistema de sessão persistente usando arquivo único global.

Ideal para desenvolvimento local e deploy single-user.
Para produção multi-user, usar cookies seria necessário.
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timedelta
from utils.session_manager import save_session, clear_session

# Arquivo único de sessão
SESSION_FILE = Path(".current_session.json")
SESSION_EXPIRY_DAYS = 7


def save_auth_single_file(auth_token: str, user_info: dict):
    """
    Salva autenticação em arquivo único.
    """
    # Salva na sessão Streamlit normal
    save_session(auth_token, user_info)

    # Salva no arquivo
    session_data = {
        "token": auth_token,
        "user": user_info,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)).isoformat()
    }

    with open(SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=2)


def restore_auth_single_file() -> bool:
    """
    Tenta restaurar sessão do arquivo único.
    Retorna True se restaurou com sucesso.
    """
    # Se já está autenticado, não faz nada
    if st.session_state.get("authenticated", False):
        return True

    # Verifica se arquivo existe
    if not SESSION_FILE.exists():
        return False

    try:
        with open(SESSION_FILE, 'r') as f:
            session_data = json.load(f)

        # Verifica expiração
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.now() > expires_at:
            # Sessão expirada, remove arquivo
            SESSION_FILE.unlink()
            return False

        # Restaura sessão
        save_session(session_data["token"], session_data["user"])

        return True
    except (json.JSONDecodeError, KeyError, ValueError):
        # Arquivo corrompido, remove
        SESSION_FILE.unlink()
        return False


def clear_auth_single_file():
    """Remove autenticação persistente."""
    # Limpa sessão Streamlit
    clear_session()

    # Remove arquivo
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
