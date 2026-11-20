# DOM-07 — Competencias, cuadro, agenda, resultados y correcciones

**Packet:** `DOM-07` (`wave-02-domain-backend/DOM-07-competitions.md`) · **Change:** `salesianos-fest-rebuild`
**Owner:** A6 · **Rama:** `master` · **Punto de rollback:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit; `git stash` nunca invocado)
**Freezes respetados:** `FREEZE-ENV-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-TC-1.0.0` · `FREEZE-PS-1.0.0`

---

## 0. ESTADO: `verification_required`

La verificación en runtime está **DIFERIDA POR INSTRUCCIÓN EXPRESA DEL USUARIO**
(preferencia `workflow/salesianos-sdd-apply-verification-deferred`):

- las pruebas se **ESCRIBEN** pero **NO se ejecutan**;
- prohibido: `pytest`, `python -m pytest`, `manage.py check`, `makemigrations`,
  `migrate`, `showmigrations`, typecheck, lint;
- prohibido invocar el Python global **y** el de `.venv`;
- toda verificación Python posterior exige **autorización explícita** y
  **debe usar `uv run`**;
- **comandos ejecutados en este paquete: NINGUNO.**

El paquete se marca **`verification_required`**, nunca `completed`. La
**revisión estática de fuente** (§6) es el sustituto del runtime mientras la
ejecución está diferida.

---

## 1. Alcance

Plan: `T-050`, `T-051`, `T-052` (3 de los 54 IDs de origen).
Reglas: `RN-K01` (elegibilidad), `RN-K02` (programación, participantes,
resultado, vencedor, estado y auditoría · vista previa y confirmación de las
correcciones), `RN-K03` (no solapar un equipo).
Flujo: `FL-11` (administrar competencia y encuentros).
Pruebas de aceptación: `QA-K01` (elegibilidad), `QA-K02` (programación),
`QA-K03` (corregir resultado) · más `QA-K04` (advance preview) y `QA-K05`
(conflicto de versión), que el plan `frontend/05` §8 exige.
Fuente del contrato de UI: `frontend/05-competencias-y-encuentros.md`.

**Dentro del alcance:** la competencia, sus equipos, sus rondas, sus
encuentros, la agenda, la programación, el resultado, el avance, la
corrección y su auditoría.

**FUERA del alcance (y NO inventado):** el cuadro PÚBLICO de `/competencias/[id]`
—el plan lo declara como propuesta sin página ID y el ledger no lo congela—;
la transición de estado de la COMPETENCIA (no hay DTO ni ruta); la
INVALIDACIÓN de una ronda (el estado existe en el vocabulario, pero ningún DTO
la comanda); la transición de SUSPENDIDO (no está en el vocabulario cerrado de
este módulo).

---

## 2. EL DISEÑO CENTRAL — una sola fuente operativa, un solo presenter

### 2.1 La fuente operativa es UNA (`FL-11` paso 6, `frontend/05` §3)

`frontend/05` §1 paso 6 y `FL-11` paso 6 exigen que **la lista, la agenda y el
bracket compartan una sola fuente de datos**. La implementación lo hace
ESTRUCTURAL, no por convención:

- `domain/selectors/proyeccion.py` es el **ÚNICO** lugar donde un modelo se
  proyecta a un `result`;
- `EncuentroResult` es la **forma canónica** del encuentro: la agenda, el
  cuadro y el detalle la reutilizan;
- `presentation/presenters/competencias_presenter.py` es el **ÚNICO presenter**
  (`CompetenciasPresenter`): no hay un presenter por ruta que pueda diverger.

El test e2e `test_el_cuadro_usa_la_misma_forma_de_encuentro_que_el_detalle`
comprueba que el encuentro del detalle y el del cuadro tienen **las mismas
claves**.

### 2.2 La elegibilidad se CONSUME por PUERTO, no se reimplementa (`RN-K01`)

`modules.salesianos_fest` es el DUEÑO de la inscripción, del equipo, de su
disciplina y del POOL de participantes. Este módulo **no duplica ninguna
regla de inscripción**:

- el puerto `IEquipoElegibleService` (ya presente en el trabajo previo de
  este paquete) se implementa en `infrastructure/services/equipo_elegible_adapter.py`;
- el adaptador **consulta** los modelos reales del dueño (`Equipo`,
  `Inscripcion`, `Participacion`, `Disciplina`) y **traduce** su veredicto;
- el veredicto trae el CÓDIGO del motivo (`MotivoNoElegibilidad`) y el
  dominio lo traduce a una excepción con código público: el cliente nunca
  adivina la razón (`QA-K01`).

**Precedencia del veredicto (fija y documentada):** `EQUIPO_NO_ENCONTRADO` →
`EDICION_DISTINTA` → `DISCIPLINA_DISTINTA` → `DISCIPLINA_INACTIVA` →
`INSCRIPCION_CANCELADA` → `EQUIPO_NO_ACTIVO` → `SIN_PLANTILLA` →
`PLANTILLA_INCOMPLETA` → `ELEGIBLE`.

**Alcance del listado:** los candidatos son los equipos de la EDICIÓN y de la
DISCIPLINA del torneo (`RN-E01`): el listado nunca expone equipos de otra
edición. `EDICION_DISTINTA` y `DISCIPLINA_DISTINTA` son los motivos del
veredicto DE UN EQUIPO (`verificar_elegibilidad`), donde el administrador
elige equipo y torneo y puede equivocarse.

### 2.3 La agenda NO solapa y el encadenado NO es silencioso

- `RN-K03`: un equipo no puede jugar DOS encuentros a la vez, **aunque sea en
  competencias distintas de la misma edición** (es el mismo equipo físico). No
  hay regla por disciplina congelada en ningún contrato, así que se aplica la
  regla GLOBAL de la edición y **no se inventa** ninguna por disciplina.
- Los intervalos son **SEMI-ABERTOS** (`[inicio, fin)`): dos encuentros que
  sólo se tocan NO se solapan.
- Un encuentro **CANCELADO no reserva la franja**.
- **Sin `select_for_update`**: SQLite no lo soporta y el proyecto ya lo tiene
  documentado (`F-55`). La protección de concurrencia es el **bloqueo
  optimista por versión**, que es la que pide el contrato (`frontend/05` §6).

### 2.4 La vista previa NUNCA escribe (`QA-K03`, `QA-K04`)

`previsualizar_avance` y `previsualizar_correccion` son **simulaciones**: no
abren transacción, no escriben y no incrementan la versión de nada. La
confirmación es la única que escribe, dentro de su propia atomicidad, con su
motivo auditado y con el bloqueo optimista.

### 2.5 La corrección declara su impacto (`QA-K03`)

La corrección calcula un **PLAN** sobre la cadena de descendientes y publica,
para cada uno, qué le pasa: `reemplaza`, `limpia_slot`, `limpia_resultado`,
`bloqueado`. Un descendiente que YA transcurrió **BLOQUEA** la cascada: sin
`override` explícito Y la aceptación del impacto, **nada se escribe**.

**La corrección NUNCA pisa una colocación MANUAL**: sólo toca los slots cuyo
valor fue PROPAGADO (`ganador_propagado`). Un slot que el administrador
colocó a mano queda intacto.

### 2.6 La auditoría es un ACTA, no un historial (`RN-K02`)

`AuditoriaOperacion` es una tabla explícita del módulo: el acta es un HECHO
de negocio, existe aunque el dato que audita cambie después, y **nunca se
borra** (una corrección posterior deja la anterior como antecedente). El
`detalle` (antes/después) es contexto TÉCNICO del servidor y **nunca se
publica en una respuesta HTTP**: el presenter no lo expone.

---

## 3. Lo entregado

### 3.1 Modelos (`Aplicacion/backend/modules/competencias/domain/models/`)

`Competencia` (edición + disciplina + nombre + estado + fecha) ·
`CompetenciaEquipo` (participación con semilla MANUAL) · `Ronda` ·
`Encuentro` (participantes, horario, bye, marcador, ganador autoritativo,
enlace + slot, ganador propagado) · `AuditoriaOperacion`.

Todos heredan `CompetenciaBaseModel`, que añade el **contador de versión** del
bloqueo optimista. Los modelos son **planos y anémicos**
(`contract/django-app-architecture-contract.md` §6).

### 3.2 Puertos (`domain/ports/__init__.py`)

- `IEquipoElegibleService` — **preexistente** (trabajo previo de este
  paquete): se CONSERVA tal cual. Sólo se le AÑADIÓ el puerto hermano
  `IAlcanceEdicion`, que el propio docstring del archivo ya anunciaba.
- `IAlcanceEdicion` — el alcance de edición, con el ORDEN CONGELADO de
  `FR-02` §2.2, resuelto por `infrastructure/services/alcance_edicion_eventos.py`.

### 3.3 Servicios core (sync, sin transacción propia)

`base_service` (versionado, motivo auditado, no-terminal) · `competencia_core_service`
(competencia + participación + ronda) · `encuentro_core_service` (participantes,
bye, enlace, estado) · `programacion_core_service` (intervalo + solapamiento) ·
`resultado_core_service` (ganador autoritativo) · `avance_core_service`
(previa + confirmación) · `correccion_core_service` (plan + aplicación) ·
`auditoria_core_service` (el acta).

### 3.4 Flujos (async, único lugar con `transaction.atomic()`)

`cuadro_flujo` (competencia, equipo, ronda, encuentro) · `encuentro_flujo`
(la edición del encuentro) · `resultado_flujo` · `avance_flujo` ·
`correccion_flujo`.

### 3.5 Selectores + proyección

`competencia_selector` (listado con contadores calculados por la base de
datos, detalle) · `encuentro_selector` (encuentro, cuadro, agenda) ·
`proyeccion` (la proyección única).

### 3.6 Orquestador

`CompetenciasOrchestrator` — una fachada delgada, **un método por ruta**.

### 3.7 Presentador y HTTP

`CompetenciasPresenter` (único) · `presentation/schemas/competencias_schemas.py`
(wrappers `*In`/`*Out`) · `presentation/controllers/competencias_controller.py`
(16 rutas, delgado).

### 3.8 Rutas (16)

| Ruta | Método | Permiso |
|---|---|---|
| `/competencias` | GET | lectura del área |
| `/competencias/agenda` | GET | lectura del área |
| `/competencias/{id}` | GET | lectura del área |
| `/competencias/{id}/cuadro` | GET | lectura del área |
| `/competencias/{id}/equipos-elegibles` | GET | lectura del área |
| `/competencias` | POST | escribir competencias |
| `/competencias/{id}/equipos` | POST | escribir competencias |
| `/competencias/{id}/equipos/{participacion_id}` | PATCH | escribir competencias |
| `/competencias/{id}/rondas` | POST | escribir competencias |
| `/competencias/{id}/encuentros` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}` | PATCH | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/resultado` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/avance/preview` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/avance` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/correccion/preview` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/correccion` | POST | escribir competencias |

Los permisos usan la autoridad centralizada (`core.permissions`):
`RequireAdminVer` para leer y `RequireCompetenciasEscribir` para escribir.
La autenticación (`JWTAuth`) responde **antes** que la autorización: 401
antes que 403 (`FREEZE-ENV-1.0.0` · `FR-01` §4.4).

**El `expected_version` viaja en el payload** de cada escritura: es la
protección de concurrencia que el contrato pide (`frontend/05` §5).

### 3.9 Migración

`migrations/0001_initial.py` — **ESCRITA A MANO** (la verificación está
diferida, así que `makemigrations` no se pudo ejecutar). Reproduce
exactamente lo que declaran los modelos. Dependencias:
`eventos.0001_initial` · `salesianos_fest.0003_pases_derechos` ·
`usuarios.0002_grupos_funcionales` · `swappable_dependency(AUTH_USER_MODEL)`.

**Reglas de la escritura a mano (aprendizaje `F-60`):**

- las restricciones de expresión se escriben con los MISMOS argumentos que
  usa el modelo (`models.F("edicion"), models.F("disciplina"),
  django.db.models.functions.text.Lower("nombre")`), para que la comparación
  de restricciones del autodetector NO las lea como distintas;
- los `Q` con varios argumentos se escriben con **argumentos nombrados**: un
  `Q` con tuplas posicionales conserva el ORDEN de las tuplas mientras que el
  `Q` del modelo ORDENA sus argumentos nombrados; con dos o más argumentos
  ambas formas NO son iguales y el drift no se estabiliza;
- el `Lower` se importa por su ruta COMPLETA, que es la que serializa el
  autodetector.

> **Aviso de verificación diferida:** `pytest.ini` usa `--nomigrations`, así
> que la suite de pruebas crea las tablas desde los MODELOS y **no ejercita
> esta migración**. La equivalencia migración ↔ modelos sólo se podrá
> confirmar con `makemigrations --check --dry-run` (comando diferido, §7).

### 3.10 DI

`di.py` → `CompetenciasModule`: liga `IEquipoElegibleService` →
`EquipoElegibleAdapter` e `IAlcanceEdicion` → `AlcanceEdicionEventos`, más
selectores, servicios core, flujos y orquestador.

---

## 4. El PRESENTADOR y su versión

- **Presenter:** `modules.competencias.presentation.presenters.competencias_presenter.CompetenciasPresenter`
  (UNO, en `presentation/presenters/competencias_presenter.py`, el nombre que
  exige `FR-07` §3).
- **`SCHEMA_VERSION` del módulo:** **`1.0.0`** — es el PRIMER contrato del
  módulo `competencias` (16 rutas nuevas + su primer presenter), así que la
  versión es la inicial (`FR-07` §2).
- **Registro global:** `core/contract_versions.SCHEMA_VERSIONS["competencias"]`
  **NO existe todavía** → es una **petición a A0** (A0-02) y una fuente de
  **drift** hasta que A0 lo añada.

---

## 5. Pruebas ESCRITAS (NO ejecutadas)

**43 funciones de prueba** en 8 ficheros, todas contra los servicios REALES
resueltos por el inyector real (**sin dobles**, sin mocks).

| Fichero | Cubre | Nº |
|---|---|---|
| `tests/integration/test_elegibilidad.py` | `QA-K01`: veredicto del puerto, precedencia de motivos, equipo no elegible que NO entra | 9 |
| `tests/integration/test_solapamiento_horario.py` | `QA-K02` / `RN-K03`: solapamiento, semi-abiertos, cancelado, agenda intacta | 6 |
| `tests/integration/test_bye_manual.py` | bye manual: un equipo, sin horario, motivo obligatorio, no se quita | 5 |
| `tests/integration/test_preview_avance.py` | `QA-K04`: la previa NO escribe, informa del bloqueo y del reintento | 4 |
| `tests/integration/test_progresion.py` | avance confirmado, acta, idempotencia, destino bloqueado, slot ocupado | 5 |
| `tests/integration/test_version_desactualizada.py` | `QA-K05`: versión obsoleta → `RESOURCE_CHANGED`, sin escritura ni acta | 4 |
| `tests/integration/test_correccion.py` | `QA-K03`: impacto, cascada, limpieza del marcador, bloqueo, override, colocación manual | 6 |
| `tests/e2e/test_competencias_controller.py` | envelope, 401 antes que 403, forma única de encuentro, 409 de duplicado y de versión | 8 |

Infraestructura de pruebas: `settings_overlay.py` (registra la app y el
módulo de DI **sin tocar `config/settings/base.py`**), `conftest.py`,
`fixtures/competencias_fixtures.py` (el mundo real: edición, disciplina,
inscripciones, equipos, POOL, cuadro), `factories.py` (funciones puras) y
`urls_competencias.py` (URLconf de prueba con el controller y los handlers
globales).

---

## 6. Revisión estática de fuente (sustituto del runtime)

**33 comprobaciones** sobre el código escrito, con **7 correcciones
aplicadas**:

| # | Comprobación | Resultado |
|---|---|---|
| C-01 | El `expected_version` NO se compara en cada grupo de la edición | **Corregido**: el bloqueo se toma UNA vez al principio del comando; si no, el segundo grupo fallaría solo con la misma versión esperada. |
| C-02 | El DTO `EncuentroActualizarData` no tenía forma de alcanzar `EN_CURSO` (el único estado que acepta un resultado) | **Corregido**: se añadió el campo `estado` (aditivo). |
| C-03 | El vocabulario de acciones de auditoría no tenía acción para el cambio de estado ni para la cancelación | **Corregido**: se añadieron `ESTADO` y `CANCELACION` (aditivos, identificadores estables nuevos). |
| C-04 | `EquipoNoElegibleError` se importaba dentro del método | **Corregido**: import arriba, junto al resto. |
| C-05 | `_validar_orden` excluía el id de la COMPETENCIA en lugar del de la PARTICIPACIÓN | **Corregido**: `excluir_id=participacion.id`. |
| C-06 | `_validar_estado` lanzaba `OrdenDuplicadoError` (código de otra regla) | **Corregido**: `TransicionInvalidaError`. |
| C-07 | El flujo de resultado comparaba el estado DESPUÉS de mutar el objeto (siempre detectaba "sin cambio") | **Corregido**: se captura el estado ANTES. |
| C-08 | La desprogramación escribía aunque el encuentro ya estuviera sin horario | **Corregido**: guarda de "no hay nada que retirar". |
| C-09 | El `Q` de la migración con varios argumentos estaba escrito con tuplas posicionales (`F-60`) | **Corregido**: se escribió con argumentos nombrados, en las 4 restricciones del modelo. |
| C-10 | El `Lower` de la migración estaba importado por una ruta corta | **Corregido**: `django.db.models.functions.text.Lower`, que es la ruta que serializa el autodetector. |
| C-11 | `UniqueConstraint` con expresiones: `fields` y `expressions` son MUTUAMENTE EXCLUYENTES en Django 5.2 | **Verificado** contra el Django 5.2.11 instalado: la restricción se serializa como expresión pura (`F`, `F`, `Lower`), no como campos. |
| C-12 | `model_fields_set` vs `exclude_none` en el DTO de edición | **Verificado**: el controller pasa `payload.model_dump(exclude_unset=True)` → un `null` explícito se distingue de un campo ausente. |
| C-13 | El enum de slots (`SlotDestino.values`) es accessible a nivel de CLASE | **Verificado** contra el Django 5.2.11 instalado (`ChoicesType.values`). |
| C-14 | Los `choices` de los 5 modelos coinciden con los de la migración, **incluido el ORDEN** | **Verificado**. |
| C-15 | El presenter NO consulta la base de datos | **Verificado**: sólo proyecta `result` objects. |
| C-16 | El controller NO contiene lógica de negocio | **Verificado**: hidrata, delega, proyecta. |
| C-17 | Los mensajes de éxito son FIJOS (no interpolan UUIDs ni ids) | **Verificado**. |
| C-18 | El detalle técnico de la auditoría no se publica | **Verificado**: `OperacionAuditadaResult` no expone `detalle`; el presenter no lo publica. |
| C-19 | El orden de las rutas: `/agenda` ANTES de `/{id}` | **Verificado**. |
| C-20 | La agenda excluye los encuentros cancelados y los sin horario | **Verificado**. |
| C-21 | El solapamiento se mide por EQUIPO, no por participación | **Verificado**. |
| C-22 | La corrección no toca una colocación manual | **Verificado** (plan `_plan`). |
| C-23 | El `override` exige `override` Y `acepta_impacto` | **Verificado**. |
| C-24 | Los mensajes de estado del bye/encuentro no interpolan datos | **Verificado**. |
| C-25 | El orden de aplicación de los grupos de la edición es FIJO | **Verificado**: participantes → horario → enlace → bye → estado. |
| C-26 | El modelo `Disciplina`/`Equipo` se resuelve por metadatos del PROPIO campo del módulo | **Verificado**: el dominio no importa el dominio de otro módulo. |
| C-27 | El adaptador de elegibilidad importa los modelos del dueño de forma PEREZOSA | **Verificado**: el grafo de módulos queda acíclico. |
| C-28 | `IAlcanceEdicion` reproduce la firma real de `EdicionScopeService` | **Verificado** contra `modules/eventos/.../edicion_scope_service.py`. |
| C-29 | Las fixtures de prueba respetan las restricciones del dueño (un equipo por disciplina e inscripción; una inscripción viva por responsable y paquete) | **Corregido**: se separaron en tres inscripciones distintas. |
| C-30 | La migración declara `swappable_dependency(AUTH_USER_MODEL)` para el actor de la auditoría | **Verificado**. |
| C-31 | `pytest.ini` usa `--nomigrations`: la suite NO ejercita la migración | **Registrado** (§3.9). |
| C-32 | Los `TextChoices` son comparables con su cadena plana (el `Q` de la migración usa `"ACTIVO"`) | **Verificado** contra `django/db/models/enums.py` instalado. |
| C-33 | Ningún archivo fuera de las raíces permitidas fue modificado | **Verificado** (§9). |

---

## 7. Comandos FUTUROS (diferidos — NO ejecutados)

Todos requieren **autorización explícita** del usuario y **deben usar
`uv run`** (nunca el Python global ni el de `.venv`).

Workdir: `Aplicacion/backend`
Entorno: `DJANGO_SETTINGS_MODULE=modules.competencias.tests.settings_overlay`

| # | Comando | Qué comprueba |
|---|---|---|
| V1 | `uv run python -m pytest modules/competencias/tests -q` | La suite del paquete (43 pruebas). |
| V2 | `uv run python -m pytest modules/competencias/tests -q -k "elegibilidad or solapamiento or bye"` | El núcleo de `QA-K01`/`QA-K02`. |
| V3 | `uv run python -m pytest modules/competencias/tests -q -k "preview or progresion or correccion or version"` | El núcleo de `QA-K03`/`QA-K04`/`QA-K05`. |
| V4 | `uv run python manage.py makemigrations --check --dry-run --settings=modules.competencias.tests.settings_overlay` | Que la migración escrita a mano coincide con los modelos (equivale a `F-60`). |
| V5 | `uv run python manage.py check --settings=modules.competencias.tests.settings_overlay` | El sistema de comprobaciones de Django. |
| V6 | `uv run python manage.py migrate --settings=modules.competencias.tests.settings_overlay` | El REPLAY de la migración. |
| V7 | `uv run python manage.py migrate competencias zero --settings=modules.competencias.tests.settings_overlay` | La reversibilidad. |
| V8 | `uv run python manage.py migrate --settings=modules.competencias.tests.settings_overlay` | El segundo REPLAY. |
| V9 | `uv run python -m pytest modules/eventos/tests modules/usuarios/tests -q --settings=modules.competencias.tests.settings_overlay` | Que las suites de los dueños siguen verdes. |
| V10 | `uv run python -m pytest core/tests -q` | Que el baseline de `core` sigue verde. |
| V11 | `uv run python -m pytest modules -q --settings=modules.competencias.tests.settings_overlay` | La raíz completa del objetivo. |

> Con `--nomigrations` en `pytest.ini`, V1–V3 y V9–V11 crean las tablas desde
> los MODELOS: para ejercitar la migración hay que añadir
> `--no-migrations` desactivado (`-p no:cacheprovider` no aplica; la opción es
> `--nomigrations` en `addopts`, que se puede anular con `--migrations`).

---

## 8. Peticiones a A0 (registro permanente — NO aplicadas)

| # | Petición | Prioridad |
|---|---|---|
| A0-01 | Registrar `modules.competencias` en `LOCAL_APPS` (`config/settings/base.py`), **DESPUÉS** de `modules.salesianos_fest` (grafo de migraciones: `eventos → usuarios → pagos → commerce → salesianos_fest → competencias`). | **BLOQUEANTE** |
| A0-02 | Registrar `modules.competencias.di.CompetenciasModule` en `NINJA_EXTRA["INJECTOR_MODULES"]`. | **BLOQUEANTE** |
| A0-03 | Registrar `CompetenciasController` en `config/api.py` (`registrar_controladores(...)`): hasta entonces **ninguna de las 16 rutas existe**. | **BLOQUEANTE** |
| A0-04 | `SCHEMA_VERSIONS["competencias"] = "1.0.0"` en `core/contract_versions.py` (+ su aserción de drift). | **BLOQUEANTE** (drift) |
| A0-05 | Catálogo público de **19 códigos** nuevos en `core/exceptions.py`: `COMPETENCIA_NO_ENCONTRADA` 404 · `RONDA_NO_ENCONTRADA` 404 · `ENCUENTRO_NO_ENCONTRADO` 404 · `COMPETENCIA_EQUIPO_NO_ENCONTRADA` 404 · `EQUIPO_NO_ENCONTRADO` 404 · `DISCIPLINA_NO_ENCONTRADA` 404 · `COMPETENCIA_DUPLICADA` 409 · `COMPETENCIA_EQUIPO_DUPLICADO` 409 · `ORDEN_DUPLICADO` 409 · `RONDA_DUPLICADA` 409 · `SOLAPAMIENTO_HORARIO` 409 · `SLOT_OCUPADO` 409 · `DESTINO_BLOQUEADO` 409 · `RESOURCE_CHANGED` 409 · `TRANSICION_INVALIDA` 409 · `HORARIO_INVALIDO` 422 · `MOTIVO_REQUERIDO` 422 · `GANADOR_INVALIDO` 422 · `ENLACE_INVALIDO` 422 · `BYE_INVALIDO` 422 · `PARTICIPANTE_INVALIDO` 422 · `EQUIPO_NO_ELEGIBLE` 422. **Mientras no estén catalogados, el catálogo global devuelve el mensaje GENÉRICO por status** (`core/exceptions.py` §`GENERIC_PUBLIC_MESSAGES`): la respuesta es segura y tipada, pero la prosa no explica el motivo. | ALTA |
| A0-06 | Ratificar (o no) las 16 rutas en `evidence/contracts/route-to-wrapper-ledger.csv` y `evidence/routes/SH-05-provisional-endpoint-and-presenter-register.md`. | ALTA |
| A0-07 | Sincronizar `00-matriz-tareas.md` con `T-050`, `T-051`, `T-052`. | MEDIA |
| A0-08 | `*.sqlite3` en `.gitignore`. | MEDIA |

**Los códigos del catálogo global que YA existen y este paquete reutiliza:**
`RESOURCE_CHANGED` 409 · `SLOT_OCUPADO` 409 · `DESTINO_BLOQUEADO` 409 ·
`EQUIPO_NO_ELEGIBLE` 422. Los demás códigos de este módulo usan la nomenclatura
nueva (`_NO_ENCONTRADA`) que A0 debe catalogar.

---

## 9. Ficheros

**Creados (73 ficheros Python + 1 de evidencia), todos dentro de las raíces
permitidas:**

| Ruta | Contenido |
|---|---|
| `Aplicacion/backend/modules/competencias/**` | 73 ficheros Python: modelos, dominio (constantes, excepciones, DTOs, results, selectores, puertos, servicios core/flujos/orquestadores), infraestructura (adaptadores), presentación (esquemas, presenter, controller), `di.py`, `models.py`, `admin.py`, `migrations/0001_initial.py` y `tests/**`. |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/domains/DOM-07-competitions.md` | Este informe. |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | Fila del tablero + transición de DOM-07. |

**Modificados (continuidad con el trabajo previo del paquete):**

| Fichero | Cambio |
|---|---|
| `domain/ports/__init__.py` | **AÑADIDO** el puerto `IAlcanceEdicion` (el docstring del archivo ya lo anunciaba). `IEquipoElegibleService` **NO se tocó**. |
| `domain/schemas/competencias_schemas.py` | **AÑADIDO** el campo `estado` a `EncuentroActualizarData`. |
| `domain/models/auditoria.py` | **AÑADIDAS** las acciones `ESTADO` y `CANCELACION`. |
| `domain/exceptions.py` | **AÑADIDA** `CompetenciaEquipoNoEncontradaError`. |

**Ninguna raíz congelada, compartida o prohibida fue tocada:** ni `contract/`,
ni `Aplicacion/plan/`, ni `Aplicacion/documentacion/`, ni `backend/`,
ni `frontend/`, ni `worker/`, ni `proxy/`, ni `.opencode/`, ni `config/`, ni
`core/`. Los módulos `commerce`, `pagos`, `eventos`, `usuarios`,
`salesianos_fest` y `marketplace` **NO se editaron**: este paquete los CONSUME
por puerto.

---

## 10. Desviaciones

| # | Desviación | Motivo |
|---|---|---|
| `D-DOM07-01` | Se AÑADIÓ `estado` a `EncuentroActualizarData`. | Sin él, `EN_CURSO` —el único estado que acepta un resultado según el vocabulario cerrado del módulo— era inalcanzable y el flujo de resultado no tenía entrada. |
| `D-DOM07-02` | Se AÑADIERON `ESTADO` y `CANCELACION` al vocabulario de acciones auditadas. | `RN-K02` exige auditar el ESTADO; el vocabulario cerrado no tenía acción para un cambio de estado ni para una cancelación. Identificadores estables nuevos (la migración es la primera). |
| `D-DOM07-03` | Se AÑADIÓ `CompetenciaEquipoNoEncontradaError` (`COMPETENCIA_EQUIPO_NO_ENCONTRADA`). | La participación en el cuadro NO es el equipo de inscripción: `EquipoNoEncontradoError` es de otro hecho. |
| `D-DOM07-04` | La transición de estado de la COMPETENCIA y la INVALIDACIÓN de una RONDA **no tienen comando**. | No hay DTO ni ruta que las pida y ningún contrato las congela: **no se inventan**. Quedan como decisiones abiertas (`OD-DOM07-01`, `OD-DOM07-02`). |
| `D-DOM07-05` | El cuadro PÚBLICO de `/competencias/[id]` **no se implementó**. | El plan lo declara como propuesta sin página ID (`frontend/05` §2) y el ledger no lo congela: la superficie pública del cuadro sería una ruta inventada. |
| `D-DOM07-06` | La regla de solapamiento es la GLOBAL de la edición, no una por disciplina. | Ningún contrato congela una regla por disciplina y `RN-K03` la deja abierta ("cuando la disciplina/regla lo prohíba"). No se inventa. |
| `D-DOM07-07` | Se usó el bloqueo OPTIMISTA (`expected_version`) y NO `select_for_update`. | SQLite no soporta `select_for_update` (`F-55`) y el propio contrato pide "versionado/`expected_version` u otra protección equivalente". |
| `D-DOM07-08` | El motivo auditado es obligatorio también al RETIRAR un equipo del cuadro (no sólo al mover su semilla). | Retirar es una decisión administrativa sensible y `RN-K02` exige auditoría. |
| `D-DOM07-09` | La migración `0001_initial` está ESCRITA A MANO. | `makemigrations` está prohibido por la instrucción del usuario (§0). Su equivalencia con los modelos está razonada estáticamente (`C-04`…`C-14`) pero **NO verificada en runtime**. |

---

## 11. Decisiones abiertas (nunca adivinadas)

- `OD-DOM07-01` — ¿quién y con qué permisos **invalida** una ronda? El
  vocabulario tiene `INVALIDADA` y el modelo la conserva, pero ningún DTO la
  comanda.
- `OD-DOM07-02` — ¿cómo se mueve una **COMPETENCIA** por su ciclo
  (`PLANIFICADA → EN_CURSO → FINALIZADA → CANCELADA`)? No hay DTO ni ruta.
- `OD-DOM07-03` — ¿cuál es el **formato del cuadro público** (`/competencias/[id]`)?
  Sin página ID en el plan y sin ruta en el ledger.
- `OD-DOM07-04` — ¿el `detalle` de la auditoría debe exponerse a alguna
  superficie interna? Hoy es sólo técnico.
- `OD-DOM07-05` — ¿la DURACIÓN de un encuentro y el FORMATO del cuadro los
  decide el administrador o los calcula el backend? Este módulo no los fija:
  el calendario es del administrador y el formato del cuadro, un dato de
  lectura.

---

## 12. Rollback

1. `uv run python manage.py migrate competencias zero --settings=modules.competencias.tests.settings_overlay`
   (**sólo con autorización de A0**).
2. Borrar `Aplicacion/backend/modules/competencias/**` y la evidencia de este
   paquete.
3. Restaurar `STATE.md` y los topics de Engram.

**Lo que NO se pierde:** la **auditoría** (`AuditoriaOperacion`) es un ACTA:
un rollback físico la borraría, pero la historia auditada de un cuadro ya
publicado se conserva con operaciones compensatorias y versionadas (un
avance corregido queda en el historial, no se borra). El punto de rollback es
`fd1c4c123df3767ef6e86908565edf2d4c27c00a` (el commit del usuario; **no
revertir ni resetear**).

---

## 13. Revisión (slices)

El paquete **supera el presupuesto de revisión de ~400 líneas** (73 ficheros
Python). Se declara en **cuatro slices autonomous**, todos verificados juntos
en la revisión estática:

| Slice | Contenido | Ficheros |
|---|---|---|
| **WU-A · dominio** | modelos, constantes, excepciones, DTOs, results, puertos, selectores, proyección | 14 |
| **WU-B · comportamiento** | servicios core, flujos, orquestador, DI, adaptador de elegibilidad | 16 |
| **WU-C · superficie** | esquemas HTTP, presenter, controller, `admin.py`, `models.py`, migración | 8 |
| **WU-D · pruebas** | overlay, conftest, fixtures, factories, URLconf, 8 ficheros de prueba | 14 |

---

## 14. Preparación de API-05 (PROVISIONAL)

**API-05** (`wave-03-api-integration/API-05-competition-admin-integration.md`)
espera a este freeze. Lo que este paquete le entrega:

- **16 rutas** con sus wrappers `*In`/`*Out` y sus presentadores;
- **un presenter único** (`CompetenciasPresenter`) y **una forma de
  encuentro** (`EncuentroOut`) que el espejo Zod replica 1:1;
- **`SCHEMA_VERSION = "1.0.0"`** del módulo `competencias`;
- el **veredicto de elegibilidad** con su código de motivo (`QA-K01`);
- la **vista previa** de avance y de corrección (`QA-K03`, `QA-K04`).

**La preparación es PROVISIONAL**: depende de (a) la verificación diferida
(§0), (b) el registro permanente de A0 (A0-01…A0-04) y (c) la ratificación de
las rutas en el ledger (A0-06). El espejo Zod del frontend **no se ha
escrito**: `frontend/**` es raíz congelada para este paquete.

---

## 15. Concurrencia

- `Aplicacion/backend/modules/marketplace/**` (**DOM-05**, A5) y
  `Aplicacion/backend/modules/salesianos_fest/**` (**DOM-01/DOM-02/DOM-03**,
  A3/A4) y `Aplicacion/frontend/**` (**FND-06 / UI-01A**, A0/A7) **NO se
  tocaron, no se revirtieron y no se fusionaron**. Sus **filas del tablero no
  se editaron**.
- Los módulos `commerce`, `pagos`, `eventos` y `usuarios` **NO se editaron**:
  este paquete los CONSUME por puerto.
- `git stash` **nunca** fue invocado. **Ningún commit** fue creado.
- El trabajo previo de este paquete (el puerto `IEquipoElegibleService` y los
  modelos, constantes, excepciones y DTOs) se **PRESERVÓ**: los cambios son
  ADITIVOS y nada se reescribió por estilo.

---

## 16. Próximo paquete

**API-05** — *Competition admin integration* — después de la verificación
diferida de DOM-07 con `uv run` (§7), que hoy exige la autorización explícita
del usuario, y después del registro permanente de A0 (A0-01…A0-04).
