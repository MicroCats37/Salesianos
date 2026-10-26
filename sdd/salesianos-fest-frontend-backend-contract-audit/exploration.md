# Exploration: Salesianos FEST — Frontend-Backend Contract Audit

**Status:** completed
**Fecha:** 2026-10-18
**Proyecto:** Salesianos
**Cambio:** `salesianos-fest-frontend-backend-contract-audit`
**Modo:** filesystem + contract + specification analysis

---

## Executive Summary

| Área | Estado | Severidad |
|------|--------|----------|
| Creación de inscripción (nested payload) | 🔴 BLOQUEANTE | CRITICAL |
| Endpoints faltantes en backend | 🔴 BLOQUEANTE | CRITICAL |
| Flujo de participante (mover/editar) | 🔴 BLOQUEANTE | CRITICAL |
| Consentimientos (Phase 6 no aplicado) | 🔴 BLOQUEANTE | HIGH |
| Estados de inscripción en frontend | 🟡 INCONSISTENTE | HIGH |
| Endpoint GET /inscripciones/ | 🟡 NO EXISTE | HIGH |

---

## Current State

### Backend Routes (confirmed from code)

| Controller | Prefix | Endpoints |
|------------|--------|-----------|
| `CatalogoController` | `/catalogo` | GET disciplinas/, promociones/, categorias/, paquetes/, paquetes/{id}/ |
| `InscripcionController` | `/inscripciones` | POST/, GET/{id}, GET/{id}/detalle, PATCH/{id}, POST/{id}/personas, PATCH/{id}/personas/{pid}/retirar |
| `EquipoController` | `/equipos` | POST/, GET/{id}, GET/inscripcion/{id} |
| `ParticipacionController` | `/participaciones` | POST/, GET/{id}, GET/equipo/{id}, PATCH/{id}/retirar |
| `CompraController` | `/compras` | POST/, GET/{id}, GET/inscripciones/{id}/compras, POST/{id}/iniciar-pago, POST/confirmar-pago |
| `AsignacionController` | `/asignaciones` | POST/, POST/liberar, GET/{id}, GET/inscripciones/{id}/asignaciones |
| `InscripcionSaldoController` | `/inscripciones` | GET/{id}/saldo |
| `AcreditacionController` | `/acreditaciones` | GET/{eid}/{pid}, PATCH/{eid}/{pid}/override-fiesta, POST/{eid}/{pid}/generar-qr |
| `AccesoController` | `/acceso` | POST/registrar |

### Frontend Routes (confirmed from code)

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/dashboard` | Lista inscripciones + estado |
| Inscripción | `/inscripcion` | Wizard de creación |
| Detalle | `/dashboard/inscripcion/{id}` | Gestión de equipos y participantes |

---

## Affected Areas

### Frontend
- `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts` — Payload mismatch (nested equipos[] vs flat backend)
- `frontend/src/features/inscripciones/services/inscripcion.service.ts` — Funciones para endpoints inexistentes
- `frontend/src/app/(app)/dashboard/page.tsx` — Estados inconsistentes

### Backend
- `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py` — Falta GET /inscripciones/
- `backend/modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py` — No acepta nested payload
- `backend/modules/salesianos_fest/presentation/controllers/participacion_controller.py` — Falta PATCH/DELETE
- `backend/modules/usuarios/domain/models/persona.py` — Campos legacy acepto_* no eliminados

---

## Approaches

### 1. Multi-Step Flow (RECOMMENDED)
1. Crear inscripción con payload plano (evento, paquete, promocion, etc.)
2. POST /equipos/ para cada equipo
3. POST /inscripciones/{id}/personas para cada participante

**Pros:** Sigue patrones existentes, simple de implementar
**Cons:** Más llamadas HTTP
**Effort:** Low-Medium

### 2. Bulk Payload
1. Extender CrearInscripcionIn para aceptar equipos[] y participantes[]
2. Crear flujo atómico que crea todo

**Pros:** Una sola llamada
**Cons:** Mayor complejidad transaccional
**Effort:** Medium-High

---

## Key Findings

### 🔴 CRITICAL — Payload Mismatch

El frontend envía `InscripcionBackendPayload` con:
```typescript
{
  evento_id, responsable_id, paquete_id, promocion_id,
  equipos: [{ disciplina_id, nombre, participantes: [...] }]
}
```

El backend `CrearInscripcionIn` solo acepta:
```python
{
  evento_id, responsable_id, paquete_id, promocion_id,
  fusion_promocion_id, delegado_id, estado, observacion
}
```

### 🔴 CRITICAL — Endpoints Inexistentes

| Frontend llama | Backend tiene |
|----------------|---------------|
| GET /inscripciones/ | ❌ NO EXISTE |
| PATCH /inscripciones/{id}/participantes/{id} | ❌ NO EXISTE |
| PATCH /inscripciones/{id}/participantes/{id}/mover | ❌ NO EXISTE |
| DELETE /inscripciones/{id}/participantes/{id} | ❌ NO EXISTE |

### 🟡 HIGH — Phase 6 No Aplicado

`Persona.acepto_bases`, `acepto_aptitud_fisica`, `acepto_imagen` siguen en `Persona`. `AceptacionInscripcion` existe pero campos legacy no eliminados.

### 🟡 HIGH — Estados Inconsistentes

Frontend: `PENDIENTE`, `PAGO_PENDIENTE`, `PAGADA`, `CONFIRMADA`, `CANCELADA`
Backend: `BORRADOR`, `RECIBIDA`, `EN_REVISION`, `OBSERVADA`, `VALIDADA`, `CONFIRMADA`, `RECHAZADA`, `CANCELADA`

`PAGO_PENDIENTE` y `PAGADA` no existen en Inscripcion.estado — son estados de Compra.

---

## Recommendation

**Approach 1 (Multi-Step)** — ya existe la infraestructura necesaria:
1. Implementar GET /inscripciones/ (lista propias)
2. Mantener payload plano, ajustar frontend
3. Agregar endpoints PATCH/DELETE para participaciones
4. Aplicar Phase 6 cleanup
5. Corregir estados en dashboard

---

## Risks

1. **Bloqueante:** Frontend no puede crear inscripciones — usuarios no pueden inscribirse
2. **Bloqueante:** Edición de participantes no funciona — datos corruptos
3. **Alto:** Consentimientos inválidos — problema legal
4. **Medio:** Estados confusos — mala UX

---

## Ready for Proposal

**Yes.** Scope claro:
1. Implementar GET /inscripciones/
2. Decidir estrategia (multi-step vs bulk)
3. Implementar endpoints PATCH/DELETE participaciones
4. Aplicar Phase 6
5. Sincronizar estados

El documento completo está en `doc_dev/INFORME_CONTRASTE_FRONTEND_BACKEND_SALESIANOS_FEST.md`.
