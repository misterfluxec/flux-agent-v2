import hashlib
import json
from typing import Dict, Any

def generate_dedup_hash(provider: str, provider_event_id: str, payload: Dict[str, Any]) -> str:
    """
    Generates a unique SHA256 hash for early deduplication (Sprint B.1).
    Ensures that the same event from the same provider is not processed twice.
    """
    # Sort keys for deterministic hashing
    payload_str = json.dumps(payload, sort_keys=True)
    raw_str = f"{provider}:{provider_event_id}:{payload_str}"
    return hashlib.sha256(raw_str.encode()).hexdigest()
