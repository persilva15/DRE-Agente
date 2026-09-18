# -*- coding: utf-8 -*-
"""
Módulo de autenticação para o DRE Agente.
Gerencia login, logout e cadastro de usuários.
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
import os
from datetime import datetime
from typing import Optional

# =============================================================================
# CAMINHO DO ARQUIVO DE CREDENCIAIS
# =============================================================================

AUTH_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(AUTH_DIR, "config.yaml")


# =============================================================================
# FUNÇÕES DE AUTENTICAÇÃO
# =============================================================================

def load_config() -> dict:
    """Carrega as credenciais do arquivo config.yaml."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        # Criar config padrão se não existir
        default_config = {
            "credentials": {
                "usernames": {
                    "admin": {
                        "email": "admin@febracis.com.br",
                        "name": "Administrador",
                        "password": "$2b$12$...",  # Será substituído pelo hash
                    }
                }
            },
            "cookie": {
                "expiry_days": 30,
                "key": "dre_febracis_key",
                "name": "dre_febracis_cookie",
            },
            "preauthorized": {
                "emails": ["admin@febracis.com.br"]
            }
        }
        save_config(default_config)
        return default_config


def save_config(config: dict):
    """Salva as credenciais no arquivo config.yaml."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        yaml.dump(config, file, default_flow_style=False)


def get_authenticator():
    """Retorna uma instância do authenticator."""
    config = load_config()
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    return authenticator


def login():
    """
    Realiza o login do usuário.
    
    Returns:
        tuple: (name, authentication_status, username)
    """
    authenticator = get_authenticator()
    
    name, authentication_status, username = authenticator.login(
        'Login', 
        'sidebar',
        location='main'
    )
    
    return name, authentication_status, username, authenticator


def logout(authenticator):
    """Realiza o logout do usuário."""
    authenticator.logout('Sair', 'sidebar')


# =============================================================================
# FUNÇÕES DE GERENCIAMENTO DE USUÁRIOS
# =============================================================================

def criar_usuario(username: str, email: str, name: str, password: str) -> bool:
    """
    Cria um novo usuário.
    
    Args:
        username: Nome de usuário (login)
        email: Email do usuário
        name: Nome completo
        password: Senha em texto puro
    
    Returns:
        bool: True se criado com sucesso
    """
    config = load_config()
    
    # Verificar se usuário já existe
    if username in config['credentials']['usernames']:
        return False
    
    # Gerar hash da senha
    hasher = stauth.Hasher([password])
    hashed_password = hasher.generate([password])[0]
    
    # Adicionar usuário
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hashed_password,
    }
    
    save_config(config)
    return True


def remover_usuario(username: str) -> bool:
    """
    Remove um usuário.
    
    Args:
        username: Nome de usuário a ser removido
    
    Returns:
        bool: True se removido com sucesso
    """
    config = load_config()
    
    if username not in config['credentials']['usernames']:
        return False
    
    # Não permitir remover o admin
    if username == 'admin':
        return False
    
    del config['credentials']['usernames'][username]
    save_config(config)
    return True


def listar_usuarios() -> list:
    """
    Lista todos os usuários.
    
    Returns:
        list: Lista de dicts com informações dos usuários
    """
    config = load_config()
    usuarios = []
    
    for username, dados in config['credentials']['usernames'].items():
        usuarios.append({
            'username': username,
            'email': dados.get('email', ''),
            'name': dados.get('name', ''),
        })
    
    return usuarios


def usuario_existe(username: str) -> bool:
    """Verifica se um usuário existe."""
    config = load_config()
    return username in config['credentials']['usernames']


def eh_admin(username: str) -> bool:
    """Verifica se o usuário é admin."""
    return username == 'admin'


# =============================================================================
# PÁGINA DE ADMIN
# =============================================================================

def renderizar_admin():
    """Renderiza a página de administração de usuários."""
    st.markdown("##  Gerenciamento de Usuários")
    
    tab1, tab2 = st.tabs(["📋 Listar Usuários", "➕ Criar Usuário"])
    
    with tab1:
        st.markdown("### Usuários Cadastrados")
        usuarios = listar_usuarios()
        
        if not usuarios:
            st.info("Nenhum usuário cadastrado")
        else:
            for u in usuarios:
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.write(f"**{u['username']}**")
                with col2:
                    st.write(f"{u['name']} ({u['email']})")
                with col3:
                    if u['username'] != 'admin':
                        if st.button("Remover", key=f"remover_{u['username']}"):
                            if remover_usuario(u['username']):
                                st.success(f"Usuário {u['username']} removido")
                                st.rerun()
                            else:
                                st.error("Erro ao remover usuário")
    
    with tab2:
        st.markdown("### Criar Novo Usuário")
        
        with st.form("criar_usuario"):
            username = st.text_input("Nome de usuário (login)")
            name = st.text_input("Nome completo")
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            password_confirm = st.text_input("Confirmar senha", type="password")
            
            submitted = st.form_submit_button("Criar Usuário")
            
            if submitted:
                if not username or not name or not email or not password:
                    st.error("Preencha todos os campos")
                elif password != password_confirm:
                    st.error("As senhas não conferem")
                elif usuario_existe(username):
                    st.error("Usuário já existe")
                else:
                    if criar_usuario(username, email, name, password):
                        st.success(f"Usuário {username} criado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao criar usuário")


# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

def inicializar_admin_padrao():
    """Cria o usuário admin padrão se não existir."""
    if not usuario_existe('admin'):
        # Senha padrão: admin123
        criar_usuario('admin', 'admin@febracis.com.br', 'Administrador', 'admin123')
        print("[AUTH] Usuário admin padrão criado (senha: admin123)")
