"""Configurações centralizadas da API."""

import os
from pathlib import Path
from typing import List, Optional, Literal
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, validator, field_validator


class Settings(BaseSettings):
    """Configurações centralizadas da API."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="Host da API")
    api_port: int = Field(default=8990, description="Porta da API")
    api_env: Literal["development", "staging", "production"] = Field(default="development")
    api_debug: bool = Field(default=False, description="Modo debug")
    api_title: str = Field(default="Claude Chat API", description="Título da API")
    api_version: str = Field(default="2.0.0", description="Versão da API")
    
    # Security
    secret_key: str = Field(..., min_length=32, description="Chave secreta para JWT")
    jwt_algorithm: str = Field(default="HS256", description="Algoritmo JWT")
    jwt_expiration_hours: int = Field(default=24, ge=1, le=168, description="Expiração JWT em horas")
    api_key_header: str = Field(default="X-API-Key", description="Header da API key")
    
    # CORS
    cors_origins: List[str] = Field(default_factory=list, description="Origins permitidas")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="Métodos permitidos")
    cors_headers: List[str] = Field(default=["Content-Type", "Authorization", "X-API-Key"], description="Headers permitidos")
    cors_credentials: bool = Field(default=True, description="Permite credentials")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Ativar rate limiting")
    rate_limit_default: str = Field(default="100/minute", description="Limite padrão")
    rate_limit_burst: int = Field(default=10, ge=1, description="Burst permitido")
    rate_limit_storage: Literal["memory", "redis"] = Field(default="memory", description="Storage para rate limiting")
    
    # Claude SDK
    claude_sdk_path: str = Field(default="./claude-code-sdk-python", description="Caminho do SDK")
    claude_permission_mode: str = Field(default="acceptEdits", description="Modo de permissão")
    claude_default_cwd: Optional[str] = Field(default=None, description="Diretório padrão")
    claude_max_turns: int = Field(default=20, ge=1, description="Máximo de turnos")
    claude_timeout_seconds: int = Field(default=300, ge=30, description="Timeout em segundos")
    
    # Session Viewer Configuration
    claude_projects_path: str = Field(default="/home/.claude/projects", description="Caminho dos projetos Claude")
    session_viewer_enabled: bool = Field(default=True, description="Ativar Session Viewer")
    
    # Redis Cache
    redis_enabled: bool = Field(default=False, description="Ativar Redis")
    redis_host: str = Field(default="localhost", description="Host Redis")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Porta Redis")
    redis_db: int = Field(default=0, ge=0, le=15, description="Database Redis")
    redis_password: Optional[str] = Field(default=None, description="Senha Redis")
    redis_ssl: bool = Field(default=False, description="SSL Redis")
    redis_pool_size: int = Field(default=10, ge=1, description="Pool size Redis")
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="Nível de log")
    log_format: Literal["json", "text"] = Field(default="json", description="Formato do log")
    log_file: Optional[str] = Field(default=None, description="Arquivo de log")
    log_rotation: str = Field(default="1 day", description="Rotação do log")
    log_retention: str = Field(default="7 days", description="Retenção do log")
    log_compression: bool = Field(default=True, description="Compressão do log")
    
    # Monitoring
    metrics_enabled: bool = Field(default=True, description="Ativar métricas")
    metrics_port: int = Field(default=9090, ge=1, le=65535, description="Porta das métricas")
    health_check_path: str = Field(default="/health", description="Caminho health check")
    health_check_interval: int = Field(default=30, ge=10, description="Intervalo health check")
    
    # Database (Future)
    database_url: Optional[str] = Field(default=None, description="URL do banco")
    database_pool_size: int = Field(default=10, ge=1, description="Pool size do banco")
    database_max_overflow: int = Field(default=20, ge=0, description="Max overflow do banco")
    
    # Session Management
    session_timeout_minutes: int = Field(default=60, ge=5, description="Timeout da sessão em minutos")
    session_max_per_user: int = Field(default=10, ge=1, description="Máximo de sessões por usuário")
    session_cleanup_interval: int = Field(default=300, ge=60, description="Intervalo de limpeza das sessões")
    
    # WebSocket
    ws_enabled: bool = Field(default=True, description="Ativar WebSocket")
    ws_ping_interval: int = Field(default=30, ge=10, description="Intervalo ping WebSocket")
    ws_ping_timeout: int = Field(default=10, ge=5, description="Timeout ping WebSocket")
    ws_max_connections: int = Field(default=1000, ge=1, description="Máximo conexões WebSocket")
    
    # External Services
    sentry_dsn: Optional[str] = Field(default=None, description="DSN do Sentry")
    slack_webhook_url: Optional[str] = Field(default=None, description="Webhook Slack")
    discord_webhook_url: Optional[str] = Field(default=None, description="Webhook Discord")
    
    # Development
    dev_auto_reload: bool = Field(default=True, description="Auto reload em dev")
    dev_cors_allow_all: bool = Field(default=False, description="CORS aberto em dev")
    dev_mock_mode: bool = Field(default=False, description="Modo mock em dev")
    
    # Production
    prod_ssl_redirect: bool = Field(default=True, description="Redirecionar SSL em prod")
    prod_ssl_cert_path: Optional[str] = Field(default=None, description="Caminho certificado SSL")
    prod_ssl_key_path: Optional[str] = Field(default=None, description="Caminho chave SSL")
    
    # Feature Flags
    feature_auth_enabled: bool = Field(default=False, description="Feature: Autenticação")
    feature_cache_enabled: bool = Field(default=False, description="Feature: Cache")
    feature_metrics_enabled: bool = Field(default=True, description="Feature: Métricas")
    feature_websocket_enabled: bool = Field(default=True, description="Feature: WebSocket")
    
    
    @validator('claude_sdk_path')
    def validate_claude_sdk_path(cls, v):
        """Valida se o caminho do SDK existe."""
        path = Path(v).resolve()
        if not path.exists():
            # Em desenvolvimento, apenas avisa
            import warnings
            warnings.warn(f"Claude SDK path not found: {path}")
        return str(path)
    
    @validator('log_file', pre=True)
    def validate_log_file(cls, v):
        """Cria diretório do log se necessário."""
        if v:
            log_path = Path(v)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @property
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento."""
        return self.api_env == "development"
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em produção."""
        return self.api_env == "production"
    
    @property
    def redis_url(self) -> str:
        """Constrói URL do Redis."""
        if self.redis_password:
            auth = f":{self.redis_password}@"
        else:
            auth = ""
        
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        
        # Exemplos para documentação
        schema_extra = {
            "example": {
                "api_host": "0.0.0.0",
                "api_port": 8990,
                "api_env": "development",
                "secret_key": "your-secret-key-here-min-32-chars",
                "cors_origins": ["http://localhost:3040", "http://localhost:3040"],
                "claude_sdk_path": "./claude-code-sdk-python"
            }
        }


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cached das configurações."""
    return Settings()


def reload_settings() -> Settings:
    """Recarrega configurações (útil em testes)."""
    get_settings.cache_clear()
    return get_settings()