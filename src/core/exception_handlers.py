import logging
import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.exceptions import FluxError
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

def setup_exception_handlers(app):
    @app.exception_handler(FluxError)
    async def flux_error_handler(request: Request, exc: FluxError):
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_problem(path=str(request.url.path)),
            headers={"Content-Type": "application/problem+json"},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP {exc.status_code} en {request.url}: {exc.detail}")
        error_messages = {
            400: "Solicitud inválida",
            401: "No autorizado",
            403: "Acceso denegado",
            404: "Recurso no encontrado",
            405: "Método no permitido",
            429: "Demasiadas solicitudes"
        }
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "codigo": exc.status_code,
                "mensaje": error_messages.get(exc.status_code, exc.detail),
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validación fallida en {request.url}: {exc.errors()}")
        formatted_errors = []
        for error in exc.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            formatted_errors.append({
                "campo": field,
                "mensaje": error["msg"],
                "valor": error.get("input")
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validacion_fallida",
                "mensaje": "Datos de entrada inválidos",
                "detalles": formatted_errors,
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        )

    @app.exception_handler(IntegrityError)
    async def db_integrity_handler(request: Request, exc: IntegrityError):
        logger.error(f"Error de integridad DB: {exc.orig}")
        error_msg = str(exc.orig).lower()
        if "unique" in error_msg:
            detalle = "El recurso ya existe"
            codigo = "recurso_duplicado"
        elif "foreign key" in error_msg:
            detalle = "Referencia inválida a otro recurso"
            codigo = "referencia_invalida"
        elif "not null" in error_msg:
            detalle = "Campo requerido faltante"
            codigo = "campo_requerido"
        else:
            detalle = "Conflicto de datos"
            codigo = "conflicto_datos"
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": codigo,
                "mensaje": detalle,
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        )

    @app.exception_handler(DBAPIError)
    async def db_error_handler(request: Request, exc: DBAPIError):
        logger.error(f"Error de base de datos: {exc.orig}", exc_info=True)
        if config.es_desarrollo:
            detalle = str(exc.orig)
        else:
            detalle = "Error en el servicio de base de datos"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "error_db",
                "mensaje": detalle,
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.critical(
            f"ERROR NO MANEJADO en {request.method} {request.url}: "
            f"{type(exc).__name__}: {exc}",
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "error_interno",
                "mensaje": "Ocurrió un error inesperado",
                "path": str(request.url.path),
                "timestamp": time.time(),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
