import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from config import obtener_config

settings = obtener_config()

class AIMemoryManager:
    """
    Motor de Memoria IA (Episódica + Semántica).
    Usa Redis para contexto rápido (ventanas de contexto LLM)
    y prepara la capa para PostgreSQL/pgvector (historial semántico a largo plazo).
    """
    def __init__(self, redis: Redis, db_session: AsyncSession):
        self.redis = redis
        self.db = db_session
        self.EPISODIC_PREFIX = "mem:episodic:{customer}:{agent}"
        self.SEMANTIC_KEY = "mem:semantic:{customer}"
        self.TTL_EPISODIC = 86400 * 7  # 7 días
        self.TTL_SEMANTIC = 86400 * 30 # 30 días
        # Potenciación: Hacer el límite configurable o dinámico
        self.EPISODIC_LIMIT = 50 

    async def save_interaction(self, customer_id: str, agent_id: str, message: str, role: str, metadata: Optional[Dict] = None):
        """Guarda interacción en memoria episódica (Redis)"""
        key = self.EPISODIC_PREFIX.format(customer=customer_id, agent=agent_id)
        entry = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        await self.redis.lpush(key, json.dumps(entry))
        await self.redis.ltrim(key, 0, self.EPISODIC_LIMIT - 1)  # Mantener las últimas N interacciones
        await self.redis.expire(key, self.TTL_EPISODIC)

    async def get_episodic_context(self, customer_id: str, agent_id: str, limit: int = 10) -> List[Dict]:
        """Recupera contexto conversacional reciente (útil para el prompt de chat)"""
        key = self.EPISODIC_PREFIX.format(customer=customer_id, agent=agent_id)
        raw = await self.redis.lrange(key, 0, limit - 1)
        # Reverse to get chronological order (oldest first)
        return [json.loads(r) for r in reversed(raw)]

    async def update_semantic_profile(self, customer_id: str, traits: Dict):
        """Actualiza perfil semántico (preferencias, tono, historial de compras, etc.)"""
        key = self.SEMANTIC_KEY.format(customer=customer_id)
        existing = await self.redis.hgetall(key)
        profile = {k.decode(): v.decode() for k, v in existing.items()}
        profile.update({k: json.dumps(v) for k, v in traits.items()})
        await self.redis.hset(key, mapping=profile)
        await self.redis.expire(key, self.TTL_SEMANTIC)

    async def get_full_context(self, customer_id: str, agent_id: str, agent_name: str = "Asistente") -> Dict:
        """Combina memoria episódica + semántica + RAG documental para el prompt"""
        episodic = await self.get_episodic_context(customer_id, agent_id)
        semantic_raw = await self.redis.hgetall(self.SEMANTIC_KEY.format(customer=customer_id))
        semantic = {k.decode(): json.loads(v.decode()) for k, v in semantic_raw.items()}
        
        return {
            "episodic": episodic,
            "semantic": semantic,
            "instructions": self._build_system_prompt(semantic, agent_name)
        }

    def _build_system_prompt(self, semantic: Dict, agent_name: str) -> str:
        """Construye el prompt base inyectando la memoria semántica del cliente"""
        profile_str = ", ".join([f"{k}: {v}" for k, v in semantic.items()])
        return f"""
        Eres {agent_name}, asistente comercial experto. 
        Contexto del cliente: {profile_str if profile_str else "Cliente nuevo, sin historial previo."}
        - Mantén coherencia con conversaciones previas.
        - Prioriza soluciones basadas en su historial.
        - Si detectas frustración o algo fuera de tu alcance, escala suavemente a un humano.
        """
        
    async def persist_to_vector_db(self, customer_id: str, agent_id: str):
        """
        [Potenciación]
        Mueve interacciones antiguas de Redis a PostgreSQL con pgvector 
        para memoria a largo plazo (RAG).
        """
        pass
