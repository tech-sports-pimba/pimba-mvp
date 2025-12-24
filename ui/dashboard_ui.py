"""Dashboard principal moderno e mobile-first."""
import streamlit as st
import requests
from datetime import date, datetime
from ui.components import custom_css, metric_card, empty_state, section_header, stat_grid


@st.cache_resource
def get_http_session() -> requests.Session:
    """Retorna sessão HTTP reutilizável."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def get_auth_headers():
    """Retorna headers com token."""
    token = st.session_state.get("auth_token", "")
    return {"Authorization": f"Bearer {token}"}


@st.cache_data(ttl=60)
def buscar_agendamentos_hoje(api_url: str):
    """Busca agendamentos de hoje."""
    session = get_http_session()
    hoje = date.today()

    try:
        resp = session.get(
            f"{api_url}/agendamentos/",
            headers=get_auth_headers(),
            params={"data_inicio": hoje.isoformat(), "data_fim": hoje.isoformat()},
            timeout=5
        )
        resp.raise_for_status()
        return resp.json().get("agendamentos", [])
    except:
        return []


@st.cache_data(ttl=120)
def buscar_stats_agendamentos(api_url: str):
    """Busca estatísticas de agendamentos."""
    session = get_http_session()

    try:
        resp = session.get(
            f"{api_url}/agendamentos/stats",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except:
        return {"total": 0, "hoje": 0, "semana": 0, "mes": 0}


def render_dashboard(api_base_url: str):
    """Renderiza dashboard baseado no role do usuário."""
    # Aplica CSS customizado
    custom_css()

    user_info = st.session_state.get("user_info", {})
    role = user_info.get("role", "unknown")

    # Cabeçalho com saudação
    st.markdown(f"# 👋 Olá, {user_info.get('nome', 'Usuário')}!")
    st.caption(f"📅 Bem-vindo de volta ao seu painel")
    st.markdown("---")

    if role == "admin":
        render_admin_dashboard(api_base_url)
    elif role == "personal":
        render_personal_dashboard(api_base_url, user_info)
    else:
        render_aluno_dashboard(api_base_url, user_info)


def render_admin_dashboard(api_base_url: str):
    """Dashboard para admins."""
    st.subheader("🔧 Painel Administrativo")

    # Grid de métricas
    stats = [
        {"title": "Personals", "value": "0", "icon": "👨‍💼", "color": "info"},
        {"title": "Alunos", "value": "0", "icon": "👥", "color": "success"},
        {"title": "Treinos Hoje", "value": "0", "icon": "📅", "color": "warning"},
        {"title": "Receita Mês", "value": "R$ 0", "icon": "💰", "color": "default"},
    ]
    stat_grid(stats)

    st.markdown("<br>", unsafe_allow_html=True)

    # Seções
    col1, col2 = st.columns(2)

    with col1:
        section_header("📊 Atividade Recente", "Últimas ações na plataforma")
        empty_state(
            icon="📋",
            title="Nenhuma atividade ainda",
            description="As atividades dos personals aparecerão aqui"
        )

    with col2:
        section_header("⚠️ Alertas do Sistema", "Requer atenção")
        empty_state(
            icon="✅",
            title="Tudo funcionando!",
            description="Nenhum alerta no momento"
        )


def render_personal_dashboard(api_base_url: str, user_info: dict):
    """Dashboard para personals."""
    st.subheader("💪 Resumo do seu Negócio")

    # Busca stats de agendamentos
    stats_agendamentos = buscar_stats_agendamentos(api_base_url)

    # Grid de métricas principais
    stats = [
        {"title": "Alunos Ativos", "value": "0", "icon": "👥", "color": "success"},
        {"title": "Treinos Hoje", "value": str(stats_agendamentos.get("hoje", 0)), "icon": "📅", "color": "info"},
        {"title": "Esta Semana", "value": str(stats_agendamentos.get("semana", 0)), "icon": "📆", "color": "warning"},
        {"title": "Este Mês", "value": str(stats_agendamentos.get("mes", 0)), "icon": "📊", "color": "default"},
    ]
    stat_grid(stats)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Layout responsivo com tabs
    tab1, tab2, tab3 = st.tabs(["📅 Treinos Hoje", "👥 Alunos", "💡 Insights"])

    with tab1:
        section_header("Agenda de Hoje", "Treinos programados para hoje")

        # Busca agendamentos de hoje
        agendamentos_hoje = buscar_agendamentos_hoje(api_base_url)

        if not agendamentos_hoje:
            empty_state(
                icon="📅",
                title="Nenhum treino hoje",
                description="Você não tem agendamentos para hoje. Use o módulo Agenda para criar.",
                action_text=None
            )
        else:
            for ag in sorted(agendamentos_hoje, key=lambda x: x["data_hora_inicio"]):
                hora_inicio = datetime.fromisoformat(ag["data_hora_inicio"].replace("Z", "+00:00"))
                hora_fim = datetime.fromisoformat(ag["data_hora_fim"].replace("Z", "+00:00"))
                hora_str = f"{hora_inicio.strftime('%H:%M')} - {hora_fim.strftime('%H:%M')}"

                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                        color: white;
                        border-radius: 12px;
                        padding: 1rem;
                        margin-bottom: 1rem;
                    ">
                        <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;">
                            👤 {ag['aluno_nome']}
                        </div>
                        <div style="display: flex; gap: 1rem; font-size: 0.9rem; opacity: 0.95;">
                            <span>⏰ {hora_str}</span>
                            {f'<span>📍 {ag["local"]}</span>' if ag.get("local") else ''}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    with tab2:
        section_header("Alunos Recentes", "Últimos cadastros")

        empty_state(
            icon="👥",
            title="Nenhum aluno cadastrado",
            description="Comece adicionando seus alunos no módulo Meus Alunos.",
            action_text="➕ Adicionar Aluno"
        )

    with tab3:
        section_header("Insights do Mês", "Estatísticas e tendências")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
                <div class="custom-card">
                    <h4>📈 Crescimento</h4>
                    <p style="color: #666;">Em breve você verá gráficos de crescimento de alunos e receita.</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div class="custom-card">
                    <h4>⭐ Engajamento</h4>
                    <p style="color: #666;">Acompanhe a frequência e evolução dos seus alunos.</p>
                </div>
            """, unsafe_allow_html=True)

    # Card de ação rápida
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚡ Ações Rápidas", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.button("➕ Novo Aluno", use_container_width=True)

        with col2:
            st.button("📅 Agendar Treino", use_container_width=True)

        with col3:
            st.button("💪 Nova Ficha", use_container_width=True)


def render_aluno_dashboard(api_base_url: str, user_info: dict):
    """Dashboard para alunos (futuro)."""
    st.subheader("📊 Seu Progresso")

    empty_state(
        icon="🚧",
        title="Dashboard do aluno em construção",
        description="Em breve você terá acesso ao seu histórico de treinos e evolução."
    )
