"""Tests for Pydantic models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models.requests import (
    ChatMessageRequest,
    SessionConfigRequest, 
    SessionActionRequest,
    AuthRequest,
    HealthCheckRequest
)
from models.responses import (
    ErrorResponse,
    SessionResponse,
    StatusResponse,
    StreamEvent,
    SessionInfoResponse,
    HealthResponse,
    AuthResponse,
    ChatResponse
)


class TestRequestModels:
    """Test request models validation."""
    
    def test_chat_message_request_valid(self):
        """Test valid chat message request."""
        data = {
            "message": "Hello, how are you?",
            "session_id": "test-session-123",
            "stream": True
        }
        
        request = ChatMessageRequest(**data)
        assert request.message == "Hello, how are you?"
        assert request.session_id == "test-session-123"
        assert request.stream == True
    
    def test_chat_message_request_strips_whitespace(self):
        """Test message whitespace is stripped."""
        data = {
            "message": "   Hello world   ",
        }
        
        request = ChatMessageRequest(**data)
        assert request.message == "Hello world"
    
    def test_chat_message_request_empty_message_fails(self):
        """Test empty message validation fails."""
        data = {
            "message": "",
        }
        
        with pytest.raises(ValidationError, match="Message cannot be empty"):
            ChatMessageRequest(**data)
    
    def test_chat_message_request_whitespace_only_fails(self):
        """Test whitespace-only message fails."""
        data = {
            "message": "   \n\t   ",
        }
        
        with pytest.raises(ValidationError, match="Message cannot be empty"):
            ChatMessageRequest(**data)
    
    def test_chat_message_request_too_long_fails(self):
        """Test message too long fails validation."""
        data = {
            "message": "x" * 50001,  # Max is 50000
        }
        
        with pytest.raises(ValidationError):
            ChatMessageRequest(**data)
    
    def test_session_config_request_valid(self):
        """Test valid session config request."""
        data = {
            "system_prompt": "You are helpful",
            "allowed_tools": ["Read", "Write", "Edit"],
            "max_turns": 20,
            "permission_mode": "acceptEdits",
            "cwd": "/home/user/project",
            "timeout_seconds": 300
        }
        
        request = SessionConfigRequest(**data)
        assert request.system_prompt == "You are helpful"
        assert request.allowed_tools == ["Read", "Write", "Edit"]
        assert request.max_turns == 20
        assert request.permission_mode == "acceptEdits"
    
    def test_session_config_request_invalid_permission_mode(self):
        """Test invalid permission mode fails."""
        data = {
            "permission_mode": "invalidMode"
        }
        
        with pytest.raises(ValidationError, match="Permission mode must be one of"):
            SessionConfigRequest(**data)
    
    def test_session_config_request_invalid_tools(self):
        """Test invalid tools fail validation."""
        data = {
            "allowed_tools": ["Read", "Write", "InvalidTool"]
        }
        
        with pytest.raises(ValidationError, match="Invalid tools"):
            SessionConfigRequest(**data)
    
    def test_session_config_request_max_turns_validation(self):
        """Test max turns validation."""
        # Too low
        with pytest.raises(ValidationError):
            SessionConfigRequest(max_turns=0)
        
        # Too high
        with pytest.raises(ValidationError):
            SessionConfigRequest(max_turns=101)
        
        # Valid
        request = SessionConfigRequest(max_turns=50)
        assert request.max_turns == 50
    
    def test_session_action_request_valid(self):
        """Test valid session action request."""
        data = {
            "session_id": "test-session-123",
            "force": True
        }
        
        request = SessionActionRequest(**data)
        assert request.session_id == "test-session-123"
        assert request.force == True
    
    def test_session_action_request_defaults(self):
        """Test session action request defaults."""
        data = {
            "session_id": "test-session-123"
        }
        
        request = SessionActionRequest(**data)
        assert request.force == False  # Default
    
    def test_auth_request_valid_password(self):
        """Test valid password auth request."""
        data = {
            "username": "testuser",
            "password": "securepassword123",
            "expires_in": 7200
        }
        
        request = AuthRequest(**data)
        assert request.username == "testuser"
        assert request.password == "securepassword123"
        assert request.expires_in == 7200
    
    def test_auth_request_valid_api_key(self):
        """Test valid API key auth request."""
        data = {
            "api_key": "sk-1234567890abcdef1234567890",
            "expires_in": 3600
        }
        
        request = AuthRequest(**data)
        assert request.api_key == "sk-1234567890abcdef1234567890"
    
    def test_auth_request_expires_in_validation(self):
        """Test expires_in validation."""
        # Too short
        with pytest.raises(ValidationError):
            AuthRequest(expires_in=100)  # Min is 300
        
        # Too long
        with pytest.raises(ValidationError):
            AuthRequest(expires_in=100000)  # Max is 86400
    
    def test_health_check_request_defaults(self):
        """Test health check request defaults."""
        request = HealthCheckRequest()
        assert request.include_details == False
        assert request.check_external == False


class TestResponseModels:
    """Test response models."""
    
    def test_error_response_valid(self):
        """Test valid error response."""
        data = {
            "status": "error",
            "message": "Something went wrong",
            "error_code": "VALIDATION_ERROR",
            "error_type": "ValueError",
            "details": {"field": "message", "issue": "too short"}
        }
        
        response = ErrorResponse(**data)
        assert response.status == "error"
        assert response.message == "Something went wrong"
        assert response.error_code == "VALIDATION_ERROR"
        assert response.details["field"] == "message"
    
    def test_session_response_valid(self):
        """Test valid session response."""
        data = {
            "status": "success",
            "session_id": "test-session-123",
            "message": "Session created"
        }
        
        response = SessionResponse(**data)
        assert response.status == "success"
        assert response.session_id == "test-session-123"
    
    def test_stream_event_assistant_text(self):
        """Test assistant text stream event."""
        data = {
            "type": "assistant_text",
            "session_id": "test-session",
            "content": "Hello there!"
        }
        
        event = StreamEvent(**data)
        assert event.type == "assistant_text"
        assert event.content == "Hello there!"
        assert event.session_id == "test-session"
    
    def test_stream_event_tool_use(self):
        """Test tool use stream event."""
        data = {
            "type": "tool_use",
            "session_id": "test-session",
            "tool": "Read",
            "tool_id": "toolu_123"
        }
        
        event = StreamEvent(**data)
        assert event.type == "tool_use"
        assert event.tool == "Read"
        assert event.tool_id == "toolu_123"
    
    def test_stream_event_result(self):
        """Test result stream event."""
        data = {
            "type": "result",
            "session_id": "test-session",
            "input_tokens": 150,
            "output_tokens": 250,
            "cost_usd": 0.0025
        }
        
        event = StreamEvent(**data)
        assert event.type == "result"
        assert event.input_tokens == 150
        assert event.output_tokens == 250
        assert event.cost_usd == 0.0025
    
    def test_health_response_valid(self):
        """Test valid health response."""
        data = {
            "status": "success",
            "service": "Claude Chat API",
            "version": "2.0.0",
            "uptime_seconds": 3600.5,
            "details": {
                "python_version": "3.11.0",
                "environment": "testing"
            }
        }
        
        response = HealthResponse(**data)
        assert response.service == "Claude Chat API"
        assert response.version == "2.0.0"
        assert response.uptime_seconds == 3600.5
        assert response.details["python_version"] == "3.11.0"
    
    def test_auth_response_valid(self):
        """Test valid auth response."""
        expires_at = datetime.now()
        
        data = {
            "status": "success",
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "expires_in": 3600,
            "expires_at": expires_at
        }
        
        response = AuthResponse(**data)
        assert response.access_token.startswith("eyJ")
        assert response.token_type == "bearer"
        assert response.expires_in == 3600
        assert response.expires_at == expires_at
    
    def test_chat_response_valid(self):
        """Test valid chat response."""
        data = {
            "status": "success",
            "session_id": "test-session",
            "response_text": "Here is my response to your question...",
            "input_tokens": 100,
            "output_tokens": 200,
            "cost_usd": 0.002,
            "tools_used": ["Read", "Write"]
        }
        
        response = ChatResponse(**data)
        assert response.session_id == "test-session"
        assert response.response_text.startswith("Here is my")
        assert response.input_tokens == 100
        assert response.tools_used == ["Read", "Write"]


class TestModelDefaults:
    """Test model default values."""
    
    def test_chat_message_request_defaults(self):
        """Test chat message request defaults."""
        request = ChatMessageRequest(message="Hello")
        
        assert request.session_id is None
        assert request.stream == True  # Default
        assert request.context is None
    
    def test_session_config_request_defaults(self):
        """Test session config request defaults."""
        request = SessionConfigRequest()
        
        assert request.system_prompt is None
        assert request.allowed_tools == []
        assert request.max_turns is None
        assert request.permission_mode == "acceptEdits"
        assert request.cwd is None
        assert request.timeout_seconds is None
    
    def test_auth_response_defaults(self):
        """Test auth response defaults."""
        data = {
            "access_token": "token123",
            "expires_in": 3600,
            "expires_at": datetime.now()
        }
        
        response = AuthResponse(**data)
        assert response.token_type == "bearer"  # Default