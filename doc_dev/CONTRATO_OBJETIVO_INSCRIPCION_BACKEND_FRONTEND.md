# CONTRATO OBJETIVO: Inscripción Frontend ↔ Backend — Salesianos FEST

> **Proyecto:** Salesianos FEST
> **Fecha:** 2026-10-18
> **Artifact:** `sdd/salesianos-fest-inscription-target-contract/explore`
> **Modo:** Read-only — documentación de contrato objetivo
> **Idioma:** Español (documentación técnica del proyecto)

---

## RESUMEN EJECUTIVO

Este documento define el **contrato objetivo completo** entre el frontend de inscripción y el backend de Salesianos FEST. Especifica el comportamiento exacto que debe implementarse: el frontend recibe un objeto `PaquetePresenter` completo en la selección y **no realiza ningún fetch adicional** de detalle. El backend permanece autoritativo y revalida todas las reglas en cada mutación.

**Regla cardinal:** `GET /catalogo/paquetes/` retorna el 100% de la información necesaria para todo el flujo de inscripción. **No hay fetch de detalle después de seleccionar paquete.**

---

## 1. PROPÓSITO DEL CONTRATO

### 1.1 Objetivo

Definir un contrato rígido y sin ambigüedades entre el frontend de inscripción y el backend, de modo que:

1. El frontend pueda completar todo el flujo de inscripción (paquete → equipos → cantidad → roster → consents) sin realizar **ningún fetch adicional** tras seleccionar un paquete.
2. El backend sea la única fuente autoritativa de reglas de negocio y revalide todo en cada mutación.
3. Se elimine la necesidad de `toCompletaBackendPayload` como intermediario compleja.

### 1.2 Principios

| # | Principio | Descripción |
|---|-----------|-------------|
| O1 | **Contrato completo en lista** | `GET /catalogo/paquetes/` retorna todo lo necesario para el wizard completo |
| O2 | **Sin fetch post-selección** | El frontend NO llama a `GET /catalogo/paquetes/{id}/` después de seleccionar paquete |
| O3 | **Backend autoritativo** | Toda validación de reglas ocurre en backend en cada mutación |
| O4 | **Esquemas espejo** | Backend Pydantic ↔ Frontend Zod con mapeo 1:1 exacto |
| O5 | **Eliminación de toCompletaBackendPayload** | El payload se construye directamente desde el estado del formulario |

### 1.3 Lo que NO es este documento

- No defiende ni extiende el actual enfoque de `toCompletaBackendPayload`
- No documenta el estado actual (eso está en `INFORME_CONTRASTE_FRONTEND_BACKEND_SALESIANOS_FEST.md`)
- No propone arquitectura parcial — define el estado objetivo completo

---

## 2. PAQUETE PRESENTER CANÓNICO — `PaquetePresenter`

### 2.1 JSON Completo — `PaquetePresenter`

Este es el objeto retornado por `GET /catalogo/paquetes/`. Contiene **todo** lo necesario para el wizard.

```json
{
  "id": "uuid-del-paquete",
  "evento_id": "uuid-del-evento",
  "nombre": "Reencuentro + Fiesta",
  "descripcion": "Descripción completa del paquete...",
  "tipo": "PACK",
  "modo_disciplinas": "ELEGIBLE",
  "cantidad_disciplinas": 1,
  "cantidad_minima_compra": 10,
  "cantidad_maxima_equipos": 3,
  "precio_preventa": 40.00,
  "precio_regular": 50.00,
  "precio_promocional": null,
  "tiene_fiesta": true,
  "tiene_box": false,
  "tiene_cerveza": false,
  "disciplinas_resumen": ["F7F", "VOL", "BAS"],
  "precios": [
    {
      "etapa": "PREVENTA",
      "precio_unitario": 40.00,
      "vigente_desde": "2026-01-01",
      "vigente_hasta": "2026-12-31"
    },
    {
      "etapa": "REGULAR",
      "precio_unitario": 50.00,
      "vigente_desde": "2027-01-01",
      "vigente_hasta": null
    }
  ],
  "beneficios": [
    {
      "tipo": "FIESTA",
      "cantidad": 1,
      "alcance": "INDIVIDUAL",
      "modo_calculo": "FIJO_INICIAL"
    }
  ],
  "disciplinas": [
    {
      "disciplina_id": "uuid-f7f",
      "disciplina_nombre": "Fútbol 7 Femenino",
      "disciplina_sigla": "F7F",
      "min_jugadores": 7,
      "max_jugadores": 10
    },
    {
      "disciplina_id": "uuid-vol",
      "disciplina_nombre": "Vóley Mixto",
      "disciplina_sigla": "VOL",
      "min_jugadores": 6,
      "max_jugadores": 8
    },
    {
      "disciplina_id": "uuid-bas",
      "disciplina_nombre": "Básquet Masculino",
      "disciplina_sigla": "BAS",
      "min_jugadores": 5,
      "max_jugadores": 10
    }
  ]
}
```

### 2.2 Campos del `PaquetePresenter` — Definición Exacta

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | `string` (UUID) | Identificador único del paquete | `"550e8400-e29b..."` |
| `evento_id` | `string` (UUID) | Evento al que pertenece | `"evento-fest-2026"` |
| `nombre` | `string` | Nombre comercial del paquete | `"Reencuentro + Fiesta"` |
| `descripcion` | `string` | Descripción completa | `"Paquete todo en uno..."` |
| `tipo` | `string` | `PACK` \| `DISCIPLINA` | `"PACK"` |
| `modo_disciplinas` | `string` | `FIJO` \| `ELEGIBLE` — **canónico** | `"ELEGIBLE"` |
| `cantidad_disciplinas` | `integer` | Cantidad de disciplinas requeridas (1-3) | `1` |
| `cantidad_minima_compra` | `integer` | Mínimo comercial de participantes | `10` |
| `cantidad_maxima_equipos` | `integer` | Máximo de equipos que se pueden crear | `3` |
| `precio_preventa` | `number\|null` | Precio en preventa (S/) | `40.00` |
| `precio_regular` | `number\|null` | Precio regular (S/) | `50.00` |
| `precio_promocional` | `number\|null` | Precio promocional vigente (si aplica) | `null` |
| `tiene_fiesta` | `boolean` | Incluye beneficio fiesta | `true` |
| `tiene_box` | `boolean` | Incluye beneficio box | `false` |
| `tiene_cerveza` | `boolean` | Incluye beneficio cerveza | `false` |
| `disciplinas_resumen` | `string[]` | Siglas de disciplinas disponibles | `["F7F","VOL","BAS"]` |
| `precios` | `PaquetePrecio[]` | Lista de precios por etapa | (ver 2.3) |
| `beneficios` | `PaqueteBeneficio[]` | Lista de beneficios incluidos | (ver 2.3) |
| `disciplinas` | `PaqueteDisciplina[]` | Disciplinas disponibles con min/max jugadores | (ver 2.3) |

### 2.3 Sub-objetos del `PaquetePresenter`

```typescript
// PaquetePrecio
interface PaquetePrecio {
  etapa: "PREVENTA" | "REGULAR";
  precio_unitario: number; // Decimal como float en JSON
  vigente_desde: string;   // ISO date "YYYY-MM-DD"
  vigente_hasta: string | null;
}

// PaqueteBeneficio
interface PaqueteBeneficio {
  tipo: "FIESTA" | "BOX" | "CERVEZA";
  cantidad: number;
  alcance: "INDIVIDUAL" | "GRUPAL";
  modo_calculo: "POR_CUPO" | "FIJO_INICIAL";
}

// PaqueteDisciplina
interface PaqueteDisciplina {
  disciplina_id: string;
  disciplina_nombre: string;
  disciplina_sigla: string;
  min_jugadores: number | null;  // null si no aplica
  max_jugadores: number | null;  // null si no aplica
}
```

### 2.4 Contrato de backend actual — Verificado ✅

**Backend ya retorna este contrato en `GET /catalogo/paquetes/`:**

- `PaqueteListOut` (backend): incluye `cantidad_minima_compra` (ya renombrado desde `cantidad_maxima_participantes`), `tiene_fiesta`, `tiene_box`, `tiene_cerveza`, `disciplinas_resumen` ✅
- `PaqueteDetailOut` (backend): incluye `precios`, `beneficios`, `disciplinas`, `minimo_compra_inicial` ✅

**Frontend ya tiene los Zod schemas correspondientes:**

- `PaqueteListContractSchema` con campos completos incluyendo `disciplinas` opcional ✅
- `PaqueteDetailContractSchema` extiende la lista con campos de detalle ✅
- `isElegible(paquete)` usa `modo_disciplinas === "ELEGIBLE"` ✅ (ya corregido)

---

## 3. MATRIZ DE RUTAS: ESTADO ACTUAL vs OBJETIVO

### 3.1 Estado Actual (verificado de código)

| Ruta | Método | Backend | Frontend | Estado |
|------|--------|---------|---------|--------|
| `/catalogo/paquetes/` | GET | ✅ `CatalogoController.listar_paquetes` | ✅ `usePaquetes()` consume | Implementado |
| `/catalogo/paquetes/{id}/` | GET | ✅ `CatalogoController.detalle_paquete` | ⚠️ Llama `fetchPaqueteDetail` tras selección | **PARCIAL — debe eliminarse** |
| `/inscripciones/completa/` | POST | ✅ `crear_inscripcion_completa` | ✅ `useCreateInscripcionCompleta` consume | Implementado |
| `/inscripciones/` | POST | ✅ `crear_inscripcion` (plano) | ❌ No usado por wizard | Legacy — no tocar |
| `/inscripciones/` | GET | ✅ Lista propias | ✅ `fetchInscripciones` | Implementado |
| `/inscripciones/{id}` | GET | ✅ Detalle simple | ✅ `fetchInscripcionDetalle` | Implementado |
| `/inscripciones/{id}/detalle` | GET | ✅ Detalle con roster | ✅ `getInscripcionDetalle` | Implementado |
| `/inscripciones/{id}/personas` | POST | ✅ Agregar persona | ✅ `agregarParticipantes` | Implementado |
| `/participaciones/{id}` | PATCH | ✅ Actualizar participación | ✅ `useEditarParticipante` | Implementado |
| `/participaciones/{id}/mover` | PATCH | ✅ Mover participación | ✅ `useMoverParticipante` | Implementado |
| `/participaciones/{id}/retirar` | PATCH | ✅ Retirar participación | ✅ `useEliminarParticipante` | Implementado |

### 3.2 Estado Objetivo

| Ruta | Método | Contrato | Cambios |
|------|--------|----------|---------|
| `/catalogo/paquetes/` | GET | `PaquetePresenter[]` — **único endpoint de catálogo usado** | Ninguno — ya está correcto |
| `/catalogo/paquetes/{id}/` | GET | — | **ELIMINAR** consumo desde wizard |
| `/inscripciones/completa/` | POST | `InscripcionCompletaRequest` → `InscripcionCompletaResponse` | Ninguno — ya está correcto |
| `/inscripciones/` | GET | `InscripcionSummary[]` | Ninguno |
| `/inscripciones/{id}/detalle` | GET | `InscripcionDetailResponse` | Ninguno |
| `/inscripciones/{id}/personas` | POST | `AgregarPersonaRequest` | Ninguno |

### 3.3 Regla de Eliminación

**ELIMINAR del flujo del wizard:** `fetchPaqueteDetail(watchedPaqueteId)` después de seleccionar paquete.

El `PaquetePresenter` ya contiene `precios`, `beneficios`, `disciplinas`, `minimo_compra_inicial` — no se necesita fetch adicional.

---

## 4. PROPIEDAD DE TABLAS Y ESCRITURA DE DATOS

### 4.1 Backend — Tablas y Responsabilidades

| Tabla | Owned By | Writes | Lectura Frontend |
|-------|----------|--------|-----------------|
| `paquetes` | `salesianos_fest` | Admin only | GET `/catalogo/paquetes/` — público |
| `paquete_disciplinas` | `salesianos_fest` | Admin only | Incluido en `PaquetePresenter.disciplinas` |
| `paquete_precios` | `salesianos_fest` | Admin only | Incluido en `PaquetePresenter.precios` |
| `paquete_beneficios` | `salesianos_fest` | Admin only | Incluido en `PaquetePresenter.beneficios` |
| `inscripciones` | `salesianos_fest` | `POST /inscripciones/completa/` | `GET /inscripciones/{id}/detalle` |
| `compras` | `salesianos_fest` | Creado atómicamente en `/completa/` | No se consulta directamente |
| `equipos` | `salesianos_fest` | Creado atómicamente en `/completa/` | `GET /inscripciones/{id}/detalle` |
| `inscripcion_personas` | `salesianos_fest` | `POST /{id}/personas` | `GET /inscripciones/{id}/detalle` |
| `participaciones` | `salesianos_fest` | `POST /{id}/personas` (interno) | `GET /inscripciones/{id}/detalle` |
| `asignaciones_cupo` | `salesianos_fest` | Backend en pago confirmado | No expuesta a frontend |

### 4.2 Flujo de Escritura

```
Wizard Submit (frontend)
  │
  │ POST /inscripciones/completa/
  │ {
  │   evento_id, paquete_id, promocion_id,
  │   cantidad, equipos: [{disciplina_id, nombre}],
  │   aceptaciones: {bases, aptitud_fisica, imagen}
  │ }
  │
Backend (atómico, transaction.atomic):
  │
  ├─→ Valida cantidad >= paquete.minimo_compra_inicial
  ├─→ Valida fecha_limite del evento
  ├─→ Obtiene precio vigente (snapshot)
  ├─→ Crea Inscripcion (BORRADOR)
  ├─→ Crea Compra (INICIAL, PENDIENTE)
  ├─→ Crea OrdenPago (PENDIENTE)
  ├─→ Crea Equipos (uno por slot de disciplina)
  │   ⚠ NO crea participaciones aún
  │
  └─→ Return { inscripcion_id, compra_id, orden_pago_id, equipos[], precio_unitario, total }
```

### 4.3 Validaciones de Escritura en Backend

| Regla | Dónde | Tipo | Error |
|-------|--------|------|-------|
| `cantidad >= minimo_compra_inicial` | `CrearInscripcionCompletaFlujo._crear_atomico` | Excepción | `CantidadInsuficienteError` |
| `fecha_limite` del evento vigente | `CrearInscripcionCompletaFlujo._crear_atomico` | Excepción | `FechaLimiteExcedidaError` |
| `paquete_id` existe | `CrearInscripcionCompletaFlujo._crear_atomico` | Excepción | `PaqueteNotFoundError` |
| R11: (evento, disciplina, persona) único activo | `ParticipacionService.crear()` | Excepción + DB constraint | `DuplicateParticipationError` |
| `max_jugadores` por disciplina | `ParticipacionService.crear()` | Excepción | `CupoExcedidoError` |

---

## 5. FRONTEND: ESTADO, PANTALLAS Y CAMPOS DE FORMULARIO

### 5.1 Estado del Wizard

```typescript
// Estado del formulario en wizard
interface InscripcionWizardState {
  // Step 1: Selección de paquete
  paquete: PaquetePresenter | null;  // Objeto completo del catálogo — NO se hace fetch adicional

  // Step 2: Equipos y promoción
  promocion_id: string;
  fusion_promocion_id: string | null;
  equipos: EquipoDraft[];

  // Step 3: Declaraciones
  aceptaciones: {
    bases: boolean;        // z.literal(true)
    aptitud_fisica: boolean; // z.literal(true)
    imagen: boolean;        // z.literal(true)
  };
}
```

### 5.2 Pantallas del Wizard

| Step | Título | Contenido |
|------|--------|-----------|
| 1 | "Elige tu paquete" | `SmartPaqueteCardsField` — cards de paquetes del catálogo |
| 2 | "Equipos y promoción" | `SmartEquipoField` + selector de promoción |
| 3 | "Declaraciones" | `StepDeclarations` — consentimientos |

### 5.3 Campos del Formulario

```typescript
// Step 1 — PaqueteSelectionField
campo: paquete_id (string, requerido)
fuente: PaquetePresenter.id del catálogo

// Step 2 — EquiposStepLayout
campo: promocion_id (string, requerido)
campo: fusion_promocion_id (string, opcional)
campo: equipos[] (array, minLength=1)
  - disciplina_id: string (requerido)
  - nombre: string (requerido, max 120)
  - categoria_id: string | null (opcional)

// Step 3 — StepDeclarations
campo: aceptaciones.bases (literal true)
campo: aceptaciones.aptitud_fisica (literal true)
campo: aceptaciones.imagen (literal true)
```

---

## 6. UX EXACTA: DESDE SELECCIÓN DE PAQUETE HASTA ROSTER Y CONSENTIMIENTOS

### 6.1 Flujo Completo Paso a Paso

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: SELECCIÓN DE PAQUETE                                        │
│                                                                     │
│ Usuario ve:                                                          │
│   - Cards con nombre, precio (por persona), badge FIJO/ELEGIBLE     │
│   - "Mínimo X jugadores" en cada card                               │
│   - Chips de disciplinas disponibles                                 │
│   - Flags de beneficios (fiesta, box, cerveza)                      │
│                                                                     │
│ Al hacer click en card:                                              │
│   → paquete_id se almacena en form state                            │
│   → PaquetePresenter COMPLETO se almacena en selectedPaquete         │
│   → ⚠ NO se hace fetch a /paquetes/{id}/                           │
│   → Wizard avanza a Step 2                                           │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: EQUIPOS Y PROMOCIÓN                                         │
│                                                                     │
│ Usuario ve (derivado del PaquetePresenter almacenado):               │
│   - SmartEquipoField pre-configurado con:                            │
│     • modo_disciplinas: FIJO → slots lockeados con disciplinas      │
│     • modo_disciplinas: ELEGIBLE → slots editables                  │
│     • cantidad_disciplinas: del paquete                              │
│     • disciplinas disponibles (del PaquetePresenter.disciplinas)    │
│     • min_jugadores / max_jugadores por disciplina                   │
│                                                                     │
│ Campo cantidad (derivado de PaquetePresenter.minimo_compra_inicial): │
│   - Input number con min = cantidad_minima_compra                   │
│   - Label: "Cantidad de jugadores (mínimo X)"                       │
│                                                                     │
│ Selección de promoción:                                             │
│   - Dropdown con promociones del catálogo                            │
│                                                                     │
│ Creación de equipos:                                                 │
│   - SmartEquipoField permite crear N equipos                         │
│   - Cada equipo: disciplina_id + nombre                             │
│   - FIJO: pre-llena y lockea la única disciplina                     │
│   - ELEGIBLE: permite seleccionar de disciplinas disponibles         │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: DECLARACIONES                                               │
│                                                                     │
│ Usuario ve:                                                          │
│   - Checkbox: "Acepto las bases del evento"                        │
│   - Checkbox: "Declaro aptitud física para participar"               │
│   - Checkbox: "Autorizo uso de imagen"                              │
│                                                                     │
│ Todos son z.literal(true) — no se envían al backend en el payload   │
│ (Se graban por persona en POST /{id}/personas)                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SUBMIT                                                               │
│                                                                     │
│ Frontend construye payload directo (SIN toCompletaBackendPayload):   │
│                                                                     │
│ POST /inscripciones/completa/                                        │
│ {                                                                    │
│   evento_id: selectedPaquete.evento_id,                              │
│   paquete_id: selectedPaquete.id,                                    │
│   promocion_id: formValues.promocion_id,                             │
│   cantidad: formValues.cantidad,  // validado min >= minimo_compra   │
│   equipos: formValues.equipos.map(eq => ({                           │
│     disciplina_id: eq.disciplina_id,                                 │
│     nombre: eq.nombre,                                               │
│   })),                                                               │
│   estado: "BORRADOR",                                                │
│ }                                                                    │
│                                                                     │
│ Backend valida TODO y retorna:                                       │
│ {                                                                    │
│   inscripcion_id, compra_id, orden_pago_id,                          │
│   cantidad, precio_unitario, total, equipos[]                        │
│ }                                                                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ POST-CREACIÓN: ROSTER Y CONSENTIMIENTOS                             │
│                                                                     │
│ En /dashboard/inscripcion/{id}:                                      │
│                                                                     │
│ Usuario agrega personas via:                                          │
│   POST /inscripciones/{id}/personas                                  │
│   {                                                                  │
│     persona_id,                                                      │
│     equipo_id (opcional — puede crearse inline)                     │
│   }                                                                  │
│                                                                     │
│ Backend graba aceptaciones por persona:                               │
│   - AceptacionInscripcion (bases, aptitud, imagen, fecha, ip)       │
│                                                                     │
│ Cada persona puede tener N participaciones:                          │
│   POST /participaciones/                                             │
│   {                                                                  │
│     inscripcion_persona_id,                                         │
│     equipo_id,                                                       │
│     rol, talla_camiseta, notas                                       │
│   }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Regla de Validación de Cantidad en Frontend

```typescript
// Validación en tiempo real (complementa la validación del backend)
const cantidadMinima = selectedPaquete?.cantidad_minima_compra ?? 1;
const cantidad = formValues.cantidad;

if (cantidad < cantidadMinima) {
  // Mostrar error: `La cantidad mínima es ${cantidadMinima} jugadores`
}
```

---

## 7. COMPORTAMIENTO FIJO/ELEGIBLE — EJEMPLOS PARA TODOS LOS PAQUETES OFICIALES

### 7.1 Paquetes PACK

#### Reencuentro + Fiesta (`modo: ELEGIBLE`, `cantidad_disciplinas: 1`, `minimo: 10`)

```json
{
  "nombre": "Reencuentro + Fiesta",
  "modo_disciplinas": "ELEGIBLE",
  "cantidad_disciplinas": 1,
  "cantidad_minima_compra": 10,
  "disciplinas": [
    { "disciplina_id": "...", "disciplina_nombre": "Fútbol 7 Femenino", "disciplina_sigla": "F7F", "min_jugadores": 7, "max_jugadores": 10 },
    { "disciplina_id": "...", "disciplina_nombre": "Vóley Mixto", "disciplina_sigla": "VOL", "min_jugadores": 6, "max_jugadores": 8 },
    { "disciplina_id": "...", "disciplina_nombre": "Básquet Masculino", "disciplina_sigla": "BAS", "min_jugadores": 5, "max_jugadores": 10 }
  ]
}
```

**UX FIJO/ELEGIBLE:**
- Badge: "ELEGIBLE" (amber)
- SmartEquipoField muestra 1 slot de disciplina **no lockeado**
- Usuario selecciona 1 disciplina de F7F, VOL o BAS
- `cantidad_disciplinas = 1` → 1 equipo mínimo

#### Pichanga + Fiesta (`modo: FIJO`, `cantidad_disciplinas: 1`, `minimo: 10`)

```json
{
  "nombre": "Pichanga + Fiesta",
  "modo_disciplinas": "FIJO",
  "cantidad_disciplinas": 1,
  "cantidad_minima_compra": 10,
  "disciplinas": [
    { "disciplina_id": "...", "disciplina_nombre": "Fútbol 7 Masculino", "disciplina_sigla": "F7M", "min_jugadores": 7, "max_jugadores": 10 }
  ]
}
```

**UX FIJO/ELEGIBLE:**
- Badge: "FIJO" (indigo)
- SmartEquipoField muestra 1 slot de disciplina **lockeado** con F7M
- `isFIJO && disciplinas.length === cantidad_disciplinas` → lock
- Usuario no puede cambiar la disciplina

#### Dúo + Fiesta Box (`modo: ELEGIBLE`, `cantidad_disciplinas: 2`, `minimo: 15`)

```json
{
  "nombre": "Dúo + Fiesta Box",
  "modo_disciplinas": "ELEGIBLE",
  "cantidad_disciplinas": 2,
  "cantidad_minima_compra": 15,
  "beneficios": [
    { "tipo": "FIESTA", "cantidad": 1, "alcance": "INDIVIDUAL", "modo_calculo": "POR_CUPO" },
    { "tipo": "BOX", "cantidad": 1, "alcance": "GRUPAL", "modo_calculo": "FIJO_INICIAL" },
    { "tipo": "CERVEZA", "cantidad": 1, "alcance": "GRUPAL", "modo_calculo": "FIJO_INICIAL" }
  ],
  "disciplinas": [
    { "disciplina_id": "...", "disciplina_nombre": "Vóley Mixto", "disciplina_sigla": "VOL" },
    { "disciplina_id": "...", "disciplina_nombre": "Básquet Masculino", "disciplina_sigla": "BAS" }
  ]
}
```

**UX FIJO/ELEGIBLE:**
- Badge: "ELEGIBLE" (amber)
- SmartEquipoField muestra **2 slots editables**
- Usuario elige 2 disciplinas de VOL y BAS
- El tooltip muestra: "Selecciona 2 disciplinas de la oferta disponible"

#### Trío + Fiesta Box (`modo: ELEGIBLE`, `cantidad_disciplinas: 3`, `minimo: 20`)

```json
{
  "nombre": "Trío + Fiesta Box",
  "modo_disciplinas": "ELEGIBLE",
  "cantidad_disciplinas": 3,
  "cantidad_minima_compra": 20,
  "beneficios": [
    { "tipo": "FIESTA", "cantidad": 1, "alcance": "INDIVIDUAL", "modo_calculo": "POR_CUPO" },
    { "tipo": "BOX", "cantidad": 1, "alcance": "GRUPAL", "modo_calculo": "FIJO_INICIAL" },
    { "tipo": "CERVEZA", "cantidad": 1, "alcance": "GRUPAL", "modo_calculo": "FIJO_INICIAL" }
  ],
  "disciplinas": [
    { "disciplina_id": "...", "disciplina_nombre": "Fútbol 7 Masculino", "disciplina_sigla": "F7M" },
    { "disciplina_id": "...", "disciplina_nombre": "Vóley Mixto", "disciplina_sigla": "VOL" },
    { "disciplina_id": "...", "disciplina_nombre": "Básquet Masculino", "disciplina_sigla": "BAS" }
  ]
}
```

**UX FIJO/ELEGIBLE:**
- Badge: "ELEGIBLE" (amber)
- SmartEquipoField muestra **3 slots editables**
- Usuario elige 3 disciplinas de F7M, VOL, BAS

### 7.2 Paquetes DISCIPLINA

#### Fútbol 7 Masculino (`modo: FIJO`, `cantidad_disciplinas: 1`, `minimo: 7`)

```json
{
  "nombre": "Fútbol 7 Masculino",
  "tipo": "DISCIPLINA",
  "modo_disciplinas": "FIJO",
  "cantidad_disciplinas": 1,
  "cantidad_minima_compra": 7,
  "beneficios": [],
  "disciplinas": [
    { "disciplina_id": "...", "disciplina_nombre": "Fútbol 7 Masculino", "disciplina_sigla": "F7M", "min_jugadores": 7, "max_jugadores": 10 }
  ]
}
```

**UX:** Badge "FIJO", 1 slot lockeado con F7M.

#### Vóley Mixto (`modo: FIJO`, `cantidad_disciplinas: 1`, `minimo: 6`)

**UX:** Badge "FIJO", 1 slot lockeado con VOL.

#### Básquet Masculino (`modo: FIJO`, `cantidad_disciplinas: 1`, `minimo: 5`)

**UX:** Badge "FIJO", 1 slot lockeado con BAS.

---

## 8. ESQUEMAS DE REQUEST/RESPONSE — API DE MUTACIONES

### 8.1 Creación Atómica: `POST /inscripciones/completa/`

**Request:**
```json
{
  "evento_id": "uuid",
  "paquete_id": "uuid",
  "promocion_id": "uuid",
  "fusion_promocion_id": null,
  "delegado_id": null,
  "cantidad": 10,
  "equipos": [
    {
      "disciplina_id": "uuid-vol",
      "nombre": "Los Chamos"
    }
  ],
  "estado": "BORRADOR",
  "observacion": ""
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "La inscripción con compra inicial se registró correctamente.",
  "data": {
    "inscripcion_id": "uuid-inscripcion",
    "inscripcion_estado": "BORRADOR",
    "compra_id": "uuid-compra",
    "orden_pago_id": "uuid-orden",
    "compra_estado": "PENDIENTE",
    "cantidad": 10,
    "precio_unitario": 40.00,
    "total": 400.00,
    "equipos": [
      {
        "id": "uuid-equipo",
        "inscripcion_id": "uuid-inscripcion",
        "disciplina": { "id": "uuid", "nombre": "Vóley Mixto", "sigla": "VOL" },
        "categoria": null,
        "nombre": "Los Chamos",
        "estado": "EQUIPO_ACTIVO",
        "created_at": "2026-10-18T10:00:00Z"
      }
    ]
  }
}
```

**Errores posibles:**

| code HTTP | code | message |
|-----------|------|---------|
| 400 | `PAQUETE_NOT_FOUND` | Paquete no encontrado |
| 400 | `CANTIDAD_INSUFICIENTE` | Cantidad insuficiente: se requiere mínimo X |
| 400 | `FECHA_LIMITE_EXCEDIDA` | La fecha límite de inscripción ha expirado |
| 401 | — | No autenticado |

### 8.2 Agregar Persona: `POST /inscripciones/{id}/personas`

**Request:**
```json
{
  "persona_id": "uuid-persona",
  "equipo_id": "uuid-equipo"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "La persona se agregó al equipo correctamente.",
  "data": {
    "participante": {
      "id": "uuid-participacion",
      "inscripcion_persona_id": "uuid-ip",
      "equipo_id": "uuid-equipo",
      "equipo_nombre": "Los Chamos",
      "evento_id": "uuid-evento",
      "disciplina": { "id": "uuid", "nombre": "Vóley Mixto", "sigla": "VOL" },
      "persona": { "id": "uuid", "nombre": "Juan Pérez", "numero_documento": "12345678" },
      "rol": "Jugador",
      "talla_camiseta": "M",
      "notas": null,
      "estado": "ACTIVO",
      "created_at": "2026-10-18T10:05:00Z"
    }
  }
}
```

### 8.3 Actualizar Participación: `PATCH /participaciones/{id}`

**Request:**
```json
{
  "rol": "Delegado",
  "talla_camiseta": "L",
  "notas": "Capitán del equipo",
  "estado": "ACTIVO"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Participación actualizada correctamente.",
  "data": { /* ParticipacionOut completo */ }
}
```

### 8.4 Mover Participación: `PATCH /participaciones/{id}/mover`

**Request:**
```json
{
  "equipo_destino_id": "uuid-equipo-destino"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Participación movida correctamente.",
  "data": { /* ParticipacionOut actualizado */ }
}
```

### 8.5 Retirar Participación: `PATCH /participaciones/{id}/retirar`

**Response (200):**
```json
{
  "success": true,
  "message": "Participación retirada correctamente.",
  "data": { /* ParticipacionOut con estado RETIRADO */ }
}
```

---

## 9. REGLAS DE VALIDACIÓN DEL SERVIDOR

### 9.1 En `POST /inscripciones/completa/`

| Campo | Validación | Error |
|-------|-----------|-------|
| `evento_id` | UUID válido, existe | `EVENTO_NOT_FOUND` |
| `paquete_id` | UUID válido, existe, activo | `PAQUETE_NOT_FOUND` |
| `promocion_id` | UUID válido, existe | `PROMOCION_NOT_FOUND` |
| `cantidad` | Entero >= `paquete.minimo_compra_inicial` | `CANTIDAD_INSUFICIENTE` |
| `equipos` | Array no vacío, máximo `paquete.cantidad_maxima_equipos` | `EQUIPOS_EXCEDIDOS` |
| `equipos[].disciplina_id` | Debe estar en `paquete.disciplinas` | `DISCIPLINA_NOT_IN_PAQUETE` |
| `equipos[].nombre` | No vacío, max 120 chars | `NOMBRE_EQUIPO_INVALIDO` |
| Fecha límite | `evento.fecha_limite_inscripcion >= hoy` | `FECHA_LIMITE_EXCEDIDA` |

### 9.2 En `POST /inscripciones/{id}/personas`

| Campo | Validación | Error |
|-------|-----------|-------|
| `persona_id` | UUID válido, existe | `PERSONA_NOT_FOUND` |
| `equipo_id` | UUID válido, pertenece a la inscripción | `EQUIPO_NOT_FOUND` |
| R11 | (evento, disciplina, persona) único activo | `DUPLICATE_PARTICIPATION` |

### 9.3 En `PATCH /participaciones/{id}`

| Campo | Validación | Error |
|-------|-----------|-------|
| `talla_camiseta` | Uno de: XS, S, M, L, XL, XXL | `TALLA_INVALIDA` |
| `estado` | `ACTIVO` \| `RETIRADO` | `ESTADO_INVALIDO` |

---

## 10. COMPORTAMIENTO DE ERRORES, LOADING Y CACHE

### 10.1 Errores

```typescript
// En useCreateInscripcionCompleta
onError: (error) => {
  if (error.code === 'CANTIDAD_INSUFICIENTE') {
    // Mostrar toast específico
    toast.error(`Cantidad insuficiente. Mínimo: ${error.minimo}`);
  } else if (error.code === 'PAQUETE_NOT_FOUND') {
    toast.error('El paquete seleccionado no existe');
  } else if (error.code === 'FECHA_LIMITE_EXCEDIDA') {
    toast.error('La fecha límite de inscripción ha expirado');
  } else {
    toast.error('Error al crear la inscripción. Intenta nuevamente.');
  }
}
```

### 10.2 Loading States

| Contexto | UI |
|----------|-----|
| Catálogo cargando | Skeleton cards (3-4 cards con `h-64`) |
| Wizard submit | Button disabled + spinner, texto "Creando..." |
| Detalle cargando | Skeleton con estructura del detalle |
| Agregar persona | Spinner en botón "Agregar" |

### 10.3 Cache

```typescript
// Catálogo — staleTime largo (cambios solo desde admin)
const { data: paquetes } = usePaquetes();
// staleTime: 5 minutos
// gcTime: 30 minutos

// Mutations invalidan lo necesario
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ['inscripciones'] });
  // NO invalidar paquetes — el catálogo no cambió
}
```

### 10.4 Revalidación

- El catálogo se revalida en cada mount del wizard (no store)
- `staleTime: 5 * 60 * 1000` previene re-fetch innecesario
- Si el admin modifica el paquete entre que se cargó el catálogo y el usuario seleccionó, el backend valida en la mutación

---

## 11. QUÉ DEBE ELIMINARSE DEL FRONTEND ACTUAL

### 11.1 Fetch Post-Selección de Paquete

**ELIMINAR de `InscripcionWizard.tsx`:**

```typescript
// ESTO DEBE ELIMINARSE:
const [selectedPaqueteDetail, setSelectedPaqueteDetail] = useState<PaqueteDetailContract | null>(null);
// ...
fetchPaqueteDetail(watchedPaqueteId)
  .then(setSelectedPaqueteDetail)
  .catch((err) => {
    console.error("Failed to fetch package detail:", err);
```

**REEMPLAZAR POR:**
```typescript
// El paquete seleccionado ya está completo en el estado del wizard
// derived del form state: selectedPaquete = paquetes.find(p => p.id === watchedPaqueteId)
// Este objeto ya tiene precios, beneficios, disciplinas, minimo_compra_inicial
```

### 11.2 Función `toCompletaBackendPayload`

**ELIMINAR de `inscripcion.schema.ts`:**

```typescript
// ESTO DEBE ELIMINARSE:
export function toCompletaBackendPayload(
  data: InscripcionFormData,
  evento_id: string,
  cantidad: number,
  delegado_id?: string | null,
): InscripcionCompletaBackendPayload {
  return {
    evento_id,
    paquete_id: data.paquete_id,
    // ... construir payload
  };
}
```

**REEMPLAZAR POR:** Construcción directa del payload desde el estado del formulario en el hook de mutación, sin función intermediaria.

### 11.3 Fetch `fetchPaqueteDetail` del `paquete.service.ts`

**NO ELIMINAR** — puede conservarse para otros usos (ej. debugging, landing page que requiera detalle). Pero **no se usa en el wizard**.

---

## 12. QUÉ IMPLEMENTACIÓN PARCIAL DEBE REEMPLAZARSE

### 12.1 Wizard — Uso del Paquete Completo

**Actualmente (parcial):**
- `InscripcionWizard.tsx` línea 149: `const [selectedPaqueteDetail, setSelectedPaqueteDetail] = useState<PaqueteDetailContract | null>(null);`
- `InscripcionWizard.tsx` línea 226: `const cantidad = selectedPaqueteDetail.minimo_compra_inicial ?? 1;`
- `InscripcionWizard.tsx` líneas 260-265: `fetchPaqueteDetail` después de seleccionar

**Objetivo (reemplazo):**
- Derivar `selectedPaquete` directamente del estado del form: `paquetes.find(p => p.id === watchedPaqueteId)`
- Derivar `cantidad` de `selectedPaquete.cantidad_minima_compra`
- **Sin fetch adicional**

### 12.2 SmartPaqueteCardsField — Badge FIJO/ELEGIBLE

**Estado actual:** ✅ Ya corregido — `isElegible = card.modo_disciplinas === "ELEGIBLE"`

**Verificar que no quede referencia a `card.cantidad_disciplinas > 1`** para inferir elegibilidad.

### 12.3 SmartEquipoField — Props de Paquete

**Cambio requerido:** `SmartEquipoField` recibe `PaquetePresenter` (completo), no solo el `paquete_id`.

```typescript
// ANTES (parcial):
interface SmartEquipoFieldProps {
  paqueteId: string | null;
  // ...
}

// OBJETIVO (reemplazo):
interface SmartEquipoFieldProps {
  paquete: PaquetePresenter | null;  // Objeto completo
  // ...
}
```

---

## 13. LOTES DE IMPLEMENTACIÓN ORDENADOS POR DEPENDENCIA

### Lote 1 — Frontend: Eliminar Fetch Post-Selección ✅ Dependencias: Ninguna

**Archivos:**
- `frontend/src/features/inscripciones/components/InscripcionWizard.tsx` — eliminar `selectedPaqueteDetail` state y `fetchPaqueteDetail`
- `frontend/src/features/inscripciones/hooks/useInscripcionCatalogs.ts` — eliminar `usePaqueteDetail` si no tiene otros consumidores

**Entregable:** Wizard funciona sin fetch post-selección usando `PaquetePresenter` del catálogo.

**Tests:**
- E2E: Selección de paquete → wizard avanza sin network request adicional
- Unit: Verificar que `selectedPaquete` se deriva del form state

### Lote 2 — Frontend: Reemplazar `toCompletaBackendPayload` ✅ Dependencias: Lote 1

**Archivos:**
- `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts` — eliminar `toCompletaBackendPayload`
- `frontend/src/features/inscripciones/hooks/useCreateInscripcionCompleta.ts` — construir payload directo

**Entregable:** Payload se construye directamente en el hook sin función intermediaria.

**Tests:**
- Snapshot test del payload generado
- Integration: Creación exitosa con payload directo

### Lote 3 — Frontend: SmartEquipoField Props ✅ Dependencias: Lote 1

**Archivos:**
- `frontend/src/features/inscripciones/components/smart-fields/SmartEquipoField.tsx` — cambiar `paqueteId: string | null` → `paquete: PaquetePresenter | null`

**Entregable:** SmartEquipoField recibe el PaquetePresenter completo.

**Tests:**
- Unit: SmartEquipoField renderiza correctamente con objeto completo

### Lote 4 — Frontend: Landing Page ✅ Dependencias: Ninguna (puede ir en paralelo)

**Archivos:**
- `frontend/src/components/landing/PaquetesCardsClient.tsx` — adaptar a usar `PaquetePresenter` del catálogo

**Entregable:** Landing page usa el mismo contrato de catálogo.

### Lote 5 — Backend: Endpoint `/catalogo/paquetes/` ✅ Dependencias: Ninguna (ya implementado)

**Estado:** ✅ Ya implementado — `PaqueteListOut` incluye `cantidad_minima_compra`, `tiene_fiesta`, `tiene_box`, `tiene_cerveza`, `disciplinas_resumen`, y `disciplinas` como array.

**Verificación:** Tests de integración para confirmar que el endpoint retorna el contrato completo.

---

## 14. MATRIZ DE ACEPTACIÓN DE TESTS

### 14.1 Tests de Contrato de Paquete

| Test | Tipo | Criterio de aceptación |
|------|------|----------------------|
| `test_paquete_list_retorna_disciplinas_completas` | Integration | `GET /catalogo/paquetes/` retorna disciplinas con `min_jugadores`, `max_jugadores` |
| `test_paquete_list_retorna_beneficios` | Integration | `GET /catalogo/paquetes/` retorna `beneficios` con `tipo`, `alcance`, `modo_calculo` |
| `test_paquete_list_retorna_precios` | Integration | `GET /catalogo/paquetes/` retorna `precios` con `etapa`, `precio_unitario`, `vigente_desde` |
| `test_paquete_list_cantidad_minima_compra` | Integration | `GET /catalogo/paquetes/` retorna `cantidad_minima_compra` como entero >= 1 |
| `test_paquete_list_modo_disciplinas_canonico` | Integration | `modo_disciplinas` es `FIJO` o `ELEGIBLE` — no inferido |

### 14.2 Tests de Wizard Sin Fetch Post-Selección

| Test | Tipo | Criterio de aceptación |
|------|------|----------------------|
| `test_wizard_seleccion_paquete_sin_detalle_fetch` | E2E | Después de seleccionar paquete, NO se hace request a `/catalogo/paquetes/{id}/` |
| `test_wizard_deriva_cantidad_desde_lista` | Unit | `cantidadMinima` se deriva de `selectedPaquete.cantidad_minima_compra`, no de un fetch |
| `test_wizard_deriva_disciplinas_desde_lista` | Unit | `disciplinas` se derivan de `selectedPaquete.disciplinas`, no de un fetch |

### 14.3 Tests de Creación Atómica

| Test | Tipo | Criterio de aceptación |
|------|------|----------------------|
| `test_create_inscripcion_completa_atomica` | Integration | `POST /inscripciones/completa/` crea Inscripcion + Compra + Equipos en misma transacción |
| `test_create_inscripcion_valida_cantidad_minima` | Integration | `cantidad < minimo` retorna `400 CANTIDAD_INSUFICIENTE` |
| `test_create_inscripcion_valida_fecha_limite` | Integration | Fecha límite excedida retorna `400 FECHA_LIMITE_EXCEDIDA` |
| `test_create_inscripcion_snapshot_precio` | Integration | Compra.precio_unitario se congela al momento de creación |
| `test_create_inscripcion_response_tiene_equipos` | Integration | Response incluye `equipos[]` con `id`, `nombre`, `disciplina` |

### 14.4 Tests de FIJO/ELEGIBLE

| Test | Tipo | Criterio de aceptación |
|------|------|----------------------|
| `test_elegible_badge_desde_modo_disciplinas` | E2E | Paquetes ELEGIBLE muestran badge "Elegible" (amber) |
| `test_fijo_badge_desde_modo_disciplinas` | E2E | Paquetes FIJO muestran badge "Fijo" (indigo) |
| `test_fijo_disciplinas_lockeadas` | E2E | Paquetes FIJO tienen slots de disciplina lockeados |
| `test_elegible_disciplinas_editables` | E2E | Paquetes ELEGIBLE permiten cambiar selección de disciplina |
| `test_pack_reencuentro_elegible` | Integration | Reencuentro tiene `modo=ELEGIBLE`, `cantidad_disciplinas=1` |
| `test_pack_pichanga_fijo` | Integration | Pichanga tiene `modo=FIJO`, `cantidad_disciplinas=1` |
| `test_pack_duo_elegible_2` | Integration | Dúo tiene `modo=ELEGIBLE`, `cantidad_disciplinas=2` |
| `test_pack_trio_elegible_3` | Integration | Trío tiene `modo=ELEGIBLE`, `cantidad_disciplinas=3` |

### 14.5 Tests de Consentimientos

| Test | Tipo | Criterio de aceptación |
|------|------|----------------------|
| `test_agregar_persona_graba_aceptaciones` | Integration | `POST /inscripciones/{id}/personas` graba `AceptacionInscripcion` con 3 consentimientos |
| `test_agregar_persona_sin_aceptaciones_falla` | Integration | Sin aceptaciones retorna error de validación |

---

## 15. DECISIONES CLAVE REGISTRADAS

| # | Decisión | Justificación |
|---|---------|---------------|
| D1 | `GET /catalogo/paquetes/` retorna el 100% del `PaquetePresenter` | Elimina round-trip post-selección, simplify frontend state |
| D2 | Eliminar `toCompletaBackendPayload` | El payload se construye directo en el hook — una transformación menos |
| D3 | Backend valida todo en cada mutación | Frontend puedederive rules pero backend es autoritativo |
| D4 | Roster (participaciones) se crea post-inscripción | La inscripción se crea en BORRADOR, roster se llena después via `POST /{id}/personas` |
| D5 | Consentimientos se graban por persona | Cada persona tiene sus 3 aceptaciones en `AceptacionInscripcion` |

---

## 16. ARTIFACTOS LEÍDOS PARA ESTE DOCUMENTO

| Artifact | Relevancia |
|----------|-----------|
| `backend/modules/salesianos_fest/presentation/controllers/catalogo_controller.py` | Rutas de catálogo confirmadas |
| `backend/modules/salesianos_fest/presentation/schemas/catalogo_schemas.py` | `PaqueteListOut`, `PaqueteDetailOut` verificados |
| `backend/modules/salesianos_fest/presentation/presenters/catalogo_presenter.py` | Mapping `present_paquete_list` y `present_paquete_detail` |
| `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py` | `POST /inscripciones/completa/` verificado |
| `backend/modules/salesianos_fest/domain/services/flujos/crear_inscripcion_completa_flujo.py` | Flujo atómico verificado con `transaction.atomic` |
| `backend/modules/salesianos_fest/domain/services/orchestrators/inscripcion_orchestrator.py` | `crear_inscripcion_completa_proceso` verificado |
| `frontend/src/features/inscripciones/schemas/paquete.schema.ts` | Zod schemas verificados con campos correctos |
| `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts` | `toCompletaBackendPayload` y `InscripcionCompletaBackendPayload` verificados |
| `frontend/src/features/inscripciones/hooks/useCreateInscripcionCompleta.ts` | Hook de mutación verificado |
| `frontend/src/features/inscripciones/components/InscripcionWizard.tsx` | Fetch post-selección verificado (líneas 149, 226, 260-265) |
| `frontend/src/features/inscripciones/components/smart-fields/SmartPaqueteCardsField.tsx` | Badge FIJO/ELEGIBLE verificado — ya usa `modo_disciplinas` |
| `contract/next-app-architecture-contract.md` | Patrones frontend |
| `contract/django-app-architecture-contract.md` | Patrones backend |
| `doc_dev/PLAN_CONTRATO_PAQUETE_FRONTEND_BACKEND.md` | Contexto de plan previo |
| `doc_dev/INFORME_INSCRIPCION_EQUIPOS_COMPRA_MINIMA_UX.md` | Gaps detectados |

---

## 17. NOTAS DE ESTADO PARCIAL / INCOMPLETO

| Área | Estado | Nota |
|------|--------|------|
| Landing page (`PaquetesCardsClient`) | ⚠️ Parcial | Usa `cantidad_maxima_participantes` (legacy) en lugar de `cantidad_minima_compra` — verificar y unificar |
| Endpoint `/catalogo/paquetes/{id}/` | ⚠️ No eliminar aún | Consumido por otros contexts (debug, admin); marcar como deprecated, no eliminar hasta que todos los consumers migren |
| Consentimientos post-creación | ✅ Implementado | `POST /inscripciones/{id}/personas` graba aceptaciones |

---

*Documento generado mediante SDD Explore read-only. No modifica código fuente. Todos los hallazgos están respaldados por evidencia de archivos reales verificados con CodeGraph y lectura directa.*
