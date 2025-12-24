"""Dashboard principal."""
import streamlit as st


def render_dashboard(api_base_url: str):
    """Renderiza dashboard baseado no role do usuário."""
    user_info = st.session_state.get("user_info", {})
    role = user_info.get("role", "unknown")

    st.title("🏠 Dashboard")
    st.markdown(f"**Bem-vindo(a), {user_info.get('nome', 'Usuário')}!**")
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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Personals", "0", help="Total de personal trainers cadastrados")

    with col2:
        st.metric("Total de Alunos", "0", help="Total de alunos na plataforma")

    with col3:
        st.metric("Agendamentos Hoje", "0", help="Total de agendamentos para hoje")

    st.info("🚧 Estatísticas completas serão implementadas nas próximas fases")


def render_personal_dashboard(api_base_url: str, user_info: dict):
    """Dashboard para personals."""
    st.subheader("💪 Resumo do seu Negócio")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Alunos Ativos", "0", help="Alunos com status ativo")

    with col2:
        st.metric("Treinos Hoje", "0", help="Agendamentos para hoje")

    with col3:
        st.metric("Receita Mês", "R$ 0,00", help="Total recebido no mês atual")

    with col4:
        st.metric("Fichas de Treino", "0", help="Total de fichas criadas")

    st.markdown("---")

    # Próximos agendamentos
    st.subheader("📅 Próximos Agendamentos")
    st.info("🚧 Você ainda não tem agendamentos. Use o módulo Agenda para criar.")

    st.markdown("---")

    # Alunos recentes
    st.subheader("👥 Alunos Recentes")
    st.info("🚧 Você ainda não tem alunos cadastrados. Use o módulo Meus Alunos para cadastrar.")


def render_aluno_dashboard(api_base_url: str, user_info: dict):
    """Dashboard para alunos (futuro)."""
    st.subheader("📊 Seu Progresso")
    st.info("🚧 Dashboard do aluno será implementado em fases futuras")
