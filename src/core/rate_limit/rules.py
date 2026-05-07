# =============================================================================
# FLUXAGENT V2 — RATE LIMIT RULES
# =============================================================================
# Definición de reglas de rate limiting configurables
# Soporte para diferentes estrategias y almacenamiento
# =============================================================================

import time
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from fastapi import Request

from .exceptions import RateLimitError

class RateLimitStrategy(Enum):
    """Estrategias de rate limiting"""
    FIXED_WINDOW = "fixed_window"      # Ventana fija
    SLIDING_WINDOW = "sliding_window"  # Ventana deslizante
    TOKEN_BUCKET = "token_bucket"      # Token bucket
    LEAKY_BUCKET = "leaky_bucket"      # Leaky bucket

@dataclass
class RateLimitRule:
    """Regla de rate limiting configurable"""
    name: str
    limit: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    path_patterns: List[str] = field(default_factory=list)
    method_patterns: List[str] = field(default_factory=list)
    tenant_ids: Optional[Set[str]] = None
    user_roles: Optional[Set[str]] = None
    headers: Optional[Dict[str, str]] = None
    priority: int = 100  # Menor = mayor prioridad
    enabled: bool = True
    
    def matches(self, request: Request) -> bool:
        """Verifica si la regla aplica al request"""
        if not self.enabled:
            return False
        
        # Verificar path patterns
        if self.path_patterns:
            path_match = any(
                re.match(pattern.replace('*', '.*'), request.url.path)
                for pattern in self.path_patterns
            )
            if not path_match:
                return False
        
        # Verificar method patterns
        if self.method_patterns:
            if request.method not in self.method_patterns:
                return False
        
        # Verificar headers requeridos
        if self.headers:
            for header, expected_value in self.headers.items():
                actual_value = request.headers.get(header)
                if actual_value != expected_value:
                    return False
        
        # Verificar tenant específico
        if self.tenant_ids:
            tenant_id = getattr(request.state, 'tenant_id', None)
            if not tenant_id or tenant_id not in self.tenant_ids:
                return False
        
        # Verificar roles de usuario
        if self.user_roles:
            user_roles = getattr(request.state, 'user_roles', set())
            if not user_roles.intersection(self.user_roles):
                return False
        
        return True

@dataclass
class RateLimitConfig:
    """Configuración global de rate limiting"""
    enabled: bool = True
    default_strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    store_type: str = "redis"  # redis, memory, database
    cleanup_interval: int = 300  # 5 minutos
    blocked_ip_duration: int = 3600  # 1 hora
    max_offenses: int = 10  # Máximo de ofensas antes de bloqueo
    whitelist_ips: Set[str] = field(default_factory=set)
    blocked_ips: Dict[str, Dict[str, Any]] = field(default_factory=dict)

class RateLimitStore:
    """Almacenamiento para rate limiting"""
    
    def __init__(self, store_type: str = "redis"):
        self.store_type = store_type
        self._client = None
    
    async def initialize(self):
        """Inicializa el store"""
        if self.store_type == "redis":
            from core.cache.client import get_cache_client
            self._client = get_cache_client()
            await self._client.connect()
        # TODO: Implementar otros stores (memory, database)
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Incrementa contador atómicamente"""
        if self._client:
            return await self._client.increment(key, amount, ttl)
        return 0
    
    async def get_count(self, key: str) -> Optional[int]:
        """Obtiene contador actual"""
        if self._client:
            # En Redis, el contador es el valor actual
            value = await self._client.get(key)
            return int(value) if value else None
        return None
    
    async def get_ttl(self, key: str) -> int:
        """Obtiene TTL de clave"""
        if self._client:
            return await self._client.get_ttl(key)
        return -2
    
    async def reset(self, key: str) -> bool:
        """Resetea contador"""
        if self._client:
            return await self._client.delete(key) > 0
        return False
    
    async def cleanup_expired(self, pattern: str = "ratelimit:*") -> int:
        """Limpia claves expiradas"""
        if self._client:
            return await self._client.delete(pattern)
        return 0

# Reglas predefinidas
def get_default_rules() -> List[RateLimitRule]:
    """Retorna reglas default para FluxAgent"""
    return [
        # Rate limits generales
        RateLimitRule(
            name="global_requests",
            limit=1000,
            window_seconds=3600,  # 1000 requests/hora
            path_patterns=["/api/*"],
            priority=1
        ),
        
        # Rate limits por tenant
        RateLimitRule(
            name="tenant_requests",
            limit=500,
            window_seconds=3600,  # 500 requests/hora por tenant
            path_patterns=["/api/*"],
            priority=10
        ),
        
        # Rate limits para endpoints críticos
        RateLimitRule(
            name="auth_endpoints",
            limit=20,
            window_seconds=300,  # 20 login/5 min
            path_patterns=["/api/v1/auth/login", "/api/v1/auth/register"],
            method_patterns=["POST"],
            priority=5
        ),
        
        RateLimitRule(
            name="message_endpoints",
            limit=100,
            window_seconds=60,  # 100 mensajes/minuto
            path_patterns=["/api/v1/chat/*", "/api/v1/whatsapp/send"],
            method_patterns=["POST"],
            priority=15
        ),
        
        RateLimitRule(
            name="file_upload",
            limit=10,
            window_seconds=300,  # 10 uploads/5 min
            path_patterns=["/api/v1/upload/*"],
            method_patterns=["POST"],
            priority=20
        ),
        
        RateLimitRule(
            name="analytics_endpoints",
            limit=60,
            window_seconds=60,  # 60 requests/minuto
            path_patterns=["/api/v1/analytics/*"],
            priority=25
        ),
        
        RateLimitRule(
            name="admin_endpoints",
            limit=200,
            window_seconds=3600,  # 200 requests/hora para admin
            path_patterns=["/api/v1/admin/*"],
            user_roles={"admin", "superadmin"},
            priority=30
        ),
        
        # Rate limits para endpoints de AI
        RateLimitRule(
            name="ai_endpoints",
            limit=50,
            window_seconds=60,  # 50 requests/minuto para IA
            path_patterns=["/api/v1/agents/*/chat", "/api/v1/voice/*"],
            priority=35
        ),
        
        # Rate limits para webhooks
        RateLimitRule(
            name="webhook_endpoints",
            limit=1000,
            window_seconds=60,  # 1000 webhooks/minuto
            path_patterns=["/api/v1/webhooks/*"],
            method_patterns=["POST"],
            priority=40
        )
    ]

def get_tenant_specific_rules(tenant_id: str, plan: str = "free") -> List[RateLimitRule]:
    """Retorna reglas específicas por tenant según plan"""
    
    # Límites por plan
    plan_limits = {
        "free": {
            "requests_per_hour": 100,
            "messages_per_minute": 10,
            "ai_requests_per_minute": 5,
            "file_uploads_per_hour": 5
        },
        "basic": {
            "requests_per_hour": 500,
            "messages_per_minute": 50,
            "ai_requests_per_minute": 25,
            "file_uploads_per_hour": 20
        },
        "pro": {
            "requests_per_hour": 2000,
            "messages_per_minute": 200,
            "ai_requests_per_minute": 100,
            "file_uploads_per_hour": 100
        },
        "enterprise": {
            "requests_per_hour": 10000,
            "messages_per_minute": 1000,
            "ai_requests_per_minute": 500,
            "file_uploads_per_hour": 500
        }
    }
    
    limits = plan_limits.get(plan, plan_limits["free"])
    
    return [
        RateLimitRule(
            name=f"tenant_{tenant_id}_requests",
            limit=limits["requests_per_hour"],
            window_seconds=3600,
            path_patterns=["/api/*"],
            tenant_ids={tenant_id},
            priority=100
        ),
        
        RateLimitRule(
            name=f"tenant_{tenant_id}_messages",
            limit=limits["messages_per_minute"],
            window_seconds=60,
            path_patterns=["/api/v1/chat/*", "/api/v1/whatsapp/send"],
            tenant_ids={tenant_id},
            priority=110
        ),
        
        RateLimitRule(
            name=f"tenant_{tenant_id}_ai",
            limit=limits["ai_requests_per_minute"],
            window_seconds=60,
            path_patterns=["/api/v1/agents/*/chat", "/api/v1/voice/*"],
            tenant_ids={tenant_id},
            priority=120
        ),
        
        RateLimitRule(
            name=f"tenant_{tenant_id}_uploads",
            limit=limits["file_uploads_per_hour"],
            window_seconds=3600,
            path_patterns=["/api/v1/upload/*"],
            tenant_ids={tenant_id},
            priority=130
        )
    ]

def get_user_specific_rules(user_id: str, role: str = "user") -> List[RateLimitRule]:
    """Retorna reglas específicas por usuario según rol"""
    
    # Límites por rol
    role_limits = {
        "user": {
            "requests_per_hour": 100,
            "messages_per_minute": 20,
            "ai_requests_per_minute": 10
        },
        "admin": {
            "requests_per_hour": 500,
            "messages_per_minute": 100,
            "ai_requests_per_minute": 50
        },
        "superadmin": {
            "requests_per_hour": 2000,
            "messages_per_minute": 500,
            "ai_requests_per_minute": 200
        }
    }
    
    limits = role_limits.get(role, role_limits["user"])
    
    return [
        RateLimitRule(
            name=f"user_{user_id}_requests",
            limit=limits["requests_per_hour"],
            window_seconds=3600,
            path_patterns=["/api/*"],
            priority=200
        ),
        
        RateLimitRule(
            name=f"user_{user_id}_messages",
            limit=limits["messages_per_minute"],
            window_seconds=60,
            path_patterns=["/api/v1/chat/*"],
            priority=210
        ),
        
        RateLimitRule(
            name=f"user_{user_id}_ai",
            limit=limits["ai_requests_per_minute"],
            window_seconds=60,
            path_patterns=["/api/v1/agents/*/chat"],
            priority=220
        )
    ]

def create_custom_rule(
    name: str,
    limit: int,
    window_seconds: int,
    path_patterns: List[str] = None,
    method_patterns: List[str] = None,
    tenant_ids: Set[str] = None,
    user_roles: Set[str] = None,
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW,
    priority: int = 100
) -> RateLimitRule:
    """Factory para crear reglas personalizadas"""
    
    return RateLimitRule(
        name=name,
        limit=limit,
        window_seconds=window_seconds,
        strategy=strategy,
        path_patterns=path_patterns or [],
        method_patterns=method_patterns or [],
        tenant_ids=tenant_ids,
        user_roles=user_roles,
        priority=priority
    )

# Validadores de configuración
def validate_rule(rule: RateLimitRule) -> List[str]:
    """Valida una regla de rate limiting"""
    errors = []
    
    if not rule.name or not rule.name.strip():
        errors.append("Nombre de regla es requerido")
    
    if rule.limit <= 0:
        errors.append("Límite debe ser mayor que 0")
    
    if rule.window_seconds <= 0:
        errors.append("Ventana de tiempo debe ser mayor que 0")
    
    if rule.priority < 0:
        errors.append("Prioridad no puede ser negativa")
    
    # Validar patrones de path
    for pattern in rule.path_patterns:
        try:
            re.compile(pattern.replace('*', '.*'))
        except re.error as e:
            errors.append(f"Patrón de path inválido '{pattern}': {e}")
    
    return errors

def validate_rules(rules: List[RateLimitRule]) -> Dict[str, List[str]]:
    """Valida múltiples reglas"""
    validation_errors = {}
    
    for rule in rules:
        rule_errors = validate_rule(rule)
        if rule_errors:
            validation_errors[rule.name] = rule_errors
    
    return validation_errors

# Utilidades para gestión de reglas
class RuleManager:
    """Gestor de reglas de rate limiting"""
    
    def __init__(self):
        self.rules: List[RateLimitRule] = []
        self.config = RateLimitConfig()
    
    def add_rule(self, rule: RateLimitRule) -> bool:
        """Agrega una regla"""
        errors = validate_rule(rule)
        if errors:
            raise RateLimitError(f"Regla inválida: {errors}")
        
        self.rules.append(rule)
        # Ordenar por prioridad
        self.rules.sort(key=lambda r: r.priority)
        return True
    
    def remove_rule(self, name: str) -> bool:
        """Remueve una regla por nombre"""
        original_length = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < original_length
    
    def get_rule(self, name: str) -> Optional[RateLimitRule]:
        """Obtiene una regla por nombre"""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
    
    def update_rule(self, name: str, **kwargs) -> bool:
        """Actualiza una regla existente"""
        rule = self.get_rule(name)
        if not rule:
            return False
        
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        # Revalidar regla actualizada
        errors = validate_rule(rule)
        if errors:
            raise RateLimitError(f"Regla actualizada inválida: {errors}")
        
        return True
    
    def enable_rule(self, name: str) -> bool:
        """Habilita una regla"""
        rule = self.get_rule(name)
        if rule:
            rule.enabled = True
            return True
        return False
    
    def disable_rule(self, name: str) -> bool:
        """Deshabilita una regla"""
        rule = self.get_rule(name)
        if rule:
            rule.enabled = False
            return True
        return False
    
    def get_rules_for_request(self, request: Request) -> List[RateLimitRule]:
        """Retorna reglas aplicables a un request"""
        return [rule for rule in self.rules if rule.matches(request)]
    
    def get_tenant_rules(self, tenant_id: str) -> List[RateLimitRule]:
        """Retorna reglas específicas de un tenant"""
        return [rule for rule in self.rules 
                if rule.tenant_ids and tenant_id in rule.tenant_ids]
    
    def export_rules(self) -> List[Dict[str, Any]]:
        """Exporta reglas a formato serializable"""
        return [
            {
                "name": rule.name,
                "limit": rule.limit,
                "window_seconds": rule.window_seconds,
                "strategy": rule.strategy.value,
                "path_patterns": rule.path_patterns,
                "method_patterns": rule.method_patterns,
                "tenant_ids": list(rule.tenant_ids) if rule.tenant_ids else None,
                "user_roles": list(rule.user_roles) if rule.user_roles else None,
                "priority": rule.priority,
                "enabled": rule.enabled
            }
            for rule in self.rules
        ]
    
    def import_rules(self, rules_data: List[Dict[str, Any]]) -> int:
        """Importa reglas desde formato serializable"""
        imported_count = 0
        
        for rule_data in rules_data:
            try:
                rule = RateLimitRule(
                    name=rule_data["name"],
                    limit=rule_data["limit"],
                    window_seconds=rule_data["window_seconds"],
                    strategy=RateLimitStrategy(rule_data.get("strategy", "fixed_window")),
                    path_patterns=rule_data.get("path_patterns", []),
                    method_patterns=rule_data.get("method_patterns", []),
                    tenant_ids=set(rule_data.get("tenant_ids", [])) if rule_data.get("tenant_ids") else None,
                    user_roles=set(rule_data.get("user_roles", [])) if rule_data.get("user_roles") else None,
                    priority=rule_data.get("priority", 100),
                    enabled=rule_data.get("enabled", True)
                )
                
                self.add_rule(rule)
                imported_count += 1
                
            except Exception as e:
                # Log error pero continuar con otras reglas
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error importando regla {rule_data.get('name', 'unknown')}: {e}")
        
        return imported_count
