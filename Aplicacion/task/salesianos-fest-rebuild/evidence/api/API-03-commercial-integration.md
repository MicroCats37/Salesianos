# API-03 — Integración comercial: pases, tienda, checkout y gestión de invitados

**Paquete:** `wave-03-api-integration/API-03-commercial-integration.md` · **Owner:** A7 · **Cambio:** `salesianos-fest-rebuild`
**Estado:** `implementation applied` — **NO cierra el paquete** (verificación en runtime diferida)
**Tareas de origen:** `T-073`, `T-074`
**Rollback:** revertir los ficheros de §6 (no hay commit creado; `git stash` nunca invocado)
**Fecha:** 2026-11-19

---

## 1. Veredicto de registro (la verdad que manda)

`Aplicacion/backend/config/api.py` es la puerta de registro (`FR-07` §3.1 regla 2): **una ruta no existe
hasta que su controller está registrado**. Estado re-verificado en este paquete:

| Controller | Registrado | Rutas vivas |
|---|---|---|
| `PaseController` | **SÍ** | `GET /pases`, `GET /pases/{pase_id}`, `POST /pases/compras`, `GET /pases/compras/{id}`, `GET/POST /pases/compras/{id}/beneficiarios`, `DELETE /pases/compras/{id}/beneficiarios/{persona_id}` |
| `AdminPaseController` | **SÍ** | `GET /administracion/pases`, `GET /administracion/pases/cortesias`, `POST /administracion/pases/cortesias` |
| `ProductoController` | **SÍ** | `GET /marketplace/categorias`, `GET /marketplace/productos`, `GET /marketplace/productos/{slug}`, `POST /marketplace/productos` (admin) |
| `PagosController` | **SÍ** | `POST /pagos/ordenes/{id}/confirmar`, `POST /pagos/izipay/notificacion`, `GET /pagos/ordenes/{id}` |
| **`PedidoController`** | **NO** | `POST /marketplace/pedidos` y `GET /marketplace/pedidos/{token}` **NO EXISTEN** |
| **`InventarioController`** | **NO** | inventario, movimientos y entregas **NO EXISTEN** |

`PedidoController` e `InventarioController` **siguen sin registrar** (`A0-RTV-02`, bloqueante). Sus
ficheros existen en `Aplicacion/backend/modules/marketplace/presentation/controllers/`, pero un
controller no registrado es **código muerto por diseño**: este paquete **NO liga** esas rutas, no
inventa ninguna y **reporta el bloqueo** (§7).

---## 2. Ledger endpoint → presenter → schema espejo

### 2.1 PASES (`features/pases/**`) — todo REGISTERED

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Servicio |
|---|---|---|---|---|---|---|
| `RT-PS-01` | GET | `/pases` | `PaseCatalogoPresenter` | `PaseCatalogoOut` | `catalogoPasesSchema` | `listarPases()` |
| `RT-PS-02` | GET | `/pases/{pase_id}` | `PaseDetallePresenter` | `PaseDetalleOut` | `paseDetalleSchema` | `obtenerPase()` |
| `RT-CM-02` | POST | `/pases/compras` | `CompraPasePresenter` | `CompraPaseCreadaOut` | `compraPaseCreadaSchema` | `comprarPase()` |
| `RT-PS-03` | GET | `/pases/compras/{compra_pase_id}` | `PaseCompraDetallePresenter` | `PaseCompraDetalleOut` | `compraPasesSchema` | `obtenerCompra()` |
| `RT-PS-04` | GET | `/pases/compras/{compra_pase_id}/beneficiarios` | `PaseBeneficiariosPresenter` | `PaseBeneficiariosOut` | `beneficiariosPaseSchema` | `listarBeneficiarios()` |
| `RT-PS-05` | POST | `/pases/compras/{compra_pase_id}/beneficiarios` | `PaseBeneficiarioAsignarPresenter` | `PaseBeneficiariosOut` | `beneficiariosPaseSchema` | `asignarBeneficiario()` |
| `RT-RT-03` | DELETE | `/pases/compras/{compra_pase_id}/beneficiarios/{persona_id}` | `PaseBeneficiarioPresenter` | `PaseBeneficiarioRevocadoOut` | `beneficiarioRevocadoSchema` | `revocarBeneficiario()` |

### 2.2 TIENDA (`features/marketplace/**`) — todo REGISTERED

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Servicio |
|---|---|---|---|---|---|---|
| `RT-MK-01` | GET | `/marketplace/categorias` | `CategoriaListaPresenter` | `list[CategoriaListaOut]` | `categoriaListaSchema` | `listarCategorias()` |
| `RT-MK-02` | GET | `/marketplace/productos` | `ProductoListaPresenter` | `PaginatedData[ProductoListItemOut]` | `productoListItemSchema` + `paginatedResultSchema` | `listarProductos()` |
| `RT-MK-03` | GET | `/marketplace/productos/{slug}` | `ProductoDetallePresenter` | `ProductoDetalleOut` | `productoDetalleSchema` | `obtenerProducto()` |

### 2.3 PEDIDO (`features/marketplace/schemas/pedido.schema.ts`) — **ESPEJO, NO LIGADO**

`PedidoItemIn`, `CrearPedidoIn`, `PedidoLineaOut`, `PedidoSeguimientoOut` y `PedidoCreadoOut` están
espejados **para que la costura sea honesta**, pero **ninguna ruta de pedido se liga, ninguna se
invoca y ninguna vista las consume en producción**. `PedidoController` no está registrado
(`A0-RTV-02`); el día que A0 lo registre, la ligação es **un fichero** y **cero** reescritura de
vistas.

### 2.4 NO LIGADO por decisión de propiedad

`GET /pagos/ordenes/{orden_id}` (`OrdenPagoOut`, con `estado_operativo`) **sí** está registrado, pero
el veredicto operativo del pago tiene **UN dueño** y ese dueño es `features/pagos`, que **no** es una
raíz de este paquete y que pertenece a **XCT-03** (`wave-04-cross-cutting/XCT-03-payment-media-notifications.md`).
Crear un segundo dueño del dataset `pagos` en `features/pases` violaría la regla de «las claves y los
hooks del pago tienen un solo dueño» (§ «Parallelism» del propio paquete). **Consecuencia honesta:**
`PASS-01`/`PASS-02` muestran el **estado comercial de la compra** (`PENDIENTE`/`PAGADA`/`ANULADA`), que
**sí** publica el presenter, y **no** un veredicto de pago que nadie ha podido leer.

---## 3. Dueños: servicios, hooks y claves

### 3.1 Un dueño por dataset

| Dataset | Cliente (servicio) | Factoría de claves | Hooks |
|---|---|---|---|
| Catálogo de pases | `features/pases/services/pase.service.ts` → `listarPases` | `features/pases/utils/pase.claves.utils.ts` → `["pase","catalogo",{…}]` | `useCatalogoPases` |
| Compra de pases y beneficiarios | mismo servicio | `["pase","compras",{compra_pase_id}(",…","beneficiarios")]` | `useCompraPaseDetalle`, `useAsignarBeneficiario`, `useRevocarBeneficiario` |
| Categorías de la tienda | `features/marketplace/services/marketplace.service.ts` → `listarCategorias` | `features/marketplace/utils/marketplace.claves.utils.ts` → `["marketplace","catalogo","categorias"]` | `useCategoriasTienda` |
| Catálogo de productos | mismo servicio → `listarProductos` | `["marketplace","catalogo","productos",{categoria_id,page,page_size}]` | `useCatalogoTienda` |
| Detalle de producto | mismo servicio → `obtenerProducto` | `["marketplace","productos",{slug}]` | `useProductoDetalle` |

**El transporte es uno**: `apiSend` de `src/lib/api.ts` (`FREEZE-ENV-1.0.0` §4.4: el `204` **nunca**
se parsea; vive en el dueño del transporte, no en cada hook).

**La lectura exporta `queryOptions`**: los hooks usan `datasetQueryOptions` de
`src/shared/utils/query-options.ts` (catalogo → 10 min; comercial → 15 s; `gcTime >= staleTime` y
`>= 5 min`).

### 3.2 Parámetros que viajan en la clave

`edicion_id` (catálogo de pases) · `compra_pase_id` (compra y beneficiarios) · `categoria_id`, `page`,
`page_size` (catálogo de la tienda) · `slug` (detalle de producto). Un parámetro `undefined` **se
descarta**: `{page:1}` y `{page:1,q:undefined}` son **la misma** entrada.

### 3.3 Capa de presentación (contenedores) y rutas

`page.tsx` → **contenedor** → vista → componentes → hooks → servicios → schemas.

| Ruta | Página | Contenedor | Hooks |
|---|---|---|---|
| `PASS-01` `/pases` | `src/app/(public)/pases/page.tsx` | `PasesRuta` | `useCatalogoPases`, `useCompraPase` |
| `PASS-02` `/pases/gestionar/[token]` | `src/app/(public)/pases/gestionar/[token]/page.tsx` | `PaseGestionarRuta` | `useCompraPaseDetalle`, `useAsignarBeneficiario`, `useRevocarBeneficiario` |
| `SHOP-01` `/tienda` | `src/app/(public)/tienda/page.tsx` | `TiendaRuta` | `useCategoriasTienda`, `useCatalogoTienda` |
| `SHOP-02` `/tienda/[slug]` | `src/app/(public)/tienda/[slug]/page.tsx` | `ProductoDetalleRuta` | `useProductoDetalle` |
| `SHOP-03` `/tienda/pedidos/[token]` | **sin cambios** | — | — (**bloqueado**, §7) |

**El filtro de categoría viaja al servidor.** La URL lleva `?categoria=<slug>` y el backend filtra
por `categoria_id`; el contenedor resuelve el slug contra las categorías publicadas y pide la página
al servidor. El navegador **nunca** filtra un catálogo por su cuenta.

---## 4. Política de caché, de errores y de payload

### 4.1 Caché

- **Ninguna escritura optimista.** El dinero, el derecho y el stock son **del servidor**: una
  mutación **no** escribe en la caché, **invalida** la clave exacta que ensucia (`FND-08` §3 regla 3).
- **La invalidación vive DENTRO de la `mutationFn`**, no en `onSettled`: un componente que se
  desmonta mientras la mutación está en vuelo no ejecutaría `onSettled` y la caché conservaría una
  respuesta que el servidor nunca dio (`FND-08` §3 regla 5).
- Invalidaciones exactas: compra → `["pase","compras",{compra_pase_id}]` (que incluye sus
  beneficiarios); asignación → la misma; revocación → la misma; alta de compra →
  `["pase","compras"]`.

### 4.2 Errores

- El éxito se lee de `response.message` y el error de `error.message`; se **ramifica por status HTTP**
  (`contract/api-wrapper-presenter-contract.md` §8). El código estable es **diagnóstico**, nunca la
  única rama de la interfaz.
- **El `204` no se parsea nunca** (vive en `apiSend`, el dueño del transporte).
- **Un cuerpo que no cumple el contrato es un fallo ruidoso**: `ErrorContratoPase` /
  `ErrorContratoMarketplace`. No hay «loguear y continuar» ni `z.any()`.
- **La denegación del enlace de invitado es NEUTRAL** (`QA-U03`): `401` (token caducado, revocado o
  desconocido), `403` (el token no autoriza este lote) y `404` (el lote no existe) responden **el
  mismo mensaje**, para que escribir un documento no sea un oráculo de existencia.
- **Los errores de campo de un 422 llegan a su control**: el wire habla `snake_case` y el formulario
  `camelCase`, así que la capa de feature (`utils/pase.error.utils.ts`) reescribe **solo el nombre**
  del campo y conserva status, código y mensaje. `GenericForm` los lleva a `setError`.
- El mensaje del servidor se muestra **verbatim** en el estado de error (`mensajeError`).

### 4.3 Payload

- **Solo-creación**: la compra y la asignación son `CREATE`; nunca se envía un diff de update.
- El **importe no se envía jamás**: el precio lo resuelve y congela el servidor (`RN-C02`).
- `undefined` = omitido; `null` = limpieza explícita de un campo nullable; **ningún campo no
  declarado** se manda.
- La asignación por documento **omite** `persona_id` (no es una limpieza: no se conoce).
- El mapeo vive en `utils/pase.payload.utils.ts`, **fuera del componente**: un componente nunca
  escribe un campo del wire.

### 4.4 Semántica del pago y de la entrega

**Pagado NO es entregado** (`RN-M07`, `QA-M04`). `SHOP-03` conserva las tres filas separadas. En
`PASS-01`/`PASS-02` el estado que se muestra es el **estado comercial de la compra** (`PENDIENTE` /
`PAGADA` / `ANULADA`), que es un hecho **declarado** por el presenter — no un veredicto de pago
derivado en el navegador.

**Ninguna actualización optimista de dinero, stock ni derecho.** Cerrar el checkout **no** borra la
compra ni la invierte: el servidor es el dueño del estado.

---

## 5. Fixtures provisionales: ELIMINADOS

| Fichero | Acción |
|---|---|
| `src/features/pases/fixtures/pase.fixture.ts` | **ELIMINADO** (`PROVISIONAL_CONTRACT_FIXTURE`) |
| `src/features/marketplace/fixtures/marketplace.fixture.ts` | **ELIMINADO** (`PROVISIONAL_CONTRACT_FIXTURE`) |

Búsqueda de cierre (`Aplicacion/frontend/src/features/pases` y `.../marketplace`): **0** coincidencias
de `PROVISIONAL_CONTRACT_FIXTURE`, `fixtures/pase.fixture` y `fixtures/marketplace.fixture`.

Los datos de las suites ahora son **la respuesta del contrato**, parseada por el **mismo espejo Zod**
que usa el servicio: una forma que el espejo rechaza rompe la suite **antes** de dibujar nada.

---## 6. Ficheros

### 6.1 Creados (25)

**`features/pases/`** (15): `schemas/pase.schema.ts` · `services/pase.service.ts` ·
`utils/pase.claves.utils.ts` · `utils/pase.adaptador.utils.ts` · `utils/pase.payload.utils.ts` ·
`utils/pase.error.utils.ts` · `utils/pase.enlace.utils.ts` · `hooks/useCatalogoPases.ts` ·
`hooks/useCompraPase.ts` · `hooks/useGestionPase.ts` · `hooks/index.ts` ·
`components/FormularioBeneficiario.tsx` · `views/PasesRuta.tsx` · `views/PaseGestionarRuta.tsx` ·
`__tests__/pase.service.test.ts`

**`features/marketplace/`** (10): `schemas/producto.schema.ts` · `schemas/pedido.schema.ts` ·
`services/marketplace.service.ts` · `utils/marketplace.claves.utils.ts` ·
`hooks/useCatalogoTienda.ts` · `hooks/useProductoDetalle.ts` · `hooks/index.ts` ·
`views/TiendaRuta.tsx` · `views/ProductoDetalleRuta.tsx` · `__tests__/marketplace.service.test.ts`

### 6.2 Modificados (21)

`features/pases/`: `types/pase.types.ts` · `schemas/comprador-pase.schema.ts` ·
`components/CatalogoPases.tsx` · `components/DialogoCheckout.tsx` ·
`components/FormularioComprador.tsx` · `components/index.ts` · `views/PasesView.tsx` ·
`views/PaseGestionarView.tsx` · `views/index.ts` · `__tests__/pases-estados.test.tsx`

`features/marketplace/`: `types/marketplace.types.ts` · `components/DialogoCheckoutTienda.tsx` ·
`views/TiendaCatalogoView.tsx` · `views/ProductoDetalleView.tsx` · `views/PedidoSeguimientoView.tsx` ·
`views/index.ts` · `__tests__/marketplace-estados.test.tsx`

Rutas (4): `src/app/(public)/pases/page.tsx` · `src/app/(public)/pases/gestionar/[token]/page.tsx` ·
`src/app/(public)/tienda/page.tsx` · `src/app/(public)/tienda/[slug]/page.tsx`

### 6.3 Eliminados (2)

`src/features/pases/fixtures/pase.fixture.ts` · `src/features/marketplace/fixtures/marketplace.fixture.ts`

**Raíces tocadas**: `Aplicacion/frontend/src/features/pases/**` ·
`Aplicacion/frontend/src/features/marketplace/**` · las **4 rutas públicas asignadas** ·
`Aplicacion/task/salesianos-fest-rebuild/evidence/**` · `STATE.md`.

**Raíces prohibidas NO tocadas**: `src/lib/**` · `src/shared/**` · `src/hooks/**` · `src/errors/**` ·
`src/components/**` · `src/providers/**` · `src/features/{admin,auth,cuenta,inscripciones,portada,public,theme}/**` ·
`Aplicacion/backend/**` · `contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**`.

---

## 7. BLOQUEOS reportados (nada se inventó)

| # | Bloqueo | Evidencia | Dueño |
|---|---|---|---|
| **B-03-01** | `POST /marketplace/pedidos` **no existe** (`PedidoController` no registrado) → el checkout de la tienda **no puede crear el pedido** | `config/api.py` (sin `registrar_controladores(PedidoController)`) · `A0-RTV-02` | **A0** (registro) |
| **B-03-02** | `GET /marketplace/pedidos/{token}` **no existe** → `SHOP-03` **no puede mostrar** el estado ni la entrega de un pedido | ídem | **A0** |
| **B-03-03** | `InventarioController` no registrado → **stock, reserva y entrega** no existen; el catálogo de productos **no publica existencias** (`D-DOM04-06`) | ídem · `DOM-06` | **A0** |
| **B-03-04** | El veredicto operativo del pago (`estado_operativo`) solo se publica en `GET /pagos/ordenes/{id}`, que exige **sesión + titularidad**; el invitado con token no puede leerlo | `PagosController` (`JWTAuth` + `IsAuthenticated`) | **XCT-03** (dueño de `features/pagos`) |
| **B-03-05** | El backend abre el lote por `compra_pase_id` (ruta) **y** por el token (cabecera `X-Pase-Token`), y **no hay ruta que resuelva un token → lote**. El enlace de invitado tiene que llevar **las dos** cosas | `pase_controller.py` + `PaseAccesoService` | **A0** (ratificar `P-01`) |
| **B-03-06** | El catálogo de la tienda **no declara moneda** (`D-UI03-08`) y `PrecioPaseOut` **tampoco** para el pase: sin moneda publicada, la interfaz **no puede imprimir una** | `producto_schemas.py` · `pase_schemas.py` | **A0** |

### 7.1 Decisiones tomadas (con su coste)

| # | Decisión | Motivo |
|---|---|---|
| **D-API03-01** | El enlace de invitado es `/pases/gestionar/{token}?compra={compra_pase_id}`: el **token** en la ruta (como declara `RUTAS.publico.paseGestionar`) y el **identificador** en la query | El backend necesita el id en la ruta y el token en la cabecera; el token **nunca** viaja en la query (`F-61`). El identificador **no es una credencial**. Es una decisión **provisional** que A0 debe ratificar (`P-01`) |
| **D-API03-02** | El frontend resuelve el **slug** de la categoría contra las categorías publicadas y pide la página al servidor con `categoria_id` | El backend filtra por **id**; el navegador no filtra un catálogo por su cuenta |
| **D-API03-03** | Las **etiquetas** de los códigos de estado (`PENDIENTE`/`PAGADA`/`ANULADA`, `ACTIVO`/`REVOCADO`) las resuelve un **adaptador** de feature (`utils/pase.adaptador.utils.ts`) | Los presenters de `DOM-03` publican **códigos y ninguna prosa** (`A0-UI03-04`) y la interfaz nunca enseña un código (`SH-03` §6). El adaptador es **temporal** |
| **D-API03-04** | El estado `cargando` se añadió a `EstadoVistaPases` / `EstadoVistaTienda` | Una lectura en vuelo no puede dibujarse como «vacío» ni como «catálogo real»: `SH-03` S-08 (sin ETA inventado) |
| **D-API03-05** | Las suites ya **no** dependen de una fixture provisional: los datos se parsean con el espejo | `FR-08` §1.4: una fixture provisional nunca llega a una ruta |
| **D-API03-06** | El formulario de asignación de `PASS-02` **se construyó** (debía `UI-03`, `D-UI03-05`) | Sin él, la mutación de asignación no tenía consumidor y `RT-PS-05` quedaba muerta |
| **D-API03-07** | Los **espejos del pedido** existen pero **no** se liga ninguna ruta de pedido | La forma queda lista; la **ligación** depende del registro (`B-03-01`) |

---## 8. Comandos y verificación

| # | Comando | Workdir | Exit | Resultado |
|---|---|---|---|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 1 error propio (`CompraPases.beneficiarios` sin `estado_etiqueta`) — **corregido** |
| V2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio |
| V3 | `npx tsc --noEmit` (tras el marketplace) | `Aplicacion/frontend` | **0** | limpio |
| V4 | `npx tsc --noEmit` (tras las suites) | `Aplicacion/frontend` | **0** | limpio — **verificación final** |
| V5 | `git status --short -- <raíces>` | raíz | 0 | 4 rutas modificadas + `features/pases/**` y `features/marketplace/**` nuevos |
| V6 | `git diff --stat -- <rutas>` | raíz | 0 | 7 ficheros (3 de ellos son de **UI-03**, no de este paquete) |
| V7 | búsqueda `PROVISIONAL_CONTRACT_FIXTURE` / `fixtures/*.fixture` en las dos features | `Aplicacion/frontend` | 0 | **0** coincidencias |

**NOT RUN** (fuera del permiso de este paquete): `vitest`, `biome`, `next build`, `npm install`,
servidores, navegadores, la auditoría de los cinco anchos (360 · 390 · 768 · 1024 · 1440),
`git stash` / `commit` / `reset` / `checkout`.

**Tests ESCRITOS, NO EJECUTADOS (4 suites):**
`features/pases/__tests__/pases-estados.test.tsx` · `features/pases/__tests__/pase.service.test.ts` ·
`features/marketplace/__tests__/marketplace-estados.test.tsx` ·
`features/marketplace/__tests__/marketplace.service.test.ts`.

Cobertura declarada: **token caducado → 401 → denegación neutral** · **409 de cupo/derecho** (el
servidor manda; la interfaz no escribe) · **422 con `field_errors` → control correcto** ·
**204 sin cuerpo → nunca se parsea** · **fallo de imagen** (`disponible: false` conserva el texto
alternativo) · **incertidumbre del pago** (el pendiente nunca se presenta como confirmado) ·
**paginación con otra forma → fallo ruidoso**.

### 8.1 La auditoría de los cinco anchos

La matriz de `salesianos-responsive-a11y` exige 360 · 390 · 768 · 1024 · 1440 **con navegador**. Este
paquete **no** puede abrir un navegador, así que la auditoría **sigue ABIERTA**. Lo que sí se ha
verificado por código:

- Los **dos formularios nuevos** (`FormularioComprador`, `FormularioBeneficiario`) declaran
  `min-h-11` en el botón y en los campos, y las suites lo comprueban leyendo el fuente.
- Los **diálogos** conservan `max-h-[90svh] overflow-y-auto` y el cierre se llama «Cerrar».
- Las **etiquetas** de los campos están asociadas por `htmlFor`/`id`, los errores por
  `aria-describedby` + `aria-invalid`, y el resumen de errores es `role="alert"` con foco.
- El estado de error **ofrece siempre la acción** que lo resuelve («Reintentar»), incluso con el
  mensaje del servidor.

---## 9. Rollback

1. Borrar los 25 ficheros creados (§6.1) y restaurar los 21 modificados (§6.2) desde `HEAD` **o**
   desde el estado previo de UI-03 (las 4 rutas se sobrescribieron **encima** de UI-03: para
   restaurar **solo** este paquete basta volver a la versión de UI-03 de esas 4 páginas).
2. `git stash` **nunca** se invocó; no hay commit de este paquete; el punto de rollback del árbol es
   el mismo que antes del paquete.
3. **Nunca** restaurar las fixtures provisionales de producción: el rollback devuelve la
   integración al estado **sin datos** de UI-03, que es el estado honesto de las rutas.

---

## 10. Preparación de los consumidores

### 10.1 XCT-01 (tickets y validación) — **PROVISIONAL**

- **Listo**: `PASS-01`, `PASS-02`, `SHOP-01` y `SHOP-02` leen del servidor real; el estado del
  derecho y el de la compra son **hechos declarados**, no etiquetas de cliente.
- **Pendiente**: la validación de entradas (módulo `validaciones`) **no existe** en el backend
  (`A0-RTV-01`); `RT-RT-03` (revocación) **sí** está registrada y ligada.
- **Arranque**: la revocación se liga a `DELETE /pases/compras/{id}/beneficiarios/{persona_id}` con
  el motivo en la query, tal y como declara el ledger.

### 10.2 XCT-03 (pago, medios y notificaciones) — **PROVISIONAL**

- **Listo**: la compra **crea** el lote y devuelve `orden_pago_id`; el espejo de `OrdenPagoOut`
  (`estado_operativo`, `intentos[]`) está disponible para quien sea su dueño.
- **Pendiente**: `features/pagos` **no** existe (no es raíz de este paquete); el veredicto de pago
  (`B-03-04`) y el reintento seguro (`POST /pagos/ordenes/{id}/confirmar`, que exige el **payload
  crudo firmado** del proveedor) siguen sin dueño en el frontend.
- **Arranque**: el verbo de reintento es `POST /pagos/ordenes/{id}/confirmar` con cabecera
  `Idempotency-Key`; la firma se verifica **en servidor** (`FR-04` §3).

### 10.3 VER-01…VER-03 — **ABIERTO**

Dependen de la ejecución de la suite (no ejecutada aquí) y de los bloqueos `B-03-01`…`B-03-03`.

---

## 11. Lo que este paquete NO ha hecho (y por qué)

- **No ha registrado ningún controller** ni ha tocado `Aplicacion/backend/**`: el registro es de A0.
- **No ha ligado `POST /marketplace/pedidos` ni `GET /marketplace/pedidos/{token}`**: no existen.
- **No ha ligado `GET /pagos/ordenes/{id}`**: ese dataset tiene un solo dueño y no es este paquete.
- **No ha inventado una ruta** para resolver un token → lote, ni una moneda para la tienda, ni un
  stock que el backend no publica.
- **No ha tocado** `src/lib/**`, `src/shared/**`, `src/hooks/**`, `src/errors/**`,
  `src/components/**`, `src/providers/**`, `contract/**`, `Aplicacion/backend/**` ni las features
  de otros paquetes (`inscripciones` de **UI-02**, `admin`, `auth`, `cuenta`, `portada`, `public`,
  `theme`).
- **No ha ejecutado** `vitest`, `biome`, `next build`, servidores ni navegadores.
- **No ha hecho** ninguna operación de git.