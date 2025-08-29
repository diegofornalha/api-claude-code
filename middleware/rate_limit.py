"""Rate limiting middleware usando slowapi."""

import time
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from loguru import logger

from config.settings import get_settings
from models.responses import ErrorResponse

settings = get_settings()


def get_rate_limit_key(request: Request) -> str:
    """
    Função para gerar chave do rate limiting.
    Combina IP + User ID (se autenticado).
    """
    # IP address base
    client_ip = get_remote_address(request)
    
    # Se tiver usuário autenticado, inclui na chave
    user_id = getattr(request.state, 'user', {}).get('sub')
    if user_id:
        return f"{client_ip}:{user_id}"
    
    return client_ip


def create_limiter() -> Limiter:
    """Cria instância do rate limiter."""
    if not settings.rate_limit_enabled:
        # Limiter desabilitado - sem limites
        return Limiter(
            key_func=get_rate_limit_key,
            enabled=False
        )
    
    # Configuração de storage
    if settings.rate_limit_storage == "redis" and settings.redis_enabled:
        import redis.asyncio as redis
        
        storage_uri = settings.redis_url
        logger.info(f"Using Redis for rate limiting: {settings.redis_host}:{settings.redis_port}")
    else:
        # Usa storage em memória
        storage_uri = "memory://"
        logger.info("Using memory storage for rate limiting")
    
    return Limiter(
        key_func=get_rate_limit_key,
        default_limits=[settings.rate_limit_default],
        storage_uri=storage_uri,
        enabled=settings.rate_limit_enabled,
        headers_enabled=True
    )


# Instância global do limiter
limiter = create_limiter()


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Handler customizado para quando rate limit é excedido.
    """
    client_ip = get_remote_address(request)
    user_id = getattr(request.state, 'user', {}).get('sub', 'anonymous')
    
    logger.warning(
        f"Rate limit exceeded for {client_ip} (user: {user_id}) "
        f"on {request.method} {request.url.path}"
    )
    
    error = ErrorResponse(
        message=f"Rate limit exceeded: {exc.detail}",
        error_code="RATE_LIMIT_EXCEEDED",
        error_type="TooManyRequests",
        details={
            "retry_after": exc.retry_after,
            "limit": exc.detail,
            "client_ip": client_ip
        }
    )
    
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error.dict()
    )
    
    # Headers informativos
    response.headers["Retry-After"] = str(int(exc.retry_after))
    response.headers["X-RateLimit-Limit"] = str(exc.detail.split("/")[0])
    response.headers["X-RateLimit-Remaining"] = "0"
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + exc.retry_after))
    
    return response


class RateLimitMiddleware:
    """Middleware personalizado para rate limiting."""
    
    def __init__(self, app, limiter: Limiter):
        self.app = app
        self.limiter = limiter
        
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Verifica rate limit apenas se habilitado
        if settings.rate_limit_enabled:
            await self._check_rate_limit(request)
        
        await self.app(scope, receive, send)
    
    async def _check_rate_limit(self, request: Request):
        """Verifica se request excede rate limit."""
        try:
            # Limites específicos por endpoint
            limits = self._get_endpoint_limits(request)
            
            if limits:
                # Aplica limite específico
                key = get_rate_limit_key(request)
                await self.limiter.check_rate_limit(key, limits)
                
        except RateLimitExceeded as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {e.detail}",
                headers={"Retry-After": str(int(e.retry_after))}
            )
    
    def _get_endpoint_limits(self, request: Request) -> Optional[str]:
        """Retorna limites específicos por endpoint."""
        path = request.url.path
        method = request.method
        
        # Limites específicos por endpoint
        endpoint_limits = {
            # Chat endpoints - mais restritivo
            "/api/chat": "50/minute",
            "/api/new-session": "20/minute",
            
            # Health checks - mais permissivo  
            "/health": "300/minute",
            "/": "300/minute",
            
            # Auth endpoints
            "/api/auth/login": "10/minute",
            
            # Session management
            "/api/sessions": "100/minute",
        }
        
        # Busca limite exato primeiro
        limit = endpoint_limits.get(path)
        if limit:
            return limit
        
        # Busca por padrão de path
        if path.startswith("/api/session/"):
            return "30/minute"
        
        if path.startswith("/api/"):
            return "100/minute"
        
        # Usa limite padrão
        return settings.rate_limit_default


def create_rate_limit_middleware(app, limiter: Limiter = None):
    """Factory para criar middleware de rate limiting."""
    if not limiter:
        limiter = create_limiter()
    
    return RateLimitMiddleware(app, limiter)


class BurstLimiter:
    """Implementa burst limiting personalizado."""
    
    def __init__(self, burst_size: int = 10, window_seconds: int = 60):
        self.burst_size = burst_size
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def check_burst(self, key: str) -> bool:
        """Verifica se request excede burst limit."""
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove requests antigas
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.window_seconds
        ]
        
        # Verifica se excede burst
        if len(self.requests[key]) >= self.burst_size:
            logger.warning(f"Burst limit exceeded for key: {key}")
            return False
        
        # Adiciona request atual
        self.requests[key].append(now)
        return True


# Instância global do burst limiter
burst_limiter = BurstLimiter(
    burst_size=settings.rate_limit_burst,
    window_seconds=60
)


async def check_burst_limit(request: Request) -> bool:
    """Dependency para verificar burst limit."""
    if not settings.rate_limit_enabled:
        return True
    
    key = get_rate_limit_key(request)
    
    if not burst_limiter.check_burst(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Burst limit exceeded - too many requests in short time"
        )
    
    return True