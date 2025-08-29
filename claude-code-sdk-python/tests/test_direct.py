#!/usr/bin/env python3
"""Script direto para testar o problema"""

import sys
import asyncio
import pytest
sys.path.insert(0, '/home/codable/terminal/claude-code-sdk-python')

from src import query, AssistantMessage, TextBlock, ResultMessage

@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_single_query():
    """Testa query simples com mock."""
    from unittest.mock import AsyncMock, patch
    
    print(f"Testando query mockada")
    
    with patch('src._internal.client.InternalClient.process_query') as mock_process:
        # Mock do generator assíncrono
        async def mock_generator():
            yield AssistantMessage(
                content=[TextBlock(text="Resposta mockada")],
                model="claude-opus-4-1-20250805"
            )
            yield ResultMessage(
                type="result",
                subtype="success",
                duration_ms=1000,
                duration_api_ms=800,
                is_error=False,
                num_turns=1,
                session_id="test-session",
                total_cost_usd=0.001,
                usage={"input_tokens": 10, "output_tokens": 20}
            )
        
        mock_process.return_value = mock_generator()
        
        response_received = False
        async for message in query(prompt="teste"):
            response_received = True
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Resposta: {block.text}")
                        assert block.text == "Resposta mockada"
            elif isinstance(message, ResultMessage):
                print(f"Tokens: {message.usage['input_tokens']} in, {message.usage['output_tokens']} out")
        
        assert response_received, "Nenhuma resposta recebida"
        print("✓ Resposta processada com sucesso")
    
    print("Script finalizado normalmente")

if __name__ == "__main__":
    import signal
    
    def timeout_handler(signum, frame):
        print("⏱️ Timeout atingido, encerrando...")
        sys.exit(1)
    
    # Define timeout de 5 segundos para execução direta
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)
    
    try:
        asyncio.run(test_single_query())
    except SystemExit:
        pass
    finally:
        signal.alarm(0)  # Cancela o alarme
        print("Saindo...")
        sys.exit(0)