#!/usr/bin/env python3
"""
🌐 EXEMPLO INTEGRAÇÃO COM WEB - Claude Code SDK Python

Este exemplo demonstra como integrar o SDK com frameworks web:
- Flask: Framework web simples
- FastAPI: Framework web moderno e rápido
- Endpoints que usam o SDK
- Cache de respostas para performance
- Métricas de performance

COMO EXECUTAR:
    python examples/exemplo_integracao_web.py

O QUE FAZ:
    - Demonstra integração com frameworks web
    - Implementa endpoints que usam o SDK
    - Mostra como processar requests HTTP
    - Implementa cache de respostas
    - Exibe métricas de performance

REQUISITOS:
    - Claude Code instalado: npm install -g @anthropic-ai/claude-code
    - Python 3.10+
    - SDK instalado: pip install -e .
    - Flask: pip install flask
    - FastAPI: pip install fastapi uvicorn
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any

# Adiciona o diretório src ao path para importar o SDK
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from src import query, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage

# Cache simples em memória
response_cache: Dict[str, Dict[str, Any]] = {}

async def process_claude_query(prompt: str, options: ClaudeCodeOptions = None) -> Dict[str, Any]:
    """
    Processa uma query do Claude e retorna resultado estruturado
    """
    start_time = time.time()
    
    try:
        response_text = ""
        usage_info = {}
        total_cost = 0.0
        
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
            elif isinstance(message, ResultMessage):
                if hasattr(message, 'usage') and message.usage:
                    if hasattr(message.usage, 'input_tokens'):
                        usage_info = {
                            'input_tokens': message.usage.input_tokens,
                            'output_tokens': message.usage.output_tokens
                        }
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    total_cost = message.total_cost_usd
        
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'response': response_text,
            'usage': usage_info,
            'total_cost_usd': total_cost,
            'processing_time_seconds': processing_time
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            'success': False,
            'error': str(e),
            'processing_time_seconds': processing_time
        }

def exemplo_flask_simples():
    """
    Exemplo simples usando Flask
    """
    try:
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/api/claude', methods=['POST'])
        def claude_endpoint():
            try:
                data = request.get_json()
                prompt = data.get('prompt', '')
                
                if not prompt:
                    return jsonify({'error': 'Prompt é obrigatório'}), 400
                
                # Verifica cache
                cache_key = f"flask_{hash(prompt)}"
                if cache_key in response_cache:
                    cached = response_cache[cache_key]
                    print(f"📦 Resposta do cache: {cache_key}")
                    return jsonify(cached)
                
                # Processa query
                print(f"🔍 Processando query Flask: {prompt[:50]}...")
                
                # Executa de forma síncrona (Flask não é assíncrono por padrão)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(process_claude_query(prompt))
                finally:
                    loop.close()
                
                # Salva no cache
                response_cache[cache_key] = result
                
                return jsonify(result)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({'status': 'healthy', 'framework': 'Flask'})
        
        print("🚀 Iniciando servidor Flask...")
        print("📡 Endpoints disponíveis:")
        print("   POST /api/claude - Envia query para Claude")
        print("   GET  /api/health - Verifica status do servidor")
        print("🌐 Servidor rodando em: http://localhost:5000")
        print("💡 Use Ctrl+C para parar")
        
        # Inicia servidor em thread separada
        import threading
        def run_flask():
            app.run(host='0.0.0.0', port=5000, debug=False)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        return True
        
    except ImportError:
        print("❌ Flask não instalado. Instale com: pip install flask")
        return False

def exemplo_fastapi_avancado():
    """
    Exemplo avançado usando FastAPI
    """
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title="Claude Code SDK API", version="1.0.0")
        
        class ClaudeRequest(BaseModel):
            prompt: str
            system_prompt: str = None
            max_turns: int = 1
            allowed_tools: list = None
        
        class ClaudeResponse(BaseModel):
            success: bool
            response: str = None
            usage: dict = None
            total_cost_usd: float = None
            processing_time_seconds: float = None
            error: str = None
        
        @app.post("/api/claude", response_model=ClaudeResponse)
        async def claude_endpoint(request: ClaudeRequest):
            try:
                # Verifica cache
                cache_key = f"fastapi_{hash(request.prompt + str(request.system_prompt))}"
                if cache_key in response_cache:
                    cached = response_cache[cache_key]
                    print(f"📦 Resposta do cache: {cache_key}")
                    return ClaudeResponse(**cached)
                
                # Configura opções
                options = None
                if request.system_prompt or request.max_turns or request.allowed_tools:
                    from src import ClaudeCodeOptions
                    options = ClaudeCodeOptions(
                        system_prompt=request.system_prompt,
                        max_turns=request.max_turns,
                        allowed_tools=request.allowed_tools
                    )
                
                # Processa query
                print(f"🔍 Processando query FastAPI: {request.prompt[:50]}...")
                result = await process_claude_query(request.prompt, options)
                
                # Salva no cache
                response_cache[cache_key] = result
                
                return ClaudeResponse(**result)
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/health")
        async def health_check():
            return {"status": "healthy", "framework": "FastAPI"}
        
        @app.get("/api/cache/stats")
        async def cache_stats():
            return {
                "cache_size": len(response_cache),
                "cache_keys": list(response_cache.keys())[:10]  # Primeiros 10
            }
        
        @app.delete("/api/cache/clear")
        async def clear_cache():
            global response_cache
            response_cache.clear()
            return {"message": "Cache limpo com sucesso"}
        
        print("🚀 Iniciando servidor FastAPI...")
        print("📡 Endpoints disponíveis:")
        print("   POST /api/claude - Envia query para Claude")
        print("   GET  /api/health - Verifica status do servidor")
        print("   GET  /api/cache/stats - Estatísticas do cache")
        print("   DELETE /api/cache/clear - Limpa cache")
        print("🌐 Servidor rodando em: http://localhost:8000")
        print("📚 Documentação: http://localhost:8000/docs")
        print("💡 Use Ctrl+C para parar")
        
        # Inicia servidor em thread separada
        import threading
        def run_fastapi():
            uvicorn.run(app, host="0.0.0.0", port=8000)
        
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        
        return True
        
    except ImportError:
        print("❌ FastAPI não instalado. Instale com: pip install fastapi uvicorn")
        return False

async def exemplo_requisicoes_http():
    """
    Exemplo de como fazer requisições HTTP para os servidores
    """
    print("\n" + "=" * 60)
    print("🌐 EXEMPLO: REQUISIÇÕES HTTP")
    print("=" * 60)
    
    try:
        import requests
        
        # Testa Flask
        print("🔍 Testando endpoint Flask...")
        try:
            response = requests.post(
                'http://localhost:5000/api/claude',
                json={'prompt': 'Diga apenas "Flask funcionando!"'},
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Flask: {result.get('response', 'Sem resposta')}")
                print(f"⏱️ Tempo: {result.get('processing_time_seconds', 0):.2f}s")
            else:
                print(f"❌ Flask: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Erro Flask: {e}")
        
        # Testa FastAPI
        print("\n🔍 Testando endpoint FastAPI...")
        try:
            response = requests.post(
                'http://localhost:8000/api/claude',
                json={
                    'prompt': 'Diga apenas "FastAPI funcionando!"',
                    'system_prompt': 'Seja conciso e direto'
                },
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ FastAPI: {result.get('response', 'Sem resposta')}")
                print(f"⏱️ Tempo: {result.get('processing_time_seconds', 0):.2f}s")
            else:
                print(f"❌ FastAPI: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Erro FastAPI: {e}")
        
        # Testa cache
        print("\n🔍 Testando cache...")
        try:
            response = requests.get('http://localhost:8000/api/cache/stats')
            if response.status_code == 200:
                stats = response.json()
                print(f"📦 Cache: {stats['cache_size']} itens")
            else:
                print(f"❌ Cache stats: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro cache: {e}")
            
    except ImportError:
        print("❌ Requests não instalado. Instale com: pip install requests")

async def main():
    """
    Função principal que executa todos os exemplos
    """
    print("🌐 DEMONSTRAÇÃO DE INTEGRAÇÃO COM WEB DO CLAUDE CODE SDK PYTHON")
    print("=" * 60)
    
    try:
        # Inicia servidores
        flask_ok = exemplo_flask_simples()
        fastapi_ok = exemplo_fastapi_avancado()
        
        if flask_ok and fastapi_ok:
            await exemplo_requisicoes_http()
        else:
            print("❌ Não foi possível iniciar todos os servidores. Verifique os requisitos.")
            
    except KeyboardInterrupt:
        print("\n👋 Programa interrompido pelo usuário.")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())
