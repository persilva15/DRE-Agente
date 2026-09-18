# -*- coding: utf-8 -*-
"""
Página de Administração - Gerenciamento de Usuários
"""
import streamlit as st
from auth import renderizar_admin, eh_admin

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Admin - DRE Febracis",
    page_icon=" ",
    layout="wide",
)

# =============================================================================
# VERIFICAR AUTENTICAÇÃO
# =============================================================================

# Verificar se está logado
if 'authentication_status' not in st.session_state:
    st.warning("Faça login primeiro")
    st.stop()

if st.session_state['authentication_status'] != True:
    st.warning("Faça login primeiro")
    st.stop()

# Verificar se é admin
username = st.session_state.get('username', '')
if not eh_admin(username):
    st.error("Acesso negado. Apenas administradores podem acessar esta página.")
    st.stop()

# =============================================================================
# RENDERIZAR ADMIN
# =============================================================================

renderizar_admin()
