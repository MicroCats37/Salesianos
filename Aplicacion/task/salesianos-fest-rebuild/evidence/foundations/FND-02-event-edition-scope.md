# FND-02 — Implementación del scope de edición (Evento / Edición)

**Change:** `salesianos-fest-rebuild` · **Paquete:** `FND-02` (`wave-01-foundations`) · **Owner:** A1
**Freeze consumido:** `FREEZE-ED-1.0.0` (FR-02) · `FREEZE-PS-1.0.0` (FR-07) · `FREEZE-ENV-1.0.0` (FR-01)
**Task original:** `T-010` · **Raíces de edición:** `Aplicacion/backend/modules/eventos/**`
**Fecha:** 2026-11-19 · **Rama:** `master` · **HEAD:** `f3df5401c56b41c340f257e67d5a306904a9e670` (sin commit)

---

## 1. Resumen ejecutivo

Se implementa el módulo Django `modules.eventos` con la entidad **`Edicion`** como unidad de
alcance (scope) y **`Evento`** como familia de evento, reemplazando el supuesto global de
"evento activo resuelto por nombre".

Entregado:

- `Evento` (id UUID + `nombre` + `slug`) y `Edicion` (id UUID + `evento_id` + `nombre` + `slug` +
  `anio` + `estado` + `modulos_habilitados` + `fecha_inicio`/`fecha_fin` + timestamps), con la
  invariante **"como máximo una edición `PUBLICADA` por evento"** expresada como
  `UniqueConstraint` condicional en la base de datos.
- El **orden único de resolución** de FR-02 §2.2 (`resolver_explicita` = nivel 1;
  `resolver_actual` = niveles 2 → 3 → 4), sin ningún fallback silencioso.
- Selectores de solo lectura, servicio core de escritura, flujo async con `transaction.atomic()`,
  orquestador async, DTOs internos, result objects, schemas HTTP compuestos por bloques
  (`SCHEMA_DRY_INTENTION`), presenter puro y controller público.
- Migración `0001_initial` generada por Django y verificada por replay (apply → reverse → re-apply).
- **63 tests** del paquete, todos en verde, incluidos aislamiento entre dos ediciones, reutilización
  del histórico, edición equivocada / ausente y la protección de concurrencia.
- **Cuatro peticiones explícitas a A0** (sección 9): registro de la app, DI, controller, catálogo
  de errores públicos y retirada de la constante de settings.

**No se editó** ningún archivo compartido de A0 (`config/settings/base.py`, `config/api.py`,
`core/**`, `conftest.py`), ni ningún otro módulo, ni el frontend, ni las raíces congeladas.

---

## 2. Decisión de scope de edición (la decisión central del paquete)

FR-02 §2.2 congela un orden de resolución. Este paquete lo implementa **literalmente** y le da un
significado distinto y comprobable a cada código de error:

| Nivel | Origen | Implementación | Error cuando falla |
|---|---|---|---|
| 1 | `edicion_id` explícito | `EdicionScopeService.resolver_explicita(edicion_id)` — **sin fallback de ningún tipo** | `EDICION_NO_ENCONTRADA` (404) |
| 2 | Edición activa del actor | `resolver_actual(ediciones_activas_actor=[...])` — el módulo aplica la REGLA ("exactamente una") sin inventar un modelo de relación | `EDICION_AMBIGUA` (409) si hay más de una |
| 3 | Edición `PUBLICADA` única | `resolver_actual()` → `contar_publicadas()` | 0 → `EDICION_NO_PUBLICADA` (404) · >1 → `EDICION_AMBIGUA` (409) |
| 4 | Sin resolución | cierre de `resolver_actual()` | `EDICION_NO_RESUELTA` (404) |

Distinción entre `EDICION_NO_PUBLICADA` y `EDICION_NO_RESUELTA` (decisión de este paquete, §7):

- **`EDICION_NO_RESUELTA`** → no hay NINGUNA edición que resuelva el alcance (base vacía, o
  resolución operativa sin default público).
- **`EDICION_NO_PUBLICADA`** → hay ediciones pero la resuelta no está `PUBLICADA` (edición
  explícita en `BORRADOR`/`CERRADA` con `exigir_publicada=True`, o catálogo sin ninguna edición
  publicada).

### 2.1 Interpretaciones declaradas (no invención de dominio)

1. **`permitir_publicada_por_defecto`** (default `True` en `resolver_actual`, `False` para
   operaciones administrativas): el freeze congela el orden pero NO dice en qué contextos el
   nivel 3 aplica. Un default de nivel 3 en una escritura podría mutar la edición equivocada
   (`implementacion/01` §4, "Nunca mutar inadvertidamente edición equivocada"), así que el módulo
   expone el interruptor y el camino administrativo lo desactiva.
2. **Nivel 2 sin proveedor de persistencia**: FR-02 §3 congela el contrato de datos de `Edicion` y
   **no** congela ninguna relación actor ↔ edición. El módulo NO inventa ese modelo: recibe la
   lista de candidatas del actor como argumento y aplica la regla. El proveedor real lo conecta el
   módulo que posea esa relación (ver §8, decisión abierta `D-FND-02-01`).
3. **`exigir_publicada`**: el nivel 1 y el nivel 2 pueden devolver una edición no publicada; el
   catálogo público la rechaza con `EDICION_NO_PUBLICADA` (FR-02 §2.6).

---

## 3. Archivos creados y modificados

### 3.1 Creados — `Aplicacion/backend/modules/eventos/**` (56 archivos)

| Ruta | Contenido |
|---|---|
| `__init__.py`, `apps.py`, `models.py`, `admin.py`, `di.py` | AppConfig, re-export puro de modelos, ModelAdmins, bindings de `injector` |
| `domain/constants.py` | `EstadoEdicion` (`BORRADOR`/`PUBLICADA`/`CERRADA`) y `ModuloLogico` (5 claves) |
| `domain/exceptions.py` | 8 excepciones de dominio con `code` estable |
| `domain/models/evento.py` | `Evento` |
| `domain/models/edicion.py` | `Edicion` + `validar_modulos_habilitados` + constraints |
| `domain/selectors/evento_selector.py` | `EventoSelector` (sin métodos "activos") |
| `domain/selectors/edicion_selector.py` | `EdicionSelector` (lecturas; `obtener_por_id` tolerante a UUID mal formado) |
| `domain/schemas/edicion_schemas.py` | `EdicionCreateData`, `EdicionUpdateData`, `EdicionPublicarData` |
| `domain/results/edicion_result.py` | `EdicionResult`, `ModuloResult`, `EdicionActualResult` |
| `domain/services/core/edicion_core_service.py` | escrituras (crear / actualizar / publicar / cerrar / `exigir_modulo`) |
| `domain/services/core/edicion_scope_service.py` | **el orden único de resolución** |
| `domain/services/flujos/edicion_flujo.py` | flujo async con `transaction.atomic()` y traducción de `IntegrityError` |
| `domain/services/orchestrators/edicion_orchestrator.py` | fachada async delgada |
| `presentation/schemas/edicion_schemas.py` | bloques `Identidad` + `General` + `Específico` → `EdicionOut`, `EdicionActualOut`, `ModuloHabilitadoOut` |
| `presentation/schemas/__init__.py` | `SCHEMA_VERSION = "1.0.0"` (FR-07 §1.1) + re-exports |
| `presentation/presenters/edicion_presenter.py` | `EdicionPresenter` (transformador puro) |
| `presentation/controllers/edicion_controller.py` | `GET /ediciones/actual` (público) |
| `management/commands/crear_edicion_inicial.py` | comando idempotente de alta de la primera edición |
| `migrations/0001_initial.py` | migración generada por Django 5.2.11 |
| `tests/**` | 63 tests + fixtures + factories + `settings_overlay.py` + `urls_eventos.py` |

### 3.2 Modificados

**Ninguno fuera de `Aplicacion/backend/modules/eventos/**`.** Los archivos que el paquete necesita
tocar y que son de A0 (`config/settings/base.py`, `config/api.py`, `core/exceptions.py`) se
solicitan por evidencia en §9, no se editan.

### 3.3 Migraciones

| Migración | Contenido | Reversible |
|---|---|---|
| `modules/eventos/migrations/0001_initial.py` | `CreateModel Evento` + `CreateModel Edicion` con las 2 constraints | sí (`migrate eventos zero` verificado) |

Esquema físico verificado sobre SQLite real (§6, V10–V15):

```sql
CREATE TABLE "eventos_edicion" (
  ...,
  CONSTRAINT "edicion_slug_unico_evento" UNIQUE ("evento_id", "slug")
);
CREATE UNIQUE INDEX "edicion_publicada_unica_evento"
  ON "eventos_edicion" ("evento_id") WHERE "estado" = 'PUBLICADA';
```

---

## 4. Contratos implementados y-exposed

| Contrato | Dónde | Estado |
|---|---|---|
| `FREEZE-ED-1.0.0` §2.1 identificadores | `domain/models/evento.py`, `domain/models/edicion.py` | implementado |
| `FREEZE-ED-1.0.0` §2.2 orden de resolución | `domain/services/core/edicion_scope_service.py` | implementado |
| `FREEZE-ED-1.0.0` §2.3 prohibiciones | sin constante de settings; sin lectura de settings en el paquete; listados con filtro por evento | implementado + test de contrato |
| `FREEZE-ED-1.0.0` §2.4 remoción | 0 coincidencias del nombre de la constante en `Aplicacion/backend/modules/eventos/**` | implementado (la retirada de `config/settings/base.py` es A0-04) |
| `FREEZE-ED-1.0.0` §2.5 módulos opcionales | `ModuloLogico` + `Edicion.modulos_habilitados` (default deshabilitado) + `EdicionCoreService.exigir_modulo` | implementado |
| `FREEZE-ED-1.0.0` §2.6 no publicada | `EDICION_NO_PUBLICADA` (404) | implementado |
| `FREEZE-ED-1.0.0` §3 contrato de datos + invariante | modelo + `UniqueConstraint` condicional | implementado |
| `FREEZE-PS-1.0.0` §1.1 versión de schema | `presentation/schemas/__init__.py::SCHEMA_VERSION = "1.0.0"` == `core.contract_versions.SCHEMA_VERSIONS["eventos"]` | implementado (test de drift) |
| `FREEZE-PS-1.0.0` §4 nombres de wrapper | `EdicionOut`, `EdicionActualOut`, `EdicionPresenter` | implementado |
| `FREEZE-ENV-1.0.0` envelope | `success_response` + `ApiResponse[...]`; los errores salen del catálogo de A0 | implementado |
| `contract/django-app-architecture-contract.md` §3/§4/§6 | layout físico, capas, naming, constraints, `on_delete=PROTECT` | implementado |
| `contract/PLAN_REFACTORIZACION.md` §1/§2/§3 | controller sagrado, capa de 4 niveles, `BaseSchema` en todos los schemas | implementado |
| `contract/SCHEMA_DRY_INTENTION.md` | 3 bloques + composición, sin schema monolítico | implementado |
| `contract/api-wrapper-presenter-contract.md` §2/§3/§8 | wrapper tipado, presenter sin ORM, errores del catálogo | implementado |
| `contract/TEST_ARCHITECTURE_CONTRACT.md` §1/§3/§4 | `integration/` + `e2e/` (sin `unit/`), fixtures en `fixtures/`, factories puras sin `factory_boy` | implementado |
| Ledger FR-07 §3.3 `RT-ED-01` | `GET /ediciones/actual` → `EdicionActualOut` | implementado (registro pendiente A0-03) |
| Ledger FR-07 §3.3 `RT-ED-02` | `GET /ediciones/{edicion_id}/catalogo` | **NO implementado** — ver §7 (D-FND-02-02) |

### 4.1 Divergencias respecto del código congelado (trazables)

| Congelado (`backend/modules/eventos/**`) | Objetivo | Motivo |
|---|---|---|
| `Evento.esta_activo` | eliminado | es el supuesto global que FR-02 §2 reemplaza |
| `Evento.fecha_inicio` / `fecha_fin` | eliminados (viven en `Edicion`) | evita dos fuentes de verdad |
| `Evento.fecha_limite_modificacion` | eliminada | no está en el plan ratified (GOV-01-OPEN-03) |
| `EventoSelector.obtener_activo()` ("la más reciente") | eliminado | FR-02 §2.2: nunca "la más reciente" |
| `EventoSelector.obtener_activo_por_nombre()` | eliminado | FR-02 §2.3: nunca por nombre |
| `Evento` sin `slug` | `Evento.slug` único | FR-02 §2.1 lo exige; permite resolver por identificador estable |
| — | `Edicion` (nueva) | FR-02 §2.1 / §3 |

---

## 5. Comportamiento expuesto

### 5.1 HTTP

`GET /api/ediciones/actual` — público, `auth=None`.

| Situación | HTTP | `error.code` |
|---|---|---|
| hay una edición `PUBLICADA` | 200 | — (`data` = edición + estado de los 5 módulos) |
| hay ediciones, ninguna publicada | 404 | `EDICION_NO_PUBLICADA` |
| no hay ediciones | 404 | `EDICION_NO_RESUELTA` |
| hay dos ediciones `PUBLICADA` (familias distintas) | 409 | `EDICION_AMBIGUA` |

El mensaje público lo decide el catálogo de A0 (`core/exceptions.py`); los códigos de este módulo
**no están todavía** en ese catálogo (petición A0-01), de modo que hoy la prosa es la genérica por
status. El `error.code` sí es estable y correcto.

### 5.2 Comando

```
python manage.py crear_edicion_inicial \
  --evento-nombre "Salesianos FEST" --evento-slug "salesianos-fest" \
  --edicion-nombre "Salesianos FEST 2026" --edicion-slug "2026" --anio 2026 \
  [--modulo inscripciones] [--publicar]
```

Idempotente (si la edición ya existe, no la duplica). FR-02 §2.4 permite usar el nombre del
evento activo como valor semilla **sólo** en un comando de gestión; aquí el nombre se pide por
parámetro, de modo que el paquete no contiene la constante y la prueba de remoción puede dar 0
coincidencias.

---

## 6. Verificación

Workdir: `Aplicacion/backend` · Intérprete: `.\.venv\Scripts\python.exe` (Python 3.10.0,
Django 5.2.11, pytest-django 4.9.0, ninja 1.5.3, ninja-extra 0.31.0, injector 0.24.0).

### 6.1 Entorno exacto

```powershell
$env:DJANGO_SETTINGS_MODULE = "modules.eventos.tests.settings_overlay"   # opcional para V1/V19
```

El overlay (`modules/eventos/tests/settings_overlay.py`) registra la app y el módulo de `injector`
**sin** tocar la configuración compartida de A0. `pytest-django` da prioridad a la variable de
entorno sobre `pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings.test`), por eso el comando
literal `python -m pytest modules/eventos/tests -q` funciona con esa variable fijada.
`EVENTOS_SQLITE_PATH` (opcional) hace que el overlay use una base SQLite en archivo en vez de la
en memoria.

### 6.2 Comandos y códigos de salida

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V1 | `python -m pytest modules/eventos/tests -q` (con overlay) | **0** | **63 passed** |
| V2 | `python -m pytest modules/eventos/tests -q` (sin overlay) | **4** | `RuntimeError: Model class ... isn't in an application in INSTALLED_APPS` — dependencia A0-02 pendiente, no un defecto del módulo |
| V3 | `python manage.py check` | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — baseline ambiental idéntico al congelado (FND-01 V1) |
| V4 | `python manage.py makemigrations --check --dry-run` | **1** | mismo `DB_NAME` — baseline idéntico (FND-01 V2) |
| V5 | `python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced)` |
| V6 | `python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| V7 | `python manage.py check --settings=modules.eventos.tests.settings_overlay` | **0** | `System check identified no issues (0 silenced)` |
| V8 | `python manage.py makemigrations --check --dry-run --settings=…overlay` | **0** | **`No changes detected`** — la migración `0001_initial` refleja EXACTAMENTE los modelos |
| V9 | `python manage.py showmigrations eventos --settings=…overlay` | **0** | `[ ] 0001_initial` |
| V10 | `python manage.py migrate --settings=…overlay` (SQLite en archivo) | **0** | aplica `eventos.0001_initial` y el resto del grafo |
| V11 | `python manage.py migrate --settings=…overlay` (2ª vez) | **0** | `No migrations to apply` — idempotente |
| V12 | `python manage.py showmigrations eventos --settings=…overlay` | **0** | `[X] 0001_initial` |
| V13 | `python manage.py migrate eventos zero --settings=…overlay` | **0** | `Unapplying eventos.0001_initial... OK` — **reversible** |
| V14 | `python manage.py migrate eventos --settings=…overlay` | **0** | `Applying eventos.0001_initial... OK` — **segundo replay** |
| V15 | inspección del esquema SQLite real | **0** | constraints condicional y compuesta presentes (§3.3) |
| V16 | `python manage.py crear_edicion_inicial … --publicar` | **0** | `Edición creada (evento nuevo).` + `Edición publicada.` — fila verificada en la base |
| V17 | `python manage.py crear_edicion_inicial …` (repetición) | **0** | `La edición ya existía; no se creó una segunda.` — idempotente |
| V18 | `python -m pytest core/tests -q` (settings por defecto) | **0** | **89 passed** — baseline de FND-01 intacto, sin regresiones |
| V19 | `python -m pytest core/tests modules/eventos/tests -q` (overlay) | **0** | **152 passed** |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **vacío** — contratos, plan y documentación intactos |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **vacío** — raíces congeladas intactas |
| R3 | `git grep -n "EVENTO_ACTIVO_NOMBRE" -- Aplicacion/backend` | **0** | 2 coincidencias, **las dos** en `config/settings/base.py` (A0-04). **0 en `modules/eventos/**`** |
| R4 | `git status --short -- Aplicacion/backend` | **0** | sólo `modules/eventos/` (nuevo) + los archivos de FND-01/FND-03 previously modificados |

### 6.3 Cobertura de tests (63)

| Archivo | Tests | Qué prueba |
|---|---:|---|
| `integration/test_edicion_modelos.py` | 11 | defaults congelados, slug único por evento, **una sola `PUBLICADA` por evento** (constraint), validación de claves de módulo, contrato de datos mínimo, fechas nulables |
| `integration/test_edicion_selectors.py` | 11 | id válido/inválido/desconocido, slug por evento, **aislamiento** del listado por evento, conteo de publicadas |
| `integration/test_edicion_scope_service.py` | 14 | los 4 niveles, `EDICION_NO_ENCONTRADA` / `NO_PUBLICADA` / `AMBIGUA` / `NO_RESUELTA`, **no elegir por defecto**, **aislamiento** entre ediciones, **reutilización del histórico** |
| `integration/test_edicion_core_service.py` | 12 | alta, slug duplicado, publicación, **publicación concurrente** (2ª publicación del mismo evento → 409), idempotencia, cierre, módulo no habilitado |
| `integration/test_edicion_presenter.py` | 4 | proyección a wrapper, los 5 módulos con su estado real, módulos deshabilitados visibles, presenter sin ORM |
| `e2e/test_ediciones_controller.py` | 5 | 200 con la edición publicada, 404 `EDICION_NO_PUBLICADA`, 404 `EDICION_NO_RESUELTA`, 409 `EDICION_AMBIGUA`, envelope sin fugas |
| `tests/test_contrato_eventos.py` | 6 | remoción de la constante, **cero lecturas de `settings`** en el paquete, drift de `SCHEMA_VERSION`, vocabularios congelados, contrato de datos |

### 6.4 Clasificación de regresiones

| Categoría | Resultado |
|---|---|
| Regresiones introducidas | **0** (V18: los 89 tests del core siguen en verde; ninguna raíz congelada tocada) |
| Baseline conocida sin tocar | V3/V4 (`DB_NAME`, ambiental), los 13 fallos del backend **congelado** (`backend/modules/**`, propiedad de los paquetes de dominio) |
| Fallos nuevos | 1 — V2: el paquete no se puede importar sin que A0 registre la app en `INSTALLED_APPS`. Es una dependencia declarada (A0-02), no un defecto: el comando literal funciona en cuanto A0 aplique el registro. |
| Byproducts | `manage.py check --settings=config.settings.development` crea un `Aplicacion/backend/db.sqlite3` de 0 bytes (FND-01 F-2): **eliminado** al terminar. `*.sqlite3` no está en el `.gitignore` del objetivo → **A0-05** |
| Concurrencia preservada | `Aplicacion/backend/modules/usuarios/**` (FND-03) y `Aplicacion/frontend/**` (FND-06) aparecieron durante el paquete: **no tocados, no revertidos, no fusionados** |
| `git stash` / commits | **no usados**. No se creó ningún commit |

---

## 7. Decisiones de scope tomadas por el paquete (con trazabilidad)

| ID | Decisión | Motivo |
|---|---|---|
| `D-FND-02-01` | El nivel 2 (edición activa del actor) se implementa como **regla sobre una lista que recibe el llamador**; no se crea modelo actor↔edición | FR-02 §3 congela el contrato de datos de `Edicion` y no congela esa relación. Inventarla sería dominio no aprobado. **Pendiente de owner** (A0 + producto + A1) |
| `D-FND-02-02` | **`RT-ED-02` (`/ediciones/{id}/catalogo`) NO se implementa en FND-02** | Su payload son los catálogos de inscripciones, pases y marketplace: modelos que pertenecen a DOM-01/03/05 y que aún no existen. Implementarlo ahora sería inventar la forma del catálogo. `FL-01` paso 3 autoriza estado vacío, pero el wrapper `CatalogoEdicionOut` pertenece al paquete que possa los dominios. **Se implementa en API-01/API-05** |
| `D-FND-02-03` | Sin rutas de escritura HTTP: las escrituras de edición sólo existen por el comando de gestión | El ledger FR-07 §3.3 no congela ninguna ruta de escritura para `eventos`. "Expose only frozen query/command contracts" ⇒ sólo `RT-ED-01` (query) + el comando (command) |
| `D-FND-02-04` | `permitir_publicada_por_defecto` como interruptor explícito | Ver §2.1 (1) |
| `D-FND-02-05` | `Edicion.estado` usa `TextChoices` con 3 valores exactos; `modulos_habilitados` es `JSONField` con lista de `str` | Contrato literal de FR-02 §3 |
| `D-FND-02-06` | `Evento.slug` es único en el sistema; `Edicion.slug` es único **por evento** | FR-02 §3 lo exige para la edición; para el evento es la consecuencia de "resolver por identificador estable" (§2.3 #2) |
| `D-FND-02-07` | `fecha_inicio` / `fecha_fin` son nulables y sin semántica | GOV-01-OPEN-03 (owner A0 + producto) |

---

## 8. Decisiones abiertas heredadas / nuevas

Se arrastran sin cambio: `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · GAP-1…GAP-4 · D-A…D-E ·
`GOV-02-UX-01`…`05` · `GOV-02-SH-01`…`08` · `GOV-02-BL-01`…`12` · `GOV-02-CM-01`…`05` ·
`P-01`…`P-12` · `GOV-01-OPEN-09` (política de backup) · `GOV-01-OPEN-10` (límites de dimensión).

Nuevas de este paquete:

| ID | Pendiente | Owner |
|---|---|---|
| `D-FND-02-01` | Fuente persistente de "ediciones activas del actor" (nivel 2 del orden) | A0 + producto + A1 |
| `D-FND-02-02` | Forma del catálogo por edición (`RT-ED-02`) | A1 + A3/A4/A5 (dueños de los dominios) |
| `D-FND-02-08` | `EDICION_AMBIGUA` debe llevar la lista de candidatas en `error.details`; el handler global de A0 sólo admite `non_field_errors` en `details` y manda el resto a `field_errors` | A0 |
| `D-FND-02-09` | `modulos_habilitados` se guarda como `JSONField` con lista de cadenas; no hay modelo `Modulo` catálogo | A1 + A0 (si más adelante se requiere catálogo administrable) |

---

## 9. Peticiones explícitas a A0 (fuera de las raíces de edición de este paquete)

| ID | Petición | Archivo / acción | Por qué no lo hace FND-02 |
|---|---|---|---|
| **A0-01** | Añadir al catálogo público `core/exceptions.py::PUBLIC_ERROR_MESSAGES` los códigos del módulo: `EDICION_NO_ENCONTRADA` (404), `EDICION_NO_PUBLICADA` (404), `EDICION_AMBIGUA` (409), `EDICION_NO_RESUELTA` (404), `EVENTO_NO_ENCONTRADO` (404), `EDICION_SLUG_DUPLICADO` (409), `EDICION_PUBLICADA_DUPLICADA` (409), `MODULO_NO_HABILITADO` (409) | `core/exceptions.py` | es de A0 (freeze `FREEZE-ENV-1.0.0`). Los códigos ya viajan estables en `error.code`; falta la prosa pública específica |
| **A0-02** | Registrar la app y el DI: `INSTALLED_APPS += ["modules.eventos"]` y `NINJA_EXTRA["INJECTOR_MODULES"] += ["modules.eventos.di.EventosModule"]` | `config/settings/base.py` (líneas 55 y 197, ya comentadas y preparadas) | es de A0. Mientras no se aplique, `python -m pytest modules/eventos/tests -q` sin overlay falla con exit 4 (V2). Con el overlay local todo pasa |
| **A0-03** | Registrar el controller: `registrar_controladores(EdicionController)` | `config/api.py` | es de A0 (FR-07 §3.1 regla 2: la ruta no existe hasta que se registra). Hasta entonces la ruta es código muerto por diseño |
| **A0-04** | Retirar `EVENTO_ACTIVO_NOMBRE` de `config/settings/base.py` (línea 177) y su comentario (líneas 169-176) | `config/settings/base.py` | es de A0 (FR-02 §2.4 lo asigna al cierre de FND-02). **El módulo ya está limpio: 0 coincidencias en `Aplicacion/backend/modules/eventos/**`** |
| **A0-05** | Añadir `*.sqlite3` al `.gitignore` del objetivo | `Aplicacion/backend/.gitignore` | es de A0 (FND-01 F-2). Cada corrida de `manage.py check --settings=config.settings.development` deja un `db.sqlite3` de 0 bytes |
| **A0-06** | Decidir `D-FND-02-08`: soporte de `details` no-campo en el handler global para la lista de candidatas de `EDICION_AMBIGUA` | `core/exceptions.py` | es de A0. El módulo ya transporta las candidatas en `EdicionAmbiguaError.candidatas` (contenido público seguro: slug/nombre/año, sin UUIDs) |
| **A0-07** | Sincronizar la matriz física `00-matriz-tareas.md` (fila `T-010`) | `Aplicacion/task/.../00-matriz-tareas.md` | la matriz está fuera de las raíces de edición de todos los paquetes (mismo caso que `T-016`/`T-018` en FND-01) |

---

## 10. Rollback

| Paso | Acción |
|---|---|
| 1 | `migrate eventos zero` (reversible, verificado en V13) — o borrar las tablas `eventos_evento` / `eventos_edicion` |
| 2 | Eliminar `Aplicacion/backend/modules/eventos/**` (56 archivos) |
| 3 | Retirar los registros que A0 haya hecho por A0-02 / A0-03 (`INSTALLED_APPS`, `INJECTOR_MODULES`, `registrar_controladores`) |
| 4 | Restaurar `STATE.md` y el topic de Engram al estado previo a este paquete |
| 5 | **NO** revertir `f3df540` (commit previo del usuario, fuera del alcance del paquete) |

**Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (sin commit creado por este paquete).

---

## 11. Consumidores desbloqueados

| Consumidor | Qué le da este paquete |
|---|---|
| **DOM-01, DOM-03, DOM-07, DOM-08** | `Edicion` con `id` estable + FK `edicion_id` como ancla de todo modelo con FK a edición; `SCHEMA_VERSION` del módulo `eventos` disponible |
| **DOM-04, DOM-05, DOM-06** | módulo con `modulos_habilitados` como configuración de la edición (RN-E02) |
| **FND-03 (identidad)** | `EventosModule` de `injector` disponible y `Evento`/`Edicion` ya registrados como app (cuando A0 aplique A0-02) |
| **FND-04 (commerce/pagos)** | mismo ancla de scope |
| **API-01…API-05** | ledger `RT-ED-01` implementada; `RT-ED-02` con decisión `D-FND-02-02`; punto de extensión `registrar_controladores` listo |
| **FND-07 / FND-08** | forma exacta del wrapper `EdicionActualOut` para el espejo Zod (`id`, `evento_id`, `evento_nombre`, `evento_slug`, `nombre`, `slug`, `anio`, `estado`, `modulos_habilitados`, `fecha_inicio`, `fecha_fin`, `created_at`, `updated_at`, `modulos[]`) |
| **XCT-01…XCT-03, VER-01…VER-03** | invariante de una sola edición publicada por evento y código de aislamiento de ediciones ya testeados |
| **UI-01…UI-05, FND-06** | el frontend deja de asumir "la edición actual" y la lee de `GET /ediciones/actual` (FR-02 §2.4, fase FND-06) |

---

## 12. Nota de concurrencia

Durante la ejecución de FND-02 aparecieron en el árbol de trabajo:

- `Aplicacion/backend/modules/usuarios/**` (paquete **FND-03**, identidad) — **no tocado**.
- `Aplicacion/frontend/**` (paquete **FND-06**, shell) — **no tocado**.
- `Aplicacion/task/.../STATE.md` — re-leído justo antes de escribir la transición; la fusión
  incluye **sólo** la fila de FND-02 y su entrada de log, sin sobrescribir FND-03 / FND-06.

Ningún archivo compartido (`config/settings/base.py`, `config/api.py`, `core/**`) fue editado: las
peticiones A0-01…A0-07 están en §9.

---

## 13. Conjunto de lectura, desviaciones y carga de revisión

### 13.1 Contrato de apply global (`00-contrato-global-de-apply.md`)

Orden de lectura obligatorio cumplido: `AGENTS.md` raíz · `contract/` (los 7 archivos; en detalle
`django-app-architecture-contract.md`, `PLAN_REFACTORIZACION.md`, `SCHEMA_DRY_INTENTION.md`,
`api-wrapper-presenter-contract.md`, `TEST_ARCHITECTURE_CONTRACT.md`) · plan
(`00-decisiones-y-alcance.md` DEC-01, `funcional/02` RN-E01/RN-E02, `funcional/03`, `funcional/04`
FL-01, `implementacion/01` §4/§5) · documentación (`04-datos-y-dominio.md`, más `01`, `02a`, `02b`
como evidencia de contexto) · skills (`sdd-apply`, `salesianos-feature-architecture`;
`salesianos-api-data` **no** se cargó: no hubo trabajo de endpoint/schema fuera del wrapper ya
congelado) · paquete y `STATE.md`.

### 13.2 Desviaciones respecto del plan/spec

| # | Desviación | Motivo |
|---|---|---|
| 1 | `RT-ED-02` (`/ediciones/{id}/catalogo`) NO implementado | su payload son los catálogos de dominios que no existen todavía; implementarlo sería inventar la forma del catálogo (`D-FND-02-02`) |
| 2 | Sin rutas de escritura HTTP para ediciones | el ledger FR-07 §3.3 no congela ninguna; sólo `RT-ED-01` + el comando de gestión (`D-FND-02-03`) |
| 3 | `permitir_publicada_por_defecto` como interruptor | el freeze no dice en qué contextos aplica el nivel 3 (`D-FND-02-04`) |
| 4 | Nivel 2 sin modelo de persistencia | FR-02 §3 congela el contrato de datos de `Edicion` y no la relación actor↔edición (`D-FND-02-01`) |
| 5 | Overlay de settings y URLconf de prueba DENTRO del paquete | `config/settings/base.py` y `config/api.py` son de A0; el paquete necesita poder verificarse sin tocarlos. Se retiran cuando A0 aplique A0-02/A0-03 |

### 13.3 Carga de revisión (contrato global, "changed-line forecast/actual count")

| Artefacto | Archivos | Líneas añadidas |
|---|---:|---:|
| `Aplicacion/backend/modules/eventos/**` | 59 | 3 113 (686 vacías · 42 de comentario · 2 385 código + docstrings) |
| `evidence/foundations/FND-02-event-edition-scope.md` | 1 | 350 |
| `STATE.md` (transición FND-02) | 1 | ~66 |
| **Total** | **61** | **~3 529** |

El paquete NO trae un "Review Workload Forecast" en su artefacto de tareas, así que no hay puerta
de decisión de carga que bloquear. La cifra real está muy por encima del presupuesto de revisión de
400 líneas: la mayor parte es **documentación de trazabilidad** (docstrings que citan la cláusula
exacta del freeze que implementa cada elemento) y el esqueleto de directorios del layout físico
congelado (25 `__init__.py` y 4 directorios `infrastructure/` vacíos por contrato §4.11). Si A0
quiere un corte revisable, la unidad natural es: (a) modelos + migración + constraints, (b) servicio
de alcance + selectors, (c) presentación + comando + tests.

### 13.4 Skills

`sdd-apply` (cargado) · `salesianos-feature-architecture` (cargado; se aplicó el layout de capas
`route → view → … → services → schemas` en su versión backend: `presentation/` → `domain/services/`
→ `domain/selectors/` → `domain/models/`) · `salesianos-api-data` **no** cargado: el paquete no
introduce endpoints fuera del ledger congelado ni cambia schemas de API compartidos; el wrapper HTTP
`EdicionActualOut` está congelado por FR-07 y su espejo Zod es trabajo de A7 (FND-07/FND-08).
