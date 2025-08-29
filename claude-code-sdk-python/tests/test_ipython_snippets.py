#!/usr/bin/env python3
"""Executa os principais snippets do IPython como script Python."""

import sys
import os
import asyncio

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import (
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
    ResultMessage,
    ClaudeCodeOptions
)


async def basic_streaming_example():
    """Exemplo básico de streaming."""
    print("=== EXEMPLO BÁSICO DE STREAMING ===\n")
    
    async with ClaudeSDKClient() as client:
        print("User: What is 2+2?")
        await client.query("What is 2+2?")
        
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
    print("\n" + "="*50 + "\n")


async def multi_turn_example():
    """Exemplo de conversação com múltiplas interações."""
    print("=== EXEMPLO DE MÚLTIPLAS INTERAÇÕES ===\n")
    
    async with ClaudeSDKClient() as client:
        async def send_and_receive(prompt):
            print(f"User: {prompt}")
            await client.query(prompt)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")
        
        await send_and_receive("Conte uma piada curta")
        print("\n---\n")
        await send_and_receive("Agora me conte um fato interessante")
    
    print("\n" + "="*50 + "\n")


async def persistent_client_example():
    """Cliente persistente para múltiplas perguntas."""
    print("=== EXEMPLO DE CLIENTE PERSISTENTE ===\n")
    
    # Cria cliente
    client = ClaudeSDKClient()
    await client.connect()
    
    # Helper para obter resposta
    async def get_response():
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
    
    # Usa múltiplas vezes
    print("User: Quanto é 2+2?")
    await client.query("Quanto é 2+2?")
    await get_response()
    print()
    
    print("User: Quanto é 10*10?")
    await client.query("Quanto é 10*10?")
    await get_response()
    print()
    
    print("User: Quanto é a raiz quadrada de 144?")
    await client.query("Quanto é a raiz quadrada de 144?")
    await get_response()
    
    # Desconecta quando terminar
    await client.disconnect()
    
    print("\n" + "="*50 + "\n")


async def with_options_example():
    """Exemplo usando opções personalizadas."""
    print("=== EXEMPLO COM OPÇÕES PERSONALIZADAS ===\n")
    
    options = ClaudeCodeOptions(
        system_prompt="Você é um assistente que responde de forma simples e direta.",
        max_turns=1,
    )
    
    async with ClaudeSDKClient(options=options) as client:
        print("User: O que é Python em uma frase?")
        await client.query("O que é Python em uma frase?")
        
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
    
    print("\n" + "="*50 + "\n")


async def collecting_messages_example():
    """Coletando todas as mensagens em uma lista."""
    print("=== EXEMPLO COLETANDO MENSAGENS ===\n")
    
    async with ClaudeSDKClient() as client:
        print("User: Quais são as cores primárias?")
        await client.query("Quais são as cores primárias?")
        
        # Coleta todas as mensagens em uma lista
        messages = [msg async for msg in client.receive_response()]
        
        # Processa depois
        for msg in messages:
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"Total de mensagens: {len(messages)}")
    
    print("\n" + "="*50 + "\n")


async def main():
    """Executa todos os exemplos."""
    print("\n" + "="*70)
    print(" DEMONSTRAÇÃO DOS SNIPPETS DO IPYTHON ")
    print("="*70 + "\n")
    
    # Executa cada exemplo
    await basic_streaming_example()
    await multi_turn_example()
    await persistent_client_example()
    await with_options_example()
    await collecting_messages_example()
    
    print("\n✅ TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!\n")


if __name__ == "__main__":
    asyncio.run(main())