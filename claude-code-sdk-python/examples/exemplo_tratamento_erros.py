#!/usr/bin/env python3
"""
⚠️ EXEMPLO TRATAMENTO DE ERROS - Claude Code SDK Python

Este exemplo demonstra como tratar diferentes tipos de erro do SDK:
- Erros de conexão
- Erros de permissão
- Erros de configuração
- Implementação de retry automático
- Logging de erros para debug

COMO EXECUTAR:
    python examples/exemplo_tratamento_erros.py

O QUE FAZ:
    - Demonstra diferentes tipos de erro do SDK
    - Implementa tratamento robusto de exceções
    - Mostra como lidar com falhas de conexão
    - Exibe mensagens de erro amigáveis
    - Implementa retry automático para falhas temporárias

REQUISITOS:
    - Claude Code instalado: npm install -g @anthropic-ai/claude-code
    - Python 3.10+
    - SDK instalado: pip install -e .
"""

import asyncio
import sys
import time
import logging
from pathlib import Path

# Adiciona o diretório src ao path para importar o SDK
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from src import (
    query, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage,
    ClaudeSDKError, CLINotFoundError, CLIConnectionError, ProcessError
)

# Configura logging para debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def exemplo_erro_cli_nao_encontrado():
    """
    Exemplo de tratamento para CLI não encontrado
    """
    print("=" * 60)
    print("❌ EXEMPLO 1: CLI NÃO ENCONTRADO")
    print("=" * 60)
    
    try:
        # Tenta fazer uma query (pode falhar se CLI não estiver instalado)
        prompt = "Olá, como você está?"
        
        print(f"🔍 Tentando query: '{prompt}'")
        print("-" * 40)
        
        async for message in query(prompt=prompt):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
        
        print("✅ Query executada com sucesso!")
        
    except CLINotFoundError as e:
        print(f"❌ Erro: CLI do Claude Code não encontrado")
        print(f"💡 Solução: npm install -g @anthropic-ai/claude-code")
        print(f"🔍 Detalhes: {e}")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

async def exemplo_erro_conexao():
    """
    Exemplo de tratamento para erros de conexão
    """
    print("\n" + "=" * 60)
    print("🌐 EXEMPLO 2: ERRO DE CONEXÃO")
    print("=" * 60)
    
    try:
        # Tenta fazer uma query que pode falhar por conexão
        prompt = "Me conte uma história curta"
        
        print(f"🔍 Tentando query: '{prompt}'")
        print("-" * 40)
        
        async for message in query(prompt=prompt):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
        
        print("✅ Query executada com sucesso!")
        
    except CLIConnectionError as e:
        print(f"❌ Erro de conexão: {e}")
        print("💡 Possíveis causas:")
        print("   - Problemas de rede")
        print("   - Claude Code não está rodando")
        print("   - Firewall bloqueando conexão")
        print("🔍 Detalhes técnicos:", e)
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

async def exemplo_erro_processo():
    """
    Exemplo de tratamento para erros de processo
    """
    print("\n" + "=" * 60)
    print("⚙️ EXEMPLO 3: ERRO DE PROCESSO")
    print("=" * 60)
    
    try:
        # Tenta fazer uma query que pode falhar por processo
        prompt = "Execute o comando 'invalid_command' que não existe"
        
        print(f"🔍 Tentando query: '{prompt}'")
        print("-" * 40)
        
        async for message in query(prompt=prompt):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
        
        print("✅ Query executada com sucesso!")
        
    except ProcessError as e:
        print(f"❌ Erro de processo: {e}")
        print(f"💡 Código de saída: {e.exit_code}")
        print("🔍 Possíveis causas:")
        print("   - Comando inválido")
        print("   - Permissões insuficientes")
        print("   - Ferramenta não disponível")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

async def exemplo_retry_automatico():
    """
    Exemplo de retry automático para falhas temporárias
    """
    print("\n" + "=" * 60)
    print("🔄 EXEMPLO 4: RETRY AUTOMÁTICO")
    print("=" * 60)
    
    max_retries = 3
    retry_delay = 2  # segundos
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Tentativa {attempt + 1} de {max_retries}")
            
            prompt = "Diga apenas 'Olá, retry funcionando!'"
            
            print(f"🔍 Query: '{prompt}'")
            print("-" * 40)
            
            async for message in query(prompt=prompt):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"📝 Claude: {block.text}")
            
            print("✅ Query executada com sucesso na primeira tentativa!")
            break
            
        except (CLIConnectionError, ProcessError) as e:
            print(f"❌ Tentativa {attempt + 1} falhou: {e}")
            
            if attempt < max_retries - 1:
                print(f"⏳ Aguardando {retry_delay} segundos antes da próxima tentativa...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Backoff exponencial
            else:
                print("💥 Todas as tentativas falharam")
                
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            break

async def exemplo_logging_erros():
    """
    Exemplo de logging de erros para debug
    """
    print("\n" + "=" * 60)
    print("📝 EXEMPLO 5: LOGGING DE ERROS")
    print("=" * 60)
    
    try:
        # Configura logging detalhado
        logger.info("Iniciando exemplo de logging")
        
        prompt = "Me diga uma piada curta"
        
        print(f"🔍 Query: '{prompt}'")
        print("-" * 40)
        
        logger.info(f"Enviando query: {prompt}")
        
        async for message in query(prompt=prompt):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
                        logger.info(f"Resposta recebida: {block.text[:50]}...")
            elif isinstance(message, ResultMessage):
                logger.info("ResultMessage recebida")
        
        logger.info("Query executada com sucesso")
        print("✅ Query executada com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante execução: {e}", exc_info=True)
        print(f"❌ Erro: {e}")
        print("📝 Verifique os logs para mais detalhes")

async def exemplo_tratamento_robusto():
    """
    Exemplo de tratamento robusto combinando todas as técnicas
    """
    print("\n" + "=" * 60)
    print("🛡️ EXEMPLO 6: TRATAMENTO ROBUSTO COMPLETO")
    print("=" * 60)
    
    def handle_error(error, context=""):
        """Função centralizada para tratamento de erros"""
        error_type = type(error).__name__
        
        print(f"❌ Erro ({error_type}): {error}")
        
        if isinstance(error, CLINotFoundError):
            print("💡 Solução: npm install -g @anthropic-ai/claude-code")
        elif isinstance(error, CLIConnectionError):
            print("💡 Solução: Verifique conexão de rede e status do Claude Code")
        elif isinstance(error, ProcessError):
            print(f"💡 Solução: Verifique permissões e comandos executados")
        else:
            print("💡 Solução: Erro inesperado, verifique logs para mais detalhes")
        
        logger.error(f"Erro em {context}: {error}", exc_info=True)
    
    try:
        logger.info("Iniciando exemplo de tratamento robusto")
        
        prompt = "Me explique o que é programação assíncrona em Python"
        
        print(f"🔍 Query: '{prompt}'")
        print("-" * 40)
        
        async for message in query(prompt=prompt):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"📝 Claude: {block.text}")
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    print(f"\n💰 Custo: ${message.total_cost_usd:.6f}")
        
        print("✅ Query executada com sucesso!")
        logger.info("Exemplo de tratamento robusto executado com sucesso")
        
    except CLINotFoundError as e:
        handle_error(e, "CLI não encontrado")
    except CLIConnectionError as e:
        handle_error(e, "Problema de conexão")
    except ProcessError as e:
        handle_error(e, "Erro de processo")
    except Exception as e:
        handle_error(e, "Erro inesperado")

async def main():
    """
    Função principal que executa todos os exemplos
    """
    print("⚠️ DEMONSTRAÇÃO DO TRATAMENTO DE ERROS DO CLAUDE CODE SDK PYTHON")
    print("=" * 60)
    
    try:
        # Executa todos os exemplos
        await exemplo_erro_cli_nao_encontrado()
        await exemplo_erro_conexao()
        await exemplo_erro_processo()
        await exemplo_retry_automatico()
        await exemplo_logging_erros()
        await exemplo_tratamento_robusto()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("=" * 60)
        
        print("\n📚 O QUE VOCÊ APRENDEU:")
        print("   ✅ Como identificar diferentes tipos de erro")
        print("   ✅ Como tratar exceções específicas do SDK")
        print("   ✅ Como implementar retry automático")
        print("   ✅ Como fazer logging para debug")
        print("   ✅ Como criar tratamento robusto de erros")
        print("   ✅ Como fornecer mensagens de erro amigáveis")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("   - Implemente retry em suas aplicações")
        print("   - Configure logging apropriado")
        print("   - Crie tratamento de erro personalizado")
        print("   - Teste cenários de falha")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Programa interrompido!")
        sys.exit(0)
