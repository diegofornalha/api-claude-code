"""Complete tests for internal client implementation."""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src._internal.client import InternalClient
from src.sdk_types import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
)


class TestInternalClientInitialization:
    """Test InternalClient initialization."""

    def test_internal_client_init(self):
        """Test InternalClient initialization."""
        client = InternalClient()
        assert client is not None
        # Verify it's a simple initialization with no state
        assert not hasattr(client, "transport")
        assert not hasattr(client, "options")


class TestProcessQuery:
    """Test process_query method."""

    @pytest.mark.asyncio
    @patch("src._internal.client.SubprocessCLITransport")
    @patch("src._internal.client.parse_message")
    async def test_process_query_with_string_prompt(self, mock_parse, mock_transport_class):
        """Test process_query with string prompt."""
        # Setup transport mock
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        # Mock receive_messages
        async def mock_receive():
            yield {"type": "user", "content": "Hello"}
            yield {"type": "assistant", "content": "Hi there"}
            yield {"type": "result", "subtype": "success"}
        
        mock_transport.receive_messages = mock_receive
        
        # Mock parse_message
        mock_parse.side_effect = [
            UserMessage(content="Hello"),
            AssistantMessage(content=[TextBlock(text="Hi there")], model="claude"),
            ResultMessage(
                subtype="success",
                duration_ms=100,
                duration_api_ms=80,
                is_error=False,
                num_turns=1,
                session_id="test"
            )
        ]
        
        # Execute
        client = InternalClient()
        options = ClaudeCodeOptions(model="claude-3-sonnet")
        
        messages = []
        async for msg in client.process_query("Hello Claude", options):
            messages.append(msg)
        
        # Verify
        assert len(messages) == 3
        assert isinstance(messages[0], UserMessage)
        assert isinstance(messages[1], AssistantMessage)
        assert isinstance(messages[2], ResultMessage)
        
        # Verify transport was created with correct parameters
        mock_transport_class.assert_called_once_with(
            prompt="Hello Claude",
            options=options,
            close_stdin_after_prompt=True
        )
        
        # Verify transport lifecycle
        assert mock_transport.connect.called
        assert mock_transport.disconnect.called

    @pytest.mark.asyncio
    @patch("src._internal.client.SubprocessCLITransport")
    @patch("src._internal.client.parse_message")
    async def test_process_query_with_async_iterable(self, mock_parse, mock_transport_class):
        """Test process_query with async iterable prompt."""
        # Setup transport mock
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        # Mock receive_messages
        async def mock_receive():
            yield {"type": "assistant", "content": "Response"}
        
        mock_transport.receive_messages = mock_receive
        
        # Mock parse_message
        mock_parse.return_value = AssistantMessage(
            content=[TextBlock(text="Response")],
            model="claude"
        )
        
        # Create async iterable prompt
        async def prompt_stream():
            yield {"message": "1"}
            yield {"message": "2"}
        
        # Execute
        client = InternalClient()
        options = ClaudeCodeOptions()
        
        messages = []
        async for msg in client.process_query(prompt_stream(), options):
            messages.append(msg)
        
        # Verify
        assert len(messages) == 1
        assert isinstance(messages[0], AssistantMessage)
        
        # Verify transport was created with async iterable
        call_args = mock_transport_class.call_args
        assert hasattr(call_args[1]["prompt"], "__aiter__")

    @pytest.mark.asyncio
    @patch("src._internal.client.parse_message")
    async def test_process_query_with_custom_transport(self, mock_parse):
        """Test process_query with custom transport provided."""
        # Create custom transport mock
        custom_transport = AsyncMock()
        
        # Mock receive_messages
        async def mock_receive():
            yield {"type": "system", "subtype": "info", "data": "test"}
        
        custom_transport.receive_messages = mock_receive
        
        # Mock parse_message
        from src.sdk_types import SystemMessage
        mock_parse.return_value = SystemMessage(subtype="info", data={"data": "test"})
        
        # Execute
        client = InternalClient()
        options = ClaudeCodeOptions()
        
        messages = []
        async for msg in client.process_query("test", options, transport=custom_transport):
            messages.append(msg)
        
        # Verify
        assert len(messages) == 1
        assert isinstance(messages[0], SystemMessage)
        
        # Verify custom transport was used
        assert custom_transport.connect.called
        assert custom_transport.disconnect.called
        
        # Verify SubprocessCLITransport was NOT created
        with patch("src._internal.client.SubprocessCLITransport") as mock_transport_class:
            mock_transport_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("src._internal.client.SubprocessCLITransport")
    @patch("src._internal.client.parse_message")
    async def test_process_query_disconnect_on_error(self, mock_parse, mock_transport_class):
        """Test that transport is disconnected even on error."""
        # Setup transport mock
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        # Mock receive_messages to raise error
        async def mock_receive():
            yield {"type": "message"}
            raise RuntimeError("Test error")
        
        mock_transport.receive_messages = mock_receive
        
        # Mock parse_message to raise on first call
        mock_parse.side_effect = RuntimeError("Parse error")
        
        # Execute
        client = InternalClient()
        options = ClaudeCodeOptions()
        
        with pytest.raises(RuntimeError) as exc_info:
            async for _ in client.process_query("test", options):
                pass
        
        assert "Parse error" in str(exc_info.value)
        
        # Verify transport was still disconnected
        assert mock_transport.connect.called
        assert mock_transport.disconnect.called

    @pytest.mark.asyncio
    @patch("src._internal.client.SubprocessCLITransport")
    @patch("src._internal.client.parse_message")
    async def test_process_query_full_iteration(self, mock_parse, mock_transport_class):
        """Test that transport is disconnected after full iteration."""
        # Setup transport mock
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        # Mock receive_messages
        async def mock_receive():
            yield {"type": "message1"}
            yield {"type": "message2"}
            yield {"type": "message3"}
        
        mock_transport.receive_messages = mock_receive
        
        # Mock parse_message
        mock_parse.side_effect = [
            UserMessage(content="1"),
            UserMessage(content="2"),
            UserMessage(content="3"),
        ]
        
        # Execute - consume all messages
        client = InternalClient()
        options = ClaudeCodeOptions()
        
        messages = []
        async for msg in client.process_query("test", options):
            messages.append(msg)
        
        # Verify all messages were received
        assert len(messages) == 3
        
        # Verify transport was connected and disconnected
        assert mock_transport.connect.called
        assert mock_transport.disconnect.called

    @pytest.mark.asyncio
    @patch("src._internal.client.SubprocessCLITransport")
    async def test_process_query_with_options_passed_to_transport(self, mock_transport_class):
        """Test that options are correctly passed to transport."""
        # Setup transport mock
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        # Mock empty receive
        async def mock_receive():
            return
            yield  # Empty generator
        
        mock_transport.receive_messages = mock_receive
        
        # Create options with specific values
        options = ClaudeCodeOptions(
            model="claude-3-opus",
            max_turns=10,
            system_prompt="Custom prompt",
            cwd="/custom/dir",
            allowed_tools=["tool1", "tool2"],
            permission_mode="auto"
        )
        
        # Execute
        client = InternalClient()
        
        messages = []
        async for msg in client.process_query("test", options):
            messages.append(msg)
        
        # Verify options were passed to transport
        mock_transport_class.assert_called_once()
        call_args = mock_transport_class.call_args
        
        assert call_args[1]["options"] is options
        assert call_args[1]["options"].model == "claude-3-opus"
        assert call_args[1]["options"].max_turns == 10
        assert call_args[1]["close_stdin_after_prompt"] is True

    @pytest.mark.asyncio
    @patch("src._internal.client.SubprocessCLITransport")
    @patch("src._internal.client.parse_message")
    async def test_process_query_multiple_messages_yielded(self, mock_parse, mock_transport_class):
        """Test processing multiple messages in sequence."""
        # Setup transport mock
        mock_transport = AsyncMock()
        mock_transport_class.return_value = mock_transport
        
        # Mock receive_messages with many messages
        async def mock_receive():
            for i in range(10):
                yield {"type": f"message_{i}", "index": i}
        
        mock_transport.receive_messages = mock_receive
        
        # Mock parse_message to return different message types
        def parse_side_effect(data):
            index = data["index"]
            if index % 3 == 0:
                return UserMessage(content=f"User {index}")
            elif index % 3 == 1:
                return AssistantMessage(
                    content=[TextBlock(text=f"Assistant {index}")],
                    model="claude"
                )
            else:
                return SystemMessage(subtype="info", data={"index": index})
        
        mock_parse.side_effect = parse_side_effect
        
        # Execute
        client = InternalClient()
        options = ClaudeCodeOptions()
        
        messages = []
        async for msg in client.process_query("test", options):
            messages.append(msg)
        
        # Verify
        assert len(messages) == 10
        
        # Check message type distribution
        user_msgs = [m for m in messages if isinstance(m, UserMessage)]
        assistant_msgs = [m for m in messages if isinstance(m, AssistantMessage)]
        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        
        assert len(user_msgs) == 4  # indices 0, 3, 6, 9
        assert len(assistant_msgs) == 3  # indices 1, 4, 7
        assert len(system_msgs) == 3  # indices 2, 5, 8

    @pytest.mark.asyncio
    async def test_process_query_transport_lifecycle(self):
        """Test complete transport lifecycle in process_query."""
        # Create a custom transport to track lifecycle
        class LifecycleTransport:
            def __init__(self):
                self.events = []
            
            async def connect(self):
                self.events.append("connect")
            
            async def disconnect(self):
                self.events.append("disconnect")
            
            async def receive_messages(self):
                self.events.append("receive_start")
                yield {"type": "test"}
                self.events.append("receive_end")
            
            def is_connected(self):
                return "connect" in self.events and "disconnect" not in self.events
        
        transport = LifecycleTransport()
        
        # Execute
        client = InternalClient()
        options = ClaudeCodeOptions()
        
        with patch("src._internal.client.parse_message") as mock_parse:
            mock_parse.return_value = UserMessage(content="test")
            
            messages = []
            async for msg in client.process_query("test", options, transport=transport):
                messages.append(msg)
        
        # Verify lifecycle
        assert transport.events == [
            "connect",
            "receive_start",
            "receive_end",
            "disconnect"
        ]