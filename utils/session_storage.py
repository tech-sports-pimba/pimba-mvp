"""Sistema de sessão persistente server-side usando arquivo temporário."""
import json
import os
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta

# Diretório para armazenar sessões
SESSION_DIR = Path(".sessions")
SESSION_DIR.mkdir(exist_ok=True)

# Tempo de expiração: 7 dias
SESSION_EXPIRY_DAYS = 7


def _get_session_file(session_id: str) -> Path:
    """Retorna path do arquivo de sessão."""
    return SESSION_DIR / f"{session_id}.json"


def save_session_persistent(session_id: str, auth_token: str, user_info: dict):
    """
    Salva sessão em arquivo server-side.

    Args:
        session_id: ID único da sessão (gerado pelo browser)
        auth_token: Token de autenticação
        user_info: Informações do usuário
    """
    session_data = {
        "token": auth_token,
        "user": user_info,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)).isoformat()
    }

    session_file = _get_session_file(session_id)
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)


def load_session_persistent(session_id: str) -> Optional[Dict]:
    """
    Carrega sessão do arquivo server-side.

    Args:
        session_id: ID único da sessão

    Returns:
        Dict com 'token' e 'user', ou None se não existir/expirada
    """
    session_file = _get_session_file(session_id)

    if not session_file.exists():
        return None

    try:
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        # Verifica expiração
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.now() > expires_at:
            # Sessão expirada, remove arquivo
            session_file.unlink()
            return None

        return {
            "token": session_data["token"],
            "user": session_data["user"]
        }
    except (json.JSONDecodeError, KeyError, ValueError):
        # Arquivo corrompido, remove
        session_file.unlink()
        return None


def delete_session_persistent(session_id: str):
    """Remove sessão do storage."""
    session_file = _get_session_file(session_id)
    if session_file.exists():
        session_file.unlink()


def cleanup_expired_sessions():
    """Remove sessões expiradas (chamado periodicamente)."""
    if not SESSION_DIR.exists():
        return

    now = datetime.now()
    for session_file in SESSION_DIR.glob("*.json"):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)

            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if now > expires_at:
                session_file.unlink()
        except:
            # Arquivo corrompido, remove
            session_file.unlink()
