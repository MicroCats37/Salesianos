# SDD Exploration: usuarios Registration Flow

> **Proyecto:** `salesianos`
> **Fecha:** 2026-09-18
> **Objetivo:** Definir el flujo de registro de usuarios responsables para Salesianos FEST.
> **Alcance:** Módulo `backend/modules/usuarios/` — endpoint `/auth/register`, servicios y schemas.
> **Modo:** Exploration only — no implementation.

---

## 1. Estado Actual

### 1.1 Modelos (ya creados vía migración 0005)

| Modelo | Archivo | Estado | Notas |
|--------|---------|--------|-------|
| `Persona` | `domain/models/persona.py` | ✅ Creado | Campos: nombres, apellidos, tipo_documento, numero_documento, genero, telefono, whatsapp, contacto_emergencia_*, aseguradora_* |
| `PersonaAceptacion` | `domain/models/persona_aceptacion.py` | ✅ Creado | Auditable: BASES, APTITUD_FISICA, IMAGEN |
| `Usuario` | `domain/models/usuario.py` | ✅ Extendido | Tiene `persona_fk` (OneToOne, nullable) + `dni` legacy |

**Constraint existente:** `UniqueConstraint(fields=['tipo_documento', 'numero_documento'])` en `Persona`.

### 1.2 Auth Existente

| Endpoint | Método | Archivo | Estado |
|----------|--------|---------|--------|
| `/auth/login/username` | POST | `auth_controller.py` | ✅ Existe |
| `/auth/login/dni` | POST | `auth_controller.py` | ✅ Existe (usa `Usuario.dni` legacy) |
| `/auth/login/email` | POST | `auth_controller.py` | ✅ Existe |
| `/auth/register` | POST | — | ❌ **NO existe** — necesita crearse |

### 1.3 Servicios Existentes

| Servicio | Ubicación | ¿Existe? |
|----------|----------|----------|
| `AuthCoreService` | `domain/services/core/auth_core_service.py` | ✅ |
| `AuthFlujo` | `domain/services/flujos/auth_flujo.py` | ✅ |
| `AuthOrchestrator` | `domain/services/orchestrators/auth_orchestrator.py` | ✅ |
| `PersonaService` | — | ❌ **NO existe** — necesita crearse |
| `RegistroFlujo` | — | ❌ **NO existe** — necesita crearse |
| `RegistroOrchestrator` | — | ❌ **NO existe** — necesita crearse |

### 1.4 Constantes Existentes

| Constant | Valores | Ubicación |
|----------|---------|-----------|
| `TipoDocumentoChoices` | DNI, CE, PAS | `domain/constants.py` |
| `GeneroChoices` | M, F | `domain/constants.py` |
| `TipoAceptacionChoices` | BASES, APTITUD_FISICA, IMAGEN | `domain/constants.py` |

### 1.5 Excepciones Existentes

- `DocumentoDuplicadoError` (en `domain/exceptions.py`) — para cuando la Persona ya existe con ese documento.

---

## 2. Flujo de Registro — Reglas de Negocio

### 2.1 Campos de Entrada

| Campo | Tipo | Validación | Requerido |
|-------|------|------------|-----------|
| `email` | string | Formato email, max 120 | ✅ Sí |
| `password` | string | Mín 8 caracteres, max 120 | ✅ Sí |
| `confirmPassword` | string | Debe ser igual a `password` | ✅ Sí |
| `tipoDocumento` | enum | DNI, CE, PAS | ✅ Sí |
| `numeroDocumento` | string | Depende del tipo: DNI=8 dígitos, CE=9 dígitos, PAS=mín 4 alfanum | ✅ Sí |
| `nombres` | string | Máx 120 caracteres | ✅ Sí |
| `apellidos` | string | Máx 120 caracteres | ✅ Sí |
| `genero` | enum | M, F | ✅ Sí |
| `telefono` | string | Opcional; si se informa, exactamente 9 dígitos | ❌ No |
| `whatsapp` | string | Opcional; si se informa, exactamente 9 dígitos | ❌ No |
| `contactoEmergenciaNombre` | string | Opcional, máx 120 | ❌ No |
| `contactoEmergenciaTelefono` | string | Opcional; si se informa, exactamente 9 dígitos | ❌ No |
| `aceptacionVersion` | string | ej. "BASES-SF26-2026-09-06"; se guarda en `PersonaAceptacion` | ✅ Sí |
| `acceptedBases` | boolean | Debe ser `true` | ✅ Sí |

### 2.2 Validaciones Cruzadas

1. `password == confirmPassword` — si no coincide, error 422.
2. Longitud de `numeroDocumento` según `tipoDocumento`:
   - DNI: exactamente 8 dígitos (`^\d{8}$`)
   - CE: exactamente 9 dígitos (`^\d{9}$`)
   - PAS: mínimo 4 caracteres alfanum (`^[A-Za-z0-9]{4,}$`)
3. Si `telefono` o `whatsapp` presentes: exactamente 9 dígitos.
4. Si `contactoEmergenciaTelefono` presente: exactamente 9 dígitos.
5. `acceptedBases` debe ser `true`.

### 2.3 Árbol de Decisión (Business Flow)

```
1. Validar inputs (schema level)
        ↓
2. ¿Existe Persona con (tipo_documento, numero_documento)?
   → NO:  Ir a paso 3
   → SÍ:  Ir a paso 4
        ↓
3. Crear Persona nueva + Usuario + BASES_Aceptacion
   → Dentro de transaction.atomic
   → Retornar tokens
        ↓
4. ¿La Persona tiene un Usuario asociado? (persona_fk → usuario)
   → SÍ:  Lanzar ConflictError "Ya existe una cuenta con este documento"
   → NO:  Ir a paso 5
        ↓
5. Crear Usuario linked a Persona existente + BASES_Aceptacion
   → Dentro de transaction.atomic
   → Retornar tokens
```

### 2.4 Estrategia de Username

- El `username` del `Usuario` se genera como: `{tipo_documento.lower()}_{numero_documento}` (ej. `dni_12345678`).
- El `username` es único por constraint de BD.
- El usuario NO elige username — se genera automáticamente.

### 2.5 Estrategia de Password

- Se usa `Usuario.set_password(password)` para hash seguro.
- No se almacenan passwords en texto plano.

### 2.6 Estrategia de Aceptaciones

- Durante el registro, solo se registra `BASES` acceptance.
- `APTITUD_FISICA` e `IMAGEN` se capturan en el wizard de inscripción (paso 4).
- Se guarda `documento_version` (ej. "BASES-SF26-2026-09-06"), `aceptado_en`, `ip_address` (del request), `user_agent`.

---

## 3. Diseño de API

### 3.1 Endpoint

```
POST /auth/register
```

**Auth:** `auth=None` (público)

### 3.2 Request Schema (`RegisterIn`)

```python
class RegisterIn(BaseSchema):
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=8, max_length=120)
    confirmPassword: str = Field(..., description="Debe coincidir con password")
    tipoDocumento: Literal["DNI", "CE", "PAS"]
    numeroDocumento: str = Field(..., min_length=1, max_length=20)
    nombres: str = Field(..., max_length=120)
    apellidos: str = Field(..., max_length=120)
    genero: Literal["M", "F"]
    telefono: str | None = Field(None, min_length=9, max_length=9)
    whatsapp: str | None = Field(None, min_length=9, max_length=9)
    contactoEmergenciaNombre: str | None = Field(None, max_length=120)
    contactoEmergenciaTelefono: str | None = Field(None, min_length=9, max_length=9)
    aceptacionVersion: str = Field(..., description="Ej: BASES-SF26-2026-09-06")
    acceptedBases: bool = Field(..., description="Debe ser true")
```

### 3.3 Response Schema (`RegisterOut`)

Mismo que `LoginTokenOut`:

```python
class RegisterOut(BaseSchema):
    access_token: str
    refresh_token: str
    expires_at: datetime
    user: AuthUserOut
```

### 3.4 Códigos de Error

| Código | Condición |
|--------|-----------|
| 200 | Registro exitoso — retorna tokens |
| 409 | Documento ya registrado con usuario existente (`DocumentoDuplicadoError`) |
| 422 | Validación fallida (passwords no coinciden, formato documento, etc.) |

---

## 4. Arquitectura de Servicios

### 4.1 Cadena de Responsabilidad

```
Controller (async thin)
  → RegistroOrchestrator (async thin facade)
    → RegistroFlujo (async con transaction.atomic)
      → PersonaCoreService (sync, CRUD Persona)
      → AuthCoreService (sync, crear Usuario + JWT)
      → [dentro del atomic: crear Persona, crear Usuario, crear PersonaAceptacion]
```

### 4.2 Archivos a Crear

| Archivo | Descripción |
|---------|-------------|
| `domain/schemas/registro_result_schemas.py` | DTOs internos: `RegistroResult` |
| `domain/services/core/persona_core_service.py` | Sync CRUD para Persona |
| `domain/services/flujos/registro_flujo.py` | Async flow con transaction.atomic |
| `domain/services/orchestrators/registro_orchestrator.py` | Fachada async |
| `presentation/schemas/registro_schemas.py` | HTTP schemas `RegisterIn`, `RegisterOut` |
| `presentation/controllers/registro_controller.py` | Controller delgado |
| `presentation/presenters/registro_presenter.py` | Transformador |

### 4.3 DI Bindings (agregar a `di.py`)

```python
# Persona CRUD
binder.bind(PersonaCoreService, to=PersonaCoreService, scope=singleton)
# Registro
binder.bind(RegistroFlujo, to=RegistroFlujo, scope=singleton)
binder.bind(RegistroOrchestrator, to=RegistroOrchestrator, scope=singleton)
```

### 4.4 Controller Registration (en `config/api.py`)

```python
from modules.usuarios.presentation.controllers.registro_controller import RegistroController
api.register_controllers(RegistroController)
```

---

## 5. Preocupaciones de Migración/Datos

### 5.1 Nullable `Usuario.persona_fk`

- `persona_fk` es `null=True` para permitir la transición de usuarios legacy que no tienen Persona.
- **No es necesario modificar** — la migración 0005 ya dejó el campo nullable.
- La constraint `UniqueConstraint(fields=['tipo_documento', 'numero_documento'])` en `Persona` protege la unicidad.

### 5.2 Login DNI Legacy vs Nuevo

- El login actual `/auth/login/dni` usa `Usuario.dni` (campo legacy en `Usuario`).
- **Recomendación:** No cambiar el login DNI legacy todavía — podría romper usuarios existentes en BD.
- El nuevo registro crea `Persona` y vincula via `persona_fk`.
- Eventually: migrar el login DNI para usar `Persona.numero_documento` con `Persona.tipo_documento` cuando el sistema tenga suficientes usuarios con Persona.

### 5.3 Historial de Migraciones

- Migración `0005_add_persona_models.py` ya fue aplicada.
- Las nuevas migraciones para el flujo de registro solo agregan tablas/constraints nuevas, no modifican las existentes.

---

## 6. Edge Cases

| Caso | Comportamiento |
|------|----------------|
| Persona no existe | Crear Persona + Usuario + BASES acceptance |
| Persona existe sin usuario | Crear Usuario + BASES acceptance, vincular a Persona existente |
| Persona existe con usuario | Error 409: "Ya existe una cuenta con este documento" |
| Documento duplicado (misma Persona) | Error 409 del constraint UNIQUE |
| Password < 8 chars | Error 422 (validación de schema) |
| Passwords no coinciden | Error 422 (validación cross-field) |
| acceptedBases = false | Error 422 |
| Formato DNI incorrecto (no 8 dígitos) | Error 422 |
| IP/User Agent en registration | Se capturan para `PersonaAceptacion` |
| Email duplicado en `Usuario.email` | El campo `email` en `Usuario` tiene `unique=True` — error 409 de BD |

---

## 7. Edge Case: Email Duplicado

- El campo `Usuario.email` tiene `unique=True`.
- Si dos registros intentan usar el mismo email, la BD rechaza con `IntegrityError`.
- El flujo debe capturar esta excepción y retornar 409 con mensaje legible: "El email ya está registrado".

---

## 8. Consideraciones de Seguridad

1. **Passwords** — usar `set_password()` (bcrypt via Django).
2. **Rate limiting** — considerar limitando `/auth/register` (no implementar en MVP, documentar como mejora).
3. **IP/User Agent** — capturar para auditoría de aceptaciones.
4. **No exponer datos sensibles** — en respuesta no retornar password ni hash.

---

## 9. Dependencias de Otros Módulos

- El flujo de registro es **independiente** del módulo `inscripciones`.
- No requiere que existan `Disciplina`, `Paquete`, etc.
- La aceptación `BASES` se registra en `PersonaAceptacion` y es independiente del wizard de inscripción.

---

## 10. Recomendación: Username vs Documento como Identifier

El usuario dijo: "user is fine using DNI as username if it matches identity and simplifies auth".

**Recomendación adoptada:** Generar `username` automáticamente como `{tipo_documento.lower()}_{numero_documento}`.

- El usuario no necesita recordar ni elegir un username.
- El login puede seguir siendo por DNI (ya existe `/auth/login/dni`).
- El campo `username` queda populated para Completitud del modelo Django auth.

---

## 11. Resumen de Decisions

| # | Decisión | Tipo |
|---|----------|------|
| DR-1 | Username generado como `{tipo_documento.lower()}_{numero_documento}` | Diseño |
| DR-2 | Registration solo crea acceptance BASES (APTITUD_FISICA e IMAGEN van en wizard) | Diseño |
| DR-3 | `acceptedBases` debe ser `true` — validación en schema | Validación |
| DR-4 | `password == confirmPassword` — validación cross-field en schema | Validación |
| DR-5 | No modificar login DNI legacy inmediatamente | Conservación |
| DR-6 | Capturar IP y User Agent en `PersonaAceptacion` | Auditoría |
| DR-7 | Manejar `IntegrityError` de email único como 409 Conflict | Error handling |

---

## 12. Artefactos Generados

- Este documento: `doc/USUARIOS_REGISTRATION_FLOW_EXPLORE.md`
- Engram artifact: `sdd/salesianos-usuarios-registration-flow/explore` (type: architecture)

---

## 13. Próximo Paso

El `sdd-apply` debe crear:

1. `domain/schemas/registro_result_schemas.py` — DTOs internos
2. `domain/services/core/persona_core_service.py` — CRUD sync de Persona
3. `domain/services/flujos/registro_flujo.py` — flujo async con transaction.atomic
4. `domain/services/orchestrators/registro_orchestrator.py` — fachada async
5. `presentation/schemas/registro_schemas.py` — HTTP schemas
6. `presentation/controllers/registro_controller.py` — endpoint POST /auth/register
7. `presentation/presenters/registro_presenter.py` — transformador
8. Actualizar `di.py` con nuevos bindings
9. Actualizar `config/api.py` para registrar controller
10. Agregar tests de integración