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

    async def get_full_context(
        self,
        customer_id: str,
        agent_id: str,
        agent_name: str = "Asistente",
        query: str | None = None,
    ) -> dict:
        episodic = await self.get_episodic_context(
            customer_id, agent_id
        )
        semantic_raw = await self.redis.hgetall(
            self.SEMANTIC_KEY.format(customer=customer_id)
        )
        semantic = {
            k.decode(): json.loads(v.decode())
            for k, v in semantic_raw.items()
        }

        # RAG: búsqueda semántica si hay query
        rag_results: list[dict] = []
        if query:
            rag_results = await self.search_semantic_memory(
                query=query,
                customer_id=customer_id,
                limit=3,
            )

        return {
            "episodic": episodic,
            "semantic": semantic,
            "rag": rag_results,
            "instructions": self._build_system_prompt(
                semantic, agent_name, rag_results
            ),
        }

    def _build_system_prompt(
        self,
        semantic: dict,
        agent_name: str,
        rag_results: list[dict] | None = None,
    ) -> str:
        profile_str = ", ".join(
            f"{k}: {v}" for k, v in semantic.items()
        )
        rag_section = ""
        if rag_results:
            rag_lines = "\n".join(
                f"  - {r['content'][:200]}"
                for r in rag_results
                if r.get("similarity", 0) > 0.75
            )
            if rag_lines:
                rag_section = (
                    f"\nContexto relevante de conversaciones anteriores:\n"
                    f"{rag_lines}"
                )
        return (
            f"Eres {agent_name}, asistente comercial experto.\n"
            f"Perfil del cliente: "
            f"{profile_str or 'Cliente nuevo, sin historial.'}"
            f"{rag_section}\n"
            f"- Mantén coherencia con conversaciones previas.\n"
            f"- Prioriza soluciones basadas en su historial.\n"
            f"- Si detectas frustración, escala a un humano."
        )

    async def _get_embedding(
        self, text: str
    ) -> list[float] | None:
        import httpx
        model = getattr(
            settings, "ollama_embedding_model",
            "nomic-embed-text"
        )
        base_url = getattr(
            settings, "ollama_base_url",
            "http://localhost:11434"
        )
        try:
            async with httpx.AsyncClient(
                timeout=30.0
            ) as client:
                r = await client.post(
                    f"{base_url}/api/embeddings",
                    json={"model": model, "prompt": text},
                )
                r.raise_for_status()
                return r.json().get("embedding")
        except Exception as exc:
            import logging
            logging.getLogger("flux.ai_memory").warning(
                "embedding_generation_failed",
                extra={"error": str(exc)},
            )
            return None

    async def persist_to_vector_db(
        self, customer_id: str, agent_id: str,
        tenant_id: str | None = None
    ) -> int:
        from sqlalchemy import text
        interactions = await self.get_episodic_context(
            customer_id, agent_id, limit=50
        )
        saved = 0
        for turn in interactions:
            content = turn.get("content", "").strip()
            if not content or len(content) < 10:
                continue
            embedding = await self._get_embedding(content)
            if not embedding:
                continue
            try:
                await self.db.execute(
                    text("""
                        INSERT INTO flux_semantic_memory
                          (tenant_id, customer_id, agent_id,
                           content, role, embedding, metadata)
                        VALUES
                          (:tid::uuid, :cid, :aid, :content,
                           :role, :emb::vector, :meta::jsonb)
                    """),
                    {
                        "tid": tenant_id,
                        "cid": customer_id,
                        "aid": agent_id,
                        "content": content,
                        "role": turn.get("role", "user"),
                        "emb": str(embedding),
                        "meta": json.dumps(
                            turn.get("metadata", {})
                        ),
                    },
                )
                saved += 1
            except Exception as exc:
                import logging
                logging.getLogger("flux.ai_memory").warning(
                    "persist_embedding_failed",
                    extra={"error": str(exc)},
                )
        await self.db.commit()
        return saved

    async def search_semantic_memory(
        self,
        query: str,
        customer_id: str,
        limit: int = 5,
    ) -> list[dict]:
        from sqlalchemy import text
        embedding = await self._get_embedding(query)
        if not embedding:
            return []
        try:
            result = await self.db.execute(
                text("""
                    SELECT content, role, metadata,
                           1 - (embedding <=> :emb::vector)
                           AS similarity
                    FROM flux_semantic_memory
                    WHERE customer_id = :cid
                      AND embedding IS NOT NULL
                    ORDER BY embedding <=> :emb::vector
                    LIMIT :limit
                """),
                {
                    "cid": customer_id,
                    "emb": str(embedding),
                    "limit": limit,
                },
            )
            return [
                {
                    "content": r.content,
                    "role": r.role,
                    "similarity": round(float(r.similarity), 3),
                    "metadata": r.metadata or {},
                }
                for r in result.fetchall()
            ]
        except Exception as exc:
            import logging
            logging.getLogger("flux.ai_memory").warning(
                "semantic_search_failed",
                extra={"error": str(exc)},
            )
            return []
