# Contrato de Arquitectura Django — Proyecto CAM

> **Versión:** 1.0  
> **Fecha:**2026-06-08  
> **Inspiración:** `modulos/identidad` (centro-de-esparcimiento)  
> **Decisión clave:** Sin repository layer artificial para envolver el ORM de Django  
> **Proyecto:** CAM — `C:\Users\Usuario\Desktop\Aplicaciones\CIP\CAM\aplicacion`

---

## 1. Propósito de Este Contrato

Este documento establece las reglas de arquitectura para crear y mantener Django apps/módulos dentro del proyecto CAM. No es un mandato de "todo o nada" — es un marco práctico que:

1. Captura los patrones probados en la app de referencia `modulos/identidad`.
2. Elimina las capas que no aportan valor real (DDD puro innecesario).
3. Permite que cada módulo evolucione sin costo inicial por ceremonial.
4. Sirve como checklist para validar nuevas apps antes de merged.

**Decisión del usuario registrada:** El ORM de Django ya es la capa de persistencia. No crear repositorios/adapters solo para envolver el ORM salvo caso justificado.

---

## 2. Principios de Arquitectura

| # | Principio | Descripción |
|---|-----------|-------------|
| P1 | **Pragmatismo sobre pureza** | Si DDD o un patrón no aporta valor concreto, no se usa. El ORM de Django es suficiente. |
| P2 | **Separación real de concerns** | La lógica de negocio NO vive en controllers ni en modelos. Tiene su propia capa. |
| P3 | ** async-first** | Los controllers son async (Django Ninja). La lógica de negocio usa async wrappers sobre operaciones sync cuando es necesario. Esta es la arquitectura establecida y verificada del proyecto. Para tests de controllers async usar SIEMPRE `ninja_extra.testing.TestAsyncClient` (o `django.test.Client`, que maneja async correctamente) — NUNCA `ninja.testing.TestClient` (no espera coroutines). |
| P4 | **Inyección de dependencias** | Usar `injector` para resolver dependencias. Nunca instanciar servicios a mano dentro de otros servicios. |
| P5 | **Transacciones explícitas** | `transaction.atomic()` se abre en el flujo (`flujo`) que necesita atomicidad, no en cada servicio individual. |
| P6 | **Modelos planos** | Los modelos Django son planos y anémicos — toda la lógica de negocio vive en servicios. |
| P7 | **Esquemas como DTOs** | Pydantic `BaseModel` para datos internos (servicios) y para HTTP (presenters transforman si hace falta). |
| P8 | **Permisos centralizados** | Los permisos de Django (is_staff, is_superuser, groups) se usan directamente. No inventar sistemas de permisos paralelos. |

---

## 2.1 Patrón async y testing (Decisión de Arquitectura Registrada)

**Decisión del usuario (2026-08-27):** los controllers son **async** — es la arquitectura establecida y verificada del proyecto.

### Cadena async coherente

- **Controller async** → **orchestrator async** → **flujo async** (`transaction.atomic`) → **core sync**.
- Los métodos del orchestrator que hacen queries ORM usan `sync_to_async(service.method)()`.
- Los flujos envuelven su método `_creacion_atomica` sync en `sync_to_async(...)()`.
- Los presenters son sync y se ejecutan en contexto async sin tocar ORM.
- **No mezclar:** prohibido un controller async que llame a un orchestrator sync, o viceversa.

### ⚠️ CRÍTICO: cliente de test correcto

| Cliente | ¿Funciona con controllers async? | Resultado si es incorrecto |
|---|---|---|
| `ninja_extra.testing.TestAsyncClient(api)` o `(ControllerClass)` | ✅ Sí | — |
| `django.test.Client` (con JWT en defaults) | ✅ Sí — maneja async internamente | — |
| `ninja.testing.TestClient` (sync) sobre controller async | ❌ NO | `AttributeError: 'coroutine' object has no attribute 'status_code'` |
| `ninja.testing.TestClient` sobre un `NinjaExtraAPI` | ❌ NO | `AttributeError: ... has no attribute 'build_routers'` |

**REGLAS:**
1. Para probar controllers async, usar `ninja_extra.testing.TestAsyncClient` con tests `async def` + `asyncio_mode="auto"`, **o** `django.test.Client` (tests `def` normales, el patrón establecido en los e2e de este proyecto).
2. `ninja.testing.TestClient` (sync) NO se usa con controllers async ni con `NinjaExtraAPI`.
3. Para un controller de `ninja_extra`, el cliente correcto es `ninja_extra.testing.TestClient`/`TestAsyncClient` (con la clase del controller o el API), no `ninja.testing.TestClient`.
4. Para controllers sync, usar `ninja_extra.testing.TestClient(ControllerClass)` (resuelve rutas relativas) o `TestClient(api)` con rutas absolutas.

---

## 3. Estructura de una Django App / Módulo CAM

```
modules/
└── <nombre_modulo>/
    ├── __init__.py              # Re-exporta modelos desde domain/models/
    ├── apps.py                  # Django AppConfig (name, label, verbose_name)
    ├── models.py                # Re-exporta desde domain/models/ (NUNCA lógica aquí)
    ├── admin.py                # Registro de ModelAdmins con forms custom
    ├── forms.py                 # Django Forms para Admin (solo si necesita)
    ├── di.py                    # Wiring de dependencias con injector (Module)
    │
    ├── domain/                  # ← lógica de negocio pura
    │   ├── __init__.py
    │   ├── constants.py # Choices de Django (TextChoices, etc.)
    │   ├── exceptions.py        # Excepciones de dominio específicas del módulo
    │   │
    │   ├── models/              # Modelos Django reales (uno por archivo)
    │   │   ├── __init__.py     # Re-exporta todos los modelos
    │   │   ├── persona.py
    │   │   ├── usuario.py
    │   │   └── ...
    │   │
    │   ├── schemas/             # DTOs internos Pydantic (para servicios, no HTTP)
    │   │   ├── __init__.py
    │   │   ├── persona_schemas.py
    │   │   └── ...
    │   │
    │   ├── results/            # DTOs de salida de servicios (result objects)
    │   │   ├── __init__.py
    │   │   └── ...
    │   │
    │   ├── ports/              # Interfaces ABC (solo si hay varias implementaciones)
    │   │   ├── __init__.py
    │   │   └── ...
    │   │
    │   ├── services/           # Lógica de negocio
    │   │   ├── __init__.py
    │   │   ├── core/           # Operaciones sync reutilizables (NO transaction.atomic propio)
    │   │   │   ├── __init__.py
    │   │   │   ├── persona_service.py
    │   │   │   ├── usuario_service.py
    │   │   │   └── ...
    │   │   ├── flujos/         # Flujos async completos (ABREN transaction.atomic)
    │   │   │   ├── __init__.py
    │   │   │   └── ...
    │   │   └── orchestrators/  # Fachadas async delgadas (solo delegan a flujos)
    │   │       ├── __init__.py
    │   │       └── ...
    │   │
    │   └── selectors/          # Interfaces de consulta ( ABC si hay varias impl)
    │       ├── __init__.py
    │       └── ...
    │
    ├── presentation/           # ← capa HTTP
    │   ├── __init__.py
    │   ├── schemas/            # Esquemas HTTP request/response (Ninja/Schema)
    │   │   ├── __init__.py
    │   │   └── ...
    │   ├── controllers/       # Controllers Ninja (薄 — solo delegan a orchestrators)
    │   │   ├── __init__.py
    │   │   └── ...
    │   ├── presenters/ # Transformadores de datos para respuestas HTTP
    │   │   ├── __init__.py
    │   │   └── ...
    │   └── routers.py         # Definición de rutas Ninja (opcional, puede ir en controller)
    │
    ├── infrastructure/         # ← implementaciones concretas
    │   ├── __init__.py
    │   ├── services.py # Implementaciones de ports (API externa, cache, etc.)
    │   ├── workers.py          # Tareas background (django-q2, celery, etc.)
    │   ├── repositories/      # VACÍO — no usar salvo caso justificado
    │   │   └── __init__.py
    │   └── selectors/         # Implementaciones concretas de selectors
    │       └── __init__.py
    │
    ├── tests/                  # Tests (ver TEST_ARCHITECTURE_CONTRACT.md)
    │   ├── __init__.py
    │   ├── integration/
    │   ├── e2e/
    │   └── factories.py       # Funciones puras dict (NO factory_boy)
    │
    ├── management/
    │   └── commands/           # manage.py commands
    │       └── ...
    │
    └── migrations/             # Migraciones Django
```

### Carpeta `domain/` vs `infrastructure/`

| Carpeta | Qué contiene | Ejemplo |
|---------|-------------|---------|
| `domain/` | Lógica pura, sin imports de Django externo (solo `django.db.models`) | `PersonaService`, `PrivilegioService`, `PrivilegioHelpers` |
| `infrastructure/` | Implementaciones que tocan APIs externas, cache, workers, o concrete query implementations | `CipClientSimulator`, `RealCipClient`, `DjangoCacheCodeVerifier` |

---

## 4. Responsabilidades por Archivo / Carpeta

###4.1 `models.py` (raíz del módulo)

**Regla:** Este archivo es un re-export puro desde `domain/models/`. No puede contener lógica.

```python
# ✓ CORRECTO
from .domain.models import Persona, Usuario, Privilegio

__all__ = ["Persona", "Usuario", "Privilegio"]

# ✗ INCORRECTO — lógica aquí
```

### 4.2 `domain/models/` (modelos Django)

- **Regla de agrupamiento:** Los modelos pueden agruparse en un mismo archivo cuando tienen una relación semántica fuerte y el agrupamiento mejora la mantenibilidad. Evitar archivos arbitrariamente grandes.
- El desarrollador decide los criterios de agrupamiento, pero deben ser coherentes y estar documentados por la semántica del archivo/módulo.
- Heredan de `BaseModel` (de `core.models`).
- **No contienen lógica de negocio** — solo campos, Meta, `__str__`, y métodos de conveniencia triviales.
- Proxy models para diferentes vistas lógicas (ej. `PersonaDatos`, `PersonaValidacion`).
- Custom managers para filtrar querysets (ej. `FamiliaManager`).
- Constraints a nivel de modelo (ej. `UniqueConstraint` con condición).

**Ejemplos de agrupamiento válido:**
- ✓ `proyecto.py` conteniendo `Proyecto` + sus proxy models + `ContactoProyecto` si están semánticamente ligados.
- ✓ `liquidacion.py` agrupando los modelos del agregado core de liquidación si son cohesivos.
- ✗ NO agrupar modelos sin relación solo porque están en la misma app.

### 4.3 `domain/services/core/` (servicios sync)

- **Son sync.** No usan `async def`.
- Operan sobre el ORM directamente.
- **NO abren `transaction.atomic()` internamente.** El caller (flujo) provee la transacción si necesita atomicidad compuesta.
- Se inyectan en flujos via `@inject` y `injector`.
- Pueden heredar de helper classes para lógica pura sin estado.

###4.4 `domain/services/flujos/` (flujos async)

- **Son async.** Usan `async def`.
- Contienen la lógica de un caso de uso completo (ej. `_proceso_registro_cip`).
- **ABREN `transaction.atomic()`** cuando hay que crear/actualizar múltiples entidades atómicamente.
- Reciben operaciones sync del core service y las envuelven en `sync_to_async` donde corresponde.
- Sin inyección propia — reciben el servicio core via constructor `@inject`.

### 4.5 `domain/services/orchestrators/` (fachadas async)

- **Son async y extremadamente delgados.**
- Un método público por endpoint del controlador.
- Solo delegan al flujo correspondiente: `return await self.flujo._proceso_*(...)`.
- **No contienen lógica de negocio.**
- Se inyectan en controllers via `@inject`.

###4.6 `domain/schemas/` (DTOs internos)

- Pydantic `BaseModel` para datos que fluyen entre servicios.
- **No son esquemas HTTP.** Los campos reflejan lo que la capa de servicios necesita, no lo que el cliente HTTP envía.
- Pueden usar `arbitrary_types_allowed=True` si necesitan aceptar instancias de modelos Django.
- Se nombran con sufijo que indica uso: `*CreateData`, `*Result`, `*PaginatedResult`.

### 4.7 `presentation/schemas/` (esquemas HTTP)

- Pydantic `Schema` de Ninja para request/response HTTP.
- Validación con `Field(...)` (min_length, max_length, etc.).
- Validators con `@field_validator` para reglas cruzadas (ej. `password == password_confirm`).
- Se nombran con sufijo: `*In`, `*Out`, `*Request`, `*Response`.

### 4.8 `presentation/controllers/` (controladores HTTP)

- Usan `@api_controller` o `@controller` de Django Ninja Extra.
- **Son-delgados:** solo reciben payload, llaman al orchestrator, retornan respuesta.
- Se inyecta el orchestrator via `@inject` en `__init__`.
- Un método por ruta.
- Permisos con `permissions=[AllowAny]` o `permissions=[IsAuthenticated]`.

### 4.9 `presentation/presenters/` (transformadores)

- Funciones o clases que transforman un result object (del dominio) en un schema HTTP.
- Ejemplo: `AuthPresenter.present_me(result)` → `MeOut`.
- Permiten que los servicios retornen objetos de dominio ricos sin acoplamiento a HTTP.

### 4.10 `infrastructure/services.py` (implementaciones de ports)

- Implementaciones concretas de las interfaces (`ports/`).
- Aquí viven los clientes HTTP (`httpx`), simulators para desarrollo (`*Simulator`), wrappers de cache, etc.
- Si solo hay una implementación y no hay intención de cambiarla, **no crear port** — implementar directamente en `infrastructure/services.py`.

### 4.11 `infrastructure/repositories/` (VACÍO)

**Regla explícita:** No crear repository layer solo para envolver el ORM de Django.

**Caso justificado para crear un repository:**
- Necesitas cambiar entre múltiples fuentes de datos (Django ORM ↔ API externa ↔ archivo).
- Necesitas cachear resultados del ORM con TTL.
- La query es extremadamente compleja y se reutiliza en muchos lugares.

**Caso NO justificado:** Solo quieres "ocultar" el ORM detrás de una interfaz porque "así se hace en DDD". El ORM de Django ya es una abstracción suficiente.

En la app de referencia `modulos/identidad`, `infrastructure/repositories/` está **vacío**.

### 4.12 `infrastructure/selectors/` (implementaciones de consulta)

- Si definiste un selector port en `domain/selectors/`, la implementación concreta va aquí.
- Si no definiste port, puedes poner queries complejas directamente en un archivo `selectors.py` dentro de `infrastructure/`.

### 4.13 `admin.py`

- Registro de `ModelAdmin` con `list_display`, `list_filter`, `search_fields`, `readonly_fields`, `fieldsets`.
- Proxy models para diferentes vistas de la misma entidad.
- Métodos helper para links a entidades relacionadas (ej. `persona_link`).
- Forms custom si el modelo no usa los campos estándar de Django User.

### 4.14 `forms.py`

- Solo si necesitas forms customizados para Django Admin (ej. `UsuarioCreationForm`, `UsuarioChangeForm`).
- No usar para forms de API — esos van en `presentation/schemas/`.

### 4.15 `di.py` (Dependency Injection Wiring)

- Define un `Module` de `injector` que hace el bind de ports a implementaciones.
- Usa `settings.DEBUG` para switch entre implementaciones (ej. `CipClientSimulator` vs `RealCipClient`).
- Se registra en `INJECTOR_MODULES` en `settings.py`.

### 4.16 `apps.py`

```python
from django.apps import AppConfig

class EntidadesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.entidades"
    label = "entidades"          # único, para evitar colisiones con auth u otros
    verbose_name = "Entidades"
```

---

## 5. Reglas de Naming

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Modelos Django | PascalCase singular | `Persona`, `Privilegio`, `ConfiguracionCategoria` |
| Campos de modelo | snake_case | `fecha_nacimiento`, `cantidad_beneficiarios_permitidos` |
| Choices (TextChoices) | PascalCase con sufijo semántico | `Genero`, `EstadoValidacion`, `EstadoPrivilegio`, `OrigenPrivilegio` |
| Constantes de módulo | UPPER_SNAKE_CASE | `MAX_ATTEMPTS`, `DEFAULT_TTL` |
| Servicios (core) | `<Entidad>Service` | `PersonaService`, `PrivilegioService`, `UserService` |
| Servicios (flujo) | `<Nombre>Flujo` | `AuthFlujo`, `PrivilegioFlujo` |
| Orchestrators | `<Nombre>Orchestrator` | `AuthOrchestrator` |
| Selectors | `<Entidad>Selector` | `PersonaSelector` |
| Schemas internos | `<Entidad><Operación>Data` | `PersonaCreateData`, `PrivilegioActivarData` |
| Schemas HTTP | `<Entidad><Operación>In/Out` | `SolicitarCodigoCIPIn`, `LoginResponseOut` |
| Result DTOs | `<Entidad><Operación>Result` | `PrivilegioResult`, `PrivilegioPaginatedResult` |
| Presenters | `<Entidad>Presenter` | `AuthPresenter`, `PrivilegioPresenter` |
| Ports (ABC) | `I<Nombre>` | `ICipClient`, `INotificationService`, `ITokenService` |
| Implementaciones | `<Nombre>Impl` o `<Nombre>Simulator` | `RealCipClient`, `CipClientSimulator` |
| Excepciones custom | `<Nombre>Error` | `CipNotFoundError`, `NotFoundError`, `ConflictError` |
| Módulo Django | snake_case plural | `identidad`, `entidades`, `ventas` |
| URL namespace | snake_case | `identidad:registro_cip`, `entidades:list` |

---

## 6. Reglas para Modelos Django

1. **Heredar de `BaseModel`** (de `core.models`) para obtener `id`, `created_at`, `updated_at`.
2. **No poner lógica de negocio en modelos** — solo campos, Meta, `__str__`.
3. **Usar `related_name` descriptivo** en ForeignKey: `persona.privilegios`, `usuario.perfil_ingeniero`.
4. **Constraints a nivel de modelo** para reglas de negocio (ej. `UniqueConstraint` con condición).
5. **`verbose_name` en todos los campos** para que el admin sea legible.
6. **Proxy models** para diferentes vistas de la misma entidad (filtro por estado, etc.).
7. **Custom managers** para querysets filtrados (ej. `Familia.objects` → solo `es_familiar=True`).
8. **`on_delete` explícito** siempre — `PROTECT` para relaciones que no se deben borrar en cascada.
9. **No usar `unique=True` + `null=True`** juntos — usar `unique_with` o contrainte explícita.
10. **Campo `estado`** como CharField con choices para máquinas de estado simples.

---

## 7. Reglas para API / Controladores (Django Ninja)

1. Usar `@api_controller("/ruta", tags=["..."])` de `ninja_extra`.
2. Permisos con `permissions=[AllowAny]` o `permissions=[IsAuthenticated]`.
3. Response schemas: `response={200: ApiResponse[MiSchemaOut]}`.
4. **No poner lógica en el controller** — delegar al orchestrator.
5. auth=None explícito en endpoints públicos: `auth=None`.
6. Usar `success_response()` del `core.responses` para wrapping estándar.
7. Params de query con `Query[...]` de Ninja.
8. Path params con `Path[...]` de Ninja.

---

## 8. Reglas para Services / Selectors

### Cuándo crear un service (core)

- La operación involucra múltiples modelos o necesita atomicidad.
- La operación se reutiliza en múltiples flujos.
- Hay branching de lógica (if/else de negocio).

### Cuándo crear un selector

- La query se reutiliza en múltiples lugares.
- La query es compleja (múltiples `select_related`, `prefetch_related`, annotate).
- Quieres poder mocking en tests.

### Estructura de un service (core) sync

```python
class PersonaService:
    def crear(self, data: PersonaCreateData) -> Persona:
        """Sync — para uso dentro de transaction.atomic."""
        payload = data.model_dump()
        return Persona.objects.create(**payload)

    def actualizar(self, persona: Persona, data: PersonaUpdateData) -> Persona:
        """Sync — para uso dentro de transaction.atomic."""
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(persona, field, value)
        persona.save()
        return persona
```

### Estructura de un flujo async

```python
class AuthFlujo:
    @inject
    def __init__(self, auth_core: AuthCoreService):
        self.auth_core = auth_core

    async def _proceso_login(self, identifier: str, password: str) -> LoginTokenResult:
        # 1. Validar
        # 2. Operaciones sync wrapped en sync_to_async
        # 3. transaction.atomic() si se necesitan múltiples writes
        # 4. Retornar result object
```

---

## 9. Regla Explícita: No Repository Layer para ORM

**Decisión arquitectónica registrada con el usuario:**

> "NO quiere DDD puro ni repositorios/adapters innecesarios para envolver el ORM de Django. Como es Django, el ORM ya sirve; simplificar trabajo."

### ¿Por qué no?

1. El ORM de Django (`Model.objects`) ya es una abstracción de persistencia bien diseñada.
2. Wrappear el ORM en un repository genera doble capa de mantenimiento sin beneficio.
3. Los tests pueden usar `pytest-django` con factories o `django.test.utils` directamente.
4. El acoplamiento a la sintaxis queryset de Django es aceptable — no hay beneficio en ocultarla.

### ¿Cuándo SÍ crear un repository?

| Caso | Ejemplo |
|------|---------|
| Múltiples fuentes de datos | Leer de API externa, escribir en Django ORM |
| Cache con TTL | `infrastructure/services.py` con `DjangoCacheCodeVerifier` |
| Query extremadamente compleja reutilizada | Selector con múltiples `select_related` y `annotate` |

### Caso de la app de referencia

`infrastructure/repositories/__init__.py` está **vacío**. No hay un solo repository. El único "repositorio" es el ORM directo.

---

## 10. Reglas para Admin, Permisos, Validaciones, Exceptions

### Admin

- `list_display`: máximo 6-7 campos para no sobrecargar.
- `list_display_links`: solo el campo identificador principal (dni, username, cip).
- `list_filter`: estados, fechas, campos categóricos.
- `search_fields`: dni, nombres, apellidos, email, teléfono.
- `readonly_fields`: `created_at`, `updated_at`, campos de auditoría.
- `date_hierarchy`: para campos de fecha cuando corresponde.
- `fieldsets` para organizar campos en grupos.
- Proxy models para separar vistas lógicas.

### Permisos

- Usar los grupos de Django (`groups`, `user_permissions`) directamente.
- `IsAuthenticated` de Ninja para endpoints que requieren login.
- Permisos custom en `core/permissions.py` si se necesitan a nivel de código.
- **No inventar sistemas de permisos paralelos** — no crear tablas de permisos custom a menos que el dominio lo requiera explícitamente.

### Validaciones

- **Modelo:** `clean()` en el modelo para validaciones que involucran múltiples campos; `constraints` de Django para reglas a nivel de DB.
- **Servicio:** validators en los schemas Pydantic internos (`domain/schemas/`).
- **HTTP:** `field_validator` y `model_validator` en los schemas de presentación (`presentation/schemas/`).
- **No duplicar validación** — si está en el modelo, no repetir en el servicio.

### Exceptions

- Usar las excepciones de `core/exceptions.py`: `NotFoundError`, `ConflictError`, `BusinessError`, `CipNotFoundError`.
- Agregar excepciones específicas del módulo en `domain/exceptions.py`.
- **No usar excepciones genéricas** (`Exception`, `ValueError`) como mecanismo de control — solo para errores realmente excepcionales.
- Los handlers en `core/exceptions.py` (`register_exception_handlers`) transforman excepciones en respuestas HTTP estandarizadas.

---

## 11. Reglas para Tests

```
tests/
├── __init__.py
├── integration/
│   ├── test_registro_cip_flow.py
│   └── ...
├── e2e/
│   └── test_e2e_*.py
└── factories.py    # Funciones puras que retornan dict payloads (NO factory_boy)
```

> **NOTA:** La fuente de verdad para tests es `contract/TEST_ARCHITECTURE_CONTRACT.md`. Esta sección se alinea con ella:
> - **NO usar `factory_boy`** — `factories.py` contiene funciones puras que retornan `dict`.
> - **NO usar `django.test.Client`** para controllers async — usar `ninja_extra.testing.TestClient` (sync) o `TestAsyncClient` (async).
> - **NO usar `unittest.mock.patch`** — usar fixture parameterization.
> - Estructura `integration/` + `e2e/`, sin `unit/`.

- **Integration tests:** Testan flujos completos contra DB real (usando `pytest-django` con `django_db` marker).
- **E2E tests:** Testan el flujo completo HTTP con el cliente del tipo correcto (ver sección 2.1).
- **Factories:** Funciones puras que retornan `dict` payloads, importables directamente. Una función por payload del módulo.
- **No testear Django ORM directamente** — testear through services.
- **Fixtures de Django** solo para setup global (perms, grupos); usar factories para datos de test.

---

## 12. Reglas para Migrations

1. **Una migration por cambio de modelo** — no acumular múltiples cambios en una sola.
2. **No editar migrations después de merged** — crear una nueva en su lugar.
3. **Nombres descriptivos:** `add_estado_to_persona`, `create_configuracion_categoria`, `add_unique_constraint_privilegio_persona`.
4. **Dependencias explícitas** si la migration depende de otra app (usar `dependencies` en `Migration` class).
5. **Historic models** (`simple_history`) si el proyecto lo requiere — ver `ConfiguracionCategoria` en referencia.

---

## 13. Cómo Crear una App Nueva Paso a Paso

### Paso 1: Crear estructura de carpetas

```bash
cd backend/modules/
python -c "import shutil; shutil.copytree('entidades', '<nuevo_modulo>')"
# Luego limpiar todo excepto __init__.py, apps.py, domain/, infrastructure/, presentation/, tests/
```

### Paso 2: Configurar `apps.py`

```python
from django.apps import AppConfig

class NuevoModuloConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.nuevo_modulo"
    label = "nuevo_modulo"
    verbose_name = "Nuevo Módulo"
```

### Paso 3: Definir modelos en `domain/models/`

- Crear `domain/models/__init__.py`.
- Modelos heredando de `BaseModel`, agrupados según relación semántica (ver sección 4.2).
- Definir choices en `domain/constants.py`.
- Re-exportar desde `models.py` raíz.

### Paso 4: Definir schemas internos en `domain/schemas/`

- `*CreateData`, `*UpdateData`, `*Result`, `*PaginatedResult`.
- Solo campos que la capa de servicios necesita.

### Paso 5: Crear servicios core en `domain/services/core/`

- Uno por entidad principal.
- Métodos sync: `crear`, `actualizar`, `obtener`, `listar`.
- **Sin `transaction.atomic()` propio.**

### Paso 6: Crear flujos en `domain/services/flujos/`

- Uno por caso de uso completo.
- Métodos `async _proceso_*`.
- `transaction.atomic()` donde corresponde.
- `sync_to_async` para llamar servicios core.

### Paso 7: Crear orchestrator en `domain/services/orchestrators/`

- Fachada delgada que recibe el flujo.
- Un método público por endpoint.
- Solo delegation.

### Paso 8: Crear schemas HTTP en `presentation/schemas/`

- `*In`, `*Out` para cada endpoint.
- Validators con `Field(...)`.

### Paso 9: Crear presenters en `presentation/presenters/`

- Transformar result objects → schemas HTTP.

### Paso 10: Crear controllers en `presentation/controllers/`

-薄 — solo delegan a orchestrator.
- Rutas con `route.get`, `route.post`, etc.

### Paso 11: Configurar `di.py`

```python
from injector import Module, singleton, Binder

class NuevoModuloModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(INuevoPort, to=RealNuevoImpl, scope=singleton)
```

### Paso 12: Registrar en `settings.py`

```python
INJECTOR_MODULES = [
    # ... otros módulos
    'modules.nuevo_modulo.di.NuevoModuloModule',
]
```

### Paso 13: Registrar en Admin (`admin.py`)

- Un `ModelAdmin` por modelo.
- Proxy models si hay diferentes vistas.

### Paso 14: Agregar tests

- Factory para cada modelo.
- Unit tests por service.
- Integration tests por flujo.

---

## 14. Qué NO Hacer

| # | Prohibido | Porque |
|---|-----------|---------|
| 1 | Poner lógica de negocio en `models.py` | Viola separación de concerns |
| 2 | Poner lógica en controllers | Controllers son puntos de entrada, no lógica |
| 3 | Crear repository solo para "envolver ORM" | El ORM ya es la abstracción de persistencia |
| 4 | `transaction.atomic()` en cada service | Quiebra atomicidad compuesta; el flujo debe controlarlo |
| 5 | Módulos con nombres duplicados (`auth`, `users`) | Usar `label` único en `AppConfig` |
| 6 | Usar `django.contrib.auth` User para usuarios de negocio | Crear modelo `Usuario` custom con `AbstractBaseUser` |
| 7 | Validación duplicada (modelo + servicio + HTTP) | Definir en un solo lugar y confiar en ello |
| 8 | Imports circulares | Estructurar con `domain.models` → `domain.services.core` → `domain.services.flujos` |
| 9 | Excepciones genéricas como control de flujo | Usar excepciones específicas del dominio |
| 10 | hardcodear URLs o credenciales | Usar `settings` (ej. `settings.CIP_API_BASE_URL`) |

---

## 15. Checklist de Aceptación para Nuevas Apps

Antes de marcar una nueva app como "completada", verificar:

- [ ] `apps.py` configurado con `name`, `label` único, `verbose_name`
- [ ] Modelos en `domain/models/`, heredan de `BaseModel`
- [ ] `models.py` raíz es re-export puro, sin lógica
- [ ] Choices definidos en `domain/constants.py` (TextChoices)
- [ ] Servicios core sync en `domain/services/core/`
- [ ] Flujos async en `domain/services/flujos/` con `transaction.atomic()` donde corresponde
- [ ] Orchestrators delgados en `domain/services/orchestrators/`
- [ ] Schemas internos en `domain/schemas/` (DTOs Pydantic)
- [ ] Schemas HTTP en `presentation/schemas/` (Ninja Schema)
- [ ] Controllers薄 en `presentation/controllers/`
- [ ] Presenters para transformación result → HTTP schema
- [ ] `di.py` configura bindings de injector
- [ ] `admin.py` registra modelos con configuración correcta
- [ ] `infrastructure/repositories/` vacío (salvo justificación documentada)
- [ ] Excepciones de dominio en `domain/exceptions.py`
- [ ] Tests: factories + unit + integration
- [ ] URLs registradas en el router principal del proyecto
- [ ] Settings actualizados si hay configuraciones nuevas

---

## 16. Notas de Mejoras Futuras

> Estas mejoras son deseables pero no críticas para el MVP. Se documentan para no perderlas.

### 16.1 Migrar a Python typing con Protocol en vez de ABC para ports

Los `ABC` son correctos pero `Protocol` de `typing` permite structural subtyping (duck typing) sin herencia explícita. Evaluar cuando el equipo esté cómodo.

### 16.2 Agregar OpenAPI docs centralizado

La app referencia tiene tags分散 en cada controller. Un plugin o middleware que genere docs consolidado mejoraría la DX.

### 16.3 Pipeline de migraciones automatizado

Actualmente las migraciones se hacen a mano. Un script que detecte cambios de modelos y genere migrations automáticamente (como `makemigrations` pero integrado en CI) ahorraría tiempo.

### 16.4 Schema versioning

Si la API crece, considerar versionado de schemas (`v1/`, `v2/`) para no romper clientes existentes. Por ahora no es necesario.

### 16.5 Eventos de dominio (Domain Events)

La app referencia no usa domain events. Si en el futuro se necesita auditoría o notificación entre módulos, considerar implementar un event bus simple con `django-q2` y topics.

### 16.6 Tests de contrato (Contract Tests)

Para módulos que se consumen entre apps (ej. si `identidad` es consumido por otra app), agregar contract tests con Pact o similar.

### 16.7 Desacoplar presenters

Actualmente los presenters viven en `presentation/presenters/`. Si la transformación se vuelve compleja, considerar moverla a un módulo dedicado o usar un mapper library como `bandit` o `modelmapper`.

---

## 17. Glosario de Patrones

| Patrón | Significado |
|--------|-------------|
| **BaseModel** | Modelo base de `core.models` con `id`, `created_at`, `updated_at` |
| **Core service** | Servicio sync reutilizable, sin transacciones propias |
| **Flujo** | Caso de uso async completo con posible `transaction.atomic()` |
| **Orchestrator** | Fachada async delgada que delega a flujo |
| **Port** | Interfaz ABC que define un contrato (ej. `ICipClient`) |
| **Presenter** | Transforma result objects de dominio en schemas HTTP |
| **Selector** | Interfaz o implementación de consultas complejas |
| **Proxy model** | Modelo Django que opera sobre la misma tabla con filtro lógico |
| **Custom manager** | Manager con `get_queryset()` filtrado para proxy models |
| **Choices** | `TextChoices` de Django para campos con valores limitados |
| **Factory** | Función pura que retorna un `dict` payload (en `factories.py`) — ver TEST_ARCHITECTURE_CONTRACT.md |

---

## 18. Referencias

- App de referencia: `C:\Users\Usuario\Desktop\Aplicaciones\CIP\centro-de-esparcimiento\backend\modulos\identidad`
- Contrato inspirado en: estructura real de `modulos.identidad` + decisiones del usuario registradas en esta sesión.
- Proyecto CAM: `C:\Users\Usuario\Desktop\Aplicaciones\CIP\CAM\aplicacion`
- Módulo `entidades` en CAM (estructura inicial): `backend/modules/entidades/`
