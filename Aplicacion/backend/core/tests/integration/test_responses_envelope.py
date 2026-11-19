"""Contrato del envelope HTTP (FREEZE-ENV-1.0.0 · FR-01 §4).

GIVEN  el módulo `core.responses` del backend objetivo
WHEN   se construye un envelope de éxito, de error o paginado
THEN   el envelope tiene EXACTAMENTE la forma congelada y una sola forma de
       paginación.
"""

import pytest

from core import responses
from core.responses import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    error_response,
    paginated_response,
    success_response,
)


# ── Éxito ────────────────────────────────────────────────────────────────────


def test_el_envelope_de_exito_declara_las_cuatro_claves():
    body = success_response({"id": 1}, "La operación se completó correctamente.")

    assert set(body) == {"success", "data", "error", "message"}
    assert body["success"] is True
    assert body["data"] == {"id": 1}
    assert body["error"] is None
    assert body["message"] == "La operación se completó correctamente."


def test_el_envelope_de_exito_admite_payload_vacio():
    body = success_response()

    assert body["success"] is True
    assert body["data"] is None
    assert body["message"] is None


def test_el_envelope_de_exito_serieliza_los_decimales_como_numeros():
    from decimal import Decimal

    body = success_response({"total": Decimal("10.50")})

    assert body["data"]["total"] == 10.5
    assert isinstance(body["data"]["total"], float)


# ── Error ────────────────────────────────────────────────────────────────────


def test_el_envelope_de_error_declara_codigo_mensaje_y_campos_de_error():
    body, status = error_response(
        code="VALIDATION_ERROR",
        message="La solicitud no es válida.",
        details={"non_field_errors": "Revisa los datos ingresados."},
        status=422,
        field_errors=[
            {"field": "email", "code": "INVALID_VALUE", "message": "Correo inválido."}
        ],
    )

    assert status == 422
    assert body["success"] is False
    assert body["data"] is None
    assert body["message"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "La solicitud no es válida."
    assert body["error"]["details"] == {
        "non_field_errors": "Revisa los datos ingresados."
    }
    assert body["error"]["field_errors"] == [
        {"field": "email", "code": "INVALID_VALUE", "message": "Correo inválido."}
    ]


def test_el_envelope_de_error_no_declara_la_raiz_del_mensaje():
    body, _ = error_response(code="RESOURCE_NOT_FOUND", message="No se encontró.")

    assert body["message"] is None


# ── Paginación ───────────────────────────────────────────────────────────────


def test_la_paginacion_vive_dentro_de_data():
    body = paginated_response([{"id": 1}, {"id": 2}], total=2, page=1, page_size=25)

    assert set(body["data"]) == {
        "items",
        "total",
        "page",
        "page_size",
        "total_pages",
    }
    assert "meta" not in body
    assert "meta" not in body["data"]


def test_la_paginacion_es_base_uno():
    body = paginated_response([], total=0, page=1, page_size=25)

    assert body["data"]["page"] == 1
    assert body["data"]["total"] == 0
    assert body["data"]["total_pages"] == 0


def test_total_pages_redondea_hacia_arriba():
    body = paginated_response([], total=26, page=1, page_size=25)

    assert body["data"]["total_pages"] == 2


def test_la_paginacion_usa_el_tope_de_page_size():
    body = paginated_response([], total=0, page=1, page_size=5_000)

    assert body["data"]["page_size"] == MAX_PAGE_SIZE


def test_la_paginacion_usa_el_page_size_por_defecto():
    body = paginated_response([], total=0)

    assert body["data"]["page_size"] == DEFAULT_PAGE_SIZE


def test_la_forma_de_paginacion_deprecada_ya_no_existe():
    """FR-01 §4.3 regla 1: `PaginatedApiResponse` + `meta` queda deprecada.

    La eliminación del código es trabajo de FND-01 (owner A0) y ocurre en este
    paquete: ninguna ruta nueva puede declarar la segunda forma de paginación.
    """
    assert not hasattr(responses, "PaginatedApiResponse")
    assert not hasattr(responses, "PaginationMeta")


@pytest.mark.parametrize("metodo", ["success_response", "error_response", "paginated_response"])
def test_los_tres_constructores_del_envelope_existen(metodo):
    assert callable(getattr(responses, metodo))
