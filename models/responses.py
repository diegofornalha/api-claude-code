"""Response models para a API Claude Chat."""

from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Status possíveis para responses."""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    INTERRUPTED = "interrupted"
    TIMEOUT = "timeout"


class StreamEventType(str, Enum):
    """Tipos de eventos de streaming."""
    PROCESSING = "processing"
    ASSISTANT_TEXT = "assistant_text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    RESULT = "result"
    ERROR = "error"
    DONE = "done"


class BaseResponse(BaseModel):
    """Response base para toda a API."""
    
    status: ResponseStatus = Field(
        description="Status da operação",
        example=ResponseStatus.SUCCESS
    )
    message: Optional[str] = Field(
        None,
        description="Mensagem adicional sobre a operação",
        example="Operation completed successfully"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp da resposta",
        example="2024-01-01T12:00:00Z"
    )


class ErrorResponse(BaseResponse):
    """Response para erros."""
    
    status: Literal[ResponseStatus.ERROR] = ResponseStatus.ERROR
    error_code: Optional[str] = Field(
        None,
        description="Código específico do erro",
        example="VALIDATION_ERROR"
    )
    error_type: Optional[str] = Field(
        None,
        description="Tipo do erro",
        example="ValueError"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalhes adicionais do erro",
        example={"field": "message", "constraint": "min_length"}
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "error_type": "ValueError",
                "details": {
                    "field": "message",
                    "constraint": "Message cannot be empty"
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class SessionResponse(BaseResponse):
    """Response para operações de sessão."""
    
    session_id: str = Field(
        description="ID da sessão",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Session created successfully",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class StatusResponse(BaseResponse):
    """Response genérica com status."""
    
    session_id: Optional[str] = Field(
        None,
        description="ID da sessão afetada (se aplicável)",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class StreamEvent(BaseModel):
    """Evento SSE para streaming."""
    
    type: StreamEventType = Field(
        description="Tipo do evento",
        example=StreamEventType.ASSISTANT_TEXT
    )
    session_id: str = Field(
        description="ID da sessão",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    content: Optional[str] = Field(
        None,
        description="Conteúdo da mensagem (para eventos de texto)",
        example="Olá! Como posso ajudar?"
    )
    tool: Optional[str] = Field(
        None,
        description="Nome da ferramenta (para eventos tool_use)",
        example="Read"
    )
    tool_id: Optional[str] = Field(
        None,
        description="ID da ferramenta (para eventos tool_result)",
        example="toolu_123"
    )
    error: Optional[str] = Field(
        None,
        description="Mensagem de erro (para eventos de erro)",
        example="Session timeout"
    )
    input_tokens: Optional[int] = Field(
        None,
        description="Tokens de entrada (para eventos result)",
        example=150
    )
    output_tokens: Optional[int] = Field(
        None,
        description="Tokens de saída (para eventos result)",
        example=250
    )
    cost_usd: Optional[float] = Field(
        None,
        description="Custo em USD (para eventos result)",
        example=0.0025
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "type": "assistant_text",
                    "session_id": "uuid",
                    "content": "Aqui está a resposta..."
                },
                {
                    "type": "tool_use",
                    "session_id": "uuid",
                    "tool": "Read",
                    "tool_id": "toolu_123"
                },
                {
                    "type": "result",
                    "session_id": "uuid",
                    "input_tokens": 150,
                    "output_tokens": 250,
                    "cost_usd": 0.0025
                }
            ]
        }


class SessionConfigInfo(BaseModel):
    """Informações de configuração de uma sessão."""
    
    system_prompt: Optional[str] = Field(
        None,
        description="System prompt da sessão"
    )
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="Ferramentas permitidas"
    )
    max_turns: Optional[int] = Field(
        None,
        description="Máximo de turnos"
    )
    permission_mode: str = Field(
        description="Modo de permissão"
    )
    cwd: Optional[str] = Field(
        None,
        description="Diretório de trabalho"
    )
    created_at: datetime = Field(
        description="Data de criação da sessão"
    )


class SessionHistoryInfo(BaseModel):
    """Informações de histórico de uma sessão."""
    
    message_count: int = Field(
        description="Número de mensagens na sessão",
        example=15
    )
    total_tokens: int = Field(
        description="Total de tokens usados",
        example=2500
    )
    total_cost: float = Field(
        description="Custo total em USD",
        example=0.025
    )
    last_activity: Optional[datetime] = Field(
        None,
        description="Última atividade na sessão"
    )


class SessionInfoResponse(BaseResponse):
    """Informações detalhadas de uma sessão."""
    
    session_id: str = Field(
        description="ID da sessão"
    )
    active: bool = Field(
        description="Se a sessão está ativa"
    )
    config: SessionConfigInfo = Field(
        description="Configuração da sessão"
    )
    history: SessionHistoryInfo = Field(
        description="Histórico da sessão"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "session_id": "uuid",
                "active": True,
                "config": {
                    "system_prompt": "Você é um assistente útil",
                    "allowed_tools": ["Read", "Write"],
                    "max_turns": 20,
                    "permission_mode": "acceptEdits",
                    "cwd": "/home/user",
                    "created_at": "2024-01-01T10:00:00Z"
                },
                "history": {
                    "message_count": 10,
                    "total_tokens": 1500,
                    "total_cost": 0.015,
                    "last_activity": "2024-01-01T12:00:00Z"
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class SessionListResponse(BaseResponse):
    """Lista de sessões."""
    
    sessions: List[SessionInfoResponse] = Field(
        description="Lista de sessões",
        default_factory=list
    )
    total: int = Field(
        description="Total de sessões disponíveis",
        example=25
    )
    limit: int = Field(
        description="Limite aplicado",
        example=20
    )
    offset: int = Field(
        description="Offset aplicado",
        example=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "sessions": [],
                "total": 25,
                "limit": 20,
                "offset": 0,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class HealthResponse(BaseResponse):
    """Response do health check."""
    
    service: str = Field(
        description="Nome do serviço",
        example="Claude Chat API"
    )
    version: str = Field(
        description="Versão da API",
        example="2.0.0"
    )
    uptime_seconds: Optional[float] = Field(
        None,
        description="Tempo de atividade em segundos",
        example=3600.5
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalhes adicionais do sistema"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "service": "Claude Chat API",
                "version": "2.0.0",
                "uptime_seconds": 3600.5,
                "details": {
                    "claude_sdk_version": "0.0.21",
                    "python_version": "3.11.0",
                    "environment": "production"
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class AuthResponse(BaseResponse):
    """Response de autenticação."""
    
    access_token: str = Field(
        description="Token de acesso JWT",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo do token",
        example="bearer"
    )
    expires_in: int = Field(
        description="Tempo de expiração em segundos",
        example=3600
    )
    expires_at: datetime = Field(
        description="Data/hora de expiração do token",
        example="2024-01-01T13:00:00Z"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": "2024-01-01T13:00:00Z",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class ChatResponse(BaseResponse):
    """Response para chat não-streaming."""
    
    session_id: str = Field(
        description="ID da sessão utilizada"
    )
    response_text: str = Field(
        description="Texto completo da resposta"
    )
    input_tokens: Optional[int] = Field(
        None,
        description="Tokens de entrada utilizados"
    )
    output_tokens: Optional[int] = Field(
        None,
        description="Tokens de saída gerados"
    )
    cost_usd: Optional[float] = Field(
        None,
        description="Custo da operação em USD"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="Ferramentas utilizadas na resposta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "session_id": "uuid",
                "response_text": "Aqui está a resposta completa...",
                "input_tokens": 150,
                "output_tokens": 300,
                "cost_usd": 0.003,
                "tools_used": ["Read", "Write"],
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }