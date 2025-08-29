#!/usr/bin/env python3
"""Teste simples do exemplo Trio."""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import trio
from src import (
    AssistantMessage,
    ClaudeCodeOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
)


def display_message(msg):
    """Display message helper."""
    if isinstance(msg, UserMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"User: {block.text}")
    elif isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"Claude: {block.text}")
    elif isinstance(msg, ResultMessage):
        print("Result ended")


async def simple_trio_example():
    """Exemplo simples com Trio."""
    print("=== Exemplo Simples com Trio ===\n")
    
    async with ClaudeSDKClient() as client:
        # Primeira pergunta
        print("User: Quanto é 10 + 20?")
        await client.query("Quanto é 10 + 20?")
        
        async for message in client.receive_response():
            display_message(message)
        print()
        
        # Segunda pergunta
        print("User: E quanto é 100 dividido por 4?")
        await client.query("E quanto é 100 dividido por 4?")
        
        async for message in client.receive_response():
            display_message(message)
        
        print("\nConversa completa!")


if __name__ == "__main__":
    trio.run(simple_trio_example)