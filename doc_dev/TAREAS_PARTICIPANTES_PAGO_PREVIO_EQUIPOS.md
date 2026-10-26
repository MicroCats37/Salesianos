# Tareas: Participantes, Pago Previo y Equipos

Fuente: `PLAN_PARTICIPANTES_PAGO_PREVIO_EQUIPOS.md`.

## Contrato Fijado

```text
InscripcionPersona: preregistro en pool, sin equipo permitido.
Participacion: solo ubicacion deportiva; requiere AsignacionCupo ACTIVA.
AsignacionCupo: derecho pagado; no depende de Participacion.
```

## Review Workload Forecast

| Campo | Valor |
|---|---|
| Lineas estimadas | 500-750 |
| Riesgo de 400 lineas | Alto |
| Estrategia | Apply por fase, con verificacion en cada una |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

## Fase 1: Garantias de Datos

- [x] 1.1 Revisar `AsignacionCupo` y agregar constraints/indices que impidan doble asignacion activa para la misma persona/compra e impongan capacidad por compra.
- [x] 1.2 Agregar indice de R11 en `Participacion(persona, evento, disciplina, estado)` y asegurar que los movimientos respeten la misma regla.
- [x] 1.3 Crear migracion/backfill destructivo para datos locales: cada participante cubierto por una compra pagada obtiene una asignacion valida; no crear filas vacias.
- [x] 1.4 Pruebas de constraints, capacidad y migracion.

## Fase 2: Reglas Backend

- [x] 2.1 Mantener `POST participantes` como preregistro sin `equipo_id`; validar que participantes activos no excedan cupos contratados validos.
- [x] 2.2 Rechazar creacion, reactivacion o movimiento de `Participacion` sin `AsignacionCupo.ACTIVA` con `CUPO_NO_ASIGNADO` (409).
- [x] 2.3 Validar en orden: autenticacion/autorizacion, fecha limite, pertenencia a inscripcion, cupo activo, R11, disciplina/categoria y `max_jugadores`.
- [x] 2.4 Pruebas para preregistro permitido, drop bloqueado sin cupo, roster lleno, R11 y fecha limite.

## Fase 3: Endpoints Atomicos y Permisos

- [x] 3.1 Crear endpoint de pool: `GET /inscripciones/{id}/pool`, con participantes sin equipo, elegibilidad de drag y motivo de bloqueo.
- [x] 3.2 Crear mutacion atomica de asignar/mover a equipo; no aceptar cambios solo en frontend.
- [x] 3.3 Reforzar todos los endpoints de participante, asignacion y movimiento: responsable de inscripcion o admin; personal de acreditacion solo lectura/escaneo.
- [x] 3.4 Pruebas de ownership, admin, usuario ajeno, idempotencia y concurrencia sobre ultimo cupo.

## Fase 4: Pago y Derechos

- [x] 4.1 Al confirmar una compra, crear asignaciones para participantes pre-registrados hasta la capacidad pagada, con orden determinista e idempotencia.
- [x] 4.2 Mantener participantes restantes bloqueados en pool cuando falte pago; no crear derechos ficticios.
- [x] 4.3 En retiro, marcar participacion retirada, liberar asignacion y recalcular acreditacion; en reingreso, reactivar solo si hay capacidad/derecho valido.
- [x] 4.4 Pruebas de pago inicial, ampliacion, pago repetido, retiro, reingreso y compra cancelada.

## Fase 5: Pool y Drag-and-Drop UI

- [x] 5.1 Crear `PoolParticipanteCard` y seccion de pool en `InscripcionDetailView` con estados: esperando pago, listo para equipo y bloqueado.
- [x] 5.2 Actualizar drag-and-drop para usar los endpoints atomicos y revertir UI si backend rechaza la operacion.
- [x] 5.3 Ocultar/deshabilitar asa de drag en tarjetas sin cupo activo y mostrar CTA Pagar/Ampliar segun saldo.
- [x] 5.4 Mantener equipos y pool responsivos/accesibles, con mensajes de validacion claros.

## Fase 6: Verificacion y Cierre

- [x] 6.1 Ejecutar matriz A01-A13, pruebas de concurrencia y test de idempotencia de confirmacion.
- [x] 6.2 Ejecutar migraciones, `manage.py check`, tests backend afectados, `npx tsc --noEmit` y `npm run build`.
- [x] 6.3 Actualizar contratos/documentacion con endpoints, permisos y flujo final; persistir verify report SDD.

> **Resultado Fase 6 (2026-10-24)**: 325 tests backend en verde (1 fallo preexistente
> y ajeno al cambio), migraciones 0010/0011 aplicadas, `manage.py check` sin
> incidencias, `npx tsc --noEmit` y `npm run build` en verde, 24/24 comprobaciones
> del contrato de UI del pool. Se corrigieron 2 defectos bloqueantes:
> `resumen_pago.disponible_pagado` (siempre 0) y `GET /inscripciones/{id}/saldo`
> (HTTP 500). Detalle y trazabilidad A01-A13 en
> `doc_dev/CONTRATO_POOL_PARTICIPANTES_PAGO_PREVIO.md`.
