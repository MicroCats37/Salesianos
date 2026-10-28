"""
Integration tests — the matrix of administrative capabilities.

The capabilities are the single vocabulary of the administration area
(`core.capacidades`), derived from the Django flags. These tests freeze the
matrix:

- `usuario` → NO capability.
- `staff` (operational staff) → reads everything and writes the operational
  domains; it does NOT approve or annul payments.
- `superusuario` (break-glass) → EVERY capability.

The HTTP part proves the REAL consequence: the sensitive routes answer 403 to
the operational staff, and the read routes answer 200 to both tiers.

Contract: `contract/django-app-architecture-contract.md` §10 — the Django
flags are the only source of truth and no permission table is introduced.
"""
import pytest

from core.capacidades import (
    CAPACIDADES_DE_STAFF,
    CAP_ADMIN_VER,
    CAP_COMPETENCIAS_ESCRIBIR,
    CAP_PAGOS_APROBAR,
    CAP_PAGOS_VER,
    CAP_USUARIOS_GESTIONAR,
    CAP_USUARIOS_VER,
    TODAS_LAS_CAPACIDADES,
    es_admin,
    nivel_de,
)
from modules.administracion.tests.factories import make_auth_header

URL_RESUMEN = "/api/administracion/resumen"
URL_PAGOS = "/api/administracion/pagos"
URL_USUARIOS = "/api/administracion/usuarios"
URL_APROBAR = "/api/administracion/pagos/{orden_pago_id}/aprobar-manual"
URL_ANULAR = "/api/administracion/pagos/{orden_pago_id}/anular-manual"
URL_CANCELAR_PASE = "/api/administracion/pases/compras/{compra_id}/cancelar"

# A body that PASSES the schema validation: the gate of the capability must
# be the ONLY reason of a rejection.
PAGO_MANUAL_VALIDO = {
    "canal": "TRANSFERENCIA_BANCARIA",
    "referencia": "OP-123",
    "monto": "100.00",
    "moneda": "PEN",
    "motivo": "Pago recibido en la oficina del colegio.",
}

# ── El mapa de capacidades ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_usuario_normal_no_tiene_capacidades(usuario_no_admin):
    """
    GIVEN: an account that is neither staff nor superuser
    WHEN:  the capability map is resolved
    THEN:  the tier is `usuario` and the capability set is EMPTY.
    """
    from core.capacidades import capacidades_de

    assert nivel_de(usuario_no_admin) == "usuario"
    assert es_admin(usuario_no_admin) is False
    assert capacidades_de(usuario_no_admin) == frozenset()


@pytest.mark.django_db
def test_staff_tiene_el_conjunto_operativo(usuario_admin_staff):
    """
    GIVEN: an operational staff
    WHEN:  the capability map is resolved
    THEN:  it reads everything and writes the operational domains, but it
            does NOT approve payments nor manage accounts.
    """
    from core.capacidades import capacidades_de

    assert nivel_de(usuario_admin_staff) == "staff"
    assert es_admin(usuario_admin_staff) is True

    capacidades = capacidades_de(usuario_admin_staff)
    assert capacidades == CAPACIDADES_DE_STAFF
    assert CAP_ADMIN_VER in capacidades
    assert CAP_COMPETENCIAS_ESCRIBIR in capacidades
    assert CAP_PAGOS_VER in capacidades
    assert CAP_USUARIOS_VER in capacidades
    assert CAP_PAGOS_APROBAR not in capacidades
    assert CAP_USUARIOS_GESTIONAR not in capacidades


@pytest.mark.django_db
def test_superusuario_resuelve_todas_las_capacidades(usuario_admin_superuser):
    """
    GIVEN: a break-glass account
    WHEN:  the capability map is resolved
    THEN:  it ALWAYS resolves the COMPLETE set: Django bypasses every check,
            so our map must never be narrower than Django's.
    """
    from core.capacidades import capacidades_de

    assert nivel_de(usuario_admin_superuser) == "superusuario"
    assert es_admin(usuario_admin_superuser) is True
    assert capacidades_de(usuario_admin_superuser) == TODAS_LAS_CAPACIDADES
    assert CAP_PAGOS_APROBAR in capacidades_de(usuario_admin_superuser)


# ── La superficie de LECTURA ──────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("url", [URL_RESUMEN, URL_PAGOS, URL_USUARIOS])
def test_staff_lee_la_superficie_de_administracion(
    api_client, usuario_admin_staff, escenario_operativo, url
):
    """
    GIVEN: an operational staff
    WHEN:  it reads the operational surface
    THEN:  it gets 200 — the staff READS everything.
    """
    response = api_client.get(url, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("url", [URL_RESUMEN, URL_PAGOS, URL_USUARIOS])
def test_usuario_normal_no_lee_la_superficie(
    api_client, usuario_no_admin, escenario_operativo, url
):
    """
    GIVEN: an account with no capability
    WHEN:  it reads the operational surface
    THEN:  it gets 403 — visibility is not authorization, and neither is.
    """
    response = api_client.get(url, **make_auth_header(usuario_no_admin))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


# ── La superficie SENSIBLE ────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url", "payload"),
    [
        (URL_APROBAR, PAGO_MANUAL_VALIDO),
        (URL_ANULAR, {"motivo": "Anulacion de la aprobacion manual."}),
        (
            URL_CANCELAR_PASE,
            {"motivo": "Cancelacion administrativa de la compra de pases."},
        ),
    ],
)
def test_staff_no_puede_ejecutar_las_acciones_sensibles(
    api_client, usuario_admin_staff, escenario_operativo, url, payload
):
    """
    GIVEN: an operational staff
    WHEN:  it calls a SENSITIVE route (approve, annul or cancel a pass)
    THEN:  it gets 403 — the sensitive capability belongs to the break-glass
            tier only.
    """
    response = api_client.post(
        url.format(orden_pago_id="11111111-2222-3333-4444-555555555555", compra_id="11111111-2222-3333-4444-555555555555"),
        **make_auth_header(usuario_admin_staff),
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url", "payload"),
    [
        (URL_APROBAR, PAGO_MANUAL_VALIDO),
        (URL_ANULAR, {"motivo": "Anulacion de la aprobacion manual."}),
        (
            URL_CANCELAR_PASE,
            {"motivo": "Cancelacion administrativa de la compra de pases."},
        ),
    ],
)
def test_superusuario_pasa_el_gate_de_las_acciones_sensibles(
    api_client, usuario_admin_superuser, escenario_operativo, url, payload
):
    """
    GIVEN: a break-glass account
    WHEN:  it calls a SENSITIVE route
    THEN:  it is NOT rejected with 403: the capability gate lets it through
            and the answer is the one of the domain (404/409/422).
    """
    response = api_client.post(
        url.format(orden_pago_id="11111111-2222-3333-4444-555555555555", compra_id="11111111-2222-3333-4444-555555555555"),
        **make_auth_header(usuario_admin_superuser),
        data=payload,
        content_type="application/json",
    )

    assert response.status_code != 403


@pytest.mark.django_db
def test_usuario_normal_no_puede_ejecutar_las_acciones_sensibles(
    api_client, usuario_no_admin, escenario_operativo
):
    """
    GIVEN: an account with no capability
    WHEN:  it calls a SENSITIVE route
    THEN:  it gets 403.
    """
    response = api_client.post(
        URL_APROBAR.format(
            orden_pago_id="11111111-2222-3333-4444-555555555555"
        ),
        **make_auth_header(usuario_no_admin),
        data=PAGO_MANUAL_VALIDO,
        content_type="application/json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_anonimo_no_puede_ejecutar_las_acciones_sensibles(
    api_client, escenario_operativo
):
    """
    GIVEN: an anonymous caller
    WHEN:  it calls a SENSITIVE route
    THEN:  it gets 401 — the JWT runs BEFORE the capability gate.
    """
    response = api_client.post(
        URL_APROBAR.format(
            orden_pago_id="11111111-2222-3333-4444-555555555555"
        ),
        data=PAGO_MANUAL_VALIDO,
        content_type="application/json",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
