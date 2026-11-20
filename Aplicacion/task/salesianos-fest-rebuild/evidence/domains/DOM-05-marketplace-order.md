# DOM-05 - Pedido de marketplace y snapshots de precio

**Artifact:** `evidence/domains/DOM-05-marketplace-order.md` · **Packet:** `DOM-05`
(`wave-02-domain-backend`) · **Change:** `salesianos-fest-rebuild` · **Owner:** A5
**Original task ID:** `T-041` — 1 de los 54 IDs del plan (acumulado con
GOV-00/01/02, FND-01…FND-05, DOM-01, DOM-02 y DOM-04: **20 de 54**)
**Freezes respetados:** `FREEZE-CM-1.0.0` (FR-04) · `FREEZE-MD-1.0.0` (FR-06) ·
`FREEZE-ED-1.0.0` (FR-02) · `FREEZE-PS-1.0.0` (FR-07) · `FREEZE-ENV-1.0.0` (FR-01) ·
`FREEZE-TC-1.0.0`

> **ESTADO: `verification_required`.** Toda la verificación en tiempo de
> ejecución está **DIFERIDA por instrucción explícita del usuario**. El
> paquete entrega el CÓDIGO y el ORIGEN DE LAS PRUEBAS, pero **no** la
> evidencia de ejecución. Ver §6.

---

## 1. Qué se entregó

El **pedido de la tienda**: el agregado `Pedido` con su detalle, el snapshot
CONGELADO del precio, el adaptador hacia la infraestructura comercial
compartida y los presenters tipados. Sin existencias, sin entrega y sin
carrito combinado.

### 1.1 Modelos (`domain/models/pedido.py`)

```
Pedido
  id: UUID               (pk)
  edicion_id: UUID        FK → eventos.Edicion      (PROTECT)
  comprador_id: UUID      FK → usuarios.Persona      (PROTECT)
  compra_id: UUID         FK → commerce.Compra       (PROTECT, null)
  estado: PENDIENTE | PAGADO | CANCELADO
  estado_entrega: PENDIENTE | ENTREGADO
  total: Decimal(12,2)    total CONGELADO por el servidor
  moneda: str             ISO-4217 (PEN)
  token: str(64)          enlace privado de seguimiento (UNIQUE)
  huella: str(64)         huella de la INTENCIÓN de pedido
  referencia: str(200)    referencia estable de la compra
  created_at, updated_at

PedidoDetalle
  id: UUID               (pk)
  pedido_id: UUID         FK → Pedido                (CASCADE)
  tipo_concepto: PRODUCTO
  concepto_id: str(64)
  concepto_nombre: str(200)   el nombre EN EL MOMENTO del pedido
  cantidad: int          (CHECK >= 1)
  precio_unitario: Decimal(10,2)  precio de catálogo congelado
  precio_aplicado: Decimal(10,2)  precio realmente aplicado (con oferta)
```

**TRES HECHOS SEPARADOS** (`RN-M07`, `QA-M04`, `RN-C08`):

| # | Hecho | Dónde vive | Quién lo mueve |
|---|---|---|---|
| 1 | `Pedido.estado` | el pedido | `marketplace` (`PedidoCoreService.marcar_estado`) |
| 2 | `estado_entrega` | el pedido | **`DOM-06`** — `marketplace` NUNCA lo cambia |
| 3 | estado del PAGO | `commerce.Compra.estado` | `commerce` — el módulo lo **proyecta** |

El pago NUNCA habilita la entrega: `marcar_estado` escribe `update_fields`
con `["estado", "updated_at"]` y **jamás** toca `estado_entrega`.

**El histórico NO cambia** (`RN-M03`): el detalle congela `precio_unitario` y
`precio_aplicado` en el momento del pedido. Una oferta posterior no altera ni
el detalle ni el total ya congelados.

### 1.2 Vocabulario cerrado (`domain/constants.py`)

| Clase | Valores | Nota |
|---|---|---|
| `EstadoPedido` | `PENDIENTE` · `PAGADO` · `CANCELADO` | el ciclo del PEDIDO |
| `EstadoPagoPedido` | `PENDIENTE` · `CONFIRMADO` · `NO_COMPLETADO` | proyección de `commerce` |
| `EstadoEntregaPedido` | `PENDIENTE` · `ENTREGADO` | lo avanza `DOM-06` |
| `TipoItemPedido` | `PRODUCTO` · `PASE` · `INSCRIPCION` | sólo `PRODUCTO` es admisible |
| `AccionPedido` | `REALIZAR_PAGO` · `ESPERAR_ENTREGA` · `REINTENTAR_COMPRA` · `VER_TICKET` | verbos del dominio, NO del proveedor |

La asimetría `PAGADO` (pedido) / `CONFIRMADO` (pago) / `PENDIENTE`
(entrega) es DELIBERADA: los tres hechos no pueden confundirse porque no
comparten vocabulario.

### 1.3 La frontera con `commerce` (puerto + adaptador)

`domain/ports/comercio.py` declara `ICommerceMarketplaceService` con DOS
operaciones:

| Operación | Para qué |
|---|---|
| `crear_o_reutilizar_compra(data)` | abrir (o recuperar) la compra que financia el pedido — `FR-04` I-4 |
| `hechos_compra(compra_id)` | LEER el hecho del pago para separar pedido, pago y entrega — `RN-M07` |

`infrastructure/services/comercio_adapter.py` es el ÚNICO punto del módulo
que habla con `commerce`, y **traduce el vocabulario**:

| `commerce` (su vocabulario) | `marketplace` (el nuestro) |
|---|---|
| `Compra.estado = PENDIENTE` | `EstadoPagoPedido.PENDIENTE` |
| `Compra.estado = PAGADA` | `EstadoPagoPedido.CONFIRMADO` |
| `Compra.estado = CANCELADA` | `EstadoPagoPedido.NO_COMPLETADO` |

El DOMINIO no importa `commerce`: conoce el puerto. El módulo se registra en
`di.py` con una **fábrica perezosa** (`_adaptador_comercio_factory`) que
consume el `CompraFlujo` y el `CompraSelector` del inyector de `commerce`:
el grafo de módulos queda acíclico y este módulo NO duplica el wiring ajeno.

### 1.4 Servicios

| Capa | Fichero | Qué hace |
|---|---|---|
| core (sync) | `domain/services/core/pedido_core_service.py` | validaciones, huella, token, resolución de líneas, congelación del precio, total derivado, escritura, proyección a result |
| flujo (async) | `domain/services/flujos/pedido_flujo.py` | **único** lugar con `transaction.atomic()`; recuperación de la intención; reconciliación pedido↔pago |
| orquestador (async) | `domain/services/orchestrators/pedido_orchestrator.py` | fachada delgada; resuelve el COMPRADOR (la `Persona` de la cuenta) |
| selector (sync) | `domain/selectors/pedido_selector.py` | lecturas que devuelven **LISTAS** (F-26) |

**Reglas que viven en el core:**

| Regla | Dónde | Rechazo |
|---|---|---|
| `RN-C01` sin carrito combinado | `validar_tipos` | `PEDIDO_ITEMS_MIXTOS` (mezcla) · `PEDIDO_ITEM_NO_PERMITIDO` (un pase o una inscripción) |
| cantidad válida | `validar_cantidades` | `PEDIDO_CANTIDAD_INVALIDA` (fuera de `1…MAX_CANTIDAD_ITEM_PEDIDO`) |
| `RN-C02` el servidor congela el precio | `resolver_lineas` + `calcular_total` | `PRODUCTO_NO_ENCONTRADO` (404) · `PRODUCTO_NO_DISPONIBLE` (409) |
| `RN-E01/RN-E02` el alcance lo resuelve el servidor | `_resolver_edicion` | `MODULO_NO_HABILITADO` (409) |
| `RN-C03/RN-C04` un reintento NO duplica | `calcular_huella` + índice parcial | — |
| `RN-U02` la titularidad | `obtener_pedido_por_token` | `PEDIDO_NO_AUTORIZADO` (403) |
| `RN-U04` el comprador es la `Persona` de la cuenta | `PedidoOrchestrator` | `COMPRADOR_SIN_PERSONA` (422) |

**La huella identifica la INTENCIÓN, no el precio:**
`sha256(tipo:producto_id:cantidad | …)` ordenado. Una oferta posterior NO
cambia la huella → un reintento sigue recuperando el MISMO pedido con su
snapshot congelado.

**La cantidad la valida el DOMINIO, no el wire.** `CrearPedidoIn` y
`PedidoItemCreateData` NO acotan el rango de la cantidad: el rechazo viaja
con el código estable `PEDIDO_CANTIDAD_INVALIDA` y no con un error de forma
del schema. La regla comercial vive en el backend, no en el contrato del
cable.

### 1.5 Presenters y superficie HTTP

| Ruta | Método | Wrapper de entrada | Wrapper de salida | Presenter |
|---|---|---|---|---|
| `RT-CM-03` | POST `/marketplace/pedidos` | `CrearPedidoIn` | `PedidoCreadoOut` | `PedidoPresenter` |
| `RT-MK-04` | GET `/marketplace/pedidos/{token}` | — | `PedidoSeguimientoOut` | `PedidoSeguimientoPresenter` |

- `POST /pedidos`: `auth=JWTAuth()` + `permissions=[IsAuthenticated]` — el
  patrón de `DOM-01`/`DOM-02`.
- `GET /pedidos/{token}`: `auth=None` (el token ES la credencial del enlace,
  P-01). El actor es **opcional**: un invitado abre su pedido con el token; un
  actor autenticado que NO es el comprador recibe 403. Una credencial rota
  responde 401 con el catálogo global.

**El presenter NO expone internos del proveedor** (FR-01 §4): ni referencia
técnica, ni intento, ni evidencia, ni firma. Expone los TRES estados, las
líneas con su precio congelado, el total, la moneda y la **siguiente acción
SEGURA** (`REALIZAR_PAGO` · `ESPERAR_ENTREGA` · `REINTENTAR_COMPRA` ·
`VER_TICKET`).

**El token viaja SÓLO en la respuesta del alta.** En el seguimiento es la
credencial del path y no se devuelve en el cuerpo.

`SCHEMA_VERSION` del módulo: **`1.0.0` → `1.1.0`** (MINOR aditivo: dos
rutas y cinco wrappers nuevos; no se elimina ni se renombra nada — FR-07
§1.2). El registro global `core/contract_versions.py` es de **A0**: su
actualización es la petición **A0-02**.

### 1.6 Lo que este paquete NO implementa

| Fuera de alcance | Por qué | Dónde vive |
|---|---|---|
| existencias / reserva / anti-sobreventa | `RN-M06` es de `DOM-06` | `DOM-06` |
| entrega y consumo del ticket | `QA-V01`/`QA-V02` son de `DOM-06` | `DOM-06` |
| `estado_entrega` | lo avanza `DOM-06`; el pago NO lo habilita | `DOM-06` |
| activation de derechos tras el pago | `RN-C08` — el coordinador de FND-05 | `FND-05` |
| pase / inscripción como artículos | `RN-C01` — tienen su propio checkout | `DOM-03` / el módulo de pases |

`Producto` NO declara stock (DOM-04, `D-DOM04-06`): `DOM-06` puede añadirlo
con una migración aditiva `003_*` sin romper `0001_initial` ni `0002_*`.

---

## 2. Migraciones

`modules/marketplace/migrations/0002_pedido_pedidodetalle_and_more.py`

- Depende de `("marketplace", "0001_initial")`, `("commerce", "0002_activacioncompra")`,
  `("eventos", "0001_initial")`, `("usuarios", "0002_grupos_funcionales")`.
- Crea `Pedido` y `PedidoDetalle`, añade el índice por estado y las
  restricciones:

| Restricción | Tipo | Qué protege |
|---|---|---|
| `marketplace_pedido_pendiente_unico_por_intencion` | UNIQUE **parcial** `(comprador, edicion, huella) WHERE estado='PENDIENTE'` | un reintento NO duplica el pedido (RN-C03, RN-C04) — el índice, no la aplicación, es la autoridad |
| `marketplace_pedido_total_no_negativo` | CHECK | el total nunca es negativo |
| `marketplace_pedido_detalle_cantidad_valida` | CHECK `cantidad >= 1` | la cantidad es válida |
| `marketplace_pedido_detalle_precio_no_negativo` | CHECK | el precio de catálogo no es negativo |
| `marketplace_pedido_detalle_precio_aplicado_no_negativo` | CHECK | el precio aplicado no es negativo |
| `ix_marketplace_pedido_estado` | índice | consulta por estado |

La FK `compra` → `commerce.Compra` es `PROTECT`: un pedido nunca borra la
compra que lo financia (el historial comercial se preserva).

> **La migración NO ha sido aplicada ni verificada en esta ronda** (§6). Su
> generación coincide con los modelos: no hay `makemigrations` pendiente
> pendiente de escritura, y la reversing es estructural (todo `CreateModel` +
> `AddConstraint` + `AddIndex`).

---

## 3. Origen de las pruebas (behavior-first)

**Las pruebas se escribieron y NO se ejecutaron** (§6). El origen es el
siguiente:

| Fichero | Tests | Qué cubre |
|---|---|---|
| `tests/integration/test_pedido_snapshot.py` | 6 | snapshot pendiente, cambio de precio posterior, los TRES estados por separado, pagado ≠ entregado, compra cancelada, el snapshot de la compra |
| `tests/integration/test_pedido_reglas.py` | 15 funciones (17 casos: la de cantidad va parametrizada ×3) | carrito mixto, sólo pases, sólo inscripciones, cantidad inválida (0, −1, > máximo), producto inexistente, producto retirado, producto de otra edición, edición sin la tienda, cuenta sin `Persona`, titularidad, reintento (mismo pedido / misma compra / intención distinta), total derivado |
| `tests/e2e/test_pedido_controller.py` | 11 | `RT-CM-03` y `RT-MK-04`: alta con snapshot, 401 sin sesión, reintento, carrito mixto 422, producto inexistente 404, cantidad inválida 422, seguimiento con los tres estados, apertura por invitado, 403 de otro usuario, 404 de token desconocido, y que la respuesta NO expone internos del pago |

**Total: 32 funciones de prueba (34 casos colectados)**, más las 35 de
`DOM-04`, que siguen intactas.

**Las pruebas son SECUENCIALES a propósito.** La carrera por la misma
intención se decide en la base de datos (índice parcial único) y su
verificación concurrente pertenece a la fase de verificación: no se
introduce ningún test con hilos.

**No hay mocks**: los dobles son implementaciones reales de los puertos y los
servicios son los de producción, resueltos por el inyector
(`service_resolver(PedidoOrchestrator)`) — la misma wiring que usa la HTTP.

### 3.1 Fixtures

`tests/fixtures/pedido_fixtures.py` (nuevo) y `tests/fixtures/marketplace_fixtures.py`
(ya existente):

| Fixture | Qué es |
|---|---|
| `persona_compradora` / `usuario_comprador` | el comprador: una `Persona` vinculada a una cuenta |
| `usuario_ajeno` | otra cuenta con su propia `Persona`: NO es el comprador |
| `usuario_sin_persona` | cuenta técnica SIN `Persona`: no puede comprar |
| `token_comprador` / `token_ajeno` | tokens JWT |
| `edicion_ajena` | edición de OTRO evento, en BORRADOR |
| `edicion_publicada_sin_tienda` | edición publicada con `marketplace` DESHABILITADO, en su propio evento (para no volver ambigua la resolución de alcance) |
| `producto_con_oferta` | precio `10.00`, oferta vigente `7.00` |
| `producto_inactivo` | `INACTIVO`: no se puede pedir |
| `producto_ajeno` | de otra edición |
| `pedido_orchestrator` | el orquestador resuelto por el inyector de producción |

`tests/factories.py` incorpora `make_item_pedido(...)` y
`make_pedido_payload(...)` para el payload del alta: **el payload no admite
un importe** — sólo `tipo`, `producto_id` y `cantidad`.

---

## 4. Revisión estática de la fuente

Revisión manual del código entregado (sin ejecución). Lo que se comprobó y
lo que se corrigió:

| # | Comprobación | Resultado |
|---|---|---|
| 1 | El total del pedido y el de la compra usan la MISMA expresión | ✓ `Σ (cantidad × precio_aplicado)` redondeado a 2 decimales, idéntica a `commerce.calcular_total`. Si difieran, `COMPRA_TOTAL_INCOHERENTE` (422) rechazaría toda compra |
| 2 | `LineaCompraMarketplace` ↔ `LineaCompraSnapshot` | ✓ mismos campos y tipos, campo por campo |
| 3 | `CompraCreateData` ↔ `CompraMarketplaceData` | ✓ `persona_id`, `origen`, `lineas`, `referencia`, `moneda`, `total` (sólo de contraste) |
| 4 | `Pedido.total` vs `Compra.total` | ✓ el pedido congela el total y la compra lo DERIVA; si no coinciden, `commerce` rechaza — la suma es la misma |
| 5 | La resolución del alcance devuelve un objeto con `modulo_habilitado()` | ✓ `EdicionScopeService.resolver_actual()` devuelve el MODELO `Edicion`, que sí expone `modulo_habilitado(clave)` |
| 6 | `resolver_actual` con nivel 3 (publicada única) | ✓ `permitir_publicada_por_defecto=True`, como en `DOM-04` |
| 7 | Los selectores devuelven listas, no querysets (F-26) | ✓ `listar_detalles` devuelve `list(...)`; `obtener_por_*` devuelven una instancia |
| 8 | El `IntegrityError` se captura FUERA del bloque atómico | ✓ `_crear_pedido_sync` lleva su propio `@transaction.atomic()`; el `except` vive en el flujo, fuera |
| 9 | `update_fields` de `marcar_estado` | ✓ `["estado", "updated_at"]` — `estado_entrega` NO se toca jamás |
| 10 | `update_fields` de `vincular_compra` | ✓ `["compra", "updated_at"]` |
| 11 | Longitudes de los campos frente a sus fuentes | ✓ `huella` 64 = sha256 hex; `token` 64 ≥ 43 de `token_urlsafe(32)`; `concepto_nombre` 200 = `Producto.nombre` 200; `referencia` 200 ≥ 57 |
| 12 | El código de `PedidoNoAutorizadoError` | ✓ `ForbiddenError.__init__` hace `self.code = self.code`: el atributo de la SUBCLASE gana, el código que viaja es `PEDIDO_NO_AUTORIZADO` |
| 13 | La autenticación opcional de `RT-MK-04` | ✓ un token roto lanza `InvalidToken` → manejador global → 401 con el catálogo. NO se usa `OptionalJWTAuth`, que degradaría un token inválido a "invitado" en silencio |
| 14 | La compra se financia con el MISMO snapshot que el pedido | ✓ `_abrir_compra_de` relee el DETALLE congelado del pedido, nunca los precios vigentes del catálogo |
| 15 | La referencia de la compra es estable | ✓ `MARKETPLACE:{pedido_id}:INICIAL` — el identificador se genera ANTES de insertar |
| 16 | El DI resuelve `CompraFlujo` sin duplicar wiring | ✓ `_adaptador_comercio_factory` consume el inyector global (`get_injector()`), donde `CommerceModule` liga `CompraFlujo` y `CompraSelector` |
| 17 | Los `TextChoices` usados en comparaciones de conjunto | ✓ en este módulo `name == value` para todos ellos, así que el `hash` del enum coincide con el de la cadena y la comparación de conjuntos es correcta |
| 18 | `PedidoDetalle.subtotal` | ✓ `(precio_aplicado × cantidad).quantize(0.01)`, la misma expresión que `LineaCompraSnapshot.subtotal` |

### 4.1 Correcciones aplicadas en esta ronda

| # | Corrección | Por qué |
|---|---|---|
| C-01 | `PedidoItemIn.cantidad` y `PedidoItemCreateData.cantidad` ya NO acotan el rango | La regla del rango es del DOMINIO: así el rechazo viaja con `PEDIDO_CANTIDAD_INVALIDA` y no con un 422 de forma del schema. El wire no lleva reglas de negocio |
| C-02 | `POST /pedidos` declara `auth=JWTAuth()` + `permissions=[IsAuthenticated]` | Patrón de `DOM-01`/`DOM-02`; antes heredaba el `auth` global sin declararlo |
| C-03 | `_actor_opcional` usa `core.security.JWTAuth` (no `ninja_jwt` directo) y una sola instancia | El módulo consume la frontera compartida del proyecto; `get_user_model()` no se resuelve en cada petición |
| C-04 | `SCHEMA_VERSION` `1.0.0` → `1.1.0` | Dos rutas y cinco wrappers nuevos = MINOR aditivo (FR-07 §1.2) |
| C-05 | `urls_marketplace.py` registra también `PedidoController` | Sin esto la superficie HTTP del pedido no existe en los tests |
| C-06 | `pedido_orchestrator` declara `db` | La fixture resuelve el inyector: la base debe existir antes |
| C-07 | Se añaden `usuario_sin_persona` y `edicion_publicada_sin_tienda` | Los rechazos `COMPRADOR_SIN_PERSONA` y `MODULO_NO_HABILITADO` necesitaban su escenario |

**Lo que NO se cambió a propósito:** el error de bloqueo de SQLite observado
en la ronda anterior (§6) **NO** motivó ningún cambio de código. El paquete no
lo depura, no lo silencia y no lo reproduce con pruebas concurrentes.

---

## 5. Lo que este paquete NO puede hacer (y por qué)

| Limitación | Consecuencia | Dónde se resuelve |
|---|---|---|
| Las rutas no existen hasta que A0 registre `PedidoController` | el código es muerto por diseño (FR-07 §3.1 regla 2) | A0-01 |
| Los códigos nuevos no están en el catálogo público | el `error.code` es estable, la prosa cae al mensaje genérico del status (F-21) | A0-03 |
| `SCHEMA_VERSION` global desactualizado | el test de drift de A0 fallará hasta que A0 actualice el registro | A0-02 || `RT-MK-04` no está en el ledger | la ruta funciona pero no está ratificada | A0-04 |
| El pago no activa derechos | `RN-C08`: la activación la coordina FND-05 | FND-05 |
| No hay existencias | `RN-M06` | DOM-06 |

---

## 6. Verificación — DIFERIDA POR INSTRUCCIÓN DEL USUARIO

> **Ninguna prueba fue ejecutada en esta ronda.** La instrucción del usuario
> para este paquete y para los siguientes es explícita:
>
> - Crear/actualizar pruebas: **SÍ**.
> - Ejecutarlas: **NO**.
> - No ejecutar `pytest`, `python -m pytest`, `manage.py check`,
>   `makemigrations`, `migrate`, typecheck, lint ni ninguna verificación
>   completa o focalizada.
> - No invocar Python global ni el Python de `.venv`.
> - Cualquier verificación Python posterior exige **autorización explícita**
>   del usuario y **debe usar `uv run`**.
> - El paquete se marca `verification_required`, **no** `completed`.

### 6.1 El SQLite lock observado en la ronda anterior (NO depurado)

La invocación anterior se interrumpió mientras ejecutaba pruebas y dejó a la
vista un **bloqueo de SQLite** (`database is locked`). **Este paquete NO lo
depura**: no se ha reproducido, no se ha instrumentado y **ningún cambio de
código se ha hecho para satisfacerlo**.

Observación estática (NO verificada en ejecución), para que quien verifique
lo tenga en el cuenta: `config/settings/test.py` declara la base SQLite de
pruebas con `"isolation_level": None` (modo autocommit). Ese ajuste es de la
configuración **compartida** (`config/settings/**`), una raíz que este paquete
NO puede editar. La hipótesis —y NO un diagnóstico— es que dos escritores
concurrentes sobre la misma base en modo autocommit se bloquean entre sí. El
diagnóstico real, la mitigación y su verificación pertenecen a A0 y a la fase
de verificación; este paquete **no las asume ni las aplica**.

| # | Comando (workdir `Aplicacion/backend`) | Qué prueba |
|---|---|---|
| V1 | `uv run python -m pytest modules/marketplace/tests -q -k "pedido or snapshot or reglas"` | las 32 pruebas nuevas de `DOM-05` |
| V2 | `uv run python -m pytest modules/marketplace/tests -q` | la suite completa del módulo (35 de DOM-04 + 32 de DOM-05) |
| V3 | `uv run python manage.py makemigrations --check --dry-run` | que la migración `0002_*` coincide con los modelos |
| V4 | `uv run python manage.py check` | que el proyecto carga con el módulo registrado |
| V5 | `uv run python manage.py migrate` → `showmigrations marketplace` → `migrate marketplace zero` → `migrate` | que la migración aplica, revierte y reaplica |
| V6 | `uv run python manage.py migrate --run-syncdb` con SQLite en fichero **FUERA** del repositorio, y `PRAGMA index_list` | que el UNIQUE parcial y los CHECK están en el esquema real |
| V7 | `uv run python -m pytest core/tests -q` | que el baseline de FND-01 sigue verde |
| V8 | `uv run python -m pytest modules/commerce/tests modules/pagos/tests -q` | que los baselines de FND-04/FND-05 siguen verdes |
| V9 | `uv run python -m pytest -q` | la suite completa del objetivo |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | que las raíces prohibidas siguen intactas |
| R2 | `git rev-parse HEAD` | que no hay commit (`f3df5401…` era el punto de rollback; el HEAD actual es `fd1c4c1…`, commit del usuario) |
| R3 | `git stash` | **nunca invocado** |

**Entorno de verificación (para quien la ejecute):** workdir
`Aplicacion/backend` · settings del proyecto (`config.settings.test`,
`DJANGO_SETTINGS_MODULE` en `pytest.ini`) o el overlay
`modules.marketplace.tests.settings_overlay` · **siempre con `uv run`** ·
la base del ensayo **fuera** del repositorio (los `.sqlite3` son un artefacto
prohibido) · el volumen real de media **nunca** se toca.

---

## 7. Peticiones a A0 (registradas, NO aplicadas)

| # | Petición | Prioridad |
|---|---|---|
| **A0-01** | `registrar_controladores(PedidoController)` en `config/api.py` | **BLOQUEANTE** (sin esto las dos rutas no existen) |
| **A0-02** | `SCHEMA_VERSIONS["marketplace"] = "1.1.0"` en `core/contract_versions.py` (el módulo ya declara `1.1.0`: el test de drift fallará hasta que se aplique) | **BLOQUEANTE** para el test de drift || **A0-03** | Catalogar **6** códigos públicos: `PEDIDO_NO_ENCONTRADO` (404) · `PEDIDO_NO_AUTORIZADO` (403) · `PEDIDO_ITEMS_MIXTOS` (422) · `PEDIDO_ITEM_NO_PERMITIDO` (409) · `PEDIDO_CANTIDAD_INVALIDA` (422) | media |
| **A0-04** | Ratificar `RT-MK-04` (`GET /marketplace/pedidos/{token}`) en `route-to-wrapper-ledger.csv` y en `SH-05`, con su presenter `PedidoSeguimientoPresenter` y su wrapper `PedidoSeguimientoOut` | media |
| **A0-05** | Ratificar en el ledger el alcance de `RT-CM-03`: el ledger dice `autenticado_o_invitado` y la implementación exige una cuenta con `Persona` (desviación `D-DOM05-06`) | media |
| **A0-06** | Añadir las dos rutas de `marketplace` al inventario de rutas de `core/tests/integration/test_registration_extension.py` (15 → 17) | media |
| **A0-07** | `*.sqlite3` en el `.gitignore` del objetivo (heredado de DOM-01/FND-01…) | baja |
| **A0-08** | Sincronizar la matriz física `00-matriz-tareas.md` (fila `T-041`) | baja |

`STOCK_INSUFICIENTE` (409) aparece en la fila del ledger de `RT-CM-03` y es
de **`DOM-06`**: este paquete no declara existencias.

**A0-02 es la MISMA clase de petición que A0-DOM02-02.** `DOM-02` ya dejó
`modules/salesianos_fest` en `1.1.0` con el registro global en `1.0.0`: el
test de drift de `core/tests/integration/test_contract_versions.py` (raíz
compartida y **prohibida** para este paquete) falla hoy por `salesianos_fest`
y, con este paquete, también por `marketplace`. La actualización del registro
—`"salesianos_fest": "1.1.0"` y `"marketplace": "1.1.0"`— es **una sola**
petición que cierra las dos a la vez.

---

## 8. Desviaciones y decisiones

| # | Desviación | Motivo |
|---|---|---|
| `D-DOM05-01` | El pedido se implementa como modelo PROPIO (`Pedido`/`PedidoDetalle`), no como una `Compra` con líneas | `Compra` no tiene detalle: su `lineas_snapshot` es un JSON. El detalle con precio CONGELADO es lo que RN-M03 exige ("pedido y su detalle registran cantidades y precio aplicado") |
| `D-DOM05-02` | El pedido REFERENCIA la compra (`compra` FK) en vez de duplicar su estado | La compra es un hecho de `commerce` (RN-C01, `D-FND-04-06`): el pedido la referencia y NO la sustituye. La FK es `PROTECT` |
| `D-DOM05-03` | El estado del PAGO no se guarda en el pedido: se PROYECTA desde `Compra` | Un único dueño del hecho. Guardarlo sería una segunda fuente de verdad que puede divergir |
| `D-DOM05-04` | El reintento se identifica por la HUELLA de los artículos (artículo + cantidad), no por el precio | Una oferta posterior no abre una intención nueva: el reintento recupera el MISMO pedido con su snapshot (RN-M03) |
| `D-DOM05-05` | La cantidad la valida el DOMINIO, no el schema del cable | El rechazo viaja con el código estable `PEDIDO_CANTIDAD_INVALIDA`. El wire no lleva reglas de negocio |
| `D-DOM05-06` | `RT-CM-03` exige una **cuenta con `Persona` vinculada**, no un invitado | `Compra.persona` es obligatorio y el documento NO es una credencial (RN-U04). La compra de invitado con datos de comprador es un flujo de IDENTIDAD (`RT-ID-02`/`RT-ID-03`), fuera de este paquete. El ledger dice `autenticado_o_invitado`: se pide su ratificación (A0-05) |
| `D-DOM05-07` | `GET /pedidos/{token}` es una ruta NUEVA (`RT-MK-04`), no está en el ledger | La necesita `SHOP-03` (`/tienda/pedidos/[token]`), que la referencia explícitamente. Se pide su ratificación (A0-04) |
| `D-DOM05-08` | El adaptador de `commerce` se construye por una **fábrica perezosa** en el DI | `commerce` liga su `CompraFlujo` en su propio módulo: consumirlo por el inyector mantiene el grafo acíclico y no duplica el wiring ajeno |
| `D-DOM05-09` | `SCHEMA_VERSION` de `marketplace` sube a `1.1.0` | Cambio aditivo (dos rutas, cinco wrappers). El registro global es de A0 → A0-02 |
| `D-DOM05-10` | La authentication opcional de `RT-MK-04` NO usa `OptionalJWTAuth` | `OptionalJWTAuth` degrada un token ROTO a "invitado" en silencio; aquí una credencial rota responde 401 (FR-01 §4.4: 401 antes que 403) |
| `D-DOM05-11` | Los pagos se consideran por el ESTADO de la compra, no por el veredicto operativo | `EstadoOperativoPagoService` es de FND-04 y publica incidencias que no son estados del pedido. El pedido refleja el hecho COMERCIAL |
| `D-DOM05-12` | Ninguna prueba concurrente | La carrera se decide en el índice parcial único; verificarla con hilos es material de la fase de verificación, no de este paquete (y reintroduciría el bloqueo de SQLite observado) |

**Decisiones abiertas nuevas:**

- `OD-DOM05-01` — el alcance de `RT-CM-03` (`autenticado_o_invitado` vs
  `autenticado`): depende de si la compra de invitado con datos de comprador
  entra en el alcance de `DOM-05` o en el de IDENTIDAD (A0-05).
- `OD-DOM05-02` — la forma del dinero en el cable: sigue heredada y ABIERTA
  (`OD-A0R2-01`); este paquete mantiene `Decimal` de punta a punta y fija el
  comportamiento OBSERVADO (cadena decimal) en sus pruebas.
- `OD-DOM05-03` — `STOCK_INSUFICIENTE` y la estrategia anti-sobreventa: las
  decide `DOM-06` (RN-M06, `PD-05`).

---

## 9. Rollback

Punto de rollback: **`fd1c4c123df3767ef6e86908565edf2d4c27c00a`** (HEAD al
inicio de esta ronda; commit del usuario, **no** de este paquete). Este
paquete **NO creó commit** y **`git stash` nunca se invocó**.

1. `uv run python manage.py migrate marketplace zero` (sólo si A0 lo autoriza:
   la migración es reversible por construcción) y borrar
   `Aplicacion/backend/modules/marketplace/migrations/0002_*`.
2. Borrar los ficheros de `DOM-05` de `modules/marketplace/`: `domain/models/pedido.py`,
   `domain/ports/comercio.py`, `domain/results/pedido_result.py`,
   `domain/schemas/pedido_schemas.py`, `domain/selectors/pedido_selector.py`,
   `domain/services/core/pedido_core_service.py`,
   `domain/services/flujos/pedido_flujo.py`,
   `domain/services/orchestrators/pedido_orchestrator.py`,
   `infrastructure/services/comercio_adapter.py`,
   `presentation/controllers/pedido_controller.py`,
   `presentation/presenters/pedido_presenter.py`,
   `presentation/schemas/pedido_schemas.py` y las pruebas de `DOM-05`.
3. Revertir `modules/marketplace/{di,admin,models}.py`,
   `domain/{constants,exceptions}.py`, `domain/models/__init__.py`,
   `presentation/schemas/__init__.py` y `tests/{conftest,factories,urls_marketplace}.py`
   a su estado previo.
4. Revertir `Aplicacion/task/salesianos-fest-rebuild/STATE.md` (fila DOM-05 +
   esta transición) y los topics de Engram.
5. **NO tocar** `Aplicacion/backend/media/`: el volumen es estado durable.

**El historial comercial y de pagos se preserva**: este rollback nunca borra
una compra, una orden de pago ni una transacción.

---

## 10. Preparación de `DOM-06` (PROVISIONAL, pendiente de verificación)

`DOM-06` (inventario, reserva y entrega) consume la interfaz congelada de este
paquete. Lo que queda DISPONIBLE:

| Elemento | Qué ofrece `DOM-05` |
|---|---|
| `Pedido.estado_entrega` | el campo EXISTE (`PENDIENTE`) y `DOM-06` lo avanza; `DOM-05` nunca lo toca |
| `PedidoDetalle` | el detalle congelado: producto, cantidad y precio aplicado — la base de la reserva |
| `Pedido.compra` | la compra que financia el pedido: el pago ya es un hecho separado y consultable |
| `EstadoEntregaPedido` | el vocabulario cerrado (`PENDIENTE` · `ENTREGADO`) ya declarado |
| `Pedido.huella` / `Pedido.token` | la identidad de la intención y la credencial del enlace |
| `Producto` | SIN campo `stock`: `DOM-06` puede añadirlo con una migración aditiva `003_*` |

**LO QUE `DOM-06` DEBE HACER (y este paquete NO hizo):**

1. Declarar el stock del producto (migración aditiva).
2. Reservar/descontar existencias dentro de la transacción, con estrategia
   anti-sobreventa (RN-M06) — y **no descontar dos veces** por webhook.
3. Mover `Pedido.estado_entrega` de `PENDIENTE` a `ENTREGADO`, registrando el
   operador y el consumo (QA-V01/QA-V02).
4. Registrar los movimientos de inventario con producto, signo, cantidad,
   motivo, referencia de origen y actor (RN-M04, QA-M02).
5. Emitir `STOCK_INSUFICIENTE` (409), que el ledger ya atribuye a `RT-CM-03`.

> **LISTO, PERO PROVISIONAL.** La interfaz está congelada y es coherente, pero
> **ninguna de estas garantías ha sido verificada en ejecución** (§6). `DOM-06`
> no debe consumirlas como hechos probados hasta que `DOM-05` se cierre con
> `uv run` y las 32 pruebas devuelvan verde.

---

## 11. Concurrencia

`Aplicacion/backend/modules/salesianos_fest/**` (**DOM-02**, A3) y
`Aplicacion/frontend/**` (FND-06 / UI-01A, otro agente) **no fueron tocados,
revertidos ni fusionados**. Las filas del tablero de `DOM-02` y del frontend
se conservaron intactas. `modules/commerce`, `modules/pagos`, `modules/eventos`
y `modules/usuarios` **no fueron editados**: este paquete los CONSUME a través
del puerto y del adaptador, nunca los modifica.

Durante este paquete el árbol recibió además **trabajo concurrente de otros
agentes**: un módulo de autenticación nuevo en `modules/usuarios/**`
(FND-03A: `AuthController`, `auth_flujo`, `auth_orchestrator`, `auth_schemas`,
sus fixtures y tres ficheros de test de integración) registrado en
`config/api.py`, y cambios en `Aplicacion/frontend/src/**`. **DOM-05 no tocó,
revirtió ni fusionó nada de eso**, y no editó las filas del tablero de
`usuarios` ni del frontend.

Ningún archivo compartido de A0 (`config/api.py`,
`config/settings/base.py`, `core/exceptions.py`, `core/contract_versions.py`,
`core/responses.py`, `core/permissions.py`, `core/security.py`) fue editado:
sus ajustes se piden como evidencia (§7).

---

## 12. Siguiente paquete

**DOM-06** — *Reserva de inventario y entrega*
(`wave-02-domain-backend/DOM-06-inventory-reservation-delivery.md`).

Precondición: la verificación de `DOM-05` con `uv run` (§6.1), que hoy está
**diferida por instrucción del usuario**.
