#!/usr/bin/env python3
"""
Claude Interceptor - Intercepta e redireciona TODAS as escritas para o arquivo correto.
"""

import sys
import os
import json
import builtins
from pathlib import Path
from datetime import datetime

# ARQUIVO ÚNICO QUE DEVE SER USADO
FIXED_SESSION_ID = "50468c19-5559-477e-ae1c-7868c067846c"
SESSIONS_DIR = Path.home() / ".claude" / "projects" / "-home-suthub--claude-api-claude-code-app-claude-code-sdk-python-wrappers-cli"
FIXED_FILE = SESSIONS_DIR / f"{FIXED_SESSION_ID}.jsonl"

# Salva a função open original
_original_open = builtins.open

def intercepted_open(file, mode='r', *args, **kwargs):
    """Intercepta abertura de arquivos e redireciona para o arquivo correto."""
    
    file_str = str(file)
    
    # Se está tentando criar/escrever em um arquivo JSONL no diretório de sessões
    if ('w' in mode or 'a' in mode) and '.jsonl' in file_str and str(SESSIONS_DIR) in file_str:
        # Se NÃO é o arquivo correto
        if not file_str.endswith(f"{FIXED_SESSION_ID}.jsonl"):
            print(f"\n⚠️ INTERCEPTADO: Tentativa de criar {Path(file_str).name}")
            print(f"✅ REDIRECIONANDO para: {FIXED_FILE.name}")
            # FORÇA o uso do arquivo correto
            return _original_open(FIXED_FILE, mode, *args, **kwargs)
    
    # Caso contrário, usa o open normal
    return _original_open(file, mode, *args, **kwargs)

# SUBSTITUI a função open globalmente
builtins.open = intercepted_open

# Agora importa o SDK (com open já interceptado)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import asyncio
from src import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage

async def run_intercepted_chat():
    """Chat com interceptação de arquivos."""
    
    print("\n" + "="*60)
    print("🛡️ CLAUDE INTERCEPTOR - REDIRECIONAMENTO FORÇADO")
    print("="*60)
    print(f"📌 ÚNICO arquivo permitido: {FIXED_SESSION_ID}")
    print(f"📄 Local: {FIXED_FILE.name}")
    
    # Conta mensagens antes
    count_before = 0
    if FIXED_FILE.exists():
        with _original_open(FIXED_FILE, 'r') as f:
            count_before = sum(1 for _ in f)
    
    print(f"📊 Mensagens antes: {count_before}")
    print("="*60)
    
    # Cria cliente (qualquer tentativa de criar novo arquivo será interceptada)
    options = ClaudeCodeOptions()
    options.session_id = FIXED_SESSION_ID
    
    client = ClaudeSDKClient(options=options)
    
    await client.connect()
    print("✅ Conectado (com interceptação ativa)")
    
    print("\n💬 Chat (digite 'sair' para terminar)")
    print("-"*60)
    
    while True:
        print("\n👤 Você: ", end="", flush=True)
        
        try:
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ['sair', 's']:
            break
        
        # Envia mensagem
        await client.query(user_input)
        
        # Recebe resposta
        print("🤖 Claude: ", end="", flush=True)
        
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
            elif isinstance(msg, ResultMessage):
                break
        
        print()
    
    await client.disconnect()
    
    # Conta mensagens depois
    count_after = 0
    if FIXED_FILE.exists():
        with _original_open(FIXED_FILE, 'r') as f:
            count_after = sum(1 for _ in f)
    
    print("\n" + "="*60)
    print(f"📊 Mensagens antes: {count_before}")
    print(f"📊 Mensagens depois: {count_after}")
    print(f"✅ Adicionadas: {count_after - count_before}")
    print(f"💾 TUDO em: {FIXED_FILE.name}")
    
    # Verifica se existem outros arquivos
    other_files = []
    for f in SESSIONS_DIR.glob("*.jsonl"):
        if f.name != f"{FIXED_SESSION_ID}.jsonl":
            other_files.append(f.name)
    
    if other_files:
        print(f"\n❌ FALHA: {len(other_files)} outros arquivos encontrados!")
        for f in other_files[:3]:
            print(f"  - {f}")
    else:
        print("\n✅✅✅ SUCESSO TOTAL: Apenas o arquivo correto existe!")
    
    print("="*60)

def main():
    print("\n🛡️ Interceptador ativado!")
    print(f"📌 Todas as escritas para {SESSIONS_DIR.name}")
    print(f"    serão redirecionadas para: {FIXED_FILE.name}")
    
    try:
        asyncio.run(run_intercepted_chat())
    except KeyboardInterrupt:
        print("\n👋 Interrompido")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()