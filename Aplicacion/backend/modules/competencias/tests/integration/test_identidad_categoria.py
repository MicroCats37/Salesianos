"""La CATEGORÍA es parte de la IDENTIDAD de una competencia.

GIVEN  una edición, una disciplina y dos categorías de esa edición
WHEN   se crean dos competencias con el MISMO nombre y la misma disciplina
       pero con categorías DISTINTAS, y una tercera con la misma
       cuaterna (edición, disciplina, categoría, nombre)
THEN   las dos primeras COEXISTEN —son dos cuadros distintos— y la tercera
       se rechaza: la identidad es de CUATRO partes (`RN-E01`, `RN-K01`).

Este fichero NO reimplementa ninguna regla del dueño de la inscripción: la
categoría es un hecho de `modules/salesianos_fest` y aquí sólo se REFERENCIA.

**EL MOTOR DE LA SUITE PLIEGA LAS MAYÚSCULAS SOLO EN ASCII.** SQLite —el
motor de las pruebas— compara `"Vóley"` y `"VÓLEY"` como nombres DISTINTOS:
`lower()` y `iexact` no pliegan el acento. PostgreSQL —el motor de
producción— sí lo pliega, y es MÁS estricto que el de las pruebas. Por eso la
identidad sin distinguir mayúsculas se comprueba aquí con un nombre ASCII (la
regla se verifica en CUALQUIER motor) y la variante acentuada se comprueba sólo
donde el motor la plega (`skipif`).
"""

from datetime import date

import pytest
from django.db import IntegrityError, connection, transaction

from modules.competencias.domain.exceptions import (
    CategoriaNoEncontradaError,
    CompetenciaDuplicadaError,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaCreateData,
)
from modules.competencias.domain.services.core.competencia_core_service import (
    CompetenciaCoreService,
)

pytestmark = pytest.mark.django_db(transaction=True)

#: Identificador que no corresponde a ninguna categoría.
CATEGORIA_INEXISTENTE = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
def core(injector):
    """El servicio core REAL de las competencias."""
    return injector.get(CompetenciaCoreService)


def _datos(edicion, disciplina, categoria, *, nombre="Vóley Mixto 2027"):
    """El `CompetenciaCreateData` de un torneo."""
    return CompetenciaCreateData(
        edicion_id=str(edicion.id),
        disciplina_id=str(disciplina.id),
        categoria_id=str(categoria),
        nombre=nombre,
        fecha=date(2027, 3, 14),
    )


# ── La identidad de CUATRO partes ────────────────────────────────────────────


def test_dos_competencias_de_la_misma_disciplina_y_categorias_distintas_coexisten(
    core,
    edicion_publicada,
    disciplina,
    categoria,
    categoria_2,
):
    """GIVEN dos categorías de la MISMA edición."""
    primera = core.crear(
        edicion_publicada,
        _datos(edicion_publicada, disciplina, categoria.id),
    )
    segunda = core.crear(
        edicion_publicada,
        _datos(edicion_publicada, disciplina, categoria_2.id),
    )

    # THEN son DOS torneos distintos: la categoría los separa.
    assert primera.id != segunda.id
    # La FK se escribe con el identificador que viaja en el DTO (texto), así
    # que se compara en su forma canónica.
    assert str(primera.categoria_id) == str(categoria.id)
    assert str(segunda.categoria_id) == str(categoria_2.id)


def test_la_misma_identidad_de_cuatro_partes_no_se_repite(
    core,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN una competencia ya creada en esa categoría."""
    core.crear(edicion_publicada, _datos(edicion_publicada, disciplina, categoria.id))

    # WHEN se intenta crear OTRA con la MISMA identidad.
    with pytest.raises(CompetenciaDuplicadaError):
        core.crear(edicion_publicada, _datos(edicion_publicada, disciplina, categoria.id))


def test_el_nombre_se_compara_sin_distinguir_mayusculas(
    core,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN una competencia con un nombre en minúsculas."""
    core.crear(
        edicion_publicada,
        _datos(edicion_publicada, disciplina, categoria.id, nombre="voley mixto 2027"),
    )

    # WHEN se intenta crear la MISMA identidad con otro ritmo de mayúsculas.
    with pytest.raises(CompetenciaDuplicadaError):
        core.crear(
            edicion_publicada,
            _datos(edicion_publicada, disciplina, categoria.id, nombre="VOLEY MIXTO 2027"),
        )


@pytest.mark.skipif(
    connection.vendor == "sqlite",
    reason=(
        "SQLite sólo pliega mayúsculas en el rango ASCII: 'VÓLEY' y 'Vóley' "
        "son nombres DISTINTOS para él. PostgreSQL (producción) sí los pliega, "
        "y es allí donde la identidad acentuada se puede comprobar."
    ),
)
def test_el_nombre_acentuado_se_compara_sin_distinguir_mayusculas(
    core,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN una competencia con un nombre acentuado en minúsculas."""
    core.crear(
        edicion_publicada,
        _datos(edicion_publicada, disciplina, categoria.id, nombre="vóley mixto 2027"),
    )

    # WHEN se intenta crear la MISMA identidad con el acento en mayúscula.
    with pytest.raises(CompetenciaDuplicadaError):
        core.crear(
            edicion_publicada,
            _datos(edicion_publicada, disciplina, categoria.id, nombre="VÓLEY MIXTO 2027"),
        )


def test_la_base_de_datos_rechaza_la_identidad_de_cuatro_partes_duplicada(
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN una competencia ya persistida con su categoría."""
    from modules.competencias.domain.models import Competencia

    persistida = Competencia.objects.create(
        edicion=edicion_publicada,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Voley Mixto 2027",
        fecha=date(2027, 3, 14),
    )

    # WHEN se inserta OTRA fila con la misma cuaterna.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Competencia.objects.create(
                edicion=edicion_publicada,
                disciplina=disciplina,
                categoria=categoria,
                nombre=persistida.nombre.upper(),
                fecha=persistida.fecha,
            )


@pytest.mark.skipif(
    connection.vendor == "sqlite",
    reason=(
        "SQLite sólo pliega mayúsculas en el rango ASCII: el índice único "
        "con `lower(nombre)` no ve el acento. PostgreSQL (producción) sí lo "
        "pliega, y es allí donde la identidad acentuada se puede comprobar."
    ),
)
def test_la_base_de_datos_rechaza_la_identidad_acentuada_duplicada(
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN una competencia con un nombre acentuado ya persistida."""
    from modules.competencias.domain.models import Competencia

    persistida = Competencia.objects.create(
        edicion=edicion_publicada,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Vóley Mixto 2027",
        fecha=date(2027, 3, 14),
    )

    # WHEN se inserta OTRA fila con la misma cuaterna.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Competencia.objects.create(
                edicion=edicion_publicada,
                disciplina=disciplina,
                categoria=categoria,
                nombre=persistida.nombre.upper(),
                fecha=persistida.fecha,
            )


# ── La categoría tiene que ser de la MISMA edición ──────────────────────────


def test_una_categoria_de_otra_edicion_no_sirve(
    core,
    edicion_publicada,
    disciplina,
    categoria_otra,
):
    """GIVEN una categoría que NO es de la edición de la competencia."""
    with pytest.raises(CategoriaNoEncontradaError) as error:
        core.crear(
            edicion_publicada,
            _datos(edicion_publicada, disciplina, categoria_otra.id),
        )

    # THEN el dominio rechaza la operación con su propio código.
    assert error.value.code == "CATEGORIA_NO_ENCONTRADA"


def test_una_categoria_inexistente_no_sirve(
    core,
    edicion_publicada,
    disciplina,
):
    """GIVEN una categoría que NO existe."""
    with pytest.raises(CategoriaNoEncontradaError):
        core.crear(
            edicion_publicada,
            _datos(edicion_publicada, disciplina, CATEGORIA_INEXISTENTE),
        )
