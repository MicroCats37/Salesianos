"""
Integration tests — the canonical pagination / search / ordering contract.

`AdminPaginacionService` owns the ONE list contract of the administrative
surface (`sdd/administracion-operativa-fest/admin-surface` §4.1):

- `page` 1-based, values below 1 clamped to 1.
- `page_size` default 25, maximum 100, values ABOVE the maximum are CLAMPED
  (not an error).
- `q` trimmed and capped at 120 characters.
- `ordering` resolved through a SERVER-SIDE WHITELIST; an unknown value is
  rejected with 422 `INVALID_REQUEST` and is NEVER interpolated into a
  queryset.
"""
import pytest
from ninja import Schema

from core.pagination import PaginatedData
from core.responses import ApiResponse, success_response
from modules.administracion.domain.exceptions import InvalidOrderingError
from modules.administracion.domain.services.core.admin_paginacion_service import (
    AdminPaginacionService,
)
from modules.administracion.presentation.presenters.admin_paginacion_presenter import (
    AdminPaginacionPresenter,
)

# Whitelist of a fictional resource: public field name -> ORM expression.
PERMITIDOS = {
    "creado": "created_at",
    "estado": "estado",
    "nombre": "persona__nombres",
}
DEFAULT_ORDERING = "-created_at"


@pytest.fixture
def servicio():
    """The admin pagination service."""
    return AdminPaginacionService()


# ── page ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        (None, 1),
        (0, 1),
        (-5, 1),
        (1, 1),
        (3, 3),
    ],
)
def test_normalizar_page(servicio, entrada, esperado):
    """GIVEN: a page parameter WHEN: normalized THEN: 1-based, never below 1."""
    assert servicio.normalizar_page(entrada) == esperado


def test_normalizar_page_con_valor_no_numerico_usa_el_default(servicio):
    """GIVEN: a non numeric page WHEN: normalized THEN: the default is used."""
    assert servicio.normalizar_page("abc") == 1


# ── page_size ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        (None, 25),
        (0, 1),
        (-10, 1),
        (10, 10),
        (100, 100),
        (101, 100),
        (5000, 100),
    ],
)
def test_normalizar_page_size(servicio, entrada, esperado):
    """GIVEN: a page_size WHEN: normalized THEN: clamped to [1, 100]."""
    assert servicio.normalizar_page_size(entrada) == esperado


def test_page_size_sobre_el_maximo_se_recorta_y_no_es_error(servicio):
    """
    GIVEN: a page_size above the maximum
    WHEN:  the pagination is built
    THEN:  it is CLAMPED, never rejected with an error.
    """
    params = servicio.construir_paginacion(
        page=1,
        page_size=9999,
        permitidos=PERMITIDOS,
        default_ordering=DEFAULT_ORDERING,
    )

    assert params.page_size == 100
    assert params.offset == 0


# ── q ─────────────────────────────────────────────────────────────────────────


def test_normalizar_q_none_devuelve_none(servicio):
    """GIVEN: no search term WHEN: normalized THEN: None."""
    assert servicio.normalizar_q(None) is None


def test_normalizar_q_vacio_devuelve_none(servicio):
    """GIVEN: a blank search term WHEN: normalized THEN: None."""
    assert servicio.normalizar_q("   ") is None


def test_normalizar_q_colapsa_espacios(servicio):
    """GIVEN: a term with repeated spaces WHEN: normalized THEN: collapsed."""
    assert servicio.normalizar_q("  Juan   Pérez  ") == "Juan Pérez"


def test_normalizar_q_limita_la_longitud(servicio):
    """GIVEN: an overlong term WHEN: normalized THEN: capped at 120 chars."""
    termino = "a" * 500

    resultado = servicio.normalizar_q(termino)

    assert resultado is not None
    assert len(resultado) == AdminPaginacionService.Q_MAXIMO


def test_normalizar_q_respeta_el_limite_de_120(servicio):
    """GIVEN: the documented cap WHEN: checked THEN: it is 120."""
    assert AdminPaginacionService.Q_MAXIMO == 120


# ── ordering ──────────────────────────────────────────────────────────────────


def test_resolver_ordering_sin_valor_usa_el_default(servicio):
    """GIVEN: no ordering WHEN: resolved THEN: the resource default is used."""
    assert (
        servicio.resolver_ordering(None, PERMITIDOS, DEFAULT_ORDERING)
        == DEFAULT_ORDERING
    )


def test_resolver_ordering_campo_permitido(servicio):
    """GIVEN: a whitelisted field WHEN: resolved THEN: its ORM expression."""
    assert (
        servicio.resolver_ordering("estado", PERMITIDOS, DEFAULT_ORDERING)
        == "estado"
    )


def test_resolver_ordering_descendente(servicio):
    """GIVEN: a whitelisted field with '-' WHEN: resolved THEN: descending."""
    assert (
        servicio.resolver_ordering("-nombre", PERMITIDOS, DEFAULT_ORDERING)
        == "-persona__nombres"
    )


def test_resolver_ordering_campo_desconocido_es_rechazado(servicio):
    """
    GIVEN: a field that is NOT whitelisted
    WHEN:  the ordering is resolved
    THEN:  it is rejected — the client text never reaches the queryset.
    """
    with pytest.raises(InvalidOrderingError) as excinfo:
        servicio.resolver_ordering("password", PERMITIDOS, DEFAULT_ORDERING)

    assert excinfo.value.code == "INVALID_REQUEST"
    assert excinfo.value.status_code == 422


def test_resolver_ordering_con_inyeccion_es_rechazado(servicio):
    """
    GIVEN: an ordering value that tries to inject ORM syntax
    WHEN:  the ordering is resolved
    THEN:  it is rejected with 422, never interpolated.
    """
    with pytest.raises(InvalidOrderingError):
        servicio.resolver_ordering(
            "created_at; DROP TABLE inscripciones",
            PERMITIDOS,
            DEFAULT_ORDERING,
        )


def test_resolver_ordering_con_guion_sin_campo_es_rechazado(servicio):
    """GIVEN: a bare '-' WHEN: resolved THEN: it is rejected."""
    with pytest.raises(InvalidOrderingError):
        servicio.resolver_ordering("-", PERMITIDOS, DEFAULT_ORDERING)


# ── construir_paginacion ──────────────────────────────────────────────────────


def test_construir_paginacion_calcula_el_offset(servicio):
    """GIVEN: page 3 and page_size 25 WHEN: built THEN: the offset is 50."""
    params = servicio.construir_paginacion(
        page=3,
        page_size=25,
        permitidos=PERMITIDOS,
        default_ordering=DEFAULT_ORDERING,
    )

    assert params.page == 3
    assert params.page_size == 25
    assert params.offset == 50


def test_construir_paginacion_normaliza_todo(servicio):
    """GIVEN: every raw parameter WHEN: built THEN: all of them are normalized."""
    params = servicio.construir_paginacion(
        page=0,
        page_size=500,
        q="  Juan   Pérez  ",
        ordering="-creado",
        permitidos=PERMITIDOS,
        default_ordering=DEFAULT_ORDERING,
    )

    assert params.page == 1
    assert params.page_size == 100
    assert params.q == "Juan Pérez"
    assert params.ordering == "-created_at"
    assert params.offset == 0


# ── The canonical envelope: ApiResponse[PaginatedData[T]] ─────────────────────


class _ItemOut(Schema):
    """Item of a fictional admin list."""

    id: str
    nombre: str


def test_el_envelope_canonico_es_api_response_de_paginated_data():
    """
    GIVEN: the canonical admin list envelope
    WHEN:  the generic composition is declared
    THEN:  it is `ApiResponse[PaginatedData[ItemOut]]`.
    """
    envelope = ApiResponse[PaginatedData[_ItemOut]]

    assert envelope is not None


def test_present_paginado_devuelve_la_forma_canonica(servicio):
    """
    GIVEN: a page of 2 items out of 7
    WHEN:  the canonical container is built
    THEN:  it carries items, total, page, page_size and total_pages.
    """
    params = servicio.construir_paginacion(
        page=2,
        page_size=3,
        permitidos=PERMITIDOS,
        default_ordering=DEFAULT_ORDERING,
    )

    items = [{"id": "1", "nombre": "Uno"}, {"id": "2", "nombre": "Dos"}]
    paginado = AdminPaginacionPresenter.present_paginado(items, 7, params)

    assert paginado.total == 7
    assert paginado.page == 2
    assert paginado.page_size == 3
    assert paginado.total_pages == 3
    assert len(paginado.items) == 2


def test_present_paginado_sin_resultados(servicio):
    """
    GIVEN: a page past the last one
    WHEN:  the canonical container is built
    THEN:  empty items with total 0 — never an error.
    """
    params = servicio.construir_paginacion(
        page=9,
        page_size=25,
        permitidos=PERMITIDOS,
        default_ordering=DEFAULT_ORDERING,
    )

    paginado = AdminPaginacionPresenter.present_paginado([], 0, params)

    assert paginado.items == []
    assert paginado.total == 0
    assert paginado.total_pages == 0


def test_present_paginado_se_envuelve_en_success_response(servicio):
    """
    GIVEN: the canonical container
    WHEN:  it is wrapped in the standard envelope
    THEN:  the JSON carries data.items/total/page/page_size/total_pages.
    """
    params = servicio.construir_paginacion(
        page=1,
        page_size=25,
        permitidos=PERMITIDOS,
        default_ordering=DEFAULT_ORDERING,
    )
    paginado = AdminPaginacionPresenter.present_paginado(
        [{"id": "1", "nombre": "Uno"}], 1, params
    )

    body = success_response(paginado)

    assert body["success"] is True
    assert body["data"]["items"] == [{"id": "1", "nombre": "Uno"}]
    assert body["data"]["total"] == 1
    assert body["data"]["page"] == 1
    assert body["data"]["page_size"] == 25
    assert body["data"]["total_pages"] == 1
