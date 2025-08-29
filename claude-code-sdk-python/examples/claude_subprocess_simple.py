#!/usr/bin/env python3
"""
🔧 Claude Subprocess Simple - Interface 100% síncrona e robusta
Cada query é independente, evitando problemas de estado
"""

import subprocess
import os
import tempfile
import re
import sys
import json
from typing import Dict

def query_claude(prompt: str, timeout: int = 120) -> Dict:
    """
    Executa query síncrona ao Claude via subprocess independente
    
    Args:
        prompt: Pergunta/comando para o Claude
        timeout: Timeout em segundos (padrão 120s)
    
    Returns:
        Dict com resultado da query
    """
    try:
        # Caminho para o módulo principal
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Cria arquivo temporário com o prompt (evita problemas de escape)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_prompt:
            temp_prompt.write(prompt)
            temp_prompt_path = temp_prompt.name
        
        # Script Python que executa uma query independente
        script_content = '''#!/usr/bin/env python3
import sys
import os
import asyncio
import json

# Adiciona o diretório src ao path
parent_dir = "{module_path}"
sys.path.insert(0, parent_dir)

from src import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def main():
    """Executa query independente"""
    # Lê prompt do arquivo
    with open("{prompt_file}", "r") as f:
        prompt = f.read().strip()
    
    client = ClaudeSDKClient()
    try:
        await client.connect()
        await client.query(prompt)
        
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
        
        # Constrói resultado
        result = {{
            "success": True,
            "content": "\\n".join(response_content),
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": 0.0
        }}
        
        if usage_info:
            if hasattr(usage_info, 'input_tokens'):
                result["input_tokens"] = usage_info.input_tokens or 0
                result["output_tokens"] = usage_info.output_tokens or 0
            elif isinstance(usage_info, dict):
                result["input_tokens"] = usage_info.get('input_tokens', 0)
                result["output_tokens"] = usage_info.get('output_tokens', 0)
        
        if cost_info:
            result["cost"] = cost_info
        
        # Imprime resultado como JSON
        print("RESULT_JSON_START")
        print(json.dumps(result))
        print("RESULT_JSON_END")
            
    except Exception as e:
        error_result = {{
            "success": False,
            "error": str(e)
        }}
        print("RESULT_JSON_START")
        print(json.dumps(error_result))
        print("RESULT_JSON_END")
        sys.exit(1)
    finally:
        try:
            await client.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
'''.format(module_path=module_path, prompt_file=temp_prompt_path.replace('\\', '\\\\'))
        
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
            cwd=module_path,
            env=dict(os.environ, PYTHONPATH=module_path)
            )
            
            if result.returncode == 0:
                # Extrai resultado JSON
                output_lines = result.stdout.split('\n')
                json_start = json_end = -1
                
                for i, line in enumerate(output_lines):
                    if line.strip() == "RESULT_JSON_START":
                        json_start = i + 1
                    elif line.strip() == "RESULT_JSON_END":
                        json_end = i
                        break
                
                if json_start != -1 and json_end != -1:
                    json_data = '\n'.join(output_lines[json_start:json_end])
                    return json.loads(json_data)
                else:
                    return {
                        "success": False,
                        "error": "Não foi possível extrair resultado JSON"
                    }
            else:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "Erro desconhecido",
                    "return_code": result.returncode
                }
        
        finally:
            # Remove arquivos temporários
            try:
                os.unlink(temp_script_path)
                os.unlink(temp_prompt_path)
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

def disconnect_claude():
    """Função de compatibilidade - não faz nada pois cada query é independente"""
    return {"success": True}

if __name__ == "__main__":
    # Teste básico
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        result = query_claude(prompt)
        
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
        print("Uso: python claude_subprocess_simple.py 'sua pergunta'")
        sys.exit(1)