"""UI de Timer Livre - para treinos rápidos não planejados."""
import streamlit as st
import time
from typing import List, Dict
from ui.components import custom_css


def render_timer_livre_page():
    """Renderiza página de timer livre para treinos não planejados."""
    custom_css()

    # Inicializa lista de exercícios na sessão
    if "timer_livre_exercicios" not in st.session_state:
        st.session_state.timer_livre_exercicios = []

    # Roteamento: se está executando, mostra executor
    if st.session_state.get("timer_livre_executando", False):
        render_executor_timer_livre()
        return

    st.title("⏱️ Timer Livre")
    st.caption("Monte e execute treinos rápidos sem salvar")
    st.markdown("---")

    # Lista atual de exercícios
    exercicios = st.session_state.timer_livre_exercicios

    if exercicios:
        st.subheader(f"💪 Treino Atual ({len(exercicios)} exercícios)")

        duracao_total = sum(ex["duracao_segundos"] + ex["descanso_segundos"] for ex in exercicios)
        duracao_min = duracao_total // 60
        duracao_seg = duracao_total % 60

        st.info(f"⏱️ Duração total: {duracao_min:02d}:{duracao_seg:02d}")

        # Mostra exercícios
        for idx, ex in enumerate(exercicios):
            dur_min = ex["duracao_segundos"] // 60
            dur_seg = ex["duracao_segundos"] % 60
            desc_min = ex["descanso_segundos"] // 60
            desc_seg = ex["descanso_segundos"] % 60

            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                    color: white;
                    border-radius: 12px;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-size: 0.75rem; opacity: 0.8;">#{idx + 1}</div>
                            <h4 style="margin: 0.25rem 0;">{ex['nome']}</h4>
                            <div style="font-size: 0.9rem; opacity: 0.95; margin-top: 0.25rem;">
                                ⏱️ {dur_min:02d}:{dur_seg:02d} • 😮‍💨 {desc_min:02d}:{desc_seg:02d}
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("🗑️", key=f"del_livre_{idx}"):
                    st.session_state.timer_livre_exercicios.pop(idx)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Botões de ação
        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ EXECUTAR TREINO", use_container_width=True, type="primary"):
                st.session_state.timer_livre_executando = True
                # Inicializa estado do executor
                st.session_state.timer_livre_idx = 0
                st.session_state.timer_livre_fase = "exercicio"
                st.session_state.timer_livre_segundos = exercicios[0]["duracao_segundos"]
                st.session_state.timer_livre_pausado = False
                st.rerun()

        with col2:
            if st.button("🗑️ Limpar Tudo", use_container_width=True):
                st.session_state.timer_livre_exercicios = []
                st.rerun()

        st.markdown("---")

    else:
        st.info("➕ Adicione exercícios abaixo para começar")

    # Form para adicionar exercício
    st.subheader("➕ Adicionar Exercício")

    with st.form("form_add_exercicio_livre", clear_on_submit=True):
        nome = st.text_input("Nome do Exercício*", placeholder="Ex: Supino, Corrida, Prancha...")

        col1, col2 = st.columns(2)

        with col1:
            st.caption("Duração do exercício")
            dur_min = st.number_input("Minutos", min_value=0, max_value=60, value=1, key="dur_min")
            dur_seg = st.number_input("Segundos", min_value=0, max_value=59, value=0, key="dur_seg")

        with col2:
            st.caption("Tempo de descanso")
            desc_min = st.number_input("Minutos", min_value=0, max_value=60, value=0, key="desc_min")
            desc_seg = st.number_input("Segundos", min_value=0, max_value=59, value=30, key="desc_seg")

        submitted = st.form_submit_button("➕ Adicionar Exercício", use_container_width=True, type="primary")

        if submitted:
            if not nome:
                st.error("❌ Nome é obrigatório")
            else:
                exercicio = {
                    "nome": nome,
                    "duracao_segundos": dur_min * 60 + dur_seg,
                    "descanso_segundos": desc_min * 60 + desc_seg,
                }

                st.session_state.timer_livre_exercicios.append(exercicio)
                st.success(f"✅ '{nome}' adicionado!")
                st.rerun()


def render_executor_timer_livre():
    """Renderiza executor do timer livre."""
    exercicios = st.session_state.timer_livre_exercicios

    if not exercicios:
        st.error("❌ Nenhum exercício no treino")
        if st.button("← Voltar"):
            st.session_state.timer_livre_executando = False
            st.rerun()
        return

    ex_atual_idx = st.session_state.timer_livre_idx
    ex_atual = exercicios[ex_atual_idx]
    fase = st.session_state.timer_livre_fase

    # Header
    st.title("⏱️ Timer Livre")

    if st.button("← Finalizar e Voltar"):
        # Limpa estado do executor
        for key in list(st.session_state.keys()):
            if key.startswith("timer_livre_") and key != "timer_livre_exercicios":
                del st.session_state[key]
        st.session_state.timer_livre_executando = False
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
            <h1 style="margin: 0; font-size: 2rem;">{ex_atual['nome']}</h1>
        </div>
    """, unsafe_allow_html=True)

    # Timer
    segundos_restantes = st.session_state.timer_livre_segundos
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
            font-size: 5rem;
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
            st.session_state.timer_livre_idx = max(0, ex_atual_idx - 1)
            st.session_state.timer_livre_fase = "exercicio"
            st.session_state.timer_livre_segundos = exercicios[st.session_state.timer_livre_idx]["duracao_segundos"]
            st.session_state.timer_livre_pausado = False
            st.rerun()

    with col2:
        pause_label = "▶️ Retomar" if st.session_state.timer_livre_pausado else "⏸️ Pausar"
        if st.button(pause_label, use_container_width=True, type="secondary"):
            st.session_state.timer_livre_pausado = not st.session_state.timer_livre_pausado
            st.rerun()

    with col3:
        if st.button("⏭️ Próximo", use_container_width=True, disabled=ex_atual_idx == len(exercicios) - 1):
            st.session_state.timer_livre_idx = min(len(exercicios) - 1, ex_atual_idx + 1)
            st.session_state.timer_livre_fase = "exercicio"
            st.session_state.timer_livre_segundos = exercicios[st.session_state.timer_livre_idx]["duracao_segundos"]
            st.session_state.timer_livre_pausado = False
            st.rerun()

    with col4:
        if st.button("✅ Concluir", use_container_width=True, type="primary"):
            if fase == "exercicio":
                # Vai para descanso
                st.session_state.timer_livre_fase = "descanso"
                st.session_state.timer_livre_segundos = ex_atual["descanso_segundos"]
                st.session_state.timer_livre_pausado = False
            else:
                # Descanso concluído
                if ex_atual_idx < len(exercicios) - 1:
                    st.session_state.timer_livre_idx += 1
                    st.session_state.timer_livre_fase = "exercicio"
                    st.session_state.timer_livre_segundos = exercicios[st.session_state.timer_livre_idx]["duracao_segundos"]
                    st.session_state.timer_livre_pausado = False
                else:
                    # Treino completo!
                    st.success("🎉 Treino completo!")
                    time.sleep(2)
                    for key in list(st.session_state.keys()):
                        if key.startswith("timer_livre_"):
                            del st.session_state[key]
            st.rerun()

    # Lista de exercícios
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("📋 Sequência")

    for idx, ex in enumerate(exercicios):
        dur_min = ex["duracao_segundos"] // 60
        dur_seg = ex["duracao_segundos"] % 60

        if idx == ex_atual_idx:
            st.markdown(f"""
                <div style="background: #fef2f2; border: 2px solid #dc2626; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;">
                    <strong style="color: #dc2626;">#{idx + 1} - {ex['nome']}</strong> (⏱️ {dur_min:02d}:{dur_seg:02d})
                </div>
            """, unsafe_allow_html=True)
        elif idx < ex_atual_idx:
            st.markdown(f"""
                <div style="background: #f0fdf4; border: 1px solid #d1fae5; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; opacity: 0.7;">
                    ✅ #{idx + 1} - {ex['nome']}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; opacity: 0.6;">
                    #{idx + 1} - {ex['nome']} (⏱️ {dur_min:02d}:{dur_seg:02d})
                </div>
            """, unsafe_allow_html=True)

    # Atualiza timer automaticamente
    if not st.session_state.timer_livre_pausado and segundos_restantes > 0:
        time.sleep(1)
        st.session_state.timer_livre_segundos -= 1
        st.rerun()
    elif segundos_restantes == 0 and not st.session_state.timer_livre_pausado:
        # Timer zerou
        if fase == "exercicio":
            st.session_state.timer_livre_fase = "descanso"
            st.session_state.timer_livre_segundos = ex_atual["descanso_segundos"]
        else:
            if ex_atual_idx < len(exercicios) - 1:
                st.session_state.timer_livre_idx += 1
                st.session_state.timer_livre_fase = "exercicio"
                st.session_state.timer_livre_segundos = exercicios[st.session_state.timer_livre_idx]["duracao_segundos"]
        st.rerun()
