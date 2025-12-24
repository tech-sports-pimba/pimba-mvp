"""UI de Fichas de Treino - mobile-first e concisa."""
import streamlit as st
import requests
import time
from typing import Optional, Dict, List
from ui.components import custom_css, section_header, empty_state
from datetime import datetime


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
def buscar_fichas(api_url: str, aluno_id: Optional[int] = None, ativa: Optional[bool] = None):
    """Busca fichas de treino."""
    session = get_http_session()

    params = {}
    if aluno_id is not None:
        params["aluno_id"] = aluno_id
    if ativa is not None:
        params["ativa"] = ativa

    try:
        resp = session.get(
            f"{api_url}/treinos/",
            headers=get_auth_headers(),
            params=params,
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Erro ao buscar fichas: {e}")
        return {"total": 0, "fichas": []}


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


def criar_ficha(api_url: str, dados: dict):
    """Cria nova ficha de treino."""
    session = get_http_session()

    try:
        resp = session.post(
            f"{api_url}/treinos/",
            headers=get_auth_headers(),
            json=dados,
            timeout=5
        )
        resp.raise_for_status()

        # Limpa cache
        buscar_fichas.clear()

        return True, "Ficha criada!"
    except requests.HTTPError as e:
        try:
            error_detail = e.response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        return False, error_detail
    except requests.RequestException as e:
        return False, f"Erro ao criar: {e}"


def deletar_ficha(api_url: str, ficha_id: int):
    """Deleta ficha de treino."""
    session = get_http_session()

    try:
        resp = session.delete(
            f"{api_url}/treinos/{ficha_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()

        # Limpa cache
        buscar_fichas.clear()

        return True, "Ficha removida!"
    except requests.RequestException as e:
        return False, f"Erro ao deletar: {e}"


def adicionar_exercicio(api_url: str, ficha_id: int, exercicio: dict):
    """Adiciona exercício a uma ficha."""
    session = get_http_session()

    try:
        resp = session.post(
            f"{api_url}/treinos/{ficha_id}/exercicios",
            headers=get_auth_headers(),
            json=exercicio,
            timeout=5
        )
        resp.raise_for_status()

        # Limpa cache
        buscar_fichas.clear()

        return True, "Exercício adicionado!"
    except requests.RequestException as e:
        return False, f"Erro ao adicionar: {e}"


def deletar_exercicio(api_url: str, exercicio_id: int):
    """Deleta exercício."""
    session = get_http_session()

    try:
        resp = session.delete(
            f"{api_url}/treinos/exercicios/{exercicio_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()

        # Limpa cache
        buscar_fichas.clear()

        return True, "Exercício removido!"
    except requests.RequestException as e:
        return False, f"Erro ao deletar: {e}"


def render_ficha_card(api_url: str, ficha: dict):
    """Renderiza card de ficha de treino."""
    num_exercicios = len(ficha.get("exercicios", []))
    duracao_total = sum(ex["duracao_segundos"] for ex in ficha.get("exercicios", []))
    duracao_min = duracao_total // 60

    # Badge de status
    badge_color = "#10b981" if ficha.get("ativa") else "#6b7280"
    badge_text = "Ativa" if ficha.get("ativa") else "Inativa"

    st.markdown(f"""
        <div style="
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 0.25rem 0; color: #dc2626;">{ficha['nome']}</h3>
                    {f'<p style="color: #666; font-size: 0.9rem; margin: 0;">{ficha["descricao"]}</p>' if ficha.get("descricao") else ''}
                </div>
                <span style="background: {badge_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.85rem; font-weight: 600;">
                    {badge_text}
                </span>
            </div>

            <div style="display: flex; gap: 1.5rem; margin-top: 0.75rem; font-size: 0.9rem; color: #666;">
                <span>💪 {num_exercicios} exercício(s)</span>
                <span>⏱️ {duracao_min}min</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        if st.button("📝 Editar", key=f"edit_{ficha['id']}", use_container_width=True):
            st.session_state.editar_ficha_id = ficha["id"]
            st.rerun()

    with col2:
        if st.button("▶️ Executar", key=f"exec_{ficha['id']}", use_container_width=True, type="primary"):
            st.session_state.executar_ficha_id = ficha["id"]
            st.rerun()

    with col3:
        if st.button("🗑️", key=f"del_{ficha['id']}"):
            sucesso, msg = deletar_ficha(api_url, ficha["id"])
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


def render_form_ficha(api_url: str):
    """Renderiza formulário de criar ficha."""
    st.subheader("➕ Nova Ficha de Treino")

    # Busca alunos
    alunos = buscar_alunos(api_url)

    with st.form("form_ficha", clear_on_submit=False):
        # Nome
        nome = st.text_input("Nome da Ficha*", placeholder="Ex: Treino A - Peito/Tríceps")

        # Descrição
        descricao = st.text_area("Descrição", placeholder="Objetivo, observações...", height=80)

        # Aluno
        aluno_options = {"Template (sem aluno)": None}
        if alunos:
            aluno_options.update({f"{a['nome']}": a['id'] for a in alunos})

        aluno_selecionado = st.selectbox("Aluno", options=list(aluno_options.keys()))
        aluno_id = aluno_options[aluno_selecionado]

        # Ativa
        ativa = st.checkbox("Ficha ativa", value=True)

        # Botões
        col_submit, col_cancel = st.columns(2)

        with col_submit:
            submitted = st.form_submit_button("✅ Criar", use_container_width=True, type="primary")

        with col_cancel:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)

        if submitted:
            if not nome:
                st.error("❌ Nome é obrigatório")
            else:
                dados = {
                    "nome": nome,
                    "descricao": descricao if descricao else None,
                    "aluno_id": aluno_id,
                    "ativa": ativa,
                    "exercicios": [],
                }

                sucesso, msg = criar_ficha(api_url, dados)

                if sucesso:
                    st.success(msg)
                    st.session_state.show_form_ficha = False
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        if cancel:
            st.session_state.show_form_ficha = False
            st.rerun()


def render_editar_ficha_page(api_base_url: str, ficha_id: int):
    """Renderiza página de edição de ficha com exercícios."""
    custom_css()

    # Busca ficha
    dados = buscar_fichas(api_base_url)
    ficha = next((f for f in dados["fichas"] if f["id"] == ficha_id), None)

    if not ficha:
        st.error("❌ Ficha não encontrada")
        if st.button("← Voltar"):
            del st.session_state.editar_ficha_id
            st.rerun()
        return

    st.title(f"📝 Editando: {ficha['nome']}")

    if st.button("← Voltar para Fichas"):
        del st.session_state.editar_ficha_id
        st.rerun()

    st.markdown("---")

    # Seção de exercícios
    st.subheader("💪 Exercícios")

    exercicios = sorted(ficha.get("exercicios", []), key=lambda x: x["ordem"])

    if not exercicios:
        empty_state(
            icon="🏋️",
            title="Nenhum exercício adicionado",
            description="Adicione exercícios abaixo",
        )
    else:
        for ex in exercicios:
            duracao_min = ex["duracao_segundos"] // 60
            duracao_seg = ex["duracao_segundos"] % 60
            descanso_min = ex["descanso_segundos"] // 60
            descanso_seg = ex["descanso_segundos"] % 60

            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                    color: white;
                    border-radius: 12px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <div style="font-size: 0.75rem; opacity: 0.8; margin-bottom: 0.25rem;">#{ex['ordem'] + 1}</div>
                            <h4 style="margin: 0 0 0.5rem 0;">{ex['nome']}</h4>
                            {f'<p style="margin: 0; font-size: 0.9rem; opacity: 0.95;">{ex["descricao"]}</p>' if ex.get("descricao") else ''}
                        </div>
                    </div>
                    <div style="display: flex; gap: 1.5rem; margin-top: 0.75rem; font-size: 0.9rem;">
                        <span>⏱️ {duracao_min:02d}:{duracao_seg:02d}</span>
                        <span>😮‍💨 Descanso: {descanso_min:02d}:{descanso_seg:02d}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("🗑️", key=f"del_ex_{ex['id']}"):
                    sucesso, msg = deletar_exercicio(api_base_url, ex["id"])
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown("<br>", unsafe_allow_html=True)

    # Form para adicionar exercício
    with st.expander("➕ Adicionar Exercício", expanded=len(exercicios) == 0):
        with st.form(f"form_add_exercicio_{ficha_id}", clear_on_submit=True):
            nome = st.text_input("Nome do Exercício*", placeholder="Ex: Supino reto, Corrida, Prancha")

            descricao = st.text_area("Descrição/Instruções", placeholder="3x12 reps, 40kg...", height=80)

            col1, col2 = st.columns(2)

            with col1:
                duracao_min = st.number_input("Duração (minutos)", min_value=0, max_value=60, value=2)
                duracao_seg = st.number_input("Duração (segundos)", min_value=0, max_value=59, value=0)

            with col2:
                descanso_min = st.number_input("Descanso (minutos)", min_value=0, max_value=60, value=1)
                descanso_seg = st.number_input("Descanso (segundos)", min_value=0, max_value=59, value=0)

            submitted = st.form_submit_button("➕ Adicionar", use_container_width=True, type="primary")

            if submitted:
                if not nome:
                    st.error("❌ Nome é obrigatório")
                else:
                    exercicio_data = {
                        "nome": nome,
                        "descricao": descricao if descricao else None,
                        "duracao_segundos": duracao_min * 60 + duracao_seg,
                        "descanso_segundos": descanso_min * 60 + descanso_seg,
                        "ordem": len(exercicios),  # Adiciona no final
                    }

                    sucesso, msg = adicionar_exercicio(api_base_url, ficha_id, exercicio_data)

                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


def render_executor_treino_page(api_base_url: str, ficha_id: int):
    """Renderiza executor de treino com timer."""
    custom_css()

    # Busca ficha
    dados = buscar_fichas(api_base_url)
    ficha = next((f for f in dados["fichas"] if f["id"] == ficha_id), None)

    if not ficha:
        st.error("❌ Ficha não encontrada")
        if st.button("← Voltar"):
            del st.session_state.executar_ficha_id
            st.rerun()
        return

    exercicios = sorted(ficha.get("exercicios", []), key=lambda x: x["ordem"])

    if not exercicios:
        st.warning("⚠️ Esta ficha não possui exercícios")
        if st.button("← Voltar"):
            del st.session_state.executar_ficha_id
            st.rerun()
        return

    # Inicializa estado do executor
    if "timer_exercicio_atual" not in st.session_state:
        st.session_state.timer_exercicio_atual = 0
        st.session_state.timer_fase = "exercicio"  # "exercicio" ou "descanso"
        st.session_state.timer_segundos_restantes = exercicios[0]["duracao_segundos"]
        st.session_state.timer_pausado = False
        st.session_state.timer_start_time = time.time()

    ex_atual_idx = st.session_state.timer_exercicio_atual
    ex_atual = exercicios[ex_atual_idx]
    fase = st.session_state.timer_fase

    # Header
    st.title(f"⏱️ {ficha['nome']}")

    if st.button("← Finalizar Treino"):
        # Limpa estado
        for key in list(st.session_state.keys()):
            if key.startswith("timer_"):
                del st.session_state[key]
        del st.session_state.executar_ficha_id
        st.rerun()

    st.markdown("---")

    # Progresso
    progresso = (ex_atual_idx + 1) / len(exercicios)
    st.progress(progresso)
    st.caption(f"Exercício {ex_atual_idx + 1} de {len(exercicios)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Card do exercício atual
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            color: white;
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
        ">
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">
                {"🏋️ EXERCITANDO" if fase == "exercicio" else "😮‍💨 DESCANSANDO"}
            </div>
            <h1 style="margin: 0 0 1rem 0; font-size: 2rem;">{ex_atual['nome']}</h1>
            {f'<p style="margin: 0; font-size: 1.1rem; opacity: 0.95;">{ex_atual["descricao"]}</p>' if ex_atual.get("descricao") else ''}
        </div>
    """, unsafe_allow_html=True)

    # Timer
    segundos_restantes = st.session_state.timer_segundos_restantes
    minutos = segundos_restantes // 60
    segundos = segundos_restantes % 60

    # Timer visual grande
    timer_color = "#dc2626" if fase == "exercicio" else "#10b981"
    st.markdown(f"""
        <div style="
            background: {timer_color};
            color: white;
            border-radius: 20px;
            padding: 3rem 2rem;
            text-align: center;
            font-size: 4rem;
            font-weight: 700;
            font-family: 'Courier New', monospace;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        ">
            {minutos:02d}:{segundos:02d}
        </div>
    """, unsafe_allow_html=True)

    # Controles
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("⏮️ Anterior", use_container_width=True, disabled=ex_atual_idx == 0):
            # Volta para exercício anterior
            st.session_state.timer_exercicio_atual = max(0, ex_atual_idx - 1)
            st.session_state.timer_fase = "exercicio"
            st.session_state.timer_segundos_restantes = exercicios[st.session_state.timer_exercicio_atual]["duracao_segundos"]
            st.session_state.timer_pausado = False
            st.session_state.timer_start_time = time.time()
            st.rerun()

    with col2:
        pause_label = "▶️ Retomar" if st.session_state.timer_pausado else "⏸️ Pausar"
        if st.button(pause_label, use_container_width=True, type="secondary"):
            st.session_state.timer_pausado = not st.session_state.timer_pausado
            st.session_state.timer_start_time = time.time()
            st.rerun()

    with col3:
        if st.button("⏭️ Próximo", use_container_width=True, disabled=ex_atual_idx == len(exercicios) - 1):
            # Avança para próximo exercício
            st.session_state.timer_exercicio_atual = min(len(exercicios) - 1, ex_atual_idx + 1)
            st.session_state.timer_fase = "exercicio"
            st.session_state.timer_segundos_restantes = exercicios[st.session_state.timer_exercicio_atual]["duracao_segundos"]
            st.session_state.timer_pausado = False
            st.session_state.timer_start_time = time.time()
            st.rerun()

    with col4:
        if st.button("✅ Concluir", use_container_width=True, type="primary"):
            # Marca exercício como concluído e avança
            if fase == "exercicio":
                # Vai para descanso
                st.session_state.timer_fase = "descanso"
                st.session_state.timer_segundos_restantes = ex_atual["descanso_segundos"]
                st.session_state.timer_pausado = False
                st.session_state.timer_start_time = time.time()
            else:
                # Descanso concluído, vai para próximo exercício
                if ex_atual_idx < len(exercicios) - 1:
                    st.session_state.timer_exercicio_atual += 1
                    st.session_state.timer_fase = "exercicio"
                    st.session_state.timer_segundos_restantes = exercicios[st.session_state.timer_exercicio_atual]["duracao_segundos"]
                    st.session_state.timer_pausado = False
                    st.session_state.timer_start_time = time.time()
                else:
                    # Treino completo!
                    st.success("🎉 Treino completo! Parabéns!")
                    time.sleep(2)
                    for key in list(st.session_state.keys()):
                        if key.startswith("timer_"):
                            del st.session_state[key]
                    del st.session_state.executar_ficha_id
            st.rerun()

    # Lista de exercícios
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("📋 Sequência de Exercícios")

    for idx, ex in enumerate(exercicios):
        duracao_min = ex["duracao_segundos"] // 60
        duracao_seg = ex["duracao_segundos"] % 60

        if idx == ex_atual_idx:
            # Exercício atual - destaque
            st.markdown(f"""
                <div style="
                    background: #fef2f2;
                    border: 2px solid #dc2626;
                    border-radius: 8px;
                    padding: 0.75rem;
                    margin-bottom: 0.5rem;
                ">
                    <strong style="color: #dc2626;">#{idx + 1} - {ex['nome']}</strong> (⏱️ {duracao_min:02d}:{duracao_seg:02d})
                </div>
            """, unsafe_allow_html=True)
        elif idx < ex_atual_idx:
            # Exercício concluído
            st.markdown(f"""
                <div style="
                    background: #f0fdf4;
                    border: 1px solid #d1fae5;
                    border-radius: 8px;
                    padding: 0.75rem;
                    margin-bottom: 0.5rem;
                    opacity: 0.7;
                ">
                    ✅ #{idx + 1} - {ex['nome']}
                </div>
            """, unsafe_allow_html=True)
        else:
            # Exercício pendente
            st.markdown(f"""
                <div style="
                    background: #f9fafb;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 0.75rem;
                    margin-bottom: 0.5rem;
                    opacity: 0.6;
                ">
                    #{idx + 1} - {ex['nome']} (⏱️ {duracao_min:02d}:{duracao_seg:02d})
                </div>
            """, unsafe_allow_html=True)

    # Atualiza timer automaticamente
    if not st.session_state.timer_pausado and segundos_restantes > 0:
        time.sleep(1)
        st.session_state.timer_segundos_restantes -= 1
        st.rerun()
    elif segundos_restantes == 0 and not st.session_state.timer_pausado:
        # Timer zerou - avança automaticamente
        if fase == "exercicio":
            # Vai para descanso
            st.session_state.timer_fase = "descanso"
            st.session_state.timer_segundos_restantes = ex_atual["descanso_segundos"]
            st.session_state.timer_start_time = time.time()
        else:
            # Descanso concluído, vai para próximo
            if ex_atual_idx < len(exercicios) - 1:
                st.session_state.timer_exercicio_atual += 1
                st.session_state.timer_fase = "exercicio"
                st.session_state.timer_segundos_restantes = exercicios[st.session_state.timer_exercicio_atual]["duracao_segundos"]
                st.session_state.timer_start_time = time.time()
        st.rerun()


def render_treinos_page(api_base_url: str):
    """Renderiza página de fichas de treino."""
    custom_css()

    # Roteamento: se está executando, mostra executor
    if "executar_ficha_id" in st.session_state:
        render_executor_treino_page(api_base_url, st.session_state.executar_ficha_id)
        return

    # Roteamento: se está editando, mostra página de edição
    if "editar_ficha_id" in st.session_state:
        render_editar_ficha_page(api_base_url, st.session_state.editar_ficha_id)
        return

    st.title("💪 Fichas de Treino")
    st.caption("Crie e gerencie suas fichas de treino")
    st.markdown("---")

    # Tabs
    tab1, tab2 = st.tabs(["📋 Minhas Fichas", "➕ Nova Ficha"])

    with tab1:
        # Filtros
        col1, col2 = st.columns([3, 1])

        with col1:
            alunos = buscar_alunos(api_base_url)
            filtro_aluno_options = {"Todas": None}
            if alunos:
                filtro_aluno_options.update({a["nome"]: a["id"] for a in alunos})

            filtro_aluno = st.selectbox("Filtrar por aluno", options=list(filtro_aluno_options.keys()))
            aluno_id_filtro = filtro_aluno_options[filtro_aluno]

        with col2:
            filtro_ativa = st.selectbox("Status", options=["Todas", "Ativas", "Inativas"])
            ativa_filtro = None if filtro_ativa == "Todas" else (filtro_ativa == "Ativas")

        st.markdown("<br>", unsafe_allow_html=True)

        # Busca fichas
        dados = buscar_fichas(api_base_url, aluno_id=aluno_id_filtro, ativa=ativa_filtro)
        fichas = dados.get("fichas", [])

        if not fichas:
            empty_state(
                icon="💪",
                title="Nenhuma ficha cadastrada",
                description="Crie sua primeira ficha de treino na aba 'Nova Ficha'",
            )
        else:
            for ficha in fichas:
                render_ficha_card(api_base_url, ficha)

    with tab2:
        render_form_ficha(api_base_url)
