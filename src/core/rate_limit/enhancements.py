# =============================================================================
# FLUXAGENT V2 — RATE LIMIT ENHANCEMENTS
# =============================================================================
# Mejoras opcionales para el rate limiting existente
# Basado en análisis de la propuesta SlowAPI
# =============================================================================

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .middleware import RateLimitMiddleware
from .rules import RateLimitRule, create_custom_rule

@dataclass
class SlowAPICompatibility:
    """Compatibilidad con sintaxis SlowAPI para migración fácil"""
    
    @staticmethod
    def create_slowapi_style_rule(
        limit: str,  # "100 per minute"
        key_func: str = "tenant",  # "tenant", "ip", "user"
        strategy: str = "fixed-window",
        per_method: bool = True
    ) -> RateLimitRule:
        """Crea regla compatible con sintaxis SlowAPI"""
        
        # Parsear "100 per minute"
        parts = limit.split()
        if len(parts) != 3 or parts[1] != "per":
            raise ValueError("Formato debe ser: '<number> per <period>'")
        
        limit_count = int(parts[0])
        period = parts[2]
        
        # Convertir período a segundos
        period_seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }.get(period, 60)
        
        # Generar nombre de regla
        rule_name = f"slowapi_{key_func}_{limit_count}_{period}"
        
        # Path patterns según key_func
        path_patterns = ["/*"]  # Default para todos
        
        return create_custom_rule(
            name=rule_name,
            limit=limit_count,
            window_seconds=period_seconds,
            path_patterns=path_patterns,
            strategy=strategy,
            priority=100
        )

class RateLimitCategories:
    """Categorías predefinidas compatibles con propuesta"""
    
    # Categorías exactas de la propuesta
    DEFAULT = "100 per minute"
    AUTH = "10 per minute"
    WHATSAPP = "30 per minute"
    VOICE = "5 per minute"
    ANALYTICS = "60 per minute"
    WEBHOOK = "20 per minute"
    
    @classmethod
    def get_rules(cls) -> list[RateLimitRule]:
        """Retorna todas las reglas como RateLimitRule"""
        rules = []
        
        for category_name, limit_str in [
            ("default", cls.DEFAULT),
            ("auth", cls.AUTH),
            ("whatsapp", cls.WHATSAPP),
            ("voice", cls.VOICE),
            ("analytics", cls.ANALYTICS),
            ("webhook", cls.WEBHOOK)
        ]:
            rule = SlowAPICompatibility.create_slowapi_style_rule(
                limit=limit_str,
                key_func="tenant",
                strategy="fixed-window"
            )
            rule.name = f"category_{category_name}"
            rules.append(rule)
        
        return rules

# Decorador compatible con sintaxis de la propuesta
def limit_by_category_enhanced(category: str):
    """
    Versión mejorada del decorador de la propuesta
    Usa el rate limit existente pero con sintaxis compatible
    """
    from .middleware import RateLimitMiddleware
    
    # Mapeo de categorías a límites
    category_limits = {
        "default": RateLimitCategories.DEFAULT,
        "auth": RateLimitCategories.AUTH,
        "whatsapp": RateLimitCategories.WHATSAPP,
        "voice": RateLimitCategories.VOICE,
        "analytics": RateLimitCategories.ANALYTICS,
        "webhook": RateLimitCategories.WEBHOOK
    }
    
    limit_str = category_limits.get(category, RateLimitCategories.DEFAULT)
    rule = SlowAPICompatibility.create_slowapi_style_rule(
        limit=limit_str,
        key_func="tenant"
    )
    
    def decorator(func):
        # Agregar metadata para middleware existente
        func._rate_limit_rule = rule
        func._rate_limit_enabled = True
        return func
    
    return decorator

# Middleware híbrido que soporta ambas sintaxis
class HybridRateLimitMiddleware(RateLimitMiddleware):
    """Middleware que soporta sintaxis existente y SlowAPI-style"""
    
    def __init__(self, app, **kwargs):
        # Inicializar con configuración existente
        super().__init__(app, **kwargs)
        
        # Agregar reglas compatibles con SlowAPI
        slowapi_rules = RateLimitCategories.get_rules()
        self.rules.extend(slowapi_rules)
        
        # Reordenar por prioridad
        self.rules.sort(key=lambda r: r.priority)
    
    async def dispatch(self, request, call_next):
        """Dispatch con soporte para decoradores estilo SlowAPI"""
        
        # Verificar si el endpoint tiene regla específica
        endpoint = getattr(request.state, 'endpoint', None)
        if endpoint and hasattr(endpoint, '_rate_limit_enabled'):
            rule = endpoint._rate_limit_rule
            if rule.matches(request):
                await self._apply_rule(rule, self._default_key_generator(request), request)
        
        # Continuar con lógica existente
        return await super().dispatch(request, call_next)

# Factory para fácil migración
def create_slowapi_compatible_middleware(app, enable_categories: bool = True):
    """
    Crea middleware compatible con sintaxis SlowAPI
    pero usando la implementación superior existente
    """
    
    if enable_categories:
        return HybridRateLimitMiddleware(app)
    else:
        return RateLimitMiddleware(app)

# Ejemplo de uso (compatibilidad con propuesta)
async def example_usage():
    """Ejemplo de cómo usar la sintaxis compatible"""
    
    # Opción 1: Usar middleware híbrido
    from fastapi import FastAPI
    app = FastAPI()
    
    # Agregar middleware compatible
    app.add_middleware(
        create_slowapi_compatible_middleware(app, enable_categories=True)
    )
    
    # Opción 2: Usar decoradores compatibles
    @limit_by_category_enhanced("whatsapp")
    async def send_whatsapp():
        return {"status": "sent"}
    
    # Opción 3: Crear reglas manualmente con sintaxis SlowAPI
    rule = SlowAPICompatibility.create_slowapi_style_rule(
        limit="50 per hour",
        key_func="tenant",
        strategy="sliding-window"
    )

# Utilidades para migración desde SlowAPI
class SlowAPIMigrationHelper:
    """Helper para migrar desde SlowAPI a implementación actual"""
    
    @staticmethod
    def convert_slowapi_config(slowapi_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte configuración SlowAPI a formato actual"""
        
        converted_config = {
            "rules": [],
            "middleware_config": {
                "enabled": True,
                "skip_paths": ["/health", "/metrics"]
            }
        }
        
        # Convertir límites por defecto
        if "default_limits" in slowapi_config:
            for limit_str in slowapi_config["default_limits"]:
                rule = SlowAPICompatibility.create_slowapi_style_rule(limit_str)
                converted_config["rules"].append(rule)
        
        # Convertir key functions
        if "key_func" in slowapi_config:
            key_func = slowapi_config["key_func"]
            if key_func == "get_ipaddr":
                converted_config["middleware_config"]["key_generator"] = "ip"
            elif key_func == "tenant_rate_limit_key":
                converted_config["middleware_config"]["key_generator"] = "tenant"
        
        return converted_config
    
    @staticmethod
    def analyze_slowapi_dependencies():
        """Analiza dependencias necesarias para SlowAPI"""
        return {
            "required": [
                "slowapi>=0.1.9",
                "redis>=4.0.0"
            ],
            "optional": [
                "slowapi-middleware>=0.1.0"
            ],
            "comparison": {
                "current_implementation": "No requiere dependencias externas",
                "slowapi": "Añade 2+ dependencias",
                "recommendation": "Mantener implementación actual"
            }
        }
