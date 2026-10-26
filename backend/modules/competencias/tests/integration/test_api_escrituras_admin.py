"""
Integration tests — the ADMINISTRATIVE write surface of the bracket (Phase 3).

The HTTP client is `ninja_extra.testing.TestAsyncClient`: the controllers are
async (`contract/django-app-architecture-contract.md` §2.1).

What this file proves:

1. the authorization of the WRITES: 401 without a token and 403 for an
   authenticated non administrator,
2. the statuses of the writes: 201 to create, 200 to mutate and 204 to
   delete,
3. the error envelope of the domain: 409 for a conflict, 422 for an invalid
   request and the STABLE code of the public catalog,
4. the optimistic lock: a stale `expected_version` fails with 409
   `RESOURCE_CHANGED` and NOTHING is written,
5. the commands of the bracket: the result, the advance and the correction.
"""
import pytest
from asgiref.sync import sync_to_async

from modules.competencias.domain.models import Competencia, Encuentro

URL_ADMIN = "/administracion/competencias"
URL_ENCUENTROS = f"{URL_ADMIN}/encuentros"

MOTIVO_HORARIO = "Programacion del encuentro del cuadro de pruebas"
MOTIVO_PARTICIPANTES = "Asignacion de los participantes del encuentro"
MOTIVO_RESULTADO = "Registro del resultado del encuentro"
MOTIVO_ENLACE = "Vinculacion del encuentro con la siguiente ronda"
MOTIVO_AVANCE = "Propagacion del ganador al encuentro enlazado"
MOTIVO_CORRECCION = "Correccion administrativa del ganador del encuentro"


def _cuerpo(response):
    """Return the body of the standard wrapper."""
    return response.json()


def _leer_version(encuentro_id) -> int:
    """Return the current version of an encounter (sync, for `sync_to_async`)."""
    return Encuentro.objects.get(id=encuentro_id).version


def _leer_existe(nombre) -> bool:
    """Return whether a competition with that name exists (sync)."""
    return Competencia.objects.filter(nombre=nombre).exists()


def _leer_encuentro(encuentro_id) -> dict:
    """Return the state of an encounter (sync, for `sync_to_async`)."""
    fila = Encuentro.objects.get(id=encuentro_id)
    return {
        "estado": fila.estado,
        "ganador_id": str(fila.ganador_id) if fila.ganador_id else None,
        "participante_1_id": (
            str(fila.participante_1_id) if fila.participante_1_id else None
        ),
    }


def _leer_nombre(competencia_id) -> str:
    """Return the name of a competition (sync, for `sync_to_async`)."""
    return Competencia.objects.get(id=competencia_id).nombre


async def _version(encuentro_id) -> int:
    """Return the current version of an encounter (the writes are committed)."""
    return await sync_to_async(_leer_version)(encuentro_id)


async def _estado_de(encuentro_id) -> dict:
    """Return the state of an encounter (the writes are committed)."""
    return await sync_to_async(_leer_encuentro)(encuentro_id)


async def _nombre_de_competencia(competencia_id) -> str:
    """Return the name of a competition (the writes are committed)."""
    return await sync_to_async(_leer_nombre)(competencia_id)


async def _existe_competencia(nombre) -> bool:
    """Return whether a competition with that name exists."""
    return await sync_to_async(_leer_existe)(nombre)


async def _poner_en_curso(cliente, encuentro_id):
    """Move an encounter to `EN_CURSO` through the HTTP surface."""
    programado = await cliente.patch(
        f"{URL_ENCUENTROS}/{encuentro_id}/estado",
        json={"estado": "PROGRAMADO", "expected_version": await _version(encuentro_id)},
    )
    assert programado.status_code == 200

    en_curso = await cliente.patch(
        f"{URL_ENCUENTROS}/{encuentro_id}/estado",
        json={"estado": "EN_CURSO", "expected_version": await _version(encuentro_id)},
    )
    assert en_curso.status_code == 200
    return en_curso


# ── Autorización de las escrituras ──────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_escritura_admin_sin_token_es_401(
    cliente_api_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """
    GIVEN: an anonymous caller
    WHEN: it tries to create a competition
    THEN: 401 `AUTHENTICATION_REQUIRED` and NOTHING is written
    """
    response = await cliente_api_competencias.post(
        URL_ADMIN,
        json={
            "evento_id": str(evento_competencia.id),
            "disciplina_id": str(disciplina_competencia.id),
            "categoria_id": str(categoria_competencia.id),
            "nombre": "Eliminatoria F7",
            "fecha": "2026-11-16",
        },
    )

    assert response.status_code == 401
    assert _cuerpo(response)["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert not await _existe_competencia("Eliminatoria F7")

@pytest.mark.django_db(transaction=True)
async def test_escritura_admin_de_un_usuario_normal_es_403(
    cliente_no_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN: it tries to create a competition
    THEN: 403 `ACTION_NOT_ALLOWED` and NOTHING is written
    """
    response = await cliente_no_admin_competencias.post(
        URL_ADMIN,
        json={
            "evento_id": str(evento_competencia.id),
            "disciplina_id": str(disciplina_competencia.id),
            "categoria_id": str(categoria_competencia.id),
            "nombre": "Eliminatoria F7",
            "fecha": "2026-11-16",
        },
    )

    assert response.status_code == 403
    assert _cuerpo(response)["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert not await _existe_competencia("Eliminatoria F7")


# ── Ciclo de vida de la competencia ──────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_admin_crea_una_competencia_201(
    cliente_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """
    GIVEN: an administrator
    WHEN: it creates a competition
    THEN: 201 with the row of the new competition
    """
    response = await cliente_admin_competencias.post(
        URL_ADMIN,
        json={
            "evento_id": str(evento_competencia.id),
            "disciplina_id": str(disciplina_competencia.id),
            "categoria_id": str(categoria_competencia.id),
            "nombre": "Eliminatoria F7",
            "fecha": "2026-11-16",
        },
    )

    assert response.status_code == 201
    cuerpo = _cuerpo(response)
    assert cuerpo["success"] is True
    assert cuerpo["data"]["nombre"] == "Eliminatoria F7"
    assert cuerpo["data"]["estado"] == "PLANIFICADA"
    assert cuerpo["data"]["version"] == 1


@pytest.mark.django_db(transaction=True)
async def test_admin_no_puede_crear_una_competencia_duplicada_409(
    cliente_admin_competencias,
    competencia,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """
    GIVEN: a competition with the same identity
    WHEN: the administrator creates another one with the same identity
    THEN: 409 `COMPETENCIA_DUPLICADA`
    """
    response = await cliente_admin_competencias.post(
        URL_ADMIN,
        json={
            "evento_id": str(evento_competencia.id),
            "disciplina_id": str(disciplina_competencia.id),
            "categoria_id": str(categoria_competencia.id),
            "nombre": "Eliminatoria F7",
            "fecha": "2026-11-16",
        },
    )

    assert response.status_code == 409
    assert _cuerpo(response)["error"]["code"] == "COMPETENCIA_DUPLICADA"


@pytest.mark.django_db(transaction=True)
async def test_admin_actualiza_una_competencia_200(
    cliente_admin_competencias,
    competencia,
):
    """
    GIVEN: a planned competition
    WHEN: the administrator renames it with its current version
    THEN: 200 with the new name and a new version
    """
    response = await cliente_admin_competencias.patch(
        f"{URL_ADMIN}/{competencia.id}",
        json={
            "nombre": "Eliminatoria F7 2026",
            "expected_version": competencia.version,
        },
    )

    assert response.status_code == 200
    cuerpo = _cuerpo(response)
    assert cuerpo["data"]["nombre"] == "Eliminatoria F7 2026"
    assert cuerpo["data"]["version"] == competencia.version + 1


@pytest.mark.django_db(transaction=True)
async def test_admin_no_puede_actualizar_con_una_version_obsoleta_409(
    cliente_admin_competencias,
    competencia,
):
    """
    GIVEN: a competition whose version moved
    WHEN: the administrator edits the stale version
    THEN: 409 `RESOURCE_CHANGED` and the name does NOT change
    """
    response = await cliente_admin_competencias.patch(
        f"{URL_ADMIN}/{competencia.id}",
        json={
            "nombre": "Eliminatoria F7 2026",
            "expected_version": competencia.version + 5,
        },
    )

    assert response.status_code == 409
    assert _cuerpo(response)["error"]["code"] == "RESOURCE_CHANGED"
    assert await _nombre_de_competencia(competencia.id) == "Eliminatoria F7"


@pytest.mark.django_db(transaction=True)
async def test_admin_elimina_una_competencia_204(
    cliente_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """
    GIVEN: a competition that was never used
    WHEN: the administrator deletes it
    THEN: 204 with an empty body and the row is gone
    """
    creada = await cliente_admin_competencias.post(
        URL_ADMIN,
        json={
            "evento_id": str(evento_competencia.id),
            "disciplina_id": str(disciplina_competencia.id),
            "categoria_id": str(categoria_competencia.id),
            "nombre": "Eliminatoria descartable",
            "fecha": "2026-11-16",
        },
    )
    assert creada.status_code == 201
    competencia_id = _cuerpo(creada)["data"]["id"]

    response = await cliente_admin_competencias.delete(f"{URL_ADMIN}/{competencia_id}")

    assert response.status_code == 204
    assert not await _existe_competencia("Eliminatoria descartable")


@pytest.mark.django_db(transaction=True)
async def test_admin_no_puede_eliminar_una_competencia_en_uso_409(
    cliente_admin_competencias,
    competencia,
    ronda,
):
    """
    GIVEN: a competition that already has rounds
    WHEN: the administrator deletes it
    THEN: 409 `DELETE_NOT_ALLOWED` — the history is kept
    """
    response = await cliente_admin_competencias.delete(f"{URL_ADMIN}/{competencia.id}")

    assert response.status_code == 409
    assert _cuerpo(response)["error"]["code"] == "DELETE_NOT_ALLOWED"
    assert await _existe_competencia("Eliminatoria F7")


# ── Equipos, rondas y encuentros ────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_admin_registra_un_equipo_201(
    cliente_admin_competencias,
    competencia,
    equipo_competencia_2,
):
    """
    GIVEN: an eligible team
    WHEN: the administrator registers it with its MANUAL order
    THEN: 201 with the participation
    """
    response = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia.id}/equipos",
        json={"equipo_id": str(equipo_competencia_2.id), "orden": 2},
    )

    assert response.status_code == 201
    cuerpo = _cuerpo(response)
    assert cuerpo["data"]["equipo_id"] == str(equipo_competencia_2.id)
    assert cuerpo["data"]["orden"] == 2
    assert cuerpo["data"]["estado"] == "ACTIVO"


@pytest.mark.django_db(transaction=True)
async def test_admin_no_puede_registrar_un_equipo_ajeno_409(
    cliente_admin_competencias,
    competencia,
    equipo_competencia_evento_ajeno,
):
    """
    GIVEN: a team of ANOTHER event
    WHEN: the administrator registers it
    THEN: 409 `EQUIPO_NO_ELEGIBLE`
    """
    response = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia.id}/equipos",
        json={"equipo_id": str(equipo_competencia_evento_ajeno.id), "orden": 2},
    )

    assert response.status_code == 409
    assert _cuerpo(response)["error"]["code"] == "EQUIPO_NO_ELEGIBLE"


@pytest.mark.django_db(transaction=True)
async def test_admin_crea_una_ronda_201(
    cliente_admin_competencias,
    competencia,
):
    """
    GIVEN: a competition
    WHEN: the administrator creates a round
    THEN: 201 with the round
    """
    response = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia.id}/rondas",
        json={"etiqueta": "Octavos de final", "orden": 1},
    )

    assert response.status_code == 201
    cuerpo = _cuerpo(response)
    assert cuerpo["data"]["etiqueta"] == "Octavos de final"
    assert cuerpo["data"]["estado"] == "ACTIVA"


@pytest.mark.django_db(transaction=True)
async def test_admin_no_puede_crear_una_ronda_duplicada_409(
    cliente_admin_competencias,
    competencia,
    ronda,
):
    """
    GIVEN: a round with a label
    WHEN: the administrator creates another one with the same label
    THEN: 409 `COMPETENCIA_DUPLICADA`
    """
    response = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia.id}/rondas",
        json={"etiqueta": "Cuartos de final", "orden": 9},
    )

    assert response.status_code == 409
    assert _cuerpo(response)["error"]["code"] == "COMPETENCIA_DUPLICADA"


@pytest.mark.django_db(transaction=True)
async def test_admin_crea_un_encuentro_201(
    cliente_admin_competencias,
    competencia,
    ronda,
):
    """
    GIVEN: a round
    WHEN: the administrator creates an encounter WITHOUT participants
    THEN: 201 — an empty bracket is a valid bracket
    """
    response = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia.id}/encuentros",
        json={"ronda_id": str(ronda.id), "orden": 7},
    )

    assert response.status_code == 201
    cuerpo = _cuerpo(response)
    assert cuerpo["data"]["orden"] == 7
    assert cuerpo["data"]["participante_1_id"] is None
    assert cuerpo["data"]["participante_2_id"] is None
    assert cuerpo["data"]["estado"] == "BORRADOR"


@pytest.mark.django_db(transaction=True)
async def test_admin_no_puede_mover_un_participante_sin_motivo_422(
    cliente_admin_competencias,
    competencia,
    encuentro,
    competencia_equipo,
    equipo_competencia_2,
):
    """
    GIVEN: an encounter
    WHEN: the administrator moves a team without the audited motive
    THEN: 422 `REASON_REQUIRED` and the slot does NOT change
    """
    response = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{encuentro.id}/participantes",
        json={
            "participante_1_id": str(equipo_competencia_2.id),
            "expected_version": encuentro.version,
        },
    )

    assert response.status_code == 422
    assert _cuerpo(response)["error"]["code"] == "REASON_REQUIRED"
    estado = await _estado_de(encuentro.id)
    assert estado["participante_1_id"] == str(competencia_equipo.id)


# ── Resultado, avance y corrección ──────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_admin_registra_el_resultado_200(
    cliente_admin_competencias,
    competencia,
    encuentro,
    competencia_equipo,
):
    """
    GIVEN: an encounter that is in course
    WHEN: the administrator registers the winner with optional scores
    THEN: 200 with the finalized encounter
    """
    await _poner_en_curso(cliente_admin_competencias, encuentro.id)

    response = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/resultado",
        json={
            "ganador_id": str(competencia_equipo.id),
            "puntaje_1": 3,
            "puntaje_2": 0,
            "motivo": MOTIVO_RESULTADO,
            "expected_version": await _version(encuentro.id),
        },
    )

    assert response.status_code == 200
    cuerpo = _cuerpo(response)
    assert cuerpo["data"]["estado"] == "FINALIZADO"
    assert cuerpo["data"]["ganador_id"] == str(competencia_equipo.id)
    assert cuerpo["data"]["puntaje_1"] == 3
    assert cuerpo["data"]["puntaje_2"] == 0


@pytest.mark.django_db(transaction=True)
async def test_admin_no_puede_registrar_un_ganador_que_no_juega_422(
    cliente_admin_competencias,
    competencia,
    encuentro,
    competencia_equipo,
    equipo_competencia_2,
):
    """
    GIVEN: an encounter that is in course
    WHEN: the administrator declares a winner that does not occupy a slot
    THEN: 422 `INVALID_WINNER` and the encounter does NOT change
    """
    await _poner_en_curso(cliente_admin_competencias, encuentro.id)

    response = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/resultado",
        json={
            "ganador_id": str(equipo_competencia_2.id),
            "motivo": MOTIVO_RESULTADO,
            "expected_version": await _version(encuentro.id),
        },
    )

    assert response.status_code == 422
    assert _cuerpo(response)["error"]["code"] == "INVALID_WINNER"
    estado = await _estado_de(encuentro.id)
    assert estado["estado"] == "EN_CURSO"
    assert estado["ganador_id"] is None


@pytest.mark.django_db(transaction=True)
async def test_admin_propaga_el_ganador_al_siguiente_encuentro(
    cliente_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    encuentro,
    competencia_equipo,
):
    """
    GIVEN: a finalized encounter linked to the next one
    WHEN: the administrator previews and confirms the advance
    THEN: the preview proposes it, the confirmation places the winner ONCE
    """
    destino = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia.id}/encuentros",
        json={"ronda_id": str(ronda_2.id), "orden": 1},
    )
    assert destino.status_code == 201
    destino_id = _cuerpo(destino)["data"]["id"]

    enlace = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/enlace",
        json={
            "siguiente_encuentro_id": destino_id,
            "slot_destino": "PARTICIPANTE_1",
            "motivo": MOTIVO_ENLACE,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert enlace.status_code == 200

    await _poner_en_curso(cliente_admin_competencias, encuentro.id)

    resultado = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/resultado",
        json={
            "ganador_id": str(competencia_equipo.id),
            "motivo": MOTIVO_RESULTADO,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert resultado.status_code == 200

    preview = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/avance/preview"
    )
    assert preview.status_code == 200
    cuerpo_preview = _cuerpo(preview)["data"]
    assert cuerpo_preview["siguiente_encuentro_id"] == destino_id
    assert cuerpo_preview["slot_destino"] == "PARTICIPANTE_1"
    assert cuerpo_preview["ya_propagado"] is False

    confirmacion = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/avance/confirm",
        json={
            "motivo": MOTIVO_AVANCE,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert confirmacion.status_code == 200
    cuerpo_confirmacion = _cuerpo(confirmacion)["data"]
    assert cuerpo_confirmacion["ya_aplicado"] is False
    assert cuerpo_confirmacion["destino"]["participante_1_id"] == str(
        competencia_equipo.id
    )

    # A REPLAY of the same command writes nothing: it is idempotent.
    replay = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/avance/confirm",
        json={
            "motivo": MOTIVO_AVANCE,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert replay.status_code == 200
    assert _cuerpo(replay)["data"]["ya_aplicado"] is True


@pytest.mark.django_db(transaction=True)
async def test_admin_corrige_el_ganador_con_impacto_auditado(
    cliente_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    encuentro,
    competencia_equipo,
    equipo_competencia_2,
):
    """
    GIVEN: a finalized encounter whose winner was propagated
    WHEN: the administrator previews and confirms the correction
    THEN: the preview shows the impact and the correction replaces the
    propagated participant (the change is audited)
    """
    incorporado = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia.id}/equipos",
        json={"equipo_id": str(equipo_competencia_2.id), "orden": 2},
    )
    assert incorporado.status_code == 201
    equipo_2_id = _cuerpo(incorporado)["data"]["id"]

    participantes = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{encuentro.id}/participantes",
        json={
            "participante_1_id": str(competencia_equipo.id),
            "participante_2_id": equipo_2_id,
            "motivo": MOTIVO_PARTICIPANTES,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert participantes.status_code == 200

    destino = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia.id}/encuentros",
        json={"ronda_id": str(ronda_2.id), "orden": 1},
    )
    destino_id = _cuerpo(destino)["data"]["id"]

    enlace = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/enlace",
        json={
            "siguiente_encuentro_id": destino_id,
            "slot_destino": "PARTICIPANTE_1",
            "motivo": MOTIVO_ENLACE,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert enlace.status_code == 200

    await _poner_en_curso(cliente_admin_competencias, encuentro.id)

    resultado = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/resultado",
        json={
            "ganador_id": str(competencia_equipo.id),
            "motivo": MOTIVO_RESULTADO,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert resultado.status_code == 200

    advance = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/avance/confirm",
        json={
            "motivo": MOTIVO_AVANCE,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert advance.status_code == 200

    preview = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/correccion/preview",
        json={"ganador_id": equipo_2_id},
    )
    assert preview.status_code == 200
    cuerpo_preview = _cuerpo(preview)["data"]
    assert cuerpo_preview["ganador_actual_id"] == str(competencia_equipo.id)
    assert cuerpo_preview["ganador_nuevo_id"] == equipo_2_id
    assert cuerpo_preview["requiere_override"] is False
    assert len(cuerpo_preview["descendientes"]) == 1

    correccion = await cliente_admin_competencias.post(
        f"{URL_ENCUENTROS}/{encuentro.id}/correccion/confirm",
        json={
            "ganador_id": equipo_2_id,
            "motivo": MOTIVO_CORRECCION,
            "expected_version": await _version(encuentro.id),
        },
    )
    assert correccion.status_code == 200
    cuerpo_correccion = _cuerpo(correccion)["data"]
    assert cuerpo_correccion["ganador_id"] == equipo_2_id
    assert cuerpo_correccion["requirio_override"] is False
    assert cuerpo_correccion["descendientes_afectados"] == 1
