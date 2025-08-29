"""Servidor FastAPI para integração com Claude Code SDK."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from fastapi import Path
from typing import Optional, Dict, Any, List
import asyncio
import json
import uuid
import os

from claude_handler import ClaudeHandler, SessionConfig
from config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="Claude Chat API",
    description="""
    ## API de Chat com Claude Code SDK
    
    Esta API fornece integração com o Claude Code SDK para conversas em streaming.
    
    ### Funcionalidades principais:
    
    * **Chat em Streaming** - Respostas em tempo real via Server-Sent Events (SSE)
    * **Gerenciamento de Sessões** - Criar, interromper e limpar sessões de chat
    * **Contexto Persistente** - Mantém histórico de conversas por sessão
    * **Interrupção em Tempo Real** - Pare respostas em andamento instantaneamente
    
    ### Como usar:
    
    1. Crie uma nova sessão com `/api/new-session`
    2. Envie mensagens para `/api/chat` com o `session_id`
    3. Receba respostas em streaming via SSE
    4. Gerencie a sessão com endpoints de controle
    
    ### Formato de Resposta SSE:
    
    As respostas são enviadas como eventos SSE no formato:
    ```
    data: {"type": "content", "content": "texto", "session_id": "uuid"}
    data: {"type": "done", "session_id": "uuid"}
    ```
    """,
    version="1.0.0",
    contact={
        "name": "Suporte API",
        "email": "api@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8990",
            "description": "Servidor de desenvolvimento"
        }
    ],
    tags_metadata=[
        {
            "name": "Chat",
            "description": "Operações de chat com Claude"
        },
        {
            "name": "Sessões",
            "description": "Gerenciamento de sessões de chat"
        },
        {
            "name": "Claude Sessions",
            "description": "Visualização e exportação do histórico de sessões Claude Code"
        },
        {
            "name": "Sistema",
            "description": "Endpoints de sistema e monitoramento"
        }
    ]
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3040", 
        "http://localhost:3039",
        "http://localhost:3041", 
        "http://127.0.0.1:3040",
        "http://127.0.0.1:3039",
        "https://suthub.agentesintegrados.com",
        "http://suthub.agentesintegrados.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers (removido session_viewer - agora em aplicação separada)

# Arquivos estáticos removidos - session viewer agora é aplicação separada

# Handler global
claude_handler = ClaudeHandler()

class ChatMessage(BaseModel):
    """Modelo para mensagem de chat."""
    message: str = Field(
        ...,
        description="Conteúdo da mensagem a ser enviada para Claude",
        example="Olá, como você pode me ajudar hoje?"
    )
    session_id: Optional[str] = Field(
        None,
        description="ID da sessão. Se não fornecido, será gerado automaticamente",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Explique o que é Machine Learning",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class SessionAction(BaseModel):
    """Modelo para ações em sessões."""
    session_id: str = Field(
        ...,
        description="ID único da sessão",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: str = Field(..., description="Status da API", example="ok")
    service: str = Field(..., description="Nome do serviço", example="Claude Chat API")

class SessionResponse(BaseModel):
    """Resposta para operações de sessão."""
    session_id: str = Field(..., description="ID da sessão", example="550e8400-e29b-41d4-a716-446655440000")

class StatusResponse(BaseModel):
    """Resposta genérica com status."""
    status: str = Field(..., description="Status da operação", example="success")
    session_id: str = Field(..., description="ID da sessão afetada", example="550e8400-e29b-41d4-a716-446655440000")

class StreamEvent(BaseModel):
    """Evento SSE para streaming."""
    type: str = Field(..., description="Tipo do evento", example="content")
    content: Optional[str] = Field(None, description="Conteúdo da mensagem", example="Olá! Como posso ajudar?")
    session_id: str = Field(..., description="ID da sessão", example="550e8400-e29b-41d4-a716-446655440000")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")

class SessionConfigRequest(BaseModel):
    """Configuração para criar ou atualizar uma sessão."""
    system_prompt: Optional[str] = Field(None, description="System prompt para a sessão", example="Você é um assistente útil")
    allowed_tools: Optional[List[str]] = Field(default_factory=list, description="Ferramentas permitidas", example=["Read", "Write", "Bash"])
    max_turns: Optional[int] = Field(None, description="Número máximo de turnos", example=10)
    permission_mode: str = Field('acceptEdits', description="Modo de permissão para edições", example="acceptEdits")
    cwd: Optional[str] = Field(None, description="Diretório de trabalho", example="/home/user/projeto")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_prompt": "Você é um assistente especializado em Python",
                "allowed_tools": ["Read", "Write", "Bash"],
                "max_turns": 10,
                "permission_mode": "acceptEdits",
                "cwd": "/home/user/projeto"
            }
        }

class SessionInfoResponse(BaseModel):
    """Informações detalhadas de uma sessão."""
    session_id: str
    active: bool
    config: Dict[str, Any]
    history: Dict[str, Any]

@app.get(
    "/",
    tags=["Sistema"],
    summary="Health Check",
    description="Verifica se a API está funcionando corretamente",
    response_description="Status da API",
    responses={
        200: {
            "description": "API funcionando normalmente",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "service": "Claude Chat API"}
                }
            }
        }
    },
    response_model=HealthResponse
)
async def root() -> HealthResponse:
    """Health check endpoint para verificar o status da API."""
    return HealthResponse(status="ok", service="Claude Chat API")

@app.get(
    "/health",
    tags=["Sistema"],
    summary="Health Check Endpoint",
    description="Endpoint específico para Docker healthcheck",
    response_description="Status da API",
    response_model=HealthResponse
)
async def health_check() -> HealthResponse:
    """Health check endpoint específico para Docker."""
    return HealthResponse(status="ok", service="Claude Chat API")

@app.post(
    "/api/chat",
    tags=["Chat"],
    summary="Enviar Mensagem",
    description="""Envia uma mensagem para Claude e recebe a resposta em streaming via SSE.
    
    As respostas são enviadas como Server-Sent Events (SSE) permitindo recebimento em tempo real.
    Cada chunk de resposta é enviado como um evento 'data' no formato JSON.
    """,
    response_description="Stream SSE com resposta de Claude",
    responses={
        200: {
            "description": "Stream SSE iniciado com sucesso",
            "content": {
                "text/event-stream": {
                    "example": "data: {\"type\": \"content\", \"content\": \"Olá!\", \"session_id\": \"uuid\"}\n\n"
                }
            }
        },
        500: {
            "description": "Erro no processamento da mensagem"
        }
    }
)
async def send_message(chat_message: ChatMessage) -> StreamingResponse:
    """Envia mensagem para Claude e retorna resposta em streaming."""
    
    # Gera session_id se não fornecido
    session_id = chat_message.session_id or str(uuid.uuid4())
    
    async def generate():
        """Gera stream SSE."""
        try:
            async for response in claude_handler.send_message(
                session_id, 
                chat_message.message
            ):
                # Formato SSE
                data = json.dumps(response)
                yield f"data: {data}\n\n"
                
        except Exception as e:
            error_data = json.dumps({
                "type": "error",
                "error": str(e),
                "session_id": session_id
            })
            yield f"data: {error_data}\n\n"
        finally:
            # Envia evento de fim
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id
        }
    )

@app.post(
    "/api/interrupt",
    tags=["Sessões"],
    summary="Interromper Sessão",
    description="""Interrompe imediatamente a geração de resposta em andamento para uma sessão específica.
    
    Útil quando o usuário deseja parar uma resposta longa ou cancelar uma operação.
    """,
    response_description="Confirmação de interrupção",
    responses={
        200: {
            "description": "Sessão interrompida com sucesso",
            "content": {
                "application/json": {
                    "example": {"status": "interrupted", "session_id": "uuid"}
                }
            }
        },
        404: {
            "description": "Sessão não encontrada"
        }
    },
    response_model=StatusResponse
)
async def interrupt_session(action: SessionAction) -> StatusResponse:
    """Interrompe a execução de uma sessão ativa."""
    success = await claude_handler.interrupt_session(action.session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return StatusResponse(status="interrupted", session_id=action.session_id)

@app.post(
    "/api/clear",
    tags=["Sessões"],
    summary="Limpar Contexto",
    description="""Limpa todo o histórico e contexto de uma sessão, mantendo o session_id.
    
    Após limpar, a sessão continua ativa mas sem histórico de mensagens anteriores.
    """,
    response_description="Confirmação de limpeza",
    responses={
        200: {
            "description": "Contexto limpo com sucesso",
            "content": {
                "application/json": {
                    "example": {"status": "cleared", "session_id": "uuid"}
                }
            }
        }
    },
    response_model=StatusResponse
)
async def clear_session(action: SessionAction) -> StatusResponse:
    """Limpa o contexto e histórico de uma sessão."""
    await claude_handler.clear_session(action.session_id)
    return StatusResponse(status="cleared", session_id=action.session_id)

@app.post(
    "/api/new-session",
    tags=["Sessões"],
    summary="Criar Nova Sessão",
    description="""Cria uma nova sessão de chat com ID único.
    
    Cada sessão mantém seu próprio contexto e histórico de conversas.
    Use o session_id retornado nas próximas chamadas para manter o contexto.
    """,
    response_description="ID da nova sessão criada",
    responses={
        200: {
            "description": "Sessão criada com sucesso",
            "content": {
                "application/json": {
                    "example": {"session_id": "550e8400-e29b-41d4-a716-446655440000"}
                }
            }
        }
    },
    response_model=SessionResponse
)
async def create_new_session() -> SessionResponse:
    """Cria uma nova sessão com ID único."""
    session_id = str(uuid.uuid4())
    await claude_handler.create_session(session_id)
    return SessionResponse(session_id=session_id)

@app.delete(
    "/api/session/{session_id}",
    tags=["Sessões"],
    summary="Deletar Sessão",
    description="""Remove permanentemente uma sessão e todo seu histórico.
    
    Esta ação é irreversível. A sessão e todas as mensagens associadas serão deletadas.
    """,
    response_description="Confirmação de exclusão",
    responses={
        200: {
            "description": "Sessão deletada com sucesso",
            "content": {
                "application/json": {
                    "example": {"status": "deleted", "session_id": "uuid"}
                }
            }
        },
        404: {
            "description": "Sessão não encontrada"
        }
    },
    response_model=StatusResponse
)
async def delete_session(session_id: str = Path(..., description="ID único da sessão a ser deletada")) -> StatusResponse:
    """Remove permanentemente uma sessão."""
    await claude_handler.destroy_session(session_id)
    return StatusResponse(status="deleted", session_id=session_id)

@app.post(
    "/api/session-with-config",
    tags=["Sessões"],
    summary="Criar Sessão com Configuração",
    description="""Cria uma nova sessão com configurações específicas.
    
    Permite definir system prompt, ferramentas permitidas, diretório de trabalho e outras opções.
    """,
    response_description="ID da nova sessão criada",
    responses={
        200: {
            "description": "Sessão criada com configurações",
            "content": {
                "application/json": {
                    "example": {"session_id": "uuid"}
                }
            }
        }
    },
    response_model=SessionResponse
)
async def create_session_with_config(config: SessionConfigRequest) -> SessionResponse:
    """Cria uma sessão com configurações específicas."""
    session_id = str(uuid.uuid4())
    
    session_config = SessionConfig(
        system_prompt=config.system_prompt,
        allowed_tools=config.allowed_tools,
        max_turns=config.max_turns,
        permission_mode=config.permission_mode,
        cwd=config.cwd
    )
    
    await claude_handler.create_session(session_id, session_config)
    return SessionResponse(session_id=session_id)

@app.put(
    "/api/session/{session_id}/config",
    tags=["Sessões"],
    summary="Atualizar Configuração da Sessão",
    description="""Atualiza a configuração de uma sessão existente.
    
    A sessão será recriada com as novas configurações mas o histórico será mantido.
    """,
    response_description="Confirmação de atualização",
    responses={
        200: {
            "description": "Configuração atualizada",
            "content": {
                "application/json": {
                    "example": {"status": "updated", "session_id": "uuid"}
                }
            }
        },
        404: {
            "description": "Sessão não encontrada"
        }
    },
    response_model=StatusResponse
)
async def update_session_config(
    session_id: str = Path(..., description="ID da sessão"),
    config: SessionConfigRequest = ...
) -> StatusResponse:
    """Atualiza configuração de uma sessão."""
    session_config = SessionConfig(
        system_prompt=config.system_prompt,
        allowed_tools=config.allowed_tools,
        max_turns=config.max_turns,
        permission_mode=config.permission_mode,
        cwd=config.cwd
    )
    
    success = await claude_handler.update_session_config(session_id, session_config)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return StatusResponse(status="updated", session_id=session_id)

@app.get(
    "/api/session/{session_id}",
    tags=["Sessões"],
    summary="Obter Informações da Sessão",
    description="""Retorna informações detalhadas sobre uma sessão específica.
    
    Inclui configurações, estatísticas de uso e status.
    """,
    response_description="Informações da sessão",
    responses={
        200: {
            "description": "Informações da sessão",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "uuid",
                        "active": True,
                        "config": {
                            "system_prompt": "...",
                            "allowed_tools": ["Read", "Write"],
                            "created_at": "2024-01-01T00:00:00"
                        },
                        "history": {
                            "message_count": 10,
                            "total_tokens": 1000,
                            "total_cost": 0.05
                        }
                    }
                }
            }
        },
        404: {
            "description": "Sessão não encontrada"
        }
    },
    response_model=SessionInfoResponse
)
async def get_session_info(session_id: str = Path(..., description="ID da sessão")) -> SessionInfoResponse:
    """Obtém informações detalhadas de uma sessão."""
    info = await claude_handler.get_session_info(session_id)
    
    if "error" in info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionInfoResponse(**info)

@app.get(
    "/api/sessions",
    tags=["Sessões"],
    summary="Listar Todas as Sessões",
    description="""Retorna lista de todas as sessões ativas com suas informações.
    
    Útil para monitoramento e gerenciamento de múltiplas conversas.
    """,
    response_description="Lista de sessões",
    responses={
        200: {
            "description": "Lista de sessões ativas",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "session_id": "uuid1",
                            "active": True,
                            "config": {"system_prompt": "..."},
                            "history": {"message_count": 5}
                        }
                    ]
                }
            }
        }
    }
)
async def list_sessions() -> List[SessionInfoResponse]:
    """Lista todas as sessões ativas."""
    sessions = await claude_handler.get_all_sessions()
    return [SessionInfoResponse(**session) for session in sessions]

@app.get(
    "/api/session/{session_id}/history",
    tags=["Sessões"],
    summary="Carregar Histórico da Sessão",
    description="""Carrega o histórico de uma sessão específica do arquivo .jsonl.
    
    Mapeia automaticamente o session_id para o caminho do arquivo físico conforme a convenção:
    - URL: /claude/cc-sdk-chat-chat/[session-id]
    - Arquivo: /home/suthub/.claude/projects/-home-suthub--claude-cc-sdk-chat-chat/[session-id].jsonl
    """,
    response_description="Histórico da sessão em formato estruturado"
)
async def get_session_history(session_id: str):
    """Carrega histórico de uma sessão específica do arquivo .jsonl."""
    import json
    from pathlib import Path
    
    try:
        # Mapeia session_id para caminho do arquivo
        file_path = Path(f"/home/suthub/.claude/projects/-home-suthub--claude-cc-sdk-chat-api/{session_id}.jsonl")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Session history not found: {session_id}")
        
        # Lê e parseia o arquivo .jsonl
        messages = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line.strip())
                        
                        # Converte para formato do frontend
                        if entry.get("type") == "user":
                            messages.append({
                                "role": "user",
                                "content": entry["message"]["content"],
                                "timestamp": entry["timestamp"],
                                "uuid": entry["uuid"]
                            })
                        elif entry.get("type") == "assistant":
                            # Extrai conteúdo de texto do assistant message
                            content = ""
                            if "content" in entry["message"] and isinstance(entry["message"]["content"], list):
                                for block in entry["message"]["content"]:
                                    if block.get("type") == "text":
                                        content += block.get("text", "")
                            
                            messages.append({
                                "role": "assistant",
                                "content": content,
                                "timestamp": entry["timestamp"],
                                "uuid": entry["uuid"],
                                "usage": entry["message"].get("usage", {})
                            })
                    except json.JSONDecodeError as e:
                        continue  # Skip malformed lines
        
        return {
            "session_id": session_id,
            "messages": messages,
            "message_count": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading session history: {str(e)}")


# Endpoints de session viewer removidos - agora em aplicação separada (/viewer/)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, reload=False)