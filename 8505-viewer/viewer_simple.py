#!/usr/bin/env python3
"""
🛠️ Streamlit Debug Interface - Versão Simplificada
Versão otimizada sem sobrecarga
"""

import streamlit as st
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configuração da página
st.set_page_config(
    page_title="🛠️ Viewer Debug - Simplificado",
    page_icon="🛠️",
    layout="wide"
)

# Estado da sessão minimalista
if "logs" not in st.session_state:
    st.session_state.logs = []

def main():
    """Interface principal simplificada"""
    
    # Cabeçalho
    st.title("🤖 Claude Chat API - Viewer Simplificado")
    st.success("✅ Sistema Funcionando - Versão Otimizada")
    
    # Layout em duas colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("📋 Status do Sistema")
        
        # Status básico
        st.info("🟢 API Status: Online")
        st.metric("Logs", len(st.session_state.logs))
        
        # Botão de teste simples
        if st.button("🧪 Teste Rápido"):
            st.success("✅ Teste executado com sucesso!")
            st.session_state.logs.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "msg": "Teste executado"
            })
    
    with col2:
        st.header("📝 Logs Recentes")
        
        # Mostrar últimos 5 logs
        if st.session_state.logs:
            for log in st.session_state.logs[-5:]:
                st.text(f"[{log['time']}] {log['msg']}")
        else:
            st.info("Nenhum log ainda")
        
        # Botão para limpar logs
        if st.button("🗑️ Limpar Logs"):
            st.session_state.logs = []
            st.rerun()
    
    # Área de testes
    st.divider()
    st.header("🎯 Área de Testes")
    
    # Input simples para teste
    test_input = st.text_area("Digite algo para testar:", height=100)
    
    if st.button("📤 Processar"):
        if test_input:
            st.success(f"✅ Processado: {len(test_input)} caracteres")
            st.session_state.logs.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "msg": f"Processado texto com {len(test_input)} chars"
            })
        else:
            st.warning("⚠️ Digite algo primeiro")
    
    # Informações básicas do sistema
    st.divider()
    with st.expander("ℹ️ Informações do Sistema"):
        st.write(f"- **Hora atual:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"- **Diretório:** {Path.cwd()}")
        st.write(f"- **Python Path:** {Path.home()}")

if __name__ == "__main__":
    main()