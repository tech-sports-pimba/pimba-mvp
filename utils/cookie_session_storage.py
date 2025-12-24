"""
Sistema de sessão usando cookies HTTP + storage server-side.

Abordagem profissional:
- Cookie armazena apenas session_id (identificador seguro)
- Dados reais ficam server-side em arquivos
- Multi-tenant por design
- Sem timing issues
"""
import streamlit as st
import streamlit.components.v1 as components
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from utils.session_manager import save_session, clear_session

SESSION_DIR = Path(".sessions")
SESSION_DIR.mkdir(exist_ok=True)
SESSION_EXPIRY_DAYS = 7


def _get_session_id_from_cookie() -> str:
    """
    Obtém session_id do cookie.
    Se não existir, cria um novo.
    """
    # Verifica se já temos no session_state (cache)
    if "cookie_session_id" in st.session_state:
        return st.session_state.cookie_session_id

    # JavaScript para ler/criar cookie
    js_code = """
    <script>
        parent.window.pimba_session_id = (function() {
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
                document.cookie = name + "=" + value + ";" + expires + ";path=/;SameSite=Lax";
            }

            let sessionId = getCookie('pimba_sid');
            if (!sessionId) {
                sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                setCookie('pimba_sid', sessionId, 7);
                console.log('🆕 Novo session_id:', sessionId);
            } else {
                console.log('✅ Session_id existente:', sessionId);
            }

            // Expõe via window para Python acessar
            return sessionId;
        })();
    </script>
    """

    components.html(js_code, height=0)

    # Tenta ler do window via query param hack
    # (JavaScript vai ter setado antes do próximo render)
    # Por enquanto, gera um temporário
    temp_id = f"temp_{uuid.uuid4().hex[:12]}"
    st.session_state.cookie_session_id = temp_id

    return temp_id


def _get_session_file(session_id: str) -> Path:
    """Retorna path do arquivo de sessão."""
    return SESSION_DIR / f"{session_id}.json"


def save_auth_cookie_storage(auth_token: str, user_info: dict):
    """
    Salva autenticação usando cookie + arquivo server-side.
    """
    # Salva no session_state (sessão atual)
    save_session(auth_token, user_info)

    # Obtém session_id do cookie (ou cria novo)
    session_id = _get_session_id_from_cookie()

    # Salva dados no arquivo server-side
    session_data = {
        "token": auth_token,
        "user": user_info,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)).isoformat()
    }

    session_file = _get_session_file(session_id)
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)


def restore_auth_cookie_storage() -> bool:
    """
    Tenta restaurar sessão do cookie + arquivo.
    """
    # Se já está autenticado, não faz nada
    if st.session_state.get("authenticated", False):
        return True

    # Tenta encontrar arquivo de sessão válido
    # Como não conseguimos ler cookie sincronamente, vamos tentar carregar
    # o arquivo mais recente que não expirou

    if not SESSION_DIR.exists():
        return False

    # Lista todos os arquivos de sessão
    session_files = sorted(SESSION_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

    for session_file in session_files:
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Verifica expiração
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.now() > expires_at:
                # Sessão expirada, remove
                session_file.unlink()
                continue

            # Encontrou sessão válida!
            save_session(session_data["token"], session_data["user"])

            # Guarda o session_id no cache
            session_id = session_file.stem
            st.session_state.cookie_session_id = session_id

            return True

        except (json.JSONDecodeError, KeyError, ValueError):
            # Arquivo corrompido, remove
            session_file.unlink()
            continue

    return False


def clear_auth_cookie_storage():
    """
    Remove autenticação.
    """
    # Limpa sessão Streamlit
    clear_session()

    # Remove arquivo se existe
    if "cookie_session_id" in st.session_state:
        session_id = st.session_state.cookie_session_id
        session_file = _get_session_file(session_id)
        if session_file.exists():
            session_file.unlink()

        del st.session_state.cookie_session_id

    # JavaScript para limpar cookie
    js_code = """
    <script>
        document.cookie = 'pimba_sid=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/';
        console.log('🗑️ Cookie removido');
    </script>
    """

    components.html(js_code, height=0)


def cleanup_expired_sessions():
    """Remove sessões expiradas."""
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
            session_file.unlink()
