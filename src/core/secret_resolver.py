import os
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class SecretProvider(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        pass

class EnvSecretProvider(SecretProvider):
    def get_secret(self, key: str) -> Optional[str]:
        return os.getenv(key)

class SecretResolver:
    """
    Enterprise Secret Lifecycle Management with Memory Cache & TTL.
    """
    def __init__(self, primary_provider: Optional[SecretProvider] = None, ttl: int = 300):
        self.provider = primary_provider or EnvSecretProvider()
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def resolve(self, key: str, default: Optional[str] = None) -> Optional[str]:
        # 1. Check Cache
        now = time.time()
        if key in self._cache:
            entry = self._cache[key]
            if now - entry["timestamp"] < self.ttl:
                return entry["value"]

        # 2. Resolve from Provider
        try:
            secret = self.provider.get_secret(key)
            if secret is not None:
                self._cache[key] = {"value": secret, "timestamp": now}
                return secret
            return default
        except Exception as e:
            # Fallback to ENV (controlled)
            print(f"Warning: Secret provider failed for {key}: {e}")
            return os.getenv(key, default)

    def invalidate_cache(self, key: Optional[str] = None):
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

# Global Instance
secrets = SecretResolver()
