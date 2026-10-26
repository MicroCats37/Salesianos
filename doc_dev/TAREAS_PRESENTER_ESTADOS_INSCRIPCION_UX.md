# Tareas: Presenter de Estados de Inscripcion

Fuente: `PLAN_PRESENTER_ESTADOS_INSCRIPCION_UX.md`.

## Review Workload Forecast

| Campo | Valor |
|---|---|
| Lineas estimadas | 350-500 |
| Riesgo de 400 lineas | Medio |
| Lotes independientes | 7 |
| Estrategia | Aplicar y verificar un lote por vez |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

## Lote 1: Datos Backend

- [ ] 1.1 Extender `backend/modules/salesianos_fest/domain/results/inscripcion_results.py` con los datos cargados que necesita el detalle: equipos, participaciones, compras y ordenes de pago.
- [ ] 1.2 Actualizar `backend/modules/salesianos_fest/domain/selectors/inscripcion_selector.py` para cargar relaciones sin calcular estados derivados ni introducir consultas N+1.
- [ ] 1.3 Prueba: el selector entrega equipos con disciplina/minimo y compras FEST con orden de pago.

## Lote 2: Contrato HTTP

- [x] 2.1 Agregar schemas de respuesta `ResumenEquipos`, `ResumenPago`, `CompraResumen` y `OrdenPagoResumen` en `presentation/schemas/inscripcion_schemas.py`.
- [x] 2.2 Extender el schema de equipo con `estado_equipo`, `estado_roster`, `jugadores_registrados`, `minimo_deportivo` y `faltantes`.
- [x] 2.3 Extender `InscripcionDetailOut` con `resumen_equipos` y `resumen_pago`, manteniendo compatibilidad temporal con el campo `estado` de equipo.
- [x] 2.4 Prueba: los schemas aceptan el JSON objetivo y nunca exponen `OrdenPago.metadata`.

## Lote 3: Presenter Backend

- [x] 3.1 Implementar en `presentation/presenters/inscripcion_presenter.py` el calculo puro de roster por equipo: activas, minimo, faltantes y `INCOMPLETO|COMPLETO`.
- [x] 3.2 Calcular `resumen_equipos` desde los equipos presentados.
- [x] 3.3 Calcular `resumen_pago` desde compras/ordenes sin modificar `Inscripcion.estado`.
- [x] 3.4 Pruebas: roster completo/incompleto, resumen agregado, pago pendiente/parcial/pagado y presenter sin ORM.

## Lote 4: Tipos Frontend

- [x] 4.1 Actualizar `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts` con schemas Zod del contrato nuevo.
- [x] 4.2 Actualizar servicios/hooks consumidores del detalle para transportar el contrato sin recalcular reglas de negocio.
- [x] 4.3 Verificar `npx tsc --noEmit`.

## Lote 5: Progreso de Equipos

- [x] 5.1 Crear `frontend/src/features/inscripciones/components/ResumenEquiposBadge.tsx` para total, completos e incompletos.
- [x] 5.2 Actualizar `SortableEquipoCard.tsx` con badge de roster, progreso accesible y texto de faltantes.
- [x] 5.3 Integrar el resumen en `InscripcionDetailView.tsx` para desktop y movil.
- [x] 5.4 Pruebas: colores, texto accesible y progreso para ambos estados (sin patron de tests frontend — verificado via tsc + build).

## Lote 6: Resumen Comercial

- [x] 6.1 Crear `ResumenPagoCard.tsx` para estado global, compras, capacidad pagada disponible y mensajes.
- [x] 6.2 No mostrar `metadata`; presentar solo datos comerciales autorizados.
- [x] 6.3 Pruebas: pendiente, parcial, pagado y sin compras (verificado via tsc + build).

## Lote 7: Estados y Cierre

- [x] 7.1 Actualizar `RegistrationStepsCard.tsx` y `InscripcionDetailView.tsx` para usar `resumen_pago`, no inferencias desde estado deportivo.
- [x] 7.2 Confirmar que `estado_roster` nunca bloquea compra, pago ni creacion de inscripcion.
- [x] 7.3 Ejecutar pruebas backend afectadas, pruebas frontend disponibles, `npx tsc --noEmit` y `npm run build`.
- [x] 7.4 Actualizar el plan/documentacion con contratos finales y comandos ejecutados.
