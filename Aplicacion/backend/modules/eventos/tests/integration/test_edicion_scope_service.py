"""`EdicionScopeService`: el ORDEN ÚNICO de resolución de edición (FR-02 §2.2).

GIVEN  un catálogo con cero, una o varias ediciones candidatas
WHEN   se resuelve el alcance
THEN   se aplica el nivel congelado que corresponda y, ante ambigüedad o
       ausencia, se responde con error — NUNCA con "la primera", "la más
       reciente" ni "la que coincida con un nombre por defecto".
"""

import uuid

import pytest

from modules.eventos.domain.exceptions import (
    EdicionAmbiguaError,
    EdicionNoEncontradaError,
    EdicionNoPublicadaError,
    EdicionNoResueltaError,
)
from modules.eventos.domain.models import Edicion


# ── Nivel 1: `edicion_id` explícito ─────────────────────────────────────────


@pytest.mark.django_db
def test_nivel_1_devuelve_la_edicion_explicita(scope_service, edicion_borrador):
    assert scope_service.resolver_explicita(edicion_borrador.id) == edicion_borrador


@pytest.mark.django_db
def test_nivel_1_con_id_inexistente_es_404(scope_service, db):
    with pytest.raises(EdicionNoEncontradaError):
        scope_service.resolver_explicita(uuid.uuid4())


@pytest.mark.django_db
def test_nivel_1_con_id_mal_formado_es_404(scope_service, db):
    with pytest.raises(EdicionNoEncontradaError):
        scope_service.resolver_explicita("no-soy-una-edicion")


@pytest.mark.django_db
def test_nivel_1_no_hace_fallback_a_la_publicada(
    scope_service, edicion_borrador, edicion_publicada
):
    """Un id explícito que no existe NO cae sobre la edición publicada."""
    with pytest.raises(EdicionNoEncontradaError):
        scope_service.resolver_explicita(uuid.uuid4())


@pytest.mark.django_db
def test_nivel_1_con_exigir_publicada_rechaza_un_borrador(
    scope_service, edicion_borrador
):
    with pytest.raises(EdicionNoPublicadaError):
        scope_service.resolver_explicita(edicion_borrador.id, exigir_publicada=True)


# ── Nivel 2: edición activa del actor ──────────────────────────────────────


@pytest.mark.django_db
def test_nivel_2_con_una_sola_candidata_usa_esa(scope_service, edicion_borrador):
    resuelta = scope_service.resolver_actual(ediciones_activas_actor=[edicion_borrador])

    assert resuelta == edicion_borrador


@pytest.mark.django_db
def test_nivel_2_con_varias_candidatas_es_ambigua(
    scope_service, edicion_borrador, edicion_cerrada
):
    with pytest.raises(EdicionAmbiguaError) as error:
        scope_service.resolver_actual(
            ediciones_activas_actor=[edicion_borrador, edicion_cerrada]
        )

    assert len(error.value.candidatas) == 2


@pytest.mark.django_db
def test_nivel_2_ambigua_no_elige_una_por_defecto(
    scope_service, edicion_borrador, edicion_cerrada, edicion_publicada
):
    """Con dos candidatas del actor y una publicada, la respuesta es AMBIGUA."""
    with pytest.raises(EdicionAmbiguaError):
        scope_service.resolver_actual(
            ediciones_activas_actor=[edicion_borrador, edicion_cerrada]
        )


# ── Nivel 3: edición PUBLICADA única ───────────────────────────────────────


@pytest.mark.django_db
def test_nivel_3_usa_la_unica_publicada(scope_service, edicion_publicada):
    assert scope_service.resolver_actual() == edicion_publicada


@pytest.mark.django_db
def test_nivel_3_con_dos_publicadas_es_ambigua(
    scope_service, edicion_publicada, evento_otro
):
    otra = Edicion.objects.create(
        evento=evento_otro,
        nombre="Otra",
        slug="otra",
        anio=2027,
        estado="PUBLICADA",
    )

    with pytest.raises(EdicionAmbiguaError) as error:
        scope_service.resolver_actual()

    assert error.value.candidatas
    assert edicion_publicada in error.value.candidatas
    assert otra in error.value.candidatas


@pytest.mark.django_db
def test_nivel_3_sin_publicadas_pero_con_ediciones_es_no_publicada(
    scope_service, edicion_borrador, edicion_cerrada
):
    """Hay ediciones pero ninguna publicada: la edición "no está publicada"."""
    with pytest.raises(EdicionNoPublicadaError):
        scope_service.resolver_actual()


# ── Nivel 4: sin resolución ────────────────────────────────────────────────


@pytest.mark.django_db
def test_nivel_4_sin_ediciones_es_no_resuelta(scope_service, db):
    with pytest.raises(EdicionNoResueltaError):
        scope_service.resolver_actual()


@pytest.mark.django_db
def test_nivel_4_con_operacion_administrativa_es_no_resuelta(
    scope_service, edicion_borrador
):
    """Sin default público, una operación administrativa NO cae sobre una edición.

    Nunca mutar inadvertidamente la edición equivocada: el default público
    queda desactivado y el resultado es un error explícito.
    """
    with pytest.raises(EdicionNoResueltaError):
        scope_service.resolver_actual(permitir_publicada_por_defecto=False)


# ── AISLAMIENTO entre ediciones ─────────────────────────────────────────────


@pytest.mark.django_db
def test_aislamiento_la_publicada_no_arrasta_a_la_cerrada(
    scope_service, edicion_publicada, edicion_cerrada, edicion_borrador
):
    """Dos ediciones del mismo evento: la resolución devuelve SÓLO la publicada."""
    resuelta = scope_service.resolver_actual()

    assert resuelta == edicion_publicada
    assert resuelta != edicion_cerrada
    assert resuelta != edicion_borrador


@pytest.mark.django_db
def test_aislamiento_el_historico_sigue_siendo_consultable(
    scope_service, edicion_publicada, edicion_cerrada
):
    """RN-E01: la edición cerrada se conserva y se puede leer por su id.

    El histórico no se borra al publicar otra edición, y consultarlo NO
    devuelve la edición vigente.
    """
    historica = scope_service.resolver_explicita(edicion_cerrada.id)

    assert historica == edicion_cerrada
    assert historica.estado == "CERRADA"
    assert historica != edicion_publicada


@pytest.mark.django_db
def test_aislamiento_las_ediciones_de_otro_evento_no_se_resuelven(
    scope_service, edicion_publicada, evento_otro
):
    """La edición publicada de otra familia no se cuela en la resolución."""
    ajena = Edicion.objects.create(
        evento=evento_otro,
        nombre="Ajena",
        slug="ajena",
        anio=2027,
        estado="PUBLICADA",
    )

    with pytest.raises(EdicionAmbiguaError):
        scope_service.resolver_actual()

    assert scope_service.resolver_explicita(ajena.id) == ajena
