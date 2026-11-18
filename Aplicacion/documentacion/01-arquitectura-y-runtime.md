# 01 — Arquitectura y Runtime

> **Ámbito:** topología de ejecución, raíces de código fuente, capa de borde (nginx), resolución de URLs, propiedad de cookies de sesión y topología de despliegue del sistema **Salesianos FEST**.
> **Método:** verificación directa en el código fuente del repositorio (`backend/`, `frontend/`, `proxy/`, `worker/`, `docker-compose.yml`).
> **Documentos hermanos:** [05 — Flujos end-to-end](./05-flujos-end-to-end.md) · [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md)

---

## 1. Propósito y alcance

Este documento describe **cómo está construido y cómo se ejecuta hoy** el sistema. No describe qué debería ser ni propone rediseños. Los defectos detectados se registran como hallazgos en [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) y **no se corrigen aquí**.

Los contratos arquitectónicos del proyecto (`contract/`) tienen prioridad sobre cualquier descripción de este documento cuando exista conflicto:

| Contrato | Alcance |
|---|---|
| `contract/django-app-architecture-contract.md` | Estructura de módulos Django, capas, DI, naming |
| `contract/next-app-architecture-contract.md` | Estructura de carpetas Next.js, estado, formularios |
| `contract/api-wrapper-presenter-contract.md` | Wrappers de API, presentadores, catálogo de errores |
| `contract/TEST_ARCHITECTURE_CONTRACT.md` | Arquitectura de pruebas backend |
| `contract/PLAN_REFACTORIZACION.md` | Reglas de controladores, orquestadores, flujos, presenters |
| `contract/SCHEMA_DRY_INTENTION.md` | Composición de schemas (bloques General / Específico / Identidad) |
| `contract/smart.md` | Patrón Smart Field y `GenericForm` |

---

## 2. Raíces de código fuente

El sistema vive en cuatro raíces más un archivo de orquestación de contenedores, todas en la raíz del repositorio:

| Raíz | Ruta | Rol | Estado |
|---|---|---|---|
| Backend | `backend/` | API Django 5 + `django-ninja-extra`, montada en `/api/` | Fuente de verdad |
| Frontend | `frontend/` | App Next.js 16 (App Router) + React 19 | Fuente de verdad |
| Borde (edge) | `proxy/` | Configuración nginx (`nginx.conf`) + compose nginx aislado | Fuente de verdad |
| Worker | `worker/scraper/` | Microservicio FastAPI de consulta de documentos (DNI/RUC) | Fuente de verdad |
| Orquestación | `docker-compose.yml` (raíz) | Levanta los 5 servicios del sistema | Fuente de verdad |

Dentro de `backend/`:

| Ruta | Contenido |
|---|---|
| `backend/config/` | `api.py` (registro de controladores), `urls.py`, `settings/{base,development,production,test}.py` |
| `backend/core/` | Núcleo transversal: `responses.py`, `exceptions.py`, `permissions.py`, `capacidades.py`, `security.py`, `models/`, `management/commands/` |
| `backend/modules/` | Módulos de negocio (ver § 6) |
| `backend/docker/entrypoint.sh` | Secuencia de arranque del contenedor backend |
| `backend/Dockerfile` | Imagen multi-etapa (uv + python:3.10-slim) |

Dentro de `frontend/src/`:

| Ruta | Contenido |
|---|---|
| `frontend/src/app/` | **Solo enrutamiento y layouts** (grupos de ruta `(auth)` y `(app)`; `/` y `/informacion` cuelgan de la raíz del grupo, sin grupo propio) |
| `frontend/src/features/` | Lógica de negocio por dominio (`auth`, `inscripciones`, `pagos`, `pases`, `admin`, `competencias`, `landing`, `portada`) |
| `frontend/src/lib/` | Infraestructura: `api.ts` (axios), `auth/` (cookies), `server/` (URLs internas, JWT) |
| `frontend/src/components/` | UI genérica reutilizable y `genericForm/` |
| `frontend/src/proxy.ts` | Puerta de autenticación de la UX (no de autorización) |

### 2.1 Estado del árbol `Aplicacion/`

`Aplicacion/` es el **destino de la reconstrucción controlada** y hoy contiene copias parciales:

| Subárbol | Contenido en `Aplicacion/` | Observación |
|---|---|---|
| `Aplicacion/frontend/` | Copia byte a byte de `frontend/src` (559 archivos en ambos; verificado por recuento y SHA-256) | Completa |
| `Aplicacion/proxy/` | `nginx.conf`, `docker-compose.yml`, `README.md` | Completa |
| `Aplicacion/worker/` | 12 archivos, idénticos a `worker/scraper` | Completa |
| `Aplicacion/backend/` | `config/`, `core/`, `docker/`, `scripts/`, `utils/`, `old_seed/`, `db.sqlite3` | **Incompleta**: `modules/` contiene únicamente `__init__.py` |

> **Consecuencia operativa:** `Aplicacion/backend/config/api.py` importa controladores de `modules.*` que **no existen** en ese árbol. El backend de `Aplicacion/` no arranca tal como está; el copiado de `backend/modules/` es un paso pendiente y obligatorio.

---

## 3. Topología general

El sistema es una red de **cuatro niveles** con **dos superficies HTTP independientes** que comparten un único puerto público:

```
                        ┌──────────────────────────────────────────┐
   Navegador  ────────►  │  proxy (nginx:1.27-alpine)              │
                        │  puerto host ${PROXY_PORT:-7000} → :80    │
                        └───┬──────────────────────────────┬───────┘
                            │                              │
             location /      │ location /backend/          │ location = /api/auth/{refresh,logout}
             _next/, /       │                              │
                            ▼                              ▼
              ┌──────────────────────┐        ┌──────────────────────────┐
              │  frontend            │        │  backend (Django)        │
              │  Next.js 16 / React  │        │  Django 5 + Ninja Extra  │
              │  :3000 (expose)      │        │  :8000 (gunicorn x2)     │
              └──────────┬───────────┘        └────┬────────────┬────────┘
                         │  server-side fetch          │            │
                         │  BACKEND_INTERNAL_URL       │            │
                         └────────────────────────────►│            ▼
                                                      │      ┌─────────────┐
                                                      │      │ scraper     │
                                                      │      │ FastAPI     │
                                                      │      │ :8001       │
                                                      │      └──────┬──────┘
                                                      ▼             │ GET /consultar/{doc}
                                              ┌─────────────┐       ▼
                                              │  PostgreSQL │   portal externo
                                              │  16-alpine  │   (RENIEC / SUNAT)
                                              │  :5432      │
                                              └─────────────┘
```

### 3.1 Nivel por nivel

| Nivel | Componente | Puerto | Expuesto al host | Nota |
|---|---|---|---|---|
| Borde | `proxy` (nginx) | 80 | **Sí** (`${PROXY_PORT:-7000}`) | Único puerto publicado en el compose raíz |
| Presentación | `frontend` (Next.js standalone) | 3000 | No (`expose: "3000"`) | `NEXT_PUBLIC_*` horneadas en build; `BACKEND_INTERNAL_URL` en runtime |
| Aplicación | `backend` (gunicorn) | 8000 | No | 2 workers, usuario `appuser` vía `gosu` |
| Datos | `db` (PostgreSQL 16-alpine) | 5432 | No | Volumen `postgres_data` |
| Auxiliar | `scraper` (FastAPI/uvicorn) | 8001 | No (`SCRAPER_PORT=7004` declarado pero **no mapeado**) | Dependencia dura del arranque del backend |

### 3.2 La regla del proxy `/backend` → `/api`

El navegador **nunca** habla con Django por `/api`. Habla con `/backend/...`, y nginx reescribe:

```nginx
location /backend/ {
    proxy_pass http://backend_upstream/api/;
}
```

El `proxy_pass` con URI final `/api/` hace que Django reciba `/api/...` (Django monta la API en `backend/config/urls.py` con `path("api/", api.urls)`). El prefijo `/backend` queda consumido por nginx.

**Consecuencia:** el backend Django debe seguir montado en `/api/` y el prefijo público `/backend` es parte del contrato de integración. Un cambio en cualquiera de los dos rompe silenciosamente todas las llamadas del navegador.

---

## 4. Capa de borde — tabla de enrutamiento nginx

Fuente: `proxy/nginx.conf`.

| Ubicación | Upstream | Propósito |
|---|---|---|
| `= /proxy-health` | el propio nginx | Responde `200 ok` — destino del healthcheck |
| `= /api/auth/refresh` | `frontend_upstream` | **El handler de refresh es de Next.js**, no de Django |
| `= /api/auth/logout` | `frontend_upstream` | **El handler de logout es de Next.js**, no de Django |
| `/backend/` | `backend_upstream/api/` | Reescritura `/backend → /api`: único camino del navegador a Django |
| `= /admin` | — | Redirección `301` a `/admin/` |
| `/admin/` | `backend_upstream` | Django Admin, sin pasar por Next.js |
| `/_nested_admin/` | `backend_upstream` | Django Admin anidado |
| `/static/` | `backend_upstream` | Estáticos servidos por Django (no por Next.js) |
| `/_next/` | `frontend_upstream` | Assets de Next.js (con cabeceras de `Upgrade`/`Connection` para websocket) |
| `/` | `frontend_upstream` | SSR de las páginas de Next.js |

Parámetros globales: `proxy_connect_timeout 10s`, `proxy_read_timeout 60s`.

El mapa `$scheme_alt` preserva el protocolo real detrás de Cloudflare:

```nginx
map $http_cf_visitor $scheme_alt {
    default $scheme;
    "~https" "https";
}
```

Todas las ubicaciones proxied fijan `Host`, `X-Real-IP`, `X-Forwarded-For` y `X-Forwarded-Proto`.

> **Contrato congelado:** la tabla de enrutamiento de arriba es parte de la superficie pública. Las dos excepciones de coincidencia exacta (`= /api/auth/refresh` y `= /api/auth/logout`) existen porque esos handlers viven en Next.js; si se eliminan, la sesión deja de poder renovarse y el cierre de sesión deja de funcionar.

---

## 5. Frontend — Next.js 16

### 5.1 Las dos URLs base del backend

`frontend/src/lib/server/backend-url.ts` resuelve **dos** URL base distintas, deliberadamente:

| Función | Consumidor | Variable | Momento | Valor por defecto |
|---|---|---|---|---|
| `backendPublicUrl()` | Navegador (bundle cliente) | `NEXT_PUBLIC_API_URL` | **Build** (Next la inlinea) | `/backend` (relativa) |
| `backendInternalUrl()` | Servidor Next (Route Handlers, Server Components) | `BACKEND_INTERNAL_URL` | **Runtime** (nunca se inlinea) | `http://backend:8000/api` |

Orden de resolución de `backendInternalUrl()`:

1. `BACKEND_INTERNAL_URL` si está definida.
2. `NEXT_PUBLIC_API_URL` si es **absoluta** (`http://`/`https://`).
3. `http://backend:8000/api` si `NEXT_PUBLIC_API_URL` es **relativa** (configuración Docker/proxy).
4. `http://localhost:8000/api` (desarrollo local sin configuración).

El módulo documenta el incidente de producción que motivó la separación: usar la URL relativa `/backend` en un `fetch` de Node lanzaba `TypeError`, la guardia de administración respondía `unavailable` y **`/administracion/**` redirigía a `/dashboard` para todos los usuarios**.

> **Hallazgo relacionado:** dos clientes del catálogo público (`features/portada/hooks/useCatalogo.ts` y `features/landing/paquetes.service.ts`) **reimplementan esta resolución de forma local** con `http://backend:8000/api` hardcodeado, sin leer `BACKEND_INTERNAL_URL`. Ver [06 — Hallazgo H-9](./06-operacion-y-deuda-tecnica.md).

### 5.2 Capas del frontend

El contrato `contract/next-app-architecture-contract.md` establece `app/` para enrutamiento y `features/` para lógica de negocio. Estructura verificada:

```
frontend/src/
├── app/          # enrutamiento: (auth), (app) + raíz (/, /informacion) + /api/auth/{refresh,logout}
├── features/     # auth, inscripciones, pagos, pases, admin, competencias, landing, portada
├── components/   # UI genérica + components/genericForm (Smart Fields)
├── lib/          # api.ts (axios), auth/, server/
└── proxy.ts      # puerta de autenticación de la UX
```

Stack declarado en `frontend/package.json`: Next `^16.2.9`, React `19.2.4`, TanStack Query `^5.95.2`, Zustand `^5.0.12`, React Hook Form `^7.72.0`, Zod `^4.3.6`, axios `^1.14.0`. Herramientas: Vitest `^3.2.7`, Biome `2.2.0`, TypeScript `^5`.

Scripts disponibles: `dev`, `build`, `start`, `lint` (Biome), `format`, `test` (Vitest), `test:watch`. **No existen** scripts `db:*`, `seed` ni `admin:create` (los documentos históricos de `doc/` los describen; ver [H-4](./06-operacion-y-deuda-tecnica.md)).

### 5.3 Rutas de página verificadas

| Grupo | Ruta |
|---|---|
| Público | `/`, `/informacion` |
| Auth | `/login`, `/register` |
| Aplicación | `/inscripcion`, `/pases`, `/dashboard`, `/dashboard/inscripcion/[id]` |
| Administración | `/administracion`, `/administracion/inscripciones`, `/administracion/inscripciones/[id]`, `/administracion/equipos`, `/administracion/participantes`, `/administracion/acreditaciones`, `/administracion/pagos`, `/administracion/usuarios`, `/administracion/competencias`, `/administracion/competencias/agenda`, `/administracion/competencias/cuadro`, `/administracion/competencias/[id]` |

### 5.4 Puertas de acceso (guardas)

| Capa | Artefacto | Qué decide | ¿Es autoridad? |
|---|---|---|---|
| UX (navegador) | `src/proxy.ts` | Si existe **credencial** (cookie de access token) | **No** — la cookie es `httpOnly: false`, por lo que cualquier script del navegador puede escribirla |
| Servidor (área admin) | `features/admin/services/admin.session.server.ts` → `getAdminSession()` | Revalida contra `GET /api/auth/me` con `cache: "no-store"` | Sí, con **cierre por defecto** (`fails closed`) |
| Backend | `backend/core/permissions.py` (`RequireAdmin`, `RequireCapability`) | Permisos y capacidades del llamador en **cada** petición | **Sí — la autoridad real** |

`getAdminSession()` tiene cuatro resultados: `admin`, `forbidden`, `unauthenticated`, `unavailable`. Está memoizado con `cache()` de React para que el layout del área y el layout de la sección no puedan discrepar.

---

## 6. Backend — Django 5 + Django Ninja Extra

### 6.1 Capas por módulo

Cada módulo bajo `backend/modules/<nombre>/` sigue la estructura del contrato Django:

```
modules/<nombre>/
├── domain/
│   ├── models/          # modelos Django (heredan de core.models.BaseModel: UUID + timestamps)
│   ├── schemas/         # DTOs internos Pydantic (*CreateData, *UpdateData, *Result)
│   ├── results/         # DTOs de salida de servicios
│   ├── services/
│   │   ├── core/        # servicios sync sobre el ORM (sin transaction.atomic propio)
│   │   ├── flujos/      # casos de uso async (abren transaction.atomic)
│   │   └── orchestrators/ # fachadas async delgadas
│   ├── selectors/       # interfaces de consulta
│   └── exceptions.py    # excepciones de dominio con código estable
├── presentation/
│   ├── schemas/         # *In / *Out HTTP (Ninja Schema)
│   ├── controllers/     # controladores delgados (un método por ruta)
│   └── presenters/      # result → schema HTTP (transformación pura)
├── infrastructure/      # implementaciones concretas (clientes HTTP, cache, workers)
├── di.py                # wiring de injector
├── tests/               # integration/ + e2e/ + fixtures/ + factories.py
└── management/commands/ # comandos operativos manuales
```

Dependencias (`backend/pyproject.toml`): Django `5.2.11`, django-ninja `1.5.3`, django-ninja-extra `0.31.0`, django-ninja-jwt `>=5.4`, django-q2 `1.9.0`, django-simple-history `3.8.0`, psycopg2-binary `2.9.10`, gunicorn `>=23.0.0`, httpx `0.28.1`, whitenoise, django-nested-admin, django-import-export. Python `>=3.10`.

### 6.2 Módulos de negocio

| Módulo | Superficie |
|---|---|
| `usuarios` | Login (`/auth/login/*`), registro, `/auth/me`, búsqueda y resolución de personas, roles y capacidades |
| `eventos` | Eventos (ediciones del festival) |
| `commerce` | `Compra`, `OrdenPago` (propietario), estados de compra |
| `pagos` | Canal Izipay: preparación, confirmación, notificación, lectura de transacción |
| `salesianos_fest` | Catálogo, cotizaciones, inscripciones, equipos, participaciones, compras, asignaciones de cupo, pases, acreditación, acceso |
| `competencias` | Cuadro, rondas, encuentros, resultados (administración y superficie pública) |
| `administracion` | Superficie read-only de administración + aprobaciones manuales de pago |

### 6.3 Registro de controladores (`backend/config/api.py`)

El archivo contiene **28 llamadas** a `api.register_controllers(...)`. **El orden es significativo**: seis controladores comparten el prefijo `/administracion` y dos comparten `/inscripciones`, por lo que el orden de registro determina qué ruta resuelve primero.

Orden verificado:

| # | Controlador | Prefijo resultante |
|---|---|---|
| 1 | `NinjaJWTDefaultController` | `/token/*` (`pair`, `refresh`, `verify`) |
| 2 | `AuthLoginController` | `/auth/login/{username,dni,email}` |
| 3 | `RegistroController` | `/auth/register` |
| 4 | `PersonaBusquedaController` | `/personas/busqueda/{documento}` |
| 5 | `PersonaResolucionController` | `/personas/resolver` |
| 6 | `AuthMeController` | `/auth/me` |
| 7 | `PagosController` | `/pagos/*` |
| 8 | `CatalogoController` | `/catalogo/*` |
| 9 | `PaseController` | `/pases/*` |
| 10 | `InscripcionController` | `/inscripciones/*` |
| 11 | `EquipoController` | `/equipos/*` |
| 12 | `ParticipacionController` | `/participaciones/*` |
| 13 | `CompraController` | `/compras/*` |
| 14 | `AsignacionController` | `/asignaciones/*` |
| 15 | `InscripcionSaldoController` | `/asignaciones/{inscripcion_id}/saldo` |
| 16 | `AcreditacionController` | `/acreditaciones/*` |
| 17 | `AccesoController` | `/acceso/*` |
| 18 | `CotizacionController` | `/cotizaciones` |
| 19–25 | `Admin{Fundacion,Resumen,Inscripcion,Pago,Operacion,Pases,Usuario}Controller` | `/administracion/*` |
| 26 | `AdminCompetenciasController` | `/administracion/competencias/*` |
| 27 | `AdminEncuentrosController` | `/administracion/competencias/encuentros/*` |
| 28 | `PublicCompetenciasController` | `/competencias/*` (público, lectura) |

> **Hallazgo:** `backend/modules/usuarios/presentation/controllers/ingeniero_habilitado_controller.py` define `GET /ingenieros/habilitados/{cip}` pero **no está registrado** en `config/api.py`. La ruta no existe en la API. Ver [H-8](./06-operacion-y-deuda-tecnica.md).

### 6.4 Configuración relevante

Fuente: `backend/config/settings/base.py`.

| Clave | Valor / regla | Efecto |
|---|---|---|
| `AUTH_USER_MODEL` | `"usuarios.Usuario"` | Modelo de usuario propio (no `django.contrib.auth.User`) |
| `NINJA_JWT.ACCESS_TOKEN_LIFETIME` | `timedelta(hours=1)` | Vida del access token |
| `NINJA_JWT.REFRESH_TOKEN_LIFETIME` | `timedelta(days=7)` | Vida del refresh token |
| `NINJA_JWT.ROTATE_REFRESH_TOKENS` | `True` | El refresh entrega un token nuevo |
| `NINJA_JWT.BLACKLIST_AFTER_ROTATION` | `True` | El refresh **anterior** se lista al rotar |
| `EVENTO_ACTIVO_NOMBRE` | `"Salesianos FEST 2026"` (configurable) | **El frontend nunca envía `evento_id`**; el backend lo resuelve por nombre. Una segunda edición exige cambiar el setting |
| `PAGO_MANUAL_APROBACION_ENABLED` | `False` por defecto (`true` en `.env`) | Interruptor de despliegue de la aprobación manual de pago |
| `PASES_FIESTA_ENABLED` | `False` por defecto (ausente en `.env`) | Interruptor de despliegue de la compra de pases |
| `Q_CLUSTER` | 4 workers, `recycle 500`, `timeout 60` | **Configuración muerta**: `django_q` está instalado pero no hay consumidor ni tareas |
| `NINJA_EXTRA.INJECTOR_MODULES` | 6 módulos | `modules.pagos.di.PagosModule` está **comentado** (el resto de `pagos` sí está activo) |
| `USE_SQLITE` / `SQLITE_PATH` | selection de motor | Ver [06 — Base de datos](./06-operacion-y-deuda-tecnica.md) |

---

## 7. Base de datos

| Aspecto | Valor |
|---|---|
| Motor de producción | PostgreSQL 16-alpine (`db` en el compose raíz) |
| Motor alternativo | SQLite, si `USE_SQLITE` ∈ {`1`,`true`,`yes`}; nombre por `SQLITE_PATH` (por defecto `:memory:`) |
| Variables efectivas | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` |
| Mapeo en compose | `DB_*` → `POSTGRES_*` del contenedor `db` |
| Modelo base | `core.models.BaseModel` = `UUIDModel` (UUID v4 como PK) + `TimestampedModel` (`created_at`, `updated_at`) |
| Historial | `django-simple-history` (usado por `competencias`) |

---

## 8. Worker — scraper de documentos

`worker/scraper/` es un microservicio **FastAPI** independiente (`uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2`, imagen `python:3.11-slim`).

| Aspecto | Detalle |
|---|---|
| Contrato de éxito | `GET /consultar/{documento}` → `{tipo_documento, numero_documento, razon_social}` |
| Detección de tipo | 8 dígitos = DNI · 11 dígitos = RUC |
| Validación | No numérico → `422 INVALID_FORMAT` · longitud no válida → `422 INVALID_LENGTH` |
| Errores | `404 NOT_FOUND` · `502 FORMAT_ERROR` (cambió el HTML del portal) · `503 UNAVAILABLE` · `504 TIMEOUT` · `500 INTERNAL_ERROR` · `422 INVALID_DOCUMENT` · `503 TRANSPORT_ERROR` |
| Campo `retryable` | Presente en los errores transitorios (`TIMEOUT`, `FORMAT_ERROR`, `UNAVAILABLE`) |
| Healthcheck | `GET /health` → `{"status": "ok"}` |
| Cliente en el backend | `modules/usuarios/infrastructure/services.py` → `RealConsultaExternaClient` (httpx), con `ConsultaExternaSimulator` en `DEBUG` |

**Dependencia dura:** en el compose raíz, `backend` declara `depends_on: scraper: condition: service_healthy`. Si el scraper no está sano, **el backend no arranca**. La búsqueda de documentos es por tanto una capacidad degradada, no caída total, pero sí bloquea el despliegue.

> **Residuo heredado:** el título del servicio sigue siendo `"CAM Scraper Documentos"` y el `FastAPI` se llama `app` en `worker/scraper/main.py`. Son vestigios de un proyecto anterior, sin efecto funcional.

---

## 9. Propiedad de las cookies de sesión

Prefijo efectivo: `NEXT_PUBLIC_AUTH_STORAGE_PREFIX` → `salesianos_auth` en `.env`; el valor por defecto **en código** es `cam_auth` (`frontend/src/lib/auth/cookies.ts`). El `frontend/Dockerfile` fija `ENV NEXT_PUBLIC_AUTH_STORAGE_PREFIX=salesianos_auth` de forma literal, sin `ARG` (ver [H-6](./06-operacion-y-deuda-tecnica.md)).

| Cookie | Nombre | La escribe | La lee | `httpOnly` | `maxAge` |
|---|---|---|---|---|---|
| Access | `salesianos_auth_access_token` | **Navegador** (`useLogin`, `useRegister`) y **servidor Next** (refresh) | Interceptor de axios, `proxy.ts`, `admin.session.server.ts` | `false` | 30 d (`cookies.ts`) / 7 d (`useLogin`) |
| Refresh | `salesianos_auth_refresh_token` | **Navegador** (login/registro) y **servidor Next** (rotación) | **Solo** el handler de refresh de Next | `false` | 7 d |
| Expiración | `salesianos_auth_expires_at` | Navegador + servidor Next | axios (`isTokenExpiringSoon`, umbral de 5 min) | `false` | 7 d |
| Sesión de usuario | `salesianos_auth_user_session` | Navegador (login/registro) | Solo hidratación de la UI — **no es autoridad** | `false` | 7 d |

Consecuencias estructurales:

- **`httpOnly: false` es una decisión, no un descuido.** Las cookies son legibles y escribibles por JavaScript del navegador. El control real es el backend (`RequireAdmin`/`RequireCapability`), reevaluado en cada petición.
- **Django nunca ve una cookie.** `ninja_jwt` emite y valida JWT; el prefijo `Bearer` es el contrato.
- **El logout es exclusivamente del lado Next.** `POST /api/auth/logout` llama `clearAuthCookies()` y **no invoca ningún endpoint del backend**. El refresh token no se lista en la blacklist. Ver [H-1](./06-operacion-y-deuda-tecnica.md).

### 9.1 Ciclo de vida del token

| Momento | Actor | Acción |
|---|---|---|
| Login / Registro | Navegador | Recibe `access`, `refresh`, `expires_at` → escribe las 4 cookies |
| Petición saliente | `lib/api.ts` | Inyecta `Authorization: Bearer <access>`; si expira en < 5 min, refresca de forma proactiva |
| Respuesta 401 | `lib/api.ts` | Refresca **una vez** (bandera `_retry`) y reintenta la petición original |
| Refresh | `POST /api/auth/refresh` (Next) | Llama `{BACKEND_INTERNAL_URL}/token/refresh`, rota las cookies de token en el servidor, devuelve `{success, data:{expires_at}}` |
| Refresh fallido | `lib/api.ts` | El 401 original se propaga |
| Logout | `POST /api/auth/logout` (Next) | Borra las 4 cookies. Sin llamada al backend |

El refresh usa **single-flight**: un único `refreshPromise` compartido entre peticiones concurrentes.

---

## 10. Topología de despliegue

### 10.1 Servicios del compose raíz (`docker-compose.yml`)

| Servicio | Imagen / build | Puerto host | Puerto interno | `depends_on` | Healthcheck |
|---|---|---|---|---|---|
| `db` | `postgres:16-alpine` | — | 5432 | — | `pg_isready` (5 s / 5 s / 5 reintentos, `start_period` 10 s) |
| `scraper` | `worker/scraper/Dockerfile` | — (`SCRAPER_PORT=7004` declarado, **no mapeado**) | 8001 | — | `urllib` a `http://localhost:8001/health` (30 s, 3 reintentos) |
| `backend` | `backend/Dockerfile` (uv, python:3.10-slim) | — | 8000 | `db` sano **y** `scraper` sano | `manage.py check` (30 s) |
| `frontend` | `frontend/Dockerfile` (3 etapas, standalone) | — | `expose 3000` (`PORT=3000`) | `backend` | Sin healthcheck |
| `proxy` | `nginx:1.27-alpine` | **`${PROXY_PORT:-7000}` → 80** | — | `frontend`, `backend` | Sin healthcheck en el compose raíz (la ruta `/proxy-health` sí existe en la config) |

Volúmenes: `postgres_data`, `backend_static`.

### 10.2 Secuencia de arranque del backend

`backend/docker/entrypoint.sh`:

1. Espera a PostgreSQL (sondeo de `psycopg2.connect` con `DB_*`, reintento cada 2 s).
2. `manage.py migrate --noinput`.
3. `chown -R appuser:appuser /app/staticfiles` + `manage.py collectstatic --noinput`.
4. `exec gosu appuser uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2`.

**No ejecuta:** seeds, creación de superusuario, ni ningún planificador. Ver [06 — Trabajos programados](./06-operacion-y-deuda-tecnica.md).

### 10.3 Imagen del frontend

Tres etapas: `deps` (`npm ci`) → `builder` (`npm run build`) → `runner` (standalone, usuario `nextjs`, uid 1001).

| Variable | Fase | Observación |
|---|---|---|
| `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_COOKIE_SECURE`, `NEXT_PUBLIC_IS_TEST_UUID`, `NEXT_PUBLIC_IZIPAY_ENABLED` | Build (`ARG` + `ENV`) | Horneadas en el bundle del navegador |
| `NEXT_PUBLIC_DEBUG_GENERIC_FORM_ERRORS` | Build (`ARG` + `ENV`) | Horneada |
| `BACKEND_INTERNAL_URL` | **Runtime** (`ARG` + `ENV`) | Solo en el servidor; nunca llega al navegador |
| `PORT`, `HOSTNAME` | Runtime | Compose fija `PORT=3000`; el Dockerfile declara `EXPOSE ${PORT:-7000}` |

> **Inconsistencias verificadas:** el `EXPOSE` por defecto del Dockerfile (`7000`) no coincide con el puerto real (`3000`); `NEXT_PUBLIC_FRONTEND_URL` y `NEXT_PUBLIC_AUTH_STORAGE_PREFIX` se pasan como `args` en el compose pero **el Dockerfile no los declara como `ARG`**, por lo que el valor efectivo es el del `ENV` literal o el valor por defecto del código. Ver [H-6](./06-operacion-y-deuda-tecnica.md).

---

## 11. Propiedad de las variables de entorno

| Variable | Consumidor | Momento | Significado |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Bundle del navegador (axios) | Build | Base pública, normalmente `/backend` |
| `BACKEND_INTERNAL_URL` | Servidor Next (route handlers, `admin.session.server.ts`) | Runtime | `http://backend:8000/api`; nunca se inlinea |
| `NEXT_PUBLIC_AUTH_STORAGE_PREFIX` | Cookies | Build | Prefijo de las cookies de sesión (`salesianos_auth`) |
| `NEXT_PUBLIC_COOKIE_SECURE` | Cookies | Build | Atributo `secure` de las cookies |
| `NEXT_PUBLIC_IZIPAY_ENABLED` | Bundle | Build | Interruptor del checkout Izipay |
| `NEXT_PUBLIC_IS_TEST_UUID` | Bundle | Build | Bandera de UUID de prueba |
| `NEXT_PUBLIC_DEBUG_GENERIC_FORM_ERRORS` | Bundle | Build | Depuración de errores de `GenericForm` |
| `NEXT_PUBLIC_FRONTEND_URL` | Bundle | Build | URL pública del frontend (declarada como `args` pero **no consumida** por el Dockerfile) |
| `PROXY_PORT` | Compose | Ejecución | Puerto publicado del proxy |
| `SCRAPER_PORT` | — | — | **Declarado pero no usado**: el scraper no publica puerto |
| `SCRAPER_URL` | `RealConsultaExternaClient` | Ejecución | Base del scraper (`http://scraper:8001`) |
| `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` | Django + compose | Ejecución | Selección de motor y credenciales |
| `USE_SQLITE`, `SQLITE_PATH` | Django | Ejecución | Selección de motor |
| `EVENTO_ACTIVO_NOMBRE` | Django | Ejecución | Evento activo, resuelto por nombre |
| `PAGO_MANUAL_APROBACION_ENABLED` | Django | Ejecución | Interruptor de despliegue |
| `PASES_FIESTA_ENABLED` | Django | Ejecución | Interruptor de despliegue |
| `IZIPAY_SHOP_ID`, `IZIPAY_KEY`, `IZIPAY_KEY_HASH`, `IZIPAY_API_URL`, `IZIPAY_CALLBACK_URL` | Django | Ejecución | Credenciales de Izipay. **`IZIPAY_KEY_HASH` vacío ⇒ la notificación del proveedor falla cerrado** |
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_*`, `SECURE_*`, `CSRF_TRUSTED_ORIGINS` | Django | Ejecución | Postura de seguridad |

---

## 12. Referencias cruzadas

- [README — Índice de la documentación](./README.md) — punto de entrada navegable del conjunto documental.
- [00 — Cobertura y trazabilidad](./00-cobertura-y-trazabilidad.md) — metodología de auditoría, recuentos exactos y checklist reejecutable.
- [02 — Backend y API](./02-backend-y-api.md) — arquitectura del servicio Django/Ninja.
- [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) — catálogo de rutas del backend.
- [03 — Frontend](./03-frontend.md) — arquitectura del frontend, rutas, features y transporte HTTP.
- [04 — Datos y dominio](./04-datos-y-dominio.md) — propiedad de datos, modelos, migraciones y fronteras de integración.
- [05 — Flujos end-to-end](./05-flujos-end-to-end.md) — los 27 flujos verificados, con su transporte, endpoint y ruta de recuperación.
- [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) — topología operativa, ausencia de planificador, y el registro de hallazgos (H-1 … H-9) y de deuda técnica.
- [07 — Guía para el agente de UI/UX](./07-guia-para-ui-ux.md) — qué puede y qué no puede cambiarse en el frontend, y cómo se entrega un cambio.
