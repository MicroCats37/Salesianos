# DOM-03 / DOM-05 / DOM-07 / DOM-08 — Cierre de validación en runtime

**Artifact:** `evidence/domains/DOM-03-05-07-08-runtime-verification.md` · **Packet:**
`sdd-apply` sólo-verificación (cierre de validación en runtime) · **Change:**
`salesianos-fest-rebuild` · **Owner:** A0 (coordinador) · **Date:** 2026-11-19

**Paquetes cerrados:** `DOM-03` (A4) · `DOM-05` (A5) · `DOM-07` (A6) · `DOM-08` (A8)

> **ESTADO: los CUATRO paquetes pasan a `completed`.** Cada uno tiene una suite
> **ejecutada y verde** con `uv run --group dev`, las puertas de Django verdes
> y el **replay de migraciones** verde sobre una base SQLite de archivo. Este
> documento es la **evidencia de ejecución** que faltaba: hasta ahora los cuatro
> paquetes tenían sus pruebas ESCRITAS pero NO EJECUTADAS.

> **NATURALEZA.** Esto **NO** es un paquete de funcionalidad nuevo: **no** se
> amplió ningún dominio. Es una pasada de **verificación en runtime** que
> (a) ejecuta lo que estaba escrito, (b) **reproduce** los defectos que se
> puedan reproducir y (c) **corrige** sólo los que sean **reproducibles y de
> alcance propio**. El trabajo concurrente de otros agentes se preservó
> intacto.

---

## 1. Entorno de verificación

| Elemento | Valor |
|---|---|
| Directorio de trabajo | `Aplicacion/backend` |
| Gestor | `uv 0.10.9` |
| Intérprete | CPython 3.10.0 |
| Django | 5.2.11 |
| Comando base | `uv run --group dev python …` (obligatorio en este paquete) |
| `pytest.ini` | `DJANGO_SETTINGS_MODULE = config.settings.test` · `addopts = --tb=short --nomigrations` · `asyncio_mode = auto` |
| Configuración efectiva | `pytest.ini` **prevalece** sobre `[tool.pytest.ini_options]` de `pyproject.toml` |

### 1.1 Overlays de settings usados

Los cuatro paquetes se verifican con su **overlay de módulo**, que replica el
registro permanente que A0 debe aplicar (A0-01 / A0-02 / A0-05). El overlay
**no** toca `config/**`: es un fichero de **verificación** dentro de la raíz
permitida del paquete.

| Overlay | Qué replica |
|---|---|
| `modules.salesianos_fest.tests.settings_overlay` | `INSTALLED_APPS += ["modules.salesianos_fest"]` · `INJECTOR_MODULES += ["…SalesianosFestModule"]` |
| `modules.marketplace.tests.settings_overlay` | `INSTALLED_APPS += ["modules.marketplace"]` · `INJECTOR_MODULES += ["…MarketplaceModule"]` · `DEBUG = False` · `STORAGES["default"]` |
| `modules.competencias.tests.settings_overlay` | `INSTALLED_APPS += ["modules.competencias"]` · `INJECTOR_MODULES += ["…CompetenciasModule"]` |
| `modules.patrocinadores.tests.settings_overlay` | `INSTALLED_APPS += ["modules.patrocinadores"]` · `INJECTOR_MODULES += ["…PatrocinadoresModule"]` · `DEBUG = False` · `STORAGES["default"]` · `MEDIA_DOMAINS += ["patrocinadores"]` |

`pytest-django` da prioridad a la variable de entorno `DJANGO_SETTINGS_MODULE`
sobre el valor de `pytest.ini`, así que con la variable fijada el overlay gana.

> **`--nomigrations` es la razón de las puertas de la §4.** `pytest.ini` corre
> las pruebas **sin migraciones** (Django crea las tablas directamente desde los
> modelos). Por eso una migración **escrita a mano** — las de DOM-03 (`0003`)
> y DOM-07 (`0001`) — **no la ejercita ninguna prueba**: sólo el **replay real**
> de la §4 la valida.

---

## 2. Suites focalizadas (comandos exactos y totales)

| # | Comando (workdir `Aplicacion/backend`) | Overlay | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `uv run --group dev python -m pytest modules/salesianos_fest/tests -q` | `modules.salesianos_fest.tests.settings_overlay` | **0** | **161 passed**, 144 warnings (39.87 s) |
| V2 | `uv run --group dev python -m pytest modules/marketplace/tests -q` | `modules.marketplace.tests.settings_overlay` | **0** | **97 passed**, 125 warnings (59.98 s) |
| V3 | `uv run --group dev python -m pytest modules/competencias/tests -q` | `modules.competencias.tests.settings_overlay` | **0** | **55 passed**, 131 warnings (12.84 s) |
| V4 | `uv run --group dev python -m pytest modules/patrocinadores/tests -q` | `modules.patrocinadores.tests.settings_overlay` | **0** | **53 passed**, 59 warnings (13.39 s) |

### 2.1 Atribución por paquete (casos recolectados, `pytest --collect-only -q`)

| Paquete | Ficheros de prueba del paquete | Casos | Trazado en el artefacto del paquete |
|---|---|---:|---|
| **DOM-03** | `test_activador_pase.py` · `test_beneficiario_pase.py` · `test_compra_pase.py` · `test_cortesia_pase.py` · `e2e/test_pase_controller.py` | **59** | 41 funciones → 59 casos (parametrización) |
| **DOM-05** | `test_pedido_reglas.py` · `test_pedido_snapshot.py` · `e2e/test_pedido_controller.py` | **34** | 32 funciones → 34 casos (una parametrizada ×3) |
| **DOM-06** | `test_inventario_movimientos.py` · `test_inventario_reserva.py` · `test_entrega_pedido.py` · `test_activador_marketplace.py` · `e2e/test_inventario_controller.py` | **28** | 28 casos (control: DOM-06 ya estaba `completed`) |
| **DOM-07** | `modules/competencias/tests/**` (módulo nuevo completo) | **55** | 43 funciones → 55 casos |
| **DOM-08** | `modules/patrocinadores/tests/**` (módulo nuevo completo) | **53** | 53 funciones → 53 casos |

**Control de coherencia:** DOM-05 (34) y DOM-06 (28) reproducen exactamente
las cifras declaradas en sus artefactos. DOM-03, DOM-07 y DOM-08 superan a su
número de funciones porque varios casos son parametrizados.

### 2.2 Warnings observados (ninguno bloqueante)

| Warning | Origen | Lectura |
|---|---|---|
| `PytestDeprecationWarning: asyncio_default_fixture_loop_scope is unset` | `pytest_asyncio` | Configuración del proyecto (`pytest.ini`), **no** de los paquetes. |
| `UserWarning: No directory at: …/staticfiles/` | `django/core/handlers/base.py` | Directorio de estáticos ausente en el árbol de trabajo. Cosmético. |
| `DeprecationWarning: get_api_controller() is deprecated` | `ninja_extra/operation.py` | Deprecación de la librería, **no** de los paquetes. |
| `RuntimeWarning: DateTimeField Encuentro.inicio_programado/fin_programado received a naive datetime` | `django/db/models/fields/__init__.py` | **Sólo DOM-07.** Las fixtures de `competencias` usan datetimes sin `tzinfo` con el soporte de zonas activo. Es un warning de las **fixtures de prueba**, no de la lógica de dominio: no se toca (ver §7, `R-RTV-04`). |

---

## 3. Puertas de Django

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V5 | `uv run --group dev python manage.py check` (settings por defecto = `config.settings.production`) | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **baseline ambiental idéntico** a FND-01/02/03/04/05 y DOM-06. **NO** es regresión. |
| V6 | `uv run --group dev python manage.py makemigrations --check --dry-run` (settings por defecto) | **1** | mismo `DB_NAME` — **baseline ambiental idéntico**. |
| V7 | `uv run --group dev python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced).` |
| V8 | `uv run --group dev python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |

### 3.1 Puertas por módulo (overlay propio)

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V9 | `manage.py check --settings=modules.salesianos_fest.tests.settings_overlay` | **0** | `no issues` |
| V10 | `manage.py makemigrations --check --dry-run --settings=modules.salesianos_fest.tests.settings_overlay` | **0** | `No changes detected` |
| V11 | `manage.py check --settings=modules.marketplace.tests.settings_overlay` | **0** | `no issues` |
| V12 | `manage.py makemigrations --check --dry-run --settings=modules.marketplace.tests.settings_overlay` | **0** | `No changes detected` |
| V13 | `manage.py check --settings=modules.competencias.tests.settings_overlay` | **0** | `no issues` |
| V14 | `manage.py makemigrations --check --dry-run --settings=modules.competencias.tests.settings_overlay` | **0** | `No changes detected` |
| V15 | `manage.py check --settings=modules.patrocinadores.tests.settings_overlay` | **0** | `no issues` |
| V16 | `manage.py makemigrations --check --dry-run --settings=modules.patrocinadores.tests.settings_overlay` | **0** | `No changes detected` |

> **HALLAZGO CERRADO — `0004_alter_comprapase_token_revocado_en` (A0-07 de DOM-06).**
> La reconciliación formal del estado registró que `modules/salesianos_fest`
> dejaba un **cambio de modelo pendiente** que rompía la puerta global
> `makemigrations --check --dry-run`. **Hoy NO existe**: el directorio de
> migraciones de `salesianos_fest` contiene `0001_initial`, `0002_pool_capacidad`
> y `0003_pases_derechos`, y **las puertas globales (V8) y por módulo (V10) son
> verdes**. La divergencia `D-DOM03-08` (migración `0003` escrita a mano y
> reconciliada estáticamente) queda **verificada en runtime** y el hallazgo
> **A0-07 de DOM-06 queda CERRADO**.

---

## 4. Replay de migraciones sobre SQLite de archivo

`pytest.ini` corre con `--nomigrations`, así que **ninguna prueba ejercita una
migración**. Las migraciones escritas a mano de DOM-03 (`0003`) y DOM-07
(`0001`) sólo se validan con un replay real. Base de datos temporal fuera del
repositorio (`%TEMP%\opencode\fest-replay\`), aplicada con
`manage.py migrate --no-input --settings=<overlay>` y la variable de entorno del
overlay correspondiente.

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V17 | `manage.py migrate --no-input --settings=modules.salesianos_fest.tests.settings_overlay` | **0** | cadena completa aplicada, incluido `salesianos_fest.0003_pases_derechos… OK` |
| V18 | `manage.py migrate --no-input --settings=modules.marketplace.tests.settings_overlay` | **0** | `marketplace.0003_entregapedido_movimientoinventario_reservainventario_and_more… OK` |
| V19 | `manage.py migrate --no-input --settings=modules.competencias.tests.settings_overlay` | **0** | `competencias.0001_initial… OK` (migración escrita a mano: **aplica y es equivalente al modelo**) |
| V20 | `manage.py migrate --no-input --settings=modules.patrocinadores.tests.settings_overlay` | **0** | `patrocinadores.0001_initial… OK` |

### 4.1 `showmigrations` — estado final del replay

| App | Migraciones aplicadas |
|---|---|
| `usuarios` | `[X] 0001_initial` · `[X] 0002_grupos_funcionales` |
| `eventos` | `[X] 0001_initial` |
| `pagos` | `[X] 0001_initial` |
| `commerce` | `[X] 0001_initial` · `[X] 0002_activacioncompra` |
| `salesianos_fest` | `[X] 0001_initial` · `[X] 0002_pool_capacidad` · `[X] 0003_pases_derechos` |
| `marketplace` | `[X] 0001_initial` · `[X] 0002_pedido_pedidodetalle_and_more` · `[X] 0003_entregapedido_movimientoinventario_reservainventario_and_more` |
| `competencias` | `[X] 0001_initial` |
| `patrocinadores` | `[X] 0001_initial` |

**Orden de la cadena respectedo:** `usuarios → pagos → commerce → marketplace →
salesianos_fest` (el grafo de migraciones del objetivo, `config/settings/base.py`
§LOCAL_APPS).

---

## 5. Barrido de regresión del backend

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V21 | `uv run --group dev python -m pytest --collect-only -q` (settings por defecto, raíz completa) | **2** | **722 collected, 6 errores de colección** → `RuntimeError: Model class modules.competencias… doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS` (y los 5 equivalentes de `patrocinadores`). **Ver §7 · A0-RTV-01.** |
| V22 | `uv run --group dev python -m pytest core/tests modules/eventos/tests modules/usuarios/tests modules/commerce/tests modules/pagos/tests modules/salesianos_fest/tests modules/marketplace/tests -q` | **0** | **722 passed**, 407 warnings (181.15 s) — **antes** de la corrección de §6 |
| V23 | el mismo comando, **después** de la corrección de §6 | **0** | **725 passed**, 407 warnings (178.26 s) — **+3** = las 3 pruebas nuevas de §6 |

### 5.1 Suite completa con los OCHO módulos de dominio registrados

Para responder a la pregunta que A0 tiene que responder («¿puedo registrar
`competencias` y `patrocinadores` sin romper nada?»), se ejecutó la suite
completa con un overlay **de verificación, fuera del repositorio**
(`%TEMP%\opencode\fest-replay\settings_all_overlay.py`, replicando A0-01 de
DOM-07 y DOM-08). **No se ha añadido ningún fichero al repositorio.**

| # | Configuración | Exit | Resultado |
|---:|---|---:|---|
| V24 | los 8 módulos de dominio registrados | **1** | **831 passed, 2 failed** (833 collected) — los 2 fallos son **de A0**, ver §7 · A0-RTV-04 |

**Los 2 fallos (antes de la corrección de §6: `828 passed, 2 failed`):**

```
FAILED core/tests/integration/test_registration_extension.py::test_no_hay_apps_de_dominio_inacabadas_registradas
FAILED core/tests/integration/test_registration_extension.py::test_solo_se_registran_los_modulos_de_di_completados
```

**Interpretación:** el guardián de A0 fija una lista **CERRADA** de apps
completadas (`APPS_DE_DOMINIO_COMPLETADAS`) y de módulos de DI
(`MODULOS_DE_DI_COMPLETADOS`). Al registrar `competencias` y `patrocinadores`
— que es exactamente lo que piden A0-01 de DOM-07 y DOM-08 — **las dos listas
quedan desfasadas y el guardián falla**. Esto **no** es un defecto de los
paquetes: es **el guardián avisando correctamente** de que el registro y su
test tienen que cambiar **juntos**.

---

## 6. Defecto REPRODUCIBLE y de alcance propio — CORREGIDO

### `D-RTV-01` — Doble fuente de verdad de la versión de schema (`salesianos_fest`)

**Qué.** `modules/salesianos_fest` declaraba la versión congelada de su
contrato HTTP **en dos sitios distintos, con dos valores distintos**:

| Fichero | Valor | Estado |
|---|---|---|
| `modules/salesianos_fest/__init__.py` | `SCHEMA_VERSION = "1.0.0"` | **OBSOLETO** — congelado en DOM-01, nunca actualizado en DOM-02 (`1.1.0`) ni DOM-03 (`1.2.0`) |
| `modules/salesianos_fest/presentation/schemas/__init__.py` | `SCHEMA_VERSION = "1.2.0"` | **CANÓNICO** — el que declara el propio módulo y el que valida `FR-07` §1.1 |

**Por qué es un defecto y no una Andersen.** `FR-07` §1.1 hace del registro de
versión el mecanismo de **detección de drift** entre el backend y el espejo Zod
del frontend. Ese mecanismo **exige una sola fuente de verdad por módulo**. Con
dos literales, `from modules.salesianos_fest import SCHEMA_VERSION` devuelve
`1.0.0` mientras el contrato real es `1.2.0`: **tres versiones deMinor**
separadas, y ninguna de las dos rutas avisa. Peor: `modules/salesianos_fest`
era el **único** módulo de dominio con esa copia en la raíz del paquete
(`marketplace`, `competencias` y `patrocinadores` **no** la tienen).

**Reproducción (antes de corregir).**

```
>>> from modules.salesianos_fest import SCHEMA_VERSION as raiz
>>> from modules.salesianos_fest.presentation.schemas import SCHEMA_VERSION as canonico
>>> raiz, canonico
('1.0.0', '1.2.0')      # <- dos valores para el MISMO contrato congelado
```

**Corrección (dentro de la raíz permitida `modules/salesianos_fest/**`).**
`modules/salesianos_fest/__init__.py` deja de declarar un literal y pasa a
**reexportar** la fuente canónica: `from
modules.salesianos_fest.presentation.schemas import SCHEMA_VERSION`. El nombre
público se conserva (`from modules.salesianos_fest import SCHEMA_VERSION`
sigue funcionando) y ahora devuelve el valor correcto. **Cero** cambio de
comportamiento: nadie leía la copia obsoleta.

**Verificación posterior.**

```
>>> import modules.salesianos_fest as m
>>> from modules.salesianos_fest.presentation.schemas import SCHEMA_VERSION
>>> m.SCHEMA_VERSION, SCHEMA_VERSION, m.SCHEMA_VERSION == SCHEMA_VERSION
('1.2.0', '1.2.0', True)
```

**Guarda de regresión (nueva).**
`modules/salesianos_fest/tests/integration/test_contrato_schema_version.py`
(3 casos) fija las **tres** condiciones:

1. `presentation.schemas.SCHEMA_VERSION == SCHEMA_VERSIONS["salesianos_fest"]`
   y **no hay drift** (`hay_drift` es `False`) — cierra el hueco que tenían
   `marketplace` y `patrocinadores` y que `salesianos_fest` **no** tenía.
2. La raíz del paquete **no** declara una segunda copia: el nombre corto
   devuelve la MISMA versión.
3. **UNICIDAD del literal**: se recorre el paquete y se comprueba que existe
   **exactamente un** `SCHEMA_VERSION = "<literal>"`, en
   `presentation/schemas/__init__.py`. Una reexportación no casa con el patrón,
   así que la guarda detecta la reintroducción de cualquier segunda copia.

**Totales tras la corrección:** `modules/salesianos_fest/tests` → **164 passed**
(161 + 3). Barrido de regresión del backend → **725 passed**.

---

## 7. Bloqueos para A0 (NO corregibles en este paquete — raíces prohibidas)

Todos los siguientes están **FUERA** de las raíces permitidas de este paquete
(`config/**`, `core/**`, `Aplicacion/plan/**`, `Aplicacion/frontend/**`) y por
eso se **REPORTAN**, no se tocan.

### `A0-RTV-01` — BLOQUEANTE · `modules.competencias` y `modules.patrocinadores` NO están en `INSTALLED_APPS`

`config/settings/base.py` §LOCAL_APPS registra seis apps de dominio
(`eventos`, `usuarios`, `pagos`, `commerce`, `salesianos_fest`, `marketplace`).
`modules.competencias` y `modules.patrocinadores` **no** están.

**Efecto reproducible:** el `pytest` de la **raíz** del backend se **INTERRUMPE**
con **exit 2** y **6 errores de colección** (V21) — `RuntimeError: Model class
modules.competencias… doesn't declare an explicit app_label and isn't in an
application in INSTALLED_APPS`. Consecuencia adicional: **la puerta global
`makemigrations --check --dry-run` es CIEGA** para estas dos apps (V8 sale
verde precisamente porque Django no las conoce).

**Acción A0:** añadir `"modules.competencias"` y `"modules.patrocinadores"` a
`LOCAL_APPS`, **respetando el grafo de migraciones** (después de
`modules.marketplace`; `competencias` referencia `eventos.Edicion` y
`usuarios.Persona`).

### `A0-RTV-02` — BLOQUEANTE · Cuatro controllers existen y NO están registrados

`config/api.py` registra diez controllers. **Faltan cuatro**, uno por cada
paquete de dominio de esta ronda:

| Controller | Paquete | Consecuencia |
|---|---|---|
| `PedidoController` | **DOM-05** | las rutas `RT-CM-03` / `RT-MK-04` **no existen** en el API |
| `InventarioController` | DOM-06 | las rutas `RT-MK-08`…`RT-MK-12` **no existen** en el API |
| `CompetenciasController` | **DOM-07** | las 16 rutas **no existen** en el API |
| `PatrocinadorController` | **DOM-08** | la ruta `RT-MD-02` **no existe** en el API |

**Acción A0:** `registrar_controladores(...)` en `config/api.py`, y **actualizar
en el MISMO cambio** las listas `CONTROLLERS_COMPLETADOS`,
`PREFIJOS_PERMITIDOS` y `RUTAS_DE_DOMINIO_CONGELADAS` de
`core/tests/integration/test_registration_extension.py` (ver `A0-RTV-04`).

### `A0-RTV-03` — BLOQUEANTE · `SCHEMA_VERSIONS` no tiene `"competencias"`

`core/contract_versions.py` registra `"patrocinadores": "1.0.0"`,
`"marketplace": "1.2.0"` y `"salesianos_fest": "1.2.0"`, pero **NO**
`"competencias"`. El módulo `modules/competencias` declara
`SCHEMA_VERSION = "1.0.0"` en `presentation/schemas/__init__.py` y **no tiene
test de drift** (a diferencia de `marketplace` y `patrocinadores`, que sí lo
tienen).

**Acción A0:** registrar `SCHEMA_VERSIONS["competencias"] = "1.0.0"` **y** añadir
en `modules/competencias/tests/**` el test de drift equivalente al de
`marketplace` (`test_producto_contrato.py::test_la_version_de_schema_coincide_con_el_registro_de_a0`).
**No se ha añadido ese test en este paquete** porque fallaría mientras el
registro no exista: un test rojo no es evidencia.

### `A0-RTV-04` — BLOQUEANTE · El guardián de registro de A0 fija listas CERRADAS

`core/tests/integration/test_registration_extension.py` define
`APPS_DE_DOMINIO_COMPLETADAS` (6 entradas) y `MODULOS_DE_DI_COMPLETADOS`
(6 entradas). **Reproducido**: al registrar `competencias` + `patrocinadores`
(lo que pide `A0-RTV-01`), fallan
`test_no_hay_apps_de_dominio_inacabadas_registradas` y
`test_solo_se_registran_los_modulos_de_di_completados` (V24).

**Acción A0:** ampliar **AMBAS** listas en el mismo commit que el registro de
`A0-RTV-01` / `A0-RTV-02`. Es un cambio **coordinado**, no opcional: el
guardián existe para que nadie registre una app a medias.

### `A0-RTV-05` — 33 códigos públicos sin catalogar (DOM-05 / DOM-07 / DOM-08)

`core/exceptions.py::PUBLIC_ERROR_MESSAGES` **no** contiene los códigos que
DOM-05, DOM-07 y DOM-08 lanzan. Comprobado por barrido de los literales
`code = "<CÓDIGO>"` del código de producción de los cuatro módulos: **78
códigos** en total, de los cuales **33 no están catalogados**.

**Reparto:** `marketplace` **13** · `competencias` **16** · `patrocinadores`
**4** · `salesianos_fest` **0** (los 17 códigos de DOM-03 **sí** están
catalogados por la reconciliación de A0 de DOM-03).

**Efecto real (leído en `core/exceptions.py::on_http_error`):** el
`error.code` **estable sí se conserva** (es el atributo `code` de la excepción),
pero la **prosa pública** cae al mensaje genérico del status HTTP y el servidor
registra un `WARNING "HttpError no catalogado (code=%s status=%s)"` en **cada**
ocurrencia.

`marketplace` (13): `MOVIMIENTO_INVENTARIO_INMUTABLE`,
`MOVIMIENTO_INVENTARIO_INVALIDO`, `MOVIMIENTO_INVENTARIO_NO_ENCONTRADO`,
`PEDIDO_CANTIDAD_INVALIDA`, `PEDIDO_ITEM_NO_PERMITIDO`, `PEDIDO_ITEMS_MIXTOS`,
`PEDIDO_NO_AUTORIZADO`, `PEDIDO_NO_ENCONTRADO`, `PEDIDO_NO_ENTREGABLE`,
`PEDIDO_NO_PAGADO`, `PEDIDO_SIN_RESERVA`, `RESERVA_NO_CONFIRMABLE`,
`STOCK_INSUFICIENTE`.

`competencias` (16): `BYE_INVALIDO`, `COMPETENCIA_EQUIPO_DUPLICADO`,
`COMPETENCIA_EQUIPO_NO_ENCONTRADA`, `COMPETENCIA_NO_ENCONTRADA`,
`DISCIPLINA_NO_ENCONTRADA`, `ENCUENTRO_NO_ENCONTRADO`, `ENLACE_INVALIDO`,
`GANADOR_INVALIDO`, `HORARIO_INVALIDO`, `MOTIVO_REQUERIDO`, `ORDEN_DUPLICADO`,
`PARTICIPANTE_INVALIDO`, `RONDA_DUPLICADA`, `RONDA_NO_ENCONTRADA`,
`SOLAPAMIENTO_HORARIO`, `TRANSICION_INVALIDA`.

`patrocinadores` (4): `GALERIA_PATROCINADOR_INVALIDA`,
`PATROCINADOR_IMAGEN_NO_ENCONTRADA`, `PATROCINADOR_NO_ENCONTRADO`,
`PATROCINADOR_SLUG_DUPLICADO`.

**Acción A0:** catalogar los 33 en `PUBLIC_ERROR_MESSAGES` (es la petición
`A0-03`/`A0-05` de los tres paquetes, ya abierta).

### `A0-RTV-06` — `core.media` deja directorios vacíos

Re-confirmado (A0-08 de DOM-08). `core/**` es raíz prohibida.

### `A0-RTV-07` — `*.sqlite3` en `.gitignore`

`Aplicacion/backend/db.sqlite3` está versionado y aparece como `M` en el árbol
de trabajo. **Byproduct de esta ronda: NINGUNO** — el fichero se escribió por
última vez a
las **09:39:29** y esta ronda termina a las **17:03**; ninguna puerta lo tocó
(`manage.py check` y `makemigrations --check` no abren la base de datos).

### `A0-RTV-08` — `00-matriz-tareas.md` sin sincronizar

Filas `T-030`…`T-032` (DOM-03), `T-041` (DOM-05), `T-050`…`T-052` (DOM-07),
`T-060` (DOM-08) y `T-042`/`T-043` (DOM-06) siguen en `pending`. La matriz
física es raíz prohibida.

---

## 8. Hallazgos CERRADOS por esta ronda

| # | Hallazgo previo | Estado |
|---|---|---|
| `C-RTV-01` | **DOM-06 · A0-07**: `modules/salesianos_fest` con cambio de modelo pendiente (`0004_alter_comprapase_token_revocado_en`) que rompía la puerta global `makemigrations --check --dry-run`. | **CERRADO** — no existe tal migración; V8 y V10 son verdes (§3). |
| `C-RTV-02` | **DOM-05**: «el bloqueo de SQLite de la ronda interrumpida NO se depuró»; hipótesis estática: `config/settings/test.py` usa `"isolation_level": None` (autocommit). | **NO REPRODUCIBLE** — las 34 pruebas de DOM-05 y las 97 del módulo `marketplace` pasan sin tocar `config/**`. La hipótesis **no se sostiene** en el estado actual del árbol. Se deja constancia; **no** se cambió código para satisfacerla. |
| `C-RTV-03` | **DOM-07**: la migración `0001_initial` escrita a mano tiene una equivalencia «razonada estáticamente y NO verificada». | **CERRADO** — V14 (`No changes detected`) + V19 (replay `competencias.0001_initial… OK`) verifican la equivalencia en runtime. |
| `C-RTV-04` | **DOM-03**: la migración `0003_pases_derechos` reconciliada estáticamente (`D-DOM03-08`). | **CERRADO** — V10 + V17 (replay) verdes. |
| `C-RTV-05` | **DOM-03 · reconciliación de A0**: 86 casos parametrizados + 7 ficheros modificados en `core/tests/**` ESCRITOS y NO ejecutados. | **CERRADO** — ejecutados dentro de V22/V23 (725 passed). |
| `C-RTV-06` | **DOM-07 · A0-02**: `SCHEMA_VERSIONS["competencias"]` ausente. | **RE-CONFIRMADO y escalado** a `A0-RTV-03` (sigue siendo de `core/**`). |

---

## 9. Decisiones ABIERTAS que este paquete NO toca

Este paquete **no inventa** política comercial ni cierra decisiones abiertas.

| Decisión | Estado | Nota |
|---|---|---|
| `H-01` — `PaseNoTransferibleError` **definida y nunca lanzada** (`modules/salesianos_fest/domain/exceptions.py`) | **ABIERTA** | Re-confirmado: sólo aparece en su definición y en `__all__`. **No se lanza** porque la política de liberación del cupo y de reemplazo del titular tras una revocación está **explícitamente ABIERTA** (`PD-02` / `GOV-01-OPEN-08`). Lanzarla sería **inventar política comercial**. Su propio docstring dice «Código REQUESTED a A0». |
| `PD-02` / `GOV-01-OPEN-08` — liberación del cupo y reemplazo del titular | **ABIERTA** | Sin dueño en esta ronda. |
| `PD-01` (BOX) | **ABIERTA** | No se modela. |
| `OD-DOM05-01`…`03` · `OD-DOM06-01` · `OD-DOM07-01`…`05` · `OD-DOM08-01`…`06` | **ABIERTAS** | Sin cambio. |
| `R-RTV-04` — datetimes sin `tzinfo` en las fixtures de `competencias` | **REPORTADA** | Warning de las **fixtures de prueba** (`RuntimeWarning`), no de la lógica de dominio. No se toca: cambiar las fixtures alteraría el alcance de las pruebas de un paquete ya verde. **A0 + A6** pueden normalizarlas a `timezone.now()`. |

---

## 10. Ficheros cambiados

**Todos dentro de las raíces permitidas. Ninguna raíz prohibida fue tocada.**

| Fichero | Acción | Qué |
|---|---|---|
| `Aplicacion/backend/modules/salesianos_fest/__init__.py` | **modificado** | La copia obsoleta `SCHEMA_VERSION = "1.0.0"` pasa a ser una **reexportación** de la fuente canónica `presentation.schemas.SCHEMA_VERSION` (`1.2.0`) — una sola fuente de verdad. |
| `Aplicacion/backend/modules/salesianos_fest/tests/integration/test_contrato_schema_version.py` | **creado** | Guarda de regresión: coincidencia con el registro de A0, ausencia de drift, unicidad del literal en el paquete y ausencia de copia en la raíz. **3 casos.** |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/domains/DOM-03-05-07-08-runtime-verification.md` | **creado** | Este documento. |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | **modificado** | Las cuatro filas de los paquetes y la transición de este cierre. |

**Fuera del repositorio** (temporal, no versionado):
`%TEMP%\opencode\fest-replay\settings_all_overlay.py` (overlay de verificación
combinado) y las cuatro bases SQLite de archivo del replay. **Ninguno se
commitea.**

---

## 11. Concurrencia preservada

- `git rev-parse HEAD` → `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit;
  **no** revertir ni resetear).
- El árbol traía **muchos cambios de otros agentes** (`Aplicacion/frontend/**`,
  `Aplicacion/backend/modules/usuarios/**`, `Aplicacion/backend/config/**`,
  `Aplicacion/backend/core/**`, `Aplicacion/backend/modules/marketplace/**`,
  `Aplicacion/backend/modules/salesianos_fest/**`): **no se tocaron, no se
  revertieron y no se fusionaron**. Sólo se editaron los dos ficheros de
  `salesianos_fest` listados en §10.
- `git stash`, `git reset`, `git checkout` y `git commit`: **nunca invocados**.

---

## 12. Rollback

1. Revertir `Aplicacion/backend/modules/salesianos_fest/__init__.py` desde
   `fd1c4c1…`.
2. Borrar
   `Aplicacion/backend/modules/salesianos_fest/tests/integration/test_contrato_schema_version.py`.
3. Borrar
   `Aplicacion/task/salesianos-fest-rebuild/evidence/domains/DOM-03-05-07-08-runtime-verification.md`.
4. Revertir las filas de DOM-03 / DOM-05 / DOM-07 / DOM-08 y la transición de
   este cierre en `STATE.md` y en los topics de Engram.
5. Los artefactos temporales de `%TEMP%\opencode\fest-replay\` se pueden borrar
   sin efecto.

**Punto de rollback:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit).

---

## 13. Totales finales

| Medida | Valor |
|---|---|
| Casos ejecutados en las 4 suites focalizadas | **161 + 97 + 55 + 53 = 366** |
| Casos de regresión del backend (settings por defecto) | **725 passed** (antes: 722) |
| Suite completa con los 8 módulos de dominio registrados | **833 collected → 831 passed + 2 failed** (los 2 fallos son de `A0-RTV-04`) |
| Puertas de Django verdes | 10 de 12 (las 2 con settings por defecto fallan por `DB_NAME`, **baseline ambiental idéntico**) |
| Replays de migración | **4 de 4** verdes |
| Defectos reproducibles corregidos | **1** (`D-RTV-01`) + **1** guarda de regresión (3 casos) |
| Hallazgos cerrados | **5** (`C-RTV-01`…`C-RTV-05`) · **1** no reproducible (`C-RTV-02`) |
| Bloqueos escalados a A0 | **8** (`A0-RTV-01`…`A0-RTV-08`), **4 BLOQUEANTES** |
| Decisiones abiertas | **0 cerradas** — ninguna inventada |

**Siguiente paquete:** `API-03` y `API-05` (los espejos Zod 1:1 de las rutas de
DOM-03 / DOM-05 / DOM-06 / DOM-07 / DOM-08) y `XCT-01`, **después** de que A0
aplique `A0-RTV-01`…`A0-RTV-04`. Con autorización explícita del usuario: la
verificación diferida de **FND-06**, **FND-07**, **FND-08** y **UI-01**
(frontend, propiedad de otro agente).
