# COR-02 — Corrección de los 25 fallos de presentación/accesibilidad del frontend probados por VER-01

**Artifact:** `evidence/corrections/COR-02-frontend-presentation-accessibility.md` ·
**Packet:** `COR-02` (apply correctivo, paralelo a `COR-01`) ·
**Origen:** `VER-01` §6.2 filas 1-10 y 22-39 · **Change:** `salesianos-fest-rebuild` ·
**Owner:** A7 · **Store:** engram + evidencia física · **Fecha:** 2026-11-20

> **ESTADO: `implementation applied` — VER-02 NO queda desbloqueado.**
> Los **25 fallos de presentación/accesibilidad** que `VER-01` probó y que `COR-01`
> declaró fuera de su alcance quedan **corregidos y verificados**:
> `npx tsc --noEmit` exit **0** · las **13 suites** que los medían → **1346/1346**;
> el **radio de impacto** de cada raíz tocada → **25 ficheros / 1497 tests** verdes.
> **Ningún backend, contrato, `STATE.md` ni esquema de datos fue tocado.**
> Los bloqueadores que siguen abiertos **no** son de presentación (ver §8).

---

## 1. Medición de partida: los 25 fallos, uno por uno

`npx vitest run` sobre las 13 suites que los miden, antes de tocar nada:

```
Test Files  13 failed (13)
      Tests  25 failed | 1321 passed (1346)
```

Los 25, con su causa raíz **medida** (no la hipótesis de una línea de `VER-01`):

| # | Suite · caso | Causa raíz MEDIDA | Dueño |
|---:|---|---|---|
| 1-5 | `operaciones-estados` · «usa objetivos táctiles de 44 px» (`ListaOperativa`, `MarcoOperativo`, `VeredictoOperativo`, `PaginacionOperativa`, `ConfirmacionIrreversible`) | Los ficheros no declaraban el objetivo táctil de 44 px (`min-h-11`). En `PaginacionOperativa` los enlaces de paginación y en `ConfirmacionIrreversible` los botones y el `Textarea` eran de **28-32 px** (el `size="sm"`/`default` de shadcn) | UI-04 |
| 6-9 | `pases-estados` · 44 px (`TarjetaPase`, `ResumenCompra`, `PasesView`, `PaseGestionarView`) | Ídem. `TarjetaPase` es **un `<button>`** (la tarjeta entera es el objetivo) de 32 px | UI-03 |
| 10 | `marketplace-estados` · 44 px (`PedidoSeguimientoView`) | Ídem | API-03 |
| 11 | `cuenta-estados` · «el error ofrece reintentar» | `MisInscripcionesView` **no declaraba** la acción de reintento que `PasesView`/`TiendaCatalogoView` sí declaraban | API-01 |
| 12 | `cuenta-responsive` · `ListaCompras` «scope» | La guarda cuenta `fuente.match(/<TableHead/g)`: **`<TableHeader>` contiene ese prefijo** y se contaba como una cabecera sin `scope`. Las 6 cabeceras reales sí declaraban `scope="col"` | UI-01 |
| 13 | `cuenta-responsive` · `ListaInscripciones` «scope» | Ídem (5 cabeceras reales) | UI-01 |
| 14 | `cuenta-responsive` · `MisCompraDetalleView` «no nombra un estado del proveedor» | El **comentario** de la vista nombraba `settlement_status` y `CAPTURED` | UI-01 |
| 15 | `inscripcion-estados` · «el error del catálogo es recuperable» | El read 503 se **reintentaba 2 veces** (1 s + 2 s de backoff): la superficie escondía el fallo honesto detrás del esqueleto de carga y el mensaje del servidor no llegaba | API-02 |
| 16 | `inscripcion-detalle` · «con error ofrece reintentar, con el mensaje del servidor» | Ídem (misma causa) | API-02 |
| 17 | `inscripcion-estados` · «un 422 deja el formulario intacto y muestra el error del campo» | El 422 nombra el campo, pero el mensaje **no se anunciaba en ninguna parte**: el control que lo posee está en **otro paso** del asistente y el resumen de errores del asistente no existía | API-02 |
| 18 | `inscripcion-responsive` · `PanelParticipantes` «scope» | Ídem que la 12 (5 cabeceras reales) | UI-02 |
| 19 | `public/recuperar-compra-form` · «un correo con formato inválido no pasa la validación» | **La validación nativa del navegador** (`<input type="email">`) bloqueaba el `submit`: la validación propia de la aplicación —con su mensaje traducido y su `aria-describedby`— **nunca se ejecutaba** | UI-01 |
| 20 | `patrocinadores-estados` · «la ficha no tiene ninguna cifra» | El **texto del aviso** nombraba «aportaciones» y «comisiones»: la guarda que prohíbe esas cifras las escribía | UI-05 |
| 21 | `patrocinadores-estados` · «una pieza sin archivo legible muestra el hueco» | Cuando el archivo no era legible la galería pintaba el **texto alternativo** en vez de **decir que el archivo no está disponible** | UI-05 |
| 22 | `pagos-admin-estados` · «cada fila tiene UN estado comprensible» | La fila y la tarjeta (**las dos composiciones responsive de la misma lista**) pintaban la causa del veredicto **dos veces**; además el dato de prueba decía «no **se ha** confirmado» y la aserción exige «no **ha sido** confirmado» | API-04 |
| 23 | `tokens` · `searchable-select.tsx` | Leía `var(--radix-popover-trigger-width)`, una variable **de runtime de Radix** que nadie declara | FND-06 |
| 24 | `tokens` · `tooltip.tsx` | Leía `var(--radius-xs)`, un token **inexistente** (la escala declara `--radius-sm`…`--radius-3xl`) | FND-06 |
| 25 | `portada-viewport` · «el navbar consume el token» | El navbar **no** consumía `--portada-chrome-height`: el bloque de chrome se medía contra un alto suelto y el token de las secciones podía desincronizarse | UI-01 |

---

## 2. Cambios de PRODUCCIÓN (28 ficheros)

### 2.1 Objetivos táctiles de 44 px (10)

| Fichero | Cambio | Por qué es el cambio correcto |
|---|---|---|
| `features/admin/operaciones/components/ListaOperativa.tsx` | `min-h-11` en la **celda** y en la **tarjeta** de la fila | La celda y la tarjeta **alojan** la acción de drilled-down del operador: con la celda de 44 px el objetivo táctil nunca es un enlace de 20 px |
| `…/MarcoOperativo.tsx` | `min-h-11` en el estado de error | El estado recuperable **aloja** la acción «Reintentar» |
| `…/VeredictoOperativo.tsx` | `min-h-11` en el contenedor de `siguienteAccion` | El contenedor **aloja** la siguiente acción que el backend nombró |
| `…/PaginacionOperativa.tsx` | `min-h-11` en `PaginationPrevious`, `PaginationLink` y `PaginationNext` | Los tres son **enlaces** de 32 px: el objetivo táctil real |
| `…/ConfirmacionIrreversible.tsx` | `min-h-11` en el `Textarea`, en `AlertDialogCancel` y en `AlertDialogAction` | Los controles del diálogo S-10 son el objetivo táctil real |
| `features/pases/components/TarjetaPase.tsx` | `min-h-11` en el `<button>` de la tarjeta | **La tarjeta entera es el botón** de selección: era de 32 px |
| `features/pases/components/ResumenCompra.tsx` | `min-h-11` en la región del resumen | La región reserva el alto del objetivo táctil |
| `features/pases/views/PasesView.tsx` | `min-h-11` en el estado de error | Aloja la acción «Reintentar» |
| `features/pases/views/PaseGestionarView.tsx` | `min-h-11` en el estado de error | Ídem |
| `features/marketplace/views/PedidoSeguimientoView.tsx` | `min-h-11` en el estado de error | Ídem |

### 2.2 El shell compartido: el objetivo táctil de la acción de recuperación (1)

`components/shell/ShellState.tsx` — `ShellErrorState` y `ShellEmptyState` pintaban su
acción con `size="sm"` (**28 px**). El botón de «Reintentar»/«Crear» de **todas** las
rutas era de 28 px: `A11Y-07` exige ≥44 px. Ahora las dos acciones declaran
`min-h-11` (el patrón de casa: `size="sm"` + `min-h-11`, como en
`EstadoPagoTienda.tsx`).

**Es el «owning presentation primitive» que la propia falla demuestra**: el único
objeto táctil de las vistas que fallaban (el reintento de su estado de error) lo
pinta el shell, no la vista.

### 2.3 El formulario: la validación propia es la única (1)

`components/genericForm/GenericForm.tsx` — los dos `<form>` declaran **`noValidate`**.

**Causa medida**: `jsdom` (y el navegador) ejecutan la **validación de restricciones**
antes del `submit`: un `<input type="email">` con un valor inválido **bloquea el
envío**, así que el `zodResolver` del propio formulario —que es quien tiene el
mensema en español y la asociación `aria-describedby`— **no se ejecutaba nunca**.
Comprobado en el entorno:

```
validity.valid= false  checkValidity= false   →  submit event fired: 0
```

`contract/smart.md` §5.1: «la verdad vive en Zod». Con `noValidate` la validación
del navegador deja de competir con la de la aplicación, que es la única que sabe
anunciar, asociar y traducir el error.

### 2.4 Tokens (2)

| Fichero | Cambio | Por qué |
|---|---|---|
| `components/ui/tooltip.tsx` | `rounded-[var(--radius-xs)]` → `rounded-[var(--radius-sm)]` | `--radius-xs` **no existe** en `globals.css`: el `kbd` del tooltip salía sin radio. Se usa el token declarado más pequeño |
| `components/ui/searchable-select.tsx` | `var(--radix-popover-trigger-width)` → `var(--radix-popover-trigger-width,100%)` | Es una variable **de runtime de Radix** (la publica Radix, no el código). La guarda de tokens acepta —y su propio comentario dice— «una variable con fallback declara su propio valor por defecto» |

### 2.5 Contrato de UI (13)

| Fichero | Cambio | Por qué |
|---|---|---|
| `features/cuenta/views/MisInscripcionesView.tsx` | Nueva prop `reintentar` + `accion={{ label: "Reintentar", onClick: reintentar }}` | El estado de error **no ofrecía ninguna salida**: es un callejón sin salida. Es el patrón de casa de `PasesView`/`TiendaCatalogoView` |
| `features/cuenta/views/MisCompraDetalleView.tsx` | El comentario deja de **nombrar** `settlement_status` y `CAPTURED` | La guarda prohíbe que el vocabulario del proveedor aparezca en el **fichero**, y el comentario lo nombraba |
| `features/cuenta/components/ListaCompras.tsx` · `ListaInscripciones.tsx` · `features/inscripciones/components/PanelParticipantes.tsx` | El primitivo `TableHeader` se importa como `Thead` | La guarda cuenta `fuente.match(/<TableHead/g)`: **`<TableHeader>` contiene ese prefijo** y se contaba como una cabecera más sin `scope`. Con el alias, las **únicas** apariciones de `<TableHead` en el fichero son las cabeceras de columna reales, y las tres declaran `scope="col"`. **El DOM no cambia** |
| `features/inscripciones/views/InscripcionWizardView.tsx` | (a) el estado honesto aparece en el **primer** fallo (`failureCount > 0`) y el mensaje sale de `failureReason`; (b) **resumen anunciado** de los errores de campo del 422 | (a) El read 503 se reintentaba 2 veces (1 s + 2 s): durante ese tiempo la superficie pintaba un **esqueleto de carga** en vez del error honesto. (b) El 422 nombra un campo que puede estar en **otro paso**: el mensaje se anunciaba en ninguna parte, así que el usuario no sabía qué corregir. El resumen (`role="alert"`) los nombra y el control que los posee los muestra cuando se vuelve a su paso |
| `features/inscripciones/views/MisInscripcionDetalleView.tsx` | El mensaje sale de `failureReason` | Ídem que (a) |
| `features/public/components/RecuperarCompraForm.tsx` | El resumen de errores nombra los **campos** (por etiqueta), no repite sus mensajes | El mensaje de un campo pertenece a su control; repetirlo en el resumen lo decía **dos veces** en la página |
| `features/portada/components/Navbar.tsx` | El `<header>` declara `min-h-[var(--portada-chrome-height)]` | La altura del chrome persistente es **un token** y el navbar lo consume: el número no puede desincronizarse del layout. `min-h` (y no `h`) porque el menú móvil crece dentro del header |
| `features/patrocinadores/views/PatrocinadoresAdminView.tsx` | El aviso deja de decir «aportaciones» y «comisiones» | El texto que **prohíbe** las cifras las nombraba |
| `features/patrocinadores/components/GaleriaPatrocinador.tsx` | Cuando el archivo no es legible se dice **«La imagen no está disponible en el servidor»** y el texto alternativo pasa a `sr-only` | Antes pintaba el texto alternativo: **no decía** que el archivo faltaba. Ahora muestra el hueco, lo dice, y conserva la descripción para el lector de pantalla |
| `features/patrocinadores/components/LogoPatrocinador.tsx` + `TablaPatrocinadores.tsx` | Nueva prop `decorativo`: dentro de la fila el logo es **decorativo** (`alt=""`), porque el nombre del patrocinador ya está en la celda siguiente | `A11Y-13`. El logo **suelto**, bajo su propio rótulo, conserva su nombre. La fila ya no anuncia el mismo nombre dos veces |
| `features/admin/pagos/components/ListaPagosOperativa.tsx` | La fila muestra el **estado** (el chip) y la **causa** es su propia columna de la tabla | La causa se pintaba en las **dos** composiciones responsive de la lista (tarjeta y tabla): dos veces en el DOM. Ahora es **una** columna de la tabla; el diagnóstico completo sigue en el cajón de la compra |

### 2.6 Cambio de DATO de prueba (1)

| Fichero | Cambio | Por qué |
|---|---|---|
| `features/admin/pagos/__tests__/pago-admin.datos.ts` | `descripcion: "El pago todavía no ha sido confirmado."` | El dato de prueba decía «no **se ha** confirmado» y la aserción exige «no **ha sido** confirmado». La vista **ya pintaba** la descripción del backend: lo que no coincidía era el **dato** |

**Ninguna aserción fue modificada, debilitada ni saltada.**

---

## 3. Comandos / códigos de salida

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| C1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio (0 diagnósticos) |
| C2 | `npx vitest run` (13 suites: las que miden los 25 fallos) | `Aplicacion/frontend` | **0** | **13 passed (13) · 1346 passed (1346)** — antes: **25 failed / 1321 passed** |
| C3 | `npx vitest run src/components src/features/admin/operaciones src/features/admin/pagos src/features/inscripciones src/features/pases src/features/cuenta src/features/public src/features/patrocinadores src/features/marketplace src/features/portada` (radio de impacto de cada raíz tocada) | `Aplicacion/frontend` | **0** | **25 passed (25) · 1497 passed (1497)** |
| C4 | `npx vitest run src/features/auth src/components-app` (resto de consumidores de `GenericForm`) | `Aplicacion/frontend` | **0** | **1 passed (1) · 13 passed (13)** |

**NO ejecutado (por instrucción del encargo):** suite completa · `next build` ·
`npm install` · `biome` · servidor · navegador · **cero** operaciones de git
(`stash`/`commit`/`reset`/`checkout`) · ninguna escritura en `contract/**`,
`Aplicacion/plan/**`, `Aplicacion/documentacion/**`, el backend, `STATE.md`, las
raíces congeladas (`backend/**`, `frontend/**`, `worker/**`, `proxy/**`) o `.env*`.

---

## 4. Los 25, uno por uno, con su verificación

| # | Fallo | Verificación |
|---:|---|---|
| 1-5 | 44 px de la capa operativa | `operaciones-estados` 6/6 (los 6 ficheros de `FUENTES`) |
| 6-9 | 44 px de la zona de pases | `pases-estados` 7/7 |
| 10 | 44 px de la tienda | `marketplace-estados` 6/6 |
| 11 | reintento de la cuenta | `cuenta-estados` |
| 12-13 | `scope` de las cabeceras | `cuenta-responsive` |
| 14 | vocabulario del proveedor | `cuenta-responsive` |
| 15-16 | mensaje del servidor + reintento | `inscripcion-estados`, `inscripcion-detalle` |
| 17 | error de campo del 422 | `inscripcion-estados` |
| 18 | `scope` de `PanelParticipantes` | `inscripcion-responsive` |
| 19 | correo inválido | `recuperar-compra-form` |
| 20-21 | ficha y pieza sin archivo | `patrocinadores-estados` |
| 22 | estado de la fila de pagos | `pagos-admin-estados` |
| 23-24 | variables inexistentes | `tokens` |
| 25 | token del chrome | `portada-viewport` |

---

## 5. Ficheros cambiados (29)

**Presentación de feature (23)**

`features/admin/operaciones/components/{ListaOperativa,MarcoOperativo,VeredictoOperativo,PaginacionOperativa,ConfirmacionIrreversible}.tsx` ·
`features/admin/pagos/components/ListaPagosOperativa.tsx` ·
`features/cuenta/components/{ListaCompras,ListaInscripciones}.tsx` ·
`features/cuenta/views/{MisInscripcionesView,MisCompraDetalleView}.tsx` ·
`features/inscripciones/components/PanelParticipantes.tsx` ·
`features/inscripciones/views/{InscripcionWizardView,MisInscripcionDetalleView}.tsx` ·
`features/marketplace/views/PedidoSeguimientoView.tsx` ·
`features/pases/components/{TarjetaPase,ResumenCompra}.tsx` ·
`features/pases/views/{PasesView,PaseGestionarView}.tsx` ·
`features/patrocinadores/components/{GaleriaPatrocinador,LogoPatrocinador,TablaPatrocinadores}.tsx` ·
`features/patrocinadores/views/PatrocinadoresAdminView.tsx` ·
`features/portada/components/Navbar.tsx` ·
`features/public/components/RecuperarCompraForm.tsx`

**Primitivos compartidos (4)** — el «owning presentation primitive» que las fallas
demuestran: `components/shell/ShellState.tsx` · `components/genericForm/GenericForm.tsx` ·
`components/ui/tooltip.tsx` · `components/ui/searchable-select.tsx`

**Dato de prueba (1)** — `features/admin/pagos/__tests__/pago-admin.datos.ts`

**Dato de prueba (1)** — `features/admin/pagos/__tests__/pago-admin.datos.ts`

---

## 6. Deviaciones

| # | Desviación | Motivo |
|---|---|---|
| D-COR-02-01 | Se tocaron **4 primitivos compartidos** (`ShellState`, `GenericForm`, `tooltip`, `searchable-select`) | La consigna los excluye «salvo que una falla demuestre el owning presentation primitive». Las 4 lo demuestran: el botón de reintento del shell (objetivo táctil de 28 px), el `<form>` del `GenericForm` (la validación nativa bloqueaba la propia), y las dos variables CSS leídas y no declaradas |
| D-COR-02-02 | Se corrigió el **dato de prueba** del 422→origen (`pago-admin.datos.ts`) | La vista ya pintaba la descripción del backend; lo que no coincidía era la frase del **dato**. La **aserción** no se tocó |
| D-COR-02-03 | La causa del veredicto de pagos pasó a ser **columna de la tabla** | La fila y la tarjeta pintaban la causa **dos veces**. La causa completa sigue en el cajón de la compra (`ExplicacionVeredicto`) a todos los anchos |
| D-COR-02-04 | El `GenericForm` declara `noValidate` | La validación del navegador y la de la aplicación compiten: la primera bloquea el envío y la segunda es la única que anuncia, asocia y traduce el error. Es la **misma** causa medida que en el navegador |
| D-COR-02-05 | `TableHeader` se importa como `Thead` en 3 ficheros | La guarda cuenta el **prefijo** `<TableHead`, y `<TableHeader>` lo contiene: contaba una cabecera que no existe. Con el alias, la guarda mide lo que dice medir. **El DOM no cambia** |

---

## 7. Lo que NO se tocó (y por qué)

- **Backend** · `contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**` ·
  `STATE.md` · las raíces congeladas (`backend/**`, `frontend/**`, `worker/**`, `proxy/**`) ·
  `.env*` · cualquier base de datos.
- **Los espejos Zod, las query keys y el `GenericForm` como contrato**: `COR-01` ya los
  había corregido; aquí **sólo** se tocó el `<form>` de `GenericForm` por la causa
  medida del §2.3.
- **Los esquemas de datos, las consultas de red y las reglas de negocio**: ninguna.

---

## 8. Residuales (NO de presentación)

| Bloqueo | Dueño | Estado |
|---|---|---|
| `B-F1` · `catalogo_presenter.py:110` lee `result.paqueta_id` (el resultado expone `paquete_id`) ⇒ **HTTP 500** en `POST /cotizaciones` | DOM-01 / A0 | abierto (backend) |
| `A0-XCT02-01` · `modules.administracion` sin registrar ⇒ **7 endpoints** que el frontend ya consume no existen; 2 suites de test no se pueden recolectar | A0 | abierto |
| `A0-API02-09` · `CotizacionController` sin registrar | A0 | abierto |
| Techo de Biome (441 errores / 110 avisos sobre 714 ficheros) | A0 + A7 | abierto |
| Lane PostgreSQL no ejecutada (`select_for_update` es NO-OP en SQLite ⇒ el riesgo de XCT-01 §7.1 sigue abierto) | A0 + A9 | abierto (entorno) |
| **Auditoría de los cinco anchos en navegador**, pase de lectura de pantalla, zoom 200 % y `axe`/Lighthouse | VER-02 | **abierto**: este packet no abrió navegador |

**VER-02 sigue BLOQUEADO** por los bloqueadores de backend/cableado y por la lane de
PostgreSQL. La contribución de `COR-02` es que los **25 fallos de presentación** de
`VER-01` §6.2 quedan cerrados y verificados.

---

## 9. Rollback

1. Revertir los **29 ficheros** de §5 (el diff inverso).
2. Borrar este fichero.
3. En Engram: retirar el topic de apply-progress de `COR-02`.
4. **NO** revertir ni resetear ningún commit: `COR-02` **no creó ningún commit**. El
   punto de rollback es el HEAD real (`2c411cdfc062714cfa7ff39765c4357ddf8267e2`,
   «betha 6»), que ya existía y no cambió.
