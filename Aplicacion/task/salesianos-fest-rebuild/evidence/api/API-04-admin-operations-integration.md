# API-04 — Integrar las operaciones administrativas: inscripciones, equipos, participantes y pagos

**Paquete:** `wave-03-api-integration/API-04-admin-operations-integration.md` · **Owner:** A7 · **Cambio:** `salesianos-fest-rebuild`
**Estado:** `implementation applied` — **NO cierra el paquete** (verificación en runtime diferida)
**Tareas de origen:** `T-075`, `T-076`
**Rollback:** revertir los ficheros de §7 (no hay commit creado; `git stash` nunca invocado)
**Fecha:** 2026-11-19

---

## 1. Veredicto de registro (la verdad que manda)

`Aplicacion/backend/config/api.py` es la puerta de registro (`FR-07` §3.1 regla 2): **una ruta no existe
hasta que su controller está registrado**. El estado se **re-verificó** en este paquete, sobre el árbol de
trabajo, el 2026-11-19:

| Controller | Registrado | Rutas vivas |
|---|---|---|
| `EdicionController` | **SÍ** | `GET /ediciones/actual` |
| `PersonaController` | **SÍ** | `GET /personas/busqueda/{documento}`, `POST /personas/resolver`, `POST /personas/confirmar` |
| `AuthController` | **SÍ** | `POST /auth/login/...`, `GET /auth/me` |
| `PagosController` | **SÍ** | `POST /pagos/ordenes/{id}/confirmar`, `POST /pagos/izipay/notificacion`, `GET /pagos/ordenes/{id}` |
| `CatalogoController` | **SÍ** | `RT-IN-12`, `RT-IN-13` |
| `InscripcionController` | **SÍ** | `POST /inscripciones`, `GET /inscripciones/{id}`, `GET /inscripciones/{id}/equipos`, `GET /inscripciones/{id}/pool`, `POST /inscripciones/{id}/participantes`, `DELETE /inscripciones/{id}/participantes/{pid}`, `POST /inscripciones/{id}/compras/cupos` |
| `ProductoController` | **SÍ** | `/marketplace/**` (4 rutas) |
| `PaseController` | **SÍ** | `RT-PS-01`…`RT-PS-05`, `RT-CM-02`, `RT-RT-03` |
| `AdminPaseController` | **SÍ** | `GET /administracion/pases`, `GET /administracion/pases/cortesias`, `POST /administracion/pases/cortesias` |
| **`AdminInscripcionController`** | **NO** | `RT-IN-07`, `RT-IN-08` **NO EXISTEN** |
| **`AdminEquipoController`** | **NO** | `RT-IN-09`, `RT-IN-10` **NO EXISTEN** |
| **`AdminParticipanteController`** | **NO** | `RT-IN-11` **NO EXISTE** |
| **`AdminPagoController`** | **NO** | `RT-PG-04`, `RT-PG-05`, `RT-PG-07` **NO EXISTEN** |
| **`AdminPersonaController`** | **NO** | `RT-ID-07`, `RT-ID-08` **NO EXISTEN** |

**Ninguna ruta administrativa del alcance de este paquete existe.** Este paquete **NO liga** ninguna de
ellas, no inventa ninguna y **reporta el bloqueo** (§11).

### 1.1 Por qué no se liga una ruta registrada que "serviría"

| Ruta registrada tempting | Por qué NO se liga en el área administrativa |
|---|---|
| `GET /inscripciones/{id}/pool` (`RT-IN-03`) | El dataset del pool **tiene un dueño**: `features/inscripciones` (API-02). Un segundo cliente del mismo endpoint daría **dos fuentes de verdad** y **dos invalidaciones** del mismo dato (`FND-08` §3 regla 1). Además el módulo **no** deja al grupo `Administrador` sustituir la titularidad del responsable (`PoolOrchestrator._verificar_responsable`: *«El grupo Administrador NO sustituye la titularidad de una inscripción ajena»*), así que el administrador recibiría **403** en la inscripción de otro. |
| `GET /inscripciones/{id}` (`RT-IN-04`) y `GET /inscripciones/{id}/equipos` | Mismo dueño (`features/inscripciones`); y el ledger de la ADMINISTRACIÓN (`RT-IN-08`) publica una lista de equipos **con su plantilla y su veredicto**, cosa que `EquipoOut` (DOM-01) **no** publica (`A0-UI04-02`). |
| `DELETE /inscripciones/{id}/participantes/{pid}` (`RT-IN-06`) | Es la ruta del **RESPONSABLE de su propia inscripción**, **no admite motivo** y el módulo **no** autoriza al administrador: no puede responder la acción **auditada** del S-10 (`A0-UI04-04`). |
| `GET /pagos/ordenes/{id}` (`RT-PG-01`) | El veredicto operativo del pago tiene **un solo dueño** y es `features/pagos` (XCT-03); además exige **titularidad del comprobador**, no del administrador (`API-03` §2.4 y `B-03-04`). |
| `GET /administracion/pases` (`RT-PS-06`) … | **Sí** están registradas, pero pertenecen al área de pases (`ADM-15`, propiedad **NO ATRIBUIDA**: `A0-API05-05`), no a las seis rutas de UI-04, y su vista es una raíz de **FND-06** (raíz prohibida). No se tocan (`A0-API04-02`). |

**Precedente del propio cambio:** `D-API01-01` (*«Only registered routes are bound… the frontend never
invents a URL nor a wrapper»*), `API-02` (`RT-IN-01` sin ruta), `API-03` (`PedidoController`/`InventarioController`)
y `API-05` (cero rutas ligadas). **API-04 es el mismo veredicto para el área administrativa.**

---

## 2. Ledger endpoint → presenter → espejo → servicio → hook → clave

### 2.1 Inscripciones (`features/admin/inscripciones/**`)

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Servicio | Hook | Clave |
|---|---|---|---|---|---|---|---|---|
| `RT-IN-07` | GET | `/administracion/inscripciones` | `AdminInscripcionListaPresenter` | `PaginatedData[AdminInscripcionListItemOut]` | `inscripcionAdminListItemSchema` | `listarInscripcionesAdmin()` | `useListaInscripcionesAdmin()` | `adminClaves.inscripciones.listPage(...)` |
| `RT-IN-08` | GET | `/administracion/inscripciones/{inscripcion_id}` | `AdminInscripcionDetallePresenter` | `AdminInscripcionDetalleOut` | `inscripcionAdminDetalleSchema` | `obtenerInscripcionAdmin()` | `useDetalleInscripcionAdmin()` | `adminClaves.inscripciones.detail(id)` |
| `A0-UI04-04` | DELETE | *(no existe ruta administrativa)* | `ParticipanteRetirarPresenter` | `PoolOut` | `poolDeInscripcionSchema` | `retirarParticipanteAdmin()` | `useRetirarParticipanteAdmin()` | `adminClaves.accion("inscripciones", id, version)` |

### 2.2 Equipos (`features/admin/equipos/**`)

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Servicio | Hook | Clave |
|---|---|---|---|---|---|---|---|---|
| `RT-IN-09` | GET | `/administracion/equipos` | `AdminEquipoListaPresenter` | `PaginatedData[AdminEquipoListItemOut]` | `equipoAdminListItemSchema` | `listarEquiposAdmin()` | `useListaEquiposAdmin()` | `adminClaves.equipos.listPage(...)` |
| `RT-IN-10` | GET | `/administracion/equipos/{equipo_id}` | `AdminEquipoDetallePresenter` | `AdminEquipoDetalleOut` | `equipoAdminDetalleSchema` | `obtenerEquipoAdmin()` | `useDetalleEquipoAdmin()` | `adminClaves.equipos.detail(id)` |

### 2.3 Participantes (`features/admin/participantes/**`)

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Servicio | Hook | Clave |
|---|---|---|---|---|---|---|---|---|
| `RT-IN-11` | GET | `/administracion/participantes` | `AdminParticipanteListaPresenter` | `PaginatedData[AdminParticipanteListItemOut]` | `participanteAdminSchema` | `listarParticipantesAdmin()` | `useListaParticipantesAdmin()` | `adminClaves.participantes.listPage(...)` |

### 2.4 Pagos (`features/admin/pagos/**`)

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Servicio | Hook | Clave |
|---|---|---|---|---|---|---|---|---|
| `RT-PG-04` | GET | `/administracion/pagos` | `AdminPagoPresenter` | `PaginatedData[AdminPagoListItemOut]` | `adminPagoListItemSchema` | `listarPagosAdmin()` | `useListaPagosAdmin()` | `adminClaves.pagos.listPage(...)` |
| `RT-PG-07` | GET | `/administracion/pagos/{compra_id}` | `AdminPagoDetallePresenter` | `AdminPagoDetalleOut` | `adminPagoDetalleSchema` | `obtenerPagoAdmin()` | `useDetallePagoAdmin()` | `adminClaves.pagos.detail(id)` |
| `RT-PG-05` | POST | `/administracion/pagos/{orden_pago_id}/aprobar-manual` | `AdminPagoManualPresenter` | `AdminPagoAprobarManualOut` | `adminPagoListItemSchema` (wrapper **no publicado**: `A0-API04-01`) | `aprobarPagoManualAdmin()` | `useAprobarPagoManualAdmin()` | `adminClaves.accion("pagos", id, version)` |
| `RT-PG-06` | GET | `/pagos/ordenes/{orden_id}/intentos` | `PagoIntentosPresenter` | `PagoIntentosOut` | — (el diagnóstico viaja dentro de `AdminPagoDetalleOut.intentos`) | — | — | — |

### 2.5 El vocabulario compartido (`features/admin/operaciones/schemas/operaciones.schema.ts`)

`estadoOperativoSchema` (`{codigo, etiqueta, descripcion}` = `EstadoOperativo` congelado de `FR-01` §5) ·
`accionOperativaSchema` · `cuposOperativosSchema` (`{adquiridos, asignados, disponibles}`) · `causaSchema`
(`{codigo, mensaje}`) · `fieldErrorSchema` · `adminErrorDetailSchema` · `adminErrorEnvelopeSchema` ·
`envelopeAdmin(...)` · `envelopeAdminPaginado(...)`.

---

## 3. Los dueños: servicio, hook, clave e invalidación

### 3.1 Un cliente, un ledger, un guard

`features/admin/operaciones/services/admin.service.ts` es **el único cliente** del área:

- `RUTAS_ADMIN` es el **ledger con la verdad de registro** (12 rutas con `ledger`, `metodo`, `ruta`,
  `presentador`, `wrapper`, `registrado`, `motivo` y `permiso`). **Un componente, un hook o un servicio
  nunca escribe una URL**: el único punto de cambio cuando A0 registre un controller es `registrado: true`.
- `urlDeRutaAdmin()` **rechaza** una ruta que no está registrada **antes** de tocar el transporte.
- `pedirAdmin()` es la **única** llamada: aplica las reglas del envelope **una vez** (el `204` **nunca**
  se parsea, el cuerpo se parsea con el espejo, un cuerpo que no cumple es un fallo **ruidoso**) y
  convierte un fallo en un `ErrorAdmin` con su **status**, su **código**, su **prosa** y sus **errores de
  campo**.

**Prueba de la guarda** (`__tests__/admin-integracion.test.ts`): una orden forzada de `RT-PG-05` o de la
retirada **falla con `ErrorRutaAdminNoRegistrada` y con CERO peticiones emitidas** (`apiSend` mockeado,
`expect(apiSendMock).not.toHaveBeenCalled()`).

### 3.2 Las claves (`features/admin/operaciones/utils/admin.claves.utils.ts`)

| Dataset | Namespace | Contenido |
|---|---|---|
| las inscripciones | `admin.inscripciones` | `AdminInscripcionListItemOut` |
| los equipos | `admin.equipos` | `AdminEquipoListItemOut` |
| los participantes | `admin.participantes` | `AdminParticipanteListItemOut` |
| los pagos | `admin.pagos` | `AdminPagoListItemOut` |

**Qué viaja en la clave:** la **edición** (`edicion_id`), el **filtro** (`q`, `ordering`, `estado_operativo`,
`estado_compra`, `estado_orden`, `tipo`, `desde`, `hasta`), la **página** (`page`, `page_size`), el
**registro** (el id de la detalle) y la **versión** (`adminClaves.accion(dataset, registroId, version)`).
Un parámetro `undefined` se **descarta**: `{page: 1}` y `{page: 1, q: undefined}` son **la misma** entrada
(`src/shared/utils/query-keys.ts`).

### 3.3 Los hooks y las lecturas

Cada hook exporta su `queryOptions` con la política `listadoAdministrativo` (30 s) y con su `enabled`
atado a la **verdad de registro**:

```ts
enabled: RUTAS_ADMIN.pagosLista.registrado
```

Con la ruta sin registrar, la superficie muestra el **estado honesto** (`sin-datos`) y **nunca** un
spinner eterno, una lista inventada o una tabla vacía.

### 3.4 La invalidación (`features/admin/operaciones/utils/admin.cache.utils.ts`)

`invalidarAdmin(cliente, ...datasets)` invalida **exactamente** la raíz del dataset indicado. Vive
**DENTRO de la `mutationFn`** (`FND-08` §3 regla 5): un componente que se desmonta mientras la orden está
en vuelo no ejecutaría `onSettled` y la caché conservaría una respuesta que el servidor nunca dio.

**No se invalida nada ajeno:** el pool de una inscripción es de `features/inscripciones` y el veredicto de
una orden de pago es de `features/pagos`; sus dueños invalidan los suyos.

---

## 4. La política de errores, de permisos y de acciones

### 4.1 El estado de una superficie (`features/admin/operaciones/utils/admin.estado.utils.ts`)

| La respuesta | El estado |
|---|---|
| la ruta **no está registrada** | `sin-datos` (el estado honesto por defecto) |
| la lectura está en vuelo | `cargando` |
| **401** / **403** | `sin-permiso` con la prosa **verbatim** del backend |
| **409** / **422** / **500** / cualquier otro | `error` con la prosa **verbatim** del backend |
| una respuesta válida | `listo` |

La interfaz **ramifica por el STATUS HTTP**, nunca por el código de máquina (el catálogo de códigos
públicos no es cerrado). El texto de un fallo es `error.message` del envelope: **verbatim**, sin traducir.

### 4.2 El 422 y los errores de campo

`error.field_errors[]` es el **único** canal de error por campo (`FREEZE-ENV-1.0.0` §4.2) y
`erroresDeCampoDeError()` lo traduce al mapa `{ campo: mensaje }` que consume `setError`. El `details`
**no** se usa como canal de campo.

### 4.3 Las acciones sensibles

| Acción | Ruta | Estado |
|---|---|---|
| Retirar a un participante (`ADM-06`, `ADM-08`) | `A0-UI04-04` (**no existe**) | **DESHABILITADA** con la razón escrita; el motivo es **obligatorio** y el comando se construiría con `payloadRetirarParticipanteAdmin()` |
| Registrar el pago externo (`ADM-14`) | `RT-PG-05` (**no registrada**) | **DESHABILITADA** con la razón escrita; el motivo es **obligatorio** y el comando se construiría con `payloadAprobarPagoManualAdmin()` |

El botón se deshabilita desde el **mismo registro** que usa el servicio
(`RUTAS_ADMIN.retirarParticipante.registrado`), de modo que **la interfaz y el transporte no pueden
discrepar** sobre la existencia de la ruta.

El **motivo travels en el comando** (la acción es auditada) y el **importe** que viaja es **el que
publicó el servidor**: el navegador no calcula un precio (`FR-08` §2.4). La **versión** viaja cuando el
backend la publique (token de concurrencia optimista): el backend rechaza una orden sobre un registro
caducado y el frontend **nunca** decide que un registro está fresco.

---

## 5. Fixtures provisionales: ELIMINADOS

| Fichero | Acción |
|---|---|
| `src/features/admin/inscripciones/fixtures/inscripciones-admin.fixture.ts` | **ELIMINADO** (y su carpeta) |
| `src/features/admin/equipos/fixtures/equipos-admin.fixture.ts` | **ELIMINADO** (y su carpeta) |
| `src/features/admin/pagos/fixtures/pagos-admin.fixture.ts` | **ELIMINADO** (y su carpeta) |
| `src/features/admin/participantes/fixtures/participantes-admin.fixture.ts` | **ELIMINADO** (y su carpeta) |

**Escaneo de cierre** (`Aplicacion/frontend/src/features/admin`): `PROVISIONAL_CONTRACT_FIXTURE` → **0**
coincidencias · imports de `fixtures/` → **0** · carpetas `fixtures/` → **0**.

Los datos de las suites son ahora **la respuesta del contrato, parseada por el MISMO espejo Zod** que usa
el servicio (`__tests__/<dominio>-admin.datos.ts`): una forma que el espejo rechaza rompe la suite
**antes** de dibujar nada (`FR-08` §1.4 · `D-API03-05` · `D-API05-07`).

---

## 6. Lo que la interfaz hace y lo que NO hace

| Regla | Dónde vive |
|---|---|
| El **veredicto** lo publica el backend; el navegador **no** cruza compra, orden e intento | `veredicto.adapter.ts` (el `rol` es el cubo **visual**; el código desconocido cae en `desconocido`) |
| Los **tres cupos** son tres hechos; el navegador **no** resta | `CifrasCupos` (UI-04) + el espejo `cuposOperativosSchema` |
| La **plantilla** son tres números; el navegador **no** compara el roster con el mínimo | `PlantillaEquipo` (UI-04) + la suite estática de equipos |
| El **conflicto** de una participación lo declara el backend | `participanteAdminSchema` (`conflicho: causaSchema \| null`) |
| La **paginación** la calcula el servidor; el navegador **no** calcula una página | `paginatedResultSchema` (forma congelada) + `estadoDesdeConsulta(..., pagina => pagina.items)` |
| El **filtro** viaja al servidor; el navegador **no** filtra un listado por su cuenta | `admin.filtros.utils.ts` (sólo los parámetros declarados viajan) |

---

## 7. Ficheros

### 7.1 Creados (30)

**`features/admin/operaciones/`** (8): `schemas/operaciones.schema.ts` · `services/admin.service.ts` ·
`utils/admin.claves.utils.ts` · `utils/admin.filtros.utils.ts` · `utils/admin.estado.utils.ts` ·
`utils/admin.cache.utils.ts` · `utils/admin.payload.utils.ts` · `__tests__/admin-integracion.test.ts`

**`features/admin/inscripciones/`** (6): `schemas/inscripcion-admin.schema.ts` ·
`services/inscripcion-admin.service.ts` · `hooks/useInscripcionesAdmin.ts` ·
`views/InscripcionesAdminRuta.tsx` · `views/InscripcionAdminDetalleRuta.tsx` ·
`__tests__/inscripcion-admin.datos.ts`

**`features/admin/equipos/`** (6): `schemas/equipo-admin.schema.ts` · `services/equipo-admin.service.ts` ·
`hooks/useEquiposAdmin.ts` · `views/EquiposAdminRuta.tsx` · `views/EquipoAdminDetalleRuta.tsx` ·
`__tests__/equipo-admin.datos.ts`

**`features/admin/participantes/`** (5): `schemas/participante-admin.schema.ts` ·
`services/participante-admin.service.ts` · `hooks/useParticipantesAdmin.ts` ·
`views/ParticipantesAdminRuta.tsx` · `__tests__/participante-admin.datos.ts`

**`features/admin/pagos/`** (5): `schemas/pago-admin.schema.ts` · `services/pago-admin.service.ts` ·
`hooks/usePagosAdmin.ts` · `views/PagosAdminRuta.tsx` · `__tests__/pago-admin.datos.ts`

### 7.2 Modificados (26)

`features/admin/operaciones/`: `utils/veredicto.adapter.ts` (nuevo `veredictoDesdeEstadoOperativo`) ·
`index.ts` · `components/ConfirmacionIrreversible.tsx` (error del backend + error de campo).

`features/admin/inscripciones/`: `components/DialogoRetirarParticipante.tsx` ( Dueeña de su mutación) ·
`components/PanelPoolInscripcion.tsx` · `views/InscripcionAdminDetalleView.tsx` (el id viaja al S-10) ·
`views/index.ts` · `index.ts` · `__tests__/inscripciones-admin-estados.test.tsx`.

`features/admin/equipos/`: `views/index.ts` · `index.ts` · `__tests__/equipos-admin-estados.test.tsx`.

`features/admin/participantes/`: `views/index.ts` · `index.ts` ·
`__tests__/participantes-admin-estados.test.tsx`.

`features/admin/pagos/`: `components/DialogoAprobarPagoManual.tsx` (dueña de su mutación) ·
`components/ListaPagosOperativa.tsx` · `views/index.ts` · `index.ts` ·
`__tests__/pagos-admin-estados.test.tsx`.

**Rutas (6)**: `app/(administracion)/administracion/inscripciones/page.tsx` ·
`…/inscripciones/[id]/page.tsx` · `…/equipos/page.tsx` · `…/equipos/[id]/page.tsx` ·
`…/participantes/page.tsx` · `…/pagos/page.tsx` — la página pasa a renderizar el **contenedor** (que
lee el dato) y no la vista (que sólo presenta).

### 7.3 Eliminados (4 + 4 carpetas)

Las cuatro fixtures provisionales y sus cuatro carpetas `fixtures/`.

### 7.4 Raíces tocadas / NO tocadas

**TOCADAS:** `Aplicacion/frontend/src/features/admin/{operaciones,inscripciones,equipos,participantes,pagos}/**` ·
las **6** rutas administrativas asignadas · `Aplicacion/task/salesianos-fest-rebuild/evidence/**` · `STATE.md`.

**NO TOCADAS (raíces prohibidas):** `src/features/admin/{components,views,utils}/**` (raíz de **FND-06**) ·
`src/lib/**` · `src/shared/**` · `src/hooks/**` · `src/errors/**` · `src/types/**` · `src/components/**` ·
`src/providers/**` · `src/features/{auth,cuenta,inscripciones,pases,marketplace,public,portada,theme,competencias,validaciones,patrocinadores}/**` ·
`Aplicacion/backend/**` · `contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**` · el `frontend/**`
raíz (copia congelada).

---

## 8. Skills cargados

| Orden | Skill | Uso en este paquete |
|---|---|---|
| 1 | `salesianos-ui-ux` | Los actores, las acciones y los estados de las seis superficies; la regla de que una ruta nunca dibuja un dato que el backend no puede devolver |
| 2 | `salesianos-feature-architecture` | La cadena **página → contenedor → vista → componentes → hooks → servicios → esquemas**; `app/**` sólo enruta; los contenedores nuevos (`*Ruta`) |
| 3 | `salesianos-api-data` | El ledger de endpoints contra el registro real, el espejo Zod 1:1, `apiSend` como único transporte, el `204` que nunca se parsea, la invalidación dirigida, el `queryOptions` por lectura |
| 4 | `salesianos-forms-smart-fields` | El motivo del S-10 (control etiquetado, error asociado y anunciado); por qué **NO** se liga a `GenericForm` (el esquema del wire **no existe**); el 422 → `fieldErrors` |
| 5 | `salesianos-responsive-a11y` | Los estados que la interfaz muestra y el descubrimiento (`sin-datos` ≠ `error` ≠ `sin-permiso`); la etiqueta y el error del campo; la auditoría de los cinco anchos **NO ejecutada** (ver §10) |

---

## 9. Comandos y verificación

| # | Comando | Workdir | Exit | Resultado |
|---|---|---|---|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 5 errores: **4 PROPIOS** (`ParamsListaAdmin` no satisfacía `Record<string, unknown>` — un `interface` sin índice; y un import mal nombrado) + **1 AJENO** (`src/features/patrocinadores/components/FormularioPatrocinador.tsx`, árbol **concurrente** de API-05, **NO tocado**) |
| V2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | **0 errores propios**; queda **1 ajeno** (el mismo de API-05) |
| V3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | **LIMPIO — el proyecto entero** ⇒ **puerta global VERDE** |
| V4 | `npx tsc --noEmit` (final, tras las suites y el escaneo de cierre) | `Aplicacion/frontend` | **0** | **LIMPIO** ⇒ **puerta global VERDE** (verificación final) |
| V5 | `npx tsc --noEmit` (tras exportar los hooks de las cuatro features desde sus barrels) | `Aplicacion/frontend` | **0** | **LIMPIO** ⇒ **puerta global VERDE** |
| V5 | `git status --short -- <raíces>` | raíz | 0 | 6 rutas modificadas + los árboles nuevos de `features/admin/**`; las demás líneas son de **agentes concurrentes** y **NO** se tocaron |

**NOT RUN** (fuera del permiso de este paquete): `vitest` · `biome check` · `next build` · `npm install` ·
servidores · navegadores · la auditoría de los cinco anchos · `pytest` · `manage.py check` ·
`git stash` / `commit` / `reset` / `checkout`.

**Fallos de base conocidos:** ninguno introducido. El único error ajeno (V1/V2) estaba en el árbol
concurrente de **API-05** (`features/patrocinadores/**`) y **se reparó solo** durante este paquete: la
corrida V3 salió 0 sin que este paquete lo tocara.

---

## 10. Tests escritos (NO ejecutados) y los cinco anchos

**Las cinco suites de este paquete están ESCRITAS y NO EJECUTADAS. Nada de lo que sigue puede leerse como
un resultado verde.**

| Suite | Qué congela |
|---|---|
| `features/admin/operaciones/__tests__/admin-integracion.test.ts` (**NUEVA**) | El ledger declara su verdad de registro · **NINGUNA** ruta del área está registrada · el guard **rechaza antes del transporte** y una orden forzada **no emite ninguna petición** · el mensaje del guard nombra el ledger y el motivo · el **mapeo de los filtros** (sólo los declarados, los enteros positivos, los inválidos se descartan, los ausentes no viajan) · las **claves** (un namespace por dataset, la edición/filtro/página/registro/versión en la clave, `undefined` **no** crea una segunda entrada) · los **estados** (sin-datos · cargando · **403 → sin-permiso** · 409/500 → error · la lista toma los ítems de la página) · los **errores de campo** del 422 y que un fallo que no es del backend **no** inventa errores · la **invalidación** exacta de un dataset y que una operación de las inscripciones **no** invalida los pagos · los comandos llevan el **motivo** y el **importe que publicó el servidor** · **NO queda ninguna fixture provisional** (marcador, imports y carpeta) |
| `features/admin/inscripciones/__tests__/inscripciones-admin-estados.test.tsx` (reescrita) | El estado honesto, la fila con el estado y su causa, los tres cupos, las cinco pestañas, el S-10 (el efecto, el motivo y el botón **deshabilitado**) · T-01 · los renders van dentro de un `QueryClientProvider` (el S-10 **posee** su mutación) |
| `features/admin/equipos/__tests__/equipos-admin-estados.test.tsx` (reescrita) | La causa del veredicto, el roster como tres hechos, la acción «Ver equipo», la elegibilidad con el motivo del backend, la nómina, las acciones **deshabilitadas** · T-01 · **el roster NO se compara con el mínimo** |
| `features/admin/participantes/__tests__/participantes-admin-estados.test.tsx` (reescrita) | El prompt primero, el estado honesto, el motivo del conflicto, los tres agrupamientos · T-01 |
| `features/admin/pagos/__tests__/pagos-admin-estados.test.tsx` (reescrita) | El estado honesto, UN veredicto por fila y **nunca** el código, el filtro por estado operativo **expuesto** (obligación congelada), los tres niveles, el diagnóstico oculto por defecto, la capa del proveedor como **texto** · T-01 · **el veredicto NO se deriva** cruzando los campos crudos |

**Los cinco anchos (360 · 390 · 768 · 1024 · 1440): la auditoría sigue ABIERTA.** No se abrió ningún
navegador. Lo que el markup garantiza y el pase de navegador tendrá que confirmar:

| Ancho | Lo que hace la composición | Lo que sigue sin verificar |
|---|---|---|
| 360 | Una columna; una tarjeta por fila; los filtros en una hoja; el detalle del pago en una hoja inferior; **todas** las acciones de 44 px | Que ninguna página desborde, que la hoja quepa, que los nombres largos se trunquen |
| 390 | La misma columna única | Ídem |
| 768 | Las listas son tablas con las columnas de prioridad; los filtros en línea | Que las tres columnas de prioridad no se compriman |
| 1024 | Las tablas publican las columnas de prioridad 2; la hoja del pago es un panel lateral | Que ninguna columna se estire ni se recorte |
| 1440 | Igual, con la banda de contenido acotada por el shell | Ídem |

**Accesibilidad decidida en el markup (no verificada en navegador):** cada filtro tiene nombre visible y
asociado; el motivo del S-10 tiene `<label>` y su error se anuncia con `role="alert"`; el error **de
campo** del backend se asocia al control por `aria-describedby`; el veredicto nunca se sustituye por el
código; el diagnóstico es un descriptor real con `aria-expanded`.

**Lagunas residuales declaradas, nunca asumidas verdes:** sin render de navegador, sin lector de pantalla,
sin reflujo al 200 %, sin axe ni Lighthouse, y **las cinco suites nunca se han ejecutado**.

---

## 11. Desviaciones, decisiones y peticiones a A0

### 11.1 Decisiones

| ID | Tipo | Qué |
|---|---|---|
| `D-API04-01` | decisión | **CERO rutas ligadas.** Ninguna ruta administrativa del alcance existe en el backend. El área se entrega como **costura tipada**: espejos Zod, ledger con la verdad de registro, guard que impide llamar a una ruta inexistente, hooks, claves, invalidación, política de errores y contenedores. |
| `D-API04-02` | decisión | **El guard es el mecanismo, no una convención.** `pedirAdmin()` construye la URL **antes** del transporte y **lanza** si la ruta no está registrada: es imposible, desde el frontend, emitir una petición a una URL que responde 404. |
| `D-API04-03` | decisión | **Un solo lugar decide la existencia de una ruta:** `RUTAS_ADMIN`. El botón de la acción **y** el servicio leen el mismo registro, de modo que la interfaz y el transporte no pueden discrepar. |
| `D-API04-04` | decisión | **El `wire` y la vista son dos formas.** El `estado_operativo` del wire es el `EstadoOperativo` congelado (`{codigo, etiqueta, descripcion}`); el cubo visual (`rol`) **no viaja**: lo añade el adaptador. Un backend no publica una decisión de la interfaz. |
| `D-API04-05` | decisión | **El `enabled` de cada lectura es la verdad de registro.** Con la ruta sin registrar la superficie muestra el estado honesto y **no** una lectura eternamente pendiente. |
| `D-API04-06` | decisión | **La invalidación vive dentro de la `mutationFn`** y **declara exactamente** el dataset que ensucia (`FND-08` §3 reglas 5 y 6). |
| `D-API04-07` | decisión | **Los datos de las suites salen del espejo** (`schema.parse(...)`) y viven en `__tests__/`: una forma que el espejo rechaza rompe la suite **antes** de dibujar. |
| `D-API04-08` | decisión | **El motivo del S-10 sigue siendo un control etiquetado** (no un `GenericForm`): el esquema del wire de la acción **no existe** porque la ruta no existe. API-04 aporta el **constructor del payload** y el **mapa de errores de campo**, que son la costura que falta para que la ligação sea un fichero. |

### 11.2 Peticiones a A0

| ID | Petición | ¿Bloqueante? |
|---|---|---|
| `A0-API04-01` | **BLOQUEANTE — registrar los cinco controllers administrativos**: `AdminInscripcionController` (`RT-IN-07`, `RT-IN-08`), `AdminEquipoController` (`RT-IN-09`, `RT-IN-10`), `AdminParticipanteController` (`RT-IN-11`), `AdminPagoController` (`RT-PG-04`, `RT-PG-05`, `RT-PG-07`) y `AdminPersonaController` (`RT-ID-07`, `RT-ID-08`). `RT-PG-04` y `RT-PG-05` **ya están CONGELADOS** en GOV-01: sólo falta el registro | **Sí** |
| `A0-API04-02` | **Publicar el wrapper `AdminPagoAprobarManualOut`** (la respuesta de `RT-PG-05`): hoy el espejo asume la compra operativa actualizada | No |
| `A0-API04-03` | **Unificar el envelope de error**: el `apiErrorSchema` compartido (`src/types/api.types.ts`) **no declara `field_errors`** y **rechaza** un `details: null`, de modo que el área administrativa declara su propio espejo del envelope de error (`adminErrorEnvelopeSchema`) | No |
| `A0-API04-04` | **Ratificar el tipo del importe** del presenter administrativo: el plan lo declara como cadena (`"0.00"`) y la proyección de `CompraOut` (DOM-01) lo manda como `float` | No |
| `A0-API04-05` | **Reconciliar los espejos** con los presenters reales en el momento del registro: hoy los cuatro espejos del área transcriben el contrato **declarado** (ledger + plan `contratos/01`), no un presenter existente | No |
| `A0-API04-06` | **Publicar la ruta administrativa de retirada** (`A0-UI04-04`): la registrada es del responsable, **no admite motivo** y el módulo **no** autoriza al administrador | **Sí** (para `ADM-06`/`ADM-08`) |
| `A0-API04-07` | **Sincronizar `00-matriz-tareas.md`** (`T-075`, `T-076`): la matriz es una raíz prohibida de este paquete | No |
| `A0-API04-08` | **Atribuir `ADM-15/17/18/19`** (el área administrativa de pases, que **sí** tiene rutas registradas: `RT-PS-06`…`RT-PS-08`). Siguen **NO ATRIBUIDAS** (`A0-API05-05`); este paquete **no** las reclamó ni las tocó | No |

### 11.3 Bloqueos reportados (nada se inventó)

| # | Bloqueo | Evidencia | Dueño |
|---|---|---|---|
| `B-04-01` | `RT-IN-07` / `RT-IN-08` no existen ⇒ la lista y el detalle de las inscripciones administrativas no tienen fuente | `config/api.py` | A0 |
| `B-04-02` | `RT-IN-09` / `RT-IN-10` no existen ⇒ la lista y el detalle de los equipos no tienen fuente | ídem | A0 |
| `B-04-03` | `RT-IN-11` no existe ⇒ la búsqueda administrativa de participantes no tiene fuente | ídem | A0 |
| `B-04-04` | `RT-PG-04` / `RT-PG-05` / `RT-PG-07` no existen ⇒ la lista operativa, el detalle comercial y la aprobación manual del pago no tienen fuente | ídem | A0 |
| `B-04-05` | `RT-PG-06` no existe (`PagosController` no expone `/intentos`) ⇒ el diagnóstico por ruta propia no tiene fuente; hoy viajaría dentro de `RT-PG-07` (también inexistente) | `pagos_controller.py` | A0 |
| `B-04-06` | `RT-ID-07` / `RT-ID-08` no existen ⇒ el panel administrativo de personas no tiene fuente | `config/api.py` | A0 |
| `B-04-07` | El **ledger contradice al módulo**: el ledger declara `RT-IN-02/03/04/05/06` como «Responsable **o** Administrador», pero `PoolOrchestrator` **no** deja al administrador sustituir la titularidad ⇒ el 403 del pool de una inscripción ajena es la respuesta **real** del backend | `pool_orchestrator.py` · `FR-03` §2.1 | A0 (conciliar el ledger con el módulo) |
| `B-04-08` | No hay **preset de pagination** en el ledger de las listas administrativas salvo `RT-PG-04`; el resto lo refleja | `SH-05` `P-11` | A0 |

---

## 12. Rollback

1. Borrar los **30** ficheros creados (§7.1) y restaurar los **26** modificados (§7.2) desde el estado
   previo a este paquete (**la versión de UI-04** de las vistas, los diálogos, los paneles, los barrels y
   las seis rutas).
2. **No** restaurar las fixtures provisionales: el rollback devuelve el área al estado **sin datos** de
   UI-04, que es el estado honesto de las rutas.
3. `git stash` **nunca** se invocó; no hay commit de este paquete; el punto de rollback del árbol es el
   mismo que antes del paquete.

---

## 13. Preparación de XCT-02 (transversal admin)

**LISTO**

- El **namespace de claves** del área administrativa existe y es **uno por dataset** (`admin.inscripciones`,
  `admin.equipos`, `admin.participantes`, `admin.pagos`) con la edición, el filtro, la página, el registro
  y la versión dentro de la clave: XCT-02 **no** tiene que inventar un namespace.
- La **capa de servicio** del área existe con un **único transporte** (`apiSend`), un **único ledger** y
  un **guard** que impide llamar a una ruta inexistente.
- La **política de estados, de errores y de permisos** está en un fichero (`admin.estado.utils.ts`) y
  cubre el `403` como estado de permiso, el `409`/`422`/`500` como error y el `422` con errores de campo.
- La **invalidación** dirigida vive en un fichero (`admin.cache.utils.ts`).
- Los **contenedores** de las seis rutas leen el dato y le entregar el estado a la vista: XCT-02 puede
  componer el resumen, el contexto de edición y la auditoría **encima** de esta capa sin reescribir las
  vistas.

**PENDIENTE**

- **CERO rutas ligadas**: sin los cinco controllers administrativos registrados (§11.3) no hay dato que
  resumir. El resumen, las métricas y la auditoría transversales **no tienen fuente** hasta entonces.
- El **contexto de edición** del área administrativa depende del `edicion_id`: la lista lo filtra, pero
  la **edición vigente** la resuelve `features/public` (`RT-ED-01`), cuyo dueño es otro (§11.3, `B-04-08`).
- La **auditoría** (actor, hora, motivo) no la publica ningún presenter del área: la decisión de qué se
  audita es de XCT-02 (`T-083`) y del módulo `administracion` del backend.

**Arranque:** cuando A0 registre `AdminPagoController` (`RT-PG-04` **congelada**), el único cambio del
frontend es `registrado: true` en `RUTAS_ADMIN.pagosLista` y el **encendido** de la lectura: la
invalidación, los estados, los errores y el filtro ya están.

---

## 14. Criterios de aceptación del paquete

- [x] **El presenter del backend aporta el estado, la causa y las acciones; el cliente no los deriva.**
      El `estado_operativo` del wire es el `EstadoOperativo` congelado; el cubo visual lo añade el
      adaptador; la suite de pagos congela estáticamente que el veredicto **NO** se cruza con los campos
      crudos.
- [x] **La propiedad de servicio, hook, clave, invalidación y envelope es explícita y está probada.**
      Un cliente (`admin.service.ts`), un ledger (`RUTAS_ADMIN`), una factoría de claves por dataset, una
      invalidación dirigida y un envelope de error propio, todo con suite.
- [x] **No queda ninguna fixture**; **una orden forzada de una operación no autorizada se maneja como el
      403 del backend** (el guard lanza antes del transporte y el `403` se mapea al estado de permiso con
      la prosa del servidor).
- [x] **Ninguna ruta administrativa inexistente fue ligada** ni inventada: el guard lo impide por
      construcción y la suite lo demuestra con **cero peticiones** emitidas.
- [x] El **único comando de runtime** fue el typecheck y está **verde** (V3 y V4, exit 0).
- [ ] La **auditoría de los cinco anchos**, el pase de tecnología asistiva, la **ejecución de las cinco
      suites** y el pase de lint siguen **DIFERIDOS** — el paquete queda `verification_required`.

---

**Integro:** `sdd/salesianos-fest-rebuild/api-04-apply-progress` (Engram) + este fichero + la transición
completa del `STATE.md` físico.
