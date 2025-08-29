"""Middleware de autenticação JWT."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from fastapi import HTTPException, Security, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger

from config.settings import get_settings
from models.responses import ErrorResponse

settings = get_settings()
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTAuth:
    """Gerenciador de autenticação JWT."""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Cria token JWT."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.jwt_algorithm
        )
        
        logger.debug(f"JWT token created for data: {data}")
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verifica e decodifica token JWT."""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            
            # Verifica se é um token de acesso
            if payload.get("type") != "access":
                raise JWTError("Invalid token type")
                
            logger.debug(f"JWT token verified for: {payload.get('sub', 'unknown')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de senha."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica senha."""
        return pwd_context.verify(plain_password, hashed_password)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """Dependency para obter usuário atual (opcional)."""
    if not credentials:
        return None
    
    try:
        payload = JWTAuth.verify_token(credentials.credentials)
        return payload
    except HTTPException:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Dependency para obter usuário atual (obrigatório)."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return JWTAuth.verify_token(credentials.credentials)


# Aliases para compatibilidade
jwt_required = get_current_user
jwt_optional = get_current_user_optional


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware de autenticação."""
    
    def __init__(self, app, protected_paths: Optional[list] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or []
        
    async def dispatch(self, request: Request, call_next):
        """Processa requisição verificando autenticação."""
        
        # Verifica se o caminho precisa de autenticação
        if not self._needs_auth(request.url.path):
            return await call_next(request)
        
        # Extrai token do header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return self._unauthorized_response()
        
        token = auth_header[7:]  # Remove "Bearer "
        
        try:
            payload = JWTAuth.verify_token(token)
            # Adiciona usuário ao request state
            request.state.user = payload
            
        except HTTPException:
            return self._unauthorized_response()
        
        return await call_next(request)
    
    def _needs_auth(self, path: str) -> bool:
        """Verifica se o caminho precisa de autenticação."""
        # Paths públicos (não precisam auth)
        public_paths = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/login",
        ]
        
        # Se não está ativada a autenticação, libera tudo
        if not settings.feature_auth_enabled:
            return False
        
        # Se está em paths públicos, não precisa auth
        if any(path.startswith(p) for p in public_paths):
            return False
        
        # Se está em paths protegidos, precisa auth
        if self.protected_paths:
            return any(path.startswith(p) for p in self.protected_paths)
        
        # Por padrão, paths da API precisam de auth
        return path.startswith("/api/")
    
    def _unauthorized_response(self) -> JSONResponse:
        """Response para requisições não autorizadas."""
        error = ErrorResponse(
            message="Authentication required",
            error_code="AUTH_REQUIRED",
            error_type="Unauthorized"
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error.dict(),
            headers={"WWW-Authenticate": "Bearer"}
        )


def create_auth_middleware(
    app, 
    protected_paths: Optional[list] = None
) -> AuthMiddleware:
    """Factory para criar middleware de autenticação."""
    return AuthMiddleware(app, protected_paths)


class APIKeyAuth:
    """Autenticação por API Key (alternativa ao JWT)."""
    
    def __init__(self, valid_keys: Optional[Dict[str, str]] = None):
        self.valid_keys = valid_keys or {}
    
    def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verifica API key e retorna identificador do usuário."""
        return self.valid_keys.get(api_key)
    
    async def __call__(self, request: Request) -> Optional[str]:
        """Dependency para verificar API key."""
        api_key = request.headers.get(settings.api_key_header)
        
        if not api_key:
            return None
        
        user_id = self.verify_api_key(api_key)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return user_id


# Instância global para API keys
api_key_auth = APIKeyAuth()


def get_api_user(user_id: str = Depends(api_key_auth)) -> str:
    """Dependency para autenticação via API key."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid API key required"
        )
    return user_id


class DualAuth:
    """Autenticação que aceita JWT ou API Key."""
    
    async def __call__(
        self, 
        request: Request,
        jwt_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
        api_user: Optional[str] = Depends(api_key_auth)
    ) -> Union[Dict[str, Any], str]:
        """Verifica JWT ou API key."""
        
        if jwt_user:
            return jwt_user
        
        if api_user:
            return {"sub": api_user, "auth_type": "api_key"}
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid JWT token or API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )


# Instância para autenticação dual
dual_auth = DualAuth()