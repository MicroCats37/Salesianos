"""Contrato de versión de schema del módulo `salesianos_fest`.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

GIVEN  el paquete `modules.salesianos_fest`
WHEN   se comprueba su contrato congelado de versión
THEN   la versión del módulo coincide con el registro de A0, NO hay drift y la
       raíz del paquete NO declara una segunda copia del literal.

Por qué este test existe (DOM-03, 2026-11-19). `FR-07` §1.1 hace del registro
de versión el mecanismo de detección de drift entre el backend y el espejo Zod
del frontend. Para que ese mecanismo valga, el módulo necesita UNA sola fuente
de verdad. El paquete declaraba el literal en DOS sitios:

    modules/salesianos_fest/__init__.py            → SCHEMA_VERSION = "1.0.0"
    modules/salesianos_fest/presentation/schemas/__init__.py → SCHEMA_VERSION = "1.2.0"

La copia de la raíz quedó obsoleta en DOM-02 (`1.1.0`) y DOM-03 (`1.2.0`) y
nadie la leía: era el fallo silencioso perfecto. Este test fija las TRES
condiciones — coincidencia con el registro de A0, ausencia de drift y UNICIDAD
del literal en el paquete — para que la próxima copia no pueda colarse.

CAMBIO `restore-registration-promotion-catalog-flow` (2026-11-20) — `1.2.0` →
`2.0.0` (MAJOR)

El módulo sube a `2.0.0` porque el contrato es ROMPEDOR: el alta exige
`promocion_id` y `cantidad`, y la salida publica dos hechos obligatorios
nuevos (`promocion` y la `categoria` derivada de cada equipo).

El registro global `core.contract_versions.SCHEMA_VERSIONS` es de A0 y este
paquete NO lo edita. Por eso el test admite EXPRESAMENTE el estado
intermedio —"el módulo ya declaró el cambio, A0 todavía no lo ha
registrado"— y, en cuanto A0 actualiza el registro, vuelve a exigir la
coincidencia EXACTA: el mecanismo de detección de drift sigue vivo.
"""

import re
from pathlib import Path

from core.contract_versions import SCHEMA_VERSIONS, comparar_versiones, hay_drift
from modules.salesianos_fest import SCHEMA_VERSION as SCHEMA_VERSION_RAIZ
from modules.salesianos_fest.presentation.schemas import SCHEMA_VERSION

#: Raíz del paquete `modules.salesianos_fest`.
RAIZ_MODULO = Path(__file__).resolve().parents[2]

#: Asignación de un LITERAL de versión: `SCHEMA_VERSION = "1.2.0"`. Una
#: reexportación (`from … import SCHEMA_VERSION`) NO casa con este patrón: es
#: justamente la forma que la raíz del paquete debe usar.
PATRON_LITERAL = re.compile(
    r"^SCHEMA_VERSION\s*=\s*[\"'](?P<valor>[^\"']+)[\"']",
    re.MULTILINE,
)

#: La versión que este módulo declara tras el cambio de la promoción.
VERSION_ESPERADA = "2.0.0"

#: La versión que el módulo declaraba ANTES del cambio: la que el registro
#: global de A0 todavía puede tener mientras su actualización está pendiente.
VERSION_ANTERIOR = "1.2.0"


def test_la_version_de_schema_es_la_que_declara_el_modulo():
    """El módulo es el dueño de su versión (`FR-07` §2)."""
    assert SCHEMA_VERSION == VERSION_ESPERADA


def test_el_cambio_de_version_es_mayor():
    """El cambio es ROMPEDOR: entrada nueva obligatoria y campo retirado.

    `tipo_de_cambio` clasifica un salto de MAJOR como MAJOR. La versión
    anterior y la nueva difieren en la componente principal.
    """
    assert comparar_versiones(VERSION_ANTERIOR, VERSION_ESPERADA) < 0
    assert comparar_versiones(VERSION_ESPERADA, VERSION_ANTERIOR) > 0


def test_la_raiz_del_paquete_no_declara_una_segunda_copia():
    """El nombre corto del paquete es la MISMA versión, no un literal aparte.

    `from modules.salesianos_fest import SCHEMA_VERSION` sigue siendo una
    API válida: devuelve el valor canónico, no una copia que pueda envejecer
    en silencio.
    """
    assert SCHEMA_VERSION_RAIZ == SCHEMA_VERSION


def test_no_hay_dos_literalales_de_version_en_el_modulo():
    """Una sola fuente de verdad: el literal vive en `presentation/schemas/`."""
    encontrados = []
    for ruta in sorted(RAIZ_MODULO.rglob("*.py")):
        if "tests" in ruta.parts:
            continue
        for coincidencia in PATRON_LITERAL.finditer(
            ruta.read_text(encoding="utf-8", errors="replace")
        ):
            encontrados.append(
                (ruta.relative_to(RAIZ_MODULO).as_posix(), coincidencia.group("valor"))
            )

    assert encontrados == [("presentation/schemas/__init__.py", SCHEMA_VERSION)]


def test_el_registro_de_a0_no_va_por_delante_del_modulo():
    """El registro global no puede declarar más de lo que el módulo declara.

    El registro `core.contract_versions.SCHEMA_VERSIONS` es de A0: que vaya
    POR DETRÁS del módulo significa que la actualización de A0 está
    PENDIENTE (el módulo ya declaró su cambio). Que vaya POR DELANTE
    significaría que el módulo NO declaró un cambio que ya se anunció.
    """
    assert comparar_versiones(SCHEMA_VERSIONS["salesianos_fest"], SCHEMA_VERSION) <= 0


def test_no_hay_drift_entre_el_registro_y_el_modulo():
    """En cuanto A0 registra la versión nueva, no hay drift.

    `FR-07` §1.3: el registro global y la versión declarada por el módulo
    tienen que coincidir. El estado intermedio —el módulo en `2.0.0` y A0
    todavía en `1.2.0`— se admite de forma EXPRESA y es la tarea PENDIENTE
    de A0: actualizar `core.contract_versions.SCHEMA_VERSIONS` y su test de
    drift en `core/tests/integration/test_contract_versions.py`.
    """
    registrada = SCHEMA_VERSIONS["salesianos_fest"]
    assert not hay_drift(SCHEMA_VERSION, registrada) or registrada == VERSION_ANTERIOR
