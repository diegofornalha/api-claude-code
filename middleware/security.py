"""Middleware de segurança para headers e proteções."""

import hashlib
import hmac
import time
from typing import Dict, List, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from config.settings import get_settings
from models.responses import ErrorResponse

settings = get_settings()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar headers de segurança."""
    
    def __init__(self, app, security_headers: Optional[Dict[str, str]] = None):
        super().__init__(app)
        self.security_headers = security_headers or self._default_security_headers()
    
    def _default_security_headers(self) -> Dict[str, str]:
        """Headers de segurança padrão."""
        return {
            # Previne ataques XSS
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Strict Transport Security (apenas em produção HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if settings.is_production else "",
            
            # Content Security Policy básico
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'"
            ),
            
            # Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            )
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Adiciona headers de segurança na resposta."""
        
        response = await call_next(request)
        
        # Adiciona headers de segurança
        for header, value in self.security_headers.items():
            if value:  # Só adiciona se tem valor
                response.headers[header] = value
        
        # Remove headers que podem vazar informações
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Middleware para whitelist de IPs."""
    
    def __init__(self, app, allowed_ips: Optional[List[str]] = None):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips or [])
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Verifica se IP está na whitelist."""
        
        if not self.allowed_ips:
            # Sem whitelist configurada
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        if client_ip not in self.allowed_ips:
            logger.warning(f"IP blocked by whitelist: {client_ip}")
            
            error = ErrorResponse(
                message="Access denied",
                error_code="IP_NOT_ALLOWED",
                error_type="Forbidden"
            )
            
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error.dict()
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP do cliente."""
        # Headers de proxy
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # IP direto
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return 'unknown'


class RequestSignatureMiddleware(BaseHTTPMiddleware):
    """Middleware para verificar assinatura HMAC de requests."""
    
    def __init__(self, app, secret_key: str, required_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.secret_key = secret_key.encode()
        self.required_paths = required_paths or []
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Verifica assinatura HMAC se requerida."""
        
        if not self._requires_signature(request.url.path):
            return await call_next(request)
        
        # Obtém assinatura do header
        signature = request.headers.get('X-Signature')
        if not signature:
            return self._signature_error("Missing signature")
        
        # Lê body do request
        body = await request.body()
        
        # Verifica assinatura
        expected_signature = self._calculate_signature(body)
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning(f"Invalid signature for {request.url.path}")
            return self._signature_error("Invalid signature")
        
        return await call_next(request)
    
    def _requires_signature(self, path: str) -> bool:
        """Verifica se path requer assinatura."""
        return any(path.startswith(required) for required in self.required_paths)
    
    def _calculate_signature(self, body: bytes) -> str:
        """Calcula assinatura HMAC SHA-256."""
        signature = hmac.new(
            self.secret_key,
            body,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def _signature_error(self, message: str) -> JSONResponse:
        """Response para erro de assinatura."""
        error = ErrorResponse(
            message=message,
            error_code="INVALID_SIGNATURE",
            error_type="Unauthorized"
        )
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error.dict()
        )


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para limitar tamanho do request."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Verifica tamanho do request."""
        
        # Verifica Content-Length header
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    logger.warning(f"Request too large: {size} bytes (max: {self.max_size})")
                    
                    error = ErrorResponse(
                        message=f"Request too large. Maximum size: {self.max_size} bytes",
                        error_code="REQUEST_TOO_LARGE",
                        error_type="PayloadTooLarge"
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content=error.dict()
                    )
            except ValueError:
                pass
        
        return await call_next(request)


class UserAgentFilterMiddleware(BaseHTTPMiddleware):
    """Middleware para filtrar User-Agents suspeitos."""
    
    def __init__(self, app, blocked_agents: Optional[List[str]] = None):
        super().__init__(app)
        self.blocked_agents = blocked_agents or self._default_blocked_agents()
    
    def _default_blocked_agents(self) -> List[str]:
        """User-Agents bloqueados por padrão."""
        return [
            'curl',
            'wget', 
            'python-requests',
            'python-urllib',
            'bot',
            'spider',
            'crawler'
        ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Filtra User-Agents suspeitos."""
        
        user_agent = request.headers.get('user-agent', '').lower()
        
        if any(blocked in user_agent for blocked in self.blocked_agents):
            # Em desenvolvimento, apenas log warning
            if settings.is_development:
                logger.warning(f"Suspicious User-Agent (allowed in dev): {user_agent}")
                return await call_next(request)
            
            logger.warning(f"Blocked User-Agent: {user_agent}")
            
            error = ErrorResponse(
                message="Access denied",
                error_code="USER_AGENT_BLOCKED", 
                error_type="Forbidden"
            )
            
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error.dict()
            )
        
        return await call_next(request)


def create_security_middleware(
    app,
    security_headers: bool = True,
    ip_whitelist: Optional[List[str]] = None,
    signature_verification: bool = False,
    request_size_limit: Optional[int] = None,
    user_agent_filter: bool = False
):
    """Factory para criar middlewares de segurança."""
    
    # Headers de segurança
    if security_headers:
        app.add_middleware(SecurityMiddleware)
        logger.info("Security headers middleware enabled")
    
    # IP Whitelist
    if ip_whitelist:
        app.add_middleware(IPWhitelistMiddleware, allowed_ips=ip_whitelist)
        logger.info(f"IP whitelist middleware enabled: {len(ip_whitelist)} IPs")
    
    # Verificação de assinatura
    if signature_verification:
        required_paths = ['/api/webhook/', '/api/callback/']
        app.add_middleware(
            RequestSignatureMiddleware, 
            secret_key=settings.secret_key,
            required_paths=required_paths
        )
        logger.info("Request signature verification enabled")
    
    # Limite de tamanho
    if request_size_limit:
        app.add_middleware(RequestSizeLimitMiddleware, max_size=request_size_limit)
        logger.info(f"Request size limit enabled: {request_size_limit} bytes")
    
    # Filtro de User-Agent
    if user_agent_filter and settings.is_production:
        app.add_middleware(UserAgentFilterMiddleware)
        logger.info("User-Agent filter enabled")
    
    return app