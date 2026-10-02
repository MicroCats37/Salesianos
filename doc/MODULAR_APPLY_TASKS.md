# Plan de Tareas Modulares — SDD Apply

> **Proyecto:** `salesianos`
> **Fecha:** 2026-09-19 (actualizado desde 2026-09-18)
> **Objetivo:** Dividir el trabajo de implementación en batches pequeños, autónomos y verificables.
> **Contrato de testing:** `contract/TEST_ARCHITECTURE_CONTRACT.md` — usar patrón `liquidaciones/tests/` como gold-standard.
> **Workflow:** `sdd-explore` → `sdd-apply` (sin proposal/spec/design/tasks intermedio).
> **Regla CRÍTICA:** Todo `sdd-apply` debe leer los archivos de `contract/` antes de editar.

---

## Nota sobre Flujo Simplificado (2026-09-19)

El flujo de inscripción es **simplificado sin BORRADOR ni pre-registro**:
- Usuario selecciona paquete → completa datos → submit una vez
- Backend crea `Inscripcion` completa en estado `RECIBIDA`
- Pago diferido al módulo `pagos` futuro
- `Paquete` tiene precio único (`precio_regular`), sin `precio_preventa`/`fecha_fin_preventa`

---

## Convenciones de Ejecución

```bash
# Backend — Windows PowerShell
cd C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos\backend
.venv\Scripts\python.exe manage.py <comando> --settings=config.settings.development
```

---

## Estado Actual

| Apply | Descripción | Estado |
|-------|-------------|--------|
| U-REG-TEST | Tests de validación de documento para registro | ✅ COMPLETO |
| Bugfix: Persona sin Usuario | Registro con Persona existente sin usuario | ✅ COMPLETO |
| U-LOGIN-MIGRATE | Migrar login DNI a Persona.numero_documento | ⏳ DEFERIDO |
| I-SCAFFOLD | Crear estructura del módulo inscripciones | ✅ COMPLETO |
| I-MODELS | Modelos core de inscripciones | ✅ COMPLETO |
| I-VALIDATIONS | Servicios y validaciones de negocio | ✅ COMPLETO |
| I-API | Endpoints HTTP y controllers | ✅ COMPLETO |
| I-AUTH-FIX | Proteger endpoints de ciclo de vida con JWT auth | ✅ COMPLETO |
| I-SEEDS | Modelo Promocion + FK en Inscripcion + seed datos | 🔲 PRÓXIMO |
| I-TESTS | Tests de inscripciones (opcional) | 🔲 Pendiente |

---

## Apply U-REG-TEST ✅ COMPLETO

### Strict Document Validation + Registration Tests

**Goal:** Implementar tests de validación de documento para `POST /auth/register` siguiendo el patrón de `liquidaciones/tests/`.

**Status:** ✅ COMPLETO — tests implementados y verificables.

**Scope/Files:**
- `backend/modules/usuarios/tests/fixtures/factories.py` — `make_payload_registro*`
- `backend/modules/usuarios/tests/fixtures/usuarios_fixtures.py` — copiar de `liquidaciones`
- `backend/modules/usuarios/tests/fixtures/registro_fixtures.py` — fixture `registro_base_setup`
- `backend/modules/usuarios/tests/conftest.py` — re-exports
- `backend/modules/usuarios/tests/integration/conftest.py` — carga módulos
- `backend/modules/usuarios/tests/integration/test_registro_documento_validacion.py` — tests de validación
- `backend/modules/usuarios/tests/e2e/conftest.py` — carga módulos
- `backend/modules/usuarios/tests/e2e/test_e2e_registro.py` — tests E2E

**Out of Scope:**
- Implementación del endpoint `/auth/register` (ya existe)
- Modificación de servicios existentes de auth
- Tests de login (ya existen)

**Verification Commands:**
```bash
# Solo tests de registro
pytest backend/modules/usuarios/tests/integration/test_registro_documento_validacion.py -v

# Tests E2E
pytest backend/modules/usuarios/tests/e2e/test_e2e_registro.py -v

# Todos los tests de usuarios
pytest backend/modules/usuarios/tests/ -v

# Con coverage
pytest --cov=modules.usuarios backend/modules/usuarios/tests/
```

**Dependencies:** Ninguna — usa fixtures existentes de `liquidaciones`

---

## Bugfix: Persona existente sin Usuario ✅ COMPLETO

### Registro con Persona sin usuario vinculado

**Goal:** Permitir que una Persona sin usuario pueda crear una cuenta y quede vinculada.

**Status:** ✅ COMPLETO — cubierto por `test_registro_documento_duplicado_crea_usuario_logueado`.

**Flujo implementado:**
1. Persona existe con documento pero sin `usuario FK`
2. Registro con el mismo documento
3. Se crea `Usuario` vinculado a `Persona` existente
4. Se retorna token de autenticación

**Test:** `test_registro_documento_duplicado_crea_usuario_logueado` en `test_registro_documento_validacion.py`

---

## Apply U-LOGIN-MIGRATE ⏳ DEFERIDO

### Migrar Login DNI a Persona.numero_documento

**Goal:** Actualizar `/auth/login/dni` para usar `Persona.numero_documento` + `Persona.tipo_documento` en lugar de `Usuario.dni` legacy.

**Status:** ⏳ DEFERIDO — no es blocker para `inscripciones`.

**Motivo de defer:**
- El login actual funciona con `Usuario.dni` legacy
- La migración requiere verificar que todos los usuarios existentes tengan `Persona` vinculada
- El flujo de registro ya crea la vinculación correctamente
- Diferir hasta que sea necesario o haya tiempo para verificar datos existentes

**Scope/Files:**
- `backend/modules/usuarios/domain/services/flujos/auth_flujo.py` — método `_proceso_login_dni`
- `backend/modules/usuarios/domain/services/core/auth_core_service.py` — consulta de búsqueda
- `backend/modules/usuarios/domain/schemas/auth_result_schemas.py` — incluir `persona_id` en `AuthUserResult`

**Out of Scope:**
- Cambios en frontend (mockup)
- Migración de datos legacy (mover `Usuario.dni` a `Persona.numero_documento`)

**Dependencies:** Apply U-REG-TEST (validación de documento necesita el mismo schema)

---

## Apply I-SCAFFOLD 🔲 PRÓXIMO

### Crear Módulo `inscripciones` Scaffolding

**Goal:** Crear la estructura de carpetas y archivos base del módulo `inscripciones` siguiendo `contract/django-app-architecture-contract.md`.

**Must-read contracts/docs antes de editar:**
- `contract/django-app-architecture-contract.md` — reglas de estructura CAM
- `doc/BACKEND_DOMAIN_PLAN.md` — sección 4.2 (modelos de inscrições)
- `doc/BACKEND_CREATEAPP_PLAN.md` — pasos de creación

**Scope/Files:**
- `backend/modules/inscripciones/__init__.py`
- `backend/modules/inscripciones/apps.py` — `InscripcionesConfig`
- `backend/modules/inscripciones/models.py` — re-export
- `backend/modules/inscripciones/admin.py` — vacio inicialmente
- `backend/modules/inscripciones/di.py` — `InscripcionesModule` (vacío)
- `backend/modules/inscripciones/domain/__init__.py`
- `backend/modules/inscripciones/domain/constants.py`
- `backend/modules/inscripciones/domain/exceptions.py`
- `backend/modules/inscripciones/domain/models/__init__.py`
- `backend/modules/inscripciones/domain/schemas/__init__.py`
- `backend/modules/inscripciones/domain/services/__init__.py`
- `backend/modules/inscripciones/domain/services/core/__init__.py`
- `backend/modules/inscripciones/domain/services/flujos/__init__.py`
- `backend/modules/inscripciones/domain/services/orchestrators/__init__.py`
- `backend/modules/inscripciones/domain/selectors/__init__.py`
- `backend/modules/inscripciones/presentation/__init__.py`
- `backend/modules/inscripciones/presentation/schemas/__init__.py`
- `backend/modules/inscripciones/presentation/controllers/__init__.py`
- `backend/modules/inscripciones/presentation/presenters/__init__.py`
- `backend/modules/inscripciones/infrastructure/__init__.py`
- `backend/modules/inscripciones/infrastructure/selectors/__init__.py`
- `backend/modules/inscripciones/tests/__init__.py`
- `backend/modules/inscripciones/tests/conftest.py`
- `backend/modules/inscripciones/tests/fixtures/__init__.py`
- `backend/modules/inscripciones/tests/integration/__init__.py`
- `backend/modules/inscripciones/tests/e2e/__init__.py`
- `backend/modules/inscripciones/migrations/__init__.py`
- Registro en `config/settings/base.py` (`LOCAL_APPS`)
- Registro en `NINJA_EXTRA.INJECTOR_MODULES`
- Registro en `config/api.py` (controllers placeholder)

**Out of Scope:**
- Modelos concretos (Disciplina, Paquete, etc.)
- Servicios y lógica de negocio
- Tests

**Verification Commands:**
```bash
# Verificar que Django cargue el nuevo módulo
.venv\Scripts\python.exe manage.py check --settings=config.settings.development

# Verificar que no haya errores de importación
.venv\Scripts\python.exe manage.py shell -c "from modules.inscripciones.apps import InscripcionesConfig; print('OK')" --settings=config.settings.development
```

**Dependencies:** Ninguna

**Rollback/Containment:** Si falla, remover el registro del módulo en settings/api y eliminar la carpeta.

---

## Apply I-MODELS

### Implementar Modelos Core de `inscripciones`

**Goal:** Crear todos los modelos según `doc/BACKEND_DOMAIN_PLAN.md` — Disciplina, Categoria, Paquete, PaqueteDisciplina, Evento, Inscripcion, InscripcionDelegado, PersonaAceptacion, EquipoInscrito, ParticipacionDisciplina, ParticipanteInscripcion.

**Must-read contracts/docs antes de editar:**
- `contract/django-app-architecture-contract.md` — reglas de modelos
- `doc/BACKEND_DOMAIN_PLAN.md` — secciones 4.2, 4.3, 4.4, 4.5
- Reglas confirmadas: D1, D6, D7, R1-R11

**Scope/Files:**
- `backend/modules/inscripciones/domain/models/disciplina.py` — `Disciplina`, `Categoria`
- `backend/modules/inscripciones/domain/models/paquete.py` — `Paquete`, `PaqueteDisciplina`
- `backend/modules/inscripciones/domain/models/evento.py` — `Evento`
- `backend/modules/inscripciones/domain/models/inscripcion.py` — `Inscripcion`, `InscripcionDelegado`, `PersonaAceptacion`
- `backend/modules/inscripciones/domain/models/equipo.py` — `EquipoInscrito`, `ParticipacionDisciplina`, `ParticipanteInscripcion`
- `backend/modules/inscripciones/domain/models/__init__.py` — re-exports
- `backend/modules/inscripciones/domain/constants.py` — `EstadoInscripcionChoices`, `GeneroChoices`, `ModalidadChoices`, etc.
- `backend/modules/inscripciones/domain/exceptions.py` — `ConflictError`, `NotFoundError`, `BusinessError`
- `backend/modules/inscripciones/admin.py` — registro de ModelAdmins
- Migraciones: `makemigrations` + `migrate`

**Out of Scope:**
- Servicios y flujos de negocio
- Controllers y endpoints
- Tests

**Verification Commands:**
```bash
# Verificar que Django detecte los modelos
.venv\Scripts\python.exe manage.py check --settings=config.settings.development

# Verificar migrations
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.settings.development

# Aplicar migrations
.venv\Scripts\python.exe manage.py migrate --settings=config.settings.development

# Listar modelos creados
.venv\Scripts\python.exe manage.py shell -c "
from django.apps import apps
models = [(m.label, m._meta.model_name) for m in apps.get_models() if 'inscripcion' in m.label.lower()]
for label, name in sorted(models):
    print(f'{label}: {name}')
" --settings=config.settings.development
```

**Dependencies:** Apply I-SCAFFOLD (estructura existente)

**Rollback/Containment:** Las migrations son forward-only; si hay error, crear migration de corrección.

**Constraints a incluir:**
- `unique(tipo_documento, numero_documento)` en Persona (ya existe en `usuarios`)
- `unique(paquete, disciplina)` en PaqueteDisciplina
- `unique(inscripcion, disciplina)` en EquipoInscrito (D7)
- `unique(evento, disciplina, persona)` en ParticipacionDisciplina (R11)
- `unique(inscripcion)` en InscripcionDelegado

---

## Apply I-VALIDATIONS

### Implementar Validaciones de Servicio

**Goal:** Crear servicios core sync + flujos async con validaciones de negocio para package/disciplines/participants/delegate.

**Must-read contracts/docs antes de editar:**
- `contract/django-app-architecture-contract.md` — reglas de servicios
- `doc/BACKEND_DOMAIN_PLAN.md` — sección 4.5 (validación dos niveles)

**Scope/Files:**
- `backend/modules/inscripciones/domain/services/core/disciplina_service.py` — CRUD Disciplina
- `backend/modules/inscripciones/domain/services/core/paquete_service.py` — CRUD Paquete
- `backend/modules/inscripciones/domain/services/core/evento_service.py` — CRUD Evento
- `backend/modules/inscripciones/domain/services/core/inscripcion_service.py` — crear/actualizar estado
- `backend/modules/inscripciones/domain/services/core/equipo_service.py` — crear equipo
- `backend/modules/inscripciones/domain/services/core/participacion_service.py` — crear participación con validación R11
- `backend/modules/inscripciones/domain/services/core/participante_service.py` — crear/actualizar rol y talle
- `backend/modules/inscripciones/domain/services/flujos/crear_inscripcion_flujo.py` — `_crear_inscripcion_flujo`
- `backend/modules/inscripciones/domain/services/flujos/agregar_participante_flujo.py` — `_agregar_participante_flujo`
- `backend/modules/inscripciones/domain/services/flujos/cambiar_estado_inscripcion_flujo.py` — `_cambiar_estado_inscripcion_flujo`
- `backend/modules/inscripciones/domain/services/flujos/asignar_delegado_flujo.py` — `_asignar_delegado_flujo`
- `backend/modules/inscripciones/domain/services/orchestrators/inscripcion_orchestrator.py`
- `backend/modules/inscripciones/domain/selectors/inscripcion_selector.py`
- `backend/modules/inscripciones/di.py` — bindings

**Validaciones a implementar:**
1. **Nivel 1 (cupo por equipo/disciplina):** `Disciplina.min_jugadores` / `max_jugadores`
2. **Nivel 2 (capacidad paquete):** `Paquete.cantidad_maxima_participantes` — conteo DISTINCT de personas
3. **R11:** `unique(evento, disciplina, persona)` en ParticipacionDisciplina — protección en servicio + BD
4. **D7:** `unique(inscripcion, disciplina)` en EquipoInscrito
5. **Delegado:** debe ser `responsable` o participante en algún equipo de la inscripción
6. **Consistencia equipo↔participacion:** `participacion.evento == equipo.inscripcion.evento` y `participacion.disciplina == equipo.disciplina`

**Out of Scope:**
- Controllers y endpoints HTTP
- Tests

**Verification Commands:**
```bash
# Verificar que Django cargue sin errores
.venv\Scripts\python.exe manage.py check --settings=config.settings.development

# Verificar bindings DI
.venv\Scripts\python.exe manage.py shell -c "
from injector import Injector
from config.api import api
# Intentar resolver un servicio
print('DI bindings OK')
" --settings=config.settings.development
```

**Dependencies:** Apply I-MODELS

**Rollback/Containment:** Si falla, revertir cambios en servicios; modelos y BD quedan intactos.

---

## Apply I-API

### Endpoints y Controllers para Catálogos e Inscripción

**Goal:** Crear schemas HTTP, controllers y presenters para los endpoints de catálogos y ciclo de vida de inscripción.

**Must-read contracts/docs antes de editar:**
- `contract/django-app-architecture-contract.md` — reglas de presentation layer
- `contract/TEST_ARCHITECTURE_CONTRACT.md` — cuando se implementen tests
- `doc/BACKEND_DOMAIN_PLAN.md` — flujos 6.1-6.4

**Scope/Files:**
- `backend/modules/inscripciones/presentation/schemas/disciplina_schemas.py` — `DisciplinaIn`, `DisciplinaOut`
- `backend/modules/inscripciones/presentation/schemas/categoria_schemas.py` — `CategoriaIn`, `CategoriaOut`
- `backend/modules/inscripciones/presentation/schemas/paquete_schemas.py` — `PaqueteIn`, `PaqueteOut`
- `backend/modules/inscripciones/presentation/schemas/evento_schemas.py` — `EventoIn`, `EventoOut`
- `backend/modules/inscripciones/presentation/schemas/inscripcion_schemas.py` — `InscripcionIn`, `InscripcionOut`
- `backend/modules/inscripciones/presentation/schemas/equipo_schemas.py` — `EquipoIn`, `EquipoOut`, `ParticipacionIn`, `ParticipacionOut`, `ParticipanteIn`, `ParticipanteOut`
- `backend/modules/inscripciones/presentation/schemas/delegado_schemas.py` — `DelegadoIn`, `DelegadoOut`
- `backend/modules/inscripciones/presentation/controllers/disciplina_controller.py` — CRUD
- `backend/modules/inscripciones/presentation/controllers/paquete_controller.py` — CRUD
- `backend/modules/inscripciones/presentation/controllers/evento_controller.py` — CRUD
- `backend/modules/inscripciones/presentation/controllers/inscripcion_controller.py` — crear/listar/cambiar estado
- `backend/modules/inscripciones/presentation/presenters/inscripcion_presenter.py`
- Registro en `config/api.py`

**Endpoints a crear:**
- `GET /inscripciones/disciplinas` — listar disciplinas activas
- `GET /inscripciones/paquetes` — listar paquetes vigentes
- `GET /inscripciones/eventos` — listar eventos activos
- `POST /inscripciones/` — crear inscripción (wizard paso 1-4)
- `GET /inscripciones/` — listar inscripciones del responsable
- `GET /inscripciones/{id}` — detalle de inscripción
- `PATCH /inscripciones/{id}/estado` — cambiar estado (Comité)
- `POST /inscripciones/{id}/delegado` — asignar delegado

**Out of Scope:**
- Tests (son otro apply)
- Frontend (mockup)

**Verification Commands:**
```bash
# Verificar que Django cargue
.venv\Scripts\python.exe manage.py check --settings=config.settings.development

# Verificar URLs registradas
.venv\Scripts\python.exe manage.py show_urls --settings=config.settings.development 2>$null || echo "Instalar django-extensions para show_urls"
```

**Dependencies:** Apply I-VALIDATIONS (servicios existentes)

**Rollback/Containment:** Si falla, desregistrar controllers de `config/api.py`; servicios y modelos quedan intactos.

---

## Apply I-AUTH-FIX ✅ COMPLETO

### Proteger endpoints de ciclo de vida con JWT auth

**Goal:** Proteger los endpoints de ciclo de vida de inscripción con autenticación JWT, tras haberlos dejado temporalmente con `auth=None` durante I-API.

**Status:** ✅ COMPLETO

**Problema identificado:**
- Endpoints生命周期 (crear, listar, obtener detalle, cambiar estado, asignar delegado, agregar participante) tenían `auth=None`
- Cualquier usuario podía crear inscripciones sin autenticarse
- El helper `_get_persona_id_from_request` era inseguro porque `auth=None` no populaba `request.user`

**Solución implementada:**
1. **Endpoints protegidos con JWT + IsAuthenticated:**
   - `POST /inscripciones/` — `auth=JWTAuth(), permissions=[IsAuthenticated]`
   - `GET /inscripciones/` — `auth=JWTAuth(), permissions=[IsAuthenticated]`
   - `GET /inscripciones/{id}` — `auth=JWTAuth(), permissions=[IsAuthenticated]`
   - `PATCH /inscripciones/{id}/estado` — `auth=JWTAuth(), permissions=[IsAuthenticated]`
   - `POST /inscripciones/{id}/delegado` — `auth=JWTAuth(), permissions=[IsAuthenticated]`
   - `POST /inscripciones/{id}/participantes` — `auth=JWTAuth(), permissions=[IsAuthenticated]`

2. **Catálogos permanecen públicos:**
   - `GET /inscripciones/disciplinas` — `auth=None` ✅
   - `GET /inscripciones/paquetes` — `auth=None` ✅
   - `GET /inscripciones/eventos` — `auth=None` ✅

3. **Extracción de persona_id segura:**
   - `_get_authenticated_persona_id(request)` usa `request.user.persona_fk_id` directamente
   - Si el usuario tiene JWT válido pero no tiene Persona vinculada, lanza `BusinessError`
   - Ya no confía en payload/header/query para extraer identidad

4. **Manejo de errores:**
   - `NotFoundError` para recursos no encontrados
   - `BusinessError` para errores de negocio (sin persona, sin permiso)
   - Se lanzan excepciones, no se retornan error dicts

**Pattern de protección descubierto:**
```python
from core.security import JWTAuth
from ninja_extra.permissions import IsAuthenticated

@route.post("/", auth=JWTAuth(), permissions=[IsAuthenticated])
async def endpoint_protegido(self, request, ...):
    persona_id = request.user.persona_fk_id  # Direct access after JWT auth
    if not persona_id:
        raise BusinessError("Usuario sin persona vinculada...")
```

**Verification Commands:**
```bash
# Verificar que Django cargue
.venv\Scripts\python.exe manage.py check --settings=config.settings.development

# Verificar imports del controller
.venv\Scripts\python.exe manage.py shell -c "from modules.inscripciones.presentation.controllers.inscripcion_controller import InscripcionController; print('OK')" --settings=config.settings.development
```

**Dependencies:** Apply I-API (controllers implementados con auth=None temporal)

**Out of Scope:**
- Tests de auth (I-TESTS)
- Frontend

---

## Apply I-SEEDS

### Modelo Promocion + FK en Inscripcion + Seed de Datos

**Goal:** Crear el modelo `Promocion` como catálogo, cambiar `Inscripcion.promocion` de CharField a FK, y crear comando de seed con datos de referencia del mockup.

**Referencia:** Exploration artifact `sdd/salesianos-inscripciones-promocion-seeds/explore`

**Must-read contracts/docs antes de editar:**
- `contract/django-app-architecture-contract.md` — reglas de modelos
- `doc/BACKEND_DOMAIN_PLAN.md` — secciones 4.2 y decisiones D1/D6/D7
- `doc/FRONTEND_MOCKUP_FLOW.md` — seed data de promociones, disciplinas, categorías

**Scope/Files:**

1. **Modelo Promocion:**
   - `backend/modules/inscripciones/domain/models/promocion.py` — nuevo
   - `backend/modules/inscripciones/domain/constants.py` — agregar `ColegioChoices`
   - `backend/modules/inscripciones/domain/models/__init__.py` — re-exportar Promocion

2. **Modificar Inscripcion:**
   - `backend/modules/inscripciones/domain/models/inscripcion.py` — cambiar `promocion` CharField → FK + agregar `fusion_promocion` FK opcional

3. **Migración:**
   - `backend/modules/inscripciones/migrations/0002_add_promocion_and_modify_inscripcion.py` — nueva migration

4. **Seed command:**
   - `backend/modules/inscripciones/management/__init__.py`
   - `backend/modules/inscripciones/management/commands/__init__.py`
   - `backend/modules/inscripciones/management/commands/seed_inscripciones.py` — seed idempotente

5. **Admin:**
   - `backend/modules/inscripciones/admin/__init__.py` — registrar PromocionAdmin

6. **Actualizar capas dependientes:**
   - `backend/modules/inscripciones/domain/schemas/inscripcion_schemas.py` — `promocion: str` → `promocion_id: UUID`
   - `backend/modules/inscripciones/presentation/schemas/inscripcion_schemas.py` — actualizar
   - `backend/modules/inscripciones/domain/services/orchestrators/inscripcion_orchestrator.py` — actualizar signatures
   - `backend/modules/inscripciones/domain/services/flujos/crear_inscripcion_flujo.py` — actualizar flujo
   - `backend/modules/inscripciones/domain/services/core/inscripcion_service.py` — actualizar
   - `backend/modules/inscripciones/presentation/controllers/inscripcion_controller.py` — endpoint POST
   - `backend/modules/inscripciones/presentation/presenters/inscripcion_presenter.py` — incluir datos de promocion
   - `backend/modules/inscripciones/tests/fixtures/factories.py` — actualizar factory

**Seed data a crear (idempotente):**

| Concepto | Valores |
|----------|---------|
| Evento | "Salesianos FEST 2026", 2026-10-01 a 2026-10-31, activo |
| Promociones | 1970 a 2026 (57 registros), colegio='ma', activa=True |
| Disciplinas | fulbito_var (M, 12), fulbito_dam (F, 12), voley_mix (X, 12), basket_var (M, 10) |
| Categorías | Junior/Senior/Master/Super Master por disciplina (ver FRONTEND_MOCKUP_FLOW.md) |
| Paquetes | "Salesianos FEST 2026", S/ 1350, max 15 participantes, valido hasta 2026-10-31 |

**Verificación:**
```bash
# Verificar que Django cargue
.venv\Scripts\python.exe manage.py check --settings=config.settings.development

# Verificar migrations
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.settings.development

# Aplicar migration
.venv\Scripts\python.exe manage.py migrate --settings=config.settings.development

# Ejecutar seed
.venv\Scripts\python.exe manage.py seed_inscripciones --settings=config.settings.development

# Verificar seed
.venv\Scripts\python.exe manage.py shell -c "
from modules.inscripciones.models import Promocion, Evento, Disciplina, Paquete
print(f'Promociones: {Promocion.objects.count()}')
print(f'Eventos: {Evento.objects.count()}')
print(f'Disciplinas: {Disciplina.objects.count()}')
print(f'Paquetes: {Paquete.objects.count()}')
" --settings=config.settings.development
```

**Dependencies:** Apply I-AUTH-FIX (ya completo)

**Out of Scope:**
- Tests (son apply separado I-TESTS)
- Frontend real (no mockup)
- Módulo de pagos

---

## Apply I-TESTS (Futuro)

### Tests de Integración para `inscripciones`

**Goal:** Implementar tests siguiendo el patrón de `liquidaciones/tests/`.

**Nota:** Este apply es opcional según el usuario. Si se solicita, seguir `contract/TEST_ARCHITECTURE_CONTRACT.md`.

---

## Orden Recomendada

```
1. Apply U-REG-TEST      → Tests de validación de documento          ✅ COMPLETO
2. Bugfix (Persona/User) → Registro con Persona sin usuario         ✅ COMPLETO
3. Apply I-SCAFFOLD      → Estructura del módulo inscripciones       ✅ COMPLETO
4. Apply I-MODELS        → Modelos core                             ✅ COMPLETO
5. Apply I-VALIDATIONS   → Servicios y validaciones                  ✅ COMPLETO
6. Apply I-API           → Endpoints HTTP                            ✅ COMPLETO
7. Apply I-AUTH-FIX      → Proteger endpoints con JWT                ✅ COMPLETO
8. Apply I-SEEDS         → Modelo Promocion + FK + seed              🔲 PRÓXIMO
9. Apply I-TESTS         → Tests (opcional, si se solicita)         🔲 Pendiente
```

**U-LOGIN-MIGRATE está DEFERIDO** — no es blocker para `inscripciones`.

---

## Decisión: ¿Batch de closure de usuarios?

**NO se necesita** un batch de closure antes de `inscripciones`.

Razones:
1. El flujo de registro funciona correctamente
2. Los elementos CIP legacy (`PerfilIngeniero`, CIP services, etc.) no bloquean `inscripciones`
3. La limpieza está documentada en `USUARIOS_MODULE_EXPLORE.md` si se necesita más adelante
4. Los elementos CIP pueden dejarse mientras no causen problemas

La limpieza puede ser un mantenimiento futuro, no un pre-requisito.

---

## Notas de Arquitectura

- **Comando base:** `.venv\Scripts\python.exe manage.py <comando> --settings=config.settings.development`
- **Contrato de testing:** `contract/TEST_ARCHITECTURE_CONTRACT.md` — seguir patrón `liquidaciones/tests/`
- **Migrations:** Siempre ejecutar `makemigrations` antes de `migrate`
- **Verificación mínima:** `manage.py check --settings=config.settings.development` después de cada apply
- **No usar `git stash`** — si hay cambios sin commitear, dejarlos en working tree y avisar al usuario
- **Regla CRÍTICA:** Todo `sdd-apply` debe leer los archivos de `contract/` antes de editar cualquier archivo del proyecto

---

## Artefactos

- Este documento: `doc/MODULAR_APPLY_TASKS.md`
- Engram artifact: `sdd/salesianos-modular-apply-tasks/explore` (type: architecture)
- Exploration artifact: `sdd/salesianos-inscripciones-promocion-seeds/explore` (type: architecture)
