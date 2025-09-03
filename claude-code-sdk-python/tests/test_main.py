#!/usr/bin/env python3
"""
Testes abrangentes para o módulo __main__.py do Claude Code SDK.

Cobre todas as funções principais:
- print_header()
- print_response()
- single_query()
- interactive_mode()
- chat_mode()
- run_examples()
- main()
- run()
"""

import pytest
import sys
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from io import StringIO
import argparse
from pathlib import Path

# Add src to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.__main__ import (
    print_header,
    print_response,
    single_query,
    interactive_mode,
    chat_mode,
    run_examples,
    main,
    run
)
from src import (
    AssistantMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
    ClaudeCodeOptions,
    ClaudeSDKClient,
    __version__
)


class TestPrintHeader:
    """Testes para a função print_header()."""
    
    def test_print_header(self, capsys):
        """Testa se o cabeçalho é impresso corretamente."""
        print_header()
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "=" * 60 in output
        assert f"🤖 Claude Code SDK Python v{__version__}" in output
        assert output.count("=" * 60) == 2  # Duas linhas de separadores


class TestPrintResponse:
    """Testes para a função print_response()."""
    
    def test_print_response_with_text(self, capsys):
        """Testa print_response com TextBlock."""
        text_block = TextBlock(text="Olá mundo!")
        message = AssistantMessage(content=[text_block], model="claude-3-5-sonnet-20241022")
        
        print_response(message)
        
        captured = capsys.readouterr()
        assert "📝 Claude: Olá mundo!" in captured.out
    
    def test_print_response_with_thinking(self, capsys):
        """Testa print_response com ThinkingBlock."""
        thinking_block = ThinkingBlock(thinking="Pensando...", signature="test")
        message = AssistantMessage(content=[thinking_block], model="claude-3-5-sonnet-20241022")
        
        print_response(message)
        
        captured = capsys.readouterr()
        # ThinkingBlock não deve ser exibido
        assert "Pensando..." not in captured.out
    
    def test_print_response_with_tool_use(self, capsys):
        """Testa print_response com ToolUseBlock."""
        tool_use = ToolUseBlock(id="1", name="read", input={"path": "test.py"})
        message = AssistantMessage(content=[tool_use], model="claude-3-5-sonnet-20241022")
        
        print_response(message)
        
        captured = capsys.readouterr()
        # ToolUseBlock não deve ser exibido diretamente
        assert "read" not in captured.out
    
    def test_print_response_with_tool_result(self, capsys):
        """Testa print_response com ToolResultBlock."""
        tool_result = ToolResultBlock(tool_use_id="1", content="resultado")
        message = AssistantMessage(content=[tool_result], model="claude-3-5-sonnet-20241022")
        
        print_response(message)
        
        captured = capsys.readouterr()
        # ToolResultBlock não deve ser exibido diretamente
        assert "resultado" not in captured.out
    
    def test_print_response_with_result_message_usage_object(self, capsys):
        """Testa print_response com ResultMessage contendo usage como objeto."""
        usage_mock = Mock()
        usage_mock.input_tokens = 100
        usage_mock.output_tokens = 50
        
        message = ResultMessage(
            subtype="result",
            duration_ms=1000,
            duration_api_ms=800,
            is_error=False,
            num_turns=1,
            session_id="test-session",
            usage=usage_mock,
            total_cost_usd=0.001234
        )
        
        print_response(message)
        
        captured = capsys.readouterr()
        assert "📊 Tokens: 100 entrada, 50 saída" in captured.out
        assert "💰 Custo: $0.001234" in captured.out
    
    def test_print_response_with_result_message_usage_dict(self, capsys):
        """Testa print_response com ResultMessage contendo usage como dict."""
        message = ResultMessage(
            subtype="result",
            duration_ms=1000,
            duration_api_ms=800,
            is_error=False,
            num_turns=1,
            session_id="test-session",
            usage={"input_tokens": 200, "output_tokens": 75},
            total_cost_usd=0.005678
        )
        
        print_response(message)
        
        captured = capsys.readouterr()
        assert "📊 Tokens: 200 entrada, 75 saída" in captured.out
        assert "💰 Custo: $0.005678" in captured.out
    
    def test_print_response_with_error(self, capsys):
        """Testa print_response com objeto não reconhecido."""
        invalid_message = "string inválida"
        
        print_response(invalid_message)
        
        captured = capsys.readouterr()
        # Não deve imprimir nada para mensagem inválida
        assert captured.out == ""


class TestSingleQuery:
    """Testes para a função single_query()."""
    
    @pytest.mark.asyncio
    async def test_single_query_success(self, capsys):
        """Testa single_query com sucesso."""
        text_block = TextBlock(text="Resposta teste")
        message = AssistantMessage(content=[text_block], model="claude-3-5-sonnet-20241022")
        
        async def async_generator():
            yield message
        
        with patch('src.__main__.query') as mock_query:
            mock_query.return_value = async_generator()
            
            result = await single_query("Pergunta teste")
            
            assert result is True
            captured = capsys.readouterr()
            assert "🔍 Pergunta: Pergunta teste" in captured.out
            assert "📝 Claude: Resposta teste" in captured.out
    
    @pytest.mark.asyncio
    async def test_single_query_with_options(self, capsys):
        """Testa single_query com opções."""
        options = ClaudeCodeOptions()
        options.system_prompt = "System test"
        
        async def empty_async_generator():
            if False:  # Never yields
                yield
        
        with patch('src.__main__.query') as mock_query:
            mock_query.return_value = empty_async_generator()
            
            await single_query("Pergunta", options)
            
            mock_query.assert_called_once_with(prompt="Pergunta", options=options)
    
    @pytest.mark.asyncio
    async def test_single_query_with_exception(self, capsys):
        """Testa single_query com exceção."""
        with patch('src.__main__.query') as mock_query:
            mock_query.side_effect = Exception("Erro teste")
            
            result = await single_query("Pergunta")
            
            assert result is False
            captured = capsys.readouterr()
            assert "❌ Erro: Erro teste" in captured.out


class TestInteractiveMode:
    """Testes para a função interactive_mode()."""
    
    @pytest.mark.asyncio
    async def test_interactive_mode_sair_command(self, capsys):
        """Testa comando 'sair' no modo interativo."""
        with patch('builtins.input', side_effect=["sair"]):
            with patch('src.__main__.single_query') as mock_single_query:
                await interactive_mode()
                
                mock_single_query.assert_not_called()
                captured = capsys.readouterr()
                assert "👋 Até logo!" in captured.out
    
    @pytest.mark.asyncio
    async def test_interactive_mode_exit_command(self, capsys):
        """Testa comando 'exit' no modo interativo."""
        with patch('builtins.input', side_effect=["exit"]):
            await interactive_mode()
            
            captured = capsys.readouterr()
            assert "👋 Até logo!" in captured.out
    
    @pytest.mark.asyncio
    async def test_interactive_mode_empty_input(self, capsys):
        """Testa entrada vazia no modo interativo."""
        with patch('builtins.input', side_effect=["", "sair"]):
            with patch('src.__main__.single_query') as mock_single_query:
                await interactive_mode()
                
                mock_single_query.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_interactive_mode_valid_question(self, capsys):
        """Testa pergunta válida no modo interativo."""
        with patch('builtins.input', side_effect=["Pergunta teste", "sair"]):
            with patch('src.__main__.single_query') as mock_single_query:
                await interactive_mode()
                
                mock_single_query.assert_called_once_with("Pergunta teste")
    
    @pytest.mark.asyncio
    async def test_interactive_mode_keyboard_interrupt(self, capsys):
        """Testa KeyboardInterrupt no modo interativo."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            await interactive_mode()
            
            captured = capsys.readouterr()
            assert "👋 Interrompido pelo usuário!" in captured.out
    
    @pytest.mark.asyncio
    async def test_interactive_mode_eof_error(self, capsys):
        """Testa EOFError no modo interativo."""
        with patch('builtins.input', side_effect=EOFError):
            await interactive_mode()
            
            captured = capsys.readouterr()
            assert "👋 Até logo!" in captured.out


class TestChatMode:
    """Testes para a função chat_mode()."""
    
    @pytest.mark.asyncio
    async def test_chat_mode_sair_command(self, capsys):
        """Testa comando 'sair' no modo chat."""
        mock_client = AsyncMock()
        # Configurar context manager
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('builtins.input', side_effect=["sair"]):
            with patch('src.__main__.ClaudeSDKClient', return_value=mock_client):
                await chat_mode()
                
                captured = capsys.readouterr()
                assert "👋 Até logo!" in captured.out
    
    @pytest.mark.asyncio
    async def test_chat_mode_valid_message(self, capsys):
        """Testa mensagem válida no modo chat."""
        text_block = TextBlock(text="Resposta")
        response_message = AssistantMessage(content=[text_block], model="claude-3-5-sonnet-20241022")
        
        # Criar um mock client que implementa async context manager
        class MockClient:
            def __init__(self):
                self.query_called_with = None
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            
            async def query(self, prompt):
                self.query_called_with = prompt
            
            async def receive_response(self):
                yield response_message
        
        mock_client = MockClient()
        
        with patch('builtins.input', side_effect=["Olá", "sair"]):
            with patch('src.__main__.ClaudeSDKClient', return_value=mock_client):
                await chat_mode()
                
                assert mock_client.query_called_with == "Olá"
                captured = capsys.readouterr()
                assert "📝 Claude:" in captured.out
    
    @pytest.mark.asyncio
    async def test_chat_mode_keyboard_interrupt(self, capsys):
        """Testa KeyboardInterrupt no modo chat."""
        mock_client = AsyncMock()
        # Configurar context manager
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            with patch('src.__main__.ClaudeSDKClient', return_value=mock_client):
                await chat_mode()
                
                captured = capsys.readouterr()
                assert "👋 Interrompido pelo usuário!" in captured.out


class TestRunExamples:
    """Testes para a função run_examples()."""
    
    @pytest.mark.asyncio
    async def test_run_examples_all_success(self, capsys):
        """Testa execução de exemplos com sucesso."""
        with patch('src.__main__.single_query', return_value=True) as mock_single_query:
            await run_examples()
            
            # Verifica se todos os 4 exemplos foram executados
            assert mock_single_query.call_count == 4
            
            # Verifica chamadas específicas
            calls = mock_single_query.call_args_list
            assert any("25 + 17" in str(call) for call in calls)
            assert any("capital do Brasil" in str(call) for call in calls)
            
            captured = capsys.readouterr()
            assert "✅ Exemplos concluídos!" in captured.out
    
    @pytest.mark.asyncio
    async def test_run_examples_with_failures(self, capsys):
        """Testa execução de exemplos com falhas."""
        with patch('src.__main__.single_query', return_value=False) as mock_single_query:
            await run_examples()
            
            captured = capsys.readouterr()
            assert "⚠️ Exemplo falhou, continuando..." in captured.out
            assert "✅ Exemplos concluídos!" in captured.out


class TestMainFunction:
    """Testes para a função main()."""
    
    @pytest.mark.asyncio
    async def test_main_no_arguments(self):
        """Testa main() sem argumentos (modo interativo)."""
        with patch('sys.argv', ['__main__.py']):
            with patch('src.__main__.print_header') as mock_header:
                with patch('src.__main__.interactive_mode') as mock_interactive:
                    await main()
                    
                    mock_header.assert_called_once()
                    mock_interactive.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_with_prompt(self):
        """Testa main() com prompt direto."""
        with patch('sys.argv', ['__main__.py', 'Pergunta teste']):
            with patch('src.__main__.single_query') as mock_single_query:
                await main()
                
                mock_single_query.assert_called_once_with('Pergunta teste', None)
    
    @pytest.mark.asyncio
    async def test_main_chat_mode(self):
        """Testa main() com modo chat."""
        with patch('sys.argv', ['__main__.py', '--chat']):
            with patch('src.__main__.chat_mode') as mock_chat:
                await main()
                
                mock_chat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_example_mode(self):
        """Testa main() com modo exemplos."""
        with patch('sys.argv', ['__main__.py', '--example']):
            with patch('src.__main__.run_examples') as mock_examples:
                await main()
                
                mock_examples.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_with_tools_option(self):
        """Testa main() com opção --tools."""
        with patch('sys.argv', ['__main__.py', '--tools', 'Read,Write', 'Pergunta']):
            with patch('src.__main__.single_query') as mock_single_query:
                await main()
                
                # Verifica se options foi passado corretamente
                args, kwargs = mock_single_query.call_args
                assert args[0] == 'Pergunta'
                options = args[1]
                assert options is not None
                assert options.allowed_tools == ['Read', 'Write']
    
    @pytest.mark.asyncio
    async def test_main_with_system_option(self):
        """Testa main() com opção --system."""
        with patch('sys.argv', ['__main__.py', '--system', 'Custom prompt', 'Pergunta']):
            with patch('src.__main__.single_query') as mock_single_query:
                await main()
                
                args, kwargs = mock_single_query.call_args
                options = args[1]
                assert options.system_prompt == 'Custom prompt'
    
    @pytest.mark.asyncio
    async def test_main_no_header_option(self):
        """Testa main() com opção --no-header."""
        with patch('sys.argv', ['__main__.py', '--no-header']):
            with patch('src.__main__.print_header') as mock_header:
                with patch('src.__main__.interactive_mode'):
                    await main()
                    
                    mock_header.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self, capsys):
        """Testa KeyboardInterrupt na função main()."""
        with patch('sys.argv', ['__main__.py']):
            with patch('src.__main__.interactive_mode', side_effect=KeyboardInterrupt):
                with pytest.raises(SystemExit) as exc_info:
                    await main()
                
                assert exc_info.value.code == 0
                captured = capsys.readouterr()
                assert "👋 Interrompido pelo usuário!" in captured.out
    
    @pytest.mark.asyncio
    async def test_main_general_exception(self, capsys):
        """Testa exceção geral na função main()."""
        with patch('sys.argv', ['__main__.py']):
            with patch('src.__main__.interactive_mode', side_effect=Exception("Erro teste")):
                with pytest.raises(SystemExit) as exc_info:
                    await main()
                
                assert exc_info.value.code == 1
                captured = capsys.readouterr()
                assert "❌ Erro: Erro teste" in captured.out


class TestRunFunction:
    """Testes para a função run()."""
    
    def test_run_success(self):
        """Testa execução bem-sucedida da função run()."""
        with patch('anyio.run') as mock_anyio_run:
            run()
            mock_anyio_run.assert_called_once_with(main)
    
    def test_run_keyboard_interrupt(self, capsys):
        """Testa KeyboardInterrupt na função run()."""
        with patch('anyio.run', side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as exc_info:
                run()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "👋 Até logo!" in captured.out


class TestMainEntryPoint:
    """Testes para o entry point if __name__ == '__main__'."""
    
    def test_main_entry_point(self):
        """Testa se o entry point chama a função run()."""
        # Testamos diretamente a função run() já que é o entry point
        with patch('anyio.run') as mock_anyio_run:
            run()
            mock_anyio_run.assert_called_once_with(main)


# Fixtures e helpers para testes
@pytest.fixture
def mock_claude_client():
    """Fixture que retorna um mock do ClaudeSDKClient."""
    client = AsyncMock(spec=ClaudeSDKClient)
    return client


@pytest.fixture
def sample_text_message():
    """Fixture que retorna uma mensagem de texto de exemplo."""
    return AssistantMessage(
        content=[TextBlock(text="Texto de exemplo")],
        model="claude-3-5-sonnet-20241022"
    )


@pytest.fixture
def sample_result_message():
    """Fixture que retorna uma mensagem de resultado de exemplo."""
    return ResultMessage(
        subtype="result",
        duration_ms=1000,
        duration_api_ms=800,
        is_error=False,
        num_turns=1,
        session_id="test-session",
        usage={"input_tokens": 10, "output_tokens": 20},
        total_cost_usd=0.001
    )


# Testes de integração
class TestIntegrationScenarios:
    """Testes de integração simulando cenários reais."""
    
    @pytest.mark.asyncio
    async def test_complete_interaction_flow(self, capsys):
        """Testa um fluxo completo de interação."""
        text_block = TextBlock(text="Olá! Como posso ajudar?")
        message = AssistantMessage(content=[text_block], model="claude-3-5-sonnet-20241022")
        
        async def async_generator():
            yield message
        
        with patch('builtins.input', side_effect=["Como você está?", "sair"]):
            with patch('src.__main__.query') as mock_query:
                mock_query.return_value = async_generator()
                
                await interactive_mode()
                
                captured = capsys.readouterr()
                assert "💬 Modo Interativo" in captured.out
                assert "📝 Claude: Olá! Como posso ajudar?" in captured.out
                assert "👋 Até logo!" in captured.out


if __name__ == "__main__":
    # Permite executar os testes diretamente
    pytest.main([__file__, "-v"])