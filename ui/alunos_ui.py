"""UI de gestão de alunos - moderna e mobile-first."""
import streamlit as st
import requests
from typing import Dict, Any, Optional
from datetime import date
from ui.components import custom_css, empty_state, section_header, badge


@st.cache_resource
def get_http_session() -> requests.Session:
    """Retorna sessão HTTP reutilizável (singleton)."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def get_auth_headers() -> Dict[str, str]:
    """Retorna headers com token de autenticação."""
    token = st.session_state.get("auth_token", "")
    return {"Authorization": f"Bearer {token}"}


@st.cache_data(ttl=30)
def listar_alunos_cached(api_url: str, busca: Optional[str] = None, ativo: Optional[bool] = None):
    """Lista alunos com cache de 30s."""
    session = get_http_session()

    params = {}
    if busca:
        params["busca"] = busca
    if ativo is not None:
        params["ativo"] = ativo

    try:
        resp = session.get(
            f"{api_url}/alunos/",
            headers=get_auth_headers(),
            params=params,
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Erro ao buscar alunos: {e}")
        return {"total": 0, "alunos": []}


@st.cache_data(ttl=60)
def get_stats_alunos(api_url: str):
    """Retorna estatísticas dos alunos."""
    session = get_http_session()
    try:
        resp = session.get(
            f"{api_url}/alunos/stats",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {"total": 0, "ativos": 0, "inativos": 0, "novos_mes": 0}


def criar_aluno_form(api_url: str):
    """Form para criar novo aluno."""
    st.subheader("➕ Cadastrar Novo Aluno")

    with st.form("form_criar_aluno", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome *", placeholder="João Silva")
            email = st.text_input("Email", placeholder="joao@exemplo.com")

        with col2:
            telefone = st.text_input("Telefone", placeholder="+55 11 98765-4321")
            data_nasc = st.date_input(
                "Data de Nascimento",
                value=None,
                min_value=date(1920, 1, 1),
                max_value=date.today()
            )

        objetivo = st.text_area(
            "Objetivo",
            placeholder="Ex: Perder peso, ganhar massa muscular, melhorar condicionamento...",
            height=100
        )

        submitted = st.form_submit_button("✅ Cadastrar Aluno", use_container_width=True, type="primary")

        if submitted:
            if not nome:
                st.error("❌ Nome é obrigatório")
                return

            payload = {"nome": nome}

            if email:
                payload["email"] = email
            if telefone:
                payload["telefone"] = telefone
            if data_nasc:
                payload["data_nascimento"] = data_nasc.isoformat()
            if objetivo:
                payload["objetivo"] = objetivo

            session = get_http_session()
            try:
                resp = session.post(
                    f"{api_url}/alunos/",
                    headers=get_auth_headers(),
                    json=payload,
                    timeout=5
                )
                resp.raise_for_status()
                st.success(f"✅ Aluno '{nome}' cadastrado com sucesso!")

                # Limpa cache para refletir novo aluno
                listar_alunos_cached.clear()
                get_stats_alunos.clear()

                st.rerun()

            except requests.HTTPError as e:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except:
                    error_detail = str(e)
                st.error(f"❌ Erro: {error_detail}")
            except requests.RequestException as e:
                st.error(f"❌ Erro ao criar aluno: {e}")


def editar_aluno_modal(api_url: str, aluno: Dict[str, Any]):
    """Modal para editar aluno."""
    with st.expander(f"✏️ Editar {aluno['nome']}", expanded=False):
        with st.form(f"form_editar_{aluno['id']}"):
            col1, col2 = st.columns(2)

            with col1:
                nome = st.text_input("Nome", value=aluno['nome'])
                email = st.text_input("Email", value=aluno.get('email') or "")

            with col2:
                telefone = st.text_input("Telefone", value=aluno.get('telefone') or "")
                # Data de nascimento
                data_nasc_value = None
                if aluno.get('data_nascimento'):
                    try:
                        from datetime import datetime
                        data_nasc_value = datetime.fromisoformat(aluno['data_nascimento'].split('T')[0]).date()
                    except:
                        pass

                data_nasc = st.date_input(
                    "Data de Nascimento",
                    value=data_nasc_value,
                    min_value=date(1920, 1, 1),
                    max_value=date.today()
                )

            objetivo = st.text_area(
                "Objetivo",
                value=aluno.get('objetivo') or "",
                height=80
            )

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                submitted = st.form_submit_button("💾 Salvar", use_container_width=True, type="primary")

            with col_btn2:
                cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

            if submitted:
                payload = {}

                if nome and nome != aluno['nome']:
                    payload["nome"] = nome
                if email != (aluno.get('email') or ""):
                    payload["email"] = email if email else None
                if telefone != (aluno.get('telefone') or ""):
                    payload["telefone"] = telefone if telefone else None
                if data_nasc:
                    payload["data_nascimento"] = data_nasc.isoformat()
                if objetivo != (aluno.get('objetivo') or ""):
                    payload["objetivo"] = objetivo if objetivo else None

                if not payload:
                    st.warning("⚠️ Nenhuma alteração detectada")
                    return

                session = get_http_session()
                try:
                    resp = session.put(
                        f"{api_url}/alunos/{aluno['id']}",
                        headers=get_auth_headers(),
                        json=payload,
                        timeout=5
                    )
                    resp.raise_for_status()
                    st.success(f"✅ Aluno atualizado!")

                    listar_alunos_cached.clear()
                    get_stats_alunos.clear()
                    st.rerun()

                except requests.RequestException as e:
                    st.error(f"❌ Erro ao atualizar: {e}")


def render_aluno_card(api_url: str, aluno: Dict[str, Any]):
    """Renderiza card de aluno."""
    # Status badge
    status_badge = badge("Ativo", "success") if aluno.get('ativo') else badge("Inativo", "danger")

    with st.container():
        st.markdown(f"""
            <div class="custom-card">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                    <div>
                        <h3 style="margin: 0 0 0.25rem 0;">👤 {aluno['nome']}</h3>
                        {status_badge}
                    </div>
                </div>
                <div style="color: #666; font-size: 0.9rem;">
                    📧 {aluno.get('email') or 'Sem email'}<br>
                    📱 {aluno.get('telefone') or 'Sem telefone'}<br>
                    🎯 {aluno.get('objetivo') or 'Sem objetivo definido'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Botões de ação
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✏️ Editar", key=f"btn_editar_{aluno['id']}", use_container_width=True):
                st.session_state[f"editing_{aluno['id']}"] = True

        with col2:
            status_text = "⏸️ Inativar" if aluno.get('ativo') else "▶️ Ativar"
            if st.button(status_text, key=f"btn_toggle_{aluno['id']}", use_container_width=True):
                toggle_status_aluno(api_url, aluno['id'])

        with col3:
            if st.button("📊 Evolução", key=f"btn_evolucao_{aluno['id']}", use_container_width=True):
                st.info("🚧 Módulo de evolução em breve!")

        with col4:
            if st.button("🗑️ Excluir", key=f"btn_delete_{aluno['id']}", use_container_width=True, type="secondary"):
                st.session_state[f"confirm_delete_{aluno['id']}"] = True

        # Confirmação de exclusão
        if st.session_state.get(f"confirm_delete_{aluno['id']}", False):
            st.warning(f"⚠️ **Confirmar exclusão de '{aluno['nome']}'?** Esta ação não pode ser desfeita!")
            col_confirm1, col_confirm2 = st.columns(2)

            with col_confirm1:
                if st.button("✅ Sim, excluir", key=f"confirm_yes_{aluno['id']}", type="primary", use_container_width=True):
                    deletar_aluno(api_url, aluno['id'], aluno['nome'])

            with col_confirm2:
                if st.button("❌ Cancelar", key=f"confirm_no_{aluno['id']}", use_container_width=True):
                    del st.session_state[f"confirm_delete_{aluno['id']}"]
                    st.rerun()

        # Modal de edição
        if st.session_state.get(f"editing_{aluno['id']}", False):
            editar_aluno_modal(api_url, aluno)


def toggle_status_aluno(api_url: str, aluno_id: int):
    """Alterna status ativo/inativo."""
    session = get_http_session()
    try:
        resp = session.patch(
            f"{api_url}/alunos/{aluno_id}/toggle-ativo",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()
        st.success("✅ Status atualizado!")

        listar_alunos_cached.clear()
        get_stats_alunos.clear()
        st.rerun()

    except requests.RequestException as e:
        st.error(f"❌ Erro ao alterar status: {e}")


def deletar_aluno(api_url: str, aluno_id: int, nome: str):
    """Deleta aluno."""
    session = get_http_session()
    try:
        resp = session.delete(
            f"{api_url}/alunos/{aluno_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()
        st.success(f"✅ Aluno '{nome}' excluído!")

        listar_alunos_cached.clear()
        get_stats_alunos.clear()

        # Limpa confirmação
        if f"confirm_delete_{aluno_id}" in st.session_state:
            del st.session_state[f"confirm_delete_{aluno_id}"]

        st.rerun()

    except requests.RequestException as e:
        st.error(f"❌ Erro ao excluir: {e}")


def render_alunos_page(api_base_url: str):
    """Renderiza página completa de gestão de alunos."""
    # Aplica CSS
    custom_css()

    st.title("👥 Meus Alunos")
    st.caption("Gerencie seus alunos de forma simples e eficiente")
    st.markdown("---")

    # Estatísticas
    stats = get_stats_alunos(api_base_url)

    from ui.components import stat_grid
    stat_grid([
        {"title": "Total", "value": str(stats["total"]), "icon": "👥", "color": "default"},
        {"title": "Ativos", "value": str(stats["ativos"]), "icon": "✅", "color": "success"},
        {"title": "Inativos", "value": str(stats["inativos"]), "icon": "⏸️", "color": "warning"},
        {"title": "Novos no Mês", "value": str(stats["novos_mes"]), "icon": "🆕", "color": "info"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2 = st.tabs(["📋 Lista de Alunos", "➕ Cadastrar Novo"])

    with tab1:
        # Filtros
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            busca = st.text_input("🔍 Buscar", placeholder="Nome ou email...", label_visibility="collapsed")

        with col2:
            filtro_status = st.selectbox(
                "Status",
                ["Todos", "Ativos", "Inativos"],
                label_visibility="collapsed"
            )

        with col3:
            if st.button("🔄 Atualizar", use_container_width=True):
                listar_alunos_cached.clear()
                get_stats_alunos.clear()
                st.rerun()

        # Determina filtro de status
        ativo_filter = None
        if filtro_status == "Ativos":
            ativo_filter = True
        elif filtro_status == "Inativos":
            ativo_filter = False

        # Lista alunos
        dados = listar_alunos_cached(api_base_url, busca if busca else None, ativo_filter)
        alunos = dados.get("alunos", [])

        if not alunos:
            empty_state(
                icon="👥",
                title="Nenhum aluno encontrado",
                description="Cadastre seu primeiro aluno na aba 'Cadastrar Novo' ou ajuste os filtros.",
                action_text=None
            )
        else:
            st.caption(f"**{dados['total']} aluno(s) encontrado(s)**")
            st.markdown("<br>", unsafe_allow_html=True)

            for aluno in alunos:
                render_aluno_card(api_base_url, aluno)
                st.markdown("<br>", unsafe_allow_html=True)

    with tab2:
        criar_aluno_form(api_base_url)
