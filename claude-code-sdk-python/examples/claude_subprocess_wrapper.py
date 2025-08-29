#!/usr/bin/env python3
"""
🔧 Claude Subprocess Wrapper - Interface 100% síncrona
Usa subprocess diretamente com o CLI para evitar problemas de asyncio
"""

import subprocess
import os
import tempfile
import re
import sys
from typing import Dict, Optional

def query_claude_sync(prompt: str, timeout: int = 120) -> Dict:
    """
    Executa query síncrona ao Claude via subprocess
    
    Args:
        prompt: Pergunta/comando para o Claude
        timeout: Timeout em segundos (padrão 120s)
    
    Returns:
        Dict com resultado da query
    """
    try:
        # Caminho para o módulo principal
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Cria script temporário que executa a query
        script_content = f'''#!/usr/bin/env python3
import sys
import os
import asyncio

# Adiciona o diretório src ao path
parent_dir = "{module_path}"
sys.path.insert(0, parent_dir)

from src import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def query_and_exit():
    """Executa query e sai"""
    client = ClaudeSDKClient()
    try:
        await client.connect()
        await client.query("{prompt.replace('"', '\\"')}")
        
        response_content = []
        usage_info = None
        cost_info = None
        
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_content.append(block.text)
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'usage') and message.usage:
                    usage_info = message.usage
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    cost_info = message.total_cost_usd
        
        # Imprime resultado formatado
        content = "\\n".join(response_content)
        print("CONTENT_START")
        print(content)
        print("CONTENT_END")
        
        if usage_info:
            if hasattr(usage_info, 'input_tokens'):
                print(f"TOKENS_{{usage_info.input_tokens or 0}}_{{usage_info.output_tokens or 0}}")
            elif isinstance(usage_info, dict):
                print(f"TOKENS_{{usage_info.get('input_tokens', 0)}}_{{usage_info.get('output_tokens', 0)}}")
        
        if cost_info:
            print(f"COST_{{{cost_info}}}")
            
    except Exception as e:
        print(f"ERROR_{{{str(e)}}}")
        sys.exit(1)
    finally:
        try:
            await client.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(query_and_exit())
'''
        
        # Cria arquivo temporário com o script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
            temp_script.write(script_content)
            temp_script_path = temp_script.name
        
        try:
            # Executa o script temporário
            result = subprocess.run([
                sys.executable, temp_script_path
            ], 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            cwd=module_path
            )
            
            if result.returncode == 0:
                # Processa saída
                output_lines = result.stdout.strip().split('\n')
                
                # Extrai conteúdo
                content_start = content_end = -1
                for i, line in enumerate(output_lines):
                    if line == "CONTENT_START":
                        content_start = i + 1
                    elif line == "CONTENT_END":
                        content_end = i
                        break
                
                if content_start != -1 and content_end != -1:
                    content = '\n'.join(output_lines[content_start:content_end])
                else:
                    content = result.stdout.strip()
                
                # Extrai tokens
                input_tokens = output_tokens = 0
                for line in output_lines:
                    if line.startswith("TOKENS_"):
                        token_match = re.search(r'TOKENS_(\d+)_(\d+)', line)
                        if token_match:
                            input_tokens = int(token_match.group(1))
                            output_tokens = int(token_match.group(2))
                
                # Extrai custo
                cost = 0.0
                for line in output_lines:
                    if line.startswith("COST_"):
                        cost_match = re.search(r'COST_\{([0-9.]+)\}', line)
                        if cost_match:
                            cost = float(cost_match.group(1))
                
                return {
                    "success": True,
                    "content": content,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": cost
                }
            else:
                # Processa erro
                error_msg = result.stderr.strip()
                
                # Extrai erro formatado
                if "ERROR_" in result.stdout:
                    for line in result.stdout.split('\n'):
                        if line.startswith("ERROR_"):
                            error_match = re.search(r'ERROR_\{(.+)\}', line)
                            if error_match:
                                error_msg = error_match.group(1)
                
                return {
                    "success": False,
                    "error": error_msg or "Erro desconhecido",
                    "return_code": result.returncode
                }
        
        finally:
            # Remove arquivo temporário
            try:
                os.unlink(temp_script_path)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Timeout: Claude demorou mais de {timeout} segundos para responder"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro inesperado: {str(e)}"
        }

# Função compatível com o wrapper anterior
def query_claude(prompt: str) -> Dict:
    """Interface compatível para query síncrona"""
    result = query_claude_sync(prompt)
    
    if result["success"]:
        return {
            "success": True,
            "content": result["content"],
            "usage": {
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"]
            } if result.get("input_tokens") else None,
            "cost": result.get("cost")
        }
    else:
        return {
            "success": False,
            "error": result["error"]
        }

def disconnect_claude():
    """Função de compatibilidade - não faz nada pois cada query é independente"""
    return {"success": True}

if __name__ == "__main__":
    # Teste básico
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        result = query_claude_sync(prompt)
        
        if result["success"]:
            print(result["content"])
            
            if result["input_tokens"] > 0 or result["output_tokens"] > 0:
                print(f"\n[Tokens: {result['input_tokens']}↑ {result['output_tokens']}↓]", end="")
            
            if result["cost"] > 0:
                print(f" [Custo: ${result['cost']:.6f}]")
        else:
            print(f"Erro: {result['error']}")
            sys.exit(1)
    else:
        print("Uso: python claude_subprocess_wrapper.py 'sua pergunta'")
        sys.exit(1)