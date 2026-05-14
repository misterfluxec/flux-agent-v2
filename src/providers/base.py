from abc import ABC, abstractmethod
from typing import Dict, Any

class ChannelProvider(ABC):
    """
    Contrato estricto para proveedores operacionales (Evolution, Telegram, Meta).
    Garantiza la consistencia en el ciclo de vida de la conexión y observabilidad.
    """

    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inicializa o solicita conexión (ej. genera QR o valida token).
        Debe retornar datos de conexión (ej. qr_code, session_id).
        """
        pass

    @abstractmethod
    async def disconnect(self, session_id: str) -> bool:
        """
        Cierra la sesión y libera recursos en el proveedor.
        """
        pass

    @abstractmethod
    async def health_check(self, session_id: str) -> Dict[str, Any]:
        """
        Realiza un ping o valida el estado de la conexión.
        Debe lanzar excepciones o devolver payload de estado.
        """
        pass

    @abstractmethod
    async def send_message(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un mensaje usando la infraestructura subyacente.
        Debe soportar retries o lanzar errores mapeados para la DLQ.
        """
        pass

    @abstractmethod
    async def validate_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Verifica firmas, secretos, o tokens en eventos entrantes.
        """
        pass

    @abstractmethod
    async def refresh_session(self, session_id: str) -> bool:
        """
        Renueva tokens o reactiva sesiones degradadas.
        """
        pass
