#!/usr/bin/env python3
"""
🎯 Streamlit Chat App - Versão Simplificada e Robusta
Interface web para Claude Code SDK sem conflitos de asyncio
"""

import streamlit as st
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional

# Configuração da página
st.set_page_config(
    page_title="Claude Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.stChatMessage {
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
}

.user-message {
    background-color: #e8f4fd;
    border-left: 4px solid #1f77b4;
}

.assistant-message {
    background-color: #f0f8f0;
    border-left: 4px solid #2ca02c;
}

.metrics-box {
    background-color: #f8f9fa;
    padding: 0.5rem;
    border-radius: 5px;
    font-size: 0.8rem;
    color: #666;
}

.title-container {
    text-align: center;
    padding: 1rem 0;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 2rem;
}

.debug-container {
    background-color: #1e1e1e;
    color: #ffffff;
    padding: 1rem;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    max-height: 300px;
    overflow-y: auto;
    margin: 1rem 0;
}

.error-message {
    background-color: #ffebee;
    color: #c62828;
    padding: 0.5rem;
    border-left: 4px solid #f44336;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.success-message {
    background-color: #e8f5e8;
    color: #2e7d2e;
    padding: 0.5rem;
    border-left: 4px solid #4caf50;
    border-radius: 5px;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Inicialização do estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = True  # Ativado por padrão
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = {"input": 0, "output": 0}
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "processing" not in st.session_state:
    st.session_state.processing = False

def add_debug_log(level: str, message: str, details: Optional[Dict] = None):
    """Adiciona log de debug ao estado da sessão"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "details": details or {}
    }
    
    st.session_state.debug_logs.append(log_entry)
    
    # Mantém apenas os últimos 100 logs
    if len(st.session_state.debug_logs) > 100:
        st.session_state.debug_logs = st.session_state.debug_logs[-100:]

def format_timestamp() -> str:
    """Formata timestamp para exibição"""
    return datetime.now().strftime("%H:%M:%S")

def format_debug_message(log_entry: Dict) -> str:
    """Formata mensagem de debug para exibição"""
    timestamp = log_entry["timestamp"].split("T")[1][:8]
    level = log_entry["level"].upper()
    message = log_entry["message"]
    
    level_colors = {
        "ERROR": "🔴",
        "WARNING": "🟡", 
        "INFO": "🔵",
        "DEBUG": "⚫"
    }
    
    icon = level_colors.get(level, "⚫")
    return f"{icon} [{timestamp}] {level}: {message}"

def send_claude_query(prompt: str) -> Dict:
    """Envia query para Claude usando wrapper Python direto"""
    add_debug_log("info", "Iniciando query via wrapper Python", {
        "prompt_length": len(prompt),
        "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt
    })
    
    start_time = time.time()
    
    try:
        # Importa o wrapper subprocess simples (cada query é independente)
        wrapper_path = os.path.join(os.path.dirname(__file__), "claude_subprocess_simple.py")
        add_debug_log("debug", "Usando wrapper subprocess independente", {"wrapper_path": wrapper_path})
        
        # Importa a função do wrapper subprocess (mais estável)
        import sys
        wrapper_dir = os.path.dirname(wrapper_path)
        if wrapper_dir not in sys.path:
            sys.path.insert(0, wrapper_dir)
        
        from claude_subprocess_simple import query_claude
        
        # Executa a query
        result = query_claude(prompt)
        execution_time = time.time() - start_time
        
        if result["success"]:
            # Extrai informações de uso
            input_tokens = result.get("input_tokens", 0)
            output_tokens = result.get("output_tokens", 0) 
            cost = result.get("cost", 0.0)
            
            # Compatibilidade com formato antigo
            if result.get("usage"):
                usage = result["usage"]
                if hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens or 0
                    output_tokens = usage.output_tokens or 0
                elif isinstance(usage, dict):
                    input_tokens = usage.get('input_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0)
            
            add_debug_log("info", "Query executada com sucesso", {
                "execution_time": f"{execution_time:.3f}s",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "content_length": len(result.get("content", ""))
            })
            
            return {
                "success": True,
                "content": result.get("content", "Resposta vazia"),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "execution_time": execution_time
            }
        else:
            add_debug_log("error", "Erro na execução da query", {
                "error": result["error"],
                "execution_time": f"{execution_time:.3f}s"
            })
            
            return {
                "success": False,
                "error": result["error"],
                "execution_time": execution_time
            }
                
    except Exception as e:
        execution_time = time.time() - start_time
        add_debug_log("error", "Erro inesperado no wrapper", {
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        return {
            "success": False,
            "error": f"Erro inesperado: {str(e)}",
            "execution_time": execution_time
        }

def send_message(prompt: str):
    """Processa mensagem do usuário"""
    add_debug_log("info", "Iniciando processamento de mensagem", {"prompt": prompt[:50]})
    
    # Adiciona mensagem do usuário
    user_msg = {
        "role": "user",
        "content": prompt,
        "timestamp": format_timestamp()
    }
    st.session_state.messages.append(user_msg)
    add_debug_log("debug", "Mensagem do usuário adicionada", {"message_id": len(st.session_state.messages)})
    
    # Envia para Claude
    add_debug_log("info", "Enviando para Claude", {"prompt_length": len(prompt)})
    result = send_claude_query(prompt)
    add_debug_log("debug", "Resultado do Claude recebido", {"success": result["success"]})
    
    if result["success"]:
        # Adiciona resposta do assistente
        assistant_msg = {
            "role": "assistant",
            "content": result["content"],
            "timestamp": format_timestamp(),
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "cost": result["cost"],
            "execution_time": result["execution_time"]
        }
        st.session_state.messages.append(assistant_msg)
        
        # Atualiza totais
        st.session_state.total_tokens["input"] += result["input_tokens"]
        st.session_state.total_tokens["output"] += result["output_tokens"]
        st.session_state.total_cost += result["cost"]
        
        add_debug_log("info", "Resposta processada com sucesso", {
            "response_length": len(result["content"]),
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "cost": result["cost"],
            "total_messages": len(st.session_state.messages)
        })
    else:
        # Adiciona mensagem de erro
        error_msg = {
            "role": "error",
            "content": f"❌ Erro: {result['error']}",
            "timestamp": format_timestamp(),
            "execution_time": result["execution_time"]
        }
        st.session_state.messages.append(error_msg)
        
        add_debug_log("error", "Falha no processamento da mensagem", {
            "error": result["error"],
            "execution_time": result["execution_time"],
            "total_messages": len(st.session_state.messages)
        })

def clear_conversation():
    """Limpa a conversa"""
    add_debug_log("info", "Limpando conversa", {
        "prev_messages": len(st.session_state.messages),
        "prev_tokens_input": st.session_state.total_tokens["input"],
        "prev_tokens_output": st.session_state.total_tokens["output"],
        "prev_cost": st.session_state.total_cost
    })
    
    st.session_state.messages = []
    st.session_state.total_tokens = {"input": 0, "output": 0}
    st.session_state.total_cost = 0.0
    
    add_debug_log("info", "Conversa limpa com sucesso")

def render_debug_panel():
    """Renderiza painel de debug"""
    if not st.session_state.debug_mode:
        return
    
    with st.expander("🔍 Debug Panel - Sistema Simplificado", expanded=False):
        debug_tab1, debug_tab2 = st.tabs(["📝 Logs", "📊 Métricas"])
        
        # Tab 1: Logs
        with debug_tab1:
            st.subheader("📝 Logs de Debug")
            
            col1, col2 = st.columns(2)
            with col1:
                max_logs = st.number_input("Máx logs:", value=20, min_value=5, max_value=100)
            with col2:
                if st.button("🗑️ Limpar Logs"):
                    st.session_state.debug_logs = []
                    st.rerun()
            
            # Exibe logs
            if st.session_state.debug_logs:
                filtered_logs = st.session_state.debug_logs[-max_logs:]
                
                for log in reversed(filtered_logs):
                    formatted_msg = format_debug_message(log)
                    
                    if log["level"] == "error":
                        st.markdown(f'<div class="error-message">{formatted_msg}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="success-message">{formatted_msg}</div>', unsafe_allow_html=True)
                    
                    # Detalhes expandidos
                    if log["details"] and st.checkbox(f"Detalhes - {log['timestamp'][-8:]}", key=f"details_{log['timestamp']}"):
                        st.json(log["details"])
            else:
                st.info("📋 Nenhum log disponível")
        
        # Tab 2: Métricas
        with debug_tab2:
            st.subheader("📊 Métricas da Sessão")
            
            # Métricas gerais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Mensagens", len(st.session_state.messages))
            with col2:
                st.metric("Tokens Entrada", st.session_state.total_tokens["input"])
            with col3:
                st.metric("Tokens Saída", st.session_state.total_tokens["output"])
            with col4:
                st.metric("Custo Total", f"${st.session_state.total_cost:.6f}")
            
            # Tabela de mensagens
            if st.session_state.messages:
                message_data = []
                for i, msg in enumerate(st.session_state.messages):
                    if msg["role"] == "assistant":
                        message_data.append({
                            "Mensagem": i//2 + 1,
                            "Tokens In": msg.get("input_tokens", 0),
                            "Tokens Out": msg.get("output_tokens", 0),
                            "Custo": f"${msg.get('cost', 0):.6f}",
                            "Tempo": f"{msg.get('execution_time', 0):.2f}s",
                            "Hora": msg["timestamp"]
                        })
                
                if message_data:
                    st.dataframe(message_data, use_container_width=True)

def main():
    """Função principal do aplicativo"""
    
    # Adiciona log de início se necessário
    if len(st.session_state.debug_logs) == 0:
        add_debug_log("info", "Aplicativo Streamlit iniciado (versão simplificada)")
    
    # Cabeçalho
    st.markdown("""
    <div class="title-container">
        <h1>🤖 Claude Chat</h1>
        <p>Interface Web</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com controles
    with st.sidebar:
        st.header("⚙️ Controles")
        
        if st.session_state.processing:
            st.warning("🟡 Processando Mensagem...")
        else:
            st.success("🟢 Wrapper Python Ativo")
        
        # Toggle Debug Mode
        st.session_state.debug_mode = st.checkbox(
            "🔍 Modo Debug", 
            value=st.session_state.debug_mode,
            help="Ativa painel de debug com logs detalhados"
        )
        
        # Botão de limpeza
        if st.button("🔄 Nova Conversa", use_container_width=True, disabled=st.session_state.processing):
            if not st.session_state.processing:
                clear_conversation()
                st.rerun()
            else:
                st.warning("Aguarde o processamento terminar antes de limpar")
        
        # Métricas
        st.header("📊 Estatísticas")
        
        st.metric("Tokens de Entrada", f"{st.session_state.total_tokens['input']:,}")
        st.metric("Tokens de Saída", f"{st.session_state.total_tokens['output']:,}")
        st.metric("Custo Total", f"${st.session_state.total_cost:.6f}")
        
    
    # Painel de Debug (se ativado)
    render_debug_panel()
    
    # Área principal do chat
    st.header("💬 Conversa")
    
    # Container para mensagens
    messages_container = st.container()
    
    # Exibe mensagens
    with messages_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="stChatMessage user-message">
                    <strong>👤 Você ({msg['timestamp']}):</strong><br>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                # Monta informações de métricas
                metrics_info = f"Tokens: {msg.get('input_tokens', 0)}↑ {msg.get('output_tokens', 0)}↓"
                metrics_info += f" | Custo: ${msg.get('cost', 0):.6f}"
                metrics_info += f" | Tempo: {msg.get('execution_time', 0):.2f}s"
                
                metrics_box = f'<div class="metrics-box">{metrics_info}</div>'
                
                st.markdown(f"""
                <div class="stChatMessage assistant-message">
                    <strong>🤖 Claude ({msg['timestamp']}):</strong><br>
                    {msg['content'].replace(chr(10), '<br>')}
                    {metrics_box}
                </div>
                """, unsafe_allow_html=True)
            elif msg["role"] == "error":
                st.markdown(f"""
                <div class="stChatMessage error-message">
                    <strong>⚠️ Erro ({msg['timestamp']}):</strong><br>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)
    
    # Input para nova mensagem
    st.header("✍️ Nova Mensagem")
    
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Digite sua mensagem:",
            placeholder="Olá Claude! Como você pode me ajudar hoje?",
            height=100,
            key="user_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            send_button = st.form_submit_button("📨 Enviar", use_container_width=True)
        
        with col2:
            example_button = st.form_submit_button("💡 Exemplo", use_container_width=True)
    
    # Processa envio
    if send_button and user_input.strip():
        if st.session_state.processing:
            st.warning("⚠️ Aguarde! Uma mensagem ainda está sendo processada...")
            add_debug_log("warning", "Tentativa de envio durante processamento", {
                "input": user_input.strip()
            })
        else:
            st.session_state.processing = True
            add_debug_log("info", "Usuário iniciou envio de mensagem", {
                "input": user_input.strip(),
                "current_messages": len(st.session_state.messages)
            })
            
            try:
                with st.spinner("🤖 Claude está pensando..."):
                    send_message(user_input.strip())
                add_debug_log("info", "Processamento da mensagem concluído", {
                    "final_messages": len(st.session_state.messages)
                })
            except Exception as e:
                add_debug_log("error", "Erro durante processamento", {
                    "error": str(e)
                })
                st.error(f"❌ Erro: {str(e)}")
            finally:
                st.session_state.processing = False
            
            st.rerun()
    
    # Processa exemplo
    if example_button:
        if st.session_state.processing:
            st.warning("⚠️ Aguarde! Uma mensagem ainda está sendo processada...")
        else:
            st.session_state.processing = True
            example_prompt = "Olá Claude! Você pode me explicar como funciona este SDK Python em 3 pontos principais?"
            add_debug_log("info", "Exemplo enviado pelo usuário")
            
            try:
                with st.spinner("🤖 Claude está pensando..."):
                    send_message(example_prompt)
            except Exception as e:
                add_debug_log("error", "Erro durante processamento do exemplo", {
                    "error": str(e)
                })
                st.error(f"❌ Erro: {str(e)}")
            finally:
                st.session_state.processing = False
            
            st.rerun()
    

if __name__ == "__main__":
    main()