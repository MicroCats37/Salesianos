# Patrón de 4 Capas — Django + Django Ninja

> **Fuente:** `contract/django-app-architecture-contract.md` + `contract/PLAN_REFACTORIZACION.md`
> **Propósito:** guía operativa del flujo Controller → Orchestrator → Flujo → Core para implementar nuevos endpoints REST.
> **Proyecto de referencia:** `modulos/identidad` (CAM)

---

## 1. La regla de oro

> **El controlador solo hace 3 cosas: parsear la entrada, llamar al Orchestrator, y retornar el éxito formateado por un Presenter.**

```
HTTP request
    ↓
┌────────────────────────────────────────────────────────────┐
│ 1. Controller   — Thin. Parsea + delega + success_response │  presentation/
└────────────────────────────┬───────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────┐
│ 2. Orchestrator — Fachada async. Valida + lanza HttpError  │  domain/services/orchestrators/
└────────────────────────────┬───────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────┐
│ 3. Flujo        — Async. transaction.atomic + composición  │  domain/services/flujos/
└────────────────────────────┬───────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────┐
│ 4. Core         — Sync. ORM puro. Cero lógica de negocio   │  domain/services/core/
└────────────────────────────┬───────────────────────────────┘
                             ↓
                          ORM Django
```

---

## 2. Responsabilidades por capa

| Capa | Carpeta | Sync/Async | Permite | Prohíbe |
|------|---------|-----------|---------|---------|
| **Controller** | `presentation/controllers/` | async (Ninja) | Parsear payload, llamar orchestrator, `success_response`, Presenter | `if`/`for`, ORM directo, `error_response` manual |
| **Orchestrator** | `domain/services/orchestrators/` | async | Validar reglas de negocio, `sync_to_async`, lanzar `HttpError`, delegar al flujo | ORM directo, `transaction.atomic`, lógica de DB compleja |
| **Flujo** | `domain/services/flujos/` | async | Componer múltiples Core calls, abrir `transaction.atomic`, retornar Result objects | ORM directo fuera de Core, decisiones de UI |
| **Core** | `domain/services/core/` | sync | `Model.objects.create/get/filter`, escribir lógica ORM pura | `if`/`for` de negocio, `transaction.atomic` propio, `@async def` |

---

## 3. Ejemplo end-to-end: `POST /auth/login`

### 3.1 Schema HTTP (`presentation/schemas/`)

```python
from core.types import BaseSchema

class LoginIn(BaseSchema):
    identifier: str        # email o DNI
    password: str

class LoginOut(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int
```

### 3.2 Controller (`presentation/controllers/auth_controller.py`)

```python
from core.responses import success_response
from modulos.identidad.domain.services.orchestrators.auth_orchestrator import AuthOrchestrator
from modulos.identidad.presentation.schemas.auth_schemas import LoginIn, LoginOut
from modulos.identidad.presentation.presenters.auth_presenter import AuthPresenter

@route.post("/login", response={200: ApiResponse[LoginOut]}, auth=None)
async def login(self, request, payload: LoginIn):
    # ✅ Solo 3 cosas: parsear (auto), delegar, retornar
    result = await self.auth_orchestrator.login_proceso(payload.identifier, payload.password)
    return success_response(AuthPresenter.present_login(result))
```

### 3.3 Orchestrator (`domain/services/orchestrators/auth_orchestrator.py`)

```python
from asgiref.sync import sync_to_async
from django.conf import settings
from ninja.errors import HttpError
from injector import inject

class AuthOrchestrator:
    @inject
    def __init__(self, auth_flujo: AuthFlujo):
        self.flujo = auth_flujo

    async def login_proceso(self, identifier: str, password: str):
        # ✅ Validación + raise HttpError
        if not identifier or not password:
            raise HttpError(400, "Credenciales incompletas")

        # ✅ sync_to_async envuelve las llamadas sync del flujo
        flujo_login = sync_to_async(self.flujo.ejecutar_login, thread_sensitive=True)

        # ✅ Asignación a variable (NO returns gigantes)
        result = await flujo_login(identifier, password)
        return result
```

### 3.4 Flujo (`domain/services/flujos/auth_flujo.py`)

```python
from django.db import transaction
from injector import inject
from modulos.identidad.domain.services.core.persona_core import PersonaCore
from modulos.identidad.domain.services.core.auth_core import AuthCore
from modulos.identidad.domain.results.auth_results import LoginResult

class AuthFlujo:
    @inject
    def __init__(self, auth_core: AuthCore, persona_core: PersonaCore):
        self.auth_core = auth_core
        self.persona_core = persona_core

    def ejecutar_login(self, identifier: str, password: str) -> LoginResult:
        # ✅ Sync. Único lugar donde se abre transaction.atomic si hay
        # múltiples writes que necesitan atomicidad compuesta.
        with transaction.atomic():
            user = self.auth_core.verificar_credenciales(identifier, password)
            tokens = self.auth_core.emitir_tokens(user)
            self.auth_core.registrar_sesion(user, tokens)
            return LoginResult(user=user, tokens=tokens)
```

### 3.5 Core (`domain/services/core/auth_core.py`)

```python
from modulos.identidad.domain.models import Usuario, Sesion

class AuthCore:
    """Sync. ORM puro. Cero lógica de negocio condicional."""

    def verificar_credenciales(self, identifier: str, password: str) -> Usuario:
        user = Usuario.objects.filter(
            email=identifier
        ).first() or Usuario.objects.filter(dni=identifier).first()

        # Las verificaciones de password son helpers puros (no lógica de negocio)
        if not user or not user.check_password(password):
            # ✅ raise HttpError también desde Core si la decisión es atómica al ORM
            from ninja.errors import HttpError
            raise HttpError(401, "Credenciales inválidas")
        return user

    def emitir_tokens(self, user: Usuario) -> dict[str, str]:
        # Delega a un helper puro (generador de JWT)
        from core.auth import _generar_token
        return {
            "access_token": _generar_token(user, ttl=settings.ACCESS_TTL),
            "refresh_token": _generar_token(user, ttl=settings.REFRESH_TTL),
        }

    def registrar_sesion(self, user: Usuario, tokens: dict) -> Sesion:
        return Sesion.objects.create(
            user=user,
            token_hash=_hash_token(tokens["access_token"]),
            expires_at=...
        )
```

---

## 4. Las 5 reglas absolutas

### Regla A — Controller sagrado (cero lógica)

```python
# ❌ PROHIBIDO en controller:
if not bungalow:
    return error_response(code="NOT_FOUND", status=404)
bungalow = await sync_to_async(Model.objects.get)(id)

# ✅ CORRECTO:
result = await self.orchestrator.listar_proceso(id)
return success_response(Presenter.present(result))
```

### Regla B — Las excepciones se lanzan, no se retornan

```python
# ❌ PROHIBIDO en controller:
return error_response(code="X", status=404)

# ✅ CORRECTO en orchestrator o core:
raise HttpError(404, "Bungalow no encontrado")
```

`backend/core/exceptions.py` captura `HttpError` globalmente y devuelve el envelope estándar.

### Regla C — Todo schema hereda de `BaseSchema`

```python
# ❌ PROHIBIDO:
class MiIn(BaseModel): ...

# ✅ CORRECTO:
class MiIn(BaseSchema):
    dni: str
    nombres: str
```

### Regla D — Cero returns gigantes en Orchestrator

```python
# ❌ PROHIBIDO:
return await sync_to_async(self.flujo.proceso(...)(...))

# ✅ CORRECTO:
result = await sync_to_async(self.flujo.proceso, thread_sensitive=True)(...)
return result
```

### Regla E — Imports absolutos siempre

```python
# ❌ PROHIBIDO:
from ...domain.services.orchestrators.auth_orchestrator import AuthOrchestrator

# ✅ CORRECTO:
from modulos.identidad.domain.services.orchestrators.auth_orchestrator import AuthOrchestrator
```

---

## 5. Los 3 patrones de firma del Controller

| Patrón | Cuándo usar | Firma |
|--------|-------------|-------|
| **1 — Dual (JSON o FormData)** | Imágenes opcionales o lote mixto | `async def(self, request)` + `parse_request_payload(...)` interno |
| **2 — FormData Estricto** | Archivos obligatorios | `async def(self, request, data: Form[...], files: File[list[UploadedFile]])` |
| **3 — JSON Estricto** | API REST clásica (solo JSON) | `async def(self, request, payload: MiIn)` con `payload` tipado |

**Regla:** La firma del controller SOLO acepta `self`, `request`, el payload (o `data`/`files`), y parámetros de ruta/query. **Cualquier otra variable suelta en la firma es un error arquitectónico.**

---

## 6. Presenter, Result y Schema: separación

```
┌─────────────────────────────────────────────────────────────────┐
│ presentation/schemas/  (HTTP)         Hereda de BaseSchema     │
│   *In, *Out                            Pydantic con Field()    │
└─────────────────────────────────────────────────────────────────┘
                                ↕ Presenter mapea
┌─────────────────────────────────────────────────────────────────┐
│ domain/results/  (interno)             Hereda de BaseModel puro │
│   *Result, *PaginatedResult            Datos ricos para el      │
│                                         controller              │
└─────────────────────────────────────────────────────────────────┘
                                ↕ Flujo retorna
┌─────────────────────────────────────────────────────────────────┐
│ domain/schemas/  (interno)            Hereda de BaseSchema      │
│   *CreateData, *UpdateData             DTOs entre servicios     │
└─────────────────────────────────────────────────────────────────┘
```

**Reglas:**
- `domain/schemas/` NO son HTTP; son contratos entre servicios.
- `domain/results/` son DTOs internos que agrupan varios modelos cuando el controller necesita datos compuestos (ej. `MeResult` = persona + perfil + configuración).
- El Presenter tiene `@staticmethod` o `@classmethod` solamente. **PROHIBIDO** que consulte DB.

---

## 7. Anti-patrones explícitos (checklist para code review)

| Anti-patrón | Cómo detectarlo |
|-------------|-----------------|
| ORM directo en controller | `grep -r "Model.objects" presentation/controllers/` |
| `if`/`for` en controller | Manual review |
| `error_response(...)` manual en controller | `grep -rn "error_response" presentation/controllers/` |
| `transaction.atomic()` en Core | `grep -rn "transaction.atomic" domain/services/core/` |
| Lógica de negocio en `models.py` | Manual review |
| Helper sin guión bajo | Naming convention |
| `...` en imports | `grep -rn "from \\.\\." modulos/` |
| `Repository` artificial | `ls infrastructure/repositories/` (debe estar vacío salvo caso justificado) |

---

## 8. Extender: agregar un nuevo endpoint (checklist)

```
1. Definir schemas HTTP en presentation/schemas/<modulo>_schemas.py
   ├── <Entidad><Operacion>In (hereda BaseSchema)
   └── <Entidad><Operacion>Out (hereda BaseSchema)

2. Definir Result interno si la respuesta es compuesta
   └── domain/results/<entidad>_results.py → <Entidad><Operacion>Result

3. Crear/actualizar método en Core (sync, ORM puro)
   └── domain/services/core/<entidad>_core.py

4. Crear/actualizar método en Flujo (async, transaction.atomic si hay joins)
   └── domain/services/flujos/<entidad>_flujo.py

5. Crear/actualizar método en Orchestrator (async, validaciones + raise)
   └── domain/services/orchestrators/<entidad>_orchestrator.py

6. Crear método en Presenter (staticmethod/classmethod)
   └── presentation/presenters/<entidad>_presenter.py

7. Crear endpoint en Controller (thin, success_response)
   └── presentation/controllers/<entidad>_controller.py

8. Registrar DI en di.py si es nuevo módulo

9. Tests:
   - test_unit_core.py (sync, sin DB → solo mockear ORM)
   - test_integration_flujo.py (con DB, transaction.atomic verificado)
   - test_e2e_controller.py (TestAsyncClient + JWT en headers)
```

---

## 9. Convenciones de naming (resumen)

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Servicio Core | `<Entidad>Service` o `<Entidad>Core` | `PersonaService`, `AuthCore` |
| Flujo | `<Modulo>Flujo` | `AuthFlujo`, `LiquidacionFlujo` |
| Orchestrator | `<Modulo>Orchestrator` | `AuthOrchestrator`, `ContactoOrchestrator` |
| Schema HTTP | `<Entidad><Operacion>In/Out` | `LoginIn`, `SolicitarCodigoCIPOut` |
| Schema interno | `<Entidad><Operacion>Data` | `PersonaCreateData`, `PrivilegioActivarData` |
| Result | `<Entidad><Operacion>Result` | `LoginResult`, `PrivilegioPaginatedResult` |
| Presenter | `<Entidad>Presenter` | `AuthPresenter` |
| Excepción | `<Nombre>Error` | `CipNotFoundError`, `ConflictError` |

---

## 10. Referencias

- `contract/django-app-architecture-contract.md` — contrato completo
- `contract/PLAN_REFACTORIZACION.md` — reglas estrictas + anti-patrones
- `contract/api-wrapper-presenter-contract.md` — wrappers tipados + presenter
- App de referencia: `modulos/identidad` (CAM)
