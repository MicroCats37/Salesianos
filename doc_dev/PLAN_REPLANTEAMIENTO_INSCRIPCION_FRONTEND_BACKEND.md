# PLAN DE REPLANTEAMIENTO: Inscripción Frontend ↔ Backend

**Proyecto:** Salesianos FEST
**Artifact:** `sdd/salesianos-fest-inscription-contract-replan/explore`
**Fecha:** 2026-10-18
**Modo:** Auditoría read-only de contratos, spec, apply-progress y código parcial

> **Corrección posterior al Explore:** `PATCH /api/participaciones/{id}` sí existe y está cubierto por `test_actualizar_participacion`. Cualquier mención posterior que lo marque como inexistente es una referencia histórica del Explore y queda reemplazada por esta corrección.

---

## 1. RUTAS Y SCHEMAS ACTUALES IMPLEMENTADOS

### 1.1 Backend — Rutas de Inscripción

| Ruta | Método | Auth | Schema Request | Schema Response | Estado |
|------|--------|------|---------------|-----------------|--------|
| `/api/inscripciones/` | POST | JWT | `CrearInscripcionIn` (plano, sin equipos) | `InscripcionOut` | ✅ Existe — no usado por wizard |
| `/api/inscripciones/completa/` | POST | JWT | `CrearInscripcionCompletaIn` | `InscripcionCompletaOut` | ✅ Existe — endpoint atómico |
| `/api/inscripciones/` | GET | JWT | — | `list[InscripcionOut]` | ✅ Existe |
| `/api/inscripciones/{id}` | GET | AllowAny | — | `InscripcionOut` | ✅ Existe |
| `/api/inscripciones/{id}/detalle` | GET | AllowAny | — | `InscripcionDetailOut` | ✅ Existe |
| `/api/inscripciones/{id}` | PATCH | AllowAny | `ActualizarInscripcionIn` | `InscripcionOut` | ✅ Existe |
| `/api/inscripciones/{id}/personas` | POST | AllowAny | `AgregarPersonaIn` | `{participante: ParticipacionOut}` | ✅ Existe |
| `/api/inscripciones/{id}/personas/{pid}/retirar` | PATCH | AllowAny | — | `InscripcionPersonaOut` | ✅ Existe |
| `/api/participaciones/{id}` | PATCH | AllowAny | `ActualizarParticipacionIn` | `ParticipacionOut` | ✅ Existe |
| `/api/participaciones/{id}/retirar` | PATCH | AllowAny | — | `ParticipacionOut` | ✅ Existe |
| `/api/participaciones/{id}/mover` | PATCH | AllowAny | `MoverParticipacionIn` | `ParticipacionOut` | ✅ Existe |

### 1.2 Frontend — Contratos de Schema

**`InscripcionCompletaBackendPayload`** (frontend/src/features/inscripciones/schemas/inscripcion.schema.ts:90-104):
```typescript
export interface InscripcionCompletaBackendPayload {
  evento_id: string;
  paquete_id: string;
  promocion_id: string;
  fusion_promocion_id?: string | null;
  delegado_id?: string | null;
  cantidad: number;
  equipos: Array<{
    disciplina_id: string;
    categoria_id?: string | null;
    nombre: string;
  }>;
  estado?: string;
  observacion?: string;
}
```

**`toCompletaBackendPayload`** (frontend/src/features/inscripciones/schemas/inscripcion.schema.ts:106-127):
```typescript
export function toCompletaBackendPayload(
  data: InscripcionFormData,
  evento_id: string,
  cantidad: number,
  delegado_id?: string | null,
): InscripcionCompletaBackendPayload {
  return {
    evento_id,
    paquete_id: data.paquete_id,
    promocion_id: data.promocion_id,
    fusion_promocion_id: data.fusion_promocion_id ?? null,
    delegado_id: delegado_id ?? null,
    cantidad,
    equipos: data.equipos.map((eq) => ({
      disciplina_id: eq.disciplina_id,
      categoria_id: eq.categoria_id ?? null,
      nombre: eq.nombre,
    })),
    estado: "ACTIVA",  // ⚠️ PROBLEMA: backend default es "BORRADOR"
    observacion: undefined,
  };
}
```

### 1.3 Backend — `CrearInscripcionCompletaIn` (presentation/schemas/inscripcion_schemas.py:150-165)

```python
class CrearInscripcionCompletaIn(BaseSchema):
    evento_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    cantidad: int  # Required initial purchase quantity
    equipos: list[EquipoParaCrearIn]
    estado: str = "BORRADOR"  # Default es BORRADOR, frontend envía "ACTIVA"
    observacion: str = ""
```

---

## 2. DESAJUSTES FRONTEND ↔ BACKEND

### 2.1 Problemas Críticos Detectados

| # | Desajuste | Severidad | Fuente |
|---|-----------|-----------|--------|
| P1 | `PATCH /participaciones/{id}` para editar participante | ✅ RESUELTO | `test_actualizar_participacion` |
| P2 | `toCompletaBackendPayload` envía `estado: "ACTIVA"` pero el backend espera default `"BORRADOR"` | 🟡 HIGH | Código frontend |
| P3 | `agregarParticipantesAEquipo` solo usa `payload.participantes[0]?.persona_id` — frágil, envía array pero solo toma el primero | 🟡 MEDIUM | inscripcion.service.ts:286 |
| P4 | El wizard **hardcodea** `cantidad = selectedPaqueteDetail.minimo_compra_inicial ?? 1` — no hay input de cantidad para el usuario | 🔴 CRITICAL | InscripcionWizard.tsx:226 |
| P5 | El campo `delegado_id` se pasa como `null` cuando no existe, pero el backend lo maneja correctamente como Optional | 🟢 BAJA | toCompletaBackendPayload |

### 2.2 Análisis de `toCompletaBackendPayload`

**Problemas identificados:**

1. **Hardcodeo de `estado: "ACTIVA"`**: El backend tiene default `"BORRADOR"`. El frontend fuerza `"ACTIVA"`. Esto podría inconsistir con el flujo de negocio donde la inscripción debería nacer en BORRADOR antes de pagar.

2. **Strip de `observacion: undefined`**: Cuando `observacion` es `undefined`, se convierte en `undefined` en el payload. El schema backend la espera como `str = ""`. Debería enviar `""` explícitamente o no enviarla.

3. **Delegado hardcodeado a `null`**: Si `delegado_id` no se provee, el frontend fuerza `null`. Esto es correcto semánticamente, pero el mapping `delegado_id ?? null` cuando `delegado_id` es `undefined` produce `null`, lo cual es correcto.

### 2.3 Análisis de `PATCH /participaciones/{id}` (RESUELTO)

**Estado actual:**
- Frontend `editarParticipante()` llama a `PATCH /participaciones/${participanteId}` con payload `{ rol?, talla_camiseta?, aseguradora_nombre?, aseguradora_numero_poliza?, notas? }`
- Backend `ParticipacionController` expone `PATCH /{id}` y delega en `actualizar_participacion_proceso`.
- Schema `ActualizarParticipacionIn` se usa en esa ruta.
- La prueba `test_actualizar_participacion` cubre la actualización.

**Impacto**: Los usuarios pueden editar rol, talla de camiseta y notas cuando la UI usa el identificador de participación correcto.

---

## 3. INTENCIÓN UX EXACTA

### 3.1 Flujo de Wizard Actual (3 pasos)

```
Step 1: Selección de Paquete
  ├─ SmartPaqueteCardsField (selección visual de paquete)
  ├─ Muestra: nombre, tipo, modo (FIJO/ELEGIBLE), precio, mínimo
  └─ Al seleccionar → fetchPaqueteDetail() → guarda en selectedPaqueteDetail

Step 2: Equipos y Promoción
  ├─ SmartSearchableSelect: promoción
  ├─ SmartSearchableSelect: fusión (opcional)
  ├─ SmartEquipoField: crea equipos por disciplina
  └─ Equipos NO tienen participantes aún — se agregan después

Step 3: Declaraciones
  └─ StepDeclarations (acepta bases, aptitud física, imagen)

Submit:
  └─ toCompletaBackendPayload(data, evento_id, cantidad_minima, null)
  └─ useCreateInscripcionCompleta().mutate(payload)
  └─ POST /inscripciones/completa/
  └─ Redirect a /dashboard/inscripcion/{id}
```

### 3.2 Flujo Post-Creación (Detalle)

```
InscripcionDetailView
  ├─ Muestra equipos vacíos (sin participantes)
  ├─ RegistrationStepsCard: pasos 1-4
  ├─ PaymentCallout: "Completa el pago"
  └─ IzipayModal: para iniciar pago

POST /inscripciones/completa/ retorna:
  {
    inscripcion_id, inscripcion_estado: "ACTIVA" (forzado),
    compra_id, orden_pago_id, compra_estado: "PENDIENTE",
    cantidad, precio_unitario, total,
    equipos: [{id, nombre, disciplina, ...}]
  }
```

### 3.3 Lo que FALTA en UX

| Lo que falta | Descripción |
|--------------|-------------|
| **Input de cantidad** | El usuario NO puede elegir la cantidad de la compra inicial. Se hardcodea a `minimo_compra_inicial`. No hay campo visible para cambiarlo. |
| **Edición de participante** | `PATCH /participaciones/{id}` no existe — no se pueden editar datos de participante |
| **Indicador de precio total** | No se muestra "Total: S/400" antes de enviar — el usuario ve precio por persona y mínimo pero no el total |
| **Confirmación de compra mínima** | El usuario no sabe explícitamente que está comprando "X personas como mínimo" |

---

## 4. DISEÑO MÍNIMO RECOMENDADO DE RUTAS/SCHEMAS CON RESPONSABILIDADES

### 4.1 Diseño Propuesto — Staged API Workflow

#### Etapa 1: Crear Inscripción + Compra Inicial (atómico)

```
POST /api/inscripciones/completa/
{
  evento_id,
  paquete_id,
  promocion_id,
  fusion_promocion_id?,  -- Optional
  delegado_id?,          -- Optional
  cantidad: int,         -- Cantidad de compra inicial (>= minimo_compra_inicial del paquete)
  estado: "BORRADOR"     -- Backend ignora y usa BORRADOR por defecto
}
→ Crea: Inscripcion(BORRADOR) + Compra(INICIAL, PENDIENTE, cantidad) + OrdenPago(PENDIENTE)
→ No crea equipos en esta etapa
→ Response: { inscripcion_id, compra_id, orden_pago_id, cantidad, precio_unitario, total }
```

**Responsabilidad**: Crear la obligación de pago sin crear equipos. Equipos se crean después.

#### Etapa 2: Crear Equipos ( separately)

```
POST /api/equipos/
{
  inscripcion_id,
  disciplina_id,
  nombre,
  categoria_id?   -- Optional
}
→ Crea equipo en la inscripción
→ Response: EquipoOut
```

**Responsabilidad**: Un equipo por disciplina, puede crearse en paralelo.

#### Etapa 3: Agregar Personas al Roster

```
POST /api/inscripciones/{id}/personas
{
  persona_id,
  equipo_id?,
  aceptaciones: ["BASES", "APTITUD_FISICA", "IMAGEN"]
}
→ Crea InscripcionPersona + Participacion si equipo_id provisto
→ Response: { participante: ParticipacionOut }
```

**Responsabilidad**: Registrar persona con consentimientos y asociarla a un equipo.

#### Etapa 4: Post-Pago (Confirmación)

```
PATCH /api/inscripciones/{id}
{ estado: "CONFIRMADA" }
```

**Responsabilidad**: Confirmar la inscripción después de que el pago sea validado.

### 4.2 Responsabilidades Exactas

| Endpoint | Qué ES | Qué NO ES |
|----------|--------|-----------|
| `POST /inscripciones/completa/` | Crear obligación de pago + reserva de compra mínima | No crea roster ni equipos |
| `POST /equipos/` | Crear equipo en inscripción existente | No crea participantes |
| `POST /inscripciones/{id}/personas` | Agregar persona con consentimientos | No hace verificación de capacidad |
| `PATCH /participaciones/{id}` | Editar rol, talla, notas de participante | No mueve entre equipos ni retira |
| `PATCH /participaciones/{id}/mover` | Mover participante a otro equipo | — |
| `PATCH /participaciones/{id}/retirar` | Retirar participante (soft delete) | — |

### 4.3 Canonicos de Presentador — Paquetes

Según `PLAN_CONTRATO_PAQUETE_FRONTEND_BACKEND.md` y apply-progress #8852:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `modo_disciplinas` | `"FIJO" \| "ELEGIBLE"` | Campo canónico — NO inferir de `cantidad_disciplinas` |
| `cantidad_minima_compra` | `int` | Mínimo comercial (era `cantidad_maxima_participantes`) |
| `cantidad_disciplinas` | `int` | Número de disciplinas del paquete (1-3) |
| `minimo_compra_inicial` | `int` | Alias para cantidad_minima_compra en el modelo |
| `precio_preventa` | `Decimal?` | Precio en preventa |
| `precio_regular` | `Decimal?` | Precio regular |
| `tiene_fiesta`, `tiene_box`, `tiene_cerveza` | `bool` | Flags de beneficios |

---

## 5. COMPARACIÓN: PAYLOAD ATÓMICO vs WORKFLOW STAGED

### 5.1 Opción A: Payload Atómico (Estado Actual Parcial)

**Descripción**: `POST /inscripciones/completa/` crea inscripción + compra + equipos en una sola transacción.

**Schema propuesto**:
```python
class CrearInscripcionCompletaIn(BaseSchema):
    evento_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    cantidad: int  # Required
    equipos: list[EquipoParaCrearIn]  # Created atomically
    estado: str = "BORRADOR"  # Ignored, siempre BORRADOR
    observacion: str = ""
```

**Pros**:
- ✅ Una sola llamada HTTP para crear todo
- ✅ Transaccionalidad garantizada por `transaction.atomic()`
- ✅ No hay estado parcial si falla algo

**Contras**:
- ❌ **Giant payload**: incluye `equipos[]` dentro de inscripción — rompe el principio de responsabilidad única
- ❌ **No escalable**: si en el futuro se necesita crear equipos en pasos diferentes (ej. uno hoy, otro mañana), no funciona
- ❌ **UX forzada**: el usuario debe crear TODOS los equipos en el momento del submit, sin poder guardar progreso intermedio
- ❌ **Campo `cantidad` hardcodeado** en frontend sin input del usuario
- ❌ **Equipos se crean sin participantes** — el roster se agrega después desde detalle, entonces los equipos nacen vacíos

**Complejidad**: Alta — el flujo atómico ya está implementado pero tiene estos problemas de diseño.

### 5.2 Opción B: Workflow Staged (RECOMENDADO)

**Descripción**: Crear inscripción + compra primero, luego equipos por separado.

**Flujo de llamadas**:
```
1. POST /inscripciones/completa/  → { inscripcion_id, compra_id, orden_pago_id, cantidad, total }
2. POST /equipos/{id}/ (x N)    → { equipo_id }
3. POST /inscripciones/{id}/personas (x M) → { participante }
4. PATCH /participaciones/{id}   → editar participante (si existe)
```

**Pros**:
- ✅ Cada endpoint tiene responsabilidad clara
- ✅ El usuario puede crear inscripción primero, luego equipos en otro momento
- ✅ Se puede validar `cantidad` vs equipos creados antes de pagar
- ✅ `PATCH /participaciones/{id}` es aditivo, no rompe nada
- ✅ Más cercano al modelo mental de "primero me inscribo, después armo equipos"
- ✅ Equipos pueden tener participantes desde el inicio del workflow

**Contras**:
- ❌ Más llamadas HTTP (3-4 en vez de 1)
- ❌ Estado parcial posible si falla una llamada intermedia
- ❌ Requiere más lógica de retry/rollback en frontend
- ❌ El `toCompletaBackendPayload` sería irrelevante — se necesitaría una nueva función `toBackendPayloadSimple`

**Complejidad**: Media — requiere más trabajo frontend pero menor acoplamiento.

### 5.3 Comparación Directa

| Criterio | A (Atómico) | B (Staged) |
|----------|-------------|-------------|
| Llamadas HTTP | 1 | 3-4 |
| Complejidad Backend | Media | Baja |
| Complejidad Frontend | Baja | Media |
| Escalabilidad | Baja | Alta |
| UX de progreso | Forzada | Flexible |
| Estado parcial | No | Posible |
| rollback manual | No | Sí |
| Equipos con participantes desde inicio | ❌ | ✅ |

---

## 6. OPCIÓN RECOMENDADA Y JUSTIFICACIÓN

### 6.1 Recomendación: **Opción B — Workflow Staged**

**Justificación:**

1. **Separación de responsabilidades**: Cada endpoint hace una cosa. `POST /inscripciones/completa/` crea obligación de pago. `POST /equipos/` crea equipos. `POST /inscripciones/{id}/personas` agrega personas.

2. **El campo `cantidad` debe ser input del usuario**: El wizard actual hardcodea `cantidad = minimo_compra_inicial`. En el workflow staged, se puede tener un paso "cantidad" antes de crear la inscripción, con validación visual.

3. **Equipos con participantes desde el inicio**: En el flujo atómico actual, los equipos nacen vacíos y las personas se agregan después desde otra pantalla. El flujo staged permite que los equipos ya tengan participantes desde el momento en que se crean.

4. **`PATCH /participaciones/{id}` es aditivo**: Implementar este endpoint no rompe nada del flujo staged — es una mejora aditiva que el frontend necesita crítica.

5. **Menos riesgo de estado inconsistente**: Aunque hay más llamadas, cada endpoint es idempotente en su contexto. El rollback es manual pero manejable con憨山UI.

6. **El problema del `toCompletaBackendPayload` gigante desaparece**: En vez de un payload monolítico con `equipos[]` anidados, cada payload es pequeño y focalizado.

### 6.2 Lo que se necesita implementar

| Componente | Estado | Acción |
|------------|--------|--------|
| `PATCH /participaciones/{id}` | 🔴 NO EXISTE | IMPLEMENTAR — crítico |
| Input de cantidad en wizard | 🔴 NO EXISTE | AGREGAR campo cantidad |
| `POST /inscripciones/completa/` | ✅ Existe | Mantener, pero sin equipos |
| `POST /equipos/` | ✅ Existe | Mantener |
| `POST /inscripciones/{id}/personas` | ✅ Existe | Mantener |
| `toCompletaBackendPayload` | ⚠️ Problemas | Rediseñar como `toSimpleBackendPayload` |

---

## 7. DATOS REQUERIDOS DEL FORMULARIO FRONTEND

### 7.1 FormData del Wizard (para workflow staged)

```typescript
interface InscripcionFormData {
  // Catálogo
  paquete_id: string;          // Requerido
  promocion_id: string;        // Requerido
  fusion_promocion_id: string | null;  // Opcional

  // Compra
  cantidad: number;            // Nuevo: cantidad de compra inicial (>= minimo)

  // Equipos
  equipos: Array<{
    disciplina_id: string;    // Requerido
    categoria_id: string | null;  // Opcional
    nombre: string;          // Requerido
    // Participantes YA NO van aquí — se agregan después
  }>;

  // Declaraciones
  acceptedBases: true;         // z.literal(true)
  fitnessDeclaration: true;    // z.literal(true)
  imageConsent: true;         // z.literal(true)
}
```

### 7.2 Datos canónicos del presentador de paquetes

| Campo | Fuente | Descripción |
|-------|--------|-------------|
| `evento_id` | `PaqueteDetailContract.evento_id` | Del paquete seleccionado |
| `paquete_id` | Form input | `paquete_id` |
| `promocion_id` | Form input | `promocion_id` |
| `fusion_promocion_id` | Form input | Opcional |
| `cantidad` | Form input (nuevo) | Cantidad de compra inicial |
| `delegado_id` | Del contexto de usuario autenticado | Server-side |
| `estado` | Server-side | Siempre `"BORRADOR"` |

---

## 8. CONTRATOS CANONICOS DE PRESENTADOR

### 8.1 Canonical Presenter Contract — Paquete

Según apply-progress #8852 y `PLAN_CONTRATO_PAQUETE_FRONTEND_BACKEND.md`:

**Backend `PaqueteListOut`**:
```python
class PaqueteListOut(BaseSchema):
    id: str
    evento_id: str
    nombre: str
    tipo: str                    # PACK | DISCIPLINA
    modo_disciplinas: str       # FIJO | ELEGIBLE — CANÓNICO
    cantidad_disciplinas: int    # 1, 2 o 3
    cantidad_minima_compra: int  # MÍNIMO COMERCIAL
    precio_preventa: Optional[Decimal]
    precio_regular: Optional[Decimal]
    tiene_fiesta: bool
    tiene_box: bool
    tiene_cerveza: bool
    disciplinas_resumen: list[str]
```

**Backend `PaqueteDetailOut`**: Extiende `PaqueteListOut` con:
```python
    descripcion: str
    precios: list[PaquetePrecioContract]
    beneficios: list[PaqueteBeneficioContract]
    disciplinas: list[PaqueteDisciplinaContract]
```

### 8.2 Frontend Zod Mirror

```typescript
export const PaqueteListContractSchema = z.object({
  id: z.string(),
  evento_id: z.string(),
  nombre: z.string(),
  tipo: z.enum(['PACK', 'DISCIPLINA']),
  modo_disciplinas: z.enum(['FIJO', 'ELEGIBLE']), // CANÓNICO
  cantidad_disciplinas: z.number().int().min(1).max(3),
  cantidad_minima_compra: z.number().int().min(1),
  precio_preventa: z.number().nullable(),
  precio_regular: z.number().nullable(),
  tiene_fiesta: z.boolean(),
  tiene_box: z.boolean(),
  tiene_cerveza: z.boolean(),
  disciplinas_resumen: z.array(z.string()),
});

export function isElegible(paquete: PaqueteListContract): boolean {
  return paquete.modo_disciplinas === "ELEGIBLE";
}
```

---

## 9. SECUENCIA DE CREACIÓN/PAGO/EQUIPOS

### 9.1 Flujo Completo Recomendado

```
1. Usuario autenticado → Wizard de inscripción
   └─ Step 1: Selección de paquete (SmartPaqueteCardsField)
       └─ PaqueteDetailContractFetched → muestra minimo_compra_inicial
   └─ Step 2 (NUEVO): Cantidad + Equipos
       ├─ Input: cantidad (number, min=cantidad_minima_compra, default=minimo)
       ├─ SmartEquipoField: crear equipos (disciplinas del paquete)
       └─ Promoción y fusión opcional
   └─ Step 3: Declaraciones
       └─ acceptedBases, fitnessDeclaration, imageConsent
   └─ Submit:
       ├─ POST /inscripciones/completa/
       │  { evento_id, paquete_id, promocion_id, cantidad, ... }
       │  → { inscripcion_id, compra_id, orden_pago_id, cantidad, total }
       ├─ POST /equipos/ (uno por equipo)
       │  { inscripcion_id, disciplina_id, nombre }
       │  → { equipo_id, ... }
       └─ Redirect a /dashboard/inscripcion/{id}

2. Detalle de Inscripción
   ├─ Muestra equipos (vacíos o con participantes)
   ├─ RegistrationStepsCard
   ├─ Botón "Agregar participante" → modal con DNI lookup
   │  └─ POST /inscripciones/{id}/personas
   │     { persona_id, equipo_id, aceptaciones: ["BASES", "APTITUD_FISICA", "IMAGEN"] }
   │     → { participante: ParticipacionOut }
   ├─ Editar participante → PATCH /participaciones/{id} (IMPLEMENTAR)
   ├─ Mover participante → PATCH /participaciones/{id}/mover
   └─ Retirar participante → PATCH /participaciones/{id}/retirar

3. Pago
   ├─ PaymentCallout: "Completa el pago"
   ├─ IzipayModal: muestra total y botón "Pagar"
   └─ POST /compras/{id}/iniciar-pago → redirect a Izipay

4. Confirmación
   ├─ Webhook Izipay → POST /compras/confirmar-pago
   └─ PATCH /inscripciones/{id} → { estado: "CONFIRMADA" }
```

### 9.2 Diagrama de Secuencia — Creación

```
Frontend                           Backend
    |                                  |
    | 1. POST /inscripciones/completa/ |
    |    { evento_id, paquete_id,      |
    |      promocion_id, cantidad }   |
    |------------------------------->  |
    |    { inscripcion_id,            |
    |      compra_id,                 |
    |      orden_pago_id,             |
    |      total }                    |
    |<-------------------------------|
    |                                  |
    | 2. POST /equipos/ (x N)        |
    |    { inscripcion_id,            |
    |      disciplina_id, nombre }     |
    |------------------------------->  |
    |    { id, nombre, disciplina }   |
    |<-------------------------------|
    |                                  |
    | Redirect /dashboard/inscripcion/{id}
    |                                  |
    | 3. POST /inscripciones/{id}/personas (x M)
    |    { persona_id, equipo_id,     |
    |      aceptaciones: [...] }      |
    |------------------------------->  |
    |    { participante: {...} }        |
    |<-------------------------------|
    |                                  |
    | 4. PATCH /participaciones/{id} (editar)
    |    { rol?, talla_camiseta? }    |
    |------------------------------->  |
    |    { ... }                      |
    |<-------------------------------|
```

---

## 10. PASOS DE MIGRACIÓN DESDE CÓDIGO PARCIAL ACTUAL

### 10.1 Estado Actual del Código

Según apply-progress #8852:
- Backend: ✅ `POST /inscripciones/completa/` existe y es atómico (crea Inscripcion + Compra + Equipos)
- Frontend: ✅ `useCreateInscripcionCompleta` + `toCompletaBackendPayload` existen
- Problema: `cantidad` hardcodeada, `estado: "ACTIVA"` incorrecto, `PATCH /participaciones/{id}` no existe

### 10.2 Plan de Migración

| Fase |一步 | Archivos | Cambio |
|------|-----|---------|--------|
| 1 | IMPLEMENTAR `PATCH /participaciones/{id}` | `ParticipacionController`, `ParticipacionOrchestrator` | Agregar route `PATCH /{id}` con `ActualizarParticipacionIn` |
| 2 | CORREGIR `toCompletaBackendPayload` | `inscripcion.schema.ts` | Cambiar `estado: "ACTIVA"` → eliminar (no enviar) y usar default del backend. Cambiar `observacion: undefined` → `""` |
| 3 | AGREGAR input de cantidad al wizard | `InscripcionWizard.tsx`, `InscripcionFormSchema` | Nuevo campo `cantidad` en Step 2 con validación `min: minimo_compra_inicial` |
| 4 | REDISEÑAR payload del wizard | `InscripcionWizard.tsx`, `useCreateInscripcionCompleta.ts` | Decidir si mantener payload atómico o separar en llamadas staged |
| 5 | ACTUALIZAR `InscripcionCompletaBackendPayload` | `inscripcion.schema.ts` | Remover `estado` y `observacion` del payload ya que son ignorados por el backend |
| 6 | PROPAGAR `delegado_id` | `useCreateInscripcionCompleta.ts` | El `delegado_id` viene del usuario autenticado — pasar correctamente |

### 10.3 Cambios Específicos por Archivo

**Backend — Archivos a CAMBIAR:**
- `ParticipacionController` — AGREGAR `PATCH /{id}` route
- `ParticipacionOrchestrator` — AGREGAR `actualizar_participacion_proceso`

**Backend — Archivos a MANTENER:**
- `CrearInscripcionCompletaIn` — No cambia
- `crear_inscripcion_completa_flujo` — No cambia
- `InscripcionController` — No cambia

**Frontend — Archivos a CAMBIAR:**
- `InscripcionWizard.tsx` — AGREGAR campo cantidad input, corregir hardcodeo
- `inscripcion.schema.ts` — CORREGIR `toCompletaBackendPayload` (`estado: "ACTIVA"` → remove, `observacion: undefined` → `""`)
- `useCreateInscripcionCompleta.ts` — Adaptar al nuevo flujo

**Frontend — Archivos a MANTENER:**
- `inscripcion.service.ts` — La mayoría de funciones se mantienen
- `useAgregarParticipantes`, `useMoverParticipante`, `useEliminarParticipante` — Se mantienen pero依赖 del PATCH endpoint

---

## 11. MATRIX DE ENDPOINTS

| Endpoint | Auth | Request Schema | Response Schema | Usado por Wizard |
|----------|------|---------------|----------------|------------------|
| `POST /inscripciones/completa/` | JWT | `CrearInscripcionCompletaIn` | `InscripcionCompletaOut` | ✅ Sí |
| `GET /inscripciones/` | JWT | — | `list[InscripcionOut]` | ✅ Sí (dashboard) |
| `GET /inscripciones/{id}/detalle` | AllowAny | — | `InscripcionDetailOut` | ✅ Sí (detail view) |
| `PATCH /inscripciones/{id}` | AllowAny | `ActualizarInscripcionIn` | `InscripcionOut` | ❌ No |
| `POST /equipos/` | AllowAny | `CrearEquipoIn` | `EquipoOut` | ❌ No (post-creación) |
| `GET /equipos/inscripcion/{id}` | AllowAny | — | `list[EquipoOut]` | ❌ No |
| `POST /inscripciones/{id}/personas` | AllowAny | `AgregarPersonaIn` | `{participante}` | ❌ No (post-creación) |
| `PATCH /participaciones/{id}` | AllowAny | `ActualizarParticipacionIn` | `ParticipacionOut` | 🔴 NO EXISTE |
| `PATCH /participaciones/{id}/mover` | AllowAny | `MoverParticipacionIn` | `ParticipacionOut` | ✅ Sí |
| `PATCH /participaciones/{id}/retirar` | AllowAny | — | `ParticipacionOut` | ✅ Sí |
| `POST /compras/` | JWT | `CompraCreateIn` | `CompraCreateOut` | ❌ No (post-creación) |
| `GET /compras/inscripciones/{id}/compras` | JWT | — | `list[CompraOut]` | ❌ No |
| `POST /compras/{id}/iniciar-pago` | JWT | — | `IzipayPrepareResponse` | ❌ No (post-creación) |
| `POST /compras/confirmar-pago` | JWT | `IzipayConfirmIn` | `IzipayConfirmOut` | ❌ No |

---

## 12. PLAN DE VALIDACIÓN Y TESTS

### 12.1 Validaciones Requeridas

| Validación | Ubicación | Tipo |
|------------|-----------|------|
| `cantidad >= minimo_compra_inicial` | Backend: `CrearInscripcionCompletaFlujo._crear_atomico` | Excepción `CantidadInsuficienteError` |
| `cantidad` es entero positivo | Backend: schema `cantidad: int` | Pydantic validation |
| `paquete_id` existe | Backend: `Paquete.objects.get(id=paquete_id)` | Excepción `PaqueteNotFoundError` |
| `disciplina_id` pertenece al paquete | Backend: validación en equipo creation | Excepción `DisciplinaNotInPaqueteError` |
| Fecha límite no excedida | Backend: `evento.puede_modificar()` | Excepción `FechaLimiteExcedidaError` |
| Unique constraint: (evento, disciplina, persona) activa | Backend: `ParticipacionService.crear()` + DB constraint | Excepción `DuplicateParticipacionError` |

### 12.2 Tests a Crear/Actualizar

| Test | Tipo | Cobertura |
|------|------|----------|
| `test_crear_inscripcion_completa_endpoint` | Integration | `POST /inscripciones/completa/` → 201, retorna InscripcionCompletaOut |
| `test_crear_inscripcion_completa_cantidad_insuficiente` | Integration | cantidad < minimo → 422 `CantidadInsuficienteError` |
| `test_editar_participante_endpoint` | Integration | `PATCH /participaciones/{id}` → 200, ParticipacionOut con campos actualizados |
| `test_editar_participante_404` | Integration | `PATCH /participaciones/{id inexistente}` → 404 |
| `test_wizard_toCompletaBackendPayload_estado` | Unit | `toCompletaBackendPayload` no envía `estado: "ACTIVA"` |
| `test_wizard_cantidad_input` | E2E | Wizard tiene input cantidad, pre-filled con minimo, validado contra minimo |
| `test_inscripcion_completa_flow_staged` | E2E | Full flow: crear inscripción → crear equipos → agregar personas |

### 12.3 Checklist de Verificación

- [ ] `PATCH /participaciones/{id}` existe en `ParticipacionController`
- [ ] `PATCH /participaciones/{id}` tiene tests de integración
- [ ] `toCompletaBackendPayload` NO envía `estado: "ACTIVA"`
- [ ] `toCompletaBackendPayload` envía `observacion: ""` en vez de `undefined`
- [ ] Wizard tiene input de cantidad
- [ ] Cantidad en wizard tiene validación `min: minimo_compra_inicial`
- [ ] Cantidad default es `minimo_compra_inicial` del paquete seleccionado
- [ ] `InscripcionCompletaBackendPayload` no tiene campo `estado` (o es opcional y se ignora)
- [ ] Todos los tests de integración pasan
- [ ] TypeScript compila sin errores

---

## 13. RIESGOS CONFIRMADOS

| # | Riesgo | Severidad | Mitigación |
|---|--------|-----------|------------|
| R1 | `PATCH /participaciones/{id}` no existe — edición de participante rota | 🔴 CRITICAL | Implementar urgencia |
| R2 | `toCompletaBackendPayload` fuerza `estado: "ACTIVA"` — inconsistencia con backend | 🟡 HIGH | Corregir a no enviar estado |
| R3 | Wizard no tiene input de cantidad — usuario no puede elegir cantidad > mínimo | 🟡 HIGH | Agregar campo cantidad |
| R4 | `agregarParticipantesAEquipo` solo usa primer elemento del array | 🟡 MEDIUM | Refactorizar a enviar array completo |
| R5 | El `delegado_id` no se provee desde el contexto de usuario autenticado | 🟡 MEDIUM | Implementar `_get_authenticated_persona_id` para obtenerlo |
| R6 | El payload `observacion: undefined` puede causar error de validación en backend | 🟡 MEDIUM | Cambiar a `""` |
| R7 | Estado de inscripción en frontend (`PENDIENTE`, `PAGADA`) no existe en backend | 🟢 LOW | Sincronizar con estados de Compra |
| R8 | El campo `rol` en frontend es `"JUGADOR"` pero backend espera `"J"` | 🟢 LOW | Estandarizar lengths |

---

## 14. ARCHIVOS A RETENER, CAMBIAR Y ELIMINAR

### 14.1 Archivos a RETENER (sin cambios)

```
Backend:
- presentation/controllers/inscripcion_controller.py  (excepto agregar PATCH /participaciones/{id})
- domain/services/flujos/crear_inscripcion_completa_flujo.py
- domain/services/orchestrators/inscripcion_orchestrator.py
- presentation/schemas/inscripcion_schemas.py (presenter schemas)
- domain/schemas/inscripcion_schemas.py (internal DTOs)

Frontend:
- features/inscripciones/services/inscripcion.service.ts  (mayoría de funciones)
- features/inscripciones/hooks/useMoverParticipante.ts
- features/inscripciones/hooks/useEliminarParticipante.ts
- features/inscripciones/components/smart-fields/SmartPaqueteCardsField.tsx
- features/inscripciones/components/smart-fields/SmartEquipoField.tsx
```

### 14.2 Archivos a CAMBIAR

| Archivo | Cambio |
|---------|--------|
| `ParticipacionController` | AGREGAR: `PATCH /{id}` route con `ActualizarParticipacionIn` |
| `ParticipacionOrchestrator` | AGREGAR: `actualizar_participacion_proceso` method |
| `InscripcionWizard.tsx` | AGREGAR: campo cantidad input; CORREGIR: hardcodeo de cantidad |
| `inscripcion.schema.ts` | CORREGIR: `toCompletaBackendPayload` (estado, observacion) |
| `useCreateInscripcionCompleta.ts` | ADAPTAR: al nuevo diseño de payload |
| `paquete.schema.ts` | Mantener según apply-progress #8852 |

### 14.3 Archivos a ELIMINAR (si no se usan)

| Archivo | Razón |
|---------|-------|
| `toBackendPayload` (old) | Fue reemplazado por `toCompletaBackendPayload` |
| Función `createInscripcion` (old non-atomic) | No se usa en wizard, solo existe para API legacy |

---

## 15. RESUMEN EJECUTIVO

| Área | Estado Actual | Acción Requerida |
|------|--------------|------------------|
| Endpoint atómico | ✅ Implementado `POST /inscripciones/completa/` | Mantener, adaptar payload |
| Endpoint editar participante | 🔴 NO EXISTE | IMPLEMENTAR URGENTE |
| Input cantidad en wizard | 🔴 NO EXISTE | AGREGAR |
| Payload `estado: "ACTIVA"` | 🟡 Incorrecto | Corregir a no enviar |
| Workflow recomendado | Staged (3-4 llamadas) | Cambiar diseño del wizard |
| Tests | ⚠️ Incompletos | Agregar para nuevos endpoints |

**Conclusión**: El endpoint atómico existe y funciona, pero tiene problemas de diseño UX (falta input de cantidad, hardcodeo de estado). El problema crítico es la ausencia del `PATCH /participaciones/{id}`. El workflow staged es la recomendación para separar responsabilidades.

---

*Documento generado mediante SDD Explore read-only. No modifica código fuente. Todos los hallazgos están respaldados por evidencia de archivos reales y apply-progress #8852.*
