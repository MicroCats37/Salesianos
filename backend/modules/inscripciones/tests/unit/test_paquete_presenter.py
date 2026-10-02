"""Unit tests for PaquetePresenter."""
import pytest

from modules.inscripciones.domain.constants import (
    ModoDisciplinasPaqueteChoices,
)
from modules.inscripciones.presentation.presenters.paquete_presenter import (
    calcular_cantidad_maxima_equipos,
    present_paquete,
)


@pytest.mark.django_db
def test_present_paquete_incluye_cantidad_maxima_equipos_elegible(
    paquete_basic,
):
    """Modo ELEGIBLE: cantidad_maxima_equipos = cantidad_disciplinas_requeridas."""
    data = present_paquete(paquete_basic)
    assert (
        data.cantidad_maxima_equipos
        == paquete_basic.cantidad_disciplinas_requeridas
    )


@pytest.mark.django_db
def test_calcular_cantidad_maxima_equipos_elegible_sin_cantidad_devuelve_1(
    paquete_basic,
):
    """Default fallback to 1 when cantidad_disciplinas_requeridas is None."""
    paquete_basic.cantidad_disciplinas_requeridas = None
    paquete_basic.save()
    assert calcular_cantidad_maxima_equipos(paquete_basic) == 1


@pytest.mark.django_db
def test_calcular_cantidad_maxima_equipos_fijo(
    paquete_basic,
    disciplina_futbol,
    disciplina_basket,
):
    """Modo FIJO: one team per PaqueteDisciplina."""
    paquete_basic.modo_disciplinas = ModoDisciplinasPaqueteChoices.FIJO
    paquete_basic.cantidad_disciplinas_requeridas = 99  # ignored for FIJO
    paquete_basic.save()

    from modules.inscripciones.domain.models import PaqueteDisciplina

    PaqueteDisciplina.objects.create(
        paquete=paquete_basic, disciplina=disciplina_futbol
    )
    PaqueteDisciplina.objects.create(
        paquete=paquete_basic, disciplina=disciplina_basket
    )

    assert calcular_cantidad_maxima_equipos(paquete_basic) == 2
    data = present_paquete(paquete_basic)
    assert data.cantidad_maxima_equipos == 2
    assert data.modo_disciplinas == ModoDisciplinasPaqueteChoices.FIJO
