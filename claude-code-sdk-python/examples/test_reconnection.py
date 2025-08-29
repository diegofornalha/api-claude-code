#!/usr/bin/env python3
"""
🔄 Teste de Reconexão Automática
Script para verificar se a reconexão funciona corretamente
"""

import asyncio
import sys
import os

# Adiciona o diretório src ao path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def test_reconnection():
    """Testa reconexão automática"""
    print("🔄 Iniciando teste de reconexão...")
    
    client = ClaudeSDKClient()
    
    try:
        # Primeira conexão
        print("1️⃣ Estabelecendo primeira conexão...")
        await client.connect()
        print("✅ Conectado com sucesso!")
        
        # Primeira query
        print("2️⃣ Enviando primeira query...")
        await client.query("Teste de conexão inicial")
        
        response_count = 0
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                response_count += 1
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Resposta recebida: {block.text[:100]}...")
        
        print(f"✅ Primeira query completada ({response_count} mensagens)")
        
        # Desconecta propositalmente
        print("3️⃣ Desconectando propositalmente...")
        await client.disconnect()
        print("🔌 Desconectado")
        
        # Tenta reconectar automaticamente
        print("4️⃣ Tentando reconexão...")
        await client.connect()
        print("✅ Reconectado com sucesso!")
        
        # Segunda query após reconexão
        print("5️⃣ Enviando segunda query após reconexão...")
        await client.query("Teste após reconexão - você ainda está funcionando?")
        
        response_count = 0
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                response_count += 1
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Resposta após reconexão: {block.text[:100]}...")
        
        print(f"✅ Segunda query completada ({response_count} mensagens)")
        print("🎉 Teste de reconexão SUCESSO!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            await client.disconnect()
            print("🔌 Cliente desconectado no final")
        except:
            pass

if __name__ == "__main__":
    print("🚀 Iniciando teste de reconexão do Claude SDK...")
    asyncio.run(test_reconnection())