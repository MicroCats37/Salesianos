# PLAN: Contrato Paquete — Backend + Frontend

> **Proyecto:** Salesianos FEST
> **Fecha:** 2026-10-18
> **Tipo:** SDD Explore — Arquitectura de Contrato
> **Artifact:** `sdd/salesianos-fest-package-presenter-contract/explore`

---

## RESUMEN EJECUTIVO

El frontend actual **infiere** reglas de negocio desde campos mal nombrados o inadecuados en lugar de consumirlos del contrato oficial del presentador. Esto genera inconsistencias en el badge ELEGIBLE/FIJO, en el label de precio (mostrado "por equipo" cuando es "por persona"), y en elTooltip de capacidad.

Este plan define el **contrato canónico de paquete** entre el backend y el frontend, covering: schema de presentador, responsabilidades de endpoints, adapter tipado con Zod, cache/query keys de React Query, flujo del wizard, diseño FIJO/ELEGIBLE, creación de equipos y UX de compra mínima, límites atómicos de creación, errores/loading/stale cache, estrategia de migración, archivos afectados, y batches de implementación en orden seguro.

---

## 1. CONTRATO CANÓNICO DE PRESENTADOR DE PAQUETE

### 1.1 Principios

| # | Principio | Descripción |
|---|-----------|-------------|
| C1 | **Un solo source of truth** | El backend define el contrato; el frontend solo consume |
| C2 | **Campo canónico para modo** | `modo_disciplinas: "FIJO" \| "ELEGIBLE"` — NO inferir de `cantidad_disciplinas` |
| C3 | **Naming claro** | `cantidad_minima_compra` (mínimo comercial) ≠ `max_jugadores` (máximo deportivo) |
| C4 | **Esquemas espejo** | Backend Pydantic ↔ Frontend Zod con mapeo 1:1 |
| C5 | **Lista vs Detalle** | Lista para selección de cards; Detalle para configuración de wizard |

### 1.2 Schema de Lista — `PaqueteListContract`

**Backend (`PaqueteListOut` renombrado):**

```python
class PaqueteListContract(BaseSchema):
    """Contrato para endpoint de listado de paquetes — información resumida para cards."""

    id: str
    evento_id: str
    nombre: str
    tipo: str                          # PACK | DISCIPLINA
    modo_disciplinas: str              # FIJO | ELEGIBLE — CAMPO CANÓNICO
    cantidad_disciplinas: int          # 1, 2 o 3
    cantidad_minima_compra: int        # MÍNIMO COMERCIAL (era cantidad_maxima_participantes)
    precio_preventa: Optional[Decimal]
    precio_regular: Optional[Decimal]
    # Beneficios flags para cards sin hacer join completo
    tiene_fiesta: bool
    tiene_box: bool
    tiene_cerveza: bool
    # Resumen de disciplinas para chips (no hace falta el detalle completo en lista)
    disciplinas_resumen: list[str]     # ["F7M", "VOL", "BAS"]
```

**Frontend (TypeScript + Zod):**

```typescript
// src/features/inscripciones/schemas/paquete.schema.ts

export const PaqueteListContractSchema = z.object({
  id: z.string(),
  evento_id: z.string(),
  nombre: z.string(),
  tipo: z.enum(['PACK', 'DISCIPLINA']),
  modo_disciplinas: z.enum(['FIJO', 'ELEGIBLE']), // CANÓNICO — NO inferir
  cantidad_disciplinas: z.number().int().min(1).max(3),
  cantidad_minima_compra: z.number().int().min(1),
  precio_preventa: z.number().nullable(),
  precio_regular: z.number().nullable(),
  tiene_fiesta: z.boolean(),
  tiene_box: z.boolean(),
  tiene_cerveza: z.boolean(),
  disciplinas_resumen: z.array(z.string()),
});

export type PaqueteListContract = z.infer<typeof PaqueteListContractSchema>;

// Helper de badge — usa modo_disciplinas directamente
export function getModoLabel(modo: PaqueteListContract['modo_disciplinas']): string {
  return modo === 'ELEGIBLE' ? 'Elegible' : 'Fijo';
}

export function isElegible(paquete: PaqueteListContract): boolean {
  return paquete.modo_disciplinas === 'ELEGIBLE';
}
```

### 1.3 Schema de Detalle — `PaqueteDetailContract`

**Backend (`PaqueteDetailOut`):**

```python
class PaqueteDetailContract(PaqueteListContract):
    """Contrato para endpoint de detalle — información completa para wizard."""

    descripcion: str
    precios: list[PaquetePrecioContract]
    beneficios: list[PaqueteBeneficioContract]
    disciplinas: list[PaqueteDisciplinaContract]

class PaquetePrecioContract(BaseSchema):
    etapa: str                    # PREVENTA | REGULAR
    precio_unitario: Decimal
    vigente_desde: date
    vigente_hasta: Optional[date]

class PaqueteBeneficioContract(BaseSchema):
    tipo: str                    # FIESTA | BOX | CERVEZA
    cantidad: int
    alcance: str                 # INDIVIDUAL | GRUPAL
    modo_calculo: str            # POR_CUPO | FIJO_INICIAL

class PaqueteDisciplinaContract(BaseSchema):
    disciplina_id: str
    disciplina_nombre: str
    disciplina_sigla: str
    min_jugadores: int
    max_jugadores: int
```

**Frontend:**

```typescript
// src/features/inscripciones/schemas/paquete.schema.ts

export const PaquetePrecioContractSchema = z.object({
  etapa: z.enum(['PREVENTA', 'REGULAR']),
  precio_unitario: z.number(),
  vigente_desde: z.string(),
  vigente_hasta: z.string().nullable(),
});

export const PaqueteBeneficioContractSchema = z.object({
  tipo: z.enum(['FIESTA', 'BOX', 'CERVEZA']),
  cantidad: z.number().int().positive(),
  alcance: z.enum(['INDIVIDUAL', 'GRUPAL']),
  modo_calculo: z.enum(['POR_CUPO', 'FIJO_INICIAL']),
});

export const PaqueteDisciplinaContractSchema = z.object({
  disciplina_id: z.string(),
  disciplina_nombre: z.string(),
  disciplina_sigla: z.string(),
  min_jugadores: z.number().int(),
  max_jugadores: z.number().int(),
});

export const PaqueteDetailContractSchema = PaqueteListContractSchema.extend({
  descripcion: z.string(),
  precios: z.array(PaquetePrecioContractSchema),
  beneficios: z.array(PaqueteBeneficioContractSchema),
  disciplinas: z.array(PaqueteDisciplinaContractSchema),
});

export type PaqueteDetailContract = z.infer<typeof PaqueteDetailContractSchema>;
```

---

## 2. RESPONSABILIDADES DE ENDPOINTS: LISTA VS DETALLE

### 2.1 `GET /api/catalogo/paquetes/` → `PaqueteListContract[]`

| Responsabilidad | Qué incluye | Qué NO incluye |
|----------------|------------|----------------|
| Selección de paquete en cards | Nombre, tipo, modo, mínimo, precios, flags de beneficios, resumen de siglas | Descripci\u00f3n completa, precios detallados con fechas, beneficios completos |
| Badges UI | `modo_disciplinas` directo | NO inferir de `cantidad_disciplinas` |
| Tooltips | `cantidad_minima_compra` con label claro | NO mostrar como "máximo participantes" |

### 2.2 `GET /api/catalogo/paquetes/{id}/` → `PaqueteDetailContract`

| Responsabilidad | Qué incluye | Qué NO incluye |
|----------------|------------|----------------|
| Configuración de wizard | Todo de lista + descripción, precios con fechas vigencia, beneficios completos, disciplinas con min/max jugadores | — |
| Validación de compra mínima | `cantidad_minima_compra` para validar input | — |
| Locking FIJO/ELEGIBLE | `modo_disciplinas` + `disciplinas` para pre-llenar y lock | — |

### 2.3 Regla de Uso

```
Wizard Step 1 (Selección paquete) → consume LIST
  ↓ usuario selecciona paquete
Wizard Step 2 (Equipos + Disciplinas) → consume DETAIL para el paquete seleccionado
  ↓ usuario completa equipos
Wizard Step 3 (Comprar) → consume DETAIL para validar mínimo y mostrar beneficios
```

---

## 3. ADAPTER TIPADO FRONTEND Y VALIDACIÓN ZOD

### 3.1 API Service

```typescript
// src/features/inscripciones/services/paquete.service.ts

import { api } from '@/lib/api';
import type { ApiResponse } from '@/types/api.types';
import {
  PaqueteListContractSchema,
  PaqueteDetailContractSchema,
  type PaqueteListContract,
  type PaqueteDetailContract,
} from '../schemas/paquete.schema';

export const paqueteQueryKeys = {
  all: ['paquetes'] as const,
  list: () => [...paqueteQueryKeys.all, 'list'] as const,
  detail: (id: string) => [...paqueteQueryKeys.all, 'detail', id] as const,
} as const;

/**
 * Fetch paquete list for cards and package selection.
 * Uses PaqueteListContract schema — lightweight for card rendering.
 */
export async function fetchPaqueteList(): Promise<PaqueteListContract[]> {
  const { data } = await api.get<ApiResponse<PaqueteListContract[]>>('/catalogo/paquetes/');

  if (!data.success || !data.data) {
    throw new Error(data.message ?? 'Error al cargar paquetes');
  }

  // Validate and parse each item with Zod
  return data.data.map((item) => {
    const result = PaqueteListContractSchema.safeParse(item);
    if (!result.success) {
      console.error('PaqueteListContract validation failed:', result.error);
      // Still return for display, but log the contract mismatch
    }
    return result.success ? result.data : item;
  });
}

/**
 * Fetch paquete detail for wizard configuration.
 * Uses PaqueteDetailContract schema — complete data for team creation.
 */
export async function fetchPaqueteDetail(id: string): Promise<PaqueteDetailContract> {
  const { data } = await api.get<ApiResponse<PaqueteDetailContract>>(`/catalogo/paquetes/${id}/`);

  if (!data.success || !data.data) {
    throw new Error(data.message ?? 'Error al cargar detalle del paquete');
  }

  const result = PaqueteDetailContractSchema.safeParse(data.data);
  if (!result.success) {
    console.error('PaqueteDetailContract validation failed:', result.error);
    // Fallback to raw data for display continuity
    return data.data;
  }

  return result.data;
}
```

### 3.2 React Query Cache y Query Keys

```typescript
// src/features/inscripciones/hooks/usePaquetes.ts

import { useQuery } from '@tanstack/react-query';
import { fetchPaqueteList, paqueteQueryKeys } from '../services/paquete.service';

export function usePaqueteList() {
  return useQuery({
    queryKey: paqueteQueryKeys.list(),
    queryFn: fetchPaqueteList,
    staleTime: 5 * 60 * 1000, // 5 min — catalog changes are admin-driven
    gcTime: 30 * 60 * 1000,  // 30 min
  });
}

// src/features/inscripciones/hooks/usePaqueteDetail.ts

import { useQuery } from '@tanstack/react-query';
import { fetchPaqueteDetail, paqueteQueryKeys } from '../services/paquete.service';

export function usePaqueteDetail(paqueteId: string | null) {
  return useQuery({
    queryKey: paqueteQueryKeys.detail(paqueteId!),
    queryFn: () => fetchPaqueteDetail(paqueteId!),
    enabled: !!paqueteId,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}
```

### 3.3 Query Keys Estables

```typescript
// Todos los query keys en un lugar único
export const queryKeys = {
  // Catálogo
  paquetes: {
    all: ['paquetes'] as const,
    list: () => [...queryKeys.paquetes.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.paquetes.all, 'detail', id] as const,
  },
  // Inscripción
  inscripcion: {
    all: ['inscripcion'] as const,
    detalle: (id: string) => [...queryKeys.inscripcion.all, 'detalle', id] as const,
  },
} as const;
```

---

## 4. FLUJO DE DATOS DEL WIZARD

### 4.1 Step 1 — Selección de Paquete

```
User sees PaqueteCards
  → usePaqueteList() returns PaqueteListContract[]
  → Each card shows:
      - nombre, tipo, modo (from modo_disciplinas directly)
      - precio (precio_preventa if available, else precio_regular)
      - badge: isElegible(paquete) ? "Elegible" : "Fijo"  ← CANÓNICO
      - "Mínimo: X jugadores"  ← from cantidad_minima_compra
      - beneficios flags (tiene_fiesta, tiene_box, tiene_cerveza)
      - disciplinas_resumen chips

User selects paquete
  → paquete_id stored in form state
  → Wizard proceeds to Step 2
```

### 4.2 Step 2 — Equipos (según modo FIJO/ELEGIBLE)

```
User sees SmartEquipoField
  → usePaqueteDetail(paqueteId) returns PaqueteDetailContract
  → Config extracted:
      - modo: paquete.modo_disciplinas  ← CANÓNICO
      - disciplinas: paquete.disciplinas (full detail with min/max)
      - cantidad_disciplinas_requeridas: paquete.cantidad_disciplinas

  FIJO mode:
    → All discipline slots pre-filled and locked
    → Locked because: isFIJO && disciplinas.length === cantidad_disciplinas_requeridas

  ELEGIBLE mode:
    → Discipline slots pre-filled with suggestions, NOT locked
    → User can change/select different disciplines
    → permiteDuplicados = cantidad_maxima_equipos > disciplinas.length
```

### 4.3 Step 3 — Compra y Checkout

```
User sees purchase summary
  → usePaqueteDetail(paqueteId) for:
      - cantidad_minima_compra: validation input minimum
      - precios: show PREVENTA vs REGULAR with dates
      - beneficios: show benefit breakdown

  Input: cantidad (number, min=cantidad_minima_compra)
  → Frontend validates before submit
  → Backend validates on receipt
```

---

## 5. DISEÑO DE INTERACCIÓN FIJO/ELEGIBLE

### 5.1 Badge en Cards

```typescript
// SmartPaqueteCardsField.tsx — CORRECTED

function PaqueteCard(card: PaqueteListContract) {
  // ✅ CORRECTO: usar modo_disciplinas directamente
  const modoLabel = getModoLabel(card.modo_disciplinas);
  const isElegibleMode = isElegible(card);

  return (
    <span className={cn(
      "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-black uppercase tracking-wider",
      isElegibleMode ? "bg-amber-400 text-slate-900" : "bg-[#312e8e]/10 text-[#312e8e]",
    )}>
      {modoLabel}
    </span>
  );
}
```

### 5.2 Locking de Disciplinas en SmartEquipoField

```typescript
// SmartEquipoField.tsx — ALREADY CORRECT (line 319)
// Se mantiene la lógica que compara modo_disciplinas

const isFIJO = paqueteActual?.modo_disciplinas === "FIJO";
const isModoFIJOAndMatched = isFIJO &&
  paqueteDisciplinas.length === paqueteActual?.cantidad_disciplinas_requeridas &&
  equiposActuales.length === paqueteDisciplinas.length &&
  equiposActuales.every((equipo) => Boolean(equipo.disciplina_id));

// Locked state solo cuando es FIJO y hay match exacto
<EquipoCard locked={isModoFIJOAndMatched} ... />
```

### 5.3 NO inferir de cantidad_disciplinas

```typescript
// ❌ INCORRECTO — ESTE ES LA RAÍZ DEL BUG
const isElegible = card.cantidad_disciplinas > 1;

// ✅ CORRECTO — usar el campo canónico
const isElegible = card.modo_disciplinas === "ELEGIBLE";
```

---

## 6. CREACIÓN DE EQUIPOS Y UX DE COMPRA MÍNIMA

### 6.1 Flujo Atómico Recomendado (según spec F1)

El contrato actual crea Inscripción y Equipos por separado (no atómico). La recomendación según spec F1:

```
Backend: Nuevo endpoint atómico
POST /api/inscripciones/completa/
{
  evento_id,
  paquete_id,
  promocion_id,
  fusion_promocion_id?,
  delegado_id?,
  cantidad: int,          // NEW: cantidad de compra mínima
  equipos: [
    { disciplina_id, nombre }
  ]
}

→ Crea atómicamente: Inscripcion + Compra(INICIAL, PENDIENTE, cantidad) + Equipos
→ Returns { inscripcion_id, compra_id, orden_pago_id, equipos[] }
```

### 6.2 Frontend: Campo de Cantidad en Wizard

```typescript
// En el form data del wizard
interface InscripcionFormData {
  paquete_id: string;
  cantidad: number;          // NEW: cantidad de compra (validada contra minimo)
  equipos: {
    disciplina_id: string;
    nombre: string;
    categoria_id?: string;
  }[];
  aceptaciones: {
    bases: boolean;
    aptitud_fisica: boolean;
    imagen: boolean;
  };
}
```

```typescript
// Validation schema
export const InscripcionWizardSchema = z.object({
  paquete_id: z.string().min(1, 'Selecciona un paquete'),
  cantidad: z.number().int().min(
    // Dynamic minimum from paquete — set at runtime via form context
    formValues.cantidad_minima_compra,
    `Mínimo ${formValues.cantidad_minima_compra} jugadores`
  ),
  equipos: z.array(z.object({
    disciplina_id: z.string().min(1),
    nombre: z.string().min(1, 'Nombre requerido'),
  })).min(1, 'Al menos un equipo'),
  aceptaciones: z.object({
    bases: z.literal(true, { errorMap: () => ({ message: 'Debes aceptar las bases' }) }),
    aptitud_fisica: z.literal(true, { errorMap: () => ({ message: 'Debes declarar aptitud física' }) }),
    imagen: z.literal(true, { errorMap: () => ({ message: 'Debes aceptar el uso de imagen' }) }),
  }),
});
```

### 6.3 UI de Cantidad Mínima

```tsx
{/* SmartPaqueteCardsField o en el Step 3 */}
<div className="flex items-center gap-2 text-sm">
  <Users className="size-4 text-slate-500" />
  <span>
    Mínimo {paquete.cantidad_minima_compra} jugadores
  </span>
</div>

{/* Input de cantidad en el formulario */}
<NumberInput
  name="cantidad"
  min={paquete.cantidad_minima_compra}
  max={99}
  label={`Cantidad de jugadores (mínimo ${paquete.cantidad_minima_compra})`}
/>
```

---

## 7. LÍMITES ATÓMICOS DE CREACIÓN (CONTRACT BOUNDARIES)

### 7.1 Creación Actual (NO atómica)

```
Frontend              Backend
    |                    |
    | POST /inscripciones/  → Crea solo Inscripcion
    |<-- {inscripcion_id}
    |                    |
    | POST /api/equipos/   → Crea Equipo 1 (separado)
    |<-- {equipo_id}
    |                    |
    | POST /api/equipos/   → Crea Equipo 2 (separado)
    |<-- {equipo_id}
```

### 7.2 Creación Recomendada (Atómica)

```
Frontend                              Backend
    |                                    |
    | POST /api/inscripciones/completa/  → Atomically:
    |   {                                →   1. Validate cantidad >= minimo
    |     paquete_id,                    →   2. Create Inscripcion (BORRADOR)
    |     cantidad,                      →   3. Create Compra (INICIAL, PENDIENTE)
    |     equipos: [{...}]               →   4. Create all Equipos
    |   }                                →   5. Return full result
    |<-- {                              
    |     inscripcion_id,               
    |     compra_id,                    
    |     orden_pago_id,                
    |     equipos: [{id, ...}]          
    |   }                               
```

### 7.3 Contract de Error

```typescript
// Errores atómicos deben ser completos — no crear estado parcial

interface AtomicCreateError {
  code: 'PAQUETE_NOT_FOUND' | 'CANTIDAD_INSUFICIENTE' | 'DISCIPLINA_NOT_IN_PAQUETE' | 'EQUIPO_DUPLICADO';
  message: string;  // Human-readable
  field?: string;    // For form error mapping
}

// El frontend nunca debe quedarse con una Inscripcion sin Equipos por error de API
```

---

## 8. COMPORTAMIENTO DE ERRORES/LOADING/STALE CACHE

### 8.1 Errores

```typescript
// usePaqueteList — error handling
export function usePaqueteList() {
  return useQuery({
    queryKey: paqueteQueryKeys.list(),
    queryFn: fetchPaqueteList,
    staleTime: 5 * 60 * 1000,
    retry: 2,
    throwOnError: false, // Don't throw — return error state
  });
}

// En componente
const { data: paquetes, isLoading, isError, error } = usePaqueteList();

if (isError) {
  return <ErrorState message={error.message} onRetry={() => queryClient.invalidateQueries(paqueteQueryKeys.list())} />;
}
```

### 8.2 Loading States

```typescript
// Skeleton para cards
{isLoading && (
  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    {[1, 2, 3, 4].map((i) => (
      <Skeleton key={i} className="h-64 w-full rounded-2xl" />
    ))}
  </div>
)}
```

### 8.3 Stale Cache Behavior

```typescript
// El catálogo NO cambia frecuentemente — staleTime largo
const { data: paquetes } = usePaqueteList();
const selectedPaquete = paquetes?.find(p => p.id === paqueteId);

// Si el admin modifica el paquete mientras el usuario está en el wizard
// → Invalidar con: queryClient.invalidateQueries(paqueteQueryKeys.detail(paqueteId))
// → Mostrar toast: "El paquete fue actualizado, por favor verifica tu selección"
```

### 8.4 Cache Invalidation Strategy

```typescript
// Cuando se crea una inscripción exitosamente
const { mutate } = useCreateInscripcionCompleta();

mutate(payload, {
  onSuccess: () => {
    // Invalidar lista de inscripciones
    queryClient.invalidateQueries({ queryKey: queryKeys.inscripcion.all });
    // NO invalidar paquetes — el catálogo no cambió
  },
});
```

---

## 9. ESTRATEGIA DE MIGRACIÓN DESDE CONSUMIDORES ACTUALES

### 9.1 Cambios Requeridos en Backend

| Cambio | Tipo | Archivo | Descripción |
|--------|------|---------|-------------|
| Renombrar `cantidad_maxima_participantes` → `cantidad_minima_compra` | Breaking | `catalogo_results.py`, `catalogo_schemas.py`, `catalogo_presenter.py`, `paquete_selector.py` | Todos los archivos del pipeline |
| Agregar `tiene_box`, `tiene_cerveza` a `PaqueteListOut` | Aditivo | `catalogo_schemas.py`, selector, presenter | Flags derivados de beneficios |
| Agregar `disciplinas_resumen` a `PaqueteListOut` | Aditivo | `catalogo_schemas.py`, selector, presenter | Lista de siglas para chips |
| Agregar endpoint `POST /inscripciones/completa/` | Nuevo | `inscripcion_controller.py`, nuevo schema y flujo | Creación atómica |

### 9.2 Cambios Requeridos en Frontend

| Cambio | Tipo | Archivo | Descripción |
|--------|------|---------|-------------|
| Corregir `isElegible` computation | Bugfix | `SmartPaqueteCardsField.tsx:36` | Usar `modo_disciplinas === "ELEGIBLE"` |
| Corregir label precio "por persona" | Bugfix | `SmartPaqueteCardsField.tsx:101` | "por persona", no "por equipo" |
| Corregir tooltip `cantidad_maxima_participantes` | Bugfix | `PaqueteCard.tsx` | "Mínimo X jugadores" |
| Actualizar `Paquete` interface | Refactor | `catalog.service.ts`, `paquetes.service.ts` | Agregar campos nuevos, renombrar |
| Crear Zod schemas | Nuevo | `paquete.schema.ts` | Validación contracts |
| Actualizar `usePaquetes` hooks | Refactor | hooks existentes | Usar nuevos query keys y tipos |

### 9.3 Estrategia de Transición

```
FASE 1: Backend primero
  1. Agregar nuevos campos ADITIVOS (no remover viejos aún)
  2. Mantener backward compatibility durante transición
  3. Agregar endpoint atómico /inscripciones/completa/

FASE 2: Frontend nuevo
  1. Agregar nuevos schemas Zod
  2. Consumir nuevos campos
  3. Mantener fallback a campos viejos durante transición

FASE 3: Cleanup
  1. Remover campos renombrados/antiguos del backend
  2. Actualizar frontend para usar solo campos nuevos
  3. Documentar breaking change para otros consumers
```

---

## 10. ARCHIVOS AFECTADOS Y TESTS

### 10.1 Backend — Archivos a Modificar

```
backend/modules/salesianos_fest/
├── domain/
│   ├── results/
│   │   └── catalogo_results.py          # PaqueteListResult: rename + add fields
│   └── selectors/
│       └── paquete_selector.py          # Mapping: cantidad_minima_compra, beneficios flags
├── presentation/
│   ├── schemas/
│   │   └── catalogo_schemas.py         # PaqueteListOut: rename + add fields
│   ├── presenters/
│   │   └── catalogo_presenter.py        # Mapping updated
│   └── controllers/
│       └── inscripcion_controller.py   # NEW: /inscripciones/completa/ endpoint
```

### 10.2 Frontend — Archivos a Modificar

```
frontend/src/features/
├── inscripciones/
│   ├── schemas/
│   │   └── paquete.schema.ts           # NEW: Zod schemas for contracts
│   ├── services/
│   │   ├── paquete.service.ts          # NEW: typed fetch functions
│   │   └── catalog.service.ts          # UPDATE: use new contract types
│   ├── hooks/
│   │   ├── usePaquetes.ts              # REFACTOR: use new query keys
│   │   └── usePaqueteDetail.ts         # REFACTOR: use new query keys
│   └── components/
│       └── smart-fields/
│           └── SmartPaqueteCardsField.tsx  # FIX: isElegible, labels
├── landing/
│   ├── paquetes.service.ts              # UPDATE: use new contract types
│   └── hooks/
│       └── useLandingPaquetes.ts       # UPDATE: use new contract types
```

### 10.3 Tests a Actualizar/Crear

| Test | Tipo | Cobertura |
|------|------|----------|
| `test_paquete_list_contract` | Unit | Schema validation, field names |
| `test_paquete_detail_contract` | Unit | Schema validation, nested objects |
| `test_presenter_paquete_list_mapping` | Unit | Presenter → schema mapping |
| `test_presenter_paquete_detail_mapping` | Unit | Presenter → schema mapping |
| `test_api_paquete_list_endpoint` | Integration | HTTP response shape |
| `test_api_paquete_detail_endpoint` | Integration | HTTP response shape |
| `test_create_inscripcion_completa_atomica` | Integration | Atomic create flow |
| `test_elegible_badge_from_modo_disciplinas` | E2E | UI badge renders correctly |
| `test_precio_label_por_persona` | E2E | Price label correct |

---

## 11. LOTEOS DE IMPLEMENTACIÓN EN ORDEN SEGURO

### Lote 1 — Backend Schema + Selector (Foundation)
**Archivos:**
- `catalogo_results.py` — rename fields
- `catalogo_schemas.py` — update schemas
- `paquete_selector.py` — update mappings
- `catalogo_presenter.py` — update presenter

**Entregable:** Endpoint `/catalogo/paquetes/` devuelve nuevos campos sin romper backward compatibility.

**Tests:** Unit + integration para presenter y selector.

---

### Lote 2 — Frontend Types + Zod (Consumo)
**Archivos:**
- `paquete.schema.ts` — nuevos schemas Zod
- `paquete.service.ts` — servicios tipados
- `catalog.service.ts` — actualizar tipos

**Entregable:** Frontend puede parsear y validar nuevas respuestas.

**Tests:** Unit para schemas Zod.

---

### Lote 3 — Frontend Components (UI Fix)
**Archivos:**
- `SmartPaqueteCardsField.tsx` — fix `isElegible`, labels
- `PaqueteCard.tsx` — fix tooltip
- `usePaquetes.ts` — nuevos query keys

**Entregable:** Badge ELEGIBLE/FIJO funciona correctamente; label precio "por persona".

**Tests:** E2E para badge y label.

---

### Lote 4 — Backend Atomic Create (Nuevo Endpoint)
**Archivos:**
- `CrearInscripcionCompletaIn` schema
- `CrearInscripcionCompletaFlujo` flujo
- `InscripcionOrchestrator.crear_inscripcion_completa`
- `inscripcion_controller.py` — nuevo endpoint

**Entregable:** `POST /inscripciones/completa/` crea atómicamente Inscripcion + Compra + Equipos.

**Tests:** Integration + E2E para flujo atómico.

---

### Lote 5 — Frontend Wizard Integration (Consumo del Nuevo Endpoint)
**Archivos:**
- Wizard actualiza para usar nuevo endpoint
- `useCreateInscripcionCompleta` hook
- Form validation con cantidad mínima

**Entregable:** Wizard completo: paquete → cantidad + equipos → creación atómica.

**Tests:** E2E flujo completo.

---

## 12. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|------------|--------|------------|
| Breaking change confunde consumers existentes | Media | Alto | Mantener backward compatibility en Lote 1; agregar alias temporales |
| Frontend infiere todavía de campos viejos | Media | Alto | Code review enfático; tests E2E que fallen si se infiere |
| Atomic create es complejo y puede fallar en race conditions | Baja | Alto | Tests de concurrencia; `select_for_update` en flujos |
| Stale cache causa inconsistencia en wizard | Baja | Medio | Invalidación explícita post-creación; toast de advertencia |
| Zod validation too strict bloquea cambios menores | Baja | Bajo | Usar `safeParse`; fallback a datos crudos con log |

---

## 13. REGLAS OFICIALES DEL CATÁLOGO (Preservar)

| Paquete | Tipo | Modo | minimo_compra_inicial | Beneficios |
|---------|------|------|----------------------|------------|
| Reencuentro + Fiesta | PACK | ELEGIBLE | 10 | Fiesta (FIJO_INICIAL) |
| Pichanga + Fiesta | PACK | FIJO | 10 | Fiesta (FIJO_INICIAL) |
| Dúo + Fiesta Box | PACK | ELEGIBLE | 15 | Fiesta (POR_CUPO) + Box + Cerveza |
| Trío + Fiesta Box | PACK | ELEGIBLE | 20 | Fiesta (POR_CUPO) + Box + Cerveza |
| Fútbol 7 Masculino | DISCIPLINA | FIJO | 7 | — |
| Fútbol 7 Femenino | DISCIPLINA | FIJO | 7 | — |
| Vóley Mixto | DISCIPLINA | FIJO | 6 | — |
| Básquet Masculino | DISCIPLINA | FIJO | 5 | — |

**Reglas preservadas:**
- `modo_disciplinas` determina badge FIJO/ELEGIBLE — no `cantidad_disciplinas`
- `minimo_compra_inicial` es mínimo comercial, no máximo deportivo
- Precios son por persona, no por equipo
- Beneficios `FIESTA` con `alcance INDIVIDUAL` y `modo_calculo POR_CUPO` = cada pessoa paga recibe beneficio

---

## 14. CONTRATO DE PRESENTADOR — CHECKLIST DE ACEPTACIÓN

- [ ] `PaqueteListContract` incluye `modo_disciplinas` canónico (no inferido)
- [ ] `PaqueteListContract` incluye `cantidad_minima_compra` (no `cantidad_maxima_participantes`)
- [ ] `PaqueteListContract` incluye `tiene_fiesta`, `tiene_box`, `tiene_cerveza`
- [ ] `PaqueteListContract` incluye `disciplinas_resumen` para chips
- [ ] `PaqueteDetailContract` extiende lista con `descripcion`, `precios`, `beneficios`, `disciplinas`
- [ ] Frontend Zod schemas hacen mirror exacto de contracts
- [ ] `isElegible(paquete)` usa `modo_disciplinas === "ELEGIBLE"`
- [ ] Label precio dice "por persona", no "por equipo"
- [ ] Tooltip dice "Mínimo X jugadores", no "Máximo X participantes"
- [ ] Query keys son estables y tipadas
- [ ] Error handling con fallback a datos crudos
- [ ] Tests cubren schema validation y rendering de badges

---

*Plan generado mediante SDD Explore read-only. No modifica código fuente. Todos los hallazgos están respaldados por evidencia de archivos reales.*
