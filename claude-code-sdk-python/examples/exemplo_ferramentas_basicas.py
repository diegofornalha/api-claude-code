#!/usr/bin/env python3
"""
🔧 EXEMPLO FERRAMENTAS BÁSICAS - Claude Code SDK Python

Este exemplo demonstra como usar as ferramentas básicas do SDK:
- Read: Para ler arquivos
- Write: Para escrever arquivos  
- Bash: Para executar comandos do sistema

COMO EXECUTAR:
    python examples/exemplo_ferramentas_basicas.py

O QUE FAZ:
    - Demonstra uso das ferramentas Read, Write e Bash
    - Mostra como configurar permissões de ferramentas
    - Implementa operações básicas de arquivo
    - Exibe resultados de comandos bash
    - Trata erros de permissão e execução

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

from src import query, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage

async def exemplo_ferramenta_read():
    """
    Exemplo usando a ferramenta Read para ler arquivos
    """
    print("=" * 60)
    print("📖 EXEMPLO 1: FERRAMENTA READ")
    print("=" * 60)
    
    # Configura opções permitindo apenas leitura
    options = ClaudeCodeOptions(
        allowed_tools=["Read"],
        system_prompt="Você é um assistente especializado em leitura de arquivos. Use apenas a ferramenta Read."
    )
    
    prompt = "Leia o arquivo pyproject.toml e me diga qual é a versão do projeto e suas dependências principais"
    
    print(f"🔍 Perguntando: '{prompt}'")
    print("-" * 40)
    
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    print(f"\n💰 Custo: ${message.total_cost_usd:.6f}")
        
        print("\n✅ Exemplo Read executado com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

async def exemplo_ferramenta_write():
    """
    Exemplo usando a ferramenta Write para criar arquivos
    """
    print("\n" + "=" * 60)
    print("✍️ EXEMPLO 2: FERRAMENTA WRITE")
    print("=" * 60)
    
    # Configura opções permitindo apenas escrita
    options = ClaudeCodeOptions(
        allowed_tools=["Write"],
        system_prompt="Você é um assistente especializado em criação de arquivos. Use apenas a ferramenta Write."
    )
    
    prompt = "Crie um arquivo chamado 'exemplo_ferramentas.txt' com o conteúdo: 'Este arquivo foi criado pelo Claude Code SDK Python usando a ferramenta Write. Data: [data atual]'"
    
    print(f"🔍 Perguntando: '{prompt}'")
    print("-" * 40)
    
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    print(f"\n💰 Custo: ${message.total_cost_usd:.6f}")
        
        print("\n✅ Exemplo Write executado com sucesso!")
        
        # Verifica se o arquivo foi criado
        arquivo_criado = Path("exemplo_ferramentas.txt")
        if arquivo_criado.exists():
            print(f"📁 Arquivo criado: {arquivo_criado}")
            print(f"📏 Tamanho: {arquivo_criado.stat().st_size} bytes")
        else:
            print("⚠️ Arquivo não foi criado")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

async def exemplo_ferramenta_bash():
    """
    Exemplo usando a ferramenta Bash para executar comandos
    """
    print("\n" + "=" * 60)
    print("💻 EXEMPLO 3: FERRAMENTA BASH")
    print("=" * 60)
    
    # Configura opções permitindo apenas Bash
    options = ClaudeCodeOptions(
        allowed_tools=["Bash"],
        system_prompt="Você é um assistente especializado em comandos bash. Use apenas a ferramenta Bash. Execute comandos simples e seguros."
    )
    
    prompt = "Execute o comando 'ls -la' para listar os arquivos do diretório atual e depois execute 'pwd' para mostrar o diretório atual"
    
    print(f"🔍 Perguntando: '{prompt}'")
    print("-" * 40)
    
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    print(f"\n💰 Custo: ${message.total_cost_usd:.6f}")
        
        print("\n✅ Exemplo Bash executado com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

async def exemplo_ferramentas_combinadas():
    """
    Exemplo combinando múltiplas ferramentas
    """
    print("\n" + "=" * 60)
    print("🔄 EXEMPLO 4: FERRAMENTAS COMBINADAS")
    print("=" * 60)
    
    # Configura opções permitindo múltiplas ferramentas
    options = ClaudeCodeOptions(
        allowed_tools=["Read", "Write", "Bash"],
        system_prompt="Você é um assistente que pode ler, escrever e executar comandos. Use as ferramentas apropriadas para cada tarefa."
    )
    
    prompt = "Leia o arquivo 'exemplo_ferramentas.txt' que criamos, adicione uma nova linha com 'Ferramentas combinadas funcionando!' e execute 'wc -l exemplo_ferramentas.txt' para contar as linhas"
    
    print(f"🔍 Perguntando: '{prompt}'")
    print("-" * 40)
    
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    print(f"\n💰 Custo: ${message.total_cost_usd:.6f}")
        
        print("\n✅ Exemplo de ferramentas combinadas executado com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

async def exemplo_tratamento_erros():
    """
    Exemplo de tratamento de erros com ferramentas
    """
    print("\n" + "=" * 60)
    print("⚠️ EXEMPLO 5: TRATAMENTO DE ERROS")
    print("=" * 60)
    
    # Configura opções com ferramentas restritas
    options = ClaudeCodeOptions(
        allowed_tools=["Read"],
        system_prompt="Você é um assistente que só pode ler arquivos. Se for solicitado para escrever ou executar comandos, explique que não tem permissão."
    )
    
    prompt = "Tente criar um arquivo chamado 'teste.txt' e executar o comando 'ls -la'"
    
    print(f"🔍 Perguntando: '{prompt}'")
    print("-" * 40)
    
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    print(f"\n💰 Custo: ${message.total_cost_usd:.6f}")
        
        print("\n✅ Exemplo de tratamento de erros executado com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

async def main():
    """
    Função principal que executa todos os exemplos
    """
    print("🔧 DEMONSTRAÇÃO DAS FERRAMENTAS BÁSICAS DO CLAUDE CODE SDK PYTHON")
    print("=" * 60)
    
    try:
        # Executa todos os exemplos
        await exemplo_ferramenta_read()
        await exemplo_ferramenta_write()
        await exemplo_ferramenta_bash()
        await exemplo_ferramentas_combinadas()
        await exemplo_tratamento_erros()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("=" * 60)
        
        print("\n📚 O QUE VOCÊ APRENDEU:")
        print("   ✅ Como configurar ferramentas permitidas")
        print("   ✅ Como usar a ferramenta Read para arquivos")
        print("   ✅ Como usar a ferramenta Write para criar arquivos")
        print("   ✅ Como usar a ferramenta Bash para comandos")
        print("   ✅ Como combinar múltiplas ferramentas")
        print("   ✅ Como tratar erros de permissão")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("   - Experimente com outras ferramentas")
        print("   - Configure permissões personalizadas")
        print("   - Crie seus próprios exemplos")
        print("   - Explore a documentação completa")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        print("\n💡 Dicas para resolver:")
        print("   1. Verifique se o Claude Code está instalado")
        print("   2. Verifique se o SDK está instalado")
        print("   3. Verifique permissões de arquivo")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Programa interrompido!")
        sys.exit(0)
