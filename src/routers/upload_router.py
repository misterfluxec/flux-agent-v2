from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import pandas as pd
import io
import logging
from database import obtener_sesion
from auth import get_tenant_actual

router = APIRouter(prefix="/api/v1/upload", tags=["Carga de Archivos"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "txt", "pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("/parse")
async def parse_file_upload(
    file: UploadFile = File(...),
    db = Depends(obtener_sesion),
    current_tenant = Depends(get_tenant_actual)
):
    """
    Recibe archivos locales, valida estructura, extrae headers y retorna preview.
    Soporta CSV, Excel y TXT.
    """
    # 1. Validaciones básicas
    filename = file.filename if file.filename else "archivo_sin_nombre"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Formato '{ext}' no soportado. Usa CSV, Excel, TXT o PDF.")
    
    # Nota: file.size puede ser None en algunos clientes, pero FastAPI suele poblarlo
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(400, f"Archivo muy grande. Máximo {MAX_FILE_SIZE // 1024 // 1024}MB.")

    try:
        content = await file.read()
        headers, preview_rows = [], []

        # 2. Extracción según tipo
        if ext in ["csv", "xlsx", "xls"]:
            if ext == "csv":
                # Intentar detectar separador si falla el default
                try:
                    df = pd.read_csv(io.BytesIO(content), sep=",", nrows=10)
                except:
                    df = pd.read_csv(io.BytesIO(content), sep=";", nrows=10)
            else:
                df = pd.read_excel(io.BytesIO(content), nrows=10)
            
            df = df.dropna(how="all")
            headers = [str(col).strip() for col in df.columns]
            # Convertir a tipos serializables JSON
            preview_rows = df.head(5).replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
            
        elif ext == "txt":
            lines = content.decode("utf-8", errors="ignore").splitlines()
            if lines and lines[0].strip():
                # Asumimos tabulación o comas
                first_line = lines[0]
                sep = "\t" if "\t" in first_line else ","
                headers = [h.strip() for h in first_line.split(sep) if h.strip()]
                
                for line in lines[1:6]:
                    if line.strip():
                        values = line.split(sep)
                        preview_rows.append(dict(zip(headers, [v.strip() for v in values])))
                
        elif ext == "pdf":
            # PDFs se procesan en background por peso. Preview inicial limitado.
            headers = ["contenido_extraido"]
            preview_rows = [{"contenido_extraido": "PDF detectado. El procesamiento de texto se realizará durante la sincronización final."}]

        if not headers and ext != "pdf":
            raise HTTPException(400, "No se detectaron columnas. Asegúrate de que la primera fila contenga los encabezados.")

        return {
            "success": True,
            "headers": headers,
            "preview_rows": preview_rows,
            "file_name": filename,
            "rows_detected_preview": len(preview_rows)
        }

    except Exception as e:
        logger.error(f"Error parsing file {filename}: {e}", exc_info=True)
        raise HTTPException(500, f"Error al procesar el archivo: {str(e)}")
