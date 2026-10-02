# Flujo de Implementación Frontend — Análisis de Gaps

> **Proyecto:** `salesianos`
> **Fecha:** 2026-09-19 (actualizado)
> **Tipo:** SDD Exploration — Doc de respaldo para implementación frontend
> **Fuente mockup:** `frontend-mokup/` (referencia UX/intención — **NO es contrato de API**)
> **Fuente backend:** Django modules `usuarios` + `inscripciones` (contrato real)

---

## ⚠️ Contrato Mandatory: `contract/smart.md`

> **IMPORTANTE:** Antes de implementar cualquier formulario, **OBLIGATORIO** leer `contract/smart.md`.

`contract/smart.md` es el contrato más importante para preservar la UI del mockup visualmente mientras se usa la arquitectura correcta de formularios.

### Principios Clave de Smart Fields

| Principio | Aplicación |
|-----------|------------|
| UI del mockup se copia visualmente | El mockup define intención UX/visual, NO lógica de formulario |
| Forms usan `GenericForm` + smart fields | Desacopla validación Zod de renderizado UI |
| Smart/custom field rendering | Para matchear cards/layout del mockup, no campos planos por defecto |
| `customFields` para casos domain-specific | Componentes hiper-específicos NO van al registro global |
| `DefaultFieldWrapper` para errores | Mensajes de error centralizados en `GenericInput`, no duplicados en componentes |

### Flujo: Mockup UI → Smart Field

```
Mockup (referencia visual)
  ↓ Copiar composición visual, estilos, layout
Componente Dumb (FileDropzone, etc.)
  ↓ Solo props: value, onChange, hasError
Capa Adaptadora (InputXxx.tsx con useController)
  ↓ Solo conexión react-hook-form
GenericInput.tsx (despachador por type registry)
  ↓ Validación Zod via GenericForm
Zod Schema (contrato de validación)
```

**El mockup NO se copia tal cual para lógica de formulario.**

---

## Nota sobre Flujo Simplificado Confirmado (2026-09-19)

El flujo de inscripción es **simplificado, sin complejidad BORRADOR/pre-registro**:

| Paso | Descripción |
|------|-------------|
| 1 | Usuario selecciona paquete |
| 2 | Usuario ingresa equipos, participantes, delegado y aceptaciones en frontend |
| 3 | Submit: frontend envía payload completo a `POST /inscripciones/` |
| 4 | Backend crea `Inscripcion` completa en un solo paso (estado inicial `RECIBIDA`) |
| 5 | Pago diferido — se implementa en módulo `pagos` futuro (no en el MVP actual) |

** mule-up is reference only**: El mockup define la intención UX/visual, no el contrato de API. Backend Django es la fuente de verdad.

---

## Resumen Ejecutivo

El frontend real (próximo a implementarse) consumirá el backend Django existente.
Este documento mapea cada pantalla del mockup contra los endpoints Django actuales,
identifica gaps y recomienda acciones antes de iniciar el desarrollo frontend.

**Estado general:** Los endpoints de ciclo de inscripción están esencialmente listos.
Las principales brechas son: catálogo de `promociones`, endpoint `me` y logout (si el frontend necesita verificar sesión), panel de admin, y alineación de payload para declaraciones/personas/acreditación.

---

## 1. Mapa de Rutas del Mockup vs. Endpoints Django

### 1.1 Auth

| Ruta mockup | Endpoint(s) mockup | Endpoint Django | Estado |
|------------|-------------------|-----------------|--------|
| `/register` | `POST /api/auth/register` | `POST /auth/register` | ✅ Listo |
| `/login` (tabs DNI/email) | `POST /api/auth/login` con `{identifier, password}` | `POST /auth/login/dni`, `POST /auth/login/email`, `POST /auth/login/username` | ⚠️ **Gap — interfaz diferente** |
| Post-login redirect | — | Redirect: admins→`/admin/dashboard`, responsables→`/dashboard` | ✅ Coincide con mockup |
| Post-register redirect | → `/inscripcion` (no `/dashboard`) | Mismo comportamiento | ✅ Coincide |
| Session check | `GET /api/auth/me` | **NO EXISTE** | 🔴 **Missing** |
| Logout | `POST /api/auth/logout` | **NO EXISTE** | 🔴 **Missing** |

**Login — estrategia clarified:**
El mockup muestra tabs DNI/email en una sola pantalla de login. El backend Django
tiene endpoints separados:
- `POST /auth/login/dni` — body `{dni, password}`
- `POST /auth/login/email` — body `{email, password}`
- `POST /auth/login/username` — body `{username, password}` (no usado en UI)

**Estrategia frontend:** El frontend real puede elegir el endpoint según el tipo
de identificador (detectar si contiene `@` → email, 8 dígitos → DNI), sin
necesidad de un endpoint unificado. Un endpoint `/auth/login` unificado es
opcional y no es requerido para continuar.

### 1.2 Catálogos

| Ruta mockup | Endpoint mockup | Endpoint Django | Estado |
|------------|----------------|-----------------|--------|
| Step 1 (promociones) | `GET /api/catalogs/promociones` | **NO EXISTE endpoint REST** | 🔴 **Missing** |
| Step 1 (bases) | `GET /api/catalogs/bases` | **NO EXISTE endpoint REST** | 🔴 **Missing** |
| Landing / Step 2 (disciplinas) | `GET /api/catalogs/disciplinas` | `GET /inscripciones/disciplinas/` | ✅ Listo |
| Landing (paquetes) | No llamada (informativo) | `GET /inscripciones/paquetes/` | ✅ Listo |
| Step 2 (categorías por disciplina) | `GET /api/catalogs/disciplinas/[id]/categorias` | `GET /inscripciones/disciplinas/{id}/categorias/` | ✅ Listo |
| Step 3 (paquete detalle) | `GET /api/catalogs/paquetes/[id]/disciplinas` | `GET /inscripciones/paquetes/{id}/disciplinas/` | ✅ Listo |
| Landing (eventos) | No llama a catálogo | `GET /inscripciones/eventos/` | ✅ Listo |

**Gap de catálogos — detalle crítico:**

#### `GET /api/catalogs/promociones` → MISSING
El mockup espera un endpoint de promociones. El wizard lo usa para el paso 1
(selección de promoción del responsable). El backend Django tiene el modelo `Promocion`
(FK en `Inscripcion`) pero **no tiene endpoint REST** para listarlo.

**Modelo existente:** `modules.inscripciones.domain.models.promocion.Promocion`
con campos `anio`, `nombre`, `colegio` ('ma'/'sjb'), `esta_activa`.

**Acción requerida:** Crear `PromocionController` con `GET /inscripciones/promociones/`
o dentro de un controlador de catálogos unificado.

#### `GET /api/catalogs/bases` → No requerido como endpoint REST
El mockup muestra "bases" como un catálogo, pero según la clarificación del usuario,
"bases" se refiere a la aceptación de condiciones/declaraciones del formulario
(aceptación de términos, declaración de aptitud física, consentimiento de imagen).

El backend modela estas aceptaciones en `PersonaAceptacion` (tabla auditable),
**no como un catálogo de documentos legales**.

**Decisión:**
- El frontend envía `acceptedBases=true`, `fitnessDeclaration=true`,
  `imageConsent=true` directamente como parte del payload de inscripción.
- `GET /bases` **no es requerido** actualmente.
- Si en el futuro se necesita versionado de documentos legales (ej., diferentes versiones
  de términos por año), se podría crear un modelo `Bases` con endpoint REST como
  **mejora opcional**.
- **`fitnessDeclaration` + `imageConsent`**: El backend **ya acepta estos campos**
  en `POST /inscripciones/`. No son gap — se envían en el payload directamente.

### 1.3 Inscripción

| Operación mockup | Endpoint mockup | Endpoint Django | Estado |
|-----------------|----------------|----------------|--------|
| Crear inscripción (wizard) | `POST /api/inscripcion` | `POST /inscripciones/` | ✅ Listo |
| Ver mi inscripción | `GET /api/inscripcion/mine` | `GET /inscripciones/` (lista del responsable) | ✅ Listo |
| Ver detalle | `GET /api/inscripcion/[id]` | `GET /inscripciones/{id}` | ✅ Listo |
| Cambiar estado (Comité) | `PATCH /api/inscripcion/[id]/estado` | `PATCH /inscripciones/{id}/estado` | ✅ Listo |
| Asignar delegado | `POST /api/inscripcion/[id]/delegado` | `POST /inscripciones/{id}/delegado` | ✅ Listo |
| Agregar participante | `POST /api/inscripcion/[id]/participantes` | `POST /inscripciones/{id}/participantes` | ✅ Listo |
| Admin: listar todas | `GET /api/admin/inscripciones` | **NO EXISTE** | 🔴 **Missing** |

**Gap de admin — detalle crítico:**
El mockup tiene `GET /api/admin/inscripciones` con paginación, filtros por estado,
y datos enrichecidos (equipos, jugadores, persona del responsable). El backend Django
**no tiene endpoint de admin** para listar todas las inscripciones.

**Acción requerida:** Crear `GET /inscripciones/admin/listar` o similar,
protegido con rol `admin_comite`/`admin_finanzas`.

---

## 2. Payload del Wizard — Análisis Detallado

### 2.1 Payload mockup (`CreateInscripcionSchema`)

```typescript
{
  userId: string,           // Override from session (no enviar tal cual)
  promocionId: string,     // FK a Promocion → MISSING endpoint
  fusionPromocionId?: uuid,
  basesId: string,          // MISSING endpoint + modelo
  paqueteMonto: number,     // Informativo (S/ 1350)
  teamName: string,
  acceptedBases: boolean,  // → PersonaAceptacion
  fitnessDeclaration: boolean, // → PersonaAceptacion (NO en schema Django!)
  imageConsent: boolean,    // → PersonaAceptacion (NO en schema Django!)
  deportistas: [{
    tipoDocumento, numeroDocumento, nombres, apellidos,
    genero?, telefono?,
    rolDisciplina: "Capitán"|"Delegado"|"Jugador",
    acreditacion,
    disciplinaIds: uuid[],   // Array — un jugador puede estar en varias
    shirtSize?
  }]
}
```

### 2.2 Payload Django (`InscripcionCreateIn`)

```python
{
  evento_id: str,          # Requerido
  paquete_id: str,         # Requerido
  promocion_id: str,      # FK
  fusion_promocion_id: str | None,
  observacion: str | None,
  accepted_bases: bool,   # ✅ Aceptado
  fitness_declaration: bool,  # ✅ Aceptado (2026-09-19)
  image_consent: bool,      # ✅ Aceptado (2026-09-19)
  equipos: [{
    disciplina_id: str,
    categoria_id: str | None,  # Nullable en el modelo
    nombre: str,
    participantes: [{
      persona_id: str,     # UUID — DEBE EXISTIR PREVIAMENTE
      rol: str = "JUGADOR",
      talle_camiseta: str | None
    }]
  }]
}
```

> **Nota (2026-09-19):** `fitness_declaration` e `image_consent` ahora son aceptados
> por el backend en `InscripcionCreateIn`. Ya no son gaps — se envían en el payload
> directamente.

### 2.3 Gaps del payload

| Campo mockup | Problema | Estado |
|-------------|----------|--------|
| `basesId` | No es un endpoint requerido. El backend usa `PersonaAceptacion` para estas aceptaciones. El frontend debe enviar `acceptedBases=true` directamente. | ✅ No es gap — aceptaciones van en payload |
| `fitnessDeclaration` | Backend ya los acepta en `POST /inscripciones/`. | ✅ **RESUELTO** — no es gap |
| `imageConsent` | Backend ya los acepta en `POST /inscripciones/`. | ✅ **RESUELTO** — no es gap |
| `deportistas[].disciplinaIds` (array) | El backend espera `participantes[].persona_id` (persona existente). El mockup envía datos de persona nueva (tipo, numero, nombres) que necesita ser creada o lookup. El flujo Django requiere que la persona ya exista. | 🔴 **GAP REAL** — requiere upsert por documento o lookup |
| `deportistas[].acreditacion` | El backend NO tiene campo `acreditacion` en `ParticipanteCreateIn`. | ⚠️ Media — solo si mockup lo requiere |
| `EquipoCreateIn.categoria_id` | El modelo `EquipoInscrito.categoria` es **nullable** (D7 decisión), pero el schema `EquipoCreateIn` lo pide como requerido. Esto debería corregirse en el backend. | ⚠️ Baja — inconsistency schema/modelo |

### 2.4 Contraste: `Promocion` como FK (cambio ya hecho)

Según `MODULAR_APPLY_TASKS.md` (apply I-SEEDS), `Inscripcion.promocion` ahora es FK
a `Promocion` en lugar de `CharField(10)`. Esto coincide con lo que el mockup espera
(`promocionId: uuid`). ✅

### 2.5 Contraste: `EquipoInscrito.categoria` optional

Según `BACKEND_DOMAIN_PLAN.md` y el schema `EquipoOut` con `categoria_id: str | None`,
la categoría es **opcional**. El frontend no debería requerir categoría al crear equipo.
✅ Confirmado — el mockup wizard step 2 no pide categoría explícitamente.

---

## 3. Paquetes — Cobertura de Seed

El mockup muestra en landing/Step 3:
- **Paquete regular**: S/ 1,350
- Límite: 15 participantes máximo
- Nombre: "Salesianos FEST 2026"

Según `MODULAR_APPLY_TASKS.md` sección I-SEEDS, el seed incluiría:
```
Paquete: "Salesianos FEST 2026", S/ 1350, max 15 participantes, válido hasta 2026-10-31
```

**Veredicto:** El seed planea el paquete correcto. Hay que verificar que el apply I-SEEDS
(o su equivalente) realmente lo haya creado.

---

## 4. Flujo Pantalla por Pantalla — Cobertura de Endpoints

### Pantalla: Landing (`/`)
- Datos: disciplinas, paquetes, evento. Endpoint: `GET /inscripciones/disciplinas/`,
  `GET /inscripciones/paquetes/`, `GET /inscripciones/eventos/`
- **Estado: ✅ Todosready**

### Pantalla: Register (`/register`)
- Submit: `POST /auth/register`
- **Estado: ✅ Listo**

### Pantalla: Login (`/login`)
- Submit: `POST /auth/login/email` o `/auth/login/dni` (frontend elige según tipo de identifier)
- **Estado: ✅ Listo — endpoints separados existen; frontend bifurca según input**

### Pantalla: Dashboard Responsable (`/dashboard`)
- Carga: `GET /inscripciones/` (lista filtrada por responsable)
- Si no tiene: botón a `/inscripcion`
- **Estado: ✅ Listo**

### Pantalla: Wizard Inscripción (`/inscripcion`)
- Step 1: `GET /inscripciones/promociones/` (MISSING si se necesita catálogo), aceptaciones van en payload
- Step 2: `GET /inscripciones/disciplinas/`, `GET /inscripciones/disciplinas/{id}/categorias/`
- Step 3: `GET /inscripciones/paquetes/`, `GET /inscripciones/paquetes/{id}/disciplinas/`
- Step 4: Solo informativa (checkboxes de declaración — van en payload)
- Submit: `POST /inscripciones/` (acepta `fitnessDeclaration` + `imageConsent`)
- **Estado: ⚠️ Step 1 — endpoint promociones condicional; aceptaciones ya resueltas**
- **Importante:** Usar `contract/smart.md` para construir los steps del wizard con GenericForm + smart fields

### Pantalla: Admin Comité (`/admin/comite/inscripciones`)
- Carga: `GET /api/admin/inscripciones` (MISSING)
- Cambio estado: `PATCH /inscripciones/{id}/estado` ✅
- **Estado: 🔴 Listado admin missing**

---

## 5. Inventario de Endpoints — Backend Django

### Auth / Usuarios

| Método | Path | Descripción | Estado |
|--------|------|-------------|--------|
| POST | `/auth/register` | Registro con Persona + Usuario + Aceptacion BASES | ✅ |
| POST | `/auth/login/dni` | Login por DNI | ✅ |
| POST | `/auth/login/email` | Login por email | ✅ |
| POST | `/auth/login/username` | Login por username (no usado en UI) | ✅ |
| GET | `/auth/me` | Obtener usuario autenticado actual | ⚠️ Solo si frontend necesita verificar sesión |
| POST | `/auth/logout` | Invalidar sesión | ⚠️ Solo si backend requiere blacklist de tokens |

### Catálogos — Inscripciones

| Método | Path | Descripción | Estado |
|--------|------|-------------|--------|
| GET | `/inscripciones/disciplinas/` | Listar disciplinas activas | ✅ |
| GET | `/inscripciones/disciplinas/{id}/categorias/` | Categorías por disciplina | ✅ |
| GET | `/inscripciones/paquetes/` | Listar paquetes activos | ✅ |
| GET | `/inscripciones/paquetes/{id}/disciplinas/` | Disciplinas de un paquete | ✅ |
| GET | `/inscripciones/eventos/` | Listar eventos activos | ✅ |
| GET | `/inscripciones/promociones/` | Listar promociones activas | 🔴 Missing |
| GET | `/inscripciones/bases/` | Catálogo de reglamento/bases | ⚠️ No requerido — ver nota sobre acceptedBases |

### Ciclo de Inscripción

| Método | Path | Auth | Descripción | Estado |
|--------|------|------|-------------|--------|
| POST | `/inscripciones/` | JWT | Crear inscripción completa | ✅ |
| GET | `/inscripciones/` | JWT | Lista del responsable | ✅ |
| GET | `/inscripciones/{id}` | JWT | Detalle de inscripción | ✅ |
| PATCH | `/inscripciones/{id}/estado` | JWT | Cambiar estado (Comité) | ✅ |
| POST | `/inscripciones/{id}/delegado` | JWT | Asignar delegado | ✅ |
| POST | `/inscripciones/{id}/participantes` | JWT | Agregar participante | ✅ |
| GET | `/inscripciones/admin/listar` | JWT (admin) | Admin: listar todas | 🔴 Missing |

---

## 6. Resumen de Gaps Prioritarios

| Prioridad | Gap | Impacto | Esfuerzo | Estado |
|-----------|-----|--------|----------|--------|
| 🔴 Alta | Lookup/creación de persona por documento | Backend espera `persona_id` existente; mockup envía datos de persona nueva | Medio | 🔴 Gap real |
| 🔴 Alta | `GET /inscripciones/promociones/` | Wizard step 1 no funciona sin catálogo (si se necesita catálogo separado) | Bajo | 🔴 Solo si catálogo es requerido |
| 🔴 Alta | `GET /inscripciones/admin/listar` | Panel de Comité no existe (solo si admin UI está en scope MVP) | Medio | 🔴 Deferido si no es MVP |
| ⚠️ Media | `acreditacion` en participantes | Backend no tiene campo `acreditacion` | Bajo | ⚠️ Solo si mockup lo requiere |
| ⚠️ Media | `GET /auth/me` y `POST /auth/logout` | Solo si el frontend necesita verificar/cerrar sesión explícitamente | Bajo | ⚠️ Opcional |
| ⚠️ Media | `EquipoCreateIn.categoria_id` requerido en schema pero nullable en modelo | Inconsistencia schema/backend | Bajo | ⚠️ Baja |

### Gaps Resueltos (backend actualizado)

| Gap | Resolución | Fecha |
|-----|------------|-------|
| `fitnessDeclaration` + `imageConsent` | Backend ya los acepta en `POST /inscripciones/` | 2026-09-19 |
| Login unificado | No requerido — endpoints separados existen y son OK | 2026-09-19 |
| `GET /bases` endpoint | No requerido — aceptaciones van en payload | 2026-09-19 |

---

## 7. Acciones Recomendadas Antes de Iniciar Frontend

### Acciones Requeridas (Gaps Reales)

1. **Deportistas: lookup/creación por documento** — Decidir estrategia:
   - Opción A: Crear persona dentro del flujo de inscripción (upsert por documento)
   - Opción B: Frontend hace lookup previo y usa `persona_id` existente
   - Requerido para que `POST /inscripciones/` funcione con datos de mockup
   - **(Requerido)**

2. **`GET /inscripciones/promociones/`** — Crear `PromocionController` simple con
   `GET /inscripciones/promociones/`, público.
   - Solo requerido si el wizard necesita catálogo de promociones
   - Si flow es package-first (sin catálogo), puede no requerirse
   - **(Condicional — revisar con user)**

### Acciones Opcionales (Según Scope MVP)

3. **Admin `GET /inscripciones/admin/listar`** — Crear endpoint con paginación,
   filtros por estado, y datos enriquecidos (responsable, conteo equipos,
   conteo jugadores). Proteger con `admin_comite`/`admin_finanzas`.
   - Solo si admin UI está en scope del MVP
   - **(Deferido si no es MVP)**

4. **`GET /auth/me`** — Crear endpoint que retorne el usuario y persona del JWT.
   - Solo si frontend necesita verificar sesión post-login explícitamente
   - **(Opcional)**

5. **`POST /auth/logout`** — Crear endpoint que invalide el token (si se usa
   blacklist) o simplemente sea un success (cliente borra JWT localmente).
   - **(Opcional — revisar con user)**

### Acciones Resueltas (Backend Ya Actualizado)

- ✅ **`fitnessDeclaration` + `imageConsent`** — Backend ya los acepta en `POST /inscripciones/`. No se requiere acción.
- ✅ **Login unificado** — No requerido. Endpoints separados `/auth/login/dni`, `/auth/login/email` existen y el frontend bifurca según tipo de identifier.
- ✅ **`GET /bases`** — No requerido. Las aceptaciones van en el payload directamente (`acceptedBases=true`, `fitnessDeclaration=true`, `imageConsent=true`).

---

## 8. Paquetes y Seed — Verificación Pendiente

El apply I-SEEDS (Pendiente según `MODULAR_APPLY_TASKS.md`) creará el seed de:
- Evento "Salesianos FEST 2026"
- 57 Promociones (1970-2026, colegio='ma')
- 4 Disciplinas
- Categorías por disciplina
- Paquete "Salesianos FEST 2026" S/ 1350, max 15

**Antes de frontend:** Verificar que este apply se haya ejecutado y los datos
estén en la BD.

---

## 9. Notas sobre Decisiones de Negocio Ya Confirmadas

| Decisión | Valor | Fuente |
|----------|-------|--------|
| `Promocion` como FK en `Inscripcion` | ✅ Hecho | MODULAR_APPLY_TASKS I-SEEDS |
| `EquipoInscrito.categoria` nullable | ✅ Confirmado | BACKEND_DOMAIN_PLAN.md D7 |
| `acceptedBases` → `PersonaAceptacion` | ✅ Modelo listo | BACKEND_DOMAIN_PLAN.md R3 |
| `Paquete.cantidad_maxima_participantes` cuenta personas DISTINCT | ✅ Confirmado | BACKEND_DOMAIN_PLAN.md D6 |
| Un equipo por inscripcion+disciplina (no por categoría) | ✅ Confirmado | BACKEND_DOMAIN_PLAN.md D7 |
| R11 protegida por UniqueConstraint en BD | ✅ Implementado | BACKEND_DOMAIN_PLAN.md |
| Login con endpoints separados (`/auth/login/dni`, `/auth/login/email`) | ✅ Confirmado | Clarificación 2026-09-19 |
| `GET /bases` no requerido; aceptaciones van en payload | ✅ Confirmado | Clarificación 2026-09-19 |
| `fitnessDeclaration` + `imageConsent` aceptados en `POST /inscripciones/` | ✅ Backend actualizado | Clarificación 2026-09-19 |
| Modelo `Bases` con versionado legal | ⚡ Opcional futuro | Solo si negocio pide documentos legales versionados |
| `contract/smart.md` es mandatory para implementación de formularios | ✅ Obligatorio | Contrato principal para preservar UI mockup |

---

*Documento generado como resultado de SDD explore phase para documentar gaps de implementación frontend.*
