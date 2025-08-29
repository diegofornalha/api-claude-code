"""Tests for configuration module."""

import pytest
import os
from pathlib import Path
from config.settings import Settings, get_settings, reload_settings


class TestSettings:
    """Test Settings class."""
    
    def test_default_settings(self, test_env_vars):
        """Test default settings are loaded correctly."""
        settings = reload_settings()
        
        assert settings.api_env == "testing"
        assert settings.api_debug == True
        assert settings.secret_key == "test-secret-key-at-least-32-characters-long"
        assert settings.log_level == "DEBUG"
        assert not settings.redis_enabled
        assert not settings.rate_limit_enabled
    
    def test_cors_origins_parsing(self):
        """Test CORS origins string parsing."""
        # Test string parsing
        os.environ["CORS_ORIGINS"] = "http://localhost:3040,http://localhost:3040,https://example.com"
        settings = reload_settings()
        
        expected_origins = [
            "http://localhost:3040",
            "http://localhost:3040", 
            "https://example.com"
        ]
        assert settings.cors_origins == expected_origins
    
    def test_environment_detection(self, test_env_vars):
        """Test environment detection methods."""
        settings = reload_settings()
        
        assert settings.is_development == False  # testing env
        assert settings.is_production == False
        
        # Test production
        os.environ["API_ENV"] = "production"
        settings = reload_settings()
        assert settings.is_production == True
        assert settings.is_development == False
        
        # Test development
        os.environ["API_ENV"] = "development"
        settings = reload_settings()
        assert settings.is_development == True
        assert settings.is_production == False
    
    def test_redis_url_construction(self, test_env_vars):
        """Test Redis URL construction."""
        os.environ.update({
            "REDIS_HOST": "test-redis",
            "REDIS_PORT": "6380",
            "REDIS_DB": "1",
            "REDIS_PASSWORD": "secret123",
            "REDIS_SSL": "true"
        })
        
        settings = reload_settings()
        expected_url = "rediss://:secret123@test-redis:6380/1"
        assert settings.redis_url == expected_url
    
    def test_redis_url_without_password(self, test_env_vars):
        """Test Redis URL without password."""
        os.environ.update({
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "REDIS_SSL": "false"
        })
        os.environ.pop("REDIS_PASSWORD", None)
        
        settings = reload_settings()
        expected_url = "redis://localhost:6379/0"
        assert settings.redis_url == expected_url
    
    def test_validation_errors(self):
        """Test validation errors for invalid settings."""
        # Test short secret key
        os.environ["SECRET_KEY"] = "short"
        
        with pytest.raises(ValueError, match="at least 32 characters"):
            Settings()
    
    def test_claude_sdk_path_validation(self, test_env_vars, temp_dir):
        """Test Claude SDK path validation."""
        # Valid path (exists)
        valid_path = temp_dir / "valid-sdk"
        valid_path.mkdir()
        
        os.environ["CLAUDE_SDK_PATH"] = str(valid_path)
        settings = reload_settings()
        assert Path(settings.claude_sdk_path) == valid_path.resolve()
        
        # Invalid path (doesn't exist) - should warn but not fail
        invalid_path = temp_dir / "invalid-sdk"
        os.environ["CLAUDE_SDK_PATH"] = str(invalid_path)
        
        with pytest.warns(UserWarning, match="Claude SDK path not found"):
            settings = reload_settings()
            assert Path(settings.claude_sdk_path) == invalid_path.resolve()
    
    def test_log_file_directory_creation(self, temp_dir):
        """Test log file directory creation."""
        log_path = temp_dir / "logs" / "test.log"
        
        os.environ["LOG_FILE"] = str(log_path)
        settings = reload_settings()
        
        # Directory should be created
        assert log_path.parent.exists()
        assert settings.log_file == str(log_path)


class TestSettingsCaching:
    """Test settings caching mechanism."""
    
    def test_settings_cached(self, test_env_vars):
        """Test that settings are cached."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance
        assert settings1 is settings2
    
    def test_settings_reload_clears_cache(self, test_env_vars):
        """Test that reload_settings clears cache."""
        settings1 = get_settings()
        
        # Change environment
        os.environ["API_DEBUG"] = "false"
        
        # Get cached settings (should be old)
        settings2 = get_settings()
        assert settings2.api_debug == True  # Still cached
        
        # Reload settings
        settings3 = reload_settings()
        assert settings3.api_debug == False  # Updated
        
        # New get_settings should return updated
        settings4 = get_settings()
        assert settings4.api_debug == False