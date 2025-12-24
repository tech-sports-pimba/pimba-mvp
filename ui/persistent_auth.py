"""Gerenciamento de autenticação persistente usando localStorage (seguro)."""
import streamlit as st
import streamlit.components.v1 as components
import json


def save_auth_persistent(auth_token: str, user_info: dict):
    """
    Salva autenticação no localStorage do navegador (SEGURO).
    Não usa URL/query params para evitar exposição do token.
    """
    from utils.session_manager import save_session

    # Salva na sessão normal do Streamlit
    save_session(auth_token, user_info)

    # Prepara dados para localStorage
    auth_data = {
        "token": auth_token,
        "user": user_info
    }
    auth_json = json.dumps(auth_data)

    # JavaScript para salvar no localStorage
    html_code = f"""
    <script>
        // Salva no localStorage
        try {{
            localStorage.setItem('pimba_auth', {json.dumps(auth_json)});
            console.log('✅ Auth salva no localStorage');
        }} catch(e) {{
            console.error('❌ Erro ao salvar auth:', e);
        }}
    </script>
    """

    # Renderiza componente (invisível)
    components.html(html_code, height=0)


def clear_auth_persistent():
    """Remove autenticação persistente do localStorage."""
    from utils.session_manager import clear_session

    # Limpa sessão Streamlit
    clear_session()

    # JavaScript para limpar localStorage
    html_code = """
    <script>
        try {
            localStorage.removeItem('pimba_auth');
            console.log('✅ Auth removida do localStorage');
        } catch(e) {
            console.error('❌ Erro ao limpar auth:', e);
        }
    </script>
    """

    # Renderiza componente (invisível)
    components.html(html_code, height=0)


def restore_session_from_storage():
    """
    Tenta restaurar sessão do localStorage.
    Retorna True se restaurou com sucesso.

    IMPORTANTE: Deve ser chamado ANTES de qualquer outro componente Streamlit.
    """
    # Se já está autenticado, não faz nada
    if st.session_state.get("authenticated", False):
        return True

    # Inicializa flag de verificação
    if "auth_check_done" not in st.session_state:
        st.session_state.auth_check_done = False

    # Se já verificou, retorna
    if st.session_state.auth_check_done:
        return st.session_state.get("authenticated", False)

    # JavaScript para ler localStorage e passar para Streamlit via query params temporários
    html_code = """
    <script>
        try {
            const authData = localStorage.getItem('pimba_auth');

            if (authData) {
                console.log('✅ Auth encontrada no localStorage');

                // Parse dos dados
                const auth = JSON.parse(authData);

                // Adiciona nos query params TEMPORARIAMENTE (só para esta execução)
                const url = new URL(window.parent.location);
                url.searchParams.set('_restore_token', auth.token);
                url.searchParams.set('_restore_user', JSON.stringify(auth.user));

                // Atualiza URL sem recarregar (apenas para Streamlit ler)
                window.parent.history.replaceState({}, '', url);

                // Força Streamlit a processar
                window.parent.postMessage({type: 'streamlit:setQueryParams'}, '*');

                // Remove os params depois de 1 segundo (limpeza)
                setTimeout(() => {
                    const cleanUrl = new URL(window.parent.location);
                    cleanUrl.searchParams.delete('_restore_token');
                    cleanUrl.searchParams.delete('_restore_user');
                    window.parent.history.replaceState({}, '', cleanUrl);
                }, 1000);
            } else {
                console.log('ℹ️ Nenhuma auth no localStorage');
            }
        } catch(e) {
            console.error('❌ Erro ao ler localStorage:', e);
        }
    </script>
    """

    # Renderiza componente
    components.html(html_code, height=0)

    # Tenta restaurar dos query params temporários
    if "_restore_token" in st.query_params:
        try:
            auth_token = st.query_params["_restore_token"]
            user_info = json.loads(st.query_params["_restore_user"])

            # Restaura sessão
            from utils.session_manager import save_session
            save_session(auth_token, user_info)

            st.session_state.auth_check_done = True

            # Limpa query params imediatamente
            del st.query_params["_restore_token"]
            del st.query_params["_restore_user"]

            return True
        except Exception as e:
            # Erro ao restaurar, limpa tudo
            if "_restore_token" in st.query_params:
                del st.query_params["_restore_token"]
            if "_restore_user" in st.query_params:
                del st.query_params["_restore_user"]

    # Marca como verificado
    st.session_state.auth_check_done = True
    return False
