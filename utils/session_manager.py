"""Gerenciamento de sessão persistente para Streamlit."""
import streamlit as st
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Constantes
SESSION_TIMEOUT_MINUTES = 60  # 1 hora
TOKEN_REFRESH_THRESHOLD_MINUTES = 50  # Renova quando faltar 10min


def init_session():
    """Inicializa variáveis de sessão se não existirem."""
    defaults = {
        "authenticated": False,
        "auth_token": None,
        "user_info": None,
        "login_timestamp": None,
        "last_activity": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_session_valid() -> bool:
    """
    Verifica se a sessão ainda é válida.

    Returns:
        bool: True se sessão válida, False caso contrário
    """
    if not st.session_state.get("authenticated", False):
        return False

    if not st.session_state.get("auth_token"):
        return False

    # Verifica timeout de inatividade
    login_timestamp = st.session_state.get("login_timestamp")
    if not login_timestamp:
        return False

    # Calcula tempo desde login
    time_since_login = datetime.now() - login_timestamp

    if time_since_login > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        logger.info("Sessão expirada por timeout")
        return False

    return True


def update_activity():
    """Atualiza timestamp de última atividade."""
    st.session_state.last_activity = datetime.now()


def save_session(auth_token: str, user_info: Dict):
    """
    Salva dados de autenticação na sessão.

    Args:
        auth_token: Token JWT do Firebase
        user_info: Dados do usuário retornados pela API
    """
    st.session_state.authenticated = True
    st.session_state.auth_token = auth_token
    st.session_state.user_info = user_info
    st.session_state.login_timestamp = datetime.now()
    st.session_state.last_activity = datetime.now()

    logger.info(f"Sessão salva para {user_info.get('email', 'unknown')}")


def clear_session():
    """Limpa dados de autenticação da sessão."""
    keys_to_keep = ["api_thread", "api_started", "api_ready"]

    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]

    # Reinicializa variáveis
    init_session()

    logger.info("Sessão limpa")


def validate_session(api_base_url: str) -> bool:
    """
    Valida sessão atual com o backend.
    Se inválida, faz logout automático.

    Args:
        api_base_url: URL base da API

    Returns:
        bool: True se sessão válida, False caso contrário
    """
    # Verifica sessão local primeiro
    if not is_session_valid():
        if st.session_state.get("authenticated"):
            logger.warning("Sessão local inválida, fazendo logout")
            clear_session()
        return False

    # Atualiza atividade
    update_activity()

    # Modo DEBUG: não valida tokens mock com backend
    auth_token = st.session_state.get("auth_token", "")
    if auth_token.startswith("dev-mock-"):
        logger.debug("Modo DEBUG detectado, pulando validação de backend")
        return True

    # Valida com backend (apenas se passou tempo suficiente desde última validação)
    last_validation = st.session_state.get("last_backend_validation")

    # Valida com backend a cada 5 minutos
    if last_validation and (datetime.now() - last_validation).seconds < 300:
        return True

    try:
        # Tenta fazer request simples ao backend
        response = requests.get(
            f"{api_base_url}/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=3
        )

        if response.status_code == 200:
            st.session_state.last_backend_validation = datetime.now()
            return True
        else:
            logger.warning(f"Backend retornou {response.status_code}, fazendo logout")
            clear_session()
            return False

    except requests.RequestException as e:
        logger.warning(f"Erro ao validar com backend: {e}")
        # Não faz logout se for erro de rede, apenas em caso de 401/403
        return True


def get_session_info() -> Optional[Dict]:
    """
    Retorna informações da sessão atual.

    Returns:
        dict ou None: Info da sessão se autenticado
    """
    if not st.session_state.get("authenticated"):
        return None

    login_time = st.session_state.get("login_timestamp")
    time_since_login = None

    if login_time:
        time_since_login = datetime.now() - login_time

    return {
        "user_info": st.session_state.get("user_info"),
        "login_timestamp": login_time,
        "time_since_login": time_since_login,
        "last_activity": st.session_state.get("last_activity"),
    }


def require_auth(api_base_url: str):
    """
    Decorator/helper para garantir autenticação.
    Redireciona para login se não autenticado.

    Args:
        api_base_url: URL base da API
    """
    if not validate_session(api_base_url):
        st.warning("⚠️ Sessão expirada. Faça login novamente.")
        st.stop()
