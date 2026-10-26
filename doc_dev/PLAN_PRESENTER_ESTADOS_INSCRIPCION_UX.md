# Plan: Presenter de Estados e UX para Detalle de Inscripcion

> **Proyecto:** Salesianos FEST
> **Fecha:** 2026-10-19 (revisado con jerarquia finalizada)
> **Artifact:** `sdd/inscripcion-detail-status-presenter-ux/explore`
> **Modo:** Read-only exploration — no modificacion de codigo
> **Idioma:** Espanol neutral tecnico

---

## Resumen Ejecutivo

Este documento presenta el plan de diseno e implementacion para un **presenter de detalle de inscripcion** que muestra de manera clara y no ambigua:

1. El estado deportivo/administrativo de la `Inscripcion` (`Inscripcion.estado`)
2. La situacion comercial/pago sin tratar incorrectamente la `Inscripcion` como pagada
3. El estado del roster de cada equipo: `estado_roster` (`INCOMPLETO`/`COMPLETO`), `jugadores_registrados`, `minimo_deportivo`, `faltantes`
4. El resumen de equipos: `resumen_equipos: { total, completos, incompletos }`
5. La capacidad contratada, registrada y pagada, y su relacion con la compra inicial y las ampliaciones

**Regla cardinal:** `Inscripcion.estado` es exclusivamente deportivo/administrativo. El pago pertenece a `Compra`/`OrdenPago`. No se inventara un estado `Inscripcion.PAGADA`.

---

## 1. Jerarquia Finalizada por el Usuario

La siguiente jerarquia es la **unica version valida** tras confirmacion explicita:

### 1.1 En `Inscripcion` (nivel raiz del response)

```json
{
  "resumen_equipos": {
    "total": 2,
    "completos": 1,
    "incompletos": 1
  }
}
```

- **`total`:** numero total de equipos de la inscripcion
- **`completos`:** equipos con `estado_roster = COMPLETO`
- **`incompletos`:** equipos con `estado_roster = INCOMPLETO`

### 1.2 En cada elemento de `equipos[]`

```json
{
  "id": "uuid-equipo",
  "nombre": "Los Tigres FC",
  "estado_equipo": "EQUIPO_ACTIVO",
  "estado_roster": "INCOMPLETO",
  "jugadores_registrados": 5,
  "minimo_deportivo": 7,
  "faltantes": 2,
  "disciplina": { ... },
  "participantes": [ ... ]
}
```

| Campo | Tipo | Descripcion |
|-------|------|------------|
| `estado_equipo` | `string` | Estado del ciclo de vida persistido: `EQUIPO_ACTIVO` o `EQUIPO_CANCELADO` |
| `estado_roster` | `INCOMPLETO \| COMPLETO` | Estado derivado de lectura, **nunca persistido**, calculado desde `jugadores_registrados` vs `minimo_deportivo` |
| `jugadores_registrados` | `int` | Conteo de `Participacion` activas en este equipo |
| `minimo_deportivo` | `int` | `Disciplina.min_jugadores` — minimo deportivo requerido |
| `faltantes` | `int` | `max(0, minimo_deportivo - jugadores_registrados)` |

### 1.3 Regla de Calculo de `estado_roster`

```
estado_roster = COMPLETO   si jugadores_registrados >= minimo_deportivo
estado_roster = INCOMPLETO si jugadores_registrados < minimo_deportivo
```

**Nota:** `estado_roster` espuramente de presentacion/progreso UI. **No bloquea** la compra comercial, el pago ni la creacion de la inscripcion por si solo.

### 1.4 Seccion `resumen_pago` Separada

Se mantiene la seccion `resumen_pago` como bloque independiente de la seccion `resumen_equipos`. Cada una es ortogonal:

- `resumen_equipos` — estado deportivo del roster
- `resumen_pago` — estado comercial/pago

---

## 2. Campos JSON Completos para `InscripcionDetailOut`

### 2.1 Estructura General

```json
{
  "id": "uuid-inscripcion",
  "evento_id": "uuid-evento",
  "evento_nombre": "Festival Deportivo Salesianos 2026",
  "responsable_id": "uuid-persona",
  "responsable_nombre": "Juan Perez",
  "paquete_id": "uuid-paquete",
  "paquete_nombre": "Reencuentro + Fiesta",
  "promocion_id": "uuid-promocion",
  "promocion_nombre": "Promocion 2005",
  "fusion_promocion_id": null,
  "delegado_id": "uuid-delegado",
  "delegado_nombre": "Carlos Gomez",
  "estado": "VALIDADA",
  "observacion": "",
  "created_at": "2026-10-15T10:00:00Z",

  "resumen_equipos": {
    "total": 2,
    "completos": 1,
    "incompletos": 1
  },

  "equipos": [
    {
      "id": "uuid-equipo-1",
      "nombre": "Los Tigres FC",
      "estado_equipo": "EQUIPO_ACTIVO",
      "estado_roster": "INCOMPLETO",
      "jugadores_registrados": 5,
      "minimo_deportivo": 7,
      "faltantes": 2,
      "disciplina": {
        "id": "uuid-disciplina",
        "nombre": "Futbol 7 Masculino",
        "sigla": "F7M"
      },
      "categoria": {
        "id": "uuid-categoria",
        "nombre": "Senior"
      },
      "participantes": [/* ParticipacionOut[] */]
    }
  ],

  "personas": [/* InscripcionPersonaSummarySchema[] */],

  "resumen_pago": {
    "tiene_compras": true,
    "compras": [
      {
        "id": "uuid-compra",
        "tipo": "INICIAL",
        "cantidad": 10,
        "precio_unitario": 40.00,
        "total": 400.00,
        "estado": "PAGADA",
        "orden_pago": {
          "id": "uuid-orden",
          "numero": "OP-2026-001",
          "estado": "PAGADA",
          "pagada_en": "2026-10-16T14:30:00Z"
        }
      }
    ],
    "compras_count": 1,
    "contratados_total": 10,
    "pagados_total": 10,
    "registrados_total": 12,
    "capacidad_disponible": 0,
    "estado_pago_global": "PAGADA",
    "mensaje_estado": "Pago confirmado"
  },

  "paquete": {
    "id": "uuid-paquete",
    "nombre": "Reencuentro + Fiesta",
    "tipo": "PACK",
    "modo_disciplinas": "ELEGIBLE",
    "cantidad_minima_compra": 10,
    "cantidad_disciplinas": 1,
    "cantidad_maxima_equipos": 3,
    "tiene_fiesta": true,
    "tiene_box": false,
    "tiene_cerveza": false
  }
}
```

### 2.2 Definicion de `resumen_equipos`

| Campo | Tipo | Descripcion |
|-------|------|------------|
| `total` | `int` | Numero total de equipos |
| `completos` | `int` | Equipos con `estado_roster = COMPLETO` |
| `incompletos` | `int` | Equipos con `estado_roster = INCOMPLETO` |

### 2.3 Definicion de `resumen_pago`

| Campo | Tipo | Descripcion |
|-------|------|------------|
| `tiene_compras` | `bool` | Indica si hay compras asociadas |
| `compras` | `CompraResumen[]` | Lista de compras (inicial + ampliaciones) |
| `compras_count` | `int` | Numero total de compras |
| `contratados_total` | `int` | `SUM(compra.cantidad)` donde `compra.estado IN (PENDIENTE, PAGADA)` |
| `pagados_total` | `int` | `SUM(compra.cantidad)` donde `compra.estado = PAGADA` |
| `registrados_total` | `int` | `COUNT(InscripcionPersona)` activas (participantes unicos) |
| `capacidad_disponible` | `int` | `pagados_total - registrados_total` (slots pagados sin asignar) |
| `estado_pago_global` | `string` | Derivado: `PAGADA` si todas pagadas, `PENDIENTE` si todas pendientes, `PARCIAL` si mixto |
| `mensaje_estado` | `string` | Mensaje legible para UI |

### 2.4 Definicion de `CompraResumen`

| Campo | Tipo | Descripcion |
|-------|------|------------|
| `id` | `string` (UUID) | Identificador de la compra |
| `tipo` | `string` | `INICIAL` o `AMPLIACION` |
| `cantidad` | `int` | Cantidad de cupos contratados |
| `precio_unitario` | `float` | Precio congelado al momento de creacion |
| `total` | `float` | `cantidad * precio_unitario` |
| `estado` | `string` | `PENDIENTE`, `PAGADA`, `CANCELADA` |
| `orden_pago` | `OrdenPagoResumen \| null` | Resumen de la orden de pago asociada |

### 2.5 Definicion de `OrdenPagoResumen`

| Campo | Tipo | Descripcion |
|-------|------|------------|
| `id` | `string` (UUID) | Identificador de la orden |
| `numero` | `string` | Numero legible de orden |
| `estado` | `string` | `PENDIENTE`, `PAGADA`, `CANCELADA` |
| `pagada_en` | `string?` | ISO timestamp si esta pagada, null si no |

---

## 3. Reglas de Dominio No Negociables

| # | Regla | Fuente |
|---|-------|--------|
| R1 | `Inscripcion.estado` es exclusivamente deportivo/administrativo | `EstadoInscripcionChoices` en `constants.py` |
| R2 | No existe ni existira `Inscripcion.PAGADA` | El estado `PAGADA` pertenece a `Compra.estado` |
| R3 | El pago pertenece a `Compra`/`OrdenPago` | `modules/commerce` y `modules/pagos` |
| R4 | `Paquete.minimo_compra_inicial` es minimo comercial, **independiente** de `Disciplina.min_jugadores` | `Paquete.minimo_compra_inicial` vs `Disciplina.min_jugadores` |
| R5 | `estado_roster` es derivado, **nunca persistido**, y **no bloquea** ninguna operacion comercial | Calculo en presenter |
| R6 | `estado_equipo` es el unico estado persistido del equipo: `EQUIPO_ACTIVO` o `EQUIPO_CANCELADO` | `EstadoEquipoChoices` en `constants.py` |
| R7 | Antes del pago: `registrados <= contratados` | Invariante del dominio |
| R8 | Solo despues del pago confirmado se crean `AsignacionCupo` activas | Flujo F2 en especificacion |

---

## 4. Responsabilidades de Selector y Presenter

### 4.1 Selector (`InscripcionSelector`)

El selector es responsable de:

1. Cargar la `Inscripcion` con todas sus relaciones
2. Cargar los `Equipo` con sus `Participacion` y relaciones anidadas (`Disciplina`, `Categoria`)
3. Cargar las `Compra` asociadas a la inscripcion (desde `commerce.Compra`)
4. **NO realiza calculos derivados** — solo carga datos

```
Selector.load_inscripcion_detalle(id)
  → Inscripcion + related
  → Equipos + Participaciones + Disciplina + Categoria
  → Compras (via commerce service)
```

### 4.2 Presenter (`InscripcionPresenter`)

El presenter es responsable de **solo transformacion**, sin acceso a DB:

1. Recibe `InscripcionDetailResult` con todos los datos cargados
2. Calcula `estado_roster`, `jugadores_registrados`, `minimo_deportivo`, `faltantes` por equipo
3. Calcula `resumen_equipos: { total, completos, incompletos }`
4. Calcula `resumen_pago` con sus campos derivados
5. Transforma a `InscripcionDetailOut`

```
Presenter.present_inscripcion_detail(result)
  → Calcula estado_roster por equipo
  → Calcula resumen_equipos
  → Calcula resumen_pago
  → Mapea a InscripcionDetailOut
```

### 4.3 Calculos del Presenter

```python
# Por cada equipo
equipo.jugadores_registrados = count(p for p in equipo.participaciones if p.estado == "ACTIVA")
equipo.minimo_deportivo = equipo.disciplina.min_jugadores
equipo.faltantes = max(0, equipo.minimo_deportivo - equipo.jugadores_registrados)
equipo.estado_roster = "COMPLETO" if equipo.jugadores_registrados >= equipo.minimo_deportivo else "INCOMPLETO"

# Resumen de equipos
resumen_equipos.total = count(equipos)
resumen_equipos.completos = count(e for e in equipos if e.estado_roster == "COMPLETO")
resumen_equipos.incompletos = count(e for e in equipos if e.estado_roster == "INCOMPLETO")
```

### 4.4 Nota sobre `estado_roster` como Display-Only

`estado_roster` es un indicador de progreso UI. **No se usa para:**

- Bloquear la creacion de compra
- Bloquear el inicio de pago
- Bloquear la transicion de estado de `Inscripcion`
- Ninguna validacion de negocio

Es equivalente a una "_computed property_" en el schema de response.

---

## 5. Estrategia de Compatibilidad con API Existente

### 5.1 No Breaking Changes

Todos los cambios son **aditivos**:

| Campo/Seccion | Cambio | Compatibilidad |
|---------------|--------|----------------|
| `equipos[].estado_equipo` | Agregado (era `estado`) | Renombrado desde `estado` — mantener ambos temporalmente |
| `equipos[].estado_roster` | Nuevo | Aditivo |
| `equipos[].jugadores_registrados` | Nuevo | Aditivo |
| `equipos[].minimo_deportivo` | Nuevo | Aditivo |
| `equipos[].faltantes` | Nuevo | Aditivo |
| `resumen_equipos` | Nuevo | Aditivo |
| `resumen_pago` | Nuevo | Aditivo |
| `paquete` | Nuevo | Aditivo |

### 5.2 Transicion de `estado` a `estado_equipo`

El campo `estado` actual del `Equipo` (`EQUIPO_ACTIVO`/`EQUIPO_CANCELADO`) se mantiene como `estado_equipo`. El presenter puede populary ambos durante la transicion para no romper clientes existentes.

---

## 6. Frontend: Flujo de Datos

### 6.1 TanStack Query

```typescript
// useInscripcionDetalle devuelve InscripcionDetailOut con todos los campos nuevos
const { data } = useInscripcionDetalle(inscripcionId);

// data.resumen_equipos.total
// data.resumen_equipos.completos
// data.resumen_equipos.incompletos

// data.equipos[0].estado_roster === "INCOMPLETO"
// data.equipos[0].jugadores_registrados
// data.equipos[0].minimo_deportivo
// data.equipos[0].faltantes

// data.resumen_pago.estado_pago_global === "PAGADA"
// data.resumen_pago.capacidad_disponible
```

### 6.2 Component Data Flow

```
InscripcionDetailView
  └── data: InscripcionDetailOut
        ├── .resumen_equipos → ResumenEquiposBadge (total/completos/incompletos)
        ├── .resumen_pago → ResumenPagoCard (estado_pago_global, mensaje_estado, compras, capacidad)
        ├── .equipos[] → SortableEquipoCard
        │     └── estado_roster → Badge (INCOMPLETO=amber, COMPLETO=green)
        │     └── jugadores_registrados + minimo_deportivo → ProgressBar
        │     └── faltantes → Label
        └── RegistrationStepsCard (usa estado + resumen_pago para pasos)
```

---

## 7. Estados de UI

### 7.1 SortableEquipoCard

| `estado_roster` | Badge | Color | Significado |
|-----------------|-------|-------|-------------|
| `INCOMPLETO` | "Incompleto" | Amber | Faltan jugadores para el minimo deportivo |
| `COMPLETO` | "Completo" | Green | Roster cumple el minimo deportivo |

### 7.2 ResumenEquiposBadge

Muestra chips: `N equipos` / `X completos` / `Y incompletos`

### 7.3 ResumenPagoCard

| `estado_pago_global` | Color | Icono |
|---------------------|-------|-------|
| `PAGADA` | Green | CheckCircle |
| `PENDIENTE` | Amber | Clock |
| `PARCIAL` | Orange | AlertCircle |
| `CANCELADA` | Red | XCircle |

### 7.4 PaymentCallout

Visible unicamente cuando:
- `estado_pago_global === "PENDIENTE"` Y
- `inscripcion.estado === "VALIDADA"`

**Ya no se infiere desde `Inscripcion.estado` unicamente.**

### 7.5 RegistrationStepsCard

| Step | Logica Actual (rota) | Logica Corregida |
|------|----------------------|------------------|
| "Pago completado" | `inscripcion.estado === "CONFIRMADA"` | `resumen_pago.estado_pago_global === "PAGADA"` |
| "Completa el pago" | `inscripcion.estado === "VALIDADA"` | `resumen_pago.estado_pago_global === "PENDIENTE" && inscripcion.estado === "VALIDADA"` |

---

## 8. Pruebas de Aceptacion

### 8.1 Backend: Selector

| Test | Criterio |
|------|----------|
| `test_selector_carga_compras_inscripcion` | `InscripcionSelector` carga `Compra` asociadas |
| `test_selector_carga_equipos_con_disciplina` | Equipos tienen `disciplina.min_jugadores` disponible |
| `test_selector_no_calcula_estado_roster` | Selector solo carga; no calcula derivados |

### 8.2 Backend: Presenter

| Test | Criterio |
|------|----------|
| `test_presenter_calcula_estado_roster_incompleto` | `jugadores_registrados < minimo_deportivo` → `INCOMPLETO` |
| `test_presenter_calcula_estado_roster_completo` | `jugadores_registrados >= minimo_deportivo` → `COMPLETO` |
| `test_presenter_calcula_faltantes` | `faltantes = max(0, minimo_deportivo - jugadores_registrados)` |
| `test_presenter_calcula_resumen_equipos` | `completos` e `incompletos` cuadran con los equipos |
| `test_presenter_no_accede_db` | Presenter no llama a ningun selector ni ORM |

### 8.3 Backend: Schema

| Test | Criterio |
|------|----------|
| `test_inscripcion_detail_out_extendido_valida` | `InscripcionDetailOut` acepta todos los campos nuevos |
| `test_estado_roster_enum_valido` | Solo acepta `INCOMPLETO` o `COMPLETO` |

### 8.4 Frontend

| Test | Criterio |
|------|----------|
| `test_badge_incompleto_cuando_estado_roster_incompleto` | Amber badge para `INCOMPLETO` |
| `test_badge_completo_cuando_estado_roster_completo` | Green badge para `COMPLETO` |
| `test_progress_bar_muestra_jugadores_minimo` | Barra con `jugadores_registrados / minimo_deportivo` |
| `test_payment_callout_solo_si_pago_pendiente` | Visible solo con `resumen_pago.estado_pago_global === "PENDIENTE"` |
| `test_registration_steps_card_usa_resumen_pago` | Paso de pago usa `resumen_pago`, no inferencia desde `estado` |

---

## 9. Lotes de Implementacion (Apply Batches)

### Lote 1: Result Objects + Selector (Backend)

**Archivos:**
- `backend/modules/salesianos_fest/domain/results/inscripcion_results.py`
- `backend/modules/salesianos_fest/domain/selectors/inscripcion_selector.py`

**Cambios:**
- Agregar campos derivados a `InscripcionDetailResult`
- Extender selector para cargar `Compra` via `commerce`

**Criterio de exito:** Result object tiene todos los datos necesarios para que el presenter transforme.

---

### Lote 2: HTTP Schemas (Backend)

**Archivos:**
- `backend/modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py`

**Cambios:**
- Agregar `ResumenEquiposSchema`
- Agregar `ResumenPagoSchema`, `CompraResumenSchema`, `OrdenPagoResumenSchema`
- Extender `EquipoDetailSchema` con `estado_equipo`, `estado_roster`, `jugadores_registrados`, `minimo_deportivo`, `faltantes`
- Extender `InscripcionDetailOut`

**Criterio de exito:** Schemas validan el contrato exacto.

---

### Lote 3: Presenter (Backend)

**Archivos:**
- `backend/modules/salesianos_fest/presentation/presenters/inscripcion_presenter.py`

**Cambios:**
- `present_inscripcion_detail` calcula `estado_roster` por equipo
- `present_inscripcion_detail` calcula `resumen_equipos`
- `present_inscripcion_detail` transforma `resumen_pago`

**Criterio de exito:** Presenter transforma sin acceder a DB.

---

### Lote 4: Zod Schemas (Frontend)

**Archivos:**
- `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts`

**Cambios:**
- Agregar `ResumenEquiposSchema`
- Agregar `ResumenPagoSchema`
- Extender `EquipoDetailSchema` con campos derivados

**Criterio de exito:** TypeScript infiere tipos correctamente.

---

### Lote 5: Componentes UI (Frontend) — ResumenEquiposBadge + SortableEquipoCard

**Archivos:**
- `frontend/src/features/inscripciones/components/ResumenEquiposBadge.tsx` (nuevo)
- `frontend/src/features/inscripciones/components/SortableEquipoCard.tsx` (actualizado)

**Cambios:**
- `SortableEquipoCard` usa `estado_roster` para badge
- `SortableEquipoCard` muestra barra de progreso `jugadores_registrados / minimo_deportivo`
- `SortableEquipoCard` muestra label de `faltantes`
- Nuevo `ResumenEquiposBadge` muestra resumen de equipos

**Criterio de exito:** Badge correcto y barra de progreso funcional.

---

### Lote 6: ResumenPagoCard (Frontend)

**Archivos:**
- `frontend/src/features/inscripciones/components/ResumenPagoCard.tsx` (nuevo)

**Cambios:**
- Renderiza `resumen_pago.estado_pago_global`
- Renderiza lista de compras
- Renderiza barra de capacidad (`capacidad_disponible`)

**Criterio de exito:** Muestra correctamente todos los estados de pago.

---

### Lote 7: PaymentCallout + RegistrationStepsCard (Frontend)

**Archivos:**
- `frontend/src/features/inscripciones/views/InscripcionDetailView.tsx`
- `frontend/src/features/inscripciones/components/RegistrationStepsCard.tsx`

**Cambios:**
- `PaymentCallout` usa `resumen_pago.estado_pago_global` (no mas inferencia desde `estado`)
- `RegistrationStepsCard` paso de pago usa `resumen_pago.estado_pago_global`

**Criterio de exito:** Correcta segregacion de estado deportivo vs comercial.

---

## 10. Artefactos Leidos para Este Plan

| Artefacto | Relevancia |
|-----------|------------|
| `contract/TEST_ARCHITECTURE_CONTRACT.md` | Patron de tests |
| `contract/api-wrapper-presenter-contract.md` | Reglas de presenters y wrappers |
| `contract/django-app-architecture-contract.md` | Patron completo Django |
| `contract/next-app-architecture-contract.md` | Arquitectura frontend |
| `contract/smart.md` | Smart Fields y desacoplamiento UI |
| `contract/SCHEMA_DRY_INTENTION.md` | Composicion de schemas |
| `backend/modules/salesianos_fest/domain/constants.py` | `EstadoInscripcionChoices`, `EstadoEquipoChoices` |
| `backend/modules/salesianos_fest/domain/models/equipo.py` | `Equipo` model |
| `backend/modules/salesianos_fest/domain/models/disciplina.py` | `Disciplina.min_jugadores` |
| `backend/modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py` | `InscripcionDetailOut` actual |
| `backend/modules/salesianos_fest/presentation/presenters/inscripcion_presenter.py` | `InscripcionPresenter` |
| `backend/modules/salesianos_fest/domain/selectors/inscripcion_selector.py` | `InscripcionSelector` |
| `frontend/src/features/inscripciones/views/InscripcionDetailView.tsx` | Detalle de inscripcion |
| `frontend/src/features/inscripciones/components/RegistrationStepsCard.tsx` | Pasos de registro |
| `frontend/src/features/inscripciones/components/SortableEquipoCard.tsx` | Card de equipo |
| `doc_dev/CONTRATO_OBJETIVO_INSCRIPCION_BACKEND_FRONTEND.md` | Contrato objetivo inscripcion |
| `doc_dev/ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md` | Especificacion funcional completa |

---

*Documento generado mediante SDD Explore read-only. No modifica codigo fuente. Todos los hallazgos estan respaldados por evidencia de archivos reales verificados con CodeGraph y lectura directa.*
