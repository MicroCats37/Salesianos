"""El alta de la inscripción rechaza los alcances inválidos.

GIVEN  una edición, un paquete o una disciplina que no son comprables
WHEN   se confirma el alta
THEN   se rechaza con el error de dominio que corresponde, y NO se crea ni
       la inscripción ni la compra (`RN-E01`, `RN-C02`, `FL-01` paso 3).
"""

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.models import Compra
from modules.eventos.domain.exceptions import (
    EdicionNoEncontradaError,
    EdicionNoPublicadaError,
    ModuloNoHabilitadoError,
)
from modules.salesianos_fest.domain.exceptions import (
    DisciplinaNoPermitidaError,
    PaqueteNoVigenteError,
)
from modules.salesianos_fest.domain.models import Equipo, Inscripcion
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    EquipoCreateData,
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.services.flujos.inscripcion_flujo import (
    InscripcionFlujo,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de inscripciones."""
    return injector.get(InscripcionFlujo)


def _intencion(edicion_id, paquete_id, disciplina_id, persona_id):
    """Construye la intención de alta."""
    return InscripcionInicialData(
        responsable_id=persona_id,
        edicion_id=edicion_id,
        paquete_id=paquete_id,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina_id, nombre="EquipoUno"),
        ],
    )


def test_una_edicion_no_publicada_no_se_puede_comprar(
    flujo, edicion_borrador, paquete, disciplina, persona
):
    """GIVEN una edición en BORRADOR
    WHEN  se confirma el alta
    THEN  se rechaza con `EDICION_NO_PUBLICADA`.
    """
    intencion = _intencion(edicion_borrador.id, paquete.id, disciplina.id, persona.id)

    with pytest.raises(EdicionNoPublicadaError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0
    assert Compra.objects.count() == 0


def test_una_edicion_inexistente_no_se_puede_comprar(
    flujo, paquete, disciplina, persona
):
    """GIVEN una edición que no existe
    WHEN  se confirma el alta
    THEN  se rechaza con `EDICION_NO_ENCONTRADA`.
    """
    from uuid import uuid4

    intencion = _intencion(uuid4(), paquete.id, disciplina.id, persona.id)

    with pytest.raises(EdicionNoEncontradaError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0


def test_una_edicion_sin_el_modulo_no_expone_compra(
    flujo, edicion_sin_modulo, disciplina, persona
):
    """GIVEN una edición sin el módulo `inscripciones` habilitado
    WHEN  se confirma el alta
    THEN  se rechaza con `MODULO_NO_HABILITADO`.
    """
    from modules.salesianos_fest.domain.models import Paquete, PaqueteDisciplina

    paquete = Paquete.objects.create(
        edicion=edicion_sin_modulo,
        nombre="Paquete de la edición sin módulo",
        slug="sin-modulo",
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)

    intencion = _intencion(edicion_sin_modulo.id, paquete.id, disciplina.id, persona.id)

    with pytest.raises(ModuloNoHabilitadoError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0


def test_un_paquete_de_otra_edicion_no_se_puede_comprar(
    flujo, edicion_publicada, edicion_otra, disciplina_otra_edicion, persona, precio
):
    """GIVEN un paquete de OTRA edición
    WHEN  se confirma el alta contra la edición actual
    THEN  se rechaza con `PAQUETE_NO_VIGENTE`: el alcance es la edición.
    """
    from modules.salesianos_fest.domain.models import Paquete, PaqueteDisciplina

    paquete_ajeno = Paquete.objects.create(
        edicion=edicion_otra,
        nombre="Paquete de otro FEST",
        slug="otro-paquete",
    )
    PaqueteDisciplina.objects.create(
        paquete=paquete_ajeno,
        disciplina=disciplina_otra_edicion,
    )

    intencion = _intencion(
        edicion_publicada.id,
        paquete_ajeno.id,
        disciplina_otra_edicion.id,
        persona.id,
    )

    with pytest.raises(PaqueteNoVigenteError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0
    assert Compra.objects.count() == 0


def test_un_paquete_sin_precio_vigente_no_se_puede_comprar(
    flujo, edicion_publicada, paquete_sin_precio, disciplina, persona
):
    """GIVEN un paquete sin precio vigente
    WHEN  se confirma el alta
    THEN  se rechaza con `PAQUETE_NO_VIGENTE`: no hay precio de reserva.
    """
    intencion = _intencion(
        edicion_publicada.id,
        paquete_sin_precio.id,
        disciplina.id,
        persona.id,
    )

    with pytest.raises(PaqueteNoVigenteError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0
    assert Compra.objects.count() == 0


def test_una_disciplina_fuera_del_paquete_no_se_puede_comprar(
    flujo, edicion_publicada, paquete, disciplina, disciplina_otra_edicion, persona, precio
):
    """GIVEN una disciplina que el paquete NO permite
    WHEN  se confirma el alta
    THEN  se rechaza con `DISCIPLINA_NO_PERMITIDA`: el padrón no lo elige
       el cliente.
    """
    intencion = _intencion(
        edicion_publicada.id,
        paquete.id,
        disciplina_otra_edicion.id,
        persona.id,
    )

    with pytest.raises(DisciplinaNoPermitidaError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0
    assert Equipo.objects.count() == 0


def test_una_disciplina_inactiva_no_se_puede_comprar(
    flujo, edicion_publicada, paquete, disciplina_inactiva, persona, precio
):
    """GIVEN una disciplina INACTIVA
    WHEN  se confirma el alta
    THEN  se rechaza con `DISCIPLINA_NO_PERMITIDA`.
    """
    from modules.salesianos_fest.domain.models import PaqueteDisciplina

    PaqueteDisciplina.objects.create(
        paquete=paquete,
        disciplina=disciplina_inactiva,
    )

    intencion = _intencion(
        edicion_publicada.id,
        paquete.id,
        disciplina_inactiva.id,
        persona.id,
    )

    with pytest.raises(DisciplinaNoPermitidaError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0


def test_dos_equipos_de_la_misma_disciplina_se_rechazan(
    flujo, edicion_publicada, paquete, disciplina, persona, precio
):
    """GIVEN un alta con dos equipos de la MISMA disciplina
    WHEN  se confirma
    THEN  se rechaza con `EQUIPO_DUPLICADO`.
    """
    intencion = InscripcionInicialData(
        responsable_id=persona.id,
        edicion_id=edicion_publicada.id,
        paquete_id=paquete.id,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoUno"),
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoDos"),
        ],
    )

    from modules.salesianos_fest.domain.exceptions import EquipoDuplicadoError

    with pytest.raises(EquipoDuplicadoError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0
