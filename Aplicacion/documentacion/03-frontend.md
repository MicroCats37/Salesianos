# 03 — Frontend

> **Estado:** vigente (documento de referencia del rebuild controlado bajo `Aplicacion/`)
> **Alcance:** frontend Next.js (App Router) — rutas, features, estado, transporte HTTP y calidad
> **Fuente de verdad:** el código. Este documento describe lo que existe hoy, no lo que debería existir
> **Owner:** frontend (la UI no es la autoridad de dominio; el backend lo es)
> **Última verificación:** 2026-11-18 sobre el árbol de trabajo local

## Convenciones de lectura

| Marcador | Significado |
|---|---|
| ✅ | Verificado en código en esta pasada |
| 🟡 | Verificado parcialmente o deducido del código con alta confianza |
| 🔴 | Brecha o incumplimiento verificado, sin resolver |

Los documentos hermanos de esta serie viven en el mismo directorio (`Aplicacion/documentacion/`) y se publican por separado; este documento no resume ni anticipa su contenido. Los contratos normativos se encuentran en [`../../contract/`](../../contract/), y son vinculantes cuando el código y el contrato discrepan: **el código describe la realidad, el contrato describe la obligación**.

Documentos hermanos disponibles en esta serie: [`01-arquitectura-y-runtime.md`](./01-arquitectura-y-runtime.md), [`04-datos-y-dominio.md`](./04-datos-y-dominio.md) y [`05-flujos-end-to-end.md`](./05-flujos-end-to-end.md) (su contenido no se anticipa aquí).

## Documentos de detalle asociados

Este documento describe la **arquitectura** del frontend. Los documentos de detalle amplían cada superficie sin duplicarla aquí:

| Documento de detalle | Qué añade a este documento |
|---|---|
| [03a — Páginas públicas y de compra](./03a-paginas-publicas-y-compra.md) | Ficha por ficha de las 8 páginas públicas, de cuenta y de compra (`/`, `/informacion`, `/login`, `/register`, `/dashboard`, `/dashboard/inscripcion/[id]`, `/inscripcion`, `/pases`) y de los 2 route handlers de sesión: guardas, servicios, payloads, estados y brechas. |
| [03b — Páginas administrativas y operativas](./03b-paginas-administrativas-y-operativas.md) | Ficha por ficha de las 16 páginas administrativas y operativas: capas de autorización, contrato de paginación, vocabulario de estados, matriz página → acción → endpoint y cadenas de backend. |
| [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) | Catálogo ruta por ruta del backend con su permiso efectivo y su wrapper. |
| [02b — Propósito y consumidores de endpoints](./02b-proposito-y-consumidores-de-endpoints.md) | Para cada endpoint: su consumidor real en el frontend, su cadena de ejecución y sus efectos. |
| [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) | Trazabilidad completa desde la pantalla hasta la escritura en base de datos, con los endpoints sin consumidor frontend. |
| [07 — Guía para el agente de UI/UX](./07-guia-para-ui-ux.md) | Qué puede y qué no puede cambiarse en el frontend, y cómo se entrega un cambio. |

---

## 1. Resumen ejecutivo

El frontend es una aplicación Next.js 16 (App Router) con React 19, TypeScript estricto, TanStack Query v5, Zustand v5, React Hook Form y Zod v4. Se organiza en **20 pantallas enrutables y 2 route handlers**, y cada pantalla resuelve contra una feature.

Cuatro conclusiones operativas:

1. ✅ **La arquitectura de rutas y features es sólida y coherente** con `contract/next-app-architecture-contract.md`: `app/` enruta, `features/` contiene la lógica, `components/` la UI reutilizable, `lib/` la infraestructura.
2. ✅ **La cadena de guardas es deliberada y de tres capas**, y su autoridad final es el backend. El frontend nunca decide permisos por sí mismo.
3. 🔴 **Un mismo endpoint de catálogo se consume desde tres clientes distintos**, con tres resoluciones de URL base, dos estrategias de autenticación y dos estilos de validación opuestos. Es la duplicación más costosa del árbol.
4. ✅ **`Aplicacion/frontend/` es una copia byte a byte de `frontend/`** (verificado por SHA-256 en esta pasada): 559/559 archivos de `src/` idénticos, 18/18 archivos de raíz idénticos, 33/33 recursos de `public/` idénticos. El frontend del rebuild está copiado y listo para normalizarse, no para reescribirse.

---

## 2. Estructura real del árbol

```
frontend/src/                       # 559 archivos
├── app/                            # ENRUTADO (31 archivos .tsx = 20 páginas + 11 layouts, + 2 route handlers)
│   ├── layout.tsx, page.tsx        # raíz y portada
│   ├── (public implicit) informacion/page.tsx
│   ├── (auth)/login|register/page.tsx
│   ├── (app)/…                     # grupo con layout de sesión
│   │   ├── dashboard/…
│   │   ├── inscripcion/page.tsx
│   │   ├── pases/page.tsx
│   │   └── administracion/…        # 7 secciones con layout propio
│   └── api/auth/{refresh,logout}/route.ts
│
├── features/                       # LÓGICA DE NEGOCIO (281 archivos)
│   ├── admin/            145       # (+ competencias/ 53, pases/ 14)
│   ├── inscripciones/     57
│   ├── pases/             38
│   ├── auth/              23
│   ├── pagos/             10
│   ├── portada/            6
│   ├── landing/            2
│   └── inscripcion/        0       # 🔴 restos vacíos
│
├── components/                    # UI REUTILIZABLE (13 carpetas)
│   ├── ui/ (shadcn), genericForm/, genericModal/, genericPagination/,
│   ├── genericErrorBoundary/, emptyState/, confirmationDialog/,
│   ├── branding/, breadcrumbs/, event/, landing/, paquetes/, portada/
│   └── AppShell.tsx, AppSidebar.tsx
│
├── components-app/                 # 🔴 18 archivos CAM heredados, EXCLUIDOS de tsconfig
│   └── forms/, tables/, pages/, pdf/, sidebar/
│
├── hooks/                          # infraestructura genérica
│   ├── callsApi/  (useApiQuery, useApiCreate, useApiUpdate, useApiDelete)
│   ├── cache/     (useGeneric{Create,Update,Delete}Mutation, useGenericOptimisticUpdate, useGenericCacheSync)
│   └── system/    (useDebounce, usePagination)
│
├── lib/                            # INFRAESTRUCTURA
│   ├── api.ts, query-client.ts, utils.ts, post-auth-redirect.ts
│   ├── auth/     (actions.ts, cookies.ts, index.ts)
│   ├── server/   (backend-url.ts, jwt.ts)
│   ├── forms/    (buildUpdatePayload.ts, imageField.ts)
│   └── batch/    (buildBatchDiff.ts, types.ts)
│
├── errors/                         # error-handler.ts, toast-adapter.ts, types.ts
├── types/                          # api.types.ts (envoltura + factory Zod)
├── utils/                          # payload-builder.ts, …
├── providers/                      # ReactQueryProvider.tsx
├── proxy.ts                        # primera capa de guardia (cortesía)
│
├── _legacy-app-routes/            # 🔴 20 archivos CAM, fuera de app/ → no enrutados
└── _legacy-features/              # 🔴 49 archivos CAM, DENTRO del grafo de compilación
```

✅ Verificado por recorrido del árbol de trabajo. El recuento por carpeta de `features/` corresponde al número de archivos bajo cada subcarpeta.

**Diferencias estructurales respecto al contrato** (`contract/next-app-architecture-contract.md` §1): el proyecto usa `src/types/` en lugar de `src/shared/{schemas,types,utils}`, y `src/lib/` contiene además `auth/`, `server/`, `forms/` y `batch/`. La realidad es coherente; no es una violación, pero la documentación de referencia debe reflejar la estructura real.

---

## 3. Mapa ruta → guard → feature → servicio → endpoint

✅ Rutas verificadas por listado de `app/**/*.tsx`. Endpoints verificados por lectura de los servicios correspondientes.

| Ruta | Guarda | Feature | Servicio / transporte | Endpoint |
|---|---|---|---|---|
| `/` | — | `portada` (config) | sin red | — |
| `/informacion` | — | `landing` + `components/landing` | `landing/paquetes.service` (**`fetch` crudo**) | `GET /catalogo/paquetes/` |
| `/login` | — | `auth` | `auth/hooks/useLogin` (axios, sin servicio dedicado) | `POST /auth/login` |
| `/register` | — | `auth` | `auth/services/register.service` (axios) | `POST /auth/register` |
| `/dashboard` | `(app)/layout.tsx` | `auth` + `inscripciones` | 🔴 lógica en la página (477 líneas) | `GET /inscripciones/` |
| `/dashboard/inscripcion/[id]` | `(app)/layout.tsx` | `inscripciones` | `useInscripcionDetalle` → `inscripcion.service` | `GET /inscripciones/{id}/detalle` |
| `/inscripcion` | `(app)/layout.tsx` | `inscripciones` (wizard) | `useInscripcionCatalogs`, `useCotizacion`, `useCreateInscripcionCompleta` | `GET /catalogo/{paquetes,disciplinas,categorias,promociones}/`, `GET /catalogo/paquetes/{id}/`, `POST /cotizaciones/`, `POST /inscripciones/completa/` |
| `/pases` | `(app)/layout.tsx` | `pases` | `pase.service`, `pase.beneficiario.service`, `persona.resolucion.service` | `GET /pases/`, `POST /pases/comprar`, `GET /personas/resolver` |
| `/administracion` | `administracion/layout.tsx` | `admin` | `admin.me.service`, `admin.resumen.service` | `GET /auth/me`, `GET /administracion/resumen`, `GET /administracion/catalogos` |
| `/administracion/inscripciones` | `AdminSeccionGuard` | `admin` | `admin.inscripcion.service` | `GET /administracion/inscripciones` |
| `/administracion/inscripciones/[id]` | `AdminSeccionGuard` | `admin` | `admin.inscripcion.service` | `GET /administracion/inscripciones/{id}` |
| `/administracion/equipos` | `AdminSeccionGuard` | `admin` | `admin.operacion.service` | `GET /administracion/equipos` |
| `/administracion/participantes` | `AdminSeccionGuard` | `admin` | `admin.operacion.service` | `GET /administracion/participantes`, `GET /administracion/participaciones` |
| `/administracion/pagos` | `AdminSeccionGuard` | `admin` | `admin.pago.service` | `GET /administracion/pagos`, `GET /administracion/pagos/{id}`, `POST .../aprobar-manual`, `POST .../anular-manual` |
| `/administracion/acreditaciones` | `AdminSeccionGuard` | `admin` | `admin.operacion.service` | `GET /administracion/acreditaciones`, `GET /administracion/acreditaciones/{id}`, `GET /administracion/accesos` |
| `/administracion/usuarios` | `AdminSeccionGuard` | `admin` | `admin.usuario.service` | `GET /administracion/usuarios`, `GET /administracion/usuarios/{id}` |
| `/administracion/competencias` (+ `/agenda`, `/cuadro`, `/[id]`) | `AdminSeccionGuard` | `admin/competencias` | `competencias.service`, `competencias.comandos.service` | `GET/POST/PATCH/DELETE /administracion/competencias*` |
| `/api/auth/refresh` | route handler | `lib/auth`, `lib/server/jwt` | `fetch` servidor → backend | `POST {backend}/token/refresh` |
| `/api/auth/logout` | route handler | `lib/auth` | — | — (solo limpieza de cookie) |

✅ No hay rutas huérfanas: toda pantalla resuelve a una feature.

---

## 4. Cadena de guardas y sesión

✅ Verificado en `src/proxy.ts`, `app/(app)/layout.tsx`, `app/(app)/administracion/layout.tsx`, `app/(app)/administracion/*/layout.tsx` (7 secciones), `features/admin/services/admin.session.server.ts`, `features/admin/components/AdminSeccionGuard.tsx`.

| Capa | Artefacto | Decide | ¿Autoridad? |
|---|---|---|---|
| 1. Edge (cortesía) | `src/proxy.ts` | ¿existe cookie de credencial? Si no → `/` | **No.** La cookie de acceso no es `httpOnly`; el propio archivo lo declara. El `matcher` excluye `api`, `_next/static`, `_next/image`, `images` y `favicon.ico` |
| 2. Área | `app/(app)/layout.tsx` | ¿hay `USER_SESSION`? Si no → `/` | No por sí sola: `USER_SESSION` es una instantánea escribible por el cliente |
| 3. Área administrativa | `app/(app)/administracion/layout.tsx` | `revalidateAdminSession()` → `GET /auth/me` (`cache: "no-store"`) | **Sí, para la experiencia.** Cierra en fallo: `unauthenticated` → `/login`, `unavailable` → `/dashboard`, `forbidden` → `AdminAccessDenied` sin renderizar hijos |
| 4. Sección | `app/(app)/administracion/*/layout.tsx` ×7 | `AdminSeccionGuard seccionId=…` → `getAdminSession()` (React `cache()`, memoizado por petición) | **Sí.** Sin capacidad → `AdminAccessDenied`, los hijos no se renderizan |
| 5. Backend | `RequireAdmin` / `RequireCapability` | Revalidaflags en cada petición → 403 | **El control real** |

Puntos a conservar:

- ✅ `getAdminSession()` usa `cache()` de React: el layout del área y el de la sección **no pueden discrepar** sobre la misma sesión.
- ✅ `features/admin/utils/admin.capacidades.ts` replica 1:1 los 11 códigos de capacidad del backend y documenta de forma explícita que *ocultar un botón no es autorizar*.
- 🔴 `COOKIE_OPTIONS.httpOnly = false` en `lib/auth/cookies.ts` (aplica a las cuatro cookies `cam_auth_*`). El comentario de `app/api/auth/refresh/route.ts` afirma lo contrario ("Set rotated tokens as httpOnly cookies"). El token de acceso es legible por cualquier script del navegador. **Decisión de seguridad, no de refactorización** (ver §11, brecha FE-2).

---

## 5. Convenciones de componentes

✅ Verificado en `components/genericForm/**`, `contract/smart.md`.

| Elemento | Regla vigente |
|---|---|
| `GenericForm.tsx` | Orquestador: `useForm` + `zodResolver`, valores por defecto, normalización del payload, exposición de `methods` |
| `GenericInput.tsx` | Despachador: resuelve el input por `type` y centraliza label, descripción, requerido y **mensajes de error** en `DefaultFieldWrapper` |
| `inputs/registry.ts` | Registro de Smart Fields **genéricos** (16 inputs: texto, número, fecha, select, checkbox, radio, password, moneda, imagen, etc.). Un campo de dominio no se registra aquí: va en `customFields` |
| Patrón Smart Field | Adaptador bidireccional: sin validación propia (la verdad es Zod), sincronización por `useController`, error delegado al wrapper (`hideErrorMessage`) |
| Modos de render | 1 — manual (`children`, **el único permitido en producción**); 2 — automático (`fields`, solo prototipado); 3 — secciones (`formSections`, herramientas internas); 4 — híbrido (`customFields`) |
| `buildApiPayload` | Vive en `utils/payload-builder.ts` y se invoca **dentro del hook de mutación**, nunca en el `onSubmit` del formulario. Detecta `File`, serializa a `FormData` y tokeniza archivos como `file_<uuid>___<nombre>` |

🔴 Los modos 2 y 3 siguen disponibles en producción pese a estar prohibidos por el contrato §5; un agente de UI puede elegir por error la vía no permitida.

✅ En `features/inscripciones/` el patrón Smart Field ya se usa en `components/forms/DocumentoLookupSmartField.tsx` y en `components/smart-fields/{SmartEquipoField,SmartPaqueteCardsField}.tsx`.

---

## 6. Gestión de estado

✅ Verificado en `lib/query-client.ts`, `providers/ReactQueryProvider.tsx`, `features/auth/store/auth.store.ts`, `features/admin/hooks/useAdminListaUrl.ts`.

| Tipo de estado | Dueño | Ubicación | Nota |
|---|---|---|---|
| Datos de servidor (canónico) | TanStack Query v5 | `lib/query-client.ts`: `staleTime` 5 s, `refetchOnWindowFocus: false` | Namespaces: `["admin",…]`, `["inscripcion",…]`, `["pases",…]`, `["landing",…]` |
| Estado de lista (filtros, página, orden, término) | **URL** | `features/admin/hooks/useAdminListaUrl.ts` + `useAdminControlLista.ts` | Todo filtro vive en el *querystring*; cualquier cambio vuelve a la página 1. Es la decisión correcta: la lista es compartible y sobrevive a un refresco |
| Sesión del cliente | Zustand v5 | `features/auth/store/auth.store.ts` | **Único** store Zustand del árbol. `persist` en `localStorage["salesianos-auth-user"]`. **Nunca se usa para autorizar** |
| Datos de inscripción | TanStack Query | `features/inscripciones/hooks/useInscripcion*` | `useInscripcionCacheSync` invalida en bloque las claves de detalle, pool, saldo y elegibles |
| Competencias | TanStack Query | `features/admin/competencias/**` | Espacio de nombres `["admin","competencias",…]`, escrito a mano en dos lugares (utilidad de claves y hook) |

✅ Cumplimiento: Zustand solo para estado de UI (una sola slice); el estado de servidor es siempre TanStack Query.

---

## 7. Transporte HTTP

### 7.1 Cliente canónico

✅ `lib/api.ts` es la instancia única de `axios`:

- `baseURL`: `backendPublicUrl()` en el navegador, `backendInternalUrl()` en el servidor (`lib/server/backend-url.ts`). El comentario del archivo explica por qué el servidor **no** puede usar la URL relativa `/backend`.
- `timeout`: 15 s.
- Interceptor de petición: inyecta `Authorization: Bearer` desde la cookie de acceso.
- Renovación: promesa compartida (`refreshPromise`) para refrescos concurrentes; refresco proactivo cuando el token expira en menos de 5 minutos; ante `401`, refresca y **reintenta una vez** (`_retry`).
- El refresco real ocurre en el route handler `/api/auth/refresh`, que llama a `POST {backend}/token/refresh` y deriva `expires_at` del `exp` real del JWT (`lib/server/jwt.ts`).

### 7.2 Envoltura de respuestas

✅ `types/api.types.ts` define la envoltura y una fábrica de esquemas:

```ts
interface ApiResponse<T> { success: boolean; data: T | null; error?: ApiError; message?: string }
function apiResponseSchema<T>(dataSchema: z.ZodType<T>): ZodType<…>
```

Coincide con la `ApiResponse` del backend (`success_response`). `message` es nullable a propósito: el backend siempre incluye la clave.

### 7.3 Dos estilos de espejo coexistentes (🔴 inconsistentes entre sí)

| Estilo | Dónde | Mecanismo | Comportamiento ante deriva |
|---|---|---|---|
| **A — sobre Zod estricto** | `features/admin/**`, `features/pases/**`, `features/portada/hooks/useCatalogo.ts` | `apiResponseSchema(...)`; el servicio hace `.parse()` del sobre completo; `admin.http.service` lanza `ApiQueryError` ante `ZodError` | **Falla de forma ruidosa**: la deriva rompe la pantalla en vez de pasar desapercibida |
| **B — solo genéricos de TypeScript** | `features/inscripciones/**` (`inscripcion.service`, `catalog.service`, `cotizacion.service`, `pool.service`, `elegibles.service`), `features/pagos/**`, `features/auth/**` | `api.get<ApiResponse<T>>()`: el genérico es una mentira de compilación; nada se valida en ejecución | **Falla de forma silenciosa**: un campo renombrado llega como `undefined` dentro de una tabla |

✅ El estilo A es el patrón de referencia. Debe ser el único estilo tras la normalización.

### 7.4 Duplicación de clientes de catálogo (🔴 hallazgo principal)

✅ Verificado por lectura de los tres clientes y por búsqueda de `await fetch(` en `frontend/src`:

| Endpoint | Cliente 1 | Cliente 2 | Cliente 3 |
|---|---|---|---|
| `GET /catalogo/paquetes/` | `features/inscripciones/services/catalog.service.ts` → `getPaquetes` (axios, interfaz `Paquete` marcada `@deprecated`, *fallback* al campo legacy `cantidad_maxima_participantes`) | `features/inscripciones/services/paquete.service.ts` → `fetchPaqueteList` (axios + Zod; **ante desajuste de Zod registra y devuelve el payload crudo**) | `features/landing/paquetes.service.ts` → `fetchPaquetes` (**`fetch` crudo**, sin autenticación, sin validación, `null` ante cualquier fallo, URL base propia con *hostname* Docker hardcodeado `http://backend:8000/api`) |
| `GET /catalogo/disciplinas/` | `catalog.service.getDisciplinas` (axios, estilo B) | `features/portada/hooks/useCatalogo.ts` (`fetch` crudo + Zod, clave `["landing","disciplinas"]`) | — |
| `GET /catalogo/categorias/` | `catalog.service.getCategorias` (axios, estilo B) | `features/portada/hooks/useCatalogo.ts` (`fetch` crudo + Zod, clave `["landing","categorias"]`) | — |
| `GET /catalogo/promociones/` | `catalog.service.getPromociones` (axios) | — | — |

✅ Consecuencias verificadas:

- **Tres resoluciones de URL base** para el mismo backend: `backendPublicUrl()` / `backendInternalUrl()` (axios), `NEXT_PUBLIC_API_URL ?? http://localhost:8000/api` con *fallback* `http://backend:8000/api` (los clientes con `fetch` crudo).
- **Dos estrategias de autenticación**: la instancia de `axios` inyecta el token; los clientes con `fetch` crudo no lo hacen.
- **Dos estrategias de error**: `ApiQueryError` con estado HTTP frente a `null` silencioso.
- **Dos espacios de nombres de caché** para los mismos datos: `["landing","disciplinas"]` frente a `["inscripcion","disciplinas"]` → **doble descarga, sin caché compartida**.
- 🔴 **Colisión de nombres de hook**: `useDisciplinas` y `useCategorias` existen **en dos features distintas** (`features/portada/hooks/useCatalogo.ts` y `features/inscripciones/hooks/useInscripcionCatalogs.ts`). Quien importe el equivocado obtiene otro transporte y otra clave de caché.

🔴 `features/portada/hooks/useCatalogo.ts` incluye además **contenidos editoriales de respaldo** (`MAPA_DISCIPLINA`, `ORDEN_DISCIPLINAS`, y fallbacks de disciplinas y categorías con identificadores ficticios) que se renderizan cuando la API no responde. La presentación puede-mostrar datos que el backend no devolvió.

---

## 8. Frontera ruta / servicio / API

✅ Verificado en `app/**`, `features/**/services/**`, `hooks/callsApi/**`.

| Capa | Responsabilidad | Regla |
|---|---|---|
| `app/**` | Enrutado, grupos de ruta, `loading`/`error`, metadata, composición de layout | **Sin lógica de negocio y sin fetching de datos.** La única excepción actual es `app/(app)/dashboard/page.tsx` (🔴 477 líneas, `"use client"`, `useState` + `useEffect` para la carga, máquina de estados `ESTADO_META` y 3 componentes en línea) — viola `next-app-architecture-contract.md` §1 y §8 |
| `app/(app)/**/layout.tsx` | Guardia de área/sección | Un layout de sección **no es opcional**: es una capa de autoridad |
| `features/<f>/services/**` | Transporte y forma de la petición | Único lugar donde se conoce la URL del backend. Valida con Zod antes de devolver (estilo A) |
| `features/<f>/hooks/**` | Estado de servidor, claves de caché, invalidación | Un endpoint, un cliente, una clave de caché |
| `features/<f>/schemas/**` | Espejo 1:1 de los *wrappers* del backend | Solo se cambia junto con el backend (🔴 `inscripcion.service.ts` declara ~25 interfaces **dentro del servicio**, contra la convención `features/*/schemas/`) |
| `features/<f>/utils/**` | Mapeo y formato puros | No pueden duplicar una regla de negocio del backend |
| `lib/api.ts`, `lib/auth/**` | Transporte y sesión | **Un solo cliente y un solo dueño de cookies.** No se duplican |
| `types/api.types.ts` | Sobre de respuesta y factory Zod | Contrato compartido |

✅ `useApiQuery` (`hooks/callsApi/useApiQuery.ts`) valida con `schema.parse(data)` y lanza `ApiQueryError`, que **conserva el estado HTTP**: la UI puede distinguir 403 de 503 sin parsear el mensaje.

---

## 9. Paridad entre `frontend/` y `Aplicacion/frontend/`

✅ Verificado en esta pasada con hash SHA-256 archivo por archivo:

| Elemento | `frontend/` | `Aplicacion/frontend/` | Resultado |
|---|---|---|---|
| `src/` | 559 archivos | 559 archivos | **559/559 idénticos, 0 diferentes, 0 faltantes** |
| Archivos de raíz (configuración) | 18 | 18 | **18/18 idénticos** (`package.json`, `tsconfig.json`, `vitest.config.ts`, `vitest.setup.ts`, `biome.json`, `next.config.ts`, `Dockerfile`, `.env.example`, …) |
| `public/` | 33 archivos | 33 archivos | **33/33 idénticos** |
| Estado en git | versionado | **0 archivos versionados** (`git ls-files Aplicacion` → vacío) | ⚠️ la copia es **no versionada** y **no está en `.gitignore`** |

⚠️ **Sobre qué se comparó:** la paridad es contra el **árbol de trabajo**, no contra el último commit. `frontend/` tiene 13 archivos modificados sin commitear y 8 archivos nuevos sin seguimiento (administración, pagos). La copia de `Aplicacion/frontend/` refleja ese estado sin commitear, de modo que arrastra cambios todavía no revisados. Antes de tratar la copia como base estable hay que decidir si se versiona el backend y el frontend juntos o por separado, y con qué línea base.

Consecuencias operativas:

1. ✅ **La mitad frontend del rebuild ya está copiada y no ha derivado.** No hay paso de copia pendiente: hay un paso de **normalización** pendiente.
2. 🔴 **Ese material no es revisable ni reversible** mientras siga fuera de git. Cualquier trabajo sobre `Aplicacion/frontend/` es irrecuperable con `git checkout`.
3. ✅ `Aplicacion/backend/` está en un estado distinto (muchos menos módulos poblados que el backend de la raíz); esta paridad no aplica al backend.
4. 🟡 El índice de CodeGraph reporta distinto número de llamadores de `api` en cada copia (24 frente a 38). Es un efecto de truncamiento del resumen de radio de impacto, no una diferencia real: los archivos son idénticos byte a byte.

---

## 10. Tests y calidad (medido)

✅ Comandos ejecutados en `frontend/` el 2026-11-18:

| Comprobación | Resultado |
|---|---|
| `npx tsc --noEmit` | **Pasa, 0 errores** |
| `npx vitest run` (carrera completa) | **2 archivos fallidos / 4 tests fallidos**, 272–274 aprobados de 276, 33–32 de 34 archivos |
| `npx vitest run` (segunda carrera) | **1 archivo fallido / 2 tests fallidos**, 274 aprobados de 276 |
| `npx vitest run <archivo de competencias>` (aislado) | **8/8 aprobar** |
| `npx biome check .` | **105 errores, 93 avisos** |
| Archivos de prueba en disco | **44**; Vitest ejecuta 34; los otros 10 quedan en el runner de Node |

### 10.1 Los tests rojos

✅ **Fallo estable (1 archivo, 2 tests):** `src/features/admin/schemas/admin.catalogos.schema.test.ts`. La muestra de estados del test no incluye `estado_capacidad_equipo`, vocabulario que el backend añadió a `AdminEstadosCatalogosOut` y que el espejo frontend `AdminEstadosCatalogosSchema` ya exige. **La causa es una deriva real backend → frontend del vocabulario**, no un test mal escrito: el fixture debe viajar con el contrato.

🔴 **Fallo inestable (1 archivo, 2 tests, solo en algunas carreras completas):** `src/features/admin/competencias/components/editors/CompetenciaEncuentroEditors.test.tsx` ("mueve los slots con su motivo y la versión del servidor"). El mismo archivo **pasa 8/8 en ejecución aislada** y pasó en la segunda carrera completa. Es una prueba **dependiente del orden** o con estado compartido: hay que determinarla antes de dar por verde la suite.

### 10.2 Estructura de pruebas

✅ Dos runners conviven:

- **Vitest** (`vitest.config.ts`): `include: ["src/**/*.test.ts", "src/**/*.test.tsx"]`, `environment: "node"` por defecto; las suites de componentes declaran `// @vitest-environment jsdom`.
- **Runner de Node** (`node --experimental-strip-types --test`): 10 suites **excluidas por nombre** dentro de `vitest.config.ts` (5 de administración y `src/features/inscripciones/utils/*.test.ts`). 🔴 Renombrar un archivo de ese conjunto cambia silenciosamente de runner.

✅ Distribución aproximada: `features/admin` 27, `features/pases` 6, `features/inscripciones` 5, `features/pagos` 2, `lib/server` 2, `features/portada` 1, `proxy.test.ts` 1.

✅ Dos patrones de prueba dignos de preservar porque verifican **contratos**, no implementaciones: `admin.catalogos.schema.test.ts` lee el **código fuente** de los componentes en ejecución (`readFileSync`) para comprobar que los filtros ya no literalizan opciones; y las suites `*Comandos.test.tsx` afirman el **conjunto exacto** de claves invalidadas por cada mutación.

---

## 11. Desviaciones respecto a los contratos y brechas verificadas

### 11.1 Matriz de desviaciones

| Regla del contrato | Realidad verificada | Valoración |
|---|---|---|
| §1 `app/` solo enruta | `app/(app)/dashboard/page.tsx` con 477 líneas de lógica de negocio | 🔴 **violación** |
| §8 sin `useEffect` para datos iniciales | `dashboard/page.tsx` usa `useEffect` + `useState` | 🔴 **violación** |
| §1 `src/shared/{schemas,types,utils}` | `src/types/api.types.ts`, sin `src/shared/` | 🟡 disposición distinta, coherente |
| §1 `lib/` = Axios + QueryClient | `lib/` además contiene `auth/`, `server/`, `forms/`, `batch/` | 🟡 coherente, más amplio |
| §2 anatomía de feature (`schemas/ services/ hooks/ utils/ components/`) | `features/landing/paquetes.service.ts` cuelga de la raíz; `features/pagos/` no tiene `hooks/`; `features/portada/` no tiene `schemas/` | 🟡 inconsistente |
| §2 esquema `{Acción}{Recurso}FormSchema` / `*ResponseSchema` | conviven `admin.*.schema.ts`, `inscripcion.schema.ts`, `pase.schema.ts` | 🟡 dos estilos |
| §3 por defecto Server Components | las pantallas de administración e inscripción son *shells* `"use client"` tras un `<Suspense>` | 🟡 pragmático, pero toda la UI es cliente |
| §3 Server Actions para mutaciones | solo `lib/auth/actions.ts` usa `"use server"`; el resto de las mutaciones va por axios | 🟡 la vía del contrato no se usa |
| §4 Zustand solo para estado de UI | un único store | ✅ cumple |
| §5 `buildApiPayload` en el hook de mutación | `utils/payload-builder.ts`, invocado en `useApiCreate` / `useGenericCreateMutation` | ✅ cumple |
| §5 modo 1 manual en producción | los modos 2 y 3 siguen disponibles | ⚠️ riesgo de uso indebido |
| §6 importaciones con nombre | sin `import * as` | ✅ cumple |
| §7 *barrels* granulares | `features/*/index.ts` re-exportan de forma granular | ✅ cumple |
| §8 sin `z.any()` | `api.types.ts` usa `z.record(z.string(), z.any())`; `GenericForm.tsx` usa `any` en 4 puntos | ⚠️ menor (no en espejos de respuesta) |
| §11 forma de `ApiResponse<T>` | `{success, data, error, message}` | ✅ cumple (coincide con el backend) |
| §9 `src/errors/{error-handler,toast-adapter}.ts` | presentes | ✅ cumple |
| §9 `src/utils/payload-builder.ts` | presente | ✅ cumple |

### 11.2 Brechas verificadas

| # | Brecha | Evidencia verificada | Impacto |
|---|---|---|---|
| FE-1 | `Aplicacion/` no está versionada ni ignorada por git | `git ls-files Aplicacion` → 0 archivos; `.gitignore` sin la entrada | El frontend ya copiado es irrecuperable. Decisión de usuario |
| FE-2 | Cookie del token de acceso con `httpOnly: false` | `lib/auth/cookies.ts` (`COOKIE_OPTIONS`) frente al comentario de `app/api/auth/refresh/route.ts` | Superficie de robo de token por XSS. Decisión de seguridad |
| FE-3 | Tres clientes para un mismo endpoint de catálogo | §7.4 | Tres bases URL, dos autenticaciones, dos estilos de validación |
| FE-4 | Dos hooks homónimos (`useDisciplinas`, `useCategorias`) | `features/portada/hooks/useCatalogo.ts` y `features/inscripciones/hooks/useInscripcionCatalogs.ts` | Ambigüedad al importar; caché partida |
| FE-5 | Dos espacios de nombres de caché para el mismo catálogo | `["landing",…]` frente a `["inscripcion",…]` | Doble descarga, sin invalidación cruzada |
| FE-6 | `PersonaResumen` declarado dos veces en el mismo archivo | `features/inscripciones/services/inscripcion.service.ts` líneas 117 y 214 | TypeScript fusiona las declaraciones: el tipo resultante exige campos de ambas formas |
| FE-7 | `components-app/` está en el `exclude` de `tsconfig.json` pero es una dependencia viva | Importadores: `features/admin/competencias/components/CompetenciasLista.tsx`, `features/admin/components/AdminOverview.tsx`, `features/inscripciones/components/{AddParticipanteModal,EditParticipanteModal,SelectorParticipanteModal}.tsx` | La exclusión es ficticia; además `components-app/sidebar/ProtectedSidebar.tsx` enlaza rutas CAM (`/liquidaciones/*`) que ya no existen |
| FE-8 | 49 archivos CAM dentro del grafo de compilación | `src/_legacy-features/**` no está en el `exclude` | 49 archivos muertos en cada typecheck, con riesgo de reutilización accidental |
| FE-9 | `dashboard/page.tsx` rompe la regla de "enrutado únicamente" | 477 líneas, `"use client"`, `ESTADO_META`, 3 componentes en línea | Pantalla más difícil de rediseñar; es el punto de entrada de la UI de usuario |
| FE-10 | Deriva de vocabulario backend → frontend | Test rojo de `admin.catalogos.schema.test.ts` (`estado_capacidad_equipo`) | La suite está roja por diseño de contrato: el fixture quedó desactualizado |
| FE-11 | Prueba dependiente del orden | `CompetenciaEncuentroEditors.test.tsx` falla en algunas carreras completas y pasa aislada | No se puede declarar la suite verde sin determinarla |
| FE-12 | Parser Django/422 documentado pero no implementado | `errors/error-handler.ts` describe el formato `detail: [{loc,msg}]` pero la cadena solo contiene `genericRestParser` | Los errores de campo se aplanan en un único mensaje y no se aplican a los campos del formulario vía `setError` |
| FE-13 | Mensajes de reserva en inglés frente a un backend en español | `errors/error-handler.ts` (`DEFAULT_MESSAGES`) | El usuario ve mensajes del backend en español y reservas de red en inglés |
| FE-14 | 105 errores y 93 avisos de Biome | `npx biome check .` | Línea base roja en la raíz del rebuild |
| FE-15 | `features/portada` y `features/landing` son el mismo concepto en dos carpetas | Una usa claves `["landing",…]` y la otra vive en `portada` | Divergencia silenciosa |
| FE-16 | Prefijo de cookies heredado de CAM | `AUTH_STORAGE_PREFIX` por defecto `cam_auth` | Resto de nomenclatura del proyecto anterior |
| FE-17 | `features/landing/paquetes.service.ts` consume el tipo del *wizard* | Importa `PaqueteListContract` de `features/inscripciones/schemas/paquete.schema` | Acoplamiento entre dos features por un esquema compartido |

### 11.3 Corrección respecto a la exploración anterior

✅ La exploración previa (`sdd/explore/rebuild-frontend-map`) registraba un pie de página con texto corrupto en `app/informacion/page.tsx`. La verificación byte a nivel de esta pasada demuestra que el archivo **está codificado en UTF-8 correctamente** (`"Asociación Okinawense del Perú"` = `41 73 6F ... C3 B3 6E ... C3 BA`). La corrupción observada era un artefacto de la consola, no del código. No hay brecha de codificación que corregir.

---

## 12. Uso previsto

Este documento es la referencia de arquitectura del frontend para el rebuild y la entrada de la guía operativa para el agente de UI/UX. Las restricciones de intervención sobre este código —qué se puede cambiar, qué está prohibido y cómo se entrega un cambio— están en [`07-guia-para-ui-ux.md`](./07-guia-para-ui-ux.md).

Los contratos normativos que aplican al frontend son:

- [`../../contract/next-app-architecture-contract.md`](../../contract/next-app-architecture-contract.md) — estructura, nombres, estado, formularios, importaciones.
- [`../../contract/api-wrapper-presenter-contract.md`](../../contract/api-wrapper-presenter-contract.md) — envoltorios por módulo, espejo 1:1 frontend/backend, propiedad de los mensajes públicos.
- [`../../contract/smart.md`](../../contract/smart.md) — Smart Fields y desacoplamiento de UI.
- [`../../contract/django-app-architecture-contract.md`](../../contract/django-app-architecture-contract.md) — el lado del backend que consume este frontend.
- [`../../contract/PLAN_REFACTORIZACION.md`](../../contract/PLAN_REFACTORIZACION.md) — reglas de controladores, presentadores y errores públicos.
- [`../../contract/TEST_ARCHITECTURE_CONTRACT.md`](../../contract/TEST_ARCHITECTURE_CONTRACT.md) — criterios de pruebas (backend), aplicables por analogía a la disciplina de espejo.
