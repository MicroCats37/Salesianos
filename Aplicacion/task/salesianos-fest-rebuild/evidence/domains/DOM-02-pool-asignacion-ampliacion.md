# DOM-02 — Pool de cupos, asignación y ampliación

**Packet:** `DOM-02` · **Change:** `salesianos-fest-rebuild` · **Owner:** A3
**Tareas de origen:** `T-022` (pool y asignación · `RN-I03`-`RN-I05` · `FL-05`) y `T-023` (ampliación y beneficios · `RN-I06` · `FL-04`) — 2 de los 54 identificadores definidos por el plan (acumulado con GOV-00/01/02, FND-01…FND-05 y DOM-01: **19 de 54**).
**Raíz física del módulo:** `Aplicacion/backend/modules/salesianos_fest/`
**Rama:** `master` · **Punto de rollback:** `f3df5401c56b41c340f257e67d5a306904a9e670` (sin cambios — **ningún commit creado**, `git stash` nunca invocado)
**Artefacto Engram packet-específico:** `sdd/salesianos-fest-rebuild/dom-02-apply-progress`
**Modo:** Standard (no hay `strict_tdd` activo en este cambio)

---

## 1. Lo entregado

El **pool de cupos** de una inscripción: la aritmética pagados/asignados/disponibles, la asignación atómica de cupos, el movimiento y la retirada de participantes, la **compra de cupos extra** y el **activador de derechos** del origen `INSCRIPCION`.

- **Pool (`Participacion`)** — el vínculo entre un cupo pagado y una persona dentro de una inscripción. Es la `AsignacionCupo` del modelo de referencia con el nombre público que fija el contrato HTTP congelado (`participantes` / `participacion_id`). `edicion` y `disciplina` son campos REDUNDANTES para que la restricción de solapamiento no dependa de un `JOIN`.
- **Capacidad (`ActivacionCapacidad`)** — el acta de cada activación. Su `clave` es **ÚNICA**: es la autoridad del «exactamente una vez» de la activación de derechos.
- **Beneficios (`BeneficioConcedido`)** — la concesión efectiva de un beneficio de paquete, con `UNIQUE (inscripcion, beneficio)`: la garantía de que un `FIJO_INICIAL` no se conceda dos veces.
- **Servicios** — `CapacidadCoreService` (los contadores, con sentencias ATÓMICAS CONDICIONALES), `PoolCoreService`, `BeneficioCoreService`, `ActivadorInscripcion` (implementa el puerto `IActivadorDominioCompra` de FND-05), `PoolFlujo`, `CompraCuposFlujo` y sus dos orquestadores.
- **HTTP** — cuatro rutas CONGELADAS: `RT-IN-03` (pool), `RT-IN-05` (agregar participante), `RT-IN-06` (retirar participante) y `RT-CM-01` (comprar cupos extra), con los presenters `PoolPresenter` y `CompraCuposPresenter` y los wrappers `PoolOut` y `CompraCreadaOut`.
- **57 tests de comportamiento nuevos** (44 de integración + 13 e2e), todos verdes.

### 1.1 La aritmética del pool (`RN-I03`)

| Magnitud | Dónde vive | Quién la calcula |
|---|---|---|
| `cupos_pagados` | `Inscripcion.cupos_pagados` | **sólo** la ACTIVACIÓN de derechos (DOM-02, vía FND-05) |
| `cupos_asignados` | `Inscripcion.cupos_asignados` | el servicio de capacidad, con `UPDATE` condicional |
| `cupos_disponibles` | **derivada** | `max(cupos_pagados - cupos_asignados, 0)` — el servidor; el cliente nunca resta (`SH-05` §1.3) |

La restricción `fest_inscripcion_asignados_no_superan_pagados` (`CHECK (cupos_asignados <= cupos_pagados)`) es la segunda línea de defensa: aunque una escritura se colase, la base de datos rechaza el saldo negativo.

### 1.2 El bloqueo (`QA-I05`)

El contador **no** se mueve con lectura-modificación-escritura, sino con un `UPDATE` cuya condición viaja DENTRO de la sentencia:

| Operación | Sentencia | Garantía |
|---|---|---|
| reservar | `UPDATE … WHERE cupos_asignados < cupos_pagados` → `+1` | dos asignaciones simultáneas no pueden sobre-suscribir: la segunda no actualiza ninguna fila |
| liberar | `UPDATE … WHERE cupos_asignados > 0` → `-1` | el contador nunca baja de cero |
| habilitar pagados | `UPDATE … SET cupos_pagados = cupos_pagados + n` | la capacidad pagada sólo crece por activación (`RN-I02`) |

**Por qué no `select_for_update`.** `select_for_update` lanza `NotSupportedError` en SQLite, y el motor de pruebas del objetivo es SQLite. La alternativa —el `UPDATE` condicional— es atómica en SQLite **y** en PostgreSQL, y además no necesita un servicio de bloqueos por fila. Es la misma garantía con menos acoplamiento al motor.

**Lo que NO está bloqueado (limitación declarada).** El **tope por equipo** (`Disciplina.maximo_por_equipo`) se comprueba dentro de la transacción, pero no está serializado: dos altas simultáneas al mismo equipo podrían superar el tope. Las invariantes **duras** (capacidad, participación duplicada, solapamiento) sí están garantizadas por la base de datos. El tope es un límite blando cuyo cumplimiento bajo concurrencia exacta queda registrado como `D-DOM-02-08`.

### 1.3 Agregar, mover y retirar (`FL-05`)

| Operación | Ruta | Qué hace |
|---|---|---|
| agregar | `POST /inscripciones/{id}/participantes` | agrega una persona al pool y le asigna **un** cupo pagado |
| **mover** | la misma ruta, con `reemplaza_participacion_id` | la persona nueva **toma el cupo** de la retirada, en la MISMA transacción: el saldo disponible nunca baja de cero por un movimiento |
| retirar | `DELETE /inscripciones/{id}/participantes/{participacion_id}` | pasa la participación a `RETIRADA` y **libera su cupo** |

El movimiento se implementa como un caso del "agregar" (campo opcional) para **no inventar una ruta fuera del ledger congelado**.

**Retirar NO es devolver dinero** (`RN-I04`, `DEC-06`, `QA-I04`): no se toca la compra, ni la orden de pago, ni el historial comercial. La participación se conserva (`RETIRADA` + `retirada_en` + `motivo`): la historia de la plantilla no se borra.

### 1.4 La elegibilidad (`RN-I05`) — SIEMPRE en backend

| Regla | Comprobación | Rechazo |
|---|---|---|
| edición | el equipo pertenece a la inscripción | `EQUIPO_NO_ENCONTRADO` (404) |
| disciplina activa | `Disciplina.estado = ACTIVA` | `PARTICIPANTE_NO_ELEGIBLE` (422) |
| disciplina permitida | `disciplina_permitida(paquete, disciplina)` — exige que sea de la EDICIÓN del paquete | `DISCIPLINA_NO_PERMITIDA` (422) |
| compatibilidad | la modalidad admite el género declarado | `PARTICIPANTE_NO_ELEGIBLE` (422) |
| tope | `maximo_por_equipo` | `EQUIPO_COMPLETO` (409) |
| duplicado | la persona no participa ya en esta inscripción | `PARTICIPANTE_DUPLICADO` (422) |
| solapamiento | la persona no participa en la misma disciplina de la edición | `PARTICIPANTE_NO_ELEGIBLE` (422) |
| capacidad | hay cupo disponible | `SIN_CUPOS_DISPONIBLES` (409) |
| titularidad | el actor es el responsable | `INSCRIPCION_NO_AUTORIZADA` (403) |

**Sobre el género sin declarar:** una disciplina `MIXTO` admite a cualquiera; una disciplina `FEMENINO`/`MASCULINO` exige un género **declarado**. Sin género conocido no se puede afirmar la compatibilidad, así que no se concede el beneficio de la duda. Es una decisión explícita (`D-DOM-02-05`), no un valor por defecto silencioso.

### 1.5 La ampliación (`FL-04`)

- Compra **separada** del alta, con su propia referencia de intención `INSCRIPCION:{id}:EXPANSION:{cantidad}` y su propia orden de pago.
- El precio lo resuelve el servidor contra el catálogo vigente; el payload **no admite importe** (`RN-C02`).
- La cantidad está acotada por el dominio: `MIN_CUPOS_POR_AMPLIACION = 1`, `MAX_CUPOS_POR_AMPLIACION = 50` → `CUPO_INVALIDO` (422), el código CONGELADO por el ledger para `RT-CM-01`.
- Un reintento con la misma cantidad devuelve la **MISMA** compra pendiente (`FR-04` I-4); una compra ya pagada no bloquea una nueva.
- La compra queda `PENDIENTE` y **no habilita cupos**: eso ocurre al activarse el pago (`RN-I02`).

### 1.6 La activación de derechos (FND-05)

`ActivadorInscripcion` implementa el puerto `IActivadorDominioCompra` y se registra en el coordinador de `commerce` en `apps.py::ready()` (el registro es un objeto único del proceso, `D-FND-05-04`).

1. Resuelve la inscripción por la **referencia de intención**, que es de este módulo (`domain/referencia.py`): `INSCRIPCION:{id}:INICIAL` | `INSCRIPCION:{id}:EXPANSION:{n}`.
2. Calcula los cupos a partir del **snapshot de líneas** que congeló `commerce` (la cantidad ya resuelta por el servidor; no vuelve a consultar el catálogo).
3. Registra la `ActivacionCapacidad` con la `clave` estable de FND-05 — **única en la base de datos**: un reintento NO vuelve a sumar cupos (`QA-I02`).
4. Suma los cupos a la capacidad pagada.
5. Concede los beneficios `FIJO_INICIAL` — **sólo en el alta**: una ampliación NO los duplica (`RN-I06`, `QA-I03`).

El activador abre su propia transacción porque lo invoca un **coordinador externo** (`commerce`), no un flujo de este módulo (`D-DOM-02-06`).

### 1.7 Los beneficios: qué está cerrado y qué NO (`RN-I06`, `PD-09`)

| Tipo | Regla | Estado en este paquete |
|---|---|---|
| `FIJO_INICIAL` | se concede UNA vez por inscripción, en la activación del ALTA | **CERRADA** — la implementa `BeneficioCoreService`; la no duplicación la garantiza `UNIQUE (inscripcion, beneficio)` |
| `POR_CUPO` | se concede por cupo comprado | **ABIERTA (`PD-09`)** — este módulo **NO concede** y **NO inventa** la regla |

Conceder un beneficio `POR_CUPO` sin regla cerrada sería **inventar un derecho con dinero detrás**: ningún contrato congela cómo se reparte (¿uno por cupo? ¿con mínimo? ¿con tope?). El módulo DECLARA el beneficio y deja la concesión explícitamente PENDIENTE. El modelo `BeneficioConcedido` acepta la acumulación de `cantidad` para cuando la regla se cierre.

---

## 2. Interfaces consumidas (congeladas)

| Interface | Dueño | Cómo | Por qué |
|---|---|---|---|
| `commerce.CompraFlujo` + `CompraCreateData` / `LineaCompraSnapshot` | `commerce` (A2) | **DIRECTO** | `commerce` es la infraestructura comercial compartida y su interfaz está congelada (`RN-C01`, `D-FND-04-06`) |
| `commerce.IActivadorDominioCompra` + `ContextoActivacionCompra` | `commerce` (FND-05) | **DIRECTO** (implementación del puerto) | el coordinador conoce interfaces, no reglas de dominio |
| `eventos.EdicionScopeService` | `eventos` (A1) | **PUERTO** `IAlcanceEdicionService` | `eventos` es el dueño del alcance de edición |
| `usuarios.TitularidadService` | `usuarios` (A1) | **PUERTO** `ITitularidadService` | ser `Administrador` no sustituye la titularidad (`FR-03` §2.1) |
| `usuarios.PersonaSelector` | `usuarios` (A1) | **PUERTO** `IResolucionPersonaService` (nuevo, DOM-02) | `FL-05` paso 2: agregar persona existente **o** resolverla por documento. El módulo CONSULTA el padrón; no crea identidades |
| `eventos.ModuloLogico.INSCRIPCIONES` | `eventos` | constante | comprobación de módulo habilitado |

---

## 3. La superficie HTTP

| Ruta | Método | Presenter | Wrapper | Códigos de error |
|---|---|---|---|---|
| `RT-IN-03` `/api/inscripciones/{id}/pool` | GET | `PoolPresenter` | `PoolOut` | 401 · 403 `INSCRIPCION_NO_AUTORIZADA` · 404 `INSCRIPCION_NO_ENCONTRADA` |
| `RT-IN-05` `/api/inscripciones/{id}/participantes` | POST | `ParticipanteAsignarPresenter` → `PoolPresenter` | `PoolOut` | 401 · 403 · 404 · 409 `SIN_CUPOS_DISPONIBLES` · 409 `EQUIPO_COMPLETO` · 422 `PARTICIPANTE_NO_ELEGIBLE` · 422 `PARTICIPANTE_DUPLICADO` · 422 `DISCIPLINA_NO_PERMITIDA` · 422 `PERSONA_NO_ENCONTRADA` · 422 `VALIDATION_ERROR` |
| `RT-IN-06` `/api/inscripciones/{id}/participantes/{participacion_id}` | DELETE | `ParticipanteRetirarPresenter` → `PoolPresenter` | `PoolOut` | 401 · 403 · 404 `PARTICIPANTE_NO_ENCONTRADO` |
| `RT-CM-01` `/api/inscripciones/{id}/compras/cupos` | POST | `CompraCuposPresenter` | `CompraCreadaOut` | 401 · 403 `COMPRA_NO_AUTORIZADA` · 404 · 409 `PAQUETE_NO_VIGENTE` · 422 `CUPO_INVALIDO` |

**Equivalencia de nombres.** El registro congelado `SH-05` nombra tres presenters distintos (`PoolPresenter`, `ParticipanteAsignarPresenter`, `ParticipanteRetirarPresenter`) que publican el MISMO wrapper `PoolOut`. Este módulo implementa `PoolPresenter` y publica `PoolOut` en las tres rutas; la equivalencia se pide su ratificación a A0 (`A0-DOM02-05`).

**Versión del contrato:** `SCHEMA_VERSION` de `salesianos_fest` sube de `1.0.0` a **`1.1.0`** (MINOR: cuatro rutas y wrappers nuevos, ninguna forma de respuesta existente modificada ni eliminada).

---

## 4. Ficheros cambiados (todos dentro de las raíces permitidas)

### Creados (17)

| Fichero | Qué hace |
|---|---|
| `domain/models/participacion.py` | `Participacion` — el pool, con las dos restricciones únicas parciales |
| `domain/models/capacidad.py` | `ActivacionCapacidad` (clave única) y `BeneficioConcedido` (único por inscripción) |
| `domain/referencia.py` | el formato CERRADO de la referencia de intención y su parser |
| `domain/selectors/pool_selector.py` | `PoolSelector` — lecturas del pool y de las activaciones |
| `domain/services/core/capacidad_core_service.py` | los contadores de capacidad (`UPDATE` condicional) |
| `domain/services/core/pool_core_service.py` | alta y baja de participaciones |
| `domain/services/core/beneficio_core_service.py` | la concesión de `FIJO_INICIAL` |
| `domain/services/core/activador_inscripcion.py` | el activador del puerto de FND-05 |
| `domain/services/flujos/pool_flujo.py` | agregar / mover / retirar + la proyección del pool |
| `domain/services/flujos/compra_cupos_flujo.py` | la compra de cupos extra |
| `domain/services/orchestrators/pool_orchestrator.py` | fachada del pool con la comprobación de titularidad |
| `domain/services/orchestrators/compra_cupos_orchestrator.py` | fachada de la ampliación |
| `domain/results/pool_result.py` | `PoolResult`, `ParticipacionResult`, `ImpedimentoResult`, `CompraCuposResult` |
| `domain/schemas/pool_schemas.py` | `ParticipanteAsignarData`, `CompraCuposData` |
| `presentation/schemas/pool_schemas.py` | `PoolOut`, `ParticipanteAsignarIn` y sus bloques |
| `presentation/schemas/compra_cupos_schemas.py` | `ComprarCuposIn`, `CompraCreadaOut` |
| `presentation/presenters/pool_presenter.py` | el presentador puro del pool |
| `presentation/presenters/compra_cupos_presenter.py` | el presentador puro de la ampliación |
| `migrations/0002_pool_capacidad.py` | la migración generada |
| `tests/integration/test_cupo_disponibles.py` | 6 tests — la aritmética del pool |
| `tests/integration/test_asignacion_participante.py` | 18 tests — agregar/mover/retirar, elegibilidad, duplicados, titularidad, carrera |
| `tests/integration/test_ampliacion_cupos.py` | 11 tests — la compra de cupos extra |
| `tests/integration/test_cupo_activacion.py` | 10 tests — la activación de derechos y los beneficios |
| `tests/e2e/test_cupo_controller.py` | 13 tests — las cuatro rutas HTTP |

### Modificados (13)

`domain/constants.py` · `domain/exceptions.py` · `domain/ports/__init__.py` · `domain/models/__init__.py` · `domain/selectors/inscripcion_selector.py` (un selector nuevo) · `domain/results/__init__.py` · `domain/schemas/__init__.py` · `models.py` · `apps.py` (el registro del activador) · `admin.py` (tres modelos nuevos) · `di.py` (los bindings nuevos) · `presentation/controllers/inscripcion_controller.py` (las cuatro rutas) · `presentation/presenters/__init__.py` · `presentation/schemas/__init__.py` (la versión) · `tests/conftest.py` · `tests/fixtures/fest_fixtures.py` · `infrastructure/services/alcance_y_titularidad.py` (el adaptador nuevo) · `infrastructure/services/__init__.py` · `domain/services/flujos/inscripcion_flujo.py` (la referencia usa ahora el módulo compartido de formato).

**Total:** ≈ **5 367 líneas** (316 de migración generada, ≈ 1 392 de tests).

**NO editados:** `commerce`, `pagos`, `eventos`, `usuarios`, `marketplace` (DOM-05), `core/**`, `config/**`, `contract/**`, `Aplicacion/plan/**`, `Aplicacion/documentacion/**`, `Aplicacion/frontend/**`, las raíces congeladas `backend/**`, `frontend/**`, `worker/**`, `proxy/**`, secretos y bases de datos.

---

## 5. Comandos / códigos de salida

Workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe` (Python 3.10.0 · Django 5.2.11 · pytest-django 4.9.0 · ninja 1.5.3 · ninja-extra 0.31.0 · injector 0.24.0). `pytest.ini` → `DJANGO_SETTINGS_MODULE = config.settings.test` (SQLite en memoria, `--nomigrations`).

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V1 | `python -m pytest modules/salesianos_fest/tests -q -k "cupo or asignacion or ampliacion"` | **0** | **59 passed** · 43 deselected — el filtro del paquete selecciona el 100 % de sus tests |
| V2 | `python -m pytest modules/salesianos_fest/tests -q` | **0** | **102 passed** (45 de DOM-01 + 57 de DOM-02) — el baseline de DOM-01 intacto |
| V3 | `python manage.py makemigrations --check --dry-run --settings=config.settings.test` | **1** | **`marketplace`** (DOM-05, concurrente) tiene migraciones pendientes: `Pedido` + `PedidoDetalle`. **Cero** pendientes de `salesianos_fest` |
| V3b | `python manage.py makemigrations salesianos_fest --check --dry-run --settings=config.settings.test` | **0** | `No changes detected in app 'salesianos_fest'` — la migración coincide con los modelos |
| V4 | `python manage.py check --settings=config.settings.test` | **0** | `System check identified no issues (0 silenced)` |
| V5 | `python manage.py check` (settings por defecto = producción) | **1** | `DB_NAME` — **baseline ambiental conocido**, idéntico a FND-01…FND-05 y DOM-01 |
| V6 | `python manage.py makemigrations --check --dry-run` (por defecto) | **1** | mismo baseline `DB_NAME` |
| V7 | `manage.py migrate --settings=…overlay` (SQLite en fichero fuera del repo) | **0** | `Applying salesianos_fest.0001_initial... OK` · `0002_pool_capacidad... OK` |
| V8 | `manage.py showmigrations salesianos_fest` | **0** | `[X] 0001_initial` · `[X] 0002_pool_capacidad` |
| V9 | `manage.py migrate salesianos_fest zero` | **0** | `Unapplying salesianos_fest.0002_pool_capacidad... OK` → `0001_initial... OK` — reversible |
| V10 | `manage.py migrate` (replay) | **0** | `Applying salesianos_fest.0001_initial... OK` → `0002_pool_capacidad... OK` — reproducible |
| V11 | inspección del esquema SQLite real | **0** | 2 índices UNIQUE parciales en `fest_participacion` · `clave … UNIQUE` en `fest_activacion_capacidad` · `UNIQUE (inscripcion_id, beneficio_id)` en `fest_beneficio_concedido` · `CHECK (cupos_asignados <= cupos_pagados)` en `fest_inscripcion` |
| V12 | `python -m pytest core/tests -q` | **1** | **156 passed · 2 failed** — las 2 son de A0 y están solicitadas (§7) |
| V13 | `python -m pytest modules/eventos/tests -q` | **0** | **63 passed** — baseline FND-02 intacto |
| V14 | `python -m pytest modules/usuarios/tests -q` | **0** | **35 passed** — baseline FND-03 intacto |
| V15 | `python -m pytest modules/commerce/tests modules/pagos/tests -q` | **0** | **96 passed** — baselines FND-04/FND-05 intactos |
| V16 | `python -m pytest modules/marketplace/tests -q` | **0** | **35 passed** — baseline DOM-04 intacto (DOM-05 en curso) |
| V17 | `python -m pytest -q` (raíz completa del objetivo) | **1** | **487 passed · 2 failed** — las 2 son de A0 (§7) |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | vacío |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | vacío — las raíces congeladas intactas |
| R3 | `git diff --name-only -- Aplicacion/backend/modules/{commerce,pagos,eventos,usuarios,marketplace}` | **0** | vacío — los módulos de otros dueños intactos |
| R4 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — sin commit |
| R5 | `git stash` | — | **nunca invocado** (`git stash list` vacío) |
| R6 | barrido de residuos bajo `Aplicacion/backend` | **0** | ningún `*.sqlite3`, ningún `db.sqlite3`, ningún `media/` — la base del ensayo vivió en `%TEMP%\opencode` y se borró |

**Estabilidad:** la suite completa del objetivo se ejecutó 2 veces con el mismo resultado (487 passed · 2 failed de A0).

---

## 6. Fallos conocidos y regresiones

### 6.1 Fallos de A0 (NO son defectos de este paquete) — 2

| Test | Causa | Petición |
|---|---|---|
| `core/tests/integration/test_registration_extension.py::test_las_rutas_de_dominio_son_exactamente_las_congeladas` | el inventario de rutas congeladas no incluye las 4 rutas nuevas | `A0-DOM02-01` |
| `core/tests/integration/test_contract_versions.py::test_no_hay_drift_entre_el_registro_y_el_modulo[salesianos_fest]` | el registro global sigue en `1.0.0` y el módulo declara `1.1.0` | `A0-DOM02-02` |

Los dos ficheros están en `core/tests/` — **raíz compartida de A0, prohibida para este paquete** — y no se editaron. El mensaje del primer fallo es exacto:

```
E   '/api/inscripciones/{inscripcion_id}/compras/cupos'
E   '/api/inscripciones/{inscripcion_id}/participantes'
E   '/api/inscripciones/{inscripcion_id}/pool'
E   '/api/inscripciones/{inscripcion_id}/participantes/{participacion_id}'
```

### 6.2 Baseline ambiental (heredado, NO es regresión)

`manage.py check` y `manage.py makemigrations --check --dry-run` con los settings por defecto siguen fallando con `DB_NAME` (exit **1**): `manage.py` usa `config.settings.production`, que exige `DB_NAME`/`DB_USER`/`DB_PASSWORD`. Idéntico a FND-01…FND-05 y DOM-01.

### 6.3 Migración pendiente de DOM-05 (concurrente, NO es regresión)

`makemigrations --check --dry-run` falla porque **`modules/marketplace`** tiene modelos sin migración (`Pedido`, `PedidoDetalle`). Esa migración es de **DOM-05**, que es su dueño: este paquete **no la generó**. El estado de `salesianos_fest` es limpio (`No changes detected in app 'salesianos_fest'`).

### 6.4 Regresiones introducidas: **0**

---

## 7. Peticiones a A0 (registradas, NO aplicadas)

| # | Petición | Dónde |
|---|---|---|
| **A0-DOM02-01** | añadir las 4 rutas nuevas al inventario congelado `RUTAS_DE_DOMINIO_CONGELADAS` (`core/tests/integration/test_registration_extension.py`): `/api/inscripciones/{inscripcion_id}/pool`, `…/participantes`, `…/participantes/{participacion_id}`, `…/compras/cupos` | `core/tests/**` |
| **A0-DOM02-02** | actualizar `core/contract_versions.py` → `SCHEMA_VERSIONS["salesianos_fest"] = "1.1.0"`, y actualizar las dos aserciones de `core/tests/integration/test_contract_versions.py` que fijan `1.0.0` (`test_los_modulos_congelados_declaran_1_0_0` y `test_el_registro_incluye_los_fundamentos_completados`) | `core/**` |
| **A0-DOM02-03** | catálogo público: 8 códigos nuevos con su prosa fija — `CUPO_INVALIDO` (422, **congelado** por el ledger para `RT-CM-01`), `SIN_CUPOS_DISPONIBLES` (409), `PARTICIPANTE_NO_ELEGIBLE` (422), `PARTICIPANTE_DUPLICADO` (422), `EQUIPO_COMPLETO` (409), `PARTICIPANTE_NO_ENCONTRADO` (404), `EQUIPO_NO_ENCONTRADO` (404), `PERSONA_NO_ENCONTRADA` (404) | `core/exceptions.py` |
| **A0-DOM02-04** | ratificar en el ledger `FR-07` §3.3 la ruta `RT-CM-01` con sus códigos (`COMPRA_NO_AUTORIZADA` 403 · `PAQUETE_NO_VIGENTE` 409 · `CUPO_INVALIDO` 422) y el nombre del presenter `CompraCuposPresenter` | evidencia de contrato de GOV-01 |
| **A0-DOM02-05** | ratificar la equivalencia de presenters de `RT-IN-03`/`RT-IN-05`/`RT-IN-06`: el registro nombra `PoolPresenter`, `ParticipanteAsignarPresenter` y `ParticipanteRetirarPresenter`; el módulo implementa `PoolPresenter` y publica `PoolOut` en las tres | `evidence/routes/SH-05…` + ledger |
| **A0-DOM02-06** | registrar las rutas de `RT-IN-03`/`RT-IN-05`/`RT-IN-06` en el ledger de presenters (`SH-05`) | `evidence/routes/**` |
| **A0-DOM02-07** | `*.sqlite3` en el `.gitignore` del objetivo (petición heredada de FND-01/02/04/05 y DOM-01) | `.gitignore` |
| **A0-DOM02-08** | sincronizar la matriz física de tareas `00-matriz-tareas.md`: filas `T-022` y `T-023` → `completed` (siguen en `pending`; la matriz está fuera de las raíces de edición de todos los paquetes — mismo precedente que DOM-01/DOM-04) | `Aplicacion/task/**` |
| **A0-DOM02-09** | decidir si `RegistroActivadoresCompra.limpiar()` debe **RESTAURAR** las registraciones de los dominios: el fixture `registro_activadores` de `commerce` vacía un registro **único del proceso** y se lleva el activador de `salesianos_fest` para el resto de la sesión de pruebas | `modules/commerce/tests/**` |
| **A0-DOM02-10** | confirmar con producto el número de `MAX_CUPOS_POR_AMPLIACION` (declarado en **50**, `D-DOM-02-07`) y el del tope por equipo (`Disciplina.maximo_por_equipo`, ya campo del catálogo) | producto + A0 |

---

## 8. Desviaciones

| # | Desviación | Por qué |
|---|---|---|
| `D-DOM-02-01` | La participación se llama `Participacion`, no `AsignacionCupo`. | El CONTRATO HTTP congelado nombra el recurso `participantes` / `participacion_id` (`RT-IN-05`, `RT-IN-06`). El concepto es el mismo (el vínculo entre un cupo pagado y una persona) y el plan lo autoriza explícitamente: «reutilizar conceptos no obliga a copiar sus columnas o constraints actuales» (`funcional/03` §7). |
| `D-DOM-02-02` | El cupo NO es una fila con identidad: es una unidad del contador `cupos_asignados`. | `RN-I03` define el saldo como `cupos_pagados_vigentes - asignaciones_activas`. Un cupo por fila habría hecho la capacidad indivisible y habría impedido el movimiento de cupo. |
| `D-DOM-02-03` | `edicion` y `disciplina` son campos REDUNDANTES en `Participacion`. | Es el mismo patrón que el `Participacion` del modelo de referencia: permiten la restricción de solapamiento SIN `JOIN`. El servicio los mantiene sincronizados. |
| `D-DOM-02-04` | El «movimiento» de cupo se implementa con el campo opcional `reemplaza_participacion_id` de `RT-IN-05`, no con una ruta nueva. | No se inventa una ruta fuera del ledger congelado. |
| `D-DOM-02-05` | Una disciplina `FEMENINO`/`MASCULINO` exige un género **declarado**. | Sin género conocido no se puede afirmar la compatibilidad. Se declara explícitamente en vez de dejar un valor por defecto silencioso. |
| `D-DOM-02-06` | `ActivadorInscripcion` abre su propia `transaction.atomic()`. | Lo invoca un coordinador EXTERNO (`commerce`), no un flujo de este módulo. La regla de §4.4 (la transacción la abre el flujo) aplica a los flujos propios; aquí la unidad atómica es «registrar la activación + sumar los cupos + conceder los beneficios» o nada. |
| `D-DOM-02-07` | `MAX_CUPOS_POR_AMPLIACION = 50` es un valor declarado por el dominio, no congelado. | `FL-04` paso 2 exige que exista un límite («se valida límite/fecha/precio»), pero ningún contrato congela el número. Se declara un valor conservador y explícito; la confirmación de producto está pendiente (`A0-DOM02-10`). |
| `D-DOM-02-08` | El tope por equipo no está serializado bajo concurrencia exacta. | `select_for_update` no existe en SQLite. Las invariantes **duras** (capacidad, duplicado, solapamiento) sí las garantiza la base de datos; el tope es blando. |
| `D-DOM-02-09` | Los beneficios `POR_CUPO` NO se conceden. | Su regla por tipo sigue ABIERTA (`PD-09`); concederla sería inventar un derecho con dinero detrás. Queda explícito y acumulable en `cantidad` para cuando se cierre. |
| `D-DOM-02-10` | `SCHEMA_VERSION` de `salesianos_fest` pasa de `1.0.0` a `1.1.0`. | El paquete congela cuatro rutas y wrappers nuevos. El cambio es ADITIVO (semántica MINOR). El registro global es de A0 → `A0-DOM02-02`. |
| `D-DOM-02-11` | `Inscripcion.cupos_solicitados` NO se incrementa con las ampliaciones. | Su semántica congelada por DOM-01 es «cupos que la inscripción compra en su alta». Cambiar el significado de un campo ya publicado rompería los espejos del frontend en vuelo. La capacidad total comprada es `cupos_pagados`. |
| `D-DOM-02-12` | `tests/conftest.py` tiene una fixture `autouse` que vuelve a registrar el activador. | El fixture `registro_activadores` de `commerce` vacía un registro **único del proceso**. Es adaptación de AISLAMIENTO DE PRUEBAS, no un atajo de la regla: la idempotencia se comprueba con la clave, no con el registro. En PRODUCCIÓN `apps.py::ready()` registra una vez y nada vacía el registro. |

---

## 9. Hechos nuevos (para `sdd/salesianos-fest-rebuild/facts`)

| # | Hecho |
|---|---|
| **F-55** | **Un `UPDATE` condicional sustituye a `select_for_update` cuando el motor de pruebas es SQLite.** `select_for_update` lanza `NotSupportedError` en SQLite; un `UPDATE … WHERE contador < capacidad` es atómico en SQLite Y en PostgreSQL, y no necesita bloqueos por fila. La condición viaja DENTRO de la sentencia, así que la base de datos —no la aplicación— decide quién entra. |
| **F-56** | **Un registro de proceso limpio por un fixture de otro módulo rompe a los dominios que se registran al arrancar.** `RegistroActivadoresCompra` es un singleton del proceso y `commerce`'s fixture `registro_activadores` lo vacía antes y después de cada test: el activador de `salesianos_fest` desaparecía para el resto de la sesión y 3 tests de DOM-02 fallaban sólo en la suite completa. En producción el registro es correcto (nadie llama a `limpiar()`), pero el fixtures de pruebas debe RESTAURAR las registraciones de los dominios, o el orden de los tests decide el resultado. |
| **F-57** | **El «cupo» del modelo objetivo es una UNIDAD de un contador, no una fila.** `RN-I03` define el saldo como una resta de contadores; el cupo no tiene identidad propia. Eso es lo que hace posible el MOVIMIENTO de cupo (liberar uno y tomar otro en la misma transacción) sin una tabla de asignaciones. |
| **F-58** | **Un código de error CONGELADO por el ledger no puede dejar que el schema HTTP lo preempta.** Si el `In` del payload validase el rango de la cantidad, Pydantic respondería `VALIDATION_ERROR` y el código congelado `CUPO_INVALIDO` (422) NUNCA llegaría al cliente. El rango lo declara y lo hace cumplir el DOMINIO; el schema sólo describe la forma. |
| **F-59** | **La versión del contrato de un módulo es un ACTO DE CONTRATO, no un número decorativo.** Subir `SCHEMA_VERSION` es lo que avisa al frontend de que el espejo Zod tiene que cambiar; mantener `1.0.0` con cuatro rutas nuevas habría hecho que el frontend creyera que nada cambió. El coste es un test de drift de A0 en rojo hasta que A0 actualiza el registro: ese es el mecanismo funcionando, no un defecto. |

---

## 10. Slices de revisión (presupuesto ≈ 400 líneas)

16 slices autónomos, ≈ **5 367 líneas** (316 de migración generada, ≈ 1 392 de tests):

| Slice | Contenido | Líneas |
|---|---|---:|
| WU-1 | `domain/models/participacion.py` + `domain/models/capacidad.py` + `domain/models/__init__.py` + `models.py` | 322 |
| WU-2 | `domain/constants.py` + `domain/exceptions.py` | 374 |
| WU-3 | `domain/referencia.py` + `domain/ports/__init__.py` + `infrastructure/services/**` | 300 |
| WU-4 | `domain/selectors/pool_selector.py` + `inscripcion_selector.py` + `domain/services/core/{capacidad,pool,beneficio}_core_service.py` | 325 |
| WU-5 | `domain/services/core/activador_inscripcion.py` + `apps.py` + `domain/results/**` | 360 |
| WU-6 | `domain/services/flujos/pool_flujo.py` | 366 |
| WU-7 | `domain/services/flujos/compra_cupos_flujo.py` + `domain/schemas/**` + `domain/services/orchestrators/**` | 352 |
| WU-8 | `presentation/schemas/**` + `presentation/presenters/**` | 339 |
| WU-9 | `presentation/controllers/inscripcion_controller.py` | 277 |
| WU-10 | `di.py` + `admin.py` | 265 |
| WU-11 | `migrations/0002_pool_capacidad.py` (generada) | 316 |
| WU-12 | `tests/conftest.py` + `tests/fixtures/fest_fixtures.py` | 379 |
| WU-13 | `tests/integration/test_cupo_disponibles.py` + `test_ampliacion_cupos.py` | 331 |
| WU-14 | `tests/integration/test_asignacion_participante.py` | 452 *(ligeramente sobre el presupuesto: un solo fichero de comportamiento no se parte sin romper la cohesión del caso)* |
| WU-15 | `tests/integration/test_cupo_activacion.py` | 297 |
| WU-16 | `tests/e2e/test_cupo_controller.py` | 312 |

**Orden de rollback:** WU-16 → WU-1. Ningún slice mezcla dominios ajenos.

---

## 11. Rollback

Punto de rollback `f3df5401c56b41c340f257e67d5a306904a9e670` (sin cambios; **sin commit**; `git stash` nunca invocado). **No revertir ni resetear ese commit.**

1. `manage.py migrate salesianos_fest zero` (verificado reversible, V9).
2. Borrar los ficheros creados listados en §4 y revertir los modificados.
3. Restaurar `STATE.md` y los topics de Engram (`sdd/salesianos-fest-rebuild/dom-02-apply-progress`, el índice `apply-progress` y el `state`).
4. **El historial comercial y de pagos se preserva**: este rollback nunca borra una compra, una orden ni una transacción, porque `commerce`/`pagos` son de otro dueño.
5. **No se borran hechos ya auditados**: `ActivacionCapacidad` y `BeneficioConcedido` son ACTAS de lo que se aplicó. En un rollback con datos vivos, la Reversión es una operación de negocio (un nuevo asiento que compense), no un borrado de historia (`RN-C08`, `DEC-06`).

---

## 12. Concurrencia

| Trabajo concurrente | Estado | Observación |
|---|---|---|
| **DOM-05** (`modules/marketplace/**`) | **activo durante el paquete** | **NO se tocó, NO se revirtió, NO se fusionó.** Sus modelos tienen migraciones pendientes y por eso `makemigrations --check --dry-run` sale **1**: esa migración es SUYA. Su suite se re-ejecutó verde (35 passed, V16). Su fila del tablero **no** se editó (A5 es su dueño). |
| **Frontend** (`Aplicacion/frontend/**`) | activo | **NO se tocó.** Su fila del tablero **no** se editó (A0/A7 es su dueño). |
| **DOM-01** (`modules/salesianos_fest/**`) | cerrado | Su código se **extiende** (nuevos modelos, servicios, rutas); su suite sigue verde (45 tests dentro de los 102 del módulo). La única modificación de su código es una refactorización de 3 líneas: `InscripcionFlujo._referencia_compra` ahora usa el formato compartido `domain/referencia.py` para que el productor y el lector del formato no puedan divergir. |
| `commerce` · `pagos` · `eventos` · `usuarios` | cerrados | **No editados.** Sus suites se re-ejecutaron verdes (V13–V15). El coordinador de `commerce` se **extiende** con un registrador, sin tocar su código. |
| `core/**` · `config/**` | de A0 | **No editados.** Sus 2 tests en rojo son la petición explícita de este paquete. |

---

## 13. Consumidores desbloqueados

- **DOM-07** (`T-050`…`T-052`) — ya tiene la aritmética del pool, la plantilla y sus estados.
- **API-02 / API-04** — ya tienen cuatro rutas vivas que espejar: `PoolOut`, `CompraCreadaOut` y sus formas de entrada. **Requieren el espejo Zod 1:1 del `SCHEMA_VERSION = 1.1.0`.**
- **API-05** — el `CompraCreadaOut` es la forma de la compra que el comprador consulta.
- **XCT-03** (`T-084`, depende de `T-023`) — ya tiene la activación idempotente, los beneficios sin duplicar y la incidencia reintentable.
- **UI-02 / UI-03 / UI-04** — el trío pagados/asignados/disponibles y la lista de impedimentos ya los publica el backend.
- **DOM-03 / DOM-06** — el patrón de activador por origen y el puerto de FND-05 ya tienen una implementación de referencia (`ActivadorInscripcion`).
- **VER-01…VER-03** — evidencia de exactamente-una-vez, de carrera y de reintento.

**Preparado para `DOM-07` y `API-02`:** el presenter y el schema están CONGELADOS en `1.1.0`, con `PoolOut` y `CompraCreadaOut` publicados y sus cuatro rutas vivas.

---

## 14. Siguiente paquete

**DOM-07** — *Competencias* (`T-050`…`T-052`) — ya puede consumir el pool: la aritmética de cupos, la plantilla y sus estados están congelados. **API-02** — ya tiene las cuatro rutas que espejar.

**Open para la siguiente ronda de A0:** `A0-DOM02-01`…`A0-DOM02-10` · `OD-A0R2-01` (forma del dinero en el cable) · `OD-A0R2-02` (`RT-IN-14` en el ledger) · `PD-09` (regla de reparto de beneficios `POR_CUPO`) · `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · `GAP-1`…`GAP-4` · `D-A`…`D-E`.
