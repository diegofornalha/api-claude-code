"""Advanced tests for ClaudeSDKClient."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

import pytest

from src._errors import CLIConnectionError
from src.client import ClaudeSDKClient
from src.sdk_types import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    UserMessage,
)


# Fixtures for common test setup
@pytest.fixture
def mock_transport():
    """Create a mock transport with common async methods."""
    transport = AsyncMock()
    transport.connect = AsyncMock()
    transport.disconnect = AsyncMock()
    transport.send_request = AsyncMock()
    transport.receive = AsyncMock()
    transport.interrupt = AsyncMock()
    return transport


@pytest.fixture
def client_options():
    """Create default client options for testing."""
    return ClaudeCodeOptions(
        model="claude-3-sonnet",
        max_turns=5,
        system_prompt="Test system prompt"
    )


@pytest.fixture
async def connected_client(mock_transport):
    """Create a client with connected mock transport."""
    client = ClaudeSDKClient()
    client._transport = mock_transport
    yield client
    # Cleanup if needed
    client._transport = None


class TestClientInitialization:
    """Test client initialization."""

    def test_init_with_default_options(self):
        """Test initialization with default options."""
        client = ClaudeSDKClient()
        assert isinstance(client.options, ClaudeCodeOptions)
        assert client._transport is None

    def test_init_with_custom_options(self):
        """Test initialization with custom options."""
        options = ClaudeCodeOptions(
            model="claude-3-opus",
            max_turns=5,
            system_prompt="Test prompt"
        )
        client = ClaudeSDKClient(options)
        assert client.options is options
        assert client.options.model == "claude-3-opus"

    def test_init_sets_environment_variable(self):
        """Test that initialization sets CLAUDE_CODE_ENTRYPOINT."""
        import os
        client = ClaudeSDKClient()
        assert os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "sdk-py-client"


class TestClientConnection:
    """Test client connection methods."""

    @pytest.mark.asyncio
    async def test_connect_with_string_prompt(self):
        """Test connecting with a string prompt."""
        with patch('src._internal.transport.subprocess_cli.SubprocessCLITransport') as MockTransport:
            # Configure mock transport
            mock_transport_instance = AsyncMock()
            mock_transport_instance.connect = AsyncMock()
            MockTransport.return_value = mock_transport_instance
            
            client = ClaudeSDKClient()
            await client.connect("Hello Claude")
            
            # Verify transport was created with correct parameters
            MockTransport.assert_called_once()
            call_args = MockTransport.call_args
            # Check using kwargs instead of args
            assert call_args.kwargs['prompt'] == "Hello Claude"  # prompt
            assert isinstance(call_args.kwargs['options'], ClaudeCodeOptions)  # options
            
            # Verify connect was called
            mock_transport_instance.connect.assert_called_once()
            assert client._transport is mock_transport_instance

    @pytest.mark.asyncio
    async def test_connect_with_async_iterable(self):
        """Test connecting with an async iterable prompt."""
        async def prompt_generator():
            yield {"type": "user", "content": "Message 1"}
            yield {"type": "assistant", "content": "Response 1"}
        
        with patch('src._internal.transport.subprocess_cli.SubprocessCLITransport') as MockTransport:
            mock_transport_instance = AsyncMock()
            mock_transport_instance.connect = AsyncMock()
            MockTransport.return_value = mock_transport_instance
            
            client = ClaudeSDKClient()
            prompt_gen = prompt_generator()
            await client.connect(prompt_gen)
            
            # Verify transport was created with async iterable
            MockTransport.assert_called_once()
            call_args = MockTransport.call_args
            # Check using kwargs
            assert hasattr(call_args.kwargs['prompt'], '__aiter__')
            
            mock_transport_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_no_prompt(self):
        """Test connecting without a prompt (interactive mode)."""
        with patch('src._internal.transport.subprocess_cli.SubprocessCLITransport') as MockTransport:
            mock_transport_instance = AsyncMock()
            mock_transport_instance.connect = AsyncMock()
            MockTransport.return_value = mock_transport_instance
            
            client = ClaudeSDKClient()
            await client.connect()
            
            # Verify transport was created with async generator for interactive mode
            MockTransport.assert_called_once()
            call_args = MockTransport.call_args
            # When no prompt is provided, connect creates an empty async generator
            assert hasattr(call_args.kwargs['prompt'], '__aiter__')
            
            mock_transport_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting client."""
        client = ClaudeSDKClient()
        mock_transport = AsyncMock()
        client._transport = mock_transport
        
        await client.disconnect()
        
        assert mock_transport.disconnect.called
        assert client._transport is None

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected."""
        client = ClaudeSDKClient()
        # Should not raise error
        await client.disconnect()
        assert client._transport is None


class TestMessageReceiving:
    """Test message receiving methods."""

    @pytest.mark.asyncio
    async def test_receive_messages_not_connected(self):
        """Test receiving messages when not connected."""
        client = ClaudeSDKClient()
        
        with pytest.raises(CLIConnectionError) as exc_info:
            async for _ in client.receive_messages():
                pass
        
        assert "Not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_receive_messages(self):
        """Test receiving messages from transport."""
        client = ClaudeSDKClient()
        
        # Create mock messages with correct structure
        mock_messages = [
            {
                "type": "assistant", 
                "message": {
                    "content": [{"type": "text", "text": "Hello"}],
                    "model": "claude-3"
                }
            },
            {
                "type": "user", 
                "message": {"content": "Hi"}
            },
            {
                "type": "result", 
                "subtype": "result",
                "duration_ms": 100,
                "duration_api_ms": 80,
                "is_error": False,
                "num_turns": 1,
                "session_id": "test",
                "result": "Success"
            }
        ]
        
        # Configure mock transport to yield messages
        async def mock_receive():
            for msg in mock_messages:
                yield msg
        
        mock_transport = MagicMock()
        # Make receive_messages return the async generator directly (not a coroutine)
        mock_transport.receive_messages = mock_receive
        client._transport = mock_transport
        
        # Collect received messages
        received = []
        async for message in client.receive_messages():
            received.append(message)
        
        assert len(received) == 3
        assert isinstance(received[0], AssistantMessage)
        assert isinstance(received[1], UserMessage)
        assert isinstance(received[2], ResultMessage)

    @pytest.mark.asyncio
    async def test_receive_result_message(self):
        """Test receiving a result message from transport."""
        client = ClaudeSDKClient()
        
        # Create mock messages ending with result
        mock_messages = [
            {
                "type": "assistant",
                "message": {
                    "content": [{"type": "text", "text": "Processing..."}],
                    "model": "claude-3"
                }
            },
            {
                "type": "result",
                "subtype": "result",
                "duration_ms": 1000,
                "duration_api_ms": 800,
                "is_error": False,
                "num_turns": 1,
                "session_id": "test_session",
                "result": "Success"
            }
        ]
        
        # Configure mock transport
        async def mock_receive():
            for msg in mock_messages:
                yield msg
        
        mock_transport = MagicMock()
        mock_transport.receive_messages = mock_receive
        client._transport = mock_transport
        
        # Receive messages and check for result
        received = []
        async for message in client.receive_messages():
            received.append(message)
            if isinstance(message, ResultMessage):
                break
        
        assert len(received) == 2
        result = received[-1]
        assert isinstance(result, ResultMessage)
        assert result.result == "Success"
        assert result.is_error is False



class TestQueryMethod:
    """Test query method."""

    @pytest.mark.asyncio
    async def test_query_not_connected(self):
        """Test querying when not connected."""
        client = ClaudeSDKClient()
        
        with pytest.raises(CLIConnectionError) as exc_info:
            await client.query("Hello")
        
        assert "Not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_with_string(self):
        """Test querying with a string prompt."""
        client = ClaudeSDKClient()
        mock_transport = AsyncMock()
        client._transport = mock_transport
        
        await client.query("Hello Claude", session_id="test_session")
        
        assert mock_transport.send_request.called
        call_args = mock_transport.send_request.call_args
        
        messages = call_args[0][0]
        assert len(messages) == 1
        assert messages[0]["type"] == "user"
        assert messages[0]["message"]["content"] == "Hello Claude"
        assert messages[0]["session_id"] == "test_session"

    @pytest.mark.asyncio
    async def test_query_with_default_session(self):
        """Test querying with default session ID."""
        client = ClaudeSDKClient()
        mock_transport = AsyncMock()
        client._transport = mock_transport
        
        await client.query("Test")
        
        call_args = mock_transport.send_request.call_args
        messages = call_args[0][0]
        assert messages[0]["session_id"] == "default"

    @pytest.mark.asyncio
    async def test_query_with_async_iterable(self):
        """Test querying with an async iterable."""
        client = ClaudeSDKClient()
        mock_transport = AsyncMock()
        client._transport = mock_transport
        
        async def message_stream():
            yield {"type": "user", "content": "msg1"}
            yield {"type": "user", "content": "msg2"}
        
        await client.query(message_stream(), session_id="stream_session")
        
        assert mock_transport.send_request.called
        call_args = mock_transport.send_request.call_args
        
        messages = call_args[0][0]
        assert len(messages) == 2
        assert all(msg["session_id"] == "stream_session" for msg in messages)

    @pytest.mark.asyncio
    async def test_query_with_empty_async_iterable(self):
        """Test querying with an empty async iterable."""
        client = ClaudeSDKClient()
        mock_transport = AsyncMock()
        client._transport = mock_transport
        
        async def empty_stream():
            return
            yield  # Never reached
        
        await client.query(empty_stream())
        
        # send_request should not be called for empty stream
        assert not mock_transport.send_request.called


class TestInterruptMethod:
    """Test interrupt method."""

    @pytest.mark.asyncio
    async def test_interrupt_not_connected(self):
        """Test interrupting when not connected."""
        client = ClaudeSDKClient()
        
        with pytest.raises(CLIConnectionError) as exc_info:
            await client.interrupt()
        
        assert "Not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_interrupt_connected(self):
        """Test interrupting when connected."""
        client = ClaudeSDKClient()
        mock_transport = AsyncMock()
        client._transport = mock_transport
        
        await client.interrupt()
        
        assert mock_transport.interrupt.called


class TestContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_connect_disconnect(self):
        """Test context manager connects and disconnects properly."""
        with patch('src._internal.transport.subprocess_cli.SubprocessCLITransport') as MockTransport:
            mock_transport_instance = AsyncMock()
            mock_transport_instance.connect = AsyncMock()
            mock_transport_instance.disconnect = AsyncMock()
            MockTransport.return_value = mock_transport_instance
            
            options = ClaudeCodeOptions()
            
            async with ClaudeSDKClient(options) as client:
                # Verify client is connected
                assert client._transport is mock_transport_instance
                mock_transport_instance.connect.assert_called_once()
                
                # Use the client
                mock_transport_instance.send_request = AsyncMock()
                await client.query("Test message")
                mock_transport_instance.send_request.assert_called_once()
            
            # Verify disconnect was called after exiting context
            mock_transport_instance.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self):
        """Test context manager handles exceptions properly."""
        with patch('src._internal.transport.subprocess_cli.SubprocessCLITransport') as MockTransport:
            mock_transport_instance = AsyncMock()
            mock_transport_instance.connect = AsyncMock()
            mock_transport_instance.disconnect = AsyncMock()
            MockTransport.return_value = mock_transport_instance
            
            options = ClaudeCodeOptions()
            
            with pytest.raises(ValueError):
                async with ClaudeSDKClient(options) as client:
                    # Verify connected
                    assert client._transport is mock_transport_instance
                    
                    # Raise an exception
                    raise ValueError("Test exception")
            
            # Verify disconnect was still called despite exception
            mock_transport_instance.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_interactive_mode(self):
        """Test context manager in interactive mode (no prompt)."""
        with patch('src._internal.transport.subprocess_cli.SubprocessCLITransport') as MockTransport:
            mock_transport_instance = AsyncMock()
            mock_transport_instance.connect = AsyncMock()
            mock_transport_instance.disconnect = AsyncMock()
            mock_transport_instance.send_request = AsyncMock()
            MockTransport.return_value = mock_transport_instance
            
            options = ClaudeCodeOptions()
            
            # Use context manager without initial prompt
            async with ClaudeSDKClient(options) as client:
                # Verify transport created with async generator for interactive mode
                MockTransport.assert_called_once()
                call_args = MockTransport.call_args
                # When no prompt is provided, connect creates an empty async generator
                assert hasattr(call_args.kwargs['prompt'], '__aiter__')
                
                # Send interactive messages
                await client.query("First message")
                await client.query("Second message")
                
                assert mock_transport_instance.send_request.call_count == 2
            
            mock_transport_instance.disconnect.assert_called_once()



class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self):
        """Test complete conversation flow from connect to disconnect."""
        with patch('src._internal.transport.subprocess_cli.SubprocessCLITransport') as MockTransport:
            # Setup mock transport with full conversation
            mock_transport = AsyncMock()
            mock_transport.connect = AsyncMock()
            mock_transport.disconnect = AsyncMock()
            mock_transport.send_request = AsyncMock()
            MockTransport.return_value = mock_transport
            
            # Setup mock receive messages as dicts with correct structure
            conversation_messages = [
                {
                    "type": "user",
                    "message": {"content": "Hello Claude"}
                },
                {
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "text", "text": "Hello! How can I help?"}],
                        "model": "claude-3"
                    }
                },
                {
                    "type": "user",
                    "message": {"content": "What's 2+2?"}
                },
                {
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "text", "text": "2+2 equals 4"}],
                        "model": "claude-3"
                    }
                },
                {
                    "type": "result",
                    "subtype": "result",
                    "duration_ms": 1500,
                    "duration_api_ms": 1200,
                    "is_error": False,
                    "num_turns": 2,
                    "session_id": "test",
                    "result": "Conversation complete"
                }
            ]
            
            async def mock_receive():
                for msg in conversation_messages:
                    yield msg
            
            mock_transport.receive_messages = mock_receive
            
            # Execute full conversation
            client = ClaudeSDKClient()
            await client.connect("Hello Claude")
            
            # Verify connection
            mock_transport.connect.assert_called_once()
            assert client._transport is mock_transport
            
            # Send additional query
            await client.query("What's 2+2?")
            
            # Receive all messages
            messages = []
            async for msg in client.receive_messages():
                messages.append(msg)
                if isinstance(msg, ResultMessage):
                    break
            
            assert len(messages) == 5
            assert isinstance(messages[0], UserMessage)
            assert isinstance(messages[1], AssistantMessage)
            assert isinstance(messages[4], ResultMessage)
            
            # Disconnect
            await client.disconnect()
            mock_transport.disconnect.assert_called_once()
            assert client._transport is None

    @pytest.mark.asyncio
    async def test_manual_connection_lifecycle(self):
        """Test manual connection lifecycle management."""
        with patch('src._internal.transport.subprocess_cli.SubprocessCLITransport') as MockTransport:
            mock_transport = AsyncMock()
            mock_transport.connect = AsyncMock()
            mock_transport.disconnect = AsyncMock()
            mock_transport.send_request = AsyncMock()
            mock_transport.interrupt = AsyncMock()
            MockTransport.return_value = mock_transport
            
            # Create client
            client = ClaudeSDKClient(ClaudeCodeOptions(
                model="claude-3-opus",
                max_turns=3
            ))
            
            # Initially not connected
            assert client._transport is None
            
            # Connect manually
            await client.connect()
            assert client._transport is mock_transport
            mock_transport.connect.assert_called_once()
            
            # Perform operations
            await client.query("Test 1")
            assert mock_transport.send_request.call_count == 1
            
            await client.query("Test 2")  
            assert mock_transport.send_request.call_count == 2
            
            # Interrupt
            await client.interrupt()
            mock_transport.interrupt.assert_called_once()
            
            # Still connected after interrupt
            assert client._transport is not None
            
            # Disconnect manually
            await client.disconnect()
            mock_transport.disconnect.assert_called_once()
            assert client._transport is None
            
            # Can reconnect
            mock_transport.connect.reset_mock()
            await client.connect("New session")
            assert client._transport is mock_transport
            mock_transport.connect.assert_called_once()

