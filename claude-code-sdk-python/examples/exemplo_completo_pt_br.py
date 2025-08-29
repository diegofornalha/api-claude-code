#!/usr/bin/env python3
"""Exemplo simples mostrando como usar o SDK"""

import sys
import asyncio
from pathlib import Path

# Adiciona o caminho do SDK corretamente
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Importa os módulos corretos
from src import query, AssistantMessage, TextBlock, ResultMessage

async def exemplo_basico():
    """Exemplo básico - pergunta simples"""
    print("=" * 50)
    print("EXEMPLO 1: Pergunta Básica")
    print("=" * 50)
    print("Perguntando: 'Quanto é 2 + 2?'\n")
    
    # Faz a query e processa a resposta
    async for message in query(prompt="Quanto é 2 + 2?"):
        if isinstance(message, AssistantMessage):
            # AssistantMessage contém a resposta do Claude
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"📝 Resposta do Claude: {block.text}")
        elif isinstance(message, ResultMessage):
            # ResultMessage contém informações sobre uso
            print(f"\n📊 Informações de uso:")
            print(f"   - Tokens entrada: {message.usage.input_tokens}")
            print(f"   - Tokens saída: {message.usage.output_tokens}")
            if message.total_cost_usd:
                print(f"   - Custo: ${message.total_cost_usd:.6f}")
    print("\n")

async def exemplo_com_opcoes():
    """Exemplo com opções personalizadas"""
    from src import ClaudeCodeOptions
    
    print("=" * 50)
    print("EXEMPLO 2: Com System Prompt Personalizado")
    print("=" * 50)
    
    # Define opções personalizadas
    options = ClaudeCodeOptions(
        system_prompt="Você é um assistente que responde sempre em português brasileiro e de forma bem simples.",
        max_turns=1  # Limita a 1 turno
    )
    
    print("System prompt: 'Responder em PT-BR de forma simples'")
    print("Perguntando: 'O que é Python?'\n")
    
    async for message in query(
        prompt="O que é Python?", 
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"📝 Resposta: {block.text}")
    print("\n")

async def exemplo_com_ferramentas():
    """Exemplo usando ferramentas"""
    from src import ClaudeCodeOptions
    
    print("=" * 50)
    print("EXEMPLO 3: Usando Ferramentas (Read)")
    print("=" * 50)
    
    options = ClaudeCodeOptions(
        allowed_tools=["Read"],  # Permite apenas leitura
        system_prompt="Você é um assistente especializado em arquivos."
    )
    
    print("Ferramentas permitidas: Read")
    print("Perguntando sobre o pyproject.toml\n")
    
    async for message in query(
        prompt="Leia o arquivo pyproject.toml e me diga qual é a versão do projeto",
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"📝 Claude: {block.text[:200]}...")  # Limita output
        elif isinstance(message, ResultMessage) and message.total_cost_usd:
            print(f"\n💰 Custo total: ${message.total_cost_usd:.4f}")

async def main():
    """Executa todos os exemplos"""
    print("\n🚀 DEMONSTRAÇÃO DO CLAUDE CODE SDK PYTHON\n")
    
    await exemplo_basico()
    await exemplo_com_opcoes()
    await exemplo_com_ferramentas()
    
    print("=" * 50)
    print("✅ Todos os exemplos executados com sucesso!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())