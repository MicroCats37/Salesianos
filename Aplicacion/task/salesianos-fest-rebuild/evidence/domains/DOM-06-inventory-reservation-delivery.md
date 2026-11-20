# DOM-06 - Inventario, reserva anti-sobreventa y entrega

**Artifact:** `evidence/domains/DOM-06-inventory-reservation-delivery.md` · **Packet:** `DOM-06`
(`wave-02-domain-backend`) · **Change:** `salesianos-fest-rebuild` · **Owner:** A5
**Original task IDs:** `T-042`, `T-043` — 2 de los 54 IDs del plan (acumulado con
GOV-00/01/02, FND-01…FND-05, DOM-01…DOM-05: **22 de 54**)
**Freezes respetados:** `FREEZE-CM-1.0.0` (FR-04) · `FREEZE-MD-1.0.0` (FR-06) ·
`FREEZE-ED-1.0.0` (FR-02) · `FREEZE-PS-1.0.0` (FR-07) · `FREEZE-ENV-1.0.0` (FR-01) ·
`FREEZE-TC-1.0.0`

> **ESTADO: `completed`.** El código y la **evidencia de ejecución** están
> entregados: la suite focalizada del módulo es VERDE (§6) y las puertas de
> Django son verdes. Las peticiones a A0 de §7 siguen ABIERTAS (son de A0, no
> de este paquete) y no impiden el cierre del paquete.

---

## 1. Qué se entregó

El **inventario** de la tienda: la bitácora de movimientos, las reservas que
sostienen la anti-sobreventa, el efecto de stock de un pago confirmado y el
acta de entrega.

### 1.1 Los TRES hechos del inventario (`RN-M06`)

| # | Hecho | Dónde vive | Quién lo mueve |
|---|---|---|---|
| 1 | `stock` — unidades FÍSICAS | `Producto.stock` | el servicio de inventario |
| 2 | `reservado` — unidades APARTADAS por pedidos pendientes | `Producto.reservado` | el servicio de inventario |
| 3 | `estado_entrega` — el hecho de la ENTREGA | `Pedido.estado_entrega` | `PedidoFlujo` (`DOM-06`) |

`disponible = stock − reservado`. El **servidor** lo calcula
(`Producto.disponible`); el cliente no inventa disponibilidad
(`frontend/03` §SHOP-01: "el catálogo nunca inventa stock disponible").

### 1.2 `PD-05` — DECIDIDO: el stock es POR EDICIÓN

`PD-05` ("¿stock compartido entre ediciones o separado por edición?") estaba
ABIERTO en `FR-09` con owner "A5 + producto". **Este paquete lo decide y lo
declara:**

> **El inventario es POR EDICIÓN.** El stock vive en el producto, y el
> producto pertenece a UNA edición (`Producto.edicion` es obligatoria y el
> slug es único por edición). El clave del inventario es el **producto** y,
> transitivamente, la **edición**. NO existe un pool compartido entre
> ediciones: no hay identidad de producto transversal entre ediciones, así
> que un pool compartido exigiría inventar esa identidad.

**Consecuencia operativa:** una edición que necesita el mismo artículo lo
declara con su propio producto. Una reposición en una edición **NO** repone
la edición siguiente.

### 1.3 Modelos (`domain/models/`)

```
Producto (MODIFICADO — migración aditiva 0003)
  stock      = PositiveInteger(default=0)   unidades físicas; 0 = AGOTADO
  reservado  = PositiveInteger(default=0)   unidades apartadas por pedidos
  CHECK (reservado <= stock)                 lo reservado NUNCA supera lo físico
  propiedad `disponible` = stock - reservado

MovimientoInventario (NUEVO — LA BITÁCORA)
  id, created_at, updated_at
  producto     FK → Producto (PROTECT)
  cantidad     Integer CON SIGNO  (+ entrada, − salida)      [RN-M04]
  tipo         VENTA | REPOSICION | MERMA | CONSUMO_INTERNO
             | AJUSTE | SALIDA_SIN_VENTA | REVERSION
  motivo       CharField(200)      obligatorio
  referencia   CharField(200) UNIQUE   ← la referencia de ORIGEN
  actor        FK → usuarios.Usuario (PROTECT, null)   obligatorio en los manuales
  compensatorio FK → self (PROTECT, null)   ← la reversa apunta al original
  CHECK (cantidad <> 0)
  INMUTABLE: save() sobre una fila existente y delete() LANZAN
             `MOVIMIENTO_INVENTARIO_INMUTABLE`

ReservaInventario (NUEVO — LA UNIDAD ANTI-SOBREVENTA)
  id, created_at, updated_at
  producto     FK → Producto (PROTECT)
  pedido       FK → Pedido (PROTECT)
  cantidad     PositiveInteger
  estado       ACTIVA | CONFIRMADA | LIBERADA
  referencia   CharField(200)   `PEDIDO:{pedido_id}:{producto_id}`
  UNIQUE (pedido, producto)     ← un pedido reserva cada producto UNA vez
  CHECK (cantidad >= 1)

EntregaPedido (NUEVO — EL ACTA DE ENTREGA)
  id, created_at, updated_at
  pedido         FK → Pedido (PROTECT)
  actor          FK → usuarios.Usuario (PROTECT)   el operador
  referencia     CharField(200) UNIQUE   `PEDIDO:{pedido_id}:ENTREGA`
  cantidad_total PositiveInteger
  detalle        JSONField   el snapshot de lo entregado
  UNIQUE (pedido)            ← una entrega por pedido (idempotencia)
  CHECK (cantidad_total >= 1)
```

### 1.4 La bitácora es INMUTABLE (`RN-M04`)

`MovimientoInventario.save()` lanza `MovimientoInmutableError` si la fila ya
existe y `delete()` lanza siempre. El Django Admin de los tres modelos nuevos
es de **SOLO LECTURA** (`has_add_permission` / `has_change_permission` /
`has_delete_permission` en `False`): la bitácora la escribe el DOMINIO.

Una corrección es un movimiento **COMPENSATORIO**: `revertir_movimiento`
crea un `REVERSION` con el signo contrario, su propio `actor` y su `motivo`,
enlazado al original por `compensatorio`.

### 1.5 Una salida sin venta NO es una compra (`RN-M05` · `QA-M02`)

`registrar_movimiento` (`MERMA`, `CONSUMO_INTERNO`, `SALIDA_SIN_VENTA`,
`REPOSICION`, `AJUSTE`) ajusta el stock y escribe el movimiento. **No crea
`Compra`, ni `OrdenPago`, ni `Pedido`.** La prueba
`test_una_salida_sin_venta_no_crea_compra_ni_pago` lo comprueba contando las
filas de `commerce.Compra` y `pagos.OrdenPago` (0 y 0).

### 1.6 La estrategia anti-sobreventa (`RN-M06` · `QA-M01`)

**RESERVA TEMPORAL con protección transaccional.** La opción "reservar
temporalmente" de `RN-M06`, implementada con el patrón de **sentencia
condicional** que ya usa `DOM-02` (`F-55` · `F-64`): la condición viaja
DENTRO de la sentencia y la base de datos decide.

```sql
-- Apartar N unidades (al crear el pedido)
UPDATE marketplace_producto SET reservado = reservado + N
 WHERE id = ? AND stock >= reservado + N;
```

Si la sentencia actualiza **cero** filas, no hay disponibilidad y el pedido
se rechaza con `STOCK_INSUFICIENTE` (409). **No se usa `select_for_update`**
(SQLite no lo soporta: `F-55`).

**El ciclo de la reserva:**

| Momento | `reservado` | `stock` | `ReservaInventario` |
|---|---|---|---|
| Pedido `PENDIENTE` creado | +N | sin cambio | `ACTIVA` |
| Pedido `CANCELADO` | −N | sin cambio | `LIBERADA` |
| Pago confirmado (activación) | −N | −N | `CONFIRMADA` + movimiento `VENTA` |

La reserva se crea **DENTRO de la misma transacción** que el alta del pedido
(`PedidoFlujo._crear_pedido_sync`): si el stock no alcanza, no queda un pedido
a medias, y si el alta pierde una carrera por la misma intención, la reserva
se revierte con ella (sólo el ganador reserva unidades).

### 1.7 El efecto de stock del pago, EXACTAMENTE una vez (`FR-04` I-2, I-3)

`ActivadorMarketplace` implementa el puerto **CONGELADO** de `commerce`
(`IActivadorDominioCompra`) para el origen `OrigenCompra.MARKETPLACE` y se
registra en `apps.py::ready()`, igual que `ActivadorPase` y
`ActivadorInscripcion`. **Los interiores de `commerce` y de `pagos` NO se
editaron**: este paquete CONSUME el puerto.

Doble red contra el doble descuento:

1. **La reserva es la autoridad**: la transición `ACTIVA → CONFIRMADA` es
   CONDICIONAL (`WHERE estado='ACTIVA'`). Si ya está `CONFIRMADA`, la segunda
   activación no hace nada.
2. **El movimiento tiene una REFERENCIA ÚNICA**
   (`PEDIDO:{pedido_id}:{producto_id}`): un segundo movimiento con la misma
   referencia es imposible en base de datos.

Resultado: `activar()` dos veces deja el stock descontado **una sola vez** y
**un solo** movimiento de venta (`STOCK_CONFIRMADO` y luego
`STOCK_YA_CONFIRMADO`).

### 1.8 La entrega es un hecho POSTERIOR (`RN-M07` · `QA-M04`)

`PedidoFlujo.confirmar_entrega(pedido_id, actor)`:

- exige un pedido **PAGADO** (`PEDIDO_NO_PAGADO` 409 si no lo está);
- mueve **SÓLO** `estado_entrega` (`marcar_estado_entrega` escribe
  `["estado_entrega", "updated_at"]`);
- crea **UN** `EntregaPedido` (UNIQUE por pedido) con el actor, la cantidad y
  el detalle de lo entregado;
- **no vuelve a mover el stock**: el stock ya salió en la VENTA. La entrega
  no es una segunda salida.

**IDEMPOTENTE Y REINTENTABLE**: confirmar dos veces devuelve el **mismo**
acta (mismo `entregada_en`); una carrera de dos confirmaciones la resuelve la
restricción única (`IntegrityError` → se lee el acta ganadora).

**ENTREGA COMPLETA, NO PARCIAL.** `RN-M07` sólo admite entrega parcial "si se
aprueba ese uso" y esa aprobación NO existe (`PD-03` sigue ABIERTO, owner
A4 + A8 + producto). Este paquete entrega el pedido COMPLETO y lo deja
dicho, en vez de inventar el consumo por unidad.

### 1.9 La frontera con `commerce` (NO se editó)

`marketplace` NO importa `commerce`. El pago se llega por el puerto ya
existente de `DOM-05` (`ICommerceMarketplaceService`) y el efecto de stock lo
produce el activador, que consume el puerto de `commerce`. **Cero ediciones**
en `modules/commerce/**` y `modules/pagos/**`.

### 1.10 Vocabulario cerrado (`domain/constants.py`)

| Clase | Valores |
|---|---|
| `EstadoReservaInventario` | `ACTIVA` · `CONFIRMADA` · `LIBERADA` |
| `TipoMovimientoInventario` | `VENTA` · `REPOSICION` · `MERMA` · `CONSUMO_INTERNO` · `AJUSTE` · `SALIDA_SIN_VENTA` · `REVERSION` |
| `SIGNO_MOVIMIENTO_MANUAL` | el signo que impone cada naturaleza (`AJUSTE` declara el suyo) |

### 1.11 Rutas (PROVISIONALES · SH-05 §1.6 · RB-07)

| Ruta | Método | Scope | Permiso | Errores |
|---|---|---|---|---|
| `RT-MK-08` | GET `/administracion/marketplace/inventario` | implícito | `Administrador` | `MODULO_NO_HABILITADO` 409 |
| `RT-MK-09` | POST `/administracion/marketplace/inventario/movimientos` | implícito | `Administrador` | `PRODUCTO_NO_ENCONTRADO` 404 · `STOCK_INSUFICIENTE` 409 · `MOVIMIENTO_INVENTARIO_INVALIDO` 422 |
| `RT-MK-12` | POST `/administracion/marketplace/inventario/movimientos/{id}/revertir` | implícito | `Administrador` | `MOVIMIENTO_INVENTARIO_NO_ENCONTRADO` 404 · `STOCK_INSUFICIENTE` 409 |
| `RT-MK-10` | GET `/administracion/marketplace/entregas` | implícito | `Administrador` | `MODULO_NO_HABILITADO` 409 |
| `RT-MK-11` | POST `/administracion/marketplace/entregas/{pedido_id}/confirmar` | implícito | `Administrador` | `PEDIDO_NO_ENCONTRADO` 404 · `PEDIDO_NO_PAGADO` 409 · `PEDIDO_NO_ENTREGABLE` 409 |

`RT-MK-08`…`RT-MK-10` vienen del registro provisional `SH-05` §1.6;
`RT-MK-11` (confirmación de entrega) y `RT-MK-12` (reversa) son **nuevas** y
se piden como ratificación (A0-04).

**NO registradas en `config/api.py`**: son rutas PROVISIONALES y `config/api.py`
es de A0 (petición A0-01). Se registran SÓLO en el URLconf de test
(`tests/urls_marketplace.py`), como hizo `DOM-03` con sus rutas provisionales.

### 1.12 Presenters y wrappers

| Ruta | Presenter | Wrapper de salida | Wrapper de entrada |
|---|---|---|---|
| `RT-MK-08` | `InventarioPresenter` | `InventarioProductoOut` | — |
| `RT-MK-09` | `InventarioPresenter` | `MovimientoInventarioOut` | `RegistrarMovimientoInventarioIn` |
| `RT-MK-12` | `InventarioPresenter` | `MovimientoInventarioOut` | `RevertirMovimientoInventarioIn` |
| `RT-MK-10` | `EntregaPresenter` | `EntregaPendienteOut` | — |
| `RT-MK-11` | `EntregaPresenter` | `EntregaConfirmadaOut` | — |

`PedidoLineaOut` (de `DOM-05`) se **REUTILIZA** en las dos salidas de
entrega: el detalle entregado es el detalle del pedido, con su precio
congelado (`SCHEMA_DRY_INTENTION`).

**El wire NO decide reglas**: la cantidad del movimiento es con signo y la
valida el DOMINIO contra la naturaleza; el precio, el stock disponible y la
autorización los decide el servidor (`RN-C02` · `RN-M06` · `RN-A01`).

`SCHEMA_VERSION` de `marketplace`: `1.1.0` → **`1.2.0`** (MINOR aditivo: cinco
rutas y seis wrappers nuevos; no se elimina ni se renombra nada).

---

## 2. Migraciones

`modules/marketplace/migrations/0003_entregapedido_movimientoinventario_reservainventario_and_more.py`

- Depende de `("marketplace", "0002_pedido_pedidodetalle_and_more")`,
  `("eventos", "0001_initial")` y `swappable_dependency(AUTH_USER_MODEL)`.
- **GENERADA con `makemigrations`** (no escrita a mano): el autodetector la
  produjo desde los modelos, así que el modelo y la migración coinciden por
  construcción (a diferencia de `DOM-03`, cuya `0003` fue escrita a mano).
- Crea `EntregaPedido`, `MovimientoInventario` y `ReservaInventario`; añade
  `stock` y `reservado` a `Producto`; crea las restricciones:

| Restricción | Tipo | Qué protege |
|---|---|---|
| `marketplace_producto_reservado_no_excede_stock` | CHECK | lo reservado nunca supera lo físico |
| `marketplace_movimiento_cantidad_no_cero` | CHECK | un movimiento tiene cantidad ≠ 0 |
| `marketplace_reserva_unica_por_pedido_producto` | UNIQUE | un pedido reserva cada producto una vez |
| `marketplace_reserva_cantidad_valida` | CHECK | cantidad reservada ≥ 1 |
| `marketplace_entrega_unica_por_pedido` | UNIQUE | una entrega por pedido (idempotencia) |
| `marketplace_entrega_cantidad_valida` | CHECK | cantidad entregada ≥ 1 |
| `marketplace_movimiento_inventario.referencia` | UNIQUE | un movimiento de venta por referencia (`FR-04` I-3) |
| `ix_mkt_movimiento_producto` | índice | bitácora por producto |
| `ix_mkt_reserva_producto` | índice | reservas por producto |

Los nombres de índice se acortaron a ≤ 30 caracteres (`models.E034`).

**El esquema real en SQLite fue inspeccionado** (§6, V8): las seis
restricciones están en el esquema, no sólo en el código.

---

## 3. Lo que este paquete NO implementa (y por qué)

| Fuera de alcance | Por qué | Dónde vive |
|---|---|---|
| la entrega por unidad / parcial | `RN-M07` sólo la admite "si se aprueba"; `PD-03` sigue ABIERTO | A4 + A8 + producto |
| el ticket y el consumo por el servicio compartido de validaciones | `RB-07` asigna la confirmación al servicio COMÚN | A8 (`XCT-01` / `T-081`) |
| el precio de la venta en el movimiento | el precio lo congela `DOM-05`; el movimiento es de unidades | `DOM-05` |
| la EXPIRACIÓN de una reserva | la política ("reserva de stock vence") no está decideda | **OD-DOM06-01** (§8) |
| la política de REEMBOLSOS/devoluciones | `PD-06` (commerce), no de inventario | `commerce` |
| el registro de las rutas en `config/api.py` | `config/api.py` es de A0 | A0-01 |
| el catálogo público de los códigos nuevos | `core/exceptions.py` es de A0 | A0-03 |

---

## 4. Pruebas (behavior-first) — **28 nuevas, todas verdes**

| Fichero | Tests | Qué cubre |
|---|---|---|
| `tests/integration/test_inventario_reserva.py` | 5 | la reserva aparta unidades · producto agotado rechazado · exceso de stock rechazado · **dos pedidos pendientes no sobrevenden** (`QA-M01`) · la cancelación libera la reserva |
| `tests/integration/test_inventario_movimientos.py` | 5 | **la salida sin venta NO crea compra ni pago** (`QA-M02`) · la bitácora es inmutable · la reversa compensa el original · el signo incoherente se rechaza · una salida mayor que el stock se rechaza |
| `tests/integration/test_activador_marketplace.py` | 3 | el módulo registra su activador para `MARKETPLACE` · la activación confirma el stock UNA vez · **una activación repetida no descuenta dos veces** (`FR-04` I-3) |
| `tests/integration/test_entrega_pedido.py` | 5 | la entrega mueve SÓLO el estado de entrega · un pedido no pagado no se entrega · **la entrega es idempotente y reintentable** · el acta registra actor y cantidades · la entrega no vuelve a mover el stock |
| `tests/e2e/test_inventario_controller.py` | 10 | 401 sin credencial · 403 para un usuario normal · el inventario muestra los TRES hechos · el movimiento actualiza el stock y la bitácora · el signo incoherente responde 422 · una VENTA no se registra a mano · la reversa compensa · la cola de entregas · la confirmación y su reintento · un pedido no pagado responde 409 |

**Sin mocks**: los servicios son los de producción, resueltos por el
inyector real (`service_resolver(PedidoOrchestrator)` /
`service_resolver(InventarioOrchestrator)`).

**La carrera simultánea REAL** (dos hilos) se verifica en la fase de
verificación (`VER-01…VER-03`), como en `DOM-05`: aquí se comprueba la MISMA
GARANTÍA de forma determinista — el segundo pedido se rechaza porque las
unidades ya están reservadas por el primero.

### 3.1 Fixtures

`tests/fixtures/inventario_fixtures.py` (nuevo): `producto_con_stock` (10
unidades) · `producto_agotado` (0 unidades) · `inventario_orchestrator` (por
inyector) · `pedido_pagado` (compra pagada + entrega `PENDIENTE`).

**Cambio en las fixtures existentes (deliberado y visible).** `DOM-06`
introduce el control de existencias: un producto sin `stock` declarado está
AGOTADO y no se puede pedir (`RN-M06`). Las dos fixtures de producto que
sirven para pedir (`producto` y `producto_con_oferta`) **declaran ahora
`stock = 100`** (`STOCK_EJEMPLO`). Sin ese cambio, las 69 pruebas de
`DOM-04`/`DOM-05` que crean pedidos pasarían a recibir `STOCK_INSUFICIENTE`.
**No se cambió ninguna aserción de `DOM-04`/`DOM-05`**: sólo el dato de
entrada.

---

## 5. Revisión estática de la fuente

| # | Comprobación | Resultado |
|---|---|---|
| 1 | La reserva se crea DENTRO de la transacción del alta | ✓ `_crear_pedido_sync` es `@transaction.atomic()` y llama a `reservar_para_pedido` |
| 2 | La condición de disponibilidad viaja en la sentencia | ✓ `filter(stock__gte=F("reservado") + cantidad).update(...)` |
| 3 | `select_for_update` NO se usa | ✓ (SQLite no lo soporta: `F-55`) |
| 4 | El `IntegrityError` del alta se captura FUERA del bloque atómico | ✓ (pre-existente de `DOM-05`, intacto) |
| 5 | `marcar_estado` NUNCA toca `estado_entrega` | ✓ `update_fields=["estado", "updated_at"]` |
| 6 | `marcar_estado_entrega` NUNCA toca `estado` | ✓ `update_fields=["estado_entrega", "updated_at"]` |
| 7 | `marcar_estado_entrega` NUNCA toca el stock | ✓ el stock sólo se mueve en el servicio de inventario |
| 8 | Una salida sin venta no crea compra/pago/pedido | ✓ el flujo de inventario no importa `commerce` ni `pagos` |
| 9 | El movimiento es inmutable | ✓ `save()` sobre fila existente y `delete()` lanzan |
| 10 | La reversa NO borra ni edita el original | ✓ crea una fila nueva con `compensatorio` |
| 11 | La referencia del movimiento de venta es ÚNICA | ✓ `UNIQUE` en la columna + `PEDIDO:{pedido}:{producto}` |
| 12 | La transición de la reserva es CONDICIONAL | ✓ `filter(id=…, estado=ACTIVA).update(...)` |
| 13 | `updated_at` se actualiza en los `.update()` | ✓ `auto_now` no dispara en `.update()`: se fija `timezone.now()` explícitamente |
| 14 | Los selectores devuelven LISTAS (F-26) | ✓ `list(...)` en `InventarioSelector` y `PedidoSelector` |
| 15 | El presentador NO consulta la base de datos | ✓ `InventarioPresenter` / `EntregaPresenter` son transformadores puros |
| 16 | El controller NO tiene `if` de negocio | ✓ hidrata, delega y devuelve `success_response` |
| 17 | El `detalle` de la entrega es el MISMO detalle del pedido | ✓ `PedidoCoreService.result_lineas` es el bloque compartido |
| 18 | `SCHEMA_VERSION` del módulo y el registro global coinciden | ✓ `1.2.0` en ambos (§6, V5) |
| 19 | El nombre de los índices cabe en 30 caracteres | ✓ `ix_mkt_movimiento_producto`, `ix_mkt_reserva_producto` |
| 20 | `Producto.reservado <= Producto.stock` | ✓ CHECK en base de datos, no sólo en el código |
| 21 | Los errores de dominio llevan `code` estable | ✓ 8 códigos nuevos declarados (§7, A0-03) |
| 22 | La excepción de la subclase es la que viaja | ✓ `MovimientoInmutableError` define su propio `code` |
| 23 | `Pedido.estado_entrega` sólo lo mueve `DOM-06` | ✓ `DOM-05` no lo toca (verificado por la suite de `DOM-05`) |

### 5.1 Correcciones aplicadas durante el paquete

| # | Corrección | Por qué |
|---|---|---|
| C-01 | Los índices se renombraron a ≤ 30 caracteres | `models.E034` bloqueaba el `makemigrations` |
| C-02 | `present_inventario_lista` usaba `resulto` en vez de `resultado` | `NameError` en la primera ejecución de la suite |
| C-03 | La confirmación de entrega toleraba la carrera con `IntegrityError` → se lee el acta ganadora | dos operadores simultáneos no deben duplicar el acta |

---

## 6. Verificación — EJECUTADA (todas con `uv run`)

Workdir `Aplicacion/backend`. `uv run --group dev` en todo caso; nunca el
Python global ni el de `.venv`. La base de ensayo de las migraciones fue un
SQLite **FUERA** del repositorio y se borró al terminar.

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V0 | `uv run --group dev pytest modules/marketplace/tests -q` (LÍNEA BASE, antes de tocar nada) | **0** | **69 passed** — el baseline de `DOM-04`/`DOM-05` |
| V1 | `uv run --group dev pytest modules/marketplace/tests -q` (tras el paquete) | **0** | **97 passed** (69 previos + 28 nuevos) — **sin regresiones** |
| V2 | `uv run --group dev python manage.py makemigrations marketplace` | **0** | generó `0003_*` (la migración coincide con los modelos) |
| V3 | `uv run --group dev python manage.py makemigrations marketplace --check --dry-run --settings=modules.marketplace.tests.settings_overlay` | **0** | `No changes detected in app 'marketplace'` |
| V4 | `USE_SQLITE=true SQLITE_PATH=:memory: uv run --group dev python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced)` |
| V5 | `uv run --group dev python manage.py migrate --settings=…overlay` (SQLite en fichero fuera del repo) | **0** | `Applying marketplace.0003_… OK` |
| V6 | `uv run --group dev python manage.py showmigrations marketplace --settings=…overlay` | **0** | `[X] 0001_initial` · `[X] 0002_…` · `[X] 0003_…` |
| V7 | `uv run --group dev python manage.py migrate marketplace zero` → `migrate marketplace` (replay) | **0** | reversible y reproducible |
| V8 | inspección del esquema SQLite real | **0** | CHECK `reservado <= stock` · UNIQUE `(pedido_id, producto_id)` · UNIQUE `pedido_id` (entrega) · UNIQUE `referencia` (movimiento) · CHECK `cantidad <> 0` · CHECK `cantidad >= 1` |
| R1 | `git status --short -- Aplicacion/backend/modules/marketplace` | **0** | sólo ficheros de `marketplace` |
| R2 | `git rev-parse HEAD` | **0** | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` — **sin commit** |
| R3 | `git stash` | — | **nunca invocado** |
| R4 | barrido de residuos (`*.sqlite3` de ensayo) | **0** | el SQLite de ensayo se borró; `db.sqlite3` es un artefacto PREEXISTENTE y su hash NO cambió con `manage.py check` (comprobado antes/después) |

**Baseline conocido (no es una regresión de este paquete):**
`makemigrations --check --dry-run` **sin** filtro de app falla porque
`modules/salesianos_fest` tiene un cambio pendiente de `DOM-03`
(`0004_alter_comprapase_token_revocado_en`). `modules/salesianos_fest/**` es
una raíz PROHIBIDA para este paquete: se registra como **A0-07** y se
reporta como hallazgo, sin tocarlo.

**Sin regresiones:** las 69 pruebas previas de `DOM-04`/`DOM-05` siguen
verdes; el único cambio en sus fixtures es el dato `stock` (§3.1).

---

## 7. Peticiones a A0 (registradas, NO aplicadas)

| # | Petición | Prioridad |
|---|---|---|
| **A0-01** | registrar `InventarioController` en `config/api.py` (y `PedidoController`, pendiente de `DOM-05`) | **BLOQUEANTE** (sin esto las rutas no existen) |
| **A0-02** | `SCHEMA_VERSIONS["marketplace"] = "1.2.0"` en `core/contract_versions.py` | **BLOQUEANTE** para el test de drift (el registro ya decía `1.2.0` al correr la suite: lo actualizó A0 en paralelo — confirmar) |
| **A0-03** | catalogar **8** códigos públicos: `STOCK_INSUFICIENTE` (409) · `MOVIMIENTO_INVENTARIO_NO_ENCONTRADO` (404) · `MOVIMIENTO_INVENTARIO_INVALIDO` (422) · `MOVIMIENTO_INVENTARIO_INMUTABLE` (409) · `PEDIDO_NO_PAGADO` (409) · `PEDIDO_NO_ENTREGABLE` (409) · `PEDIDO_SIN_RESERVA` (409) · `RESERVA_NO_CONFIRMABLE` (409) | media |
| **A0-04** | ratificar en el ledger y en `SH-05` las rutas `RT-MK-08`…`RT-MK-12` (las tres primeras ya están en `SH-05`; `RT-MK-11` y `RT-MK-12` son nuevas) | media |
| **A0-05** | reconciliar con `RB-07`: la confirmación de entrega la asigna el **servicio compartido de validaciones** (A8); este paquete congela el contrato de entrega de la tienda y el acta | media |
| **A0-06** | añadir las rutas de `marketplace` al inventario congelado de rutas de `core/tests/integration/test_registration_extension.py` | media |
| **A0-07** | **`modules/salesianos_fest` tiene un cambio de modelo pendiente** (`0004_alter_comprapase_token_revocado_en`): `makemigrations --check --dry-run` global falla por eso, no por `marketplace` | **ALTA** |
| **A0-08** | `*.sqlite3` en el `.gitignore` del objetivo | baja |
| **A0-09** | sincronizar la matriz física `00-matriz-tareas.md` (filas `T-042` y `T-043`) | baja |
| **A0-10** | decisión de producto sobre la **expiración** de una reserva (`OD-DOM06-01`) | media |

`STOCK_INSUFICIENTE` (409) es el código **CONGELADO** por el ledger `FR-07`
§3.3 para `RT-CM-03`: ya estaba atribuido a `DOM-06`.

---

## 8. Decisiones abiertas (nunca adivinadas)

- **`OD-DOM06-01` — la EXPIRACIÓN de una reserva.** Una reserva `ACTIVA` se
  mantiene hasta que el pedido se paga o se cancela. **No hay política de
  vencimiento implementada** ("reserva de stock vence" aparece en la matriz
  de recuperación del plan, pero la política —plazo, quién la ejecuta— es de
  producto). Consecuencia declarada: un comprador que abre un pedido y
  nunca paga **retiene** sus unidades. Es un coste operativo CONSCIENTE, no
  un olvido: la alternativa (un TTL inventado) sería inventar una política
  comercial.
- **`PD-03` — entrega parcial**: sigue ABIERTA (A4 + A8 + producto). Este
  paquete entrega el pedido COMPLETO.
- **`PD-06` — devoluciones/reembolsos**: sigue ABIERTA (commerce). Una
  devolución exigiría un movimiento compensatorio, que la bitácora ya
  soporta, pero la política no existe.

---

## 9. Desviaciones

| # | Desviación | Motivo |
|---|---|---|
| `D-DOM06-01` | El stock es **POR EDICIÓN** y el `stock` por defecto es **0** (agotado) | `PD-05` lo pedía; el producto es POR EDICIÓN, así que un pool compartido exigiría una identidad de producto transversal que no existe. `stock = 0` hace que "agotado" sea un hecho, no una suposición del cliente |
| `D-DOM06-02` | Las dos fixtures de producto que sirven para pedir **declaran `stock = 100`** | sin `stock` el producto está AGOTADO y las 69 pruebas de `DOM-04`/`DOM-05` no podrían crear pedidos. No se cambió ninguna aserción: sólo el dato de entrada |
| `D-DOM06-03` | `RT-MK-11` (confirmación de entrega) y `RT-MK-12` (reversa) son rutas NUEVAS y PROVISIONALES | `SH-05` §1.6 no las tiene; `RB-07` asigna la confirmación al servicio compartido de validaciones (A8). Se congelan aquí y se piden como ratificación (A0-04, A0-05) |
| `D-DOM06-04` | La reserva se crea al alta del pedido `PENDIENTE`, no al confirmar el pago | `QA-M01` ("un pedido pendiente no vende más del stock disponible") exige que las unidades estén APARTADAS mientras el pedido está pendiente; si sólo se protegieran al cobrar, N pedidos pendientes podrían "vender" más de lo que hay |
| `D-DOM06-05` | La entrega es COMPLETA, no parcial | `RN-M07` sólo admite la parcial "si se aprueba ese uso" y `PD-03` sigue abierto |
| `D-DOM06-06` | El movimiento de `VENTA` no lleva `actor` | lo produce el SISTEMA al confirmar el pago; el actor manual es obligatorio en los movimientos manuales (`RN-M04`) |
| `D-DOM06-07` | `Producto.stock` y `Producto.reservado` se añaden con una migración ADITIVA `0003_*` | `DOM-04` y `DOM-05` no declaraban existencias; `DOM-05` lo dejó explícitamente para `DOM-06` (`D-DOM04-06`) |

---

## 10. Hechos nuevos

> **Numeración:** `F-65`…`F-69` ya las usó **DOM-07** (competencias) el
> 2026-11-19; las de este paquete van de **`F-70`** a **`F-74`**.

- **F-70** — El patrón de la **sentencia condicional** (`UPDATE … WHERE
  stock >= reservado + N`) extiende el de `DOM-02` (`F-55`) a un caso de DOS
  columnas: no hace falta un contador de filas ni un `select_for_update`;
  basta con que la condición compare una columna con la ARITMÉTICA de otra
  (`F("reservado") + N`).
- **F-71** — Un `CheckConstraint` con `F()` (`Q(reservado__lte=F("stock"))`)
  es válido en Django 5.2 y genera `CHECK ("reservado" <= ("stock"))` en
  SQLite: la BASE DE DATOS puede garantizar la coherencia entre dos
  columnas propias, sin repetir la regla en el código.
- **F-72** — `auto_now` NO dispara en `QuerySet.update()`: un `updated_at`
  que se mueve con `.update()` tiene que fijarse a mano
  (`timezone.now()`), o la fila queda con una fecha de modificación falsa.
- **F-73** — El `SELECT` de Django puede filtrar por la ARITMÉTICA de dos
  columnas propias (`stock__gte=F("reservado") + N`): la disponibilidad
  protegida se expresa como una condición de la base de datos y no como
  un `if` en Python.
- **F-74** — `makemigrations` es más seguro que la migración a mano para un
  paquete con restricciones: el autodetector produce una migración que
  coincide con los modelos POR CONSTRUCCIÓN. `DOM-03` sufrió por lo
  contrario (su `0003` escrita a mano dejó un `0004` contradictorio).
  **PERO** el autodetector tiene un límite: los nombres de índice deben
  caber en 30 caracteres (`models.E034`), y `makemigrations` escribe el
  nombre que tú le des.

---

## 11. Rollback

Punto de rollback: **`fd1c4c123df3767ef6e86908565edf2d4c27c00a`** (HEAD al
inicio de la ronda; commit del usuario, **no** de este paquete). Este paquete
**NO creó commit** y **`git stash` nunca se invocó**.

1. `uv run python manage.py migrate marketplace 0002_pedido_pedidodetalle_and_more --settings=…` (sólo si A0 lo autoriza) y borrar `modules/marketplace/migrations/0003_*`.
2. Borrar los 20 ficheros nuevos de `modules/marketplace/` listados en §12.
3. Revertir los ficheros modificados de `modules/marketplace/` listados en §12.
4. Revertir `Aplicacion/task/salesianos-fest-rebuild/STATE.md` (fila DOM-06 +
   esta transición) y los topics de Engram.
5. **NO tocar** `Aplicacion/backend/media/`: el volumen es estado durable.

**El historial comercial y de pagos se preserva**: este rollback nunca borra
una compra, una orden de pago ni una transacción.

**La bitácora NO se borra**: el plan exige que "el rollback de código nunca
borre la bitácora de auditoría" (`Rollback` del propio paquete). Con datos
vivos, un rollback es un **asiento compensatorio** (un `REVERSION` o un
`AJUSTE`), no un borrado.

---

## 12. Ficheros cambiados

### Creados (20)

| Ruta | Qué es |
|---|---|
| `modules/marketplace/domain/models/movimiento_inventario.py` | la bitácora INMUTABLE |
| `modules/marketplace/domain/models/reserva_inventario.py` | la reserva anti-sobreventa |
| `modules/marketplace/domain/models/entrega_pedido.py` | el acta de entrega |
| `modules/marketplace/domain/schemas/inventario_schemas.py` | DTOs internos |
| `modules/marketplace/domain/results/inventario_result.py` | result objects |
| `modules/marketplace/domain/selectors/inventario_selector.py` | lecturas del inventario |
| `modules/marketplace/domain/services/core/inventario_core_service.py` | reservas, stock, movimientos, reversas |
| `modules/marketplace/domain/services/core/activador_marketplace.py` | `IActivadorDominioCompra` para `MARKETPLACE` |
| `modules/marketplace/domain/services/flujos/inventario_flujo.py` | los casos de uso de escritura |
| `modules/marketplace/domain/services/orchestrators/inventario_orchestrator.py` | la fachada async |
| `modules/marketplace/migrations/0003_entregapedido_movimientoinventario_reservainventario_and_more.py` | la migración |
| `modules/marketplace/presentation/schemas/inventario_schemas.py` | wrappers HTTP |
| `modules/marketplace/presentation/presenters/inventario_presenter.py` | presenters |
| `modules/marketplace/presentation/controllers/inventario_controller.py` | las 5 rutas provisionales |
| `modules/marketplace/tests/fixtures/inventario_fixtures.py` | fixtures del inventario |
| `modules/marketplace/tests/integration/test_inventario_reserva.py` | 5 pruebas |
| `modules/marketplace/tests/integration/test_inventario_movimientos.py` | 5 pruebas |
| `modules/marketplace/tests/integration/test_activador_marketplace.py` | 3 pruebas |
| `modules/marketplace/tests/integration/test_entrega_pedido.py` | 5 pruebas |
| `modules/marketplace/tests/e2e/test_inventario_controller.py` | 10 pruebas |

### Modificados (17 + 5 que ya estaban sucios por `DOM-05`)

`admin.py` · `apps.py` · `di.py` · `domain/constants.py` ·
`domain/exceptions.py` · `domain/models/__init__.py` · `domain/models/producto.py` ·
`domain/selectors/pedido_selector.py` · `domain/services/core/pedido_core_service.py` ·
`domain/services/flujos/pedido_flujo.py` ·
`domain/services/orchestrators/pedido_orchestrator.py` · `models.py` ·
`presentation/presenters/__init__.py` · `presentation/schemas/__init__.py` ·
`tests/conftest.py` · `tests/factories.py` ·
`tests/fixtures/marketplace_fixtures.py` · `tests/urls_marketplace.py`
— y, en el árbol de tareas, `STATE.md` (esta transición) y este fichero de
evidencia.

### NO editados (raíces prohibidas)

`config/api.py` · `core/**` · `modules/commerce/**` · `modules/pagos/**` ·
`modules/salesianos_fest/**` · `modules/eventos/**` · `modules/usuarios/**` ·
`Aplicacion/frontend/**` · `contract/**` · `Aplicacion/plan/**` · la raíz
congelada `backend/**`.

---

## 13. Concurrencia

`Aplicacion/backend/modules/competencias/**` (**DOM-07**, A6) y
`Aplicacion/frontend/**` (FND-06 / UI-01A) están **ACTIVOS** en el árbol
durante este paquete: **no fueron tocados, revertidos ni fusionados**, y
**sus filas del tablero NO se editaron**. Los interiores de `commerce`,
`pagos`, `eventos` y `usuarios` **no fueron editados**: este paquete los
CONSUME por el puerto.

`core/contract_versions.py` (de A0) fue actualizado a `marketplace: 1.2.0`
**en paralelo** por otro actor durante la ventana del paquete: el test de
drift quedó VERDE sin que este paquete lo editara. Se deja constancia por
si A0 quiere confirmar que la actualización corresponde a `DOM-06`.

`Aplicacion/backend/db.sqlite3` es un artefacto **PREEXISTENTE y sucio** (de
trabajo concurrente). Se comprobó, mediante hash antes/después, que
`manage.py check` **no** lo modifica.

---

## 14. Siguiente paquete

**API-03** (los wrappers de `DOM-03`…`DOM-06` que espejar) y **XCT-01**
(el ticket y la entrega de productos, `T-081`) — tras la ratificación de las
rutas provisionales por A0 (A0-01, A0-04) y la congelación del presenter de
entrega que este paquete deja established.
