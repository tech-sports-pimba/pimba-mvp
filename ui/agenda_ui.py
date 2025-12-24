"""UI de agenda/calendário - mobile-first e concisa."""
import streamlit as st
import requests
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
from ui.components import custom_css, section_header, badge, empty_state


@st.cache_resource
def get_http_session() -> requests.Session:
    """Retorna sessão HTTP reutilizável."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def get_auth_headers() -> Dict[str, str]:
    """Retorna headers com token de autenticação."""
    token = st.session_state.get("auth_token", "")
    return {"Authorization": f"Bearer {token}"}


@st.cache_data(ttl=60)
def buscar_agendamentos(api_url: str, data_inicio: date, data_fim: date):
    """Busca agendamentos do período com cache de 60s."""
    session = get_http_session()

    try:
        resp = session.get(
            f"{api_url}/agendamentos/",
            headers=get_auth_headers(),
            params={
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
            },
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Erro ao buscar agendamentos: {e}")
        return {"total": 0, "agendamentos": []}


@st.cache_data(ttl=120)
def buscar_alunos(api_url: str):
    """Busca lista de alunos ativos."""
    session = get_http_session()

    try:
        resp = session.get(
            f"{api_url}/alunos/",
            headers=get_auth_headers(),
            params={"ativo": True},
            timeout=5
        )
        resp.raise_for_status()
        return resp.json().get("alunos", [])
    except requests.RequestException:
        return []


def criar_agendamento(api_url: str, dados: dict):
    """Cria novo agendamento."""
    session = get_http_session()

    try:
        resp = session.post(
            f"{api_url}/agendamentos/",
            headers=get_auth_headers(),
            json=dados,
            timeout=5
        )
        resp.raise_for_status()

        # Limpa cache
        buscar_agendamentos.clear()

        return True, "Agendamento criado!"
    except requests.HTTPError as e:
        try:
            error_detail = e.response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        return False, error_detail
    except requests.RequestException as e:
        return False, f"Erro ao criar: {e}"


def deletar_agendamento(api_url: str, agendamento_id: int):
    """Deleta agendamento."""
    session = get_http_session()

    try:
        resp = session.delete(
            f"{api_url}/agendamentos/{agendamento_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()

        # Limpa cache
        buscar_agendamentos.clear()

        return True, "Agendamento removido!"
    except requests.RequestException as e:
        return False, f"Erro ao deletar: {e}"


def render_calendario_semanal(api_url: str, data_base: date):
    """Renderiza calendário semanal mobile-first."""
    # Calcula início da semana (segunda-feira)
    inicio_semana = data_base - timedelta(days=data_base.weekday())
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]

    # Busca agendamentos da semana
    dados = buscar_agendamentos(
        api_url,
        dias_semana[0],
        dias_semana[-1]
    )
    agendamentos = dados.get("agendamentos", [])

    # Agrupa por dia
    agendamentos_por_dia: Dict[str, List] = {}
    for ag in agendamentos:
        data_ag = datetime.fromisoformat(ag["data_hora_inicio"].replace("Z", "+00:00")).date()
        data_key = data_ag.isoformat()
        if data_key not in agendamentos_por_dia:
            agendamentos_por_dia[data_key] = []
        agendamentos_por_dia[data_key].append(ag)

    # Navegação de semana
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("◀️", use_container_width=True):
            st.session_state.data_base = data_base - timedelta(days=7)
            st.rerun()

    with col2:
        mes_ano = inicio_semana.strftime("%B %Y").capitalize()
        st.markdown(f"<h4 style='text-align: center; margin: 0;'>{mes_ano}</h4>", unsafe_allow_html=True)

    with col3:
        if st.button("▶️", use_container_width=True):
            st.session_state.data_base = data_base + timedelta(days=7)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Renderiza dias da semana
    hoje = date.today()
    dias_nomes = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    for idx, dia in enumerate(dias_semana):
        eh_hoje = dia == hoje
        dia_key = dia.isoformat()
        agendamentos_dia = agendamentos_por_dia.get(dia_key, [])

        # Card do dia
        border_color = "#dc2626" if eh_hoje else "#e5e7eb"
        bg_color = "#fef2f2" if eh_hoje else "white"

        st.markdown(f"""
            <div style="
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1rem;
                background: {bg_color};
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <div>
                        <span style="color: #666; font-size: 0.85rem;">{dias_nomes[idx]}</span>
                        <h3 style="margin: 0; color: {'#dc2626' if eh_hoje else '#111'};">{dia.day}</h3>
                    </div>
                    <span style="background: #dc2626; color: white; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.85rem; font-weight: 600;">
                        {len(agendamentos_dia)}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Agendamentos do dia
        if agendamentos_dia:
            for ag in sorted(agendamentos_dia, key=lambda x: x["data_hora_inicio"]):
                render_agendamento_card(api_url, ag)
        else:
            st.caption("Nenhum treino agendado")

        # Botão de adicionar
        if st.button(f"➕ Adicionar", key=f"add_{dia_key}", use_container_width=True, type="secondary"):
            st.session_state.criar_agendamento_data = dia
            st.session_state.show_form_agendamento = True
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)


def render_agendamento_card(api_url: str, agendamento: dict):
    """Renderiza card de agendamento."""
    hora_inicio = datetime.fromisoformat(agendamento["data_hora_inicio"].replace("Z", "+00:00"))
    hora_fim = datetime.fromisoformat(agendamento["data_hora_fim"].replace("Z", "+00:00"))

    hora_str = f"{hora_inicio.strftime('%H:%M')} - {hora_fim.strftime('%H:%M')}"
    status = agendamento.get("status", "agendado")

    # Status badge
    status_colors = {
        "agendado": ("🗓️", "#3b82f6"),
        "confirmado": ("✅", "#10b981"),
        "cancelado": ("❌", "#ef4444"),
        "realizado": ("✔️", "#6b7280"),
    }
    emoji, cor = status_colors.get(status, ("📅", "#666"))

    with st.container():
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                color: white;
                border-radius: 8px;
                padding: 0.75rem;
                margin-bottom: 0.5rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem;">
                            👤 {agendamento['aluno_nome']}
                        </div>
                        <div style="font-size: 0.85rem; opacity: 0.9;">
                            ⏰ {hora_str}
                        </div>
                        {f'<div style="font-size: 0.85rem; opacity: 0.9; margin-top: 0.25rem;">📍 {agendamento["local"]}</div>' if agendamento.get("local") else ''}
                    </div>
                    <div style="font-size: 1.25rem;">{emoji}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Botão de deletar
        if st.button("🗑️ Remover", key=f"del_{agendamento['id']}", type="secondary"):
            sucesso, msg = deletar_agendamento(api_url, agendamento["id"])
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


def render_form_agendamento(api_url: str, data_padrao: Optional[date] = None):
    """Renderiza formulário de criar agendamento."""
    st.subheader("➕ Novo Agendamento")

    # Busca alunos
    alunos = buscar_alunos(api_url)

    if not alunos:
        st.warning("⚠️ Você precisa cadastrar alunos antes de criar agendamentos")
        return

    with st.form("form_agendamento", clear_on_submit=False):
        # Aluno
        opcoes_alunos = {f"{a['nome']} ({a['email'] or 'sem email'})": a['id'] for a in alunos}
        aluno_selecionado = st.selectbox("Aluno", options=list(opcoes_alunos.keys()))
        aluno_id = opcoes_alunos[aluno_selecionado]

        # Data e hora
        col1, col2 = st.columns(2)

        with col1:
            data_agendamento = st.date_input(
                "Data",
                value=data_padrao or date.today(),
                min_value=date.today() - timedelta(days=365),
                max_value=date.today() + timedelta(days=365)
            )

        with col2:
            hora_agendamento = st.time_input("Hora", value=datetime.now().time())

        # Duração
        duracao = st.select_slider(
            "Duração",
            options=[15, 30, 45, 60, 75, 90, 120],
            value=60,
            format_func=lambda x: f"{x} min"
        )

        # Local
        local = st.text_input("Local", placeholder="Academia, Casa do aluno, Online...")

        # Observações
        observacoes = st.text_area("Observações", placeholder="Notas sobre o treino...", height=80)

        # Botões
        col_submit, col_cancel = st.columns(2)

        with col_submit:
            submitted = st.form_submit_button("✅ Criar", use_container_width=True, type="primary")

        with col_cancel:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)

        if submitted:
            # Combina data + hora
            data_hora = datetime.combine(data_agendamento, hora_agendamento)

            dados = {
                "aluno_id": aluno_id,
                "data_hora_inicio": data_hora.isoformat(),
                "duracao_minutos": duracao,
                "local": local if local else None,
                "observacoes": observacoes if observacoes else None,
            }

            sucesso, msg = criar_agendamento(api_url, dados)

            if sucesso:
                st.success(msg)
                st.session_state.show_form_agendamento = False
                st.rerun()
            else:
                st.error(f"❌ {msg}")

        if cancel:
            st.session_state.show_form_agendamento = False
            st.rerun()


def render_agenda_page(api_base_url: str):
    """Renderiza página de agenda."""
    custom_css()

    st.title("📅 Agenda")
    st.caption("Visualize e gerencie seus treinos agendados")
    st.markdown("---")

    # Data base para calendário (persiste na sessão)
    if "data_base" not in st.session_state:
        st.session_state.data_base = date.today()

    # Tabs
    tab1, tab2 = st.tabs(["📅 Calendário", "➕ Novo Agendamento"])

    with tab1:
        # Botão para hoje
        if st.button("📍 Hoje", type="secondary"):
            st.session_state.data_base = date.today()
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Renderiza calendário semanal
        render_calendario_semanal(api_base_url, st.session_state.data_base)

    with tab2:
        render_form_agendamento(api_base_url)

    # Form flutuante (quando clica em adicionar em um dia específico)
    if st.session_state.get("show_form_agendamento", False):
        with st.expander("📝 Novo Agendamento", expanded=True):
            data_selecionada = st.session_state.get("criar_agendamento_data")
            render_form_agendamento(api_base_url, data_selecionada)
