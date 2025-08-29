"""Configuração de logging estruturado com loguru."""

import sys
import logging
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from .settings import get_settings

settings = get_settings()


class InterceptHandler(logging.Handler):
    """Handler para interceptar logs do stdlib e enviar para loguru."""
    
    def emit(self, record: logging.LogRecord) -> None:
        """Intercepta e reencaminha logs para loguru."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # Encontra o caller correto
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def format_record(record: Dict[str, Any]) -> str:
    """Formata record do loguru para formato customizado."""
    format_string = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    if record["exception"]:
        format_string += "\n{exception}"
    
    return format_string


def setup_logging() -> None:
    """Configura sistema de logging estruturado."""
    
    # Remove handlers padrão do loguru
    logger.remove()
    
    # Configuração base do formato
    log_format = format_record if settings.is_development else None
    
    # Console output
    if settings.is_development:
        logger.add(
            sys.stdout,
            format=format_record,
            level=settings.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    else:
        logger.add(
            sys.stdout,
            level=settings.log_level,
            serialize=settings.log_format == "json",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            colorize=False
        )
    
    # File output
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.log_file,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            level=settings.log_level,
            serialize=True,  # Sempre JSON para arquivos
            compression="gz" if settings.log_compression else None,
            backtrace=True,
            diagnose=True,
            enqueue=True  # Thread-safe
        )
    
    # Intercepta logs do Python stdlib
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Intercepta logs de bibliotecas específicas
    libraries_to_intercept = [
        "uvicorn",
        "uvicorn.error", 
        "uvicorn.access",
        "fastapi",
        "starlette",
        "asyncio",
        "httpx",
        "aiohttp"
    ]
    
    for lib_name in libraries_to_intercept:
        lib_logger = logging.getLogger(lib_name)
        lib_logger.handlers = [InterceptHandler()]
        lib_logger.propagate = False
    
    # Configura nível específico para algumas bibliotecas
    if not settings.is_development:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger.info(
        "Logging configured",
        level=settings.log_level,
        format=settings.log_format,
        file=settings.log_file,
        development=settings.is_development
    )


def get_logger(name: str = None):
    """Retorna logger configurado para um módulo."""
    if name:
        return logger.bind(name=name)
    return logger


# Configurações específicas para contextos
def log_request(request, response=None, duration_ms=None):
    """Log estruturado para requests HTTP."""
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "remote_addr": getattr(request.client, 'host', 'unknown'),
        "user_agent": request.headers.get('user-agent', ''),
    }
    
    if response:
        log_data["status_code"] = response.status_code
    
    if duration_ms:
        log_data["duration_ms"] = duration_ms
    
    logger.info("HTTP Request", **log_data)


def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log estruturado para erros."""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if context:
        error_data.update(context)
    
    logger.error("Application Error", **error_data)


def log_performance(operation: str, duration_ms: float, metadata: Dict[str, Any] = None):
    """Log estruturado para métricas de performance."""
    perf_data = {
        "operation": operation,
        "duration_ms": duration_ms,
    }
    
    if metadata:
        perf_data.update(metadata)
    
    level = "WARNING" if duration_ms > 1000 else "INFO"
    logger.log(level, "Performance Metric", **perf_data)