# CORR-VER01-A0 · Residuales de backend de VER-01 (R-1 y R-2) corregidos

**Artifact:** `evidence/corrections/CORR-VER01-A0-residuales-backend.md` ·
**Change:** `salesianos-fest-rebuild` · **Owner:** A0 (cableado) ·
**Modo:** apply correctivo · **Store:** engram + evidencia física · **Fecha:** 2026-11-20

> **ESTADO: `applied` — los DOS residuales de backend medidos por VER-01 §7.1
> (R-1 y R-2) están corregidos y la suite COMPLETA del backend está VERDE.**
>
> **`STATE.md` NO se editó**: esta corrección corre en PARALELO con otra del
> mismo VER-01; el dueño de VER-01 reconcilia el tablero compartido cuando las
> dos terminen.

---

## 1. Qué se corrigió (y por qué)

Los dos residuales de `CORR-VER01-backend-blockers.md` §7.1 eran, ambos,
**deuda de A0** que ese packet no podía pagar (sus archivos estaban fuera de
sus raíces y los acababa de tocar un agente concurrente). Este packet los
cierra, y **nada más**: no toca módulos, frontend, contratos ni `STATE.md`.

| # | Residual medido | Corrección | Dueño |
|---:|---|---|---|
| **R-1** | `core/tests/integration/test_contract_versions.py::test_no_hay_drift_entre_el_registro_y_el_modulo[salesianos_fest]` ⇒ `hay_drift('2.0.0', '1.2.0')` | `core/contract_versions.py` → `SCHEMA_VERSIONS["salesianos_fest"] = "2.0.0"` + su test de paridad actualizado | A0 |
| **R-2** | `core/tests/integration/test_exceptions_public_catalog.py::test_todo_codigo_de_dominio_esta_en_el_catalogo_publico` ⇒ `PrecioCambiadoError → PRECIO_CAMBIADO` sin catalogar | `core/exceptions.py` → `PUBLIC_ERROR_MESSAGES["PRECIO_CAMBIADO"]` + 3 pruebas focales nuevas | A0 |

### 1.1 R-1 · El registro global seguía a `1.2.0` (fuente CONFIRMADA)

El módulo **declara** `SCHEMA_VERSION = "2.0.0"` en su fuente canónica
(`modules/salesianos_fest/presentation/schemas/__init__.py:52`), y su propio
docstring documenta el MAJOR de 2026-11-20
(`restore-registration-promotion-catalog-flow`) por tres hechos: entrada
obligatoria nueva (`promocion_id`, `cantidad`), dos hechos de salida nuevos y
obligatorios (`promocion`, `categoria` derivada) y tres rutas añadidas.

El registro global de A0 (`core/contract_versions.py`) seguía en `"1.2.0"`:
el mecanismo de detección de drift (`FR-07` §1.3) hizo exactamente su trabajo
— avisar de que el contrato del módulo ya no es el que el registro congela.
**El registro NO inventa versiones**: refleja la que DECLARA el dueño del
módulo, así que se alineó a `2.0.0` (no se tocó el módulo).

`modules/salesianos_fest/tests/integration/test_contrato_schema_version.py`
(fuera de las raíces de este packet, **NO** editado) admite el estado
intermedio de forma expresa (`registrada == VERSION_ANTERIOR`) y sigue
verde: con el registro ya en `2.0.0` la condición "no hay drift" se cumple
por la rama principal.

### 1.2 R-2 · `PRECIO_CAMBIADO` no tenía prosa pública

`modules.salesianos_fest.domain.exceptions.PrecioCambiadoError` declara el
código estable `PRECIO_CAMBIADO` (409, `ConflictError`) y **PIDE** su prosa a
A0 ("Código REQUESTED a A0"). Sin entrada en el catálogo, la respuesta
caía al mensaje **GENÉRICO** del status 409 ("Conflicto con el estado actual
del recurso."): seguro, pero no distinguible de cualquier otro conflicto.

La prosa se añadió en la sección que el propio catálogo ya reserva a los
códigos de `modules.salesianos_fest` que piden texto a A0 ("Promociones,
categorías y cotización"), con las convenciones del catálogo:

- **prosa FIJA**: no interpola `{`, `}`, `%` ni `$` (ni precios, ni importes,
  ni ids, ni slugs, ni texto crudo de la excepción);
- **409** explícito en el comentario, igual que el resto de la sección;
- la **siguiente acción segura** (volver a cotizar) es lo que el cliente
  necesita: es la categoría "Concurrency" del contrato de wrappers (§8).

```
"PRECIO_CAMBIADO": (
    "El precio del paquete cambió desde la cotización. Vuelve a cotizar."
),
```

---

## 2. Ficheros cambiados (4 modificados) — TODOS dentro de las raíces permitidas

| Fichero | Acción | Qué |
|---|---|---|
| `Aplicacion/backend/core/contract_versions.py` | modificado | `SCHEMA_VERSIONS["salesianos_fest"]`: `"1.2.0"` → `"2.0.0"` + comentario del MAJOR de 2026-11-20 (el motivo del salto queda en la fuente, no en un literal) |
| `Aplicacion/backend/core/exceptions.py` | modificado | `PUBLIC_ERROR_MESSAGES["PRECIO_CAMBIADO"]` (409) con prosa fija en la sección de códigos de `salesianos_fest` que piden prosa a A0 |
| `Aplicacion/backend/core/tests/integration/test_contract_versions.py` | modificado | `test_el_registro_refleja_la_version_declarada_de_salesianos_fest` → `"2.0.0"`; `test_la_version_de_salesianos_fest_es_un_cambio_minor_aditivo` → `…_es_un_cambio_mayor_rompedor` (el salto vigente es MAJOR: `1.2.0` → `2.0.0`; DOM-03 `1.1.0` → `1.2.0` sigue siendo MINOR y se conserva como aserción) |
| `Aplicacion/backend/core/tests/integration/test_exceptions_public_catalog.py` | modificado | **3 pruebas focales nuevas** para `PRECIO_CAMBIADO`: presencia en catálogo, prosa fija y atado catálogo ↔ clase de dominio (`PrecioCambiadoError` · `PRECIO_CAMBIADO` · 409) |

**Fuera de las raíces permitidas: NADA.** Cero cambios en `contract/**`,
`Aplicacion/plan/**`, `Aplicacion/documentacion/**`, `Aplicacion/backend/modules/**`,
frontend, `STATE.md` ni los **raíces congelados** (`backend/**`, `frontend/**`,
`worker/**`, `proxy/**`). Cero `git stash` / `reset` / `checkout` / `commit` /
`push`. Cero instalaciones: `uv run --group dev` exclusivamente.

---

## 3. Comandos / códigos de salida (workdir `Aplicacion/backend`)

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| C1 | `uv run --group dev python -m pytest core/tests/integration/test_contract_versions.py core/tests/integration/test_exceptions_public_catalog.py -q` (**ANTES** del cambio) | **1** | **2 failed, 179 passed** — **RED medido**: exactamente R-1 y R-2, con los mismos mensajes de VER-01 §7.1 |
| C2 | el mismo (**DESPUÉS** del cambio) | **0** | **184 passed** (179 previos + 5 nuevas: 3 de catálogo + 2 reescritas de paridad) |
| C3 | `uv run --group dev python -m pytest core/tests modules/salesianos_fest/tests/integration/test_contrato_schema_version.py modules/salesianos_fest/tests/integration/test_precio_por_persona.py modules/marketplace/tests/integration/test_producto_contrato.py modules/eventos/tests/test_contrato_eventos.py modules/patrocinadores/tests/integration/test_patrocinadores_contrato.py -q` | **0** | **308 passed** — `core/**` completo + los **cinco** consumidores del registro de versiones (los cuatro módulos con test de drift + el contrato del módulo tocado) |
| C4 | `uv run --group dev python -m pytest modules core -q` (**suite COMPLETA del backend**) | **0** | **974 passed**, 665 warnings, 186.89 s — **CERO fallos** (antes: `2 failed, 969 passed`, VER-01/CORR-VER01 C14) |
| C5 | `uv run --group dev python -m pytest --collect-only -q` (raíz) | **0** | **974 tests collected**, **0 errores de recolección** |
| C6 | `uv run --group dev python manage.py check --settings=config.settings.test` | **0** | `System check identified no issues (0 silenced).` |
| C7 | `uv run --group dev python manage.py makemigrations --check --dry-run --settings=config.settings.test` | **0** | `No changes detected` |

**Comandos NO ejecutados (y por qué):** `next build` · `npm install` ·
navegador · auditoría de cinco anchos · suite de frontend · **lane PostgreSQL**
de `BL-05` §2 (no hay PostgreSQL en este entorno: los casos de concurrencia
`QA-V02` / `QA-I05` corren sobre SQLite, donde `select_for_update` es un
**NO-OP** — el riesgo que XCT-01 §7.1 declaró **sigue ABIERTO**) ·
`git stash` / `commit` / `reset` / `checkout` · `uv sync` · Python global.

---

## 4. Prueba RED (el defecto estaba ahí y la prueba lo caza)

El RED **no** se fabricó a posteriori: es la línea base medida sobre el árbol
concurrente, ANTES de editar (C1). Los dos fallos son **exactamente** los
residuales R-1 y R-2 de `CORR-VER01-backend-blockers.md` §7.1:

```
FAILED core/tests/integration/test_contract_versions.py::test_no_hay_drift_entre_el_registro_y_el_modulo[salesianos_fest]
E   AssertionError: assert True is False
E    +  where True = hay_drift('2.0.0', '1.2.0')
E    +    where '2.0.0' = <module 'modules.salesianos_fest.presentation.schemas'>SCHEMA_VERSION
E    +    and '1.2.0' = schema_version('salesianos_fest')

FAILED core/tests/integration/test_exceptions_public_catalog.py::test_todo_codigo_de_dominio_esta_en_el_catalogo_publico
E   AssertionError: Códigos sin catalogar: ['modules.salesianos_fest.domain.exceptions.PrecioCambiadoError → PRECIO_CAMBIADO']

2 failed, 179 passed in 1.36s
```

Después de aplicar la corrección (C2) la misma línea base da **184 passed**
y la suite completa (C4) da **974 passed, 0 failed**.

---

## 5. Residuales que QUEDAN (ninguno bloquea el backend)

| # | Residuo | Gravedad | Dueño |
|---:|---|---|---|
| **X-1** | **Lane PostgreSQL**: los casos de concurrencia (`QA-V02`, `QA-I05`) corren sobre SQLite, donde `select_for_update` es un **NO-OP**. El riesgo de concurrencia real (`RN-C02`, precio-vs-cotización) **no** está probado en un motor con bloqueo de filas. | **ENTORNO** (no bloqueante de VER-02) | QA / A0 |
| **X-2** | **Espejo Zod del frontend** (`features/<dominio>/schemas/<dominio>.schema.ts` → `SCHEMA_VERSION`) para el dominio de `salesianos_fest` **NO existe** todavía: el grep del frontend sólo encuentra espejos de `validaciones` (`1.0.0`) y un comentario en `competencias`. El mecanismo de drift FR-07 §1.3 queda **unilineal** (backend ↔ registro) hasta que A7 publique el espejo. | baja | A7 / UI |
| **X-3** | `Aplicacion/backend/db.sqlite3` aparece modificado en `git status`: es el **artefacto de la corrida de pruebas** sobre el árbol concurrente, no una edición de fuente de este packet. | ninguna | — |

**Los 40 fallos de frontend** que VER-01 §11 medía **siguen FUERA DE ALCANCE**
(dueños UI-01/UI-03/UI-04/UI-05/API-01…API-05/FND-06/FND-07/FND-08): este packet
no toca frontend.

---

## 6. Concurrencia preservada

- Los **cuatro** ficheros de este packet **ya estaban modificados** por el
  agente concurrente (`restore-registration-promotion-catalog-flow`) antes de
  empezar: sus cambios (`competencias`/`patrocinadores`/`validaciones` en el
  registro y en `MODULOS_COMPLETADOS`, los 33 códigos de catálogo y el barrido
  del catálogo) **no se tocaron, no se revertieron ni se fusionaron**. Este
  packet **edita encima** de su estado actual, nunca encima de `HEAD`.
- `git stash` · `git reset` · `git checkout` · `git commit` · `git push`:
  **nunca invocados**. `uv sync` / instalaciones: **nunca**.
- `STATE.md` **no** se editó (corrección paralela): el dueño de VER-01
  reconcilia el tablero compartido cuando las dos correcciones terminen.
- Engram: observación **packet-específica**
  `sdd/salesianos-fest-rebuild/corr-ver01-a0-residuales-backend` (los topics
  compartidos `…/apply-progress` y `…/state` **no** se tocaron).

---

## 7. Rollback

1. `core/contract_versions.py`: devolver `"salesianos_fest": "2.0.0"` a
   `"1.2.0"` (y borrar el comentario del MAJOR de 2026-11-20).
2. `core/exceptions.py`: borrar la entrada `"PRECIO_CAMBIADO"` (y su
   comentario) de `PUBLIC_ERROR_MESSAGES`.
3. `core/tests/integration/test_contract_versions.py`: devolver
   `test_el_registro_refleja_la_version_declarada_de_salesianos_fest` a
   `"1.2.0"` y renombrar `test_la_version_de_salesianos_fest_es_un_cambio_mayor_rompedor`
   a `…_es_un_cambio_minor_aditivo` (quedando sólo la aserción MINOR).
4. `core/tests/integration/test_exceptions_public_catalog.py`: borrar el bloque
   "Cotización" (las 3 pruebas y `CODIGOS_COTIZACION`).
5. En Engram: borrar el topic
   `sdd/salesianos-fest-rebuild/corr-ver01-a0-residuales-backend`.
6. **Punto de rollback:** `2c411cdfc062714cfa7ff39765c4357ddf8267e2` ("betha 6")
   — el HEAD real, que ya existía cuando empezó VER-01. **No revertir ni
   resetear ese commit** (el árbol trae el trabajo sin commitear de varios
   agentes, incluido el de este packet).

> **La historia de los pagos NUNCA se borra en un rollback:** un cobro, un
> derecho habilitado y una activación registrada son hechos (`RN-C08`,
> `RN-P08`).

---

## 8. Estado para VER-02

**BACKEND DESBLOQUEADO**: los tres bloqueadores de VER-01 §6.1 (B-F1,
A0-XCT02-01, A0-API02-09) y los dos residuales de §7.1 (R-1, R-2) están
corregidos y medidos en verde. La suite completa del backend es
**974 passed / 0 failed**.

| Bloqueador de VER-01 §11 | Estado |
|---|---|
| B-F1 (`catalogo_presenter.py:110`) | CORREGIDO (CORR-VER01) |
| A0-XCT02-01 (`modules.administracion` sin registrar) | CORREGIDO (CORR-VER01) |
| A0-API02-09 (`CotizacionController` sin registrar) | CORREGIDO (CORR-VER01) |
| admin.E108 | NO APLICA: la condición no se cumple (`check` verde) |
| **R-1** (drift de `salesianos_fest`) | **CORREGIDO (este packet)** |
| **R-2** (`PRECIO_CAMBIADO` sin prosa) | **CORREGIDO (este packet)** |
| 40 fallos de frontend | FUERA DE ALCANCE (dueños UI-01…UI-05/API-01…API-05/FND-06…FND-08) |
| Lane PostgreSQL | ENTORNO: no disponible (X-1) |
