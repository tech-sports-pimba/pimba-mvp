"""UI de acompanhamento de evolução/desempenho dos alunos."""
import streamlit as st
import requests
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from ui.components import custom_css, empty_state, section_header, stat_grid


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


@st.cache_data(ttl=30)
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
    except:
        return []


@st.cache_data(ttl=30)
def buscar_registros_aluno(api_url: str, aluno_id: int):
    """Busca registros de evolução do aluno."""
    session = get_http_session()
    try:
        resp = session.get(
            f"{api_url}/evolucao/aluno/{aluno_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Erro ao buscar registros: {e}")
        return {"total": 0, "registros": []}


@st.cache_data(ttl=30)
def buscar_stats_aluno(api_url: str, aluno_id: int):
    """Busca estatísticas do aluno."""
    session = get_http_session()
    try:
        resp = session.get(
            f"{api_url}/evolucao/aluno/{aluno_id}/stats",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except:
        return {
            "total_registros": 0,
            "total_presencas": 0,
            "taxa_presenca": 0.0,
            "nivel_medio": None,
            "ultimo_registro": None
        }


def criar_registro(api_url: str, aluno_id: int, dados: dict):
    """Cria novo registro de evolução."""
    session = get_http_session()

    try:
        resp = session.post(
            f"{api_url}/evolucao/aluno/{aluno_id}",
            headers=get_auth_headers(),
            json=dados,
            timeout=5
        )
        resp.raise_for_status()

        # Limpa caches
        buscar_registros_aluno.clear()
        buscar_stats_aluno.clear()

        return True, "✅ Registro criado!"
    except requests.HTTPError as e:
        try:
            error_detail = e.response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        return False, f"❌ Erro: {error_detail}"
    except requests.RequestException as e:
        return False, f"❌ Erro ao criar: {e}"


def deletar_registro(api_url: str, registro_id: int):
    """Deleta registro."""
    session = get_http_session()

    try:
        resp = session.delete(
            f"{api_url}/evolucao/{registro_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()

        # Limpa caches
        buscar_registros_aluno.clear()
        buscar_stats_aluno.clear()

        return True, "✅ Registro removido!"
    except requests.RequestException as e:
        return False, f"❌ Erro ao deletar: {e}"


def render_stats_aluno(api_url: str, aluno_id: int):
    """Renderiza estatísticas do aluno."""
    stats = buscar_stats_aluno(api_url, aluno_id)

    stat_items = [
        {
            "title": "Total Registros",
            "value": str(stats["total_registros"]),
            "icon": "📋",
            "color": "default"
        },
        {
            "title": "Presenças",
            "value": str(stats["total_presencas"]),
            "icon": "✅",
            "color": "success"
        },
        {
            "title": "Taxa Presença",
            "value": f"{stats['taxa_presenca']:.1f}%",
            "icon": "📊",
            "color": "info"
        },
        {
            "title": "Nível Médio",
            "value": f"{stats['nivel_medio']:.1f}" if stats['nivel_medio'] else "N/A",
            "icon": "💪",
            "color": "warning"
        },
    ]

    stat_grid(stat_items)

    if stats["ultimo_registro"]:
        ultimo = datetime.fromisoformat(stats["ultimo_registro"]).strftime("%d/%m/%Y")
        st.caption(f"📅 Último registro: {ultimo}")


def render_form_registro(api_url: str, aluno_id: int):
    """Form para criar novo registro."""
    st.subheader("➕ Novo Registro")

    with st.form("form_criar_registro", clear_on_submit=True):
        data_registro = st.date_input(
            "Data*",
            value=date.today(),
            max_value=date.today()
        )

        col1, col2 = st.columns(2)

        with col1:
            presente = st.checkbox("✅ Aluno presente", value=True)

        with col2:
            nivel_treino = st.select_slider(
                "💪 Nível do Treino",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: {
                    1: "1 - Muito Leve",
                    2: "2 - Leve",
                    3: "3 - Moderado",
                    4: "4 - Intenso",
                    5: "5 - Muito Intenso"
                }[x]
            )

        observacoes = st.text_area(
            "📝 Observações",
            placeholder="Como foi o treino? Dificuldades? Progressos?",
            height=100
        )

        submitted = st.form_submit_button("💾 Salvar Registro", use_container_width=True, type="primary")

        if submitted:
            payload = {
                "data_registro": data_registro.isoformat(),
                "presente": presente,
                "nivel_treino": nivel_treino if presente else None,
                "observacoes": observacoes if observacoes else None,
            }

            sucesso, mensagem = criar_registro(api_url, aluno_id, payload)

            if sucesso:
                st.success(mensagem)
                st.rerun()
            else:
                st.error(mensagem)


def render_lista_registros(api_url: str, aluno_id: int):
    """Renderiza lista de registros."""
    st.subheader("📊 Histórico")

    dados = buscar_registros_aluno(api_url, aluno_id)
    registros = dados.get("registros", [])

    if not registros:
        empty_state(
            icon="📋",
            title="Nenhum registro ainda",
            description="Adicione o primeiro registro para começar a acompanhar a evolução.",
            action_text=None
        )
    else:
        st.caption(f"**{dados['total']} registro(s)**")
        st.markdown("<br>", unsafe_allow_html=True)

        for reg in registros:
            render_registro_card(api_url, reg)


def render_registro_card(api_url: str, registro: Dict[str, Any]):
    """Renderiza card de registro."""
    # Data formatada
    data_obj = datetime.fromisoformat(registro["data_registro"].split("T")[0])
    data_formatada = data_obj.strftime("%d/%m/%Y")

    # Status presença
    presente = registro.get("presente", False)
    status_cor = "#10b981" if presente else "#ef4444"
    status_texto = "✅ Presente" if presente else "❌ Ausente"

    # Nível
    nivel = registro.get("nivel_treino")
    nivel_texto = f"💪 Nível {nivel}/5" if nivel else ""

    st.markdown(f"""
        <div style="
            background: white;
            border-left: 4px solid {status_cor};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div style="font-size: 0.95rem; font-weight: 600;">
                    📅 {data_formatada}
                </div>
                <div>
                    <span style="background: {status_cor}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; margin-right: 0.5rem;">
                        {status_texto}
                    </span>
                    {f'<span style="background: #f59e0b; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem;">{nivel_texto}</span>' if nivel_texto else ''}
                </div>
            </div>
            {f'<div style="color: #666; font-size: 0.9rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #e5e7eb;">{registro.get("observacoes", "")}</div>' if registro.get("observacoes") else ''}
        </div>
    """, unsafe_allow_html=True)

    # Botão de deletar
    if st.button("🗑️ Excluir", key=f"del_reg_{registro['id']}", type="secondary"):
        st.session_state[f"confirm_delete_reg_{registro['id']}"] = True

    # Confirmação de exclusão
    if st.session_state.get(f"confirm_delete_reg_{registro['id']}", False):
        st.warning("⚠️ **Confirmar exclusão?**")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Sim", key=f"confirm_yes_reg_{registro['id']}", type="primary", use_container_width=True):
                sucesso, mensagem = deletar_registro(api_url, registro['id'])
                if sucesso:
                    st.success(mensagem)
                    del st.session_state[f"confirm_delete_reg_{registro['id']}"]
                    st.rerun()
                else:
                    st.error(mensagem)

        with col2:
            if st.button("❌ Não", key=f"confirm_no_reg_{registro['id']}", use_container_width=True):
                del st.session_state[f"confirm_delete_reg_{registro['id']}"]
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)


def render_evolucao_page(api_base_url: str):
    """Renderiza página completa de evolução."""
    custom_css()

    st.title("📊 Evolução")
    st.caption("Acompanhe o desempenho e presença dos seus alunos")
    st.markdown("---")

    # Seleção de aluno
    alunos = buscar_alunos(api_base_url)

    if not alunos:
        empty_state(
            icon="👥",
            title="Nenhum aluno cadastrado",
            description="Cadastre seus alunos no módulo 'Meus Alunos' para começar o acompanhamento.",
            action_text=None
        )
        return

    aluno_options = {f"{a['nome']} ({a['email'] or 'sem email'})": a["id"] for a in alunos}

    aluno_selecionado = st.selectbox(
        "👤 Selecione um aluno",
        options=list(aluno_options.keys())
    )

    if not aluno_selecionado:
        st.info("👆 Selecione um aluno para ver a evolução")
        return

    aluno_id = aluno_options[aluno_selecionado]

    st.markdown("---")

    # Estatísticas
    section_header("📈 Estatísticas", "Resumo de desempenho")
    render_stats_aluno(api_base_url, aluno_id)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2 = st.tabs(["📊 Histórico", "➕ Novo Registro"])

    with tab1:
        render_lista_registros(api_base_url, aluno_id)

    with tab2:
        render_form_registro(api_base_url, aluno_id)
