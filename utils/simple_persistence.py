"""Persistência simples de sessão usando cookies via JavaScript."""
import streamlit as st
import streamlit.components.v1 as components
import json
import hashlib
import time


def get_or_create_session_id():
    """
    Obtém ou cria um session_id único persistente.
    Usa cookies do navegador.
    """
    # Inicializa storage de sessões se não existir
    if "sessions_store" not in st.session_state:
        st.session_state.sessions_store = {}

    # HTML/JS para gerenciar cookie de sessão
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

        function deleteCookie(name) {
            document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/";
        }

        // Tenta obter session_id do cookie
        let sessionId = getCookie('pimba_session');

        if (!sessionId) {
            // Gera novo session_id
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            setCookie('pimba_session', sessionId, 30); // 30 dias
            console.log('🆕 Novo session_id criado:', sessionId);
        } else {
            console.log('✅ Session_id encontrado:', sessionId);
        }

        // Envia para Streamlit via query param temporário
        const url = new URL(window.parent.location);
        url.searchParams.set('_session_id', sessionId);
        window.parent.history.replaceState({}, '', url);

        // Limpa depois
        setTimeout(() => {
            const cleanUrl = new URL(window.parent.location);
            cleanUrl.searchParams.delete('_session_id');
            window.parent.history.replaceState({}, '', cleanUrl);
        }, 500);
    </script>
    """

    # Renderiza componente
    components.html(cookie_js, height=0)

    # Lê session_id do query param
    if "_session_id" in st.query_params:
        session_id = st.query_params["_session_id"]
        st.session_state.persistent_session_id = session_id
        return session_id

    # Retorna do session_state se já existe
    return st.session_state.get("persistent_session_id")


def save_session_data(auth_token: str, user_info: dict):
    """
    Salva dados de autenticação associados ao session_id.
    """
    from utils.session_manager import save_session

    # Salva na sessão normal
    save_session(auth_token, user_info)

    # Obtém ou cria session_id
    session_id = get_or_create_session_id()

    if session_id:
        # Armazena no session_state global (persiste no servidor)
        if "sessions_store" not in st.session_state:
            st.session_state.sessions_store = {}

        st.session_state.sessions_store[session_id] = {
            "token": auth_token,
            "user": user_info,
            "timestamp": time.time()
        }

        # Marca session_id atual
        st.session_state.current_session_id = session_id


def restore_session_data():
    """
    Restaura dados de autenticação do session_id.
    Retorna True se restaurou com sucesso.
    """
    # Se já autenticado, não faz nada
    if st.session_state.get("authenticated", False):
        return True

    # Obtém session_id
    session_id = get_or_create_session_id()

    if not session_id:
        return False

    # Verifica se existe sessão armazenada
    sessions_store = st.session_state.get("sessions_store", {})
    session_data = sessions_store.get(session_id)

    if not session_data:
        return False

    # Verifica se não expirou (30 dias)
    age = time.time() - session_data["timestamp"]
    if age > (30 * 24 * 60 * 60):  # 30 dias
        # Sessão expirada, remove
        del sessions_store[session_id]
        return False

    # Restaura sessão
    from utils.session_manager import save_session
    save_session(session_data["token"], session_data["user"])

    return True


def clear_session_data():
    """
    Limpa dados de sessão.
    """
    from utils.session_manager import clear_session

    # Limpa sessão normal
    clear_session()

    # Remove do store
    session_id = st.session_state.get("current_session_id")
    if session_id and "sessions_store" in st.session_state:
        sessions_store = st.session_state.sessions_store
        if session_id in sessions_store:
            del sessions_store[session_id]

    # Limpa cookie
    clear_cookie_js = """
    <script>
        document.cookie = 'pimba_session=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/';
        console.log('🗑️ Cookie de sessão removido');
    </script>
    """
    components.html(clear_cookie_js, height=0)
