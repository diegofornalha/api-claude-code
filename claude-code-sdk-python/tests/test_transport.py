"""Complete tests for transport module to achieve 100% coverage."""

from collections.abc import AsyncIterator
from typing import Any

import pytest

from src._internal.transport import Transport


class TestTransportAbstractClass:
    """Test Transport abstract base class."""

    def test_transport_is_abstract(self):
        """Test that Transport cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            Transport()
        assert "Can't instantiate abstract class" in str(exc_info.value)

    def test_transport_requires_all_methods(self):
        """Test that subclasses must implement all abstract methods."""
        
        # Create incomplete implementation
        class IncompleteTransport(Transport):
            async def connect(self) -> None:
                pass
        
        # Should raise TypeError because not all methods are implemented
        with pytest.raises(TypeError) as exc_info:
            IncompleteTransport()
        assert "Can't instantiate abstract class" in str(exc_info.value)

    def test_transport_complete_implementation(self):
        """Test that complete implementation can be instantiated."""
        
        class CompleteTransport(Transport):
            def __init__(self):
                self.connected = False
            
            async def connect(self) -> None:
                self.connected = True
            
            async def disconnect(self) -> None:
                self.connected = False
            
            async def send_request(
                self, messages: list[dict[str, Any]], options: dict[str, Any]
            ) -> None:
                pass
            
            async def receive_messages(self) -> AsyncIterator[dict[str, Any]]:
                yield {"type": "test"}
            
            def is_connected(self) -> bool:
                return self.connected
        
        # Should instantiate without error
        transport = CompleteTransport()
        assert transport is not None
        assert not transport.is_connected()

    @pytest.mark.asyncio
    async def test_transport_methods_behavior(self):
        """Test that implemented methods work as expected."""
        
        class TestTransport(Transport):
            def __init__(self):
                self.connected = False
                self.messages = []
                self.received_requests = []
            
            async def connect(self) -> None:
                self.connected = True
            
            async def disconnect(self) -> None:
                self.connected = False
            
            async def send_request(
                self, messages: list[dict[str, Any]], options: dict[str, Any]
            ) -> None:
                self.received_requests.append({
                    "messages": messages,
                    "options": options
                })
            
            async def receive_messages(self) -> AsyncIterator[dict[str, Any]]:
                for msg in self.messages:
                    yield msg
            
            def is_connected(self) -> bool:
                return self.connected
        
        transport = TestTransport()
        
        # Test initial state
        assert not transport.is_connected()
        
        # Test connect
        await transport.connect()
        assert transport.is_connected()
        
        # Test send_request
        test_messages = [{"content": "test"}]
        test_options = {"session_id": "123"}
        await transport.send_request(test_messages, test_options)
        assert len(transport.received_requests) == 1
        assert transport.received_requests[0]["messages"] == test_messages
        assert transport.received_requests[0]["options"] == test_options
        
        # Test receive_messages
        transport.messages = [{"type": "msg1"}, {"type": "msg2"}]
        received = []
        async for msg in transport.receive_messages():
            received.append(msg)
        assert len(received) == 2
        assert received[0]["type"] == "msg1"
        
        # Test disconnect
        await transport.disconnect()
        assert not transport.is_connected()

    def test_transport_inheritance(self):
        """Test that Transport properly inherits from ABC."""
        from abc import ABC
        assert issubclass(Transport, ABC)

    def test_transport_module_exports(self):
        """Test that module exports Transport correctly."""
        from src._internal.transport import __all__
        assert "Transport" in __all__
        assert len(__all__) == 1

    @pytest.mark.asyncio
    async def test_custom_transport_with_state(self):
        """Test custom transport implementation with state management."""
        
        class StatefulTransport(Transport):
            def __init__(self):
                self.state = "disconnected"
                self.message_queue = []
                self.send_count = 0
                self.receive_count = 0
            
            async def connect(self) -> None:
                if self.state == "disconnected":
                    self.state = "connected"
                else:
                    raise RuntimeError("Already connected")
            
            async def disconnect(self) -> None:
                if self.state == "connected":
                    self.state = "disconnected"
                    self.message_queue.clear()
                else:
                    raise RuntimeError("Not connected")
            
            async def send_request(
                self, messages: list[dict[str, Any]], options: dict[str, Any]
            ) -> None:
                if self.state != "connected":
                    raise RuntimeError("Not connected")
                self.send_count += 1
                self.message_queue.extend(messages)
            
            async def receive_messages(self) -> AsyncIterator[dict[str, Any]]:
                if self.state != "connected":
                    raise RuntimeError("Not connected")
                while self.message_queue:
                    self.receive_count += 1
                    yield self.message_queue.pop(0)
            
            def is_connected(self) -> bool:
                return self.state == "connected"
        
        transport = StatefulTransport()
        
        # Test state transitions
        assert transport.state == "disconnected"
        await transport.connect()
        assert transport.state == "connected"
        
        # Test sending messages
        await transport.send_request([{"msg": "1"}, {"msg": "2"}], {})
        assert transport.send_count == 1
        assert len(transport.message_queue) == 2
        
        # Test receiving messages
        received = []
        async for msg in transport.receive_messages():
            received.append(msg)
        assert len(received) == 2
        assert transport.receive_count == 2
        
        # Test disconnect
        await transport.disconnect()
        assert transport.state == "disconnected"
        assert len(transport.message_queue) == 0
        
        # Test error on operations when disconnected
        with pytest.raises(RuntimeError):
            await transport.send_request([], {})

    def test_transport_method_signatures(self):
        """Test that Transport methods have correct signatures."""
        import inspect
        
        # Check connect signature
        connect_sig = inspect.signature(Transport.connect)
        assert len(connect_sig.parameters) == 1  # self
        assert connect_sig.return_annotation == None
        
        # Check disconnect signature
        disconnect_sig = inspect.signature(Transport.disconnect)
        assert len(disconnect_sig.parameters) == 1  # self
        assert disconnect_sig.return_annotation == None
        
        # Check send_request signature
        send_sig = inspect.signature(Transport.send_request)
        assert len(send_sig.parameters) == 3  # self, messages, options
        assert "messages" in send_sig.parameters
        assert "options" in send_sig.parameters
        
        # Check receive_messages signature
        receive_sig = inspect.signature(Transport.receive_messages)
        assert len(receive_sig.parameters) == 1  # self
        
        # Check is_connected signature
        connected_sig = inspect.signature(Transport.is_connected)
        assert len(connected_sig.parameters) == 1  # self
        assert connected_sig.return_annotation == bool

    @pytest.mark.asyncio
    async def test_transport_async_iterator_protocol(self):
        """Test that receive_messages properly implements async iterator protocol."""
        
        class IteratorTransport(Transport):
            def __init__(self):
                self.connected = True
            
            async def connect(self) -> None:
                pass
            
            async def disconnect(self) -> None:
                pass
            
            async def send_request(
                self, messages: list[dict[str, Any]], options: dict[str, Any]
            ) -> None:
                pass
            
            async def receive_messages(self) -> AsyncIterator[dict[str, Any]]:
                # Test yielding multiple messages
                for i in range(3):
                    yield {"index": i}
            
            def is_connected(self) -> bool:
                return self.connected
        
        transport = IteratorTransport()
        
        # Test that receive_messages returns an async iterator
        iterator = transport.receive_messages()
        assert hasattr(iterator, "__aiter__")
        assert hasattr(iterator, "__anext__")
        
        # Test iteration
        messages = []
        async for msg in transport.receive_messages():
            messages.append(msg)
        
        assert len(messages) == 3
        assert messages[0]["index"] == 0
        assert messages[2]["index"] == 2