# Informe de Contraste Frontend vs Backend — Salesianos FEST

**Fecha:** 2026-10-18
**Proyecto:** Salesianos
**Modo:** Auditoría de contrato read-only
**Artifact:** `sdd/salesianos-fest-frontend-backend-contract-audit/explore`

---

## Resumen Ejecutivo

| Área | Estado | Severidad |
|------|--------|----------|
| Creación de inscripción (nested payload) | 🔴 **BLOQUEANTE** | CRITICAL |
| Endpoints faltantes en backend | 🔴 **BLOQUEANTE** | CRITICAL |
| Flujo de participante (mover/editar) | 🔴 **BLOQUEANTE** | CRITICAL |
| Consentimientos por participante | 🟡 **DEPENDIENTE DEL NUEVO FLUJO** | HIGH |
| Estados de inscripción en frontend | 🟡 **INCONSISTENTE** | HIGH |
| Endpoint GET /inscripciones/ | 🟡 **NO EXISTE** | HIGH |
| Campo `delegado_id` en create | 🟡 **INCONSISTENTE** | MEDIUM |
| Schema de respuesta InscripcionOut | 🟡 **CAMPO EXTRA** | LOW |

---

## 1. Ruta de la Inscripción (Inscription Form Flow)

### 1.1 Flujo Actual Frontend

```
/inscripcion (page.tsx)
  └─> <InscripcionClientShell />
        ├─> Step 1: Selection (paquete, promocion)
        ├─> Step 2: Equipos (disciplinas + participantes)
        │     └─> ParticipanteForm ( DNI lookup, datos personales)
        └─> Submit: toBackendPayload() => POST /inscripciones/
```

**Archivo:** `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts:90-120`

```typescript
export function toBackendPayload(data, evento_id, responsable_id): InscripcionBackendPayload {
  return {
    evento_id,
    responsable_id,
    paquete_id: data.paquete_id,
    promocion_id: data.promocion_id,
    fusion_promocion_id: data.fusion_promocion_id ?? null,
    estado: "BORRADOR",
    equipos: data.equipos.map((eq) => ({
      disciplina_id: eq.disciplina_id,
      categoria_id: null,
      nombre: eq.nombre,
      participantes: eq.participantes.map((p) => ({
        tipoDocumento: p.tipoDocumento,
        numeroDocumento: p.numeroDocumento,
        nombres: p.nombres,
        apellidos: p.apellidos,
        genero: p.genero,
        telefono: p.telefono ?? null,
        whatsapp: p.whatsapp ?? null,
        rol: p.rol ?? "JUGADOR",
        talle_camiseta: p.talle_camiseta ?? null,
        notas: p.notas ?? null,
      })),
    })),
  };
}
```

### 1.2 Backend Expected Payload

**Archivo:** `backend/modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py:63-73`

```python
class CrearInscripcionIn(BaseSchema):
    evento_id: str
    responsable_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    estado: str = "BORRADOR"
    observacion: str = ""
```

### 1.3 🔴 CRITICAL MISMATCH

| Campo | Frontend (`InscripcionBackendPayload`) | Backend (`CrearInscripcionIn`) |
|-------|--------------------------------------|-------------------------------|
| Nested `equipos[]` | ✅ Envía `[{disciplina_id, nombre, participantes[]}]` | ❌ No acepta nested arrays |
| `delegado_id` | ❌ No lo envía | ✅ Lo espera |
| `observacion` | ❌ No la envía | ✅ La espera |
| Participantes inline | ✅ Inline en `equipos[].participantes[]` | ❌ No existen en este schema |

**El frontend envía un payload con equipos Y participantes anidados. El backend solo acepta campos planos de inscripción.**

Además, cada participante del formulario contiene datos personales, mientras que el endpoint existente exige un `persona_id` ya creado. El flujo corregido debe resolver o crear la Persona antes de agregarla a la inscripción.

---

## 2. Matriz de Rutas — Frontend vs Backend

### 2.1 Catálogo (públicas)

| Frontend Hook | Frontend URL | Backend Route | Método | Auth | Estado |
|---------------|--------------|--------------|--------|------|--------|
| `usePaquetes()` | — | `GET /catalogo/paquetes/` | GET | None | ✅ MATCH |
| `usePaqueteDisciplinas()` | — | `GET /catalogo/paquetes/{id}/` | GET | None | ✅ MATCH |
| `useDisciplinas()` | — | `GET /catalogo/disciplinas/` | GET | None | ✅ MATCH |
| `useCategorias()` | — | `GET /catalogo/categorias/` | GET | None | ✅ MATCH |
| `usePromociones()` | — | `GET /catalogo/promociones/` | GET | None | ✅ MATCH |

### 2.2 Inscripción

| Frontend Service | Frontend Usage | Backend Route | Método | Auth | Estado |
|------------------|----------------|---------------|--------|------|--------|
| `createInscripcion()` | `POST /inscripciones/` | `POST /inscripciones/` | POST | None | ⚠️ Payload mismatch |
| `getMisInscripciones()` | `GET /inscripciones/` | `GET /inscripciones/` | GET | None | 🔴 NO EXISTE |
| `getInscripcionDetalle()` | `GET /inscripciones/{id}/detalle` | `GET /inscripciones/{id}/detalle` | GET | None | ✅ MATCH |
| — | — | `PATCH /inscripciones/{id}` | PATCH | None | ✅ Existe |
| — | — | `POST /inscripciones/{id}/personas` | POST | None | ✅ Existe |
| — | — | `PATCH /inscripciones/{id}/personas/{id}/retirar` | PATCH | None | ✅ Existe |

### 2.3 Equipos y Participaciones

| Frontend Service | Frontend Usage | Backend Route | Método | Auth | Estado |
|------------------|----------------|---------------|--------|------|--------|
| — | — | `POST /equipos/` | POST | None | ✅ Existe |
| — | — | `GET /equipos/{id}` | GET | None | ✅ Existe |
| — | — | `GET /equipos/inscripcion/{id}` | GET | None | ✅ Existe |
| `agregarParticipantesAEquipo()` | `POST /inscripciones/{id}/personas` | `POST /inscripciones/{id}/personas` | POST | None | ✅ MATCH |
| `editarParticipante()` | `PATCH /inscripciones/{id}/participantes/{id}` | ❌ NO EXISTE | PATCH | — | 🔴 NO EXISTE |
| `moverParticipante()` | `PATCH /inscripciones/{id}/participantes/{id}/mover` | ❌ NO EXISTE | PATCH | — | 🔴 NO EXISTE |
| `eliminarParticipante()` | `DELETE /inscripciones/{id}/participantes/{id}` | ❌ NO EXISTE | DELETE | — | 🔴 NO EXISTE |

### 2.4 Compras y Pagos

| Frontend Service | Frontend Usage | Backend Route | Método | Auth | Estado |
|------------------|----------------|---------------|--------|------|--------|
| (en inscripcion.service.ts) | `POST /compras/` | `POST /compras/` | POST | JWT | ✅ MATCH |
| — | `GET /compras/{id}` | `GET /compras/{id}` | GET | JWT | ✅ MATCH |
| — | `GET /compras/inscripciones/{id}/compras` | `GET /compras/inscripciones/{id}/compras` | GET | JWT | ✅ MATCH |
| — | `POST /compras/{id}/iniciar-pago` | `POST /compras/{id}/iniciar-pago` | POST | JWT | ✅ MATCH |
| — | `POST /compras/confirmar-pago` | `POST /compras/confirmar-pago` | POST | JWT | ✅ MATCH |

### 2.5 Asignaciones y Acreditación

| Frontend Service | Frontend Usage | Backend Route | Método | Auth | Estado |
|------------------|----------------|---------------|--------|------|--------|
| — | `POST /asignaciones/` | `POST /asignaciones/` | POST | JWT | ✅ MATCH |
| — | `POST /asignaciones/liberar` | `POST /asignaciones/liberar` | POST | JWT | ✅ MATCH |
| — | `GET /asignaciones/{id}` | `GET /asignaciones/{id}` | GET | JWT | ✅ MATCH |
| — | `GET /asignaciones/inscripciones/{id}/asignaciones` | `GET /asignaciones/inscripciones/{id}/asignaciones` | GET | JWT | ✅ MATCH |
| — | `GET /inscripciones/{id}/saldo` | `GET /inscripciones/{id}/saldo` | GET | JWT | ✅ MATCH |
| — | `GET /acreditaciones/{evento}/{persona}` | `GET /acreditaciones/{evento_id}/{persona_id}` | GET | JWT | ✅ MATCH |
| — | `PATCH /acreditaciones/{evento}/{persona}/override-fiesta` | `PATCH /acreditaciones/{evento_id}/{persona_id}/override-fiesta` | PATCH | JWT | ✅ MATCH |
| — | `POST /acreditaciones/{evento}/{persona}/generar-qr` | `POST /acreditaciones/{evento_id}/{persona_id}/generar-qr` | POST | JWT | ✅ MATCH |
| — | `POST /acceso/registrar` | `POST /acceso/registrar` | POST | JWT | ✅ MATCH |

---

## 3. Matriz de Schemas y Payloads

### 3.1 InscripcionCreate Flow

| Campo | Frontend Zod/TS | Backend Schema | Observación |
|-------|-----------------|---------------|------------|
| `evento_id` | ✅ En toBackendPayload | ✅ CrearInscripcionIn | — |
| `responsable_id` | ✅ En toBackendPayload | ✅ CrearInscripcionIn | — |
| `paquete_id` | ✅ En toBackendPayload | ✅ CrearInscripcionIn | — |
| `promocion_id` | ✅ En toBackendPayload | ✅ CrearInscripcionIn | — |
| `fusion_promocion_id` | ✅ En toBackendPayload | ✅ CrearInscripcionIn | — |
| `delegado_id` | ❌ No se envía | ✅ CrearInscripcionIn | **Gap** |
| `estado` | ✅ "BORRADOR" | ✅ Valor por defecto | — |
| `observacion` | ❌ No se envía | ✅ CrearInscripcionIn | **Gap** |
| `equipos[]` | ✅ Nested array | ❌ No existe | **CRITICAL MISMATCH** |
| `participantes[]` | ✅ Inline en equipos | ❌ No existe | **CRITICAL MISMATCH** |

### 3.2 Backend Response — InscripcionOut vs Frontend InscripcionOut

| Campo Backend | Tipo | Frontend Usa | Observación |
|--------------|------|--------------|-------------|
| `id` | string | ✅ | — |
| `evento_id` | string | ✅ | — |
| `evento_nombre` | string | ✅ | — |
| `responsable_id` | string | ✅ | — |
| `responsable_nombre` | string | ✅ | — |
| `paquete_id` | string | ✅ | — |
| `paquete_nombre` | string | ✅ | — |
| `promocion_id` | string | ✅ | — |
| `promocion_nombre` | string | ✅ | — |
| `fusion_promocion_id` | string\|null | ✅ | — |
| `delegado_id` | string\|null | ✅ | — |
| `estado` | string | ✅ | — |
| `observacion` | string | ✅ | — |
| `created_at` | string | ✅ | — |
| `cantidad_equipos` | int (computed) | ✅ | En frontend service |
| `cantidad_participantes` | int (computed) | ✅ | En frontend service |

---

## 4. Estados de Inscripción

### Frontend Dashboard (`dashboard/page.tsx:29-89`)

```typescript
type EstadoInscripcion = "CONFIRMADA" | "PENDIENTE" | "PAGO_PENDIENTE" | "PAGADA" | "CANCELADA" | string;
```

### Backend Model (`domain/models/inscripcion.py`)

```python
class EstadoInscripcionChoices(models.TextChoices):
    BORRADOR = "BORRADOR", "Borrador"
    RECIBIDA = "RECIBIDA", "Recibida"
    EN_REVISION = "EN_REVISION", "En revisión"
    OBSERVADA = "OBSERVADA", "Observada"
    VALIDADA = "VALIDADA", "Validada"
    CONFIRMADA = "CONFIRMADA", "Confirmada"
    RECHAZADA = "RECHAZADA", "Rechazada"
    CANCELADA = "CANCELADA", "Cancelada"
```

### 🟡 INCONSISTENCY

| Estado Frontend | Estado Backend | Notas |
|-----------------|----------------|-------|
| PENDIENTE | BORRADOR, RECIBIDA | Frontend no tiene BORRADOR/RECIBIDA |
| PAGO_PENDIENTE | No existe | ⚠️ Estado mixto (inscripción + compra) |
| PAGADA | No existe | ⚠️ El pago es Compra, no Inscripcion |
| CONFIRMADA | CONFIRMADA | ✅ |
| CANCELADA | CANCELADA | ✅ |

**Problema:** `PAGO_PENDIENTE` y `PAGADA` son estados de frontend que mezclan `Inscripcion.estado` con `Compra.estado`. El backend los maneja separadamente (spec inv19).

---

## 5. Campos Faltantes en Backend — Endpoints que el Frontend Llama pero No Existen

### 🔴 CRITICAL — Estas llamadas fallarán en runtime

| Frontend Call | Endpoint Llamado | Problema |
|--------------|------------------|----------|
| `getMisInscripciones()` | `GET /inscripciones/` | El backend solo tiene `POST /`, `GET /{id}`, `GET /{id}/detalle`, `PATCH /{id}` |
| `editarParticipante()` | `PATCH /inscripciones/{id}/participantes/{id}` | No existe endpoint |
| `moverParticipante()` | `PATCH /inscripciones/{id}/participantes/{id}/mover` | No existe endpoint |
| `eliminarParticipante()` | `DELETE /inscripciones/{id}/participantes/{id}` | No existe endpoint |

**Nota:** El backend tiene `PATCH /participaciones/{id}/retirar` que solo cambia estado a RETIRADA. No hay endpoint para editar, mover o eliminar participaciones.

---

## 6. Consentimientos por Participante

### Estado Actual

- ✅ `Persona` ya no tiene flags globales de consentimiento.
- ✅ `AceptacionInscripcion` existe en `domain/models/aceptacion_inscripcion.py`
- ✅ Tests para aceptaciones existen en `test_inscripcion.py`
- ⚠️ El formulario valida declaraciones globales, pero el backend las registra por participante en `POST /inscripciones/{id}/personas` mediante `aceptaciones`.

### Problema

Phase 6 está aplicado en el backend. El formulario debe enviar las aceptaciones al alta de cada participante, después de crear la inscripción y resolver su `persona_id`.

---

## 7. Mismatches de Campo y Naming

| Área | Frontend | Backend | Severidad |
|------|----------|---------|----------|
| `rol` en participante | `"JUGADOR"` (string) | `"J"` (CharField 1 char) | 🟡 INCOMPATIBLE |
| `talle_camiseta` | `talle_camiseta` | `talla_camiseta` | 🔴 TYPO MISMATCH |
| `nombre` en Persona | `nombre` (full name) | `nombres` + `apellidos` separados | 🟡 ESTRUCTURA DIFERENTE |

---

## 8. Mapeo de Archivos Afectados

### Frontend (requiere cambios)

| Archivo | Cambio Necesario |
|---------|------------------|
| `features/inscripciones/schemas/inscripcion.schema.ts` | Cambiar estructura de payload — no enviar equipos/participantes inline |
| `features/inscripciones/services/inscripcion.service.ts` | Agregar endpoints faltantes (o eliminar funciones que no existen) |
| `features/inscripciones/hooks/useCreateInscripcion.ts` | Cambiar flujo — crear inscripción sin equipos primero |
| `features/inscripciones/views/InscripcionClientShell.tsx` | Flujo de creación en 2 pasos: crear inscripción, luego agregar equipos y participantes |
| `app/(app)/dashboard/page.tsx` | Eliminar estados `PAGO_PENDIENTE` y `PAGADA` del frontend |

### Backend (requiere cambios)

| Archivo | Cambio Necesario |
|---------|------------------|
| `presentation/controllers/inscripcion_controller.py` | Agregar endpoint `GET /inscripciones/` (lista propias del usuario) |
| `presentation/schemas/inscripcion_schemas.py` | Crear schema para crear inscripción + equipos + participantes en una llamada, O separar en múltiples llamadas |
| `domain/services/flujos/crear_inscripcion_flujo.py` | Implementar lógica de crear equipos y participantes si se quiere bulk create |
| `presentation/controllers/participacion_controller.py` | Agregar endpoints PATCH/DELETE para participacion |
| Flujo de persona | Resolver o crear una `Persona` antes de llamar a `POST /inscripciones/{id}/personas` |

---

## 9. Diagrama de Secuencia — Flujo de Inscripción Actual vs Requerido

### Actual (INCORRECTO)

```
Frontend                    Backend
   |                           |
   | POST /inscripciones/      |
   | {evento_id, paquete_id,   |
   |  promocion_id,           |
   |  equipos: [{              |
   |    disciplina_id,          |
   |    participantes: [...]    |
   |  }]}                      |
   |-------------------------->|
   |   422 Validation Error    |
   |   "equipos no es valido"  |
```

### Correcto (Requerido)

**Opción A: Bulk create** — Backend acepta nested payload
```
Frontend                    Backend
   |                           |
   | POST /inscripciones/      |
   | {evento_id, paquete_id,   |
   |  promocion_id,           |
   |  equipos: [{              |
   |    disciplina_id,          |
   |    participantes: [...]    |
   |  }]}                      |
   |-------------------------->|
   |   201 Created             |
   |   {id, ...}              |
```

**Opción B: Multi-step** — Crear inscripción, luego crear equipos, luego agregar participantes
```
Frontend                    Backend
   |                           |
   | POST /inscripciones/      |
   | {evento_id, paquete_id,  |
   |  promocion_id}           |
   |-------------------------->|
    |   201 {id}               |
    |                           |
    | Resolver/crear Persona    |
    |-------------------------->|
    |   {persona_id}            |
    |                           |
    | POST /equipos/            |
   | {inscripcion_id,         |
   |  disciplina_id, nombre}   |
   |-------------------------->|
   |   201 {id}               |
   |                           |
   | POST /inscripciones/{id}/personas |
   | {persona_id, equipo_id}  |
   |-------------------------->|
   |   201 {participante}     |
```

---

## 10. Matriz de Prueba/Verificación

| Escenario | Backend Endpoint | Verificación | Estado |
|-----------|------------------|-------------|--------|
| Listar inscripciones propias | `GET /inscripciones/` | Devuelve lista del usuario autenticado | 🔴 NO IMPLEMENTADO |
| Crear inscripción simple | `POST /inscripciones/` | Crea con estado BORRADOR | ⚠️ MISMATCH PAYLOAD |
| Agregar equipo | `POST /equipos/` | Crea equipo en inscripción | ✅ |
| Agregar participante | `POST /inscripciones/{id}/personas` | Crea InscripcionPersona + Participacion | ✅ |
| Editar participante | `PATCH /inscripciones/{id}/participantes/{id}` | Actualiza datos | 🔴 NO EXISTE |
| Mover participante | `PATCH /inscripciones/{id}/participantes/{id}/mover` | Cambia de equipo | 🔴 NO EXISTE |
| Eliminar participante | `DELETE /inscripciones/{id}/participantes/{id}` | Elimina o retira | 🔴 NO EXISTE |
| Retirar participante | `PATCH /participaciones/{id}/retirar` | Solo cambia estado a R | ✅ |
| Consentimiento | `AceptacionInscripcion` | Por persona/inscripción | ⚠️ Requiere enviar `aceptaciones` al alta de cada participante |

---

## 11. Orden de Implementación

### Fase 1: Correcciones CRITICAL (Bloqueantes)

1. **Agregar `GET /inscripciones/` al backend** — Lista inscripciones propias del usuario
2. **Decidir estrategia de payload** — Opción A (bulk) vs Opción B (multi-step)
3. **Implementar endpoints faltantes** — Editar, mover, eliminar participantes
4. **Corregir typo `talle_camiseta` → `talla_camiseta`** en frontend

### Fase 2: Consistencia de Estados

5. **Eliminar estados falsos** — `PAGO_PENDIENTE`, `PAGADA` no existen en backend
6. **Ajustar flujo de estados** — Mostrar `Compra.estado` separado de `Inscripcion.estado`

### Fase 3: Consentimientos (Phase 6)

7. **Mover aceptaciones al alta de participante** — Enviar `aceptaciones` por cada `persona_id`
8. **Resolver o crear Persona** — El formulario tiene datos completos, pero el endpoint requiere un `persona_id` existente

### Fase 4: Testing

9. **Agregar tests de integración** — Para endpoints nuevos
10. **Verificar flujo completo end-to-end** — Con datos reales

---

## 12. Riesgos

| Riesgo | Severidad | mitigación |
|--------|----------|------------|
| Frontend no puede crear inscripciones | 🔴 CRITICAL | Implementar bulk create o multi-step |
| Endpoints faltantes rompen edición de participantes | 🔴 CRITICAL | Implementar endpoints PATCH/DELETE |
| Estados inconsistentes confunden al usuario | 🟡 HIGH | Unificar modelo de estados |
| Consentimientos globales no persistidos por participante | 🟡 HIGH | Enviar `aceptaciones` por participante |
| Campo `rol` incompatible (JUGADOR vs J) | 🟡 MEDIUM | Estandarizar lengths |
| Typo `talle_camiseta` en frontend | 🟡 MEDIUM | Corregir a `talla_camiseta` |

---

## 13. Archivos Obsoletos o No Utilizados en Frontend

| Archivo | Notas |
|---------|-------|
| `features/inscripciones/services/inscripcion.service.ts` | Tiene funciones para endpoints que no existen |
| `agregarParticipantesAEquipo()` | Usa endpoint correcto ✅ |
| `editarParticipante()` | 🔴 Endpoint no existe |
| `moverParticipante()` | 🔴 Endpoint no existe |
| `eliminarParticipante()` | 🔴 Endpoint no existe |

---

## 14. Resumen de Cambios Requeridos

### Frontend

| # | Archivo | Cambio |
|---|---------|--------|
| 1 | `inscripcion.schema.ts` | Cambiar `toBackendPayload()` para enviar payload correcto |
| 2 | `inscripcion.service.ts` | Eliminar funciones para endpoints inexistentes |
| 3 | `InscripcionClientShell.tsx` | Posiblemente cambiar flujo a multi-step |
| 4 | `dashboard/page.tsx` | Eliminar estados falsos `PAGO_PENDIENTE`, `PAGADA` |

### Backend

| # | Archivo | Cambio |
|---|---------|--------|
| 1 | `inscripcion_controller.py` | Agregar `GET /inscripciones/` con filtro por usuario |
| 2 | `inscripcion_schemas.py` | Crear schema para bulk create O mantener flat y exigir multi-step |
| 3 | `participacion_controller.py` | Agregar PATCH y DELETE para participaciones |
| 4 | Flujo de personas | Resolver o crear Persona antes de agregarla a la inscripción |

---

*Este documento fue generado como parte del SDD Explore para `salesianos-fest-frontend-backend-contract-audit`. No modifica código fuente.*
