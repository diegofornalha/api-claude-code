"""Testes abrangentes para a função query."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from collections.abc import AsyncIterable
from pathlib import Path
import os

from src.query import query
from src.sdk_types import (
    ClaudeCodeOptions, 
    UserMessage, 
    AssistantMessage, 
    TextBlock, 
    SystemMessage,
    ResultMessage
)


class TestQuery:
    """Testes para a função query."""

    @pytest.fixture
    def mock_client(self):
        """Mock do InternalClient."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def mock_transport(self):
        """Mock de um transport personalizado."""
        transport = AsyncMock()
        transport.connect = AsyncMock()
        transport.disconnect = AsyncMock()
        transport.receive_messages = AsyncMock()
        return transport

    @pytest.fixture
    def sample_messages(self):
        """Mensagens de exemplo para testes."""
        return [
            UserMessage(content="Hello"),
            AssistantMessage(
                content=[TextBlock(text="Hello! How can I help you?")],
                model="claude-3-5-sonnet-20241022"
            ),
            ResultMessage(
                subtype="result",
                duration_ms=1500,
                duration_api_ms=800,
                is_error=False,
                num_turns=1,
                session_id="test-session",
                total_cost_usd=0.01
            )
        ]

    @pytest.mark.asyncio
    async def test_query_with_string_prompt(self, mock_client, sample_messages):
        """Testar query com prompt string simples."""
        with patch('src.query.InternalClient', return_value=mock_client):
            # Configurar mock para retornar mensagens
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Executar query
            messages = []
            async for message in query(prompt="What is 2+2?"):
                messages.append(message)
            
            # Verificar resultado
            assert len(messages) == 3
            assert isinstance(messages[0], UserMessage)
            assert isinstance(messages[1], AssistantMessage)
            assert isinstance(messages[2], ResultMessage)

    @pytest.mark.asyncio
    async def test_query_with_custom_options(self, mock_client, sample_messages):
        """Testar query com opções personalizadas."""
        with patch('src.query.InternalClient', return_value=mock_client):
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Criar opções personalizadas
            custom_options = ClaudeCodeOptions(
                system_prompt="You are a helpful Python expert",
                max_thinking_tokens=5000,
                permission_mode="acceptEdits",
                max_turns=10
            )
            
            # Executar query
            messages = []
            async for message in query(
                prompt="Create a Python function",
                options=custom_options
            ):
                messages.append(message)
            
            # Verificar resultado
            assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_query_with_custom_cwd(self, mock_client, sample_messages):
        """Testar query com diretório de trabalho customizado."""
        with patch('src.query.InternalClient', return_value=mock_client):
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Criar opções com cwd customizado
            custom_cwd = "/home/user/project"
            options = ClaudeCodeOptions(cwd=custom_cwd)
            
            # Executar query
            messages = []
            async for message in query(
                prompt="List files in current directory",
                options=options
            ):
                messages.append(message)
            
            # Verificar resultado
            assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_query_with_all_parameters(self, mock_client, mock_transport, sample_messages):
        """Testar query com todos os parâmetros possíveis."""
        with patch('src.query.InternalClient', return_value=mock_client):
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Criar opções completas
            full_options = ClaudeCodeOptions(
                system_prompt="Expert developer",
                append_system_prompt="Use best practices",
                max_thinking_tokens=10000,
                permission_mode="bypassPermissions",
                max_turns=20,
                model="claude-3-5-sonnet-20241022",
                cwd="/test/project",
                allowed_tools=["read", "write", "bash"],
                disallowed_tools=["dangerous_tool"],
                add_dirs=["/extra/dir"],
                env={"TEST_ENV": "true"},
                extra_args={"verbose": "true"}
            )
            
            # Executar query com todos parâmetros
            messages = []
            async for message in query(
                prompt="Complex development task",
                options=full_options,
                transport=mock_transport
            ):
                messages.append(message)
            
            # Verificar resultado
            assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_query_with_async_generator(self, mock_client, sample_messages):
        """Testar query com generator assíncrono como prompt."""
        with patch('src.query.InternalClient', return_value=mock_client):
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Criar generator assíncrono
            async def async_prompts():
                yield {"type": "user", "message": {"role": "user", "content": "Hello"}}
                yield {"type": "user", "message": {"role": "user", "content": "How are you?"}}
                yield {"type": "user", "message": {"role": "user", "content": "Goodbye"}}
            
            # Executar query
            messages = []
            async for message in query(prompt=async_prompts()):
                messages.append(message)
            
            # Verificar resultado
            assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_query_error_handling(self, mock_client):
        """Testar tratamento de erros."""
        with patch('src.query.InternalClient', return_value=mock_client):
            # Configurar mock para lançar exceção imediatamente
            def mock_process_query_error(*args, **kwargs):
                raise Exception("Connection failed")
            
            mock_client.process_query = mock_process_query_error
            
            # Verificar que a exceção é propagada
            with pytest.raises(Exception, match="Connection failed"):
                async for message in query(prompt="Test error"):
                    pass

    @pytest.mark.asyncio
    async def test_query_with_interactive_mode(self, mock_client, sample_messages):
        """Testar modo interativo (prompt=None não é suportado, mas testar comportamento)."""
        with patch('src.query.InternalClient', return_value=mock_client):
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Executar query com prompt vazio (simulando modo interativo)
            messages = []
            async for message in query(prompt=""):
                messages.append(message)
            
            # Verificar que funciona mesmo com prompt vazio
            assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_query_response_iteration(self, mock_client):
        """Testar iteração sobre respostas."""
        with patch('src.query.InternalClient', return_value=mock_client):
            # Criar sequência de mensagens mais complexa
            complex_messages = [
                UserMessage(content="Start conversation"),
                AssistantMessage(
                    content=[TextBlock(text="Starting analysis...")],
                    model="claude-3-5-sonnet-20241022"
                ),
                SystemMessage(subtype="thinking", data={"content": "Processing..."}),
                AssistantMessage(
                    content=[TextBlock(text="Analysis complete!")],
                    model="claude-3-5-sonnet-20241022"
                ),
                ResultMessage(
                    subtype="result",
                    duration_ms=3000,
                    duration_api_ms=1500,
                    is_error=False,
                    num_turns=2,
                    session_id="complex-session",
                    total_cost_usd=0.05,
                    result="Success"
                )
            ]
            
            async def mock_process_query(*args, **kwargs):
                for msg in complex_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Executar query e coletar todos os tipos de mensagens
            user_messages = []
            assistant_messages = []
            system_messages = []
            result_messages = []
            
            async for message in query(prompt="Complex analysis task"):
                if isinstance(message, UserMessage):
                    user_messages.append(message)
                elif isinstance(message, AssistantMessage):
                    assistant_messages.append(message)
                elif isinstance(message, SystemMessage):
                    system_messages.append(message)
                elif isinstance(message, ResultMessage):
                    result_messages.append(message)
            
            # Verificar que todos os tipos foram coletados corretamente
            assert len(user_messages) == 1
            assert len(assistant_messages) == 2
            assert len(system_messages) == 1
            assert len(result_messages) == 1
            
            # Verificar conteúdo específico
            assert user_messages[0].content == "Start conversation"
            assert assistant_messages[0].content[0].text == "Starting analysis..."
            assert assistant_messages[1].content[0].text == "Analysis complete!"
            assert system_messages[0].subtype == "thinking"
            assert result_messages[0].num_turns == 2

    @pytest.mark.asyncio
    async def test_query_environment_variable_set(self, mock_client, sample_messages):
        """Testar que a variável de ambiente é configurada corretamente."""
        with patch('src.query.InternalClient', return_value=mock_client):
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Executar query
            messages = []
            async for message in query(prompt="Test env variable"):
                messages.append(message)
            
            # Verificar que a variável de ambiente foi configurada
            assert os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "sdk-py"

    @pytest.mark.asyncio
    async def test_query_default_options(self, mock_client, sample_messages):
        """Testar que opções padrão são criadas quando None é passado."""
        with patch('src.query.InternalClient', return_value=mock_client):
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Executar query sem opções (None implícito)
            messages = []
            async for message in query(prompt="Test default options"):
                messages.append(message)
            
            # Verificar resultado e variável de ambiente
            assert len(messages) == 3
            assert os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "sdk-py"

    @pytest.mark.asyncio
    async def test_query_with_pathlib_cwd(self, mock_client, sample_messages):
        """Testar query com cwd usando Path do pathlib."""
        with patch('src.query.InternalClient', return_value=mock_client):
            async def mock_process_query(*args, **kwargs):
                for msg in sample_messages:
                    yield msg
            
            mock_client.process_query = mock_process_query
            
            # Usar Path para cwd
            path_cwd = Path("/home/user/project")
            options = ClaudeCodeOptions(cwd=path_cwd)
            
            # Executar query
            messages = []
            async for message in query(
                prompt="Test with Path cwd",
                options=options
            ):
                messages.append(message)
            
            # Verificar resultado
            assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_query_empty_response(self, mock_client):
        """Testar comportamento com resposta vazia."""
        with patch('src.query.InternalClient', return_value=mock_client):
            # Configurar mock para não retornar nada
            async def mock_process_query(*args, **kwargs):
                # Generator vazio
                return
                yield  # unreachable
            
            mock_client.process_query = mock_process_query
            
            # Executar query
            messages = []
            async for message in query(prompt="Empty response test"):
                messages.append(message)
            
            # Verificar que nenhuma mensagem foi recebida
            assert len(messages) == 0