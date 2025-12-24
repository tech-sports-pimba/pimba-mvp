"""Sistema de sessão persistente SIMPLES usando apenas arquivos server-side."""
import streamlit as st
import uuid
from utils.session_storage import (
    save_session_persistent,
    load_session_persistent,
    delete_session_persistent
)
from utils.session_manager import save_session, clear_session


def _get_or_create_session_id() -> str:
    """
    Obtém ou cria session_id único para este st.session_state.
    Cada aba/janela do browser terá seu próprio session_id.
    """
    if "persistent_session_id" not in st.session_state:
        # Gera novo UUID
        st.session_state.persistent_session_id = f"sess_{uuid.uuid4().hex}"

    return st.session_state.persistent_session_id


def save_auth_simple(auth_token: str, user_info: dict):
    """
    Salva autenticação de forma persistente (server-side).
    """
    # Salva na sessão Streamlit normal
    save_session(auth_token, user_info)

    # Obtém session_id (cria se não existir)
    session_id = _get_or_create_session_id()

    # Salva no storage server-side
    save_session_persistent(session_id, auth_token, user_info)


def restore_auth_simple() -> bool:
    """
    Tenta restaurar sessão do storage server-side.
    Retorna True se restaurou com sucesso.
    """
    # Se já está autenticado, não faz nada
    if st.session_state.get("authenticated", False):
        return True

    # Obtém session_id (se não existir, significa primeira visita)
    if "persistent_session_id" not in st.session_state:
        return False

    session_id = st.session_state.persistent_session_id

    # Tenta carregar do storage
    session_data = load_session_persistent(session_id)

    if not session_data:
        return False

    # Restaura sessão
    save_session(session_data["token"], session_data["user"])

    return True


def clear_auth_simple():
    """Remove autenticação persistente."""
    # Limpa sessão Streamlit
    clear_session()

    # Remove do storage server-side
    session_id = st.session_state.get("persistent_session_id")
    if session_id:
        delete_session_persistent(session_id)

    # Limpa session_id (força criação de novo na próxima vez)
    if "persistent_session_id" in st.session_state:
        del st.session_state.persistent_session_id
