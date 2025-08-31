"""Advanced tests for ClaudeSDKClient."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

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
    @patch("src.client.SubprocessCLITransport")
    async def test_connect_with_string_prompt(self, mock_transport_class):
        """Test connecting with a string prompt."""
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        client = ClaudeSDKClient()
        await client.connect("Hello Claude")
        
        assert client._transport is mock_transport
        assert mock_transport.connect.called
        
        # Check that string prompt was passed
        call_args = mock_transport_class.call_args
        assert call_args[1]["prompt"] == "Hello Claude"

    @pytest.mark.asyncio
    @patch("src.client.SubprocessCLITransport")
    async def test_connect_with_async_iterable(self, mock_transport_class):
        """Test connecting with an async iterable."""
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        async def message_stream():
            yield {"message": "test1"}
            yield {"message": "test2"}
        
        client = ClaudeSDKClient()
        await client.connect(message_stream())
        
        assert client._transport is mock_transport
        assert mock_transport.connect.called

    @pytest.mark.asyncio
    @patch("src.client.SubprocessCLITransport")
    async def test_connect_with_no_prompt(self, mock_transport_class):
        """Test connecting with no prompt (interactive mode)."""
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        client = ClaudeSDKClient()
        await client.connect()
        
        assert client._transport is mock_transport
        assert mock_transport.connect.called
        
        # Check that an empty async generator was created
        call_args = mock_transport_class.call_args
        prompt = call_args[1]["prompt"]
        # Verify it's an async generator
        assert hasattr(prompt, "__aiter__")

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
    @patch("src.client.parse_message")
    async def test_receive_messages(self, mock_parse):
        """Test receiving and parsing messages."""
        client = ClaudeSDKClient()
        
        # Mock transport
        mock_transport = AsyncMock()
        async def mock_receive():
            yield {"type": "user", "data": "message1"}
            yield {"type": "assistant", "data": "message2"}
        
        mock_transport.receive_messages = mock_receive
        client._transport = mock_transport
        
        # Mock parse_message
        mock_parse.side_effect = [
            UserMessage(content="parsed1"),
            AssistantMessage(content=[], model="claude")
        ]
        
        messages = []
        async for msg in client.receive_messages():
            messages.append(msg)
        
        assert len(messages) == 2
        assert isinstance(messages[0], UserMessage)
        assert isinstance(messages[1], AssistantMessage)

    @pytest.mark.asyncio
    @patch("src.client.parse_message")
    async def test_receive_response_until_result(self, mock_parse):
        """Test receive_response stops after ResultMessage."""
        client = ClaudeSDKClient()
        
        # Mock transport
        mock_transport = AsyncMock()
        async def mock_receive():
            yield {"type": "user"}
            yield {"type": "assistant"}
            yield {"type": "result"}  # Should stop after this
            yield {"type": "another"}  # Should not receive this
        
        mock_transport.receive_messages = mock_receive
        client._transport = mock_transport
        
        # Mock parse_message
        mock_parse.side_effect = [
            UserMessage(content="user"),
            AssistantMessage(content=[], model="claude"),
            ResultMessage(
                subtype="success",
                duration_ms=100,
                duration_api_ms=80,
                is_error=False,
                num_turns=1,
                session_id="test"
            ),
            UserMessage(content="should not see this")
        ]
        
        messages = []
        async for msg in client.receive_response():
            messages.append(msg)
        
        assert len(messages) == 3
        assert isinstance(messages[2], ResultMessage)
        # Verify we didn't receive the 4th message
        assert mock_parse.call_count == 3


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
    @patch("src.client.SubprocessCLITransport")
    async def test_context_manager_connect_disconnect(self, mock_transport_class):
        """Test that context manager connects and disconnects."""
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        async with ClaudeSDKClient() as client:
            assert client._transport is mock_transport
            assert mock_transport.connect.called
        
        # After exiting context, should be disconnected
        assert mock_transport.disconnect.called

    @pytest.mark.asyncio
    @patch("src.client.SubprocessCLITransport")
    async def test_context_manager_with_exception(self, mock_transport_class):
        """Test that context manager disconnects even with exception."""
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        with pytest.raises(ValueError):
            async with ClaudeSDKClient() as client:
                assert client._transport is mock_transport
                raise ValueError("Test error")
        
        # Should still disconnect after exception
        assert mock_transport.disconnect.called

    @pytest.mark.asyncio
    @patch("src.client.SubprocessCLITransport")
    async def test_context_manager_interactive_mode(self, mock_transport_class):
        """Test context manager for interactive conversation."""
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        # Mock receive_messages to return some messages
        async def mock_receive():
            yield {"type": "assistant", "content": "Ready"}
            yield {"type": "result", "subtype": "success"}
        
        mock_transport.receive_messages = mock_receive
        
        async with ClaudeSDKClient() as client:
            # Should be able to send query
            await client.query("Hello")
            assert mock_transport.send_request.called
            
            # Should be able to receive messages
            messages = []
            with patch("src.client.parse_message") as mock_parse:
                mock_parse.side_effect = [
                    AssistantMessage(content=[TextBlock(text="Ready")], model="claude"),
                    ResultMessage(
                        subtype="success",
                        duration_ms=100,
                        duration_api_ms=80,
                        is_error=False,
                        num_turns=1,
                        session_id="test"
                    )
                ]
                
                async for msg in client.receive_response():
                    messages.append(msg)
            
            assert len(messages) == 2


class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    @patch("src.client.SubprocessCLITransport")
    @patch("src.client.parse_message")
    async def test_complete_conversation_flow(self, mock_parse, mock_transport_class):
        """Test a complete conversation flow."""
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        # Mock message stream
        message_queue = []
        
        async def mock_receive():
            for msg in message_queue:
                yield msg
        
        mock_transport.receive_messages = mock_receive
        
        # Setup parse_message mock
        def parse_side_effect(data):
            if data["type"] == "user":
                return UserMessage(content=data.get("content", ""))
            elif data["type"] == "assistant":
                return AssistantMessage(
                    content=[TextBlock(text=data.get("text", ""))],
                    model="claude"
                )
            elif data["type"] == "result":
                return ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=80,
                    is_error=False,
                    num_turns=1,
                    session_id="test"
                )
            return None
        
        mock_parse.side_effect = parse_side_effect
        
        async with ClaudeSDKClient() as client:
            # Send first query
            await client.query("What's 2+2?")
            
            # Simulate response
            message_queue.extend([
                {"type": "assistant", "text": "2+2 equals 4"},
                {"type": "result"}
            ])
            
            # Receive response
            responses = []
            async for msg in client.receive_response():
                responses.append(msg)
            
            assert len(responses) == 2
            assert isinstance(responses[0], AssistantMessage)
            assert isinstance(responses[1], ResultMessage)
            
            # Send follow-up
            message_queue.clear()
            await client.query("What about 3+3?")
            
            # Simulate second response
            message_queue.extend([
                {"type": "assistant", "text": "3+3 equals 6"},
                {"type": "result"}
            ])
            
            # Receive second response
            responses = []
            async for msg in client.receive_response():
                responses.append(msg)
            
            assert len(responses) == 2

    @pytest.mark.asyncio
    @patch("src.client.SubprocessCLITransport")
    async def test_manual_connection_lifecycle(self, mock_transport_class):
        """Test manual connection and disconnection."""
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        client = ClaudeSDKClient()
        
        # Manual connect
        async def message_stream():
            yield {"type": "user", "message": {"content": "Initial"}}
        
        await client.connect(message_stream())
        assert client._transport is not None
        assert mock_transport.connect.called
        
        # Use the client
        await client.query("Follow-up message")
        assert mock_transport.send_request.called
        
        # Manual disconnect
        await client.disconnect()
        assert mock_transport.disconnect.called
        assert client._transport is None