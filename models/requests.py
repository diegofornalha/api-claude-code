"""Request models para a API Claude Chat."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ChatMessageRequest(BaseModel):
    """Modelo para requisição de mensagem de chat."""
    
    message: str = Field(
        ..., 
        min_length=1,
        max_length=50000,
        description="Conteúdo da mensagem a ser enviada para Claude",
        example="Olá, como você pode me ajudar hoje?"
    )
    session_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="ID da sessão. Se não fornecido, será gerado automaticamente",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    stream: bool = Field(
        default=True,
        description="Se deve usar streaming para a resposta",
        example=True
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contexto adicional para a mensagem",
        example={"user_id": "123", "conversation_type": "support"}
    )
    
    @validator('message')
    def validate_message_content(cls, v):
        """Valida conteúdo da mensagem."""
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Explique o que é Machine Learning em termos simples",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "stream": True,
                "context": {
                    "user_id": "user123",
                    "conversation_type": "educational"
                }
            }
        }


class SessionConfigRequest(BaseModel):
    """Configuração para criar ou atualizar uma sessão."""
    
    system_prompt: Optional[str] = Field(
        None, 
        max_length=10000,
        description="System prompt para a sessão",
        example="Você é um assistente útil especializado em programação Python"
    )
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="Ferramentas permitidas na sessão",
        example=["Read", "Write", "Bash", "Edit"]
    )
    max_turns: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Número máximo de turnos na conversação",
        example=20
    )
    permission_mode: str = Field(
        default="acceptEdits",
        description="Modo de permissão para edições de arquivos",
        example="acceptEdits"
    )
    cwd: Optional[str] = Field(
        None,
        max_length=500,
        description="Diretório de trabalho para a sessão",
        example="/home/user/projeto"
    )
    timeout_seconds: Optional[int] = Field(
        None,
        ge=30,
        le=3600,
        description="Timeout em segundos para operações",
        example=300
    )
    
    @validator('permission_mode')
    def validate_permission_mode(cls, v):
        """Valida modo de permissão."""
        allowed_modes = ["acceptEdits", "rejectEdits", "confirmEdits"]
        if v not in allowed_modes:
            raise ValueError(f"Permission mode must be one of: {allowed_modes}")
        return v
    
    @validator('allowed_tools')
    def validate_allowed_tools(cls, v):
        """Valida ferramentas permitidas."""
        valid_tools = {
            "Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep",
            "LS", "Task", "WebFetch", "WebSearch", "TodoWrite"
        }
        invalid_tools = set(v) - valid_tools
        if invalid_tools:
            raise ValueError(f"Invalid tools: {invalid_tools}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_prompt": "Você é um assistente especializado em Python e desenvolvimento web",
                "allowed_tools": ["Read", "Write", "Edit", "Bash"],
                "max_turns": 20,
                "permission_mode": "acceptEdits",
                "cwd": "/home/user/projeto",
                "timeout_seconds": 300
            }
        }


class SessionActionRequest(BaseModel):
    """Modelo para ações em sessões (interrupt, clear, delete)."""
    
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID único da sessão",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    force: bool = Field(
        default=False,
        description="Força a ação mesmo se houver operações em andamento",
        example=False
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "force": False
            }
        }


class AuthRequest(BaseModel):
    """Modelo para requisição de autenticação."""
    
    username: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Nome de usuário (opcional para API key auth)",
        example="admin"
    )
    password: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Senha (opcional para API key auth)",
        example="secure_password_123"
    )
    api_key: Optional[str] = Field(
        None,
        min_length=10,
        max_length=200,
        description="API key para autenticação",
        example="sk-1234567890abcdef"
    )
    expires_in: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="Tempo de expiração do token em segundos",
        example=3600
    )
    
    @validator('api_key', 'password', pre=True)
    def validate_credentials(cls, v, field):
        """Valida credenciais sensíveis."""
        if v and len(v.strip()) < field.field_info.min_length:
            raise ValueError(f"{field.name} too short")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "secure_password_123",
                "expires_in": 3600
            }
        }


class HealthCheckRequest(BaseModel):
    """Modelo para requisição de health check."""
    
    include_details: bool = Field(
        default=False,
        description="Incluir detalhes no health check",
        example=False
    )
    check_external: bool = Field(
        default=False,
        description="Verificar serviços externos (Redis, etc)",
        example=False
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "include_details": True,
                "check_external": True
            }
        }


class SessionFilterRequest(BaseModel):
    """Modelo para filtrar sessões."""
    
    active_only: bool = Field(
        default=True,
        description="Mostrar apenas sessões ativas",
        example=True
    )
    created_after: Optional[datetime] = Field(
        None,
        description="Mostrar sessões criadas após esta data",
        example="2024-01-01T00:00:00"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Número máximo de sessões a retornar",
        example=50
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset para paginação",
        example=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "active_only": True,
                "created_after": "2024-01-01T00:00:00",
                "limit": 20,
                "offset": 0
            }
        }