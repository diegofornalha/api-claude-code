"""Pytest configuration and fixtures."""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from config.settings import get_settings, reload_settings
from server import app
from claude_handler import ClaudeHandler


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_env_vars(temp_dir: Path):
    """Set up test environment variables."""
    test_env = {
        "API_ENV": "testing",
        "API_DEBUG": "true",
        "SECRET_KEY": "test-secret-key-at-least-32-characters-long",
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": str(temp_dir / "test.log"),
        "CLAUDE_SDK_PATH": str(temp_dir / "mock-sdk"),
        "REDIS_ENABLED": "false",
        "RATE_LIMIT_ENABLED": "false",
        "FEATURE_AUTH_ENABLED": "false",
    }
    
    # Backup original env vars
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    # Create mock SDK directory
    mock_sdk_dir = temp_dir / "mock-sdk"
    mock_sdk_dir.mkdir()
    
    yield test_env
    
    # Restore original env vars
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def test_settings(test_env_vars):
    """Get test settings with reload."""
    settings = reload_settings()
    yield settings
    # Clear cache after test
    get_settings.cache_clear()


@pytest.fixture
def test_client(test_settings) -> Generator[TestClient, None, None]:
    """Create test client for sync tests."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client(test_settings) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_claude_handler(test_settings):
    """Create mock Claude handler for testing."""
    handler = ClaudeHandler()
    yield handler


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "message": "Hello, this is a test message",
        "session_id": "test-session-123",
        "stream": True
    }


@pytest.fixture
def sample_session_config():
    """Sample session configuration for testing."""
    return {
        "system_prompt": "You are a helpful test assistant",
        "allowed_tools": ["Read", "Write"],
        "max_turns": 10,
        "permission_mode": "acceptEdits",
        "cwd": "/tmp/test"
    }


@pytest.fixture
def mock_jwt_token(test_settings):
    """Generate mock JWT token for testing."""
    from middleware.auth import JWTAuth
    
    token_data = {
        "sub": "test-user",
        "username": "testuser",
        "scopes": ["read", "write"]
    }
    
    return JWTAuth.create_access_token(token_data)


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture(autouse=True)
def cleanup_sessions(mock_claude_handler):
    """Cleanup sessions after each test."""
    yield
    # Clean up any sessions created during test
    asyncio.run(cleanup_handler_sessions(mock_claude_handler))


async def cleanup_handler_sessions(handler: ClaudeHandler):
    """Cleanup all sessions in handler."""
    session_ids = list(handler.clients.keys())
    for session_id in session_ids:
        try:
            await handler.destroy_session(session_id)
        except Exception:
            pass  # Ignore cleanup errors


class MockClaudeSDKClient:
    """Mock Claude SDK Client for testing."""
    
    def __init__(self, options=None):
        self.options = options
        self.connected = False
        self.messages = []
    
    async def connect(self):
        """Mock connect."""
        self.connected = True
    
    async def disconnect(self):
        """Mock disconnect."""
        self.connected = False
    
    async def query(self, message: str):
        """Mock query."""
        self.messages.append(message)
    
    async def receive_response(self):
        """Mock response generator."""
        from src import AssistantMessage, TextBlock, ResultMessage
        
        # Mock assistant response
        yield AssistantMessage(
            content=[TextBlock(text="This is a mock response to: " + self.messages[-1])]
        )
        
        # Mock result
        yield ResultMessage(
            usage={"input_tokens": 10, "output_tokens": 20},
            total_cost_usd=0.001
        )
    
    async def interrupt(self):
        """Mock interrupt."""
        pass


@pytest.fixture
def mock_claude_sdk_client(monkeypatch):
    """Mock the Claude SDK client."""
    def mock_client_init(options=None):
        return MockClaudeSDKClient(options)
    
    monkeypatch.setattr("claude_handler.ClaudeSDKClient", mock_client_init)
    yield mock_client_init


# Async test markers
pytest_plugins = ["pytest_asyncio"]