# VER-01 — Baseline, Regression And Payment Reliability Verification

**Artifact:** `evidence/verification/VER-01-baseline-regression-payments.md` ·
**Packet:** `VER-01` · **Original plan tasks:** `T-090`, `T-091` ·
**Change:** `salesianos-fest-rebuild` · **Owner:** A9 + A2 ·
**Mode:** apply (verification + cleanup only) · **Artifact store:** engram + physical evidence ·
**Date:** 2026-11-20

> **ESTADO: `verification_required` — VER-02 DESBLOQUEADO para su alcance.**
>
> **Este documento tiene DOS PASADAS.** La §1…§11 registran la **primera** medición
> (2026-11-20, ~02:5x), sobre el árbol tal como estaba **antes** de las cuatro
> correcciones aplicadas en paralelo. La **§12** es la **re-verificación sobre el árbol
> ACTUAL**, que **sustituye** los números de las §2 y §3.
>
> **Resumen vigente (§12):** backend **974 passed / 0 failed** · frontend **2276 passed /
> 0 failed** · `tsc` **0** · `docker compose config` **0** · **22** controllers · **75**
> rutas vivas · **DRIFT A = 0** (antes 8). Las cuatro correcciones
> (`CORR-VER01` #11484 · `COR-01` #11483 · `CORR-VER01-A0` #11488 · `COR-02` #11490)
> cerraron **todos** los bloqueadores de producto y de cableado que esta primera pasada
> midió.
>
> **VER-01 no se firma `completed`** por dos razones honestas: (1) el **techo de Biome**
> sigue roto (445/110 vs 105/93) — deuda **heredada** de todo el frontend del rebuild,
> en código de producción ajeno, dueño **A0 + A7** (§12.4); (2) la **lane PostgreSQL no
> se pudo ejecutar** — **bloqueo de ENTORNO**, no de código: la garantía de concurrencia
> `QA-V02` / `QA-I05` sigue sin probarse en un motor con bloqueo de filas (§12.3).

---

## 1. Entorno de verificación

| Elemento | Valor |
|---|---|
| Directorio de trabajo (backend) | `Aplicacion/backend` |
| Directorio de trabajo (frontend) | `Aplicacion/frontend` |
| Gestor | `uv 0.10.9` (f675560f3) |
| Intérprete | CPython 3.10.0 |
| Django | 5.2.11 · pytest 8.3.4 · pytest-asyncio · pytest-django |
| Base de datos de la suite | SQLite `:memory:` (`config.settings.test`) |
| `pytest.ini` | `DJANGO_SETTINGS_MODULE = config.settings.test` · `addopts = --tb=short --nomigrations` · `asyncio_mode = auto` |
| Frontend | vitest 5.1.1 · TypeScript `tsc --noEmit` · biome |
| HEAD | `2c411cdfc062714cfa7ff39765c4357ddf8267e2` ("betha 6") — **sin commit creado por este packet** (ya existía cuando empezó) |
| Overlays usados | **fuera del repositorio**: `%TEMP%\opencode\ver01\ver01_admin_overlay.py` y `ver01_migrate_overlay.py` |

**Restricciones respetadas:** `uv run --group dev …` **exclusivamente** (nunca
Python global, nunca `.venv\Scripts\python.exe` directo, nunca `uv sync`) ·
nunca `git stash` / `reset` / `checkout` / `commit` / `push` · ningún fichero
de `contract/**` · ningún `Aplicacion/plan/**` · ningún `.env*` · ninguna
base de datos del repositorio.

---

## 2. Comandos / códigos de salida

### 2.1 Backend (workdir `Aplicacion/backend`, `uv run --group dev`)

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| B1 | `python -m pytest --collect-only -q` | **2** | **690 collected, 2 collection errors** — `modules/administracion/tests/{integration/test_admin_auditoria,integration/test_admin_operacion}.py`: `RuntimeError: Model class modules.administracion.domain.models.accion_auditada.AccionAuditada doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS` |
| B2 | `python -m pytest modules -q` (registro **permanente**) | **2** | **2 errors during collection** — los mismos dos ficheros. La suite completa **no se puede recolectar** mientras `modules.administracion` no esté registrada |
| B3 | `python -m pytest modules -q --ds=ver01_admin_overlay` (overlay de 1 app) | **1** | **1 failed, 700 passed** (701 collected), 656 warnings, 184.67 s — **ver §2.5: el recuento cambió durante el packet por un fichero de test de otro agente** |
| B4 | `python -m pytest modules/commerce/tests modules/pagos/tests modules/notificaciones/tests -q` | **0** | **115 passed**, 35 warnings, 7.24 s — **laLane de pagos completa** |
| B5 | `python -m pytest modules/competencias/tests modules/salesianos_fest/tests/integration/test_asignacion_participante.py -q` | **0** | **72 passed**, 131 warnings, 13.58 s (tras las correcciones de §5) |
| B6 | `python -m pytest modules/administracion/tests -q --ds=ver01_admin_overlay` | **0** | **15 passed**, 3.21 s (tras las correcciones de §5) |
| B7 | `python manage.py check` (settings por defecto = `production`) | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **baseline ambiental B7, idéntico** a GOV-02/FND-01…FND-05/DOM-*/XCT-* |
| B8 | `python manage.py makemigrations --check --dry-run` (por defecto) | **1** | mismo `DB_NAME` — **baseline ambiental B7** |
| B9 | `python manage.py check --settings=config.settings.test` | **0** | `System check identified no issues (0 silenced).` |
| B10 | `python manage.py makemigrations --check --dry-run --settings=config.settings.test` | **0** | `No changes detected` |
| B11 | `python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced).` |
| B12 | `python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| B13 | `python manage.py migrate --settings=ver01_migrate_overlay` (SQLite en `%TEMP%`) | **0** | todas las migraciones aplicadas, incluidas `notificaciones.0001_initial` y `validaciones.0001_initial` |
| B14 | `python manage.py showmigrations --settings=ver01_migrate_overlay` | **0** | 11 apps de dominio presentes en el grafo |
| B15 | `python manage.py migrate administracion zero --settings=ver01_migrate_overlay` | **0** | `Unapplying administracion.0001_initial... OK` — **reversible** |
| B16 | `python manage.py migrate administracion --settings=ver01_migrate_overlay` | **0** | `Applying administracion.0001_initial... OK` — **replay** |
| B17 | `python manage.py makemigrations --check --dry-run --settings=ver01_migrate_overlay` (**con `administracion` registrada**) | **0** | `No changes detected` — la migración escrita a mano coincide EXACTAMENTE con los modelos. **La puerta ciega de A0-wiring-validation §5 queda cerrada** |

### 2.2 Frontend (workdir `Aplicacion/frontend`)

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| F1 | `npx tsc --noEmit` | **0** | **LIMPIO** — 0 diagnósticos, **puerta global VERDE** |
| F2 | `npx vitest run` | **1** | **20 files failed \| 32 passed (52)** · **40 failed \| 2235 passed (2275)** · 70.56 s |
| F3 | `npx biome check .` | **1** | **Checked 714 files** · **441 errors** · **110 warnings** |
| F4 | `npx vitest run src/features/pagos` | **0** | **6 passed** (suite de XCT-03 escrita y nunca ejecutada) |
| F5 | `npx biome check <los 14 ficheros que este packet tocó>` | **1** | **20 errors**, todos `assist/source/organizeImports` en 9 ficheros **cuyos imports este packet NO tocó** ⇒ **deuda preexistente**, 0 introducida por VER-01 |

### 2.3 Despliegue

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| D1 | `docker compose config --quiet` | `Aplicacion` | **0** | compose válido |

### 2.4 No ejecutado (y por qué)

`next build` · `npm install` · servidores · navegador · **auditoría de cinco
anchos (360 / 390 / 768 / 1024 / 1440)** · la **lane PostgreSQL** de `BL-05`
§2 (no hay PostgreSQL disponible en este entorno) · `git stash` / `commit` /
`reset` / `checkout`.

### 2.5 CONCURRENCIA: el árbol cambió bajo este packet

Durante la ejecución de VER-01, **otro agente escribió en el árbol del
objetivo**. El caso medido:

| Fichero | Creado | Tests | Dueño |
|---|---|---:|---|
| `Aplicacion/backend/modules/salesianos_fest/tests/integration/test_seed_catalogo_garantias.py` | **2026-11-20 02:48:31** (después de la primera corrida completa del backend de este packet, a las ~02:45) | **9** | **concurrente** (raíz de `salesianos_fest`, DOM-01) |

**Efecto medido sobre el recuento:** la primera corrida completa dio
`1 failed, 691 passed` (**692** tests) y la corrida de cierre, sobre el MISMO
árbol de este packet, dio `1 failed, 700 passed` (**701** collected). La
diferencia son exactamente los **9** tests del fichero nuevo. **Los 9 tests
nuevos pasan** (no añaden ningún fallo).

**Lo que este packet NO hizo:** ese fichero **no** se tocó, **no** se revirtió,
**no** se fusionó y **no** se cuenta como trabajo de VER-01. **Los números que
secriben en este informe son los de la corrida de cierre** (701 collected /
700 passed), que son los del árbol tal como queda.

---

## 3. Baseline → target: qué es regresión y qué no

El oráculo de `BL-04` §3 registra el estado del **raíz congelado**
(`backend/`, `frontend/`). El **objetivo** (`Aplicacion/backend`,
`Aplicacion/frontend`) es otro árbol, con ~150 ficheros más y con las suites
que el rebuild escribió y **nunca ejecutó** (la preferencia `#11299` lo
prohibía durante el apply). Por eso la comparación correcta es:

| Baseline `BL-04` (raíz congelada) | Estado en el objetivo | Veredicto |
|---|---|---|
| 13 backend rojos (B1…B6) | **0** de esos 13 reaparecen: el objetivo tiene sus propios módulos y suites | **MEJORA** |
| `admin.catalogos.schema.test.ts` rojo (B8) | el fichero **no existe** en el objetivo | **MEJORA** (la zona fue reconstruida) |
| `tsc` 0 diagnósticos | **0** | **MANTENIDO** |
| Biome 105 / 93 (566 ficheros) | **441 / 110** (714 ficheros) | **REGRESIÓN contra el techo** (densidad 0.19 → 0.62 errores/fichero) |
| `manage.py check` → `DB_NAME` (B7) | **idéntico** | **BASELINE AMBIENTAL, NO REGRESIÓN** |
| 4 warnings de React (B10) | no aparecen | **MEJORA** |

**Conclusión del oráculo:** los 13 fallos backend y el fichero rojo frontend
del baseline **no reaparecen**. Lo que queda son fallos **nuevos**,Nacidos de
suites escritas y nunca ejecutadas. Todos están clasificados en §6.

---

## 4. Evidencia de pagos (step 3 del packet)

`B4` + `F4` + `F2` dan la ejecución real de los escenarios de **modal /
reintento / callback duplicado / recuperación post-pago**. Los casos que los
cubre, con su nombre literal:

| Escenario | Caso | Resultado |
|---|---|---|
| **Callback duplicado** | `test_un_webhook_duplicado_no_genera_dos_notificaciones` | **PASS** |
| | `test_un_webhook_duplicado_no_habilita_el_derecho_dos_veces` | **PASS** |
| | `test_la_confirmacion_repetida_no_duplica_el_pago` | **PASS** |
| | `test_la_notificacion_tardia_no_duplica_el_pago` | **PASS** |
| | `test_el_registro_es_idempotente_aunque_lleguen_dos_voltas` | **PASS** |
| **Idempotencia** | `test_la_repeticion_devuelve_el_registro_previo` | **PASS** |
| | `test_la_misma_clave_con_otra_huella_es_un_conflicto` | **PASS** |
| | `test_la_misma_clave_en_otro_ambito_es_otra_operacion` | **PASS** |
| | `test_la_huella_no_guarda_el_payload` | **PASS** |
| | `test_una_clave_valida_se_acepta` · `test_una_clave_vacia_significa_que_no_hay_idempotencia` · `test_una_clave_demasiado_larga_se_rechaza` · `test_una_clave_con_caracteres_no_admitidos_se_rechaza` | **PASS** |
| **Reintento** | `test_el_reintento_tras_un_fallo_habilita_el_derecho` | **PASS** |
| | `test_un_reintento_concurrente_no_habilita_el_derecho_dos_veces` | **PASS** |
| | `test_la_clave_de_activacion_es_estable_entre_reintentos` | **PASS** |
| | `test_la_confirmacion_tardia_converge_en_una_sola_activacion` | **PASS** |
| **Recuperación post-pago (conciliación)** | `test_la_conciliacion_encuentra_un_pago_sin_derecho_habilitado` | **PASS** |
| | `test_la_conciliacion_converge_y_no_habilita_el_derecho_dos_veces` | **PASS** |
| | `test_la_conciliacion_no_revierte_el_cobro` | **PASS** |
| | `test_sin_aplicar_la_conciliacion_solo_informa_y_no_muta` | **PASS** |
| | `test_el_fallo_del_coordinador_no_revierte_el_cobro` | **PASS** |
| | `test_una_orden_no_confirmada_no_se_concilia` | **PASS** |
| **Independencia de la notificación** | `test_el_fallo_de_la_notificacion_no_revierte_el_pago_confirmado` | **PASS** |
| | `test_la_notificacion_solo_se_intenta_cuando_el_derecho_esta_habilitado` | **PASS** |
| | `test_la_confirmacion_publica_el_veredicto_de_activacion` | **PASS** |
| **Firma del proveedor** | `test_la_notificacion_sin_firma_es_400` · `test_la_notificacion_con_firma_invalida_se_rechaza` · `test_la_notificacion_sin_clave_de_comercio_falla_cerrado` | **PASS** |
| **Modal / frontend de pagos** | `npx vitest run src/features/pagos` → 6 casos | **PASS** |

**Veredicto de pagos:** los **cinco** escenarios del packet tienen ejecución
real y **verde**. El canal `estado_activacion` (XCT-03) está **publicado y
verificado**: `test_el_vocabulario_del_veredicto_operativo_no_se_amplia_ni_se_renumera`
**PASS** (el vocabulario congelado de 8 códigos **no** se amplía) y
`test_la_activacion_activada_no_cambia_el_veredicto_operativo` **PASS**.

---

## 5. Correcciones aplicadas por este packet (sólo defectos de TEST)

Ninguna toca producto, contratos, planes, configuración de producto, bases de
datos ni secretos. Todas están en ficheros de test o en el setup de test.

| # | Fichero | Defecto de test | Prueba |
|---:|---|---|---|
| F-01 | `Aplicacion/backend/modules/competencias/tests/fixtures/competencias_fixtures.py` | Las fixtures creaban `Inscripcion` y `Equipo` **sin** `promocion` ni `categoria`, que el contrato objetivo volvió **obligatorios** (`NOT NULL`). Fixtures nuevas `promocion` (global, `anio=2027`), `categoria` y `categoria_otra` | 45 **errores** → **0** |
| F-02 | `Aplicacion/backend/modules/competencias/tests/conftest.py` | Las fixtures nuevas no estaban **registradas** (el `conftest` importa los nombres uno a uno, patrón `TEST_ARCHITECTURE_CONTRACT` §3.3) | — |
| F-03 | `Aplicacion/backend/modules/salesianos_fest/tests/integration/test_asignacion_participante.py` | `NameError: name 'inscripcion' is not defined` — el test usaba `inscripcion.promocion_id` sin pedir la fixture | 1 **failed** → **PASS** |
| F-04 | `Aplicacion/backend/modules/administracion/tests/conftest.py` | Exportaciones **obsoletas**: faltaban `promocion` y `categoria` (exigidas por las fixtures del dueño) y `inscripcion_sin_pagos` chocaba con la UNIQUE `(edición, responsable, paquete)` al convivir con `inscripcion` ⇒ fixture **local** con otro responsable | 3 **errores** → **0** |
| F-05 | `Aplicacion/backend/modules/administracion/tests/integration/test_admin_operacion.py` | Construía `EstadoOperativoPagoService(...)` sin el puerto `activacion_service` que **XCT-03** añadió ⇒ stub mínimo añadido | 2 **errores** → **0** |
| F-06 | `Aplicacion/frontend/src/lib/__tests__/route-map.guard.test.ts` | **Defecto de plataforma**: las excepciones declaradas se comparaban contra `relative()` **sin normalizar**, de modo que en Windows **nunca** aplicaban. Allowlist de endpoints del backend **obsoleta** (10 ficheros de `services/`). Exclusión de los ficheros de datos de `__tests__/` | 13 **failed** → **532 passed** |
| F-07 | `Aplicacion/frontend/src/components/shell/__tests__/shell.test.tsx` | El harness renderizaba el shell **sin `TooltipProvider`** (que la aplicación **sí** monta en `src/providers/AppProviders.tsx`). Consulta ambigua del enlace «Resumen» | 10 **failed** → **17 passed** |
| F-08 | `Aplicacion/frontend/vitest.setup.ts` | jsdom **no implementa `IntersectionObserver`** y el índice de anclas lo usa; el setup compartido cubría `ResizeObserver`, puntero, `scrollIntoView` y `matchMedia`, pero **no** el observador de intersección | 3 **failed** → **PASS** |
| F-09 | `Aplicacion/frontend/src/features/public/__tests__/informacion-indice.test.tsx` | La vista usa un hook de TanStack Query ⇒ el harness necesita `QueryClientProvider` (patrón ya establecido en `inscripciones-admin-estados.test.tsx`) | 3 **failed** → **PASS** |
| F-10 | 10 suites de frontend (ver §5.1) | Consultas **ambiguas**: `getByText` exige unicidad y el componente publica la etiqueta legitimamente más de una vez (insignia + título, fila + tarjeta) ⇒ `getAllBy…(…)[0]` | 26 **failed** → **0** |

### 5.1 Ficheros de F-10

`src/features/cuenta/__tests__/cuenta-estados.test.tsx` ·
`src/features/competencias/__tests__/competencias-estados.test.tsx` ·
`src/features/marketplace/__tests__/marketplace-estados.test.tsx` ·
`src/features/patrocinadores/__tests__/patrocinadores-estados.test.tsx` ·
`src/features/validaciones/__tests__/validaciones-estados.test.tsx` ·
`src/features/admin/inscripciones/__tests__/inscripciones-admin-estados.test.tsx` ·
`src/features/admin/participantes/__tests__/participantes-admin-estados.test.tsx` ·
`src/features/admin/pagos/__tests__/pagos-admin-estados.test.tsx` ·
`src/features/admin/equipos/__tests__/equipos-admin-estados.test.tsx` ·
`src/features/inscripciones/__tests__/inscripcion-estados.test.tsx`

Un caso de F-10 merece nombre propio: en
`equipos-admin-estados.test.tsx` la cifra visible `"6 / 7–10"` se compone de
**dos** nodos de texto (`"6"` y `" / 7–10"`, el segundo dentro de un
`aria-hidden`), de modo que **ninguna** expresión regular sobre el texto
directo del nodo podía encontrarla. La aserción mira ahora el `textContent`
del elemento que la compone.

---

## 6. Libro de fallos: clasificación, dueño y evidencia

Leyenda: **REGRESIÓN DE PAQUETE** = defecto de producto introducido por un
paquete del rebuild, con dueño identificable · **BASELINE EXISTENTE** =
fallo ya registrado en el oráculo · **ENTORNO** = limitación del entorno ·
**DEPENDENCIA BLOQUEADA** = falta el registro/cableado de otro actor.

### 6.1 Backend (1 fallo + 2 errores de recolección)

| # | Test / error | Clase | Causa raíz | Dueño | Corrección |
|---:|---|---|---|---|---|
| B-F1 | `modules/salesianos_fest/tests/e2e/test_inscripcion_controller.py::test_la_cotizacion_es_publica_y_devuelve_el_token_de_concurrencia` | **REGRESIÓN DE PAQUETE** | `AttributeError: 'CotizacionResult' object has no attribute 'paqueta_id'. Did you mean: 'paquete_id'?` en `modules/salesianos_fest/presentation/presenters/catalogo_presenter.py:110` (`UUID(result.paqueta_id)`) — el presenter lee un campo que el resultado no tiene. **HTTP 500** en `POST /cotizaciones` | **DOM-01 / A0** — `modules/salesianos_fest/**` es raíz de **producción**, **prohibida** para VER-01 | **NO corregido.** Corrección de una línea: `result.paqueta_id` → `result.paquete_id` |
| B-F2 | `modules/administracion/tests/integration/test_admin_auditoria.py` (colección) | **DEPENDENCIA BLOQUEADA** | `modules.administracion` **no** está en `INSTALLED_APPS`: sus modelos no se pueden importar (`doesn't declare an explicit app_label`) | **A0 — `A0-XCT02-01`** | **NO corregido** (config compartida, raíz prohibida). Con overlay: **15/15 PASS** |
| B-F3 | `modules/administracion/tests/integration/test_admin_operacion.py` (colección) | **DEPENDENCIA BLOQUEADA** | ídem | **A0 — `A0-XCT02-01`** | ídem |

### 6.2 Frontend (40 fallos)

| # | Suite / test | Clase | Causa raíz | Dueño |
|---:|---|---|---|---|
| 1-5 | `admin/operaciones/__tests__/operaciones-estados.test.tsx` — `ConfirmacionIrreversible.tsx`, `ListaOperativa.tsx`, `MarcoOperativo.tsx`, `PaginacionOperativa.tsx`, `VeredictoOperativo.tsx` «usan objetivos táctiles de 44 px» | **REGRESIÓN DE PAQUETE** | Los ficheros **NO contienen** `min-h-11` (44 px). `MarcoOperativo.tsx` **no tiene ni un botón**: la aserción sobre su fuente es vacía | **UI-04 / A7** |
| 6-9 | `pases/__tests__/pases-estados.test.tsx` — `ResumenCompra.tsx`, `TarjetaPase.tsx`, `PasesView.tsx`, `PaseGestionarView.tsx` «44 px» | **REGRESIÓN DE PAQUETE** | ídem: sin `min-h-11` | **UI-03 / A7** |
| 10 | `marketplace/__tests__/marketplace-estados.test.tsx` — `PedidoSeguimientoView.tsx` «44 px» | **REGRESIÓN DE PAQUETE** | ídem | **API-03 / A7** |
| 11-14 | `validaciones/__tests__/validacion-contrato.test.ts` — las 4 formas congeladas | **REGRESIÓN DE PAQUETE** | El **espejo Zod** de `features/validaciones/schemas/validacion.schema.ts` **no** acepta las formas congeladas de `FR-05` §3.1/§3.2 | **XCT-01 / A7** (el espejo es producción) |
| 15 | `validaciones/__tests__/validacion-mirrors.test.ts` — «el derecho de entrada se REUSA del dueño del lote» | **REGRESIÓN DE PAQUETE** | El espejo no modela la referencia al derecho del dueño | **API-05 / A7** |
| 16 | `admin/auditoria/__tests__/auditoria-admin-estados.test.tsx` — «el espejo RECHAZA un acta con el contexto crudo» | **REGRESIÓN DE PAQUETE** | El espejo Zod del acta **acepta** el contexto crudo que el contrato exige sanear | **XCT-02 / A7** |
| 17 | `auth/__tests__/identidad-sesion-integration.test.ts` — «la entrada de la confirmación declara sus campos y sus límites» | **REGRESIÓN DE PAQUETE** | El espejo de la confirmación **acepta** una carga que el contrato declara inválida | **FND-03 / A7** |
| 18 | `pase.service.test.ts` — «el token nunca viaja en la query string» + «la lectura de la compra viaja con el token en la cabecera» | **REGRESIÓN DE PAQUETE** | `ErrorContratoPase: La respuesta del servidor no cumple el contrato esperado.` — el cliente y el presenter no hablan el mismo idioma | **API-03 / A7** |
| 19 | `pase.service.test.ts` — «una edición ausente es la misma entrada que ninguna» | **REGRESIÓN DE PAQUETE** | La factoría de query keys emite `['pase','catalogo',{}]` y el test espera `['pase','catalogo']` | **FND-08 / A7** |
| 20 | `marketplace.service.test.ts` — «un filtro ausente es la misma entrada que ninguno» | **REGRESIÓN DE PAQUETE** | misma deriva de query keys (`['marketplace','catalogo',…(2)]` vs `…(1)`) | **FND-08 / A7** |
| 21 | `marketplace.service.test.ts` — «el detalle se pide por el identificador del producto» | **REGRESIÓN DE PAQUETE** | `ErrorContratoMarketplace` — la envoltura del presenter y el espejo Zod no coinciden | **API-03 / A7** |
| 22-24 | `inscripciones/__tests__/inscripcion-estados.test.tsx` — «un 422 deja el formulario intacto…», «el error del catálogo es recuperable…», `inscripcion-detalle.test.tsx` «con error ofrece reintentar…» | **REGRESIÓN DE PAQUETE** | El texto del servidor **«El servicio de inscripciones no está disponible.»** y «El nombre del equipo es demasiado largo.» **no se renderizan**; la acción **«Reintentar»** no existe en ese estado | **API-02 / A7** |
| 25 | `cuenta/__tests__/cuenta-estados.test.tsx` — «el error ofrece reintentar» | **REGRESIÓN DE PAQUETE** | `MisInscripcionesView` **no** acepta el callback `reintentar` (el patrón `accion={reintentar ? {label:"Reintentar"} : undefined}` de `PasesView`/`TiendaCatalogoView` no está en la vista de la cuenta) ⇒ el estado de error **no** ofrece reintento | **API-01 / A7** |
| 26 | `cuenta/__tests__/cuenta-responsive.test.ts` — `ListaCompras.tsx` «marca cada columna con scope» | **REGRESIÓN DE PAQUETE** | 6 cabeceras con `scope` donde el test espera 7 | **API-01 / A7** |
| 27 | `cuenta/__tests__/cuenta-responsive.test.ts` — `ListaInscripciones.tsx` «marca cada columna con scope» | **REGRESIÓN DE PAQUETE** | 5 donde el test espera 6 | **API-01 / A7** |
| 28 | `cuenta/__tests__/cuenta-responsive.test.ts` — `MisCompraDetalleView.tsx` «no nombra un estado del proveedor» | **REGRESIÓN DE PAQUETE** | La vista contiene el literal `settlement_status` | **API-01 / A7** |
| 29 | `inscripciones/__tests__/inscripcion-responsive.test.ts` — `PanelParticipantes` «marca cada columna con scope» | **REGRESIÓN DE PAQUETE** | 5 donde el test espera 6 | **API-02 / A7** |
| 30 | `public/__tests__/recuperar-compra-form.test.tsx` — «un correo con formato inválido no pasa la validación» | **REGRESIÓN DE PAQUETE** | El mensaje «Ese correo no tiene un formato válido.» **no se renderiza** | **UI-01 / A7** |
| 31 | `patrocinadores/__tests__/patrocinadores-estados.test.tsx` — «la ficha del patrocinador no tiene ninguna cifra» | **REGRESIÓN DE PAQUETE** | La ficha **sí** muestra cifras (`/aportaci/i`, `/comisi/i` presentes) | **UI-05 / API-05** |
| 32 | `patrocinadores/__tests__/patrocinadores-estados.test.tsx` — «una pieza sin archivo legible muestra el hueco» | **REGRESIÓN DE PAQUETE** | El texto «no está disponible en el servidor» **no se renderiza** | **UI-05 / API-05** |
| 33 | `admin/pagos/__tests__/pagos-admin-estados.test.tsx` — «cada fila tiene UN estado comprensible, el del backend» | **REGRESIÓN DE PAQUETE** | El texto «El pago todavía no ha sido confirmado.» **no se renderiza** | **API-04 / A8** |
| 34-36 | `genericForm/__tests__/generic-form.lifecycle.test.tsx` — «hands the File over untouched», «lets Zod own the coercion», «calls setError EXACTLY ONCE per field» | **REGRESIÓN DE PAQUETE** | El `GenericForm` **no** invoca el mapper de alta (`vi.fn()` **0 llamadas**) ni propaga los errores de campo (`setError` **0 llamadas**) | **FND-07 / A7** |
| 37-38 | `components/__tests__/tokens.test.ts` — `searchable-select.tsx` (`radix-popover-trigger-width`) y `tooltip.tsx` (`radius-xs`) «no lee variables inexistentes» | **REGRESIÓN DE PAQUETE** | Dos variables CSS **leídas y no declaradas**: `--radius-xs` (token de diseño ausente en `globals.css`) y `--radix-popover-trigger-width` (variable de runtime de Radix, no un token) | **FND-06 / A7** |
| 39 | `portada/__tests__/portada-viewport.test.ts` — «el navbar consume el token y no un alto suelto» | **REGRESIÓN DE PAQUETE** | El navbar **no** usa `h-[var(--portada-chrome-height)]` | **UI-01 / FND-06** |

**Total: 40 fallos de frontend pendientes** (las filas agrupadas `1-5`, `6-9`,
`11-14`, `22-24` y `34-36` suman sus filas). Los **26** fallos de ambigüedad
de este mismo conjunto **sí** quedaron corregidos en §5 (F-10): el recuento
**antes** de este packet era de **86** fallos de frontend y ahora es de **40**.

### 6.3 Baseline / entorno / dependencias que NO son regresión

| Ítem | Clase | Evidencia |
|---|---|---|
| `manage.py check` y `makemigrations --check --dry-run` con settings por defecto → `DB_NAME` | **BASELINE EXISTENTE (B7)** | `BL-04` §3.5 · idéntico en GOV-02, FND-01…FND-05, DOM-*, XCT-* |
| La **lane PostgreSQL** de `BL-05` §2 (`--ds=<postgres>`) | **ENTORNO** | No hay PostgreSQL disponible: los casos de concurrencia (`QA-V02`, `QA-I05`) corren sobre SQLite, donde `select_for_update` es un **NO-OP**. El riesgo que XCT-01 §7.1 declaró **sigue ABIERTO** |
| `pytest.ini` con `--nomigrations` | **BASELINE EXISTENTE** | `BL-04` §5 lo declara raíz prohibida; VER-01 no lo tocó. El replay de migraciones se hizo **fuera** de pytest (`B13`…`B17`) |
| `admin.E108` (`PaqueteAdmin.list_display[3] → cupos_incluidos`) | **RESUELTO** | XCT-02 lo declarara preexistente; `B9`/`B11` lo dan por **verde** hoy |

---

## 7. Inventario de endpoints y drift de consumidores (step 4)

Generado **desde el registro vivo** (`config/api.py` → `api.get_openapi_schema()`)
y contrastado con los endpoints que **consumen** los `services/*.ts` del
frontend (mapeo: el navegador llama `/backend/<path>` y nginx lo reescribe a
`/api/<path>` — `proxy/nginx.conf` §`location /backend/`).

| Magnitud | Valor |
|---|---:|
| Controllers registrados | **15** (`NinjaJWTDefaultController`, `EdicionController`, `PersonaController`, `AuthController`, `PagosController`, `CatalogoController`, `InscripcionController`, `ProductoController`, `PedidoController`, `InventarioController`, `PaseController`, `AdminPaseController`, `CompetenciasController`, `PatrocinadorController`, `ValidacionController`) |
| Rutas vivas | **62** |
| Endpoints consumidos por el frontend (con prefijo resuelto) | **28** |
| **DRIFT A** · endpoints consumidos **sin** ruta registrada | **8** |
| **DRIFT B** · rutas registradas **sin** consumidor estático | **42** |
| Rutas declaradas en el ledger de GOV-01 | **18** |

### 7.1 DRIFT A — el frontend llama a rutas que NO existen (BLOQUEANTE)

| Endpoint consumido | Ruta viva | Dueño | Petición abierta |
|---|---|---|---|
| `/administracion/resumen` | `/api/administracion/resumen` | **A0** | **`A0-XCT02-01`** |
| `/administracion/auditoria` | `/api/administracion/auditoria` | **A0** | **`A0-XCT02-01`** |
| `/administracion/inscripciones` | `/api/administracion/inscripciones` | **A0** | **`A0-XCT02-01`** |
| `/administracion/equipos` | `/api/administracion/equipos` | **A0** | **`A0-XCT02-01`** |
| `/administracion/pagos` | `/api/administracion/pagos` | **A0** | **`A0-XCT02-01`** |
| `/administracion/participantes` | `/api/administracion/participantes` | **A0** | **`A0-XCT02-01`** |
| `/administracion/personas` | `/api/administracion/personas` | **A0** | **`A0-XCT02-01`** |
| `/cotizaciones` | `/api/cotizaciones` | **A0** | **`A0-API02-09`** |

**Siete** de las ocho son el **mismo** hueco: `modules.administracion` no está
en `INSTALLED_APPS` y sus seis controllers no están registrados
(`A0-XCT02-01`). El servicio `admin.service.ts` del frontend los consume
**hoy**: esas siete llamadas responden **404**. La octava es
`CotizacionController`, que **sí** está implementado pero **no** registrado
(`A0-API02-09`), y además arrastra el defecto de producto B-F1.

**Nota de honestidad del inventario:** el barrido de DRIFT B (42) es una
**cota inferior**, no un inventario exacto: sólo detecta literales y
plantillas resolubles estáticamente, de modo que una ruta construida por
concatenación no aparece. Las 42 rutas incluyen las que **no** debe consumir
nadie (`/api/token/**` de JWT, `/api/pagos/izipay/notificacion` servidor-a-servidor)
y las que sí se consumen por una vía no detectable. **No se afirma drift donde
no se ha medido.**

### 7.2 Reconciliación del cableado (estado real ≠ estado escrito)

`evidence/foundations/A0-wiring-validation.md` (2026-11-19) y las filas de
`STATE.md` de `DOM-05`, `DOM-06`, `DOM-07`, `DOM-08`, `XCT-01` y `XCT-03`
afirman que **«A0 wiring NOT applied»**. **Eso es hoy FALSO**: el árbol real
registra `competencias`, `patrocinadores`, `validaciones` y `notificaciones`
en `INSTALLED_APPS`, y registra `PedidoController`, `InventarioController`,
`CompetenciasController`, `PatrocinadorController` y `ValidacionController`
en `config/api.py`. **VER-01 lo ha medido en runtime** (`B3`: 62 rutas vivas;
`B17`: `makemigrations --check` verde **con** `administracion` registrada).

**Lo que SIGUE sin cablear (una sola app):** `modules.administracion`
(`A0-XCT02-01`) y `CotizacionController` (`A0-API02-09`).

---

## 8. Ficheros cambiados por este packet

**Backend (5)** — todos dentro de `modules/*/tests/**` (defectos de test):

| Fichero | Acción |
|---|---|
| `Aplicacion/backend/modules/competencias/tests/fixtures/competencias_fixtures.py` | modificado (F-01) |
| `Aplicacion/backend/modules/competencias/tests/conftest.py` | modificado (F-02) |
| `Aplicacion/backend/modules/salesianos_fest/tests/integration/test_asignacion_participante.py` | modificado (F-03) |
| `Aplicacion/backend/modules/administracion/tests/conftest.py` | modificado (F-04) |
| `Aplicacion/backend/modules/administracion/tests/integration/test_admin_operacion.py` | modificado (F-05) |

**Frontend (14)** — todos dentro de `src/**/__tests__/**` o el setup de test:

| Fichero | Acción |
|---|---|
| `Aplicacion/frontend/vitest.setup.ts` | modificado (F-08) |
| `Aplicacion/frontend/src/lib/__tests__/route-map.guard.test.ts` | modificado (F-06) |
| `Aplicacion/frontend/src/components/shell/__tests__/shell.test.tsx` | modificado (F-07) |
| `Aplicacion/frontend/src/features/public/__tests__/informacion-indice.test.tsx` | modificado (F-09) |
| `Aplicacion/frontend/src/features/cuenta/__tests__/cuenta-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/competencias/__tests__/competencias-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/marketplace/__tests__/marketplace-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/patrocinadores/__tests__/patrocinadores-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/validaciones/__tests__/validaciones-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/admin/inscripciones/__tests__/inscripciones-admin-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/admin/participantes/__tests__/participantes-admin-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/admin/pagos/__tests__/pagos-admin-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/admin/equipos/__tests__/equipos-admin-estados.test.tsx` | modificado (F-10) |
| `Aplicacion/frontend/src/features/inscripciones/__tests__/inscripcion-estados.test.tsx` | modificado (F-10) |

**Artefactos (2):** este fichero (creado) y `Aplicacion/task/salesianos-fest-rebuild/STATE.md` (modificado).

**Fuera del repositorio (temporal, no versionado, nada commiteado):**
`%TEMP%\opencode\ver01\{ver01_admin_overlay.py, ver01_migrate_overlay.py,
endpoint_inventory.py, fix_ambiguous_queries.py, fix_ambiguous_queries_2.py,
dbg.py}` y las capturas de salida `*.txt`.

**Cero** ficheros de `contract/**`, `Aplicacion/plan/**`,
`Aplicacion/documentacion/**`, de los **raíces congelados** (`backend/**`,
`frontend/**`, `worker/**`, `proxy/**`), de `.env*` o de bases de datos del
repositorio fueron tocados. **Cero** ficheros de producción fueron tocados.

---

## 9. Rollback

1. Revertir los **5** ficheros de test del backend (`git checkout` de esos
   paths, o el diff inverso) — la corrección de `modules/salesianos_fest/tests/integration/test_asignacion_participante.py` convive con una modificación **preexistente** de otro agente: revertir el fichero **entero** revertiría también su trabajo ⇒ revertir **sólo** las 3 líneas de la firma.
2. Revertir los **14** ficheros de test del frontend.
3. Borrar este fichero y revertir la transición de `STATE.md`.
4. En Engram: restaurar `sdd/salesianos-fest-rebuild/state` y `…/apply-progress`.
5. Los overlays de `%TEMP%` se pueden borrar sin efecto.

**Punto de rollback:** **`2c411cdfc062714cfa7ff39765c4357ddf8267e2`** ("betha 6")
— el HEAD real en el momento del cierre, que **ya existía** cuando este packet
empezó (commit del 2026-11-19 22:58) y que **no cambió**: VER-01 **no creó
ningún commit**. **Nunca** revertir ni resetear ese commit.

> **Aviso sobre el SHA que heredan los paquetes.** Todas las transiciones
> anteriores apuntan a `f3df5401c56b61c340f257e67a5a306904e9e670` ("betha 4"),
> pero **ese objeto NO existe en este repositorio** (`git cat-file` → *"could
> not get object info"*). El SHA real de "betha 4" es
> `f3df5401c56b41c340f257e67d5a306904a9e670` (con `b41c` y `d5a3`). El typo está
> **propagado** por los paquetes GOV-00…XCT-03 y por el `STATE.md`; **A0 debe
> corregirlo** en el próximo paquete que toque ese estado, porque un rollback
> que apunte a un SHA inexistente **no se puede ejecutar**.

**La historia de los pagos NUNCA se borra en un rollback:** un cobro, un
derecho habilitado y una activación registrada son hechos (`RN-C08`,
`RN-P08`). Un rollback del CÓDIGO no deshace un cobro que la base ya
registró.

---

## 10. Bloqueos que quedan y dueño

| Id | Bloqueo | Dueño | Bloquea |
|---|---|---|---|
| **B-F1** | `catalogo_presenter.py:110` lee `result.paqueta_id`; el resultado expone `paquete_id` ⇒ **HTTP 500** en `POST /cotizaciones` | **DOM-01 / A0** | El flujo de cotización del alta |
| **A0-XCT02-01** | `modules.administracion` no registrada ⇒ **7 endpoints administrativos que el frontend YA consume NO existen** y 2 ficheros de test **no se pueden recolectar** | **A0** | `VER-02`, el panel administrativo, `RT-ADM-01/02` + las seis superficies |
| **A0-API02-09** | `CotizacionController` no registrado ⇒ `POST /cotizaciones` no existe | **A0** | El token de concurrencia de la cotización |
| **UI-04/UI-03/API-03** | 10 componentes sin objetivo táctil de 44 px (`min-h-11`) | **A7** | La auditoría de accesibilidad de cinco anchos |
| **A7 (espejos)** | 7 fallos de espejo Zod (validaciones, auditoría, identidad, pase, marketplace) | **A7** | El contrato en el navegador |
| **FND-08** | 3 fallos de deriva de query keys (pase, marketplace) | **A7** | La invalidación de caché |
| **FND-07** | 3 fallos del `GenericForm` (el mapper de alta no se invoca; `setError` no se llama) | **A7** | El alta de formularios |
| **API-01/API-02** | 7 fallos de contrato de UI (reintento ausente ×2, copy del servidor ×3, `scope` de columnas ×2) | **A7** | La aceptación de las superficies de cuenta e inscripción |
| **API-04 / API-05 / UI-05 / UI-01 / FND-06** | 6 fallos de contrato de UI (copy del pago, ficha del patrocinador ×2, piece rota, navbar sin token, variables CSS ×2) | **A7** | La aceptación de esas superficies |
| **A0 (Biome)** | El techo del baseline (105/93) está **superado** con creces (441/110 sobre 714 ficheros): los paquetes que escribieron el frontend **nunca** corrieron Biome | **A0 + A7** | La puerta de lint del objetivo |
| **Entorno** | La **lane PostgreSQL** no se pudo ejecutar: los casos de concurrencia (`QA-V02`, `QA-I05`) se validaron sobre SQLite, donde `select_for_update` es un NO-OP | **A0 + A9** | La garantía de serialización |

---

## 11. ¿Queda VER-02 desbloqueado?

> **SUPERADA por la §12** (re-verificación sobre el árbol actual, tras las cuatro
> correcciones). Este apartado conserva el veredicto de la **primera** medición; el
> **vigente** es el de la §12.7: **VER-02 queda DESBLOQUEADO para su alcance**, con dos
> condiciones de bloqueo explícitas (el techo de Biome y la lane PostgreSQL).

**NO.** *(veredicto de la primera medición)*

El packet de este documento dice: *«[VER-02] only when regressions are cleared
or explicitly blocking»*. Las **regresiones** (los fallos nuevos que este
packet podía corregir en raíces de test) **están corregidas**: 45 errores
backend + 2 fallos backend + 46 fallos frontend de test → **0**. El resto
**es explícitamente bloqueante**:

- **1 defecto de producto** en el backend (B-F1) que rompe la cotización;
- **40 fallos de producto** en el frontend, con dueño identificado;
- **2 dependencias bloqueadas** de cableado (A0) que hacen que **7 rutas que
  el frontend consume no existan** y que la suite del backend **no se pueda
  recolectar**;
- **1 lane de verificación** (PostgreSQL) que no se pudo ejecutar.

El **drift de endpoints** está **medido y clasificado** (8 rutas consumidas
sin ruta registrada, con su petición A0 abierta), y por tanto **explícitamente
bloqueante**: no está «resuelto».

**VER-02 (`VER-02-e2e-ux-security.md`) queda BLOQUEADO** hasta que:
1. A0 aplique `A0-XCT02-01` y `A0-API02-09` (y el guardián de registro se
   amplíe en el **mismo** cambio, como exige `A0-wiring-validation` §6);
2. DOM-01/A0 corrija `catalogo_presenter.py:110`;
3. los dueños de UI/frontend cierren los 40 fallos de §6.2;
4. se ejecute la **lane PostgreSQL** para la concurrencia.

### 11.1 Reconciliación de estado (lo que este packet deja escrito)

`STATE.md` y los topics de Engram pasan a registrar **la verdad medida**:

- `VER-01` → **`verification_required`** (no `completed`): ejecutó, clasificó
  y corrigió lo que le era propio, pero **no** cerró los defectos de producto;
- las filas que decían **«A0 wiring NOT applied»** (DOM-05, DOM-06, DOM-07,
  DOM-08, XCT-01, XCT-03) se **corrigen**: el cableado **sí** está aplicado
  hoy, salvo `modules.administracion` (`A0-XCT02-01`) y
  `CotizacionController` (`A0-API02-09`);
- `VER-02` y `VER-03` siguen **`pending`** y **bloqueados** por lo anterior.


---

## 12. Re-verificación tras las correcciones (2026-11-20, segunda pasada)

Esta sección **SUSTITUYE** los números de las §2 y §3 para el árbol actual. Las
correcciones aplicadas **en paralelo** a este packet —
[`CORR-VER01`](../../evidence/corrections/CORR-VER01-backend-blockers.md) (#11484) ·
[`COR-01`](../../evidence/corrections/COR-01-frontend-contract-foundation.md) (#11483) ·
[`CORR-VER01-A0`](../../evidence/corrections/CORR-VER01-A0-residuales-backend.md) (#11488) ·
[`COR-02`](../../evidence/corrections/COR-02-frontend-presentation-accessibility.md) (#11490) —
**superaron** los hallazgos de las §6.1/§6.2 de la primera pasada. Este packet
**no** se apoyó en sus notas: **re-midió** el árbol actual.

### 12.1 Lo que las correcciones cerraron (verificado contra el código actual)

| Corrección | Qué cerró | Verificación en el árbol actual |
|---|---|---|
| **CORR-VER01** (#11484) | **B-F1** (`catalogo_presenter.py:110` leía `result.paqueta_id`) | `catalogo_presenter.py:110` → `paquete_id=UUID(result.paquete_id)` |
| | **A0-XCT02-01** (`modules.administracion` sin registrar) | `config/settings/base.py:118` → `"modules.administracion"` en `LOCAL_APPS`; `:325` → `AdministracionModule` en `INJECTOR_MODULES`; **6** controllers de `administracion` registrados en `config/api.py` |
| | **A0-API02-09** (`CotizacionController` sin registrar) | `config/api.py:66` importa y `:216` registra `CotizacionController` |
| | El allowlist del guardián de registro (5 listas cerradas) | `core/tests/integration/test_registration_extension.py` alineado con el registro real |
| **COR-01** (#11483) | **15** fallos de contrato/fundación del frontend | `query-keys.ts` (`buildQueryKey` sin objeto de parámetros), `auditoria-admin.schema.ts` (`.strict()`), `identidad.schema.ts` (`genero` = `z.enum(["M","F"])`) + 5 ficheros de test |
| **CORR-VER01-A0** (#11488) | **R-1** (drift de `salesianos_fest`) · **R-2** (`PRECIO_CAMBIADO` sin prosa) | `core/contract_versions.py:80` → `"salesianos_fest": "2.0.0"` · `core/exceptions.py:779` → `PUBLIC_ERROR_MESSAGES["PRECIO_CAMBIADO"]` |
| **COR-02** (#11490) | **25** fallos de presentación/accesibilidad del frontend | 28 ficheros de producción + 1 de dato de prueba (§2.1–§2.5 de su evidencia) |

### 12.2 Comandos / códigos de salida (ÁRBOL ACTUAL)

**Backend** (workdir `Aplicacion/backend`, **sólo** `uv run --group dev`):

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| R1 | `python -m pytest modules core -q` (suite combinada) | **0** | **974 passed**, 665 warnings, 182.69 s |
| R2 | `python -m pytest --collect-only -q` (raíz) | **0** | **974 collected**, **0 errores de recolección** (la §2.1 B1 medía *exit 2 · 690 collected + 2 errores*) |
| R3 | `python -m pytest modules/commerce/tests modules/pagos/tests modules/notificaciones/tests -q` (**lane de pagos**) | **0** | **115 passed**, 35 warnings, 20.49 s |
| R4 | `python -m pytest core/tests/integration/test_media_despliegue.py -q` (**medios y despliegue**) | **0** | **6 passed** |
| R5 | `python -m pytest core/tests/integration/test_registration_extension.py core/tests/integration/test_a0_cableado_administracion_cotizacion.py -q` (**guardián de registro**) | **0** | **19 passed** |
| R6 | `python manage.py check --settings=config.settings.test` | **0** | `System check identified no issues (0 silenced).` |
| R7 | `python manage.py makemigrations --check --dry-run --settings=config.settings.test` | **0** | `No changes detected` |
| R8 | `python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced).` |
| R9 | `python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| R10 | `python manage.py check` (settings por defecto = producción) | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **baseline ambiental B7**, idéntico a la §2.1 B7 |
| R11 | `python manage.py makemigrations --check --dry-run` (por defecto) | **1** | mismo `DB_NAME` — **baseline ambiental B7** |

**Frontend** (workdir `Aplicacion/frontend`):

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| R12 | `npx tsc --noEmit` | **0** | **LIMPIO** — 0 diagnósticos |
| R13 | `npx vitest run` (suite completa) | **0** | **52 files passed (52)** · **2276 passed (2276)** · **0 fallos** — antes: `20 files failed / 40 failed \| 2235 passed` |
| R14 | `npx biome check .` (**exigido por el packet**) | **1** | `Checked 714 files` · **445 errors** · **110 warnings** — ver §12.4 |

**Despliegue:**

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| R15 | `docker compose config --quiet` | `Aplicacion` | **0** | compose válido |

**Inventario de endpoints (regenerado desde el registro vivo):**

| Magnitud | Primera pasada | **Ahora** |
|---|---:|---:|
| Controllers registrados | 15 | **22** |
| Rutas vivas | 62 | **75** |
| Endpoints consumidos por el frontend | 28 | **28** |
| **DRIFT A** · consumidos SIN ruta registrada | **8** | **0** ✅ |
| DRIFT B · registradas SIN consumidor estático | 42 | **47** (cota inferior) |

### 12.3 El fallo que queda: **la lane PostgreSQL** — BLOQUEO DE ENTORNO, no de código

**Existe** un proceso `postgres.exe` escuchando en el puerto 5432, pero **NO existe un
entorno PostgreSQL de prueba CONFIGURADO** para el objetivo:

| Comprobación | Resultado |
|---|---|
| `Aplicacion/backend/.env` | declara `USE_SQLITE` y `SQLITE_PATH`; **ninguna** variable `DB_*` |
| Módulo de settings para PostgreSQL en el objetivo | **ninguno**: `config/settings/` = `base`, `development`, `production`, `test` — y `test` está **fijado** a SQLite `:memory:` |
| Servicio `db` de `Aplicacion/docker-compose.yml` (`postgres:16-alpine`) | **no se puede levantar**: el demonio Docker **no está corriendo** (`//./pipe/dockerDesktopLinuxEngine` no existe) |
| Conexión con las credenciales que declara el propio compose (`salesianos_db` / `salesianos_user` / `changeme`) por `127.0.0.1` **y** por `localhost` | **fallo**: `OperationalError` vacío (el servidor cierra durante la autenticación) |

⇒ **NO se ejecutó** la lane PostgreSQL de `BL-05` §2 y **NO se cuenta como fallo de
código**. Se registra como **BLOQUEO DE ENTORNO**. El riesgo que XCT-01 §7.1 declaró
sigue **ABIERTO**: los casos de concurrencia (`QA-V02`, `QA-I05`) se validaron sobre
SQLite, donde `select_for_update` es un **NO-OP**, de modo que la serialización real
(`RN-C02`, precio-vs-cotización) **no está probada** en un motor con bloqueo de filas.

### 12.4 Biome: el techo, clasificado con precisión

El packet **exige** `npx biome check .`, así que se ejecutó. El techo congelado
(`BL-04` §3.3) es **105 errors / 93 warnings** sobre **566** ficheros (raíz congelada).

| Medición | Errores | Avisos | Ficheros |
|---|---:|---:|---:|
| Techo del baseline (raíz congelada) | 105 | 93 | 566 |
| VER-01, primera pasada (2026-11-20 ~02:5x) | 441 | 110 | 714 |
| **VER-01, segunda pasada (ahora)** | **445** | **110** | **714** |

**Clasificación: REGRESIÓN CONTRA EL TECHO, HEREDADA — no introducida por este packet ni
por las correcciones.** La prueba es una comparación **fichero a fichero contra `HEAD`**:
en los **29** ficheros que las correcciones tocaron, el recuento de errores de Biome
**bajó de 45 a 38 (−7)**. Las **4** diagnósticos *nuevos* dentro de esos ficheros (3 ×
`assist/source/organizeImports` por el alias deliberado `TableHeader as Thead` de COR-02, y
1 × `suppressions/unused` por su edición de `InscripcionWizardView`) están **más que
compensados** por los 11 que eliminaron. El **+4** del árbol viene de trabajo
concurrente **fuera** de esos ficheros.

**Consecuencia:** la puerta de lint del objetivo está **ROJA** (445 ≫ 105) y **lo
seguirá estando** aunque se corrigieran las 4 diagnósticos nuevas. **No es una
corrección de VER-01**: el código es de producción de otros paquetes (raíz prohibida para
este packet) y la deuda es de **todo** el frontend del rebuild, que **nunca corrió Biome**
(la restricción de apply lo prohibía). **Dueño: A0 + A7.**

### 12.5 Lo que este packet **NO** corrigió en esta segunda pasada

**Ninguna regresión nueva que corregir.** Los 4 diagnósticos nuevos de Biome están
compensados por 11 eliminados en los mismos ficheros, y la puerta sigue roja por la
deuda heredada (§12.4). No se tocó **código de producción de ningún paquete**.

### 12.6 El typo del SHA de rollback: petición precisa a A0

Este packet **ya corrigió** el SHA en **su propia** evidencia y en **su propia**
transición (§9 y la transición del `STATE.md`): ambos usan
**`2c411cdfc062714cfa7ff39765c4357ddf8267e2`** ("betha 6"), que **existe** y **no cambió**
(VER-01 no creó ningún commit).

Queda **una** copia del typo, y está en **evidencia histórica de otro packet**:

| Ubicación | Contenido | Por qué NO se corrige aquí |
|---|---|---|
| `STATE.md` línea **2603** (transición de **XCT-03**, `T-084`/`T-085`/`T-086`) | `**Rollback point:** \`f3df5401c56b61c340f257e67a5a306904e9e670\`` | Es la **transición de otro packet**: reescribirla cambiaría **evidencia histórica**. Además las transiciones de GOV-00…XCT-02 de la **fila** del tablero citan el mismo SHA con la misma forma corrupta |

**SHA real:** `f3df5401c56b41c340f257e67d5a306904a9e670` ("betha 4") — se verifica con
`git rev-parse f3df5401c56b41c340f257e67d5a306904a9e670`. El typo está en el
transcripción (`b61c340…` en vez de `b41c340…`, `e9e670` en vez de `a9e670`).

> **A0-VER01-01 (petición precisa).** Corregir el SHA de rollback en las **entradas
> históricas** que lo citan (`STATE.md` línea 2603 y las filas de GOV-00…XCT-02), por
> el SHA **real** `f3df5401c56b41c340f257e67d5a306904a9e670`, **dejando constancia** de la
> corrección (no un borrado silencioso: una entrada histórica que se corrige se marca
> como corregida, con el SHA bueno y la fecha). **Motivo:** un rollback que apunte a un
> objeto inexistente **no se puede ejecutar**, y es el punto de retorno que declara la
> mitad de los packets del rebuild.

### 12.7 Veredicto de VER-01 en el árbol actual

| Criterio de aceptación del packet | Estado |
|---|---|
| "Every failure is classified with baseline evidence and owner" | ✅ — las 41 de la primera pasada, clasificadas; **todas cerradas** por las cuatro correcciones salvo las de la §12.4 (Biome) |
| "new regressions block progress" | ⚠️ — **una** regresión contra el techo de Biome, **heredada** (§12.4), dueño A0 + A7. **Ninguna** introducida por este packet ni por las correcciones |
| "QA-C01-C03 and payment duplicate/retry/reconciliation behavior have real execution evidence" | ✅ — **R3** (115 passed) + **R13** (2276/2276) + §4 |
| "Endpoint inventory/consumer drift is resolved or explicitly blocking" | ✅ **RESUELTO**: DRIFT A = **0** (antes 8) · 22 controllers · 75 rutas |

**VER-01 NO se firma `completed`**, por dos razones honestas:

1. **La puerta de lint está ROJA contra el techo** (445/110 vs 105/93) — deuda
   **heredada** de todo el frontend del rebuild, en código de producción que este packet
   no puede tocar, con dueño **A0 + A7**.
2. **La lane PostgreSQL no se pudo ejecutar** (§12.3) — **bloqueo de entorno**, no de
   código: la garantía de concurrencia `QA-V02` / `QA-I05` sigue **sin probarse** en un
   motor con bloqueo de filas.

**VER-02 queda DESBLOQUEADO para su alcance** (e2e, UX y seguridad): todo lo que las
correcciones tocaron está **verde**, `tsc` **0**, `vitest` **2276/2276**, backend
**974/974**, **75** rutas vivas y **DRIFT A = 0**. Los dos puntos de la §12.7 se
**arrastran** como condiciones de bloqueo explícitas: el techo de Biome debe cerrarse
antes de la **firma**, y la lane PostgreSQL debe correrse antes del **corte de
producción**.
