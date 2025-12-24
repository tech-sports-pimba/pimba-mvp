"""
Streamlit app com autenticação NATIVA do Streamlit.

Usa st.login e st.user - cookies gerenciados pelo Streamlit!
"""
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import time
import threading
import requests
import uvicorn
from config.settings import settings

# Configuração da página
st.set_page_config(
    page_title="Pimba - Personal Trainer Manager",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Imports dos módulos UI
from ui.dashboard_ui import render_dashboard
from ui.alunos_ui import render_alunos_page
from ui.agenda_ui import render_agenda_page
from ui.treinos_ui import render_treinos_page
from ui.timer_ui import render_timer_livre_page
from ui.pagamentos_ui import render_pagamentos_page
from ui.evolucao_ui import render_evolucao_page

# API config
API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# Lock global para API
_api_lock = threading.Lock()
_api_started = False


def start_fastapi_server():
    """Inicia servidor Uvicorn."""
    from api.main import app

    config = uvicorn.Config(
        app=app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()


def init_api_thread():
    """Inicializa API (singleton global)."""
    global _api_started

    with _api_lock:
        if not _api_started:
            thread = threading.Thread(target=start_fastapi_server, daemon=True)
            thread.start()
            _api_started = True


def wait_for_api_health(max_retries: int = 10) -> bool:
    """Aguarda API responder."""
    for i in range(max_retries):
        try:
            resp = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass

        time.sleep(0.1 * (2 ** i))

    return False


def render_sidebar():
    """Renderiza sidebar (funciona em DEV e PROD)."""
    with st.sidebar:
        # Logo
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 3rem;">💪</div>
                <h2 style="margin: 0.5rem 0 0 0;">Pimba</h2>
                <p style="color: #666; font-size: 0.85rem; margin: 0;">Personal Trainer Manager</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # User info (adapta ao DEBUG)
        if not settings.DEBUG:
            # PRODUÇÃO (DEBUG=False): Pega do st.user
            email = st.user.email
            nome = email.split('@')[0]
        else:
            # DESENVOLVIMENTO (DEBUG=True): Pega do session_state
            user_info = st.session_state.get("user_info", {})
            email = user_info.get("email", "dev@localhost")
            nome = user_info.get("nome", "Usuário Dev")

        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                        padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem; color: white;">
                <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">
                    👤 {nome}
                </div>
                <div style="font-size: 0.85rem; opacity: 0.9;">
                    {email}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Menu
        st.markdown("### 📍 Navegação")

        menu_items = [
            "🏠 Dashboard",
            "👥 Meus Alunos",
            "📅 Agenda",
            "💪 Treinos",
            "⏱️ Timer",
            "💰 Financeiro",
            "📊 Evolução",
        ]

        menu = st.radio("menu", menu_items, label_visibility="collapsed")

        st.markdown("---")

        # Logout (adapta ao DEBUG)
        if st.button("🚪 Sair", use_container_width=True, type="secondary"):
            if not settings.DEBUG:
                st.logout()  # PRODUÇÃO: usa logout nativo
            else:
                # DESENVOLVIMENTO: limpa session_state
                st.session_state.clear()
                st.rerun()

        return menu


def login_debug():
    """Tela de login para DESENVOLVIMENTO (DEBUG=True)."""
    st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">💪</div>
            <h1 style="font-size: 2.5rem; font-weight: 700;
                       background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;">
                Pimba
            </h1>
            <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
                Gestão inteligente para personal trainers
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.warning("""
        **🚧 Modo Desenvolvimento (DEBUG=True)**

        A sessão **NÃO persiste** no F5 (limitação do Streamlit).

        Para habilitar persistência, configure **DEBUG=False** no `.env` e use autenticação do Streamlit Cloud.
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("👨‍💼 Admin", use_container_width=True, type="primary"):
            st.session_state.authenticated = True
            st.session_state.auth_token = settings.DEV_ADMIN_TOKEN  # Token mock para API
            st.session_state.user_info = {
                "email": settings.DEV_ADMIN_EMAIL,
                "nome": settings.DEV_ADMIN_NAME,
                "role": "admin",
            }
            st.rerun()

    with col2:
        if st.button("🏋️ Personal", use_container_width=True, type="primary"):
            st.session_state.authenticated = True
            st.session_state.auth_token = settings.DEV_PERSONAL_TOKEN  # Token mock para API
            st.session_state.user_info = {
                "email": settings.DEV_PERSONAL_EMAIL,
                "nome": settings.DEV_PERSONAL_NAME,
                "role": "personal",
            }
            st.rerun()

    with col3:
        if st.button("🎓 Aluno", use_container_width=True, type="primary"):
            st.session_state.authenticated = True
            st.session_state.auth_token = "dev-mock-aluno"  # Token mock genérico
            st.session_state.user_info = {
                "email": "aluno@dev.com",
                "nome": "Aluno Teste",
                "role": "aluno",
            }
            st.rerun()


def main():
    """App principal - funciona com DEBUG=True (dev) e DEBUG=False (prod)."""
    # 1. Inicializa API
    init_api_thread()

    # 2. Aguarda API
    if "api_ready" not in st.session_state:
        with st.spinner("⏳ Inicializando API..."):
            if wait_for_api_health():
                st.session_state.api_ready = True
                st.rerun()
            else:
                st.error("❌ Falha ao inicializar API")
                st.stop()

    # 3. VERIFICA LOGIN BASEADO EM DEBUG
    if settings.DEBUG:
        # MODO DEBUG (DEBUG=True): Login simples para desenvolvimento
        if not st.session_state.get("authenticated"):
            login_debug()
            st.stop()
    else:
        # MODO PRODUÇÃO (DEBUG=False): Autenticação nativa do Streamlit
        if not st.user.is_logged_in:
            st.markdown("""
                <div style="text-align: center; padding: 3rem 1rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">💪</div>
                    <h1 style="font-size: 2.5rem; font-weight: 700;
                               background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                               -webkit-background-clip: text;
                               -webkit-text-fill-color: transparent;">
                        Pimba
                    </h1>
                    <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
                        Gestão inteligente para personal trainers
                    </p>
                </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔐 Entrar", use_container_width=True, type="primary"):
                    st.login()

            st.info("""
                **Sistema de autenticação nativa do Streamlit**

                Após o login, sua sessão será mantida automaticamente, mesmo ao recarregar a página! 🎉

                O cookie expira em 30 dias.
            """)
            st.stop()

    # 4. USUÁRIO LOGADO! 🎉
    # Renderiza sidebar e pega menu selecionado
    menu = render_sidebar()

    # Renderiza conteúdo baseado no menu
    if menu == "🏠 Dashboard":
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
