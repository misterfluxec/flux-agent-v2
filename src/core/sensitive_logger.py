import logging
import re
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Patrones de datos sensibles a enmascarar
SENSITIVE_PATTERNS = [
    (re.compile(r'(sk-[a-zA-Z0-9]{24,})'), r'sk-***'),  # OpenAI/Meta tokens
    (re.compile(r'(EAAC[0-9A-Za-z]{20,})'), r'EAAC***'),   # Facebook access tokens
    (re.compile(r'("byoa_cloud_token":\s*")([^"]+)(")'), r'\1***\3'),  # JSON tokens
    (re.compile(r'(password|secret|key|token)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***'),  # Genérico
]

def mask_sensitive_data(text: str) -> str:
    """Enmascara datos sensibles en strings para logging seguro"""
    if not text:
        return text
    masked = str(text)
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked

def log_safe(func: Callable) -> Callable:
    """
    Decorador para funciones que registran logs:
    - Enmascara automáticamente argumentos y mensajes que contengan datos sensibles
    - Útil para endpoints que manejan credenciales BYOA
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            safe_msg = mask_sensitive_data(str(e))
            safe_args = [mask_sensitive_data(str(a)) for a in args]
            safe_kwargs = {k: mask_sensitive_data(str(v)) for k, v in kwargs.items()}
            logger.error(f"{func.__name__} failed: {safe_msg} | kwargs={safe_kwargs}", exc_info=True)
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            safe_msg = mask_sensitive_data(str(e))
            safe_args = [mask_sensitive_data(str(a)) for a in args]
            safe_kwargs = {k: mask_sensitive_data(str(v)) for k, v in kwargs.items()}
            logger.error(f"{func.__name__} failed: {safe_msg} | kwargs={safe_kwargs}", exc_info=True)
            raise

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

# Función helper para logging manual seguro
def log_info_safe(message: str, **context):
    """Log de info con enmascaramiento automático de contexto"""
    safe_context = {k: mask_sensitive_data(str(v)) for k, v in context.items()}
    # Formatear el contexto en un string para el logger básico
    context_str = " | ".join(f"{k}={v}" for k, v in safe_context.items()) if safe_context else ""
    full_msg = f"{mask_sensitive_data(message)} | {context_str}" if context_str else mask_sensitive_data(message)
    logger.info(full_msg)

def log_error_safe(message: str, error: Exception = None, **context):
    """Log de error con enmascaramiento automático"""
    safe_msg = mask_sensitive_data(message)
    safe_error = mask_sensitive_data(str(error)) if error else None
    safe_context = {k: mask_sensitive_data(str(v)) for k, v in context.items()}
    context_str = " | ".join(f"{k}={v}" for k, v in safe_context.items()) if safe_context else ""
    full_msg = f"{safe_msg}: {safe_error} | {context_str}" if safe_error else f"{safe_msg} | {context_str}"
    if error:
        logger.error(full_msg, exc_info=True)
    else:
        logger.error(full_msg)
