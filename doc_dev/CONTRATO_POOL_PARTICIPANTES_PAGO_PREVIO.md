# CONTRATO: Pool de Participantes con Pago Previo y Equipos — Salesianos FEST

> **Cambio SDD**: `participantes-pago-previo-equipos`
> **Estado**: Implementado (Fases 1–6). Verificado en Fase 6.
> **Persistencia**: `sdd/participantes-pago-previo-equipos/apply-progress` (Engram)
> **Planes**: `PLAN_PARTICIPANTES_PAGO_PREVIO_EQUIPOS.md` · `TAREAS_PARTICIPANTES_PAGO_PREVIO_EQUIPOS.md`

---

## 1. Propósito

Este documento fija el contrato **definitivo** de la feature: endpoints, permisos,
códigos de error, semántica de capacidad y flujo final. Es la referencia de la
Fase 6 (Verificación y Cierre) y sustituye a las hipótesis del plan original
cuando ambas difieren (ver §9 — Desviaciones).

---

## 2. Contrato de datos (invariante)

```text
InscripcionPersona: pre-registro en el pool. SIN equipo. NO es derecho.
Participacion:      ubicación deportiva EXCLUSIVA. Requiere AsignacionCupo ACTIVA.
AsignacionCupo:     derecho pagado. NO depende de Participacion.
```

| Entidad | Estados | Creación | Transición clave |
|---|---|---|---|
| `InscripcionPersona` | `A` activo, `R` retirado | Preregistro (Fase 2) | `R` al retirar de la inscripción |
| `Participacion` | `A` activa, `R` retirada | Solo con `AsignacionCupo` ACTIVA (Fase 2) | `R` al liberar el cupo |
| `AsignacionCupo` | `ACTIVA`, `LIBERADA`, `REVOCADA` | Al confirmar el pago (Fase 4) | `LIBERADA` al retirar · `REVOCADA` al cancelar compra |

**Invariante central**: una `Participacion` activa implica un `AsignacionCupo`
ACTIVA funded por una `Compra` PAGADA. Quien tiene cupo pagado puede estar en el
pool (aún sin equipo); quien tiene `Participacion` activa siempre tuvo cupo.

**Restricciones de base de datos** (Fase 1, migraciones `0010`/`0011`):

- `unique_activa_inscripcion_persona` — un solo cupo ACTIVO por persona/inscripción.
- `unique_activa_compra_persona` — un solo cupo ACTIVO por persona/compra.
- Índices: `(compra, estado)`, `(inscripcion_persona, estado)`, `(inscripcion, estado)`.
- Índice R11 en `Participacion(persona, evento, disciplina, estado)`.

---

## 3. Endpoints

Prefijo: `/api`.

### 3.1 Mutaciones del roster

| Método | Ruta | Auth | Body | Respuesta |
|---|---|---|---|---|
| POST | `/inscripciones/{id}/personas` | JWT + owner/admin | `AgregarPersonaIn` (**sin** `equipo_id`) | `201` `{participante}` |
| PATCH | `/inscripciones/{id}/personas/{persona_id}/retirar` | JWT + owner/admin | — | `200` `InscripcionPersonaOut` |
| POST | `/inscripciones/{id}/pool/asignar` | JWT + owner/admin | `AsignarAEquipoIn` | `200` `{participante}` |
| PATCH | `/participaciones/{id}/mover` | JWT + owner/admin | `MoverParticipacionIn` | `200` `ParticipacionOut` |

### 3.1.1 Pool primero (regla vigente)

> **El pool es el ÚNICO punto de alta de un participante.** Registrar y asignar
> son dos operaciones distintas y en ese orden.

- `POST /inscripciones/{id}/personas` **sin** `equipo_id` = **preregistro**:
  crea solo `InscripcionPersona`. Valida capacidad contratada y fecha límite,
  y **reclama el cupo pagado** disponible en la misma transacción.
- `POST /inscripciones/{id}/personas` **con** `equipo_id` + `persona_data` =
  **RECHAZADO** con `422 PARTICIPANTE_DEBE_PREREGISTRARSE`. Intentar crear una
  persona nueva dentro de un equipo saltaría el pre-registro y el reparto FIFO
  de cupos.
- `POST /inscripciones/{id}/personas` **con** `equipo_id` + `persona_id` =
  colocación de una persona **ya registrada** (ruta de compatibilidad para
  consumidores de la API). El frontend ya no la usa: la asignación se hace
  siempre por el selector.
- `POST /inscripciones/{id}/pool/asignar` es la **única** autoridad para el
  drop **pool → equipo**: crea la `Participacion` de forma atómica.
- `PATCH /participaciones/{id}/mover` sigue siendo la autoridad del drop
  **equipo → equipo** (el endpoint de pool *crea* una `Participacion`; reutilizarlo
  para alguien ya colocado dispararía `R11_DUPLICATE_PARTICIPATION`).

### 3.2 Lecturas del pool

| Método | Ruta | Auth | Respuesta |
|---|---|---|---|
| GET | `/inscripciones/{id}/pool` | JWT + owner/admin | `PoolOut` |
| GET | `/inscripciones/{id}/saldo` | JWT (autenticado) | `SaldoOut` |
| GET | `/inscripciones/{id}/detalle` | Público | `InscripcionDetailOut` |

`PoolOut`:

```jsonc
{
  "inscripcion_id": "uuid",
  "pool": [
    {
      "id": "uuid",              // InscripcionPersona.id
      "persona": { "id": "...", "nombre": "...", "nombres": "...",
                   "apellidos": "...", "numero_documento": "..." },
      "estado": "A",
      "created_at": "2026-...Z",
      "tiene_cupo_activo": true,   // ← autoridad de elegibilidad
      "motivo_bloqueo": null        // ← motivo UI-safe cuando no es elegible
    }
  ]
}
```

`motivo_bloqueo` es un texto **UI-safe** — nunca expone IDs internos, nombres de
constraints, datos de compra ni errores SQL. Valores en uso:

| `motivo_bloqueo` | Significado |
|---|---|
| `null` | Eligible (`tiene_cupo_activo = true`) |
| `"Cupo pendiente de asignar"` | Hay capacidad pagada libre; el derecho aún no se asignó |
| `"No hay cupos pagados disponibles"` | Capacidad pagada agotada |

El pool **excluye** a quien ya tiene `Participacion` activa (aparece en el grupo
colapsable "Ya asignados" del frontend, colgado del roster del equipo).

`SaldoOut`:

```jsonc
{ "inscripcion_id": "uuid", "contratados": 15, "pagados": 10,
  "asignados_pagados": 3, "disponibles_pagados": 7 }
```

---

## 4. Matriz de permisos

Actor: **owner** = responsable de la inscripción · **admin** = `is_staff` o
`is_superuser` · **delegado** = solo lectura.

| Acción | Owner | Delegado | Admin | Anónimo |
|---|:--:|:--:|:--:|:--:|
| Ver detalle de inscripción | ✅ | ✅ | ✅ | ✅ (público) |
| Ver pool (`GET /pool`) | ✅ | ❌ | ✅ | ❌ (401) |
| Ver saldo (`GET /saldo`) | ✅ | ✅ | ✅ | ❌ (401) |
| Preregistrar persona en el pool | ✅ | ❌ | ✅ | ❌ (401) |
| Asignar persona del pool a un equipo | ✅ | ❌ | ✅ | ❌ (401) |
| Mover participante entre equipos | ✅ | ❌ | ✅ | ❌ (401) |
| Retirar persona / liberar cupo | ✅ | ❌ | ✅ | ❌ (401) |
| Crear/ampliar compra, confirmar pago | ✅ | ❌ | ✅ | ❌ (401) |
| Override de fiesta / bloqueo de equipo | ❌ | ❌ | ✅ | ❌ (401) |

El control de ownership vive en `_check_ownership_or_admin()`
(`inscripcion_controller.py`): admin pasa siempre; el resto debe ser el
responsable de la inscripción. Usuario no relacionado → **403 `FORBIDDEN`**.

---

## 5. Códigos de error del dominio

| Código | HTTP | Origen | Causa |
|---|---|---|---|
| `PARTICIPANTE_DEBE_PREREGISTRARSE` | 422 | `ParticipanteDebePreregistrarseError` | `persona_data` + `equipo_id`: una persona nueva no puede crearse dentro de un equipo (regla pool primero) |
| `PERSONA_REQUIRED` | 422 | `PersonaDataRequiredError` | Falta `persona_id` **o** `persona_data` (XOR) |
| `CUPO_NO_ASIGNADO` | 409 | `CupoNoAsignadoError` | La `Participacion` requiere un cupo ACTIVA que no existe |
| `CUPO_AGOTADO` | 409 | `CupoAgotadoError` | No queda capacidad pagada disponible |
| `CUPO_CONTRATADO_EXCEDIDO` | 409 | `CupoContratadoExcedidoError` | Preregistro por encima de la capacidad contratada |
| `PERSONA_YA_ASIGNADA` | 409 | `PersonaYaAsignadaError` | Ya existe un `AsignacionCupo` ACTIVA para esa persona |
| `R11_DUPLICATE_PARTICIPATION` | 409 | `R11ViolationError` | Misma persona en dos equipos de la misma disciplina |
| `ROSTER_COMPLETO` | 409 | `RosterCompletoError` | El equipo alcanzó `max_jugadores` |
| `FECHA_LIMITE_EXCEDIDA` | 409 | `FechaLimiteExcedidaError` | El evento no admite modificaciones |
| `FORBIDDEN` | 403 | `ForbiddenError` | El actor no es owner ni admin |

### 5.1 Orden de validación (obligatorio)

```text
1. Autenticación        → 401
2. Ownership / admin    → 403
3. Guard de payload     → PARTICIPANTE_DEBE_PREREGISTRARSE (422)
                          (`persona_data` + `equipo_id` → el pool es el único
                           punto de alta; el guard es de dominio, corre antes
                           de abrir la transacción)
4. Fecha límite         → FECHA_LIMITE_EXCEDIDA
5. Pertenencia a la inscripción (persona/inscripcion_persona)
6. Cupo ACTIVA          → CUPO_NO_ASIGNADO
7. R11                  → R11_DUPLICATE_PARTICIPATION
8. Disciplina / categoría del equipo destino
9. Roster máximo        → ROSTER_COMPLETO
```

El orden importa: la **fecha límite** se evalúa **antes** del cupo, y el **cupo**
antes que **R11** y el roster. Un usuario con fecha vencida recibe
`FECHA_LIMITE_EXCEDIDA` aunque también le falte el cupo. El guard de payload
se evalúa **antes** que todo lo demás porque es una regla de forma de la
entrada: no depende del estado de la inscripción ni abre escritura alguna.

---

## 6. Flujo final

```text
[FASE 1 — Crear inscripción]
POST /inscripciones/completa/
  → Inscripcion(BORRADOR) + Compra(PENDIENTE) + OrdenPago + CompraInscripcion + Equipos
  → SIN personas

[FASE 2 — Pool sin cupos pagados]
POST /inscripciones/{id}/personas            (sin equipo_id)
  → crea SOLO InscripcionPersona(estado=A)
  → valida: fecha límite + capacidad contratada (CUPO_CONTRATADO_EXCEDIDO)
  → reclama el cupo pagado disponible (misma transacción, FIFO)
GET /inscripciones/{id}/pool
  → cada pre-registrado con `tiene_cupo_activo` + `motivo_bloqueo`
GET /inscripciones/{id}/saldo
  → {contratados, pagados, asignados_pagados, disponibles_pagados}

[FASE 2 bis — Auto-registro del responsable]
POST /inscripciones/{id}/personas            (sin equipo_id, con persona_id)
  → mismo pre-registro, reutilizando la Persona del usuario autenticado
  → NUNCA coloca al responsable en un equipo: eso es el selector

[FASE 3 — Confirmar el pago]
Callback → ConfirmarPagoFlujo  (idempotente por orden_pago_id)
  → Compra = PAGADA
  → DENTRO de la misma transacción:
       AsignacionCoreService.asignar_cupos_a_preregistrados()
         → AsignacionCupo(ACTIVA) para los pre-registrados, orden determinista
           (created_at, tipo_documento, numero_documento, id)
         → los excedentes quedan bloqueados, SIN derecho ficticio
       sync_acreditacion_desde_compras()
         → preserva el override admin (BLOQUEADA / AUTORIZADA)

[FASE 4 — Pool → Equipo]
POST /inscripciones/{id}/pool/asignar  {inscripcion_persona_id, equipo_id}
  → valida: ownership → fecha límite → cupo ACTIVA → R11 → roster
  → crea la Participacion ATÓMICAMENTE

[FASE 5 — Equipo → Equipo]
PATCH /participaciones/{id}/mover  {equipo_id}
  → valida: ownership → fecha límite → cupo ACTIVA → R11 → roster
  → mueve la Participacion

[FASE 6 — Retiro / reingreso / cancelación]
POST /inscripciones/{id}/personas/{persona_id}/retirar
  → Participacion(estado=R) + AsignacionCupo(LIBERADA) + recálculo de acreditación
Reingreso (asignar de nuevo)
  → reactiva la asignación LIBERADA si la compra de origen tiene capacidad libre
  → si no hay capacidad, el cupo queda LIBERADA y la persona sigue bloqueada
Cancelación de compra
  → REVOCA solo las asignaciones de esa compra
```

---

## 7. Semántica de capacidad y saldo

```text
contratados      = Σ CompraInscripcion.cantidad   (compras PENDIENTE + PAGADA, CANCELADA excluida)
pagados          = Σ CompraInscripcion.cantidad   (compras PAGADA)
asignados_pagados = COUNT(AsignacionCupo ACTIVA funded by a PAGADA compra of this inscripcion)
disponibles_pagados = pagados - asignados_pagados   (≥ 0)

INVARIANTE: disponibles_pagados ≥ 0
INVARIANTE: disponibles_pagados == resumen_pago.disponible_pagado
```

### 7.1 `resumen_pago.disponible_pagado` (corregido en Fase 6)

`resumen_pago.disponible_pagado` es la **misma magnitud** que
`saldo.disponibles_pagados`: los cupos pagados que todavía están libres. Se
calcula en el presenter como `total_pagado_cantidad - asignados_pagados`.

El selector carga `asignados_pagados` (conteo crudo de `AsignacionCupo` ACTIVA
funded por compras PAGADA de la inscripción) para que el presenter siga siendo un
transformador puro, sin acceso al ORM — ver `contract/api-wrapper-presenter-contract.md` §3.

> **Defecto corregido en Fase 6**: la fórmula anterior era
> `max(0, total_pagado_cantidad - total_contratado)`. Como `total_contratado`
> incluye las compras PENDIENTE, el resultado era **siempre 0**. En la pantalla
> del pool eso se veía como "Disponible: 0 lugares" junto al chip "Disponibles: N"
> del propio pool — dos números contradictivos en la misma vista.
> Regresión cubierta por `test_fase6_verificacion_pool.py`.

---

## 8. Contrato del frontend (pool)

### 8.1 El frontend NO calcula elegibilidad

El backend decide (`tiene_cupo_activo`); el frontend solo traduce a estado visual
(`frontend/src/features/inscripciones/utils/pool.estado.ts`):

| Condición del backend | Estado UI | Asignable a un equipo |
|---|---|:--:|
| `tiene_cupo_activo = true` | `listo` | ✅ (si hay equipos destino) |
| `estado_pool = "CUPO_POR_ASIGNAR"` | `cupo_por_asignar` | ❌ candado |
| `estado_pool = "SIN_CAPACIDAD"` | `bloqueado` | ❌ candado |
| `estado_pool = "ESPERANDO_PAGO"` | `esperando_pago` | ❌ candado |

Motivos desconocidos caen en `bloqueado` — el estado seguro: quien no tiene cupo
confirmado nunca puede asignarse a un equipo.

El frontend tampoco decide **dónde** se registra una persona: el alta ocurre
siempre en el pool (`frontend/src/features/inscripciones/utils/pool.primero.ts`
centraliza el copy del CTA y de los estados vacíos). El selector del equipo
sólo **asigna** personas ya registradas.

### 8.1.1 Pool primero en la UI

| Superficie | Antes (drag / colocación directa) | Ahora (pool primero) |
|---|---|---|
| Cabecera del pool | Botón secundario "Agregar al pool" | CTA **primario** "Agregar participante", `w-full` en móvil |
| Pool vacío | Sin acción posible | CTA **primario** "Agregar el primer participante" |
| Selector de equipo | Botón "Registrar nuevo participante" | **Eliminado** — el estado vacío apunta al pool |
| Tarjeta de equipo | Botón "Agregarme" (colocación directa) | **Eliminado** — sólo el selector |
| Modal de alta | Modos `equipo` y `pool` | **Sólo pool** (`AddParticipanteModal` es pool-only) |

El auto-registro del responsable se conserva como **pre-registro en el pool**
(`POST /inscripciones/{id}/personas` con `persona_id` y **sin** `equipo_id`):
no existe ningún atajo que coloque a alguien en un equipo directamente.

### 8.2 CTA Pagar / Ampliar

```text
sinCapacidadPagada = saldo.disponibles_pagados === 0
hayPagosPendientes = resumenPago.compras_pendientes > 0

bloqueados.length > 0 AND sinCapacidadPagada:
  ├─ hayPagosPendientes → CTA "Pagar"   (abre el modal Izipay existente;
  │                                     requiere inscripción VALIDADA
  │                                     y NEXT_PUBLIC_IZIPAY_ENABLED=true)
  └─ sin pagos pendientes → CTA "Ampliar" (aviso al Comité Organizador;
                            no existe endpoint de ampliación en el frontend)
```

### 8.3 Mutación atómica con rollback

`useAsignarParticipanteAEquipo` (pool → equipo, reutiliza
`POST /inscripciones/{id}/pool/asignar`):

1. `onMutate` — snapshot de pool + detalle; la persona sale del pool y entra al
   roster del equipo destino con un id optimista
   `optimistic:<equipo_id>:<inscripcion_persona_id>` (el id del equipo forma
   parte de la clave: un mismo cupo habilita a la persona en varias
   disciplinas).
2. `onError` — restauración EXACTA de ambos snapshots y `notify.error(getErrorMessage(error))`.
3. `onSuccess` — invalidación de `inscripcion-pool` + `inscripcion-detalle` +
   `inscripcion-saldo` + el **prefijo** `inscripcion-elegibles` (2 elementos:
   la asignación cambia la elegibilidad de todos los equipos de la inscripción).

El pre-registro en el pool (`usePreregistrarEnPool`) invalida las mismas
cuatro cachés: una persona recién pre-registrada debe poder asignarse de
inmediato, y el selector lee su propio endpoint (`…/equipos/{id}/elegibles`),
no el pool.

El drop **equipo → equipo** usa `PATCH /participaciones/{id}/mover` y también
muestra el mensaje real del backend (`getErrorMessage`), no
"Request failed with status code 409".

---

## 9. Desviaciones respecto del plan original

| # | Plan | Implementado | Motivo |
|---|---|---|---|
| 1 | "Todo drop usa la mutación atómica de Fase 3" | pool → equipo usa `POST /pool/asignar`; equipo → equipo usa `PATCH /participaciones/{id}/mover` | El endpoint de pool **crea** una `Participacion`; reutilizarlo sobre alguien ya colocado dispara `R11_DUPLICATE_PARTICIPATION` y rompería todo el arrastre entre equipos. El propio backend lo documenta como autoridad **exclusiva del pool** |
| 2 | `GET /inscripciones/{id}/detalle` público | público | Coherente con el plan §4.1 |
| 3 | A01 espera `resumen_pago.estado_mensaje = "Sin actividades de pago"` tras crear inscripción + compra | `"Pago pendiente"` | El flujo de §2.2 **siempre** crea una `Compra` PENDIENTE: existe una actividad de pago pendiente, así que "Sin actividades de pago" sería falso. `"Sin actividades de pago"` sí se devuelve cuando no hay ninguna compra |
| 4 | `disponible_pagado = total_pagado_cantidad - total_contratado` | `total_pagado_cantidad - asignados_pagados` | La fórmula original era siempre 0 (ver §7.1) |
| 5 | CTA "Ampliar compra" con endpoint | Aviso al Comité Organizador | No existe endpoint de ampliación en el frontend; no se inventó uno |
| 6 | `PATCH /participaciones/{id}/asignar-a-equipo` (Fase 3, §4.2) | `POST /inscripciones/{id}/pool/asignar` | Variante de ruta elegida en Fase 3; misma semántica (asignación atómica de un participante del pool) |

---

## 10. Matriz de aceptación A01–A13 (trazabilidad)

| ID | Escenario | Cobertura | Test |
|---|---|---|---|
| A01 | Inscripción + compra sin personas → detalle | Fase 6 | `test_a01_detalle_muestra_equipos_y_personas_vacias`, `test_a01_sin_compras_estado_mensaje_sin_actividades_de_pago`, `test_a01_pool_vacio_sin_participantes` |
| A02 | Preregistrar sin `equipo_id` → pool | Fase 2/3 | `test_preregistro_sin_equipo_id_permitido_cuando_hay_capacidad`, `test_preregistrar_en_pool_crea_solo_inscripcion_persona` |
| A03 | Asignar sin cupo → `CUPO_NO_ASIGNADO` | Fase 2/3 | `test_crear_participacion_sin_cupo_rechazado_cupo_no_asignado`, `test_agregar_persona_con_equipo_id_sin_cupo_rechazado`, `test_asignar_a_equipo_via_http_fails_without_cup` |
| A04 | Pago con 3 pre-registrados y 10 cupos → 3 asignaciones | Fase 4 | `test_pago_inicial_asigna_cupos_hasta_capacidad_pagada` |
| A05 | Arrastrar con cupo a un equipo | Fase 3 | `test_asignar_a_equipo_via_http_creates_participacion_atomically` |
| A06 | Mover con cupo activo entre equipos | Fase 2 | `test_mover_participacion_con_cupo_activo_permitido` |
| A07 | Mover sin cupo activo → `CUPO_NO_ASIGNADO` | Fase 2 | `test_mover_participacion_sin_cupo_rechazado` |
| A08 | Dos requests concurrentes consumen el último cupo | Fase 1 | `test_t14_concurrent_ultimo_cupo_desde_dos_requests` |
| A09 | Equipo lleno → `ROSTER_COMPLETO` | Fase 2/3 | `test_roster_lleno_impide_agregar_mas_jugadores`, `test_asignar_a_equipo_roster_full_blocks` |
| A10 | R11 → `R11_DUPLICATE_PARTICIPATION` | Fase 2 | `test_r11_impide_dos_participaciones_activas_misma_disciplina` |
| A11 | Drag después de la fecha límite | Fase 2 | `test_fecha_limite_excedida_impide_agregar_persona`, `test_agregar_persona_fecha_limite_excedida_bloquea_antes_de_cupo` |
| A12 | Reingreso reactiva el cupo liberado | Fase 4 | `test_reingreso_reactiva_el_cupo_liberado`, `test_reingreso_sin_capacidad_queda_bloqueado` |
| A13 | Override admin BLOQUEADA preservado tras el sync post-pago | Fase 6 | `test_a13_override_bloqueada_preservado_tras_sync_post_pago`, `test_a13_sync_preserva_override_bloqueada_con_asignacion_activa` |
| A14 | `persona_data` + `equipo_id` → `422 PARTICIPANTE_DEBE_PREREGISTRARSE` (pool primero) | Pool primero | `test_persona_data_con_equipo_id_es_rechazado_con_422`, `test_el_mensaje_publico_del_guard_no_expone_identificadores`, `test_el_guard_no_escribe_nada`, `test_el_guard_rechaza_en_el_dominio_antes_de_la_transaccion` |
| A15 | El pre-registro (sin `equipo_id`) sigue funcionando y reclama el cupo pagado | Pool primero | `test_preregistro_sin_equipo_id_sigue_funcionando`, `test_el_autoregistro_del_responsable_va_al_pool`, `test_el_preregistro_reclama_el_cupo_pagado`, `test_persona_existente_con_equipo_id_sigue_funcionando` |

**Concurrencia e idempotencia adicionales**:
`test_t14_concurrent_ultimo_cupo_desde_dos_requests` (último cupo),
`test_t15_concurrent_qr_scans_simultaneos` (escaneo QR),
`test_pago_repetido_es_idempotente` y `test_confirmar_pago_idempotente`
(idempotencia de la confirmación de pago).

---

## 11. Verificación (Fase 6)

```text
backend/.venv/Scripts/python.exe -m pytest modules/ -q
  → 325 passed, 1 failed  (el fallo es preexistente y ajeno al cambio — ver §12)

manage.py check                     → System check identified no issues
manage.py makemigrations --check    → No changes detected
manage.py migrate                   → 0010, 0011 aplicadas (sin pendientes)
manage.py migrate --check           → exit 0

frontend: npx tsc --noEmit          → exit 0
frontend: npm run build             → ✓ Compiled successfully (Next 16.2.9)
frontend: node --experimental-strip-types check_pool_contrato_fase6.ts
                                    → 24 OK / 0 FAIL
```

---

## 12. Deuda técnica conocida

| # | Ítem | Impacto | Estado |
|---|---|---|---|
| 1 | `modules/usuarios/tests/integration/test_persona_busqueda.py::test_busqueda_endpoint_devuelve_forma_contractual` falla: el envelope de éxito incluye `message` y el test exige `{success, data, error}` | Ajeno a esta feature (`core/responses.py` sin cambios en este trabajo) | **Preexistente** — falla igual en HEAD |
| 2 | `test_asignacion.py::test_saldo_sin_compras` **mockea** `AsignacionOrchestrator.obtener_saldo` ("to avoid async/sync issues in test") | El mock ocultaba el defecto de la Fase 6 (§13) | La Fase 6 añade cobertura **sin mock** (`test_fase6_verificacion_pool.py`) |
| 3 | `PoolParticipantesSeccion` depende de `saldo` para el CTA; si la query de saldo falla, `saldo = null` y el CTA no se renderiza | Degradación silenciosa | Corregida la causa raíz en Fase 6 (§13) |
| 4 | El frontend no tiene runner de tests | La regresión de `pool.estado.ts` se cubre con un script determinista, no con un framework | Fuera de alcance |
| 5 | `modules/salesianos_fest/tests/integration/test_cotizacion.py::test_obtener_precio_vigente_respeta_fechas_no_fallback` falla entre 19:00 y 23:59 local (UTC-5): `CotizacionFlujo` usa `timezone.now().date()` (UTC) y el fixture usa `date.today()` (local) | Ajeno al pool (no importa ningún módulo cambiado) | **Preexistente** — corregido en otro cambio: usar `timezone.localdate()` |
| 6 | El guard de pool primero (`422 PARTICIPANTE_DEBE_PREREGISTRARSE`) es un error de **VALIDACIÓN** en un flujo que, por lo demás, responde `409` | Bajo impacto: es la única combinación rechazada y el mensaje público guía al pool | Aceptado — el guard es de forma del payload, no de estado de negocio |

---

## 13. Defectos corregidos en Fase 6

### 13.1 `resumen_pago.disponible_pagado` siempre 0

**Causa**: `max(0, total_pagado_cantidad - total_contratado)`; como
`total_contratado` incluye las compras PENDIENTE, la resta nunca era positiva.

**Impacto**: la tarjeta "Resumen Comercial" mostraba siempre "Disponible: 0
lugares" mientras el pool mostraba "Disponibles: N" — dos números
contradictorios en la misma pantalla. No afectaba al CTA (que usa `/saldo`),
pero sí al estado de capacidad pagado mostrado al usuario.

**Corrección**: `disponible_pagado = max(0, total_pagado_cantidad - asignados_pagados)`,
con `asignados_pagados` precargado por el selector (el presenter sigue sin ORM).

**Archivos**: `inscripcion_results.py`, `inscripcion_selector.py`,
`inscripcion_presenter.py`, `inscripcion_schemas.py`, `inscripcion.schema.ts`.

**Regresión**: `test_fase6_verificacion_pool.py` (6 tests) +
`test_inscripcion_presenter_phase3.py` (actualizado).

### 13.2 `GET /inscripciones/{id}/saldo` → HTTP 500

**Causa**: `AsignacionOrchestrator.obtener_saldo` awaits
`AsignacionCoreService.calcular_saldo_inscripcion`, que es **síncrono** y hace
acceso al ORM. Dentro del event loop del controller async eso lanza
`SynchronousOnlyOperation` → 500. El patrón correcto (`sync_to_async`) sí se usaba
en los orchestrators hermanos, pero no en este.

**Impacto**: `saldo` llega `null` al frontend → los chips de capacidad no se
renderizan y el CTA **"Pagar"/"Ampliar" nunca aparece**. Los participantes
bloqueados en el pool se quedan sin señal para pagar. El defecto estaba oculto
porque el único test del endpoint mockeaba el orchestrator.

**Corrección**: `await sync_to_async(self.asignacion_core.calcular_saldo_inscripcion)(inscripcion_id)`,
igual que `InscripcionOrchestrator.obtener_inscripcion_detalle_proceso`.

**Archivo**: `asignacion_orchestrator.py`.

**Regresión**: `test_fase6_verificacion_pool.py` (los 4 tests que leen `/saldo`
sin mock).

---

## 14. Cambio "pool primero" (2026-10-24)

Cambio SDD `pool-first-participant-registration-ux`. Sin migración, sin cambio
de modelo y **sin tocar la semántica comercial de los cupos** ni
`Inscripcion.estado`.

### 14.1 Regla aplicada

> El alta y el pre-registro de un participante ocurren **sólo en el pool**.
> Los equipos **sólo asignan** participantes elegibles ya registrados.

### 14.2 Backend

| Elemento | Cambio |
|---|---|
| `ParticipanteDebePreregistrarseError` | Nueva excepción de dominio, código estable `PARTICIPANTE_DEBE_PREREGISTRARSE`, HTTP **422** (categoría Validation) |
| `InscripcionPersonaCreateData._no_equipo_con_persona_data` | **Guard de entrada** de dominio: `persona_data` + `equipo_id` → error, antes de abrir la transacción |
| `core/exceptions.py` | `UnprocessableEntityError` (base 422) + entrada del catálogo público `PARTICIPANTE_DEBE_PREREGISTRARSE` |
| `AgregarPersonaIn` / `agregar_persona` | Docstrings actualizados: el endpoint es el pre-registro; `equipo_id` sólo admite personas ya registradas |
| Ownership | Sin cambios: `check_ownership_or_admin` sigue evaluándose **antes** del guard |

Rutas y semántica comercial **sin cambios**: `POST /{id}/personas` (sin
`equipo_id`), `POST /{id}/pool/asignar`, `GET /{id}/pool`, `GET /{id}/saldo`,
`GET /{id}/equipos/{id}/elegibles`.

### 14.3 Frontend

| Elemento | Cambio |
|---|---|
| `PoolParticipantesSeccion` | CTA **primario** "Agregar participante" en cabecera (`w-full` en móvil) + CTA en el pool vacío + "Agregarme al pool" (pre-registro, no colocación) |
| `SelectorParticipanteModal` | Eliminado el botón "Registrar nuevo participante"; el estado vacío apunta al pool |
| `EquipoCard` | Eliminado el botón "Agregarme"; el roster vacío guía al pool y luego al selector |
| `AddParticipanteModal` | **Pool-only** (se eliminan `modo`, `equipoId`, `equipoLabel` y los campos de equipo) |
| `InscripcionDetailView` | Eliminados los borradores por equipo, el modal de alta por equipo y el modal de auto-registro |
| `inscripcion.service.ts` | Eliminada `agregarParticipantesAEquipo` y sus tipos |
| `pool.primero.ts` (nuevo) | Copy del CTA y de los estados vacíos (pool primero) |
| `pool.preregistro.ts` | `buildPreregistroSelfPayload()` — auto-registro del responsable **sin** `equipo_id` |
| `usePreregistrarEnPool` | Invalida también el prefijo `inscripcion-elegibles` |

Eliminados: `AgregarmeModal.tsx`, `useAgregarParticipantes.ts`.

### 14.4 Verificación

```text
backend
  pytest modules/salesianos_fest/tests/integration/test_pool_first_registration_guard.py -q
      → 10 passed
  pytest modules/salesianos_fest/tests/ -q    → 292 passed, 1 failed (preexistente #5)
  pytest modules/ -q                           → 424 passed, 2 failed (preexistente #5 y #1)
  manage.py check                              → System check identified no issues
  manage.py makemigrations --check --dry-run   → No changes detected (SIN MIGRACIÓN)

frontend
  node --experimental-strip-types --test …pool.estado.test.ts …asignacion.estado.test.ts
      …pool.primero.test.ts …pool.preregistro.test.ts   → 27 passed, 0 failed
  npx tsc --noEmit                             → exit 0
  npm run build                                → ✓ Compiled successfully (Next 16.2.9, 11 routes)
  npx biome check <archivos tocados>           → sólo ruido preexistente (§12)
```

---

*Documento generado en la Fase 6 — Verificación y Cierre — del cambio SDD
`participantes-pago-previo-equipos`; §14 añadido por el cambio SDD
`pool-first-participant-registration-ux`.*
