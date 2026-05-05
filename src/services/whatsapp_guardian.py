"""
WHATSAPP BAN PROTECTOR
======================
Sistema de protección proactiva contra bloqueos de WhatsApp.
Implementa:
- Rate limiting por número
- Filtro de contenido spam
- Logging de auditoría
- Detección de comportamiento no humano
"""

import time
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


class MessageType(Enum):
    SERVICE = "service"        # Mensajes iniciados por usuario (gratuitos)
    UTILITY = "utility"       # Notificaciones (templated)
    AUTHENTICATION = "authentication"  # OTPs
    MARKETING = "marketing"    # Promociones (costoso, requiere aprobación)


@dataclass
class ValidationReport:
    """Reporte de validación de mensaje."""
    result: ValidationResult = ValidationResult.ALLOW
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def allow(self, message: str = ""):
        self.result = ValidationResult.ALLOW
        self.message = message or "Mensaje permitido"
        
    def warn(self, message: str):
        self.result = ValidationResult.WARN
        self.message = message
        
    def block(self, message: str):
        self.result = ValidationResult.BLOCK
        self.message = message


class WhatsAppBanProtector:
    """
    Sistema de protección proactiva contra bloqueos de WhatsApp/Meta.
    """
    
    # Patrones que pueden触发 spam detection
    SPAM_KEYWORDS = [
        "gratis", "gratis!", "gana", "ganaste", "Premio", "premio",
        "click aquí", "haz click", "有限", "limited", "urgente",
        "sin costo", "sin cargo", "100% gratis", "gana dinero",
        "trabajo desde casa", "ingresa ahora", "registro gratis"
    ]
    
    # Ratios de seguridad
    MAX_MESSAGES_PER_SECOND = 1
    MAX_MESSAGES_PER_MINUTE = 20
    MAX_MESSAGES_PER_HOUR = 100
    MAX_CONVERSATIONS_PER_DAY = 500
    MIN_DELAY_MS = 800
    MAX_DELAY_MS = 1500
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._init_redis()
    
    def _init_redis(self):
        if not self.redis:
            try:
                import redis.asyncio as redis
                from config import obtener_config
                config = obtener_config()
                self.redis = redis.from_url(config.redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Redis no disponible para ban protector: {e}")
    
    async def validate_message_before_send(
        self, 
        tenant_id: str, 
        message: str, 
        recipient: str,
        message_type: str = "service"
    ) -> ValidationReport:
        """
        Valida mensaje antes del envío para prevenir bans.
        """
        report = ValidationReport()
        
        # 1. Rate limiting por número (evita comportamiento robótico)
        if await self._exceeds_human_pattern(tenant_id, recipient):
            report.block("Rate limit exceeded: comportamiento no humano detectado")
            await self._log_block(tenant_id, recipient, "rate_limit", report.message)
            return report
        
        # 2. Filtro de contenido spam
        if self._contains_spam_patterns(message):
            if message_type == "marketing":
                # Marketing con palabras spam = BLOCK
                report.block("Contenido spam detectado en mensaje de marketing")
                await self._log_block(tenant_id, recipient, "spam_marketing", report.message)
                return report
            else:
                # Otros tipos = WARN
                report.warn(f"Contenido potencialmente spam. Revisar: {message[:50]}...")
        
        # 3. Verificar longitud excesiva
        if len(message) > 4096:
            report.block("Mensaje demasiado largo (max 4096 caracteres)")
            await self._log_block(tenant_id, recipient, "length", report.message)
            return report
        
        # 4. Verificar demasiados emojis (spam indicator)
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F]', message))
        if emoji_count > 10:
            report.warn(f"Demasiados emojis ({emoji_count}). Puede considerarse spam.")
        
        # 5. Logging para auditoría (requerido por Meta)
        await self._log_outbound_message(tenant_id, message, recipient, message_type)
        
        if report.result == ValidationResult.ALLOW:
            report.allow("Mensaje validado correctamente")
        
        return report
    
    async def _exceeds_human_pattern(self, tenant_id: str, recipient: str) -> bool:
        """Detecta si el envío parece automatizado (riesgo de ban)."""
        if not self.redis:
            return False
        
        try:
            key_prefix = f"whatsapp:rate:{tenant_id}:{recipient}"
            
            # Verificar mensajes por segundo
            sec_key = f"{key_prefix}:sec"
            count_sec = await self.redis.get(sec_key)
            if count_sec and int(count_sec) >= self.MAX_MESSAGES_PER_SECOND:
                logger.warning(f"Rate limit exceeded per second for {recipient}")
                return True
            
            # Verificar mensajes por minuto
            min_key = f"{key_prefix}:min"
            count_min = await self.redis.get(min_key)
            if count_min and int(count_min) >= self.MAX_MESSAGES_PER_MINUTE:
                logger.warning(f"Rate limit exceeded per minute for {recipient}")
                return True
            
            # Verificar conversaciones hoy
            day_key = f"{key_prefix}:today"
            count_day = await self.redis.get(day_key)
            if count_day and int(count_day) >= self.MAX_CONVERSATIONS_PER_DAY:
                logger.warning(f"Daily conversation limit exceeded for {recipient}")
                return True
            
            # Incrementar contadores
            pipe = self.redis.pipeline()
            pipe.incr(sec_key)
            pipe.expire(sec_key, 1)
            pipe.incr(min_key)
            pipe.expire(min_key, 60)
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)
            await pipe.execute()
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False
    
    def _contains_spam_patterns(self, message: str) -> bool:
        """Detecta patrones de spam en el contenido."""
        message_lower = message.lower()
        
        for keyword in self.SPAM_KEYWORDS:
            if keyword.lower() in message_lower:
                logger.warning(f"Spam keyword detected: {keyword}")
                return True
        
        # Detectar URLs cortas sospechosas
        short_urls = re.findall(r'https?://[\w\-]{1,15}\.\w+', message)
        if len(short_urls) > 2:
            logger.warning("Multiple short URLs detected")
            return True
        
        # Detectar números de teléfono en mensaje marketing
        phone_pattern = re.findall(r'\d{8,}', message)
        if len(phone_pattern) > 3:
            logger.warning("Multiple phone numbers detected")
            return True
        
        return False
    
    async def _log_outbound_message(
        self, 
        tenant_id: str, 
        message: str, 
        recipient: str,
        message_type: str
    ):
        """Logging para auditoría (requerido por Meta)."""
        if not self.redis:
            return
        
        try:
            log_key = f"whatsapp:audit:{tenant_id}"
            
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "recipient": recipient,
                "message_type": message_type,
                "message_length": len(message),
                "result": "sent"
            }
            
            await self.redis.lpush(log_key, str(log_entry))
            await self.redis.ltrim(log_key, 0, 999)  # Mantener últimos 1000
            
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
    
    async def _log_block(self, tenant_id: str, recipient: str, reason: str, message: str):
        """Log de mensajes bloqueados."""
        logger.warning(f"Message blocked - tenant: {tenant_id}, recipient: {recipient}, reason: {reason}")
        
        if self.redis:
            try:
                block_key = f"whatsapp:blocks:{tenant_id}"
                await self.redis.lpush(block_key, f"{time.time()}:{recipient}:{reason}:{message[:100]}")
                await self.redis.ltrim(block_key, 0, 99)
            except:
                pass
    
    async def get_health_status(self, tenant_id: str) -> Dict[str, Any]:
        """Retorna estado de salud del número de WhatsApp."""
        if not self.redis:
            return {"status": "unknown", "reason": "Redis not available"}
        
        try:
            # Contar bloqueos recientes
            block_key = f"whatsapp:blocks:{tenant_id}"
            blocks = await self.redis.lrange(block_key, 0, 9)
            
            block_count = len(blocks)
            
            # Determinar calidad
            if block_count == 0:
                quality = "GREEN"
            elif block_count < 5:
                quality = "YELLOW"
            else:
                quality = "RED"
            
            return {
                "quality_rating": quality,
                "recent_blocks": block_count,
                "status": "healthy" if quality == "GREEN" else "degraded",
                "recommendation": self._get_recommendation(quality, block_count)
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"status": "unknown", "error": str(e)}
    
    def _get_recommendation(self, quality: str, blocks: int) -> str:
        """Recomienda acciones según calidad."""
        if quality == "GREEN":
            return "Número en buen estado. Continúa operación normal."
        elif quality == "YELLOW":
            return "Precaución: Reduces mensajes de marketing por 24h. Evita palabras spam."
        else:
            return "CRÍTICO: Número en riesgo. Detén mensajes de marketing inmediatamente. espera 48h."