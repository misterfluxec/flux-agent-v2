"""
FLUXAGENT V2 — HYBRID CHANNEL ROUTER
======================================
Router inteligente que decide:
  1. Qué canal usar (Cloud API vs Evolution API)
  2. Qué credenciales usar (pool global vs BYOA del cliente)
  3. Cuándo hacer fallback y cómo

Reemplaza el anterior HybridWhatsAppRouter con soporte completo de cuotas híbridas.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from config import obtener_config
from core.encryption import EncryptionService, mask_sensitive

logger = logging.getLogger(__name__)
config = obtener_config()

# ---------------------------------------------------------------------------
# Constantes de canal y modo (strings alineados con constraint CHECK de BD)
# ---------------------------------------------------------------------------
CLOUD_API     = "cloud_api"
EVOLUTION_API = "evolution_api"
FALLBACK      = "fallback"

GLOBAL_POOL = "global_pool"
BYOA        = "byoa"
HYBRID      = "hybrid"


@dataclass
class SendResult:
    """Resultado del envío con metadatos de canal y costo."""
    success: bool
    message_id: Optional[str] = None
    channel_used: str = ""
    is_fallback: bool = False
    cost_usd: float = 0.0
    error: Optional[str] = None


class QuotaExhaustedError(Exception):
    """Se lanza cuando no hay cuota disponible en ningún canal."""
    pass


class ChannelUnavailableError(Exception):
    """Se lanza cuando un canal específico no está disponible o configurado."""
    pass


class HybridChannelRouter:
    """
    Resuelve configuración de envío para un tenant dado basándose en su
    quota_mode y cuotas disponibles.

    Uso:
        resolution = HybridChannelRouter.resolve(tenant_dict, message_type="service")
        # resolution["channel"], resolution["credentials"], resolution["quota_source"]
    """

    @classmethod
    def resolve(cls, tenant: dict, message_type: str = "service") -> Dict[str, Any]:
        """
        Punto de entrada principal.

        Args:
            tenant      : Dict con las columnas de la tabla tenants (incluyendo
                          columnas de migración 008: quota_mode, used_cloud_api, etc.)
            message_type: service | utility | authentication | marketing

        Returns:
            {
              channel      : str ("cloud_api" | "evolution_api"),
              credentials  : dict,
              quota_source : str ("global_pool" | "byoa" | "byoa_fallback"),
              cost_estimate: {"meta_cost": float, "markup": float}
            }
        """
        quota_mode = tenant.get("quota_mode", GLOBAL_POOL)

        if quota_mode == BYOA:
            return cls._resolve_byoa(tenant, message_type)
        elif quota_mode == HYBRID:
            return cls._resolve_hybrid(tenant, message_type)
        else:
            return cls._resolve_global_pool(tenant, message_type)

    # ------------------------------------------------------------------
    # Estrategias privadas
    # ------------------------------------------------------------------

    @classmethod
    def _resolve_byoa(cls, tenant: dict, message_type: str) -> Dict[str, Any]:
        """El cliente usa sus propias credenciales; no consume cuota del pool."""
        if not tenant.get("is_byoa_enabled"):
            raise ChannelUnavailableError("BYOA no está habilitado para este tenant")

        cloud_token      = EncryptionService.decrypt(tenant.get("byoa_cloud_token") or "")
        phone_number_id  = tenant.get("byoa_phone_number_id")

        if cloud_token and phone_number_id:
            logger.debug(
                "Tenant %s: BYOA → Cloud API (token=%s)",
                tenant.get("id"), mask_sensitive(cloud_token)
            )
            return {
                "channel": CLOUD_API,
                "credentials": {
                    "access_token": cloud_token,
                    "phone_number_id": phone_number_id,
                    "waba_id": tenant.get("byoa_waba_id"),
                },
                "quota_source": BYOA,
                "cost_estimate": {"meta_cost": "billed_to_customer", "markup": 0},
            }

        evolution_url = tenant.get("byoa_evolution_url")
        evolution_key = EncryptionService.decrypt(tenant.get("byoa_evolution_api_key") or "")

        if evolution_url:
            logger.debug("Tenant %s: BYOA → Evolution API", tenant.get("id"))
            return {
                "channel": EVOLUTION_API,
                "credentials": {
                    "base_url": evolution_url,
                    "api_key": evolution_key,
                },
                "quota_source": BYOA,
                "cost_estimate": {"meta_cost": 0, "markup": 0},
            }

        raise ChannelUnavailableError(
            "BYOA habilitado pero sin credenciales de Cloud API ni Evolution configuradas"
        )

    @classmethod
    def _resolve_hybrid(cls, tenant: dict, message_type: str) -> Dict[str, Any]:
        """Intenta pool global primero; si se agota activa BYOA del cliente."""
        try:
            return cls._resolve_global_pool(tenant, message_type)
        except QuotaExhaustedError:
            if tenant.get("is_byoa_enabled"):
                logger.info(
                    "Tenant %s: cuota global agotada → activando BYOA fallback",
                    tenant.get("id")
                )
                result = cls._resolve_byoa(tenant, message_type)
                result["quota_source"] = "byoa_fallback"
                return result
            raise

    @classmethod
    def _resolve_global_pool(cls, tenant: dict, message_type: str) -> Dict[str, Any]:
        """Usa el pool de credenciales compartidas de FluxAgent."""
        preferred = cls._select_channel(tenant, message_type)

        if cls._has_quota(tenant, preferred):
            channel = preferred
        elif tenant.get("auto_fallback_enabled", True):
            alt = EVOLUTION_API if preferred == CLOUD_API else CLOUD_API
            if cls._has_quota(tenant, alt):
                logger.info(
                    "Tenant %s: sin cuota en %s, usando canal alternativo %s",
                    tenant.get("id"), preferred, alt
                )
                channel = alt
            else:
                raise QuotaExhaustedError(
                    f"Sin cuota disponible. "
                    f"cloud_api={cls._remaining(tenant, CLOUD_API)}, "
                    f"evolution_api={cls._remaining(tenant, EVOLUTION_API)}"
                )
        else:
            raise QuotaExhaustedError(f"Sin cuota para {preferred}")

        if channel == CLOUD_API:
            access_token     = getattr(config, "whatsapp_access_token", "")
            phone_number_id  = getattr(config, "whatsapp_phone_number_id", "")
            if not access_token or not phone_number_id:
                raise ChannelUnavailableError(
                    "WHATSAPP_ACCESS_TOKEN o WHATSAPP_PHONE_NUMBER_ID no configurados en .env"
                )
            return {
                "channel": CLOUD_API,
                "credentials": {
                    "access_token": access_token,
                    "phone_number_id": phone_number_id,
                },
                "quota_source": GLOBAL_POOL,
                "cost_estimate": cls._estimate_cost(message_type),
            }

        # Evolution API global
        return {
            "channel": EVOLUTION_API,
            "credentials": {
                "base_url": getattr(config, "evolution_api_url", ""),
                "api_key":  getattr(config, "evolution_api_key", ""),
            },
            "quota_source": GLOBAL_POOL,
            "cost_estimate": {"meta_cost": 0, "markup": 0},
        }

    # ------------------------------------------------------------------
    # Helpers estáticos
    # ------------------------------------------------------------------

    @staticmethod
    def _select_channel(tenant: dict, message_type: str) -> str:
        if message_type == "marketing":
            return CLOUD_API
        return tenant.get("preferred_channel", EVOLUTION_API)

    @staticmethod
    def _has_quota(tenant: dict, channel: str) -> bool:
        """Devuelve True si hay cuota. -1 en el plan significa ilimitado."""
        plan_quota = tenant.get(f"{channel}_quota", 0)
        if plan_quota == -1:
            return True
        used = tenant.get(f"used_{channel}", 0)
        return (plan_quota - used) > 0

    @staticmethod
    def _remaining(tenant: dict, channel: str) -> int:
        quota = tenant.get(f"{channel}_quota", 0)
        if quota == -1:
            return 999_999
        used = tenant.get(f"used_{channel}", 0)
        return max(0, quota - used)

    @staticmethod
    def _estimate_cost(message_type: str) -> Dict[str, float]:
        """Precios LATAM de WhatsApp Cloud API 2025."""
        pricing = {
            "service":        0.005,
            "utility":        0.008,
            "authentication": 0.006,
            "marketing":      0.035,
        }
        meta_cost = pricing.get(message_type, pricing["service"])
        return {"meta_cost": meta_cost, "markup": round(meta_cost * 0.15, 6)}


# Mantener alias para compatibilidad con código existente
HybridWhatsAppRouter = HybridChannelRouter