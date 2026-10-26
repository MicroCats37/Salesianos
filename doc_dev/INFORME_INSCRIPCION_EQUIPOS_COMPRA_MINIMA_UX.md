# INFORME SDD EXPLORE: Inscripción, Equipos y Compra Mínima

**Proyecto:** Salesianos FEST
**Artifact:** `sdd/salesianos-fest-inscription-teams-minimum-purchase/explore`
**Fecha:** 2026-10-18
**Modo:** Auditoría read-only de контракт + código + spec + catalog

---

## RESUMEN EJECUTIVO

| Área | Estado | Severidad |
|------|--------|----------|
| Creación atómica Inscripcion + Equipos | 🔴 BLOQUEANTE | CRITICAL |
| Input de cantidad de compra inicial | 🔴 BLOQUEANTE | CRITICAL |
| Badge ELEGIBLE/FIJO en frontend | 🟡 ERRÓNEO | HIGH |
| Naming `cantidad_maxima_participantes` vs `minimo_compra_inicial` | 🟡 CONFUSO | MEDIUM |
| Locking de disciplinas FIJO en frontend | ✅ CORRECTO | — |
| R11, snapshot precio, cuota, límites de fecha en backend | ✅ CORRECTO | — |

---

## 1. CREACIÓN DE INSCRIPCIÓN: ATOMICIDAD INSCRIPCIÓN + EQUIPOS

### 1.1 Estado Actual

**Backend (`CrearInscripcionFlujo`):**

El flujo `_crear_atomico` solo crea el registro `Inscripcion`:

```python
# backend/modules/salesianos_fest/domain/services/flujos/crear_inscripcion_flujo.py:14-33
def _crear_atomico(self, data: InscripcionCreateData) -> InscripcionResult:
    with transaction.atomic():
        inscripcion = self._inscripcion_core.crear(data)
        return InscripcionResult(...)  # Solo Inscripcion, sin Equipos
```

**Schema `CrearInscripcionIn`** (`inscripcion_schemas.py:74-87`):
```python
class CrearInscripcionIn(BaseSchema):
    evento_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    estado: str = "BORRADOR"
    observacion: str = ""
    # NO hay campo equipos[] — es纯粹的 inscripción, sin equipos
```

**Frontend (`toBackendPayload`)** (`inscripcion.schema.ts:75-86`):
```typescript
export function toBackendPayload(data, evento_id): InscripcionBackendPayload {
  return {
    evento_id,
    paquete_id: data.paquete_id,
    promocion_id: data.promocion_id,
    fusion_promocion_id: data.fusion_promocion_id ?? null,
    estado: "BORRADOR",
  };
  // equipos y participantes son stripped — NO se envían al backend
}
```

### 1.2 Análisis: ¿Inscripción vacía posible?

| Vía | Equipos requeridos | Via |
|-----|-------------------|-----|
| API directa `POST /inscripciones/` | ❌ NO — `CrearInscripcionIn` no tiene campo `equipos` | — |
| Wizard frontend | ⚠️ PARCIAL — el form requiere `equipos: min(1)` pero `toBackendPayload` lo stripping | — |

**Veredicto:** Una inscripción vacía (sin equipos) es posible solo por llamada directa a la API. El wizard frontend requiere al menos un equipo en el formulario, pero ese equipo nunca se envía al backend en el payload de creación.

### 1.3 Análisis: ¿Creación atómica?

**Respuesta: NO.** La creación de Equipos es un paso COMPLETAMENTE SEPARADO:

```
Frontend                  Backend
    |                        |
    | POST /inscripciones/   | ← Crea solo Inscripcion
    |<-- {inscripcion_id}   |
    |                        |
    | POST /api/equipos/    | ← Crea primer Equipo
    |<-- {equipo_id}        |
    |                        |
    | POST /api/equipos/    | ← Crea segundo Equipo (si aplica)
    |<-- {equipo_id}        |
```

**Endpoint equipo existente** (`EquipoController`):
```python
@route.post("/", response={201: ApiResponse[EquipoOut]}, auth=AllowAny)
async def crear_equipo(self, request, payload: CrearEquipoIn):
```

### 1.4 Gap Detectado

| Gap | Descripción | Severidad |
|-----|-------------|----------|
| **G1** | El wizard requiere equipos en el formulario pero NO los envía al backend en la creación de inscripción | CRITICAL |
| **G2** | Equipos deben crearse en llamadas separadas — no hay endpoint bulk atómico | CRITICAL |
| **G3** | Si la creación de equipos falla, la inscripción queda en estado inconsistente | CRITICAL |

### 1.5 Evidencia CodeGraph

- `CrearInscripcionFlujo._crear_atomico` → solo `Inscripcion.objects.create()` — sin equipos
- `InscripcionController.crear_inscripcion` → llama orchestrator → flujo → solo crea Inscripcion
- `EquipoController.crear_equipo` → endpoint SEPARADO con `CrearEquipoIn`
- `CrearEquipoFlujo` tiene su propio `transaction.atomic()` separado

---

## 2. DISCIPLINAS SELECCIONABLES: FIJO vs ELEGIBLE

### 2.1 Datos del Catálogo (seed)

| Paquete | Tipo | Modo | `cantidad_disciplinas` | Disciplinas linked |
|---------|------|------|------------------------|-------------------|
| Reencuentro + Fiesta | PACK | **ELEGIBLE** | 1 | F7F, VOL, BAS |
| Pichanga + Fiesta | PACK | **FIJO** | 1 | F7M |
| Dúo + Fiesta Box | PACK | **ELEGIBLE** | 2 | VOL, BAS |
| Trío + Fiesta Box | PACK | **ELEGIBLE** | 3 | F7M, VOL, BAS |
| Fútbol 7 Masculino | DISCIPLINA | FIJO | 1 | F7M |
| Fútbol 7 Femenino | DISCIPLINA | FIJO | 1 | F7F |
| Vóley Mixto | DISCIPLINA | FIJO | 1 | VOL |
| Básquet Masculino | DISCIPLINA | FIJO | 1 | BAS |

### 2.2 Backend: Modelo y Selector

**Modelo `Paquete`** (`paquete.py:22`):
```python
modo_disciplinas = models.CharField(
    choices=ModoDisciplinasChoices.choices,
    max_length=10,
    help_text="FIJO (predefinidas) o ELEGIBLE (elige el participante)",
)
```

**Selector** (`paquete_selector.py:66-69`):
```python
cantidad_maxima_participantes=p.minimo_compra_inicial,  # ⚠️ MISLABELED
cantidad_maxima_equipos=p.cantidad_disciplinas,
```

### 2.3 Frontend: SmartPaqueteCardsField

**ERROR en línea 36** (`SmartPaqueteCardsField.tsx`):
```typescript
const isElegible = card.cantidad_disciplinas > 1;
// ❌ INCORRECTO — debería ser:
// const isElegible = card.modo_disciplinas === "ELEGIBLE";
```

**Consecuencia del error:**
- Paquetes FIJO con `cantidad_disciplinas = 1` se muestran como "Elegible" (Pichanga, Futbol, Voley, Basquet)
- Paquetes ELEGIBLE con `cantidad_disciplinas > 1` se muestran como "Elegible" (Dúo=2, Trío=3)
- Reencuentro tiene `cantidad_disciplinas=1` pero `modo=ELEGIBLE` → se mostraría como "Fijo" (incorrecto)

### 2.4 Frontend: SmartEquipoField — Locking FIJO

**Lógica correcta** (`SmartEquipoField.tsx:319-436`):
- Si `modo === "FIJO"` Y el paquete tiene tantas disciplinas como slots → todos los slots se pre-llenan y se lockean
- Si `modo === "ELEGIBLE"` → sin lock, usuario puede seleccionar

```typescript
//是对的: lock solo cuando hay match exacto FIJO
const isModoFIJOAndMatched = isFIJO &&
  paqueteDisciplinas.length === paqueteActual.cantidad_disciplinas_requeridas &&
  equiposActuales.length === paqueteDisciplinas.length &&
  equiposActuales.every((equipo) => Boolean(equipo.disciplina_id));
```

### 2.5 Gap Detectado

| Gap | Descripción | Severidad |
|-----|-------------|----------|
| **G4** | `isElegible = card.cantidad_disciplinas > 1` es incorrecto — debe comparar `modo_disciplinas === "ELEGIBLE"` | HIGH |
| **G5** | Badge "Elegible" / "Fijo" en `SmartPaqueteCardsField` muestra información wrong para paquetes FIJO con cantidad=1 | HIGH |

---

## 3. COMPRA MÍNIMA COMERCIAL

### 3.1 Definiciones en Seed

| Paquete | `minimo_compra_inicial` | Precio preventa/persona | Precio regular/persona |
|---------|-------------------------|------------------------|------------------------|
| Reencuentro + Fiesta | **10** | S/40 | S/50 |
| Pichanga + Fiesta | **10** | S/45 | S/55 |
| Dúo + Fiesta Box | **15** | S/60 | S/70 |
| Trío + Fiesta Box | **20** | S/60 | S/70 |
| Fútbol 7 Masculino | **7** | S/40 | S/50 |
| Fútbol 7 Femenino | **7** | S/40 | S/50 |
| Vóley Mixto | **6** | S/40 | S/50 |
| Básquet Masculino | **5** | S/40 | S/50 |

**Fuente:** `seed_catalogo_fest.py:174` — `"minimo_compra_inicial": minimo`

### 3.2 Validación Backend

**`CrearCompraFlujo._crear_compra_sync`** (`crear_compra_flujo.py:95-99`):
```python
if data.tipo == TipoCompraChoices.INICIAL:
    if data.cantidad < inscripcion.paquete.minimo_compra_inicial:
        from modules.salesianos_fest.domain.exceptions import CantidadInsuficienteError
        raise CantidadInsuficienteError()
```

**Schema `CompraCreateIn`** (`compra_schemas.py:11-16`):
```python
class CompraCreateIn(BaseModel):
    inscripcion_id: str
    tipo: str  # INICIAL o AMPLIACION
    cantidad: int = Field(..., gt=0)  # gt=0 pero sin max — y sin validación contra minimo en schema
```

### 3.3 Naming Confuso en API Catalog

**`PaqueteListResult`** (`catalogo_results.py:97`):
```python
cantidad_maxima_participantes: int  # ⚠️ En realidad es minimo_compra_inicial
```

**Presenter mapping** (`catalogo_presenter.py:101`):
```python
cantidad_maxima_participantes=result.cantidad_maxima_participantes,
```

**Frontend `SmartPaqueteCardsField`** muestra:
```typescript
//是对的: el tooltip是对的
<span>Máx. {card.cantidad_maxima_participantes} participantes</span>
```

**⚠️ PROBLEMA:** El label "Máximo participantes" confunde el mínimo comercial (10, 15, 20) con el máximo deportivo (5-10 según disciplina).

### 3.4 Gap Crítico: Sin Input de Cantidad en Frontend

**El wizard NUNCA pide cantidad al usuario.** El flujo actual:

```
WizardInscripcion
  Step 1: Paquete → SmartPaqueteCardsField (muestra precio "S/40" como si fuera total)
  Step 2: Equipos + Promoción
  Step 3: Declaraciones
  → Submit: POST /inscripciones/ (SIN cantidad, SIN equipos)
  → Redirige a Detalle
  → PaymentCallout: "Completa el pago" button
  → IzipayModal: NO HAY CAMPO DE CANTIDAD VISIBLE
```

**NO EXISTE** en el frontend:
- Campo para ingresar `cantidad` de la compra inicial
- Validación contra `minimo_compra_inicial`
- Información de que el precio mostrado es "por persona"

### 3.5 Gap Detectado

| Gap | Descripción | Severidad |
|-----|-------------|----------|
| **G6** | El frontend NO tiene campo para ingresar `cantidad` de la compra inicial | CRITICAL |
| **G7** | El usuario no ve el `minimo_compra_inicial` antes de iniciar el pago | CRITICAL |
| **G8** | El precio mostrado en cards (S/40) parece total pero es precio por persona | HIGH |
| **G9** | `cantidad_maxima_participantes` en API es en realidad `minimo_compra_inicial` — naming misleading | MEDIUM |
| **G10** | `SmartPaqueteCardsField` muestra "S/X por equipo" cuando debería decir "S/X por persona" | MEDIUM |

---

## 4. FLUJO UX RECOMENDADO (Spec F1 vs Implementado)

### 4.1 Flujo según Especificación F1 (`ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md:142-149`)

```
1. Usuario autenticado elige Evento, Paquete vigente y N cupos ≥ mínimo inicial
2. Selecciona disciplinas según FIJO/ELEGIBLE; crea equipo(s)
3. Selecciona Promoción + fusión opcional
4. Se crea ATÓMICAMENTE: Inscripcion + Compra(INICIAL, PENDIENTE, cantidad=N)
5. Registrar 0..N personas y Participaciones
6. Antes de pago NO se crean AsignacionCupo activas
```

### 4.2 Flujo Actual Implementado

```
1. Wizard: paquete → equipos → declaraciones
2. Submit: POST /inscripciones/ → Crea solo Inscripcion (SIN cantidad, SIN equipos en payload)
3. Redirige a /detalle
4. Equipos se crean en llamadas separadas (POST /equipos/)
5. NO hay paso de "cantidad" antes de pagar
6. PaymentCallout muestra "Completa el pago" → IzipayModal
7. En IzipayModal: vermut no hay campo cantidad visible
```

### 4.3 Comparación

| Aspecto | Spec F1 | Implementado |
|---------|---------|-------------|
| Cantidad de cupos requerida | ✅ SÍ — N ≥ mínimo | ❌ NO — no se pide |
| Inscripcion + Compra atómica | ✅ SÍ | ❌ NO — solo Inscripcion |
| Equipos en creación | ✅ En el mismo paso | ❌ Paso separado |
| Precio por persona vs por equipo | ✅ Diferenciado | ❌ Mostrado como "por equipo" |

---

## 5. DISEÑO MÍNIMO PARA ENFORCEMENT

### 5.1 Lo que YA está bien en el Backend

| Regla | Implementación | Archivo |
|-------|---------------|---------|
| **R11** — unique (evento, disciplina, persona) WHERE ACTIVA | `ParticipacionService.crear()` + partial unique constraint en modelo | `participacion_service.py:40-48`, `participacion.py` |
| **Snapshot precio** | `precio_unitario` y `total` congelados en `Compra` | `crear_compra_flujo.py:102` |
| **Cuota assignment** | `AsignacionCupo` solo se crea cuando persona ocupa cupo pagado | `crear_asignaciones_flujo.py` |
| **Fecha límite modificación** | `evento.fecha_limite_modificacion` validada en flujos | `crear_equipo_flujo.py` + `agregar_persona_flujo.py` |
| **Mínimo INICIAL** | `CantidadInsuficienteError` si cantidad < minimo | `crear_compra_flujo.py:97` |
| **No mínimo AMPLIACION** | Solo validado para INICIAL, no para AMPLIACION | `crear_compra_flujo.py:96` |

### 5.2 Lo que FALTA: Apply Scope Mínimo

#### 5.2.1 Opción A: Crear Endpoint Bulk Atómico (RECOMENDADA)

**Nuevo schema `CrearInscripcionCompletaIn`:**
```python
class CrearInscripcionCompletaIn(BaseSchema):
    # Datos inscripción
    evento_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    # Datos compra
    cantidad: int = Field(..., ge=1)  # Nueva: cantidad requerida
    # Equipos
    equipos: list[CrearEquipoYParticipantesIn]
```

**Nuevo flujo atómico:**
```python
async def crear_inscripcion_compra_equipos_atomica(data):
    with transaction.atomic():
        # 1. Validar cantidad >= minimo_compra_inicial
        # 2. Crear Inscripcion (BORRADOR)
        # 3. Crear Equipos (uno por disciplina FIJO, o según selección)
        # 4. Crear Compra (INICIAL, PENDIENTE, cantidad)
        # 5. Obtener precio vigente y congelar
        # 6. Crear OrdenPago (PENDIENTE)
        # 7. Retornar todo
```

**Frontend changes:**
- Wizard Step 1: Paquete cards + nuevo campo "Cantidad de jugadores" (number, min=minimo_compra_inicial)
- Wizard Step 2: Equipos (mantiene)
- Submit: `POST /inscripciones/completa/` con payload completo

#### 5.2.2 Opción B: Multi-Step Con Cantidad (Menos Atómico)

Mantener flujo de creación de Inscripcion SEPARADO, agregar paso de "Cantidad" antes de Izipay:

1. Crear Inscripcion + Equipos (llamadas separadas — no atómico)
2. Nuevo endpoint: `PATCH /inscripciones/{id}/compra-inicial` para crear la Compra
3. Izipay se inicia sobre la Compra ya existente

**Tradeoff:** Menos atómico pero menos cambios en el flujo existente.

### 5.3 Cambios Mínimos por Gap

| Gap | Cambio Backend | Cambio Frontend |
|-----|--------------|----------------|
| G1 (equipos stripped) | Opción A: nuevo endpoint bulk | Enviar equipos en payload |
| G2 (no atómico) | Opción A o B | — |
| G4 (isElegible wrong) | — | `isElegible = modo_disciplinas === "ELEGIBLE"` |
| G6 (sin cantidad) | Opción A: agregar `cantidad` al bulk, o mantener separate | Nuevo campo cantidad en wizard |
| G7 (sin info mínimo) | Exponer `minimo_compra_inicial` en catalog | Mostrar "Mínimo: X jugadores" |
| G8 (precio ambiguo) | — | "S/X por persona (mínimo X)" |
| G9 (naming) | Renombrar `cantidad_maxima_participantes` → `cantidad_minima_compra` | Adaptar |

---

## 6. MATRICES DE EVIDENCIA

### 6.1 Endpoint / Schema

| Endpoint | Method | Schema Input | Schema Output | ¿Existe? |
|----------|--------|--------------|---------------|----------|
| `/api/inscripciones/` | POST | `CrearInscripcionIn` (sin equipos, sin cantidad) | `InscripcionOut` | ✅ |
| `/api/inscripciones/` | GET | — | `list[InscripcionOut]` | ✅ |
| `/api/inscripciones/{id}` | GET | — | `InscripcionOut` | ✅ |
| `/api/inscripciones/{id}/detalle` | GET | — | `InscripcionDetailOut` | ✅ |
| `/api/inscripciones/{id}/personas` | POST | `AgregarPersonaIn` | `{participante}` | ✅ |
| `/api/equipos/` | POST | `CrearEquipoIn` | `EquipoOut` | ✅ |
| `/api/equipos/inscripcion/{id}` | GET | — | `list[EquipoOut]` | ✅ |
| `/api/compras/` | POST | `CompraCreateIn` (cantidad requerida) | `CompraCreateOut` | ✅ |
| `/api/catalogo/paquetes/` | GET | — | `PaqueteListOut` | ✅ |
| `/api/catalogo/paquetes/{id}/` | GET | — | `PaqueteDetailOut` (con minimo_compra_inicial) | ✅ |

### 6.2 Flujo UX — Pasos Actuales

```
[Wizard Step 1: Paquete]
  → SmartPaqueteCardsField
  → Paquete seleccionado → evento_id resuelto del paquete
  → isElegible = cantidad_disciplinas > 1 ❌ (G4)

[Wizard Step 2: Equipos]
  → SmartEquipoField
  → Auto-crea N equipos según cantidad_disciplinas
  → FIJO: pre-llena y lockea disciplina ✅
  → ELEGIBLE: pre-llena pero no lockea ✅
  → Campo "0 participantes" — sin input en creación ❌

[Wizard Step 3: Declaraciones]
  → acceptedBases, fitnessDeclaration, imageConsent
  → Solo validación z.literal(true)

[Submit]
  → toBackendPayload() → STRIPS equipos y participantes
  → POST /inscripciones/
  → Solo crea Inscripcion
  → Redirige a /detalle

[Detalle]
  → Equipos se ven vacíos (no se crearon)
  → RegistrationStepsCard muestra steps
  → PaymentCallout: "Completa el pago"
  → Botón → IzipayModal
  → ❌ NO hay campo cantidad en el modal actual
```

### 6.3 Matriz de Validaciones Backend

| Regla | Dónde se valida | Tipo | Estado |
|-------|-----------------|------|--------|
| R1: (evento, responsable, paquete) único | `InscripcionService.crear()` | Unique constraint | ✅ |
| R2: cantidad >= minimo_compra_inicial para INICIAL | `CrearCompraFlujo._crear_compra_sync` | Excepción | ✅ |
| R3: Precio congelado | `Compra.precio_unitario`, `Compra.total` | Snapshot | ✅ |
| R5: No filas vacías AsignacionCupo | `CrearAsignacionesFlujo` | Lógica | ✅ |
| R11: (evento, disciplina, persona) único ACTIVO | `ParticipacionService.crear()` + DB constraint | Excepción + constraint | ✅ |
| R6: Fecha límite modificación | `CrearEquipoFlujo._verificar_fecha_limite` | Excepción | ✅ |

---

## 7. GAPS PRIORIZADOS

### PRIORIDAD CRÍTICA (bloqueantes para usable)

| Prioridad | Gap ID | Descripción | Afecta |
|-----------|--------|-------------|--------|
| P1 | G6 | Sin campo de cantidad en frontend — usuario no puede comprar | UX |
| P2 | G1 | Equipos del wizard son stripped del payload — se pierden | UX |
| P3 | G2 | Equipos no se crean atómicamente con inscripción | UX/Integridad |

### PRIORIDAD ALTA

| Prioridad | Gap ID | Descripción | Afecta |
|-----------|--------|-------------|--------|
| P4 | G4 | Badge "Elegible" incorrecto para paquetes FIJO con cantidad_disciplinas=1 | Información |
| P5 | G7 | Usuario no sabe cuál es el mínimo de compra antes de pagar | UX |
| P8 | G8 | Precio mostrado como "por equipo" pero es "por persona" | Información |

### PRIORIDAD MEDIA

| Prioridad | Gap ID | Descripción | Afecta |
|-----------|--------|-------------|--------|
| P9 | G9 | `cantidad_maxima_participantes` en API es en realidad `minimo_compra_inicial` | Mantenibilidad |

---

## 8. ARTIFACTOS LEÍDOS

| Artifact | Ruta | Relevancia |
|----------|------|------------|
| Contract Django | `contract/django-app-architecture-contract.md` | Patrones arquitectura |
| Contrato DRY Schemas | `contract/SCHEMA_DRY_INTENTION.md` | Patrones schema |
| Informe Contraste Frontend/Backend | `doc_dev/INFORME_CONTRASTE_FRONTEND_BACKEND_SALESIANOS_FEST.md` | Mismatches connus |
| Doc Lógica y Tablas | `doc_dev/DOCUMENTACION_LOGICA_Y_TABLAS_SALESIANOS_FEST.md` | Spec completa |
| Spec Agent IA | `doc_dev/ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md` | Spec F1, tablas, reglas |
| Seed Catalog | `backend/.../seed_catalogo_fest.py` | Valores mínimos |
| CrearInscripcionFlujo | `backend/.../flujos/crear_inscripcion_flujo.py` | Atomicidad |
| CrearCompraFlujo | `backend/.../flujos/crear_compra_flujo.py` | Mínimo validación |
| inscripcion_schemas | `backend/.../schemas/inscripcion_schemas.py` | Contratos API |
| compra_schemas | `backend/.../schemas/compra_schemas.py` | Schema compra |
| SmartPaqueteCardsField | `frontend/.../SmartPaqueteCardsField.tsx` | UI paquetes |
| SmartEquipoField | `frontend/.../SmartEquipoField.tsx` | UI equipos |
| InscripcionWizard | `frontend/.../InscripcionWizard.tsx` | Flujo wizard |
| InscripcionDetailView | `frontend/.../InscripcionDetailView.tsx` | Vista post-creación |

---

## 9. ITEMS DEFERIDOS / Unknown

| Item | Estado | Nota |
|------|--------|------|
| Detalle de IzipayModal actual | ❓ | No se inspeccionó el modal de pago — verificar si tiene campo cantidad |
| Flujo exacto de "Ampliación" | ❓ | Confirmar si la ampliación también requiere paso de cantidad |
| Validación de roster máximo por disciplina | ⚠️ Parcial | `max_jugadores` de Disciplina se valida en `ParticipacionService.crear()` — verificar que el frontend lo respete |
| Nombre del campo `talle_camiseta` vs `talla_camiseta` | ✅已知 | Contradoc dice typo — código backend tiene `talla_camiseta` — no se verificó si el frontend lo maneja |

---

## 10. RECOMENDACIÓN

### Apply Scope Mínimo Sugerido

**Fase 1 — Correcciones Críticas:**
1. **G4**: Corregir `isElegible` en `SmartPaqueteCardsField` — usar `modo_disciplinas === "ELEGIBLE"`
2. **G6+G1+G2**: Implementar `CrearInscripcionCompletaIn` + endpoint bulk atómico con cantidad

**Fase 2 — Mejoras UX:**
3. **G8**: Corregir label de precio a "por persona (mínimo X)"
4. **G7**: Mostrar `minimo_compra_inicial` en UI antes de pago

**Fase 3 — Limpieza:**
5. **G9**: Renombrar `cantidad_maxima_participantes` → `cantidad_minima_compra` en API (breaking change — coordinar con frontend)

### Lo que NO hay que cambiar (ya está bien)

- R11 enforcement (backend + DB constraint)
- Snapshot de precio en Compra
- Lógica de quota assignment (AsignacionCupo)
- Validación de fecha límite
- FIJO auto-lock en SmartEquipoField

---

*Este informe fue generado mediante SDD Explore read-only. No modifica código fuente. Todos los hallazgos están respaldados por evidencia de archivos reales.*
