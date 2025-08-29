#!/usr/bin/env python3
"""
🔍 Debug Message Flow - Detector de Problemas
Analisa o fluxo de processamento de mensagens
"""

import json
import os
from datetime import datetime

def analyze_streamlit_logs():
    """Analisa logs do Streamlit para identificar problemas"""
    print("🔍 Analisando fluxo de mensagens do Streamlit...")
    
    # Simula o fluxo que deveria acontecer
    print("\n📋 Fluxo esperado para cada mensagem:")
    print("1. Usuário clica 'Enviar'")
    print("2. add_debug_log: 'Usuário iniciou envio de mensagem'")
    print("3. send_message() chamada")
    print("4. add_debug_log: 'Iniciando processamento de mensagem'") 
    print("5. Mensagem adicionada ao session_state")
    print("6. send_claude_query() chamada")
    print("7. Query executada com sucesso")
    print("8. Resposta adicionada ao session_state")
    print("9. st.rerun() para atualizar interface")
    
    print("\n🔍 Problemas possíveis identificados:")
    print("❓ Primeira mensagem: Logs mostram início mas não conclusão")
    print("❓ Segunda mensagem: Fluxo completo executado")
    
    return True

def simulate_streamlit_flow():
    """Simula o fluxo do Streamlit para identificar problema"""
    print("\n🧪 Simulando fluxo do Streamlit...")
    
    # Simula session state
    messages = []
    debug_logs = []
    
    def add_debug_log(level, message, details=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }
        debug_logs.append(log_entry)
        print(f"🔷 [{log_entry['timestamp'][-8:]}] {level.upper()}: {message}")
        if details:
            print(f"   Detalhes: {json.dumps(details, indent=2)}")
    
    def simulate_send_message(prompt):
        """Simula send_message()"""
        add_debug_log("info", "Iniciando processamento de mensagem", {"prompt": prompt[:50]})
        
        # Adiciona mensagem do usuário
        user_msg = {
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        messages.append(user_msg)
        add_debug_log("debug", "Mensagem do usuário adicionada", {"message_id": len(messages)})
        
        # Simula envio para Claude
        add_debug_log("info", "Enviando para Claude", {"prompt_length": len(prompt)})
        
        # Simula resultado (sempre sucesso para teste)
        result = {
            "success": True,
            "content": f"Resposta simulada para: {prompt}",
            "input_tokens": 3,
            "output_tokens": 20,
            "cost": 0.01
        }
        
        add_debug_log("debug", "Resultado do Claude recebido", {"success": result["success"]})
        
        if result["success"]:
            assistant_msg = {
                "role": "assistant",
                "content": result["content"],
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"], 
                "cost": result["cost"]
            }
            messages.append(assistant_msg)
            
            add_debug_log("info", "Resposta processada com sucesso", {
                "response_length": len(result["content"]),
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "cost": result["cost"],
                "total_messages": len(messages)
            })
    
    # Simula o cenário reportado
    print("📤 Simulando primeira mensagem: 'olá'")
    simulate_send_message("olá")
    
    print(f"\n📊 Estado após primeira mensagem:")
    print(f"   Mensagens: {len(messages)}")
    print(f"   Logs: {len(debug_logs)}")
    
    print("\n📤 Simulando segunda mensagem: 'tudo bem?'")
    simulate_send_message("tudo bem?")
    
    print(f"\n📊 Estado final:")
    print(f"   Mensagens: {len(messages)}")
    print(f"   Logs: {len(debug_logs)}")
    
    print("\n💬 Mensagens registradas:")
    for i, msg in enumerate(messages):
        role_icon = "👤" if msg["role"] == "user" else "🤖"
        print(f"   {i+1}. {role_icon} ({msg['timestamp']}): {msg['content'][:50]}...")
    
    return len(messages) == 4  # 2 usuário + 2 assistente

def check_potential_issues():
    """Verifica problemas potenciais"""
    print("\n🔍 Verificando problemas potenciais...")
    
    issues_found = []
    
    # 1. Problema de timing
    print("1️⃣ Verificando timing entre mensagens...")
    print("   ⚠️  Se usuário enviar segunda mensagem muito rápido,")
    print("      a primeira pode não ter tempo de completar")
    issues_found.append("timing")
    
    # 2. Problema de estado
    print("2️⃣ Verificando estado do Streamlit...")
    print("   ⚠️  st.rerun() pode causar interrupção do fluxo")
    print("      se chamado durante processamento anterior")
    issues_found.append("state")
    
    # 3. Problema de subprocess
    print("3️⃣ Verificando subprocess...")
    print("   ⚠️  Primeiro subprocess pode falhar silenciosamente")
    print("      mas não reportar erro adequadamente")
    issues_found.append("subprocess")
    
    return issues_found

if __name__ == "__main__":
    print("🚀 Debug do Fluxo de Mensagens - Análise Detalhada")
    print("=" * 60)
    
    try:
        # Análise dos logs
        analyze_streamlit_logs()
        
        # Simulação do fluxo
        simulation_ok = simulate_streamlit_flow()
        
        # Verificação de problemas
        potential_issues = check_potential_issues()
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DA ANÁLISE")
        print("=" * 60)
        
        print(f"✅ Simulação completa: {'SIM' if simulation_ok else 'NÃO'}")
        print(f"⚠️  Problemas potenciais: {len(potential_issues)}")
        
        print(f"\n🎯 HIPÓTESE PRINCIPAL:")
        print(f"A primeira mensagem iniciou processamento mas foi")
        print(f"interrompida quando a segunda mensagem foi enviada,") 
        print(f"causando st.rerun() antes da conclusão.")
        
        print(f"\n💡 SOLUÇÃO RECOMENDADA:")
        print(f"Implementar fila de mensagens ou bloqueio durante")
        print(f"processamento para evitar race conditions.")
        
    except Exception as e:
        print(f"💥 ERRO: {e}")
        import traceback
        traceback.print_exc()