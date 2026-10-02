"""
documento_scraper.py — Lógica de scraping para consulta unificada de RUC (11 dígitos) y DNI (8 dígitos).

Flujo:
  1. GET /FrameCriterioBusquedaWeb.jsp  → obtiene sesión/cookie
  2. POST /jcrS00Alias                  → scraping y parsing HTML

Manejo de errores:
  - ScraperTimeoutError     → El portal no respondió a tiempo
  - ScraperUnavailableError → El portal no responde / error de red
  - ScraperFormatError      → Formato HTML del portal cambió
  - DocumentNotFoundError   → Documento no encontrado
"""

import random
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

TIMEOUT_CONNECT = 10   # segundos para conectar
TIMEOUT_READ = 120     # segundos para leer respuesta


class TipoDocumento(str, Enum):
    RUC = "RUC"
    DNI = "DNI"


@dataclass
class ConsultaResult:
    tipo_documento: TipoDocumento
    numero_documento: str
    razon_social: str


# ──────────────────────────────────────────────
# Excepciones tipadas
# ──────────────────────────────────────────────

@dataclass
class ScraperError(Exception):
    """Base para todas las excepciones del scraper."""
    documento: str | None = None
    original_error: BaseException | None = None
    timestamp: str = ""
    retryable: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class ScraperTimeoutError(ScraperError):
    """El portal no respondió dentro del timeout configurado."""
    timeout_type: str = "read"
    retryable: bool = True


@dataclass
class ScraperUnavailableError(ScraperError):
    """Error de red o portal no disponible."""
    reason: str = ""
    retryable: bool = True


@dataclass
class ScraperFormatError(ScraperError):
    """El HTML del portal cambió — la estructura esperada no existe."""
    parser_hint: str = ""
    retryable: bool = False


class DocumentNotFoundError(ScraperError):
    """El documento no existe en el registro del portal."""
    tipo: TipoDocumento | None = None
    retryable: bool = False

    def __init__(self, documento: str, tipo: TipoDocumento):
        self.documento = documento
        self.tipo = tipo
        self.retryable = False
        super().__init__(documento=documento)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _generate_token(length: int = 52) -> str:
    """Genera token aleatorio para el formulario."""
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(chars) for _ in range(length))


def _create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-PE,es;q=0.9",
    })
    return session


def _init_session(session: requests.Session) -> None:
    try:
        logger.debug("GET init page...")
        session.get(
            f"{BASE_URL}/FrameCriterioBusquedaWeb.jsp",
            timeout=(TIMEOUT_CONNECT, TIMEOUT_READ),
        )
    except requests.exceptions.ConnectTimeout as e:
        logger.exception("ConnectTimeout initiating session")
        raise ScraperUnavailableError(
            reason="connect_timeout",
            original_error=e,
        ) from e
    except requests.exceptions.ReadTimeout as e:
        logger.exception("ReadTimeout initiating session")
        raise ScraperTimeoutError(
            timeout_type="read",
            original_error=e,
        ) from e
    except requests.exceptions.ConnectionError as e:
        logger.exception("ConnectionError initiating session")
        raise ScraperUnavailableError(
            reason="connection_error",
            original_error=e,
        ) from e


def _post_query(session: requests.Session, data: dict) -> BeautifulSoup:
    try:
        logger.debug("POST query: accion=%s", data.get("accion"))
        response = session.post(
            f"{BASE_URL}/jcrS00Alias",
            data=data,
            headers={"Referer": f"{BASE_URL}/FrameCriterioBusquedaWeb.jsp"},
            timeout=(TIMEOUT_CONNECT, TIMEOUT_READ),
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.exceptions.ReadTimeout as e:
        logger.exception("ReadTimeout during POST query")
        raise ScraperTimeoutError(
            timeout_type="read",
            original_error=e,
        ) from e
    except requests.exceptions.ConnectionError as e:
        logger.exception("ConnectionError during POST query")
        raise ScraperUnavailableError(
            reason="connection_error",
            original_error=e,
        ) from e
    except requests.exceptions.HTTPError as e:
        logger.exception("HTTPError during POST query: %s", e.response.status_code)
        raise ScraperUnavailableError(
            reason="http_error",
            original_error=e,
        ) from e


def _check_server_error(soup: BeautifulSoup) -> None:
    title = soup.find("title")
    if title and "Pagina de Error" in title.get_text():
        logger.exception("Portal returned error page")
        raise ScraperUnavailableError(
            reason="server_error_page",
        )


# Señales que SUNAT usa cuando el documento NO existe en su registro.
# Caso típico DNI inexistente: "El Sistema RUC NO REGISTRA un número de RUC para el DNI número X"
NOT_FOUND_SIGNALS = (
    "no es válido",
    "no es valido",
    "no se encontr",
    "no existe",
    "no registra",   # "NO REGISTRA un número de RUC..." ← caso SUNAT para DNI sin RUC asociado
)


def _check_not_found(soup: BeautifulSoup, documento: str, tipo: TipoDocumento) -> None:
    """Lanza DocumentNotFoundError si el HTML contiene señales de 'no encontrado'."""
    page_text = soup.get_text().lower()
    if any(sig in page_text for sig in NOT_FOUND_SIGNALS):
        raise DocumentNotFoundError(documento, tipo)


def _parse_ruc(soup: BeautifulSoup, ruc: str) -> ConsultaResult:
    _check_server_error(soup)
    _check_not_found(soup, ruc, TipoDocumento.RUC)

    for h4 in soup.find_all("h4"):
        text = h4.get_text(strip=True)
        if " - " in text and len(text) > 15:
            parts = text.split(" - ", 1)
            numero = parts[0].strip()
            razon = parts[1].strip()
            if numero.isdigit() and len(numero) == 11:
                return ConsultaResult(
                    tipo_documento=TipoDocumento.RUC,
                    numero_documento=numero,
                    razon_social=razon,
                )

    items = soup.find_all("div", class_="list-group-item")
    if not items:
        logger.exception("ScraperFormatError parsing RUC %s: list-group-item divs not found", ruc)
        raise ScraperFormatError(
            parser_hint="list-group-item divs for RUC",
            documento=ruc,
        )

    result_data: dict = {}
    for item in items:
        cols = item.find_all("div", class_=lambda c: c and "col-sm" in c)
        if len(cols) >= 2:
            label = " ".join(cols[0].get_text(" ", strip=True).split()).rstrip(":")
            value = " ".join(cols[1].get_text(" ", strip=True).split())
            result_data[label] = value

    razon_social_field = result_data.get("Número de RUC", "")
    razon_social = ""
    if razon_social_field and " - " in razon_social_field:
        razon_social = razon_social_field.split(" - ", 1)[1].strip()

    if not razon_social:
        tipo_doc_field = result_data.get("Tipo de Documento", "")
        if tipo_doc_field and " - " in tipo_doc_field:
            parts = tipo_doc_field.split(" - ", 1)
            candidate = parts[1].strip()
            if candidate and not candidate.upper().startswith("DNI"):
                razon_social = candidate

    if not razon_social:
        logger.exception("ScraperFormatError parsing RUC %s: razon social field not found", ruc)
        raise ScraperFormatError(
            parser_hint="razon social field for RUC",
            documento=ruc,
        )

    return ConsultaResult(
        tipo_documento=TipoDocumento.RUC,
        numero_documento=ruc,
        razon_social=razon_social,
    )


def _parse_dni(soup: BeautifulSoup, dni: str) -> ConsultaResult:
    _check_server_error(soup)
    _check_not_found(soup, dni, TipoDocumento.DNI)

    first_result = soup.find("a", class_="aRucs")
    if not first_result:
        list_group = soup.find("div", class_="list-group")
        if list_group is not None:
            raise DocumentNotFoundError(dni, TipoDocumento.DNI)
        logger.exception("ScraperFormatError parsing DNI %s: aRucs anchor not found", dni)
        raise ScraperFormatError(
            parser_hint="aRucs anchor or list-group for DNI",
            documento=dni,
        )

    headings = first_result.find_all("h4")
    nombre = ""
    for h4 in headings:
        raw_text = h4.get_text(" ", strip=True)
        normalized = " ".join(raw_text.split())
        if not normalized:
            continue
        if normalized.startswith("RUC:"):
            continue
        if normalized.startswith("DNI"):
            if " - " in normalized:
                nombre = normalized.split(" - ", 1)[1].strip()
            else:
                nombre = normalized[len("DNI"):].lstrip(" :\t-").strip()
            break
        nombre = normalized
        break

    if not nombre:
        logger.exception("ScraperFormatError parsing DNI %s: h4 nombre not found inside aRucs", dni)
        raise ScraperFormatError(
            parser_hint="h4 nombre inside aRucs for DNI",
            documento=dni,
        )

    return ConsultaResult(
        tipo_documento=TipoDocumento.DNI,
        numero_documento=dni,
        razon_social=nombre,
    )


def _extract_nombre_con_coma_desde_ruc_detail(soup: BeautifulSoup, dni: str) -> str:
    """
    Extrae el nombre separado por comas desde el HTML del detalle de RUC.

    El campo "Tipo de Documento" tiene el formato:
        "DNI 74827847 - CALLIRGOS OROZCO, PIERO ALDAIR"
              ↑     ↑   ↑                     ↑
              │     │   └── NOMBRES
              │     └────── APELLIDO_PATERNO APELLIDO_MATERNO
              └──────────── número de documento

    Devuelve SOLO el nombre: "CALLIRGOS OROZCO, PIERO ALDAIR"
    """
    items = soup.find_all("div", class_="list-group-item")
    for item in items:
        cols = item.find_all("div", class_=lambda c: c and "col-sm" in c)
        if len(cols) < 2:
            continue
        label = " ".join(cols[0].get_text(" ", strip=True).split()).rstrip(":")
        if label != "Tipo de Documento":
            continue
        value = " ".join(cols[1].get_text(" ", strip=True).split())
        if " - " not in value:
            continue
        nombre = value.split(" - ", 1)[1].strip()
        if "," in nombre:
            return nombre

    logger.warning(
        "No se encontró nombre separado por comas en el detalle RUC para DNI %s",
        dni,
    )
    raise ScraperFormatError(
        parser_hint="Tipo de Documento con nombre separado por comas",
        documento=dni,
    )


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def consultar(documento: str) -> ConsultaResult:
    """
    Consulta por número de documento (8 dígitos = DNI, 11 dígitos = RUC).
    """
    if not documento.isdigit():
        raise ValueError(f"El documento debe ser numérico: {documento!r}")

    longitud = len(documento)
    if longitud == 11:
        return _consultar_ruc(documento)
    elif longitud == 8:
        return _consultar_dni(documento)
    else:
        raise ValueError(
            f"Documento inválido: {longitud} dígitos. Se esperan 8 (DNI) o 11 (RUC)"
        )


def _consultar_ruc(ruc: str) -> ConsultaResult:
    session = _create_session()
    _init_session(session)

    data = {
        "accion": "consPorRuc",
        "razSoc": "",
        "nroRuc": ruc,
        "nrodoc": "",
        "token": _generate_token(),
        "contexto": "ti-it",
        "modo": "1",
        "rbtnTipo": "1",
        "search1": ruc,
        "tipdoc": "",
        "search2": "",
        "search3": "",
        "codigo": "",
    }
    soup = _post_query(session, data)
    return _parse_ruc(soup, ruc)


def _consultar_dni(dni: str) -> ConsultaResult:
    """
    Consulta por DNI con flujo "click" + fallback.

    Flujo principal (nombre con coma, separado):
      1) POST consPorTipdoc   → HTML con <a class="aRucs" data-ruc="...">
      2) Extraer data-ruc     → RUC del primer resultado (simula el "click")
      3) POST consPorRuc      → HTML del detalle del RUC
      4) Parsear campo "Tipo de Documento" → nombre con coma
         Ej: "DNI 74827847 - CALLIRGOS OROZCO, PIERO ALDAIR"
             → "CALLIRGOS OROZCO, PIERO ALDAIR"

    Fallback (si el portal no responde o el HTML cambió):
      - Cualquier excepción del paso 2, 3 o 4 → parsear el h4 del
        resultado DNI original (comportamiento histórico, nombre
        concatenado sin coma).
    """
    session = _create_session()
    _init_session(session)

    # ── Paso 1: búsqueda por DNI (siempre se hace) ──
    data_dni = {
        "accion": "consPorTipdoc",
        "razSoc": "",
        "nroRuc": "",
        "nrodoc": dni,
        "token": _generate_token(),
        "contexto": "ti-it",
        "modo": "1",
        "rbtnTipo": "2",
        "search1": "",
        "tipdoc": "1",   # 1 = DNI
        "search2": dni,
        "search3": "",
        "codigo": "",
    }
    soup_dni = _post_query(session, data_dni)

    # ── Intentar el flujo "click" → RUC detail → nombre con coma ──
    try:
        # Paso 2: extraer RUC del primer resultado
        ruc = _extract_ruc_from_dni_result(soup_dni, dni)

        # Paso 3: POST consPorRuc con ese RUC
        data_ruc = {
            "accion": "consPorRuc",
            "razSoc": "",
            "nroRuc": ruc,
            "nrodoc": "",
            "token": _generate_token(),
            "contexto": "ti-it",
            "modo": "1",
            "rbtnTipo": "1",
            "search1": ruc,
            "tipdoc": "",
            "search2": "",
            "search3": "",
            "codigo": "",
        }
        soup_ruc = _post_query(session, data_ruc)

        # Paso 4: nombre con coma desde el detalle
        nombre = _extract_nombre_con_coma_desde_ruc_detail(soup_ruc, dni)

        logger.info(
            "DNI %s: nombre con coma extraído vía RUC detail (%s)",
            dni,
            nombre,
        )
        return ConsultaResult(
            tipo_documento=TipoDocumento.DNI,
            numero_documento=dni,
            razon_social=nombre,
        )

    except (
        ScraperFormatError,
        ScraperUnavailableError,
        ScraperTimeoutError,
        requests.exceptions.RequestException,
    ) as exc:
        # Fallback: la página de detalle no respondió, cambió el HTML,
        # o el portal no está disponible. Usamos el comportamiento
        # histórico: parsear el h4 del resultado DNI (nombre concatenado).
        logger.warning(
            "DNI %s: fallback al parser histórico (%s: %s)",
            dni,
            type(exc).__name__,
            exc,
        )
        return _parse_dni(soup_dni, dni)


def _extract_ruc_from_dni_result(soup: BeautifulSoup, dni: str) -> str:
    """Extrae el data-ruc del primer <a class="aRucs"> del HTML de búsqueda DNI."""
    _check_not_found(soup, dni, TipoDocumento.DNI)

    first_result = soup.find("a", class_="aRucs")
    if not first_result:
        list_group = soup.find("div", class_="list-group")
        if list_group is not None:
            raise DocumentNotFoundError(dni, TipoDocumento.DNI)
        raise ScraperFormatError(
            parser_hint="aRucs anchor or list-group for DNI",
            documento=dni,
        )

    ruc = first_result.get("data-ruc")
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        raise ScraperFormatError(
            parser_hint="data-ruc attribute on aRucs for DNI",
            documento=dni,
        )

    return ruc