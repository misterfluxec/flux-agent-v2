from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel

class ProviderCapability(BaseModel):
    """Registry of what an external provider supports"""
    provider_name: str
    supports_media: bool = False
    supports_voice: bool = False
    supports_reactions: bool = False
    supports_templates: bool = False
    supports_status_events: bool = False # Delivered, Read, etc.

class IntegrationAdapter(ABC):
    """Base class for all external integrations (Meta, Shopify, etc.)"""
    
    def __init__(self, capabilities: ProviderCapability):
        self.capabilities = capabilities

    @abstractmethod
    async def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to the external provider"""
        pass
    
    @abstractmethod
    async def receive(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming data from the external provider (webhook)"""
        pass

class ExternalProviderError(Exception):
    """Custom exception for integration failures"""
    def __init__(self, provider: str, message: str, status_code: int = 500):
        self.provider = provider
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")
