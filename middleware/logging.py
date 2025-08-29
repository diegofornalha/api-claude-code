"""Middleware de logging para requests HTTP."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from loguru import logger

from config.settings import get_settings

settings = get_settings()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests HTTP."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa request adicionando logging."""
        
        # Gera ID único para o request
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Informações do request
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        method = request.method
        url = str(request.url)
        user_agent = request.headers.get('user-agent', '')
        
        # Log do request de entrada
        logger.info(
            "HTTP Request",
            request_id=request_id,
            method=method,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent[:100] if user_agent else '',
            content_length=request.headers.get('content-length', 0)
        )
        
        try:
            # Processa request
            response = await call_next(request)
            
            # Calcula tempo de processamento
            process_time = time.time() - start_time
            
            # Adiciona headers informativos
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            # Log do response
            self._log_response(
                request_id=request_id,
                method=method, 
                url=url,
                status_code=response.status_code,
                process_time=process_time,
                content_length=response.headers.get('content-length', 0),
                client_ip=client_ip
            )
            
            return response
            
        except Exception as e:
            # Log de erro
            process_time = time.time() - start_time
            
            logger.error(
                "HTTP Request Error",
                request_id=request_id,
                method=method,
                url=url,
                error=str(e),
                error_type=type(e).__name__,
                process_time=process_time,
                client_ip=client_ip
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP real do cliente considerando proxies."""
        # Headers de proxy comuns
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            # Pega o primeiro IP da lista
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # IP direto
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return 'unknown'
    
    def _log_response(
        self,
        request_id: str,
        method: str,
        url: str, 
        status_code: int,
        process_time: float,
        content_length: int,
        client_ip: str
    ):
        """Log estruturado do response."""
        
        # Determina nível do log baseado no status
        if status_code >= 500:
            log_level = "error"
        elif status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"
        
        # Log da resposta
        logger.log(
            log_level.upper(),
            "HTTP Response",
            request_id=request_id,
            method=method,
            url=url,
            status_code=status_code,
            process_time_ms=round(process_time * 1000, 2),
            content_length=content_length,
            client_ip=client_ip,
            slow_request=process_time > 2.0
        )


class StreamingLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware específico para logging de streaming responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa request com logging especial para streaming."""
        
        response = await call_next(request)
        
        # Se é streaming response, adiciona logging especial
        if isinstance(response, StreamingResponse):
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.info(
                "Streaming Response Started",
                request_id=request_id,
                url=str(request.url),
                content_type=response.headers.get('content-type', '')
            )
            
            # Wrapper para o generator de streaming
            original_body_iterator = response.body_iterator
            
            async def logging_body_iterator():
                """Iterator que adiciona logging ao streaming."""
                chunk_count = 0
                total_bytes = 0
                
                async for chunk in original_body_iterator:
                    chunk_count += 1
                    total_bytes += len(chunk) if chunk else 0
                    
                    # Log a cada 100 chunks (para não spammar)
                    if chunk_count % 100 == 0:
                        logger.debug(
                            "Streaming Progress",
                            request_id=request_id,
                            chunks_sent=chunk_count,
                            total_bytes=total_bytes
                        )
                    
                    yield chunk
                
                # Log final do streaming
                logger.info(
                    "Streaming Response Completed",
                    request_id=request_id,
                    total_chunks=chunk_count,
                    total_bytes=total_bytes
                )
            
            response.body_iterator = logging_body_iterator()
        
        return response


def create_logging_middleware(app, streaming_support: bool = True):
    """Factory para criar middleware de logging."""
    
    # Middleware básico sempre
    app.add_middleware(LoggingMiddleware)
    
    # Middleware para streaming se solicitado
    if streaming_support:
        app.add_middleware(StreamingLoggingMiddleware)
    
    return app


class RequestTracker:
    """Utilitário para rastrear requests em andamento."""
    
    def __init__(self):
        self.active_requests = {}
    
    def start_request(self, request_id: str, info: dict):
        """Registra início de request."""
        self.active_requests[request_id] = {
            'start_time': time.time(),
            'info': info
        }
    
    def end_request(self, request_id: str):
        """Finaliza rastreamento do request."""
        if request_id in self.active_requests:
            del self.active_requests[request_id]
    
    def get_active_requests(self) -> dict:
        """Retorna requests ativos."""
        return self.active_requests.copy()
    
    def get_long_running_requests(self, threshold_seconds: float = 30.0) -> list:
        """Retorna requests que estão rodando há muito tempo."""
        now = time.time()
        long_running = []
        
        for request_id, data in self.active_requests.items():
            duration = now - data['start_time']
            if duration > threshold_seconds:
                long_running.append({
                    'request_id': request_id,
                    'duration': duration,
                    'info': data['info']
                })
        
        return long_running


# Instância global do tracker
request_tracker = RequestTracker()


def log_long_running_requests():
    """Log de requests que estão rodando há muito tempo."""
    long_running = request_tracker.get_long_running_requests()
    
    if long_running:
        logger.warning(
            "Long Running Requests Detected",
            count=len(long_running),
            requests=[{
                'request_id': req['request_id'],
                'duration_seconds': req['duration']
            } for req in long_running]
        )


def get_request_stats() -> dict:
    """Retorna estatísticas dos requests ativos."""
    active = request_tracker.get_active_requests()
    
    return {
        'active_requests': len(active),
        'long_running': len(request_tracker.get_long_running_requests()),
        'requests': list(active.keys())
    }