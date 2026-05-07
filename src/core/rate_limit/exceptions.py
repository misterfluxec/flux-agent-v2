# =============================================================================
# FLUXAGENT V2 — RATE LIMIT EXCEPTIONS
# =============================================================================
# Excepciones personalizadas para rate limiting
# Soporte para diferentes tipos de errores y metadatos
# =============================================================================

from typing import Optional, Dict, Any
from fastapi import HTTPException, status

class RateLimitError(Exception):
    """Base exception para rate limiting"""
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.rule_name = rule_name
        self.identifier = identifier
        self.metadata = metadata or {}

class RateLimitExceeded(RateLimitError, HTTPException):
    """Excepción cuando se excede el límite de rate limiting"""
    
    def __init__(
        self,
        limit: int,
        current: int,
        window: int,
        reset_time: int,
        retry_after: int,
        rule_name: Optional[str] = None,
        identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        # Crear mensaje descriptivo
        message = (
            f"Rate limit exceeded: {current}/{limit} requests "
            f"in the last {window} seconds"
        )
        
        # Inicializar excepción base
        RateLimitError.__init__(
            self,
            message=message,
            rule_name=rule_name,
            identifier=identifier,
            metadata={
                **(metadata or {}),
                "limit": limit,
                "current": current,
                "window": window,
                "reset_time": reset_time,
                "retry_after": retry_after
            }
        )
        
        # Inicializar HTTPException
        HTTPException.__init__(
            self,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": message,
                "limit": limit,
                "current": current,
                "window": window,
                "reset_time": reset_time,
                "retry_after": retry_after,
                "rule_name": rule_name
            }
        )
        
        self.limit = limit
        self.current = current
        self.window = window
        self.reset_time = reset_time
        self.retry_after = retry_after

class RateLimitRuleError(RateLimitError):
    """Error en configuración de reglas de rate limiting"""
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        validation_errors: Optional[list] = None
    ):
        super().__init__(
            message=message,
            rule_name=rule_name,
            metadata={"validation_errors": validation_errors or []}
        )
        self.validation_errors = validation_errors or []

class RateLimitStoreError(RateLimitError):
    """Error en el almacenamiento de rate limiting"""
    
    def __init__(
        self,
        message: str,
        store_type: Optional[str] = None,
        operation: Optional[str] = None
    ):
        super().__init__(
            message=message,
            metadata={
                "store_type": store_type,
                "operation": operation
            }
        )
        self.store_type = store_type
        self.operation = operation

class RateLimitConfigError(RateLimitError):
    """Error en configuración global de rate limiting"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            metadata={
                "config_key": config_key,
                "config_value": config_value
            }
        )
        self.config_key = config_key
        self.config_value = config_value

class IPBlockedError(RateLimitError, HTTPException):
    """Excepción cuando una IP está bloqueada"""
    
    def __init__(
        self,
        ip: str,
        reason: str,
        blocked_at: int,
        expires_at: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        message = f"IP {ip} is blocked: {reason}"
        
        # Inicializar excepción base
        RateLimitError.__init__(
            self,
            message=message,
            metadata={
                **(metadata or {}),
                "ip": ip,
                "reason": reason,
                "blocked_at": blocked_at,
                "expires_at": expires_at
            }
        )
        
        # Inicializar HTTPException
        HTTPException.__init__(
            self,
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "ip_blocked",
                "message": message,
                "ip": ip,
                "reason": reason,
                "blocked_at": blocked_at,
                "expires_at": expires_at
            }
        )
        
        self.ip = ip
        self.reason = reason
        self.blocked_at = blocked_at
        self.expires_at = expires_at

class TenantRateLimitError(RateLimitError):
    """Error específico para rate limiting de tenant"""
    
    def __init__(
        self,
        tenant_id: str,
        message: str,
        plan: Optional[str] = None,
        current_usage: Optional[int] = None,
        plan_limit: Optional[int] = None
    ):
        super().__init__(
            message=message,
            metadata={
                "tenant_id": tenant_id,
                "plan": plan,
                "current_usage": current_usage,
                "plan_limit": plan_limit
            }
        )
        self.tenant_id = tenant_id
        self.plan = plan
        self.current_usage = current_usage
        self.plan_limit = plan_limit

class UserRateLimitError(RateLimitError):
    """Error específico para rate limiting de usuario"""
    
    def __init__(
        self,
        user_id: str,
        message: str,
        role: Optional[str] = None,
        current_usage: Optional[int] = None,
        user_limit: Optional[int] = None
    ):
        super().__init__(
            message=message,
            metadata={
                "user_id": user_id,
                "role": role,
                "current_usage": current_usage,
                "user_limit": user_limit
            }
        )
        self.user_id = user_id
        self.role = role
        self.current_usage = current_usage
        self.user_limit = user_limit

# Helper functions para crear excepciones
def create_rate_limit_exceeded(
    rule_name: str,
    identifier: str,
    limit: int,
    current: int,
    window: int
) -> RateLimitExceeded:
    """Factory para crear RateLimitExceeded con timestamps calculados"""
    
    import time
    
    reset_time = int(time.time()) + window
    retry_after = window
    
    return RateLimitExceeded(
        limit=limit,
        current=current,
        window=window,
        reset_time=reset_time,
        retry_after=retry_after,
        rule_name=rule_name,
        identifier=identifier
    )

def create_ip_blocked_error(
    ip: str,
    reason: str,
    duration_seconds: int = 3600
) -> IPBlockedError:
    """Factory para crear IPBlockedError con timestamps calculados"""
    
    import time
    
    blocked_at = int(time.time())
    expires_at = blocked_at + duration_seconds
    
    return IPBlockedError(
        ip=ip,
        reason=reason,
        blocked_at=blocked_at,
        expires_at=expires_at
    )

def create_tenant_rate_limit_error(
    tenant_id: str,
    plan: str,
    current_usage: int,
    plan_limit: int,
    resource_type: str = "requests"
) -> TenantRateLimitError:
    """Factory para crear TenantRateLimitError"""
    
    message = (
        f"Tenant {tenant_id} has exceeded {resource_type} limit: "
        f"{current_usage}/{plan_limit} (plan: {plan})"
    )
    
    return TenantRateLimitError(
        tenant_id=tenant_id,
        message=message,
        plan=plan,
        current_usage=current_usage,
        plan_limit=plan_limit
    )

def create_user_rate_limit_error(
    user_id: str,
    role: str,
    current_usage: int,
    user_limit: int,
    resource_type: str = "requests"
) -> UserRateLimitError:
    """Factory para crear UserRateLimitError"""
    
    message = (
        f"User {user_id} ({role}) has exceeded {resource_type} limit: "
        f"{current_usage}/{user_limit}"
    )
    
    return UserRateLimitError(
        user_id=user_id,
        message=message,
        role=role,
        current_usage=current_usage,
        user_limit=user_limit
    )

# Decorador para manejar excepciones de rate limiting
def handle_rate_limit_errors(func):
    """Decorador para manejar excepciones de rate limiting"""
    import functools
    import logging
    
    logger = logging.getLogger(__name__)
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RateLimitExceeded as e:
            # Log específico para rate limit
            logger.warning(
                f"🚫 Rate limit exceeded: {e.rule_name} - "
                f"Identifier: {e.identifier} - "
                f"Current: {e.current}/{e.limit}"
            )
            raise
        except IPBlockedError as e:
            # Log específico para IP bloqueada
            logger.warning(
                f"🚫 IP blocked: {e.ip} - "
                f"Reason: {e.reason} - "
                f"Expires: {e.expires_at}"
            )
            raise
        except TenantRateLimitError as e:
            # Log específico para tenant limit
            logger.warning(
                f"🚫 Tenant rate limit exceeded: {e.tenant_id} - "
                f"Plan: {e.plan} - "
                f"Usage: {e.current_usage}/{e.plan_limit}"
            )
            raise
        except RateLimitError as e:
            # Log genérico para otros errores de rate limiting
            logger.error(f"Rate limiting error: {e.message}")
            raise
        except Exception as e:
            # Log para errores inesperados
            logger.error(f"Unexpected error in rate limiting: {e}", exc_info=True)
            raise
    
    return wrapper
