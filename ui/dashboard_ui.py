"""Dashboard principal moderno e mobile-first."""
import streamlit as st
from ui.components import custom_css, metric_card, empty_state, section_header, stat_grid


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

    # Grid de métricas principais
    stats = [
        {"title": "Alunos Ativos", "value": "0", "icon": "👥", "color": "success"},
        {"title": "Treinos Hoje", "value": "0", "icon": "📅", "color": "info"},
        {"title": "Receita Mês", "value": "R$ 0,00", "icon": "💰", "color": "default"},
        {"title": "Fichas Criadas", "value": "0", "icon": "📋", "color": "warning"},
    ]
    stat_grid(stats)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Layout responsivo com tabs
    tab1, tab2, tab3 = st.tabs(["📅 Agenda", "👥 Alunos", "💡 Insights"])

    with tab1:
        section_header("Próximos Agendamentos", "Seus treinos marcados")

        # Empty state bonito
        empty_state(
            icon="📅",
            title="Nenhum treino agendado",
            description="Você ainda não tem agendamentos. Use o módulo Agenda para criar.",
            action_text="➕ Criar Agendamento"
        )

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
