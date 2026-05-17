# =============================================================================
# FLUXAGENT V2 — GESTOR DE ARCHIVOS DE INGESTA
# =============================================================================
# Encapsula la persistencia física, validación de tipos y limpieza.
# =============================================================================

import os
import shutil
import aiofiles
import logging
from uuid import UUID, uuid4
from fastapi import UploadFile

logger = logging.getLogger(__name__)

class FileHandler:
    """
    Gestiona el ciclo de vida de los archivos subidos para ingesta.
    Aísla al resto del sistema de la gestión de rutas y disco.
    """
    
    def __init__(self, base_path: str = "uploads/knowledge"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def save_upload(self, upload_file: UploadFile, tenant_id: UUID) -> str:
        """
        Guarda un archivo subido en una ruta segura y aislada por tenant.
        Retorna la ruta absoluta del archivo guardado.
        """
        tenant_dir = os.path.join(self.base_path, str(tenant_id))
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Nombre de archivo seguro: uuid + extensión original
        ext = os.path.splitext(upload_file.filename)[1]
        file_name = f"{uuid4()}{ext}"
        dest_path = os.path.join(tenant_dir, file_name)
        
        async with aiofiles.open(dest_path, "wb") as out_file:
            while content := await upload_file.read(1024 * 1024): # 1MB chunks
                await out_file.write(content)
        
        logger.info(f"Archivo guardado: {dest_path} (Tenant: {tenant_id})")
        return os.path.abspath(dest_path)

    def cleanup(self, file_path: str):
        """Elimina un archivo procesado si existe."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Archivo eliminado tras proceso: {file_path}")
        except Exception as e:
            logger.warning(f"No se pudo eliminar el archivo {file_path}: {e}")

    def get_mime_type(self, file_path: str) -> str:
        """Determina el type de archivo (placeholder para validaciones futuras)."""
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".pdf": "application/pdf",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv": "text/csv",
            ".txt": "text/plain"
        }
        return mapping.get(ext, "application/octet-stream")
