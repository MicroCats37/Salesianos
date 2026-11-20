# A0 — Reconciliación del cableado compartido de DOM-03

**Reconciliación:** `A0` · **Paquete:** `DOM-03` (pases, beneficiarios y cortesía) ·
**Change:** `salesianos-fest-rebuild` · **Fecha:** 2026-11-19
**Naturaleza:** reconciliación del **cableado compartido** de un paquete de
dominio ya implementado y validado. **NO** es una reimplementación del
dominio y **NO** es un paquete nuevo.
**Estado:** `verification_required` — la verificación en runtime está
**DIFERIDA por instrucción explícita** (preferencia
`workflow/salesianos-sdd-apply-verification-deferred`): las pruebas se
ESCRIBEN pero **NO se ejecutan**.

**Comandos ejecutados durante esta reconciliación: NINGUNO.** No se ejecutó
`pytest`, `manage.py check`, `makemigrations`, `migrate`, `showmigrations`,
typecheck, lint, generación de OpenAPI ni ningún otro comando de verificación.
No se invocó el Python global ni el de `.venv`. No se activó ningún venv.
En su lugar se hizo una **REVISIÓN ESTÁTICA** de la fuente (§6).

---

## 1. Qué se reconcilió

| # | Petición de DOM-03 | Entregado | Fichero |
|---|---|---|---|
| A0-01 | Registrar `PaseController` y `AdminPaseController` | Los dos controllers registrados, al final de la lista (orden de prefijo sin solape) | `config/api.py` |
| A0-02 | `SCHEMA_VERSIONS["salesianos_fest"] = "1.2.0"` | Registro actualizado a `1.2.0` (paridad con el `SCHEMA_VERSION` declarado por el módulo) | `core/contract_versions.py` |
| A0-03 | Catalogar 9 códigos públicos | Catalogados: **4 ya existían** (ratificados, NO duplicados) + **5 nuevos** | `core/exceptions.py` |
| A0-04 | Catalogar 5 códigos de autenticación/autorización | Catalogados los **5** (2 nuevos + 3 de A0-03 ya contados) | `core/exceptions.py` |
| A0-05 | Ratificar `RT-PS-01`…`RT-PS-08` en el ledger + `SH-05` | **NO RATIFICADO** — el ledger y `SH-05` son evidencia de contrato de GOV-01/GOV-02, fuera de las raíces permitidas. Las rutas quedan **registradas y vivas** y el inventario de A0 las lleva explícitamente | — (§7 · `OD-A0R3-01`) |
| A0-06 | Ratificar la cabecera `X-Pase-Token` | **NO RATIFICADO** — decisión de canal provisional (`OD-DOM03-04`); el mecanismo está implementado y testeado | — (§7 · `OD-A0R3-02`) |
| A0-07 | Inventario de rutas **+10** (o +8) | **+8 rutas vivas** (10 handlers → 8 paths únicos: `RT-PS-07` y `RT-PS-08` comparten path; `RT-MD-01`/`RT-MK-02` ya compartían) | `core/tests/integration/test_registration_extension.py` |
| A0-08 | `*.sqlite3` en `.gitignore` | **NO APLICADO** — raíz fuera de las permitidas (heredado de FND-01…DOM-05) | — (§7) |
| A0-09 | Ruta de revocación de CORTESÍA | **NO INVENTADA** — el ledger no la declara; se registra como decisión abierta de producto + A0 | — (§7 · `OD-A0R3-03`) |
| A0-10 | Sincronizar la matriz física de tareas | **NO APLICADO** — fuera de las raíces permitidas (y el coordinador fusionará el estado compartido) | — (§7) |
| A0-11 | Unificar las DOS definiciones de "administrador" | **NO APLICADO** — `core.capacidades.es_admin` sigue siendo la ÚNICA autoridad; DOM-03 la usa. La divergencia se registra | — (§7 · `OD-A0R3-04`) |

**Además, y sólo porque el inventario de rutas de A0 es una ASERCIÓN sobre la
superficie VIVA**, esta reconciliación absorbe dos peticiones de A0 que
estaban PENDIENTES y que NO podían quedar fuera sin dejar el test de A0
estáticamente roto (§4):

| Petición pendiente | Origen | Qué se hizo |
|---|---|---|
| `A0-DOM02-01` — las 4 rutas del pool en el inventario de rutas | DOM-02 | Las 4 rutas de `RT-IN-03`/`RT-IN-05`/`RT-IN-06`/`RT-CM-01` añadidas al inventario vivo |
| `A0-DOM02-03` — 8 códigos públicos del pool | DOM-02 | 7 códigos nuevos catalogados (`PERSONA_NO_ENCONTRADA` ya estaba, no se duplicó) |

`A0-DOM02-02` (la versión de `salesianos_fest`) queda **SUBSUMIDO** en el
`1.2.0` de esta reconciliación.

---

## 2. El registro de los controllers (`config/api.py`)

```python
registrar_controladores(
    EdicionController,
    PersonaController,
    AuthController,
    PagosController,
    CatalogoController,
    InscripcionController,
    ProductoController,
    PaseController,        # ← DOM-03
    AdminPaseController,   # ← DOM-03
)
```

**Los dos controllers se registrar AL FINAL** de la lista. El orden es
significativo (`FR-07` §3.1.2: "cuando dos controllers comparten prefijo de
ruta, el último registrado es el que resuelve primero") y añadir al final es
lo ÚNICO que no puede cambiar el orden de resolución de las rutas que ya
existían.

**No hay colisión de prefijos.** Los prefijos vivos son disjuntos:

| Prefijo | Controller | Dueño |
|---|---|---|
| `/api/token` | `NinjaJWTDefaultController` | `ninja_jwt` |
| `/api/ediciones` | `EdicionController` | FND-02 |
| `/api/personas` | `PersonaController` | FND-03 |
| `/api/auth` | `AuthController` | FND-03A |
| `/api/pagos` | `PagosController` | FND-04 |
| `/api/catalogo` | `CatalogoController` | DOM-01 |
| `/api/inscripciones` | `InscripcionController` | DOM-01 + DOM-02 |
| `/api/marketplace` | `ProductoController` | DOM-04 |
| `/api/pases` | `PaseController` | **DOM-03** |
| `/api/administracion/pases` | `AdminPaseController` | **DOM-03** |

`/api/pases` **no** es prefijo de `/api/administracion/pases` ni al revés, y
ningún otro controller vivo usa `/api/administracion`. `ProductoController`
(`/api/marketplace`) y `PaseController` (`/api/pases`) tampoco se solapan.

**Colisión de rutas DENTRO de `PaseController`: comprobada y descartada.**
El controller declara `GET /{pase_id}` **antes** que `GET /compras/{compra_pase_id}`.
Django resuelve los patrones en orden, pero `pase_id: UUID` se convierte en
`<uuid:pase_id>`, que **no** casa con dos segmentos:

| Petición | Patrón que casa | Correcto |
|---|---|---|
| `GET /api/pases` | `pases/` | ✓ `RT-PS-01` |
| `GET /api/pases/{uuid}` | `pases/<uuid:pase_id>` | ✓ `RT-PS-02` |
| `POST /api/pases/compras` | `pases/compras` | ✓ `RT-CM-02` |
| `GET /api/pases/compras/{uuid}` | `pases/compras/<uuid:compra_pase_id>` | ✓ `RT-PS-03` |
| `GET /api/pases/compras/{uuid}/beneficiarios` | ruta explícita | ✓ `RT-PS-04` |
| `POST /api/pases/compras/{uuid}/beneficiarios` | ruta explícita | ✓ `RT-PS-05` |
| `DELETE /api/pases/compras/{uuid}/beneficiarios/{uuid}` | ruta explícita | ✓ `RT-RT-03` |

`GET /api/pases/compras` (un solo segmento "compras") NO casa con
`<uuid:pase_id>` (falla el conversor) y no es una ruta del ledger: no hay
sombra que revisar.

**El DI ya está cableado.** `SalesianosFestModule` está registrado en
`NINJA_EXTRA["INJECTOR_MODULES"]` desde la reconciliación A0 de DOM-01/DOM-04,
y `modules/salesianos_fest/di.py` liga `PaseOrchestrator`,
`BeneficiarioOrchestrator` y `CortesiaOrchestrator` (DOM-03 §3.1). **No hizo
falta tocar `config/settings/base.py`.**

---

## 3. El catálogo público de errores (`core/exceptions.py`)

### 3.1 Los 14 códigos de DOM-03

| Código | Status | ¿Nuevo en este lote? |
|---|---|---|
| `PASE_NO_DISPONIBLE` | 409 | **YA CATALOGADO** — ratificado, no duplicado |
| `CANTIDAD_INVALIDA` | 422 | nuevo |
| `PASE_NO_ENCONTRADO` | 404 | **YA CATALOGADO** — ratificado, no duplicado |
| `COMPRA_PASE_NO_ENCONTRADA` | 404 | nuevo |
| `PASE_BENEFICIARIO_NO_ENCONTRADO` | 404 | **YA CATALOGADO** — ratificado, no duplicado |
| `PASE_NO_TRANSFERIBLE` | 409 | **YA CATALOGADO** — ratificado, no duplicado |
| `PASE_DUPLICADO` | 409 | nuevo |
| `SIN_PASES_DISPONIBLES` | 409 | nuevo |
| `COMPRA_PASE_NO_PAGADA` | 409 | nuevo |
| `TOKEN_PASE_INVALIDO` | 401 | nuevo |
| `ACTOR_REQUERIDO` | 401 | nuevo |
| `COMPRA_PASE_NO_AUTORIZADA` | 403 | nuevo |
| `CORTESIA_MOTIVO_INVALIDO` | 422 | nuevo |
| `CORTESIA_NO_ENCONTRADA` | 404 | nuevo |

**10 códigos nuevos.** Los 4 preexistentes NO se duplicaron — precedente:
`MODULO_NO_HABILITADO` ya catalogado por FND-02 no se duplicó en la
reconciliación A0 de DOM-01/DOM-04.

**Los 4 preexistentes están en el catálogo heredado "Pases de fiesta (catálogo
independiente)", traído del backend anterior.** Sus códigos coinciden con
los de DOM-03 y sus status coinciden con las clases de dominio, así que la
ratificación es coherente. Su PROSA es la heredada (§7 · `OD-A0R3-05`).

### 3.2 Los 7 códigos de DOM-02 absorbidos

`CUPO_INVALIDO` 422 · `SIN_CUPOS_DISPONIBLES` 409 · `PARTICIPANTE_NO_ELEGIBLE`
422 · `PARTICIPANTE_DUPLICADO` 422 · `EQUIPO_COMPLETO` 409 ·
`PARTICIPANTE_NO_ENCONTRADO` 404 · `EQUIPO_NO_ENCONTRADO` 404.

`PERSONA_NO_ENCONTRADA` (404) ya estaba catalogado por FND-03: no se duplicó.

**Por qué se absorben aquí y no se dejan para otro lote.** `CUPO_INVALIDO` está
**CONGELADO** por el ledger `FR-07` §3.3 para `RT-CM-01`, que es una ruta
**VIVA** (la sirve `InscripcionController`, registrado). Sin prosa en el
catálogo, el mensaje público cae al genérico del status y el código congelado
deja de tener la prosa que el ledger le supone. La petición `A0-DOM02-03` lleva
pendiente desde DOM-02 (2026-11-19 02:27) y esta reconciliación es la primera
escritura de A0 sobre la misma raíz compartida y el mismo módulo.

**No se rompió nada de DOM-02**: sus tests (`modules/salesianos_fest/tests/**`,
raíz prohibida para este lote) afirman el **CÓDIGO**, nunca el mensaje. Y el
handler lee el código de la EXCEPCIÓN (`getattr(exc, "code")`), no del
catálogo: catalogar no cambia ningún `error.code` ya emitido.

### 3.3 La prosa

Toda la prosa es **texto español fijo**. Ninguna interpola UUID, id interno,
slug, precio, ruta de disco, restricción SQL, payload de proveedor ni
credencial (`contract/api-wrapper-presenter-contract.md` §8). Las prosa de los
códigos nuevos son LITERALMENTE la que el propio dominio ya escribió en sus
excepciones (`modules/salesianos_fest/domain/exceptions.py`), que son prosa
pública segura por diseño; las dos de recurso ausente se redactaron con el
mismo patrón del catálogo ("No se encontró … solicitada.").

| Código | Prosa pública |
|---|---|
| `CANTIDAD_INVALIDA` | La cantidad de pases solicitados no es válida. |
| `COMPRA_PASE_NO_ENCONTRADA` | No se encontró la compra de pases solicitada. |
| `PASE_DUPLICADO` | La persona ya tiene un pase activo de este tipo en la edición. |
| `SIN_PASES_DISPONIBLES` | No hay pases disponibles para asignar en esta compra. |
| `COMPRA_PASE_NO_PAGADA` | La compra de pases todavía no está pagada. |
| `TOKEN_PASE_INVALIDO` | El enlace de gestión del pase no es válido. |
| `ACTOR_REQUERIDO` | Debes iniciar sesión para realizar esta operación. |
| `COMPRA_PASE_NO_AUTORIZADA` | No tiene autorización para gestionar esta compra de pases. |
| `CORTESIA_MOTIVO_INVALIDO` | El motivo de la cortesía es obligatorio. |
| `CORTESIA_NO_ENCONTRADA` | No se encontró la cortesía solicitada. |

### 3.4 El status no lo decide el catálogo

`PUBLIC_ERROR_MESSAGES` es un mapa **código → prosa**. El status lo fija la
CLASE de excepción que el dominio lanza. Para que catálogo y dominio no
puedan divergir, el test compartido ata las dos cosas: **21 excepciones de
dominio** (14 de DOM-03 + 7 de DOM-02) se instancian y se comprueba que
`exc.code` es el esperado y `exc.status_code` es el status catalogado.

Statuses verificados contra la clase de dominio:

| Status | Clases |
|---|---|
| 401 | `TokenPaseInvalidoError`, `ActorRequeridoError` (heredan de `ninja.errors.HttpError` con `status_code=401`; el handler global de `HttpError` los cubre porque leen `getattr(exc, "code")`) |
| 403 | `CompraPaseNoAutorizadaError` (`ForbiddenError`) |
| 404 | `PaseNoEncontradoError`, `CompraPaseNoEncontradaError`, `PaseBeneficiarioNoEncontradoError`, `CortesiaNoEncontradaError`, `ParticipanteNoEncontradoError`, `EquipoNoEncontradoError` (`NotFoundError`) |
| 409 | `PaseNoDisponibleError`, `PaseNoTransferibleError`, `PaseDuplicadoError`, `SinPasesDisponiblesError`, `CompraPaseNoPagadaError`, `SinCuposDisponiblesError`, `EquipoCompletoError` (`ConflictError`) |
| 422 | `CantidadInvalidaError`, `CortesiaMotivoInvalidoError`, `CupoInvalidoError`, `ParticipanteNoElegibleError`, `ParticipanteDuplicadoError` (`UnprocessableEntityError`) |

---

## 4. La versión de contrato (`core/contract_versions.py`)

```python
"salesianos_fest": "1.2.0",
```

El módulo `modules/salesianos_fest/presentation/schemas/__init__.py` declara
`SCHEMA_VERSION = "1.2.0"` (DOM-01 `1.0.0` → DOM-02 `1.1.0` → DOM-03
`1.2.0`). **La paridad queda restablecida** y el test de drift
(`test_no_hay_drift_entre_el_registro_y_el_modulo`) deja de fallar.

El cambio es **MINOR y ADITIVO** (`tipo_de_cambio("1.1.0", "1.2.0") == "MINOR"`):
DOM-03 añade diez rutas y ninguna forma de respuesta existente se eliminó,
renombró ni cambió de tipo.

**`"marketplace"` NO se tocó**: ya estaba en `1.1.0` por el trabajo concurrente
de DOM-05 (que declara `SCHEMA_VERSION = "1.1.0"`), y su reconciliación
completa (controller del pedido, códigos) **queda fuera de este lote**.

**La clave `"pases"` sigue en `1.0.0`.** Es el nombre de DOMINIO del ledger
(`FR-07` §2: "`pases` / `beneficios` (derechos)"), no el nombre físico del
módulo: los pases viven en `modules/salesianos_fest`. Es la misma divergencia
ya documentada para `inscripciones` (`D-DOM-01-08`). No se tocó: el registro
no inventa versiones de módulos que no existen.

---

## 5. Los tests compartidos actualizados (ESCRITOS, NO EJECUTADOS)

### 5.1 `core/tests/integration/test_registration_extension.py`

El inventario de rutas es una **aserción sobre la superficie VIVA**: si una
ruta viva no está en la lista, el test falla; si la lista tiene una ruta que
no está viva, el test falla. Por eso la lista tiene que ser EXACTA.

- `CONTROLLERS_COMPLETADOS` — los 10 controllers vivos, **en el orden de
  registro** de `config/api.py` (incluye `AuthController`, que ya estaba
  registrado por el trabajo concurrente de FND-03A y que la lista no recogía:
  el test ya fallaba antes de este lote).
- `PREFIJOS_PERMITIDOS` — + `/api/auth`, `/api/pases`,
  `/api/administracion/pases`.
- `RUTAS_DE_DOMINIO_CONGELADAS` — **31 paths de dominio** (antes 15):
  + 4 de `FND-03A` (autenticación) · + 4 de `DOM-02` (pool) · + 8 de `DOM-03`
  (pases y administración de pases).

### 5.2 `core/tests/integration/test_contract_versions.py`

Dos aserciones fijaban `1.0.0` para módulos que ya NO están en `1.0.0`:

- `test_los_modulos_congelados_declaran_1_0_0` — se sacaron `marketplace` y
  `salesianos_fest` de la lista de congelados en `1.0.0` (los dos
  evolucionaron). Los congelados restantes (`eventos`, `usuarios`,
  `commerce`, `pagos`, `pases`, `beneficios`, `validaciones`,
  `patrocinadores`) siguen en `1.0.0`.
- `test_el_registro_incluye_los_fundamentos_completados` — ya no fija
  `1.0.0` a todos los completados: comprueba que están REGISTRADOS. La
  versión exacta la comprueba el test de drift contra la declaración del
  módulo (que es la autoridad) y, para `salesianos_fest`, una aserción
  explícita de `1.2.0`.
- Se añadieron `test_el_registro_refleja_la_version_declarada_de_salesianos_fest`
  y `test_la_version_de_salesianos_fest_es_un_cambio_minor_aditivo`.

**Acoplamiento deliberado a `marketplace`: NINGUNO.** La versión de
`marketplace` NO se fija en el test compartido; la compara con la que
declara el módulo. Si DOM-05 la vuelve a mover, este test no se rompe.

### 5.3 `core/tests/integration/test_exceptions_public_catalog.py`

- `CODIGOS_DOM03` (14) + `CODIGOS_DOM02` (7) + `STATUS_DOM03` + `STATUS_DOM02`.
- `test_los_codigos_de_dom03_y_dom02_estan_en_el_catalogo` (21 casos).
- `test_la_prosa_de_los_codigos_de_dom03_y_dom02_es_prosa_fija` (21 casos) —
  sin `{`, `}`, `%` ni `$`.
- `test_cada_codigo_de_dom03_responde_con_el_status_pedido` (14) y
  `test_cada_codigo_de_dom02_responde_con_el_status_pedido` (7).
- `test_el_status_del_codigo_es_el_de_la_clase_de_dominio` (14) y
  `test_el_status_del_codigo_de_dom02_es_el_de_la_clase_de_dominio` (7) — **la
  invariante nueva**: el catálogo y la excepción del dominio no pueden
  divergir.

**Casos de test nuevos en `core/tests/**`: 86 parametrizados** (21 catálogo +
21 prosa fija + 14 status DOM-03 + 7 status DOM-02 + 14 status↔clase DOM-03 +
7 status↔clase DOM-02 + 2 de versión) **más 7 tests modificados** (el
inventario de controllers, el de prefijos, el de rutas, los dos de versión y
los dos de dominios inacabados).

---

## 6. Revisión estática (comprobaciones hechas SIN ejecutar nada)

| # | Comprobación | Resultado |
|---|---|---|
| A-01 | Los imports de `config/api.py` apuntan a ficheros que existen | OK — `modules/salesianos_fest/presentation/controllers/pase_controller.py` existe y exporta `PaseController` y `AdminPaseController` (`__all__`) |
| A-02 | No hay dos `pase_controller.py` en `Aplicacion/backend` | OK — sólo el de DOM-03; el homónimo del árbol congelado `backend/**` es OTRO root y no se importa |
| A-03 | Colisión de prefijos de ruta | OK — los 10 prefijos vivos son disjuntos (§2) |
| A-04 | Colisión de rutas dentro de `PaseController` | OK — `<uuid:pase_id>` no casa con dos segmentos (§2) |
| A-05 | El DI de los tres orquestadores está ligado | OK — `PaseOrchestrator`, `BeneficiarioOrchestrator`, `CortesiaOrchestrator` en `SalesianosFestModule` (DOM-03 §3.1) |
| A-06 | `SalesianosFestModule` está en `INJECTOR_MODULES` | OK — ya estaba (reconciliación A0 de DOM-01/DOM-04) |
| A-07 | `modules.salesianos_fest` está en `LOCAL_APPS` | OK — ya estaba |
| A-08 | Paridad `SCHEMA_VERSIONS["salesianos_fest"]` ↔ `SCHEMA_VERSION` del módulo | OK — `1.2.0` = `1.2.0` |
| A-09 | El cambio de versión es MINOR | OK — `tipo_de_cambio("1.1.0", "1.2.0") == "MINOR"` |
| A-10 | Los 14 códigos de DOM-03 están catalogados | OK — 4 ratificados + 10 nuevos |
| A-11 | Los 7 códigos de DOM-02 absorbidos están catalogados | OK |
| A-12 | Cada código nuevo tiene prosa NO VACÍA | OK — 21 entradas, todas con texto |
| A-13 | La prosa no interpola nada | OK — sin `{`, `}`, `%`, `$` en las 21 |
| A-14 | Cada status del catálogo coincide con el de su clase de dominio | OK — 21 excepciones instanciadas y comprobadas (§3.4) |
| A-15 | `TokenPaseInvalidoError` / `ActorRequeridoError` los cubre el handler global | OK — heredan de `ninja.errors.HttpError`, que es el `HttpError` que `core/exceptions.py` registra; el handler lee `getattr(exc, "code")` |
| A-16 | El handler NO se debilita | OK — no se tocó `register_exception_handlers`, ni `public_message_for`, ni `GENERIC_PUBLIC_MESSAGES` |
| A-17 | Los códigos de `marketplace` y `DOM-05` NO se tocaron | OK — `marketplace` sigue en `1.1.0` y su controller (`pedido_controller.py`) NO está registrado |
| A-18 | Ningún controller INACABADO registrado | OK — `competencias_controller.py` (`/competencias`), `pedido_controller.py` (`/marketplace`) y `patrocinadores_controller.py` (`/patrocinadores`) EXISTEN pero NO están registrados |
| A-19 | El test URLconf del módulo y el API del proyecto no colisionan | OK — `modules/salesianos_fest/tests/urls_salesianos_fest.py` monta su PROPIA instancia con `urls_namespace` único; `ninja_extra` guarda la instancia por PATH VIEW, no por clase de controller (mismo patrón ya validado en verde con `CatalogoController` e `InscripcionController`) |
| A-20 | La lista de controllers del test está en el MISMO orden que el registro | OK |
| A-21 | `controllers_registrados()` es idempotente con la lista nueva | OK — `registrar_controladores` deduplica por identidad |
| A-22 | Ningún interior de `modules/**` editado | OK (§8) |
| A-23 | `STATE.md`, matriz de tareas, ledger y registros compartidos NO editados | OK (§8) |
| A-24 | Los cambios sucios preexistentes del worktree se preservaron | OK — `AuthController` en `config/api.py`, `marketplace: 1.1.0`, `modules/usuarios/**`, `modules/marketplace/**`, `modules/salesianos_fest/**`, `frontend/**` intactos |

---

## 7. Decisiones abiertas que NO se inventaron

| ID | Decisión | Owner | Por qué NO se resolvió aquí |
|---|---|---|---|
| `OD-A0R3-01` | Ratificar `RT-PS-01`…`RT-PS-08` en el ledger `FR-07` §3.3 y en `SH-05` §1.4 | GOV-01 + A0 | El ledger y `SH-05` son **evidencia de contrato congelada**: están fuera de las raíces permitidas. Precedente: `OD-A0R2-02` (misma situación con `RT-IN-14`). Las rutas **funcionan y están registradas**; el inventario de A0 las lleva |
| `OD-A0R3-02` | Canal del token de gestión: `X-Pase-Token` | A0 + A7 + producto | `P-01` deja el canal abierto y DOM-03 lo declara PROVISIONAL (`OD-DOM03-04`). El mecanismo está implementado y testeado; ratificarlo aquí sería inventar un canal congelado |
| `OD-A0R3-03` | Ruta de revocación de una CORTESÍA (`FL-07` paso 4) | A4 + A0 + producto | **El ledger NO declara ruta** (`RT-RT-03` es de beneficiarios de COMPRA). El dominio expone la operación. No se creó una ruta que el ledger no declara |
| `OD-A0R3-04` | Las DOS definiciones de "administrador" (`core.capacidades.es_admin` = `is_staff OR is_superuser` vs `usuarios.GrupoFuncionalService.es_administrador` = grupo `Administrador`) | A0 + producto | DOM-03 usa `core.capacidades` (la autoridad ÚNICA del proyecto, FND-01). Unificarlo cambiaría comportamiento de autorización en TODO el proyecto: no es una reconciliación de cableado |
| `OD-A0R3-05` | Prosa heredada de `PASE_NO_TRANSFERIBLE` ("Ese pase no es transferible a otra persona.") | A0 + A4 | El código es CONGELADO por el ledger pero la SEMÁNTICA de DOM-03 es otra: el derecho ya revocado (`RN-P08`) o la compra no pagada (`RN-P02`). La prosa heredada viene del backend anterior y hoy **no es observable** (§8, H-01). Cambiar un mensaje público de un módulo ya validado en `1.2.0` es un PATCH que le toca al dueño del módulo (`FR-07` §1.2), no a una reconciliación |
| `OD-A0R3-06` | `*.sqlite3` en el `.gitignore` del objetivo | A0 | Fuera de las raíces permitidas (heredado de FND-01…DOM-05). No quedó ningún `.sqlite3` en el repositorio |
| `OD-A0R3-07` | Sincronización de la matriz física de tareas (`T-030`, `T-031`, `T-032`) y del `STATE.md` compartido | A0 + coordinador | Fuera de las raíces permitidas y explícitamente diferido: el coordinador fusionará el estado compartido cuando DOM-07/DOM-08 terminen |
| `OD-A0R3-08` | `PD-01` (BOX) · `PD-02` (política de revocación) · `PD-03` (ticket por unidad) | A4 + A8 + producto | Decisiones de PRODUCTO: no son cableado. Siguen abiertas tal como las dejó DOM-03 |
| `OD-A0R3-09` | `GOV-01-OPEN-05` (expiración/rotación del token: `VIGENCIA_TOKEN_PASE_DIAS = 30`) | A1 + A0 + producto | El MECANISMO está congelado; el número es un valor declarado y conservador. No se cambió |

---

## 8. Hallazgos estáticos (NO se cruzaron en `modules/**`)

**H-01 — `PaseNoTransferibleError` está DEFINIDA pero NO se lanza en ninguna
parte.** `grep` sobre `Aplicacion/backend/modules/**` encuentra la clase
(`domain/exceptions.py:385`) y su export en `__all__`, y **ningún** flujo la
levanta. El código está CONGELADO por el ledger `FR-07` §3.3 para `RT-RT-03`,
así que el contrato se cumple, pero **su prosa pública no es observable hoy**.
Cuando la política de revocación (`PD-02`) se cierre, hay que decidir si la
revocación de un derecho ya revocado responde 409 `PASE_NO_TRANSFERIBLE` o
200 con `ya_revocado=True` (DOM-03 congela la revocación como **idempotente**:
la segunda revocación informa del estado final, NO es un error). **Es un
hallazgo de DOMINIO**: NO se tocó `modules/salesianos_fest/**` y NO se inventó
comportamiento.

**H-02 — el inventario de rutas de A0 estaba ROTO por DOM-02 y por
FND-03A, no sólo por DOM-03.** `test_las_rutas_de_dominio_son_exactamente_las_congeladas`
fallaba desde DOM-02 (4 rutas del pool sin listar) y
`test_el_registro_expone_los_controllers_vivos` fallaba desde FND-03A
(`AuthController` registrado sin listar). DOM-02 lo dejó registrado y explícito
(§9 de su apply-progress: "2 fallos de A0"). Esta reconciliación los arregla
porque el inventario es una aserción sobre la superficie VIVA.

---

## 9. Comandos FUTUROS (NO ejecutados — requieren autorización explícita)

Workdir `Aplicacion/backend`. **Toda** verificación posterior exige
autorización del usuario y `uv run`:

```bash
# 1. Puertas de Django
uv run python manage.py check --settings=config.settings.development
uv run python manage.py makemigrations --check --dry-run --settings=config.settings.development

# 2. Registro y contrato (lo que esta reconciliación toca)
uv run python -m pytest core/tests/integration/test_registration_extension.py -q
uv run python -m pytest core/tests/integration/test_contract_versions.py -q
uv run python -m pytest core/tests/integration/test_exceptions_public_catalog.py -q

# 3. Suite compartida completa de A0
uv run python -m pytest core/tests -q

# 4. El módulo dueño de los packets absorbidos (DOM-01 + DOM-02 + DOM-03)
uv run python -m pytest modules/salesianos_fest/tests -q

# 5. Los paquetes vecinos (no editados)
uv run python -m pytest modules/eventos/tests modules/usuarios/tests \
  modules/commerce/tests modules/pagos/tests modules/marketplace/tests -q

# 6. Suite completa del objetivo
uv run python -m pytest -q

# 7. Migraciones (no tocadas por este lote, pero DOM-03 tiene 0003 sin verificar)
uv run python manage.py makemigrations salesianos_fest --check --dry-run
```

> **La base de datos del ensayo debe vivir FUERA del repositorio** (los
> `*.sqlite3` son un artefacto prohibido).

**Lo que la verificación debe comprobar y NO se ha comprobado:**

1. Que `PaseController` y `AdminPaseController` exponen exactamente los 8 paths
   esperados en el esquema OpenAPI vivo del proyecto.
2. Que la superficie de dominio viva son **31** paths y que el inventario
   cerrado de A0 los contiene **exactamente**.
3. Que los 21 códigos del catálogo devuelven su prosa (y no la genérica) con
   el status de su clase de dominio.
4. Que la suite de `salesianos_fest` sigue verde con los controllers
   registrados **y** con el URLconf de test (doble instancia de `ninja_extra`).
5. Que `marketplace` no se rompió: `SCHEMA_VERSION = "1.1.0"` en el registro y
   en el módulo.

---

## 10. Ficheros cambiados

| Fichero | Acción | Qué se hizo |
|---|---|---|
| `Aplicacion/backend/config/api.py` | Modificado | Import + registro de `PaseController` y `AdminPaseController`; comentarios de registro actualizados |
| `Aplicacion/backend/core/contract_versions.py` | Modificado | `SCHEMA_VERSIONS["salesianos_fest"]` → `1.2.0` |
| `Aplicacion/backend/core/exceptions.py` | Modificado | **17** códigos públicos nuevos (10 de DOM-03 + 7 de DOM-02 absorbidos); 5 ratificados sin duplicar |
| `Aplicacion/backend/core/tests/integration/test_registration_extension.py` | Modificado | Inventario de controllers, prefijos y rutas vivas (31 paths) |
| `Aplicacion/backend/core/tests/integration/test_contract_versions.py` | Modificado | Aserciones de versión liberadas de `1.0.0`; paridad con el módulo + `1.2.0` explícito |
| `Aplicacion/backend/core/tests/integration/test_exceptions_public_catalog.py` | Modificado | 21 códigos con status; prosa fija; status atado a la clase de dominio |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/A0-reconciliation-dom03.md` | **Creado** | Este informe |

**NO editados:** `Aplicacion/backend/modules/**` (ningún interior de dominio,
**incluido `modules/salesianos_fest/**`**) · `Aplicacion/frontend/**` · los
árboles congelados `backend/**`, `frontend/**`, `worker/**`, `proxy/**`,
`.opencode/**` · `contract/**` · `Aplicacion/plan/**` ·
`Aplicacion/documentacion/**` · `Aplicacion/task/salesianos-fest-rebuild/STATE.md` ·
`00-matriz-tareas.md` · el ledger `route-to-wrapper-ledger.csv` · `SH-05` ·
los registros compartidos de estado y de apply-progress.

---

## 11. Rollback

Punto de rollback: `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (HEAD del
usuario; este lote **no** creó ningún commit). `git stash` **nunca** invocado.
**No revertir ni resetear** ese commit.

1. `config/api.py`: quitar el import de `pase_controller` y los dos nombres
   `PaseController` y `AdminPaseController` de `registrar_controladores(...)`.
2. `core/contract_versions.py`: devolver `"salesianos_fest"` a `"1.0.0"`.
3. `core/exceptions.py`: quitar las 17 entradas nuevas.
4. `core/tests/integration/test_registration_extension.py`: restaurar la lista
   previa de controllers, prefijos e inventario (15 paths).
5. `core/tests/integration/test_contract_versions.py`: restaurar las dos
   aserciones que fijaban `1.0.0` y quitar las dos aserciones nuevas.
6. `core/tests/integration/test_exceptions_public_catalog.py`: quitar el bloque
   de DOM-03/DOM-02.
7. Borrar este fichero de evidencia.

**El historial comercial y de pagos se preserva**: este rollback nunca borra
una compra, una orden, una transacción ni un acta.

---

## 12. Concurrencia

| Ruta | Estado |
|---|---|
| `Aplicacion/backend/modules/competencias/**` (DOM-07) | **NO tocada.** Ni revertida ni fusionada. Sus filas de tablero NO se editaron |
| `Aplicacion/backend/modules/patrocinadores/**` (DOM-08) | **NO tocada.** Sus controllers **NO** se registran (A0 no registra dominios inacabados) |
| `Aplicacion/backend/modules/marketplace/**` (DOM-05) | **NO tocada.** Su reconciliación (pedido, códigos) **queda fuera de este lote** |
| `Aplicacion/backend/modules/usuarios/**` (FND-03A) | **NO tocada.** Su registro de `AuthController` en `config/api.py` (cambio sucio preexistente) se **PRESERVÓ** y se reflejó en el inventario de A0 |
| `Aplicacion/backend/modules/salesianos_fest/**` (DOM-01/02/03) | **NO tocada.** Ni un interior de dominio, ni un test de módulo |
| `Aplicacion/frontend/**` | **NO tocada.** Ni revertida ni fusionada |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | **NO editado** (cambio sucio preexistente de DOM-03/DOM-05/DOM-07). El estado compartido lo fusiona el coordinador |
| `sdd/salesianos-fest-rebuild/state` · `.../apply-progress` (Engram) | **NO escritos.** El coordinador los fusiona al cerrar DOM-07/DOM-08 |
| `00-matriz-tareas.md` · `route-to-wrapper-ledger.csv` · `SH-05` | **NO editados** (evidencia de contrato de GOV-01/GOV-02) |

---

## 13. Consumidores desbloqueados

**API-03** (el espejo comercial: las diez rutas de pases + wrappers y
presenters nombrados, ahora **vivas**) · **API-05** (el catálogo de pases de
la edición) · **XCT-01** (el derecho que `validaciones` consulta) ·
**XCT-03** (pago / entrega / consumo separados) · **UI-02 / UI-03 / UI-04**
(el catálogo, el enlace de gestión por token, el panel de cortesías) ·
**A7** (el espejo Zod de `salesianos_fest` a `1.2.0`).

**Desbloqueado de paso:** el drift de versión de `salesianos_fest` (estaba
roto desde DOM-02) · el inventario de rutas de A0 (roto desde DOM-02) ·
la prosa pública del pool de cupos (roto desde DOM-02) · la prosa pública de
los diez códigos de pases.

**Siguen bloqueados (no son de A0):** `XCT-01` necesita la verificación
diferida · `DOM-06` (pedido pagado vs entregado) · `FND-07` · la validación
de `DOM-03` con `uv run`.

---

## 14. Siguiente paso

1. **Verificar** con `uv run` (§9) — requiere autorización explícita del
   usuario.
2. **Fusionar el estado compartido** (`STATE.md`, matriz de tareas, topics
   `state` y `apply-progress`) cuando DOM-07 y DOM-08 terminen: es el
   coordinador, no este lote.
3. **Despachar las decisiones abiertas** de §7 que son de producto
   (`OD-A0R3-03` ruta de revocación de cortesía, `OD-A0R3-05` prosa de
   `PASE_NO_TRANSFERIBLE`, `PD-01`/`PD-02`/`PD-03`).
4. **Ratificar en el ledger** (`FR-07` §3.3 y `SH-05` §1.4) las ocho rutas
   de DOM-03 y las cuatro del pool de DOM-02: es GOV-01, no A0.
