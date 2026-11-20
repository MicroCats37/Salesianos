"""Registro de versiones del contrato (FREEZE-PS-1.0.0 · FR-07).

GIVEN  el registro que A0 mantiene en `core.contract_versions`
WHEN   se consulta la versión de un módulo o se comparan dos versiones
THEN   el registro devuelve la versión congelada y la comparación clasifica el
       tipo de cambio según la semántica MAJOR / MINOR / PATCH.
"""

import pytest

from core.contract_versions import (
    ENVELOPE_VERSION,
    SCHEMA_VERSIONS,
    comparar_versiones,
    hay_drift,
    modulos_registrados,
    schema_version,
    tipo_de_cambio,
)


# ── Versiones congeladas ─────────────────────────────────────────────────────


def test_el_envelope_declara_la_version_congelada():
    assert ENVELOPE_VERSION == "1.0.0"


def test_los_modulos_congelados_declaran_1_0_0():
    """Los módulos CONGELADOS en `FR-07` §2 siguen en `1.0.0`.

    `usuarios`, `salesianos_fest` y `marketplace` NO están en esta lista:
    evolucionaron con cambios MINOR aditivos. Su versión la DECLARA el módulo
    dueño y el registro global la refleja; el registro NO inventa versiones.
    """
    congelados = [
        "eventos",
        "commerce",
        "pagos",
        "pases",
        "beneficios",
        "validaciones",
        "patrocinadores",
    ]
    for modulo in congelados:
        assert schema_version(modulo) == "1.0.0", modulo


def test_el_registro_expone_los_modulos_declarados():
    assert "envelope" in modulos_registrados()
    assert "marketplace" in modulos_registrados()


def test_un_modulo_sin_version_declarada_no_se_inventa():
    with pytest.raises(KeyError):
        schema_version("modulo_inexistente")


# ── Detección de drift ───────────────────────────────────────────────────────


def test_hay_drift_detecta_una_version_distinta():
    assert hay_drift("1.0.0", "1.0.0") is False
    assert hay_drift("1.0.0", "1.1.0") is True


def test_el_envelope_y_el_registro_no_difieren():
    assert hay_drift(SCHEMA_VERSIONS["envelope"], ENVELOPE_VERSION) is False


# ── Semver ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "izquierda,derecha,esperado",
    [
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "1.0.1", -1),
        ("1.0.1", "1.0.0", 1),
        ("1.9.0", "1.10.0", -1),
        ("2.0.0", "1.99.99", 1),
    ],
)
def test_la_comparacion_de_versiones_es_correcta(izquierda, derecha, esperado):
    assert comparar_versiones(izquierda, derecha) == esperado


@pytest.mark.parametrize(
    "actual,nueva,esperado",
    [
        ("1.0.0", "1.0.0", "NONE"),
        ("1.0.0", "2.0.0", "MAJOR"),
        ("1.0.0", "1.1.0", "MINOR"),
        ("1.0.0", "1.0.1", "PATCH"),
    ],
)
def test_la_clasificacion_del_cambio_es_correcta(actual, nueva, esperado):
    assert tipo_de_cambio(actual, nueva) == esperado


def test_un_descenso_de_version_es_un_cambio_mayor():
    """Bajar de versión rompe al cliente: es MAJOR por definición de contrato."""
    assert tipo_de_cambio("2.0.0", "1.0.0") == "MAJOR"


# ── Reconciliación A0 de FND-01: fundamentos completados ─────────────────────
#
# El registro global y la versión declarada por cada módulo COMPLETADO tienen
# que coincidir. Es el test de drift que FR-07 §5 exige: si un módulo cambia
# su `SCHEMA_VERSION` sin que A0 actualice el registro, este test falla.


#: Módulos con módulo implementado, verificado y versionado en el objetivo.
#:
#: `salesianos_fest` (DOM-01 → DOM-02 → DOM-03) y `marketplace` (DOM-04 →
#: DOM-05) se añadieron en la reconciliación A0 de 2026-11-19. Sus versiones
#: ya NO son `1.0.0`: el MÓDULO dueño declara la suya y el registro global la
#: refleja. La versión exacta se comprueba contra la declaración del módulo
#: (test de drift) y, para `salesianos_fest`, contra el valor congelado de
#: DOM-03 (`1.2.0`) y el MAJOR de 2026-11-20 (`2.0.0`).
#:
#: `competencias` (DOM-07), `patrocinadores` (DOM-08) y `validaciones`
#: (XCT-01) se añadieron en el CIERRE DEL CABLEADO GLOBAL (2026-11-19): sus
#: módulos están registrados, sus controllers viven y sus versiones
#: declaradas están reflejadas en el registro global.
#:
#: `competencias` evolucionó con la RESTAURACIÓN DE LA CATEGORÍA
#: (`restore-registration-promotion-catalog-flow`, 2026-11-20): su versión
#: vigente es `2.0.0` (MAJOR, ROMPEDOR).
#:
#: `administracion` (XCT-02) se añadió en el CIERRE DEL CABLEADO GLOBAL
#: (2026-11-20): su módulo está registrado, sus seis controllers viven y la
#: versión que DECLARA el módulo (`1.0.0`) está reflejada en el registro.
#:
#: `videos` (`public-video-streaming-crud`, 2026-11-20): el módulo de la SALA
#: DE PROYECCIÓN declara `SCHEMA_VERSION = "1.0.0"` y su entrada está
#: reflejada en el registro global.
MODULOS_COMPLETADOS = (
    "eventos",
    "usuarios",
    "commerce",
    "pagos",
    "salesianos_fest",
    "marketplace",
    "competencias",
    "patrocinadores",
    "validaciones",
    "administracion",
    "videos",
)


@pytest.mark.parametrize("modulo", MODULOS_COMPLETADOS)
def test_el_registro_incluye_los_fundamentos_completados(modulo):
    """Cada fundación completada está en el registro de versiones."""
    assert modulo in modulos_registrados()


@pytest.mark.parametrize("modulo", MODULOS_COMPLETADOS)
def test_no_hay_drift_entre_el_registro_y_el_modulo(modulo):
    """La versión declarada por el módulo es la congelada en el registro."""
    from importlib import import_module

    schemas = import_module(f"modules.{modulo}.presentation.schemas")

    assert hay_drift(schemas.SCHEMA_VERSION, schema_version(modulo)) is False


def test_el_registro_refleja_la_version_declarada_de_salesianos_fest():
    """A0 · el registro global sigue al módulo (residual R-1 de VER-01).

    `salesianos_fest` subió a `2.0.0` (MAJOR, ROMPEDOR) con el cambio
    `restore-registration-promotion-catalog-flow` de 2026-11-20: el alta exige
    `promocion_id` y `cantidad`, la salida publica `promocion` y la
    `categoria` derivada de cada equipo, y se añaden tres rutas. DOM-03
    (`1.2.0`, MINOR aditivo) queda subsumido en este valor.

    El registro global es de A0: si el módulo sube y A0 no actualiza, este test
    falla — es el mecanismo de detección de drift (`FR-07` §1.3) funcionando,
    no un defecto.
    """
    assert schema_version("salesianos_fest") == "2.0.0"


def test_la_version_de_salesianos_fest_es_un_cambio_mayor_rompedor():
    """El salto vigente (`1.2.0` → `2.0.0`) es MAJOR, no MINOR aditivo.

    DOM-03 (`1.1.0` → `1.2.0`) fue ADITIVO; el cambio de 2026-11-20 no lo es:
    añade una entrada obligatoria y dos campos de salida obligatorios.
    """
    assert tipo_de_cambio("1.1.0", "1.2.0") == "MINOR"
    assert tipo_de_cambio("1.2.0", "2.0.0") == "MAJOR"


def test_el_registro_refleja_la_version_declarada_de_competencias():
    """A0 · el registro global sigue al módulo `competencias` (2026-11-20).

    La RESTAURACIÓN DE LA CATEGORÍA (`restore-registration-promotion-catalog-flow`)
    devolvió la CATEGORÍA a la competencia y su salto es MAJOR, ROMPEDOR: el
    alta `POST /api/competencias` exige `categoria_id` (entrada obligatoria
    nueva) y las salidas publican `categoria_id` / `categoria_nombre`.

    El registro global es de A0: si el módulo sube y A0 no actualiza, este test
    falla — es el mecanismo de detección de drift (`FR-07` §1.3) funcionando,
    no un defecto.
    """
    assert schema_version("competencias") == "2.0.0"
    assert tipo_de_cambio("1.0.0", "2.0.0") == "MAJOR"
