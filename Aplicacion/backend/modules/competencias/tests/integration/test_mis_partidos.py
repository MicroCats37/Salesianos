"""MIS PARTIDOS: la lectura de la cuenta, con la identidad del servidor.

Change: `partidos-marcadores-competencias` · Batch 3B

GIVEN  una cuenta con un equipo en un cuadro
WHEN   la cuenta lee `GET /api/cuenta/mis-partidos`
THEN   la respuesta contiene SUS partidos, en sus tres cubos, con el ganador
       explícito y la versión; y NO contiene los partidos de otra cuenta

AND    la ruta exige SESIÓN: sin credencial responde 401
AND    la ruta NO acepta ninguna persona, usuario ni equipo: la identidad la
       decide el servidor
AND    una cuenta sin `Persona`, sin participaciones o sin equipos recibe una
       lista VACÍA, nunca un error
"""

from datetime import date

import pytest
from django.test import Client
from ninja_jwt.tokens import RefreshToken

from modules.competencias.domain.constants import EstadoEncuentro
from modules.competencias.domain.models import (
    Competencia,
    CompetenciaEquipo,
    Encuentro,
    Ronda,
)
from modules.salesianos_fest.domain.models import Participacion

pytestmark = [
    pytest.mark.urls("modules.competencias.tests.urls_competencias"),
    pytest.mark.django_db,
]

RUTA = "/api/cuenta/mis-partidos"


def _autorizacion(usuario) -> dict:
    token = str(RefreshToken.for_user(usuario).access_token)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _ids_de_los_cubos(cuerpo) -> list[str]:
    """Los identificadores de los partidos publicados, en los tres cubos."""
    return [
        encuentro["id"]
        for cubo in ("en_vivo", "proximos", "finalizados")
        for encuentro in cuerpo["data"][cubo]
    ]


@pytest.fixture
def usuario_sin_persona(db):
    """Una cuenta SIN `Persona`: no tiene ningún equipo."""
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="sin-persona",
        password="Prueba-12345",
    )


@pytest.fixture
def cuenta(
    db,
    edicion_publicada,
    disciplina,
    categoria,
    usuario_admin,
    persona,
    equipo,
    participacion,
    competencia,
    ronda,
    equipo_en_cuadro,
):
    """Una cuenta con UN equipo en el cuadro y un partido programado."""
    encuentro = Encuentro.objects.create(
        ronda=ronda,
        orden=1,
        estado=EstadoEncuentro.PROGRAMADO,
        participante_1=equipo_en_cuadro,
        inicio_programado="2027-03-14T15:00:00Z",
        fin_programado="2027-03-14T16:00:00Z",
    )
    return {
        "usuario": usuario_admin,
        "encuentro": encuentro,
        "equipo": equipo,
        "equipo_en_cuadro": equipo_en_cuadro,
        "participacion": participacion,
        "ronda": ronda,
        "competencia": competencia,
    }


def test_sin_credencial_la_ruta_responde_401(db, cuenta):
    """GIVEN una petición ANÓNIMA."""
    respuesta = Client().get(RUTA)

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_la_cuenta_ve_sus_partidos(db, cuenta):
    """GIVEN una cuenta con un equipo en un cuadro."""
    respuesta = Client().get(RUTA, **_autorizacion(cuenta["usuario"]))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["data"]["total"] == 1
    assert [e["id"] for e in cuerpo["data"]["proximos"]] == [
        str(cuenta["encuentro"].id)
    ]
    assert cuerpo["data"]["en_vivo"] == []
    assert cuerpo["data"]["finalizados"] == []
    # El equipo de la cuenta viaja con su nombre.
    assert [e["equipo_nombre"] for e in cuerpo["data"]["equipos"]] == [
        cuenta["equipo"].nombre
    ]
    # Y con su versión: el cliente puede descartar un evento viejo.
    assert cuerpo["data"]["proximos"][0]["version"] == cuenta["encuentro"].version


def test_la_ruta_no_acepta_ninguna_identidad_del_cliente(
    db, cuenta, persona_2, usuario_ajeno
):
    """GIVEN una petición que intenta viajar por otra persona."""
    respuesta = Client().get(
        f"{RUTA}?persona_id={persona_2.id}&usuario_id={usuario_ajeno.id}",
        **_autorizacion(cuenta["usuario"]),
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    # La identidad la decide la SESIÓN: el identificador ajeno se IGNORA.
    assert _ids_de_los_cubos(cuerpo) == [str(cuenta["encuentro"].id)]


def test_una_cuenta_sin_persona_no_ve_nada(db, cuenta, usuario_sin_persona):
    """GIVEN una cuenta SIN `Persona`."""
    respuesta = Client().get(RUTA, **_autorizacion(usuario_sin_persona))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["data"]["total"] == 0
    assert cuerpo["data"]["equipos"] == []
    assert _ids_de_los_cubos(cuerpo) == []


def test_una_cuenta_sin_equipos_no_ve_nada(db, cuenta, usuario_admin):
    """GIVEN una cuenta con `Persona` pero SIN participaciones."""
    Participacion.objects.filter(persona_id=usuario_admin.persona_fk_id).delete()

    respuesta = Client().get(RUTA, **_autorizacion(usuario_admin))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["data"]["total"] == 0
    assert cuerpo["data"]["equipos"] == []


def test_los_partidos_de_otra_cuenta_no_se_publican(
    db,
    cuenta,
    edicion_publicada,
    disciplina,
    categoria,
    persona_2,
    usuario_ajeno,
    equipo_2,
    inscripcion_2,
):
    """GIVEN una cuenta con un partido propio y OTRA con un partido ajeno."""
    competencia_ajena = Competencia.objects.create(
        edicion=edicion_publicada,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Torneo ajeno",
        fecha=date(2027, 3, 15),
    )
    ronda_ajena = Ronda.objects.create(
        competencia=competencia_ajena,
        etiqueta="Final ajena",
        orden=1,
    )
    Participacion.objects.create(
        inscripcion=inscripcion_2,
        persona=persona_2,
        equipo=equipo_2,
        edicion=edicion_publicada,
        disciplina=disciplina,
        rol="JUGADOR",
        estado="ACTIVA",
    )
    equipo_ajeno = CompetenciaEquipo.objects.create(
        competencia=competencia_ajena,
        equipo=equipo_2,
        orden=1,
        estado="ACTIVO",
    )
    Encuentro.objects.create(
        ronda=ronda_ajena,
        orden=1,
        estado=EstadoEncuentro.PROGRAMADO,
        participante_1=equipo_ajeno,
        inicio_programado="2027-03-15T15:00:00Z",
        fin_programado="2027-03-15T16:00:00Z",
    )

    respuesta = Client().get(RUTA, **_autorizacion(cuenta["usuario"]))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert _ids_de_los_cubos(cuerpo) == [str(cuenta["encuentro"].id)]
    # El equipo ajeno NO aparece en los equipos de la cuenta.
    assert [e["equipo_nombre"] for e in cuerpo["data"]["equipos"]] == [
        cuenta["equipo"].nombre
    ]


def test_un_partido_con_el_equipo_en_el_segundo_slot_aparece_una_vez(
    db,
    cuenta,
    edicion_publicada,
    disciplina,
    categoria,
    persona,
    equipo_2,
    inscripcion_2,
):
    """GIVEN un partido en el que el equipo de la cuenta ocupa el SEGUNDO slot.

    La consulta es UNA sola (los dos slots a la vez): un partido aparece UNA
    vez, nunca dos. Y una persona no puede jugar dos veces en la misma
    disciplina de la misma edición (`fest_participacion`), así que el caso de
    "dos equipos propios en el mismo partido" es imposible por dominio.
    """
    from modules.competencias.domain.models import Competencia
    from modules.salesianos_fest.domain.models import Disciplina

    disciplina_2 = Disciplina.objects.create(
        edicion=edicion_publicada,
        nombre="Básquet",
        slug="basquet",
        minimo_por_equipo=1,
        maximo_por_equipo=12,
    )
    competencia_2 = Competencia.objects.create(
        edicion=edicion_publicada,
        disciplina=disciplina_2,
        categoria=categoria,
        nombre="Torneo de básquet",
        fecha=date(2027, 3, 16),
    )
    ronda_2 = Ronda.objects.create(
        competencia=competencia_2,
        etiqueta="Primera",
        orden=1,
    )
    Participacion.objects.create(
        inscripcion=inscripcion_2,
        persona=persona,
        equipo=equipo_2,
        edicion=edicion_publicada,
        disciplina=disciplina_2,
        rol="JUGADOR",
        estado="ACTIVA",
    )
    equipo_2_en_cuadro = CompetenciaEquipo.objects.create(
        competencia=competencia_2,
        equipo=equipo_2,
        orden=1,
        estado="ACTIVO",
    )
    segundo_slot = Encuentro.objects.create(
        ronda=ronda_2,
        orden=1,
        estado=EstadoEncuentro.PROGRAMADO,
        participante_2=equipo_2_en_cuadro,
        inicio_programado="2027-03-16T15:00:00Z",
        fin_programado="2027-03-16T16:00:00Z",
    )

    respuesta = Client().get(RUTA, **_autorizacion(cuenta["usuario"]))

    cuerpo = respuesta.json()
    publicados = _ids_de_los_cubos(cuerpo)
    assert len(publicados) == len(set(publicados))
    assert str(segundo_slot.id) in publicados
    assert str(cuenta["encuentro"].id) in publicados


def test_los_tres_cubos_y_el_ganador_explicito(db, cuenta):
    """GIVEN un partido en juego y otro finalizado con ganador declarado."""
    en_juego = Encuentro.objects.create(
        ronda=cuenta["ronda"],
        orden=2,
        estado=EstadoEncuentro.EN_CURSO,
        participante_1=cuenta["equipo_en_cuadro"],
        inicio_programado="2027-03-14T17:00:00Z",
        fin_programado="2027-03-14T18:00:00Z",
        iniciado_en="2027-03-14T17:05:00Z",
    )
    finalizado = Encuentro.objects.create(
        ronda=cuenta["ronda"],
        orden=3,
        estado=EstadoEncuentro.FINALIZADO,
        participante_1=cuenta["equipo_en_cuadro"],
        puntaje_1=1,
        puntaje_2=7,
        marcador_detalle="Set 1: 1-7",
        inicio_programado="2027-03-14T15:00:00Z",
        fin_programado="2027-03-14T16:00:00Z",
        iniciado_en="2027-03-14T15:02:00Z",
        finalizado_en="2027-03-14T15:55:00Z",
    )
    finalizado.ganador = cuenta["equipo_en_cuadro"]
    finalizado.save()

    respuesta = Client().get(RUTA, **_autorizacion(cuenta["usuario"]))

    cuerpo = respuesta.json()
    assert [e["id"] for e in cuerpo["data"]["en_vivo"]] == [str(en_juego.id)]
    assert [e["id"] for e in cuerpo["data"]["finalizados"]] == [
        str(finalizado.id)
    ]
    assert [e["id"] for e in cuerpo["data"]["proximos"]] == [
        str(cuenta["encuentro"].id)
    ]
    assert cuerpo["data"]["total"] == 3

    final = cuerpo["data"]["finalizados"][0]
    # El ganador viaja como lo publicó el backend; el marcador NO lo decide.
    assert final["ganador_equipo_id"] == str(cuenta["equipo_en_cuadro"].equipo_id)
    assert final["ganador_equipo_nombre"] == cuenta["equipo"].nombre
    assert final["puntaje_1"] == 1
    assert final["puntaje_2"] == 7
    # La versión viaja: el cliente puede descartar un evento viejo.
    assert final["version"] == finalizado.version


def test_un_partido_cancelado_no_se_publica(db, cuenta):
    """GIVEN un partido CANCELADO de la cuenta."""
    cancelado = Encuentro.objects.create(
        ronda=cuenta["ronda"],
        orden=2,
        estado=EstadoEncuentro.CANCELADO,
        participante_1=cuenta["equipo_en_cuadro"],
        inicio_programado="2027-03-14T17:00:00Z",
        fin_programado="2027-03-14T18:00:00Z",
    )

    respuesta = Client().get(RUTA, **_autorizacion(cuenta["usuario"]))

    cuerpo = respuesta.json()
    assert str(cancelado.id) not in _ids_de_los_cubos(cuerpo)
    assert cuerpo["data"]["total"] == 1
