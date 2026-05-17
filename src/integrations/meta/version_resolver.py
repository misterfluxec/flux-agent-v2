from typing import Dict, Any, Optional
from integrations.quarantine import QuarantineReason

class MetaVersionResolver:
    """
    Decides which MetaNormalizer version to use.
    v2.5: Implements Fallback to Quarantine for unknown versions.
    """
    
    @staticmethod
    def resolve_version(raw_payload: Dict[str, Any]) -> str:
        # Simplified logic
        metadata = raw_payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {})
        version = metadata.get("version", "v16")
        return version

    @staticmethod
    def get_normalizer(version: str):
        if version == "v16":
            from integrations.meta.normalizer import MetaNormalizer
            return MetaNormalizer
        
        # Fallback Policy: Return None to trigger Quarantine
        return None

    @staticmethod
    def handle_unknown_version(version: str, raw_payload: Dict[str, Any]):
        """Logic to move to Quarantine when version is unknown"""
        return {
            "reason_code": QuarantineReason.UNKNOWN_VERSION,
            "reason_detail": f"Meta API version {version} not supported by any normalizer."
        }
