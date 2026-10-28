"""
Integration tests of the A1-A14 MATRIX of the administrative surface.

This file is the EVIDENCE of the verification phase (task 6.2). It does not
test a single endpoint in depth — it proves, for EVERY surface of the area:

- the route exists and answers 200 for an administrator,
- it is CLOSED to anonymous (401) and to an authenticated non-admin (403),
- the response NEVER carries a forbidden key (credentials, payment internals,
  the live QR),
- the list endpoints share the SAME canonical pagination contract,
- the ordering whitelist is enforced on EVERY list,
- the documented filters narrow with the documented values,
- the rows of ANOTHER edition never enter the lists,
- the operational surface (A1-A14) declares NO write method at all.

The per-endpoint depth (exact metrics, 404s, no-mutation snapshots) lives in
the files that own each surface; this file closes the GAPS of the matrix.
"""
from datetime import date, timedelta

import pytest

from modules.administracion.domain.services.core.admin_operacion_service import (
    DEFAULT_ORDERING_ACCESOS,
    DEFAULT_ORDERING_ACREDITACIONES,
    DEFAULT_ORDERING_EQUIPOS,
    DEFAULT_ORDERING_INSCRIPCIONES,
    DEFAULT_ORDERING_PAGOS,
    DEFAULT_ORDERING_PARTICIPACIONES,
    DEFAULT_ORDERING_PARTICIPANTES,
    DEFAULT_ORDERING_USUARIOS,
    ORDERING_ACCESOS,
    ORDERING_ACREDITACIONES,
    ORDERING_EQUIPOS,
    ORDERING_INSCRIPCIONES,
    ORDERING_PAGOS,
    ORDERING_PARTICIPACIONES,
    ORDERING_PARTICIPANTES,
    ORDERING_USUARIOS,
)
from modules.administracion.tests.factories import (
    make_auth_header,
    make_forbidden_keys,
    make_forbidden_keys_de_cuentas,
    make_list_query,
)


# ── The matrix ────────────────────────────────────────────────────────────────

#: The fourteen surfaces of the administrative area, with the code of the
#: `admin-surface` document they belong to.
SUPERFICIES = (
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "A6",
    "A7",
    "A8",
    "A9",
    "A10",
    "A11",
    "A12",
    "A13",
    "A14",
)

#: The eight LIST surfaces — the ones that share the pagination contract.
SUPERFICIES_LISTA = ("A3", "A5", "A7", "A8", "A9", "A10", "A12", "A13")

#: The public ordering field of every list, per the documented contract.
ORDEN_POR_LISTA = {
    "A3": "estado",
    "A5": "estado_compra",
    "A7": "nombre",
    "A8": "persona",
    "A9": "rol",
    "A10": "autorizacion_fiesta",
    "A12": "punto_acceso",
    "A13": "username",
}

#: The secrets that must not travel even INSIDE a string of the response.
SECRETOS_EN_TEXTO = (
    "password",
    "password_hash",
    "codigo_qr",
    "token_sesion",
    "auth_token",
    "transaction_id",
    "response_message",
)

#: The static URL of every LIST surface — no id of the scenario is needed.
URLS_LISTA = {
    "A3": "/api/administracion/inscripciones",
    "A5": "/api/administracion/pagos",
    "A7": "/api/administracion/equipos",
    "A8": "/api/administracion/participantes",
    "A9": "/api/administracion/participaciones",
    "A10": "/api/administracion/acreditaciones",
    "A12": "/api/administracion/accesos",
    "A13": "/api/administracion/usuarios",
}

#: The path prefixes of the operational administration surface (A1-A14) that
#: THIS module owns. Every route under them must be READ-ONLY, EXCEPT the
#: audited writes of the manual payment approval.
PREFIJOS_SUPERFICIE_OPERATIVA = (
    "/api/administracion/health",
    "/api/administracion/resumen",
    "/api/administracion/catalogos",
    "/api/administracion/inscripciones",
    "/api/administracion/pagos",
    "/api/administracion/equipos",
    "/api/administracion/participantes",
    "/api/administracion/participaciones",
    "/api/administracion/acreditaciones",
    "/api/administracion/accesos",
    "/api/administracion/usuarios",
)

#: The ONLY writes of the operational administration surface: the audited
#: approval and annulment of a payment received outside the provider. They
#: are admin-only, they record the actor and their motive, and they are
#: covered by their own suite (`modules/pagos/tests/integration/
#: test_admin_pago_manual.py`).
RUTAS_ESCRITURA_AUDITADA = (
    "/api/administracion/pagos/{orden_pago_id}/aprobar-manual",
    "/api/administracion/pagos/{orden_pago_id}/anular-manual",
)

#: The administrative namespaces owned by ANOTHER module. They are EXCLUDED
#: from the read-only guarantee of this file: the `competencias`
#: administration namespace declares write methods (POST/PATCH/DELETE) by
#: design, and that module owns (and tests) its own evidence.
NAMESPACES_DE_OTROS_MODULOS = (
    "/api/administracion/competencias",
)


@pytest.fixture
def urls_matriz(escenario_operativo, usuario_admin_staff):
    """The concrete URL of every surface A1-A14 of the active event."""
    escenario = escenario_operativo
    return {
        "A1": "/api/administracion/resumen",
        "A2": "/api/administracion/catalogos",
        "A3": "/api/administracion/inscripciones",
        "A4": f"/api/administracion/inscripciones/{escenario['inscripcion_1'].id}",
        "A5": "/api/administracion/pagos",
        "A6": f"/api/administracion/pagos/{escenario['orden_inicial'].id}",
        "A7": "/api/administracion/equipos",
        "A8": "/api/administracion/participantes",
        "A9": "/api/administracion/participaciones",
        "A10": "/api/administracion/acreditaciones",
        "A11": (
            f"/api/administracion/acreditaciones/{escenario['acreditacion_1'].id}"
        ),
        "A12": "/api/administracion/accesos",
        "A13": "/api/administracion/usuarios",
        "A14": f"/api/administracion/usuarios/{usuario_admin_staff.id}",
    }


def _claves(node) -> list:
    """Return EVERY key of a JSON body, at any depth."""
    if isinstance(node, dict):
        collected = list(node.keys())
        for valor in node.values():
            collected.extend(_claves(valor))
        return collected
    if isinstance(node, list):
        collected = []
        for item in node:
            collected.extend(_claves(item))
        return collected
    return []


def _es_ruta_de_la_superficie_operativa(ruta: str) -> bool:
    """
    True when the path belongs to the operational administration surface
    (A1-A14) owned by THIS module.

    The scope is EXPLICIT and does NOT depend on the total number of
    administrative routes: a path belongs to the surface when it lives under
    one of the owned prefixes and it is NOT under a namespace owned by
    another module.
    """
    if not ruta.startswith("/api/administracion"):
        return False
    if any(
        ruta == namespace or ruta.startswith(f"{namespace}/")
        for namespace in NAMESPACES_DE_OTROS_MODULOS
    ):
        return False
    return any(
        ruta == prefijo or ruta.startswith(f"{prefijo}/")
        for prefijo in PREFIJOS_SUPERFICIE_OPERATIVA
    )


# ── A1-A14: route, authorization, payload, secrets ───────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("superficie", SUPERFICIES)
def test_matriz_a1_a14_responde_200_para_admin(
    api_client,
    usuario_admin_staff,
    urls_matriz,
    superficie,
):
    """
    GIVEN: an administrator
    WHEN:  GET every surface of the matrix
    THEN:  200 with the canonical envelope.
    """
    response = api_client.get(
        urls_matriz[superficie], **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "data" in body


@pytest.mark.django_db
@pytest.mark.parametrize("superficie", SUPERFICIES)
def test_matriz_a1_a14_esta_cerrada_para_anonimos(
    api_client, urls_matriz, superficie
):
    """
    GIVEN: an anonymous caller
    WHEN:  GET every surface of the matrix
    THEN:  401 `AUTHENTICATION_REQUIRED` — the JWT always runs first.
    """
    response = api_client.get(urls_matriz[superficie])

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
@pytest.mark.parametrize("superficie", SUPERFICIES)
def test_matriz_a1_a14_esta_cerrada_para_no_administradores(
    api_client, usuario_no_admin, urls_matriz, superficie
):
    """
    GIVEN: an authenticated NON administrator
    WHEN:  GET every surface of the matrix
    THEN:  403 `ACTION_NOT_ALLOWED` — the permission is server-side.
    """
    response = api_client.get(
        urls_matriz[superficie], **make_auth_header(usuario_no_admin)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
@pytest.mark.parametrize("superficie", SUPERFICIES)
def test_matriz_a1_a14_no_expone_ninguna_clave_prohibida(
    api_client,
    usuario_admin_staff,
    urls_matriz,
    superficie,
):
    """
    GIVEN: an administrator
    WHEN:  GET every surface of the matrix
    THEN:  the body carries NO forbidden key, at any depth, and no secret
           inside a string.
    """
    response = api_client.get(
        urls_matriz[superficie], **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200

    # Las cuentas (A13/A14) publican el NIVEL de cada cuenta
    # (`is_staff`, `is_superuser`, `nivel`): un administrador de cuentas debe
    # poder ver quién tiene el nivel de break-glass. El resto de las
    # superficies NO lo publican.
    if superficie in {"A13", "A14"}:
        prohibido_keys = make_forbidden_keys_de_cuentas()
    else:
        prohibido_keys = make_forbidden_keys()

    claves = {clave.lower() for clave in _claves(response.json())}
    for prohibido in prohibido_keys:
        assert prohibido not in claves

    cuerpo = response.text.lower()
    for secreto in SECRETOS_EN_TEXTO:
        assert secreto not in cuerpo


@pytest.mark.django_db
def test_la_superficie_administrativa_no_declara_ningun_metodo_de_escritura():
    """
    GIVEN: the OpenAPI schema of the API
    WHEN:  every path of the operational administration surface (A1-A14) is
           inspected — the namespaces owned by another module are excluded
    THEN:  the ONLY declared method is `get` — the area is read-only.
    """
    from config.api import api

    schema = api.get_openapi_schema()
    rutas_operativas = [
        ruta
        for ruta in schema["paths"]
        if _es_ruta_de_la_superficie_operativa(ruta)
    ]

    assert rutas_operativas, "la superficie operativa no expone ninguna ruta"
    for prefijo in PREFIJOS_SUPERFICIE_OPERATIVA:
        assert any(
            ruta == prefijo or ruta.startswith(f"{prefijo}/")
            for ruta in rutas_operativas
        ), f"la superficie operativa no expone la ruta {prefijo}"
    for ruta in rutas_operativas:
        metodos = set(schema["paths"][ruta].keys())
        if ruta in RUTAS_ESCRITURA_AUDITADA:
            # The audited writes of the manual payment approval: the ONLY
            # writes of the operational surface.
            assert metodos == {"post"}, f"{ruta} declara {sorted(metodos)}"
            continue
        assert metodos == {"get"}, f"{ruta} declara {sorted(metodos)}"


@pytest.mark.django_db
@pytest.mark.parametrize("metodo", ["post", "put", "patch", "delete"])
def test_la_superficie_administrativa_rechaza_las_escrituras(
    api_client, usuario_admin_staff, urls_matriz, metodo
):
    """
    GIVEN: an administrator with a valid token
    WHEN:  a WRITE method is used against a read-only surface
    THEN:  the request is refused — the area has no write path at all.
    """
    respuesta = getattr(api_client, metodo)(
        urls_matriz["A3"], **make_auth_header(usuario_admin_staff)
    )

    assert respuesta.status_code in (404, 405)
    assert not (200 <= respuesta.status_code < 300)


# ── The canonical pagination contract, on EVERY list ─────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("superficie", SUPERFICIES_LISTA)
def test_la_paginacion_canonica_se_aplica_en_todas_las_listas(
    api_client, usuario_admin_staff, urls_matriz, superficie
):
    """
    GIVEN: a list surface of the matrix
    WHEN:  it is requested with the pagination parameters
    THEN:  the canonical contract holds: base 1, default 25, max 100 CLAMPED,
           and a page out of range answers an EMPTY list — never a 404.
    """
    headers = make_auth_header(usuario_admin_staff)
    url = urls_matriz[superficie]

    por_defecto = api_client.get(url, **headers).json()["data"]
    assert por_defecto["page"] == 1
    assert por_defecto["page_size"] == 25
    assert por_defecto["total"] >= 0
    assert por_defecto["total_pages"] == -(-por_defecto["total"] // 25)

    recortado = api_client.get(
        url, **headers, data=make_list_query(page_size=500)
    ).json()["data"]
    assert recortado["page_size"] == 100

    base_uno = api_client.get(
        url, **headers, data=make_list_query(page=0)
    ).json()["data"]
    assert base_uno["page"] == 1

    fuera_de_rango = api_client.get(
        url, **headers, data=make_list_query(page=9999)
    )
    assert fuera_de_rango.status_code == 200
    assert fuera_de_rango.json()["data"]["items"] == []


# ── The ordering whitelist, on EVERY list ────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("superficie", SUPERFICIES_LISTA)
def test_el_ordenamiento_por_lista_blanca_se_aplica_en_todas_las_listas(
    api_client, usuario_admin_staff, urls_matriz, superficie
):
    """
    GIVEN: a list surface of the matrix
    WHEN:  it is ordered by a whitelisted field and by an unknown one
    THEN:  the whitelisted field answers 200 and the unknown one answers
           422 `INVALID_REQUEST` — the raw client text never reaches the ORM.
    """
    headers = make_auth_header(usuario_admin_staff)
    url = urls_matriz[superficie]
    campo = ORDEN_POR_LISTA[superficie]

    permitido = api_client.get(
        url, **headers, data=make_list_query(ordering=campo)
    )
    assert permitido.status_code == 200

    descendente = api_client.get(
        url, **headers, data=make_list_query(ordering=f"-{campo}")
    )
    assert descendente.status_code == 200

    desconocido = api_client.get(
        url, **headers, data=make_list_query(ordering="campo_inexistente")
    )
    assert desconocido.status_code == 422
    assert desconocido.json()["error"]["code"] == "INVALID_REQUEST"

    inyectado = api_client.get(
        url, **headers, data=make_list_query(ordering=f"{campo}; DROP TABLE x")
    )
    assert inyectado.status_code == 422
    assert inyectado.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.django_db
def test_las_listas_blancas_de_orden_coinciden_con_el_contrato():
    """
    GIVEN: the ordering whitelists of the backend
    WHEN:  they are compared with the documented contract
    THEN:  they hold exactly the documented public fields — the contract the
           frontend mirrors 1:1.
    """
    assert set(ORDERING_INSCRIPCIONES) == {
        "created_at",
        "estado",
        "responsable",
        "paquete",
    }
    assert set(ORDERING_PAGOS) == {
        "created_at",
        "total",
        "cantidad",
        "estado_compra",
        "estado_orden",
        "pagada_en",
    }
    assert set(ORDERING_EQUIPOS) == {"created_at", "nombre", "disciplina", "estado"}
    assert set(ORDERING_PARTICIPANTES) == {"created_at", "persona", "estado"}
    assert set(ORDERING_PARTICIPACIONES) == {
        "created_at",
        "persona",
        "equipo",
        "disciplina",
        "rol",
        "estado",
    }
    assert set(ORDERING_ACREDITACIONES) == {
        "persona",
        "estado",
        "autorizacion_fiesta",
    }
    assert set(ORDERING_ACCESOS) == {"fecha_hora", "resultado", "punto_acceso"}
    assert set(ORDERING_USUARIOS) == {
        "created_at",
        "username",
        "nombres",
        "last_login",
    }


@pytest.mark.django_db
def test_los_ordenes_por_defecto_coinciden_con_el_contrato():
    """GIVEN: the default ordering of every list WHEN: read THEN: documented."""
    assert DEFAULT_ORDERING_INSCRIPCIONES == "-created_at"
    assert DEFAULT_ORDERING_PAGOS == "-created_at"
    assert DEFAULT_ORDERING_EQUIPOS == "-created_at"
    assert DEFAULT_ORDERING_PARTICIPANTES == "-created_at"
    assert DEFAULT_ORDERING_PARTICIPACIONES == "-created_at"
    assert DEFAULT_ORDERING_ACREDITACIONES == "persona__nombres"
    assert DEFAULT_ORDERING_ACCESOS == "-fecha_hora"
    assert DEFAULT_ORDERING_USUARIOS == "-created_at"


# ── The documented filters, with the documented values ───────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("superficie", "filtro", "valor", "total_esperado"),
    [
        # A5 — the state of the payment ORDER (the purchase state is already
        # covered by the file of the payments).
        ("A5", "estado_orden", "VENCIDA", 1),
        # A7 — the registration that owns the team and the free text.
        ("A7", "inscripcion_id", "@inscripcion_1", 3),
        ("A7", "q", "Tigres", 1),
        # A8 — the people WITHOUT an active cup and the free text.
        ("A8", "con_cupo", "false", 4),
        ("A8", "q", "Alvarez", 1),
        # A9 — the roster rows: discipline, role, registration and free text.
        ("A9", "disciplina_id", "@disciplina_voley", 1),
        ("A9", "rol", "C", 1),
        ("A9", "inscripcion_id", "@inscripcion_2", 2),
        ("A9", "q", "Mendoza", 2),
        ("A9", "q", "Panteras", 1),
        # A13 — the accounts that are NOT administrators.
        ("A13", "es_admin", "false", 2),
    ],
)
def test_los_filtros_documentados_estrechan_la_lista(
    api_client,
    usuario_admin_staff,
    usuario_admin_superuser,
    usuario_no_admin,
    usuario_inactivo,
    urls_matriz,
    escenario_operativo,
    superficie,
    filtro,
    valor,
    total_esperado,
):
    """
    GIVEN: a documented filter of a list surface
    WHEN:  it is applied with a DOCUMENTED value
    THEN:  it narrows the list to the expected rows.
    """
    escenario = escenario_operativo
    if valor.startswith("@"):
        valor = str(escenario[valor[1:]].id)

    response = api_client.get(
        urls_matriz[superficie],
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(**{filtro: valor}),
    )

    assert response.status_code == 200
    assert response.json()["data"]["total"] == total_esperado


@pytest.mark.django_db
@pytest.mark.parametrize("superficie", ["A5", "A12"])
def test_el_rango_de_fechas_estrcha_por_fecha_de_creacion(
    api_client, usuario_admin_staff, urls_matriz, escenario_operativo, superficie
):
    """
    GIVEN: a list surface with an ISO date range (`desde` / `hasta`)
    WHEN:  the range is moved one day before and one day after the creation
           date of the rows
    THEN:  the range narrows to every row, and to NONE.
    """
    headers = make_auth_header(usuario_admin_staff)
    url = urls_matriz[superficie]

    base = api_client.get(url, **headers).json()["data"]
    total = base["total"]
    assert total > 0

    campo_fecha = "fecha_hora" if superficie == "A12" else "created_at"
    fecha = date.fromisoformat(base["items"][0][campo_fecha][:10])

    dentro = api_client.get(
        url, **headers, data=make_list_query(desde=fecha.isoformat())
    ).json()["data"]
    assert dentro["total"] == total

    hasta = api_client.get(
        url, **headers, data=make_list_query(hasta=fecha.isoformat())
    ).json()["data"]
    assert hasta["total"] == total

    futuro = api_client.get(
        url,
        **headers,
        data=make_list_query(desde=(fecha + timedelta(days=1)).isoformat()),
    ).json()["data"]
    assert futuro["total"] == 0

    pasado = api_client.get(
        url,
        **headers,
        data=make_list_query(hasta=(fecha - timedelta(days=1)).isoformat()),
    ).json()["data"]
    assert pasado["total"] == 0


# ── The event scope, on EVERY event-scoped list ──────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    "superficie", ["A3", "A5", "A7", "A8", "A9", "A10", "A12"]
)
def test_las_filas_de_otra_edicion_no_entran_en_las_listas(
    api_client, usuario_admin_staff, escenario_otra_edicion, superficie
):
    """
    GIVEN: rows that belong to ANOTHER edition of the event
    WHEN:  every event-scoped list is requested
    THEN:  the list is EMPTY — the active event is resolved server-side and
           the rows of another edition never enter the area.

    The accounts (A13) are NOT part of this matrix on purpose: an account is
    a global identity, not a row of an edition.
    """
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import (
        AcreditacionEvento,
        ControlAcceso,
        Equipo,
        Inscripcion,
        Participacion,
    )

    # Sanity: the rows of the other edition DO exist in the database.
    assert Inscripcion.objects.count() == 1
    assert Equipo.objects.count() == 1
    assert Participacion.objects.count() == 1
    assert Compra.objects.count() == 1
    assert AcreditacionEvento.objects.count() == 1
    assert ControlAcceso.objects.count() == 1

    response = api_client.get(
        URLS_LISTA[superficie], **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.django_db
def test_el_detalle_de_otra_edicion_responde_404(
    api_client, usuario_admin_staff, escenario_otra_edicion
):
    """
    GIVEN: a registration of ANOTHER edition
    WHEN:  its drilldown is requested
    THEN:  404 `RESOURCE_NOT_FOUND` — the surface never confirms that the
           resource exists outside its scope.
    """
    url = (
        f"/api/administracion/inscripciones/"
        f"{escenario_otra_edicion['inscripcion_fuera'].id}"
    )

    response = api_client.get(url, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


# ── The read-only behaviour of the WHOLE area ────────────────────────────────


@pytest.mark.django_db
def test_ninguna_lectura_de_la_matriz_muta_una_tabla(
    api_client, usuario_admin_staff, urls_matriz, escenario_operativo
):
    """
    GIVEN: the whole operational scenario
    WHEN:  every surface of the matrix is read
    THEN:  NO row of any touched table changed — the area performs zero
           writes.
    """
    from django.contrib.auth import get_user_model

    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import OrdenPago, TransaccionPago
    from modules.salesianos_fest.domain.models import (
        AcreditacionEvento,
        AsignacionCupo,
        CompraInscripcion,
        ControlAcceso,
        Equipo,
        Inscripcion,
        InscripcionPersona,
        Participacion,
    )

    User = get_user_model()
    antes = {
        "inscripciones": Inscripcion.objects.count(),
        "equipos": Equipo.objects.count(),
        "participaciones": Participacion.objects.count(),
        "personas_inscripcion": InscripcionPersona.objects.count(),
        "asignaciones": AsignacionCupo.objects.count(),
        "acreditaciones": AcreditacionEvento.objects.count(),
        "accesos": ControlAcceso.objects.count(),
        "compras": Compra.objects.count(),
        "lineas_compra_inscripcion": CompraInscripcion.objects.count(),
        "ordenes": OrdenPago.objects.count(),
        "transacciones": TransaccionPago.objects.count(),
        "usuarios": User.objects.count(),
    }

    headers = make_auth_header(usuario_admin_staff)
    for url in urls_matriz.values():
        assert api_client.get(url, **headers).status_code == 200

    despues = {
        "inscripciones": Inscripcion.objects.count(),
        "equipos": Equipo.objects.count(),
        "participaciones": Participacion.objects.count(),
        "personas_inscripcion": InscripcionPersona.objects.count(),
        "asignaciones": AsignacionCupo.objects.count(),
        "acreditaciones": AcreditacionEvento.objects.count(),
        "accesos": ControlAcceso.objects.count(),
        "compras": Compra.objects.count(),
        "lineas_compra_inscripcion": CompraInscripcion.objects.count(),
        "ordenes": OrdenPago.objects.count(),
        "transacciones": TransaccionPago.objects.count(),
        "usuarios": User.objects.count(),
    }

    assert antes == despues
