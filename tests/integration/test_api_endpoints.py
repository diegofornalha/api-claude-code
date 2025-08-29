"""Integration tests for API endpoints."""

import pytest
import json
from httpx import AsyncClient
from fastapi import status

from models.requests import ChatMessageRequest, SessionConfigRequest


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_root_health_check(self, async_client: AsyncClient):
        """Test root health check endpoint."""
        response = await async_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Claude Chat API"
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test dedicated health endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["service"] == "Claude Chat API"
        assert data["version"] == "2.0.0"


class TestSessionManagement:
    """Test session management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_new_session(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test creating new session."""
        response = await async_client.post("/api/new-session")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data
        assert len(data["session_id"]) > 10  # UUID-like string
    
    @pytest.mark.asyncio
    async def test_create_session_with_config(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test creating session with configuration."""
        config_data = {
            "system_prompt": "You are a helpful test assistant",
            "allowed_tools": ["Read", "Write"],
            "max_turns": 10,
            "permission_mode": "acceptEdits"
        }
        
        response = await async_client.post(
            "/api/session-with-config",
            json=config_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data
    
    @pytest.mark.asyncio
    async def test_get_session_info_not_found(self, async_client: AsyncClient):
        """Test getting info for non-existent session."""
        response = await async_client.get("/api/session/non-existent-session")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_get_session_info_exists(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test getting info for existing session."""
        # First create a session
        create_response = await async_client.post("/api/new-session")
        session_id = create_response.json()["session_id"]
        
        # Then get its info
        response = await async_client.get(f"/api/session/{session_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["session_id"] == session_id
        assert data["active"] == True
        assert "config" in data
        assert "history" in data
    
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, async_client: AsyncClient):
        """Test listing sessions when none exist."""
        response = await async_client.get("/api/sessions")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test listing sessions with existing sessions."""
        # Create a couple of sessions
        session_ids = []
        for i in range(2):
            response = await async_client.post("/api/new-session")
            session_ids.append(response.json()["session_id"])
        
        # List sessions
        response = await async_client.get("/api/sessions")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check session data structure
        for session in data:
            assert session["status"] == "success"
            assert "session_id" in session
            assert session["session_id"] in session_ids
    
    @pytest.mark.asyncio
    async def test_delete_session(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test deleting a session."""
        # Create session
        create_response = await async_client.post("/api/new-session")
        session_id = create_response.json()["session_id"]
        
        # Delete session
        response = await async_client.delete(f"/api/session/{session_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "deleted"
        assert data["session_id"] == session_id
        
        # Verify session is gone
        get_response = await async_client.get(f"/api/session/{session_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_clear_session(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test clearing a session."""
        # Create session
        create_response = await async_client.post("/api/new-session")
        session_id = create_response.json()["session_id"]
        
        # Clear session
        clear_data = {"session_id": session_id}
        response = await async_client.post("/api/clear", json=clear_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cleared"
        assert data["session_id"] == session_id
    
    @pytest.mark.asyncio
    async def test_interrupt_session(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test interrupting a session."""
        # Create session
        create_response = await async_client.post("/api/new-session")
        session_id = create_response.json()["session_id"]
        
        # Interrupt session
        interrupt_data = {"session_id": session_id}
        response = await async_client.post("/api/interrupt", json=interrupt_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "interrupted"
        assert data["session_id"] == session_id


class TestChatEndpoints:
    """Test chat functionality endpoints."""
    
    @pytest.mark.asyncio
    async def test_chat_with_new_session(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test chat endpoint creating new session."""
        chat_data = {
            "message": "Hello, this is a test message",
            "stream": False  # Easier to test non-streaming first
        }
        
        response = await async_client.post("/api/chat", json=chat_data)
        
        # Should return SSE stream
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_chat_with_existing_session(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test chat with existing session."""
        # Create session first
        create_response = await async_client.post("/api/new-session")
        session_id = create_response.json()["session_id"]
        
        # Send chat message
        chat_data = {
            "message": "Hello with existing session",
            "session_id": session_id
        }
        
        response = await async_client.post("/api/chat", json=chat_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Check session ID in response headers
        assert response.headers.get("X-Session-ID") == session_id
    
    @pytest.mark.asyncio
    async def test_chat_streaming_response_format(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test streaming response format."""
        chat_data = {
            "message": "Test streaming response"
        }
        
        response = await async_client.post("/api/chat", json=chat_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Read streaming response
        content = response.content.decode()
        
        # Should contain SSE formatted data
        assert "data: " in content
        
        # Parse SSE events
        events = []
        for line in content.split('\n'):
            if line.startswith('data: '):
                event_data = line[6:]  # Remove "data: " prefix
                if event_data.strip():
                    try:
                        events.append(json.loads(event_data))
                    except json.JSONDecodeError:
                        pass
        
        # Should have at least processing and done events
        assert len(events) >= 2
        
        # Check event structure
        for event in events:
            assert "type" in event
            assert "session_id" in event
    
    @pytest.mark.asyncio
    async def test_chat_invalid_message(self, async_client: AsyncClient):
        """Test chat with invalid message."""
        chat_data = {
            "message": "",  # Empty message
        }
        
        response = await async_client.post("/api/chat", json=chat_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_chat_message_too_long(self, async_client: AsyncClient):
        """Test chat with message too long."""
        chat_data = {
            "message": "x" * 50001,  # Exceeds max length
        }
        
        response = await async_client.post("/api/chat", json=chat_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSessionConfiguration:
    """Test session configuration endpoints."""
    
    @pytest.mark.asyncio
    async def test_update_session_config_valid(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test updating session configuration."""
        # Create session
        create_response = await async_client.post("/api/new-session")
        session_id = create_response.json()["session_id"]
        
        # Update config
        new_config = {
            "system_prompt": "You are now a specialized assistant",
            "allowed_tools": ["Read", "Write", "Edit"],
            "max_turns": 15
        }
        
        response = await async_client.put(
            f"/api/session/{session_id}/config",
            json=new_config
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "updated"
        assert data["session_id"] == session_id
        
        # Verify config was updated
        info_response = await async_client.get(f"/api/session/{session_id}")
        info_data = info_response.json()
        assert info_data["config"]["system_prompt"] == "You are now a specialized assistant"
        assert info_data["config"]["max_turns"] == 15
    
    @pytest.mark.asyncio
    async def test_update_session_config_invalid_session(self, async_client: AsyncClient):
        """Test updating config for non-existent session."""
        config = {
            "system_prompt": "Test prompt"
        }
        
        response = await async_client.put(
            "/api/session/non-existent/config",
            json=config
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_update_session_config_invalid_data(self, async_client: AsyncClient, mock_claude_sdk_client):
        """Test updating config with invalid data."""
        # Create session
        create_response = await async_client.post("/api/new-session")
        session_id = create_response.json()["session_id"]
        
        # Invalid config
        invalid_config = {
            "permission_mode": "invalidMode",  # Invalid permission mode
            "max_turns": -5  # Invalid max turns
        }
        
        response = await async_client.put(
            f"/api/session/{session_id}/config",
            json=invalid_config
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    @pytest.mark.asyncio
    async def test_invalid_session_id_format(self, async_client: AsyncClient):
        """Test endpoints with malformed session IDs."""
        invalid_session_id = "not-a-valid-uuid"
        
        # Test various endpoints
        endpoints = [
            f"/api/session/{invalid_session_id}",
        ]
        
        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            # Should handle gracefully, either 404 or validation error
            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    @pytest.mark.asyncio
    async def test_malformed_json_request(self, async_client: AsyncClient):
        """Test endpoints with malformed JSON."""
        response = await async_client.post(
            "/api/chat",
            content='{"message": "test", "invalid": }',  # Malformed JSON
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """Test endpoints with missing required fields."""
        # Chat without message
        response = await async_client.post("/api/chat", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Session action without session_id
        response = await async_client.post("/api/interrupt", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY