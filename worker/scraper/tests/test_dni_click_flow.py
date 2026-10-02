"""
test_dni_click_flow.py — Test del flujo DNI → click RUC → nombre separado por comas.

Validado con datos REALES del portal SUNAT:
  - Campo "Tipo de Documento" trae: "DNI 74827847 - CALLIRGOS OROZCO, PIERO ALDAIR"
  - La coma separa apellidos de nombres.

Lo que verifica:
  - _consultar_dni hace 2 POST (DNI search + RUC detail) en el happy path
  - El RUC de la 2da POST es el data-ruc del 1er resultado
  - El nombre retornado contiene "," (separado por comas)
  - Si la 2da POST falla por timeout/portal caído → FALLBACK al parser histórico
  - Si el HTML del detalle cambió → FALLBACK al parser histórico
"""

import pytest
from unittest.mock import patch, PropertyMock
from bs4 import BeautifulSoup

from documento_scraper import (
    consultar,
    TipoDocumento,
    DocumentNotFoundError,
    ScraperFormatError,
    ScraperUnavailableError,
    ScraperTimeoutError,
)


# ──────────────────────────────────────────────
# HTML fixtures (basados en captura real de SUNAT)
# ──────────────────────────────────────────────

DNI_SEARCH_HTML = """
<html><body>
<div class="list-group">
  <a href="#" class="list-group-item clearfix aRucs" data-ruc="10748278473">
    <h4 class="list-group-item-heading">RUC: 10748278473</h4>
    <h4 class="list-group-item-heading">CALLIRGOS OROZCO PIERO ALDAIR</h4>
    <p class="list-group-item-text">Ubicación: TRUJILLO</p>
    <p class="list-group-item-text">Estado: <strong><span class="text-success">ACTIVO</span></strong></p>
  </a>
</div>
</body></html>
"""

RUC_DETAIL_HTML = """
<html><body>
<div class="list-group">
  <div class="list-group-item">
    <div class="row">
      <div class="col-sm-5">Número de RUC</div>
      <div class="col-sm-7">10748278473 - CALLIRGOS OROZCO PIERO ALDAIR</div>
    </div>
  </div>
  <div class="list-group-item">
    <div class="row">
      <div class="col-sm-5">Tipo Contribuyente</div>
      <div class="col-sm-7">PERSONA NATURAL SIN NEGOCIO</div>
    </div>
  </div>
  <div class="list-group-item">
    <div class="row">
      <div class="col-sm-5">Tipo de Documento</div>
      <div class="col-sm-7">DNI 74827847 - CALLIRGOS OROZCO, PIERO ALDAIR</div>
    </div>
  </div>
  <div class="list-group-item">
    <div class="row">
      <div class="col-sm-5">Estado del Contribuyente</div>
      <div class="col-sm-7">ACTIVO</div>
    </div>
  </div>
</div>
</body></html>
"""

RUC_DETAIL_HTML_BROKEN = """
<html><body>
<div class="list-group">
  <div class="list-group-item">
    <div class="row">
      <div class="col-sm-5">Tipo de Documento</div>
      <div class="col-sm-7">DNI 74827847 - CALLIRGOS OROZCO PIERO ALDAIR</div>
    </div>
  </div>
</div>
</body></html>
"""

RUC_DETAIL_HTML_SIN_COMA = """
<html><body>
<div class="list-group">
  <div class="list-group-item">
    <div class="row">
      <div class="col-sm-5">Tipo de Documento</div>
      <div class="col-sm-7">DNI 74827847 - CALLIRGOS OROZCO PIERO ALDAIR</div>
    </div>
  </div>
</div>
</body></html>
"""


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


# ──────────────────────────────────────────────
# 1. Happy path: DNI → click → nombre con coma
# ──────────────────────────────────────────────

def test_dni_click_flow_realiza_dos_requests():
    """Happy path: el flujo DNI hace 2 POST (DNI search + RUC detail)."""
    dni_soup = _soup(DNI_SEARCH_HTML)
    ruc_soup = _soup(RUC_DETAIL_HTML)

    with patch("documento_scraper._post_query") as mock_post:
        mock_post.side_effect = [dni_soup, ruc_soup]

        result = consultar("74827847")

        assert mock_post.call_count == 2


def test_dni_click_flow_segunda_request_usa_consPorRuc_con_data_ruc():
    """La 2da POST debe usar consPorRuc con el RUC del data-ruc."""
    dni_soup = _soup(DNI_SEARCH_HTML)
    ruc_soup = _soup(RUC_DETAIL_HTML)

    with patch("documento_scraper._post_query") as mock_post:
        mock_post.side_effect = [dni_soup, ruc_soup]

        consultar("74827847")

        segunda = mock_post.call_args_list[1]
        data = segunda.kwargs.get("data") or segunda.args[1]
        assert data.get("accion") == "consPorRuc"
        assert data.get("nroRuc") == "10748278473"


def test_dni_click_flow_retorna_nombre_con_coma():
    """El nombre retornado debe tener coma separando apellidos de nombres."""
    dni_soup = _soup(DNI_SEARCH_HTML)
    ruc_soup = _soup(RUC_DETAIL_HTML)

    with patch("documento_scraper._post_query") as mock_post:
        mock_post.side_effect = [dni_soup, ruc_soup]

        result = consultar("74827847")

        assert result.tipo_documento == TipoDocumento.DNI
        assert result.numero_documento == "74827847"
        assert "," in result.razon_social
        assert result.razon_social == "CALLIRGOS OROZCO, PIERO ALDAIR"


# ──────────────────────────────────────────────
# 2. Fallback: si la 2da POST falla, volver al parser histórico
# ──────────────────────────────────────────────

def test_fallback_si_ruc_detail_cae_unavailable():
    """Si la 2da POST falla por portal caído, fallback al nombre concatenado."""
    dni_soup = _soup(DNI_SEARCH_HTML)

    with patch("documento_scraper._post_query") as mock_post:
        # 1ra OK, 2da lanza Unavailable
        from requests.exceptions import ConnectionError
        mock_post.side_effect = [dni_soup, ConnectionError("portal caído")]

        result = consultar("74827847")

        # FALLBACK: nombre concatenado del h4 (sin coma)
        assert result.tipo_documento == TipoDocumento.DNI
        assert result.razon_social == "CALLIRGOS OROZCO PIERO ALDAIR"
        assert "," not in result.razon_social


def test_fallback_si_ruc_detail_cae_timeout():
    """Si la 2da POST hace timeout, volver al parser histórico."""
    dni_soup = _soup(DNI_SEARCH_HTML)

    with patch("documento_scraper._post_query") as mock_post:
        mock_post.side_effect = [dni_soup, ScraperTimeoutError(timeout_type="read")]

        result = consultar("74827847")

        assert result.razon_social == "CALLIRGOS OROZCO PIERO ALDAIR"


def test_fallback_si_detalle_sin_coma():
    """Si el HTML del detalle no tiene la coma, fallback al parser histórico."""
    dni_soup = _soup(DNI_SEARCH_HTML)
    ruc_soup = _soup(RUC_DETAIL_HTML_SIN_COMA)

    with patch("documento_scraper._post_query") as mock_post:
        mock_post.side_effect = [dni_soup, ruc_soup]

        result = consultar("74827847")

        # Fallback: parser histórico devuelve "CALLIRGOS OROZCO PIERO ALDAIR"
        assert result.razon_social == "CALLIRGOS OROZCO PIERO ALDAIR"


def test_fallback_si_detalle_html_cambio():
    """Si el HTML del detalle cambió (sin campo Tipo de Documento), fallback."""
    html_sin_tipo_doc = """
    <html><body>
    <div class="list-group">
      <div class="list-group-item">
        <div class="row">
          <div class="col-sm-5">Numero RUC</div>
          <div class="col-sm-7">10748278473</div>
        </div>
      </div>
    </div>
    </body></html>
    """
    dni_soup = _soup(DNI_SEARCH_HTML)
    ruc_soup = _soup(html_sin_tipo_doc)

    with patch("documento_scraper._post_query") as mock_post:
        mock_post.side_effect = [dni_soup, ruc_soup]

        result = consultar("74827847")

        # Fallback
        assert result.razon_social == "CALLIRGOS OROZCO PIERO ALDAIR"


# ──────────────────────────────────────────────
# 3. Casos de error reales
# ──────────────────────────────────────────────

def test_dni_sin_resultados_lanza_NotFound_sin_hacer_segunda_request():
    """Si el DNI no devuelve resultados, no se intenta la 2da POST."""
    html_vacio = '<html><body><div class="list-group"></div></body></html>'
    dni_soup = _soup(html_vacio)

    with patch("documento_scraper._post_query") as mock_post:
        mock_post.side_effect = [dni_soup]

        with pytest.raises(DocumentNotFoundError):
            consultar("00000000")

        assert mock_post.call_count == 1


def test_dni_sin_data_ruc_cae_a_fallback_historico():
    """Si el primer resultado no tiene data-ruc, NO debe fallar:
    usa el parser histórico (comportamiento original del worker)."""
    html_sin_data_ruc = """
    <html><body>
    <div class="list-group">
      <a href="#" class="list-group-item clearfix aRucs">
        <h4 class="list-group-item-heading">CALLIRGOS OROZCO PIERO ALDAIR</h4>
      </a>
    </div>
    </body></html>
    """
    dni_soup = _soup(html_sin_data_ruc)

    with patch("documento_scraper._post_query") as mock_post:
        mock_post.side_effect = [dni_soup]

        result = consultar("00000000")

        assert result.tipo_documento == TipoDocumento.DNI
        assert result.razon_social == "CALLIRGOS OROZCO PIERO ALDAIR"
        # No se hace la 2da POST porque no hay RUC para consultar
        assert mock_post.call_count == 1


# ──────────────────────────────────────────────
# 4. E2E real contra SUNAT
# ──────────────────────────────────────────────

@pytest.mark.e2e
def test_e2e_dni_click_flow_nombre_viene_con_coma():
    """E2E real: DNI 74827847 → nombre debe tener coma."""
    result = consultar("74827847")

    assert result.tipo_documento == TipoDocumento.DNI
    assert result.numero_documento == "74827847"
    assert "," in result.razon_social, (
        f"E2E: el nombre debe traer coma, vino {result.razon_social!r}"
    )
    for parte in ("CALLIRGOS", "OROZCO", "PIERO", "ALDAIR"):
        assert parte in result.razon_social
    print(f"\n[E2E DNI click flow] razon_social = {result.razon_social!r}")