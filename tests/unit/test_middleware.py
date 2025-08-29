"""Tests for middleware components."""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from middleware.auth import JWTAuth, get_current_user, get_current_user_optional
from middleware.rate_limit import create_limiter, get_rate_limit_key, BurstLimiter
from middleware.cors import get_cors_origins, is_origin_allowed, CORSValidator


class TestJWTAuth:
    """Test JWT authentication middleware."""
    
    def test_create_access_token(self, test_settings):
        """Test JWT token creation."""
        data = {"sub": "testuser", "scopes": ["read", "write"]}
        token = JWTAuth.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        assert token.count('.') == 2  # JWT has 3 parts separated by dots
    
    def test_verify_token_valid(self, test_settings):
        """Test valid token verification."""
        data = {"sub": "testuser", "username": "test"}
        token = JWTAuth.create_access_token(data)
        
        payload = JWTAuth.verify_token(token)
        assert payload["sub"] == "testuser"
        assert payload["username"] == "test"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_token_invalid(self, test_settings):
        """Test invalid token verification."""
        with pytest.raises(HTTPException) as exc_info:
            JWTAuth.verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in str(exc_info.value.detail)
    
    def test_verify_token_expired(self, test_settings):
        """Test expired token verification."""
        data = {"sub": "testuser"}
        # Create token with very short expiration
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = JWTAuth.create_access_token(data, expires_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            JWTAuth.verify_token(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "mySecurePassword123"
        hashed = JWTAuth.hash_password(password)
        
        assert hashed != password  # Should be hashed
        assert len(hashed) > 50  # Bcrypt hashes are long
        assert hashed.startswith('$2b$')  # Bcrypt prefix
    
    def test_verify_password(self):
        """Test password verification."""
        password = "mySecurePassword123"
        wrong_password = "wrongPassword"
        
        hashed = JWTAuth.hash_password(password)
        
        assert JWTAuth.verify_password(password, hashed) == True
        assert JWTAuth.verify_password(wrong_password, hashed) == False
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid(self, test_settings):
        """Test get_current_user with valid token."""
        data = {"sub": "testuser", "username": "test"}
        token = JWTAuth.create_access_token(data)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = await get_current_user(credentials)
        assert user["sub"] == "testuser"
        assert user["username"] == "test"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid(self, test_settings):
        """Test get_current_user with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )
        
        with pytest.raises(HTTPException):
            await get_current_user(credentials)
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_none(self, test_settings):
        """Test get_current_user_optional with no token."""
        result = await get_current_user_optional(None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_valid(self, test_settings):
        """Test get_current_user_optional with valid token."""
        data = {"sub": "testuser"}
        token = JWTAuth.create_access_token(data)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = await get_current_user_optional(credentials)
        assert user["sub"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_invalid(self, test_settings):
        """Test get_current_user_optional with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )
        
        result = await get_current_user_optional(credentials)
        assert result is None  # Should return None for invalid token


class TestRateLimiting:
    """Test rate limiting middleware."""
    
    def test_create_limiter_disabled(self, test_settings):
        """Test limiter creation when disabled."""
        limiter = create_limiter()
        assert limiter.enabled == False
    
    def test_get_rate_limit_key_ip_only(self):
        """Test rate limit key generation with IP only."""
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.state = Mock()
        mock_request.state.user = {}
        
        with patch('middleware.rate_limit.get_remote_address', return_value="192.168.1.1"):
            key = get_rate_limit_key(mock_request)
            assert key == "192.168.1.1"
    
    def test_get_rate_limit_key_with_user(self):
        """Test rate limit key generation with authenticated user."""
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.state = Mock()
        mock_request.state.user = {"sub": "testuser"}
        
        with patch('middleware.rate_limit.get_remote_address', return_value="192.168.1.1"):
            key = get_rate_limit_key(mock_request)
            assert key == "192.168.1.1:testuser"
    
    def test_burst_limiter_within_limit(self):
        """Test burst limiter within limit."""
        limiter = BurstLimiter(burst_size=5, window_seconds=60)
        
        # Should allow requests within limit
        for i in range(5):
            assert limiter.check_burst(f"test-key-{i}") == True
    
    def test_burst_limiter_exceed_limit(self):
        """Test burst limiter exceeding limit."""
        limiter = BurstLimiter(burst_size=2, window_seconds=60)
        
        # First two requests should pass
        assert limiter.check_burst("test-key") == True
        assert limiter.check_burst("test-key") == True
        
        # Third should fail
        assert limiter.check_burst("test-key") == False
    
    def test_burst_limiter_window_reset(self):
        """Test burst limiter window reset."""
        limiter = BurstLimiter(burst_size=2, window_seconds=1)  # 1 second window
        
        # Fill up the limit
        assert limiter.check_burst("test-key") == True
        assert limiter.check_burst("test-key") == True
        assert limiter.check_burst("test-key") == False
        
        # Wait for window to reset
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.check_burst("test-key") == True


class TestCORS:
    """Test CORS middleware functionality."""
    
    def test_get_cors_origins_development(self, test_settings):
        """Test CORS origins in development."""
        # Mock development settings
        with patch.object(test_settings, 'is_development', True):
            with patch.object(test_settings, 'dev_cors_allow_all', False):
                with patch.object(test_settings, 'cors_origins', []):
                    origins = get_cors_origins()
                    
                    # Should include default development origins
                    assert "http://localhost:3040" in origins
                    assert "http://localhost:3040" in origins
                    assert "http://127.0.0.1:3040" in origins
    
    def test_get_cors_origins_allow_all(self, test_settings):
        """Test CORS origins with allow all."""
        with patch.object(test_settings, 'is_development', True):
            with patch.object(test_settings, 'dev_cors_allow_all', True):
                origins = get_cors_origins()
                assert origins == ["*"]
    
    def test_is_origin_allowed_explicit(self, test_settings):
        """Test origin checking with explicit origins."""
        with patch('middleware.cors.get_cors_origins', return_value=[
            "http://localhost:3040",
            "https://example.com"
        ]):
            assert is_origin_allowed("http://localhost:3040") == True
            assert is_origin_allowed("https://example.com") == True
            assert is_origin_allowed("http://evil.com") == False
    
    def test_is_origin_allowed_wildcard(self, test_settings):
        """Test origin checking with wildcard."""
        with patch('middleware.cors.get_cors_origins', return_value=["*"]):
            assert is_origin_allowed("http://anywhere.com") == True
            assert is_origin_allowed("https://evil.com") == True
    
    def test_is_origin_allowed_development_localhost(self, test_settings):
        """Test origin checking allows localhost in development."""
        with patch('middleware.cors.get_cors_origins', return_value=[]):
            with patch.object(test_settings, 'is_development', True):
                assert is_origin_allowed("http://localhost:8990") == True
                assert is_origin_allowed("http://127.0.0.1:3040") == True
                assert is_origin_allowed("https://localhost:443") == False  # https not allowed
    
    def test_cors_validator_preflight_valid(self, test_settings):
        """Test CORS validator for valid preflight."""
        with patch('middleware.cors.is_origin_allowed', return_value=True):
            with patch.object(test_settings, 'cors_methods', ["GET", "POST"]):
                with patch.object(test_settings, 'cors_headers', ["Content-Type", "Authorization"]):
                    
                    valid = CORSValidator.validate_preflight(
                        origin="http://localhost:3040",
                        method="POST", 
                        headers="Content-Type,Authorization"
                    )
                    assert valid == True
    
    def test_cors_validator_preflight_invalid_origin(self, test_settings):
        """Test CORS validator with invalid origin."""
        with patch('middleware.cors.is_origin_allowed', return_value=False):
            valid = CORSValidator.validate_preflight(
                origin="http://evil.com",
                method="POST",
                headers="Content-Type"
            )
            assert valid == False
    
    def test_cors_validator_preflight_invalid_method(self, test_settings):
        """Test CORS validator with invalid method."""
        with patch('middleware.cors.is_origin_allowed', return_value=True):
            with patch.object(test_settings, 'cors_methods', ["GET", "POST"]):
                valid = CORSValidator.validate_preflight(
                    origin="http://localhost:3040",
                    method="DELETE",  # Not in allowed methods
                    headers="Content-Type"
                )
                assert valid == False
    
    def test_cors_validator_get_headers(self, test_settings):
        """Test CORS validator header generation."""
        with patch('middleware.cors.is_origin_allowed', return_value=True):
            with patch.object(test_settings, 'cors_methods', ["GET", "POST"]):
                with patch.object(test_settings, 'cors_headers', ["Content-Type"]):
                    with patch.object(test_settings, 'cors_credentials', True):
                        
                        headers = CORSValidator.get_cors_headers("http://localhost:3040")
                        
                        assert headers["Access-Control-Allow-Origin"] == "http://localhost:3040"
                        assert headers["Access-Control-Allow-Credentials"] == "true"
                        assert "GET, POST" in headers["Access-Control-Allow-Methods"]
                        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
                        assert "86400" in headers["Access-Control-Max-Age"]