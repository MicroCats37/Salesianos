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
"""

import re
from pathlib import Path

from core.contract_versions import SCHEMA_VERSIONS, hay_drift
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


def test_la_version_de_schema_coincide_con_el_registro_de_a0():
    """FR-07 §1.1: la versión del módulo vive en `presentation/schemas/`."""
    assert SCHEMA_VERSION == SCHEMA_VERSIONS["salesianos_fest"]
    assert not hay_drift(SCHEMA_VERSION, SCHEMA_VERSIONS["salesianos_fest"])


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
