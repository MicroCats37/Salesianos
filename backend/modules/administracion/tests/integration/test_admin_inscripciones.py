"""
Integration tests — the registrations table and its drilldown (A3, A4).

Covers the contract of `sdd/administracion-operativa-fest/admin-surface` §10:

1. authorization on every endpoint (401 / 403 / 200),
2. the canonical paginated envelope,
3. the EVENT scope (rows of another edition are never listed),
4. the counters of a registration (exact numbers on the hand-built fixture),
5. the filters (each narrows, combined with AND, invalid → 422),
6. the free-text search over the DOCUMENTED fields, with SQL metacharacters,
7. the server-side ordering whitelist (unknown → 422),
8. the pagination semantics (1-based, clamped, page beyond the end),
9. the drilldown blocks and the 404 of an unknown / out-of-scope id,
10. no secret leakage and no accidental mutation.

The HTTP client is `django.test.Client`: the controllers are async and this is
the pattern already established by the rest of the project
(`contract/django-app-architecture-contract.md` §2.1).
"""
import pytest

from modules.administracion.tests.factories import (
    make_auth_header,
    make_forbidden_keys,
    make_list_query,
)

URL_LISTA = "/api/administracion/inscripciones"
URL_DETALLE = "/api/administracion/inscripciones/{inscripcion_id}"


# ── Autorización ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_lista_anonimo_responde_401(api_client):
    """
    GIVEN: an anonymous caller
    WHEN:  GET /api/administracion/inscripciones
    THEN:  401 with the stable code AUTHENTICATION_REQUIRED.
    """
    response = api_client.get(URL_LISTA)

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert body["data"] is None


@pytest.mark.django_db
def test_lista_no_admin_responde_403(api_client, usuario_no_admin):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN:  GET /api/administracion/inscripciones
    THEN:  403 with the stable code ACTION_NOT_ALLOWED and no data.
    """
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_no_admin))

    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert body["data"] is None


@pytest.mark.django_db
def test_detalle_anonimo_responde_401(api_client, escenario_operativo):
    """GIVEN: an anonymous caller WHEN: the drilldown THEN: 401."""
    response = api_client.get(
        URL_DETALLE.format(inscripcion_id=escenario_operativo["inscripcion_1"].id)
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_detalle_no_admin_responde_403(api_client, usuario_no_admin, escenario_operativo):
    """GIVEN: an authenticated non-admin WHEN: the drilldown THEN: 403."""
    response = api_client.get(
        URL_DETALLE.format(inscripcion_id=escenario_operativo["inscripcion_1"].id),
        **make_auth_header(usuario_no_admin),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_lista_admin_responde_200(api_client, usuario_admin_staff, escenario_operativo):
    """GIVEN: an administrator WHEN: the list THEN: 200 with the envelope."""
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert set(body.keys()) == {"success", "data", "error", "message"}
    assert set(body["data"].keys()) == {
        "items",
        "total",
        "page",
        "page_size",
        "total_pages",
    }


@pytest.mark.django_db
def test_detalle_admin_responde_200(api_client, usuario_admin_staff, escenario_operativo):
    """GIVEN: an administrator WHEN: the drilldown THEN: 200."""
    response = api_client.get(
        URL_DETALLE.format(inscripcion_id=escenario_operativo["inscripcion_1"].id),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


# ── Alcance del evento ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_lista_solo_incluye_el_evento_activo(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a registration of ANOTHER edition
    WHEN:  GET the list
    THEN:  it is NOT listed — the scope is the active event.
    """
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff))

    ids = [item["id"] for item in response.json()["data"]["items"]]

    assert str(escenario_operativo["inscripcion_fuera"].id) not in ids
    assert response.json()["data"]["total"] == 2


# ── Contadores ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_contadores_de_la_inscripcion_son_exactos(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: the hand-built scenario
    WHEN:  GET the list
    THEN:  every counter of the first registration is EXACT.

    - equipos: 2 ACTIVE (the cancelled one is not part of the operation),
    - personas: 2 ACTIVE registered people,
    - participaciones: 3 ACTIVE roster rows (one person plays TWO disciplines),
    - cupos: 3 contracted, 2 paid, 1 free, 150.00 paid.
    """
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff))

    items = response.json()["data"]["items"]
    por_id = {item["id"]: item for item in items}

    primera = por_id[str(escenario_operativo["inscripcion_1"].id)]

    assert primera["evento_nombre"] == "Salesianos FEST 2026"
    assert primera["responsable_nombre"] == "Ana Torres"
    assert primera["responsable_documento"] == "11111111"
    assert primera["paquete_nombre"] == "Pack FEST"
    assert primera["promocion_nombre"] == "Promoción 2026"
    assert primera["estado"] == "RECIBIDA"
    assert primera["equipos_total"] == 2
    assert primera["equipos_completos"] == 2
    assert primera["personas"] == 2
    assert primera["participaciones"] == 3
    assert primera["cupos_contratados"] == 3
    assert primera["cupos_pagados"] == 2
    assert primera["cupos_disponibles"] == 1
    assert primera["monto_pagado"] == 150.0

    segunda = por_id[str(escenario_operativo["inscripcion_2"].id)]

    assert segunda["equipos_total"] == 1
    assert segunda["equipos_completos"] == 0
    assert segunda["personas"] == 3
    assert segunda["participaciones"] == 1
    assert segunda["cupos_contratados"] == 2
    assert segunda["cupos_pagados"] == 1
    assert segunda["cupos_disponibles"] == 0
    assert segunda["monto_pagado"] == 50.0


@pytest.mark.django_db
def test_personas_y_participaciones_son_numeros_distintos(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: one person playing TWO disciplines
    WHEN:  GET the list
    THEN:  `personas` and `participaciones` are DIFFERENT numbers.
    """
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff))

    items = response.json()["data"]["items"]
    por_id = {item["id"]: item for item in items}
    primera = por_id[str(escenario_operativo["inscripcion_1"].id)]

    assert primera["personas"] == 2
    assert primera["participaciones"] == 3


# ── Filtros ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_filtro_por_estado(api_client, usuario_admin_staff, escenario_operativo):
    """GIVEN: two registrations in different states WHEN: filter THEN: one row."""
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(estado="VALIDADA"),
    )

    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["estado"] == "VALIDADA"


@pytest.mark.django_db
def test_filtros_combinados_se_aplican_con_and(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: two registrations of the SAME package and promotion
    WHEN:  two filters are combined
    THEN:  they narrow with AND.
    """
    base = make_list_query(
        paquete_id=str(escenario_operativo["paquete"].id),
        promocion_id=str(escenario_operativo["promocion"].id),
    )

    ambos = api_client.get(
        URL_LISTA, **make_auth_header(usuario_admin_staff), data=base
    )
    assert ambos.json()["data"]["total"] == 2

    base["estado"] = "RECIBIDA"
    uno = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff), data=base)
    assert uno.json()["data"]["total"] == 1


@pytest.mark.django_db
def test_filtro_por_responsable(api_client, usuario_admin_staff, escenario_operativo):
    """GIVEN: the responsible filter WHEN: applied THEN: only their rows."""
    responsable_id = str(escenario_operativo["inscripcion_1"].responsable_id)

    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(responsable_persona_id=responsable_id),
    )

    items = response.json()["data"]["items"]
    assert response.json()["data"]["total"] == 1
    assert items[0]["responsable_documento"] == "11111111"


@pytest.mark.django_db
def test_filtro_con_valor_fuera_del_vocabulario_responde_422(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a filter value outside the vocabulary
    WHEN:  GET the list
    THEN:  422 `INVALID_REQUEST` — never a 500 and never a silent filter.
    """
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(estado="NO_EXISTE"),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.django_db
def test_filtro_con_uuid_invalido_responde_422(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: a malformed id filter WHEN: applied THEN: 422 `INVALID_REQUEST`."""
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(paquete_id="no-es-un-uuid"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.django_db
def test_filtro_por_uuid_inexistente_devuelve_lista_vacia(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a well formed id that does NOT exist
    WHEN:  GET the list
    THEN:  an EMPTY list — not an error.
    """
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(paquete_id="11111111-1111-1111-1111-111111111111"),
    )

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []
    assert response.json()["data"]["total"] == 0


# ── Búsqueda ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_busqueda_por_nombre_del_responsable(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: a free-text term WHEN: searched THEN: the documented fields match."""
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(q="Torres"),
    )

    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["responsable_nombre"] == "Ana Torres"


@pytest.mark.django_db
def test_busqueda_por_documento_y_por_paquete(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: the documented searchable fields WHEN: searched THEN: they match."""
    por_documento = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(q="22222222"),
    )
    assert por_documento.json()["data"]["total"] == 1

    por_paquete = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(q="Pack FEST"),
    )
    assert por_paquete.json()["data"]["total"] == 2


@pytest.mark.django_db
def test_busqueda_con_metacaracteres_sql_es_segura(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a term with SQL metacharacters
    WHEN:  searched
    THEN:  it does not error and it does not match anything.
    """
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(q="'; DROP TABLE inscripciones; --"),
    )

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []


# ── Ordenamiento ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_ordenamiento_por_campo_permitido(
    api_client, usuario_admin_staff, escenario_paginacion
):
    """
    GIVEN: a scenario with many registrations
    WHEN:  the list is ordered by a whitelisted field
    THEN:  the order is honoured (ascending and descending).
    """
    headers = make_auth_header(usuario_admin_staff)

    ascendente = api_client.get(
        URL_LISTA,
        **headers,
        data=make_list_query(ordering="responsable", page_size=100),
    )
    nombres_asc = [item["responsable_nombre"] for item in ascendente.json()["data"]["items"]]

    descendente = api_client.get(
        URL_LISTA,
        **headers,
        data=make_list_query(ordering="-responsable", page_size=100),
    )
    nombres_desc = [
        item["responsable_nombre"] for item in descendente.json()["data"]["items"]
    ]

    assert nombres_asc == sorted(nombres_asc)
    assert nombres_desc == list(reversed(nombres_asc))


@pytest.mark.django_db
def test_ordenamiento_fuera_de_la_lista_blanca_responde_422(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an ordering field that is not whitelisted
    WHEN:  GET the list
    THEN:  422 `INVALID_REQUEST` — the raw text never reaches the queryset.
    """
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(ordering="created_at; DROP TABLE inscripciones"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


# ── Paginación ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_paginacion_por_defecto_es_25(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: no page_size WHEN: listed THEN: the default is 25."""
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    assert data["page"] == 1
    assert data["page_size"] == 25


@pytest.mark.django_db
def test_page_size_sobre_el_maximo_se_recorta(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: a page_size above the maximum WHEN: listed THEN: it is CLAMPED."""
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(page_size=5000),
    )

    assert response.json()["data"]["page_size"] == 100


@pytest.mark.django_db
def test_paginacion_es_de_base_1_y_total_pages_es_correcto(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: two matching rows
    WHEN:  the list is paginated with page_size 1
    THEN:  page 1 and page 2 hold one row each and total_pages is 2.
    """
    headers = make_auth_header(usuario_admin_staff)

    primera = api_client.get(
        URL_LISTA, **headers, data=make_list_query(page=1, page_size=1)
    ).json()["data"]
    segunda = api_client.get(
        URL_LISTA, **headers, data=make_list_query(page=2, page_size=1)
    ).json()["data"]

    assert len(primera["items"]) == 1
    assert len(segunda["items"]) == 1
    assert primera["items"][0]["id"] != segunda["items"][0]["id"]
    assert primera["total"] == 2
    assert primera["total_pages"] == 2


@pytest.mark.django_db
def test_pagina_fuera_del_rango_devuelve_lista_vacia(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a page beyond the last one
    WHEN:  listed
    THEN:  an EMPTY list — NOT a 404.
    """
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(page=99, page_size=1),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"] == []
    assert data["total"] == 2


# ── Drilldown ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_detalle_expone_los_seis_bloques(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a registration of the active event
    WHEN:  GET the drilldown
    THEN:  the teams, the participants, the purchases, the assignments, the
          acceptances and the balance are present.
    """
    response = api_client.get(
        URL_DETALLE.format(inscripcion_id=escenario_operativo["inscripcion_1"].id),
        **make_auth_header(usuario_admin_staff),
    )

    data = response.json()["data"]

    assert data["equipos"]
    assert data["participantes"]
    assert data["compras"]
    assert data["asignaciones"]
    assert data["aceptaciones"]
    assert data["saldo"] == {
        "contratados": 3,
        "pagados": 2,
        "asignados_pagados": 1,
        "disponibles_pagados": 1,
    }


@pytest.mark.django_db
def test_detalle_incluye_el_plantilla_de_cada_equipo(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: a team with two roster rows WHEN: the drilldown THEN: they travel."""
    response = api_client.get(
        URL_DETALLE.format(inscripcion_id=escenario_operativo["inscripcion_1"].id),
        **make_auth_header(usuario_admin_staff),
    )

    equipos = {equipo["nombre"]: equipo for equipo in response.json()["data"]["equipos"]}

    assert len(equipos["Los Tigres"]["participaciones"]) == 2
    assert equipos["Los Tigres"]["jugadores_registrados"] == 2
    assert equipos["Los Tigres"]["estado_roster"] == "COMPLETO"
    assert equipos["Las Panteras"]["estado_roster"] == "COMPLETO"
    assert equipos["Las Panteras"]["participaciones"][0]["disciplina_sigla"] == "VM"


@pytest.mark.django_db
def test_detalle_con_id_inexistente_responde_404(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an unknown id
    WHEN:  GET the drilldown
    THEN:  404 `RESOURCE_NOT_FOUND`.
    """
    response = api_client.get(
        URL_DETALLE.format(
            inscripcion_id="11111111-2222-3333-4444-555555555555"
        ),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.django_db
def test_detalle_de_otra_edicion_responde_404(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a registration of ANOTHER edition
    WHEN:  GET the drilldown
    THEN:  404 `RESOURCE_NOT_FOUND` — NOT 403: the surface never confirms the
          existence of a resource outside its scope.
    """
    response = api_client.get(
        URL_DETALLE.format(inscripcion_id=escenario_operativo["inscripcion_fuera"].id),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.django_db
def test_detalle_con_id_mal_formado_responde_404(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: a malformed id WHEN: the drilldown THEN: 404, never a 500."""
    response = api_client.get(
        URL_DETALLE.format(inscripcion_id="no-es-un-uuid"),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


# ── Sin fugas y sin mutaciones ───────────────────────────────────────────────


@pytest.mark.django_db
def test_respuesta_no_contiene_claves_prohibidas(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: the list and the drilldown
    WHEN:  they are inspected
    THEN:  no credential, no payment internals and no live QR travel.
    """
    headers = make_auth_header(usuario_admin_staff)

    lista = api_client.get(URL_LISTA, **headers).text.lower()
    detalle = api_client.get(
        URL_DETALLE.format(inscripcion_id=escenario_operativo["inscripcion_1"].id),
        **headers,
    ).text.lower()

    for prohibido in make_forbidden_keys():
        assert prohibido not in lista
        assert prohibido not in detalle


@pytest.mark.django_db
def test_los_endpoints_de_lectura_no_mutan_nada(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a snapshot of every table the surface touches
    WHEN:  every endpoint is called
    THEN:  nothing changed — the administrative area is READ-ONLY.
    """
    from modules.salesianos_fest.domain.models import (
        AceptacionInscripcion,
        AcreditacionEvento,
        AsignacionCupo,
        CompraInscripcion,
        ControlAcceso,
        Equipo,
        Inscripcion,
        InscripcionPersona,
        Participacion,
    )
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import OrdenPago, TransaccionPago

    def _snapshot():
        return {
            "inscripciones": Inscripcion.objects.count(),
            "inscripciones_personas": InscripcionPersona.objects.count(),
            "equipos": Equipo.objects.count(),
            "participaciones": Participacion.objects.count(),
            "compras": Compra.objects.count(),
            "compras_inscripcion": CompraInscripcion.objects.count(),
            "asignaciones": AsignacionCupo.objects.count(),
            "aceptaciones": AceptacionInscripcion.objects.count(),
            "acreditaciones": AcreditacionEvento.objects.count(),
            "controles": ControlAcceso.objects.count(),
            "ordenes": OrdenPago.objects.count(),
            "transacciones": TransaccionPago.objects.count(),
            "estados_equipos": list(
                Equipo.objects.order_by("id").values_list("id", "estado")
            ),
        }

    antes = _snapshot()

    headers = make_auth_header(usuario_admin_staff)
    api_client.get(URL_LISTA, **headers)
    api_client.get(
        URL_DETALLE.format(inscripcion_id=escenario_operativo["inscripcion_1"].id),
        **headers,
    )

    assert _snapshot() == antes
