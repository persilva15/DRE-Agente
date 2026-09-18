# -*- coding: utf-8 -*-
"""
Autenticação simples para DRE Agente.
Sem dependência de streamlit-authenticator.
"""
import streamlit as st
import hashlib
import secrets


# =============================================================================
# CREDENCIAIS (hardcoded para cloud, sem arquivos)
# =============================================================================

USUARIOS = {
    "admin": {
        "nome": "Administrador",
        "email": "admin@febracis.com.br",
        "senha_hash": hashlib.sha256("admin123".encode()).hexdigest(),
    }
}


# =============================================================================
# FUNÇÕES
# =============================================================================

def _hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def login():
    """
    Renderiza formulário de login na sidebar.
    Retorna (name, authentication_status, username, authenticator_dummy).
    """
    # Se já está logado, retorna dados do session
    if st.session_state.get("logado"):
        username = st.session_state.get("username", "")
        dados = USUARIOS.get(username, {})
        return dados.get("nome", ""), True, username, None

    # Formulário de login
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔐 Login")
        username = st.text_input("Usuário", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Entrar", use_container_width=True):
            if username in USUARIOS:
                if _hash_senha(senha) == USUARIOS[username]["senha_hash"]:
                    st.session_state["logado"] = True
                    st.session_state["username"] = username
                    st.session_state["nome"] = USUARIOS[username]["nome"]
                    st.rerun()
                else:
                    st.error("Senha incorreta")
            else:
                st.error("Usuário não encontrado")

        st.markdown("---")

    return None, None, None, None


def logout():
    """Remove dados de login do session."""
    st.session_state.pop("logado", None)
    st.session_state.pop("username", None)
    st.session_state.pop("nome", None)
    st.rerun()


def esta_logado() -> bool:
    """Verifica se usuário está logado."""
    return st.session_state.get("logado", False)


def get_username() -> str:
    """Retorna username logado."""
    return st.session_state.get("username", "")


def get_nome() -> str:
    """Retorna nome do usuário logado."""
    return st.session_state.get("nome", "")


def eh_admin() -> bool:
    """Verifica se é admin."""
    return get_username() == "admin"


# =============================================================================
# PÁGINA DE ADMIN
# =============================================================================

def renderizar_admin():
    """Renderiza administração (simplificado para cloud)."""
    st.markdown("##  Gerenciamento de Usuários")

    st.info("""
    **Usuário administrador padrão:**
    - Usuário: `admin`
    - Senha: `admin123`

    Para alterar a senha, edite o arquivo `auth/__init__.py`.
    """)

    st.markdown("### Usuários Cadastrados")
    for u, dados in USUARIOS.items():
        st.write(f"**{u}** — {dados['nome']} ({dados['email']})")
