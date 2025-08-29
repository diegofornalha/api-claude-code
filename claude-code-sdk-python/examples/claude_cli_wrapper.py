#!/usr/bin/env python3
"""
🔧 Claude CLI Wrapper - Interface síncrona para Streamlit
Wrapper direto que usa o SDK sem conflitos de asyncio
"""

import asyncio
import sys
import os

# Adiciona o diretório src ao path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

class ClaudeCLIWrapper:
    """Wrapper síncrono para o Claude SDK"""
    
    def __init__(self):
        self.client = None
        self.connected = False
    
    async def _ensure_connected(self):
        """Garante que o cliente está conectado"""
        if not self.client:
            self.client = ClaudeSDKClient()
        
        if not self.connected:
            await self.client.connect()
            self.connected = True
    
    async def _query_async(self, prompt: str):
        """Executa query assíncrona"""
        await self._ensure_connected()
        
        # Envia a query
        await self.client.query(prompt)
        
        # Coleta a resposta
        response_content = []
        usage_info = None
        cost_info = None
        
        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_content.append(block.text)
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'usage') and message.usage:
                    usage_info = message.usage
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    cost_info = message.total_cost_usd
        
        return {
            "content": "\n".join(response_content),
            "usage": usage_info,
            "cost": cost_info
        }
    
    def query(self, prompt: str):
        """Interface síncrona para queries"""
        # Cria um novo loop de eventos para esta query
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(self._query_async(prompt))
            return result
        finally:
            # Não fecha o loop aqui para manter a conexão
            pass
    
    async def _disconnect_async(self):
        """Desconecta assincronamente"""
        if self.client and self.connected:
            await self.client.disconnect()
        self.connected = False
        self.client = None
    
    def disconnect(self):
        """Interface síncrona para desconectar"""
        if self.connected:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._disconnect_async())
            finally:
                loop.close()

# Instância global do wrapper
_wrapper = ClaudeCLIWrapper()

def query_claude(prompt: str):
    """Função simples para fazer query ao Claude"""
    try:
        result = _wrapper.query(prompt)
        return {
            "success": True,
            "content": result["content"],
            "usage": result["usage"],
            "cost": result["cost"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def disconnect_claude():
    """Função para desconectar o Claude"""
    try:
        _wrapper.disconnect()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Teste básico
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        result = query_claude(prompt)
        
        if result["success"]:
            print(result["content"])
            
            # Mostra métricas se disponível
            if result["usage"]:
                usage = result["usage"]
                if hasattr(usage, 'input_tokens'):
                    print(f"\n[Tokens: {usage.input_tokens}↑ {usage.output_tokens}↓]", end="")
                elif isinstance(usage, dict):
                    print(f"\n[Tokens: {usage.get('input_tokens', 0)}↑ {usage.get('output_tokens', 0)}↓]", end="")
            
            if result["cost"]:
                print(f" [Custo: ${result['cost']:.6f}]")
        else:
            print(f"Erro: {result['error']}")
            sys.exit(1)
    else:
        print("Uso: python claude_cli_wrapper.py 'sua pergunta'")
        sys.exit(1)