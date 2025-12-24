"""Tela de autenticação/login moderna e mobile-first."""
import streamlit as st
import requests


def render_auth_page(api_base_url: str):
    """
    Renderiza página de login moderna.
    Mobile-first com visual clean e profissional.
    """
    # CSS customizado para página de login
    st.markdown("""
        <style>
        .login-container {
            max-width: 420px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }

        .logo-section {
            text-align: center;
            margin-bottom: 2rem;
        }

        .logo-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }

        .app-title {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        /* Desktop: aumenta área de login */
        @media (min-width: 768px) {
            .login-container {
                max-width: 480px;
            }
        }

        .app-subtitle {
            color: #666;
            font-size: 0.95rem;
            margin-bottom: 2rem;
        }

        .login-card {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid #f0f0f0;
        }

        .dev-mode-section {
            margin-top: 2rem;
            padding: 1.5rem;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #ffc107;
        }

        .role-button {
            margin-bottom: 0.75rem;
        }

        @media (max-width: 768px) {
            .login-container {
                padding: 1rem 0.5rem;
            }

            .login-card {
                padding: 1.5rem;
            }

            .logo-icon {
                font-size: 3rem;
            }

            .app-title {
                font-size: 1.75rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # Container principal
    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    # Logo e título
    st.markdown("""
        <div class="logo-section">
            <div class="logo-icon">💪</div>
            <h1 class="app-title">Pimba</h1>
            <p class="app-subtitle">Gestão inteligente para personal trainers</p>
        </div>
    """, unsafe_allow_html=True)

    # Card de login
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    # Modo desenvolvimento
    with st.expander("🚧 Modo Desenvolvimento", expanded=False):
        st.warning(
            "**Atenção:** Modo de desenvolvimento ativo. "
            "Você será autenticado sem verificar credenciais do Firebase."
        )

        st.markdown("**Escolha seu perfil:**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("👨‍💼 Admin", use_container_width=True, type="secondary"):
                st.session_state.authenticated = True
                st.session_state.user_info = {
                    "user_id": 1,
                    "nome": "Admin",
                    "email": "admin@pimba.com",
                    "role": "admin",
                    "firebase_uid": "dev-mock-uid-admin",
                }
                st.session_state.auth_token = "dev-mock-token"
                st.success("✅ Logado como Admin!")
                st.rerun()

        with col2:
            if st.button("💪 Personal", use_container_width=True, type="primary"):
                st.session_state.authenticated = True
                st.session_state.user_info = {
                    "user_id": 2,
                    "nome": "Personal Trainer",
                    "email": "personal@pimba.com",
                    "role": "personal",
                    "firebase_uid": "dev-mock-uid-personal",
                    "personal_id": 1,
                }
                st.session_state.auth_token = "dev-mock-token-personal"
                st.success("✅ Logado como Personal!")
                st.rerun()

    st.markdown("---")

    # Login com Firebase (placeholder)
    st.markdown("### 🔐 Login")

    st.info(
        "**Firebase Auth** será integrado aqui em produção.\n\n"
        "Por enquanto, use o **Modo Desenvolvimento** acima para testar o sistema."
    )

    with st.form("login_form"):
        st.text_input("📧 Email", placeholder="seu@email.com", key="login_email")
        st.text_input("🔑 Senha", type="password", placeholder="••••••••", key="login_password")

        col1, col2 = st.columns([2, 1])
        with col1:
            remember = st.checkbox("Lembrar de mim")
        with col2:
            st.markdown("<div style='text-align: right;'><small>Esqueceu?</small></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            st.error("❌ Firebase Auth ainda não implementado. Use o Modo Desenvolvimento.")

    st.markdown('</div>', unsafe_allow_html=True)  # Fecha login-card

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #999; font-size: 0.875rem; padding: 1rem 0;">
            <p>Primeira vez aqui? Use o <strong>Modo Desenvolvimento</strong> para explorar.</p>
            <p style="margin-top: 0.5rem;">💡 <small>Desenvolvido com Streamlit + FastAPI + Firebase</small></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # Fecha login-container
