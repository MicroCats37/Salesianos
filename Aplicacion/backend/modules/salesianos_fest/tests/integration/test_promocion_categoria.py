"""La promoción de la inscripción y la categoría DERIVADA del equipo.

GIVEN  una promoción activa, su categoría en la edición y una promoción
       fusionada
WHEN   se confirma el alta
THEN   el equipo lleva la categoría DERIVADA de la promoción principal, la
       fusión es sólo metadato DESCRIPTIVO y el backend rechaza lo que no
       puede resolver (`D-CAT-01`, `D-CAT-02`, `D-CAT-05`).

La regla que se comprueba aquí es la que el rebuild había perdido: la
categoría NO la declara el cliente y NO se inventa una banda competitive que
el catálogo no cubre.
"""

import pytest
from asgiref.sync import async_to_sync

from modules.salesianos_fest.domain.exceptions import (
    CategoriaNoResueltaError,
    FusionPromocionInvalidaError,
    PromocionNoEncontradaError,
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


def _intencion(edicion, paquete, disciplina, persona, promocion, **extra):
    """La intención de alta con la promoción indicada."""
    return InscripcionInicialData(
        responsable_id=persona.id,
        edicion_id=edicion.id,
        paquete_id=paquete.id,
        promocion_id=promocion.id,
        cantidad=10,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoUno"),
        ],
        **extra,
    )


def test_la_categoria_se_deriva_de_la_promocion_principal(
    flujo, edicion_publicada, paquete, disciplina, persona, precio, promocion, categoria
):
    """GIVEN una promoción que cae en el rango de una categoría
    WHEN  se confirma el alta
    THEN  el equipo lleva esa categoría: la deriva el servidor, no el
       cliente (`D-CAT-05`).
    """
    intencion = _intencion(edicion_publicada, paquete, disciplina, persona, promocion)

    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    equipo = Equipo.objects.get()
    assert equipo.categoria_id == categoria.id
    assert Inscripcion.objects.get().promocion_id == promocion.id


def test_una_promocion_sin_categoria_se_rechaza(
    flujo, edicion_publicada, paquete, disciplina, persona, precio, promocion_sin_categoria
):
    """GIVEN una promoción que NO cae en ninguna categoría de la edición
    WHEN  se confirma el alta
    THEN  se rechaza con `CATEGORIA_NO_RESUELTA`: no se inventa una banda
       competitiva (`D-CAT-05`).
    """
    intencion = _intencion(
        edicion_publicada,
        paquete,
        disciplina,
        persona,
        promocion_sin_categoria,
    )

    with pytest.raises(CategoriaNoResueltaError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0
    assert Equipo.objects.count() == 0


def test_una_promocion_inexistente_se_rechaza(
    flujo, edicion_publicada, paquete, disciplina, persona, precio
):
    """GIVEN una promoción que NO existe en el catálogo global
    WHEN  se confirma el alta
    THEN  se rechaza con `PROMOCION_NO_ENCONTRADA`.
    """
    from uuid import uuid4

    intencion = InscripcionInicialData(
        responsable_id=persona.id,
        edicion_id=edicion_publicada.id,
        paquete_id=paquete.id,
        promocion_id=uuid4(),
        cantidad=10,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoUno"),
        ],
    )

    with pytest.raises(PromocionNoEncontradaError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0


def test_una_promocion_inactiva_se_rechaza(
    flujo,
    edicion_publicada,
    paquete,
    disciplina,
    persona,
    precio,
    promocion_inactiva,
    categoria,
):
    """GIVEN una promoción INACTIVA
    WHEN  se confirma el alta
    THEN  se rechaza con `PROMOCION_NO_ENCONTRADA`: no se elige una
       promoción retirada del catálogo.
    """
    intencion = _intencion(
        edicion_publicada,
        paquete,
        disciplina,
        persona,
        promocion_inactiva,
    )

    with pytest.raises(PromocionNoEncontradaError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0


def test_la_fusion_se_guarda_como_metadato_sin_alterar_la_categoria(
    flujo,
    edicion_publicada,
    paquete,
    disciplina,
    persona,
    precio,
    promocion,
    promocion_fusion,
    categoria,
):
    """GIVEN una promoción FUSIONADA (dos cohortes)
    WHEN  se confirma el alta
    THEN  la fusión se guarda como metadato DESCRIPTIVO y la categoría, los
       cupos y el total son los de la promoción PRINCIPAL (`D-CAT-02`).
    """
    intencion = _intencion(
        edicion_publicada,
        paquete,
        disciplina,
        persona,
        promocion,
        fusion_promocion_id=promocion_fusion.id,
    )

    resultado = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    inscripcion = Inscripcion.objects.get()
    assert inscripcion.fusion_promocion_id == promocion_fusion.id
    assert inscripcion.promocion_id == promocion.id
    assert Equipo.objects.get().categoria_id == categoria.id
    assert resultado.inscripcion.cupos_solicitados == 10
    assert resultado.compra.cantidad == 10


def test_la_fusion_no_puede_ser_la_misma_promocion(
    flujo,
    edicion_publicada,
    paquete,
    disciplina,
    persona,
    precio,
    promocion,
    categoria,
):
    """GIVEN una fusión con la MISMA promoción que la principal
    WHEN  se confirma el alta
    THEN  se rechaza con `FUSION_PROMOCION_INVALIDA`: una fusión no es un
       alias de la promoción principal (`D-CAT-02`).
    """
    intencion = _intencion(
        edicion_publicada,
        paquete,
        disciplina,
        persona,
        promocion,
        fusion_promocion_id=promocion.id,
    )

    with pytest.raises(FusionPromocionInvalidaError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0
