import os
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

LLM_MODE = os.getenv("LLM_MODE", "local")


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        pass
    
    @abstractmethod
    async def generate_streaming(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        pass


class OllamaProvider(LLMProvider):
    """Proveedor local usando Ollama."""
    
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "qwen2.5:3b",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        try:
            async with httpx.AsyncClient(timeout=config.ollama_timeout) as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    },
                    "keep_alive": "5m"
                }
                resp = await client.post(f"{config.ollama_base_url}/api/chat", json=payload)
                resp.raise_for_status()
                return resp.json().get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    async def generate_streaming(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "qwen2.5:3b",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        try:
            async with httpx.AsyncClient(timeout=config.ollama_timeout) as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
                async with client.stream("POST", f"{config.ollama_base_url}/api/chat", json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            data = line.strip()
                            if data.startswith("data:"):
                                data = data[5:].strip()
                            if data:
                                try:
                                    import json
                                    chunk = json.loads(data)
                                    content = chunk.get("message", {}).get("content", "")
                                    if content:
                                        yield content
                                except:
                                    continue
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield ""


class OpenAIProvider(LLMProvider):
    """Proveedor cloud OpenAI (desactivado por defecto)."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no configurado")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                resp = await client.post(
                    f"{self.base_url}/chat/completions", 
                    json=payload, 
                    headers=headers
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise
    
    async def generate_streaming(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no configurado")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                }
                async with client.stream("POST", f"{self.base_url}/chat/completions", json=payload, headers=headers) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            import json
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield ""


class AnthropicProvider(LLMProvider):
    """Proveedor cloud Anthropic Claude (desactivado por defecto)."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "claude-3-haiku-20240307",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurado")
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        system_msg = ""
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content", "")
            else:
                filtered_messages.append(msg)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system_msg,
                    "messages": filtered_messages
                }
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages", 
                    json=payload, 
                    headers=headers
                )
                resp.raise_for_status()
                return resp.json()["content"][0]["text"]
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise
    
    async def generate_streaming(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "claude-3-haiku-20240307",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurado")
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        system_msg = ""
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content", "")
            else:
                filtered_messages.append(msg)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system_msg,
                    "messages": filtered_messages,
                    "stream": True
                }
                async with client.stream("POST", "https://api.anthropic.com/v1/messages", json=payload, headers=headers) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            import json
                            chunk = json.loads(data)
                            if chunk.get("type") == "content_block_delta":
                                content = chunk.get("delta", {}).get("text", "")
                                if content:
                                    yield content
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield ""


class LLMRouter:
    """
    Router que permite switch entre proveedores local y cloud.
    Por defecto usa Ollama local (desactivado cloud).
    """
    
    def __init__(self):
        self.mode = LLM_MODE
        self.providers: Dict[str, LLMProvider] = {
            "local": OllamaProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider()
        }
        logger.info(f"LLMRouter inicializado en modo: {self.mode}")
    
    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """Obtiene el proveedor configurado o el especificado."""
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        
        if self.mode == "cloud":
            default_cloud = os.getenv("DEFAULT_CLOUD_PROVIDER", "openai")
            return self.providers.get(default_cloud, self.providers["local"])
        
        return self.providers["local"]
    
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Genera respuesta usando el proveedor configurado.
        """
        prov = self.get_provider(provider)
        
        if provider:
            effective_model = model or self._get_default_model(provider)
        else:
            effective_model = model or config.ollama_modelo_chat
        
        return await prov.generate(messages, effective_model, temperature, max_tokens)
    
    async def generate_streaming(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """Genera respuesta en streaming."""
        prov = self.get_provider(provider)
        
        if provider:
            effective_model = model or self._get_default_model(provider)
        else:
            effective_model = model or config.ollama_modelo_chat
        
        async for chunk in prov.generate_streaming(messages, effective_model, temperature, max_tokens):
            yield chunk
    
    def _get_default_model(self, provider: str) -> str:
        """Retorna el modelo por defecto para cada provider."""
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-haiku-20240307",
            "local": config.ollama_modelo_chat
        }
        return defaults.get(provider, "qwen2.5:3b")
    
    def is_cloud_enabled(self) -> bool:
        """Verifica si el modo cloud está habilitado."""
        return self.mode == "cloud"
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Retorna proveedores disponibles y su estado."""
        return {
            "local": True,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY"))
        }


llm_router = LLMRouter()