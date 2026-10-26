"""
Integration tests — the PUBLIC read surface of the bracket (Phase 3).

The HTTP client is `ninja_extra.testing.TestAsyncClient`: the controllers are
async (`contract/django-app-architecture-contract.md` §2.1).

What this file proves:

1. the statuses and the STANDARD WRAPPER of every read,
2. the filters (discipline, category, state),
3. the EMPTY and the PARTIAL brackets (nothing is invented),
4. the AUTHORIZED SCOPE: a competition of an edition that is not active is
   invisible to the public reader — 404, never a 403 and never a leak,
5. the public surface is READ-ONLY: it exposes no write at all.
"""
import pytest

URL_COMPETENCIAS = "/competencias"


def _cuerpo(response):
    """Return the body of the standard wrapper."""
    return response.json()


# ── Envoltorio y estados ────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_devuelve_el_envoltorio_estandar(
    cliente_api_competencias,
    competencia,
    competencia_equipo,
    encuentro,
):
    """
    GIVEN: a competition of an authorized edition
    WHEN: the public reader asks for the list
    THEN: 200 with the standard wrapper and the row of the competition
    """
    response = await cliente_api_competencias.get(URL_COMPETENCIAS)

    assert response.status_code == 200
    cuerpo = _cuerpo(response)
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert isinstance(cuerpo["data"], list)

    fila = cuerpo["data"][0]
    assert fila["id"] == str(competencia.id)
    assert fila["nombre"] == "Eliminatoria F7"
    assert fila["estado"] == "PLANIFICADA"
    assert fila["total_equipos"] == 1
    assert fila["total_encuentros"] == 1


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_de_un_concurso_desconocido_es_404(
    cliente_api_competencias,
):
    """
    GIVEN: an id that does not exist
    WHEN: the public reader asks for its detail
    THEN: 404 with the stable code of the catalog
    """
    response = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    cuerpo = _cuerpo(response)
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "COMPETENCIA_NOT_FOUND"


# ── Alcance autorizado ──────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_solo_muestra_los_eventos_autorizados(
    cliente_api_competencias,
    competencia,
    competencia_fuera_de_alcance,
):
    """
    GIVEN: a competition of an authorized edition and another one of an
    edition that is NOT active
    WHEN: the public reader asks for the list
    THEN: only the competition of the authorized edition is returned
    """
    response = await cliente_api_competencias.get(URL_COMPETENCIAS)

    assert response.status_code == 200
    ids = [fila["id"] for fila in _cuerpo(response)["data"]]
    assert str(competencia.id) in ids
    assert str(competencia_fuera_de_alcance.id) not in ids


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_fuera_del_alcance_es_404(
    cliente_api_competencias,
    competencia_fuera_de_alcance,
):
    """
    GIVEN: a competition of an edition the reader is NOT authorized for
    WHEN: the public reader asks for its detail or for its bracket
    THEN: 404 — the surface never confirms the existence of a resource the
    reader cannot see
    """
    detalle = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}/{competencia_fuera_de_alcance.id}"
    )
    cuadro = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}/{competencia_fuera_de_alcance.id}/cuadro"
    )

    assert detalle.status_code == 404
    assert cuadro.status_code == 404
    assert _cuerpo(detalle)["error"]["code"] == "COMPETENCIA_NOT_FOUND"
    assert _cuerpo(cuadro)["error"]["code"] == "COMPETENCIA_NOT_FOUND"


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_de_encuentros_ignora_el_alcance(
    cliente_api_competencias,
    encuentro,
    ronda,
):
    """
    GIVEN: an encounter of an authorized edition
    WHEN: the public reader asks for the encounters
    THEN: only the encounters of the authorized editions are returned
    """
    response = await cliente_api_competencias.get(f"{URL_COMPETENCIAS}/encuentros")

    assert response.status_code == 200
    ids = [fila["id"] for fila in _cuerpo(response)["data"]]
    assert str(encuentro.id) in ids
    assert all(fila["ronda_id"] == str(ronda.id) for fila in _cuerpo(response)["data"])


# ── Filtros ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_filtra_por_disciplina(
    cliente_api_competencias,
    competencia,
    disciplina_competencia_2,
):
    """
    GIVEN: a competition of one discipline
    WHEN: the public reader filters by ANOTHER discipline
    THEN: the list is empty (the filter is applied on the server)
    """
    response = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}?disciplina_id={disciplina_competencia_2.id}"
    )

    assert response.status_code == 200
    assert _cuerpo(response)["data"] == []


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_filtra_por_categoria(
    cliente_api_competencias,
    competencia,
    categoria_competencia_ajena,
):
    """
    GIVEN: a competition of one category
    WHEN: the public reader filters by ANOTHER category
    THEN: the list is empty
    """
    response = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}?categoria_id={categoria_competencia_ajena.id}"
    )

    assert response.status_code == 200
    assert _cuerpo(response)["data"] == []


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_filtra_por_estado(
    cliente_api_competencias,
    competencia,
):
    """
    GIVEN: a planned competition
    WHEN: the public reader filters by another state
    THEN: the list is empty, and filtering by its own state returns it
    """
    vacio = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}?estado=FINALIZADA"
    )
    propio = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}?estado=PLANIFICADA"
    )

    assert _cuerpo(vacio)["data"] == []
    assert [f["id"] for f in _cuerpo(propio)["data"]] == [str(competencia.id)]


# ── Cuadro vacío y cuadro parcial ───────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_de_un_cuadro_vacio(
    cliente_api_competencias,
    competencia_2,
):
    """
    GIVEN: a competition WITHOUT rounds
    WHEN: the public reader asks for its bracket
    THEN: 200 with an EMPTY bracket — nothing is invented
    """
    response = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}/{competencia_2.id}/cuadro"
    )

    assert response.status_code == 200
    cuadro = _cuerpo(response)["data"]
    assert cuadro["rondas"] == []
    assert cuadro["total_equipos"] == 0
    assert cuadro["nombre"] == "Eliminatoria F7 B"


@pytest.mark.django_db(transaction=True)
async def test_lectura_publica_de_un_cuadro_parcial(
    cliente_api_competencias,
    competencia,
    ronda,
    encuentro,
    competencia_equipo,
):
    """
    GIVEN: an encounter with ONE participant
    WHEN: the public reader asks for its bracket
    THEN: the empty slot stays empty and no participant is invented
    """
    response = await cliente_api_competencias.get(
        f"{URL_COMPETENCIAS}/{competencia.id}/cuadro"
    )

    assert response.status_code == 200
    cuadro = _cuerpo(response)["data"]
    assert len(cuadro["rondas"]) == 1

    columna = cuadro["rondas"][0]
    assert columna["etiqueta"] == "Cuartos de final"
    assert len(columna["encuentros"]) == 1

    fila = columna["encuentros"][0]
    assert fila["participante_1_id"] == str(competencia_equipo.id)
    assert fila["participante_2_id"] is None
    assert fila["participante_2_nombre"] is None
    assert fila["ganador_id"] is None
    assert fila["inicio_programado"] is None
