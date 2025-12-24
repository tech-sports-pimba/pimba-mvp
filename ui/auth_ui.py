"""Tela de autenticação/login."""
import streamlit as st
import requests


def render_auth_page(api_base_url: str):
    """
    Renderiza página de login.

    Para MVP: login simples com email/senha.
    No futuro: integrar Firebase UI Web component.
    """
    st.title("🔐 Login - Pimba")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Acesso ao Sistema")

        # Para MVP: permite bypass de autenticação para desenvolvimento
        if st.checkbox("🚧 Modo Desenvolvimento (bypass auth)", value=False):
            st.warning(
                "**Atenção:** Modo de desenvolvimento ativo. "
                "Você será autenticado como admin sem verificar credenciais."
            )

            if st.button("Entrar como Admin", use_container_width=True):
                # Mock user para desenvolvimento
                st.session_state.authenticated = True
                st.session_state.user_info = {
                    "user_id": 1,
                    "nome": "Admin Dev",
                    "email": "admin@pimba.com",
                    "role": "admin",
                    "firebase_uid": "dev-mock-uid",
                }
                st.session_state.auth_token = "dev-mock-token"
                st.success("✅ Login como admin (dev mode)")
                st.rerun()

            if st.button("Entrar como Personal", use_container_width=True):
                # Mock personal para desenvolvimento
                st.session_state.authenticated = True
                st.session_state.user_info = {
                    "user_id": 2,
                    "nome": "Personal Dev",
                    "email": "personal@pimba.com",
                    "role": "personal",
                    "firebase_uid": "dev-mock-uid-personal",
                    "personal_id": 1,
                }
                st.session_state.auth_token = "dev-mock-token-personal"
                st.success("✅ Login como personal (dev mode)")
                st.rerun()

        else:
            st.info(
                "🚀 **Produção:** Integrar Firebase Auth aqui.\n\n"
                "Por enquanto, use o modo de desenvolvimento acima para testar o sistema."
            )

            # Placeholder para login real (Firebase)
            with st.form("login_form"):
                st.text_input("Email", key="login_email")
                st.text_input("Password", type="password", key="login_password")

                submitted = st.form_submit_button("Entrar", use_container_width=True)

                if submitted:
                    st.error(
                        "❌ Login com Firebase ainda não implementado. "
                        "Use o modo de desenvolvimento acima."
                    )

        st.markdown("---")
        st.caption(
            "💡 **Dica:** Para produção, configure Firebase Auth "
            "e integre Firebase UI Web component aqui."
        )
