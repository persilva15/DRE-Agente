# -*- coding: utf-8 -*-
"""
Módulo de autenticação para o DRE Agente.
Usa st.secrets para credenciais (compatível com Streamlit Cloud).
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
import os


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

def get_config() -> dict:
    """
    Retorna config de autenticação.
    No Streamlit Cloud: usa st.secrets
    Local: usa config.yaml
    """
    is_cloud = os.environ.get('STREAMLIT_SERVER_RUN_ON_CLOUD', 'false').lower() == 'true'

    if is_cloud:
        # Streamlit Cloud: usar secrets
        try:
            cred = st.secrets["auth"]
            return {
                "credentials": {
                    "usernames": {
                        cred["username"]: {
                            "email": cred["email"],
                            "name": cred["name"],
                            "password": cred["password_hash"],
                        }
                    }
                },
                "cookie": {
                    "expiry_days": 30,
                    "key": "dre_febracis_key",
                    "name": "dre_febracis_cookie",
                },
            }
        except Exception:
            # Fallback: admin hardcoded
            return _get_default_config()
    else:
        # Local: tentar config.yaml, senão usar default
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return _get_default_config()


def _get_default_config() -> dict:
    """Config padrão com admin/admin123."""
    hasher = stauth.Hasher()
    return {
        "credentials": {
            "usernames": {
                "admin": {
                    "email": "admin@febracis.com.br",
                    "name": "Administrador",
                    "password": hasher.hash("admin123"),
                }
            }
        },
        "cookie": {
            "expiry_days": 30,
            "key": "dre_febracis_key",
            "name": "dre_febracis_cookie",
        },
    }


# =============================================================================
# AUTENTICAÇÃO
# =============================================================================

def get_authenticator():
    """Retorna instância do authenticator."""
    config = get_config()
    return stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )


def login():
    """Realiza login. Retorna (name, auth_status, username, authenticator)."""
    authenticator = get_authenticator()
    name, authentication_status, username = authenticator.login(location="sidebar")
    return name, authentication_status, username, authenticator


def logout(authenticator):
    """Realiza logout."""
    authenticator.logout(location="sidebar")


def eh_admin(username: str) -> bool:
    """Verifica se é admin."""
    return username == "admin"


# =============================================================================
# GERENCIAMENTO DE USUÁRIOS (apenas local)
# =============================================================================

def criar_usuario(username: str, email: str, name: str, password: str) -> bool:
    """Cria novo usuário (apenas local)."""
    is_cloud = os.environ.get('STREAMLIT_SERVER_RUN_ON_CLOUD', 'false').lower() == 'true'
    if is_cloud:
        return False  # Não permite criar no cloud

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    config = get_config()

    if username in config["credentials"]["usernames"]:
        return False

    hasher = stauth.Hasher()
    config["credentials"]["usernames"][username] = {
        "email": email,
        "name": name,
        "password": hasher.hash(password),
    }

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)
    return True


def remover_usuario(username: str) -> bool:
    """Remove usuário (apenas local)."""
    is_cloud = os.environ.get('STREAMLIT_SERVER_RUN_ON_CLOUD', 'false').lower() == 'true'
    if is_cloud or username == "admin":
        return False

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    config = get_config()

    if username not in config["credentials"]["usernames"]:
        return False

    del config["credentials"]["usernames"][username]
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)
    return True


def listar_usuarios() -> list:
    """Lista usuários."""
    config = get_config()
    return [
        {"username": u, "email": d.get("email", ""), "name": d.get("name", "")}
        for u, d in config["credentials"]["usernames"].items()
    ]


def usuario_existe(username: str) -> bool:
    """Verifica se usuário existe."""
    config = get_config()
    return username in config["credentials"]["usernames"]


# =============================================================================
# PÁGINA DE ADMIN
# =============================================================================

def renderizar_admin():
    """Renderiza administração de usuários."""
    st.markdown("##  Gerenciamento de Usuários")

    tab1, tab2 = st.tabs(["📋 Listar Usuários", "➕ Criar Usuário"])

    with tab1:
        st.markdown("### Usuários Cadastrados")
        for u in listar_usuarios():
            col1, col2 = st.columns([2, 4])
            with col1:
                st.write(f"**{u['username']}**")
            with col2:
                st.write(f"{u['name']} ({u['email']})")

    with tab2:
        is_cloud = os.environ.get('STREAMLIT_SERVER_RUN_ON_CLOUD', 'false').lower() == 'true'
        if is_cloud:
            st.info("Cadastro de usuários disponível apenas na versão local.")
        else:
            with st.form("criar_usuario"):
                username = st.text_input("Nome de usuário")
                name = st.text_input("Nome completo")
                email = st.text_input("Email")
                password = st.text_input("Senha", type="password")
                password_confirm = st.text_input("Confirmar senha", type="password")

                if st.form_submit_button("Criar"):
                    if not all([username, name, email, password]):
                        st.error("Preencha todos os campos")
                    elif password != password_confirm:
                        st.error("Senhas não conferem")
                    elif usuario_existe(username):
                        st.error("Usuário já existe")
                    elif criar_usuario(username, email, name, password):
                        st.success(f"Usuário {username} criado!")
                        st.rerun()
