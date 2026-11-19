"""La titularidad de la inscripción la decide el responsable, no el rol.

GIVEN  una inscripción con un responsable concreto
WHEN   la consulta o la gestiona OTRO actor
THEN   se rechaza con `INSCRIPCION_NO_AUTORIZADA`; el grupo `Administrador`
       NO sustituye la titularidad (`FR-03` §2.1, `RN-U04`).
"""

import pytest
from asgiref.sync import async_to_sync

from modules.salesianos_fest.domain.exceptions import (
    CompradorSinPersonaError,
    InscripcionNoAutorizadaError,
)
from modules.salesianos_fest.domain.models import Inscripcion
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    EquipoCreateData,
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.services.flujos.inscripcion_flujo import (
    InscripcionFlujo,
)
from modules.salesianos_fest.domain.services.orchestrators.inscripcion_orchestrator import (
    InscripcionOrchestrator,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de inscripciones."""
    return injector.get(InscripcionFlujo)


@pytest.fixture
def orquestador(injector):
    """El orquestador real de inscripciones."""
    return injector.get(InscripcionOrchestrator)


@pytest.fixture
def inscripcion(flujo, edicion_publicada, paquete, disciplina, persona, precio):
    """Una inscripción creada por `persona`."""
    intencion = InscripcionInicialData(
        responsable_id=persona.id,
        edicion_id=edicion_publicada.id,
        paquete_id=paquete.id,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoUno"),
        ],
    )
    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)
    return Inscripcion.objects.get()


def test_el_responsable_puede_consultar_su_inscripcion(
    orquestador, inscripcion, usuario_responsable
):
    """GIVEN la cuenta del responsable
    WHEN  consulta su inscripción
    THEN  la obtiene.
    """
    detalle = async_to_sync(orquestador.obtener_inscripcion)(
        usuario_responsable,
        inscripcion.id,
    )

    assert detalle.id == str(inscripcion.id)


def test_otro_actor_no_puede_consultar_la_inscripcion(
    orquestador, inscripcion, usuario_ajeno
):
    """GIVEN la cuenta de OTRA persona
    WHEN  consulta la inscripción
    THEN  se rechaza con `INSCRIPCION_NO_AUTORIZADA`.
    """
    with pytest.raises(InscripcionNoAutorizadaError):
        async_to_sync(orquestador.obtener_inscripcion)(
            usuario_ajeno,
            inscripcion.id,
        )


def test_otro_actor_no_puede_listar_los_equipos(
    orquestador, inscripcion, usuario_ajeno
):
    """GIVEN la cuenta de OTRA persona
    WHEN  lista los equipos de la inscripción
    THEN  se rechaza con `INSCRIPCION_NO_AUTORIZADA`.
    """
    with pytest.raises(InscripcionNoAutorizadaError):
        async_to_sync(orquestador.listar_equipos)(usuario_ajeno, inscripcion.id)


def test_el_grupo_administrador_no_sustituye_la_titularidad(
    orquestador, inscripcion, usuario_ajeno, db
):
    """GIVEN una cuenta del grupo `Administrador` que NO es la responsable
    WHEN  consulta la inscripción
    THEN  se rechaza: ser administrador no hace responsable de una
       inscripción ajena (`FR-03` §2.1 regla 3).
    """
    from modules.usuarios.domain.constants import GrupoFuncionalChoices

    grupo = db_group(db, GrupoFuncionalChoices.ADMINISTRADOR)
    usuario_ajeno.groups.add(grupo)

    with pytest.raises(InscripcionNoAutorizadaError):
        async_to_sync(orquestador.obtener_inscripcion)(
            usuario_ajeno,
            inscripcion.id,
        )


def test_una_cuenta_sin_persona_no_puede_inscribirse(
    orquestador, edicion_publicada, paquete, disciplina, db
):
    """GIVEN una cuenta autenticada SIN persona vinculada
    WHEN  intenta el alta
    THEN  se rechaza con `COMPRADOR_SIN_PERSONA`.
    """
    from modules.usuarios.domain.models import Usuario

    cuenta = Usuario.objects.create_user(
        username="cuenta-tecnica",
        password="Prueba-12345",
    )

    intencion = InscripcionInicialData(
        edicion_id=edicion_publicada.id,
        paquete_id=paquete.id,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoUno"),
        ],
    )

    with pytest.raises(CompradorSinPersonaError):
        async_to_sync(orquestador.crear_inscripcion_inicial)(cuenta, intencion)


def db_group(db, nombre):
    """El grupo funcional indicado."""
    from django.contrib.auth.models import Group

    grupo, _ = Group.objects.get_or_create(name=nombre)
    return grupo
