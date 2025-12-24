"""Gerenciador de sessão persistente com cookies + server-side storage."""
import streamlit as st
import streamlit.components.v1 as components
from utils.session_storage import (
    save_session_persistent,
    load_session_persistent,
    delete_session_persistent,
    cleanup_expired_sessions
)
from utils.session_manager import save_session


def get_browser_session_id() -> str:
    """
    Obtém ou cria session_id persistente no browser via cookie.
    Retorna o session_id ou None se ainda não foi gerado.
    """
    # Se já temos o session_id no session_state, retorna
    if "browser_session_id" in st.session_state:
        return st.session_state.browser_session_id

    # JavaScript para gerenciar cookie de sessão
    cookie_js = """
    <script>
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }

        function setCookie(name, value, days) {
            const d = new Date();
            d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
            const expires = "expires=" + d.toUTCString();
            document.cookie = name + "=" + value + ";" + expires + ";path=/;SameSite=Strict";
        }

        // Tenta obter session_id do cookie
        let sessionId = getCookie('pimba_session_id');

        if (!sessionId) {
            // Gera novo session_id
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            setCookie('pimba_session_id', sessionId, 7); // 7 dias
        }

        // Envia para Streamlit via query param temporário
        const url = new URL(window.parent.location);
        url.searchParams.set('_session_id', sessionId);
        window.parent.history.replaceState({}, '', url);
    </script>
    """

    # Renderiza componente (invisível)
    components.html(cookie_js, height=0)

    # Tenta ler do query param
    if "_session_id" in st.query_params:
        session_id = st.query_params["_session_id"]
        st.session_state.browser_session_id = session_id

        # Limpa query param
        del st.query_params["_session_id"]

        return session_id

    return None


def save_auth_with_cookie(auth_token: str, user_info: dict):
    """
    Salva autenticação de forma persistente.
    Usa cookie para identificar sessão + storage server-side para dados.
    """
    # Salva na sessão Streamlit normal
    save_session(auth_token, user_info)

    # Obtém session_id do browser
    session_id = get_browser_session_id()

    if session_id:
        # Salva no storage server-side
        save_session_persistent(session_id, auth_token, user_info)


def restore_auth_from_cookie() -> bool:
    """
    Tenta restaurar sessão do storage server-side.
    Retorna True se restaurou com sucesso.
    """
    # Se já está autenticado, não faz nada
    if st.session_state.get("authenticated", False):
        return True

    # Limpa sessões expiradas (manutenção)
    cleanup_expired_sessions()

    # Obtém session_id do browser
    session_id = get_browser_session_id()

    if not session_id:
        return False

    # Tenta carregar do storage
    session_data = load_session_persistent(session_id)

    if not session_data:
        return False

    # Restaura sessão
    save_session(session_data["token"], session_data["user"])

    return True


def clear_auth_with_cookie():
    """Remove autenticação persistente."""
    from utils.session_manager import clear_session

    # Limpa sessão Streamlit
    clear_session()

    # Remove do storage server-side
    session_id = st.session_state.get("browser_session_id")
    if session_id:
        delete_session_persistent(session_id)

    # Limpa cookie do browser
    clear_cookie_js = """
    <script>
        document.cookie = 'pimba_session_id=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/';
    </script>
    """
    components.html(clear_cookie_js, height=0)
