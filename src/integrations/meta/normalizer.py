import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Tuple
from uuid import UUID
from integrations.canonical import CanonicalMessage, CanonicalEnvelope
from integrations.base import IntegrationAdapter, ProviderCapability
from integrations.idempotency_utils import generate_dedup_hash

class MetaNormalizer:
    """
    Pure translator for Meta (WhatsApp Cloud API) payloads.
    No domain logic here. Only structural mapping.
    """
    
    @staticmethod
    def to_canonical(raw_payload: Dict[str, Any]) -> CanonicalMessage:
        try:
            entry = raw_payload.get("entry", [{}])[0]
            change = entry.get("changes", [{}])[0]
            value = change.get("value", {})
            message = value.get("messages", [{}])[0]
            
            msg_type = message.get("type", "text")
            content = ""
            if msg_type == "text":
                content = message.get("text", {}).get("body", "")
            elif msg_type == "button":
                content = message.get("button", {}).get("text", "")
            elif msg_type == "interactive":
                content = message.get("interactive", {}).get("button_reply", {}).get("title", "")
            
            return CanonicalMessage(
                external_id=message.get("id"),
                channel="whatsapp",
                sender_id=message.get("from"),
                content=content,
                timestamp=float(message.get("timestamp", datetime.utcnow().timestamp())),
                metadata={
                    "display_phone_number": value.get("metadata", {}).get("display_phone_number"),
                    "contacts": value.get("contacts", []),
                    "type": msg_type
                }
            )
        except (IndexError, KeyError) as e:
            raise ValueError(f"Invalid Meta payload structure: {e}")

class MetaAdapter(IntegrationAdapter):
    def __init__(self):
        super().__init__(ProviderCapability(
            provider_name="meta",
            supports_media=True,
            supports_voice=True,
            supports_reactions=True,
            supports_templates=True,
            supports_status_events=True
        ))
        self.normalizer = MetaNormalizer()

    async def wrap_envelope(self, raw_data: Dict[str, Any], tenant_id: UUID, correlation_id: str, raw_id: str) -> CanonicalEnvelope:
        """Creates the Fortress Envelope for a Meta payload"""
        # Extract provider ID for dedup
        try:
            entry = raw_data.get("entry", [{}])[0]
            change = entry.get("changes", [{}])[0]
            value = change.get("value", {})
            message = value.get("messages", [{}])[0]
            provider_event_id = message.get("id", "unknown")
        except Exception:
            provider_event_id = "error_extracting_id"

        return CanonicalEnvelope(
            provider="meta",
            provider_event_id=provider_event_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            received_at=datetime.utcnow().timestamp(),
            country_code="EC", # Should be resolved from tenant config in real flow
            raw_reference_id=raw_id,
            dedup_hash=generate_dedup_hash("meta", provider_event_id, raw_data)
        )

    async def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
