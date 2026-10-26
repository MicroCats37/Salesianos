# Exploration: Participantes — Reactivación con Asignación de Cupos

> **Proyecto:** `Salesianos`
> **Fecha:** 2026-10-19
> **Tipo:** Architecture Exploration
> **Artifact:** `sdd/participantes-reactivacion-asignacion-impacto/explore`
> **Modo:** Exploration — no implementation

---

## 1. Escenario y Preguntas Centrales

El usuario necesita validar el impacto de cambiar a una única fila `Participacion` por `(evento, disciplina, persona)` con transiciones A↔R (reactivación), separando claramente el estado deportivo del derecho comercial pagado.

Preguntas clave:
1. ¿Cuál es el ciclo de vida exacto desde registro hasta reingreso y expansión?
2. ¿La reactivación de participación debería crear, reactiva, liberar, revocar o solo solicitar un `AsignacionCupo`?
3. ¿Qué permisos/autorizaciones se necesitan para cada acción?
4. ¿Cómo impacta a los endpoints REST y acciones del frontend?
5. ¿Qué constraints, migraciones y escenarios de concurrencia existen?

---

## 2. Estado Actual del Sistema

### 2.1 Modelo de Datos — Cuatro Entidades Principales

#### `InscripcionPersona`
- **FK:** inscripcion, persona
- **Estados:** `A` (Activo), `R` (Retirado)
- **Constraint:** Unique `(inscripcion, persona)`
- **Propósito:** Vincula persona a inscripción (varios equipos por inscripción)

#### `Participacion`
- **FK:** inscripcion_persona, equipo, evento, disciplina, persona
- **Estados:** `A` (Activa), `R` (Retirada)
- **Constraint parcial DB:** Unique `(evento, disciplina, persona)` WHERE `estado=A` (R11)
- **Propósito:** Participación deportiva por equipo/disciplina
- **Redundancia controlada:** evento, disciplina, persona son copias para constraint sin JOIN

#### `CompraInscripcion`
- **FK:** compra (genérica commerce.Compra), inscripcion
- **Tipos:** `INICIAL`, `AMPLIACION`
- **Constraint parcial:** Unique `(inscripcion, tipo=INICIAL)` — una compra inicial por inscripción
- **Propósito:** Vincular compra comercial genérica a la inscripción FEST con detalles (cantidad, precio unitario snapshot, total)

#### `AsignacionCupo`
- **FK:** inscripcion, compra, inscripcion_persona
- **Estados:** `ACTIVA`, `LIBERADA`, `REVOCADA`
- **Constraint parcial:** Unique `(inscripcion, inscripcion_persona)` WHERE `estado=ACTIVA`
- **Propósito:** Cupo comercial pagado asignado a persona

### 2.2 Estados y Constantes

```
EstadoParticipacionChoices:  A="Activa", R="Retirada"
EstadoInscripcionPersonaChoices: A="Activo", R="Retirado"
EstadoAsignacionCupoChoices:  ACTIVA, LIBERADA, REVOCADA
TipoCompraChoices: INICIAL, AMPLIACION
EstadoCompraChoices: PENDIENTE, PAGADA, CANCELADA
```

### 2.3 Ciclo de Vida Actual (completo)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: REGISTRO                                                          │
│                                                                           │
│ POST /inscripciones/completa/                                             │
│   → Crea Inscripcion (BORRADOR)                                           │
│   → Crea Compra (INICIAL, PENDIENTE) con cantidad ≥ minimo_compra_inicial │
│   → Crea OrdenPago (PENDIENTE)                                           │
│   → Crea Equipos (disciplina, categoría, nombre)                         │
│   → No crea Participacion aún (roster vacío)                             │
│   → No crea AsignacionCupo                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: REGISTRAR PERSONAS (sin pago aún)                                │
│                                                                           │
│ POST /inscripciones/{id}/personas  (con o sin equipo_id)                 │
│   → Crear/reutilizar InscripcionPersona (estado=A si era R)              │
│   → Si equipo_id: crear Participacion(estado=A)                          │
│   → R11 se verifica: solo bloquea si existe OTRA fila A para             │
│     (evento, disciplina, persona)                                         │
│   → No crea AsignacionCupo (aún no hay pago)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: PAGO                                                             │
│                                                                           │
│ POST /compras/{id}/iniciar-pago → Izipay                                 │
│ POST /compras/confirmar-pago → ConfirmarPagoFlujo                        │
│   → Marca Compra.estado = PAGADA                                          │
│   → NO cambia Inscripcion.estado                                          │
│   → Trigger: CrearAsignacionesFlujo                                      │
│     → Crea AsignacionCupo(ACTIVA) para cada InscripcionPersona.estado=A  │
│       que aún no tiene asignacion activa                                  │
│     → Sincroniza AcreditacionEvento                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 4: AGREGAR PERSONA DESPUÉS DEL PAGO                                 │
│                                                                           │
│ POST /asignaciones/ (after payment)                                      │
│   → AsignarPersonaFlujo                                                   │
│   → Verifica saldo disponible (pagados - asignaciones_activas)            │
│   → Crea/recicla InscripcionPersona(estado=A)                            │
│   → Crea Participacion si equipo_id                                       │
│   → Crea AsignacionCupo(ACTIVA) desde compra con saldo disponible       │
│   → Si no hay saldo: CupoAgotadoError (409)                             │
│   → Si persona ya tiene asignacion activa: PersonaYaAsignadaError         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 5: RETIRAR PERSONA                                                  │
│                                                                           │
│ PATCH /participaciones/{id}/retirar  (retiro individual)                 │
│   → ParticipacionOrchestrator.retirer_participacion_proceso               │
│   → Participacion.estado = R                                              │
│   → NO libera AsignacionCupo automáticamente                              │
│                                                                           │
│ PATCH /inscripciones/{id}/personas/{persona_id}/retirar  (retiro total) │
│   → RetirarPersonaFlujo                                                  │
│   → Participacion.estado = R para TODAS las participaciones              │
│   → InscripcionPersona.estado = R                                         │
│   → Sincroniza AcreditacionEvento desde OTRAS inscripciones pagadas      │
│                                                                           │
│ POST /asignaciones/liberar                                               │
│   → LiberarCupoFlujo                                                     │
│   → Participacion.estado = R para todas en esta inscripcion               │
│   → Si persona NO tiene otras participaciones activas en esta inscripcion │
│     → AsignacionCupo.estado = LIBERADA                                   │
│   → Cupo queda LIBERADO pero no destruido — disponible para reasignación │
│   → Sincroniza AcreditacionEvento considerando TODAS las inscripciones   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 6: REINGRESO / REACTIVACIÓN                                         │
│                                                                           │
│ POST /inscripciones/{id}/personas  (persona con InscripcionPersona.estado=R)│
│   → AgregarPersonaFlujo                                                  │
│   →get_or_create InscripcionPersona                                      │
│   → Si estado=R: ip.estado = A (REACTIVA)                               │
│   → SI equipo_id: crear NUEVA Participacion(estado=A) — ROW NUEVA        │
│   → R11 no bloquea porque solo verifica estado=A                          │
│   → Si hay saldo disponible: POST /asignaciones/ crea AsignacionCupo     │
│                                                                           │
│ ⚠️ PROBLEMA: Se crea NUEVA fila Participacion por cada reingreso        │
│    Una persona puede tener múltiples filas R + una A                      │
│    El array participantes[] del presenter INCLUYE filas R                │
│    Pero jugadores_registrados SOLO cuenta filas A                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 7: MOVER ENTRE EQUIPOS                                              │
│                                                                           │
│ PATCH /participaciones/{id}/mover                                        │
│   → ParticipacionOrchestrator.mover_participacion_proceso                 │
│   → Solo actualiza participacion.equipo_id (NO crea fila nueva)           │
│   → NO se verifica R11 en el move (porque no se llama a crear())         │
│   → Si persona ya tiene participación activa en otro equipo de la        │
│     misma disciplina, técnicamente no viola R11 pero el move             │
│     no está validado                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 8: AMPLIACIÓN (más cupos)                                           │
│                                                                           │
│ POST /compras/ (tipo=AMPLIACION)                                          │
│   → Nueva Compra(AMPLIACION, PENDIENTE)                                  │
│   → Mínimo inicial NO se aplica                                           │
│   → Tras pago: CrearAsignacionesFlujo crea AsignacionCupo adicionales    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Análisis: Reactivación de Participación

### 3.1 Dos Concepciones del Mundo

**Concepción A — Filas Históricas (Actual):**
- Cada reingreso crea NUEVA fila `Participacion(estado=A)`
- La/las filas `R` permanecen como auditoría
- Una persona puede tener: `[R, R, A]` — múltiples ciclos de entrada/salida
- R11 funciona trivially: solo verifica `A`

**Concepción B — Única Fila por (evento, disciplina, persona):**
- Una sola fila `Participacion` por `(evento, disciplina, persona)`
- Transiciones A↔R para reactivar
- Múltiples ciclos de entrada/salida = transiciones de estado, no filas nuevas
- R11 se cumple por el unique constraint parcial

### 3.2 Separación Deportivo vs. Comercial

**Estado Deportivo (Participacion):**
- Solo representa si la persona está jugando activamente en un equipo
- R11 protege contra doble participación activa en misma disciplina
- Reactivación = cambiar estado de R → A en la fila existente

**Derecho Comercial (AsignacionCupo):**
- Representa derecho pagado por un cupo específico de una compra específica
- Un cupo LIBERADO no se "reactiva" automáticamente — se reasigna a otra persona
- La pregunta "¿debo crear, reactivar, liberar, revocar o solo solicitar un AsignacionCupo?"
  → **RESPUESTA: Solo solicitar.** Si hay saldo disponible, se crea nueva asignación. Si no hay, el flujo falla.

### 3.3 Análisis de Opciones para Reactivación

| Opción | Descripción | Pros | Contras | Complejidad |
|--------|-------------|------|---------|-------------|
| **A — Mantener Filas Múltiples** | Cada reingreso crea fila nueva A; R permanece como auditoría | Historial completo de ida/vuelta; R11 funciona trivialmente; alineado con spec F5 | Múltiples filas R por persona; `participantes[]` incluye histórico; conteos visuales inconsistentes | N/A (actual) |
| **B — Única Fila A↔R** | Una fila por (evento, disciplina, persona);transiciones A↔R | Una sola fila; estado natural tipo state machine; más simple queries | Pierde historial de ciclos; requiere validación explícita en reingreso (no crear si A existe) | Media |
| **C — Fila Única + Historial Auxiliar** | Participacion con transiciones; tabla HistoricoParticipacion separados | Historial preservado fuera de la fila principal; consulta simple para estado actual | Más complejo; dos tablas que mantener | Alta |

---

## 4. Permisos y Autorizaciones

### 4.1 Análisis de Autorización Actual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ AUTORIZACIÓN ACTUAL (del código)                                           │
│                                                                             │
│ Controllers usan auth=None (públicos) o auth=JWTAuth()                      │
│ La VALIDACIÓN DE PROPIEDAD ocurre en el código del controller:              │
│                                                                             │
│ CompraController: _validate_compra_ownership()                               │
│   → Verifica: compra.compra_inscripcion.inscripcion.responsable_id == user  │
│   → Si no: PermissionDenied                                                 │
│                                                                             │
│ AsignacionController: todas requieren IsAuthenticated                        │
│   → Pero NO verifican propiedad en el endpoint liberar_cupo                 │
│   → El flujo LiberarCupoFlujo verifica fecha_limite pero NO quién llama   │
│                                                                             │
│ InscripcionController: muchos auth=None                                     │
│   → POST /inscripciones/ requiere JWT                                       │
│   → POST /inscripciones/{id}/personas auth=None (público)                  │
│   → PATCH /participaciones/{id}/retirar auth=None (público)                │
│   → PATCH /participaciones/{id}/mover auth=None (público)                  │
│                                                                             │
│ ❌ PROBLEMA: Endpoints críticos de modificación son públicos                │
│    Cualquier persona puede retirar o mover participantes de cualquier        │
│    inscripción sin verificar que es el responsable o admin                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Permisos Requeridos por Acción

| Acción | Actor | Verificación Necesaria | Actual |
|--------|-------|------------------------|--------|
| Crear Inscripción | Usuario autenticado (responsable) | JWT + responsable derivado del auth | ✅ JWT + ownership implícito |
| Agregar Persona | Responsable/Delegado | Verificar que user es responsable o delegado de la inscripción | ❌ No verificado |
| Retirar Participacion | Responsable/Delegado | Verificar que user es responsable o delegado | ❌ No verificado |
| Mover Participacion | Responsable/Delegado | Verificar que user es responsable o delegado | ❌ No verificado |
| Asignar Cupo (post-pago) | Responsable | Verificar que user es responsable | ❌ No verificado en endpoint |
| Liberar Cupo | Responsable/Admin | Verificar que user es responsable o admin | ❌ No verificado |
| Override Fiesta | Admin | Solo admins | ✅ Implementation exists |
| Confirmar Pago | Sistema (callback Izipay) | Validación de firma/callback | ✅ Existe |

### 4.3 NO Asumir Que un Permiso "Debe Ser Eliminado"

El análisis de autorización debe ser descriptivo, no prescriptivo. Si un endpoint es público pero no debería serlo, eso es un gap que documentar, no algo que se asume que "debe ser removido" sin validación con el usuario/producto.

---

## 5. Impacto en Endpoints REST y Frontend

### 5.1 Endpoints Afectados

```
ENDPOINTS PARTICIPANTE:
├── POST   /inscripciones/{id}/personas        → agregar/reactivar persona
├── PATCH  /participaciones/{id}/retirar       → retiro individual
├── PATCH  /participaciones/{id}/mover        → mover entre equipos
├── PATCH  /participaciones/{id}              → actualizar rol/talla/notas
│
ENDPOINTS ASIGNACIÓN:
├── POST   /asignaciones/                     → asignar pessoa (post-pago)
├── POST   /asignaciones/liberar             → liberar cupo
├── GET    /asignaciones/inscripciones/{id}/asignaciones
│
FRONTEND ACTIONS (inscripcion.service.ts):
├── agregarParticipantesAEquipo()  → POST /inscripciones/{id}/personas
├── eliminarParticipante()        → PATCH /participaciones/{id}/retirar
├── moverParticipante()           → PATCH /participaciones/{id}/mover
├── editarParticipante()          → PATCH /participaciones/{id}
```

### 5.2 Simplificación de Endpoints Participantes

Con Opción B (úica fila A↔R), el endpoint `POST /inscripciones/{id}/personas` puede manejar:
1. Persona nueva → crear InscripcionPersona + Participacion
2. Persona con InscripcionPersona.estado=R → reactiva a A + crear/reutilizar Participacion

**Ya hace esto parcialmente** — el problema es que CREA nueva Participacion en vez de REUTILIZAR la existente.

**Con Opción B**, el flujo sería:
1. Buscar Participacion existente para (evento, disciplina, persona) con estado=R
2. Si existe: participacion.estado = A (reactivar)
3. Si no existe Y no hay A: crear nueva

### 5.3 Schema API — Inconsistencia Actual

```typescript
// frontend/src/features/inscripciones/services/inscripcion.service.ts

interface EquipoDetalleOut {
  jugadores_registrados: number;  // ✅ Cuenta SOLO estado="A"
  participantes: ParticipanteOut[]; // ⚠️ Incluye estado="A" y estado="R"
}
```

Esta inconsistencia existe en el presenter actual y fue documentada en PLAN_REINGRESO_PARTICIPACION_Y_DERECHOS_PAGADOS.md.

---

## 6. Constraints de Base de Datos y Concurrencia

### 6.1 Constraints Actuales

```python
# Participacion
UniqueConstraint(
    fields=["evento", "disciplina", "persona"],
    condition=Q(estado="A"),
    name="unique_r11_evento_disciplina_persona_activa",
)

# AsignacionCupo
UniqueConstraint(
    fields=["inscripcion", "inscripcion_persona"],
    condition=Q(estado="ACTIVA"),
    name="unique_activa_inscripcion_persona",
)
```

### 6.2 Concurrencia — Tests Existentes

| Test | Escenario | Resultado |
|------|-----------|-----------|
| `test_t14_concurrent_ultimo_cupo_desde_dos_requests` | Dos requests concurrentes consumen el último cupo | Solo uno succeed, otro CUPO_AGOTADO |
| `test_t15_concurrent_qr_scans_simultaneos` | Dos escaneos QR simultáneos | Solo uno PERMITIDO |

### 6.3 Para Opción B (Única Fila A↔R)

**Constraint sin cambio:**
- Unique parcial `(evento, disciplina, persona)` WHERE `estado=A` sigue funcionando

**Race Conditions a Considerar:**

1. **Reactivación concurrente:**
   - Request 1: Busca Participacion R → prepara cambiar a A
   - Request 2: Busca Participacion R → prepara cambiar a A
   - Ambas ven la misma fila R
   - Ambas intentan SET estado=A
   - **Solución:** `select_for_update()` en la fila antes de actualizar

2. **Reactivación + otra request que crea nueva:**
   - Request 1: Reactivando persona R → encuentra fila R
   - Request 2: Creando nueva participación (caso raro de múltiples equipos)
   - Si Request 2 también crea A, podría violate R11
   - **Solución:** Locking at transaction level + retry

### 6.4 Migración para Opción B (Destructiva)

```sql
-- Paso 1: Para cada (evento, disciplina, persona) con múltiples filas Participacion
-- Mantener la fila con estado='A' más reciente (o created_at más reciente)
-- Para filas R: mover a tabla HistoricoParticipacion

BEGIN;

-- Crear tabla de histórico
CREATE TABLE historico_participaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inscripcion_persona_id UUID NOT NULL,
    equipo_id UUID NOT NULL,
    evento_id UUID NOT NULL,
    disciplina_id UUID NOT NULL,
    persona_id UUID NOT NULL,
    rol VARCHAR(1),
    talla_camiseta VARCHAR(3),
    notas TEXT,
    estado VARCHAR(1),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    -- Flags de auditoría
    es_reactivacion BOOLEAN DEFAULT FALSE,
    ciclo_retiro_ingreso INTEGER DEFAULT 1,
    migrated_from_participacion_id UUID,
    migrated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insertar todas las filas R en histórico
INSERT INTO historico_participaciones (...)
SELECT ... FROM participaciones WHERE estado='R';

-- Eliminar filas R de la tabla principal
DELETE FROM participaciones WHERE estado='R';

-- Verificar que ahora cada (evento, disciplina, persona) tiene max 1 fila
-- Esto debería satisfaces el constraint único sin condición

COMMIT;
```

⚠️ **DATA ES DISPOSABLE** — el usuario dijo que los datos pueden ser descartados en futuras aplicaciones. Esto facilita enormemente la migración.

---

## 7. Casos de Edge y Escenarios Explícitos

### 7.1 Escenario: Reactivación con Cupo Pagado Liberado

```
Estado Inicial:
- Persona tiene Participacion(estado=A) en equipo de fútbol
- Persona tiene AsignacionCupo(estado=ACTIVA) de compra pagada

Acción: Responsable retira a la persona
Resultado:
- Participacion.estado = R
- AsignacionCupo.estado = LIBERADA (porque no hay más participaciones activas)
- Cupo queda LIBERADO, disponible para reasignación

Reactivación (mismo evento, misma disciplina):
- Request: POST /inscripciones/{id}/personas con persona existente
- Con Opción A: Crear nueva Participacion(estado=A)
- Con Opción B: Cambiar Participacion.estado = A
- Pero: ¿debe crear AsignacionCupo automáticamente?

Análisis:
- El cupo original fue LIBERADO, no destruido
- Si hay saldo disponible de OTRA compra pagada, se puede reasignar
- Si NO hay saldo, debe solicitarse nueva ampliación
- El flujo correcto es: solicitar AsignacionCupo si hay saldo disponible
- NO "reactivar" automáticamente el cupo liberado
```

### 7.2 Escenario: Reactivación sin Cupo Disponible

```
Estado:
- Persona con Participacion(estado=R)
- AsignacionCupo(estado=LIBERADA) de última compra
- CompraAMPLIACION(PENDIENTE) — nueva ampliación en curso
- No hay saldo disponible aún

Reactivación:
- Participacion.estado = A (reactivar sports)
- AsignacionCupo: debe esperar a que la ampliación se pague
- Flujo correcto: sports se reactiva, commercial se asigna cuando haya saldo
```

### 7.3 Escenario: Aceptado vs. Rechazado Explícito

| Escenario | Sports (Participacion) | Commercial (AsignacionCupo) | Resultado |
|-----------|------------------------|----------------------------|----------|
| Reactivación normal con saldo disponible | R → A (reactivar) | Crear nueva ACTIVA si hay saldo | ✅ Aceptado |
| Reactivación sin saldo disponible | R → A (reactivar) | Error: CupoAgotadoError | ⚠️ Parcial |
| Persona ya tiene A (reingreso sin retiro previo) | — | — | ❌ Bloqueado por R11 |
| Mismo evento, diferente disciplina | Crear nueva A | Crear si hay saldo | ✅ Aceptado |
| Admin revocando cupo | Sin cambio | REVOCADA | ⚠️ Admin action |

---

## 8. Recomendación de Diseño

### 8.1 Diseño Recomendado: Opción B (Única Fila A↔R)

**Justificación:**
1. **Simplicidad:** Una sola fila por (evento, disciplina, persona) para estado actual
2. **Semántica clara:** Transiciones A↔R representan ciclos de entrada/salida
3. **R11 funciona igual:** Constraint parcial solo en filas A
4. **Query simplicity:** `participantes_ativos` = filtro simple, no múltiples filas
5. **Data disposable:** El usuario dijo que datos son descartables — facilita migración

### 8.2 Cambios Necesarios por Componente

```
PARTICIPANTE LIFECYCLE:
─────────────────────
1. Registro inicial:
   → Crear InscripcionPersona(estado=A)
   → Crear Participacion(estado=A) si hay equipo

2. Retiro:
   → Participacion.estado = R (no destruir)

3. Reactivación:
   → Buscar Participacion(estado=R) para (evento, disciplina, persona)
   → Si existe: Participacion.estado = A
   → Si NO existe: Error (debe pasar por registro normal)
   → NO crear fila nueva

ASIGNACIONCUPOLIFECYCLE:
────────────────────────
4. Asignación post-pago:
   → Crear AsignacionCupo(estado=ACTIVA) por persona
   → Origen: primera compra PAGADA con saldo disponible

5. Liberación:
   → AsignacionCupo.estado = LIBERADA
   → Cupo disponible para reasignación

6. Reactivación comercial:
   → Al reactivar Participacion, si persona no tiene AsignacionCupo(ACTIVA)
   → Solicitar nueva si hay saldo disponible
   → Si no hay saldo: el flujo falla con CupoAgotadoError
   → Usuario debe comprar ampliación primero
```

### 8.3 Permisos — Correcciones Necesarias

| Endpoint | Corrección |
|---------|-----------|
| `POST /inscripciones/{id}/personas` | Agregar verificación de que user es responsable/delegado |
| `PATCH /participaciones/{id}/retirar` | Agregar verificación de propiedad |
| `PATCH /participaciones/{id}/mover` | Agregar verificación de propiedad |
| `POST /asignaciones/liberar` | Agregar verificación de propiedad |

**NO asumir que estos permisos "deben eliminarse" — documentar el gap y dejar que el usuario/producto decida.**

---

## 9. Plan de Pruebas Detallado

### 9.1 Tests de Reactivación (Participacion)

| ID | Escenario | Resultado Esperado | Tipo |
|----|-----------|-------------------|------|
| T-R01 | Reactivar persona con Participacion.estado=R → cambia a A | ✅ Participacion.estado=A, sin nueva fila | Unit |
| T-R02 | Reactivar persona que NO tiene Participacion previa | ❌ Error o crear nueva (definir) | Integration |
| T-R03 | Reactivar persona con Participacion.estado=A ya existente | ❌ R11 bloquea | Unit |
| T-R04 | Reactivar y Simultaneously otra request crea A (concurrencia) | ✅ Uno succeed, otro falla por R11 | Concurrency |
| T-R05 | Reactivar persona con saldo disponible → crea AsignacionCupo | ✅ AsignacionCupo(ACTIVA) creada | Integration |
| T-R06 | Reactivar persona sin saldo disponible | ❌ CupoAgotadoError | Integration |

### 9.2 Tests de Retiro y Liberación

| ID | Escenario | Resultado Esperado | Tipo |
|----|-----------|-------------------|------|
| T-L01 | Retirar Participacion → estado=R, no destruye AsignacionCupo | ✅ Participacion.estado=R, AsignacionCupo intacta | Integration |
| T-L02 | Liberar Cupo (persona sin más participaciones activas) | ✅ AsignacionCupo.estado=LIBERADA | Integration |
| T-L03 | Liberar Cupo, reasignar a otra persona | ✅ Nueva AsignacionCupo(ACTIVA) para persona B | Integration |
| T-L04 | Reactivar persona A, luegoLiberar Cupo, luegoIntentar reactivar (sin saldo) | ❌ CupoAgotadoError | Integration |

### 9.3 Tests de Concurrencia

| ID | Escenario | Resultado Esperado | Tipo |
|----|-----------|-------------------|------|
| T-C01 | Dos requests concurrentes reactivan la misma Participacion R | ✅ Uno succeed, DB consistency | Concurrency |
| T-C02 | Dos requests concurrentes consuman último saldo disponible | ✅ Uno succeed, otro CupoAgotadoError | Concurrency |
| T-C03 | Request de reactivación + Request de retiro simultáneos | ✅ Estado final consistente | Concurrency |

### 9.4 Tests de Autorización

| ID | Escenario | Resultado Esperado | Tipo |
|----|-----------|-------------------|------|
| T-Auth01 | No-owner intenta agregar persona → 403 | ❌ PermissionDenied | Security |
| T-Auth02 | No-owner intenta retirar → 403 | ❌ PermissionDenied | Security |
| T-Auth03 | Owner intenta agregar persona → 200 | ✅ Success | Security |
| T-Auth04 | Admin override fiesta → siempre allowed | ✅ Success | Security |

---

## 10. Plan de Migración / Batches de Apply

### Batch 1: Modelo y Constraints

1. Agregar campo `es_reactivable` o flags de auditoría a Participacion (opcional)
2. Agregar constraint único sin condición parcial (después de limpiar datos)
3. Crear tabla HistoricoParticipacion si se decide preservar auditoría

### Batch 2: Lógica de Negocio

1. Modificar `AgregarPersonaFlujo` para buscar Participacion.R y reutilizar
2. Modificar `ParticipacionOrchestrator.retirer_participacion_proceso` para no destruir
3. Modificar `ParticipacionCoreService` para manejar R→A en vez de crear

### Batch 3: Asignación de Cupos

1. Modificar `AsignarPersonaFlujo` para detectar si es reactivación
2. Mantener lógica de solicitar saldo disponible — NO reutilizar cupo LIBERADO automáticamente

### Batch 4: Frontend y API

1. Actualizar schemas `EquipoDetalleOut` para separar `participantes` de `historico` (Opción D)
2. Actualizar servicios frontend para manejar el nuevo flujo
3. Tests end-to-end de ciclos completos

### Batch 5: Validación y Concurrencia

1. Agregar `select_for_update` en flujos de reactivación
2. Tests de concurrencia específicamente para T-C01
3. Validar R11 con múltiples filas R y una A

---

## 11. Riesgos Identificados

1. **Inconsistencia visual en frontend:** `participantes[]` incluye R mientras `jugadores_registrados` solo cuenta A
2. **Gap de autorización:** Endpoints críticos son públicos cuando deberían requerir propiedad
3. **Concurrency en reactivación:** Sin `select_for_update`, dos requests podrían crear estado inconsistido
4. **Mover entre equipos no verifica R11:** `_mover_atomico` no llama a crear() por lo que R11 no se re-verifica
5. **Datos existentes:** Si se migra de filas múltiples a fila única, se pierde historial de ciclos
6. **Reactivación comercial:** No está claro si un cupo LIBERADO puede reutilizarse automáticamente o requiere nueva asignación

---

## 12. Comparación de Diseños y Recomendación Final

### Diseño 1: Status Quo (Filas Múltiples)

| Aspecto | Evaluación |
|---------|-----------|
| R11 | ✅ Funciona correctamente |
| Historial | ✅ Completo |
| Consistencia UI | ❌ `participantes[]` incluye R |
| Query simplicity | ❌ Requiere filtrar por estado |
| Data model | ⚠️ Múltiples filas R por persona |

### Diseño 2: Única Fila A↔R (Recomendado)

| Aspecto | Evaluación |
|---------|-----------|
| R11 | ✅ Funciona con constraint parcial |
| Historial | ⚠️ Pierde ciclos (aceptable si data disposable) |
| Consistencia UI | ✅ `participantes` = activos |
| Query simplicity | ✅ Sin filtro de estado |
| Migration | ⚠️ Requiere cleanup de filas R |

### Recomendación: **Diseño 2 (Única Fila A↔R)**

**Razón:** El usuario explicitly dijo "Data is disposable in future applies" — esto hace la migración viable. La simplicidad de una sola fila con transiciones de estado es preferable para mantenimiento futuro.

**Condiciones:**
1. Data disposable — confirmado por usuario
2. Historial de ciclos no es business-critical
3. Reactivación comercial sigue el patrón de "solicitar si hay saldo"

---

## 13. Archivos y Áreas Afectadas

| Archivo | Por Qué | Cambio |
|---------|---------|--------|
| `domain/models/participacion.py` | Constraint R11 | Sin cambio |
| `domain/services/core/participacion_service.py` | Lógica de crear | Buscar R existente antes de crear |
| `domain/services/flujos/agregar_persona_flujo.py` | Flujo de agregar persona | Reutilizar Participacion.R → A |
| `domain/services/orchestrators/participacion_orchestrator.py` | Endpoints de participación | Sin cambio fundamental |
| `domain/services/flujos/asignar_persona_flujo.py` | Asignación post-pago | Sin cambio (crear es correcto) |
| `domain/services/flujos/liberar_cupo_flujo.py` | Liberación de cupo | Sin cambio |
| `presentation/controllers/inscripcion_controller.py` | Endpoints agregar/retirar | Agregar auth checks |
| `presentation/presenters/inscripcion_presenter.py` | Presenter de roster | Separar `participantes` de `historico` |
| `frontend/src/features/inscripciones/services/inscripcion.service.ts` | Tipos frontend | Actualizar `EquipoDetalleOut` |

---

## 14. Listo para Proposal

**Respuesta: SÍ — está listo para propuesta formal**

El sistema está bien comprendido, las opciones están analizadas, y la recomendación es clara. El siguiente paso es crear el artifact `proposal` formal con:

1. Diseño recomendado: Opción B — Única Fila A↔R
2. Separación clara: Deportivo (Participacion A↔R) vs. Comercial (AsignacionCupo — solo crear/solicitar, no reutilizar automáticamente)
3. Permisos: Documentar gaps de autorización como hallazgos, no como correcciones automáticas
4. Plan de migración: 5 batches modulares
5. Tests: 15+ tests de cobertura

---

## 15. Referencias

- Spec FEST: `doc_dev/ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md`
- Previous exploration: `doc_dev/PLAN_REINGRESO_PARTICIPACION_Y_DERECHOS_PAGADOS.md`
- Tablas y lógica: `doc_dev/DOCUMENTACION_LOGICA_Y_TABLAS_SALESIANOS_FEST.md`
- Contrato arquitectónico: `contract/PLAN_REFACTORIZACION.md`
- Contrato test: `contract/TEST_ARCHITECTURE_CONTRACT.md`
- R11 constraint: `domain/models/participacion.py:97-105`
- AsignacionCupo states: `domain/models/asignacion_cupo.py`
- Reingreso actual: `domain/services/flujos/agregar_persona_flujo.py:86-93`
- Concurrency tests: `tests/integration/test_asignacion.py:496-603`
