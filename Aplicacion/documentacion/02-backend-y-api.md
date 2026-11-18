# Backend y API — Arquitectura del servicio Django/Ninja

> **Ámbito:** servicio backend de Salesianos FEST, código en `backend/`.
> **Estado:** verificación directa sobre el código fuente y la introspección del runtime (Django 5 + `django-ninja-extra`).
> **Documento par:** [02a-inventario-de-endpoints.md](02a-inventario-de-endpoints.md).

---

## Documentos de detalle asociados

Este documento describe la **arquitectura** del backend. Los documentos de detalle amplían cada superficie sin duplicarla aquí:

| Documento de detalle | Qué añade a este documento |
|---|---|
| [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) | Catálogo ruta por ruta: método, ruta, `auth`, permiso efectivo, wrapper de respuesta y estado (registrada / no registrada). |
| [02b — Propósito y consumidores de endpoints](./02b-proposito-y-consumidores-de-endpoints.md) | Propósito de negocio de cada una de las 111 rutas, consumidor real en el frontend, cadena de ejecución, tablas tocadas, invariantes e implicaciones de error. |
| [04 — Datos y dominio](./04-datos-y-dominio.md) | Propiedad de tablas, modelos, migraciones y fronteras de integración. |
| [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) | Los 13 comandos de gestión del proyecto, qué tablas siembran y con qué riesgo. |
| [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) | Trazabilidad completa desde la pantalla hasta la escritura en base de datos. |

---

## 1. Alcance y método de verificación

Este documento describe la arquitectura real del backend y las reglas que gobiernan su capa HTTP. Todo lo que aquí se afirma como **verificado** se comprobó de una de estas dos formas:

1. **Lectura directa del código fuente** bajo `backend/` (rutas, decoradores, firmas, imports, registros).
2. **Introspección del runtime**: arranque de Django con `DJANGO_SETTINGS_MODULE=config.settings.development` y recorrido de `config.api.api._routers`, que devuelve el conjunto de rutas efectivamente registradas, sus métodos HTTP y sus *auth callbacks*.

La introspección de runtime es la que determina qué rutas **existen de verdad**. Un controlador puede estar escrito en disco y no estar registrado; en ese caso la ruta no existe para el cliente. El inventario de [02a-inventario-de-endpoints.md](02a-inventario-de-endpoints.md) distingue ambas situaciones ruta por ruta.

Lo que **no** se verificó se declara explícitamente como vacío o material obsoleto en la sección 9.

---

## 2. Política de fuente de verdad

El proyecto tiene cuatro fuentes de verdad con alcances distintos. Confundirlas es la causa más común de documentación incorrecta.

| Fuente | Autoridad sobre | No decide |
|---|---|---|
| `contract/` (5 documentos normativos) | Cómo debe ser el código: estructura de módulos, capas, wrappers, mensajes públicos, permisos, estrategia de tests | Qué rutas existen hoy |
| `backend/` (código) | Qué existe hoy: rutas, esquemas, permisos efectivos, comportamiento | Cómo debería ser |
| `frontend/src/features/**/services/*.ts` | Qué forma consume el cliente final: fija el contrato de respuesta en la práctica | Nada del backend |
| `Aplicacion/documentacion/` (esta carpeta) | Explicación navegable del estado actual | Nada; es derivada |

Reglas que se aplican en este documento y en su par:

- **El contrato manda sobre el código.** Cuando el código contradice `contract/`, se documenta el comportamiento real y se marca la desviación; no se documenta como si cumpliera el contrato.
- **El runtime manda sobre la lectura estática** para decidir existencia de rutas. El código fuente (`@route.get(...)`) describe la intención; `api._routers` describe la realidad.
- **Esta documentación es derivada y regenerable.** El inventario de endpoints no se mantiene a mano: se reconstruye contrastando el AST de los controladores contra las rutas registradas en runtime. Si se añade un controlador, hay que volver a generarlo.
- **La doc no presupone el contenido de los documentos hermanos.** Se enlazan por nombre de archivo (`01-…`, `03-…`, `04-…`, `05-…`, `07-…`), pero cada uno mantiene su propio alcance.

---

## 3. Topología de ejecución

| Pieza | Ubicación | Responsabilidad |
|---|---|---|
| API Django | `backend/` | Toda la lógica de negocio y la superficie HTTP bajo `/api/` |
| Proxy nginx | `proxy/nginx.conf` | Punto de entrada público. Reescribe `/backend/*` → `/api/*` y reserva `/api/auth/refresh` y `/api/auth/logout` para Next.js |
| Frontend Next.js | `frontend/` | UI. Es también dueño de la renovación y el cierre de sesión (`/api/auth/{refresh,logout}`) |
| Microservicio scraper | `worker/scraper/main.py` | Servicio FastAPI independiente: `GET /consultar/{documento}` y `GET /health`. El backend lo consume por el puerto `IConsultaExternaClient`, no por HTTP anidado |
| Base de datos | PostgreSQL 16 (`docker-compose.yml`) | Persistencia |

Rutas de Django (`backend/config/urls.py`):

```
/admin/            → django.contrib.admin
/_nested_admin/    → nested_admin.urls
/api/              → config.api.api.urls   (API NinjaExtra)
/__debug__/        → debug_toolbar (solo DEBUG)
/media/            → MEDIA_ROOT (solo DEBUG)
```

El compose de la raíz construye el backend con `dockerfile: backend/Dockerfile`, es decir **`backend/` es hoy el árbol que se despliega**. `Aplicacion/backend/` es el árbol destino del relocalizado: `config/` y `core/` ya están copiados (hash idéntico al de `backend/config/api.py`), pero **`Aplicacion/backend/modules/` está vacío**. La reconstruir es el trabajo pendiente; mientras tanto, la referencia de comportamiento es `backend/modules/`.

---

## 4. Arquitectura Django + django-ninja-extra

### 4.1 Registro centralizado de controladores

No hay registro por router. `backend/config/api.py` es el manifiesto único:

- Una instancia de `NinjaExtraAPI` con `auth=JWTAuth()` y `docs_url="/docs"` (`urls_namespace="api"`).
- **28 llamadas** a `api.register_controllers(...)`, una por clase de controlador.
- `register_exception_handlers(api)` al final, que instala los manejadores globales de error.

Detalle verificado: existe una rama `PYTEST_CURRENT_TEST` que construye una **segunda** instancia de la API con `urls_namespace` único y la cachea en `sys._ninja_api_instance`, para no chocar con el `urls_namespace` global durante los tests. El código de aplicación no se ve afectado, pero cualquier script que intente importar `config.api` en un proceso con esa variable de entorno obtendrá la API de test, no la de producción.

El **orden de registro es significativo**: seis controladores comparten el prefijo `/administracion` y dos comparten `/administracion/competencias`. La resolución de rutas depende del orden, no de la unicidad del prefijo. Reordenar `register_controllers` puede cambiar silenciosamente qué ruta atiende una petición.

### 4.2 Ciclo de vida de una petición

```
HTTP → ruta Ninja (auth=JWTAuth salvo auth=None)
     → gate de permiso (core.permissions)
     → Controller (async: parsea, delega, no captura excepciones)
     → Orchestrator (async: fachada delgada)
     → Flujo (async: abre transaction.atomic)
     → Core service (sync: ORM, sin transacción propia)
     → Selector (sync: consulta ORM, devuelve Result DTO)
     → Presenter (transformación pura, sin ORM)
     → Schema Out (presentation/schemas/)
     → success_response(...) → {"success", "data", "error", "message"}
```

Reglas de este ciclo, tal como las define `contract/PLAN_REFACTORIZACION.md` y `contract/django-app-architecture-contract.md`:

- El **controller** hace tres cosas: parsear la entrada, llamar al orquestador, devolver el éxito formateado por un presenter. Prohibido `if` de negocio, ORM directo y `error_response(...)` manual.
- El **orquestador** es una fachada async mínima: un método público por endpoint, que delega al flujo. Sin lógica de negocio.
- El **flujo** es el único lugar donde se abre `transaction.atomic`.
- El **core service** es sync, opera el ORM y no abre transacciones propias.
- El **selector** carga datos (incluidas relaciones) y devuelve DTOs de dominio; no conoce la capa HTTP.
- El **presenter** sólo transforma `Result` → `Schema Out`. No consulta la base de datos.

### 4.3 Estructura de un módulo

Cada módulo de negocio vive bajo `backend/modules/<nombre>/` y sigue el contrato de arquitectura:

```
modules/<nombre>/
├── apps.py                 AppConfig (name, label, verbose_name)
├── models.py               re-export puro de domain/models/
├── admin.py, forms.py      superficie Django Admin
├── di.py                   Module de injector (bindings de ports)
├── domain/
│   ├── constants.py        TextChoices
│   ├── exceptions.py       excepciones de dominio con code estable
│   ├── models/             modelos Django (heredan de BaseModel)
│   ├── schemas/            DTOs internos Pydantic
│   ├── results/            DTOs de salida de servicios
│   ├── ports/              interfaces ABC
│   ├── selectors/          interfaces de consulta
│   └── services/
│       ├── core/           servicios sync (sin transaction.atomic)
│       ├── flujos/         casos de uso async (abren transaction.atomic)
│       └── orchestrators/  fachadas async delgadas
├── infrastructure/         implementaciones de ports, clientes externos
├── presentation/
│   ├── schemas/            esquemas HTTP (Ninja Schema)
│   ├── controllers/        controladores Ninja
│   └── presenters/         transformadores Result → Schema Out
├── management/commands/    comandos de gestión
└── migrations/
```

`domain/schemas/` y `domain/results/` cumplen funciones distintas y ambos heredan de `BaseSchema`/`BaseModel` según el caso: los primeros son contratos de datos internos, los segundos son DTOs de retorno que el presenter convierte en esquemas HTTP.

### 4.4 Fronteras asíncronas

La cadena asíncrona coherente, según `contract/django-app-architecture-contract.md` §2.1:

```
Controller async → Orchestrator async → Flujo async → Core sync
```

- El core service es **sync** y se invoca con `sync_to_async(...)()` desde el flujo o el orquestador.
- El flujo envuelve su operación sync atómica con `sync_to_async(...)()`.
- El presenter es sync y se ejecuta dentro del contexto async **sin tocar el ORM**.
- Está prohibido que un controller async llame a un orquestador sync, o viceversa.

**Desviación verificada**: varios controladores de `modules/salesianos_fest` no respetan la frontera. Llaman a selectores o flow directamente desde la capa HTTP, con `sync_to_async` propio y, en el caso de `CompraController`, instanciando `InscripcionSelector()` a mano dentro del método. Archivos afectados:

- `salesianos_fest/presentation/controllers/compra_controller.py` (`InscripcionSelector()` manual en las líneas 124 y 201)
- `salesianos_fest/presentation/controllers/asignacion_controller.py`
- `salesianos_fest/presentation/controllers/acreditacion_controller.py`
- `salesianos_fest/presentation/controllers/catalogo_controller.py`
- `salesianos_fest/presentation/controllers/cotizacion_controller.py`
- `salesianos_fest/presentation/controllers/inscripcion_controller.py`

Esto contradice `contract/PLAN_REFACTORIZACION.md` §1.A (controlador sin lógica ni ORM) y §1.D (asignación a variable en orquestadores). Es una desviación de la arquitectura documentada, no un patrón sancionado.

### 4.5 Inyección de dependencias

`injector` con un `Module` por app, registrado en `config/settings/base.py` bajo `NINJA_EXTRA["INJECTOR_MODULES"]`:

```
modules.usuarios.di.UsuariosModule
modules.eventos.di.EventosModule
modules.commerce.di.CommerceModule
modules.salesianos_fest.di.SalesianosFestModule
modules.competencias.di.CompetenciasModule
modules.administracion.di.AdministracionModule
# modules.pagos.di.PagosModule  ← comentado
```

`modules/pagos/di.py` existe en disco pero **no está registrado**. Los bindings de pagos (por ejemplo el `singleton` de `IzipayClient`) no se aplican; las dependencias se resuelven por auto-construcción implícita de `injector`. Funciona hoy por accidente, no por diseño.

Los **ports** son el mecanismo de inversión entre módulos. El triángulo `pagos` ↔ `commerce` ↔ `salesianos_fest` se formaliza con `IPropietarioOrdenPagoService`, `IEstadoCompraOrdenPagoService` e `IConfirmadorOrdenPagoService`, implementados en `modules/commerce/infrastructure/services.py` y `modules/salesianos_fest/infrastructure/services.py`.

---

## 5. Contratos de request, response y error

### 5.1 Sobre de respuesta

`backend/core/responses.py` define un único sobre:

```python
class ApiResponse(Schema, Generic[T]):
    success: bool
    data: Optional[T]
    error: Optional[ErrorDetail]   # {code, message, details}
    message: Optional[str]
```

- `success_response(data, message=None)` serializa con `model_dump(mode="json")` y convierte `Decimal → float` de forma recursiva.
- `error_response(code, message, details, status)` produce `{"success": False, "data": None, "error": {...}}` junto con el status HTTP.
- El `message` es texto fijo, contextual y declarativo en el controller. No se interpola identificadores.

También existe `PaginatedApiResponse[T]` (con `meta: PaginationMeta`), pero **no se usa en ninguna ruta**: la forma vigente de paginación es `ApiResponse[PaginatedData[X]]`.

### 5.2 Paginación

`backend/core/pagination.py` define `PaginatedData[T]` con `items`, `total`, `page`, `page_size`, `total_pages`, anidado dentro de `ApiResponse`. Se usa en las lecturas del área de administración (`/administracion/{inscripciones,equipos,participantes,participaciones,acreditaciones,accesos,pagos,usuarios}`).

### 5.3 Errores

`backend/core/exceptions.py` es el **único** punto de traducción de excepciones a respuestas HTTP:

- `PUBLIC_ERROR_MESSAGES`: catálogo código → prosa en español. Es la única fuente de texto público de error.
- `register_exception_handlers(api)` instala manejadores para `ObjectDoesNotExist`, `PermissionDenied`, `NinjaAuthenticationError`, `NinjaExtraAuthenticationFailed`, `NinjaExtraPermissionDenied`, `PydanticValidationError`, `NinjaValidationError`, `HttpError`, `DjangoValidationError`, `ValueError`, `IntegrityError` y `Exception` (500 `INTERNAL_ERROR`).
- Clases de dominio que heredan de `HttpError` y llevan un `code` estable: `NotFoundError` (404), `ConflictError` (409), `BusinessError` (400), `ForbiddenError` (403), `AdminRequiredError` (403), `UnprocessableEntityError` (422), `CipNotFoundError` (404), más las específicas de cada módulo en `domain/exceptions.py`.

Mapeo de categorías (según `contract/api-wrapper-presenter-contract.md` §8) y su implementación observada:

| Categoría | Status | Código | ¿En el catálogo público? |
|---|---|---|---|
| Autenticación | 401 | `AUTHENTICATION_REQUIRED` | Sí |
| Autorización | 403 | `ACTION_NOT_ALLOWED` | Sí |
| No encontrado | 404 | `RESOURCE_NOT_FOUND` | Sí |
| Validación | 422 | `INVALID_REQUEST` | Sí |
| Conflicto de negocio | 409 | `RESOURCE_CHANGED` | Sí |
| Inesperado | 500 | `INTERNAL_ERROR` | No aplica (mensaje genérico) |

**Desviación verificada (catálogo incompleto)**: los manejadores de `ObjectDoesNotExist` y `PermissionDenied` de Django emiten los códigos `NOT_FOUND` y `PERMISSION_DENIED`, y los de validación emiten `VALIDATION_ERROR`; ninguno de esos tres códigos existe en `PUBLIC_ERROR_MESSAGES`. Esos códigos salen con un mensaje redactado en el handler, no desde el catálogo.

**Desviación verificada (filtrado de texto crudo)**: el manejador de `ValueError` devuelve `str(exc)` literalmente tanto en `message` como en `details`. `contract/api-wrapper-presenter-contract.md` §8 prohíbe expresamente exponer texto crudo de excepción en la respuesta pública. Este es el punto más sensible del contrato de errores.

---

## 6. Política de autenticación y autorización (observada)

### 6.1 Autenticación

- `django-ninja-jwt` con `JWTAuth()` como `auth` global de la API.
- `AUTH_USER_MODEL = "usuarios.Usuario"`.
- `config/settings/base.py`: access token 1 h, refresh token 7 días, `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`, cabecera `Authorization: Bearer <token>`.
- El **login del proyecto es propio** (`/api/auth/login/{username,dni,email}`), no el built-in de ninja-jwt. El built-in sigue registrado en `/api/token/{pair,refresh,verify}`.
- Las rutas públicas declaran `auth=None` explícitamente; el `auth` global queda anulado para esa ruta.
- `ninja_jwt` está en `INSTALLED_APPS` junto con `ninja_jwt.token_blacklist`, de modo que la revocación por lista negra es operativa.

### 6.2 Autorización

Dos niveles, resueltos en el orden **autenticación → autorización**: un cliente anónimo recibe 401 antes de que se evalúe cualquier permiso.

**Nivel 1 — Capacidades.** `backend/core/capacidades.py` traduce las banderas de Django (`is_staff`, `is_superuser`) a un vocabulario explícito de **11 códigos**:

```
admin.ver                             admin.pagos.ver
admin.inscripciones.escribir          admin.pagos.aprobar
admin.equipos.escribir                admin.usuarios.ver
admin.competencias.escribir           admin.usuarios.gestionar
admin.acreditaciones.escribir         admin.usuarios.promover_superusuario
admin.configuracion.gestionar
```

Tres niveles de actor:

| Nivel | Capacidades |
|---|---|
| `usuario` | ninguna |
| `staff` | las 7 operativas (lee todo el área, escribe en dominios operativos); **no** aprueba ni anula pagos, **no** gestiona cuentas |
| `superusuario` | las 11 (break-glass). El nivel nunca se estrecha por debajo del bypass automático de Django |

**Nivel 2 — Gates.** `backend/core/permissions.py` traduce las capacidades a clases de permiso de `ninja_extra`: `RequireAdmin` (staff o superusuario) y `RequireCapability` con subclases concretas (`RequireAdminVer`, `RequirePagosVer`, `RequirePagosAprobar`, `RequireUsuariosVer`, `RequireAcreditacionesEscribir`, `RequireCompetenciasEscribir`, `RequireInscripcionesEscribir`, `RequireEquiposEscribir`, `RequireUsuariosGestionar`, `RequirePromoverSuperusuario`).

Regla verificada en la librería instalada (`ninja_extra/operation.py`, resolución del contexto de ejecución):

```python
permission_classes = route_function.route.permissions or _api_controller.permission_classes
```

Es decir, **las permisos declarados a nivel de ruta reemplazan la lista del controlador**. Consecuencia práctica: una ruta sensible debe declarar **todas** las puertas que necesita, no solo la adicional. Un `permissions=[]` vacío no sustituye nada (la lista vacía es falsy y cae al valor del controlador).

**Nivel 3 — Propiedad (ownership).** `modules/salesianos_fest/presentation/ownership.py` implementa la autorización por titularidad, que es ortogonal al rol:

- El `responsable` de la inscripción puede actuar sobre ella.
- Un admin Django (`is_staff`/`is_superuser`) puede actuar sobre cualquier inscripción.
- Cualquier otro actor recibe `ForbiddenError` (403).
- Los recursos sin `inscripcion_id` propio (equipo, participación, asignación) se resuelven primero a su inscripción padre, para no duplicar la lógica por endpoint.
- La acreditación se autoriza por persona acreditada, no por inscripción: `check_acreditacion_access_or_admin`.
- La regla delega en `core.capacidades.es_admin`; no se reimplementa la definición de admin.

La cobertura efectiva de estos helpers no fue auditada endpoint por endpoint (ver sección 9).

---

## 7. Mapa de módulos

| Módulo | App Django | Prefijos HTTP que posee | Modelos | DI registrado |
|---|---|---|---|---|
| `modules.usuarios` | sí | `/auth`, `/auth/login`, `/personas` | Persona, Usuario, PerfilIngeniero | Sí |
| `modules.eventos` | sí | — (sin superficie HTTP) | Evento | Sí |
| `modules.commerce` | sí | — (sin superficie HTTP) | Compra | Sí |
| `modules.salesianos_fest` | sí | `/catalogo`, `/pases`, `/cotizaciones`, `/inscripciones`, `/equipos`, `/participaciones`, `/compras`, `/asignaciones`, `/acreditaciones`, `/acceso` | 20 (inscripcion, equipo, participacion, pase, paquete, compra_inscripcion, compra_pase, asignacion_cupo, acreditacion, control_acceso, …) | Sí |
| `modules.competencias` | sí | `/administracion/competencias`, `/administracion/competencias/encuentros`, `/competencias` | Competencia, Ronda, Encuentro, CompetenciaEquipo | Sí |
| `modules.administracion` | sí | `/administracion`, `/administracion/pases` | — (superficie de lectura agregada) | Sí |
| `modules.pagos` | sí | `/pagos` | Pago, AprobacionPagoManual | **No** (`PagosModule` comentado) |

Superficie HTTP registrada: **111 rutas** sobre 29 controladores (28 del proyecto + `NinjaJWTDefaultController` de la librería). Detalle completo en [02a-inventario-de-endpoints.md](02a-inventario-de-endpoints.md).

---

## 8. Trabajo en segundo plano

**No hay cola de tareas en uso.** `django_q` está instalado (`THIRD_PARTY_APPS`) y `Q_CLUSTER` está configurado (`backend/config/settings/base.py`), pero no existe ninguna llamada a `async_task` ni a `schedule()` en el código del proyecto: sólo aparecen dentro del propio paquete `django_q` instalado. Tampoco hay `qcluster` invocado desde el compose.

El trabajo en segundo plano se ejecuta hoy exclusivamente como **comandos de gestión** de `manage.py`:

| Comando | Módulo |
|---|---|
| `create_admin` | core |
| `reset_dev` | core |
| `seed_catalogo_fest` | salesianos_fest |
| `reconciliar_pagos` | salesianos_fest |
| `reparar_cupos` | salesianos_fest |
| `verificar_pases` | salesianos_fest |
| `auditar_genero_disciplinas` | salesianos_fest |
| `verificar_pagos` | pagos |
| `verificar_intentos_pago` | pagos |
| `seed_commerce` | commerce |
| `seed_admin`, `seed_colegiados`, `seed_perfiles_ingeniero_faltantes` | usuarios |

Son **13 comandos de gestión propios del proyecto** (11 bajo `backend/modules/*/management/commands/` y 2 bajo `backend/core/management/commands/`). Dos de ellos (`seed_colegiados`, `seed_perfiles_ingeniero_faltantes`) son inejecutables por imports rotos; ver [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) § 2.

Ninguno de ellos está disparado por un cron declarado en el repositorio: su ejecución depende de una llamada externa.

---

## 9. Estado verificado, vacíos y material obsoleto

### 9.1 Verificado contra el código y el runtime

- Registro centralizado con 28 `register_controllers`; orden significativo por prefijo compartido.
- 111 rutas HTTP registradas; 112 rutas declaradas en código (una sin registrar).
- Autenticación JWT global, `auth=None` en las rutas públicas.
- Reemplazo de permisos de ruta sobre los de controlador, verificado en la librería instalada.
- Mapa de 11 capacidades y tres niveles de actor.
- Sobre `ApiResponse` único; paginación con `PaginatedData` anidado.
- Catálogo `PUBLIC_ERROR_MESSAGES` y los 11 manejadores globales.
- `PagosModule` sin registrar en `INJECTOR_MODULES`.
- `django_q` instalado y configurado, sin uso en el código del proyecto.
- `backend/` es el árbol que construye `docker-compose.yml`; `Aplicacion/backend/modules/` está vacío.

### 9.2 Vacíos (no verificados o incompletos)

- **Cobertura de ownership no auditada ruta por ruta.** `ownership.py` expone cinco helpers; no se comprobó exhaustivamente cuáles de las ~20 rutas de FEST los invocan y cuáles dependen únicamente del permiso de rol.
- **`evento_id` en la ruta sin validar contra el evento activo.** El backend resuelve el evento activo desde `settings.EVENTO_ACTIVO_NOMBRE`, pero `/api/acreditaciones/{evento_id}/{persona_id}` recibe un `evento_id` en la ruta. No se verificó si ese parámetro se contrasta con el evento activo.
- **Paridad de esquemas backend ↔ frontend no verificada campo por campo.** El inventario registra el consumidor de cada ruta, pero no se hizo un diff `zod` ↔ Pydantic.
- **Dos respuestas sin tipar**: `POST /api/inscripciones/{inscripcion_id}/personas` y `POST /api/inscripciones/{inscripcion_id}/pool/asignar` declaran `ApiResponse` sin tipo de carga útil.
- **Baseline de tests no medido.** No se ejecutó la suite de `backend/`; sin una línea base no se puede distinguir una regresión de un fallo preexistente.
- **Contrato del worker sin verificar en el límite.** `worker/scraper/main.py` expone `GET /consultar/{documento}` y `GET /health`; el mapeo de indisponibilidad (503/504) hacia `RealConsultaExternaClient` no se comprobó, ni existe health check del scraper en el compose.
- **Campos de `MeOut` no leídos.** El flag `require_admin` que consume el frontend no se contrastó con la definición real del esquema.

### 9.3 Desviaciones de contrato y material obsoleto

| Elemento | Situación verificada | Referencia contractual |
|---|---|---|
| `core/exceptions.py`, manejador de `ValueError` | Devuelve `str(exc)` en la respuesta pública | `api-wrapper-presenter-contract.md` §8 |
| `core/exceptions.py`, catálogo | `NOT_FOUND`, `PERMISSION_DENIED`, `VALIDATION_ERROR` no están en `PUBLIC_ERROR_MESSAGES` | `api-wrapper-presenter-contract.md` §8 |
| `modules/salesianos_fest/presentation/controllers/*` | Llaman a selectores y flows desde el controller, con instanciación manual de `InscripcionSelector()` | `PLAN_REFACTORIZACION.md` §1.A/§1.D |
| `config/settings/base.py` | `PagosModule` comentado en `INJECTOR_MODULES` | `django-app-architecture-contract.md` §4.15 |
| `config/settings/base.py`, líneas 62-64 | El comentario dice que `modules.pagos` está «temporarily disabled in Fase 1» y que se re-enable en Fase 4, pero la app **está** en `LOCAL_APPS` y el módulo se registra en `config/api.py` | Comentario obsoleto |
| `config/settings/base.py`, línea 62 | El comentario menciona `modules.inscripciones.Inscripcion`; ese módulo no existe (la inscripción vive en `modules.salesianos_fest`) | Comentario obsoleto |
| `core/security.py` | Mantiene `SystemPermissions`, `CheckPermission` y `verify_user_permissions` (permisos Django con prefijo `core.`), en paralelo al mapa de capacidades | `django-app-architecture-contract.md` §10 |
| `modules/usuarios/presentation/controllers/ingeniero_habilitado_controller.py` | Controlador escrito y **no registrado**: `GET /api/ingenieros/habilitados/{cip}` es código muerto | — |
| `modules/commerce/domain/models` frente a `modules/salesianos_fest/domain/models/compra_inscripcion.py` y `compra_pase.py` | El agregado comercial tiene dos dueños | `api-wrapper-presenter-contract.md` §1 |
| `modules/pagos/domain/services/core/estado_operativo_pago_service.py` | Importa `modules.commerce.domain.constants` de forma directa, pese a que el puerto `IEstadoCompraOrdenPagoService` existe para evitarlo | `modules/commerce/di.py` |

### 9.4 Advertencia sobre documentos previos

Este documento y su par no asumen el contenido de documentos anteriores del repositorio. Las carpetas `doc/`, `doc_dev/`, `doc-dev/`, `docs/`, `docs-dev/` y `salesianos-fest-2026-main/` contienen material de épocas distintas del proyecto y **no** deben usarse como referencia de comportamiento actual. Todo lo afirmado aquí procede de `backend/` y de la introspección del runtime.

---

## 10. Documentos relacionados

En esta misma carpeta:

- [README.md](README.md) — índice navegable del conjunto documental.
- [00-cobertura-y-trazabilidad.md](00-cobertura-y-trazabilidad.md) — auditoría de cobertura, recuentos y checklist reejecutable.
- [01-arquitectura-y-runtime.md](01-arquitectura-y-runtime.md) — arquitectura general y runtime de la aplicación.
- [02a-inventario-de-endpoints.md](02a-inventario-de-endpoints.md) — inventario de endpoints validado contra el runtime.
- [02b-proposito-y-consumidores-de-endpoints.md](02b-proposito-y-consumidores-de-endpoints.md) — propósito, consumidores y efectos de cada endpoint.
- [03-frontend.md](03-frontend.md) — capa de frontend.
- [03a-paginas-publicas-y-compra.md](03a-paginas-publicas-y-compra.md) — fichas de las páginas públicas, de cuenta y de compra.
- [03b-paginas-administrativas-y-operativas.md](03b-paginas-administrativas-y-operativas.md) — fichas de las páginas administrativas y operativas.
- [04-datos-y-dominio.md](04-datos-y-dominio.md) — modelo de datos y dominio.
- [04a-seeds-y-datos-iniciales.md](04a-seeds-y-datos-iniciales.md) — mecanismos de siembra y datos iniciales.
- [05-flujos-end-to-end.md](05-flujos-end-to-end.md) — recorridos de extremo a extremo.
- [05a-matriz-pagina-flujo-endpoint-datos.md](05a-matriz-pagina-flujo-endpoint-datos.md) — matriz de trazabilidad página → flujo → endpoint → datos.
- [07-guia-para-ui-ux.md](07-guia-para-ui-ux.md) — guía para diseño de interfaz.

Contratos normativos (fuera de esta carpeta, en la raíz del repositorio): `contract/django-app-architecture-contract.md`, `contract/api-wrapper-presenter-contract.md`, `contract/next-app-architecture-contract.md`, `contract/TEST_ARCHITECTURE_CONTRACT.md`, `contract/PLAN_REFACTORIZACION.md`, `contract/SCHEMA_DRY_INTENTION.md`, `contract/smart.md`.
