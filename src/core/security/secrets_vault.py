import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from core.encryption import EncryptionService

logger = logging.getLogger(__name__)

class SecretReference(BaseModel):
    """
    Referencia a un secreto almacenado.
    Evita pasar credenciales crudas por el sistema.
    """
    credential_id: str
    tenant_id: str
    provider: str
    encrypted_payload: str

class SecretsVault:
    """
    Abstracción inicial de bóveda de secretos (Modo Beta).
    Utiliza el EncryptionService subyacente para encriptar payloads JSON.
    Futuro: Migrar a AWS Secrets Manager, Doppler, o GCP Secret Manager.
    """
    
    @staticmethod
    def store_credentials(tenant_id: str, provider: str, raw_credentials: Dict[str, Any]) -> SecretReference:
        """
        Toma credenciales planas (ej: user/pass de SQL Server), las serializa a JSON,
        y las encripta. Retorna una referencia segura.
        """
        json_payload = json.dumps(raw_credentials)
        
        # En el futuro, la llave de cifrado podría estar combinada con el tenant_id
        # para aislamiento criptográfico por tenant.
        encrypted = EncryptionService.encrypt(json_payload)
        
        # Generar ID de referencia (en modo real se guardaría en DB)
        # Para el Beta, devolvemos la referencia en memoria/objeto.
        import uuid
        credential_id = f"cred_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"[SecretsVault] Credenciales cifradas almacenadas para tenant={tenant_id}, provider={provider}")
        
        return SecretReference(
            credential_id=credential_id,
            tenant_id=tenant_id,
            provider=provider,
            encrypted_payload=encrypted
        )

    @staticmethod
    def retrieve_credentials(secret_ref: SecretReference) -> Dict[str, Any]:
        """
        Recupera y desencripta las credenciales a partir de su referencia.
        """
        try:
            decrypted = EncryptionService.decrypt(secret_ref.encrypted_payload)
            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"[SecretsVault] Fallo al recuperar credencial {secret_ref.credential_id}: {str(e)}")
            raise ValueError(f"No se pudieron descifrar las credenciales del proveedor {secret_ref.provider}")
