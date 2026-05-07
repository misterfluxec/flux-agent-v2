# =============================================================================
# FLUXAGENT V2 — CACHE KEYS
# =============================================================================
# Generador de claves type-safe y consistentes
# Hash de parámetros para evitar claves muy largas
# =============================================================================

import hashlib
import json
import re
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

class CacheNamespace(Enum):
    """Namespaces predefinidos para cache"""
    ANALYTICS = "analytics"
    AGENTS = "agents"
    USERS = "users"
    TENANTS = "tenants"
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    WHATSAPP = "whatsapp"
    VOICE = "voice"
    AUTH = "auth"
    RATE_LIMIT = "ratelimit"
    SESSIONS = "sessions"
    WEBHOOKS = "webhooks"

class CacheKeyBuilder:
    """Construye claves de cache consistentes y predecibles"""
    
    def __init__(self, namespace: Union[str, CacheNamespace], entity: str):
        self.namespace = namespace.value if isinstance(namespace, CacheNamespace) else namespace
        self.entity = entity
        self.prefix = "fluxagent"
    
    def build(self, **kwargs) -> str:
        """
        Genera clave: fluxagent:{namespace}:{entity}:{hash_params}
        
        Los parámetros se ordenan y hashean para claves consistentes.
        """
        # Filtrar valores None y convertir a JSON canónico
        clean_params = self._clean_params(kwargs)
        
        if not clean_params:
            return f"{self.prefix}:{self.namespace}:{self.entity}:all"
        
        # Hash de parámetros para evitar claves muy largas
        params_hash = self._hash_params(clean_params)
        
        return f"{self.prefix}:{self.namespace}:{self.entity}:{params_hash}"
    
    def build_tenant_scoped(self, tenant_id: str, **kwargs) -> str:
        """Helper para claves con aislamiento por tenant"""
        return self.build(tenant_id=tenant_id, **kwargs)
    
    def build_user_scoped(self, user_id: str, **kwargs) -> str:
        """Helper para claves con aislamiento por usuario"""
        return self.build(user_id=user_id, **kwargs)
    
    def build_time_scoped(self, time_window: str, **kwargs) -> str:
        """Helper para claves con ventana de tiempo"""
        return self.build(time_window=time_window, **kwargs)
    
    def _clean_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia y normaliza parámetros"""
        clean = {}
        
        for key, value in sorted(params.items()):
            if value is None:
                continue
            
            # Normalizar tipos complejos
            if isinstance(value, (datetime, timedelta)):
                clean[key] = str(value)
            elif isinstance(value, (dict, list, tuple)):
                clean[key] = json.dumps(value, sort_keys=True, default=str)
            elif hasattr(value, 'model_dump'):  # Pydantic models
                clean[key] = value.model_dump_json()
            else:
                clean[key] = str(value)
        
        return clean
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Genera hash consistente de parámetros"""
        params_json = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(params_json.encode()).hexdigest()[:16]
    
    @staticmethod
    def from_pattern(pattern: str, **kwargs) -> str:
        """
        Construye clave desde patrón con placeholders.
        
        Ej: CacheKeyBuilder.from_pattern("analytics:tenant_{tenant_id}:days_{days}", tenant_id="123", days=7)
        """
        # Validar que todos los placeholders tengan valores
        placeholders = re.findall(r'\{(\w+)\}', pattern)
        missing = [p for p in placeholders if p not in kwargs]
        
        if missing:
            raise ValueError(f"Faltan valores para placeholders: {missing}")
        
        return pattern.format(**kwargs)

# Factories para claves comunes
class CacheKeys:
    """Factory methods para claves de cache comunes"""
    
    @staticmethod
    def analytics_overview(tenant_id: str, days: int) -> str:
        builder = CacheKeyBuilder(CacheNamespace.ANALYTICS, "overview")
        return builder.build_tenant_scoped(tenant_id, days=days)
    
    @staticmethod
    def analytics_daily_stats(tenant_id: str, date: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.ANALYTICS, "daily_stats")
        return builder.build_tenant_scoped(tenant_id, date=date)
    
    @staticmethod
    def agent_list(tenant_id: str, status: Optional[str] = None) -> str:
        builder = CacheKeyBuilder(CacheNamespace.AGENTS, "list")
        return builder.build_tenant_scoped(tenant_id, status=status)
    
    @staticmethod
    def agent_details(tenant_id: str, agent_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.AGENTS, "details")
        return builder.build_tenant_scoped(tenant_id, agent_id=agent_id)
    
    @staticmethod
    def user_profile(user_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.USERS, "profile")
        return builder.build_user_scoped(user_id)
    
    @staticmethod
    def user_permissions(user_id: str, tenant_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.USERS, "permissions")
        return builder.build(user_id=user_id, tenant_id=tenant_id)
    
    @staticmethod
    def tenant_config(tenant_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.TENANTS, "config")
        return builder.build_tenant_scoped(tenant_id)
    
    @staticmethod
    def tenant_limits(tenant_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.TENANTS, "limits")
        return builder.build_tenant_scoped(tenant_id)
    
    @staticmethod
    def conversation_messages(tenant_id: str, conversation_id: str, limit: int = 50) -> str:
        builder = CacheKeyBuilder(CacheNamespace.CONVERSATIONS, "messages")
        return builder.build_tenant_scoped(tenant_id, conversation_id=conversation_id, limit=limit)
    
    @staticmethod
    def whatsapp_instance_status(tenant_id: str, instance_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.WHATSAPP, "instance_status")
        return builder.build_tenant_scoped(tenant_id, instance_id=instance_id)
    
    @staticmethod
    def voice_processing_status(tenant_id: str, task_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.VOICE, "processing_status")
        return builder.build_tenant_scoped(tenant_id, task_id=task_id)
    
    @staticmethod
    def auth_session(session_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.AUTH, "session")
        return builder.build(session_id=session_id)
    
    @staticmethod
    def auth_token(token_hash: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.AUTH, "token")
        return builder.build(token_hash=token_hash)
    
    @staticmethod
    def rate_limit(identifier: str, endpoint: str, window: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.RATE_LIMIT, "limit")
        return builder.build(identifier=identifier, endpoint=endpoint, window=window)
    
    @staticmethod
    def webhook_processing(webhook_id: str) -> str:
        builder = CacheKeyBuilder(CacheNamespace.WEBHOOKS, "processing")
        return builder.build(webhook_id=webhook_id)
    
    @staticmethod
    def search_results(query: str, tenant_id: str, filters: Optional[Dict] = None) -> str:
        builder = CacheKeyBuilder(CacheNamespace.ANALYTICS, "search")
        return builder.build_tenant_scoped(tenant_id, query=query, filters=filters or {})

# Patrones de invalidación
class CachePatterns:
    """Patrones comunes para invalidación de cache"""
    
    @staticmethod
    def tenant_all(tenant_id: str) -> str:
        """Invalida todo el cache de un tenant"""
        return f"fluxagent:*:*tenant_{tenant_id}*"
    
    @staticmethod
    def tenant_analytics(tenant_id: str) -> str:
        """Invalida cache de analytics de un tenant"""
        return f"fluxagent:{CacheNamespace.ANALYTICS.value}:*tenant_{tenant_id}*"
    
    @staticmethod
    def tenant_agents(tenant_id: str) -> str:
        """Invalida cache de agents de un tenant"""
        return f"fluxagent:{CacheNamespace.AGENTS.value}:*tenant_{tenant_id}*"
    
    @staticmethod
    def user_all(user_id: str) -> str:
        """Invalida todo el cache de un usuario"""
        return f"fluxagent:*:*user_{user_id}*"
    
    @staticmethod
    def agent_related(tenant_id: str, agent_id: str) -> str:
        """Invalida cache relacionado con un agente específico"""
        patterns = [
            f"fluxagent:{CacheNamespace.AGENTS.value}:*tenant_{tenant_id}*",
            f"fluxagent:{CacheNamespace.ANALYTICS.value}:*tenant_{tenant_id}*",
            f"fluxagent:{CacheNamespace.CONVERSATIONS.value}:*tenant_{tenant_id}*agent_{agent_id}*"
        ]
        return patterns
    
    @staticmethod
    def conversation_related(tenant_id: str, conversation_id: str) -> str:
        """Invalida cache relacionado con una conversación"""
        return f"fluxagent:{CacheNamespace.CONVERSATIONS.value}:*tenant_{tenant_id}*conversation_{conversation_id}*"

# Utilidades para manejo de claves
class CacheKeyUtils:
    """Utilidades para manejo avanzado de claves"""
    
    @staticmethod
    def parse_key(key: str) -> Dict[str, str]:
        """Parsea clave y extrae componentes"""
        parts = key.split(':')
        if len(parts) < 4 or parts[0] != 'fluxagent':
            return {}
        
        return {
            'prefix': parts[0],
            'namespace': parts[1],
            'entity': parts[2],
            'hash': parts[3] if len(parts) > 3 else None
        }
    
    @staticmethod
    def is_tenant_key(key: str) -> bool:
        """Verifica si clave pertenece a un tenant específico"""
        return 'tenant_' in key
    
    @staticmethod
    def extract_tenant_id(key: str) -> Optional[str]:
        """Extrae tenant_id de una clave"""
        match = re.search(r'tenant_([a-f0-9\-]+)', key)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_user_id(key: str) -> Optional[str]:
        """Extrae user_id de una clave"""
        match = re.search(r'user_([a-f0-9\-]+)', key)
        return match.group(1) if match else None
    
    @staticmethod
    def estimate_key_size(key: str) -> Dict[str, int]:
        """Estima tamaño de clave en bytes"""
        return {
            'bytes': len(key.encode('utf-8')),
            'characters': len(key),
            'parts': len(key.split(':'))
        }
    
    @staticmethod
    def validate_key(key: str) -> Dict[str, Any]:
        """Valida formato de clave"""
        errors = []
        warnings = []
        
        # Longitud máxima recomendada
        if len(key) > 250:
            warnings.append("Clave muy larga (>250 chars)")
        
        # Debe tener prefijo correcto
        if not key.startswith('fluxagent:'):
            errors.append("Clave debe empezar con 'fluxagent:'")
        
        # Debe tener suficientes partes
        parts = key.split(':')
        if len(parts) < 4:
            errors.append("Clave debe tener formato: prefix:namespace:entity:hash")
        
        # Namespace válido
        if len(parts) >= 2:
            namespace = parts[1]
            valid_namespaces = [ns.value for ns in CacheNamespace]
            if namespace not in valid_namespaces:
                warnings.append(f"Namespace '{namespace}' no está en la lista de namespaces predefinidos")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'recommendations': [
                "Usar CacheKeyBuilder para generar claves consistentes",
                "Incluir tenant_id en claves de datos multi-tenant",
                "Usar hash para parámetros complejos"
            ]
        }
