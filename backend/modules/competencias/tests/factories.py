"""
Payload factories of the competencias module.

Pure functions that return `dict` payloads — NO database, NO pytest
(contract/TEST_ARCHITECTURE_CONTRACT.md §4). Import them directly:

    from modules.competencias.tests.factories import make_competencia_payload

Two families live here:

- the payloads of the DOMAIN (the ones the core services consume),
- the payloads of the HTTP SURFACE (the bodies that travel through the
  controllers). The bodies are never written inline in a test.
"""
import math
from datetime import date, datetime, timedelta

from django.utils import timezone

FECHA_COMPETENCIA = date(2026, 11, 16)
# `make_aware` REQUIRES a naive datetime: it attaches the current timezone.
HORA_INICIO = timezone.make_aware(datetime(2026, 11, 16, 10, 0))  # noqa: DTZ001
HORA_FIN = timezone.make_aware(datetime(2026, 11, 16, 11, 0))  # noqa: DTZ001
HORA_INICIO_TARDE = timezone.make_aware(datetime(2026, 11, 16, 14, 0))  # noqa: DTZ001

ETIQUETAS_RONDAS = ("Primera ronda", "Segunda ronda", "Tercera ronda")


def make_competencia_payload(
    evento_id,
    disciplina_id,
    categoria_id,
    nombre="Eliminatoria F7",
    fecha=FECHA_COMPETENCIA,
    estado="PLANIFICADA",
    **extra,
):
    """Payload of a competition (event + discipline + category + name)."""
    payload = {
        "evento_id": str(evento_id),
        "disciplina_id": str(disciplina_id),
        "categoria_id": str(categoria_id),
        "nombre": nombre,
        "fecha": fecha,
        "estado": estado,
    }
    payload.update(extra)
    return payload


def make_competencia_equipo_payload(
    competencia_id,
    equipo_id,
    orden=1,
    estado="ACTIVO",
    **extra,
):
    """Payload of a team registered in the bracket of a competition."""
    payload = {
        "competencia_id": str(competencia_id),
        "equipo_id": str(equipo_id),
        "orden": orden,
        "estado": estado,
    }
    payload.update(extra)
    return payload


def make_ronda_payload(
    competencia_id,
    etiqueta="Cuartos de final",
    orden=1,
    estado="ACTIVA",
    **extra,
):
    """Payload of a round of the bracket."""
    payload = {
        "competencia_id": str(competencia_id),
        "etiqueta": etiqueta,
        "orden": orden,
        "estado": estado,
    }
    payload.update(extra)
    return payload


def make_encuentro_payload(
    ronda_id,
    orden=1,
    participante_1_id=None,
    participante_2_id=None,
    inicio_programado=None,
    fin_programado=None,
    estado="BORRADOR",
    es_bye=False,
    **extra,
):
    """Payload of an encounter — every slot/schedule field is optional."""
    payload = {
        "ronda_id": str(ronda_id),
        "orden": orden,
        "participante_1_id": (
            str(participante_1_id) if participante_1_id is not None else None
        ),
        "participante_2_id": (
            str(participante_2_id) if participante_2_id is not None else None
        ),
        "inicio_programado": inicio_programado,
        "fin_programado": fin_programado,
        "estado": estado,
        "es_bye": es_bye,
    }
    payload.update(extra)
    return payload


def make_horario_payload(inicio=HORA_INICIO, duracion_minutos=60):
    """Return the `(inicio, fin)` pair of a valid scheduled interval."""
    return inicio, inicio + timedelta(minutes=duracion_minutos)


def make_horario_tarde_payload(duracion_minutos=60):
    """Return the `(inicio, fin)` pair of an afternoon interval.

    It lets the tests schedule two encounters of the same team without
    overlapping them (the overlap check is portable between competitions).
    """
    return make_horario_payload(
        inicio=HORA_INICIO_TARDE,
        duracion_minutos=duracion_minutos,
    )


def make_bracket_parcial_payload(num_equipos: int) -> dict:
    """Manual bracket plan of `num_equipos` teams.

    The domain NEVER generates a bracket by itself: this factory only
    describes what an administrator would type by hand — the rounds, the
    encounters, the slots and the MANUAL byes — so the tests can prove that
    the system never invents a participant nor chooses a bye.

    The participants are POSITIONS of the team list: `None` means the slot
    stays empty (a partial bracket) and `es_bye` marks the encounter that the
    administrator reserved as a bye.
    """
    rondas = []
    restantes = num_equipos
    while True:
        encuentros_ronda = math.ceil(restantes / 2)
        encuentros = []
        if not rondas:
            pares = num_equipos // 2
            for orden in range(1, pares + 1):
                encuentros.append(
                    {
                        "orden": orden,
                        "participante_1": (orden - 1) * 2,
                        "participante_2": (orden - 1) * 2 + 1,
                        "es_bye": False,
                    }
                )
            if num_equipos % 2 == 1:
                # The administrator DECIDES which team gets the bye.
                encuentros.append(
                    {
                        "orden": pares + 1,
                        "participante_1": num_equipos - 1,
                        "participante_2": None,
                        "es_bye": True,
                    }
                )
        else:
            for orden in range(1, encuentros_ronda + 1):
                encuentros.append(
                    {
                        "orden": orden,
                        "participante_1": None,
                        "participante_2": None,
                        "es_bye": False,
                    }
                )
        rondas.append(
            {
                "etiqueta": (
                    ETIQUETAS_RONDAS[len(rondas)]
                    if len(rondas) < len(ETIQUETAS_RONDAS)
                    else f"Ronda {len(rondas) + 1}"
                ),
                "orden": len(rondas) + 1,
                "encuentros": encuentros,
            }
        )
        restantes = encuentros_ronda
        if restantes <= 1:
            break
    return {"rondas": rondas}


# ── Payloads of the HTTP surface (E2E) ───────────────────────────────────────
#
# The bodies that travel through the controllers. They are ISO strings (the
# wire format) and they never live inline in a test
# (contract/TEST_ARCHITECTURE_CONTRACT.md §4).

#: The competition happens on ONE day: every schedule of its bracket shares
#: it. The offset is the one of `America/Lima` (UTC-5, no daylight saving).
FECHA_COMPETENCIA_ISO = "2026-11-16"
HORA_INICIO_ISO = "2026-11-16T10:00:00-05:00"
HORA_FIN_ISO = "2026-11-16T11:00:00-05:00"
HORA_INICIO_TARDE_ISO = "2026-11-16T14:00:00-05:00"
HORA_FIN_TARDE_ISO = "2026-11-16T15:00:00-05:00"
#: A slot that OVERLAPS `HORA_INICIO_ISO`/`HORA_FIN_ISO`: the same team
#: cannot play it (the intervals are semi-open, so it overlaps).
HORA_INICIO_SOLAPADO_ISO = "2026-11-16T10:30:00-05:00"
HORA_FIN_SOLAPADO_ISO = "2026-11-16T11:30:00-05:00"
#: A slot that only TOUCHES `HORA_FIN_ISO`: it starts when the other ends, so
#: it does NOT overlap.
HORA_INICIO_ENCADENADO_ISO = "2026-11-16T11:00:00-05:00"
HORA_FIN_ENCADENADO_ISO = "2026-11-16T12:00:00-05:00"

#: The audited motives of the protected mutations (the domain demands 5..500
#: characters for them).
MOTIVO_BYE = "Pase manual asignado por el administrador del cuadro"
MOTIVO_PROGRAMACION = "Programacion del encuentro del cuadro de pruebas"
MOTIVO_PARTICIPANTES = "Asignacion de los participantes del encuentro"
MOTIVO_ENLACE = "Vinculacion del encuentro con la siguiente ronda"
MOTIVO_RESULTADO = "Registro del resultado del encuentro"
MOTIVO_AVANCE = "Propagacion del ganador al encuentro enlazado"
MOTIVO_CORRECCION = "Correccion administrativa del ganador del encuentro"
MOTIVO_CANCELACION = "Cancelacion de la competencia tras el rollback del despliegue"


def make_competencia_create_http_payload(
    evento_id,
    disciplina_id,
    categoria_id,
    nombre="Eliminatoria E2E",
    fecha=FECHA_COMPETENCIA_ISO,
):
    """Body of `POST /administracion/competencias`."""
    return {
        "evento_id": str(evento_id),
        "disciplina_id": str(disciplina_id),
        "categoria_id": str(categoria_id),
        "nombre": nombre,
        "fecha": fecha,
    }


def make_competencia_equipo_create_http_payload(equipo_id, orden=1):
    """Body of `POST /administracion/competencias/{id}/equipos`."""
    return {"equipo_id": str(equipo_id), "orden": orden}


def make_ronda_create_http_payload(etiqueta="Primera ronda", orden=1):
    """Body of `POST /administracion/competencias/{id}/rondas`."""
    return {"etiqueta": etiqueta, "orden": orden}


def make_encuentro_create_http_payload(
    ronda_id,
    orden=1,
    participante_1_id=None,
    participante_2_id=None,
):
    """Body of `POST /administracion/competencias/{id}/encuentros`.

    Both participants are optional ON PURPOSE: an empty or partial bracket
    must be readable and editable.
    """
    return {
        "ronda_id": str(ronda_id),
        "orden": orden,
        "participante_1_id": (
            str(participante_1_id) if participante_1_id is not None else None
        ),
        "participante_2_id": (
            str(participante_2_id) if participante_2_id is not None else None
        ),
    }


def make_bye_http_payload(expected_version=1, motivo=MOTIVO_BYE):
    """Body of `POST /administracion/competencias/encuentros/{id}/bye`."""
    return {"motivo": motivo, "expected_version": expected_version}


def make_programacion_http_payload(
    inicio=HORA_INICIO_ISO,
    fin=HORA_FIN_ISO,
    expected_version=1,
    motivo=MOTIVO_PROGRAMACION,
):
    """Body of `PATCH /administracion/competencias/encuentros/{id}/programacion`."""
    return {
        "inicio_programado": inicio,
        "fin_programado": fin,
        "motivo": motivo,
        "expected_version": expected_version,
    }


def make_participantes_http_payload(
    participante_1_id=None,
    participante_2_id=None,
    expected_version=1,
    motivo=MOTIVO_PARTICIPANTES,
):
    """Body of `PATCH /administracion/competencias/encuentros/{id}/participantes`."""
    return {
        "participante_1_id": (
            str(participante_1_id) if participante_1_id is not None else None
        ),
        "participante_2_id": (
            str(participante_2_id) if participante_2_id is not None else None
        ),
        "motivo": motivo,
        "expected_version": expected_version,
    }


def make_estado_competencia_http_payload(
    estado,
    expected_version=1,
    motivo=MOTIVO_CANCELACION,
):
    """Body of `PATCH /administracion/competencias/{id}/estado`."""
    return {"estado": estado, "motivo": motivo, "expected_version": expected_version}


def make_enlace_http_payload(
    siguiente_encuentro_id,
    slot_destino="PARTICIPANTE_1",
    expected_version=1,
    motivo=MOTIVO_ENLACE,
):
    """Body of `POST /administracion/competencias/encuentros/{id}/enlace`."""
    return {
        "siguiente_encuentro_id": str(siguiente_encuentro_id),
        "slot_destino": slot_destino,
        "motivo": motivo,
        "expected_version": expected_version,
    }


def make_resultado_http_payload(
    ganador_id,
    expected_version=1,
    puntaje_1=None,
    puntaje_2=None,
    marcador_detalle=None,
    motivo=MOTIVO_RESULTADO,
):
    """Body of `POST /administracion/competencias/encuentros/{id}/resultado`."""
    return {
        "ganador_id": str(ganador_id),
        "puntaje_1": puntaje_1,
        "puntaje_2": puntaje_2,
        "marcador_detalle": marcador_detalle,
        "motivo": motivo,
        "expected_version": expected_version,
    }


def make_avance_confirmar_http_payload(expected_version=1, motivo=MOTIVO_AVANCE):
    """Body of `POST /administracion/competencias/encuentros/{id}/avance/confirm`."""
    return {"motivo": motivo, "expected_version": expected_version}
