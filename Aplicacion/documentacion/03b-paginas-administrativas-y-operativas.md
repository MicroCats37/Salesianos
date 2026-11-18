# 03b — Páginas administrativas y operativas

> **Estado:** vigente (documento de referencia del rebuild controlado bajo `Aplicacion/`)
> **Alcance:** frontend Next.js (App Router) — las 16 páginas enrutables de administración, operación, acreditación/acceso, competencia, capacidad, equipo, participante y pase de fiesta, más los 2 *route handlers* de sesión que las sostienen
> **Fuente de verdad:** el código. Este documento describe lo que existe hoy, no lo que debería existir
> **Owner:** frontend (la UI no es la autoridad de dominio; el backend lo es)
> **Última verificación:** 2026-11-18 sobre el árbol de trabajo local (`frontend/src/app`, `frontend/src/features/admin`, `frontend/src/features/inscripciones`, `frontend/src/features/pases`, `backend/modules/administracion`, `backend/modules/competencias`, `backend/core`)

## Convenciones de lectura

| Marcador | Significado |
|---|---|
| ✅ | Verificado en código en esta pasada |
| 🟡 | Verificado parcialmente o deducido del código con alta confianza |
| 🔴 | Brecha o incumplimiento verificado, sin resolver |

Los documentos hermanos de esta serie viven en el mismo directorio (`Aplicacion/documentacion/`) y se publican por separado; este documento no resume ni anticipa su contenido. Los contratos normativos están en [`../../contract/`](../../contract/) y son vinculantes cuando el código y el contrato discrepan: **el código describe la realidad, el contrato describe la obligación**.

Documentos hermanos: [`03-frontend.md`](./03-frontend.md) (mapa ruta → feature → endpoint), [`02-backend-y-api.md`](./02-backend-y-api.md) y [`02a-inventario-de-endpoints.md`](./02a-inventario-de-endpoints.md) (catálogo de endpoints), [`04-datos-y-dominio.md`](./04-datos-y-dominio.md) (modelos y tablas), [`05-flujos-end-to-end.md`](./05-flujos-end-to-end.md) (flujos), [`06-operacion-y-deuda-tecnica.md`](./06-operacion-y-deuda-tecnica.md) (deuda técnica), [`README.md`](./README.md) (índice del conjunto documental) y [`00-cobertura-y-trazabilidad.md`](./00-cobertura-y-trazabilidad.md) (recuentos de cobertura verificados).

---

## 1. Resumen ejecutivo

La superficie administrativa está **implementada y viva**: 16 páginas enrutables (12 dentro de `/administracion`, 4 del panel del responsable y de los pases de fiesta) resuelven contra 40+ endpoints de Django, con un modelo de permisos por **capacidades** evaluado en el servidor, paginación canónica, filtros propiedad de la URL, estados de carga/empty/error explícitos y validación Zod 1:1 de cada envoltorio del backend.

Cuatro conclusiones operativas:

1. ✅ **La autoridad es el backend, siempre.** El frontend tiene tres capas de guarda visibles (`proxy.ts` → `(app)/layout.tsx` → `administracion/layout.tsx` + `AdminSeccionGuard`) y todas son **corteses**: la última decisión la toma `RequireCapability` (`backend/core/permissions.py`) en cada petición. El cliente nunca decide un permiso.
2. ✅ **El modelo de capacidades es el único vocabulario de autorización** (`backend/core/capacidades.py`), con tres niveles: `usuario` (sin capacidades), `staff` (lee todo, escribe en dominios operativos) y `superusuario` (break-glass, conjunto completo). El frontend replica el vocabulario (`features/admin/utils/admin.capacidades.ts`) **solo para ocultar controles**.
3. ✅ **La superficie es de lectura porosa y de escritura quirúrgica.** 10 de las 16 páginas son de solo lectura; 3 escriben dentro del área administrativa (`/administracion/pagos`, `/administracion/competencias/cuadro`, `/administracion/competencias/[id]`) con exactamente 3 acciones sensibles, todas con motivo auditado y bloqueo optimista `expected_version`; las 3 restantes escriben para el propio responsable (detalle de inscripción, asistente de inscripción y compra de pases).
4. 🔴 **Hay superficie declarada y no implementada**: 5 de las 11 capacidades del backend (`admin.inscripciones.escribir`, `admin.equipos.escribir`, `admin.acreditaciones.escribir`, `admin.usuarios.gestionar`, `admin.usuarios.promover_superusuario`) **no tienen ningún endpoint que las use**, y la clase `RequireAdmin` no se usa en ningún controlador. La UI no ofrece esas acciones, pero el vocabulario ya las promete.

---

## 2. Cobertura de rutas

Rutas verificadas por listado de `frontend/src/app/**/*.tsx` + `route.ts`.

| # | Ruta | Tipo | Red | Scope |
|---|---|---|---|---|
| 1 | `/administracion` | página | ✅ `GET /auth/me`, `GET /administracion/resumen` | admin |
| 2 | `/administracion/inscripciones` | página | ✅ `GET /administracion/inscripciones`, `GET /administracion/catalogos` | admin |
| 3 | `/administracion/inscripciones/[id]` | página dinámica | ✅ `GET /administracion/inscripciones/{id}` | admin |
| 4 | `/administracion/pagos` | página | ✅ `GET /administracion/pagos`, `GET /administracion/pagos/{id}` | admin |
| 5 | `/administracion/equipos` | página | ✅ `GET /administracion/equipos`, `GET /administracion/catalogos` | admin |
| 6 | `/administracion/participantes` | página (2 pestañas) | ✅ `GET /administracion/participantes`, `GET /administracion/participaciones`, `GET /administracion/catalogos` | admin |
| 7 | `/administracion/acreditaciones` | página (2 pestañas) | ✅ `GET /administracion/acreditaciones`, `GET /administracion/acreditaciones/{id}`, `GET /administracion/accesos`, `GET /administracion/catalogos` | admin |
| 8 | `/administracion/usuarios` | página | ✅ `GET /administracion/usuarios`, `GET /administracion/usuarios/{id}` | admin |
| 9 | `/administracion/competencias` | página | ✅ `GET /administracion/competencias`, `GET /administracion/catalogos` | admin |
| 10 | `/administracion/competencias/agenda` | página | ✅ `GET /administracion/competencias/agenda`, `GET /administracion/catalogos` | admin |
| 11 | `/administracion/competencias/cuadro` | página | ✅ `GET /administracion/competencias` (selector), `GET /administracion/competencias/{id}/cuadro` | admin |
| 12 | `/administracion/competencias/[id]` | página dinámica | ✅ `GET /administracion/competencias/{id}` + comandos de escritura | admin |
| 13 | `/dashboard` | página | ✅ `GET /inscripciones/` | responsable de equipo |
| 14 | `/dashboard/inscripcion/[id]` | página dinámica | ✅ `GET /inscripciones/{id}/detalle`, `GET /inscripciones/{id}/pool`, `GET /inscripciones/{id}/saldo`, `GET /inscripciones/{id}/equipos/{equipoId}/elegibles` | responsable de equipo |
| 15 | `/inscripcion` | página | ✅ `GET /catalogo/{paquetes,disciplinas,categorias,promociones}/`, `GET /catalogo/paquetes/{id}/`, `POST /cotizaciones/`, `POST /inscripciones/completa/` | responsable de equipo |
| 16 | `/pases` | página | ✅ `GET /pases/`, `POST /pases/comprar`, `GET /pases/compras/{id}`, `GET /pases/compras/{id}/beneficiarios`, `POST /pases/compras/{id}/beneficiarios`, `DELETE /pases/compras/{id}/beneficiarios/{personaId}`, `GET /personas/resolver` | comprador de pases |

**Route handlers (Next.js), fuera de `app/**/page.tsx` pero parte del mismo flujo operativo:**

| Handler | Método | Propósito | Llamada al backend |
|---|---|---|---|
| `/api/auth/refresh` | `POST` | Rota los tokens desde la cookie httpOnly de refresco y reescribe `ACCESS_TOKEN`, `REFRESH_TOKEN` y `EXPIRES_AT` | ✅ `POST {backend}/token/refresh` (interno, `backendInternalUrl()`) |
| `/api/auth/logout` | `POST` | Borra las cookies de sesión | ❌ ninguna (sólo `clearAuthCookies()`) |

**Páginas en `app/` que quedan fuera de este alcance** (públicas, no operativas): `/` (portada, sin red), `/informacion` (`GET /catalogo/paquetes/` con `fetch` crudo), `/login`, `/register`.

**🟡 Ninguna página enrutable de este documento carece de llamada de red.** La única ruta sin ninguna llamada es `/api/auth/logout`, que es un route handler, no una página. En `/administracion/competencias/cuadro` la llamada al cuadro se **deshabilita** (`enabled: competenciaId.length > 0`) mientras no se elija competencia, pero la página sí llama a `GET /administracion/competencias` para poblar el selector.

---

## 3. La arquitectura de la superficie

### 3.1 Las cinco capas de autorización

| Capa | Archivo | Qué decide | Qué NO decide |
|---|---|---|---|
| 1 · Proxy | `frontend/src/proxy.ts` | Si hay **credencial** (cookie `ACCESS_TOKEN`). Sin token → `redirect("/")`. Rutas públicas: `/`, `/login`, `/register`, `/informacion` | Roles, capacidades, permisos (lo dice explícitamente en su docstring) |
| 2 · Grupo `(app)` | `frontend/src/app/(app)/layout.tsx` | Si hay sesión legible (`getUserSession()`); sin ella → `redirect("/")` | Nada de roles |
| 3 · Área admin | `frontend/src/app/(app)/administracion/layout.tsx` | Revalida contra `GET /api/auth/me` vía `backendInternalUrl()` con `cache: "no-store"`. 4 desenlaces: `unauthenticated`→`/login`, `unavailable`→`/dashboard` (**cierra en falso**), `forbidden`→`AdminAccessDenied`, `admin`→`AdminShell` | Nada de capacidades por sección |
| 4 · Sección | `frontend/src/app/(app)/administracion/*/layout.tsx` → `AdminSeccionGuard` | Si el llamador posee la **capacidad de la sección** (`session.user.capacidades`); si no, `AdminAccessDenied` con mensaje propio | Sigue sin ser la autoridad: el backend reevalúa |
| 5 · Backend | `RequireCapability` / subclases concretas | **La autoridad.** 401 anónimo, 403 no autorizado, 200/201 autorizado | — |

✅ Verificado en `proxy.ts`, `(app)/layout.tsx`, `administracion/layout.tsx`, `AdminSeccionGuard.tsx`, `core/permissions.py`.

**Memoización de la sesión.** `getAdminSession` está envuelto en `cache()` de React (`features/admin/services/admin.session.server.ts`), de modo que el layout del área y el de la sección colapsan en **una sola** petición al backend por render y no pueden discrepar entre sí.

**El cookie `USER_SESSION` nunca es autoridad.** Es escribible por el cliente y no se revalida; el propio código lo declara en `admin.session.server.ts` y `admin.guard.service.ts`. El único indicador que la UI consume es `es_admin`, siempre leído de `GET /api/auth/me`.

### 3.2 El modelo de capacidades

✅ Espejo 1:1 verificado entre `backend/core/capacidades.py` y `frontend/src/features/admin/utils/admin.capacidades.ts`.

| Nivel | `is_staff` | `is_superuser` | Capacidades |
|---|---|---|---|
| `usuario` | no | no | ninguna |
| `staff` | sí | no | `admin.ver`, `admin.inscripciones.escribir`, `admin.equipos.escribir`, `admin.competencias.escribir`, `admin.acreditaciones.escribir`, `admin.pagos.ver`, `admin.usuarios.ver` |
| `superusuario` | sí (implicito) | sí | las 11 completas |

Regla de negocio: `admin = is_staff OR is_superuser`. El superusuario **nunca** es estrechado por el mapa (Django salta cualquier check con `is_superuser=True`).

| Capacidad | Gate backend | Usado por |
|---|---|---|
| `admin.ver` | `RequireAdminVer` | A1, A2, A3, A4, A7, A8, A9, A10, A11, A12, `/administracion/health` |
| `admin.pagos.ver` | `RequirePagosVer` | A5, A6, `/administracion/pases/*` |
| `admin.pagos.aprobar` | `RequirePagosAprobar` | aprobar-manual, anular-manual, cancelar compra de pases (**break-glass**) |
| `admin.usuarios.ver` | `RequireUsuariosVer` | A13, A14 |
| `admin.competencias.escribir` | `RequireCompetenciasEscribir` | todas las rutas de `/administracion/competencias*` (lectura **y** escritura) |
| 🔴 `admin.inscripciones.escribir` | `RequireInscripcionesEscribir` | **ninguna** |
| 🔴 `admin.equipos.escribir` | `RequireEquiposEscribir` | **ninguna** |
| 🔴 `admin.acreditaciones.escribir` | `RequireAcreditacionesEscribir` | **ninguna** |
| 🔴 `admin.usuarios.gestionar` | `RequireUsuariosGestionar` | **ninguna** |
| 🔴 `admin.usuarios.promover_superusuario` | `RequirePromoverSuperusuario` | **ninguna** |
| 🔴 `admin.configuracion.gestionar` | — (sin clase) | **ninguna** |
| 🔴 `RequireAdmin` (clase) | `core/permissions.py` | **ningún controlador** (sólo la definición) |

### 3.3 El contrato de paginación, búsqueda y orden (canónico)

✅ `backend/modules/administracion/domain/services/core/admin_paginacion_service.py` ↔ `frontend/src/features/admin/utils/admin.lista.utils.ts`.

| Parámetro | Default | Regla | Verificación |
|---|---|---|---|
| `page` | 1 | base 1; valores < 1 se ajustan a 1 | ambos lados |
| `page_size` | 25 | tope 100; **exceso se recorta, no es error** | ambos lados |
| `q` | — | texto libre sobre los campos documentados del recurso; se normaliza y se recorta a 120 caracteres | ambos lados |
| `ordering` | por recurso | **lista blanca servidor**; formato `campo` / `-campo`; un campo desconocido → 422 `INVALID_REQUEST` | ambos lados |

Forma canónica de la respuesta paginada (`backend/core/pagination.py::PaginatedData`, espejada en `features/admin/schemas/admin.paginacion.schema.ts`):

```json
{ "success": true, "data": { "items": [], "total": 0, "page": 1, "page_size": 25, "total_pages": 1 }, "error": null, "message": null }
```

✅ El área admin **no** reutiliza el tercer shape incompatible `shared/types/api.types.ts::PaginatedResponse`.

**Lista blanca de orden (backend `ORDERING_*` ↔ frontend `ORDEN_*` en `admin.orden.utils.ts`):** inscripciones `created_at|estado|responsable|paquete`; pagos `created_at|total|cantidad|estado_compra|estado_orden|pagada_en`; equipos `created_at|nombre|disciplina|estado`; participantes `created_at|persona|estado`; participaciones `created_at|persona|equipo|disciplina|rol|estado`; acreditaciones `persona|estado|autorizacion_fiesta`; accesos `fecha_hora|resultado|punto_acceso`; usuarios `created_at|username|nombres|last_login`.

### 3.4 El patrón de lista operativa (compartido por 6 páginas)

`features/admin/components/AdminListaOperativa.tsx` es el shell de las seis tablas del área que lo usan (`inscripciones`, `equipos`, `participantes` —2 pestañas—, `acreditaciones` —2 pestañas—, `pagos` y `usuarios`). Las páginas de **competencias** usan en cambio `AppDataTable` (`components-app/tables`), un componente heredado con otro contrato.

- **Estados obligatorios**: carga (skeleton de 6 filas), error (inline + botón «Reintentar»), vacío (sin datos) y vacío-filtrado (con acción «Limpiar filtros»). El error **nunca** es sólo un toast.
- **Tabla o tarjetas**: se decide por el **número de columnas** (`ADMIN_COLUMNAS_MINIMO_PARA_TABLA = 5`). Con ≥ 5 columnas la tabla sólo aparece desde `xl`; por debajo, la misma lista se renderiza como tarjetas. Con < 5 columnas la tabla aparece desde `md`.
- **Toolbar**: búsqueda libre con *debounce* de 400 ms, selector de orden (sólo campos públicos de la lista blanca) y filtros de recurso. Por debajo de 768 px los filtros de recurso **no se montan**: viven dentro de un `Sheet` inferior (`AdminFiltrosSheet`) con contador de filtros activos. La rama se decide en JavaScript (`useIsMobileState`), no con clases CSS.
- **Paginación**: `components/genericPagination/Pagination.tsx`, alimentada por `page`/`page_size` del estado de la URL.
- **Propiedad de la URL**: filtros, orden, paginación y drilldown abierto viven en el *query string*. Dos páginas con dos listas usan **namespaces** de prefijo (`participantes_`, `participaciones_`, `acreditaciones_`, `accesos_`) para que el filtro de una pestaña nunca llegue al endpoint de la otra.
- **Deriva de clave**: la clave de la query de TanStack incluye el estado completo, de modo que dos combinaciones de filtros nunca comparten caché.

### 3.5 El vocabulario de estados (espejo cliente)

✅ `features/admin/utils/admin.estado.utils.ts`. Un estado desconocido se renderiza **neutro** (`slate`) conservando su valor crudo: la UI nunca inventa una semántica.

| Estado | Etiqueta | Origen |
|---|---|---|
| `LISTO` | Listo para equipo | `EstadoPoolChoices` (derivado) |
| `ESPERANDO_PAGO` | Esperando pago | idem |
| `SIN_CAPACIDAD` | Sin capacidad pagada | idem |
| `CUPO_POR_ASIGNAR` | Cupo por asignar | idem |
| `CON_CUPOS` / `AL_LIMITE` | Con cupos / Al límite | `EstadoCapacidadEquipoChoices` (veredicto de capacidad) |
| `COMPLETO` / `INCOMPLETO` | Completo / Incompleto | completitud de plantilla (derivada) |
| `AUTOMATICA` / `AUTORIZADA` / `BLOQUEADA` | Automática / Autorizada / Bloqueada | override de fiesta |
| `PERMITIDO` / `DENEGADO` | Permitido / Denegado | resultado de acceso |
| `INICIAL` / `AMPLIACION` / `PASE` | Inicial / Ampliación / Pase de fiesta | tipo de compra |
| `IZIPAY` / `MANUAL` / `SIN_PAGO` | (evidencia) | origen del pago; `SIN_PAGO` = «Sin evidencia» |

---

## 4. Catálogo de páginas

### 4.1 `/administracion` — Resumen operativo

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion` (`app/(app)/administracion/page.tsx`) |
| **Propósito** | Vista panorámica del evento activo: 9 bloques de métricas + listas de atención |
| **Rol / guard** | Layout del área (revalidación contra backend) + `RequireAdminVer` en A1/A2 |
| **Componentes** | `AdminOverview` → `AdminPageHeader` (hero), `AdminKpiCard` × 8–9, `AdminAlertList` × N |
| **Datos** | `useAdminResumen()` → `admin.resumen.service` → `GET /api/administracion/resumen` |
| **Auxiliar** | `useAdminCatalogos()` → `GET /api/administracion/catalogos` (no se usa en el resumen; lo usan las tablas) |
| **Backend** | `AdminResumenController.resumen` → `AdminResumenOrchestrator.obtener_resumen` → `AdminConsultaService.construir_resumen` → `AdminResumenSelector` + `ControlAccesoSelector` → `AdminResumenPresenter.present_resumen` |

**Secciones visibles**

1. **Hero del evento** — nombre, badge «Evento activo/inactivo», rango de fechas, `fecha_limite_modificacion` y badge **Editable / Cerrada** (`evento.puede_modificar`, calculado por `Evento.puede_modificar()`).
2. **Rejilla de KPIs** — tarjetas clicables (enlace a la sección correspondiente). Bloques: inscripciones, pagos, cupos, **pases**, equipos, participantes, acreditaciones, accesos.
3. **«Requiere atención»** — listas de alerta. Cada ítem con ruta es un **enlace a la lista ya filtrada**; los ítems sin filtro expresable quedan como texto plano (nunca un enlace que prometa un filtro inexistente).

**Respuesta (`AdminResumenOut`) — 9 bloques**

| Bloque | Campos |
|---|---|
| `evento` | `id`, `nombre`, `fecha_inicio`, `fecha_fin`, `esta_activo`, `fecha_limite_modificacion`, `puede_modificar` |
| `inscripciones` | `total`, `por_estado` (mapa con el vocabulario **completo**, estados sin filas a 0), `creadas_ultimos_7_dias` |
| `pagos` | `compras_total`, `compras_pagadas`, `compras_pendientes`, `compras_canceladas`, `monto_pagado`, `monto_pendiente`, `ordenes_vencidas`, `compras_pagadas_sin_liquidar` |
| `cupos` | `contratado`, `pagado`, `asignado_activo`, `disponible_pagado`, `inscripciones_con_capacidad_exhaustada` |
| `pases` | `pases_vendidos`, `pases_pagados`, `monto_pases_pagado`, `beneficiarios_activos` |
| `equipos` | `total`, `completos`, `incompletos`, `por_disciplina[]` (`disciplina_id`, `sigla`, `nombre`, `total`) |
| `participantes` | `personas_distintas`, `participaciones_activas`, `en_pool`, `sin_cupo_activo` |
| `acreditaciones` | `total`, `por_estado`, `con_acceso_fiesta`, `bloqueadas_por_admin` |
| `accesos` | `permitidos`, `denegados`, `ultimo_acceso` |

**Acciones del usuario** → resultado

| Acción | Resultado |
|---|---|
| Clic en un KPI con ruta | Navega a la sección filtrada correspondiente |
| Clic en un ítem de alerta con ruta | Navega a la lista ya filtrada |
| «Reintentar» (estado de error) | `refetch()` de la query del resumen |

**Estados de UI**: carga → `AdminOverviewSkeleton` (8 tiles + 2 grupos); error → `AdminErrorState` con «Reintentar»; 403 → `AdminAccessDenied`; sin payload → `RichEmptyState` con «Reintentar»; sin alertas → panel verde «Sin pendientes operativos».

**Dependencias**: la separación `pases` vs `cupos` es deliberada — el ingreso de los pases **no** contamina las métricas deportivas. `personas_distintas` ≠ `participaciones_activas` por diseño.

**🟡 Sin efectos laterales**: es lectura pura. `GET /administracion/health` existe en backend (`AdminFundacionController`) pero **ninguna página lo consume**.

---

### 4.2 `/administracion/inscripciones` — Tabla de registros (A3)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/inscripciones` |
| **Propósito** | Listado paginado de las inscripciones del evento activo con sus agregados operativos |
| **Rol / guard** | `AdminSeccionGuard seccionId="inscripciones"` (requiere `admin.ver`) + `RequireAdminVer` en A3 |
| **Componente** | `AdminInscripcionesLista` |
| **Datos** | `useAdminInscripciones(estado)` → `admin.inscripcion.service` → `GET /api/administracion/inscripciones` |
| **Catálogos** | `useAdminCatalogos()` → `GET /api/administracion/catalogos` |

**Columnas (9)** — `Responsable` (nombre + documento), `Paquete` (paquete + promoción), `Estado` (badge), `Equipos` (`completos/total`), `Personas`, `Participaciones`, `Cupos pagados` (`pagados/contratados`), `Monto pagado`, `Creada`.

> Las columnas `Personas` y `Participaciones` son **números distintos por diseño** y la tabla los muestra por separado: un cupo pagado habilita a una persona en **todas** las disciplinas contratadas.

**Filtros**: `estado` (vocabulario `EstadoInscripcionChoices`), `paquete_id`, `promocion_id` — todos desde `AdminCatalogosOut.estados.inscripcion` / `.paquetes` / `.promociones`.
**Orden**: `created_at`, `estado`, `responsable`, `paquete` (por defecto `-created_at`).
**Búsqueda**: `q` sobre responsable y paquete (documentado en el controlador).

**Acciones del usuario** → resultado

| Acción | Resultado |
|---|---|
| Escribir en «Buscar» | Tras 400 ms escribe `q` en la URL y vuelve a la página 1 |
| Elegir un filtro de recurso | Escribe el filtro en la URL, vuelve a la página 1, refetch |
| Cambiar el orden | Escribe `ordering`, vuelve a la página 1, refetch |
| Clic en la fila | `router.push(/administracion/inscripciones/{id})` |
| «Limpiar filtros» | Borra `q` y los filtros; **conserva** el `page_size` |
| Cambiar página / tamaño | Escribe en la URL, refetch |

**Backend**: `AdminInscripcionController.listar_inscripciones` → `AdminOperacionOrchestrator.listar_inscripciones` → `AdminOperacionService.listar_inscripciones` (valida filtros contra el vocabulario → 422 `INVALID_REQUEST` si el valor es inválido) → `AdminInscripcionSelector.listar` → `AdminInscripcionPresenter.present_listado` → `success_response`.

**Modelos/tablas**: `inscripciones` (join con `usuarios_persona`, `paquetes`, `promociones`), `equipos`, `participaciones`, `inscripciones_personas`, `asignaciones_cupo`, `commerce_compra`, `pagos_ordenpago`.
**Efectos laterales**: ninguno (lectura pura).

**🟡 Brecha**: el backend acepta además el filtro `responsable_persona_id` (`AdminInscripcionController`, validado como UUID), pero **la UI no lo expone**. Es un filtro backend sin control en la interfaz.

---

### 4.3 `/administracion/inscripciones/[id]` — Detalle de un registro (A4)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/inscripciones/[id]` (dinámica; `params` es una `Promise` en Next 16) |
| **Propósito** | Drilldown de una inscripción con 6 bloques: equipos, participantes, compras, asignaciones, aceptaciones y saldo |
| **Rol / guard** | Layout de sección + `RequireAdminVer` en A4 |
| **Componente** | `AdminInscripcionDetalle` |
| **Datos** | `useAdminInscripcionDetalle(id)` → `GET /api/administracion/inscripciones/{id}` |

**Cabecera**: evento, responsable (nombre + documento), paquete, promoción, badge de estado, `delegado_nombre`, `fecha_limite_modificacion` y `observacion` (caja ámbar si existe).

**Pestañas y su contenido**

| Pestaña | Contenido | Columnas |
|---|---|---|
| Equipos | Una tarjeta por equipo: disciplina, categoría, `inscripcion_ref`, `jugadores_registrados` / `minimo_deportivo` / `maximo_deportivo`, badge de **capacidad** (`CON_CUPOS`/`AL_LIMITE`), badge de **completitud**; debajo, la tabla de roster | Persona (nombre + documento), Rol, Talla, Estado |
| Participantes | Tabla de personas registradas | Persona, Estado del cupo (badge + `motivo_bloqueo`), Disciplinas |
| Compras | Tabla de compras de la inscripción | Tipo, Cantidad, Total, Compra (badge), Orden (badge) |
| Asignaciones | Tabla de asignaciones de cupo | Persona, Estado (badge), Motivo, Liberada |
| Aceptaciones | Tabla de aceptaciones legales | Aceptación (tipo), Versión, Medio, Aceptado |
| Saldo | 4 tarjetas numéricas | `contratados`, `pagados`, `asignados_pagados`, `disponibles_pagados` |

**Acciones del usuario** → resultado

| Acción | Resultado |
|---|---|
| Clic en «Volver a las inscripciones» | `Link` a `/administracion/inscripciones` |
| Cambio de pestaña | Cambio local de `Tabs` (no cambia la URL) |
| «Reintentar» | `refetch()` del detalle |

**Backend**: `AdminInscripcionController.obtener_inscripcion` → `AdminOperacionOrchestrator.obtener_inscripcion_detalle` → `AdminOperacionService.obtener_inscripcion_detalle` (compone el bloque de compras con `AdminPagoSelector.listar_compras_de_inscripcion` y el de participantes con `AdminParticipanteSelector.listar_por_inscripcion` sobre el resultado de `AdminInscripcionSelector.obtener_detalle`) → `AdminInscripcionPresenter.present_detalle`.

**Contrato de error**: un id desconocido **y** un id de otra edición se responden igual → 404 `RESOURCE_NOT_FOUND`. La superficie nunca confirma la existencia de un recurso fuera de su alcance.

**Efectos laterales**: ninguno. **La página es de solo lectura**: no valida, no rechaza, no libera cupos, no reasigna.

**🟡** Los datos del detalle los recomputa el backend (`inscripcion_selector.obtener_detalle` + `model_copy(update=...)`), no el cliente. La UI no recalcula ningún contador.

---

### 4.4 `/administracion/pagos` — Compras y órdenes de pago (A5/A6)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/pagos` |
| **Propósito** | Tabla de compras del evento con **veredicto operativo** del pago, drilldown de la orden y 3 acciones sensibles |
| **Rol / guard** | `AdminSeccionGuard seccionId="pagos"` (sección visible con `admin.pagos.ver`) + `RequirePagosVer` en A5/A6 y `RequirePagosAprobar` en las escrituras |
| **Componentes** | `AdminPagosLista`, `AdminPagoManualDialog`, `AdminPaseCancelarDialog` |
| **Datos** | `useAdminPagos(estado)` → `GET /api/administracion/pagos`; `useAdminPagoDetalle(id)` → `GET /api/administracion/pagos/{orden_pago_id}` |

**Columnas (10)** — `N° orden`, `Responsable`, `Tipo` (badge INICIAL/AMPLIACION/PASE), `Producto`, `Derechos de pase` (sólo si `tipo === "PASE"`), `Cantidad`, `Total`, `Estado del pago` (badge del **veredicto** `estado_operativo` + línea secundaria «Evidencia: …»), `Pagada el`, `Creada`.

> La tabla muestra **un solo estado por fila**: el veredicto del operador. Los tres hechos que lo componen (estado de compra, estado de orden, fecha de pago) se quedan en el drilldown como rastro de auditoría. El cliente **nunca** recalcula el veredicto.

**Filtros**: `estado_compra`, `estado_orden`, `tipo`, `desde`/`hasta` (rango de fechas ISO `YYYY-MM-DD`).

**🔴 Brecha**: el backend acepta y valida el filtro `estado_operativo` (vocabulario `EstadoOperativoPago`) y es **precisamente el filtro más útil** para el operador (la tabla muestra ese campo), pero **la UI no lo expone**. La lista obliga a filtrar por los hechos en lugar de por el veredicto.

**Drilldown (panel lateral derecho, estado en la URL `?detalle={orden_pago_id}`)**

| Bloque | Contenido |
|---|---|
| Veredicto | Badge `estado_operativo` + nota `estadoOperativoPagoAviso(...)` cuando el código nombra una discrepancia |
| Datos | N° orden, Responsable, Tipo, Producto, Total, Creada |
| Evidencia y estados | Estado de la compra, Estado de la orden, Evidencia (`origen_pago`), Fecha de pago |
| Intentos de pago | Tabla (desktop) / lista (móvil): Estado, Monto, Método, Código, Fecha |
| Aprobaciones manuales | Lista por estado, canal, referencia, actor, fecha y motivo; si fue anulada, quién, cuándo y por qué |
| Derechos de pase | Sólo si `tipo === "PASE"`: slot + estado por beneficiario + contadores activos/revocados |
| Acciones | «Registrar el pago manual», «Anular la aprobación», «Cancelar la compra de pases» |

**Acciones del usuario** → resultado de negocio

| Acción | Payload | Resultado |
|---|---|---|
| «Registrar el pago manual» | `POST /api/administracion/pagos/{id}/aprobar-manual` con `{canal, referencia, monto, moneda, motivo}` | `AprobarPagoManualFlujo`: registra la **evidencia** antes de la liquidación comercial; el monto y la moneda deben coincidir **exactamente** con la orden (409 `MONTO_NO_COINCIDE`); idempotente; **no crea transacción del proveedor** |
| «Anular la aprobación» | `POST /api/administracion/pagos/{id}/anular-manual` con `{motivo}` | `CancelarCompraFlujo._anular_pago_manual`: actualiza atómicamente aprobación + orden + compra, y **revoca sólo los derechos financiados** por esa compra (asignaciones de cupo y beneficiarios). No es reembolso monetario |
| «Cancelar la compra de pases» | `POST /api/administracion/pases/compras/{compra_id}/cancelar` con `{motivo}` | Cancela compra y orden, revoca permanentemente los derechos nominativos y recalcula el acceso efectivo de cada persona afectada |

**Visibilidad de las acciones sensibles**: los tres botones sólo se renderizan si `useAdminTieneCapacidad("admin.pagos.aprobar")` — es decir, **sólo el nivel break-glass**. El staff ve la lista pero no los botones; el backend respondería 403 de todos modos (doble barrera).

**Inválidación tras escritura** (`useAdminPagosComandos.ts`): `["admin","pagos"]` (prefijo, todas las variantes), `["admin","pago",{id}]` (exacto) y `["admin","resumen"]` (exacto, los totales pagados se movieron).

**Contrato de datos**: el wrapper **no modela** `metadata`, `token_sesion`, `response_message` ni `transaction_id` — no están declarados en el Zod, luego no se pueden renderizar. El `codigo_qr` tampoco aparece en ninguna respuesta de esta página.

**Estados de UI**: carga (skeleton), error + «Reintentar», vacío y vacío-filtrado; el drilldown tiene sus propios estados (skeleton 4 filas, error + reintento, «Orden no encontrada»).

**Modelos/tablas**: `commerce_compra`, `salesianos_fest_compra_inscripcion`, `pagos_ordenpago`, `pagos_transaccionpago`, aprobaciones manuales de pago, `asignaciones_cupo`, beneficiarios de pase.

---

### 4.5 `/administracion/equipos` — Equipos y capacidad de plantilla (A7)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/equipos` |
| **Propósito** | Tabla de plantillas del evento con su disciplina, categoría, completitud y **veredicto de capacidad** |
| **Rol / guard** | `AdminSeccionGuard seccionId="equipos"` + `RequireAdminVer` en A7 |
| **Componente** | `AdminEquiposLista` |
| **Datos** | `useAdminEquipos(estado)` → `GET /api/administracion/equipos` |

**Columnas (9)** — `Equipo`, `Disciplina` (sigla + nombre), `Categoría`, `Inscripción` (ref + estado), `Plantilla` (`N jugadores` + `mín X · máx Y`), `Capacidad` (badge `CON_CUPOS`/`AL_LIMITE`), `Completitud` (badge `COMPLETO`/`INCOMPLETO`), `Estado` (badge del equipo), `Creada`.

> `minimo_deportivo` y `maximo_deportivo` son **dos hechos**, no los extremos de una fracción: el mínimo es lo que el equipo necesita para competir y el máximo es el tope duro de la disciplina. La capacidad y la completitud las **deriva el servidor**; el cliente no compara `jugadores_registrados` con ningún umbral.

**Filtros**: `disciplina_id`, `estado`, `roster` (COMPLETO/INCOMPLETO). **Orden**: `created_at`, `nombre`, `disciplina`, `estado`.

**Acciones del usuario** → resultado
- Búsqueda, filtros, orden, paginación, «Limpiar filtros»: idénticos al patrón común (§3.4).
- La fila **no** es clicable: `AdminEquiposLista` **no** pasa `onAbrir` a `AdminListaOperativa`, por lo que la tarjeta móvil se renderiza como `<article>` (no un `<button>`). **No hay drilldown de equipo en la UI**, aunque el backend tiene `AdminEquipoDetalleSchema` (`participaciones[]`) declarado en el Zod. 🔴 El wrapper del detalle existe pero **no hay endpoint ni página que lo usen**.

**🟡 Brecha**: el backend acepta el filtro `inscripcion_id` y el Zod declara `AdminEquipoDetalle`; ninguno de los dos tiene presencia en la interfaz.

---

### 4.6 `/administracion/participantes` — Personas y participaciones (A8/A9)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/participantes` |
| **Propósito** | Dos superficies distintas en dos pestañas: **personas registradas** (el pool) y **filas de roster** |
| **Rol / guard** | `AdminSeccionGuard seccionId="participantes"` + `RequireAdminVer` en A8 y A9 |
| **Componente** | `AdminParticipantesLista` → `PanelParticipantes` + `PanelParticipaciones` |

**Pestaña 1 — Personas registradas (A8)**, namespace de URL `participantes_`

| Columna | Contenido |
|---|---|
| Persona | Nombre + documento |
| Vínculo | `estado` de la persona (`A` Activo / `R` Retirado) |
| Estado del cupo | Badge del veredicto de pool (`LISTO`, `ESPERANDO_PAGO`, `SIN_CAPACIDAD`, `CUPO_POR_ASIGNAR`) + `motivo_bloqueo` |
| Disciplinas | Lista de disciplinas (join del servidor) |
| Registrada | Fecha |

**Filtros**: `estado_pool`, `disciplina_id`, `con_cupo` (true/false).

**Pestaña 2 — Participaciones por disciplina (A9)**, namespace `participaciones_`

| Columna | Contenido |
|---|---|
| Persona | Nombre + documento |
| Equipo | Nombre del equipo |
| Disciplina | Sigla |
| Rol | `J` Jugador / `C` Capitán / `D` Delegado |
| Talla | `talla_camiseta` |
| Fila de roster | `A` Activa / `R` Retirada |
| Creada | Fecha |

**Filtros**: `disciplina_id`, `rol`, `estado`.

**Acciones del usuario** → resultado
- Cambio de pestaña: escribe/borra `?tab=participaciones` (o `participaciones`) conservando el resto de parámetros.
- El resto: patrón común.

**🟡 Nota de diseño (no brecha)**: las dos listas **nunca** se reconcilian en el navegador. Un cupo pagado habilita en varias disciplinas, luego «personas» y «participaciones» son magnitudes distintas por construcción.

**🟡 Brecha**: el backend acepta `inscripcion_id` en A9 y la UI no lo expone.

---

### 4.7 `/administracion/acreditaciones` — Acreditaciones y bitácora de accesos (A10/A11/A12)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/acreditaciones` |
| **Propósito** | Estado de acreditación de las personas del evento y bitácora de los accesos registrados por los lectores |
| **Rol / guard** | `AdminSeccionGuard seccionId="acreditaciones"` + `RequireAdminVer` en A10, A11 y A12 |
| **Componente** | `AdminAcreditacionesLista` → `PanelAcreditaciones` + `PanelAccesos` |

**Pestaña 1 — Acreditaciones (A10)**, namespace `acreditaciones_`

| Columna | Contenido |
|---|---|
| Persona | Nombre + documento |
| Estado | Badge (`PENDIENTE`/`ACTIVA`/`SUSPENDIDA`/`REVOCADA`) |
| Acceso fiesta | Sí/No |
| Autorización | Badge (`AUTOMATICA`/`AUTORIZADA`/`BLOQUEADA`) |
| Habilitado | Override del administrador (`—`/Sí/No) |
| Accesos permitidos | Contador |
| Último acceso | Fecha |

**Filtros**: `estado`, `autorizacion_fiesta`, `acceso_fiesta` (true/false).

**Drilldown (panel lateral, `?acreditaciones_detalle={id}`)**: 8 bloques (Persona, Documento, Estado, Autorización de fiesta, Acceso a la fiesta, Acceso a box, Habilitado por el administrador, Accesos permitidos), la `observacion` si existe, y la tabla de accesos (**Resultado**, **Punto**, **Operador**, **Fecha**).

**Pestaña 2 — Registro de accesos (A12)**, namespace `accesos_`

| Columna | Contenido |
|---|---|
| Persona | Nombre + documento |
| Resultado | Badge (`PERMITIDO`/`DENEGADO`) |
| Punto de acceso | Texto o `—` |
| Operador | Nombre o `—` |
| Fecha y hora | Fecha |

**Filtros**: `resultado`, `punto_acceso` (desde `AdminCatalogosOut.puntos_acceso`), `desde`/`hasta`.

**🔴 Seguridad verificada**: el `codigo_qr` **no está declarado** en ningún esquema Zod de esta página (`admin.acreditacion.schema.ts` lo documenta explícitamente). El QR vivo es una credencial bearer y sólo se entrega por la acción explícita de generación del módulo propietario. En esta página **no existe ninguna acción de override**: la UI es de lectura.

**Efectos laterales**: ninguno.

**🟡 Brecha menor**: `AdminAcreditacionListItemSchema` declara `acceso_box` (nullable) y el drilldown lo muestra, pero **la lista no lo muestra** y **no hay filtro por box**.

---

### 4.8 `/administracion/usuarios` — Cuentas (A13/A14)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/usuarios` |
| **Propósito** | Tabla de cuentas registradas con su rol en el evento y su drilldown |
| **Rol / guard** | `AdminSeccionGuard seccionId="usuarios"` (requiere `admin.usuarios.ver`) + `RequireUsuariosVer` en A13/A14 |
| **Componente** | `AdminUsuariosLista` |
| **Datos** | `useAdminUsuarios(estado)` → `GET /api/administracion/usuarios`; `useAdminUsuarioDetalle(id)` → `GET /api/administracion/usuarios/{id}` |

**Columnas (8)** — `Usuario`, `Nombre`, `Correo`, `Documento`, `Nivel` (badge: Superusuario/Staff/Participante), `Estado` (Activo/Inactivo), `Último acceso`, `Creado`.

**Filtros**: `estado` (activo/inactivo), `es_admin` (true/false). **Orden**: `created_at`, `username`, `nombres`, `last_login`.

**Drilldown (panel lateral, `?detalle={id}`)**: 10 bloques de identidad (Usuario, Nombre, Correo, Documento, Nivel, Staff, Superusuario, Estado, Último acceso, Creado) + tabla de **inscripciones del evento** (Estado, Creada).

**🔴 Observación de diseño, documentada**: el campo del detalle que contiene las inscripciones se llama `personas[]` en el contrato (`AdminUsuarioDetailSchema.personas`), aunque semánticamente son inscripciones. Es una nomenclatura heredada del backend arrastrada al Zod.

**🔴 Límite explícito de la superficie**: la sección **no** gestiona cuentas. No promueve, no degrada, no activa ni desactiva, no reinicia contraseñas. El tier break-glass **se publica** (`is_staff`, `is_superuser`, `nivel`) para que un administrador de cuentas vea quién lo tiene, pero `admin.usuarios.gestionar` y `admin.usuarios.promover_superusuario` **no tienen endpoint**.

**Efectos laterales**: ninguno.

---

### 4.9 `/administracion/competencias` — Lista de competencias

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/competencias` |
| **Propósito** | Listado de las competencias del evento con sus contadores de equipos y encuentros |
| **Rol / guard** | `AdminSeccionGuard seccionId="competencias"` + `RequireCompetenciasEscribir` (**la lectura también exige la capacidad de escritura**) |
| **Componente** | `CompetenciasLista` (usa `AppDataTable` de `components-app/tables`, no `AdminListaOperativa`) |
| **Datos** | `useCompetenciasLista(filtros)` → `GET /api/administracion/competencias` |

**Columnas (5)** — `Competencia` (nombre + fecha), `Estado` (badge), `Equipos` (total), `Encuentros` (total + finalizados), `Acciones` (enlace «Detalle» + enlace al cuadro).

**Filtros**: `disciplina_id`, `categoria_id`, `estado`, `fecha_desde`/`fecha_hasta`.
**Subnavegación**: `CompetenciasSubnav` (Lista · Agenda · Cuadro).

**Acciones**: «Detalle» → `/administracion/competencias/{id}`; «Cuadro» → `/administracion/competencias/cuadro?id={id}`.

**Backend**: `AdminCompetenciasController.listar_competencias` → `CompetenciaLecturaOrchestrator.listar_competencias` → `CompetenciasPresenter.present_listado`. Vive en **`modules/competencias`**, no en `modules/administracion`.

**🔴 Observación**: la lista de competencias **no está paginada** (`ApiResponse[list[CompetenciaListOut]]`) y la UI lo refleja con `showPagination={false}`. Es la única lista del área sin paginación — decisión consciente (el cuadro completo debe ser visible), pero rompe la homogeneidad del contrato.

**🔴 Brecha**: el backend acepta el filtro `evento_id`; la UI no lo envía nunca (el backend resuelve el evento por su cuenta).

---

### 4.10 `/administracion/competencias/agenda` — Agenda de un día

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/competencias/agenda` |
| **Propósito** | Agenda **temporal**: los encuentros programados de un día, agrupados por franja |
| **Rol / guard** | Igual que la lista (sección + `RequireCompetenciasEscribir`) |
| **Componente** | `CompetenciasAgenda` |
| **Datos** | `useAgendaCompetencias(filtros)` → `GET /api/administracion/competencias/agenda` |

**Filtros**: `fecha` (día, `YYYY-MM-DD`), `disciplina_id`, `categoria_id`, `estado` (estado del **encuentro**).

**Render**: franjas temporales; en cada encuentro: competencia, participantes (`A vs B` o «Por definir»), badge de estado, horario, duración en minutos, marca «Bye» y marcador si lo hay.

**Contrato**: un día sin encuentros es una **agenda vacía**, nunca un error. Si el cliente no indica día, el backend resuelve el día actual y lo devuelve en la respuesta (`datos.fecha`).

**Efectos laterales**: ninguno (lectura pura). No hay reordenamiento ni edición desde la agenda.

---

### 4.11 `/administracion/competencias/cuadro` — Cuadro de una competencia

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/competencias/cuadro` (la competencia viaja en `?id=`) |
| **Propósito** | Cuadro (bracket) en rejilla: una columna por ronda, una celda por encuentro |
| **Rol / guard** | Igual que la lista |
| **Componente** | `CompetenciasCuadro` → `CeldaCuadro` + `CompetenciasAccionesEncuentro` |
| **Datos** | `useCompetenciasLista({})` (selector) + `useCompetenciaCuadro(id)` → `GET /api/administracion/competencias/{id}/cuadro` |

**Celda de encuentro**: ronda/orden, marca «Bye», los dos participantes (el ganador en peso tipográfico mayor), marcador, badge de estado, horario si lo hay, y el bloque de **acciones del encuentro** (programación, bye, enlace/desenlace, resultado, avance y corrección).

**Acciones del usuario** → endpoints

| Acción | Endpoint | Efecto |
|---|---|---|
| Elegir competencia | — | Escribe `?id=` en la URL (no es una llamada) |
| Programar horario | `PATCH /administracion/competencias/encuentros/{id}/programacion` | Fija inicio/fin; el horario siempre comparte la fecha de la competencia; un equipo no puede jugar dos encuentros a la vez (409 `EQUIPO_SOLAPADO`) |
| Configurar bye manual | `POST .../encuentros/{id}/bye` | Bye **manual**: exactamente un participante, sin horario ni score, final. El sistema nunca elige un bye |
| Enlazar al siguiente | `POST .../encuentros/{id}/enlace` | El enlace y su slot destino se escriben juntos y **siempre hacia adelante** (ronda posterior): no se pueden crear ciclos (422 `INVALID_LINK`) |
| Desenlazar | `POST .../encuentros/{id}/desenlace` | Exige motivo auditado; una propagación ya aplicada no puede quedar huérfana (409 `INVALID_STATE_TRANSITION`) |
| Registrar resultado | `POST .../encuentros/{id}/resultado` | Ganador **autoritativo** y obligatorio (422 `INVALID_WINNER`); los puntajes son informativos y no determinan ni contradicen al ganador |
| Previsualizar avance | `POST .../encuentros/{id}/avance/preview` | **Nunca escribe**: propone la propagación |
| Confirmar avance | `POST .../encuentros/{id}/avance/confirm` | Coloca al ganador en el slot enlazado; 409 `DESTINO_BLOQUEADO` / `SLOT_OCUPADO` |
| Previsualizar corrección | `POST .../encuentros/{id}/correccion/preview` | **Nunca escribe**: analiza el impacto sobre los descendientes |
| Confirmar corrección | `POST .../encuentros/{id}/correccion/confirm` | Exige `override=true` **y** `acepta_impacto=true` **y** motivo si un descendiente ya empezó/terminó: nunca hay cascada silenciosa |

**Inválidación**: cada mutación invalida el detalle y el cuadro **exactos** de la competencia y, por prefijo, la lista y la agenda.

**🟡 Brecha**: `useCompetenciasLista({})` del selector **ignora cualquier filtro**; el selector del cuadro ofrece todas las competencias, aunque la lista filtrada offería un subconjunto. Además, con `?id=` ausente la query del cuadro queda `enabled: false` (sin petición) y el componente muestra el bloque «Todavía no hay un cuadro seleccionado».

---

### 4.12 `/administracion/competencias/[id]` — Detalle y administración del cuadro

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/administracion/competencias/[id]` |
| **Propósito** | Detalle de una competencia (equipos y rondas) + panel de administración del cuadro |
| **Rol / guard** | Igual que la lista |
| **Componente** | `CompetenciasDetalle` → `CompetenciasEditores` |
| **Datos** | `useCompetenciaDetalle(id)` → `GET /api/administracion/competencias/{id}` |

**Secciones**: cabecera con nombre, fecha, contadores y badge de estado; lista de **equipos** (orden manual + estado); lista de **rondas** (etiqueta, nº de encuentros, estado); enlace «Volver a las competencias»; y el panel **«Administrar la competencia»**.

**Editores (uno abierto a la vez, por legibilidad)**

| Editor | Endpoint | Notas |
|---|---|---|
| Alta de equipo | `POST /administracion/competencias/{id}/equipos` | El equipo debe estar activo y ser del mismo evento/disciplina/categoría (409 `EQUIPO_NO_ELEGIBLE`). El **orden es manual**, nunca sembrado por el sistema |
| Edición de equipo | `PATCH .../equipos/{equipoId}` | Orden y estado de la participación |
| Alta de ronda | `POST .../rondas` | Etiqueta y orden únicos dentro del cuadro (409 `COMPETENCIA_DUPLICADA`) |
| Edición de ronda | `PATCH .../rondas/{rondaId}` | Etiqueta, orden y motivo |
| Alta de encuentro | `POST .../encuentros` | Los dos participantes son **opcionales a propósito**: un cuadro vacío o parcial debe ser legible y editable sin inventar participantes |

**Contrato de concurrencia**: toda mutación protegida exige **motivo auditado** y **bloqueo optimista** `expected_version` (el cliente lo toma del `version` que devolvió el servidor, nunca lo escribe el usuario). Un `expected_version` obsoleto → 409 `RESOURCE_CHANGED` y **no se escribe nada**.

**Estados de UI**: carga (skeleton), error con «Reintentar», y estados vacíos explícitos por bloque («Todavía no hay equipos…», «Todavía no hay rondas…»).

**Modelos/tablas**: competencias, rondas, encuentros, participación de equipo en competencia, enlaces entre encuentros, y el rastro de auditoría asociado.

---

### 4.13 `/dashboard` — Panel del responsable de equipo

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/dashboard` (`app/(app)/dashboard/page.tsx`) |
| **Propósito** | Panel del responsable: estado de sus inscripciones, pasos pendientes y acceso al alta |
| **Rol / guard** | Sólo `(app)/layout.tsx` (sesión). **No hay guard de rol ni de capacidad** — cualquier usuario autenticado entra |
| **Datos** | `getMisInscripciones()` → `GET /api/inscripciones/` |
| **Componentes** | `FlowProgress` (4 pasos), `InscripcionCard`, `EmptyState` — **todo definido dentro del propio archivo de página** |

**Secciones**: hero de marca con saludo y CTA «Crear Inscripción»; diagrama «Cómo funciona» de 4 pasos (Crear inscripción → Validar por el Comité → Completar el pago → Inscribir personas) coloreado según el estado de la primera inscripción; y la rejilla de tarjetas «Mis Inscripciones».

**Tarjeta por inscripción**: id corto (`#xxxxxxxx`), fecha de creación, badge de estado (8 estados con su descripción), paquete y promoción, contadores de **equipos** y **jugadores**, y CTA «Continuar».

**Acciones del usuario** → resultado

| Acción | Resultado |
|---|---|
| «Crear Inscripción» / «Crear primera inscripción» | `router.push("/inscripcion")` |
| Clic en una tarjeta | `router.push(/dashboard/inscripcion/{id})` |
| «Ver el festival» | `Link` a `/` |

**Estados de UI**: spinner con «Cargando inscripciones…»; error en caja rosa (sin botón de reintento: 🔴 **no hay acción de reintento**, sólo re-recarga de página); vacío → `EmptyState` con CTA; éxito → rejilla de tarjetas.

**🔴 Desviación arquitectónica verificada**: esta página tiene **499 líneas y contiene lógica de negocio y estado propio** (`useState` + `useEffect` + `fetch` manual), en contra de `contract/next-app-architecture-contract.md` §1 (las páginas componen features) y frente al patrón TanStack Query que usan todas las páginas del área admin. Es la página más grande y menos homogénea del conjunto. Además usa `confirm()` nativo para el borrado en el detalle, no un diálogo de confirmación.

**Dependencias**: `evento.fecha_limite_modificacion` se comunica en el texto del hero («antes del 21 de noviembre») como **texto fijo**, no como dato del evento. 🔴

---

### 4.14 `/dashboard/inscripcion/[id]` — Detalle operativo de una inscripción (participante/equipo/capacidad)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/dashboard/inscripcion/[id]` |
| **Propósito** | Panel operativo del responsable: equipos, roster, **pool de personas**, elegibilidad, saldo de cupos y pago |
| **Rol / guard** | `(app)/layout.tsx` + propiedad de la inscripción en el backend (ownership) |
| **Componente** | `InscripcionDetailView` (+ `EquipoCard`, `PoolParticipantesSeccion`, `ResumenPagoCard`, `EstadoProgresoCard`, `PaymentCallout`, `DatosInscripcionCard`) |
| **Datos** | `useInscripcionDetalle(id)`, `useInscripcionPool(id)`, `useInscripcionSaldo(id)`, `useElegiblesEquipos(id, equipoIds)` |

**Secciones**: barra superior con «Volver»; `InscripcionHero`; columna principal con `EstadoProgresoCard` (badge + significado + barra de progreso + checklist), `PaymentCallout` (acción de pago), sección **Pool de participantes** y sección **Equipos**; columna lateral con `ResumenPagoCard` (agregado comercial) y `DatosInscripcionCard`.

**Acciones del usuario** → endpoint → resultado de negocio

| Acción | Endpoint | Resultado |
|---|---|---|
| Agregar persona al pool | `POST /inscripciones/{id}/personas` | Crea **sólo** el `InscripcionPersona` (sin equipo). El backend aplica su propio gate de capacidad contratada (`CUPO_CONTRATADO_EXCEDIDO`) y su deadline |
| «Agregarme al pool» | idem (con `persona_id` del responsable) | Auto-preregistro del responsable; el botón **desaparece** si ya está en el pool (control muerto por diseño, no por descuido) |
| Asignar persona a un equipo | `POST /inscripciones/{id}/pool/asignar` | El backend crea la `Participacion` y aplica **todos** los gates (cupo, R11, plantilla, deadline) en una transacción |
| Editar participante | `PATCH /participaciones/{id}` | Actualiza rol, talla, aseguradora y notas |
| Retirar participante | `PATCH /participaciones/{id}/retirar` | `estado = "R"` (retiro lógico, no borrado físico) |
| Pagar | `IzipayModal` → proveedor | Refresca el estado de la compra tras el pago |
| Consultar elegibles | `GET /inscripciones/{id}/equipos/{equipoId}/elegibles` | Lista de candidatos **con veredicto del backend** (`asignable`, `motivo_no_asignable`, `ya_en_disciplina`) |

**Reglas de capacidad y asignación**
- El **pool** es la única fuente de elegibilidad: `estado_pool` ∈ {`LISTO`, `ESPERANDO_PAGO`, `SIN_CAPACIDAD`, `CUPO_POR_ASIGNAR`} + `motivo_bloqueo`.
- El **saldo** (`GET /inscripciones/{id}/saldo`) es la fuente de verdad de la capacidad pagada: `contratados`, `pagados`, `asignados_pagados`, `disponibles_pagados`.
- La lista de **elegibles** por equipo añade `disciplinas_asignadas[]` y `ya_en_disciplina` (R11: nunca dos participaciones activas en la misma disciplina).
- El cliente **nunca** deriva elegibilidad: la renderiza.

**Estados de UI**: carga (`InscripcionSkeleton`); error (`InscripcionErrorState` **con** botón de reintento); vacío por sección (`EquiposEmptyState`, pool vacío, sin compras); éxito.

**Efectos laterales**: alta de `InscripcionPersona`, alta de `Participacion`, edición/retiro de participación, aceptaciones legales creadas atómicamente con la preregistración.

**🟡 Nota**: el borrado de participante usa `confirm()` nativo (`InscripcionDetailView.handleRemoveParticipante`) y hace **actualización optimista de caché** con rollback por invalidación. El proyecto ya dispone de `components/confirmationDialog/` y no se usa aquí.

---

### 4.15 `/inscripcion` — Asistente de inscripción (paquete → equipos → declaraciones)

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/inscripcion` |
| **Propósito** | Alta atómica de inscripción + compra + equipos mediante un asistente de 3 pasos |
| **Rol / guard** | `(app)/layout.tsx` |
| **Componentes** | `InscripcionClientShell` (decoración GSAP) → `InscripcionWizard` → `SmartPaqueteCardsField`, `SmartEquipoField`, `StepDeclarations` |
| **Datos** | `usePaquetes`, `usePromociones`, `useCotizacion`, `useCreateInscripcionCompleta` |

**Pasos**: 1 · Paquete → 2 · Equipos y promoción → 3 · Declaraciones.

**Endpoints**

| Endpoint | Uso |
|---|---|
| `GET /catalogo/paquetes/` | Paquetes disponibles (con `precio_promocional`/`precio_regular` normalizados y `cantidad_minima_compra`) |
| `GET /catalogo/paquetes/{id}/` | Detalle del paquete: disciplinas con `min_jugadores`/`max_jugadores` |
| `GET /catalogo/disciplinas/` | Disciplinas (modalidad, min/max, activa) |
| `GET /catalogo/categorias/` | Categorías con rango de años (`anio_minimo`/`anio_maximo`) |
| `GET /catalogo/promociones/` | Promociones (año, nombre, activa) |
| `POST /cotizaciones/` | Cotización precio × cantidad |
| `POST /inscripciones/completa/` | Alta atómica: inscripción + compra + equipos |

**Payload de `POST /inscripciones/completa/`**

```json
{
  "evento_id": "...", "paquete_id": "...", "promocion_id": "...",
  "fusion_promocion_id": null, "delegado_id": null,
  "cantidad": 2,
  "equipos": [{ "disciplina_id": "...", "categoria_id": null, "nombre": "..." }],
  "estado": "BORRADOR", "observacion": "",
  "precio_unitario_cotizado": 120.0, "cotizacion_version": null
}
```

**Respuesta**: `{inscripcion_id, inscripcion_estado, compra_id, orden_pago_id, compra_estado, cantidad, precio_unitario, total, equipos[]}`.

**Resultado de negocio**: la inscripción nace `BORRADOR` con su compra `PENDIENTE` y su orden de pago; el redirect es a `/dashboard/inscripcion/{inscripcion_id}`.

**Control de precio**: el backend **revalida** el precio cotizado. Si cambió, responde con el código `PRECIO_CAMBIO` y el frontend muestra un toast con el nuevo total (8 s) pidiendo recalcular la cotización. 🟡

**🟡 Desviación verificada**: `cotizacion_version` viaja como **metadato que el backend aún no valida** (lo dice el propio comentario del tipo en `inscripcion.service.ts`: *"metadata, not validated server-side yet"*). Enviar una versión de cotización obsoleta no protege al cliente.

**🟡 Las declaraciones (consentimientos) son estado LOCAL del formulario** y no forman parte del payload: los aceptamientos legales se registran **por persona** vía `POST /inscripciones/{id}/personas`. El asistente valida manualmente que estén marcadas antes de enviar.

**Efectos laterales**: creación de inscripción, compra, orden de pago y equipos en una sola operación de negocio.

---

### 4.16 `/pases` — Compra de pases de fiesta

| Aspecto | Detalle |
|---|---|
| **Ruta** | `/pases` |
| **Propósito** | Compra de un lote de pases de fiesta y asignación nominativa de sus derechos |
| **Rol / guard** | `(app)/layout.tsx`; la compra es del usuario y los endpoints son *owner-scoped* |
| **Componente** | `PaseCompraView` + `PaseCatalogoCard`, `PaseCantidadPanel`, `PaseCompraResultado`, `PaseBeneficiariosPanel`, `PaseLookupPersonaField`, `PaseRevocarDialog`, `PaseQrHint` + `IzipayModal` |

**Endpoints**

| Endpoint | Uso | Nota |
|---|---|---|
| `GET /pases/` | Catálogo público de pases | Catálogo vacío si el rollout está apagado o no hay pase activo |
| `POST /pases/comprar` | Compra del lote | El cuerpo lleva **sólo** `pase_id` y `cantidad`: el precio y el total los congela el servidor |
| `GET /pases/compras/{id}` | Estado de la compra | Sólo el comprador (`Compra.responsable`) |
| `GET /pases/compras/{id}/beneficiarios` | Derechos del lote | Sólo el comprador |
| `POST /pases/compras/{id}/beneficiarios` | Asignar personas a slots libres | La compra debe estar **pagada**; los slots son inmutables y un slot revocado no se restaura |
| `DELETE /pases/compras/{id}/beneficiarios/{personaId}` | Revocar un derecho | Motivo obligatorio y auditado; **no es una transferencia**: el slot se consume para siempre |
| `GET /personas/resolver` | Resolver una persona existente | La API **nunca** crea una persona a partir de texto libre |

**Acciones del usuario** → resultado

| Acción | Resultado |
|---|---|
| Elegir un pase del catálogo | Fija `pase_id` y reinicia `cantidad` a 1 |
| Ajustar la cantidad | Limita por `paseCantidadLimite(pase)` (máximo por compra) |
| «Continuar al pago» | `POST /pases/comprar` → muestra el resumen (N° orden, precio unitario, total) y abre el modal del proveedor |
| Pago | `IzipayModal` → al volver, `refetch` del estado de la compra (**el navegador nunca decide que una activación se completó**) |
| «Comprar otro pase» | Reinicia el estado local; la compra anterior queda sólo para lectura |
| Asignar beneficiarios | Se muestra el panel sólo cuando `paseCompraPagada(...)` es verdadera |
| Revocar beneficiario | Diálogo con motivo obligatorio → `DELETE` → el derecho se consume definitivamente |

**Estados de UI**: catálogo en carga (3 skeletons), error en caja roja, catálogo vacío (aviso), resultado de la compra, panel de beneficiarios condicionado al pago.

**Dependencias**: el pase es un producto **independiente** de la inscripción deportiva; su revenue se reporta en el bloque `pases` del resumen, separado de `cupos`.

**🟡 Nota**: `PaseQrHint` sugiere el uso del QR, pero el QR vivo no se descarga ni se muestra en esta página; la credencial la emite el módulo de acreditaciones.

---

## 5. Matriz exhaustiva página → acción → endpoint

| Página | Acción del usuario | Método + endpoint | Payload enviado | Campos de respuesta usados | Efecto lateral |
|---|---|---|---|---|---|
| `/administracion` | cargar | `GET /api/auth/me` | — | `es_admin`, `capacidades`, `nivel`, `is_staff`, `is_superuser` | ninguno |
| `/administracion` | cargar | `GET /api/administracion/resumen` | — | los 9 bloques (ver §4.1) | ninguno |
| `/administracion` | clic en KPI con ruta | — (navegación) | — | — | ninguno |
| `/administracion` | «Reintentar» | `GET /api/administracion/resumen` | — | idem | ninguno |
| `/administracion/inscripciones` | cargar | `GET /api/administracion/inscripciones` | `page`, `page_size`, `q?`, `ordering?`, `estado?`, `paquete_id?`, `promocion_id?` | `items[]`, `total`, `page`, `page_size`, `total_pages` | ninguno |
| `/administracion/inscripciones` | cargar filtros | `GET /api/administracion/catalogos` | — | `estados.inscripcion`, `paquetes[]`, `promociones[]`, `disciplinas[]`, `categorias[]`, `puntos_acceso[]` | ninguno |
| `/administracion/inscripciones` | buscar / filtrar / ordenar / paginar | `GET /api/administracion/inscripciones` (variantes de query) | idem | idem | ninguno |
| `/administracion/inscripciones` | clic en fila | — (navegación a `[id]`) | — | — | ninguno |
| `/administracion/inscripciones/[id]` | cargar | `GET /api/administracion/inscripciones/{id}` | — | cabecera + `equipos[]`(+`participaciones[]`), `participantes[]`, `compras[]`, `asignaciones[]`, `aceptaciones[]`, `saldo{}` | ninguno |
| `/administracion/inscripciones/[id]` | «Reintentar» | idem | — | idem | ninguno |
| `/administracion/inscripciones/[id]` | «Volver a las inscripciones» | — (navegación) | — | — | ninguno |
| `/administracion/pagos` | cargar | `GET /api/administracion/pagos` | `page`, `page_size`, `q?`, `ordering?`, `estado_compra?`, `estado_orden?`, `tipo?`, `desde?`, `hasta?` | `items[]` (`compra_id`, `orden_pago_id`, `numero_orden`, `responsable_nombre`, `tipo`, `producto_nombre`, `cantidad`, `total`, `estado_operativo`, `origen_pago`, `pagada_en`, `beneficiarios_activos/revocados`) | ninguno |
| `/administracion/pagos` | abrir drilldown | `GET /api/administracion/pagos/{orden_pago_id}` | — | `+ transacciones[]`, `aprobaciones[]`, `beneficiarios[]`, `monto_orden`, `moneda_orden` | ninguno |
| `/administracion/pagos` | «Registrar el pago manual» | `POST /api/administracion/pagos/{id}/aprobar-manual` | `{canal, referencia, monto, moneda, motivo}` | `resultado`, `settlement_status`, `estado_orden`, `estado_aprobacion`, `actor`, `approved_at` | **evidencia de pago registrada** + liquidación comercial; nunca crea transacción del proveedor |
| `/administracion/pagos` | «Anular la aprobación» | `POST /api/administracion/pagos/{id}/anular-manual` | `{motivo}` | `estado_compra`, `estado_orden`, `asignaciones_revocadas`, `beneficiarios_revocados`, `personas_afectadas`, `anulada_por/en` | **revoca** asignaciones de cupo y derechos financiados por esa compra |
| `/administracion/pagos` | «Cancelar la compra de pases» | `POST /api/administracion/pases/compras/{compra_id}/cancelar` | `{motivo}` | `estado_compra`, `estado_orden`, `ya_cancelada`, `beneficiarios_revocados`, `personas_afectadas` | **cancela** compra y orden; revoca derechos; recalcula el acceso efectivo |
| `/administracion/equipos` | cargar / filtrar / ordenar | `GET /api/administracion/equipos` | `page`, `page_size`, `q?`, `ordering?`, `disciplina_id?`, `estado?`, `roster?` | `items[]` (`nombre`, `disciplina_sigla/nombre`, `categoria_nombre`, `inscripcion_ref`, `inscripcion_estado`, `jugadores_registrados`, `minimo_deportivo`, `maximo_deportivo`, `estado_capacidad`, `estado_roster`) | ninguno |
| `/administracion/equipos` | cargar filtros | `GET /api/administracion/catalogos` | — | `disciplinas[]`, `estados.equipo`, `estados.roster` | ninguno |
| `/administracion/participantes` (tab personas) | cargar / filtrar | `GET /api/administracion/participantes` | `page`, `page_size`, `q?`, `ordering?`, `estado_pool?`, `disciplina_id?`, `con_cupo?` | `items[]` (`persona_nombre/documento`, `estado`, `estado_pool`, `motivo_bloqueo`, `disciplinas[]`) | ninguno |
| `/administracion/participantes` (tab roster) | cargar / filtrar | `GET /api/administracion/participaciones` | `page`, `page_size`, `q?`, `ordering?`, `disciplina_id?`, `rol?`, `estado?` | `items[]` (`persona_nombre/documento`, `equipo_nombre`, `disciplina_sigla`, `rol`, `talla_camiseta`, `estado`) | ninguno |
| `/administracion/participantes` | cambiar de pestaña | — (URL `?tab=`) | — | — | ninguno |
| `/administracion/acreditaciones` (tab acreditaciones) | cargar / filtrar | `GET /api/administracion/acreditaciones` | `page`, `page_size`, `q?`, `ordering?`, `estado?`, `autorizacion_fiesta?`, `acceso_fiesta?` | `items[]` (`persona_nombre/documento`, `estado`, `acceso_fiesta`, `autorizacion_fiesta`, `habilitado`, `accesos_permitidos`, `ultimo_acceso`) | ninguno |
| `/administracion/acreditaciones` | abrir drilldown | `GET /api/administracion/acreditaciones/{id}` | — | `+ accesos[]`, `observacion`, `acceso_box` | ninguno |
| `/administracion/acreditaciones` (tab accesos) | cargar / filtrar | `GET /api/administracion/accesos` | `page`, `page_size`, `q?`, `ordering?`, `resultado?`, `punto_acceso?`, `desde?`, `hasta?` | `items[]` (`persona_nombre/documento`, `resultado`, `punto_acceso`, `operador_nombre`, `fecha_hora`) | ninguno |
| `/administracion/usuarios` | cargar / filtrar | `GET /api/administracion/usuarios` | `page`, `page_size`, `q?`, `ordering?`, `estado?`, `es_admin?` | `items[]` (`username`, `nombres`, `apellidos`, `email`, `persona_documento`, `nivel`, `is_staff`, `is_superuser`, `is_active`, `last_login`) | ninguno |
| `/administracion/usuarios` | abrir drilldown | `GET /api/administracion/usuarios/{id}` | — | `+ personas[]` (inscripciones del evento) | ninguno |
| `/administracion/competencias` | cargar / filtrar | `GET /api/administracion/competencias` | `disciplina_id?`, `categoria_id?`, `estado?`, `fecha_desde?`, `fecha_hasta?` | `items[]` (`nombre`, `fecha`, `estado`, `total_equipos`, `total_encuentros`, `total_encuentros_finalizados`) — **sin paginación** | ninguno |
| `/administracion/competencias` | «Detalle» / «Cuadro» | — (navegación) | — | — | ninguno |
| `/administracion/competencias/agenda` | cargar / filtrar | `GET /api/administracion/competencias/agenda` | `fecha?`, `disciplina_id?`, `categoria_id?`, `estado?` | `fecha`, `total`, `encuentros[]` | ninguno |
| `/administracion/competencias/cuadro` | elegir competencia | `GET /api/administracion/competencias` | `{}` | `items[]` (para el selector) | ninguno |
| `/administracion/competencias/cuadro` | ver el cuadro | `GET /api/administracion/competencias/{id}/cuadro` | — | `nombre`, `fecha`, `total_equipos`, `rondas[]`, `encuentros[]` | ninguno |
| `/administracion/competencias/cuadro` | programar | `PATCH /api/administracion/competencias/encuentros/{id}/programacion` | `{inicio_programado, fin_programado, motivo, expected_version}` | encuentro actualizado | agenda/horario del encuentro |
| `/administracion/competencias/cuadro` | bye manual | `POST .../encuentros/{id}/bye` | `{motivo, expected_version}` | encuentro actualizado | encuentro queda como bye final |
| `/administracion/competencias/cuadro` | enlazar | `POST .../encuentros/{id}/enlace` | `{siguiente_encuentro_id, slot_destino, motivo, expected_version}` | encuentro actualizado | enlace del bracket + slot destino |
| `/administracion/competencias/cuadro` | desenlazar | `POST .../encuentros/{id}/desenlace` | `{motivo, expected_version}` | encuentro actualizado | se elimina el enlace |
| `/administracion/competencias/cuadro` | registrar resultado | `POST .../encuentros/{id}/resultado` | `{ganador_id, puntaje_1?, puntaje_2?, marcador_detalle?, motivo, expected_version}` | encuentro actualizado | ganador autoritativo + auditoría |
| `/administracion/competencias/cuadro` | previsualizar avance | `POST .../encuentros/{id}/avance/preview` | — | propuesta de propagación | **ninguno (no escribe)** |
| `/administracion/competencias/cuadro` | confirmar avance | `POST .../encuentros/{id}/avance/confirm` | `{motivo, expected_version}` | avance aplicado | ganador colocado en el slot enlazado |
| `/administracion/competencias/cuadro` | previsualizar corrección | `POST .../encuentros/{id}/correccion/preview` | `{ganador_id}` | análisis de impacto | **ninguno (no escribe)** |
| `/administracion/competencias/cuadro` | confirmar corrección | `POST .../encuentros/{id}/correccion/confirm` | `{ganador_id, motivo, override, acepta_impacto, expected_version}` | corrección aplicada | reescritura del ganador (con override explícito) |
| `/administracion/competencias/[id]` | alta de equipo | `POST /api/administracion/competencias/{id}/equipos` | `{equipo_id, orden}` | equipo de la competencia | participación creada con orden manual |
| `/administracion/competencias/[id]` | editar equipo | `PATCH .../equipos/{equipoId}` | `{orden, estado, motivo, expected_version}` | equipo actualizado | orden/estado + auditoría |
| `/administracion/competencias/[id]` | alta de ronda | `POST .../rondas` | `{etiqueta, orden}` | ronda creada | ronda creada |
| `/administracion/competencias/[id]` | editar ronda | `PATCH .../rondas/{rondaId}` | `{etiqueta, orden, motivo, expected_version}` | ronda actualizada | ronda actualizada |
| `/administracion/competencias/[id]` | alta de encuentro | `POST .../encuentros` | `{ronda_id, orden, participante_1_id?, participante_2_id?}` | encuentro creado | encuentro creado (participantes opcionales) |
| `/dashboard` | cargar | `GET /api/inscripciones/` | — | `id`, `estado`, `paquete_nombre`, `promocion_nombre`, `cantidad_equipos`, `cantidad_participantes`, `created_at` | ninguno |
| `/dashboard` | «Crear Inscripción» | — (navegación a `/inscripcion`) | — | — | ninguno |
| `/dashboard` | clic en tarjeta | — (navegación a `/dashboard/inscripcion/{id}`) | — | — | ninguno |
| `/dashboard/inscripcion/[id]` | cargar detalle | `GET /api/inscripciones/{id}/detalle` | — | cabecera, `equipos[]`(+`participantes[]`), `personas[]`, `resumen_equipo`, `resumen_pago`, `resumen_participantes` | ninguno |
| `/dashboard/inscripcion/[id]` | cargar pool | `GET /api/inscripciones/{id}/pool` | — | `pool[]` (`tiene_cupo_activo`, `estado_pool`, `motivo_bloqueo`) | ninguno |
| `/dashboard/inscripcion/[id]` | cargar saldo | `GET /api/inscripciones/{id}/saldo` | — | `contratados`, `pagados`, `asignados_pagados`, `disponibles_pagados` | ninguno |
| `/dashboard/inscripcion/[id]` | cargar elegibles | `GET /api/inscripciones/{id}/equipos/{equipoId}/elegibles` | — | `elegibles[]` (`asignable`, `motivo_no_asignable`, `ya_en_disciplina`, `disciplinas_asignadas[]`) | ninguno |
| `/dashboard/inscripcion/[id]` | agregar persona al pool | `POST /api/inscripciones/{id}/personas` | `{persona_id? \| persona_data?, aceptaciones?[]}` | `participante` (`id`, `persona`, `estado`) | **crea** `InscripcionPersona` (+ aceptaciones legales atómicas) |
| `/dashboard/inscripcion/[id]` | «Agregarme al pool» | `POST /api/inscripciones/{id}/personas` | `{persona_id}` | idem | idem |
| `/dashboard/inscripcion/[id]` | asignar a equipo | `POST /api/inscripciones/{id}/pool/asignar` | `{inscripcion_persona_id, equipo_id, rol, talla_camiseta, notas}` | `participante` | **crea** `Participacion` (con gates: cupo, R11, plantilla, deadline) |
| `/dashboard/inscripcion/[id]` | editar participante | `PATCH /api/participaciones/{id}` | `{rol?, talla_camiseta?, aseguradora_*, notas?}` | participante | actualización de la participación |
| `/dashboard/inscripcion/[id]` | retirar participante | `PATCH /api/participaciones/{id}/retirar` | — | `{participante_id}` | `estado = "R"` |
| `/dashboard/inscripcion/[id]` | pagar | modal Izipay → proveedor | — | estado de compra refrescado | liquidación del pago |
| `/inscripcion` | cargar catálogos | `GET /api/catalogo/paquetes/` · `/catalogo/disciplinas/` · `/catalogo/categorias/` · `/catalogo/promociones/` | — | precios, mínimos, disciplinas, categorías, promociones | ninguno |
| `/inscripcion` | detalle de paquete | `GET /api/catalogo/paquetes/{id}/` | — | `disciplinas[]` (`min_jugadores`, `max_jugadores`) | ninguno |
| `/inscripcion` | cotizar | `POST /api/cotizaciones/` | `{paquete_id, cantidad}` | precio unitario y total | ninguno |
| `/inscripcion` | enviar | `POST /api/inscripciones/completa/` | ver §4.15 | `inscripcion_id`, `compra_id`, `orden_pago_id`, `total`, `equipos[]` | **crea** inscripción + compra + orden + equipos |
| `/pases` | catálogo | `GET /api/pases/` | — | `items[]` de pase (id, nombre, precio) | ninguno |
| `/pases` | comprar | `POST /api/pases/comprar` | `{pase_id, cantidad}` | `compra_id`, `orden_pago_id`, `numero_orden`, `total` | **crea** compra + orden de pago |
| `/pases` | estado de la compra | `GET /api/pases/compras/{id}` | — | `estado_compra`, `estado_orden`, `origen_pago`, `beneficiarios_asignados/pendientes` | ninguno |
| `/pases` | listar beneficiarios | `GET /api/pases/compras/{id}/beneficiarios` | — | slots, estado por beneficiario | ninguno |
| `/pases` | asignar beneficiarios | `POST /api/pases/compras/{id}/beneficiarios` | `{beneficiario_ids[]}` | derechos asignados | **crea** derechos nominativos (requiere compra pagada) |
| `/pases` | revocar beneficiario | `DELETE /api/pases/compras/{id}/beneficiarios/{personaId}` | `{motivo}` | derecho revocado | **revoca** el derecho (slot consumido para siempre) |
| `/pases` | resolver persona | `GET /api/personas/resolver` | documento/nombre | persona existente | ninguno |

---

## 6. Cadenas de backend (controlador → orquestación → selector/servicio → presentador)

### 6.1 Superficie `/api/administracion/*` (módulo `modules.administracion`)

```
HTTP  →  Controller (async, thin)  →  Orchestrator (async facade)  →  Service/Selector (sync)  →  Presenter (puro)  →  ApiResponse
```

| Endpoint | Controller | Orquestador | Servicio / selector | Presentador |
|---|---|---|---|---|
| `GET /administracion/resumen` | `AdminResumenController.resumen` | `AdminResumenOrchestrator.obtener_resumen` | `AdminConsultaService.construir_resumen` → `AdminResumenSelector` + `ControlAccesoSelector` | `AdminResumenPresenter.present_resumen` |
| `GET /administracion/catalogos` | `AdminResumenController.catalogos` | `AdminResumenOrchestrator.obtener_catalogos` | `AdminConsultaService.construir_catalogos` → `DisciplinaSelector`, `PromocionSelector`, `CategoriaSelector`, `PaqueteSelector`, `ControlAccesoSelector` | `AdminCatalogosPresenter.present_catalogos` |
| `GET /administracion/inscripciones` | `AdminInscripcionController.listar_inscripciones` | `AdminOperacionOrchestrator.listar_inscripciones` | `AdminOperacionService.listar_inscripciones` → `AdminInscripcionSelector.listar` | `AdminInscripcionPresenter.present_listado` |
| `GET /administracion/inscripciones/{id}` | `AdminInscripcionController.obtener_inscripcion` | `…obtener_inscripcion_detalle` | `AdminOperacionService.obtener_inscripcion_detalle` → `AdminInscripcionSelector.obtener_detalle` + `AdminPagoSelector.listar_compras_de_inscripcion` + `AdminParticipanteSelector.listar_por_inscripcion` | `AdminInscripcionPresenter.present_detalle` |
| `GET /administracion/pagos` | `AdminPagoController.listar_pagos` | `…listar_pagos` | `AdminOperacionService.listar_pagos` → `AdminPagoSelector.listar` | `AdminPagoPresenter.present_listado` |
| `GET /administracion/pagos/{id}` | `AdminPagoController.obtener_pago` | `…obtener_pago_detalle` | `AdminOperacionService.obtener_pago_detalle` → `AdminPagoSelector.obtener_detalle` | `AdminPagoPresenter.present_detalle` |
| `POST /administracion/pagos/{id}/aprobar-manual` | `AdminPagoController.aprobar_pago_manual` | `…aprobar_pago_manual` | **`AprobarPagoManualFlujo`** (módulo `pagos`) | `AdminPagoPresenter.present_aprobar_manual` |
| `POST /administracion/pagos/{id}/anular-manual` | `AdminPagoController.anular_pago_manual` | `…anular_pago_manual` | **`CancelarCompraFlujo._anular_pago_manual`** (módulo `salesianos_fest`) | `AdminPagoPresenter.present_anular_manual` |
| `GET /administracion/equipos` | `AdminOperacionController.listar_equipos` | `…listar_equipos` | `AdminOperacionService.listar_equipos` → `AdminEquipoSelector.listar` | `AdminInscripcionPresenter.present_equipo_listado` |
| `GET /administracion/participantes` | `AdminOperacionController.listar_participantes` | `…listar_participantes` | `AdminOperacionService.listar_participantes` → `AdminParticipanteSelector.listar` | `AdminInscripcionPresenter.present_participante_listado` |
| `GET /administracion/participaciones` | `AdminOperacionController.listar_participaciones` | `…listar_participaciones` | `AdminOperacionService.listar_participaciones` → `AdminParticipanteSelector.listar_participaciones` | `AdminInscripcionPresenter.present_participacion_listado` |
| `GET /administracion/acreditaciones` | `AdminOperacionController.listar_acreditaciones` | `…listar_acreditaciones` | `AdminOperacionService.listar_acreditaciones` → `AdminAcreditacionSelector.listar` | `AdminAcreditacionPresenter.present_listado` |
| `GET /administracion/acreditaciones/{id}` | `AdminOperacionController.obtener_acreditacion` | `…obtener_acreditacion_detalle` | `AdminOperacionService.obtener_acreditacion_detalle` → `AdminAcreditacionSelector.obtener_detalle` | `AdminAcreditacionPresenter.present_detalle` |
| `GET /administracion/accesos` | `AdminOperacionController.listar_accesos` | `…listar_accesos` | `AdminOperacionService.listar_accesos` → `AdminAcreditacionSelector.listar_accesos` | `AdminAcreditacionPresenter.present_listado_accesos` |
| `GET /administracion/usuarios` | `AdminUsuarioController.listar_usuarios` | `…listar_usuarios` | `AdminOperacionService.listar_usuarios` → `AdminUsuarioSelector.listar` | `AdminUsuarioPresenter.present_listado` |
| `GET /administracion/usuarios/{id}` | `AdminUsuarioController.obtener_usuario` | `…obtener_usuario_detalle` | `AdminOperacionService.obtener_usuario_detalle` → `AdminUsuarioSelector.obtener_detalle` | `AdminUsuarioPresenter.present_detalle` |
| `POST /administracion/pases/compras/{id}/cancelar` | `AdminPasesController.cancelar_compra_pase` | `…cancelar_compra_pase` | **`CancelarCompraFlujo._cancelar_compra_pase`** | `AdminPasesPresenter.present_cancelar_compra_pase` |
| `GET /administracion/health` | `AdminFundacionController.health` | `AdminFundacionOrchestrator.obtener_fundacion` | `AdminEventoActivoService.resolver_evento_activo` | `AdminFundacionPresenter.present_fundacion` |

**Reglas transversales verificadas**

- El **evento activo** se resuelve en el servidor (`AdminEventoActivoService`, desde `settings.EVENTO_ACTIVO_NOMBRE`); el cliente **nunca** envía `evento_id` en estas rutas. Sin evento activo → 404 `EVENTO_ACTIVO_NO_ENCONTRADO`.
- Los servicios son **sync por contrato** (`contract/django-app-architecture-contract.md` §4.3): sin `async def`, sin `transaction.atomic`, sin ruta de escritura. El orquestador envuelve las llamadas ORM en `sync_to_async` (nunca `asyncio.to_thread`).
- Los errores de dominio (`InvalidFilterError`, `InvalidOrderingError`, `AdminResourceNotFoundError`) se traducen en códigos públicos estables por los handlers globales de `core/exceptions.py`.
- El módulo `modules.administracion` **no tiene modelos de negocio** (`models.py` es un re-export vacío): no hay tablas propias ni migraciones. Consume selectores de los módulos propietarios.

### 6.2 Superficie `/api/administracion/competencias*` (módulo `modules.competencias`)

| Endpoint | Controller | Orquestador | Presentador |
|---|---|---|---|
| `GET /competencias` | `AdminCompetenciasController.listar_competencias` | `CompetenciaLecturaOrchestrator.listar_competencias` | `CompetenciasPresenter.present_listado` |
| `GET /competencias/agenda` | `AdminCompetenciasController.obtener_agenda` | `CompetenciaLecturaOrchestrator.obtener_agenda` | `present_agenda` |
| `GET /competencias/{id}` | `AdminCompetenciasController.obtener_competencia` | `CompetenciaLecturaOrchestrator.obtener_competencia` | `present_detalle` |
| `GET /competencias/{id}/cuadro` | `AdminCompetenciasController.obtener_cuadro` | `CompetenciaLecturaOrchestrator.obtener_cuadro` | `present_cuadro` |
| `GET /competencias/{id}/equipos` \| `/rondas` \| `/encuentros` | `AdminCompetenciasController.listar_*` | `CompetenciaLecturaOrchestrator.listar_*` | `present_equipos/rondas/encuentros` |
| `POST/PATCH/DELETE /competencias…` | `AdminCompetenciasController` | `CompetenciaOrchestrator`, `CompetenciaEquipoOrchestrator`, `RondaOrchestrator`, `EncuentroOrchestrator` | `present_competencia/equipos/rondas/encuentros` |
| `PATCH/POST /competencias/encuentros/{id}/*` | `AdminEncuentrosController` | `EncuentroOrchestrator`, `ResultadoOrchestrator`, `AvanceOrchestrator`, `CorreccionOrchestrator` | `present_encuentros/resultado/avance/correccion` |

Las mutaciones de encuentros viven en un **controlador separado** (`/administracion/competencias/encuentros`) porque el orden de registro de los controladores importa: el prefijo más largo debe declararse antes (`backend/config/api.py`).

### 6.3 Superficie del responsable (`modules.salesianos_fest`)

Los endpoints que consumen `/dashboard`, `/dashboard/inscripcion/[id]` e `/inscripcion` (`/inscripciones/`, `/inscripciones/completa/`, `/inscripciones/{id}/detalle`, `/inscripciones/{id}/pool`, `/inscripciones/{id}/pool/asignar`, `/inscripciones/{id}/saldo`, `/inscripciones/{id}/personas`, `/inscripciones/{id}/equipos/{equipoId}/elegibles`, `/participaciones/{id}`, `/participaciones/{id}/retirar`) pertenecen al módulo `salesianos_fest` y están fuera de la superficie `/administracion`.

---

## 7. Modelos y tablas afectados por la superficie

| Tabla / modelo | Dónde aparece |
|---|---|
| `eventos` (`Evento`) | Cabecera del resumen; resolución del evento activo; `fecha_limite_modificacion` |
| `usuarios_usuario` (`Usuario`) | Tabla de cuentas; `is_staff`, `is_superuser`, `is_active`, `last_login` |
| `usuarios_persona` (`Persona`) | Nombres y documentos en todas las tablas; `persona_fk` de `Usuario` |
| `inscripciones` (`Inscripcion`) | A3, A4; `estado`, `observacion`, `delegado` |
| `paquetes` / `promociones` (`Paquete`, `Promocion`) | Filtros y columnas de A3; `tipo` de paquete |
| `categorias` (`Categoria`) | Filtro de la lista de competencias; columna de A7 |
| `disciplinas` (`Disciplina`) | Filtros; `sigla`; `min_jugadores`/`max_jugadores` |
| `equipos` (`Equipo`) | A7 y bloque Equipos de A4; `EQUIPO_ACTIVO`/`EQUIPO_CANCELADO` |
| `participaciones` (`Participacion`) | A9 y roster de A4; rol `J/C/D`; R11 |
| `inscripciones_personas` (`InscripcionPersona`) | A8; pool del panel del responsable; `estado` A/R |
| `aceptaciones_inscripcion` (`AceptacionInscripcion`) | Pestaña Aceptaciones de A4 |
| `asignaciones_cupo` (`AsignacionCupo`) | Pestaña Asignaciones de A4; saldo de cupos; `ACTIVA/LIBERADA/REVOCADA` |
| `commerce_compra` (`Compra`) | A5/A6; `PENDIENTE/PAGADA/CANCELADA`; `tipo` |
| `salesianos_fest_compra_inscripcion` (`CompraInscripcion`) | Cantidad de cupos contratados y monto congelado |
| `pagos_ordenpago` (`OrdenPago`) | A5/A6; número, estado, `pagada_en` |
| `pagos_transaccionpago` (`TransaccionPago`) | Intentos de pago del drilldown |
| Aprobaciones manuales de pago | Historial de aprobaciones/anulaciones del drilldown |
| `acreditaciones_evento` (`AcreditacionEvento`) | A10/A11; `autorizacion_fiesta`, `habilitado`, `acceso_fiesta`; `codigo_qr` **fuera de la superficie** |
| `controles_acceso` (`ControlAcceso`) | A12; `resultado`, `punto_acceso`, `operador`, `fecha_hora` |
| Pases: `pase`, compra de pase, beneficiarios | `/pases` y bloque «Derechos de pase» de A6 |
| Competencias, rondas, encuentros, participación de equipo, enlaces | `/administracion/competencias*` |

**Invariante clave que la UI respeta y no recalcula**: la **capacidad pagada** es `CompraInscripcion.cantidad` para compras `PAGADA`; las filas de `AsignacionCupo` son *reclamaciones*, y su número no puede superar esa capacidad. La UI muestra `pagados/contratados` y `disponibles_pagados` **tal como los devuelve el servidor**.

---

## 8. Estados de interfaz (carga, vacío, éxito, error, reintento, navegación)

| Página | Carga | Vacío | Error | Reintento | Navegación |
|---|---|---|---|---|---|
| `/administracion` | skeleton de 8 tiles + 2 grupos | `RichEmptyState` «Sin resumen disponible» | `AdminErrorState` | ✅ botón «Reintentar» | enlaces de KPI y de alerta |
| `/administracion/inscripciones` | skeleton de tabla/tarjetas | «Todavía no hay inscripciones» / «Sin resultados» | inline con mensaje | ✅ | fila → detalle |
| `/administracion/inscripciones/[id]` | skeleton de 8 filas | «Inscripción no encontrada» | inline | ✅ + enlace «Volver» | «Volver a las inscripciones» |
| `/administracion/pagos` | skeleton | «Todavía no hay pagos» / «Sin resultados» | inline | ✅ | fila → drilldown (URL `?detalle=`) |
| `/administracion/equipos` | skeleton | «Todavía no hay equipos» / «Sin resultados» | inline | ✅ | — (fila no clicable) |
| `/administracion/participantes` | skeleton (2 paneles) | «Todavía no hay participantes» / «Todavía no hay participaciones» | inline | ✅ | cambio de pestaña (`?tab=`) |
| `/administracion/acreditaciones` | skeleton | «Todavía no hay acreditaciones» / «Todavía no hay accesos» | inline | ✅ | drilldown (`?acreditaciones_detalle=`) |
| `/administracion/usuarios` | skeleton | «Todavía no hay usuarios» / «Sin resultados» | inline | ✅ | drilldown (`?detalle=`) |
| `/administracion/competencias` | skeleton (`AppDataTable`) | «Todavía no hay competencias» / «Sin resultados» | inline (`AppDataTable`) | ✅ | enlaces Detalle / Cuadro |
| `/administracion/competencias/agenda` | skeleton | «La agenda de este día está vacía» | inline con botón | ✅ | subnav |
| `/administracion/competencias/cuadro` | skeleton | «El cuadro todavía está vacío» / «Todavía no hay un cuadro seleccionado» | inline con botón | ✅ | selector (`?id=`) |
| `/administracion/competencias/[id]` | skeleton | por bloque («Todavía no hay equipos/rondas») | inline con botón | ✅ | enlace «Volver a las competencias» |
| `/dashboard` | spinner + «Cargando inscripciones…» | `EmptyState` con CTA | caja rosa **sin botón** | 🔴 no | a `/inscripcion` y al detalle |
| `/dashboard/inscripcion/[id]` | `InscripcionSkeleton` | por sección | `InscripcionErrorState` | ✅ | «Volver» al panel |
| `/inscripcion` | por paso (queries de catálogo) | catálogos vacíos | mensaje del form | ✅ (el form) | redirect al detalle tras crear |
| `/pases` | 3 skeletons de tarjeta | «Los pases de fiesta todavía no están disponibles» | caja roja | ✅ (refetch del catálogo) | — |

**Regla general verificada**: el fallo **nunca** es sólo un toast; la sección admin usa error inline con reintento. La **excepción** es `/dashboard`, que no ofrece reintento.

---

## 9. Dependencias de negocio: capacidad, propiedad, asignación y acreditación

| Dependencia | Dónde se materializa | Quién es la autoridad |
|---|---|---|
| **Capacidad de cupos** | `cupos` del resumen, columna «Cupos pagados» de A3, pestaña «Saldo» de A4, `disponibles_pagados` del panel del responsable | Backend (`AsignacionCoreService.calcular_saldo_inscripcion`, `CompraInscripcion.cantidad`) |
| **Capacidad de plantilla de equipo** | Columnas «Capacidad» y «Completitud» de A7, badges del bloque Equipos de A4 | Backend (veredicto derivado: `CON_CUPOS`/`AL_LIMITE`, `COMPLETO`/`INCOMPLETO`) |
| **Elegibilidad de asignación** | Selector de participantes, pool del panel del responsable | Backend (`tiene_cupo_activo`, `estado_pool`, `asignable`, `motivo_no_asignable`) |
| **Propiedad (ownership)** | `/dashboard/**`, `/inscripcion/**`, `/pases/**` | Backend (`check_ownership_or_admin` / `Compra.responsable`) |
| **Asignación / R11** | Pool → equipo; `disciplinas_asignadas`, `ya_en_disciplina` | Backend (transacción única con cupo, R11, plantilla y deadline) |
| **Deadline de modificación** | Badge «Editable / Cerrada» del resumen, `fecha_limite_modificacion` en A4 | Backend (`Evento.puede_modificar()`) |
| **Acreditación y override de fiesta** | Columnas «Acceso fiesta» y «Autorización» de A10; badges del drilldown | Backend (`AcreditacionEvento.autorizacion_fiesta`, `habilitado`, `acceso_fiesta`) |
| **Control de acceso** | Pestaña «Registro de accesos» (A12) | Backend (`ControlAcceso.resultado`) |
| **Límites del bracket** | Cuadro y agenda | Backend (orden manual, byes manuales, enlaces hacia adelante, `expected_version`) |
| **Costo de los pases** | Resumen (`pases`) y A5 (`tipo = PASE`) | Backend (precio congelado en la compra) |

**Regla de oro de la superficie**: el frontend **no** recalcula ningún contador, saldo, veredicto ni elegibilidad. Los mappers (`features/admin/utils/admin.estado.utils.ts`, `admin.resumen.utils.ts`, `admin.lista.utils.ts`) sólo **formatean** lo que el servidor devolvió; un valor desconocido se renderiza neutro, nunca interpretado.

---

## 10. Brechas, implementaciones parciales, controles muertos y desajustes

### 🔴 Brechas funcionales

1. **Cinco capacidades declaradas sin ningún endpoint**: `admin.inscripciones.escribir`, `admin.equipos.escribir`, `admin.acreditaciones.escribir`, `admin.usuarios.gestionar` y `admin.usuarios.promover_superusuario` tienen gate en `core/permissions.py` y aparecen en el mapa de capacidades, pero **ningún controlador las usa**. La UI no ofrece esas acciones. El vocabulario promete una superficie de escritura que no existe.
2. **`RequireAdmin` no se usa**: la clase genérica (`es_admin`) está definida pero todos los controladores usan las subclases por capacidad (`RequireAdminVer`, `RequirePagosVer`, …). Queda como código muerto (documentado, no usado).
3. **Filtro `estado_operativo` sin control en la UI** (A5). Es el filtro que mejor corresponde al campo más prominent de la tabla (el veredicto del operador).
4. **Filtros backend sin control en la UI**: `responsable_persona_id` (A3), `inscripcion_id` (A7 y A9), `evento_id` (competencias).
5. **Sin drilldown de equipo**: existe `AdminEquipoDetalleSchema` (con `participaciones[]`) en el Zod, pero **no hay endpoint ni página** que lo usen, y la fila de A7 no es clicable.
6. **El drilldown de competition no expone la escritura**: la edición de encuentros vive en el **cuadro**, no en `/competencias/[id]`; `/competencias/[id]` sólo crea equipos, rondas y encuentros.
7. **Sin acciones de acreditación**: la sección es de lectura. El override de fiesta y la regeneración de QR (acciones sensibles documentadas en el contrato) **no tienen control en la UI**.

### 🟡 Implementaciones parciales

8. **La lista de competencias no está paginada**, a diferencia de las otras nueve. El `AppDataTable` se renderiza con `showPagination={false}`.
9. **El selector del cuadro ignora los filtros**: `useCompetenciasLista({})` pide todas las competencias, aunque la lista filtrada offerería un subconjunto.
10. **`/dashboard` se aparta del patrón del producto**: 499 líneas con `useState`/`useEffect` y `fetch` manual, en lugar de una feature y TanStack Query; usa `confirm()` nativo en vez de un diálogo de confirmación (que el proyecto ya tiene en `components/confirmationDialog/`).
11. **`cotizacion_version` viaja sin validación del servidor**: es metadato que el backend aún no comprueba (`inscripcion.service.ts` lo declara como tal).
12. **Las declaraciones del asistente son estado local** y no forman parte del payload: los aceptamientos legales se registran por persona en otro endpoint.

### 🟡 Controles muertos o potencialmente confusos

13. **El botón «Agregarme al pool» se auto-oculta** si el responsable ya está en el pool (`responsableEnPool`): correcto, pero es un control que desaparece sin explicación visible.
14. **`adminPaseCancelable(estado_compra, estado_orden)`** controla la visibilidad de «Cancelar la compra de pases»; en la UI sólo se evalúa dentro del drilldown de una orden (`pago.tipo === "PASE"`), de modo que **el botón es inalcanzable para compras de pase sin `orden_pago_id`** (fila sin orden → el drilldown no se abre, porque `onAbrir` sólo actúa si `item.orden_pago_id` existe).
15. **`AdminPagosLista` usa una clave compuesta** (`${compra_id}-${created_at}`) para las filas, porque la compra no tiene id de orden en todos los casos: la identidad de la fila no es estable.

### 🟡 Desajustes de documentación interna (código vs comentarios)

16. `features/admin/utils/admin.secciones.ts` y `AdminSeccionNav.tsx` dicen «**siete** secciones» y «siete etiquetas», pero `ADMIN_SECCIONES` declara **ocho** (Resumen, Inscripciones, Pagos, Equipos, Competencias, Participantes, Acreditaciones, Usuarios).
17. `features/admin/competencias/services/competencias.service.ts` documenta las rutas como `RequireAdmin`, cuando el gate real es `RequireCompetenciasEscribir`.
18. `features/admin/schemas/admin.resumen.schema.ts` llama «nueve bloques» al resumen (correcto: 9), mientras la exploración histórica de Engram (`sdd/administracion-operativa-fest/explore`) hablaba de ocho: el bloque `pases` se añadió después.
19. El campo `personas[]` del detalle de usuario **contiene inscripciones**, no personas (`AdminUsuarioDetailSchema`): nomenclatura heredada del backend.

### 🔴 Riesgo de seguridad (recordatorio, ya vigente en el código)

20. La superficie administrativa **no es una frontera de seguridad**: la autorización real son las clases `RequireCapability` del backend, y la UI sólo anticipa. Los endpoints públicos del módulo `salesianos_fest` (`GET /inscripciones/{id}/detalle`, `POST /equipos/`, `PATCH /inscripciones/{id}`, entre otros) siguen siendo la deuda pendiente del *workstream* de hardening, tal como registra `sdd/administracion-operativa-fest/explore`.

---

## 11. Verificación de la cobertura

**Rutas enrutables documentadas: 16/16.** Las 16 páginas de `frontend/src/app` dentro del alcance administrativo/operativo están descritas en §4, con su cadena de backend en §6, sus endpoints en §5 y su modelo de estados en §8.

| Comprobación | Resultado |
|---|---|
| Páginas de `app/**/page.tsx` en el alcance | 16 — todas documentadas |
| Route handlers relacionados | 2 (`/api/auth/refresh`, `/api/auth/logout`) — documentados en §2 |
| Layouts de sección con guard | 7 (`inscripciones`, `pagos`, `equipos`, `participantes`, `acreditaciones`, `usuarios`, `competencias`) |
| Páginas **sin** llamada de red | 0 (la única ruta sin red es `/api/auth/logout`, que no es una página) |
| Endpoints admin referenciados | 15 de lectura (`resumen`, `catalogos`, `inscripciones`×2, `pagos`×2, `equipos`, `participantes`, `participaciones`, `acreditaciones`×2, `accesos`, `usuarios`×2, `health`) + 3 de escritura (`aprobar-manual`, `anular-manual`, `pases/…/cancelar`) |
| Rutas de competencias | 29 en total (7 lecturas + 22 escrituras) en 2 controladores; la UI consume 4 lecturas y 15 comandos |
| Endpoints de competencias (`modules/competencias`) | 2 controladores, 9 orquestadores, 1 presentador |
| Capas de autorización documentadas | 5 (proxy, grupo `(app)`, área admin, sección, backend) |

**Fuentes leídas para esta verificación**: `contract/` (7 archivos), `frontend/src/app/**` (33 archivos), `frontend/src/features/admin/**` (145 archivos), `frontend/src/features/inscripciones/**` (57), `frontend/src/features/pases/**` (38), `frontend/src/proxy.ts`, `frontend/src/components/AppSidebar.tsx`, `backend/core/{capacidades,permissions,pagination,exceptions}.py`, `backend/config/api.py`, `backend/modules/administracion/**` (completo), `backend/modules/competencias/presentation/controllers/**`, y la exploración previa en Engram `sdd/administracion-operativa-fest/explore` (obs #9227) usada **sólo como contexto histórico** y contrastada contra el código actual.

**Contradicción con la exploración previa, resuelta a favor del código**: la exploración `sdd/administracion-operativa-fest/explore` (2026-10-25) afirmaba que «no existe superficie `/administracion`». Hoy **sí existe y está completa**: 13 rutas admin, 17 endpoints de lectura, 3 de escritura y un panel de competencias con 18 rutas. Este documento refleja el código vigente.
