"""
main.py — FastAPI microservicio de scraping para consulta unificada de documentos.

Endpoint:
  GET /consultar/{documento}
    - 8 dígitos  → búsqueda por DNI
    - 11 dígitos → búsqueda por RUC

Respuestas de error (con código y detalle):
  200  OK            → dato encontrado
  404  Not Found     → RUC/DNI no existe
  422  Unprocessable → documento inválido (no 8 ni 11 dígitos, no numérico)
  504  Gateway Timeout → el portal de consultas no respondió a tiempo
  502  Bad Gateway   → HTML del portal cambió (ScraperFormatError)
  503  Unavailable   → portal no disponible / sin conectividad
"""

import logging
from contextlib import asynccontextmanager

import requests.exceptions
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from documento_scraper import (
    DocumentNotFoundError,
    ScraperFormatError,
    ScraperTimeoutError,
    ScraperUnavailableError,
    TipoDocumento,
    consultar,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────

class ConsultaResponse(BaseModel):
    tipo_documento: TipoDocumento
    numero_documento: str
    razon_social: str


class ErrorResponse(BaseModel):
    error: str        # código máquina: TIMEOUT, NOT_FOUND, FORMAT_ERROR, etc.
    detail: str       # mensaje legible para logs y debugging
    retryable: bool | None = None


# ──────────────────────────────────────────────
# App
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Scraper de documentos iniciado — listo para consultas")
    yield
    logger.info("Scraper de documentos detenido")


app = FastAPI(
    title="CAM Scraper Documentos",
    description="Microservicio de scraping para consulta unificada de RUC/DNI",
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# Helpers de respuesta
# ──────────────────────────────────────────────

def _error(status: int, error: str, detail: str, retryable: bool | None = None) -> JSONResponse:
    logger.warning("Scraper error [%s] %s: %s", status, error, detail)
    content = {"error": error, "detail": detail}
    if retryable is not None:
        content["retryable"] = retryable
    return JSONResponse(status_code=status, content=content)


# ──────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────

@app.get(
    "/consultar/{documento}",
    response_model=ConsultaResponse,
    responses={
        200: {"description": "Dato encontrado"},
        404: {"model": ErrorResponse, "description": "Documento no encontrado"},
        422: {"model": ErrorResponse, "description": "Documento inválido"},
        502: {"model": ErrorResponse, "description": "Formato HTML del portal cambió"},
        503: {"model": ErrorResponse, "description": "Portal de consultas no disponible"},
        504: {"model": ErrorResponse, "description": "Timeout esperando al portal"},
    },
    summary="Consulta documento por número",
    description=(
        "Detecta automáticamente el tipo: **8 dígitos = DNI**, **11 dígitos = RUC**."
    ),
)
def consultar_documento(documento: str) -> JSONResponse | ConsultaResponse:
    logger.info("Consultando documento: %r", documento)

    if not documento.isdigit():
        return _error(422, "INVALID_FORMAT", f"El documento debe contener solo dígitos: {documento!r}")

    longitud = len(documento)
    if longitud not in (8, 11):
        return _error(
            422,
            "INVALID_LENGTH",
            f"Longitud inválida: {longitud} dígitos. Se esperan 8 (DNI) o 11 (RUC)",
        )

    try:
        result = consultar(documento)
        logger.info(
            "Consulta exitosa: tipo=%s numero=%s razon=%r",
            result.tipo_documento,
            result.numero_documento,
            result.razon_social,
        )
        return ConsultaResponse(
            tipo_documento=result.tipo_documento,
            numero_documento=result.numero_documento,
            razon_social=result.razon_social,
        )

    except DocumentNotFoundError as e:
        return _error(404, "NOT_FOUND", str(e))

    except ScraperTimeoutError as e:
        cause = f" ({e.__cause__})" if e.__cause__ else ""
        return _error(
            504,
            "TIMEOUT",
            f"El portal de consultas no respondió a tiempo{cause}",
            retryable=e.retryable,
        )

    except ScraperFormatError as e:
        cause = f" ({e.__cause__})" if e.__cause__ else ""
        hint = f" [parser_hint={e.parser_hint}]" if e.parser_hint else ""
        return _error(
            502,
            "FORMAT_ERROR",
            f"El HTML del portal cambió — el scraper necesita actualización{cause}{hint}",
            retryable=e.retryable,
        )

    except ScraperUnavailableError as e:
        cause = f" ({e.__cause__})" if e.__cause__ else ""
        return _error(
            503,
            "UNAVAILABLE",
            f"Portal de consultas no disponible{cause}",
            retryable=e.retryable,
        )

    except ValueError as e:
        return _error(422, "INVALID_DOCUMENT", str(e))

    except requests.exceptions.RequestException as e:
        # All requests library errors should have been caught earlier;
        # if we reach here something unexpected happened in the transport layer
        logger.exception("RequestException inesperado consultando %r: %s", documento, e)
        return _error(503, "TRANSPORT_ERROR", f"Error de transporte no clasificado: {type(e).__name__}")

    except Exception as e:
        # Genuinely unexpected: AttributeError, KeyError, OSError, etc.
        # These indicate bugs in the scraping logic, not transient failures
        logger.exception("Error inesperado consultando %r", documento)
        return _error(500, "INTERNAL_ERROR", f"Error inesperado: {type(e).__name__}")


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}
