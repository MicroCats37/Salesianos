# SDD Exploration: usuarios Module Cleanup Plan

> **Proyecto:** `salesianos`
> **Fecha:** 2026-09-18
> **Objetivo:** Identificar qué conservar, remover o adaptar en el módulo `usuarios` existente para alinearlo con el dominio Salesianos (User + Persona central).
> **Alcance:** Solo el módulo `backend/modules/usuarios/` — sin tocar `inscripciones` ni otros módulos.

---

## 1. Estado Actual del Módulo `usuarios`

### 1.1 Estructura de Archivos

```
usuarios/
├── __init__.py                      # Re-exporta desde domain/models/
├── apps.py                          # UsuariosConfig (label="usuarios")
├── models.py                        # Re-exporta Usuario, PerfilIngeniero
├── di.py                           # UsuariosModule (injector bindings)
├── admin/
│   ├── __init__.py                  # Re-exporta todos los admins
│   ├── usuario_admin.py             # UsuarioAdmin (UserAdmin)
│   ├── perfil_admin.py              # PerfilIngenieroAdmin
│   └── catalogo_admin.py            # CapituloAdmin, EspecialidadIngenieroAdmin,
│                                    # EspecialidadRevisionAdmin, IngenieroHabilitacionAdmin
├── domain/
│   ├── models/
│   │   ├── __init__.py             # Re-exporta todos los modelos
│   │   ├── usuario.py              # Usuario (AbstractBaseUser + PermissionsMixin)
│   │   └── perfil_ingeniero.py     # PerfilIngeniero, Capitulo, EspecialidadIngeniero,
│   │                                # EspecialidadRevision, IngenieroHabilitacion
│   ├── services/
│   │   ├── core/
│   │   │   ├── auth_core_service.py        # Sync auth operations
│   │   │   ├── perfil_ingeniero_core_service.py  # PerfilIngeniero CRUD
│   │   │   └── ingeniero_habilitacion_core_service.py  # Habilitacion history
│   │   ├── flujos/
│   │   │   ├── auth_flujo.py               # Async login by username/dni/email
│   │   │   └── ingeniero_habilitado_flujo.py  # CIP verification flow
│   │   └── orchestrators/
│   │       ├── auth_orchestrator.py
│   │       └── ingeniero_habilitado_orchestrator.py
│   ├── schemas/
│   │   ├── auth_result_schemas.py   # AuthUserResult, LoginTokenResult
│   │   └── ingeniero_habilitado_schemas.py  # CipColegiadoData, IngenieroHabilitadoResult
│   ├── exceptions.py                # Placeholder vacío
│   └── services.py                  # Placeholder vacío
├── infrastructure/
│   ├── services.py                  # ICipClient, RealCipClient, CipClientSimulator
│   ├── selectors.py                 # Placeholder vacío
│   ├── repositories.py              # Placeholder vacío
│   └── models.py                    # Placeholder vacío
├── presentation/
│   ├── controllers/
│   │   ├── auth_controller.py       # AuthLoginController (async)
│   │   └── ingeniero_habilitado_controller.py  # IngenieroHabilitadoController
│   ├── schemas/
│   │   ├── auth_schemas.py          # LoginUsernameIn, LoginDniIn, LoginEmailIn, LoginTokenOut
│   │   └── ingeniero_habilitado_schemas.py  # HTTP schemas
│   ├── presenters/
│   │   ├── auth_presenter.py
│   │   └── ingeniero_habilitado_presenter.py
│   └── routers.py                  # Placeholder vacío
├── migrations/
│   ├── 0001_initial.py              # All models + historical tables
│   ├── 0002_remove_codigo_especialidad_revision.py
│   └── 0003_update_usuario_username.py
└── management/commands/
    ├── seed_colegiados.py
    └── seed_perfiles_ingeniero_faltantes.py
```

### 1.2 Modelos Existentes

| Modelo | Archivo | Descripción | ¿Mantener? |
|--------|---------|-------------|------------|
| `Usuario` | `usuario.py` | Custom user (AbstractBaseUser + PermissionsMixin). Campos: username, dni, email, nombres, apellidos | ✅ SÍ — adaptar |
| `PerfilIngeniero` | `perfil_ingeniero.py` | Perfil profesional ingeniero CIP. OneToOne → Usuario | ❌ REMOVER |
| `Capitulo` | `perfil_ingeniero.py` | Capítulo profesional CIP | ❌ REMOVER |
| `EspecialidadIngeniero` | `perfil_ingeniero.py` | Especialidad por capítulo CIP | ❌ REMOVER |
| `EspecialidadRevision` | `perfil_ingeniero.py` | Especialidad de cálculo para liquidaciones | ❌ REMOVER |
| `IngenieroHabilitacion` | `perfil_ingeniero.py` | Historial de búsquedas CIP | ❌ REMOVER |

### 1.3 Arquitectura de Servicios

El módulo sigue correctamente el contrato de arquitectura Django CAM:

```
Controller (async thin) → Orchestrator (async thin facade) → Flujo (async with transaction.atomic)
                                                                    ↓
                                                       Core Service (sync, no atomic)
```

- **Auth:** `AuthCoreService` → `AuthFlujo` → `AuthOrchestrator` → `AuthLoginController`
- **IngenieroHabilitacion:** `PerfilIngenieroCoreService` + `IngenieroHabilitacionCoreService` → `IngenieroHabilitadoFlujo` → `IngenieroHabilitadoOrchestrator` → `IngenieroHabilitadoController`

### 1.4 bindings DI en `di.py`

```python
# Auth
binder.bind(AuthCoreService, to=AuthCoreService, scope=singleton)
binder.bind(AuthFlujo, to=AuthFlujo, scope=singleton)
binder.bind(AuthOrchestrator, to=AuthOrchestrator, scope=singleton)

# CIP client (DEBUG → Simulator, else Real)
binder.bind(ICipClient, to=CipClientSimulator/RealCipClient)

# PerfilIngeniero
binder.bind(PerfilIngenieroCoreService, ...)
binder.bind(IngenieroHabilitacionCoreService, ...)
binder.bind(IngenieroHabilitadoFlujo, ...)
binder.bind(IngenieroHabilitadoOrchestrator, ...)
```

### 1.5 Dependencias Externas

- **`AUTH_USER_MODEL = "usuarios.Usuario"`** en `config/settings/base.py` — crítico, no romper.
- Controllers registrados en `config/api.py`:
  - `AuthLoginController` → `/api/auth/login/username|dni|email`
  - `IngenieroHabilitadoController` → `/api/ingenieros/habilitados/{cip}`
- Módulo registrado en `NINJA_EXTRA.INJECTOR_MODULES` como `modules.usuarios.di.UsuariosModule`
- Módulo en `LOCAL_APPS` como `modules.usuarios`

---

## 2. Elementos a REMOVER (específicos de la app anterior CIP)

### 2.1 Modelos Completos de PerfilIngeniero

| Archivo | Elemento | Razón de Remoción |
|---------|----------|-------------------|
| `domain/models/perfil_ingeniero.py` | `PerfilIngeniero` | Dominio CIP/ingeniería — no existe en Salesianos |
| `domain/models/perfil_ingeniero.py` | `Capitulo` | Dominio CIP — no existe en Salesianos |
| `domain/models/perfil_ingeniero.py` | `EspecialidadIngeniero` | Dominio CIP — no existe en Salesianos |
| `domain/models/perfil_ingeniero.py` | `EspecialidadRevision` | Dominio CIP/liquidaciones — no existe en Salesianos |
| `domain/models/perfil_ingeniero.py` | `IngenieroHabilitacion` | Dominio CIP — no existe en Salesianos |

### 2.2 Infraestructura CIP

| Archivo | Elemento | Razón |
|---------|----------|-------|
| `infrastructure/services.py` | `ICipClient`, `RealCipClient`, `CipClientSimulator` | API CIP externa — no existe en Salesianos |
| `infrastructure/services.py` | `CipDataError`, `CipServiceUnavailableError` | Excepciones específicas del cliente CIP |

### 2.3 Servicios de Ingeniero

| Archivo | Elemento | Razón |
|---------|----------|-------|
| `domain/services/core/perfil_ingeniero_core_service.py` | `PerfilIngenieroCoreService` | Solo tiene sentido con PerfilIngeniero |
| `domain/services/core/ingeniero_habilitacion_core_service.py` | `IngenieroHabilitacionCoreService` | Solo tiene sentido con IngenieroHabilitacion |
| `domain/services/flujos/ingeniero_habilitado_flujo.py` | `IngenieroHabilitadoFlujo` | Solo tiene sentido con CIP |
| `domain/services/orchestrators/ingeniero_habilitado_orchestrator.py` | `IngenieroHabilitadoOrchestrator` | Solo tiene sentido con flujo CIP |
| `domain/schemas/ingeniero_habilitado_schemas.py` | `CapituloData`, `CipColegiadoData`, `IngenieroHabilitadoResult` | Solo tiene sentido con CIP |
| `domain/schemas/ingeniero_habilitado_schemas.py` | Todo el archivo | Reemplazar por schemas de Persona |
| `presentation/controllers/ingeniero_habilitado_controller.py` | `IngenieroHabilitadoController` | Endpoint CIP — no existe en Salesianos |
| `presentation/schemas/ingeniero_habilitado_schemas.py` | HTTP schemas para CIP | No existe en Salesianos |
| `presentation/presenters/ingeniero_habilitado_presenter.py` | `IngenieroHabilitadoPresenter` | Solo tiene sentido con CIP |

### 2.4 Admin de Modelos de Ingeniero

| Archivo | Elemento |
|---------|----------|
| `admin/perfil_admin.py` | `PerfilIngenieroAdmin` — remover |
| `admin/catalogo_admin.py` | `CapituloAdmin`, `EspecialidadIngenieroAdmin`, `EspecialidadRevisionAdmin`, `IngenieroHabilitacionAdmin` — remover |
| `admin/__init__.py` | Actualizar re-exports |

### 2.5 Management Commands

| Archivo | Descripción | Razón |
|---------|-------------|-------|
| `management/commands/seed_colegiados.py` | Seed PerfilIngeniero desde JSON CIP | Dominio CIP |
| `management/commands/seed_perfiles_ingeniero_faltantes.py` | Seed CIP faltantes | Dominio CIP |

### 2.6 Migraciones

⚠️ **CRÍTICO:** Las migraciones existentes (`0001_initial.py`) crean todos los modelos incluyendo los que se removerán. **No se deben modificar ni eliminar migrations existentes** — eso rompería el historial de migrations en bases de datos ya migradas.

**Estrategia:** Las migraciones existentes se mantienen intactas. El trabajo de sdd-apply solo agrega nuevas migraciones para:
1. Agregar campo `persona_fk` a `Usuario`
2. Crear modelo `Persona` y `PersonaAceptacion`
3. La tabla `auth_historicalusuario` etc. ya fue creada por migrations anteriores — no se toca.

---

## 3. Elementos a ADAPTAR para Salesianos

### 3.1 Modelo `Usuario` — Adaptar

**Estado actual:**
```python
class Usuario(AbstractBaseUser, PermissionsMixin, DjangoAuthMixin, BaseModel):
    nombres = CharField(max_length=255, blank=True, null=True)
    apellidos = CharField(max_length=255, blank=True, null=True)
    email = EmailField(max_length=255, unique=True, blank=True, null=True)
    username = CharField(max_length=150, unique=True, validators=[username_validator])
    dni = CharField(max_length=8, unique=True, validators=[dni_validator], blank=True, null=True)
```

**Cambios requeridos:**
- Agregar `persona_fk = OneToOneField("usuarios.Persona", on_delete=PROTECT, related_name="usuario", null=True, blank=True)`
- **CONSERVAR** `username` (se usa para auth JWT — el login de Salesianos puede usar username o documentoid)
- **CONSERVAR** `email` (para comunicación)
- **REMOVER** `nombres`, `apellidos` → estos viven en `Persona`
- **REMOVER** `dni` → vive en `Persona.numero_documento` con tipo_documento

**Nota:** Los campos `nombres`, `apellidos`, `dni` existentes en `Usuario` pueden ficar como null temporalmente durante la transición, pero la dirección final es que `Persona` sea la fuente de verdad de la identidad de la persona.

### 3.2 Auth — Adaptar

**Lo que cambia:**
- `AuthFlujo._proceso_login_dni` y `_proceso_login_email` se conservan pero pueden adaptarse para buscar por `Persona.numero_documento` en lugar de `Usuario.dni`
- `AuthUserResult` debe incluir `persona_id` (UUID de Persona) en lugar de campos de persona redundantes
- El flujo de registro (`_proceso_registro`) aún no existe en el módulo — se creará con `Persona` en `inscripciones`

**Lo que NO cambia:**
- La arquitectura async (core → flujo → orchestrator → controller) es correcta y se conserva
- Los presenters y schemas HTTP de auth (`LoginUsernameIn`, `LoginDniIn`, `LoginEmailIn`, `LoginTokenOut`) se conservan

### 3.3 DI — Adaptar `di.py`

**Bindings a REMOVER:**
- `ICipClient` (y sus implementaciones)
- `PerfilIngenieroCoreService`
- `IngenieroHabilitacionCoreService`
- `IngenieroHabilitadoFlujo`
- `IngenieroHabilitadoOrchestrator`

**Bindings a CONSERVAR:**
- `AuthCoreService`
- `AuthFlujo`
- `AuthOrchestrator`

---

## 4. Elementos a CREAR para Salesianos

### 4.1 Modelo `Persona` (nuevo)

Según `BACKEND_DOMAIN_PLAN.md`:

```python
class Persona(BaseModel):
    class TipoDocumentoChoices(models.TextChoices):
        DNI = "DNI", "DNI"
        CE = "CE", "Carnet de Extranjería"
        PAS = "PAS", "Pasaporte"

    class GeneroChoices(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    nombres = CharField(max_length=255)
    apellidos = CharField(max_length=255)
    tipo_documento = CharField(max_length=3, choices=TipoDocumentoChoices.choices)
    numero_documento = CharField(max_length=20)
    genero = CharField(max_length=1, choices=GeneroChoices.choices)
    telefono = CharField(max_length=9, blank=True, null=True)
    whatsapp = CharField(max_length=9, blank=True, null=True)
    contacto_emergencia_nombre = CharField(max_length=120, blank=True, null=True)
    contacto_emergencia_telefono = CharField(max_length=9, blank=True, null=True)
    aseguradora_nombre = CharField(max_length=255, blank=True, null=True)
    aseguradora_numero_poliza = CharField(max_length=50, blank=True, null=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["tipo_documento", "numero_documento"], name="unique_tipo_numero_documento")
        ]
```

### 4.2 Modelo `PersonaAceptacion` (nuevo)

Según `BACKEND_DOMAIN_PLAN.md`:

```python
class PersonaAceptacion(BaseModel):
    persona = ForeignKey("usuarios.Persona", on_delete=CASCADE, related_name="aceptaciones")
    tipo_aceptacion = CharField(max_length=30)  # 'BASES', 'APTITUD_FISICA', 'IMAGEN'
    documento_version = CharField(max_length=50)  # ej. "BASES-SF26-2026-09-06"
    aceptado_en = DateTimeField()
    ip_address = GenericIPAddressField(blank=True, null=True)
    user_agent = CharField(max_length=500, blank=True, null=True)
```

### 4.3 Constants para Persona

```python
# domain/constants.py (nuevo o extender)
class TipoDocumentoChoices(models.TextChoices):
    DNI = "DNI", "DNI"
    CE = "CE", "Carnet de Extranjería"
    PAS = "PAS", "Pasaporte"

class GeneroChoices(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"

class TipoAceptacionChoices(models.TextChoices):
    BASES = "BASES", "Bases del evento"
    APTITUD_FISICA = "APTITUD_FISICA", "Certificado de aptitud física"
    IMAGEN = "IMAGEN", "Uso de imagen"
```

---

## 5. Verificación de Referencias Cruzadas (Riesgos de Deletion)

### 5.1 Referencias desde Otros Módulos

| Módulo | Referencia | Impacto |
|--------|------------|---------|
| `liquidaciones` | `PerfilIngeniero` en seeds y modelos | ⚠️ Verificar — puede depender de `PerfilIngeniero` para delegados/inspectores |
| `finanzas` | Posible uso de `PerfilIngeniero` | ⚠️ Verificar |

**Acción requerida:** Antes de aplicar la limpieza, ejecutar:
```bash
.venv\Scripts\python.exe -c "
import django; django.setup()
from django.apps import apps
for model in apps.get_models():
    for field in model._meta.get_fields():
        if hasattr(field, 'related_model') and field.related_model:
            if 'perfil' in field.related_model._meta.label.lower() or 'capitulo' in field.related_model._meta.label.lower() or 'especialidad' in field.related_model._meta.label.lower() or 'ingeniero' in field.related_model._meta.label.lower():
                print(f'{model._meta.label}.{field.name} → {field.related_model._meta.label}')
" --settings=config.settings.development
```

### 5.2 Referencias en Seeds y Commands

- `seed_colegiados.py` → depende de `PerfilIngeniero`, `Capitulo`, `EspecialidadIngeniero`, `IngenieroHabilitacion`
- `seed_perfiles_ingeniero_faltantes.py` → depende de `PerfilIngeniero`, `IngenieroHabilitacion`
- Posibles seeds en `liquidaciones/seeds/` que referencien CIP

### 5.3 Settings y Config

- `AUTH_USER_MODEL = "usuarios.Usuario"` — **NO MODIFICAR** — el modelo `Usuario` se conserva
- `modules.usuarios` en `LOCAL_APPS` — se conserva
- `modules.usuarios.di.UsuariosModule` en `NINJA_EXTRA.INJECTOR_MODULES` — se conserva (con bindings reducidos)

---

## 6. Plan de Cleanup/Adaptación para `sdd-apply`

### Fase U1: Agregar `Persona` y `PersonaAceptacion` (nuevos modelos)

**Archivos a crear:**
1. `domain/models/persona.py` — modelo `Persona`
2. `domain/models/persona_aceptacion.py` — modelo `PersonaAceptacion`
3. `domain/models/__init__.py` — agregar re-exports
4. `domain/constants.py` — Choices para `TipoDocumento`, `Genero`, `TipoAceptacion`
5. `domain/exceptions.py` — excepciones de dominio (ej. `DocumentoDuplicadoError`)

**Migración:**
```bash
.venv\Scripts\python.exe manage.py makemigrations usuarios --settings=config.settings.development
.venv\Scripts\python.exe manage.py migrate --settings=config.settings.development
```

### Fase U2: Agregar `persona_fk` a `Usuario`

**Cambio en `domain/models/usuario.py`:**
```python
persona_fk = models.OneToOneField(
    "usuarios.Persona",
    on_delete=models.PROTECT,
    related_name="usuario",
    blank=True,
    null=True,
)
```

**Migración:**
```bash
.venv\Scripts\python.exe manage.py makemigrations usuarios --settings=config.settings.development
.venv\Scripts\python.exe manage.py migrate --settings=config.settings.development
```

### Fase U3: Remover elementos CIP (limpieza)

**Archivos a ELIMINAR:**
```
domain/models/perfil_ingeniero.py
domain/services/core/perfil_ingeniero_core_service.py
domain/services/core/ingeniero_habilitacion_core_service.py
domain/services/flujos/ingeniero_habilitado_flujo.py
domain/services/orchestrators/ingeniero_habilitado_orchestrator.py
domain/schemas/ingeniero_habilitado_schemas.py
presentation/controllers/ingeniero_habilitado_controller.py
presentation/schemas/ingeniero_habilitado_schemas.py
presentation/presenters/ingeniero_habilitado_presenter.py
admin/perfil_admin.py
admin/catalogo_admin.py
infrastructure/services.py  (reemplazar con placeholder o contenido Salesianos)
management/commands/seed_colegiados.py
management/commands/seed_perfiles_ingeniero_faltantes.py
```

**Archivos a MODIFICAR:**
- `domain/models/__init__.py` — quitar re-exports de modelos CIP
- `admin/__init__.py` — quitar re-exports de admins CIP
- `di.py` — quitar bindings CIP
- `config/api.py` — desregistrar `IngenieroHabilitadoController`
- `presentation/controllers/__init__.py` — actualizar re-exports

**NO ELIMINAR migrations existentes.**

### Fase U4: Actualizar Auth para Salesianos

- Adaptar `AuthUserResult` para incluir `persona_id`
- Adaptar `AuthFlujo._proceso_login_dni` para buscar por `Persona.numero_documento`
- Crear schemas de registro de usuario con `Persona` (cuando se defina el flujo de registro)

---

## 7. Comandos de Verificación Post-Apply

```bash
# 1. Verificar que Django cargue sin errores
.venv\Scripts\python.exe manage.py check --settings=config.settings.development

# 2. Verificar que las apps estén instaladas
.venv\Scripts\python.exe manage.py check --deploy --settings=config.settings.development

# 3. Verificar que las tablas de modelos nuevos existan
.venv\Scripts\python.exe manage.py show_urls --settings=config.settings.development 2>$null || echo "show_urls no disponible"

# 4. Listar modelos registrados en admin
.venv\Scripts\python.exe manage.py shell -c "
from django.apps import apps
models = [(m.label, m._meta.model_name) for m in apps.get_models() if 'persona' in m.label.lower()]
for label, name in models:
    print(f'{label}: {name}')
" --settings=config.settings.development

# 5. Verificar que el endpoint de auth siga funcionando
# GET /api/auth/login/username (probar con credenciales existentes)

# 6. Verificar que el endpoint CIP ya NO exista (después de U3)
# GET /api/ingenieros/habilitados/000001 → debe dar 404
```

---

## 8. Resumen de Decisiones

| # | Decisión | Tipo |
|---|----------|------|
| D-U1 | Conservar `Usuario` (Auth) como está, agregar `persona_fk` | Adaptación |
| D-U2 | Crear `Persona` con campos según BACKEND_DOMAIN_PLAN.md | Nuevo |
| D-U3 | Crear `PersonaAceptacion` para aceptaciones auditable | Nuevo |
| D-U4 | Remover todo el subsystem CIP (PerfilIngeniero, Capitulo, CIP client, etc.) | Remoción |
| D-U5 | NO modificar migraciones existentes — agregar nuevas nomás | Conservación |
| D-U6 | Auth login por DNI/email sigue funcionando — adapta a buscar en Persona | Adaptación |
| D-U7 | Mantener arquitectura async (core → flujo → orchestrator → controller) | Conservación |

---

## 9. Artefactos Generados

- Este documento: `doc/USUARIOS_MODULE_EXPLORE.md`
- Engram artifact: `sdd/salesianos-usuarios-module-cleanup/explore` (type: architecture)
