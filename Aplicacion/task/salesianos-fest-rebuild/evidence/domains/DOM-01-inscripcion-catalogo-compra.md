# DOM-01 — Inscripción: catálogo, alta inicial y compra congelada

**Paquete:** `DOM-01` (`wave-02-domain-backend`) · **Cambio:** `salesianos-fest-rebuild`
**Tareas de origen:** `T-020`, `T-021` (2 de las 54 filas de `00-matriz-tareas.md`)
**Propietario:** A3 · **Fecha:** 2026-11-19 · **Modo:** Standard
**Raíz física del módulo:** `Aplicacion/backend/modules/salesianos_fest/`
**Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (sin commit creado, `git stash` nunca invocado)

---

## 1. Resultado del paquete

DOM-01 deja implementado y verificado el **catálogo de inscripción por edición** y el
**alta de la inscripción inicial con su compra pendiente**:

| Entregable | Dónde | Comportamiento congelado que cumple |
|---|---|---|
| Catálogo por EDICIÓN | `Disciplina`, `Paquete`, `PaqueteDisciplina`, `PaqueteBeneficio`, `PaquetePrecio` | `RN-E01` (todo el catálogo cuelga de `eventos.Edicion`) · `RN-C02` (el precio lo resuelve y congela el servidor) · `FL-01` paso 3 (**no hay precio de reserva**) |
| Inscripción y equipos | `Inscripcion`, `Equipo` | `RN-I01` (responsable = `Persona`) · `RN-I02` (**los cupos pagados nacen en cero**) · `RN-I03` (el saldo lo calcula el servidor y nunca es negativo) |
| Compra inicial | `InscripcionFlujo` → `commerce.CompraFlujo` | `RN-C01` (cada dominio tiene su propio flujo de compra) · `RN-C02` (snapshot congelado) · `FR-04` I-4 (reabrir el checkout **no** crea otra compra) |
| Superficie HTTP | `CatalogoController`, `InscripcionController` + presenters tipados | `FREEZE-PS-1.0.0` (wrappers compuestos por bloques, `SCHEMA_VERSION`) · `FREEZE-ENV-1.0.0` (envelope y códigos estables) |

**45 tests de comportamiento, todos verdes.** La compra inicial es **recuperable**
(reintentar devuelve la misma inscripción y su misma compra pendiente) y **no habilita
ningún cupo** hasta que la activación de derechos verifique el pago (DOM-02).

---

## 2. Módulo y archivos

### 2.1 Raíz física

`Aplicacion/backend/modules/salesianos_fest/` — **módulo Django `salesianos_fest`**, elegido
por DOM-01 (DOM-02 lo consume: *"Registration module root selected by DOM-01"*) y coherente
con el comando de verificación del paquete (`modules/salesianos_fest/tests`).

### 2.2 Archivos creados (63)

| Capa | Archivo | Contenido |
|---|---|---|
| Paquete | `__init__.py` · `apps.py` · `models.py` · `admin.py` · `di.py` | `SCHEMA_VERSION = "1.0.0"` · `AppConfig` (`label = "salesianos_fest"`) · re-export puro de modelos · admin de operación · bindings de DI |
| Dominio | `domain/constants.py` | Vocabularios cerrados: `EstadoDisciplina`, `EstadoPaquete`, `TipoBeneficioPaquete`, `EstadoInscripcion`, `EstadoEquipo`, `ModalidadDisciplina`, `CausaOperativaInscripcion` |
| Dominio | `domain/exceptions.py` | 6 excepciones de dominio con `code` estable: `PAQUETE_NO_VIGENTE`, `DISCIPLINA_NO_PERMITIDA`, `EQUIPO_DUPLICADO`, `INSCRIPCION_NO_ENCONTRADA`, `INSCRIPCION_NO_AUTORIZADA`, `COMPRADOR_SIN_PERSONA` |
| Dominio | `domain/models/catalogo.py` | `Disciplina`, `Paquete`, `PaqueteDisciplina`, `PaqueteBeneficio`, `PaquetePrecio` |
| Dominio | `domain/models/inscripcion.py` | `Inscripcion` (con `HistoricalRecords`), `Equipo` |
| Dominio | `domain/schemas/catalogo_schemas.py` · `domain/schemas/inscripcion_schemas.py` | DTOs internos (`PaqueteOfertaData`, `DisciplinaOfertaData`, `EquipoCreateData`, `InscripcionInicialData`) |
| Dominio | `domain/results/catalogo_result.py` · `domain/results/inscripcion_result.py` | Results que el presenter proyecta a wrappers HTTP |
| Dominio | `domain/selectors/catalogo_selector.py` · `domain/selectors/inscripcion_selector.py` | Consultas de SOLO LECTURA, siempre acotadas por edición |
| Dominio | `domain/services/core/catalogo_core_service.py` · `…/inscripcion_core_service.py` | Servicios core sync, sin `transaction.atomic()` propio |
| Dominio | `domain/services/flujos/catalogo_flujo.py` · `…/inscripcion_flujo.py` | Flujos async; `inscripcion_flujo.py` es el ÚNICO lugar con `transaction.atomic()` |
| Dominio | `domain/services/orchestrators/catalogo_orchestrator.py` · `…/inscripcion_orchestrator.py` | Fachadas async delgadas: un método por endpoint |
| Dominio | `domain/ports/__init__.py` | Puertos `IAlcanceEdicionService` e `ITitularidadService` |
| Infraestructura | `infrastructure/services/alcance_y_titularidad.py` | Adaptadores de los puertos (el único punto que toca `eventos` y `usuarios`) |
| Infraestructura | `infrastructure/repositories/__init__.py` | **VACÍO a propósito** (`django-app-architecture-contract.md` §4.11 y §9) |
| Presentación | `presentation/schemas/catalogo_schemas.py` · `…/inscripcion_schemas.py` | Wrappers HTTP tipados, compuestos por bloques (Identidad + General + Específico) |
| Presentación | `presentation/presenters/catalogo_presenter.py` · `…/inscripcion_presenter.py` | Transformadores puros; el presenter de inscripción **publica la causa operativa** |
| Presentación | `presentation/controllers/catalogo_controller.py` · `…/inscripcion_controller.py` | Controllers "sagrados": cero lógica, cero ORM, cero `error_response` |
| Migración | `migrations/0001_initial.py` | `0001_initial` (706 líneas generadas) con `dependencies = [("eventos","0001_initial"), ("usuarios","0002_grupos_funcionales"), swappable_dependency(AUTH_USER_MODEL)]` |
| Tests | `tests/fixtures/fest_fixtures.py` · `tests/conftest.py` · `tests/settings_overlay.py` · `tests/urls_salesianos_fest.py` · `tests/factories.py` *(no procede: los payloads se construyen en los tests por ser DTOs de dominio)* | Fixtures, overlay de verificación y URLconf de prueba |
| Tests | `tests/integration/test_catalogo_paquetes.py` · `test_catalogo_disciplinas_inscripcion.py` · `test_inscripcion_inicial.py` · `test_inscripcion_alcance_invalido.py` · `test_inscripcion_pago_pendiente.py` · `test_inscripcion_duplicada.py` · `test_inscripcion_permiso.py` · `test_inscripcion_concurrencia.py` | 38 tests de comportamiento |
| Tests | `tests/e2e/test_inscripcion_controller.py` | 7 tests de superficie HTTP |

### 2.3 Archivos modificados

| Archivo | Cambio |
|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | Fila DOM-01 del tablero + transición de este paquete |

**Ningún archivo compartido de A0 fue editado** (`config/settings/base.py`, `config/api.py`,
`core/exceptions.py`, `core/contract_versions.py`, `core/types.py`, `core/responses.py`).
**Ningún archivo de `commerce`, `pagos`, `eventos` ni `usuarios` fue editado.** Ninguna raíz
congelada, ningún contrato, ningún plan, ningún documento, ningún secreto, ninguna base de datos.

---

## 3. Interfaces consumidas (congeladas)

| Interfaz | Dueño | Cómo se consume | Qué se rinde |
|---|---|---|---|
| `modules.commerce.domain.services.flujos.compra_flujo.CompraFlujo` | `commerce` (A2) | **DIRECTO** — es la interfaz comercial CONGELADA (`FREEZE-CM-1.0.0`, `RN-C01`, `D-FND-04-06`: "los dominios crean su compra en proceso") | La compra inicial: `CompraCreateData(persona_id, origen=INSCRIPCION, lineas=[LineaCompraSnapshot], referencia="INSCRIPCION:{id}:INICIAL")`. El total lo deriva `commerce` de las líneas; este módulo **no** declara ningún total |
| `modules.commerce.domain.schemas.compra_schemas.{CompraCreateData, LineaCompraSnapshot}` | `commerce` | DTOs de dominio (NO schemas HTTP) | El snapshot inmutable de lo comprado |
| `modules.eventos.domain.services.core.edicion_scope_service.EdicionScopeService` | `eventos` (A1) | **A TRAVÉS DE PUERTO** `IAlcanceEdicionService` → `AlcanceEdicionAdapter` | El orden congelado de resolución de edición (FR-02 §2.2): `resolver_explicita` (nivel 1) y `resolver_actual` (niveles 2→3→4) |
| `modules.eventos.domain.constants.ModuloLogico` | `eventos` | Constante de vocabulario | La comprobación `edicion.modulo_habilitado("inscripciones")` (`FR-02` §2.5, `RN-E02`) |
| `modules.usuarios.domain.services.core.titularidad_service.TitularidadService` | `usuarios` (A1) | **A TRAVÉS DE PUERTO** `ITitularidadService` → `TitularidadAdapter` | El sujeto de la titularidad sale SIEMPRE de la cuenta autenticada (`RN-U04`) y la comprobación `TITULARIDAD_RESPONSABLE` la hace el MÓDULO DUEÑO del recurso (`FR-03` §2.1) |
| `modules.commerce.domain.services.core.registro_activadores_compra.RegistroActivadoresCompra` | `commerce` (A0, FND-05) | **NO** se consume todavía | El activador `IActivadorDominioCompra` de origen `INSCRIPCION` es de **DOM-02**; DOM-01 deja `cupos_pagados = 0` |

**Por qué `commerce` es directo y `eventos`/`usuarios` van por puerto.** `commerce` es la
INFRAESTRUCTURA comercial compartida y su interfaz está congelada para que los dominios la
consuman en proceso; `eventos` y `usuarios` son dominios con dueño, y atravesarlos por un
puerto evita que este módulo dependa de sus internos. La asimetría es deliberada y está
documentada en `domain/ports/__init__.py`.

---

## 4. Reglas congeladas y cómo se cumplen

| Regla | Cumplimiento | Prueba |
|---|---|---|
| `RN-E01` — el catálogo es de una edición | `Disciplina`, `Paquete` y `PaquetePrecio` cuelgan de `eventos.Edicion`; el selector SIEMPRE filtra por edición | `test_el_catalogo_es_por_edicion` · `test_el_catalogo_de_disciplinas_no_mezcla_ediciones` |
| `RN-C02` — el precio lo calcula y congela el servidor | El flujo resuelve el precio VIGENTE del catálogo y lo entrega como línea; el total lo deriva `commerce`. El payload HTTP **no** admite ningún importe | `test_el_servidor_congela_el_precio_del_catalogo` |
| `FL-01` paso 3 — **no hay precio de reserva** | Un paquete sin precio vigente (o con precio vencido) NO aparece en el catálogo y NO se puede comprar | `test_un_paquete_sin_precio_no_esta_a_la_venta` · `test_un_paquete_con_precio_vencido_no_esta_a_la_venta` · `test_un_paquete_sin_precio_vigente_no_se_puede_comprar` |
| `RN-I01` — la inscripción tiene un responsable | `Inscripcion.responsable` es una FK a `usuarios.Persona`; el cliente no lo declara: lo resuelve el orquestador desde la cuenta autenticada | `test_el_alta_crea_la_inscripcion_sus_equipos_y_la_compra_pendiente` · `test_una_cuenta_sin_persona_no_puede_inscribirse` |
| `RN-I02` — una compra pendiente NO habilita cupos | `Inscripcion.cupos_pagados` nace en `0`; `cupos_disponibles` se deriva (`pagados − asignados`) y es `0` mientras el pago esté pendiente | `test_la_inscripcion_nace_con_cero_cupos_pagados` · `test_el_saldo_disponible_es_cero_mientras_el_pago_pendiente` · `test_el_alta_devuelve_la_inscripcion_y_su_compra_pendiente` |
| `RN-I03` — el saldo nunca es negativo | `CHECK (cupos_asignados <= cupos_pagados)` en la base de datos + `max(…, 0)` en la proyección | `fest_inscripcion_asignados_no_superan_pagados` (verificado en el esquema SQLite) |
| `RN-I05` — la elegibilidad se verifica en backend | El PATRÓN NO lo elige el cliente: cada disciplina debe existir en la edición, estar `ACTIVA` y estar incluida en el paquete | `test_una_disciplina_fuera_del_paquete_no_se_puede_comprar` · `test_una_disciplina_inactiva_no_se_puede_comprar` |
| `RN-C01` — cada dominio tiene su propio flujo de compra | No hay carrito conjunto: la compra la crea `InscripcionFlujo` a través de `CompraFlujo` | `test_el_alta_crea_la_inscripcion_sus_equipos_y_la_compra_pendiente` (origen `INSCRIPCION`) |
| `RN-C02` / `FR-04` I-4 — reabrir el checkout no crea otra compra | La referencia de la intención es estable (`INSCRIPCION:{id}:INICIAL`) y `CompraFlujo` la reutiliza | `test_el_reintento_no_crea_una_segunda_compra` |
| `RN-C03` — cerrar el modal no cancela | El paquete no expone ninguna cancelación; la compra queda `PENDIENTE` y recuperable | `test_la_compra_queda_pendiente_y_es_recuperable` |
| `RN-I06` — comprar cupos extra no duplica beneficios `FIJO_INICIAL` | El paquete DECLARA el beneficio (`FIJO_INICIAL` / `POR_CUPO`); la concesión es de DOM-02 y la regla completa sigue ABIERTA (`PD-09`) | `test_el_paquete_se_publica_con_su_precio_vigente_y_sus_beneficios` (el beneficio se publica como OFRECIDO, `RN-P01`) |
| `FR-02` §2.5 / `RN-E02` — un módulo no habilitado no expone catálogo | `ModuloNoHabilitadoError` (`MODULO_NO_HABILITADO`, 409) | `test_una_edicion_sin_el_modulo_no_expone_compra` · `test_una_edicion_sin_el_modulo_no_expone_catalogo` |
| `FR-03` §2.1 — el grupo NO sustituye la titularidad | Una cuenta del grupo `Administrador` que no es la responsable recibe `INSCRIPCION_NO_AUTORIZADA` | `test_el_grupo_administrador_no_sustituye_la_titularidad` |
| `RN-U04` — el documento es un identificador, no una credencial | El sujeto de la titularidad sale SIEMPRE de la cuenta autenticada | `test_una_cuenta_sin_persona_no_puede_inscribirse` · `test_otro_actor_no_puede_consultar_la_inscripcion` |
| `QA-I01` — 0 cupos habilitados antes del pago | Verificado en integración y en e2e | `test_la_inscripcion_nace_con_cero_cupos_pagados` · `test_el_alta_devuelve_la_inscripcion_y_su_compra_pendiente` |

---

## 5. Los controladores no contienen reglas de negocio

`PLAN_REFACTORIZACION.md` §1.A y `django-app-architecture-contract.md` §4.8. Los dos
controllers de este paquete:

- **no** consultan el ORM (ni `objects.all()` ni un selector);
- **no** tienen `if`/`for` de negocio;
- **no** construyen respuestas de error (`error_response` no aparece);
- **no** calculan precios, cupos ni elegibilidad;
- sólo parsean, delegan al orquestador y devuelven `success_response(presenter.present(result))`.

La **causa operativa** la declara el dominio (`CausaOperativaInscripcion`) y la **publica el
presenter** (`InscripcionPresenter.present_inicial`), no el controller: por eso el comprador
sabe si su alta se creó o se reutilizó sin que el controller decida nada.

---

## 6. Comandos y códigos de salida

**Entorno:** workdir `Aplicacion/backend` · intérprete `.\.venv\Scripts\python.exe` (Python 3.10)
· settings de verificación `modules.salesianos_fest.tests.settings_overlay` (SQLite en memoria)
· `DJANGO_SETTINGS_MODULE` fijado por variable de entorno (F-13: pytest-django da prioridad a
la variable sobre `pytest.ini`).

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V1 | `python -m pytest modules/salesianos_fest/tests -q -k "paquete or inscripcion"` | **0** | **45 passed**, 38 warnings — el filtro del paquete selecciona el 100 % de los tests del módulo |
| V2 | `python -m pytest modules/salesianos_fest/tests -q` | **0** | **45 passed** (suite completa del módulo) |
| V3 | `python manage.py makemigrations --check --dry-run --settings=modules.salesianos_fest.tests.settings_overlay` | **0** | `No changes detected` — la migración coincide con los modelos |
| V4 | `python manage.py check --settings=modules.salesianos_fest.tests.settings_overlay` | **0** | `System check identified no issues (0 silenced)` |
| V5 | `python manage.py check` (settings por defecto) | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **baseline ambiental idéntico** a FND-01/02/03/04/05, NO es una regresión |
| V6 | `python manage.py makemigrations --check --dry-run` (settings por defecto) | **1** | mismo `DB_NAME` — baseline ambiental idéntico |
| V7 | `manage.py migrate --settings=…overlay` (SQLite en archivo) | **0** | `Applying salesianos_fest.0001_initial... OK` |
| V8 | `manage.py showmigrations salesianos_fest --settings=…overlay` | **0** | `[X] 0001_initial` |
| V9 | `manage.py migrate --settings=…overlay` (repetición) | **0** | `No migrations to apply` — idempotente |
| V10 | `manage.py migrate salesianos_fest zero --settings=…overlay` | **0** | `Unapplying salesianos_fest.0001_initial... OK` — reversible |
| V11 | `manage.py migrate salesianos_fest --settings=…overlay` (replay) | **0** | `Applying salesianos_fest.0001_initial... OK` — reproducible |
| V12 | inspección del esquema SQLite | **0** | `UNIQUE (edicion_id, responsable_id, paquete_id) WHERE NOT (estado = 'CANCELADA')` + `CHECK (cupos_asignados <= cupos_pagados)` + 6 UNIQUE más |
| V13 | `python -m pytest core/tests -q` (settings del proyecto) | **0** | **100 passed** — baseline FND-01 intacto |
| V14 | `python -m pytest modules/eventos/tests -q` (overlay FND-02) | **0** | **63 passed** — baseline FND-02 intacto |
| V15 | `python -m pytest modules/usuarios/tests -q` (overlay FND-03) | **0** | **35 passed** — baseline FND-03 intacto |
| V16 | `python -m pytest modules/commerce/tests modules/pagos/tests -q` (overlay FND-04) | **0** | **96 passed** — baseline FND-04/FND-05 intacto |
| V17 | `python -m pytest -q` (raíz del objetivo, overlay DOM-01) | **1** | **338 passed · 1 failed** — el único fallo es `modules/pagos/tests/integration/test_pago_confirmacion.py::test_la_compra_se_marca_pagada_sin_activar_derechos` (ver §8) |
| V18 | `python -m pytest -q` (raíz del objetivo, settings por defecto) | **2** | `RuntimeError: Model class … doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS` — **A0-01 pendiente** (misma clase que el V2 de FND-02), no un defecto del módulo |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **vacío** |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **vacío** — raíces congeladas intactas |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — sin commit creado |
| R4 | `git stash` | — | **nunca invocado** |

**Artefactos sobrantes:** la rehearsal de migraciones usó un SQLite **fuera del repositorio**
(`%TEMP%\opencode\dom01_migraciones.sqlite3`), que se **borró** al terminar. No queda ningún
`*.sqlite3` en `Aplicacion/backend/` (las bases de datos son un artefacto prohibido).

---

## 7. Fallos conocidos y regresiones

### 7.1 Fallos conocidos (NO regresiones)

| # | Fallo | Estado | Dueño |
|---|---|---|---|
| B-1 | `manage.py check` / `makemigrations --check --dry-run` con los settings por defecto → `DB_NAME` | **Baseline ambiental idéntico** a FND-01…FND-05 | A0 (existente) |
| B-2 | `python -m pytest -q` con los settings por defecto → `RuntimeError: … isn't in an application in INSTALLED_APPS` | **A0-01 pendiente**: el paquete no puede registrar su propia app (`config/settings/base.py` es de A0). Misma clase que el V2 de FND-02 | **A0** (petición A0-01) |

### 7.2 Regresión INTRODUCIDA por este paquete (1)

| # | Test | Causa | Resolución |
|---|---|---|---|
| **R-DOM-01-01** | `modules/pagos/tests/integration/test_pago_confirmacion.py::test_la_compra_se_marca_pagada_sin_activar_derechos` | El test de FND-05 afirma `assert not apps.is_installed("modules.salesianos_fest")` para probar que **todavía no existe ninguna app de derechos** en el objetivo. **DOM-01 crea esa app** (la app de inscripciones), así que la premisa del test queda obsoleta: la app existe, pero **NO** contiene tablas de derechos ni un activador — eso es de DOM-02 | El fichero está en una **raíz prohibida** para este paquete (`commerce`/`pagos`), así que **NO se editó**. Petición explícita a **A0/A2**: actualizar la aserción a `assert not apps.is_installed("modules.validaciones")` (o comprobar la ausencia del *activador* de origen `INSCRIPCION`, que es la afirmación real que el test quiere hacer) |

**Alcance exacto:** el fallo aparece SÓLO cuando `modules.salesianos_fest` está registrado
(overlay DOM-01 → V17). Con los settings por defecto (V16) la suite `commerce`+`pagos` sigue
verde (96 passed). Con el registro permanente que A0 hará, el fallo passing a ser permanente:
**por eso la petición es bloqueante para el registro de la app**, no para este paquete.

**Ninguna aserción de `commerce`, `pagos`, `eventos` ni `usuarios` fue tocada.** No hay
regresión funcional: 338 de 339 tests de la raíz del objetivo pasan, y los 45 tests de este
paquete pasan.

---

## 8. Solicitudes a A0 (registradas, NO aplicadas)

| # | Solicitud | Fichero de A0 | Por qué |
|---|---|---|---|
| **A0-01** | Registrar la app `modules.salesianos_fest` en `INSTALLED_APPS` **después** de `modules.commerce` (grafo de migraciones) y su módulo de DI `modules.salesianos_fest.di.SalesianosFestModule` en `NINJA_EXTRA["INJECTOR_MODULES"]` | `config/settings/base.py` | Sin el registro la app no existe para Django: el paquete no se puede importar ni servir (B-2). El overlay local replica exactamente este registro y debe ser retirado cuando A0 lo aplique (F-39) |
| **A0-02** | Registrar los controllers `CatalogoController` e `InscripcionController` con `registrar_controladores(...)` | `config/api.py` | FR-07 §3.1.2: **una ruta no existe hasta que su controller está registrado**. Hasta entonces, el código de este paquete es código muerto por diseño (igual que la nota de `config/api.py` sobre `pases`/`marketplace`) |
| **A0-03** | Añadir al catálogo público los códigos: `PAQUETE_NO_VIGENTE` (409, ya declarado por el ledger para `RT-CM-01`), `DISCIPLINA_NO_PERMITIDA` (422), `EQUIPO_DUPLICADO` (422), `INSCRIPCION_NO_ENCONTRADA` (404), `INSCRIPCION_NO_AUTORIZADA` (403), `COMPRADOR_SIN_PERSONA` (422) | `core/exceptions.py` | Los códigos viajan estables en `error.code`; sin prosa en el catálogo la respuesta cae al mensaje genérico por status (F-21). Las fases de error del paquete **no construyen prosa** (el texto vive en la excepción, nunca sale al cliente) |
| **A0-04** | Actualizar la aserción obsoleta de FND-05 (`assert not apps.is_installed("modules.salesianos_fest")`) | `modules/pagos/tests/integration/test_pago_confirmacion.py` | R-DOM-01-01 (§7.2) |
| **A0-05** | Ratificar en el ledger la ruta nueva `RT-IN-14` (`POST /inscripciones`, alta de la inscripción inicial) y los nombres `CatalogoPaquetesPresenter`/`CatalogoDisciplinasPresenter`/`InscripcionDetallePresenter`/`EquiposInscripcionPresenter` que este paquete usa | `evidence/contracts/route-to-wrapper-ledger.csv` + `SH-05` | El ledger de GOV-01 no tenía fila para el ALTA de la inscripción inicial (sólo para la ampliación `RT-CM-01`, que es de DOM-02). Todas las rutas de este paquete son **provisionales** hasta que A0 las ratifique |
| **A0-06** | Registrar `salesianos_fest` (o `inscripciones`) en `core/contract_versions.py` y añadirlo a `MODULOS_COMPLETADOS` del test de drift | `core/contract_versions.py` + `core/tests/integration/test_contract_versions.py` | El módulo declara `SCHEMA_VERSION = "1.0.0"` (FR-07 §1.1, dueño del módulo); el registro global es de A0 |
| **A0-07** | Sincronizar la matriz física `00-matriz-tareas.md` (filas `T-020`, `T-021`) | `Aplicacion/task/salesianos-fest-rebuild/00-matriz-tareas.md` | La matriz está fuera de las raíces de edición permitidas de este paquete (mismo aviso que FND-02…FND-05) |
| **A0-08** | `*.sqlite3` en el `.gitignore` del objetivo | `Aplicacion/backend/.gitignore` | Petición heredada de FND-01…FND-05 (este paquete no dejó ningún `.sqlite3` en el repo) |
| **A0-09** | Decidir la **forma del dinero en el wire** (divergencia `D-DOM-01-01`, §9) | `core/responses.py` / `core/types.py` | El dinero se declara como `Decimal` en los wrappers (igual que `pagos`) y sale como **cadena** en el JSON, aunque `core/responses.py` quiere números (`_decimal_to_float`) y `BaseSchema.model_config` declara `ser_json_decimal_to_float` sin que exista un serializador que lo implemente. Afecta a `pagos` también |

---

## 9. Desviaciones y decisiones

| # | Decisión / desviación | Motivo |
|---|---|---|
| **D-DOM-01-01** | El dinero se declara `Decimal` en los wrappers y sale como **cadena** en el JSON (mismo criterio que el módulo `pagos` ya completado) | Cambiarlo exigiría editar `core/responses.py`/`core/types.py` (A0) y desalinearía este módulo de `pagos`. Los tests comprueban el **valor** (`Decimal(str(x))`), no la forma, para que la resolución de A0-09 no rompa el contrato |
| **D-DOM-01-02** | La ruta del ALTA es `POST /inscripciones` (`RT-IN-14`, **provisional**) y no existe en el ledger de GOV-01 | El ledger sólo preveía `RT-CM-01` (`/inscripciones/{id}/compras/cupos`), que es la **ampliación** de DOM-02. El alta inicial no tenía fila: se pide su ratificación (A0-05) en vez de inventar una ruta sin registrar |
| **D-DOM-01-03** | La cantidad de cupos la decide el **servidor** (`paquete.cupos_incluidos`); el payload HTTP no admite cantidad | `RN-C02`: el cliente no impone un importe ni una cantidad comercial. La ampliación con cantidad es de DOM-02 (`RT-CM-01` → `ComprarCuposIn`) |
| **D-DOM-01-04** | La inscripción y su compra son hechos **separados** (la inscripción se crea en una transacción atómica; la compra en la de `commerce`) | Recuperabilidad: si la compra falla, la inscripción queda viva y el reintento la reutiliza y crea (o recupera) su compra. Perder una inscripción ya creada sería peor que reintentarla |
| **D-DOM-01-05** | El precio vigente se resuelve por `vigente_desde <= hoy` y (`vigente_hasta` nula o `>= hoy`), tomando el más reciente | El paquete puede tener una HISTORIA de precios; el vigente es un hecho del catálogo |
| **D-DOM-01-06** | Un equipo por disciplina y por inscripción (`UNIQUE (inscripcion, disciplina)`) | El padrón no lo elige el cliente y una inscripción no lleva dos equipos de la misma disciplina. La elegibilidad de participantes es de DOM-02 |
| **D-DOM-01-07** | `Inscripcion` tiene `HistoricalRecords` | La inscripción es un hecho de negocio que DOM-02 va a mutar (asignaciones); el rastro de cambios se conserva desde el principio |
| **D-DOM-01-08** | El módulo se llama `salesianos_fest` (raíz física) y su app label es `salesianos_fest`; el ledger nombra el dominio `inscripciones` | El ledger de GOV-01 nombra el DOMINIO (`inscripciones`); la raíz física la elige DOM-01 (DOM-02 lo consume). La equivalencia se pide confirmar en A0-05/A0-06 |
| **D-DOM-01-09** | `eventos` y `usuarios` se cruzan por PUERTO; `commerce` se consume DIRECTO | `commerce` es la infraestructura comercial compartida con interfaz congelada (`D-FND-04-06`); `eventos`/`usuarios` son dominios con dueño y sus internos no se importan desde aquí |
| **D-DOM-01-10** | El flujo reintenta la lectura de la inscripción ganadora hasta 5 veces (50 ms) tras un `IntegrityError` | La perdedora de una carrera puede no ver todavía la fila ganadora: sin el reintento, el `IntegrityError` se propagaría como un 500 en vez de reutilizarse |
| **D-DOM-01-11** | No se crea `tests/factories.py` | Los payloads de este paquete son DTOs de dominio (no dicts de API): los tests los construyen con los DTOs reales, que es la forma exacta que consume el flujo |

---

## 10. Slices de revisión (presupuesto ≈ 400 líneas)

El alcance del paquete (catálogo + inscripción + compra + superficie HTTP + 45 tests) **supera**
el presupuesto de revisión de 400 líneas por cambio. Se divide en **8 slices autónomos**, cada uno
con su frontera, su verificación y su orden de reversión. Ningún slice mezcla dominios ajenos.

| Slice | Contenido | Líneas | Verificación propia |
|---|---|---:|---|
| **WU-1** | Catálogo — modelos (`domain/models/catalogo.py`), vocabulario (`domain/constants.py`), re-exports, `apps.py` | 497 | `manage.py makemigrations --check --dry-run` (el modelo no deriva de la migración) |
| **WU-2** | Catálogo — excepciones de dominio, selector, servicio core, DTOs, results, flujo, orquestador | 684 | `test_catalogo_paquetes.py` + `test_catalogo_disciplinas_inscripcion.py` (10 tests) |
| **WU-3** | Catálogo — superficie HTTP (schemas, presenter, controller) + `__init__` de presentación | 435 | V1/V2 (los 10 tests de catálogo) |
| **WU-4** | Inscripción — modelo, selector, servicio core, results y DTOs internos | 421 | `test_inscripcion_inicial.py` (3 tests) |
| **WU-5** | Inscripción — flujo de alta y compra congelada, puertos y adaptadores de infraestructura | 544 | `test_inscripcion_inicial.py` + `test_inscripcion_alcance_invalido.py` (10 tests) |
| **WU-6** | Inscripción — orquestador, superficie HTTP, DI y admin | 711 | `test_inscripcion_permiso.py` + `test_inscripcion_controller.py` (e2e) |
| **WU-7** | Tests — fixtures, overlay, URLconf y los seis ficheros de casos de integración | 1 254 | V1/V2 (38 tests de integración) |
| **WU-8** | Tests e2e + migración inicial generada | 1 002 | V7…V12 (apply/rollback/replay) + V2 |

**Líneas totales:** ≈ 5 644 (de las cuales 706 son la migración generada y ≈ 1 590 son tests).
**Orden de reversión:** WU-8 → WU-7 → WU-6 → WU-5 → WU-4 → WU-3 → WU-2 → WU-1
(el flujo y la superficie HTTP se quitan antes que los modelos).

---

## 11. Rollback

1. `manage.py migrate salesianos_fest zero --settings=…` → revierte `0001_initial` (V10 = 0).
2. Borrar `Aplicacion/backend/modules/salesianos_fest/` (todo el contenido del paquete).
3. Restaurar `Aplicacion/task/salesianos-fest-rebuild/STATE.md` a su contenido previo.
4. En Engram: restaurar `sdd/salesianos-fest-rebuild/apply-progress` y `/state` a sus
   observaciones previas y borrar el topic packet-específico de DOM-01.
5. **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (no se creó ningún commit).
   **No revertir ni resetear** ese commit.
6. **El historial comercial y de pago se conserva:** el rollback de este paquete no borra
   compras, órdenes ni transacciones, porque `commerce`/`pagos` son de otro dueño.

---

## 12. Concurrencia y trabajo preservado

| Raíz | Dueño | Acción de este paquete |
|---|---|---|
| `Aplicacion/backend/modules/marketplace/**` | **DOM-04 (A5)** — en curso | **NO tocada.** No se leyó para escribir, no se editó, no se fusionó |
| `Aplicacion/frontend/**` | FND-06 / UI-01A (A0 + A7) | **NO tocada** |
| `Aplicacion/backend/modules/{commerce,pagos,eventos,usuarios}/**` | A2 / A1 / A0 | **NO editados.** Sus suites se re-ejecutaron verdes (V13…V16) |
| `Aplicacion/backend/config/**`, `Aplicacion/backend/core/**` | A0 | **NO editados.** Se registran como peticiones A0-01/02/03/06/09 |
| `contract/**`, `Aplicacion/plan/**`, `Aplicacion/documentacion/**` | Normativo | **NO editados** (R1 vacío) |
| `backend/**`, `frontend/**`, `worker/**`, `proxy/**`, `.opencode/**` | Raíces congeladas | **NO editados** (R2 vacío) |

La fila `DOM-04` del tablero **no se editó** (DOM-04 es su dueño) y la fila `FND-06` tampoco
(A0/A7 es su dueño).

---

## 13. Listo para el siguiente paquete (DOM-02)

**DOM-02 — `wave-02-domain-backend/DOM-02-inscription-pool-expansion.md`** (`T-022`, `T-023`):

| Necesita de DOM-01 | Estado |
|---|---|
| La app y su DI registrados | **Pendiente de A0-01** (mientras tanto, el overlay local `modules.salesianos_fest.tests.settings_overlay` lo replica) |
| `Inscripcion` con `cupos_pagados` / `cupos_asignados` / `cupos_disponibles` | **Listo** (los campos y el `CHECK` ya existen) |
| La restricción `UNIQUE (inscripcion, disciplina)` | **Lista** (el pool y la asignación construyen sobre ella) |
| La compra de origen `INSCRIPCION` | **Lista** (`Compra.origen = INSCRIPCION`, la referencia estable y el snapshot) |
| El activador `IActivadorDominioCompra` de origen `INSCRIPCION` | **A implementar en DOM-02** (el puerto, la clave y el doble de prueba ya existen de FND-05) |
| La expansión `RT-CM-01` (`POST /inscripciones/{id}/compras/cupos`, `ComprarCuposIn`) | **A implementar en DOM-02** (este paquete NO la implementa: es la compra de ampliación, no la inicial) |
| La elegibilidad y el saldo del pool | **A implementar en DOM-02** |
| La regla de beneficios por tipo (`PD-09`) | **Sigue ABIERTA** — este paquete declara el beneficio, no lo reparte |

**En el ledger, `RT-CM-01` ya está CONGELADO por GOV-01** (`CompraCuposPresenter` →
`CompraCreadaOut` ← `ComprarCuposIn`; `COMPRA_NO_AUTORIZADA` 403 · `PAQUETE_NO_VIGENTE` 409 ·
`CUPO_INVALIDO` 422; permiso `TITULARIDAD_RESPONSABLE`). `CUPO_INVALIDO` **no** está en el
catálogo público de A0: DOM-02 debe pedirlo junto con el resto de sus códigos.

---

## 14. Criterios de aceptación del paquete

- [x] **El catálogo es real, por edición y sin precio de reserva** — V2 (45 tests), V3
      (`No changes detected`), V12 (esquema SQLite con las 7 restricciones).
- [x] **La compra inicial es recuperable** — `test_el_reintento_devuelve_la_misma_inscripcion`,
      `test_el_reintento_no_crea_una_segunda_compra`, `test_el_reintento_no_duplica_los_equipos`.
- [x] **No habilita cupos no pagados** — `test_la_inscripcion_nace_con_cero_cupos_pagados`,
      `test_el_saldo_disponible_es_cero_mientras_el_pago_pendiente`, e2e
      `test_el_alta_devuelve_la_inscripcion_y_su_compra_pendiente` (`cupos_pagados == 0`).
- [x] **No duplica la inscripción** — `test_el_reintento_devuelve_la_misma_inscripcion`,
      `test_la_base_de_datos_rechaza_la_inscripcion_duplicada`,
      `test_la_carrera_perdida_reutiliza_la_inscripcion_ganadora`,
      `test_dos_altas_simultaneas_no_duplican`.
- [x] **Los presenters poseen las causas operativas y los controllers no tienen reglas** —
      §5 (revisión del código de los dos controllers).
- [x] **Comandos del paquete ejecutados y registrados con su código de salida** — §6.
- [x] **Ningún archivo prohibido editado** — R1/R2 vacíos, §2.3.
- [x] **Sin commit y sin `git stash`** — R3/R4.
