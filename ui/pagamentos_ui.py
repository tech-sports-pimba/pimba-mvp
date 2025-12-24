"""UI de gestão de pagamentos - controle financeiro simples."""
import streamlit as st
import requests
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from decimal import Decimal
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
def buscar_pagamentos(
    api_url: str,
    tipo: Optional[str] = None,
    aluno_id: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """Busca pagamentos com cache de 30s."""
    session = get_http_session()

    params = {}
    if tipo:
        params["tipo"] = tipo
    if aluno_id:
        params["aluno_id"] = aluno_id
    if data_inicio:
        params["data_inicio"] = data_inicio
    if data_fim:
        params["data_fim"] = data_fim

    try:
        resp = session.get(
            f"{api_url}/pagamentos/",
            headers=get_auth_headers(),
            params=params,
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Erro ao buscar pagamentos: {e}")
        return {"total": 0, "pagamentos": []}


@st.cache_data(ttl=60)
def buscar_resumo_financeiro(api_url: str, mes: Optional[int] = None, ano: Optional[int] = None):
    """Busca resumo financeiro com cache de 60s."""
    session = get_http_session()

    params = {}
    if mes:
        params["mes"] = mes
    if ano:
        params["ano"] = ano

    try:
        resp = session.get(
            f"{api_url}/pagamentos/resumo",
            headers=get_auth_headers(),
            params=params,
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {
            "total_recebido": 0,
            "total_a_receber": 0,
            "total_mes": 0,
            "quantidade_pagamentos": 0
        }


@st.cache_data(ttl=30)
def buscar_alunos(api_url: str):
    """Busca lista de alunos."""
    session = get_http_session()
    try:
        resp = session.get(
            f"{api_url}/alunos/",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()
        return resp.json().get("alunos", [])
    except:
        return []


def criar_pagamento(api_url: str, dados: dict):
    """Cria novo pagamento."""
    session = get_http_session()

    try:
        resp = session.post(
            f"{api_url}/pagamentos/",
            headers=get_auth_headers(),
            json=dados,
            timeout=5
        )
        resp.raise_for_status()

        # Limpa caches
        buscar_pagamentos.clear()
        buscar_resumo_financeiro.clear()

        return True, "✅ Pagamento registrado!"
    except requests.HTTPError as e:
        try:
            error_detail = e.response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        return False, f"❌ Erro: {error_detail}"
    except requests.RequestException as e:
        return False, f"❌ Erro ao criar: {e}"


def deletar_pagamento(api_url: str, pagamento_id: int):
    """Deleta pagamento."""
    session = get_http_session()

    try:
        resp = session.delete(
            f"{api_url}/pagamentos/{pagamento_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()

        # Limpa caches
        buscar_pagamentos.clear()
        buscar_resumo_financeiro.clear()

        return True, "✅ Pagamento removido!"
    except requests.RequestException as e:
        return False, f"❌ Erro ao deletar: {e}"


def render_dashboard_financeiro(api_url: str):
    """Renderiza dashboard financeiro."""
    st.subheader("📊 Resumo Financeiro")

    # Seletor de mês/ano
    col1, col2 = st.columns(2)

    hoje = date.today()

    with col1:
        mes = st.selectbox(
            "Mês",
            options=list(range(1, 13)),
            index=hoje.month - 1,
            format_func=lambda x: [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ][x - 1]
        )

    with col2:
        ano = st.number_input(
            "Ano",
            min_value=2020,
            max_value=2100,
            value=hoje.year
        )

    # Busca resumo
    resumo = buscar_resumo_financeiro(api_url, mes=mes, ano=ano)

    # Grid de métricas
    stats = [
        {
            "title": "Recebido (Mês)",
            "value": f"R$ {float(resumo['total_mes']):.2f}",
            "icon": "💰",
            "color": "success"
        },
        {
            "title": "Total Recebido",
            "value": f"R$ {float(resumo['total_recebido']):.2f}",
            "icon": "✅",
            "color": "info"
        },
        {
            "title": "A Receber",
            "value": f"R$ {float(resumo['total_a_receber']):.2f}",
            "icon": "⏳",
            "color": "warning"
        },
        {
            "title": "Pagamentos (Mês)",
            "value": str(resumo['quantidade_pagamentos']),
            "icon": "📋",
            "color": "default"
        },
    ]

    stat_grid(stats)


def render_form_pagamento(api_url: str):
    """Form para criar novo pagamento."""
    st.subheader("➕ Registrar Pagamento")

    with st.form("form_criar_pagamento", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            valor = st.number_input(
                "Valor (R$)*",
                min_value=0.01,
                step=0.01,
                format="%.2f"
            )

            data_pagamento = st.date_input(
                "Data*",
                value=date.today(),
                max_value=date.today()
            )

        with col2:
            tipo = st.selectbox(
                "Tipo*",
                options=["recebido", "a_receber"],
                format_func=lambda x: "✅ Recebido" if x == "recebido" else "⏳ A Receber"
            )

            alunos = buscar_alunos(api_url)
            aluno_options = {"Nenhum (geral)": None}
            if alunos:
                aluno_options.update({a["nome"]: a["id"] for a in alunos})

            aluno_selecionado = st.selectbox(
                "Aluno",
                options=list(aluno_options.keys())
            )
            aluno_id = aluno_options[aluno_selecionado]

        descricao = st.text_area(
            "Descrição",
            placeholder="Ex: Mensalidade de dezembro, Sessão avulsa, etc.",
            height=80
        )

        submitted = st.form_submit_button("💾 Registrar Pagamento", use_container_width=True, type="primary")

        if submitted:
            if valor <= 0:
                st.error("❌ Valor deve ser maior que zero")
                return

            payload = {
                "valor": float(valor),
                "data_pagamento": data_pagamento.isoformat(),
                "tipo": tipo,
                "descricao": descricao if descricao else None,
            }

            if aluno_id:
                payload["aluno_id"] = aluno_id

            sucesso, mensagem = criar_pagamento(api_url, payload)

            if sucesso:
                st.success(mensagem)
                st.rerun()
            else:
                st.error(mensagem)


def render_lista_pagamentos(api_url: str):
    """Renderiza lista de pagamentos."""
    st.subheader("💳 Histórico de Pagamentos")

    # Filtros
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        filtro_tipo = st.selectbox(
            "Tipo",
            options=["Todos", "Recebido", "A Receber"],
            label_visibility="collapsed"
        )
        tipo_filter = None
        if filtro_tipo == "Recebido":
            tipo_filter = "recebido"
        elif filtro_tipo == "A Receber":
            tipo_filter = "a_receber"

    with col2:
        alunos = buscar_alunos(api_url)
        aluno_options = {"Todos os alunos": None}
        if alunos:
            aluno_options.update({a["nome"]: a["id"] for a in alunos})

        aluno_selecionado = st.selectbox(
            "Aluno",
            options=list(aluno_options.keys()),
            label_visibility="collapsed"
        )
        aluno_id_filter = aluno_options[aluno_selecionado]

    with col3:
        if st.button("🔄 Atualizar", use_container_width=True):
            buscar_pagamentos.clear()
            buscar_resumo_financeiro.clear()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Busca pagamentos
    dados = buscar_pagamentos(
        api_url,
        tipo=tipo_filter,
        aluno_id=aluno_id_filter
    )
    pagamentos = dados.get("pagamentos", [])

    if not pagamentos:
        empty_state(
            icon="💳",
            title="Nenhum pagamento encontrado",
            description="Registre seu primeiro pagamento usando o formulário acima.",
            action_text=None
        )
    else:
        st.caption(f"**{dados['total']} pagamento(s) encontrado(s)**")
        st.markdown("<br>", unsafe_allow_html=True)

        for pag in pagamentos:
            render_pagamento_card(api_url, pag)


def render_pagamento_card(api_url: str, pagamento: Dict[str, Any]):
    """Renderiza card de pagamento."""
    # Cor baseada no tipo
    cor = "#10b981" if pagamento["tipo"] == "recebido" else "#f59e0b"
    tipo_texto = "✅ Recebido" if pagamento["tipo"] == "recebido" else "⏳ A Receber"

    # Data formatada
    data_obj = datetime.fromisoformat(pagamento["data_pagamento"].split("T")[0])
    data_formatada = data_obj.strftime("%d/%m/%Y")

    # Aluno
    aluno_texto = pagamento.get("aluno_nome") or "Geral"

    st.markdown(f"""
        <div style="
            background: white;
            border-left: 4px solid {cor};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: {cor};">
                        R$ {float(pagamento['valor']):.2f}
                    </div>
                    <div style="font-size: 0.85rem; color: #666;">
                        {tipo_texto} • 📅 {data_formatada}
                    </div>
                </div>
                <div style="background: {cor}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem;">
                    👤 {aluno_texto}
                </div>
            </div>
            {f'<div style="color: #666; font-size: 0.9rem; margin-top: 0.5rem;">{pagamento.get("descricao", "")}</div>' if pagamento.get("descricao") else ''}
        </div>
    """, unsafe_allow_html=True)

    # Botão de deletar
    if st.button("🗑️ Excluir", key=f"del_pag_{pagamento['id']}", type="secondary"):
        st.session_state[f"confirm_delete_pag_{pagamento['id']}"] = True

    # Confirmação de exclusão
    if st.session_state.get(f"confirm_delete_pag_{pagamento['id']}", False):
        st.warning(f"⚠️ **Confirmar exclusão?** Esta ação não pode ser desfeita!")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Sim, excluir", key=f"confirm_yes_pag_{pagamento['id']}", type="primary", use_container_width=True):
                sucesso, mensagem = deletar_pagamento(api_url, pagamento['id'])
                if sucesso:
                    st.success(mensagem)
                    del st.session_state[f"confirm_delete_pag_{pagamento['id']}"]
                    st.rerun()
                else:
                    st.error(mensagem)

        with col2:
            if st.button("❌ Cancelar", key=f"confirm_no_pag_{pagamento['id']}", use_container_width=True):
                del st.session_state[f"confirm_delete_pag_{pagamento['id']}"]
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)


def render_pagamentos_page(api_base_url: str):
    """Renderiza página completa de pagamentos."""
    custom_css()

    st.title("💰 Financeiro")
    st.caption("Controle simples de receitas e pagamentos")
    st.markdown("---")

    # Dashboard financeiro
    render_dashboard_financeiro(api_base_url)

    st.markdown("---")

    # Tabs
    tab1, tab2 = st.tabs(["💳 Histórico", "➕ Novo Pagamento"])

    with tab1:
        render_lista_pagamentos(api_base_url)

    with tab2:
        render_form_pagamento(api_base_url)
