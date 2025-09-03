#!/usr/bin/env python3
"""
Claude Monitor - Monitora o diretório e FORÇA todos os arquivos para o arquivo correto.
"""

import os
import sys
import time
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime

# ARQUIVO ÚNICO
FIXED_SESSION_ID = "81ee33cb-7da3-4597-9449-7831c9fdd2cc"
SESSIONS_DIR = Path.home() / ".claude" / "projects" / "-home-suthub--claude-api-claude-code-app-claude-code-sdk-python-wrappers-cli"
FIXED_FILE = SESSIONS_DIR / f"{FIXED_SESSION_ID}.jsonl"

# Adiciona SDK ao path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage

class DirectoryMonitor:
    """Monitora o diretório e impede criação de novos arquivos."""
    
    def __init__(self):
        self.running = True
        self.intercepted = []
        
    def monitor_loop(self):
        """Loop que monitora e remove arquivos indevidos."""
        # Silencioso - opera em background sem mensagens
        
        while self.running:
            try:
                # Lista todos os arquivos JSONL
                for file in SESSIONS_DIR.glob("*.jsonl"):
                    # Se NÃO é o arquivo correto
                    if file.name != f"{FIXED_SESSION_ID}.jsonl":
                        # Silencioso - não mostra detecção
                        
                        # Lê o conteúdo do arquivo indevido
                        try:
                            with open(file, 'r') as f:
                                lines = f.readlines()
                            
                            # Adiciona ao arquivo correto
                            if lines:
                                with open(FIXED_FILE, 'a') as f:
                                    for line in lines:
                                        f.write(line)
                                pass  # Silencioso - não mostra movimento
                            
                            # Remove o arquivo indevido
                            file.unlink()
                            # Silencioso - não mostra remoção
                            self.intercepted.append(file.name)
                            
                        except Exception as e:
                            print(f"❌ Erro ao processar {file.name}: {e}")
                
            except Exception as e:
                print(f"❌ Erro no monitor: {e}")
            
            time.sleep(0.1)  # Verifica a cada 100ms
    
    def start(self):
        """Inicia o monitor em thread separada."""
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Para o monitor."""
        self.running = False

async def run_monitored_chat():
    """Chat com monitoramento ativo."""
    
    # Inicia o monitor
    monitor = DirectoryMonitor()
    monitor.start()
    
    # Conta mensagens antes
    count_before = 0
    if FIXED_FILE.exists():
        with open(FIXED_FILE, 'r') as f:
            count_before = sum(1 for _ in f)
    
    print("\n" + "="*60)
    print("💬 Chat com sessão persistente")
    print(f"📁 Arquivo: {FIXED_FILE.name}")
    print(f"📊 Histórico: {count_before} mensagens")
    print("="*60)
    
    # Cria cliente
    options = ClaudeCodeOptions()
    options.session_id = FIXED_SESSION_ID
    
    client = ClaudeSDKClient(options=options)
    
    await client.connect()
    print("✅ Conectado")
    
    print("💬 Digite sua mensagem (ou 'sair')\n")
    print("-"*60)
    
    conversation_count = 0
    
    while True:
        print(f"\n👤 Você: ", end="", flush=True)
        
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
        conversation_count += 1
        
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
        
        # Pequena pausa para o monitor processar
        await asyncio.sleep(0.2)
    
    await client.disconnect()
    monitor.stop()
    
    # Conta mensagens depois
    count_after = 0
    if FIXED_FILE.exists():
        with open(FIXED_FILE, 'r') as f:
            count_after = sum(1 for _ in f)
    
    print("\n" + "="*60)
    print(f"💬 Chat finalizado")
    print(f"📊 Total de mensagens: {count_after}")
    print(f"💾 Histórico salvo em: {FIXED_FILE.name}")
    print("="*60)

def main():
    # Inicia silenciosamente
    
    try:
        asyncio.run(run_monitored_chat())
    except KeyboardInterrupt:
        print("\n👋 Interrompido")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()