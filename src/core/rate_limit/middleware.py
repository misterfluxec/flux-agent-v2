# =============================================================================
# FLUXAGENT V2 — RATE LIMIT MIDDLEWARE
# =============================================================================
# Middleware configurable para rate limiting multi-tenant
# Soporte para diferentes estrategias y almacenamiento en Redis
# =============================================================================

import time
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from .rules import RateLimitRule, RateLimitStore, get_default_rules
from .exceptions import RateLimitExceeded
from core.cache.client import get_cache_client

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware configurable para rate limiting"""
    
    def __init__(
        self, 
        app,
        rules: Optional[List[RateLimitRule]] = None,
        store: Optional[RateLimitStore] = None,
        key_generator: Optional[Callable[[Request], str]] = None,
        skip_paths: Optional[List[str]] = None,
        enabled: bool = True
    ):
        super().__init__(app)
        self.rules = rules or get_default_rules()
        self.store = store or RateLimitStore()
        self.key_generator = key_generator or self._default_key_generator
        self.skip_paths = skip_paths or [
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
            "/metrics"
        ]
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa request aplicando rate limiting"""
        
        # Skip si está deshabilitado o es path excluido
        if not self.enabled or self._should_skip_path(request.url.path):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            # Generar clave de identificación
            identifier = await self.key_generator(request)
            
            # Aplicar reglas de rate limiting
            for rule in self.rules:
                if rule.matches(request):
                    await self._apply_rule(rule, identifier, request)
            
            # Ejecutar request
            response = await call_next(request)
            
            # Agregar headers de rate limiting
            await self._add_rate_limit_headers(response, identifier)
            
            return response
            
        except RateLimitExceeded as e:
            # Respuesta con headers de rate limit
            response = Response(
                content='{"error": "rate_limit_exceeded", "message": "Too many requests"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
            
            # Agregar headers informativos
            response.headers["X-RateLimit-Limit"] = str(e.limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, e.limit - e.current))
            response.headers["X-RateLimit-Reset"] = str(e.reset_time)
            response.headers["X-RateLimit-Retry-After"] = str(e.retry_after)
            response.headers["Retry-After"] = str(e.retry_after)
            
            logger.warning(
                f"🚫 Rate limit excedido: {identifier} - "
                f"Rule: {rule.name} - Path: {request.url.path}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error en rate limiting: {e}", exc_info=True)
            # En caso de error, permitir request (fail-open)
            return await call_next(request)
        
        finally:
            # Log de performance
            duration = time.time() - start_time
            if duration > 0.1:  # Log si toma más de 100ms
                logger.warning(f"Rate limiting lento: {duration:.3f}s")
    
    def _should_skip_path(self, path: str) -> bool:
        """Determina si el path debe saltarse"""
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True
        return False
    
    async def _default_key_generator(self, request: Request) -> str:
        """Generador default de clave basado en tenant y usuario"""
        # Prioridad: tenant_id > user_id > IP
        identifier = None
        
        # Intentar obtener tenant_id del request state
        if hasattr(request.state, 'tenant_id'):
            identifier = f"tenant_{request.state.tenant_id}"
        
        # Intentar obtener user_id del request state
        elif hasattr(request.state, 'user_id'):
            identifier = f"user_{request.state.user_id}"
        
        # Fallback a IP
        else:
            client_ip = self._get_client_ip(request)
            identifier = f"ip_{client_ip}"
        
        # Agregar path para granularidad
        path_key = request.url.path.replace('/', '_').strip('_')
        return f"{identifier}:{path_key}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtiene IP real del cliente considerando proxies"""
        # Headers comunes de proxies
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback a IP de conexión
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _apply_rule(self, rule: RateLimitRule, identifier: str, request: Request):
        """Aplica una regla específica de rate limiting"""
        
        # Construir clave para esta regla
        rule_key = f"ratelimit:{rule.name}:{identifier}"
        
        # Obtener contador actual
        current_count = await self.store.increment(
            key=rule_key,
            amount=1,
            ttl=rule.window_seconds
        )
        
        # Verificar si excede el límite
        if current_count > rule.limit:
            # Calcular tiempo de reset y retry
            reset_time = int(time.time()) + rule.window_seconds
            retry_after = rule.window_seconds
            
            raise RateLimitExceeded(
                limit=rule.limit,
                current=current_count,
                window=rule.window_seconds,
                reset_time=reset_time,
                retry_after=retry_after,
                rule_name=rule.name,
                identifier=identifier
            )
    
    async def _add_rate_limit_headers(self, response: Response, identifier: str):
        """Agrega headers informativos de rate limiting"""
        
        # Obtener status actual de rate limits
        headers = {}
        
        for rule in self.rules:
            rule_key = f"ratelimit:{rule.name}:{identifier}"
            
            # Obtener contador y TTL
            current = await self.store.get_count(rule_key)
            ttl = await self.store.get_ttl(rule_key)
            
            if current is not None:
                headers[f"X-RateLimit-{rule.name.title()}-Limit"] = str(rule.limit)
                headers[f"X-RateLimit-{rule.name.title()}-Remaining"] = str(
                    max(0, rule.limit - current)
                )
                headers[f"X-RateLimit-{rule.name.title()}-Reset"] = str(
                    int(time.time()) + ttl if ttl > 0 else int(time.time())
                )
        
        # Agregar headers a respuesta
        for key, value in headers.items():
            response.headers[key] = value

class AdvancedRateLimitMiddleware(RateLimitMiddleware):
    """Middleware avanzado con características adicionales"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.blocked_ips = {}  # IP bloqueadas temporalmente
        self.whitelist_ips = set()  # IPs whitelist
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Versión avanzada con bloqueo dinámico"""
        
        # Verificar IP bloqueada
        client_ip = self._get_client_ip(request)
        if client_ip in self.blocked_ips:
            block_info = self.blocked_ips[client_ip]
            if time.time() < block_info['expires']:
                return Response(
                    content='{"error": "ip_blocked", "message": "IP temporarily blocked"}',
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json"
                )
            else:
                # Remover bloqueo expirado
                del self.blocked_ips[client_ip]
        
        # Verificar whitelist
        if client_ip in self.whitelist_ips:
            return await call_next(request)
        
        try:
            return await super().dispatch(request, call_next)
            
        except RateLimitExceeded as e:
            # Bloquear IP si excede límite múltiples veces
            await self._handle_repeat_offender(client_ip, e)
            
            # Llamar al handler original
            raise
    
    async def _handle_repeat_offender(self, client_ip: str, exception: RateLimitExceeded):
        """Maneja ofensores repetidos"""
        
        # Obtener contador de ofensas
        offense_key = f"offenses:{client_ip}"
        offense_count = await self.store.increment(
            key=offense_key,
            amount=1,
            ttl=3600  # 1 hora
        )
        
        # Bloquear temporalmente si hay muchas ofensas
        if offense_count > 10:  # Más de 10 ofensas en 1 hora
            block_duration = min(offense_count * 300, 3600)  # Entre 5 min y 1 hora
            
            self.blocked_ips[client_ip] = {
                'blocked_at': time.time(),
                'expires': time.time() + block_duration,
                'offense_count': offense_count,
                'reason': 'repeat_rate_limit_violations'
            }
            
            logger.warning(
                f"🚫 IP bloqueada temporalmente: {client_ip} - "
                f"Duration: {block_duration}s - Offenses: {offense_count}"
            )
    
    def add_whitelist_ip(self, ip: str):
        """Agrega IP a whitelist"""
        self.whitelist_ips.add(ip)
        logger.info(f"✅ IP agregada a whitelist: {ip}")
    
    def remove_whitelist_ip(self, ip: str):
        """Remueve IP de whitelist"""
        self.whitelist_ips.discard(ip)
        logger.info(f"🗑️ IP removida de whitelist: {ip}")
    
    def block_ip(self, ip: str, duration: int, reason: str = "manual"):
        """Bloquea IP manualmente"""
        self.blocked_ips[ip] = {
            'blocked_at': time.time(),
            'expires': time.time() + duration,
            'reason': reason
        }
        logger.warning(f"🚫 IP bloqueada manualmente: {ip} - Duration: {duration}s - Reason: {reason}")
    
    def unblock_ip(self, ip: str):
        """Desbloquea IP manualmente"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            logger.info(f"✅ IP desbloqueada: {ip}")

# Helper functions para configuración
def create_rate_limit_middleware(
    app,
    tenant_limits: Optional[Dict[str, Dict[str, int]]] = None,
    global_limits: Optional[Dict[str, int]] = None,
    custom_rules: Optional[List[RateLimitRule]] = None
) -> RateLimitMiddleware:
    """Factory para crear middleware con configuración personalizada"""
    
    # Reglas default
    rules = get_default_rules()
    
    # Agregar reglas personalizadas
    if custom_rules:
        rules.extend(custom_rules)
    
    # Agregar reglas por tenant
    if tenant_limits:
        for tenant_id, limits in tenant_limits.items():
            for endpoint, limit_config in limits.items():
                rule = RateLimitRule(
                    name=f"tenant_{tenant_id}_{endpoint}",
                    limit=limit_config.get('limit', 100),
                    window_seconds=limit_config.get('window', 3600),
                    path_patterns=[f"/api/v1/{endpoint}"],
                    tenant_id=tenant_id
                )
                rules.append(rule)
    
    # Agregar reglas globales
    if global_limits:
        for endpoint, limit_config in global_limits.items():
            rule = RateLimitRule(
                name=f"global_{endpoint}",
                limit=limit_config.get('limit', 1000),
                window_seconds=limit_config.get('window', 3600),
                path_patterns=[f"/api/v1/{endpoint}"]
            )
            rules.append(rule)
    
    return RateLimitMiddleware(app, rules=rules)
