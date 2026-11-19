"""Modelo `Edicion`: invariantes de datos (FR-02 §3).

GIVEN  el contrato de datos congelado de la edición
WHEN   se crean ediciones y se ejercen sus invariantes
THEN   los defaults son los congelados, los slugs son únicos por evento y sólo
       puede existir una edición `PUBLICADA` por evento.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from modules.eventos.domain.constants import EstadoEdicion, ModuloLogico
from modules.eventos.domain.models import Edicion, Evento


@pytest.mark.django_db
def test_la_edicion_nace_en_borrador(db, evento):
    """GIVEN: una edición nueva WHEN: se crea THEN: su estado es BORRADOR."""
    edicion = Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
    )

    assert edicion.estado == EstadoEdicion.BORRADOR
    assert edicion.esta_publicada is False


@pytest.mark.django_db
def test_los_modulos_nacen_deshabilitados(db, evento):
    """RN-E02: el valor por defecto de cada módulo es DESHABILITADO."""
    edicion = Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
    )

    assert edicion.modulos_habilitados == []
    for modulo in ModuloLogico:
        assert edicion.modulo_habilitado(modulo.value) is False


@pytest.mark.django_db
def test_el_evento_tiene_su_propio_identificador_estable(db, evento):
    """FR-02 §2.1: el evento se identifica por `id` + `nombre` + `slug`."""
    assert evento.slug == "salesianos-fest"
    assert Evento.objects.filter(slug="salesianos-fest").count() == 1


@pytest.mark.django_db
def test_el_slug_es_unico_por_evento(db, evento):
    """GIVEN: una edición con un slug WHEN: se repite el slug THEN: IntegrityError."""
    Edicion.objects.create(evento=evento, nombre="A", slug="2026", anio=2026)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Edicion.objects.create(evento=evento, nombre="B", slug="2026", anio=2027)


@pytest.mark.django_db
def test_el_mismo_slug_puede_existir_en_otro_evento(db, evento, evento_otro):
    """GIVEN: dos eventos WHEN: ambos declaran el mismo slug de edición THEN: es válido.

    El slug de una edición es único DENTRO del evento, no en todo el sistema:
    dos familias de evento pueden tener la edición "2026".
    """
    Edicion.objects.create(evento=evento, nombre="A", slug="2026", anio=2026)
    Edicion.objects.create(evento=evento_otro, nombre="B", slug="2026", anio=2026)

    assert Edicion.objects.filter(slug="2026").count() == 2


@pytest.mark.django_db
def test_solo_una_edicion_publicada_por_evento(db, evento):
    """FR-02 §3: como máximo una edición PUBLICADA por evento.

    La `UniqueConstraint` condicional es la autoridad: la base de datos
    rechaza la segunda publicación aunque el código no la haya comprobado.
    """
    primera = Edicion.objects.create(
        evento=evento,
        nombre="A",
        slug="2026",
        anio=2026,
        estado=EstadoEdicion.PUBLICADA,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Edicion.objects.create(
                evento=evento,
                nombre="B",
                slug="2027",
                anio=2027,
                estado=EstadoEdicion.PUBLICADA,
            )

    assert Edicion.objects.filter(
        evento=evento,
        estado=EstadoEdicion.PUBLICADA,
    ).count() == 1
    assert primera.esta_publicada is True


@pytest.mark.django_db
def test_cada_evento_puede_tener_su_propia_publicada(db, evento, evento_otro):
    """Dos eventos distintos pueden estar publicados a la vez (familias)."""
    Edicion.objects.create(
        evento=evento,
        nombre="A",
        slug="2026",
        anio=2026,
        estado=EstadoEdicion.PUBLICADA,
    )
    Edicion.objects.create(
        evento=evento_otro,
        nombre="B",
        slug="2026",
        anio=2026,
        estado=EstadoEdicion.PUBLICADA,
    )

    assert Edicion.objects.filter(estado=EstadoEdicion.PUBLICADA).count() == 2


@pytest.mark.django_db
def test_el_validador_rechaza_claves_de_modulo_desconocidas(db, evento):
    """Una clave que no pertenece al catálogo no es un módulo nuevo silencioso."""
    edicion = Edicion(
        evento=evento,
        nombre="A",
        slug="2026",
        anio=2026,
        modulos_habilitados=["inscripciones", "modulo_inventado"],
    )

    with pytest.raises(ValidationError):
        edicion.full_clean()


@pytest.mark.django_db
def test_el_validador_acepta_las_claves_del_catalogo(db, evento):
    edicion = Edicion(
        evento=evento,
        nombre="A",
        slug="2026",
        anio=2026,
        modulos_habilitados=[ModuloLogico.INSCRIPCIONES.value],
    )

    edicion.full_clean()

    assert edicion.modulo_habilitado(ModuloLogico.INSCRIPCIONES.value) is True
    assert edicion.modulo_habilitado(ModuloLogico.MARKETPLACE.value) is False


@pytest.mark.django_db
def test_el_contrato_minimo_de_datos_esta_completo(db, evento):
    """FR-02 §3: los campos del contrato de datos mínimo están presentes."""
    edicion = Edicion.objects.create(
        evento=evento,
        nombre="A",
        slug="2026",
        anio=2026,
    )

    for campo in (
        "id",
        "evento_id",
        "nombre",
        "slug",
        "anio",
        "estado",
        "modulos_habilitados",
        "fecha_inicio",
        "fecha_fin",
        "created_at",
        "updated_at",
    ):
        assert hasattr(edicion, campo), campo


@pytest.mark.django_db
def test_las_fechas_son_nulables_sin_semantica(db, evento):
    """GOV-01-OPEN-03: las fechas de la edición no tienen semántica aprobada."""
    edicion = Edicion.objects.create(
        evento=evento,
        nombre="A",
        slug="2026",
        anio=2026,
    )

    assert edicion.fecha_inicio is None
    assert edicion.fecha_fin is None
