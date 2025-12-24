"""Tela de autenticação/login moderna e mobile-first."""
import streamlit as st
import streamlit.components.v1 as components
import requests
import os
import json
from utils.single_file_session import save_auth_single_file
from config.settings import settings


def render_auth_page(api_base_url: str):
    """
    Renderiza página de login moderna.
    - DEBUG=True: Modo desenvolvimento com logins mock rápidos (sem Firebase)
    - DEBUG=False: Login via Firebase (Google ou email/senha)
    """
    # Verifica modo DEBUG
    is_debug = os.getenv("DEBUG", "False").lower() == "true"

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

        .google-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.95rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }

        .google-btn:hover {
            border-color: #dc2626;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.15);
        }

        .divider {
            text-align: center;
            margin: 1.5rem 0;
            color: #999;
            font-size: 0.875rem;
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


    # DESENVOLVIMENTO: Modo debug ativo
    if is_debug:
        st.info("🚧 **Modo Desenvolvimento Ativo** (DEBUG=True)")

        # AUTO-LOGIN: Restaura último perfil usado
        last_login_file = ".last_login"

        # Verifica se deve fazer auto-login
        if not st.session_state.get("authenticated", False) and os.path.exists(last_login_file):
            try:
                with open(last_login_file, 'r') as f:
                    last_profile = f.read().strip()

                if last_profile == "admin":
                    admin_info = {
                        "user_id": 1,
                        "nome": settings.DEV_ADMIN_NAME,
                        "email": settings.DEV_ADMIN_EMAIL,
                        "role": "admin",
                        "firebase_uid": settings.DEV_ADMIN_UID,
                    }
                    # DEBUG: usa save_auth_single_file (com persistência)
                    save_auth_single_file(settings.DEV_ADMIN_TOKEN, admin_info)
                    st.rerun()
                elif last_profile == "personal":
                    personal_info = {
                        "user_id": 2,
                        "nome": settings.DEV_PERSONAL_NAME,
                        "email": settings.DEV_PERSONAL_EMAIL,
                        "role": "personal",
                        "firebase_uid": settings.DEV_PERSONAL_UID,
                        "personal_id": settings.DEV_PERSONAL_ID,
                    }
                    # DEBUG: usa save_auth_single_file (com persistência)
                    save_auth_single_file(settings.DEV_PERSONAL_TOKEN, personal_info)
                    st.rerun()
            except:
                pass  # Ignora erros silenciosamente

        # Opção de trocar perfil
        with st.expander("Trocar perfil de teste"):
            col1, col2 = st.columns(2)

            with col1:
                if st.button("👨‍💼 Admin", use_container_width=True):
                    admin_info = {
                        "user_id": 1,
                        "nome": settings.DEV_ADMIN_NAME,
                        "email": settings.DEV_ADMIN_EMAIL,
                        "role": "admin",
                        "firebase_uid": settings.DEV_ADMIN_UID,
                    }
                    # Salva último perfil usado
                    with open(last_login_file, 'w') as f:
                        f.write("admin")
                    # DEBUG: usa save_auth_single_file (com persistência)
                    save_auth_single_file(settings.DEV_ADMIN_TOKEN, admin_info)
                    st.rerun()

            with col2:
                if st.button("💪 Personal", use_container_width=True, type="primary"):
                    personal_info = {
                        "user_id": 2,
                        "nome": settings.DEV_PERSONAL_NAME,
                        "email": settings.DEV_PERSONAL_EMAIL,
                        "role": "personal",
                        "firebase_uid": settings.DEV_PERSONAL_UID,
                        "personal_id": settings.DEV_PERSONAL_ID,
                    }
                    # Salva último perfil usado
                    with open(last_login_file, 'w') as f:
                        f.write("personal")
                    # DEBUG: usa save_auth_single_file (com persistência)
                    save_auth_single_file(settings.DEV_PERSONAL_TOKEN, personal_info)
                    st.rerun()

    # PRODUÇÃO: Firebase Auth
    else:
        render_firebase_auth(api_base_url)

    st.markdown('</div>', unsafe_allow_html=True)  # Fecha login-card

    # Footer
    st.markdown("---")

    st.markdown('</div>', unsafe_allow_html=True)  # Fecha login-container


def render_firebase_auth(api_base_url: str):
    """
    Renderiza interface de autenticação Firebase.
    Suporta:
    - Login com Google
    - Login com email/senha
    """
    # Pega config do Firebase (precisa das credenciais web)
    firebase_config = get_firebase_web_config()

    if not firebase_config:
        st.error(
            "⚠️ **Firebase não configurado**\n\n"
            "Para usar autenticação em produção, você precisa:\n"
            "1. Adicionar as credenciais Firebase Web no .env\n"
            "2. Ou ativar DEBUG=True para desenvolvimento"
        )
        return

    # Firebase Auth UI
    st.markdown("### 🔐 Login")

    # Login com Google
    if st.button("🔐 Continuar com Google", use_container_width=True, type="secondary"):
        st.session_state.show_google_auth = True

    if st.session_state.get("show_google_auth", False):
        render_google_signin(firebase_config, api_base_url)

    st.markdown('<div class="divider">ou</div>', unsafe_allow_html=True)

    # Login com email/senha
    with st.form("firebase_login_form"):
        email = st.text_input("📧 Email", placeholder="seu@email.com")
        password = st.text_input("🔑 Senha", type="password", placeholder="••••••••")

        col1, col2 = st.columns([2, 1])
        with col1:
            remember = st.checkbox("Lembrar de mim")
        with col2:
            st.markdown(
                "<div style='text-align: right;'><small>Esqueceu?</small></div>",
                unsafe_allow_html=True
            )

        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("❌ Preencha email e senha")
            else:
                # Chama Firebase Auth
                authenticate_with_firebase(email, password, api_base_url)


def get_firebase_web_config():
    """
    Retorna configurações do Firebase Web SDK.
    Precisa estar no .env como FIREBASE_WEB_CONFIG (JSON).
    """
    import json

    config_str = os.getenv("FIREBASE_WEB_CONFIG", "")

    if not config_str:
        return None

    try:
        return json.loads(config_str)
    except json.JSONDecodeError:
        return None


def authenticate_with_firebase(email: str, password: str, api_base_url: str):
    """
    Autentica com Firebase usando REST API e envia token para backend.
    """
    # Pega API key do Firebase Web Config
    import json
    web_config_str = os.getenv("FIREBASE_WEB_CONFIG", "")

    if not web_config_str:
        st.error("❌ FIREBASE_WEB_CONFIG não configurado no .env")
        return

    try:
        web_config = json.loads(web_config_str)
        api_key = web_config.get("apiKey")
    except json.JSONDecodeError:
        st.error("❌ FIREBASE_WEB_CONFIG inválido")
        return

    if not api_key:
        st.error("❌ apiKey não encontrado no FIREBASE_WEB_CONFIG")
        return

    # Autentica com Firebase Auth REST API
    firebase_auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

    try:
        response = requests.post(
            firebase_auth_url,
            json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            },
            timeout=10
        )

        if response.status_code != 200:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Erro desconhecido")

            # Traduz mensagens comuns
            error_translations = {
                "EMAIL_NOT_FOUND": "Email não encontrado",
                "INVALID_PASSWORD": "Senha incorreta",
                "USER_DISABLED": "Usuário desabilitado",
                "INVALID_LOGIN_CREDENTIALS": "Email ou senha incorretos",
            }

            translated_error = error_translations.get(error_message, error_message)
            st.error(f"❌ {translated_error}")
            return

        # Sucesso! Pega o ID token
        auth_data = response.json()
        id_token = auth_data.get("idToken")

        # Envia token para backend para validar e obter dados do usuário
        try:
            backend_response = requests.post(
                f"{api_base_url}/auth/login",
                json={"id_token": id_token},  # Corrigido: id_token em vez de token
                timeout=5
            )

            if backend_response.status_code == 200:
                user_data = backend_response.json()

                # Salva na sessão com persistência
                save_auth_single_file(id_token, user_data)

                st.success(f"✅ Bem-vindo, {user_data.get('nome', 'Usuário')}!")
                st.rerun()
            else:
                # Não exibe detalhes do erro que podem conter tokens
                st.error("❌ Erro ao validar credenciais. Verifique email e senha.")

        except requests.RequestException as e:
            st.error("❌ Erro ao conectar com servidor. Tente novamente.")

    except requests.RequestException as e:
        st.error(f"❌ Erro ao conectar com Firebase: {e}")


def render_google_signin(firebase_config: dict, api_base_url: str):
    """
    Renderiza componente de login com Google usando Firebase signInWithPopup.
    """
    # Cria HTML com Firebase SDK e Google Sign-In
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            #status {{
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                text-align: center;
            }}
            .loading {{
                background: #f0f9ff;
                color: #0369a1;
                border: 2px solid #bae6fd;
            }}
            .error {{
                background: #fef2f2;
                color: #991b1b;
                border: 2px solid #fecaca;
            }}
            .success {{
                background: #f0fdf4;
                color: #166534;
                border: 2px solid #bbf7d0;
            }}
        </style>
    </head>
    <body>
        <div id="status" class="loading">🔄 Abrindo janela do Google...</div>

        <script>
            const firebaseConfig = {json.dumps(firebase_config)};

            if (!firebase.apps.length) {{
                firebase.initializeApp(firebaseConfig);
            }}

            const auth = firebase.auth();
            const provider = new firebase.auth.GoogleAuthProvider();

            // Força a seleção de conta
            provider.setCustomParameters({{
                prompt: 'select_account'
            }});

            // Inicia o fluxo de login
            auth.signInWithPopup(provider)
                .then((result) => {{
                    document.getElementById('status').className = 'loading';
                    document.getElementById('status').innerHTML = '✅ Login realizado! Validando...';

                    return result.user.getIdToken();
                }})
                .then((idToken) => {{
                    // Envia para backend
                    return fetch('{api_base_url}/auth/login', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ id_token: idToken }})
                    }})
                    .then(response => {{
                        if (!response.ok) {{
                            throw new Error('Falha na autenticação');
                        }}
                        return response.json();
                    }})
                    .then(data => {{
                        // Sucesso! Envia dados para Streamlit
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            data: {{
                                success: true,
                                user: data,
                                token: idToken
                            }}
                        }}, '*');

                        document.getElementById('status').className = 'success';
                        document.getElementById('status').innerHTML = '✅ Login realizado! Redirecionando...';
                    }});
                }})
                .catch((error) => {{
                    console.error('Erro:', error);

                    let errorMsg = 'Erro ao fazer login com Google';
                    if (error.code === 'auth/popup-closed-by-user') {{
                        errorMsg = 'Login cancelado';
                    }} else if (error.code === 'auth/popup-blocked') {{
                        errorMsg = 'Popup bloqueado. Permita popups neste site.';
                    }}

                    document.getElementById('status').className = 'error';
                    document.getElementById('status').innerHTML = '❌ ' + errorMsg;

                    // Envia erro para Streamlit
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        data: {{
                            success: false,
                            error: errorMsg
                        }}
                    }}, '*');
                }});
        </script>
    </body>
    </html>
    """

    # Renderiza componente
    result = components.html(html_code, height=150, scrolling=False)

    # Processa resultado do login (result pode ser None ou um dict)
    if result and isinstance(result, dict):
        if result.get("success"):
            user_data = result.get("user", {})
            token = result.get("token", "")

            # Salva na sessão com persistência
            save_auth_single_file(token, user_data)
            st.session_state.show_google_auth = False

            st.success(f"✅ Bem-vindo, {user_data.get('nome', 'Usuário')}!")
            st.rerun()
        elif result.get("error"):
            st.error(f"❌ {result.get('error', 'Erro desconhecido')}")
            st.session_state.show_google_auth = False
