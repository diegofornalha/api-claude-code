#!/usr/bin/env python3
"""Demonstração simples do Claude Code SDK Python"""

import asyncio
import sys
from pathlib import Path

# Adiciona src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import query, AssistantMessage, TextBlock, ResultMessage

async def main():
    """Exemplo básico de uso do SDK"""
    
    print("=" * 60)
    print("🎯 DEMONSTRAÇÃO DO CLAUDE CODE SDK PYTHON")
    print("=" * 60)
    
    perguntas = [
        "Qual é o resultado de 10 + 15?",
        "Me diga uma piada curta",
        "Como fazer um bolo simples em 3 passos?"
    ]
    
    for pergunta in perguntas:
        print(f"\n❓ Pergunta: {pergunta}")
        print("-" * 40)
        
        async for message in query(prompt=pergunta):
            if isinstance(message, AssistantMessage):
                print("💬 Resposta:")
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"   {block.text}")
                        
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    print(f"\n💰 Custo: ${message.total_cost_usd:.6f}")
    
    print("\n" + "=" * 60)
    print("✅ Demonstração concluída com sucesso!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())