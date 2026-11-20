"""Registro de versiones del contrato HTTP (presenters / schemas).

Freeze: `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

La versión **no** es un campo del wire. Es un registro que A0 mantiene y que
ambos lados declaran:

| Elemento | Ubicación en el objetivo | Owner |
|---|---|---|
| Registro global de versiones | `core/contract_versions.py` (este archivo) | A0 |
| Versión del envelope | `ENVELOPE_VERSION` (este archivo) | A0 |
| Versión por módulo | `modules/<modulo>/presentation/schemas/__init__.py` → `SCHEMA_VERSION` | Dueño del módulo |
| Presenter asociado | `modules/<modulo>/presentation/presenters/<modulo>_presenter.py` | Dueño del módulo |
| Espejo frontend | `features/<dominio>/schemas/<dominio>.schema.ts` → `export const SCHEMA_VERSION` | A7 |

Semántica (FR-07 §1.2):

| Cambio | Versión |
|---|---|
| Se **elimina** o **renombra** un campo, se cambia su tipo, se elimina un endpoint o un wrapper | **MAJOR** |
| Se **agrega** un campo opcional, un endpoint nuevo, un wrapper nuevo | **MINOR** |
| Corrección editorial, mensaje público, documentación | **PATCH** |

Detección de drift: un test de contrato compara la versión declarada en el
espejo Zod con la de este registro y falla si difieren. La función
`hay_drift` es la primitiva que usan esos tests.
"""

from __future__ import annotations

# ── Envelope ─────────────────────────────────────────────────────────────────

#: Versión del envelope de éxito / error / paginación.
ENVELOPE_VERSION = "1.0.0"

# ── Módulos ──────────────────────────────────────────────────────────────────

#: Versión congelada por módulo (FR-07 §2).
#:
#: La clave es el NOMBRE FÍSICO del módulo en el objetivo (`modules/<clave>`),
#: no el nombre del dominio en el ledger: `salesianos_fest` es el módulo que
#: implementa el dominio `inscripciones` (A0-06 del paquete DOM-01).
SCHEMA_VERSIONS: dict[str, str] = {
    "envelope": ENVELOPE_VERSION,
    "eventos": "1.0.0",
    "usuarios": "1.1.0",
    "commerce": "1.0.0",
    "pagos": "1.0.0",
    "pases": "1.0.0",
    "beneficios": "1.0.0",
    "validaciones": "1.0.0",
    "marketplace": "1.2.0",
    "patrocinadores": "1.0.0",
    # DOM-07 · Reconciliación A0 de 2026-11-19 (cierre del cableado global):
    # el módulo `competencias` declara `SCHEMA_VERSION` en
    # `modules/competencias/presentation/schemas/__init__.py`. Sin esta
    # entrada NO hay mecanismo de detección de drift entre el contrato del
    # backend y su espejo Zod (FR-07 §1.3).
    #
    # A0 · Reconciliación de 2026-11-20 (cierre de la RESTAURACIÓN DE LA
    # CATEGORÍA, cambio `restore-registration-promotion-catalog-flow`): el
    # módulo `competencias` subió a `2.0.0` (MAJOR, ROMPEDOR) porque el alta
    # `POST /api/competencias` exige `categoria_id` (ENTRADA OBLIGATORIA
    # nueva: la identidad pasa de tres partes a cuatro — edición, disciplina,
    # categoría, nombre) y las salidas publican `categoria_id` y
    # `categoria_nombre`. El registro global es de A0 y refleja la versión que
    # DECLARA el módulo: mientras no se actualice, el test de drift de
    # `core/tests/integration/test_contract_versions.py` falla
    # (`hay_drift('2.0.0', '1.0.0')`).
    "competencias": "2.0.0",
    # DOM-01 · Reconciliación A0 de 2026-11-19 (A0-06): el módulo declara
    # `SCHEMA_VERSION = "1.0.0"` y el registro global es de A0.
    #
    # DOM-03 · Reconciliación A0 de 2026-11-19 (A0-02): el módulo `salesianos_fest`
    # subió a `1.2.0` (MINOR, ADITIVO) con el dominio de pases, beneficiarios y
    # cortesía — diez rutas nuevas, ninguna forma de respuesta eliminada ni
    # renombrada. DOM-02 (pool de cupos, `1.1.0`) queda subsumido en este valor.
    #
    # A0 · Corrección de los residuales de VER-01 (2026-11-20): el cambio
    # `restore-registration-promotion-catalog-flow` subió el módulo a `2.0.0`
    # (MAJOR, ROMPEDOR) por tres hechos: `POST /api/inscripciones` exige dos
    # campos NUEVOS y obligatorios (`promocion_id` y `cantidad`),
    # `InscripcionDetalleOut` publica dos hechos NUEVOS y obligatorios
    # (`promocion` y la `categoria` derivada por el servidor) y se AÑADEN tres
    # rutas (`GET /api/catalogo/promociones`, `GET /api/catalogo/categorias` y
    # `POST /api/cotizaciones`). El registro global es de A0 y refleja la
    # versión que DECLARA el módulo: mientras no se actualice, el test de
    # drift de `core/tests/integration/test_contract_versions.py` falla
    # (`hay_drift('2.0.0', '1.2.0')`).
    "salesianos_fest": "2.0.0",
    # XCT-02 · Reconciliación A0 de 2026-11-20 (cierre del cableado global):
    # el módulo `administracion` declara `SCHEMA_VERSION = "1.0.0"` en
    # `modules/administracion/presentation/schemas/__init__.py`. Sin esta
    # entrada NO hay mecanismo de detección de drift entre el contrato del
    # backend y el de su módulo dueño (FR-07 §1.3): el panel publicaría
    # formas nuevas sin que nadie lo notara.
    "administracion": "1.0.0",
    # `public-video-streaming-crud` (2026-11-20): el módulo `videos` declara
    # `SCHEMA_VERSION = "1.0.0"` en
    # `modules/videos/presentation/schemas/__init__.py`. Sin esta entrada NO
    # hay mecanismo de detección de drift entre el contrato del backend y su
    # espejo Zod (FR-07 §1.3).
    "videos": "1.0.0",
}


def schema_version(modulo: str) -> str:
    """Versión congelada de un módulo.

    Lanza `KeyError` si el módulo no está en el registro: un módulo sin
    versión declarada es un módulo que todavía no consumió su freeze.
    """
    return SCHEMA_VERSIONS[modulo]


def modulos_registrados() -> tuple[str, ...]:
    """Módulos que ya declararon versión."""
    return tuple(sorted(SCHEMA_VERSIONS))


# ── Semver ───────────────────────────────────────────────────────────────────


def comparar_versiones(izquierda: str, derecha: str) -> int:
    """Compara dos versiones semver.

    Devuelve `-1` si `izquierda` < `derecha`, `0` si son iguales y `1` si
    `izquierda` > `derecha`. Componentes no numéricos se comparan como texto.
    """
    partes_izquierda = _partes(izquierda)
    partes_derecha = _partes(derecha)
    for a, b in zip(partes_izquierda, partes_derecha):
        if a == b:
            continue
        if isinstance(a, int) and isinstance(b, int):
            return -1 if a < b else 1
        return -1 if str(a) < str(b) else 1
    if len(partes_izquierda) == len(partes_derecha):
        return 0
    return -1 if len(partes_izquierda) < len(partes_derecha) else 1


def _partes(version: str) -> list:
    partes = []
    for bruto in str(version).split("."):
        try:
            partes.append(int(bruto))
        except ValueError:
            partes.append(bruto)
    return partes


def tipo_de_cambio(actual: str, nueva: str) -> str:
    """Clasifica el cambio entre dos versiones: `MAJOR`, `MINOR`, `PATCH` o `NONE`."""
    if actual == nueva:
        return "NONE"
    comparacion = comparar_versiones(actual, nueva)
    if comparacion >= 0:
        # Una versión que baja o se reescribe es un cambio MAJOR por definición
        # de contrato: el cliente puede depender de lo que se eliminó.
        return "MAJOR"
    partes_actual = _partes(actual)
    partes_nueva = _partes(nueva)
    if partes_actual[0] != partes_nueva[0]:
        return "MAJOR"
    if len(partes_actual) > 1 and len(partes_nueva) > 1 and partes_actual[1] != partes_nueva[1]:
        return "MINOR"
    return "PATCH"


def hay_drift(actual: str, declarada: str) -> bool:
    """Si la versión declarada difiere de la congelada."""
    return actual != declarada


__all__ = [
    "ENVELOPE_VERSION",
    "SCHEMA_VERSIONS",
    "comparar_versiones",
    "hay_drift",
    "modulos_registrados",
    "schema_version",
    "tipo_de_cambio",
]
