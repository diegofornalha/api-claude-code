#!/usr/bin/env python3
"""
🎯 EXEMPLO HELLO WORLD - Claude Code SDK Python

Este é o exemplo mais simples para começar a usar o SDK.
Ideal para primeiro contato e aprendizado básico.

COMO EXECUTAR:
    python examples/exemplo_hello_world.py

O QUE FAZ:
    - Faz uma pergunta simples ao Claude
    - Mostra a resposta
    - Exibe informações de uso (tokens, custo)
    - Demonstra o fluxo básico do SDK

REQUISITOS:
    - Claude Code instalado: npm install -g @anthropic-ai/claude-code
    - Python 3.10+
    - SDK instalado: pip install -e .
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar o SDK
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from src import query, AssistantMessage, TextBlock, ResultMessage

async def hello_world_example():
    """
    Exemplo básico: pergunta simples e mostra resposta
    """
    print("=" * 60)
    print("🤖 CLAUDE CODE SDK PYTHON - HELLO WORLD")
    print("=" * 60)
    
    # Pergunta simples para começar
    prompt = "Olá! Pode me dizer 'Olá, mundo!' em português?"
    
    print(f"\n🔍 Perguntando ao Claude:")
    print(f"   '{prompt}'")
    print("-" * 40)
    
    try:
        # Executa a query e processa cada mensagem
        async for message in query(prompt=prompt):
            
            if isinstance(message, AssistantMessage):
                # AssistantMessage contém a resposta do Claude
                print("\n📝 Resposta do Claude:")
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"   {block.text}")
                        
            elif isinstance(message, ResultMessage):
                # ResultMessage contém informações sobre o uso
                print("\n📊 Informações de Uso:")
                
                # Mostra tokens se disponível
                if hasattr(message, 'usage') and message.usage:
                    if hasattr(message.usage, 'input_tokens'):
                        print(f"   🎯 Tokens de entrada: {message.usage.input_tokens}")
                        print(f"   🎯 Tokens de saída: {message.usage.output_tokens}")
                    elif isinstance(message.usage, dict):
                        print(f"   🎯 Tokens de entrada: {message.usage.get('input_tokens', 0)}")
                        print(f"   🎯 Tokens de saída: {message.usage.get('output_tokens', 0)}")
                
                # Mostra custo se disponível
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    print(f"   💰 Custo total: ${message.total_cost_usd:.6f}")
        
        print("\n" + "=" * 60)
        print("✅ Exemplo executado com sucesso!")
        print("🎉 Você acabou de usar o Claude Code SDK Python!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
        print("\n💡 Dicas para resolver:")
        print("   1. Verifique se o Claude Code está instalado:")
        print("      npm install -g @anthropic-ai/claude-code")
        print("   2. Verifique se o SDK está instalado:")
        print("      pip install -e .")
        print("   3. Verifique se está no diretório correto")
        sys.exit(1)

async def exemplo_interativo():
    """
    Exemplo interativo: permite fazer perguntas personalizadas
    """
    print("\n" + "=" * 60)
    print("💬 MODO INTERATIVO")
    print("=" * 60)
    print("Digite suas perguntas (ou 'sair' para terminar):")
    print("-" * 40)
    
    while True:
        try:
            # Pega input do usuário
            user_input = input("\n👤 Você: ").strip()
            
            # Comandos de saída
            if user_input.lower() in ['sair', 'exit', 'quit', 'q']:
                print("👋 Até logo! Obrigado por usar o SDK!")
                break
            
            # Ignora input vazio
            if not user_input:
                continue
            
            print(f"\n🔍 Processando: '{user_input}'")
            print("-" * 40)
            
            # Executa a query
            async for message in query(prompt=user_input):
                if isinstance(message, AssistantMessage):
                    print("\n📝 Claude:")
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"   {block.text}")
                            
                elif isinstance(message, ResultMessage):
                    if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                        print(f"\n💰 Custo: ${message.total_cost_usd:.6f}")
            
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrompido pelo usuário!")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")

async def main():
    """
    Função principal que executa todos os exemplos
    """
    print("🚀 INICIANDO EXEMPLOS DO CLAUDE CODE SDK PYTHON")
    print("=" * 60)
    
    # Exemplo básico
    await hello_world_example()
    
    # Pergunta se quer continuar interativo
    try:
        resposta = input("\n💭 Quer continuar no modo interativo? (s/n): ").strip().lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            await exemplo_interativo()
    except KeyboardInterrupt:
        print("\n👋 Até logo!")
    
    print("\n🎯 RESUMO DO QUE APRENDEU:")
    print("   ✅ Como importar o SDK")
    print("   ✅ Como fazer uma query simples")
    print("   ✅ Como processar respostas")
    print("   ✅ Como usar o modo interativo")
    print("   ✅ Como tratar erros básicos")
    print("\n🚀 Próximo passo: experimente outros exemplos em examples/")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Programa interrompido!")
        sys.exit(0)
