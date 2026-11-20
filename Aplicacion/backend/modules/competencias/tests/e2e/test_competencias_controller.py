"""Superficie HTTP de las competencias, el cuadro y la agenda.

GIVEN  una cuenta con permisos de administración y una edición con disciplina
WHEN   se consulta la lista, el detalle, el cuadro, la agenda y los equipos
       candidatos, y se crea la estructura del cuadro
THEN   responde el envelope congelado con los wrappers OPERATIVOS, la
       autorización se decide en el backend y las rutas de PREVISUALIZACIÓN
       NO escriben (`RN-A01`, `FR-01`, `QA-K04`).

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).
"""

import json

import pytest
from django.test import Client

pytestmark = [
    pytest.mark.urls("modules.competencias.tests.urls_competencias"),
    pytest.mark.django_db,
]


@pytest.fixture
def cliente():
    """Cliente HTTP de prueba."""
    return Client()


def _autorizacion(usuario) -> dict:
    """El header `Authorization` del usuario indicado."""
    from ninja_jwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(usuario).access_token)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


# ── Lecturas ────────────────────────────────────────────────────────────────


def test_la_lista_devuelve_las_competencias_de_la_edicion(
    cliente,
    usuario_admin,
    competencia,
):
    """GIVEN una cuenta con permisos y una competencia de la edición."""
    respuesta = cliente.get(
        "/api/competencias",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert len(cuerpo["data"]) == 1
    assert cuerpo["data"][0]["id"] == str(competencia.id)
    assert cuerpo["data"][0]["nombre"] == competencia.nombre


def test_la_lista_publica_la_categoria_de_cada_competencia(
    cliente,
    usuario_admin,
    competencia,
    categoria,
):
    """GIVEN una competencia con su categoría."""
    respuesta = cliente.get(
        "/api/competencias",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 200
    fila = json.loads(respuesta.content)["data"][0]
    assert fila["categoria_id"] == str(categoria.id)
    assert fila["categoria_nombre"] == categoria.nombre


def test_la_lista_se_filtra_por_categoria(
    cliente,
    usuario_admin,
    competencia,
    competencia_categoria_2,
    categoria,
    categoria_2,
):
    """GIVEN dos competencias de la misma edición con categorías DISTINTAS."""
    respuesta = cliente.get(
        "/api/competencias",
        data={"categoria_id": str(categoria_2.id)},
        **_autorizacion(usuario_admin),
    )

    # THEN el filtro deja SÓLO las competencias de esa categoría.
    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert [fila["id"] for fila in cuerpo["data"]] == [
        str(competencia_categoria_2.id)
    ]
    assert cuerpo["data"][0]["categoria_id"] == str(categoria_2.id)


def test_el_detalle_trae_equipos_y_cuadro(
    cliente,
    usuario_admin,
    competencia,
    equipo_en_cuadro,
    ronda,
    encuentro,
    categoria,
):
    """GIVEN una competencia con un equipo y un encuentro."""
    respuesta = cliente.get(
        f"/api/competencias/{competencia.id}",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    detalle = cuerpo["data"]
    assert detalle["id"] == str(competencia.id)
    assert detalle["categoria_id"] == str(categoria.id)
    assert detalle["categoria_nombre"] == categoria.nombre
    assert len(detalle["equipos"]) == 1
    assert detalle["equipos"][0]["id"] == str(equipo_en_cuadro.id)
    assert len(detalle["rondas"]) == 1
    assert len(detalle["rondas"][0]["encuentros"]) == 1
    # La MISMA forma de encuentro en el detalle y en el cuadro.
    assert detalle["rondas"][0]["encuentros"][0]["id"] == str(encuentro.id)


def test_el_cuadro_usa_la_misma_forma_de_encuentro_que_el_detalle(
    cliente,
    usuario_admin,
    competencia,
    ronda,
    encuentro,
):
    """GIVEN una competencia con un cuadro."""
    detalle = json.loads(
        cliente.get(
            f"/api/competencias/{competencia.id}",
            **_autorizacion(usuario_admin),
        ).content
    )
    cuadro = json.loads(
        cliente.get(
            f"/api/competencias/{competencia.id}/cuadro",
            **_autorizacion(usuario_admin),
        ).content
    )

    # THEN el encuentro del detalle y el del cuadro tienen las MISMAS claves.
    encuentro_detalle = detalle["data"]["rondas"][0]["encuentros"][0]
    encuentro_cuadro = cuadro["data"][0]["encuentros"][0]
    assert set(encuentro_detalle) == set(encuentro_cuadro)


def test_la_agenda_devuelve_los_encuentros_del_dia(
    cliente,
    usuario_admin,
    edicion_publicada,
):
    """GIVEN una edición vigente."""
    respuesta = cliente.get(
        "/api/competencias/agenda",
        data={"fecha": "2027-03-14"},
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["data"]["fecha"] == "2027-03-14"
    assert cuerpo["data"]["total"] == 0
    assert cuerpo["data"]["encuentros"] == []


def test_los_equipos_candidatos_traen_el_motivo_del_veredicto(
    cliente,
    usuario_admin,
    competencia,
    equipo,
    participacion,
    categoria,
):
    """GIVEN un equipo elegible en la competencia."""
    respuesta = cliente.get(
        f"/api/competencias/{competencia.id}/equipos-elegibles",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert len(cuerpo["data"]) == 1
    veredicto = cuerpo["data"][0]
    assert veredicto["equipo_id"] == str(equipo.id)
    assert veredicto["es_elegible"] is True
    assert veredicto["motivo"] == "ELEGIBLE"
    assert veredicto["categoria_id"] == str(categoria.id)
    assert veredicto["categoria_nombre"] == categoria.nombre


# ── Autorización ────────────────────────────────────────────────────────────


def test_un_usuario_sin_permisos_no_alcanza_la_superficie(
    cliente,
    usuario_ajeno,
    competencia,
):
    """GIVEN una cuenta autenticada SIN permisos administrativos."""
    respuesta = cliente.get(
        "/api/competencias",
        **_autorizacion(usuario_ajeno),
    )

    # THEN el backend rechaza la operación con 403.
    assert respuesta.status_code == 403
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "ACTION_NOT_ALLOWED"


def test_un_visitante_no_alcanza_la_superficie(cliente):
    """GIVEN una petición anónima."""
    respuesta = cliente.get("/api/competencias")

    # THEN la autenticación responde ANTES que la autorización: 401.
    assert respuesta.status_code == 401
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED"


# ── Escrituras ──────────────────────────────────────────────────────────────


def test_la_creacion_de_una_competencia_devuelve_el_detalle(
    cliente,
    usuario_admin,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN una edición, una disciplina y una categoría."""
    respuesta = cliente.post(
        "/api/competencias",
        data=json.dumps(
            {
                "edicion_id": str(edicion_publicada.id),
                "disciplina_id": str(disciplina.id),
                "categoria_id": str(categoria.id),
                "nombre": "Vóley Mixto 2027",
                "fecha": "2027-03-14",
            }
        ),
        content_type="application/json",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 201
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert cuerpo["message"]
    assert cuerpo["data"]["nombre"] == "Vóley Mixto 2027"
    assert cuerpo["data"]["disciplina_id"] == str(disciplina.id)
    assert cuerpo["data"]["categoria_id"] == str(categoria.id)


def test_la_creacion_de_una_competencia_duplicada_se_rechaza(
    cliente,
    usuario_admin,
    edicion_publicada,
    disciplina,
    categoria,
    competencia,
):
    """GIVEN una competencia con la misma identidad."""
    respuesta = cliente.post(
        "/api/competencias",
        data=json.dumps(
            {
                "edicion_id": str(edicion_publicada.id),
                "disciplina_id": str(disciplina.id),
                "categoria_id": str(categoria.id),
                "nombre": "vóley mixto 2027",
                "fecha": "2027-03-14",
            }
        ),
        content_type="application/json",
        **_autorizacion(usuario_admin),
    )

    # THEN el backend rechaza el duplicado con 409.
    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "COMPETENCIA_DUPLICADA"


def test_la_creacion_de_una_ronda_y_un_encuentro(
    cliente,
    usuario_admin,
    competencia,
):
    """GIVEN una competencia."""
    respuesta_ronda = cliente.post(
        f"/api/competencias/{competencia.id}/rondas",
        data=json.dumps({"etiqueta": "Cuartos de final", "orden": 1}),
        content_type="application/json",
        **_autorizacion(usuario_admin),
    )
    assert respuesta_ronda.status_code == 201
    ronda = json.loads(respuesta_ronda.content)["data"]

    respuesta_encuentro = cliente.post(
        f"/api/competencias/{competencia.id}/encuentros",
        data=json.dumps({"ronda_id": ronda["id"], "orden": 1}),
        content_type="application/json",
        **_autorizacion(usuario_admin),
    )

    assert respuesta_encuentro.status_code == 201
    encuentro = json.loads(respuesta_encuentro.content)["data"]
    # Un encuentro vacío es un borrador LEGÍTIMO.
    assert encuentro["estado"] == "BORRADOR"
    assert encuentro["participantes"][0]["equipo_id"] is None


def test_la_edicion_con_version_obsoleta_responde_409(
    cliente,
    usuario_admin,
    competencia,
    equipo_en_cuadro,
):
    """GIVEN una participación con una versión que ya no es la actual."""
    respuesta = cliente.patch(
        f"/api/competencias/{competencia.id}/equipos/{equipo_en_cuadro.id}",
        data=json.dumps(
            {
                "orden": 4,
                "motivo": "Cambio de semilla",
                "expected_version": equipo_en_cuadro.version - 1,
            }
        ),
        content_type="application/json",
        **_autorizacion(usuario_admin),
    )

    # THEN el backend responde `RESOURCE_CHANGED` y no aplica el cambio.
    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "RESOURCE_CHANGED"
