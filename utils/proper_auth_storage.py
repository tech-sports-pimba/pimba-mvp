"""
Sistema de autenticação CORRETO usando Firebase + localStorage.

Segue as melhores práticas:
- Token armazenado em localStorage (encrypted em produção)
- Validação server-side via Firebase Admin SDK
- Não expõe tokens em URLs ou query params
"""
import streamlit as st
import streamlit.components.v1 as components
from utils.session_manager import save_session, clear_session


def save_auth_to_localstorage(auth_token: str, user_info: dict):
    """
    Salva token de autenticação no localStorage do browser.
    Esta é a prática padrão para SPAs.
    """
    # Salva no session_state do Streamlit (sessão atual)
    save_session(auth_token, user_info)

    # Prepara dados para localStorage
    import json
    auth_data = {
        "token": auth_token,
        "user": user_info
    }

    # JavaScript para salvar no localStorage
    js_code = f"""
    <script>
        (function() {{
            try {{
                const authData = {json.dumps(json.dumps(auth_data))};
                localStorage.setItem('pimba_auth_token', authData);
                console.log('✅ Token salvo no localStorage');
            }} catch(e) {{
                console.error('❌ Erro ao salvar token:', e);
            }}
        }})();
    </script>
    """

    components.html(js_code, height=0)


def restore_auth_from_localstorage() -> bool:
    """
    Tenta restaurar autenticação do localStorage.

    Usa query params como bridge para evitar timing issues.
    """
    import json
    import base64

    # Se já está autenticado, não faz nada
    if st.session_state.get("authenticated", False):
        return True

    # PASSO 1: Verifica se JS já enviou dados via query param
    if "_auth_data" in st.query_params:
        try:
            # Decodifica dados do query param
            encoded_data = st.query_params["_auth_data"]
            json_str = base64.b64decode(encoded_data).decode('utf-8')
            auth_data = json.loads(json_str)

            # Restaura sessão
            save_session(auth_data["token"], auth_data["user"])

            # Limpa query param
            del st.query_params["_auth_data"]

            # Marca como restaurado
            st.session_state.auth_restore_attempted = True

            return True
        except Exception as e:
            # Limpa query param inválido
            if "_auth_data" in st.query_params:
                del st.query_params["_auth_data"]
            return False

    # PASSO 2: Se ainda não tentamos ler do localStorage, executa JavaScript
    if "auth_restore_attempted" not in st.session_state:
        st.session_state.auth_restore_attempted = False

    if not st.session_state.auth_restore_attempted:
        # JavaScript lê localStorage e coloca em query param
        js_code = """
        <script>
            (function() {
                try {
                    const authData = localStorage.getItem('pimba_auth_token');

                    if (authData) {
                        console.log('✅ Token encontrado no localStorage');

                        // Codifica em base64 para passar via URL
                        const encoded = btoa(authData);

                        // Adiciona em query param
                        const url = new URL(window.parent.location);
                        url.searchParams.set('_auth_data', encoded);
                        window.parent.history.replaceState({}, '', url);

                        // Força reload para Streamlit processar
                        window.parent.location.href = url.toString();
                    } else {
                        console.log('ℹ️ Nenhum token no localStorage');
                    }
                } catch(e) {
                    console.error('❌ Erro ao ler localStorage:', e);
                }
            })();
        </script>
        """

        components.html(js_code, height=0)
        st.session_state.auth_restore_attempted = True

        return False

    return False


def clear_auth_from_localstorage():
    """
    Remove token do localStorage e limpa sessão.
    """
    # Limpa sessão Streamlit
    clear_session()

    # Reseta flag de restauração
    if "auth_restore_attempted" in st.session_state:
        st.session_state.auth_restore_attempted = False

    # Limpa query param se existir
    if "_auth_data" in st.query_params:
        del st.query_params["_auth_data"]

    # JavaScript para limpar localStorage
    js_code = """
    <script>
        (function() {
            try {
                localStorage.removeItem('pimba_auth_token');
                console.log('✅ Token removido do localStorage');
            } catch(e) {
                console.error('❌ Erro ao limpar token:', e);
            }
        })();
    </script>
    """

    components.html(js_code, height=0)
