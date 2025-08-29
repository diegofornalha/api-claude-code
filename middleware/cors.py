"""CORS middleware configuration."""

from typing import List
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config.settings import get_settings

settings = get_settings()


def create_cors_middleware(app) -> CORSMiddleware:
    """Cria e configura middleware CORS."""
    
    # Configuração baseada no ambiente
    if settings.is_development and settings.dev_cors_allow_all:
        logger.warning("Development mode: CORS allowing all origins")
        cors_origins = ["*"]
        cors_methods = ["*"]
        cors_headers = ["*"]
    else:
        cors_origins = settings.cors_origins
        cors_methods = settings.cors_methods
        cors_headers = settings.cors_headers
    
    # Valida configurações
    if not cors_origins:
        logger.warning("No CORS origins configured, using default localhost")
        cors_origins = [
            "http://localhost:3040",
            "http://localhost:3040", 
            "http://127.0.0.1:3040",
            "http://127.0.0.1:3040"
        ]
    
    logger.info(f"CORS configured with origins: {cors_origins}")
    
    # Adiciona middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=cors_methods,
        allow_headers=cors_headers,
        expose_headers=[
            "X-Session-ID",
            "X-Request-ID", 
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ],
        max_age=86400  # 24 hours
    )
    
    return app


def get_cors_origins() -> List[str]:
    """Retorna lista de origins permitidas."""
    if settings.is_development and settings.dev_cors_allow_all:
        return ["*"]
    
    origins = settings.cors_origins.copy()
    
    # Adiciona origins padrão em desenvolvimento
    if settings.is_development:
        default_dev_origins = [
            "http://localhost:3040",
            "http://localhost:3040",
            "http://127.0.0.1:3040", 
            "http://127.0.0.1:3040"
        ]
        
        for origin in default_dev_origins:
            if origin not in origins:
                origins.append(origin)
    
    return origins


def is_origin_allowed(origin: str) -> bool:
    """Verifica se origin é permitida."""
    allowed_origins = get_cors_origins()
    
    # Se permite todas
    if "*" in allowed_origins:
        return True
    
    # Verifica match exato
    if origin in allowed_origins:
        return True
    
    # Em desenvolvimento, permite localhost com qualquer porta
    if settings.is_development:
        if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
            return True
    
    return False


class CORSValidator:
    """Validador de CORS requests."""
    
    @staticmethod
    def validate_preflight(origin: str, method: str, headers: str) -> bool:
        """Valida requisição preflight."""
        # Verifica origin
        if not is_origin_allowed(origin):
            logger.warning(f"CORS: Origin not allowed: {origin}")
            return False
        
        # Verifica método
        if method not in settings.cors_methods and "*" not in settings.cors_methods:
            logger.warning(f"CORS: Method not allowed: {method}")
            return False
        
        # Verifica headers
        if headers and "*" not in settings.cors_headers:
            requested_headers = [h.strip() for h in headers.split(",")]
            for header in requested_headers:
                if header not in settings.cors_headers:
                    logger.warning(f"CORS: Header not allowed: {header}")
                    return False
        
        return True
    
    @staticmethod
    def get_cors_headers(origin: str) -> dict:
        """Retorna headers CORS para resposta."""
        headers = {}
        
        # Origin
        if is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
        
        # Credentials
        if settings.cors_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        # Methods
        headers["Access-Control-Allow-Methods"] = ", ".join(settings.cors_methods)
        
        # Headers
        headers["Access-Control-Allow-Headers"] = ", ".join(settings.cors_headers)
        
        # Expose headers
        expose_headers = [
            "X-Session-ID",
            "X-Request-ID",
            "X-RateLimit-Limit", 
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        headers["Access-Control-Expose-Headers"] = ", ".join(expose_headers)
        
        # Max age
        headers["Access-Control-Max-Age"] = "86400"
        
        return headers