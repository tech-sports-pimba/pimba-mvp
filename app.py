"""
Streamlit app principal.
Sobe FastAPI em thread separada e renderiza UI.
"""
# IMPORTANTE: Carregar .env ANTES de qualquer import
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import time
import threading
import requests
import uvicorn
from typing import Optional
from config.settings import settings
from utils.session_manager import init_session, validate_session, clear_session
from utils.cookie_session_storage import (
    restore_auth_cookie_storage,
    clear_auth_cookie_storage,
    cleanup_expired_sessions
)

# Configuração da página (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Pimba - Personal Trainer Manager",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Imports dos módulos UI (após st.set_page_config)
from ui.auth_ui import render_auth_page
from ui.dashboard_ui import render_dashboard
from ui.alunos_ui import render_alunos_page
from ui.agenda_ui import render_agenda_page
from ui.treinos_ui import render_treinos_page
from ui.timer_ui import render_timer_livre_page
from ui.pagamentos_ui import render_pagamentos_page
from ui.evolucao_ui import render_evolucao_page

# Configurações da API
API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
MAX_HEALTH_RETRIES = 10


def start_fastapi_server():
    """Inicia servidor Uvicorn em thread daemon."""
    from api.main import app

    config = uvicorn.Config(
        app=app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        access_log=False,  # Reduz logs
    )
    server = uvicorn.Server(config)
    server.run()


def init_api_thread():
    """Inicializa thread da API (singleton via session_state)."""
    if "api_thread" not in st.session_state:
        thread = threading.Thread(target=start_fastapi_server, daemon=True)
        thread.start()
        st.session_state.api_thread = thread
        st.session_state.api_started = True


def wait_for_api_health(max_retries: int = MAX_HEALTH_RETRIES) -> bool:
    """
    Aguarda API responder no /health com retry exponencial.
    Retorna True se OK, False se falhar.
    """
    for i in range(max_retries):
        try:
            resp = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass

        # Backoff exponencial: 0.1s, 0.2s, 0.4s, 0.8s, ...
        time.sleep(0.1 * (2 ** i))

    return False


def render_sidebar():
    """Renderiza sidebar moderna e mobile-friendly."""
    with st.sidebar:
        # Logo e branding
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 3rem;">💪</div>
                <h2 style="margin: 0.5rem 0 0 0; font-weight: 700;">Pimba</h2>
                <p style="color: #666; font-size: 0.85rem; margin: 0;">Personal Trainer Manager</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Verifica se está autenticado
        if st.session_state.get("authenticated", False):
            user_info = st.session_state.get("user_info", {})

            # Card do usuário
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                            padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem; color: white;">
                    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">
                        👤 {user_info.get('nome', 'Usuário')}
                    </div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">
                        {user_info.get('email', 'email@exemplo.com')}
                    </div>
                    <div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.5rem;">
                        🎭 {user_info.get('role', 'N/A').upper()}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Navegação principal
            st.markdown("### 📍 Navegação")

            menu_items = {
                "🏠 Dashboard": "🏠",
                "👥 Meus Alunos": "👥",
                "📅 Agenda": "📅",
                "💪 Treinos": "💪",
                "⏱️ Timer": "⏱️",
                "💰 Financeiro": "💰",
                "📊 Evolução": "📊",
            }

            menu = st.radio(
                "menu",
                list(menu_items.keys()),
                label_visibility="collapsed",
            )

            st.markdown("---")

            # Botão de sair
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("🚪 Sair", use_container_width=True, type="secondary"):
                    # Limpa sessão (cookie + arquivo)
                    clear_auth_cookie_storage()
                    st.rerun()

         

            return menu
        else:
            st.info("🔒 Faça login para acessar")
            return None


def main():
    """Aplicação principal."""
    # 0. Inicializa gerenciamento de sessão
    init_session()

    # 1. Inicializa API em thread (idempotente)
    init_api_thread()

    # 2. Aguarda API estar pronta
    if "api_ready" not in st.session_state:
        with st.spinner("⏳ Inicializando API interna..."):
            if wait_for_api_health():
                st.session_state.api_ready = True
                st.rerun()
            else:
                st.error(
                    f"❌ **Falha ao inicializar API.**\n\n"
                    f"A API não respondeu em {API_BASE_URL}/health após {MAX_HEALTH_RETRIES} tentativas.\n\n"
                    f"**Possíveis causas:**\n"
                    f"- Variáveis de ambiente não configuradas (.env)\n"
                    f"- Porta {API_PORT} já em uso\n"
                    f"- Erro de conexão com banco de dados\n\n"
                    f"Verifique os logs do terminal."
                )
                st.stop()

    # 3. Limpa sessões expiradas
    cleanup_expired_sessions()

    # 4. Tenta restaurar sessão (cookie + arquivo server-side)
    current_page = st.query_params.get("page", "app")

    if current_page != "login" and not st.session_state.get("authenticated", False):
        # Tenta restaurar sessão mais recente
        restore_auth_cookie_storage()

    # 5. Roteamento baseado em autenticação
    is_authenticated = st.session_state.get("authenticated", False)

    if not is_authenticated:
        # Não autenticado: redireciona para /login
        if current_page != "login":
            st.query_params["page"] = "login"
            st.rerun()
        else:
            # Mostra página de login
            render_auth_page(API_BASE_URL)
    else:
        # Autenticado: remove query param de login e mostra dashboard
        if current_page == "login":
            if "page" in st.query_params:
                del st.query_params["page"]
            st.rerun()

        # Valida sessão antes de renderizar (previne sessões expiradas)
        if not validate_session(API_BASE_URL):
            st.warning("⚠️ Sessão expirada. Faça login novamente.")
            st.query_params["page"] = "login"
            st.rerun()
            return

        # Renderiza sidebar e conteúdo
        menu = render_sidebar()

        # Roteamento especial: se usuário clicou em executar/editar ficha no dashboard
        if "executar_ficha_id" in st.session_state or "editar_ficha_id" in st.session_state:
            render_treinos_page(API_BASE_URL)
        elif menu == "🏠 Dashboard":
            render_dashboard(API_BASE_URL)
        elif menu == "👥 Meus Alunos":
            render_alunos_page(API_BASE_URL)
        elif menu == "📅 Agenda":
            render_agenda_page(API_BASE_URL)
        elif menu == "💪 Treinos":
            render_treinos_page(API_BASE_URL)
        elif menu == "⏱️ Timer":
            render_timer_livre_page()
        elif menu == "💰 Financeiro":
            render_pagamentos_page(API_BASE_URL)
        elif menu == "📊 Evolução":
            render_evolucao_page(API_BASE_URL)


if __name__ == "__main__":
    main()
