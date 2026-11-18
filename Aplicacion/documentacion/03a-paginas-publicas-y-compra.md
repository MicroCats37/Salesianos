# 03a — Páginas públicas, de cuenta y de compra (frontend)

> **Estado:** vigente (documento de referencia del rebuild controlado bajo `Aplicacion/`)
> **Alcance:** frontend Next.js (App Router) — páginas públicas, autenticación, cuenta del responsable, preinscripción deportiva y compra de pases de fiesta
> **Fuente de verdad:** el código. Este documento describe lo que existe hoy, no lo que debería existir
> **Owner:** frontend (la UI no es la autoridad de dominio; el backend lo es)
> **Última verificación:** 2026-11-18 sobre el árbol de trabajo local (`frontend/` y `backend/`)

## Convenciones de lectura

| Marcador | Significado |
|---|---|
| ✅ | Verificado en código en esta pasada (frontend y backend) |
| 🟡 | Verificado parcialmente o deducido del código con alta confianza |
| 🔴 | Brecha, duplicación o incoherencia verificada, sin resolver |

Este documento es la ficha operativa de **cada pantalla no administrativa** del rebuild: qué hace, quién la usa, qué llama, qué escribe, qué falla y qué está roto. Los contratos normativos viven en [`../../contract/`](../../contract/); el código describe la realidad y el contrato describe la obligación.

Documentos hermanos de la serie: [`README.md`](./README.md) (índice del conjunto documental), [`00-cobertura-y-trazabilidad.md`](./00-cobertura-y-trazabilidad.md) (recuentos verificados), [`01-arquitectura-y-runtime.md`](./01-arquitectura-y-runtime.md), [`02-backend-y-api.md`](./02-backend-y-api.md), [`02a-inventario-de-endpoints.md`](./02a-inventario-de-endpoints.md), [`02b-proposito-y-consumidores-de-endpoints.md`](./02b-proposito-y-consumidores-de-endpoints.md), [`03-frontend.md`](./03-frontend.md), [`04-datos-y-dominio.md`](./04-datos-y-dominio.md), [`05-flujos-end-to-end.md`](./05-flujos-end-to-end.md), [`05a-matriz-pagina-flujo-endpoint-datos.md`](./05a-matriz-pagina-flujo-endpoint-datos.md), [`06-operacion-y-deuda-tecnica.md`](./06-operacion-y-deuda-tecnica.md), [`07-guia-para-ui-ux.md`](./07-guia-para-ui-ux.md). Este documento no resume ni anticipa su contenido: describe el frontend no administrativo con detalle de endpoint.

**Nota sobre el árbol.** `Aplicacion/frontend/` es copia byte a byte de `frontend/` (verificado en [`03-frontend.md`](./03-frontend.md) §9). Todas las rutas de este documento se expresan desde la raíz del repositorio (`frontend/src/...`, `backend/modules/...`) y aplican a ambas copias.

---

## 1. Resumen ejecutivo

El frontend no administrativo comprende **8 páginas enrutables y 2 route handlers**. Cinco conclusiones:

1. ✅ **La capa de datos de servidor está bien delimitada**: todo estado remoto vive en TanStack Query; el único store Zustand del árbol (`features/auth/store/auth.store.ts`) guarda la sesión del cliente y **nunca autoriza**.
2. ✅ **La autoridad comercial y de elegibilidad está en el backend**: el frontend no calcula precios finales, no decide si una persona puede entrar a un equipo y no confirma pagos. Pide, renderiza lo que llega y propaga el error público del backend.
3. ✅ **Los flujos de escritura son atómicos en el servidor**: `POST /inscripciones/completa/`, `POST /inscripciones/{id}/pool/asignar`, `POST /pases/comprar` y el relay de Izipay resuelven en una transacción del backend.
4. 🔴 **La portada y `/informacion` son dos marketing sites paralelos** con el mismo catálogo consumido por dos clientes distintos, con bases de URL y espacios de nombres de caché diferentes; ambas muestran **datos de respaldo estático** como si fueran datos reales cuando la API no responde.
5. 🔴 **La página `/dashboard` viola el contrato de arquitectura**: 499 líneas de lógica de negocio dentro de `app/`, con `useState` + `useEffect` para la carga inicial, máquina de estados propia y tres componentes en línea.

| Métrica | Valor verificado |
|---|---|
| Páginas enrutables no administrativas | **8** (`/`, `/informacion`, `/login`, `/register`, `/dashboard`, `/dashboard/inscripcion/[id]`, `/inscripcion`, `/pases`) |
| Route handlers no administrativos | **2** (`/api/auth/refresh`, `/api/auth/logout`) |
| Páginas administrativas (fuera de alcance) | 12 (`/administracion/**`) |
| Endpoints backend referenciados | **32** de negocio + 1 de token |
| Route handlers que NO llaman al backend | **1** (`/api/auth/logout`) |
| Páginas cuyo contenido es totalmente estático | **0**; las secciones *editoriales* de `/` y `/informacion` sí lo son |
| Clientes HTTP distintos para un mismo endpoint de catálogo | **3** (axios + Zod, `fetch` crudo con validación, `fetch` crudo sin validación) |

---

## 2. Alcance, cobertura y exclusiones

### 2.1 Qué entra

Todas las páginas y route handlers de `frontend/src/app` **que no son de administración**, es decir: pública, autenticación, cuenta del responsable, preinscripción deportiva (registro + pago + roster) y compra de pases de fiesta (checkout + pago + beneficiarios).

### 2.2 Qué queda fuera

| Ruta | Motivo de exclusión |
|---|---|
| `/administracion`, `/administracion/usuarios`, `/administracion/inscripciones`, `/administracion/inscripciones/[id]`, `/administracion/equipos`, `/administracion/participantes`, `/administracion/pagos`, `/administracion/acreditaciones`, `/administracion/competencias`, `/administracion/competencias/[id]`, `/administracion/competencias/agenda`, `/administracion/competencias/cuadro` | Área administrativa: su propia capa de autoridad (`AdminSeccionGuard`) y su propio juego de endpoints (`/administracion/**`). Se documenta aparte. |

### 2.3 Inventario de cobertura (verificado)

| # | Ruta | Archivo de ruta | Tipo | ¿Llama al backend? |
|---|---|---|---|---|
| 1 | `/` | `frontend/src/app/page.tsx` | Server Component | ✅ Sí (3 endpoints, vía 3 componentes cliente) |
| 2 | `/informacion` | `frontend/src/app/informacion/page.tsx` | Server Component | ✅ Sí (1 endpoint) |
| 3 | `/login` | `frontend/src/app/(auth)/login/page.tsx` | Server Component → cliente | ✅ Sí (login + `GET /auth/me`) |
| 4 | `/register` | `frontend/src/app/(auth)/register/page.tsx` | Server Component → cliente | ✅ Sí (registro + lookup de documento) |
| 5 | `/dashboard` | `frontend/src/app/(app)/dashboard/page.tsx` | **Client Component con lógica** | ✅ Sí (`GET /inscripciones/`) |
| 6 | `/dashboard/inscripcion/[id]` | `frontend/src/app/(app)/dashboard/inscripcion/[id]/page.tsx` | Server Component → cliente | ✅ Sí (11 endpoints) |
| 7 | `/inscripcion` | `frontend/src/app/(app)/inscripcion/page.tsx` | Server Component → cliente | ✅ Sí (4 endpoints) |
| 8 | `/pases` | `frontend/src/app/(app)/pases/page.tsx` | Server Component → cliente | ✅ Sí (10 endpoints) |
| 9 | `/api/auth/refresh` | `frontend/src/app/api/auth/refresh/route.ts` | Route handler | ✅ Sí (`POST {backend}/token/refresh`) |
| 10 | `/api/auth/logout` | `frontend/src/app/api/auth/logout/route.ts` | Route handler | ❌ **No** (solo limpia cookies) |

**Recuento de páginas cubiertas: 8 páginas enrutables + 2 route handlers = 10 artefactos de ruta.**

---

## 3. Guardas, sesión y capas transversales

### 3.1 Cadena de guardas (aplica a todo el alcance)

| Capa | Artefacto | Decide | ¿Es autoridad? |
|---|---|---|---|
| 1. Edge (cortesía) | `frontend/src/proxy.ts` | Si existe la cookie `AUTH_COOKIES.ACCESS_TOKEN`. Sin ella → `redirect("/")`. Rutas públicas exentas: `/`, `/login`, `/register`, `/informacion` | **No.** La cookie no es `httpOnly`; el propio archivo lo declara. El `matcher` excluye `api`, `_next/static`, `_next/image`, `images`, `favicon.ico` y cualquier ruta con extensión |
| 2. Área `(app)` | `frontend/src/app/(app)/layout.tsx` | `getUserSession()` lee la cookie `USER_SESSION`; si no hay → `redirect("/")` | No por sí sola: `USER_SESSION` es una instantánea escribible por el cliente |
| 3. Backend | `JWTAuth()` / `IsAuthenticated` / `RequireAdmin` / `RequireCapability` | Revalida credenciales y permisos en **cada** petición | **Sí. La autoridad real.** El 403 del backend es la puerta, no el frontend |

Consecuencias verificadas:

- ✅ Un visitante anónimo que abre `/dashboard`, `/inscripcion`, `/pases` o `/dashboard/inscripcion/[id]` **cae en `/`** (no en `/login`): lo decide `proxy.ts`; si llegara al layout, `getUserSession()` también lo devuelve a `/`.
- ✅ `proxy.ts` además redirige `/login → /dashboard` cuando ya hay cookie de acceso.
- 🔴 La cookie `USER_SESSION` es **escrita por el cliente** (`useLogin`/`useRegister` con `cookies-next`) y contiene el JSON del usuario: el saludo del dashboard y el destino de navegación post-login dependen de datos que el navegador puede alterar. No autoriza nada, pero **sí** decide qué se muestra.

### 3.2 Transporte HTTP compartido

`frontend/src/lib/api.ts` es la instancia única de `axios`:

- `baseURL`: `backendPublicUrl()` en el navegador (`/backend`, mismo origen, proxy Nginx) y `backendInternalUrl()` en el servidor (`BACKEND_INTERNAL_URL` o `http://backend:8000/api`). El archivo explica que el servidor **no** puede resolver la URL relativa del navegador.
- `timeout`: 15 s.
- Interceptor de petición: inyecta `Authorization: Bearer` desde la cookie de acceso; **refresco proactivo** cuando el token expira en menos de 5 minutos.
- Interceptor de respuesta: ante `401`, refresca **una sola vez** (`_retry`) y reintenta.

🔴 **Dos clientes de catálogo se saltan `lib/api.ts`**: `features/landing/paquetes.service.ts` y `features/portada/hooks/useCatalogo.ts` usan `fetch` crudo, con `NEXT_PUBLIC_API_URL ?? http://localhost:8000/api` y fallback `http://backend:8000/api` en SSR. Consecuencias: no envían `Authorization`, no reintentan ante `401`, no refrescan el token y resuelven la URL por su cuenta.

### 3.3 Convenciones de estado

| Tipo de estado | Dueño | Ubicación | Nota |
|---|---|---|---|
| Datos de servidor | TanStack Query v5 | `frontend/src/lib/query-client.ts` (`staleTime` 5 s, `refetchOnWindowFocus: false`) | Namespaces: `["landing",…]`, `["inscripcion",…]`, `["inscripcion-detalle",…]`, `["inscripcion-pool",…]`, `["inscripcion-saldo",…]`, `["inscripcion-elegibles",…]`, `["pases",…]` |
| Sesión del cliente | Zustand v5 | `frontend/src/features/auth/store/auth.store.ts` (`persist` en `localStorage`) | Único store del árbol. **Nunca autoriza** |
| Cotización en curso | `useState` local | `features/inscripciones/hooks/useCotizacion.ts` | Efímera: pertenece a la sesión del wizard y a la cantidad seleccionada |
| Cantidades por paquete | `useState` + `useRef` espejo | `features/inscripciones/components/smart-fields/SmartPaqueteCardsField.tsx` | El `ref` evita perder incrementos en el mismo batch de React |
| Consentimientos del wizard | `useState` local | `features/inscripciones/components/InscripcionWizard.tsx` | **No** viajan en el payload atómico; el backend registra aceptaciones por persona |

---

## 4. Mapa ruta → feature → servicio → endpoint

✅ Verificado por lectura de las páginas, sus imports y los servicios/hooks correspondientes.

| Ruta | Feature | Servicio / transporte | Endpoint(s) backend |
|---|---|---|---|
| `/` | `portada` (config + copy) + `components/portada/**` | `features/portada/hooks/useCatalogo.ts` (`fetch` crudo) · `features/landing/hooks/useLandingPaquetes.ts` → `features/landing/paquetes.service.ts` (`fetch` crudo) | `GET /catalogo/disciplinas/`, `GET /catalogo/categorias/`, `GET /catalogo/paquetes/` |
| `/informacion` | `landing` + `components/landing/**` | `features/landing/hooks/useLandingPaquetes.ts` → `features/landing/paquetes.service.ts` (`fetch` crudo) | `GET /catalogo/paquetes/` |
| `/login` | `auth` | `features/auth/hooks/useLogin.ts` (axios directo) · `features/admin/services/admin.me.service.ts` (axios) | `POST /auth/login/dni`, `POST /auth/login/email`, `POST /auth/login/username`, `GET /auth/me` |
| `/register` | `auth` + `inscripciones` (lookup) | `features/auth/services/register.service.ts` (axios) · `features/inscripciones/services/inscripcion.service.ts` → `consultarDocumento` (axios) | `POST /auth/register`, `GET /personas/busqueda/{documento}` |
| `/dashboard` | `inscripciones` (lógica en la página) | `features/inscripciones/services/inscripcion.service.ts` → `getMisInscripciones` (axios) | `GET /inscripciones/` |
| `/dashboard/inscripcion/[id]` | `inscripciones` + `pagos` | `inscripcion.service.ts`, `pool.service.ts`, `elegibles.service.ts`, `pago.service.ts` (axios) | `GET /inscripciones/{id}/detalle`, `GET /inscripciones/{id}/pool`, `GET /inscripciones/{id}/saldo`, `GET /inscripciones/{id}/equipos/{equipoId}/elegibles`, `POST /inscripciones/{id}/personas`, `POST /inscripciones/{id}/pool/asignar`, `PATCH /participaciones/{id}`, `PATCH /participaciones/{id}/retirar`, `POST /compras/{compraId}/iniciar-pago`, `POST /pagos/izipay/confirmar`, `GET /pagos/transacciones/{txId}` |
| `/inscripcion` | `inscripciones` | `paquete.service.ts`, `catalog.service.ts`, `cotizacion.service.ts`, `inscripcion.service.ts` (axios) | `GET /catalogo/paquetes/`, `GET /catalogo/promociones/`, `POST /cotizaciones/`, `POST /inscripciones/completa/` |
| `/pases` | `pases` + `pagos` | `pase.service.ts`, `pase.beneficiario.service.ts`, `persona.resolucion.service.ts`, `pago.service.ts` (axios + Zod) | `GET /pases/`, `POST /pases/comprar`, `GET /pases/compras/{compraId}`, `GET /pases/compras/{compraId}/beneficiarios`, `POST /pases/compras/{compraId}/beneficiarios`, `DELETE /pases/compras/{compraId}/beneficiarios/{personaId}`, `GET /personas/resolver`, `POST /compras/{compraId}/iniciar-pago`, `POST /pagos/izipay/confirmar`, `GET /pagos/transacciones/{txId}` |
| `/api/auth/refresh` | `lib/auth` + `lib/server/jwt` | `fetch` servidor → `backendInternalUrl()` | `POST {backend}/token/refresh` (controlador JWT de `django-ninja-jwt`, registrado en `backend/config/api.py:104`) |
| `/api/auth/logout` | `lib/auth` | — | **Ninguno** |

---

## 5. Fichas por página

---

### 5.1 `/` — Portada del festival

**Ruta y propósito funcional.** Página institucional que presenta el evento (deporte, familia y fiesta), muestra el catálogo de paquetes con su precio vigente y sirve de punto de entrada a la preinscripción deportiva y a la compra de pases. No gestiona datos del usuario: no escribe nada y no exige sesión.

**Usuario/rol previsto y puntos de entrada.**

- Visitante anónimo (rol principal).
- Con sesión previa: el `Navbar` muestra “Mi cuenta” en lugar de “Iniciar sesión” (`components/landing/Navbar.tsx:41-50`).
- Puntos de entrada: raíz del dominio, enlace directo, enlaces de campaña (WhatsApp/Facebook) y el `redirect("/")` de `proxy.ts` / `app/(app)/layout.tsx` para usuarios no autenticados.

**Secciones visibles y componentes importantes.** ✅ Verificado en `frontend/src/app/page.tsx:44-69`, en orden de render:

| # | Componente | Qué muestra |
|---|---|---|
| 0 | `ScrollSnapScope` | Comportamiento de scroll con anclas |
| 1 | `Navbar` (`components/landing/Navbar.tsx`) + `NavbarBrand` | Navegación por anclas (`NAV_LINKS`), botón “Iniciar sesión”/“Mi cuenta”, “Comprar pase de fiesta”, CTA “Inscribir equipo”, botón “En vivo” (oculto: `EN_VIVO.url === ""`) |
| 2 | `HeroPortada` | Claims del evento; CTA “VIVE EL FESTIVAL” → `#paquetes` y “Mira quiénes vienen” → `#promociones` (`features/portada/copy.ts:20-21`) |
| 3 | `FestivalRibbon` | Cinta promocional |
| 4 | `MomentosSection` | Momentos del festival + `Countdown` a la fecha del evento |
| 5 | `ExperienceSection` | Experiencia del evento; enlace al calendario `.ics` |
| 6 | `PromotionsSection` | Promociones: **datos estáticos** de `features/portada/config/promotions.ts` |
| 7 | `ChampionshipSection` | ✅ **Tabs por disciplina** con datos del backend |
| 8 | `ScheduleSection` | Cronograma del día; ✅ **Categorías** del backend |
| 9 | `FamilySection` | Contenido de familia (estático) |
| 10 | `PartySection` | La fiesta (estático) |
| 11 | `TicketsSection` | ✅ **Paquetes** del backend con precio por etapa de venta |
| 12 | `PartyPassSection` | Pase de fiesta (estático; usa `pricing-stage.ts` para la etiqueta de etapa) |
| 13 | `RegistrationSteps` | Pasos de inscripción; CTA → `ENLACES.registro` = `/inscripcion` |
| 14 | `LiveSection` | Transmisión en vivo (estado “proximamente”; diálogo con `EN_VIVO.url` vacío) |
| 15 | `VenueSection` | Sede y mapa (Google Maps embebido + enlace externo) |
| 16 | `SponsorsSection` | Auspiciadores: **lista vacía** (`AUSPICIADORES: []` en `config/festival.ts:60`) |
| 17 | `FaqSection` | Preguntas frecuentes (estático) |
| 18 | `ClosingSection` | Cierre + CTA → `/inscripcion` |
| 19 | `PortadaFooter` | Pie: marca, redes, WhatsApp |
| 20 | `MobileTicketBar` | Barra fija en móvil → `#paquetes` |

**Acciones del usuario.**

- Navegar por anclas internas (`#experiencia`, `#promociones`, `#campeonato`, `#familia`, `#fiesta`, `#paquetes`, `#auspiciadores`).
- Cambiar de pestaña en el campeonato (`ChampionshipSection`, `role="tablist"`, navegación por flechas/Home/End).
- Cambiar de pestaña en el bloque de paquetes (`PACK` ↔ `DISCIPLINA`) en `TicketsSection`.
- Descargar el calendario (`/salesianos-fest-2026.ics`, `ENLACES.calendario`).
- Ir a “Inscribir equipo” → `/inscripcion`; a “Ya tengo una cuenta” → `/login`; a “Comprar pase de fiesta” → `/pases` **si hay sesión**, o → `/register` si no la hay (`Navbar.tsx:50`).
- Contacto externo: WhatsApp (`https://wa.me/51967951650`), Facebook, Instagram, TikTok, mapa de Google.

**Guardas, prerrequisitos y destinos.**

- ✅ Ruta pública: `proxy.ts` la exime explícitamente.
- ✅ No hay prerrequisito de sesión para ver nada.
- 🔴 `Navbar.tsx:41-45` enruta a `/admin/dashboard` cuando `user.rol` es `admin_comite` o `admin_finanzas`, **ruta que no existe** en el árbol (`app/(app)/administracion` es la ruta real). Un usuario con ese rol en la cookie `USER_SESSION` clicaría “Mi cuenta” y recibiría un 404. El cálculo real de `rol` en el backend (`me_controller.py:96`) devuelve `"admin"` o `"user"`, por lo que la rama es alcanzable solo con una cookie manipulada.

**Estado, hooks, formularios, esquemas y servicios.**

| Elemento | Ubicación | Detalle |
|---|---|---|
| `useDisciplinas()` | `features/portada/hooks/useCatalogo.ts:225` | `useQuery`, clave `["landing","disciplinas"]`, `staleTime` 5 min, `gcTime` 30 min. `fetch` crudo a `GET /catalogo/disciplinas/` |
| `useCategorias()` | `features/portada/hooks/useCatalogo.ts:235` | `useQuery`, clave `["landing","categorias"]`. `fetch` crudo a `GET /catalogo/categorias/` |
| `useLandingPaquetes()` | `features/landing/hooks/useLandingPaquetes.ts:6` | `useQuery`, clave `["landing","paquetes"]` (**sin** `staleTime`: hereda el global de 5 s) → `fetchPaquetes()` |
| `fetchCatalogo<T>()` | `features/portada/hooks/useCatalogo.ts:201` | `fetch` + `cache: "no-store"` + `apiResponseSchema(esquema).safeParse`. Devuelve `null` ante cualquier fallo |
| `fetchPaquetes()` | `features/landing/paquetes.service.ts:30` | `fetch` + `cache: "no-store"`. **Sin validación Zod**: solo comprueba `success` y `data` y normaliza los tres precios con `Number()` |
| Esquemas | `features/portada/hooks/useCatalogo.ts:17-38` | `DisciplinaOutSchema` y `CategoriaOutSchema`, espejo 1:1 de `DisciplinaOut`/`CategoriaOut` del backend |
| Configuración estática | `features/portada/config/festival.ts`, `config/promotions.ts`, `features/portada/copy.ts` | Fechas, enlaces, secciones, textos, promociones |
| Etapa de venta | `features/portada/pricing-stage.ts` + `useEtapaPrecio()` en `TicketsSection.tsx:23` | Calcula la etapa vigente en el **navegador** y refresca cada 60 s |
| Formularios | — | **Ninguno**: la portada no tiene formularios |

**Endpoints backend consumidos.**

| Endpoint | Campos de request | Respuesta usada | Por qué |
|---|---|---|---|
| `GET /api/catalogo/disciplinas/` | — (sin body, sin auth) | `id`, `nombre`, `sigla`, `min_jugadores` (el resto del `DisciplinaOut` se valida pero no se pinta) | Alimenta las tabs del campeonato; `min_jugadores` se muestra como “Equipos con un mínimo de N integrantes” |
| `GET /api/catalogo/categorias/` | — (sin body, sin auth) | `nombre`, `promocion_desde`, `promocion_hasta` | Desplegable “Categorías” del cronograma |
| `GET /api/catalogo/paquetes/` | — (sin body, sin auth) | `id`, `tipo` (para filtrar PACK/DISCIPLINA), `nombre`, `descripcion`, `precios[]`/precios por etapa, `disciplinas`, `beneficios`, `tiene_fiesta/box/cerveza` | Renderiza las tarjetas comerciales con el importe de la etapa vigente |

**Cadena de ejecución backend (verificada).**

- `GET /catalogo/disciplinas/` → `backend/modules/salesianos_fest/presentation/controllers/catalogo_controller.py:36` `CatalogoController.listar_disciplinas` (`auth=None`, `permissions=[AllowAny]`) → `DisciplinaSelector.get_activas` (consulta `disciplinas` con `esta_activa=True`) → `CatalogoPresenter.present_disciplinas` → `success_response(...)`.
- `GET /catalogo/categorias/` → `catalogo_controller.py:62` → `CategoriaSelector.get_activas` (`categorias`) → `CatalogoPresenter.present_categorias`.
- `GET /catalogo/paquetes/` → `catalogo_controller.py:75` → `PaqueteSelector.get_activos` (`paquetes` + `paquetes_precios` + `paquetes_disciplinas` + `paquetes_beneficios`) → `CatalogoPresenter.present_paquetes` (convierte los `Decimal` a `float`, porque el Zod del frontend exige `z.number()`).

**Modelos y tablas leídos.** `paquetes`, `paquetes_precios`, `paquetes_disciplinas`, `paquetes_beneficios`, `disciplinas`, `categorias`. **Ninguna escritura.** La portada no produce efectos secundarios.

**Comportamiento de estados.**

| Estado | Comportamiento verificado |
|---|---|
| Carga | Solo `TicketsSection` muestra un esqueleto (4 tarjetas `animate-pulse`). `ChampionshipSection` y `ScheduleSection` **no muestran loader**: pintan directamente el contenido de respaldo |
| Vacío | `useCatalogo` devuelve `null` → `ChampionshipSection` usa `DISCIPLINAS_FALLBACK` y `ScheduleSection` usa `CATEGORIAS_FALLBACK`; `TicketsSection` con `paquetes === null` **no muestra ninguna tarjeta** (lista vacía sin mensaje) |
| Éxito | Listas del backend con fallback de presentación (`presentacionDisciplina`) para las canchas y el aforo, que **no existen en la API** |
| Validación | No aplica (no hay formulario) |
| Error de negocio | No aplica. Los fallos de red se silencian: `fetchCatalogo` y `fetchPaquetes` capturan la excepción y devuelven `null` |
| Recuperación | 🔴 **No hay recuperación**: si la API falla, la página muestra datos de respaldo y no reintenta. `fetchCatalogo` devuelve `null` en vez de lanzar, así que **nunca hay estado de error ni reintento manual** |

**Brechas, duplicación y código muerto.**

- 🔴 **Datos de respaldo presentados como reales**: `DISCIPLINAS_FALLBACK`, `CATEGORIAS_FALLBACK` y `FALLBACK_PAQUETES` (8 paquetes con precios 40/45/50/55/60/70) se renderizan con el mismo aspecto que los del backend. El usuario no puede distinguir “catálogo real” de “respaldo editorial”. Documentado en `features/portada/hooks/useCatalogo.ts:110-115` y `components/landing/Paquetes.tsx:135-272`.
- 🔴 **Dos clientes de `GET /catalogo/paquetes/`** con bases de URL distintas (`NEXT_PUBLIC_API_URL` vs. `backendPublicUrl()`), sin autenticación y con estrategias de validación opuestas (`fetchPaquetes` no valida; `paquete.service.fetchPaqueteList` sí valida con Zod).
- 🔴 **Dos espacios de nombres de caché** para el mismo catálogo: `["landing","paquetes"]` frente a `["inscripcion","paquetes"]` → doble descarga, sin invalidación cruzada.
- 🔴 **Dos hooks homónimos** `useDisciplinas`/`useCategorias` en `features/portada/hooks/useCatalogo.ts` y `features/inscripciones/hooks/useInscripcionCatalogs.ts`.
- 🔴 `TicketsSection` no distingue “catálogo vacío” de “catálogo no cargado”: si el backend devuelve `[]`, la sección queda en blanco.
- 🟡 `useEtapaPrecio()` replica en el navegador la etapa comercial (preventa/regular) con las ventanas de `features/portada/config/festival.ts:23-29`. Es **una segunda fuente de verdad** del calendario de ventas: el backend también resuelve la etapa vigente en `paquetes_precios`.
- 🟡 `EN_VIVO.url === ""` y `AUSPICIADORES = []`: las secciones “En vivo” y “Auspiciadores” renderizan estructura sin contenido. `SponsorsSection` y `LiveSection` son, hoy, cascos vacíos.
- 🟡 `components/landing/*` (`Hero.tsx`, `EventInfoBlocks.tsx`, `Process.tsx`, `Reglamento.tsx`, `HeroOverlaySection.tsx`) coexiste con `components/portada/*`: la primera familia sirve a `/informacion`, la segunda a `/`. Ninguna de las dos está muerta, pero el solapamiento conceptual es real.

---

### 5.2 `/informacion` — Micrositio de información

**Ruta y propósito funcional.** Página informativa del evento con el catálogo de paquetes, la cobertura deportiva y una galería. Es la versión “micrositio” de la portada: mismo dominio de datos, presentación distinta.

**Usuario/rol previsto y puntos de entrada.** Visitante anónimo. Ruta pública en `proxy.ts`. ✅ Ninguna ruta interna del árbol enlaza a `/informacion` de forma directa; queda accesible por URL.

**Secciones visibles y componentes importantes.** ✅ `frontend/src/app/informacion/page.tsx:12-101`:

| # | Componente | Detalle |
|---|---|---|
| 1 | `Navbar` (`components/landing/Navbar.tsx`) | Usa los `DEFAULT_NAV_LINKS`: `#disciplinas`, `#paquetes`, `#proceso`, `#reglamento` |
| 2 | `HeroOverlaySection` | Hero con imagen, datos del evento y `PreinscribirButton` |
| 3 | `Paquetes` | ✅ **Catálogo del backend** + `PaquetesCards` + `PreinscribirCTA` |
| 4 | `Disciplines` | Cobertura deportiva: **datos hardcodeados** (`DISCIPLINES`, `CATEGORY_ROWS` en `components/landing/Disciplines.tsx:10-60`) |
| 5 | `Gallery` | Carrusel de imágenes (Embla), sin datos remotos |
| 6 | Footer inline | Marca (`FestBrandHeader`), redes sociales, texto legal |

**Acciones del usuario.** Cambiar de pestaña de paquetes, navegar por anclas, “Preinscribir equipo” → `/inscripcion` si hay sesión, `/register` si no (`components/landing/PreinscribirButton.tsx:19`).

**Guardas, prerrequisitos y destinos.** Ruta pública. Sin prerrequisitos.

**Estado, hooks, formularios, esquemas y servicios.**

| Elemento | Ubicación |
|---|---|
| `useLandingPaquetes()` | `features/landing/hooks/useLandingPaquetes.ts:6` — clave `["landing","paquetes"]` |
| `fetchPaquetes()` | `features/landing/paquetes.service.ts:30` — `fetch` crudo, `cache: "no-store"`, **sin Zod** |
| `Paquetes` | `components/landing/Paquetes.tsx:274` — si `paquetes` es `null` o vacío → `FALLBACK_PAQUETES` (8 paquetes) |
| `PaquetesCards` / `PaqueteComercialCard` / `PreventaBanner` | `components/landing/PaquetesCards.tsx`, `components/paquetes/**` |
| `useAuthUser()` | `features/auth/store/auth.store.ts` — solo para decidir `/inscripcion` vs `/register` |
| Formularios | Ninguno |

**Endpoints backend consumidos.**

| Endpoint | Request | Respuesta usada | Por qué |
|---|---|---|---|
| `GET /api/catalogo/paquetes/` | — | Lista de paquetes con precios, disciplinas y beneficios | Es el contenido comercial del micrositio |

**Cadena de ejecución backend.** Idéntica a la de la portada: `CatalogoController.listar_paquetes` → `PaqueteSelector.get_activos` → `CatalogoPresenter.present_paquetes` → `success_response`.

**Modelos y tablas leídos.** `paquetes`, `paquetes_precios`, `paquetes_disciplinas`, `paquetes_beneficios`. **Ninguna escritura.**

**Comportamiento de estados.**

| Estado | Comportamiento |
|---|---|
| Carga | 🔴 `Paquetes` **no** muestra esqueleto: mientras la query vuela, renderiza directamente los 8 paquetes de respaldo |
| Vacío | `FALLBACK_PAQUETES` |
| Éxito | Catálogo del backend |
| Validación | No aplica |
| Error de negocio | No aplica (público) |
| Recuperación | 🔴 Ninguna. El error de red se traga `fetchPaquetes` y devuelve `null` |

**Brechas, duplicación y código muerto.**

- 🔴 **Anclas rotas**: el `Navbar` de esta página ofrece `#proceso` y `#reglamento`, pero la página **no renderiza** `Process` ni `Reglamento` (`components/landing/Process.tsx` y `Reglamento.tsx` existen y están exportados por `components/landing/index.ts` pero no se importan en `app/informacion/page.tsx`). Dos de los cuatro enlaces del navbar no llevan a ninguna sección.
- 🔴 `Disciplines` muestra **categorías y aforos hardcodeados** (“Máximo 12 jugadores”, “Junior 2012–2025…”) mientras el backend tiene `Disciplina.min_jugadores/max_jugadores` y `Categoria.promocion_desde/promocion_hasta`. La información puede divergir del dominio sin señal alguna para el usuario.
- 🔴 `components/landing/Paquetes.tsx` y `components/portada/TicketsSection.tsx` renderizan el mismo catálogo con dos clientes HTTP distintos y dos espacios de caché distintos.
- 🟡 `Hero.tsx` y `HeroOverlaySection.tsx` son dos implementaciones del mismo hero (16 KB cada una); solo se usa la segunda en `/informacion` y `HeroPortada` en `/`. `components/landing/Hero.tsx` es **código muerto** ✅ (verificado: ningún archivo de `app/` lo importa).
- 🟡 `PaquetesCardsClient.tsx` es un *wrapper* de 324 bytes que solo reexporta `PaquetesCards`; no aparece en ningún import del árbol de `app/` ni de `features/`.

---

### 5.3 `/login` — Inicio de sesión

**Ruta y propósito funcional.** Autenticación de usuarios existentes por **tres credenciales alternativas**: DNI, email o nombre de usuario. Entrega los tokens, guarda la sesión en cookies y en el store, y redirige al destino que corresponde al rol.

**Usuario/rol previsto y puntos de entrada.**

- Visitante no autenticado. Entra desde “Iniciar sesión” en el `Navbar` de `/` y `/informacion`, desde “Ya tengo una cuenta” en `TicketsSection`, o desde el enlace “Inscribe tu equipo” de la propia pantalla de login.
- Con sesión previa: `proxy.ts:57-59` redirige `/login → /dashboard`.

**Secciones visibles y componentes importantes.** ✅ `features/auth/views/LoginClientShell.tsx`:

- `AuthShell` (marca + panel visual) → `AuthGlassCard` → `LoginBody`.
- Selector de 3 pestañas: **DNI** (por defecto), **Email**, **Usuario**.
- Cada pestaña monta su propio formulario (`DniTabForm`, `EmailTabForm`, `UsernameTabForm`) con un `PasswordInputField` propio (mostrar/ocultar contraseña).
- Pie: enlace “Inscribe tu equipo” → `/register`.

**Acciones del usuario.** Elegir credencial, escribir identificador y contraseña, alternar la visibilidad de la contraseña, enviar, o navegar a `/register`.

**Guardas, prerrequisitos y destinos.**

- ✅ Ruta pública; `proxy.ts` la exime y además la redirige a `/dashboard` si ya hay token.
- ✅ El backend exige `JWTAuth` solo en la capa privada; el login es `auth=None`.
- Destinos tras éxito ✅ `resolverDeDestino()` (`features/auth/utils/resolver-destino.ts`):
  1. `consumePostAuthRedirect()` (sessionStorage, clave de `components/event/PreinscribirCta`) si existe;
  2. si `GET /auth/me` responde `es_admin === true` → `/administracion`;
  3. en cualquier otro caso (incluido fallo de `/auth/me`) → `/dashboard`.

**Estado, hooks, formularios, esquemas y servicios.**

| Elemento | Ubicación | Detalle |
|---|---|---|
| `useLogin()` | `features/auth/hooks/useLogin.ts:51` | `useMutation`; resuelve el endpoint según el campo presente en el payload (`username` → `/dni` → `email`) |
| `LoginDniFormSchema` / `LoginEmailFormSchema` / `LoginUsernameFormSchema` | `features/auth/schemas/login.schema.ts` | Validación Zod por pestaña |
| `useForm` + `zodResolver` | `LoginClientShell.tsx:137` | Validación de cliente antes de la red |
| `useAuthStore().setAuth` | `features/auth/store/auth.store.ts` | Persiste el usuario en el store (Zustand + `persist`) |
| `setCookie` (cookies-next) | `features/auth/hooks/useLogin.ts:87-90` | Escribe `ACCESS_TOKEN`, `REFRESH_TOKEN`, `EXPIRES_AT`, `USER_SESSION` con `httpOnly: false`, `sameSite: "lax"`, `maxAge` 7 días |
| `handleApiError` | `errors/error-handler.ts` | Convierte el error en mensaje para `toast.error` |
| `getAdminMe()` | `features/admin/services/admin.me.service.ts:23` | `GET /auth/me`; se usa **desde una feature pública** (acoplamiento `auth → admin`) |

**Endpoints backend consumidos.**

| Endpoint | Campos de request | Respuesta usada | Por qué |
|---|---|---|---|
| `POST /api/auth/login/dni` | `{ dni, password }` | `access_token`, `refresh_token`, `expires_at`, `user` (id, username, email, is_staff, is_superuser, persona_id) | Token de acceso y sesión |
| `POST /api/auth/login/email` | `{ email, password }` | idem | idem |
| `POST /api/auth/login/username` | `{ username, password }` | idem | idem |
| `GET /api/auth/me` | — | `es_admin` (único campo usado) | Decidir el destino post-login |

**Cadena de ejecución backend (verificada).**

- `POST /auth/login/{dni,email,username}` → `backend/modules/usuarios/presentation/controllers/auth_controller.py:42/61/80` (`AuthLoginController`, `@api_controller("/auth/login")`, `auth=None`) → `AuthOrchestrator.login_dni|login_email|login_username` (`domain/services/orchestrators/auth_orchestrator.py`) → `AuthFlujo` (`domain/services/flujos/auth_flujo.py`) → `AuthPresenter.present_login` → `success_response(..., message="Inicio de sesión exitoso.")`.
- `GET /auth/me` → `backend/modules/usuarios/presentation/controllers/me_controller.py:53` `AuthMeController.me` (`auth=JWTAuth()`), **sin orchestrator**: lee `request.user`, `persona_fk` y calcula `es_admin = is_staff OR is_superuser` (`core/permissions.py`).

**Modelos y tablas leídos/escritos.**

- Lectura: `usuarios_usuario` (y `usuarios_persona` vía `persona_fk`) para autenticar y para `GET /auth/me`.
- Escritura: **ninguna**. El login no crea ni modifica filas.

**Comportamiento de estados.**

| Estado | Comportamiento verificado |
|---|---|
| Carga | Botón “Verificando…” con spinner mientras `isSubmitting \|\| isPending`; las tres pestañas crean **tres instancias** de `useLogin()` (una por formulario) |
| Vacío | No aplica (formulario) |
| Éxito | `toast.success(message)` con el mensaje del backend y `router.push(destino)` |
| Validación | Zod en cliente: `LoginDniFormSchema` (DNI de 8 dígitos), `LoginEmailFormSchema` (email), `LoginUsernameFormSchema`, y `password` obligatorio. Los errores se pintan bajo el campo con borde `destructive` |
| Error de negocio | `catch` → `toast.error(handleApiError(error).message)`. El mensaje es el público del backend (`error.message` del sobre), no el texto crudo del HTTP |
| Recuperación | ✅ **No hay recuperación de credenciales**: si el usuario se equivoca, reintenta a mano. El interceptor de `lib/api.ts` no interviene porque el login es público |

**Brechas, duplicación y código muerto.**

- 🔴 **El login escribe cookies desde el cliente con `httpOnly: false`**, mientras existe `lib/auth/actions.ts::setAuthCookies` (Server Action, misma semántica) que **nadie invoca**: ✅ `setAuthCookies` solo aparece en su definición y en el barrel `lib/auth/index.ts`. Es **código muerto**, y su existencia sugiere que en algún momento el login pasó por Server Action. Hoy la cookie del token de acceso es legible por cualquier script del navegador.
- 🔴 **Tres instancias de `useLogin()`** (una por pestaña) y tres formularios casi idénticos duplicados línea a línea (`DniTabForm`, `EmailTabForm`, `UsernameTabForm`): ~170 líneas de código repetido que cualquier cambio de UX debe aplicar tres veces.
- 🔴 El parámetro `isLoading` de las tres pestañas **siempre vale `false`** (`LoginClientShell.tsx:473-475`): existe una vía de carga que nunca se usa.
- 🔴 `LoginClientShell` depende de `features/admin/services/admin.me.service.ts` para decidir el destino. La feature pública `auth` importa la feature `admin`: acoplamiento que contradice la separación por dominio y arrastra el esquema de administración al login.
- 🟡 `resolveLogin()` decide el endpoint por **presencia de clave** (`"username" in payload`), no por discriminador: es frágil ante campos opcionales.
- 🟡 `features/auth/utils/resolver-destino.ts` **silencia el error** de `GET /auth/me` (`catch → /dashboard`): si el backend está caído, el usuario aterriza en `/dashboard` y no sabe por qué.
- 🟡 El store guarda el `user` completo y la cookie `USER_SESSION` guarda su JSON: dos copias del mismo dato, una de ellas editable por el cliente.

---

### 5.4 `/register` — Creación de cuenta

**Ruta y propósito funcional.** Alta del usuario responsable: crea la cuenta de acceso y, con ella, la `Persona` asociada, la aceptación de bases y los tokens de sesión. Incluye autocompletado de nombres desde RENIEC/SUNAT mediante la búsqueda de documento.

**Usuario/rol previsto y puntos de entrada.**

- Visitante no autenticado que quiere preinscribir un equipo o comprar un pase.
- Entradas: `Navbar` (“Inscribir equipo” → `/register` si no hay sesión), `PreinscribirButton`/`PreinscribirCTA` (`components/landing`), “Inscribe tu equipo” desde `/login`.
- Con `?nextUrl=` en la URL: el registro devuelve al usuario a ese destino (`useRegister.ts:70-74`). El destino se decodifica con `decodeURIComponent` y se usa como ruta de `router.push`.

**Secciones visibles y componentes importantes.** ✅ `features/auth/views/RegisterClientShell.tsx` → `AuthShell variant="register" invertColumns` → `AuthGlassCard` → `RegisterForm` (`features/auth/components/RegisterForm.tsx`):

| Campo | Control | Reglas de cliente |
|---|---|---|
| Email | `SmartEmailField` | Obligatorio, ≤120, formato email |
| Contraseña | `SmartPasswordField` | 8–120 caracteres, con mostrar/ocultar |
| Confirmar | `SmartConfirmPasswordField` | Obligatorio; debe coincidir (`refine` → error en `confirmPassword`) |
| Tipo de documento | `SmartTipoDocumentoField` (Select) | `DNI` \| `CE` \| `PAS` |
| Número de documento | `SmartNumeroDocumentoField` | DNI 8 dígitos, CE 9, PAS ≥4 alfanuméricos en mayúsculas. Longitud máxima según tipo (8/9/20) |
| Buscar por DNI | Botón de lupa (solo si `tipoDocumento === "DNI"` y 8 dígitos) | Autocompleta `nombres` y `apellidos` |
| Nombres / Apellidos | `SmartTextField` | Obligatorios, ≤120 |
| Género | `SmartSelectField` | `M` \| `F` |
| Bases | `SmartAcceptedBasesCheckboxField` | `z.literal(true)` — obligatorio marcar |
| Teléfono / WhatsApp / contacto de emergencia | Campos declarados en el esquema, **no renderizados** | Envían `null` |

**Acciones del usuario.** Buscar nombres por DNI, rellenar o corregir el documento (el cambio de tipo de documento **borra** el número y los nombres auto-completados, `RegisterForm.tsx:302-310`), marcar las bases, crear la cuenta.

**Guardas, prerrequisitos y destinos.**

- ✅ Ruta pública (eximida en `proxy.ts`).
- Destinos tras éxito ✅ `useRegister.ts:70-78`: `nextUrl` de la query → `consumePostAuthRedirect()` → `/inscripcion`. Después `router.push(destino)` **y** `router.refresh()`.

**Estado, hooks, formularios, esquemas y servicios.**

| Elemento | Ubicación | Detalle |
|---|---|---|
| `useRegister()` | `features/auth/hooks/useRegister.ts:40` | `useMutation`; en `onSuccess` persiste tokens, actualiza el store, redirige |
| `registerUser()` | `features/auth/services/register.service.ts:11` | `POST /auth/register` con el payload tal cual (camelCase) |
| `RegisterFormSchema` | `features/auth/schemas/register.schema.ts:37` | `.strict()` + `refine` (contraseñas) + `superRefine` (documento según tipo) |
| `RegisterResponse` | `features/auth/schemas/register.schema.ts:131` | Espejo de `RegisterOut` |
| `GenericForm` | `components/genericForm/GenericForm.tsx` | `useForm` + `zodResolver`; `showErrorsAsToasts` |
| `useDocumentoLookup()` | `features/inscripciones/hooks/useDocumentoLookup.ts:54` | `useMutation` → `GET /personas/busqueda/{documento}`; **divide** `razon_social` en nombres/apellidos con heurística local (`splitRazonSocial`) |
| `persistAuthTokens` | `features/auth/hooks/useRegister.ts:21` | Cookies cliente `httpOnly: false`, `maxAge` 7 días |

**Endpoints backend consumidos.**

| Endpoint | Campos de request | Respuesta usada | Por qué |
|---|---|---|---|
| `POST /api/auth/register` | `email`, `password`, `confirmPassword`, `tipoDocumento`, `numeroDocumento`, `nombres`, `apellidos`, `genero`, `telefono`, `whatsapp`, `contactoEmergenciaNombre`, `contactoEmergenciaTelefono`, `acceptedBases` (camelCase, coincide 1:1 con `RegisterIn`) | `access_token`, `refresh_token`, `expires_at`, `user{id,username,email,is_staff,is_superuser,persona_id}` | Crear la cuenta y autenticar de inmediato |
| `GET /api/personas/busqueda/{documento}` | — (path param: 8 dígitos → DNI/RENIEC, 11 → RUC/SUNAT) | `tipo_documento`, `numero_documento`, `razon_social` | Autocompletar nombres y apellidos antes de escribir a mano |

**Cadena de ejecución backend (verificada).**

- `POST /auth/register` → `backend/modules/usuarios/presentation/controllers/registro_controller.py:35` `RegistroController.register` (`auth=None`) → `RegistroOrchestrator.registrar` (`domain/services/orchestrators/registro_orchestrator.py`) → `RegistroFlujo` (`domain/services/flujos/registro_flujo.py`) → `RegistroPresenter.present_registro` → `success_response(..., message="Registro exitoso. Ya puedes iniciar sesión.")`. **Efectos**: crea `Persona` (si no existe para ese documento), `Usuario` y la `Aceptacion` de BASES con IP y user-agent (`registro_controller.py:42,54-55`).
- `GET /personas/busqueda/{documento}` → `backend/modules/usuarios/presentation/controllers/persona_busqueda_controller.py:37` (`auth=None`, `permissions=[AllowAny]`) → `PersonaBusquedaOrchestrator.buscar_documento` → `PersonaBusquedaFlujo` → `PersonaBusquedaPresenter.present_documento`. Consulta **servicios externos** (RENIEC/SUNAT), no la base de datos del festival.

**Modelos y tablas leídos/escritos.**

- `POST /auth/register` **escribe**: `usuarios_persona`, `usuarios_usuario` y el registro de aceptación (tabla de aceptaciones de la app `usuarios`).
- `GET /personas/busqueda/{documento}` **no** lee ni escribe la base del festival: consume un servicio externo.

**Comportamiento de estados.**

| Estado | Comportamiento verificado |
|---|---|
| Carga | Botón “Creando cuenta…” con spinner mientras `isSubmitting`; el botón de búsqueda de DNI muestra spinner mientras `documentoLookup.isPending` |
| Vacío | No aplica (formulario); el formulario inicia con `telefono/whatsapp/contacto*` en `null` y `acceptedBases: false` |
| Éxito | `toast.success(message)` con el mensaje del backend; persistencia de cookies y del store; redirección |
| Validación | Zod en cliente + `GenericForm` con `showErrorsAsToasts`; los errores de campo se pintan bajo el input con `AlertCircle`; `superRefine` del documento; `refine` de contraseñas |
| Error de negocio | `useRegister.onError` → `toast.error(message)` con el mensaje público del backend. Ejemplo verificado en el backend: email o documento ya registrados → 409 (`registro_controller.py:44`) |
| Recuperación | ✅ El campo de documento conserva el valor; el usuario puede corregir y reintentar. La búsqueda de DNI **no** revierte los nombres ya escritos: al cambiar el tipo de documento sí se borran (`RegisterForm.tsx:302-310`) |

**Brechas, duplicación y código muerto.**

- 🔴 **`acceptedBases` viaja al backend pero el controlador no lo lee**: `RegistroController.register` pasa los campos de persona y **no** pasa `acceptedBases` al orchestrator (`registro_controller.py:46-60`). La casilla funciona como puerta de UX, no como registro del consentimiento específico: la aceptación que persiste el backend es la de su propio flujo de registro. 🟡 El detalle exacto de qué aceptación se graba requiere leer `RegistroFlujo`.
- 🔴 `telefono`, `whatsapp`, `contactoEmergenciaNombre` y `contactoEmergenciaTelefono` están **declarados en el esquema y enviados como `null`**, pero no hay ningún campo que los capture: el formulario y el contrato backend no están sincronizados. Son campos muertos del lado del cliente.
- 🔴 La **heurística `splitRazonSocial`** del frontend descompone `razon_social` por heurística (coma primero; si no, primer token = apellido). El backend expone el documento completo; la descomposición es una interpretación local que puede asignar mal el orden de los nombres en formatos sin coma.
- 🔴 `features/inscripciones/hooks/useDocumentoLookup.ts` (feature de inscripciones) se usa desde `features/auth/components/RegisterForm.tsx`: dependencia cruzada entre features.
- 🟡 `RegisterClientShell` reproduce el mismo patrón de “chispas” (`SubtleFormSparks`) que `InscripcionClientShell`: ~110 líneas duplicadas de animación decorativa.
- 🟡 `GenericForm` se usa en modo 1 (manual, `children`), conforme al contrato ✅, pero `showErrorsAsToasts` duplica el mensaje en toast **y** bajo el campo.

---

### 5.5 `/dashboard` — Cuenta del responsable

**Ruta y propósito funcional.** Panel del usuario responsable: lista sus inscripciones, muestra el estado de cada una y traduce ese estado a un flujo de 4 pasos (crear → validar por el comité → pagar → inscribir personas). Es el punto de retorno después de crear o pagar.

**Usuario/rol previsto y puntos de entrada.**

- Usuario autenticado con `Persona` asociada (el backend exige `persona_fk_id`; sin él devuelve `BusinessError` 400: `inscripcion_controller.py:59-66`).
- Entradas: “Mi cuenta” del `Navbar`, `resolverDeDestino()` tras login/registro, botón “Volver” del detalle de inscripción, `router.push("/dashboard")` desde `EquiposEmptyState`.

**Secciones visibles y componentes importantes.** ✅ `frontend/src/app/(app)/dashboard/page.tsx` (499 líneas, `"use client"`):

| Zona | Contenido |
|---|---|
| Hero de marca | “Hola, {primer nombre del usuario}!” + botón “Crear Inscripcion” → `/inscripcion` + enlace “Ver el festival” → `/` |
| Diagrama de flujo | `FLOW_STEPS` (4 pasos: Crear inscripción, Validar por el Comité, Completar el pago, Inscribir personas) con `FlowProgress` |
| Panel “Mis Inscripciones” | Tarjetas `InscripcionCard` por inscripción |
| Estado vacío | `EmptyState` → botón “Crear primera inscripcion” → `/inscripcion` |
| Estado de error | Caja rosa con el mensaje de error |

**Acciones del usuario.** Crear una inscripción, abrir el detalle de una inscripción, volver a la portada y consultar su estado.

**Guardas, prerrequisitos y destinos.**

- ✅ `proxy.ts` exige cookie de acceso; `app/(app)/layout.tsx` exige `USER_SESSION`.
- ✅ Destinos: `/inscripcion`, `/dashboard/inscripcion/{id}`, `/`.

**Estado, hooks, formularios, esquemas y servicios.**

| Elemento | Ubicación | Detalle |
|---|---|---|
| `getMisInscripciones()` | `features/inscripciones/services/inscripcion.service.ts:107` | `GET /inscripciones/` con axios; devuelve el sobre `ApiResponse<InscripcionOut[]>` **sin validar en ejecución** (estilo B) |
| `useAuthUser()` | `features/auth/store/auth.store.ts` | Nombre del usuario para el saludo (no es autoridad) |
| `useState` ×3 + `useEffect` | `app/(app)/dashboard/page.tsx:376-396` | `inscripciones`, `loading`, `error`; la carga se dispara en un `useEffect` con array de dependencias `[]` |
| `ESTADO_META` | `app/(app)/dashboard/page.tsx:47-122` | Tabla de 8 estados del backend (`BORRADOR`, `RECIBIDA`, `EN_REVISION`, `OBSERVADA`, `VALIDADA`, `CONFIRMADA`, `RECHAZADA`, `CANCELADA`) con etiqueta, descripción, color, icono y `stepIndex` (1..4) |
| `FLOW_STEPS` | `app/(app)/dashboard/page.tsx:124-145` | Los 4 pasos del recorrido |
| `InscripcionCard`, `FlowProgress`, `EmptyState` | **Definidos dentro del archivo de ruta** (líneas 147-371) | Componentes privados de la página |

**Endpoints backend consumidos.**

| Endpoint | Request | Respuesta usada | Por qué |
|---|---|---|---|
| `GET /api/inscripciones/` | — (JWT) | `id`, `estado`, `created_at`, `paquete_nombre`, `promocion_nombre`, `cantidad_equipos`, `cantidad_participantes` | Lista las inscripciones del responsable y su estado |

**Cadena de ejecución backend (verificada).**

`GET /inscripciones/` → `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py:155` `InscripcionController.listar_mis_inscripciones` (`auth=JWTAuth()`) → `_get_authenticated_persona_id(request)` (lee `request.user.persona_fk_id`; sin él, `BusinessError`) → `InscripcionOrchestrator.listar_por_responsable_proceso` (`inscripcion_orchestrator.py:172`) → `InscripcionSelector.get_by_responsable` (consulta `inscripciones` del responsable) → `InscripcionPresenter.present_inscripcion` por cada elemento → `success_response(..., message="Inscripciones encontradas.")`.

**Modelos y tablas leídos.** `inscripciones` (del responsable) y las relaciones que el presenter usa para el nombre de paquete/promoción y los contadores de equipos y participantes (`equipos`, `participaciones`, `paquetes`, `promociones`). **Ninguna escritura.**

**Comportamiento de estados.**

| Estado | Comportamiento verificado |
|---|---|
| Carga | Spinner + “Cargando inscripciones...” (`page.tsx:463-470`) |
| Vacío | `EmptyState` con CTA a `/inscripcion` |
| Éxito | Tarjetas por inscripción; el diagrama de flujo se posiciona con el estado de **la primera** inscripción (`inscripciones[0]?.estado`) |
| Validación | No aplica |
| Error de negocio | Si el sobre llega con `success === false` → `error = res.error?.message ?? "Error al cargar inscripciones"`; si la petición lanza → `"Error de conexion"`. Ambos pintan una caja rosa **sin botón de reintento** |
| Recuperación | 🔴 **No hay recuperación**: el `useEffect` corre una sola vez (dependencias `[]`); el usuario debe recargar la página a mano |

**Brechas, duplicación y código muerto.**

- 🔴 **Violación de `contract/next-app-architecture-contract.md` §1 y §8**: lógica de negocio, carga de datos y componentes dentro de `app/`. La página más difícil de rediseñar de todo el árbol no administrativo.
- 🔴 **`useEffect` + `useState` para la carga inicial** (prohibido por §8): no usa TanStack Query, no hay caché, no hay reintento y no hay invalidación. El mismo dato ya existe en el cliente HTTP canónico.
- 🔴 **El diagrama de flujo depende de `inscripciones[0]`**: con varias inscripciones, el progreso mostrado es el de la primera, no el de la que el usuario está mirando. Es información engañosa.
- 🔴 **El estado del diagrama usa `"PENDIENTE"` como valor por defecto** (`page.tsx:434`), que **no es un estado de inscripción** (los estados reales son `BORRADOR`, `RECIBIDA`, `EN_REVISION`, `OBSERVADA`, `VALIDADA`, `CONFIRMADA`, `RECHAZADA`, `CANCELADA`). `ESTADO_META["PENDIENTE"]` no existe → `meta` es `undefined` → `currentStep = 1`. La página acepta estados que el backend nunca emite.
- 🔴 **El texto de `RECHAZADA`/`CANCELADA` no es accionable**: “Contacta al Comite” sin enlace, sin teléfono y sin canal. La página no ofrece ninguna salida al usuario en esos dos estados.
- 🔴 **Error de red con mensaje en inglés y fuera del catálogo público**: `"Error de conexion"` y `"Error al cargar inscripciones"` están **hardcodeados en el componente**, en contra del contrato §5 (los componentes no manejan lógica de error cruda) y de la política de mensajes públicos del backend.
- 🔴 `ESTADO_META` **duplica el vocabulario de estados** que el backend expone en `EstadoInscripcionChoices`: una segunda fuente de verdad para el ciclo de vida de la inscripción.
- 🟡 `InscripcionOut` declara `paquete_nombre`/`promocion_nombre`/`cantidad_equipos`/`cantidad_participantes` como opcionales; si el backend no los envía, la tarjeta los oculta sin avisar.

---

### 5.6 `/dashboard/inscripcion/[id]` — Detalle de inscripción

**Ruta y propósito funcional.** Pantalla operativa de una inscripción: estado y progreso, resumen de pago, equipos y roster, pool de participantes preinscritos, alta de personas y pago. Es la pantalla con más superficie funcional del alcance.

**Usuario/rol previsto y puntos de entrada.**

- Responsable de la inscripción o administrador Django (`is_staff`/`is_superuser`). El backend aplica `check_ownership_or_admin(request, inscripcion_id)` en cada endpoint.
- Entradas: clic en una tarjeta de `/dashboard`; redirección post-creación (`useCreateInscripcionCompleta.onSuccess` → `/dashboard/inscripcion/{inscripcion_id}`).

**Secciones visibles y componentes importantes.** ✅ `features/inscripciones/views/InscripcionDetailView.tsx`:

| Zona | Componente | Función |
|---|---|---|
| Barra superior | botón “Volver” → `/dashboard` | Navegación |
| Cabecera | `InscripcionHero` | Evento, paquete, promoción, fecha |
| Estado | `EstadoProgresoCard` | Estado, significado, barra de progreso y checklist; scroll a equipos |
| Pago | `PaymentCallout` | Único punto de pago de la página; se habilita según `resumen_pago` y `estado` (`utils/pago.estado.ts::puedeIniciarPago`) |
| Pool | `PoolParticipantesSeccion` + `PoolParticipanteCard` | Personas preinscritas sin equipo; CTA “Agregarme al pool” y “Asignar” |
| Equipos | `EquipoCard` por equipo (expandible) | Roster por equipo, contador de faltantes, acciones de asignar/editar/retirar |
| Columna lateral | `ResumenPagoCard` (compacta) + `DatosInscripcionCard` | Dinero y datos de la inscripción |
| Modales | `SelectorParticipanteModal`, `AddParticipanteModal`, `EditParticipanteModal`, `IzipayModal` | Asignación, alta, edición y pago |

**Acciones del usuario.**

1. Agregarse a sí mismo al pool.
2. Agregar otra persona al pool (preinscripción, sin equipo).
3. Asignar una persona del pool a un equipo.
4. Editar un participante (rol, talla, aseguradora, notas).
5. Retirar (eliminar) un participante.
6. Pagar la compra pendiente (Izipay).

**Guardas, prerrequisitos y destinos.**

- ✅ `proxy.ts` (cookie) + `app/(app)/layout.tsx` (`USER_SESSION`).
- ✅ Backend: `JWTAuth()` + `check_ownership_or_admin` por endpoint.
- Destinos: `/dashboard` (volver), modal de pago (Izipay).

**Estado, hooks, formularios, esquemas y servicios.**

| Elemento | Ubicación | Clave de caché / detalle |
|---|---|---|
| `useInscripcionDetalle(id)` | `hooks/useInscripcionDetalle.ts` | `["inscripcion-detalle", id]`, `staleTime` 30 s, `gcTime` 5 min |
| `useInscripcionPool(id)` | `hooks/useInscripcionPool.ts` | `["inscripcion-pool", id]` |
| `useInscripcionSaldo(id)` | `hooks/useInscripcionPool.ts` | `["inscripcion-saldo", id]` |
| `useElegiblesEquipos(id, equipoIds[])` | `hooks/useElegiblesEquipo.ts` | `useQueries` sobre `["inscripcion-elegibles", id, equipoId]` — **una consulta por equipo**, prefetch de la matriz persona × equipo |
| `useElegiblesEquipo(id, equipoId)` | `hooks/useElegiblesEquipo.ts:61` | La misma clave: el modal abre sin loading |
| `usePreregistrarEnPool(id)` | `hooks/usePreregistrarEnPool.ts:30` | Invalida pool, detalle, saldo y elegibles |
| `useAsignarParticipanteAEquipo(id)` | `hooks/useAsignarParticipanteAEquipo.ts:99` | Optimista con rollback: quita del pool y añade al roster, y en error restaura los snapshots |
| `useEditarParticipante(id, participanteId)` | `hooks/useEditarParticipante.ts:22` | Actualiza la caché en sitio con el `ParticipanteOut` del backend |
| `useInscripcionCacheSync(id)` | `hooks/useInscripcionCacheSync.ts:105` | `invalidate()` barre detalle + pool + saldo + elegibles |
| `eliminarParticipante()` | `services/inscripcion.service.ts:353` | `PATCH /participaciones/{id}/retirar` |
| `buildPreregistroPayload` / `buildPreregistroSelfPayload` | `utils/pool.preregistro.ts` | Construyen el payload de preinscripción |
| `compraPagableId(resumen_pago)` | `utils/pago.estado.ts` | Deriva la compra pagable del resumen comercial |
| `IzipayModal` | `features/pagos/components/IzipayModal.tsx` | Único componente que habla con la pasarela |
| Formularios | `participante.schema.ts`, `participanteEdit.schema.ts` | Alta y edición de participante |

**Endpoints backend consumidos.**

| # | Endpoint | Campos de request | Respuesta usada | Por qué |
|---|---|---|---|---|
| 1 | `GET /api/inscripciones/{id}/detalle` | — | `equipos[]` (con `participantes[]`, `estado_roster`, `jugadores_registrados`, `minimo_deportivo`, `faltantes`), `personas[]`, `resumen_equipos`, `resumen_pago`, `resumen_participantes`, `estado`, `paquete_nombre`, `promocion_nombre`, `delegado_nombre` | Fuente única del estado de la inscripción |
| 2 | `GET /api/inscripciones/{id}/pool` | — | `pool[]` con `persona`, `tiene_cupo_activo`, `estado_pool` (`LISTO`/`ESPERANDO_PAGO`/`SIN_CAPACIDAD`/`CUPO_POR_ASIGNAR`), `motivo_bloqueo` | Quién espera y por qué no puede entrar |
| 3 | `GET /api/inscripciones/{id}/saldo` | — | `contratados`, `pagados`, `asignados_pagados`, `disponibles_pagados` | Capacidad pagada libre |
| 4 | `GET /api/inscripciones/{id}/equipos/{equipoId}/elegibles` | — | `elegibles[]` con `asignable`, `motivo_no_asignable`, `disciplinas_asignadas[]`, `ya_en_disciplina` | Veredicto del backend por equipo: el frontend no decide elegibilidad |
| 5 | `POST /api/inscripciones/{id}/personas` | `persona_id` **o** `persona_data{tipo_documento,numero_documento,nombres,apellidos,genero,…}` (XOR), `aceptaciones[]` (`BASES`/`APTITUD_FISICA`/`IMAGEN`) | `participante{id,inscripcion_id,persona,estado}` | Preinscripción: crea la `InscripcionPersona` sin equipo |
| 6 | `POST /api/inscripciones/{id}/pool/asignar` | `inscripcion_persona_id`, `equipo_id`, `rol` (def. `J`), `talla_camiseta`, `notas` | `participante` | Colocar una persona en un equipo (transaccional) |
| 7 | `PATCH /api/participaciones/{participacionId}` | `rol`, `talla_camiseta`, `aseguradora_nombre`, `aseguradora_numero_poliza`, `notas` | `ParticipanteOut` | Editar datos de un jugador |
| 8 | `PATCH /api/participaciones/{participacionId}/retirar` | — | `{ participante_id }` | Retirar (no borrar) |
| 9 | `POST /api/compras/{compraId}/iniciar-pago` | — | `token`, `merchant_code`, `amount`, `currency`, `order_number`, `transaction_id`, `buyer_*` | Abrir la pasarela con datos derivados por el backend |
| 10 | `POST /api/pagos/izipay/confirmar` | `{ kr_answer: <payload del proveedor> }` | `success`, `response_message`, `settlement_status` | Verificar el pago; **el backend liquida la operación comercial** |
| 11 | `GET /api/pagos/transacciones/{transactionId}` | — | estado de la transacción | Canal de **recuperación** cuando el relay es incierto |

**Cadena de ejecución backend (verificada).**

| Endpoint | Controller | Orchestrator / Flow / Selector | Presenter |
|---|---|---|---|
| `GET /inscripciones/{id}/detalle` | `inscripcion_controller.py:192` `obtener_inscripcion_detalle` | `InscripcionOrchestrator.obtener_inscripcion_detalle_proceso` (`:94`) → `InscripcionSelector` | `InscripcionPresenter.present_inscripcion_detail` (incluye `resumen_pago`, `resumen_equipos`, `resumen_participantes`) |
| `GET /inscripciones/{id}/pool` | `inscripcion_controller.py:327` `obtener_pool` | `InscripcionOrchestrator.obtener_pool_proceso` (`:176`) → `InscripcionSelector.get_pool` | `InscripcionPresenter.present_pool` |
| `GET /inscripciones/{id}/saldo` | `asignacion_controller.py:221` `InscripcionSaldoController.obtener_saldo` | `AsignacionOrchestrator.obtener_saldo` (`asignacion_orchestrator.py:82`) → `AsignacionCoreService.calcular_saldo_inscripcion` (servicio **síncrono**; el orchestrator lo envuelve, porque no envolverlo lo convertía en un 500) | `AsignacionPresenter.present_saldo` |
| `GET /inscripciones/{id}/equipos/{equipoId}/elegibles` | `inscripcion_controller.py:350` | `InscripcionOrchestrator.obtener_elegibles_equipo_proceso` (`:184`) → `InscripcionSelector.get_elegibles_equipo` | `InscripcionPresenter.present_elegibles_equipo` |
| `POST /inscripciones/{id}/personas` | `inscripcion_controller.py:240` `agregar_persona` | `InscripcionOrchestrator.agregar_persona_proceso` (`:100`) → `AgregarPersonaFlujo` (`flujos/agregar_persona_flujo.py`) | `InscripcionPresenter.present_inscripcion_persona` |
| `POST /inscripciones/{id}/pool/asignar` | `inscripcion_controller.py:378` `asignar_a_equipo` | `InscripcionOrchestrator.asignar_a_equipo_proceso` (`:202`) → `ParticipacionCoreService` (transacción: cupo, R11, roster, deadline) | `InscripcionPresenter.present_participacion` |
| `PATCH /participaciones/{id}` | `inscripcion_controller.py:635` `ParticipacionController` | `ParticipacionOrchestrator` → servicio core | `InscripcionPresenter.present_participacion` |
| `PATCH /participaciones/{id}/retirar` | `inscripcion_controller.py:597` | `ParticipacionOrchestrator` / `RetirarPersonaFlujo` | `InscripcionPresenter.present_participacion` |
| `POST /compras/{compraId}/iniciar-pago` | `compra_controller.py:228` `iniciar_pago` | `CompraOrchestrator.iniciar_pago` (`compra_orchestrator.py:53`) → `IniciarPagoFlujo` (`flujos/iniciar_pago_flujo.py`) | `CompraPresenter` |
| `POST /pagos/izipay/confirmar` | `pagos_controller.py:102` `confirmar_pago` | `PagosOrchestrator.confirmar_pago_izipay` (`pagos_orchestrator.py:66`) → `ConfirmarPagoFlujo` / `RegistrarPagoIzipayFlujo` | `IzipayPresenter.present_confirm` |
| `GET /pagos/transacciones/{txId}` | `pagos_controller.py:180` | `PagosOrchestrator.obtener_transaccion` (`:110`) | `IzipayPresenter.present_transaccion` |

**Modelos y tablas leídos o escritos.**

| Operación | Modelos / tablas |
|---|---|
| Lectura | `inscripciones`, `equipos`, `participaciones`, `inscripciones_personas`, `asignaciones_cupo`, `commerce_compra` + `salesianos_fest_compra_inscripcion`, `pagos_ordendago` (`OrdenPago`), `pagos_transaccionpago` (`TransaccionPago`), `paquetes`, `promociones`, `usuarios_persona` |
| Escritura (preinscripción) | `inscripciones_personas` (+ `usuarios_persona` cuando el backend hace *upsert* por `(tipo_documento, numero_documento)`) y aceptaciones (`aceptaciones_inscripcion`) |
| Escritura (asignación) | `participaciones` y `asignaciones_cupo` (consumo de cupo pagado) |
| Escritura (pago) | `pagos_ordendago` (estado), `pagos_transaccionpago` (evidencia), `commerce_compra` (estado), `salesianos_fest_compra_inscripcion` |

**Comportamiento de estados.**

| Estado | Comportamiento verificado |
|---|---|
| Carga | `InscripcionSkeleton` mientras `isLoading`. El pool muestra su propio estado (`poolLoading`) y el saldo se carga en paralelo |
| Vacío | `EquiposEmptyState` si `inscripcion.equipos.length === 0` (con botón de vuelta a `/dashboard`); el pool vacío lo resuelve `PoolParticipantesSeccion` con guía (`utils/pool.primero.ts`) |
| Éxito | Estados reales del backend: `estado`, `resumen_pago`, `resumen_equipos`, `resumen_participantes`; los equipos se expanden por defecto en la primera carga (`useEffect` que mapea `expandedEquipos`) |
| Validación | Formularios con Zod (`participante.schema.ts`, `participanteEdit.schema.ts`). `AddParticipanteModal` exige documento; `SelectorParticipanteModal` deshabilita a quien el backend marca `asignable === false` y muestra `motivo_no_asignable` |
| Error de negocio | 🟡 El mensaje del backend se muestra como toast (`notify.error`/`toast.error`). En el pool, `poolError` se pinta como bloque de error con su `message`. En la asignación, el rollback restaura el estado previo y luego invalida |
| Recuperación | ✅ **La mejor cadena de recuperación del alcance**: (a) `IzipayModal` sondea `GET /pagos/transacciones/{id}` con polling acotado cuando el relay del proveedor es incierto; (b) el rollback optimista de la asignación; (c) `cache.invalidate()` tras cada mutación; (d) `InscripcionErrorState` con botón de reintento (`refetch()`) cuando falla la carga del detalle |

**Brechas, duplicación y código muerto.**

- 🔴 **`GET /inscripciones/{id}/saldo` se consulta una vez al cargar** y solo se refresca cuando `cache.invalidate()` lo barre. Tras el pago sí se invalida (`IzipayModal.onSuccess → cache.invalidate` ✅), pero cualquier otro camino de pago (pago manual del comité) no invalida desde el cliente, porque esa vía está en la administración: el saldo puede quedar desactualizado en pantalla.
- 🔴 **`useElegiblesEquipos` lanza una consulta por equipo** (N+1 de red): con 4 equipos son 4 peticiones a `/elegibles` en cada carga del detalle. El backend ya devuelve el roster y el pool; la matriz completa por equipo se pide equipo por equipo.
- 🔴 **La preinscripción puede duplicar personas**: `AddParticipanteModal` acepta datos en línea (`persona_data`) y el backend hace *upsert* por documento; si el documento ya existe con otra `Persona`, la UI no avisa.
- 🟡 `handleRemoveParticipante` usa `window.confirm()` (línea 173): un `confirm` nativo dentro de una app con diseño propio; y **no hay modal de confirmación** (`components/confirmationDialog/` existe en el árbol y no se usa aquí).
- 🟡 La eliminación llama `eliminarParticipante` **sin `await`** (cadena `.then().catch()`) mientras el resto de la vista usa `async/await`: dos estilos de control de flujo en la misma función.
- 🟡 `InscripcionDetailView` mezcla 4 modales controlados por 6 `useState` distintos (`selectorEquipo`, `selectorCandidatoId`, `addPoolOpen`, `editingParticipante`, `editingEquipo`, `paymentModalOpen`): el estado de UI de la pantalla es el más voluminoso del alcance.
- 🟡 `AddParticipanteModal` y `EditParticipanteModal` importan de `components-app/**` (`AppFormModal`), que está en el `exclude` de `tsconfig.json` pero es dependencia viva (brecha FE-7 de [`03-frontend.md`](./03-frontend.md)).

---

### 5.7 `/inscripcion` — Preinscripción deportiva (wizard)

**Ruta y propósito funcional.** Flujo de 3 pasos para **crear** una inscripción deportiva de forma atómica: elegir paquete y cantidad, elegir promoción y crear los equipos, y aceptar las declaraciones. Envía una sola operación que crea inscripción + compra inicial + equipos + orden de pago.

**Usuario/rol previsto y puntos de entrada.**

- Usuario autenticado con `Persona` (el backend deriva `responsable_id` del JWT; sin `persona_fk_id` → `BusinessError`).
- Entradas: `ENLACES.registro` (`/inscripcion`) desde la portada y el cierre; “Inscribir equipo” del `Navbar`; “Crear Inscripcion” y “Crear primera inscripcion” del dashboard; `registrationHref` del `Navbar` cuando hay sesión.

**Secciones visibles y componentes importantes.** ✅ `features/inscripciones/components/InscripcionWizard.tsx`:

| Paso | Contenido | Componentes |
|---|---|---|
| Indicador | 3 pasos: Paquete → Equipos → Declaraciones | `STEPS` |
| Banner | `InfoBanner` con el texto del paso | — |
| **Paso 1 – Paquete** | Tarjetas de paquetes con tabs `PACK`/`DISCIPLINA`, stepper de cantidad y precio calculado | `SmartPaqueteCardsField` → `PaqueteComercialCard` |
| **Paso 2 – Equipos** | Select de promoción (buscable), select de fusión (opcional) y creación de equipos por disciplina | `SmartSearchableSelectField`, `EquiposStepLayout`, `SmartEquipoField` |
| **Paso 3 – Declaraciones** | 3 casillas: bases, aptitud física, imagen | `StepDeclarations` |
| Navegación | “Anterior” / “Siguiente” / “Enviar inscripción” | `GenericForm` |

**Acciones del usuario.**

1. Elegir paquete (y tab por tipo).
2. Subir/bajar la cantidad (mínimo = `cantidad_minima_compra` del paquete).
3. Elegir promoción y, opcionalmente, fusión de promoción.
4. Crear un equipo por disciplina del paquete (nombre + disciplina; la categoría queda `null`).
5. Marcar las 3 declaraciones.
6. Enviar.

**Guardas, prerrequisitos y destinos.**

- ✅ `proxy.ts` + `app/(app)/layout.tsx`.
- ✅ Backend: `JWTAuth()`.
- Destinos: éxito → `/dashboard/inscripcion/{inscripcion_id}`; error `PRECIO_CAMBIO` → permanece en el wizard.

**Estado, hooks, formularios, esquemas y servicios.**

| Elemento | Ubicación | Detalle |
|---|---|---|
| `usePaquetes()` | `hooks/useInscripcionCatalogs.ts:49` → `services/paquete.service.ts::fetchPaqueteList` | `["inscripcion","paquetes"]`, `staleTime` 5 min; **valida con Zod** (`PaqueteListContractSchema`) y, ante desajuste, registra el error y devuelve el payload crudo |
| `usePromociones()` | `hooks/useInscripcionCatalogs.ts:113` → `services/catalog.service.ts::getPromociones` | `["inscripcion","promociones"]`; estilo B (genérico de TypeScript, **sin validación en ejecución**) |
| `useCotizacion()` | `hooks/useCotizacion.ts:22` | Estado **local** (`useState`), no caché de TanStack Query. Guardia de secuencia (`requestSeq`) para que solo la respuesta más reciente escriba |
| `SmartPaqueteCardsField` | `components/smart-fields/SmartPaqueteCardsField.tsx` | Debounce de 400 ms antes de cotizar; publica `precio_unitario_cotizado` y `cotizacion_version` al formulario **solo** si la cotización coincide en paquete y cantidad |
| `SmartEquipoField` | `components/smart-fields/SmartEquipoField.tsx` | Deriva el catálogo de disciplinas del paquete seleccionado; **no** hace fetch |
| `useCreateInscripcionCompleta()` | `hooks/useCreateInscripcionCompleta.ts:52` | `POST /inscripciones/completa/` con `estado: "BORRADOR"` fijo |
| `InscripcionFormSchema` | `schemas/inscripcion.schema.ts:95` | `paquete_id`, `promocion_id`, `fusion_promocion_id?`, `equipos[]` (mínimo 1), `cantidad?`, `precio_unitario_cotizado?`, `cotizacion_version?` |
| `EquipoSchema` | `schemas/inscripcion.schema.ts:82` | `disciplina_id`, `categoria_id?`, `nombre` (1–120), `participantes[]` |
| `toBackendPayload()` | `schemas/inscripcion.schema.ts:150` | 🔴 Función **sin uso**: el wizard construye el payload atómico en `useCreateInscripcionCompleta`, no aquí |
| `GenericForm` | `components/genericForm/GenericForm.tsx` | Modo 1 (manual) ✅ |
| `usePaqueteDetail`, `usePaqueteDisciplinas`, `useDisciplinas`, `useCategorias` | `hooks/useInscripcionCatalogs.ts` | 🔴 **No los usa ninguna pantalla**: código muerto (§8) |

**Endpoints backend consumidos.**

| Endpoint | Campos de request | Respuesta usada | Por qué |
|---|---|---|---|
| `GET /api/catalogo/paquetes/` | — | Lista con `cantidad_minima_compra`, `cantidad_disciplinas`, `modo_disciplinas`, `disciplinas[]`, `precios[]` | Las tarjetas de paquete y la derivación de los equipos |
| `GET /api/catalogo/promociones/` | — | `id`, `nombre`, `anio` | Select de promoción y de fusión |
| `POST /api/cotizaciones/` | `{ paquete_id, cantidad }` | `paquete_id`, `cantidad_cotizada`, `precio_unitario`, `total`, `version`, `estado` | Precio de referencia que el usuario ve antes de enviar |
| `POST /api/inscripciones/completa/` | `evento_id`, `paquete_id`, `promocion_id`, `fusion_promocion_id`, `delegado_id` (null), `cantidad`, `equipos[{disciplina_id,categoria_id,nombre}]`, `estado` (`BORRADOR`), `observacion` (""), `precio_unitario_cotizado`, `cotizacion_version` | `inscripcion_id`, `inscripcion_estado`, `compra_id`, `orden_pago_id`, `compra_estado`, `cantidad`, `precio_unitario`, `total`, `equipos[]` | Crear atómicamente inscripción + compra + equipos + orden de pago |

**Cadena de ejecución backend (verificada).**

| Endpoint | Controller | Orchestrator / Flow | Selector / Presenter |
|---|---|---|---|
| `GET /catalogo/paquetes/` | `catalogo_controller.py:75` | — (solo selector) | `PaqueteSelector.get_activos` → `CatalogoPresenter.present_paquetes` |
| `GET /catalogo/promociones/` | `catalogo_controller.py:49` | — | `PromocionSelector.get_activas` → `CatalogoPresenter.present_promociones` |
| `POST /cotizaciones/` | `cotizacion_controller.py:32` (`auth=None`) | `CotizacionFlujo.cotizar` (`flujos/cotizacion_flujo.py:54`) | Devuelve directamente el `CotizacionResponse` (no persiste nada) |
| `POST /inscripciones/completa/` | `inscripcion_controller.py:104` (`auth=JWTAuth()`) | `InscripcionOrchestrator.crear_inscripcion_completa_proceso` (`:55`) → `CrearInscripcionCompletaFlujo` (`flujos/crear_inscripcion_completa_flujo.py:88`) | `InscripcionPresenter.present_equipo` por equipo; el resultado lo arma el controller (`InscripcionCompletaOut`) |

**Modelos y tablas leídos o escritos.**

| Operación | Modelos / tablas |
|---|---|
| Lectura | `paquetes`, `paquetes_precios`, `paquetes_disciplinas`, `paquetes_beneficios`, `promociones` |
| Escritura | `inscripciones` (estado `BORRADOR`), `equipos`, `commerce_compra` (tipo `INICIAL`, estado `PENDIENTE`), `salesianos_fest_compra_inscripcion`, `pagos_ordendago` (`OrdenPago` `PENDIENTE`) |

**Efectos secundarios del alta.** ✅ El roster **no** se crea en este paso: la inscripción nace sin personas y el usuario las agrega después desde el detalle. Los consentimientos del wizard **no** se envían: el backend registra las aceptaciones **por persona** en `POST /inscripciones/{id}/personas`.

**Comportamiento de estados.**

| Estado | Comportamiento verificado |
|---|---|
| Carga | Paso 1: 3 esqueletos de tarjeta (`Skeleton`) mientras `usePaquetes` vuela. Paso 2: el select de promoción se deshabilita mientras `promocionesQuery.isLoading` |
| Vacío | Paso 1: “No hay paquetes disponibles para este filtro.” cuando el tab no tiene paquetes; el tab vacío se deshabilita automáticamente y se salta al primero con datos |
| Éxito | `toast.success(message)` (mensaje del backend) y `router.push(/dashboard/inscripcion/{id})` |
| Validación | Zod por paso: `stepFields` marca `paquete_id` (paso 1) y `promocion_id` + `equipos` (paso 2). “Siguiente” dispara `methods.trigger(fields)` y, si falla, muestra “Completa los campos obligatorios antes de continuar”. **Paso 3**: las 3 declaraciones se validan **manualmente** en `onSubmit` (“Debes aceptar las 3 declaraciones para continuar”) |
| Error de negocio | 🔴 Caso específico verificado: el backend puede responder `PRECIO_CAMBIO`; el hook lo traduce a un toast de 8 s con el nuevo total y pide recalcular. Otros errores: `toast.error(message)` del backend |
| Recuperación | ✅ El usuario puede volver atrás y corregir (el estado del formulario se conserva); el paso 1 mantiene el paquete y la cantidad; al cambiar de paquete se invalidan `precio_unitario_cotizado` y `cotizacion_version` |

**Brechas, duplicación y código muerto.**

- 🔴 **Dos clientes del mismo endpoint de paquetes**: `paquete.service.fetchPaqueteList` (Zod, `["inscripcion","paquetes"]`) y `landing/paquetes.service.fetchPaquetes` (sin Zod, `["landing","paquetes"]`) → **doble descarga del mismo catálogo** en el navegador y dos espacios de caché sin invalidación cruzada.
- 🔴 **Dos hooks homónimos** `useDisciplinas`/`useCategorias` en `features/portada/hooks/useCatalogo.ts` y `features/inscripciones/hooks/useInscripcionCatalogs.ts`: el segundo juego **no lo usa nadie**.
- 🔴 **Código muerto verificado en `features/inscripciones/hooks/useInscripcionCatalogs.ts`**: `usePaqueteDetail` (`:28`), `usePaqueteDisciplinas` (`:60`), `useDisciplinas` (`:79`), `useCategorias` (`:96`) — ninguna pantalla los importa. Con ellos quedan sin uso los servicios `paquete.service.fetchPaqueteDetail`, `catalog.service.getPaqueteDisciplinas`, `catalog.service.getDisciplinas`, `catalog.service.getCategorias` y `catalog.service.getPaquetes` (este último, además, con la interfaz `Paquete` marcada `@deprecated`).
- 🔴 `toBackendPayload()` (`schemas/inscripcion.schema.ts:150`) no lo usa nadie: el payload atómico se arma dentro del hook, contra la convención de `schemas/`.
- 🔴 **Los consentimientos del wizard no se persisten**: el usuario marca 3 casillas y la inscripción se crea sin registro de esas aceptaciones; el backend solo las registra cuando se agrega cada persona. La casilla “Acepto las bases” del wizard es una puerta de UX sin valor probatorio.
- 🔴 `SmartPaqueteCardsField` **duplica** `usePaquetes()` y el wizard también lo llama: tres instancias de la misma query (`InscripcionWizard`, `StepDeclarations`, `SmartPaqueteCardsField`) que comparten clave y caché, pero multiplican los hooks y la superficie de invalidación.
- 🔴 `useCotizacion` guarda la cotización en `useState` local y no en TanStack Query: al navegar fuera del wizard y volver, la cotización se pierde y hay que recotizar (400 ms de debounce por cada cambio de paquete o cantidad).
- 🟡 `StepDeclarations` vuelve a pedir `usePaquetes()` para mostrar los datos del paquete en el resumen del paso 3: coste de hook, no de red (misma clave de caché).
- 🟡 `InscripcionFormSchema` declara `precio_unitario_cotizado` y `cotizacion_version` como **campos de formulario** que en realidad son metadatos de negocio escritos por un componente lateral: mezcla de responsabilidades dentro del esquema Zod del formulario.

---

### 5.8 `/pases` — Compra de pases de fiesta

**Ruta y propósito funcional.** Flujo dedicado (independiente del wizard deportivo) para comprar un lote de pases de fiesta nominativos: elegir pase y cantidad → registrar la compra → pagar con Izipay → asignar las personas que usarán los pases.

**Usuario/rol previsto y puntos de entrada.**

- Usuario autenticado con `Persona` (el backend exige `responsable_id`; `PaseController.comprar_pases` lee `request.user.persona_fk_id`).
- Entradas: “Comprar pase de fiesta” del `Navbar` → `/pases` si hay sesión, `/register` si no (`components/landing/Navbar.tsx:50`).

**Secciones visibles y componentes importantes.** ✅ `features/pases/views/PaseCompraView.tsx`:

| Zona | Contenido |
|---|---|
| Cabecera | Título y explicación: “El pase da acceso nominativo a la fiesta, sin inscripción deportiva. El precio lo fija el servidor.” |
| Catálogo | `PaseCatalogoCard` por pase; selección + cantidad (`PaseCantidadPanel`) |
| Acción | “Continuar al pago” (submit de `GenericForm`) |
| Resultado | `PaseCompraResultado`: número de orden, nombre del pase, cantidad, unitario, total, moneda, estados, origen de pago, beneficiarios asignados/pendientes, y botón de pago |
| Reset | “Comprar otro pase” |
| Panel de beneficiarios | `PaseBeneficiariosPanel` (solo cuando la compra está `PAGADA`): contadores de slots, `PaseLookupPersonaField`, `PaseRevocarDialog`, `PaseQrHint` |
| Pago | `IzipayModal` |

**Acciones del usuario.**

1. Elegir pase y cantidad (límite = `min(50, cantidad_maxima)`; `cantidad_maxima === 0` significa inventario ilimitado).
2. Registrar la compra y pasar al pago.
3. Pagar con Izipay.
4. Buscar personas por documento (coincidencia **exacta**) y asignarlas a los slots libres.
5. Revocar un pase asignado (motivo obligatorio y auditado).

**Guardas, prerrequisitos y destinos.**

- ✅ `proxy.ts` + `app/(app)/layout.tsx` + `JWTAuth()` + `IsAuthenticated` en el backend.
- ✅ Requisito de negocio: la compra debe estar `PENDIENTE` y su orden de pago sin pagar para ser pagable; los beneficiarios solo se gestionan con la compra `PAGADA` (`PaseCompraView.tsx:143-147`).
- Destinos: ninguno interno (flujo cerrado en la misma página); el usuario puede reponer el flujo con “Comprar otro pase”.

**Estado, hooks, formularios, esquemas y servicios.**

| Elemento | Ubicación | Detalle |
|---|---|---|
| `usePasesCatalogo()` | `hooks/usePasesCatalogo.ts:25` | `queryOptions`, clave `["pases","catalogo"]`, `staleTime` 60 s, `gcTime` 5 min |
| `useCrearCompraPase()` | `hooks/useCompraPase.ts:39` | Invalida el catálogo tras comprar (el inventario se mueve) |
| `useCompraPaseEstado(compraId)` | `hooks/useCompraPaseEstado.ts:27` | Clave `["pases","compra",compraId]`, `staleTime` 15 s; **fuente de verdad del estado comercial** tras el pago |
| `useBeneficiariosCompra(compraId)` | `hooks/useBeneficiariosCompra.ts:27` | Clave `["pases","beneficiarios",compraId]`, `staleTime` 15 s |
| `useAsignarBeneficiarios()` | `hooks/useAsignarBeneficiarios.ts:64` | Payload `{ beneficiario_ids: [...] }`; invalida beneficiarios + estado de la compra |
| `useRevocarBeneficiario()` | `hooks/useRevocarBeneficiario.ts` | `DELETE` con `{ motivo }` |
| `useResolverPersona()` | `hooks/useResolverPersona.ts` | `GET /personas/resolver`; el 404 se distingue por `error.status` |
| `paseCompraFormSchema` | `schemas/pase.schema.ts:183` | `pase_id` + `cantidad` (1…50) |
| `paseComprarInSchema` | `schemas/pase.schema.ts:74` | Espejo 1:1 de `PaseComprarIn`; **sin precio**: el navegador nunca manda importes |
| `paseCatalogoEnvelopeSchema`, `paseCompraCreadaEnvelopeSchema`, `paseCompraEstadoEnvelopeSchema` | `schemas/pase.schema.ts` | Espejos Zod 1:1 de los wrappers del backend |
| `PASE_CANTIDAD_MAXIMA_POR_COMPRA = 50` | `utils/pase.precio.ts:23` | Espejo del `CANTIDAD_MAXIMA_POR_COMPRA` del backend |
| `paseComprable`, `paseTotal`, `paseEtapaVigente` | `utils/pase.precio.ts` | Reglas puras que **replican** la resolución de precio del backend |
| `IzipayModal` | `features/pagos/components/IzipayModal.tsx` | Único puente con la pasarela |

**Endpoints backend consumidos.**

| Endpoint | Campos de request | Respuesta usada | Por qué |
|---|---|---|---|
| `GET /api/pases/` | — (público) | `id`, `nombre`, `descripcion`, `activo`, `precio_vigente`, `precio_preventa`, `precio_regular`, `cantidad_maxima`, `precios[]` | Catálogo público de pases comprables |
| `POST /api/pases/comprar` | `{ pase_id, cantidad }` (sin importe) | `compra_id`, `orden_pago_id`, `numero_orden`, `pase_nombre`, `cantidad`, `precio_unitario`, `total`, `estado_compra`, `estado_orden` | Registrar la compra: el servidor **congela** los importes |
| `GET /api/pases/compras/{compraId}` | — | Lo anterior + `moneda`, `origen_pago` (`IZIPAY`/`MANUAL`/`SIN_PAGO`), `created_at`, `beneficiarios_asignados`, `beneficiarios_pendientes` | Estado autoritativo tras el pago |
| `GET /api/pases/compras/{compraId}/beneficiarios` | — | `cantidad_pases`, `activos`, `revocados`, `slots_usados`, `slots_disponibles`, `beneficiarios[]` (con `slot`, `estado`, `motivo_revocacion`) | Contabilidad inmutable de slots |
| `POST /api/pases/compras/{compraId}/beneficiarios` | `{ beneficiario_ids: [...] }` (solo UUIDs) | `beneficiarios` asignados | Asignar personas existentes a los slots libres |
| `DELETE /api/pases/compras/{compraId}/beneficiarios/{personaId}` | `{ motivo }` | Beneficiario revocado | Revocación permanente y auditada |
| `GET /api/personas/resolver` | query: `tipo_documento`, `numero_documento` | `persona_id`, `nombre_completo`, `tipo_documento`, `numero_documento` | Resolver **exactamente** una `Persona` ya registrada (nunca crea personas) |
| `POST /api/compras/{compraId}/iniciar-pago` | — | Token y configuración del SDK | Abrir la pasarela |
| `POST /api/pagos/izipay/confirmar` | `{ kr_answer }` | `success`, `settlement_status`, `response_message` | Verificar el pago |
| `GET /api/pagos/transacciones/{txId}` | — | Estado de la transacción | Recuperación de un relay incierto |

**Cadena de ejecución backend (verificada).**

| Endpoint | Controller | Orchestrator / Flow | Presenter |
|---|---|---|---|
| `GET /pases/` | `pase_controller.py:49` `listar_pases` (`auth=None`) | `PaseOrchestrator.listar_catalogo` (`:57`) → `ListarPasesFlujo` (`flujos/listar_pases_flujo.py`) | `PasePresenter.present_pases` |
| `POST /pases/comprar` | `pase_controller.py:69` `comprar_pases` (`auth=JWTAuth()`) | `PaseOrchestrator.comprar_pases` (`:65`) → `CrearCompraPaseFlujo` (`flujos/crear_compra_pase_flujo.py:64`) | `PasePresenter.present_compra_creada` |
| `GET /pases/compras/{id}` | `pase_controller.py:105` | `PaseOrchestrator.obtener_compra` (`:80`) → `ObtenerCompraPaseFlujo` (`flujos/obtener_compra_pase_flujo.py`) | `PasePresenter.present_compra_estado` |
| `GET /pases/compras/{id}/beneficiarios` | `pase_controller.py:135` | `PaseOrchestrator.listar_beneficiarios` (`:94`) → `ListarBeneficiariosPaseFlujo` | `PasePresenter.present_beneficiarios_lista` |
| `POST /pases/compras/{id}/beneficiarios` | `pase_controller.py` `asignar_beneficiarios` | `PaseOrchestrator.asignar_beneficiarios` (`:108`) → `AsignarBeneficiariosPaseFlujo` (`flujos/asignar_beneficiarios_pase_flujo.py`) | `PasePresenter.present_beneficiarios_asignados` |
| `DELETE /pases/compras/{id}/beneficiarios/{personaId}` | `pase_controller.py` `revocar_beneficiario` | `PaseOrchestrator.revocar_beneficiario` (`:124`) → `RevocarBeneficiarioPaseFlujo` | `PasePresenter.present_beneficiario_revocado` |
| `GET /personas/resolver` | `persona_resolucion_controller.py:60` (`JWTAuth` + `IsAuthenticated`) | `PersonaResolucionOrchestrator.resolver_persona` → `PersonaResolucionFlujo` (`flujos/persona_resolucion_flujo.py`) | `PersonaResolucionPresenter.present_persona` |
| `POST /compras/{id}/iniciar-pago` | `compra_controller.py:228` | `CompraOrchestrator.iniciar_pago` → `IniciarPagoFlujo` | `CompraPresenter` |
| `POST /pagos/izipay/confirmar` | `pagos_controller.py:102` | `PagosOrchestrator.confirmar_pago_izipay` → `ConfirmarPagoFlujo` / `RegistrarPagoIzipayFlujo` | `IzipayPresenter.present_confirm` |
| `GET /pagos/transacciones/{txId}` | `pagos_controller.py:180` | `PagosOrchestrator.obtener_transaccion` | `IzipayPresenter.present_transaccion` |

**Modelos y tablas leídos o escritos.**

| Operación | Modelos / tablas |
|---|---|
| Lectura (catálogo) | `pases`, `pases_precios` |
| Escritura (compra) | `commerce_compra`, `salesianos_fest_compra_pase` (`CompraPase`), `pagos_ordendago` |
| Escritura (beneficiarios) | `pases_beneficiarios` (`PaseBeneficiario`: slot, estado, motivo, auditoría) |
| Lectura (personas) | `usuarios_persona` (coincidencia exacta por `(tipo_documento, numero_documento)`) |
| Escritura (pago) | `pagos_ordendago`, `pagos_transaccionpago`, `commerce_compra` |

**Comportamiento de estados.**

| Estado | Comportamiento verificado |
|---|---|
| Carga | Catálogo: 3 esqueletos (`Skeleton`). Compra: el `useCompraPaseEstado` vuela en segundo plano tras crear la compra |
| Vacío | “Los pases de fiesta todavía no están disponibles.” cuando `catalogo.data.length === 0` (catálogo vacío = despliegue apagado o sin pase activo) |
| Éxito | Se muestra `PaseCompraResultado` con el estado real; tras el pago, `refetchCompra()` trae el estado autoritativo y, si está `PAGADA`, aparece el panel de beneficiarios |
| Validación | `paseCompraFormSchema`: `pase_id` obligatorio y `cantidad` entre 1 y 50. El botón se deshabilita si no hay pase seleccionado. El panel de beneficiarios bloquea si la selección excede los slots libres (“Solo quedan N slot(s) libres”) |
| Error de negocio | `GenericForm` expone `submissionMessage` y la vista lo pinta como bloque rojo con el mensaje del backend; `notify.error` en los hooks de mutación. El 404 de `/personas/resolver` se traduce en “No hay ninguna persona registrada con ese documento” (estado ámbar, no error) |
| Recuperación | ✅ **La más completa del alcance**: (a) `IzipayModal` sondea el estado de la transacción con polling acotado si el relay del proveedor no responde; (b) el estado de la compra se relee del backend después del pago (`refetchCompra`), nunca se infiere en el navegador; (c) los slots revocados **no** se reutilizan (contabilidad inmutable del backend) |

**Brechas, duplicación y código muerto.**

- 🔴 **El precio se resuelve en dos lugares**: `pase.precio.ts` replica `_es_vigente`, la precedencia de etapas y el tope de 50 del backend. El propio archivo lo admite (“The rules MIRROR the backend”). Cualquier cambio de calendario en el backend exige cambiar el frontend en el mismo commit.
- 🔴 **`PaseCompraResultado` y el panel de beneficiarios dependen de dos lecturas distintas** (`/pases/compras/{id}` y `/pases/compras/{id}/beneficiarios`) que el backend calcula de forma independiente: un desajuste entre ambas es posible durante la invalidación.
- 🟡 `PaseLookupPersonaField` usa un `<select>` nativo mientras el resto del proyecto usa el `Select` de shadcn: inconsistencia visual en el mismo formulario.
- 🟡 La revocación consume el slot **para siempre** y no existe flujo de reasignación visible: decisión de negocio correcta, sin salida en la UI.
- 🟡 `pase.precio.ts` mantiene `paseEtapaVigente` y `paseTotal`, que calculan precio y total aunque el documento diga que el navegador nunca calcula el precio: el total de la compra lo devuelve el backend (importes congelados). El código del helper no interviene en el flujo de compra, pero queda disponible como puerta a duplicar la regla.

---

### 5.9 `/api/auth/refresh` — Route handler de refresco de token

**Ruta y propósito.** Proxy de servidor que rota los tokens de sesión. Lo invoca `lib/api.ts` (nunca el usuario directamente).

**Disparador.** ✅ `lib/api.ts:40`: `fetch("/api/auth/refresh", { method: "POST" })` desde el interceptor de axios, de forma (a) proactiva cuando el token expira en menos de 5 minutos y (b) reactiva ante un `401` (con un único reintento de la petición original).

**Guardas y prerrequisitos.** ✅ Sin autenticación propia: se autentica con la **cookie de refresh**. El `matcher` de `proxy.ts` excluye `api`, así que esta ruta no pasa por la cortesía de `proxy.ts`.

**Cadena de ejecución (verificada).**

1. Lee `AUTH_COOKIES.REFRESH_TOKEN` de `cookies()`.
2. `fetch(`${backendInternalUrl()}/token/refresh`, { method: "POST", body: JSON.stringify({ refresh }) })` → controlador JWT de `django-ninja-jwt` (`NinjaJWTDefaultController`, registrado en `backend/config/api.py:104`).
3. Deriva `expires_at` del claim `exp` real del token emitido (`lib/server/jwt.ts::expiracionDeToken`), con fallback de 60 min (`MINUTOS_FALLBACK`) si el token viene malformado.
4. Escribe las cookies `ACCESS_TOKEN`, `REFRESH_TOKEN` (si el backend rota) y `EXPIRES_AT`.
5. Responde `{ success: true, data: { expires_at } }`.

**Modelos y tablas.** No toca la base de datos: solo valida y rota tokens. La rotación **sí** invalida el refresh anterior en el backend (🟡 `ROTATE_REFRESH_TOKENS=True`, según el comentario del propio archivo).

**Comportamiento de estados.**

| Estado | Respuesta verificada |
|---|---|
| Éxito | `200 { success: true, data: { expires_at } }` |
| Error de negocio | `401 { success: false, error: { message: "Refresh token no encontrado" } }` (sin cookie) y `401 … "Refresh fallido"` (el backend rechazó) |
| Error técnico | `500 … "Token de acceso no recibido"` (respuesta 2xx sin `access`) y `500 … "Error interno del servidor"` (excepción) |

**Brechas y duplicación.**

- 🔴 **El comentario del archivo contradice el código**: la línea 88 dice “Set rotated tokens as httpOnly cookies” y la línea 29 dice “sets the rotated tokens as cookies (non-httpOnly for client access)”, pero `lib/auth/cookies.ts:20-25` fija `httpOnly: false` para las cuatro cookies. El token de acceso es legible por cualquier script.
- 🔴 `accessTokenCookieOptions` declara `maxAge: 30 días` para un token que el backend emite con `ACCESS_TOKEN_LIFETIME = 1h`. La cookie sobrevive 30 veces más que el token: el cliente cree que tiene sesión y recibe un `401` real. La cookie de refresh sí está alineada (7 días).
- 🟡 La cookie `EXPIRES_AT` tiene `maxAge: 7 días` aunque el token dure 1 h: `isTokenExpiringSoon()` lee esa cookie y, si el refresco falla, **no puede distinguir** “token expirado” de “cookie vieja”, y reintenta el refresco en cada petición.
- 🟡 El refresco proactivo ocurre **antes** de cada petición cuando `expires_at` está en el pasado; combinado con la cookie de 30 días, un usuario que vuelve tras un mes dispara un refresco inútil en la primera petición.

---

### 5.10 `/api/auth/logout` — Route handler de cierre de sesión

**Ruta y propósito.** Elimina las cookies de sesión del navegador.

**Disparador.** ✅ `components/AppSidebar.tsx:114`: `await fetch("/api/auth/logout", { method: "POST" })`.

**Guardas y prerrequisitos.** ✅ Sin guardas: el handler solo borra cookies.

**Cadena de ejecución (verificada).** `clearAuthCookies()` (`lib/auth/actions.ts:46`) borra `ACCESS_TOKEN`, `REFRESH_TOKEN`, `EXPIRES_AT` y `USER_SESSION`; responde `200 { success: true }`.

**Modelos y tablas.** **Ninguna**. No llama al backend.

**Comportamiento de estados.** Éxito: `{ success: true }`. No hay estado de error: si el borrado falla, el handler lanza y Next.js devuelve un 500 genérico.

**Brechas y duplicación.**

- 🔴 **No hay revocación del refresh token en el backend**: la cookie local se borra, pero el refresh token sigue siendo válido en el servidor hasta que expira (7 días). Un token filtrado antes del logout sigue sirviendo.
- 🔴 **No se limpia el store Zustand**: `auth.store` persiste en `localStorage`, así que el usuario sigue “autenticado” en el cliente tras el logout hasta que la página se recarga. `useAuthUser()` puede seguir devolviendo un usuario en las páginas que lo leen (navbar, dashboard) → el navbar puede seguir mostrando “Mi cuenta”.
- 🔴 **Orphan endpoint**: el logout vive en `components/AppSidebar.tsx`, un componente del área **administrativa**. No hay forma de cerrar sesión desde el alcance no administrativo: el `Navbar` de `/` y `/informacion` no tiene botón de logout.

---

## 6. Trazabilidad: ruta → servicio → endpoint → backend → modelo/tabla

✅ Verificado contra `frontend/src/**` y `backend/modules/**`.

| Ruta | Servicio / hook (frontend) | Endpoint | Controller backend | Orchestrator / Flow / Selector | Presenter | Modelos / tablas |
|---|---|---|---|---|---|---|
| `/` | `features/portada/hooks/useCatalogo.ts::useDisciplinas` | `GET /catalogo/disciplinas/` | `CatalogoController.listar_disciplinas` | `DisciplinaSelector.get_activas` | `CatalogoPresenter.present_disciplinas` | lectura `disciplinas` |
| `/` | `features/portada/hooks/useCatalogo.ts::useCategorias` | `GET /catalogo/categorias/` | `CatalogoController.listar_categorias` | `CategoriaSelector.get_activas` | `CatalogoPresenter.present_categorias` | lectura `categorias` |
| `/` | `features/landing/hooks/useLandingPaquetes.ts` → `features/landing/paquetes.service.ts` | `GET /catalogo/paquetes/` | `CatalogoController.listar_paquetes` | `PaqueteSelector.get_activos` | `CatalogoPresenter.present_paquetes` | lectura `paquetes`, `paquetes_precios`, `paquetes_disciplinas`, `paquetes_beneficios` |
| `/informacion` | idem anterior | `GET /catalogo/paquetes/` | idem | idem | idem | idem |
| `/login` | `features/auth/hooks/useLogin.ts` | `POST /auth/login/dni` | `AuthLoginController.login_dni` | `AuthOrchestrator.login_dni` → `AuthFlujo` | `AuthPresenter.present_login` | lectura `usuarios_usuario`, `usuarios_persona` |
| `/login` | idem | `POST /auth/login/email` | `AuthLoginController.login_email` | `AuthOrchestrator.login_email` → `AuthFlujo` | idem | idem |
| `/login` | idem | `POST /auth/login/username` | `AuthLoginController.login_username` | `AuthOrchestrator.login_username` → `AuthFlujo` | idem | idem |
| `/login` | `features/admin/services/admin.me.service.ts::getAdminMe` | `GET /auth/me` | `AuthMeController.me` | (sin orchestrator) | (presentación en el controller) | lectura `usuarios_usuario`, `usuarios_persona` |
| `/register` | `features/auth/services/register.service.ts::registerUser` | `POST /auth/register` | `RegistroController.register` | `RegistroOrchestrator.registrar` → `RegistroFlujo` | `RegistroPresenter.present_registro` | **escribe** `usuarios_persona`, `usuarios_usuario`, aceptación de bases |
| `/register` | `features/inscripciones/hooks/useDocumentoLookup.ts` → `inscripcion.service.ts::consultarDocumento` | `GET /personas/busqueda/{documento}` | `PersonaBusquedaController.buscar_documento` | `PersonaBusquedaOrchestrator` → `PersonaBusquedaFlujo` | `PersonaBusquedaPresenter.present_documento` | servicio externo (RENIEC/SUNAT); sin escritura local |
| `/dashboard` | `features/inscripciones/services/inscripcion.service.ts::getMisInscripciones` | `GET /inscripciones/` | `InscripcionController.listar_mis_inscripciones` | `InscripcionOrchestrator.listar_por_responsable_proceso` → `InscripcionSelector.get_by_responsable` | `InscripcionPresenter.present_inscripcion` | lectura `inscripciones` + relaciones |
| `/dashboard/inscripcion/[id]` | `inscripcion.service.ts::getInscripcionDetalle` | `GET /inscripciones/{id}/detalle` | `InscripcionController.obtener_inscripcion_detalle` | `InscripcionOrchestrator.obtener_inscripcion_detalle_proceso` | `InscripcionPresenter.present_inscripcion_detail` | lectura `inscripciones`, `equipos`, `participaciones`, `usuarios_persona` |
| `/dashboard/inscripcion/[id]` | `pool.service.ts::getPool` | `GET /inscripciones/{id}/pool` | `InscripcionController.obtener_pool` | `InscripcionOrchestrator.obtener_pool_proceso` → `InscripcionSelector.get_pool` | `InscripcionPresenter.present_pool` | lectura `inscripciones_personas`, `participaciones`, `asignaciones_cupo` |
| `/dashboard/inscripcion/[id]` | `pool.service.ts::getSaldoInscripcion` | `GET /inscripciones/{id}/saldo` | `InscripcionSaldoController.obtener_saldo` | `AsignacionOrchestrator.obtener_saldo` → `AsignacionCoreService.calcular_saldo_inscripcion` | `AsignacionPresenter.present_saldo` | lectura `commerce_compra`, `salesianos_fest_compra_inscripcion`, `asignaciones_cupo` |
| `/dashboard/inscripcion/[id]` | `elegibles.service.ts::getElegiblesEquipo` | `GET /inscripciones/{id}/equipos/{equipoId}/elegibles` | `InscripcionController.obtener_elegibles_equipo` | `InscripcionOrchestrator.obtener_elegibles_equipo_proceso` → `InscripcionSelector.get_elegibles_equipo` | `InscripcionPresenter.present_elegibles_equipo` | lectura `inscripciones_personas`, `participaciones` |
| `/dashboard/inscripcion/[id]` | `pool.service.ts::preregistrarEnPool` | `POST /inscripciones/{id}/personas` | `InscripcionController.agregar_persona` | `InscripcionOrchestrator.agregar_persona_proceso` → `AgregarPersonaFlujo` | `InscripcionPresenter.present_inscripcion_persona` | **escribe** `inscripciones_personas` (+ `usuarios_persona` por upsert) y aceptaciones |
| `/dashboard/inscripcion/[id]` | `pool.service.ts::asignarPoolAEquipo` | `POST /inscripciones/{id}/pool/asignar` | `InscripcionController.asignar_a_equipo` | `InscripcionOrchestrator.asignar_a_equipo_proceso` → `ParticipacionCoreService` | `InscripcionPresenter.present_participacion` | **escribe** `participaciones`, `asignaciones_cupo` |
| `/dashboard/inscripcion/[id]` | `inscripcion.service.ts::editarParticipante` | `PATCH /participaciones/{id}` | `ParticipacionController` (PATCH) | `ParticipacionOrchestrator` | `InscripcionPresenter.present_participacion` | **escribe** `participaciones` |
| `/dashboard/inscripcion/[id]` | `inscripcion.service.ts::eliminarParticipante` | `PATCH /participaciones/{id}/retirar` | `ParticipacionController.retirar` | `ParticipacionOrchestrator` / `RetirarPersonaFlujo` | idem | **escribe** `participaciones` (estado `R`) |
| `/dashboard/inscripcion/[id]`, `/pases` | `features/pagos/services/pago.service.ts::iniciarPagoIzipay` | `POST /compras/{compraId}/iniciar-pago` | `CompraController.iniciar_pago` | `CompraOrchestrator.iniciar_pago` → `IniciarPagoFlujo` | `CompraPresenter` | lectura/escritura `commerce_compra`, `pagos_ordendago`; crea `pagos_transaccionpago` |
| `/dashboard/inscripcion/[id]`, `/pases` | `pago.service.ts::confirmarPagoIzipay` | `POST /pagos/izipay/confirmar` | `PagosController.confirmar_pago` | `PagosOrchestrator.confirmar_pago_izipay` → `ConfirmarPagoFlujo` / `RegistrarPagoIzipayFlujo` | `IzipayPresenter.present_confirm` | **escribe** `pagos_ordendago`, `pagos_transaccionpago`, `commerce_compra` |
| `/dashboard/inscripcion/[id]`, `/pases` | `pago.service.ts::obtenerEstadoTransaccion` | `GET /pagos/transacciones/{txId}` | `PagosController.obtener_transaccion` | `PagosOrchestrator.obtener_transaccion` | `IzipayPresenter.present_transaccion` | lectura `pagos_transaccionpago` |
| `/inscripcion` | `paquete.service.ts::fetchPaqueteList` | `GET /catalogo/paquetes/` | `CatalogoController.listar_paquetes` | `PaqueteSelector.get_activos` | `CatalogoPresenter.present_paquetes` | lectura `paquetes` + relaciones |
| `/inscripcion` | `catalog.service.ts::getPromociones` | `GET /catalogo/promociones/` | `CatalogoController.listar_promociones` | `PromocionSelector.get_activas` | `CatalogoPresenter.present_promociones` | lectura `promociones` |
| `/inscripcion` | `cotizacion.service.ts::cotizarPaquete` | `POST /cotizaciones/` | `CotizacionController.cotizar` (`auth=None`) | `CotizacionFlujo.cotizar` | (respuesta directa, sin persistencia) | lectura `paquetes`, `paquetes_precios`; **sin escritura** |
| `/inscripcion` | `inscripcion.service.ts::createInscripcionCompleta` | `POST /inscripciones/completa/` | `InscripcionController.crear_inscripcion_completa` | `InscripcionOrchestrator.crear_inscripcion_completa_proceso` → `CrearInscripcionCompletaFlujo` | `InscripcionPresenter.present_equipo` | **escribe** `inscripciones`, `equipos`, `commerce_compra`, `salesianos_fest_compra_inscripcion`, `pagos_ordendago` |
| `/pases` | `pase.service.ts::fetchCatalogoPases` | `GET /pases/` | `PaseController.listar_pases` | `PaseOrchestrator.listar_catalogo` → `ListarPasesFlujo` | `PasePresenter.present_pases` | lectura `pases`, `pases_precios` |
| `/pases` | `pase.service.ts::crearCompraPase` | `POST /pases/comprar` | `PaseController.comprar_pases` | `PaseOrchestrator.comprar_pases` → `CrearCompraPaseFlujo` | `PasePresenter.present_compra_creada` | **escribe** `commerce_compra`, `salesianos_fest_compra_pase`, `pagos_ordendago` |
| `/pases` | `pase.service.ts::fetchCompraPase` | `GET /pases/compras/{compraId}` | `PaseController.obtener_compra_pase` | `PaseOrchestrator.obtener_compra` → `ObtenerCompraPaseFlujo` | `PasePresenter.present_compra_estado` | lectura `commerce_compra`, `pagos_ordendago`, `pases_beneficiarios` |
| `/pases` | `pase.beneficiario.service.ts::fetchBeneficiariosCompra` | `GET /pases/compras/{compraId}/beneficiarios` | `PaseController.listar_beneficiarios` | `PaseOrchestrator.listar_beneficiarios` → `ListarBeneficiariosPaseFlujo` | `PasePresenter.present_beneficiarios_lista` | lectura `pases_beneficiarios` |
| `/pases` | `pase.beneficiario.service.ts::asignarBeneficiariosCompra` | `POST /pases/compras/{compraId}/beneficiarios` | `PaseController.asignar_beneficiarios` | `PaseOrchestrator.asignar_beneficiarios` → `AsignarBeneficiariosPaseFlujo` | `PasePresenter.present_beneficiarios_asignados` | **escribe** `pases_beneficiarios` |
| `/pases` | `pase.beneficiario.service.ts::revocarBeneficiarioCompra` | `DELETE /pases/compras/{compraId}/beneficiarios/{personaId}` | `PaseController.revocar_beneficiario` | `PaseOrchestrator.revocar_beneficiario` → `RevocarBeneficiarioPaseFlujo` | `PasePresenter.present_beneficiario_revocado` | **escribe** `pases_beneficiarios` (revocación auditada) |
| `/pases` | `persona.resolucion.service.ts::resolverPersona` | `GET /personas/resolver` | `PersonaResolucionController.resolver_persona` | `PersonaResolucionOrchestrator` → `PersonaResolucionFlujo` | `PersonaResolucionPresenter.present_persona` | lectura `usuarios_persona` (coincidencia exacta) |
| `/api/auth/refresh` | `app/api/auth/refresh/route.ts` | `POST {backend}/token/refresh` | `NinjaJWTDefaultController` (`django-ninja-jwt`) | (interno del paquete JWT) | (interno del paquete JWT) | sin escritura directa; invalida el refresh anterior |
| `/api/auth/logout` | `app/api/auth/logout/route.ts` | **ninguno** | — | — | — | ninguna |

---

## 7. Catálogo de endpoints consumidos (detalle de contrato)

| # | Endpoint | Método | Auth | Consumido por | Campos de request | Campos de response usados | Validación en cliente |
|---|---|---|---|---|---|---|---|
| 1 | `/catalogo/disciplinas/` | GET | pública | `/` | — | `id`, `nombre`, `sigla`, `min_jugadores` | Zod (`DisciplinaOutSchema`) |
| 2 | `/catalogo/categorias/` | GET | pública | `/` | — | `nombre`, `promocion_desde`, `promocion_hasta` | Zod (`CategoriaOutSchema`) |
| 3 | `/catalogo/paquetes/` | GET | pública | `/`, `/informacion`, `/inscripcion` | — | lista de paquetes | 🔴 **ninguna** en `/` y `/informacion`; Zod (`PaqueteListContractSchema`) en `/inscripcion` |
| 4 | `/catalogo/promociones/` | GET | pública | `/inscripcion` | — | `id`, `nombre`, `anio` | ❌ ninguna (estilo B) |
| 5 | `/catalogo/paquetes/{id}/` | GET | pública | — (hook muerto) | — | — | Zod (`PaqueteDetailContractSchema`) |
| 6 | `/cotizaciones/` | POST | pública | `/inscripcion` | `paquete_id`, `cantidad` | `paquete_id`, `cantidad_cotizada`, `precio_unitario`, `total`, `version`, `estado` | ❌ ninguna |
| 7 | `/auth/login/dni` | POST | pública | `/login` | `dni`, `password` | `access_token`, `refresh_token`, `expires_at`, `user` | Zod (formulario) |
| 8 | `/auth/login/email` | POST | pública | `/login` | `email`, `password` | idem | Zod |
| 9 | `/auth/login/username` | POST | pública | `/login` | `username`, `password` | idem | Zod |
| 10 | `/auth/register` | POST | pública | `/register` | 13 campos camelCase | `access_token`, `refresh_token`, `expires_at`, `user` | Zod (`.strict()`) |
| 11 | `/auth/me` | GET | JWT | `/login` | — | `es_admin` | ❌ ninguna |
| 12 | `/personas/busqueda/{documento}` | GET | pública | `/register` | path param | `tipo_documento`, `numero_documento`, `razon_social` | ❌ ninguna |
| 13 | `/personas/resolver` | GET | JWT | `/pases` | query `tipo_documento`, `numero_documento` | `persona_id`, `nombre_completo`, `tipo_documento`, `numero_documento` | Zod (envoltura) |
| 14 | `/inscripciones/` | GET | JWT | `/dashboard` | — | `id`, `estado`, `created_at`, `paquete_nombre`, `promocion_nombre`, `cantidad_equipos`, `cantidad_participantes` | ❌ ninguna (estilo B) |
| 15 | `/inscripciones/completa/` | POST | JWT | `/inscripcion` | 11 campos | `inscripcion_id`, `compra_id`, `orden_pago_id`, `cantidad`, `precio_unitario`, `total`, `equipos[]` | ❌ ninguna (payload construido a mano) |
| 16 | `/inscripciones/{id}/detalle` | GET | JWT + ownership | detalle | — | objeto `InscripcionDetalleOut` completo | ❌ ninguna |
| 17 | `/inscripciones/{id}/pool` | GET | JWT + ownership | detalle | — | `pool[]` + estado de elegibilidad | ❌ ninguna |
| 18 | `/inscripciones/{id}/saldo` | GET | JWT + ownership | detalle | — | `contratados`, `pagados`, `asignados_pagados`, `disponibles_pagados` | ❌ ninguna |
| 19 | `/inscripciones/{id}/equipos/{equipoId}/elegibles` | GET | JWT + ownership | detalle | — | `elegibles[]` con veredicto por candidato | ❌ ninguna |
| 20 | `/inscripciones/{id}/personas` | POST | JWT + ownership | detalle | `persona_id` \| `persona_data`, `aceptaciones[]` | `participante` | Zod (`participante.schema.ts`) |
| 21 | `/inscripciones/{id}/pool/asignar` | POST | JWT + ownership | detalle | `inscripcion_persona_id`, `equipo_id`, `rol`, `talla_camiseta`, `notas` | `participante` | ❌ ninguna (payload con defaults) |
| 22 | `/participaciones/{id}` | PATCH | JWT | detalle | `rol`, `talla_camiseta`, `aseguradora_*`, `notas` | `ParticipanteOut` | Zod |
| 23 | `/participaciones/{id}/retirar` | PATCH | JWT | detalle | — | `{ participante_id }` | ❌ ninguna |
| 24 | `/pases/` | GET | pública | `/pases` | — | `PaseListOut[]` | Zod |
| 25 | `/pases/comprar` | POST | JWT | `/pases` | `pase_id`, `cantidad` | `PaseCompraCreadaOut` | Zod (`paseComprarInSchema`) |
| 26 | `/pases/compras/{id}` | GET | JWT + owner | `/pases` | — | `PaseCompraEstadoOut` | Zod |
| 27 | `/pases/compras/{id}/beneficiarios` | GET | JWT + owner | `/pases` | — | `PaseBeneficiariosListaOut` | Zod |
| 28 | `/pases/compras/{id}/beneficiarios` | POST | JWT + owner | `/pases` | `beneficiario_ids[]` | `PaseBeneficiariosAsignadosOut` | Zod |
| 29 | `/pases/compras/{id}/beneficiarios/{personaId}` | DELETE | JWT + owner | `/pases` | `motivo` | `PaseBeneficiarioRevocadoOut` | Zod |
| 30 | `/compras/{id}/iniciar-pago` | POST | JWT + owner | detalle, `/pases` | — | token y configuración Izipay | ❌ ninguna |
| 31 | `/pagos/izipay/confirmar` | POST | JWT + owner | detalle, `/pases` | `kr_answer` | `success`, `settlement_status`, `response_message` | ❌ ninguna |
| 32 | `/pagos/transacciones/{txId}` | GET | JWT + owner | detalle, `/pases` | — | estado de la transacción | ❌ ninguna |
| 33 | `{backend}/token/refresh` | POST | cookie de refresh | `lib/api.ts` | `refresh` | `access`, `refresh` | ❌ ninguna |

**Cuentas finales:** **33 contratos HTTP distintos** referenciados: 32 endpoints del backend (31 alcanzables desde una pantalla + 1 solo alcanzable por código muerto: `GET /catalogo/paquetes/{id}/`) y 1 endpoint de token (`POST {backend}/token/refresh`). El frontend expone además 2 route handlers propios: `/api/auth/refresh` y `/api/auth/logout`.

---

## 8. Brechas, duplicación y código muerto (consolidado)

| # | Hallazgo | Evidencia verificada | Impacto |
|---|---|---|---|
| FE-A1 | `dashboard/page.tsx` rompe el contrato de arquitectura | 499 líneas de lógica, `useState`+`useEffect` para carga, `ESTADO_META`, 3 componentes en línea | Pantalla más difícil de rediseñar; sin caché, sin reintento |
| FE-A2 | El diagrama de flujo del dashboard usa el estado de la **primera** inscripción | `page.tsx:434` | Información engañosa con varias inscripciones |
| FE-A3 | `"PENDIENTE"` usado como estado de inscripción por defecto | `page.tsx:434` vs. `EstadoInscripcionChoices` | Estado inexistente; `ESTADO_META` no lo contempla |
| FE-A4 | Sin botón de reintento en el error del dashboard | `page.tsx:472-476` | El usuario debe recargar a mano |
| FE-A5 | Mensajes de error en inglés y fuera del catálogo público | `page.tsx:387,390` | Inconsistencia de idioma y de propiedad del mensaje |
| FE-A6 | `useDisciplinas`/`useCategorias` duplicados entre features | `features/portada/hooks/useCatalogo.ts:225,235` vs `features/inscripciones/hooks/useInscripcionCatalogs.ts:79,96` | Ambigüedad al importar; caché partida |
| FE-A7 | Dos clientes del mismo endpoint de paquetes | `features/landing/paquetes.service.ts:30` vs `features/inscripciones/services/paquete.service.ts:18` | Dos bases URL, dos validaciones, dos claves de caché |
| FE-A8 | Datos de respaldo presentados como datos reales | `useCatalogo.ts:116-185`, `Paquetes.tsx:135-272` | El usuario no puede distinguir catálogo real de respaldo |
| FE-A9 | `useCatalogo` y `fetchPaquetes` silencian todo error | `useCatalogo.ts:219-221`, `paquetes.service.ts:48-50` | Sin estado de error ni reintento manual |
| FE-A10 | Anclas rotas en `/informacion` | `Navbar.tsx:18-23` vs `app/informacion/page.tsx` | 2 de 4 enlaces no llevan a ninguna sección |
| FE-A11 | `Disciplines` y `CATEGORY_ROWS` hardcodeados frente al dominio | `components/landing/Disciplines.tsx:10-60` | Puede divergir del backend sin señal |
| FE-A12 | Código muerto: `usePaqueteDetail`, `usePaqueteDisciplinas`, `useDisciplinas`, `useCategorias` (inscripciones) | `useInscripcionCatalogs.ts:28,60,79,96` — sin importadores | 4 hooks + 4 servicios + `catalog.service.getPaquetes` (`@deprecated`) |
| FE-A13 | Código muerto: `toBackendPayload()` | `schemas/inscripcion.schema.ts:150` | Sin uso; contradice la convención de `schemas/` |
| FE-A14 | Código muerto: `setAuthCookies()` (Server Action) | `lib/auth/actions.ts:17` — solo definición y barrel | La sesión se escribe desde el cliente; la Server Action quedó huérfana |
| FE-A15 | Código muerto: `components/landing/Hero.tsx` | Sin importadores | 16 KB de hero alterno sin uso |
| FE-A16 | Cookie del token de acceso con `httpOnly: false` | `lib/auth/cookies.ts:20-25` | Superficie de robo de token por XSS |
| FE-A17 | `maxAge` de 30 días para un token de 1 hora | `lib/auth/cookies.ts:28-31` vs. `ACCESS_TOKEN_LIFETIME = 1h` | Sesión fantasma: 30 días de cookie contra 1 h de token |
| FE-A18 | Comentario del route handler que contradice el código | `app/api/auth/refresh/route.ts:88` vs `cookies.ts:20-25` | Confusión sobre el modelo de seguridad |
| FE-A19 | El logout no revoca el refresh token ni limpia el store Zustand | `app/api/auth/logout/route.ts`, `auth.store.ts` | Sesión revocable solo en el cliente |
| FE-A20 | El logout no es accesible desde el alcance no administrativo | Solo `components/AppSidebar.tsx:114` lo invoca | El usuario no puede cerrar sesión desde `/` |
| FE-A21 | Dependencia `auth → admin` | `features/auth/utils/resolver-destino.ts:1` | La feature pública importa el cliente de administración |
| FE-A22 | Tres formularios de login duplicados | `LoginClientShell.tsx:128,223,316` | ~170 líneas repetidas; 3 instancias de `useLogin()` |
| FE-A23 | Parámetro `isLoading` siempre `false` en el login | `LoginClientShell.tsx:473-475` | Vía de carga muerta |
| FE-A24 | Campos de formulario no renderizados en el registro | `telefono`, `whatsapp`, `contacto*` en `register.schema.ts` | Contrato desalineado con la UI; siempre `null` |
| FE-A25 | `acceptedBases` no se propaga al backend | `registro_controller.py:46-60` no lo pasa | La casilla es una puerta de UX, no un registro de consentimiento |
| FE-A26 | Los consentimientos del wizard no se persisten | `InscripcionWizard.tsx:145-149,218-224` | El backend solo registra aceptaciones por persona |
| FE-A27 | `useElegiblesEquipos` hace N peticiones (una por equipo) | `useElegiblesEquipo.ts:95-102` | N+1 de red en cada carga del detalle |
| FE-A28 | `window.confirm()` en el detalle | `InscripcionDetailView.tsx` (`confirm(...)`) | UX ajena al diseño; existe `components/confirmationDialog/` sin usar |
| FE-A29 | `POST /inscripciones/completa/` sin validación Zod del payload | `useCreateInscripcionCompleta.ts:61-73` | El contrato se arma a mano y puede derivar sin aviso |
| FE-A30 | `getMisInscripciones` sin validación en ejecución | `inscripcion.service.ts:107` | Estilo B: una deriva del backend llega como `undefined` |
| FE-A31 | Precio de venta duplicado en el navegador | `features/portada/pricing-stage.ts`, `features/pases/utils/pase.precio.ts` | Dos fuentes de verdad del calendario comercial |
| FE-A32 | `Navbar` de `landing` apunta a `/admin/dashboard` (ruta inexistente) | `components/landing/Navbar.tsx:41-44` | 404 para usuarios con rol administrativo en la cookie |
| FE-A33 | `PaseLookupPersonaField` usa `<select>` nativo | `components/pases/PaseLookupPersonaField.tsx:87` | Inconsistencia visual con el resto del proyecto |

---

## 9. Referencias de fuentes

### Frontend — rutas y componentes

- `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, `frontend/src/app/informacion/page.tsx`
- `frontend/src/app/(auth)/login/page.tsx`, `frontend/src/app/(auth)/register/page.tsx`
- `frontend/src/app/(app)/layout.tsx`, `frontend/src/app/(app)/dashboard/page.tsx`
- `frontend/src/app/(app)/dashboard/inscripcion/[id]/page.tsx`
- `frontend/src/app/(app)/inscripcion/page.tsx`, `frontend/src/app/(app)/pases/page.tsx`
- `frontend/src/app/api/auth/refresh/route.ts`, `frontend/src/app/api/auth/logout/route.ts`
- `frontend/src/proxy.ts`, `frontend/src/lib/api.ts`, `frontend/src/lib/query-client.ts`
- `frontend/src/lib/auth/{actions.ts,cookies.ts,index.ts}`, `frontend/src/lib/post-auth-redirect.ts`, `frontend/src/lib/server/{backend-url.ts,jwt.ts}`
- `frontend/src/components/landing/{Navbar,Paquetes,PaquetesCards,Disciplines,Gallery,HeroOverlaySection,PreinscribirButton,PreinscribirCTA,index}.tsx`
- `frontend/src/components/portada/{TicketsSection,ChampionshipSection,ScheduleSection,PromotionsSection,PartyPassSection,RegistrationSteps,ClosingSection,MobileTicketBar,PortadaFooter}.tsx`
- `frontend/src/components/paquetes/{PaqueteComercialCard,PreventaBanner,paquete-copy.ts,DisciplinaIcon}.tsx`

### Frontend — features

- `frontend/src/features/portada/{config/festival.ts,config/promotions.ts,copy.ts,pricing-stage.ts,hooks/useCatalogo.ts}`
- `frontend/src/features/landing/{paquetes.service.ts,hooks/useLandingPaquetes.ts}`
- `frontend/src/features/auth/{views/LoginClientShell.tsx,views/RegisterClientShell.tsx,components/RegisterForm.tsx,hooks/useLogin.ts,hooks/useRegister.ts,schemas/login.schema.ts,schemas/register.schema.ts,services/register.service.ts,store/auth.store.ts,utils/resolver-destino.ts}`
- `frontend/src/features/inscripciones/{views/InscripcionClientShell.tsx,views/InscripcionDetailView.tsx,components/InscripcionWizard.tsx,components/smart-fields/SmartPaqueteCardsField.tsx,components/smart-fields/SmartEquipoField.tsx,components/steps/StepDeclarations.tsx,hooks/*,services/*,schemas/*,utils/*}`
- `frontend/src/features/pases/{views/PaseCompraView.tsx,components/*,hooks/*,services/*,schemas/pase.schema.ts,utils/pase.precio.ts}`
- `frontend/src/features/pagos/{components/IzipayModal.tsx,services/pago.service.ts,schemas/pago.schema.ts,utils/*}`
- `frontend/src/features/admin/services/admin.me.service.ts` (único punto de dependencia `auth → admin`)

### Backend — controladores, orquestadores, flujos y selectores

- `backend/modules/salesianos_fest/presentation/controllers/{catalogo_controller,cotizacion_controller,inscripcion_controller,asignacion_controller,compra_controller,pase_controller}.py`
- `backend/modules/salesianos_fest/domain/services/orchestrators/{inscripcion_orchestrator,pase_orchestrator,compra_orchestrator,asignacion_orchestrator}.py`
- `backend/modules/salesianos_fest/domain/services/flujos/{cotizacion_flujo,crear_inscripcion_completa_flujo,agregar_persona_flujo,crear_compra_pase_flujo,obtener_compra_pase_flujo,listar_pases_flujo,listar_beneficiarios_pase_flujo,asignar_beneficiarios_pase_flujo,revocar_beneficiario_pase_flujo,iniciar_pago_flujo,confirmar_pago_flujo}.py`
- `backend/modules/salesianos_fest/domain/selectors/{disciplina_selector,categoria_selector,promocion_selector,paquete_selector,inscripcion_selector}.py`
- `backend/modules/salesianos_fest/presentation/presenters/{catalogo_presenter,inscripcion_presenter,pase_presenter,asignacion_presenter}.py`
- `backend/modules/pagos/presentation/controllers/pagos_controller.py`, `backend/modules/pagos/domain/services/orchestrators/pagos_orchestrator.py`
- `backend/modules/usuarios/presentation/controllers/{auth_controller,registro_controller,me_controller,persona_busqueda_controller,persona_resolucion_controller}.py`
- `backend/modules/usuarios/domain/services/orchestrators/{auth_orchestrator,registro_orchestrator,persona_busqueda_orchestrator,persona_resolucion_orchestrator}.py`
- `backend/modules/usuarios/domain/services/flujos/{auth_flujo,registro_flujo,persona_busqueda_flujo,persona_resolucion_flujo}.py`
- `backend/config/api.py` (registro de controladores y del controlador JWT)

### Backend — modelos

- `backend/modules/salesianos_fest/domain/models/{paquete,paquete_precio,paquete_disciplina,paquete_beneficio,disciplina,categoria,promocion,inscripcion,inscripcion_persona,equipo,participacion,asignacion_cupo,aceptacion_inscripcion,pase,pase_precio,pase_beneficiario,compra_pase,compra_inscripcion}.py`
- `backend/modules/commerce/domain/models/compra.py`, `backend/modules/pagos/domain/models/pago.py`
- `backend/modules/usuarios/domain/models/{persona,usuario}.py`

### Contratos normativos aplicados

- `contract/next-app-architecture-contract.md` — estructura, nombres, estado, formularios, importaciones, anti-patrones.
- `contract/api-wrapper-presenter-contract.md` — envoltorios por módulo, espejo 1:1 frontend/backend, propiedad de los mensajes públicos.
- `contract/smart.md` — Smart Fields y desacoplamiento de UI.
- `contract/django-app-architecture-contract.md` — el lado del backend que consume este frontend.
- `contract/PLAN_REFACTORIZACION.md` — reglas de controladores, presentadores y errores públicos.
- `contract/TEST_ARCHITECTURE_CONTRACT.md` — criterios de pruebas (backend), aplicables por analogía a la disciplina de espejo.

---

## 10. Verificación y alcance de esta pasada

| Comprobación | Resultado |
|---|---|
| Páginas no administrativas inventariadas | **8/8** (`/`, `/informacion`, `/login`, `/register`, `/dashboard`, `/dashboard/inscripcion/[id]`, `/inscripcion`, `/pases`) |
| Route handlers no administrativos inventariados | **2/2** (`/api/auth/refresh`, `/api/auth/logout`) |
| Páginas con ficha completa (propsito, roles, secciones, acciones, guardas, estado, endpoints, cadena backend, modelos, estados, brechas) | **10/10** |
| Endpoints backend trazados | **32 de negocio + 1 de token**, cada uno con su controller y presentador |
| Cadenas backend verificadas contra el código (no inferidas) | 30 de 31 (🟡 `POST /auth/register`: el efecto de `acceptedBases` queda para `RegistroFlujo`; el interior del controlador JWT de `django-ninja-jwt` es de la librería y no del repositorio) |
| Modelos/tablas citados | 23, con `db_table` explícito cuando existe y tabla Django por defecto cuando no (`usuarios_persona`, `usuarios_usuario`, `pagos_ordendago`, `pagos_transaccionpago`) |
| Modificaciones de código de aplicación | **Ninguna**. Solo se creó este documento |

**Limitaciones declaradas.** 🟡 La verificación se hizo por lectura de código y por búsqueda textual; no se ejecutaron las suites de pruebas ni se levantó el entorno, de modo que el comportamiento en ejecución de los endpoints no se observó directamente. 🟡 Dos afirmaciones requieren lectura adicional del backend para cerrarse: el detalle de la aceptación de bases en `RegistroFlujo` y el contenido exacto de `PagoIzipayConfirm` (settlement) en `pagos/`.

