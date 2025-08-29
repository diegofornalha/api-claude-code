#!/usr/bin/env python3
"""
🚀 EXEMPLO MAIS SIMPLES POSSÍVEL - 3 LINHAS!
"""
import asyncio, sys
sys.path.insert(0, 'src')
from src import query

# Isso é tudo que você precisa! 🎉
asyncio.run(
    print(response.content[0].text) 
    async for response in query("Olá! Diga 'Oi mundo!'") 
    if hasattr(response, 'content')
)

# Versão expandida (mais legível):
async def main():
    async for msg in query("Quanto é 2 + 2?"):
        if hasattr(msg, 'content'):
            for block in msg.content:
                if hasattr(block, 'text'):
                    print(block.text)

if __name__ == "__main__":
    asyncio.run(main())