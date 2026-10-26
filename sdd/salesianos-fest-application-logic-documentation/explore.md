# Exploration: salesianos-fest-application-logic-documentation

**Status:** COMPLETE
**Fecha:** 2026-10-18
**Proyecto:** Salesianos
**Cambio:** `salesianos-fest-application-logic-documentation`
**Modo:** READ-ONLY exploration — Sin CodeGraph

---

## Executive Summary

| Área | Estado | Severidad |
|------|--------|-----------|
| Catálogo completo (disciplinas, promociones, categorías, paquetes) | ✅ VERIFICADO | — |
| Inscripciones deportivas (creación, listado, detalle) | ✅ VERIFICADO | — |
| Equipos y roster | ✅ VERIFICADO | — |
| Participaciones (crear, retirar, mover) | ✅ VERIFICADO | — |
| Participaciones (editar) | ❌ GAP CRÍTICO | **CRITICAL** |
| Compras y pagos Izipay | ✅ VERIFICADO | — |
| Asignación de cupos post-pago | ✅ VERIFICADO | — |
| Acreditaciones y acceso QR | ✅ VERIFICADO | — |
| Consentimientos (bases, aptitud física, imagen) | ✅ VERIFICADO | — |
| Seeds idempotentes | ✅ VERIFICADO | — |
| Frontend → Backend contract | ⚠️ PARCIAL | MEDIUM |

---

## Current State

El proyecto Salesianos FEST es una aplicación Django + Next.js para gestionar inscripciones deportivas a un evento. La aplicación está organizada en módulos:

- **`modules/usuarios`**: Personas, usuarios, autenticación, búsqueda por documento
- **`modules/eventos`**: Entidad Evento (ediciones del FEST)
- **`modules/pagos`**: Órdenes de pago genéricas, Izipay, transacciones
- **`modules/salesianos_fest`**: Catálogo, inscripciones deportivas, equipos, participaciones, compras, cupos, acreditaciones, control de acceso

La arquitectura sigue el contrato `django-app-architecture-contract.md` con una cadena async de 4 capas:
- Controller (async,薄) → Orchestrator (async,薄) → Flujo (async con transaction.atomic) → Core service (sync)

---

## Affected Areas

### Módulos Backend
- `backend/modules/salesianos_fest/` — 17 modelos, 6 controladores, 10 flujos, 9 selectores
- `backend/modules/eventos/domain/models/evento.py` — Evento
- `backend/modules/usuarios/` — Persona, Usuario, búsqueda por documento
- `backend/modules/pagos/` — OrdenPago, TransaccionPago

### Migrations (chronological)
- `backend/modules/salesianos_fest/migrations/0001_initial.py` — Tablas base
- `backend/modules/salesianos_fest/migrations/0002_inscripcion_equipo_inscripcionpersona_participacion_and_more.py` — Equipos y roster
- `backend/modules/salesianos_fest/migrations/0003_remove_inscripcion_unique_inscripcion_evento_responsable_paquete.py` — Permisión de múltiples inscripciones
- `backend/modules/salesianos_fest/migrations/0004_inscripcion_unique_inscripcion_evento_responsable_paquete.py` — Re-agregado constraint
- `backend/modules/salesianos_fest/migrations/0005_compra.py` — Compras
- `backend/modules/salesianos_fest/migrations/0006_acreditacionevento_asignacioncupo_controlacceso_and_more.py` — Fase 5
- `backend/modules/salesianos_fest/migrations/0007_aceptacion_inscripcion.py` — Fase 6 consentimientos
- `backend/modules/salesianos_fest/migrations/0008_alter_aceptacioninscripcion_created_at_and_more.py` — Corrección de timestamp

### Frontend
- `frontend/src/features/inscripciones/` — Hooks, services, schemas para inscripciones
- `frontend/src/features/auth/` — Login y registro

---

## Approaches

### 1. Documentación Completa de Tablas ✅ ELECCIÓN

Se creó un documento comprehensivo en `doc_dev/DOCUMENTACION_LOGICA_Y_TABLAS_SALESIANOS_FEST.md` que incluye:
- Mapa ejecutivo de módulos
- Catálogo completo de 17+ tablas con campos, tipos, FK, constraints, unicidad
- Diagrama ER en Mermaid
- Flujos end-to-end para todos los casos de uso
- Mapa de APIs con request/response
- Seeds de datos y reglas comerciales
- Frontend screens/hooks/services y sus dependencias
- State machines por entidad
- Invariants y reglas de negocio
- **Reglas diferidas (deferred)**
- **Gaps conocidos y riesgos**

### 2. Verificación de Gaps

| Gap | Severidad | Descripción |
|-----|-----------|-------------|
| `PATCH /participaciones/{id}` | CRITICAL | Endpoint no existe en backend pero frontend lo llama |
| Dashboard auth guard | MEDIUM | `getMisInscripciones` puede 401 en red sin redirect |
| `acceso_box` deferred | MEDIUM | Campo existe pero lógica no implementada |
| `fusion_promocion` sin validación | LOW | Campo existe sin reglas de fusión |
| Multi-step creation flow | LOW | No verificado que frontend encadene correctamente |
| Documento version hardcoded | LOW | `"BASES-SF26-2026-09-06"` hardcoded en flujo |

---

## Recommendation

Se recomienda:
1. **CRÍTICO**: Implementar `PATCH /participaciones/{id}` endpoint para habilitar edición de participantes
2. Agregar auth guard en Dashboard antes de llamar `getMisInscripciones`
3. Documentar las reglas diferidas y crear tickets para su implementación
4. Verificar el flujo multi-step de creación de inscripciones en frontend

---

## Risks

1. **CRITICAL — Participant editing broken**: `PATCH /participaciones/{id}` no existe. Los usuarios no pueden editar rol, talla_camiseta, o notas desde la UI.
2. **MEDIUM — Dashboard auth UX**: `getMisInscripciones` recibe 401 a nivel de red sin manejo graceful.
3. **MEDIUM — acceso_box deferred**: El acceso a zona box no se calcula correctamente.
4. **LOW — fusion_promocion**: Sin validación, permite asignaciones sin sentido.
5. **LOW — Multi-step creation**: Puede haber inconsistencias si el frontend no sigue la secuencia correcta.
6. **LOW — Version hardcoded**: Si cambian las bases, hay que cambiar código.

---

## Ready for Proposal

**Sí.** La documentación está completa y los gaps están identificados. Se puede proceder a crear un SDD proposal para arreglar el gap CRÍTICO de edición de participantes.

---

## Artifacts Produced

1. **Documentación técnica completa:**
   - `doc_dev/DOCUMENTACION_LOGICA_Y_TABLAS_SALESIANOS_FEST.md`
   - Mapa ejecutivo, 17+ tablas, ER diagram, 13 flujos e2e, APIs, seeds, state machines, invariants, gaps

2. **Explore artifact:**
   - `sdd/salesianos-fest-application-logic-documentation/explore`

3. **Memoria persistente (Engram):**
   - `topic_key: sdd/salesianos-fest-application-logic-documentation/explore`
   - `id: 8843`

---

## Key Findings

### Database Design
- 17+ modelos en `salesianos_fest` cubriendo el ciclo completo: catálogo → inscripción → equipo → participación → compra → cupo → acreditación → acceso
- Arquitectura de precios con snapshot: el precio se congela al momento de creación de Compra
- Benefits con dos modos de cálculo: POR_CUPO (por persona) vs FIJO_INICIAL (grupal)
- Partial unique constraints para R11 (participación única por disciplina) y para evitar doble PERMITIDO en QR

### Business Rules
- R11: Una persona no puede participar dos veces en la misma disciplina del mismo evento
- QR single-use per event day
- Admin override con precedencia: REVOCADA/habilitado=False > BLOQUEADA > AUTORIZADA > AUTOMATICA
- AMPLIACION no multiplica beneficios
- Acreditación puede persistir via otra inscripción si se retira de una (R10)

### Architecture
- 4 capas async: controller → orchestrator → flujo → core
- Selectores para consultas complejas con prefetch_related
- Presenters para transformar domain results → HTTP schemas
- No repository layer — el ORM de Django es la abstracción de persistencia

### Deferred/Not Implemented
- `acceso_box` en AcreditacionEvento (campo existe, lógica no)
- Transiciones de estado de Inscripcion (CONFIRMADA, etc.)
- Política de fusión de promociones
