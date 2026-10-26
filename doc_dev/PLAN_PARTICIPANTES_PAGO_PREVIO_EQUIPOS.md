# Plan: Participantes, Pago Previo y Equipos — Salesianos Fest

> **Estado:** Análisis de exploración SDD  
> **Proyecto:** Salesianos  
> **Fecha:** 19 de octubre de 2026  
> **Persistencia:** `sdd/participantes-pago-previo-equipos/explore` (Engram)

---

## 1. Objetivo del Cambio

Implementar el flujo completo donde:

1. El formulario inicial de inscripción crea **sólo** `Inscripcion` + `Compra` (PENDIENTE) + `OrdenPago` + `Equipo` — sin personas.
2. Después de crear la inscripción, la UI muestra un **pool de participantes**. Agregar una persona crea/solo `InscripcionPersona` (pre-registrada); estos son participantes pendientes.
3. Los participantes pre-registrados activos están limitados por la capacidad comprada/contratada. Aparecen en el pool pero **no pueden arrastrarse a un equipo** y no reciben pago/acreditación/becas.
4. La asignación a equipo (`Participacion`) se permite **sólo** cuando ese participante tiene un `AsignacionCupo` activa来源于 compra pagada. El drag/drop debe usar mutation(es) backend dedicada, nunca estado solo frontend.
5. La confirmación de pago convierte la capacidad en pagada; determinar la política exacta para producir registros `AsignacionCupo` para personas pre-registradas: asignación determinista automática, acción responsable explícita, o híbrida. **Recomendación: híbrida con detonador automático en confirmación de pago.**
6. `Participacion` esPlacement deportivo únicamente; beneficios/acreditación derivan de asignación de cupo activa pagada, nunca de participation.
7. Reglas de disciplina max/min de equipo, R11, fecha límite de mutación, permisos owner/admin, pago cancelado/fallido y re-ingreso/retiro/movimiento de equipo deben ser atendidos.

---

## 2. Estado Actual vs. Estado Objetivo

### 2.1 Diagrama de Flujo — Estado Actual

```
[Wizard] → POST /inscripciones/completa/
  → Crea: Inscripcion + Compra + OrdenPago + CompraInscripcion + Equipos
  → NO crea personas

[Detalle] → GET /inscripciones/{id}/detalle
  → Muestra equipos con participantes directamente dentro de tarjetas de equipo
  → NO hay sección "pool" separada

[Agregar persona] → POST /inscripciones/{id}/personas
  → si equipo_id: crear InscripcionPersona + Participacion (sin validar cup pagado)
  → si no equipo_id: crear solo InscripcionPersona

[Drag-drop equipo] → PATCH /participaciones/{id}/mover
  → Mover Participacion entre equipos
  → NO valida si la persona tiene AsignacionCupo activa pagada

[Pago Izipay] → Callback → ConfirmarPagoFlujo
  → Marca Compra = PAGADA
  → NO llama a CrearAsignacionesFlujo automáticamente

[Post-pago asignar] → POST /api/asignaciones/
  → Crea AsignacionCupo (consume saldo disponible)
  → NO crea Participacion
```

### 2.2 Diagrama de Flujo — Estado Objetivo

```
[FASE 1: Crear inscripción + compra + equipos]
POST /inscripciones/completa/
  → Inscripcion (BORRADOR) + Compra (PENDIENTE) + OrdenPago + CompraInscripcion + Equipos
  → Sin personas todavía

[FASE 2: Pool de participantes — sin cupos pagados]
GET /inscripciones/{id}/detalle
  → Sección "Pool de participantes" (nueva UI)
  → Muestra: InscripcionPersona(s) sin AsignacionCupo activa
  → Estado: TARJETA_BLOQUEADA (sin asa de drag, badge "Esperando pago")

[Agregar persona al pool]
POST /inscripciones/{id}/personas (sin equipo_id)
  → Crear/reativar InscripcionPersona (estado=A)
  → NO crear Participacion
  → Validar: inscritos ≤ contratados (cupos contratados, no pagados)

GET /inscripciones/{id}/saldo
  → { contratados, pagados, asignados_pagados, disponibles_pagados }

[Confirmar pago Izipay]
Callback → ConfirmarPagoFlujo
  → Marca Compra = PAGADA (select_for_update, idempotente)
  → DENTRO de la misma transacción atómica:
     → CrearAsignacionesFlujo._crear_asignaciones_por_compra()
       → Para cadapersona pre-registrada (InscripcionPersona.estado=A, sin AsignacionCupo activa):
          → Crear AsignacionCupo (origen=primera CompraPagada con saldo disponible)
       → Sync AcreditacionEvento
  → Return CompraConfirmedResult

[FASE 3: Pool → Equipo (con cup pagado)]
POST /inscripciones/{id}/pool/asignar        (implementado — ver contrato §3.1)
  → Validar: persona tiene AsignacionCupo activa en esta inscripcion
  → Crear Participacion (validar R11 + roster máximo)
  → Return ParticipacionOut

[Drag-drop backend]
PATCH /participaciones/{id}/mover
  → Validar: persona de la Participacion tiene AsignacionCupo activa en la inscripcion destino
  → Validar: R11 + roster máximo del equipo destino
  → Mover Participacion al nuevo equipo

[Retirar persona de inscripcion]
POST /api/asignaciones/liberar
  → Retirar Participaciones (estado=R)
  → Si no hay más Participaciones activas: AsignacionCupo → LIBERADA
  → Sync AcreditacionEvento (desde todos los orígenes activos)
```

---

## 3. Modelo de Datos y Propiedad de Estados

### 3.1 Entidades y Sus Estados

| Entidad | Estados posibles | Política de transición |
|---------|----------------|-----------------------|
| `Inscripcion` | BORRADOR, RECIBIDA, EN_REVISION, OBSERVADA, VALIDADA, CONFIRMADA, RECHAZADA, CANCELADA | Admin/owner según rol; pago NO cambia estado deportivo |
| `Compra` (commerce) | PENDIENTE, PAGADA, CANCELADA | Solo commerce; ConfirmarPagoFlujo-transitiona PENDIENTE→PAGADA |
| `CompraInscripcion` | — | Datos de la compra específica de la inscripción |
| `AsignacionCupo` | ACTIVA, LIBERADA, REVOCADA | ACTIVA solo cuando el cupo está consumido por persona con compra pagada; LIBERADA al retirar de todas las participaciones; REVOCADA por admin |
| `InscripcionPersona` | A (activo), R (retirado) | Creador por agregar_persona_flujo; retira cuando se retira de la inscripción |
| `Participacion` | A (activa), R (retirada) | Solo se crea si existe AsignacionCupo ACTIVA para esa persona; retira al liberar cupo |
| `AcreditacionEvento` | PENDIENTE, ACTIVA, SUSPENDIDA, REVOCADA | Sincroniza desde compras pagadas + overrides admin |

### 3.2 Regla de Capacidad

```
contratados      = SUM(CompraInscripcion.cantidad) WHERE Compra.estado IN (PENDIENTE, PAGADA) y no CANCELADA
pagados          = SUM(CompraInscripcion.cantidad) WHERE Compra.estado = PAGADA
asignados_pagados = COUNT(AsignacionCupo WHERE estado=ACTIVA AND origen compra PAGADA)
disponibles_pagados = pagados - asignados_pagados
registrados      = COUNT(InscripcionPersona WHERE estado=A)

INVARIANTE: registrados ≤ contratados  (siempre)
INVARIANTE: disponibles_pagados ≥ 0  (siempre, por construcción)

Participants con AsignacionCupo.estado=ACTIVA → участвуют en equipos (Participacion activa)
Participants sin AsignacionCupo activa → pool bloqueado
```

### 3.3 Participacion Sin Cupo Pagado — Regla de Bloqueo

```
Crear Participacion (mover o nuevo) SÓLO si:
  1. Existe AsignacionCupo WHERE
       inscripcion_persona.persona = persona_id AND
       inscripcion = inscripcion_id AND
       estado = ACTIVA
  2. La AsignacionCupo.origin compra.estado = PAGADA
```

**Implementación en `ParticipacionCoreService.crear()` y `.mover()`:**
- Consultar `AsignacionCoreService.obtener_asignacion_activa_por_persona(inscripcion_id, persona_id)`
- Validar que exista y que el origen esté PAGADO
- Si no existe → `CupoNoAsignadoError` ( nuevo código, 409 Conflict)

---

## 4. Inventario de Endpoints API

### 4.1 Endpoints Existentes (no cambiar firma, posiblemente mudar comportamiento)

| Método | Ruta | Request | Response | Auth | Comportamiento actual | Cambio |
|--------|------|---------|----------|------|----------------------|--------|
| POST | `/inscripciones/completa/` | `CrearInscripcionCompletaIn` | `InscripcionCompletaOut` | JWT | Crea todo átomo, sin personas | Mantener |
| GET | `/inscripciones/{id}/detalle` | — | `InscripcionDetailOut` | público | Equipos con participantes | Agregar campo `personas_sin_cupo` y `asignaciones_cupo` al result |
| POST | `/inscripciones/{id}/personas` | `AgregarPersonaIn` | `{participante: ParticipacionOut}` | JWT | Si `equipo_id` → crea Participacion (sin validar cup) | **Modificar**: si `equipo_id` → validar cup activo; nuevo código `CUPO_NO_ASIGNADO` |
| PATCH | `/participaciones/{id}/mover` | `MoverParticipacionIn` | `ParticipacionOut` | público | Mover entre equipos (sin validar cup) | **Modificar**: validar cup activo en inscripcion destino |
| GET | `/inscripciones/{id}/saldo` | — | `SaldoOut` | JWT | Retorna saldoInscripcion | Mantener |
| POST | `/api/asignaciones/` | `AsignarPersonaIn` | `AsignarPersonaOut` | JWT | Crea AsignacionCupo, no Participacion | Mantener |
| POST | `/api/asignaciones/liberar` | `LiberarCupoIn` | `LiberarCupoOut` | JWT | Libera cup | Mantener |

### 4.2 Endpoints Nuevos

| Método | Ruta | Request | Response | Auth | Propósito |
|--------|------|---------|----------|------|---------|
| POST | `/inscripciones/{id}/pool/asignar` | `AsignarAEquipoIn` | `{participante}` | JWT + owner/admin | Consumir cupo disponible y crear Participacion en un solo paso atómico. Valida cup activo + R11 + roster. **Única autoridad del drop pool → equipo** |
| GET | `/inscripciones/{id}/pool` | — | `PoolOut` | JWT + owner/admin | Lista de InscripcionPersona sin `Participacion` activa, con `tiene_cupo_activo` y `motivo_bloqueo` (UI-safe) |
| GET | `/inscripciones/{id}/saldo` | — | `SaldoOut` | JWT | `contratados` / `pagados` / `asignados_pagados` / `disponibles_pagados` — fuente de verdad de la capacidad pagada libre |

#### Schema `AsignarAEquipoIn`
```python
class AsignarAEquipoIn(BaseSchema):
    equipo_destino_id: str
```

#### Schema `PoolParticipantesOut`
```python
class PoolParticipanteSchema(BaseSchema):
    id: str  # InscripcionPersona.id
    persona: PersonaSummarySchema
    estado: str  # A o R
    cupos_disponibles: int  # COUNT(AsignacionCupo activa para esta persona en esta inscripcion)
    puede_asignarse: bool  # cupos_disponibles > 0

class PoolParticipantesOut(BaseSchema):
    inscripcion_id: str
    saldo: SaldoInscripcionResult  # mismo que GET /saldo
    participantes: list[PoolParticipanteSchema]
    puede_agregar_mas: bool  # registrados < contratados
```

### 4.3 Códigos de Error (extensión de dominio existente)

| Código | Status HTTP | Mensaje público | Causa |
|--------|-------------|-----------------|-------|
| `CUPO_NO_ASIGNADO` | 409 | "Esta persona no tiene un cupo pagado asignado. Completa el pago primero." | Participacion requiere cup activo sin encontrar |
| `CUPO_AGOTADO` | 409 | "No hay cupos pagados disponibles." | disponibles_pagados = 0 |
| `PERSONA_YA_ASIGNADA` | 409 | "Esta persona ya tiene un cupo activo en esta inscripción." | Ya existe AsignacionCupo activa |
| `R11_DUPLICATE_PARTICIPATION` | 409 | "Esta persona ya participa en la misma disciplina de este evento." | Constraint R11 |
| `ROSTER_COMPLETO` | 409 | "El equipo alcanzó el número máximo de jugadores." | max_jugadores |
| `FECHA_LIMITE_EXCEDIDA` | 409 | "La fecha límite para modificaciones ha sido excedida." | Evento cerrado |

---

## 5. Orden de Validación y Errores

### 5.1 Endpoint `PATCH /participaciones/{id}/asignar-a-equipo`

```
1. extrair persona_id desde Participacion actual
2. extrair inscripcion_id desde Participacion actual
3. validar fecha_limite (Evento.puede_modificar)
4. obtener AsignacionCupo activa para (inscripcion_id, persona_id)
   → si no existe o origen compra != PAGADA → CUPO_NO_ASIGNADO
5. obtener equipo destino (equipo_destino_id)
6. validar disciplina del equipo pertenece al paquete
7. validar R11: no otra Participacion activa para (evento, disciplina, persona)
8. validar roster: count(Participacion activa en equipo_destino) < disciplina.max_jugadores
9. UPDATE Participacion.equipo = equipo_destino
10. RETURN ParticipacionOut
```

### 5.2 Endpoint `POST /inscripciones/{id}/personas` (con equipo_id)

```
1. validar fecha_limite
2. upsert Persona (por dni)
3. get_or_create InscripcionPersona (inscripcion, persona)
4. **NUEVO**: obtener AsignacionCupo activa para (inscripcion_id, persona_id)
   → si no existe → CUPO_NO_ASIGNADO
5. crear Participacion (R11 + roster)
6. sync AcreditacionEvento
7. RETURN ParticipacionOut
```

### 5.3 Endpoint `PATCH /participaciones/{id}/mover`

```
1. obtener Participacion actual
2. extraer inscripcion_id desde Participacion
3. extraer persona_id desde Participacion.inscripcion_persona.persona
4. **NUEVO**: obtener AsignacionCupo activa para (inscripcion_id, persona_id)
   → si no existe → CUPO_NO_ASIGNADO
5. obtener equipo destino
6. validar disciplina pertenece al paquete
7. R11 en equipo destino
8. roster max en equipo destino
9. UPDATE Participacion.equipo
10. RETURN ParticipacionOut
```

---

## 6. Matriz de Permisos

| Acción | Responsable (owner) | Delegado | Admin | Anónimo |
|--------|---------------------|----------|-------|---------|
| Ver pool de participantes | ✅ | ✅ | ✅ | ❌ |
| Agregar persona al pool | ✅ | ❌ | ✅ | ❌ |
| Asignar persona de pool a equipo | ✅ | ❌ | ✅ | ❌ |
| Mover participante entre equipos | ✅ (propia inscripción) | ❌ | ✅ | ❌ |
| Retirar persona (liberar cup) | ✅ | ❌ | ✅ | ❌ |
| Crear/confirmar inscripción | ✅ | ❌ | ✅ | ❌ |
| Override fiesta admin | ❌ | ❌ | ✅ | ❌ |
| Bloquear equipo | ❌ | ❌ | ✅ | ❌ |
| Cancelar inscripción | ✅ | ❌ | ✅ | ❌ |

**Reglas de negocio adicionales:**
- El **delegado** de la inscripción NO puede agregar personas ni asignar a equipos (solo puede visualizar).
- Operaciones de escritura requieren que el evento tenga `puede_modificar() = True`.
- Un usuario puede tener múltiplesInscripciones en el mismo evento solo si son paquetes distintos (UniqueConstraint en modelo).

---

## 7. Máquina de Estados UX Frontend

### 7.1 Estados de la Tarjeta de Participante

```
┌─────────────────────────────────────────────────────────┐
│  ESTADO: SIN_CUPO (pre-registrado, sin pago)         │
│  - Sin asa de drag                                     │
│  - Borde: dashed, color: gray-300                      │
│  - Badge: "Esperando pago" (amber)                    │
│  - Acciones visibles: editar, eliminar               │
│  - CTA: "Pagar" (si contratados > 0 y no pagados)   │
│  - Drag: deshabilitado                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ESTADO: CON_CUPO_DISPONIBLE (cupo pagado, en pool)  │
│  - Asa de drag visible                                 │
│  - Borde: solid, color: primary-200                  │
│  - Badge: "Listo para asignar" (green)              │
│  - Acciones: editar, eliminar, arrastrar a equipo   │
│  - Drag: habilitado → PUT /participaciones/{id}/mover │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ESTADO: EN_EQUIPO (participación activa)             │
│  - Asa de drag visible                                 │
│  - Borde: solid, color: primary-500                  │
│  - Muestra dentro de SortableEquipoCard               │
│  - Acciones: editar, retirer                           │
│  - Drag: habilitado → mover a otro equipo             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ESTADO: CUPOS_AGOTADOS (pool lleno, sin cupos)       │
│  - Sin asa de drag                                     │
│  - Borde: dashed, color: rose-200                    │
│  - Badge: "Cupos agotados" (rose)                    │
│  - Acciones: editar                                   │
│  - CTA: "Ampliar compra"                             │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Transiciones de Estado UI

```
[SIN_CUPO] --pago confirmado--> [CON_CUPO_DISPONIBLE]
[SIN_CUPO] --ampliar compra pagada--> [CON_CUPO_DISPONIBLE]
[CON_CUPO_DISPONIBLE] --drag a equipo--> [EN_EQUIPO]
[CON_CUPO_DISPONIBLE] --retirar persona--> [eliminado del pool]
[EN_EQUIPO] --liberar cup--> [CON_CUPO_DISPONIBLE] (cupo liberado vuelve al pool)
[EN_EQUIPO] --retirar persona de inscripción--> [eliminado]
[CUPOS_AGOTADOS] --ampliar compra pagada--> [CON_CUPO_DISPONIBLE]
```

### 7.3 Flags de Habilitación del Drag-and-Drop

```typescript
type DragEligibility = {
  puedeArrastrar: boolean;       // tiene AsignacionCupo activa
  mensajeBloqueo: string | null; // razón si no puede
  tipoBloqueo: 'SIN_CUPO' | 'FECHA_CERRADA' | 'ROSTER_COMPLETO' | null;
};
```

El `DndContext` en `InscripcionDetailView` debe consultar `DragEligibility` por cada participante antes de permitir el drop.

---

## 8. Concurrencia e Idempotencia

### 8.1 Race Conditions y Soluciones

| Escenario | Solución |
|-----------|----------|
| Dos requests concurrentes consumen el último cupo disponible | `SELECT_FOR_UPDATE` en `Compra` dentro de `transaction.atomic` en `CrearAsignacionesFlujo` (ya implementado, ver T14 test) |
| Pago duplicado (dos callbacks Izipay) | `ConfirmarPagoFlujo._confirmar_sync` es idempotente: si Compra ya PAGADA, retorna `already_confirmed=True` sin error |
| Drag-drop simultáneo de la misma persona a dos equipos | `mover_participacion_proceso` usa `transaction.atomic`; R11 UniqueConstraint previene doble participación activa |
| Dos calls concurrentes a `asignar_persona` para la misma persona | `AsignacionCupo` tiene constraint parcial única `(inscripcion, inscripcion_persona)` WHERE `estado=ACTIVA`; segundo call obtiene `PersonaYaAsignadaError` |
| Callback de pago llega antes de que el frontend muestre la página | El frontend consulta `GET /inscripciones/{id}/detalle` después de abrirse el modal de pago; TanStack Query refetchiza tras cierre del modal |

### 8.2 Idempotencia de Operaciones

| Operación | Key de idempotencia | Comportamiento duplicado |
|-----------|---------------------|------------------------|
| Confirmar pago | `orden_pago_id` | Segunda llamada retorna `already_confirmed=True` |
| Asignar persona a cup | `(inscripcion_id, persona_id)` + idempotency header | Si ya existe AsignacionCupo ACTIVA → `PersonaYaAsignadaError` |
| Mover participación | `participacion_id` | Segunda llamada es no-op (mover al mismo equipo) |
| Crear asignaciones post-pago | `compra_id` | `CrearAsignacionesFlujo` calcula asignaciones ya hechas y solo crea las faltantes |

---

## 9. Impactos de Migración de Datos

### 9.1 Registros Existentes Sin AsignacionCupo

Para inscripciones ya creadas con `InscripcionPersona` y `Participacion` sin `AsignacionCupo`:

**Opción recomendada: backfill automático + constraint**

1. Crear migración que para cada `Inscripcion` con al menos una `Compra.PAGADA`:
   - Calcular `pagados = SUM(cantidad)` de `CompraInscripcion` donde `Compra.estado=PAGADA`
   - Para cadapersona (`InscripcionPersona.estado=A`) sin `AsignacionCupo`:
     - Si `pagados - asignados < COUNT(personas_sin_asignacion)` → asignar en orden FIFO de `created_at`
     - Crear `AsignacionCupo(estado=ACTIVA, origen=primera_compra_pagada)`

2. Para personas pre-registradas en inscripciones sin compra pagada:
   - Dejar sin `AsignacionCupo`; el nuevo flujo las mostrará como `SIN_CUPO`

### 9.2 Constraint Nueva en Base de Datos

```python
# En AsignacionCupo.Meta.constraints
models.UniqueConstraint(
    fields=["compra", "estado"],
    condition=models.Q(estado=EstadoAsignacionCupoChoices.ACTIVA),
    name="unique_activa_compra_persona",
)
# Previene sobre-asignación desde la misma compra
```

### 9.3 Índices para Rendimiento

```python
# En AsignacionCupo
indexes = [
    models.Index(fields=["inscripcion", "estado"]),
    models.Index(fields=["compra", "estado"]),
    models.Index(fields=["inscripcion_persona", "estado"]),
]

# En Participacion — ya existe constraint parcial para R11
# Para queries de elegibilidad de drag-drop, agregar índice:
models.Index(fields=["persona", "evento", "disciplina", "estado"]),
```

---

## 10. Concerns de Seguridad

| Concern | Mitigación |
|---------|-----------|
| Usuario arrastra a persona sin cup a equipo | Backend valida `AsignacionCupo` activa en toda mutation de Participacion |
| Usuario modifica cup de otra inscripción | `AsignacionCupo.inscripcion` FK enforced; no cross-inscripción |
| Reingreso de persona ya asignada (misma disciplina, otro equipo) | R11 constraint previene en DB; servicio double-check |
| Overrides admin de fiesta revocados por sync | `sync_acreditacion_desde_compras` preserva overrides con `autorizacion_fiesta=BLOQUEADA/AUTORIZADA` |
| Exposición de QR de acceso | `codigo_qr` UUID v4 no adivinable; un solo uso por escaneo (ControlAcceso) |
| Precio alterado en frontend | Backend revalida `precio_unitario_cotizado` vs catálogo en `CrearInscripcionCompletaFlujo` |
| Cupos negative por bug de concurrencia | `SELECT_FOR_UPDATE` + constraint `COUNT(asignaciones) <= CompraInscripcion.cantidad` en servicio |

---

## 11. Matriz de Aceptación

| ID | Escenario | Resultado esperado | Validación |
|----|-----------|-------------------|------------|
| A01 | Crear inscripción + compra sin personas → GET detalle | Equipos visibles, `personas=[]`, `resumen_pago.estado_mensaje="Sin actividades de pago"` | UI muestra pool vacío |
| A02 | Agregar persona al pool (sin equipo_id) → GET detalle | Persona aparece en `personas` y pool, `cupos_disponibles=0` | Tarjeta bloqueada, badge "Esperando pago" |
| A03 | Intentar arrastrar persona sin cup a equipo | Backend拒绝 con `CUPO_NO_ASIGNADO`, UI muestra toast de error | Drag no procede |
| A04 | Confirmar pago con 3 personas pre-registradas, 10 cupos pagados | 3 `AsignacionCupo` creadas automáticamente, pool muestra 3 participantes como `CON_CUPO_DISPONIBLE` | Cards desbloqueadas |
| A05 | Arrastrar persona con cup a equipo | Backend crea/mueve `Participacion`, UI actualiza equipo roster | Persona aparece en equipo, pool decrementa |
| A06 | Mover persona entre equipos (con cup activo) | Backend mueve Participacion, R11 y roster validados | Persona en nuevo equipo |
| A07 | Mover persona sin cup activo entre equipos | Backend rechaza con `CUPO_NO_ASIGNADO` | Error 409 |
| A08 | T14: dos requests concurrentes consumen el último cupo | Solo una asignación succeeds, la otra obtiene `CUPO_AGOTADO` | DB tiene exactamente 1 AsignacionCupo |
| A09 | Agregar persona con cup a equipo lleno (max_jugadores) | Backend rechaza con `ROSTER_COMPLETO` | — |
| A10 | R11: misma persona en dos equipos de la misma disciplina | Backend rechaza con `R11_DUPLICATE_PARTICIPATION` | — |
| A11 | Drag-drop después de fecha límite | Backend rechaza con `FECHA_LIMITE_EXCEDIDA` | — |
| A12 | Re-ingreso: persona retirada de inscripción con cup libre | `asignar_persona` reactiva `AsignacionCupo` existente LIBERADA | Cup vuelve a estado ACTIVA |
| A13 | Admin bloquea fiesta → sync post-pago | Override BLOQUEADA preservado, no se sobreescribe | — |

---

## 12. Lotes de Aplicación Modulares (Apply Batches)

### Batch 1: Infraestructura de Datos
- Migración: agregar constraint `unique_activa_compra_persona` en `AsignacionCupo`
- Migración: índice en `Participacion(persona, evento, disciplina, estado)`
- Backfill script: crear `AsignacionCupo` para inscripciones con Compra.PAGADA existente

### Batch 2: Validación de Cup en Backend
- Modificar `ParticipacionCoreService.crear()`: agregar validación `obtener_asignacion_activa_por_persona`
- Modificar `ParticipacionCoreService.mover()`: misma validación
- Nuevo error `CupoNoAsignadoError` (código `CUPO_NO_ASIGNADO`, 409)
- Modificar `agregar_persona_flujo` para validar cup cuando `equipo_id` presente
- Modificar `mover_participacion_proceso` para validar cup

### Batch 3: Endpoint de Asignación Atómica
- Nuevo endpoint `PATCH /participaciones/{id}/asignar-a-equipo` (o reutilizar `mover` pero con validación)
- Nuevo endpoint `GET /inscripciones/{id}/pool` con `PoolParticipantesOut`
- Modificar `InscripcionSelector.get_by_id_with_details` para prefetch `asignaciones_cupo`

### Batch 4: Integración de Pago
- Modificar `ConfirmarPagoFlujo` para llamar `CrearAsignacionesFlujo` dentro de la transacción de confirmación
- Garantizar idempotencia: si ya se crearon asignaciones, no duplicar

### Batch 5: Frontend Pool UI
- Nueva sección "Pool de participantes" en `InscripcionDetailView`
- Nuevo componente `PoolParticipanteCard` con estados visuales por `DragEligibility`
- Modificar `SortableEquipoCard` para ocultar asa de drag cuando `!puedeArrastrar`
- Modificar `handleDragEnd` para consultar elegibilidad antes de permitir drop
- CTA "Pagar" / "Ampliar compra" visible según estado de saldo

### Batch 6: Tests y Verificación
- Tests de integración: A01–A13
- Test de concurrencia: T14 ya existe
- Test de idempotencia de confirmación de pago

---

## 13. Decisiones Pendientes (que no bloquean la exploración)

1. **¿Ampliaciones durante período de inscripción?** ¿Se pueden agregar personas pre-registradas cuando la compra está PENDIENTE (ampliación en curso)? El spec dice: "previo al pago, crear asignaciones ficticias para cupos no asignados." Recomendación: NO crear asignaciones ficticias; mantener `disponibles_pendientes = contratados - registrados` y mostrar "pendiente de pago" en pool.

2. **Reembolso parcial:** ¿Si se cancela una compra pagada, se revoca automáticamente las `AsignacionCupo` derivadas? Recomendación: sí, con `estado=REVOCADA` y `motivo="Cancelación de compra"`.

3. **Categoría del equipo en split/retiro:** Si se retira el último jugador de un equipo y luego se reingresa en otro equipo de distinta categoría, ¿cambia la categoría del equipo destino?

---

## 14. Cierre de la Fase 6 — Verificacion y Cierre (2026-10-24)

> Contrato definitivo de endpoints, permisos y flujo final:
> `doc_dev/CONTRATO_POOL_PARTICIPANTES_PAGO_PREVIO.md`

### 14.1 Matriz A01-A13 — resultado

Los 13 escenarios de la matriz de aceptacion (§11) quedaron ejecutados y en verde.
A01 y A13 recibieron cobertura **nueva** en esta fase (no existian a nivel HTTP);
A02-A12 ya estaban cubiertos por las suites de Fase 1 a Fase 4. La tabla de
trazabilidad test-por-test esta en el contrato, §10.

Dos desviaciones documentadas de la matriz original:

- **A01**: el plan espera `resumen_pago.estado_mensaje = "Sin actividades de pago"`
  tras crear inscripcion + compra. El flujo de §2.2 **siempre** crea una `Compra`
  PENDIENTE, asi que existe una actividad de pago pendiente y el mensaje
  correcto es `"Pago pendiente"`. `"Sin actividades de pago"` se devuelve cuando
  no hay ninguna compra.
- **A13**: el override `BLOQUEADA` ya se preservaba en
  `AcreditacionCoreService.sync_acreditacion_desde_compras` (return temprano), pero
  no habia test que lo probara a traves del sync post-pago. La Fase 6 lo cubre.

### 14.2 Defectos corregidos en Fase 6

| # | Defecto | Impacto | Correccion |
|---|---|---|---|
| 1 | `resumen_pago.disponible_pagado = max(0, total_pagado_cantidad - total_contratado)` — `total_contratado` incluye las compras PENDIENTE, luego el valor era **siempre 0** | La tarjeta "Resumen Comercial" mostraba "Disponible: 0 lugares" mientras el pool mostraba "Disponibles: N" en la misma pantalla | `max(0, total_pagado_cantidad - asignados_pagados)`, con `asignados_pagados` precargado por el selector (el presenter sigue sin ORM) |
| 2 | `GET /inscripciones/{id}/saldo` devolvia **HTTP 500** (`SynchronousOnlyOperation`): el orchestrator async hacia `await` sobre un core service sincrono con ORM | `saldo = null` en el frontend → los chips de capacidad no se renderizan y el CTA **Pagar/Ampliar nunca aparece**. El defecto estaba oculto porque el unico test del endpoint mockeaba el orchestrator | `await sync_to_async(self.asignacion_core.calcular_saldo_inscripcion)(inscripcion_id)`, igual que `InscripcionOrchestrator.obtener_inscripcion_detalle_proceso` |

Detalle completo en el contrato, §13.

### 14.3 Comandos ejecutados y resultados

```text
backend/.venv/Scripts/python.exe -m pytest modules/ -q
  → 325 passed, 1 failed (preexistente y ajeno al cambio)

DJANGO_SETTINGS_MODULE=config.settings.development python manage.py check
  → System check identified no issues (0 silenced)
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py makemigrations --check --dry-run
  → No changes detected
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py migrate
  → Applying salesianos_fest.0010 ... OK
    Applying salesianos_fest.0011 ... OK
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py migrate --check
  → exit 0 (sin migraciones pendientes)

frontend: npx tsc --noEmit   → exit 0
frontend: npm run build      → ✓ Compiled successfully (Next 16.2.9, 11 rutas)
frontend: node --experimental-strip-types check_pool_contrato_fase6.ts
  → 24 OK / 0 FAIL
```

### 14.4 Pendientes que NO bloquean el cierre

1. `modules/usuarios/tests/.../test_persona_busqueda.py::test_busqueda_endpoint_devuelve_forma_contractual`
   falla porque el envelope de exito incluye `message`. Es **preexistente**
   (`core/responses.py` sin cambios en este trabajo) y ajeno a esta feature.
2. `test_asignacion.py::test_saldo_sin_compras` sigue mockeando el orchestrator de
   saldo. La Fase 6 anade cobertura sin mock, pero el mock preexistente conviene
   retirarlo para que la regresion sea visible en ese archivo.
3. `test_inscripcion_presenter_phase3.py` fue actualizado: sus asserts codificaban
   la formula defectuosa. Los valores correctos se/an con `asignados_pagados`
   explicito en `make_result`.

---

*Documento generado por SDD Explore — 19 de octubre de 2026*
*Fase 6 (Verificacion y Cierre) — 24 de octubre de 2026*
