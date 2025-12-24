"""
Cliente HTTP para fazer requests autenticados para a API.

Automaticamente inclui o session_id ou token nos headers.
"""
import streamlit as st
import requests
from typing import Optional, Dict, Any


def get_auth_headers() -> Dict[str, str]:
    """
    Retorna headers de autenticação baseado na sessão atual.

    Returns:
        Dict com headers (X-Session-ID ou Authorization)
    """
    headers = {"Content-Type": "application/json"}

    # PRIORIDADE 1: Session ID (backend PostgreSQL)
    session_id = st.session_state.get("backend_session_id")

    if session_id:
        headers["X-Session-ID"] = session_id
        return headers

    # PRIORIDADE 2: Firebase Token (modo antigo)
    auth_token = st.session_state.get("auth_token", "")

    if auth_token and not auth_token.startswith("session_"):
        headers["Authorization"] = f"Bearer {auth_token}"

    return headers


def api_get(url: str, **kwargs) -> requests.Response:
    """
    GET autenticado.

    Args:
        url: URL da API
        **kwargs: Argumentos adicionais para requests.get()

    Returns:
        Response
    """
    headers = get_auth_headers()

    # Merge com headers personalizados se fornecidos
    if "headers" in kwargs:
        headers.update(kwargs["headers"])

    kwargs["headers"] = headers

    return requests.get(url, **kwargs)


def api_post(url: str, **kwargs) -> requests.Response:
    """
    POST autenticado.

    Args:
        url: URL da API
        **kwargs: Argumentos adicionais para requests.post()

    Returns:
        Response
    """
    headers = get_auth_headers()

    if "headers" in kwargs:
        headers.update(kwargs["headers"])

    kwargs["headers"] = headers

    return requests.post(url, **kwargs)


def api_put(url: str, **kwargs) -> requests.Response:
    """
    PUT autenticado.

    Args:
        url: URL da API
        **kwargs: Argumentos adicionais para requests.put()

    Returns:
        Response
    """
    headers = get_auth_headers()

    if "headers" in kwargs:
        headers.update(kwargs["headers"])

    kwargs["headers"] = headers

    return requests.put(url, **kwargs)


def api_delete(url: str, **kwargs) -> requests.Response:
    """
    DELETE autenticado.

    Args:
        url: URL da API
        **kwargs: Argumentos adicionais para requests.delete()

    Returns:
        Response
    """
    headers = get_auth_headers()

    if "headers" in kwargs:
        headers.update(kwargs["headers"])

    kwargs["headers"] = headers

    return requests.delete(url, **kwargs)
