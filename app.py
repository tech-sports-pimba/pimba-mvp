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
    """Renderiza sidebar com navegação."""
    with st.sidebar:
        st.title("💪 Pimba")
        st.caption("Personal Trainer Manager")
        st.divider()

        # Verifica se está autenticado
        if st.session_state.get("authenticated", False):
            user_info = st.session_state.get("user_info", {})
            st.write(f"👤 **{user_info.get('nome', 'Usuário')}**")
            st.caption(f"Role: {user_info.get('role', 'N/A')}")
            st.divider()

            menu = st.radio(
                "📍 Navegação",
                ["🏠 Dashboard", "👥 Meus Alunos", "📅 Agenda", "💪 Treinos", "⏱️ Timer", "💰 Financeiro", "📊 Evolução"],
                label_visibility="collapsed",
            )

            st.divider()

            if st.button("🚪 Sair", use_container_width=True):
                # Limpa sessão
                for key in list(st.session_state.keys()):
                    if key not in ["api_thread", "api_started", "api_ready"]:
                        del st.session_state[key]
                st.rerun()

            return menu
        else:
            st.info("🔒 Não autenticado")
            return None


def main():
    """Aplicação principal."""
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

    # 3. Renderiza UI baseado em autenticação
    if not st.session_state.get("authenticated", False):
        # Tela de login
        render_auth_page(API_BASE_URL)
    else:
        # Renderiza sidebar e conteúdo
        menu = render_sidebar()

        if menu == "🏠 Dashboard":
            render_dashboard(API_BASE_URL)
        elif menu == "👥 Meus Alunos":
            st.info("🚧 Módulo de Alunos em desenvolvimento (Fase 2)")
        elif menu == "📅 Agenda":
            st.info("🚧 Módulo de Agenda em desenvolvimento (Fase 3)")
        elif menu == "💪 Treinos":
            st.info("🚧 Módulo de Treinos em desenvolvimento (Fase 4)")
        elif menu == "⏱️ Timer":
            st.info("🚧 Timer de Treino em desenvolvimento (Fase 4)")
        elif menu == "💰 Financeiro":
            st.info("🚧 Módulo Financeiro em desenvolvimento (Fase 5)")
        elif menu == "📊 Evolução":
            st.info("🚧 Módulo de Evolução em desenvolvimento (Fase 6)")


if __name__ == "__main__":
    main()
