#!/usr/bin/env python3
"""
🛠️ Streamlit Debug Interface - Viewer Claude Session Summarizer
Interface de debug para testar e monitorar o sistema de resumo de sessões
"""

import streamlit as st
import json
import time
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import asyncio

# Configuração da página
st.set_page_config(
    page_title="🛠️ Viewer Debug - Session Summarizer",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.debug-container {
    background-color: #1e1e1e;
    color: #ffffff;
    padding: 1rem;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    max-height: 400px;
    overflow-y: auto;
    margin: 1rem 0;
}

.success-box {
    background-color: #d4edda;
    color: #155724;
    padding: 1rem;
    border-left: 4px solid #28a745;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.error-box {
    background-color: #f8d7da;
    color: #721c24;
    padding: 1rem;
    border-left: 4px solid #dc3545;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.warning-box {
    background-color: #fff3cd;
    color: #856404;
    padding: 1rem;
    border-left: 4px solid #ffc107;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.info-box {
    background-color: #d1ecf1;
    color: #0c5460;
    padding: 1rem;
    border-left: 4px solid #17a2b8;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Configurações
VIEWER_URL = "http://localhost:3041"
CLAUDE_PROJECTS_PATH = Path("/home/suthub/.claude/projects")

# Estado da sessão
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []
if "test_results" not in st.session_state:
    st.session_state.test_results = {}
if "selected_session" not in st.session_state:
    st.session_state.selected_session = None
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = True  # Ativado por padrão

def add_debug_log(level: str, message: str, details: dict = None):
    """Adiciona log de debug com melhor rastreamento"""
    import traceback
    import inspect
    
    # Só registra logs se modo debug estiver ativo OU for um erro
    if not st.session_state.get('debug_mode', False) and level.upper() != "ERROR":
        return
    
    # Capturar informação do contexto
    caller_info = {}
    try:
        frame = inspect.currentframe().f_back
        caller_info = {
            "function": frame.f_code.co_name,
            "line": frame.f_lineno,
            "file": frame.f_code.co_filename.split('/')[-1]
        }
    except:
        caller_info = {"function": "unknown", "line": 0, "file": "unknown"}
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "details": details or {},
        "caller": caller_info,
        "stack_trace": traceback.format_stack()[-3:-1] if level.upper() == "ERROR" else None
    }
    st.session_state.debug_logs.append(log_entry)
    
    # Manter apenas os últimos 500 logs (aumentado para melhor debug)
    if len(st.session_state.debug_logs) > 500:
        st.session_state.debug_logs = st.session_state.debug_logs[-500:]

def test_viewer_connection():
    """Testa conexão com o viewer"""
    try:
        response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=5)
        if response.status_code == 200:
            sessions = response.json()
            add_debug_log("info", f"Viewer conectado - {len(sessions)} sessões encontradas")
            return True, len(sessions)
        else:
            add_debug_log("error", f"Viewer respondeu com status {response.status_code}")
            return False, 0
    except Exception as e:
        add_debug_log("error", f"Erro ao conectar com viewer: {str(e)}")
        return False, 0

def get_available_sessions():
    """Obtém lista de sessões disponíveis"""
    try:
        response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        add_debug_log("error", f"Erro ao obter sessões: {str(e)}")
    return []

def test_summarizer_with_custom_content(custom_content: str, summary_type: str = "conciso"):
    """Testa resumo com conteúdo customizado"""
    execution_time = 0
    try:
        add_debug_log("info", f"Iniciando teste com conteúdo customizado", {
            "content_length": len(custom_content),
            "summary_type": summary_type
        })
        
        # Criar prompt personalizado diretamente
        base_instruction = "Analise esta conversa e crie um resumo estruturado em português brasileiro."
        
        if summary_type == "conciso":
            format_instruction = """
Formato CONCISO (máximo 20 palavras apenas):
📋 **Contexto**: [tipo de projeto/problema]
🎯 **Objetivo**: [o que foi solicitado]
✅ **Resultado**: [o que foi implementado/resolvido]
🔧 **Tecnologias**: [principais ferramentas]

Resumo ultra-conciso em 20 palavras:"""
        elif summary_type == "detalhado":
            format_instruction = """
Formato DETALHADO (máximo 400 palavras):
📋 **Contexto Completo**: [situação e background do projeto]
🎯 **Objetivos**: [todos os goals e requisitos discutidos]
⚙️ **Implementação**: [detalhes técnicos, arquitetura, decisões]
✅ **Resultados**: [tudo que foi entregue e funcionalidades]
🔧 **Tecnologias**: [stack completo utilizado]
💡 **Insights**: [aprendizados e decisões importantes]
🔄 **Próximos Passos**: [se mencionados na conversa]

Resumo:"""
        elif summary_type == "anti-churn":
            format_instruction = """
Formato ANTI-CHURN (estratégia para retenção de cliente):
💼 **Situação do Cliente**: [contexto da solicitação de cancelamento]
🎯 **Problema Identificado**: [razões pelo cancelamento - falta de leads qualificados, baixa conversão, budget limitado]
💡 **Soluções Propostas**: [estratégias específicas para gerar leads qualificados]
📊 **Análise BANT**: [Budget, Authority, Need, Timeline - como melhorar cada aspecto]
🔧 **Plano de Ação**: [passos concretos para reverter o cancelamento]
💰 **Proposta de Valor**: [benefícios claros que justifiquem continuar o serviço]
📈 **Métricas de Sucesso**: [como medir melhoria nos resultados]

Estratégia anti-churn:"""
        else:  # bullet_points
            format_instruction = """
Formato BULLET POINTS:
🎯 **Objetivos Principais:**
• [objetivo 1]
• [objetivo 2]

⚙️ **Implementação:**
• [implementação 1]
• [implementação 2]

✅ **Resultados:**
• [resultado 1]
• [resultado 2]

🔧 **Tecnologias:**
• [tech 1]
• [tech 2]

Resumo:"""
        
        full_prompt = f"{base_instruction}\n{format_instruction}\n\nConversa para análise:\n{custom_content[:10000]}"  # Limitar a 10k chars
        
        start_time = time.time()
        
        # Fazer chamada direta ao endpoint de resumo customizado
        payload = {
            "custom_content": custom_content,
            "summary_type": summary_type
        }
        
        try:
            response = requests.post(
                f"{VIEWER_URL}/api/summarize-custom", 
                json=payload,
                timeout=120,
                headers={"Content-Type": "application/json"}
            )
            execution_time = time.time() - start_time
            
            add_debug_log("debug", f"Resposta da API customizada recebida", {
                "status_code": response.status_code,
                "execution_time": execution_time,
                "response_size": len(response.content) if response.content else 0
            })
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    add_debug_log("info", f"Resumo customizado concluído com sucesso em {execution_time:.2f}s", {
                        "summary_length": len(result.get('summary', '')),
                        "has_summary": bool(result.get('summary')),
                        "success": result.get('success', False)
                    })
                    return True, result, execution_time
                except json.JSONDecodeError as je:
                    add_debug_log("error", f"Erro ao decodificar JSON customizado: {str(je)}")
                    return False, {"error": f"Resposta inválida: {str(je)}"}, execution_time
            else:
                error_details = {
                    "status_code": response.status_code,
                    "response_text": response.text[:1000]
                }
                add_debug_log("error", f"Erro HTTP {response.status_code} no resumo customizado", error_details)
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}, execution_time
        
        except requests.exceptions.Timeout:
            add_debug_log("error", f"Timeout no resumo customizado após {execution_time:.2f}s")
            return False, {"error": f"Timeout após {execution_time:.2f}s"}, execution_time
        except requests.exceptions.ConnectionError as ce:
            add_debug_log("error", f"Erro de conexão no resumo customizado: {str(ce)}")
            return False, {"error": f"Erro de conexão: {str(ce)}"}, execution_time
        
    except Exception as e:
        add_debug_log("error", f"Erro no teste customizado: {str(e)}")
        return False, {"error": str(e)}, execution_time

def test_summarizer_endpoint(directory: str, session_id: str, summary_type: str = "conciso"):
    """Testa endpoint de resumo com debug detalhado"""
    execution_time = 0
    try:
        add_debug_log("info", f"Iniciando teste de resumo", {
            "directory": directory,
            "session_id": session_id,
            "summary_type": summary_type,
            "url": f"{VIEWER_URL}/api/summarize"
        })
        
        payload = {
            "directory": directory,
            "session_id": session_id,
            "summary_type": summary_type
        }
        
        start_time = time.time()
        
        # Teste de conectividade primeiro
        try:
            health_check = requests.get(f"{VIEWER_URL}/health", timeout=5)
            add_debug_log("debug", f"Health check: {health_check.status_code}")
        except Exception as he:
            add_debug_log("warning", f"Health check falhou: {str(he)}")
        
        response = requests.post(
            f"{VIEWER_URL}/api/summarize", 
            json=payload,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        execution_time = time.time() - start_time
        
        add_debug_log("debug", f"Resposta recebida", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "execution_time": execution_time,
            "response_size": len(response.content) if response.content else 0
        })
        
        if response.status_code == 200:
            try:
                result = response.json()
                add_debug_log("info", f"Resumo concluído com sucesso em {execution_time:.2f}s", {
                    "summary_length": len(result.get('summary', '')),
                    "metrics": result.get('metrics', {}),
                    "has_summary": bool(result.get('summary')),
                    "success": result.get('success', False)
                })
                return True, result, execution_time
            except json.JSONDecodeError as je:
                add_debug_log("error", f"Erro ao decodificar JSON da resposta: {str(je)}", {
                    "response_text": response.text[:500],  # Primeiros 500 chars
                    "content_type": response.headers.get('content-type')
                })
                return False, {"error": f"Resposta inválida: {str(je)}"}, execution_time
        else:
            error_details = {
                "status_code": response.status_code,
                "response_text": response.text[:1000],  # Primeiros 1000 chars
                "headers": dict(response.headers)
            }
            add_debug_log("error", f"Erro HTTP {response.status_code} no resumo", error_details)
            return False, {"error": f"HTTP {response.status_code}: {response.text}"}, execution_time
            
    except requests.exceptions.Timeout as te:
        add_debug_log("error", f"Timeout na requisição de resumo após {execution_time:.2f}s: {str(te)}")
        return False, {"error": f"Timeout após {execution_time:.2f}s"}, execution_time
    except requests.exceptions.ConnectionError as ce:
        add_debug_log("error", f"Erro de conexão no resumo: {str(ce)}", {
            "url": f"{VIEWER_URL}/api/summarize",
            "directory": directory
        })
        return False, {"error": f"Erro de conexão: {str(ce)}"}, execution_time
    except Exception as e:
        add_debug_log("error", f"Erro inesperado na requisição de resumo: {str(e)}", {
            "exception_type": type(e).__name__,
            "directory": directory,
            "session_id": session_id
        })
        return False, {"error": f"Erro inesperado: {str(e)}"}, execution_time

def main():
    """Interface principal de debug"""
    
    # Cabeçalho
    st.markdown("""
    <div style="background: linear-gradient(90deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
        <h1>🤖 Claude Chat API</h1>
        <p>✅ Sistema Totalmente Funcional - Gerando Resumos com IA</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com controles
    with st.sidebar:
        st.header("🔧 Controles")
        
        # Toggle Debug Mode
        st.session_state.debug_mode = st.checkbox(
            "🔍 Modo Debug Avançado", 
            value=st.session_state.debug_mode,
            help="Ativa logs detalhados e informações técnicas avançadas"
        )
        
        st.divider()
        
        # Status da API
        st.subheader("🌟 Status da API")
        
        # Teste automático de conexão
        try:
            response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=10)
            if response.status_code == 200:
                sessions = response.json()
                st.success(f"🚀 API Online - {len(sessions)} sessões")
            else:
                st.error(f"⚠️ API respondeu com código {response.status_code}")
        except Exception as e:
            st.error(f"❌ API Offline - {str(e)}")
        
        # Teste de conexão manual
        if st.button("🔄 Testar Novamente", key="test_again_1", use_container_width=True):
            st.rerun()
        
        st.divider()
        
        # Limpeza de logs
        if st.button("🗑️ Limpar Logs", key="clear_logs_1", use_container_width=True):
            st.session_state.debug_logs = []
            st.rerun()
        
        # Informações avançadas quando debug está ativo
        if st.session_state.debug_mode:
            st.subheader("🔍 Debug Avançado")
            
            # Estatísticas dos logs
            if st.session_state.debug_logs:
                log_levels = {}
                for log in st.session_state.debug_logs[-50:]:  # Últimos 50
                    level = log["level"].upper()
                    log_levels[level] = log_levels.get(level, 0) + 1
                
                st.json({"Logs por nível": log_levels})
            
            # Debug level
            debug_level = st.selectbox(
                "Nível de Debug",
                ["info", "warning", "error", "all"],
                index=3,  # "all" selecionado por padrão
                help="Mostra mais detalhes técnicos quando ativo"
            )
            
            st.metric("Logs em Memória", len(st.session_state.debug_logs))
            st.metric("Testes Executados", len(st.session_state.test_results))
            
            # Configurações avançadas de sessão
            st.subheader("⚙️ Config de Sessão")
            
            # System prompt personalizado
            custom_system_prompt = st.text_area(
                "System Prompt:",
                value=st.session_state.get('session_system_prompt', ''),
                height=80,
                placeholder="Ex: Você é um especialista em...",
                help="Prompt de sistema para novas sessões de chat"
            )
            st.session_state.session_system_prompt = custom_system_prompt
            
            # Ferramentas permitidas
            available_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch"]
            selected_tools = st.multiselect(
                "Ferramentas:",
                available_tools,
                default=st.session_state.get('session_tools', available_tools),  # Todos selecionados por padrão
                help="Ferramentas que o Claude pode usar"
            )
            st.session_state.session_tools = selected_tools
            
            # Outras configurações
            max_turns = st.number_input("Max Turnos:", value=20, min_value=1, max_value=100)
            st.session_state.session_max_turns = max_turns
        
        st.divider()
        
        # Informações do sistema
        st.subheader("📊 Status do Sistema")
        
        # Indicadores de status em tempo real
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            # Contar erros recentes (últimos 10 minutos)
            recent_errors = 0
            current_time = datetime.now()
            for log in st.session_state.debug_logs[-50:]:  # Últimos 50 logs
                log_time = datetime.fromisoformat(log["timestamp"])
                if (current_time - log_time).total_seconds() < 600:  # 10 minutos
                    if log["level"].upper() == "ERROR":
                        recent_errors += 1
            
            error_status = "🔴 Erros" if recent_errors > 0 else "✅ Normal"
            st.metric("Status", error_status, delta=f"{recent_errors} erros recentes")
        
        with col_status2:
            st.metric("Logs Total", len(st.session_state.debug_logs))
        
        with col_status3:
            # Status dos últimos testes
            recent_tests = len(st.session_state.test_results) if hasattr(st.session_state, 'test_results') else 0
            success_rate = 0
            if hasattr(st.session_state, 'test_results') and st.session_state.test_results:
                successful = sum(1 for r in st.session_state.test_results.values() 
                               if r['result'].get('success', False))
                success_rate = (successful / len(st.session_state.test_results) * 100) if st.session_state.test_results else 0
            
            st.metric("Testes", recent_tests, delta=f"{success_rate:.0f}% sucesso")
        
        
        # Alertas importantes na página principal
        if recent_errors > 0:
            st.error(f"⚠️ **{recent_errors} erro(s) recente(s) detectado(s)!** Verifique a aba 'Logs de Debug' para detalhes.")
        
        # Resumo dos últimos testes falhados
        if hasattr(st.session_state, 'test_results'):
            failed_tests = [r for r in st.session_state.test_results.values() if not r.get('success', True)]
            if failed_tests:
                st.warning(f"⚠️ **{len(failed_tests)} teste(s) falharam.** Veja detalhes na aba 'Métricas'.")
            elif len(st.session_state.test_results) > 0:
                successful_tests = len([r for r in st.session_state.test_results.values() if r.get('success', True)])
                st.success(f"🎯 **{successful_tests} teste(s) executado(s) com sucesso!** Sistema funcionando perfeitamente.")
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs([
        "🧪 Testes de Resumo", 
        "📝 Logs de Debug", 
        "📊 Métricas"
    ])
    
    # Tab 1: Testes de Resumo
    with tab1:
        st.header("🧪 Testes de Funcionalidade")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 Sessões Disponíveis")
            
            # Atualização automática da lista de sessões
            sessions = get_available_sessions()
            st.session_state.available_sessions = sessions
                
            if sessions:
                session_options = []
                for session in sessions[:20]:  # Limita a 20 para performance
                    display_name = f"{session['directory']} | {session['session_id'][:8]}..."
                    session_options.append((display_name, session))
                    
                selected_idx = st.selectbox(
                    "Selecionar Sessão:",
                    range(len(session_options)),
                    format_func=lambda i: session_options[i][0] if session_options else "Nenhuma"
                )
                    
                if session_options:
                    st.session_state.selected_session = session_options[selected_idx][1]
                    selected_session = session_options[selected_idx][1]
                    
                    # Botões de ação para a sessão selecionada
                    col_action1, col_action2, col_action3 = st.columns(3)
                    
                    with col_action1:
                        if st.button("🗑️ Deletar", key="delete_selected_session", use_container_width=True, type="secondary"):
                            # Deletar a sessão selecionada
                            try:
                                delete_url = f"{VIEWER_URL}/api/session/{selected_session['directory']}/{selected_session['session_id']}"
                                delete_response = requests.delete(delete_url, timeout=10)
                            
                                if delete_response.status_code == 200:
                                    st.success(f"✅ Sessão {selected_session['session_id'][:8]}... deletada!")
                                    
                                    # Log da exclusão
                                    add_debug_log("info", "Sessão deletada via seletor", {
                                        "deleted_directory": selected_session['directory'],
                                        "deleted_session_id": selected_session['session_id']
                                    })
                                    
                                    # Limpar seleção atual e atualizar
                                    st.session_state.selected_session = None
                                    if 'last_generated_summary' in st.session_state:
                                        del st.session_state.last_generated_summary
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erro ao deletar: HTTP {delete_response.status_code}")
                                    add_debug_log("error", f"Erro ao deletar sessão: HTTP {delete_response.status_code}")
                            
                            except Exception as e:
                                st.error(f"❌ Erro na exclusão: {str(e)}")
                                add_debug_log("error", f"Erro na exclusão da sessão: {str(e)}")
                    
                    with col_action2:
                        # Link direto para o viewer web
                        viewer_url = f"http://localhost:3041/{selected_session['directory']}/{selected_session['session_id']}"
                        st.markdown(f"[🌐 Abrir Web]({viewer_url})", unsafe_allow_html=True)
                    
                    with col_action3:
                        if st.button("🔄 Recarregar", key="reload_session_data", use_container_width=True, type="secondary"):
                            # Forçar recarregamento dos dados da sessão
                            st.rerun()
                    
                    
                    # Carregar e exibir conteúdo da sessão para edição
                    file_path = Path(selected_session.get('file_path', ''))
                    
                    # Carregar metadados da sessão
                    if file_path.exists():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                            
                            # Extrair conversa de forma simplificada para estatísticas
                            conversation_parts = []
                            for line in lines:
                                try:
                                    data = json.loads(line.strip())
                                    if data.get('type') == 'user':
                                        message_content = data.get('message', {}).get('content', '')
                                        conversation_parts.append(f"👤 Usuário: {message_content}")
                                    elif data.get('type') == 'assistant':
                                        message = data.get('message', {})
                                        if isinstance(message.get('content'), list):
                                            # Extrair texto dos blocos de conteúdo
                                            text_parts = []
                                            for block in message['content']:
                                                if isinstance(block, dict) and block.get('type') == 'text':
                                                    text_parts.append(block.get('text', ''))
                                            content = ' '.join(text_parts)
                                        else:
                                            content = str(message.get('content', ''))
                                        conversation_parts.append(f"🤖 Claude: {content}")
                                except json.JSONDecodeError:
                                    continue
                            
                            full_conversation = '\n\n'.join(conversation_parts)
                            
                            # Armazenar conversa original para uso posterior
                            st.session_state.original_conversation = full_conversation
                            
                            # Informações sobre a sessão
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                st.info(f"📊 {len(conversation_parts)} mensagens")
                            with col_info2:
                                st.info(f"📝 {len(full_conversation):,} caracteres")
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
                    else:
                        st.error(f"❌ Arquivo não encontrado: {file_path}")
                            
                    # Área de Resumo Gerado com UI/UX melhorada
                    if 'last_generated_summary' in st.session_state:
                        summary_data = st.session_state.last_generated_summary
                        is_success = summary_data.get('success', False)
                        
                        if is_success:
                                # Apenas o conteúdo, sem headers ou informações extras
                                
                                # Área de texto com melhor formatação
                                summary_content = summary_data.get('result', {}).get('summary', 'N/A')
                                
                                # Parser de markdown melhorado para resumos
                                import re
                                
                                def parse_summary_markdown(content: str) -> str:
                                    """Parser robusto para formatação de resumos"""
                                    html = content
                                    
                                    # Headers (## título)
                                    html = re.sub(r'^## (.*?)$', 
                                                 r'<h3 style="color: #667eea; margin: 25px 0 15px 0; font-weight: bold; font-size: 18px; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px;">\1</h3>', 
                                                 html, flags=re.MULTILINE)
                                    
                                    # Bold com emojis (📋 **texto**)
                                    html = re.sub(r'(📋|🎯|✅|🔧|⚙️|💡|🔄)\s*\*\*(.*?)\*\*:', 
                                                 r'<div style="margin: 15px 0;"><span style="font-size: 16px; margin-right: 10px;">\1</span><strong style="color: #333; font-size: 15px;">\2:</strong></div>', 
                                                 html)
                                    
                                    # Bold simples
                                    html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #333;">\1</strong>', html)
                                    
                                    # Separadores horizontais
                                    html = re.sub(r'^---$', r'<hr style="border: none; border-top: 2px solid #e9ecef; margin: 25px 0;">', html, flags=re.MULTILINE)
                                    
                                    # Listas com bullet points (• item)
                                    html = re.sub(r'^• (.*?)$', r'<div style="margin: 8px 0 8px 20px; color: #555;"><span style="color: #667eea; margin-right: 8px;">•</span>\1</div>', html, flags=re.MULTILINE)
                                    
                                    # Código inline (`código`)
                                    html = re.sub(r'`(.*?)`', r'<code style="background: #f8f9fa; padding: 2px 6px; border-radius: 4px; font-family: monospace; color: #e83e8c;">\1</code>', html)
                                    
                                    # Emojis isolados com espaçamento
                                    html = re.sub(r'^(📋|🎯|✅|🔧|⚙️|💡|🔄|📊|💰)', r'<span style="display: inline-block; margin-right: 8px; font-size: 16px;">\1</span>', html, flags=re.MULTILINE)
                                    
                                    # Quebras de linha duplas para parágrafos
                                    html = re.sub(r'\n\s*\n', '</p><p style="margin: 15px 0; line-height: 1.6;">', html)
                                    
                                    # Quebras simples
                                    html = html.replace('\n', '<br>')
                                    
                                    # Envolver em parágrafo se não começar com tag
                                    if not html.strip().startswith('<'):
                                        html = f'<p style="margin: 15px 0; line-height: 1.6;">{html}</p>'
                                    
                                    return html
                                
                                # Aplicar parser melhorado
                                html_content = parse_summary_markdown(summary_content)
                                
                                # Mostrar apenas o conteúdo limpo
                                st.markdown(f"""
                                <div style="background: #ffffff; border: 2px solid #e9ecef; border-radius: 12px; 
                                            padding: 25px; margin: 15px 0; font-family: 'Segoe UI', Arial, sans-serif;
                                            line-height: 1.8; color: #212529; font-size: 15px;
                                            box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                                    {html_content}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Botões de ação para sucesso
                                col_action1, col_action2, col_action3 = st.columns(3)
                                
                                with col_action1:
                                    if st.button("📋 Copiar Conteúdo", key="copy_improved", use_container_width=True):
                                        st.success("✅ Use Ctrl+A e Ctrl+C na área de texto acima")
                                
                                with col_action2:
                                    if st.button("🗑️ Deletar Sessão", key="delete_session", use_container_width=True):
                                        # Deletar permanentemente a nova sessão criada
                                        created_session = summary_data.get('new_session_created')
                                        
                                        if created_session:
                                            try:
                                                # Fazer DELETE request para a API
                                                delete_url = f"{VIEWER_URL}/api/session/{created_session['directory']}/{created_session['session_id']}"
                                                delete_response = requests.delete(delete_url, timeout=10)
                                                
                                                if delete_response.status_code == 200:
                                                    st.success(f"✅ Sessão {created_session['session_id'][:8]}... deletada permanentemente!")
                                                    
                                                    # Log da exclusão
                                                    add_debug_log("info", "Sessão criada foi deletada permanentemente", {
                                                        "deleted_directory": created_session['directory'],
                                                        "deleted_session_id": created_session['session_id'],
                                                        "delete_url": delete_url
                                                    })
                                                    
                                                    # Remover da visualização também
                                                    del st.session_state.last_generated_summary
                                                    st.rerun()
                                                else:
                                                    st.error(f"❌ Erro ao deletar: HTTP {delete_response.status_code}")
                                                    add_debug_log("error", f"Erro ao deletar sessão: HTTP {delete_response.status_code}")
                                            
                                            except Exception as e:
                                                st.error(f"❌ Erro na exclusão: {str(e)}")
                                                add_debug_log("error", f"Erro na exclusão da sessão: {str(e)}")
                                        else:
                                            st.warning("⚠️ Nenhuma nova sessão para deletar")
                                            # Apenas remover da visualização se não há sessão para deletar
                                            del st.session_state.last_generated_summary
                                            st.rerun()
                                
                                with col_action3:
                                    if st.button("🔗 Nova Conversa", key="show_new_conversation", use_container_width=True):
                                        # Usar a sessão específica criada durante esta geração
                                        created_session = summary_data.get('new_session_created')
                                        
                                        if created_session:
                                            new_conversation_url = f"http://localhost:3041/{created_session['directory']}/{created_session['session_id']}"
                                            
                                            st.markdown(f"""
                                            **🔗 Nova Conversa Criada por Esta Geração:**
                                            
                                            [{new_conversation_url}]({new_conversation_url})
                                            """)
                                            st.info(f"📍 **Diretório:** `{created_session['directory']}`")
                                            st.info(f"🆔 **ID:** `{created_session['session_id']}`")
                                            st.success("🎯 **Esta é a sessão exata criada durante a geração do resumo!**")
                                            
                                            # Log da nova conversa específica
                                            add_debug_log("info", "Exibindo nova conversa específica", {
                                                "specific_directory": created_session['directory'],
                                                "specific_session_id": created_session['session_id'],
                                                "conversation_url": new_conversation_url
                                            })
                                        else:
                                            st.warning("⚠️ Nenhuma nova sessão foi detectada durante esta geração")
                                            st.info("💡 Isso pode acontecer se a geração não criou uma nova conversa ou se houve erro na detecção")
                            
                        else:
                            # Card de erro
                            st.markdown(f"""
                                <div style="background: #f8d7da; border-radius: 15px; padding: 25px; 
                                            box-shadow: 0 8px 25px rgba(0,0,0,0.1); border-left: 5px solid #dc3545; margin: 20px 0;">
                                    <div style="color: #721c24;">
                                        <h4 style="margin: 0 0 15px 0; display: flex; align-items: center;">
                                            <span style="margin-right: 8px;">⚠️</span>
                                            Erro na Geração do Resumo
                                        </h4>
                                        <div style="background: white; padding: 15px; border-radius: 8px; color: #333;">
                                            <strong>Detalhes:</strong> {summary_data.get('error', 'Erro desconhecido')}<br>
                                            <small><strong>Tempo:</strong> {summary_data.get('execution_time', 0):.2f}s</small>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                            # Botões de ação também para erros
                            col_error1, col_error2 = st.columns(2)
                            
                            with col_error1:
                                if st.button("🔗 Ver Nova Conversa", key="show_new_conversation_error", use_container_width=True):
                                    created_session = summary_data.get('new_session_created')
                                    
                                    if created_session:
                                        new_conversation_url = f"http://localhost:3041/{created_session['directory']}/{created_session['session_id']}"
                                        
                                        st.markdown(f"""
                                        **🔗 Nova Conversa (mesmo com erro):**
                                        
                                        [{new_conversation_url}]({new_conversation_url})
                                        """)
                                        st.info(f"📍 **Diretório:** `{created_session['directory']}`")
                                        st.info(f"🆔 **ID:** `{created_session['session_id']}`")
                                        st.info("💡 **Uma nova sessão foi criada mesmo com o erro**")
                                    else:
                                        st.warning("⚠️ Nenhuma nova sessão foi criada durante este erro")
                            
                            with col_error2:
                                if st.button("🗑️ Limpar Erro", key="clear_error", use_container_width=True):
                                    del st.session_state.last_generated_summary
                                    st.success("✅ Erro removido da visualização!")
                                    st.rerun()
                            
                        
                else:
                    st.warning("⚠️ Nenhuma sessão encontrada")
            else:
                st.info("📋 Clique em 'Atualizar Lista' para carregar sessões")
        
        with col2:
            st.subheader("🎯 Teste de Resumo")
            
            if st.session_state.selected_session:
                session = st.session_state.selected_session
                
                summary_type = st.selectbox(
                    "Tipos:",
                    ["conciso", "bullet_points", "detalhado", "anti-churn"],  # conciso em primeiro
                    help="Escolha o formato de resumo desejado"
                )
                
                # Explicação dos tipos
                if summary_type == "conciso":
                    st.info("📋 **Conciso**: Resumo estruturado em até 20 palavras apenas com contexto, objetivo, resultado e tecnologias")
                elif summary_type == "bullet_points":
                    st.info("🔸 **Bullet Points**: Lista organizada por tópicos com pontos principais da conversa")
                elif summary_type == "detalhado":
                    st.info("📖 **Detalhado**: Análise completa em até 400 palavras incluindo implementação, insights e próximos passos")
                else:  # anti-churn
                    st.info("💼 **Anti-Churn**: Estratégia para retenção de cliente com soluções para gerar leads qualificados e reverter cancelamento")
                
                if st.button("🚀 Executar Teste de Resumo", key="exec_test_1", use_container_width=True):
                    # Capturar lista de sessões ANTES da geração
                    sessions_before = []
                    try:
                        response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=10)
                        if response.status_code == 200:
                            sessions_before = [s['session_id'] for s in response.json()]
                    except:
                        pass
                    
                    # Verificar se há conversa original e prompt customizado
                    has_conversation = hasattr(st.session_state, 'original_conversation') and st.session_state.original_conversation
                    has_custom_prompt = st.session_state.get('custom_system_prompt', '').strip()
                    use_enhanced_mode = has_conversation and has_custom_prompt
                    
                    # Log início do teste
                    add_debug_log("info", f"Iniciando teste de resumo tipo '{summary_type}'", {
                        "session_id": session['session_id'],
                        "directory": session['directory'],
                        "summary_type": summary_type,
                        "has_custom_prompt": bool(has_custom_prompt),
                        "enhanced_mode": use_enhanced_mode,
                        "sessions_before_count": len(sessions_before)
                    })
                    
                    with st.spinner("🤖 Gerando resumo..."):
                        if use_enhanced_mode:
                            # Combinar prompt customizado com conversa
                            enhanced_content = f"""INSTRUÇÕES ESPECÍFICAS: {has_custom_prompt}

CONVERSA PARA ANÁLISE:
{st.session_state.original_conversation}"""
                            
                            success, result, exec_time = test_summarizer_with_custom_content(
                                enhanced_content,
                                summary_type
                            )
                        elif has_conversation:
                            # Usar conversa original sem prompt customizado
                            success, result, exec_time = test_summarizer_with_custom_content(
                                st.session_state.original_conversation,
                                summary_type
                            )
                        else:
                            # Usar método original (fallback)
                            success, result, exec_time = test_summarizer_endpoint(
                                session['directory'], 
                                session['session_id'],
                                summary_type
                            )
                        
                        # Capturar lista de sessões APÓS a geração para detectar nova sessão
                        new_session_created = None
                        try:
                            response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=10)
                            if response.status_code == 200:
                                sessions_after = response.json()
                                sessions_after_ids = [s['session_id'] for s in sessions_after]
                                
                                # Encontrar nova sessão criada
                                new_session_ids = set(sessions_after_ids) - set(sessions_before)
                                if new_session_ids:
                                    new_session_id = list(new_session_ids)[0]
                                    new_session_created = next(s for s in sessions_after if s['session_id'] == new_session_id)
                                    
                                    add_debug_log("info", f"Nova sessão detectada: {new_session_id}", {
                                        "new_session": new_session_created,
                                        "sessions_before": len(sessions_before),
                                        "sessions_after": len(sessions_after)
                                    })
                        except Exception as e:
                            add_debug_log("warning", f"Erro ao detectar nova sessão: {str(e)}")
                    
                    if success:
                        # Mensagem de sucesso personalizada
                        if use_enhanced_mode:
                            st.success(f"✅ Resumo gerado com prompt personalizado em {exec_time:.2f}s")
                            st.info("🎯 **Prompt aplicado:** Suas instruções específicas foram incluídas na análise")
                        else:
                            st.success(f"✅ Resumo gerado em {exec_time:.2f}s")
                        
                        # Log sucesso
                        add_debug_log("info", f"Teste concluído com sucesso em {exec_time:.2f}s", {
                            "execution_time": exec_time,
                            "summary_length": len(result.get('summary', '')),
                            "tokens_used": result.get('metrics', {}).get('input_tokens', 0) + result.get('metrics', {}).get('output_tokens', 0),
                            "used_custom_prompt": use_enhanced_mode
                        })
                        
                        
                        # Métricas
                        metrics = result.get('metrics', {})
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.metric("Tokens In", metrics.get('input_tokens', 0))
                        with col_b:
                            st.metric("Tokens Out", metrics.get('output_tokens', 0))
                        with col_c:
                            st.metric("Custo", f"${metrics.get('cost', 0):.6f}")
                        
                        # Salva resultado para análise (incluindo prompt customizado e nova sessão)
                        test_result = {
                            "timestamp": datetime.now().isoformat(),
                            "session": session,
                            "result": result,
                            "execution_time": exec_time,
                            "summary_type": summary_type,
                            "success": True,
                            "custom_prompt": st.session_state.get('custom_system_prompt', '') if use_enhanced_mode else None,
                            "new_session_created": new_session_created  # A sessão específica criada por esta geração
                        }
                        
                        # Chave única incluindo prompt se houver
                        result_key = f"{session['session_id']}_{summary_type}"
                        if use_enhanced_mode:
                            result_key += f"_custom_{hash(has_custom_prompt) % 10000}"
                        
                        st.session_state.test_results[result_key] = test_result
                        
                        # Salvar resumo para exibição na UI melhorada
                        st.session_state.last_generated_summary = test_result
                        
                        # Forçar atualização da interface para mostrar o resumo automaticamente
                        st.rerun()
                    else:
                        error_msg = result.get('error', 'Erro desconhecido')
                        st.error(f"❌ Erro no resumo: {error_msg}")
                        
                        # Log detalhado do erro
                        add_debug_log("error", f"Falha no teste de resumo: {error_msg}", {
                            "session_id": session['session_id'],
                            "directory": session['directory'],
                            "summary_type": summary_type,
                            "execution_time": exec_time,
                            "error_details": result
                        })
                        
                        # Salva resultado do erro para análise (incluindo nova sessão se criada)
                        test_result = {
                            "timestamp": datetime.now().isoformat(),
                            "session": session,
                            "result": result,
                            "execution_time": exec_time,
                            "summary_type": summary_type,
                            "success": False,
                            "error": error_msg,
                            "new_session_created": new_session_created  # Mesmo em erro pode ter criado sessão
                        }
                        st.session_state.test_results[f"{session['session_id']}_{summary_type}"] = test_result
                        
                        # Salvar erro para exibição na UI
                        st.session_state.last_generated_summary = test_result
                        
                        # Forçar atualização da interface para mostrar o erro automaticamente
                        st.rerun()
            else:
                st.info("📋 Selecione uma sessão para testar")
    
    # Tab 2: Logs de Debug
    with tab2:
        st.header("📝 Logs de Debug")
        
        if not st.session_state.debug_mode:
            st.info("🔍 **Modo Debug Desativado** - Ative na sidebar para ver logs detalhados. Apenas erros são registrados.")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            max_logs = st.number_input("Máximo de logs:", value=50, min_value=10, max_value=200)
        with col2:
            reverse_order = st.checkbox("Mais recentes primeiro", value=True)
        with col3:
            if st.session_state.debug_mode:
                st.success("🔍 Debug Ativo")
            else:
                st.warning("⚠️ Debug Inativo")
        
        # Exibe logs
        if st.session_state.debug_logs:
            filtered_logs = st.session_state.debug_logs[-max_logs:]
            
            if not reverse_order:
                filtered_logs = list(reversed(filtered_logs))
            
            # Agrupar logs em linhas de 2 colunas (como nos testes)
            for i in range(0, len(filtered_logs), 2):
                cols = st.columns(2)
                
                for j, col in enumerate(cols):
                    if i + j < len(filtered_logs):
                        log = filtered_logs[i + j]
                        timestamp = log["timestamp"].split("T")[1][:8]
                        level = log["level"].upper()
                        message = log["message"]
                        
                        # Escolher emoji e cor baseado no level
                        if level == "ERROR":
                            emoji = "🔴"
                            color = "#fee"
                            border_color = "#f66"
                        elif level == "WARNING":
                            emoji = "🟡"
                            color = "#ffeaa7"
                            border_color = "#fdcb6e"
                        else:
                            emoji = "🔵"
                            color = "#e3f2fd"
                            border_color = "#2196f3"
                        
                        with col:
                            # Container estilizado como os testes
                            debug_info = ""
                            if st.session_state.debug_mode:
                                caller = log.get("caller", {})
                                debug_info = f"""
                                <div style="color: #666; font-size: 12px; margin-top: 5px;">
                                    📍 {caller.get('file', 'unknown')}:{caller.get('line', 0)} → {caller.get('function', 'unknown')}()
                                </div>
                                """
                            
                            st.markdown(f"""
                            <div style="border: 2px solid {border_color}; border-radius: 10px; 
                                        padding: 15px; margin: 10px 0; background: {color};">
                                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 20px; margin-right: 8px;">{emoji}</span>
                                    <strong style="color: #333;">[{timestamp}] {level}</strong>
                                </div>
                                <div style="color: #555; font-size: 14px; margin-bottom: 10px;">
                                    {message}
                                </div>
                                {debug_info}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Detalhes expandidos dentro do card
                            if log.get("details"):
                                with st.expander(f"🔍 Detalhes ({timestamp})"):
                                    st.json(log["details"])
                                    
                            # Stack trace para erros (só no modo debug)
                            if st.session_state.debug_mode and log.get("stack_trace"):
                                with st.expander(f"📚 Stack Trace ({timestamp})", expanded=False):
                                    for line in log["stack_trace"]:
                                        st.code(line.strip(), language="python")
        else:
            st.info("📋 Nenhum log de debug disponível")
    
    # Tab 3: Métricas
    with tab3:
        st.header("📊 Métricas de Performance")
        
        if st.session_state.test_results:
            st.subheader("📈 Resumo dos Testes")
            
            # Métricas gerais
            total_tests = len(st.session_state.test_results)
            successful_tests = sum(1 for result in st.session_state.test_results.values() 
                                 if result['result'].get('success', False))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Testes", total_tests)
            with col2:
                st.metric("Sucessos", successful_tests)
            with col3:
                success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
                st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
            
            # Separar sucessos e falhas
            successful_results = [r for r in st.session_state.test_results.values() if r.get('success', True)]
            failed_results = [r for r in st.session_state.test_results.values() if not r.get('success', True)]
            
            # Mostrar falhas primeiro se houver
            if failed_results:
                st.subheader("❌ Testes Falhados")
                
                for test_result in failed_results:
                    session = test_result['session']
                    
                    # Card de erro
                    st.markdown(f"""
                    <div style="border: 2px solid #f66; border-radius: 10px; 
                                padding: 15px; margin: 10px 0; background: #fee;">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 20px; margin-right: 8px;">❌</span>
                            <strong style="color: #333;">Erro em {test_result['summary_type']}</strong>
                        </div>
                        <div style="color: #555; font-size: 14px; margin-bottom: 5px;">
                            <strong>Sessão:</strong> {session['session_id'][:12]}...
                        </div>
                        <div style="color: #555; font-size: 14px; margin-bottom: 5px;">
                            <strong>Diretório:</strong> {session['directory']}
                        </div>
                        <div style="color: #555; font-size: 14px; margin-bottom: 5px;">
                            <strong>Tempo:</strong> {test_result['execution_time']:.2f}s
                        </div>
                        <div style="color: #d63384; font-size: 14px; font-weight: bold;">
                            <strong>Erro:</strong> {test_result.get('error', 'Erro desconhecido')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Detalhes do erro
                    with st.expander(f"🔍 Detalhes completos - {session['session_id'][:8]}"):
                        st.json(test_result)
            
            # Tabela de sucessos
            st.subheader("📋 Histórico Completo")
            
            results_data = []
            for key, test_result in st.session_state.test_results.items():
                session = test_result['session']
                result = test_result.get('result', {})
                
                is_success = test_result.get('success', result.get('success', False))
                status_icon = "✅" if is_success else "❌"
                
                results_data.append({
                    "Status": status_icon,
                    "Sessão": session['session_id'][:8] + "...",
                    "Diretório": session['directory'][:20] + "...",
                    "Tipo": test_result['summary_type'],
                    "Tempo (s)": f"{test_result['execution_time']:.2f}",
                    "Tokens": f"{result.get('metrics', {}).get('input_tokens', 0)}↑ {result.get('metrics', {}).get('output_tokens', 0)}↓" if is_success else "N/A",
                    "Custo": f"${result.get('metrics', {}).get('cost', 0):.6f}" if is_success else "N/A",
                    "Data": test_result['timestamp'][:19]
                })
            
            if results_data:
                st.dataframe(results_data, use_container_width=True)
            
        else:
            st.info("📊 Execute alguns testes para ver métricas aqui")

if __name__ == "__main__":
    main()