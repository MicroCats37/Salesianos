# GOV-01 — Registro de congelamiento de contratos de ejecución

**Paquete:** `GOV-01-contract-freeze` · **Cambio:** `salesianos-fest-rebuild` · **Proyecto:** Salesianos
**Tareas de origen:** `T-003`, `T-004`, `T-005`, `T-006`, `T-007` · **Owner:** A0 (+ A1, A2, A4, A7, A8)
**Estado:** completed · **Fecha:** 2026-11-18 · **Modo:** Standard (paquete de gobernanza, sin código de producto)

---

## 1. Resultado del paquete

**status:** ok

**executive_summary:** GOV-01 congeló nueve interfaces de ejecución que bloqueaban el trabajo paralelo — scope de edición, identidad y titularidad, commerce/pagos/idempotencia, ciclo de vida de derechos, multimedia, envelope único de respuesta/error/paginación, versiones de presenters/schemas con ledger ruta→wrapper, contrato de fixtures provisionales y cliente de prueba — resolviendo explícitamente las tres contradicciones detectadas entre el plan, los contratos normativos y el código congelado, y sin modificar `contract/**`. Se registran 10 `PD-*` y 13 pendientes de gobierno con owner y ámbito de bloqueo, ninguno ratificado.

---

## 2. Registro de freezes

| Freeze | Alcance | Owner | Archivo | Estado |
|---|---|---|---|---|
| `FREEZE-ED-1.0.0` | Scope de edición; reemplaza `EVENTO_ACTIVO_NOMBRE` | A0 + A1 | `FR-02-edition-scope.md` | FROZEN |
| `FREEZE-ID-1.0.0` | Persona / Usuario / titularidad / resolver local→RENIEC / invitado | A1 | `FR-03-identity-titularidad.md` | FROZEN |
| `FREEZE-CM-1.0.0` | Commerce, pagos, idempotencia, activación | A2 + A0 | `FR-04-commerce-payments-idempotency.md` | FROZEN |
| `FREEZE-RT-1.0.0` | Derechos: preview / confirm / revoke | A4 + A5 + A8 | `FR-05-rights-lifecycle.md` | FROZEN |
| `FREEZE-MD-1.0.0` | Multimedia: almacenamiento, validación, multipart | A0 + A5 + A8 | `FR-06-media.md` | FROZEN |
| `FREEZE-ENV-1.0.0` | Envelope único, error, paginación, `estado_operativo` | A0 | `FR-01-envelope-error-pagination.md` | FROZEN |
| `FREEZE-TC-1.0.0` | Cliente de prueba HTTP | A0 | `FR-01-envelope-error-pagination.md` §7 | FROZEN (operativo) |
| `FREEZE-PS-1.0.0` | Versiones de presenters/schemas + ledger ruta→wrapper | A0 + A7 | `FR-07-presenter-schema-versions.md` | FROZEN |
| `FREEZE-FX-1.0.0` | Fixtures provisionales tipadas | A7 + A0 | `FR-08-provisional-fixtures.md` | FROZEN |

`FR-09-open-decisions-register.md` no es un freeze: es el registro de lo que **queda abierto**.

## 3. Decisiones congeladas

| ID | Decisión | Base |
|---|---|---|
| `D-01` | El scope de datos es la `Edicion`, identificada por UUID. La resolución sigue un **orden único** (`edicion_id` explícito → edición activa del actor → única edición `PUBLICADA` → error). Nunca se elige por defecto. `EVENTO_ACTIVO_NOMBRE` **se elimina** de settings y solo puede sobrevivir como semilla de un comando de gestión | `FR-02` §2 |
| `D-02` | `Persona` única por `(tipo_documento, numero_documento)` y existente sin cuenta; `Usuario` con cuenta opcional 1:1 y exactamente dos grupos funcionales; cuatro titularidades nombradas (`RESPONSABLE`, `COMPRADOR`, `BENEFICIARIO`, `ADMIN`) que se verifican sobre el recurso | `FR-03` §1–§2 |
| `D-03` | `Compra` (commerce) con origen de tres valores, total y snapshot congelados; `OrdenPago` y `TransaccionPago` (pagos) como hechos separados; siete garantías de idempotencia y clave `Idempotency-Key` obligatoria en el borde HTTP | `FR-04` §1–§2 |
| `D-04` | El ciclo de vida del derecho tiene tres operaciones: `Preview` no muta, `Confirm` es atómico e idempotente con registro auditado, `Revoke` es permanente, auditado e idempotente. El módulo `validaciones` verifica contra el módulo dueño y nunca concede derechos | `FR-05` §2 |
| `D-05` | Media: `ImageField`, ruta única `MEDIA_ROOT/<dominio>/<entidad_id>/<uuid><ext>`, allowlist MIME + tamaño + firma antes de persistir, protocolo multipart `data` + `files` (`<token>___<realname>`), rechazo de token ausente y de archivo huérfano, limpieza obligatoria en todos los caminos | `FR-06` §2 |
| `D-06` | **Un** envelope. Éxito `{success, data, error:null, message}`; error `{code, message, details?, field_errors[]}` con `field_errors` como **único** canal de error por campo; paginación única `data:{items,total,page,page_size,total_pages}` con `page` base 1, `page_size` 25/100; `PaginatedApiResponse` + `meta` queda deprecada | `FR-01` §4 |
| `D-07` | `estado_operativo` con `codigo` / `etiqueta` / `descripcion`. El vocabulario vivo `EstadoOperativoPago` (8 valores) se conserva **sin renumerar**. El frontend nunca deriva el veredicto. El filtro `estado_operativo` debe quedar expuesto en la UI de pagos | `FR-01` §5 |
| `D-08` | Cliente de prueba: `ninja_extra.testing.TestAsyncClient` para controllers `async def` (regla por defecto), `django.test.Client` como alternativa, `ninja.testing.TestClient` y `ninja_extra.testing.TestClient` **prohibidos** contra controllers async. La enmienda documental del contrato de tests queda abierta (`GOV-01-OPEN-01`) | `FR-01` §7 |
| `D-09` | Versiones semver por módulo en un registro único de A0, espejo Zod con `SCHEMA_VERSION` por dominio y test de contrato que falla ante drift. El ledger ruta→wrapper declara módulo, presenter, wrapper, schema de entrada, errores, status, scope, permiso, versión y carácter provisional | `FR-07` §1–§3 |
| `D-10` | Fixtures provisionales: cinco condiciones obligatorias, marcador literal `PROVISIONAL_CONTRACT_FIXTURE`, tipo TS con `satisfies` (no Zod), ubicación dentro del feature, prohibición de reglas de negocio, y corte verificable por el paquete de integración | `FR-08` §1 |

## 4. Contradicciones y su resolución

| ID | Contradicción | Resolución | Estado |
|---|---|---|---|
| `C-ENV-01` | Dos formas de paginación en el código congelado (`PaginatedData` dentro de `data` vs `PaginatedApiResponse` + `meta`) | Se congela **una**: `data:{items,total,page,page_size,total_pages}`. `PaginatedApiResponse` deprecada; 13 rutas de administración ya cumplen; conversión del resto asignada a FND-01/FND-08 | **RESUELTA** |
| `C-ENV-02` | `error.details` plano (`dict`) frente a `error.field_errors` (lista) del plan | Dos canales **ortogonales**: `details` solo contexto no-campo; `field_errors` lista tipada `{field, code, message}` es el **único** canal de error por campo. La conversión del `details` plano ocurre en la frontera de error | **RESUELTA** |
| `C-ENV-03` | `TEST_ARCHITECTURE_CONTRACT.md` §2/§10.5 vs `django-app-architecture-contract.md` §2.1 sobre el cliente de prueba | Decisión operativa rectora (`D-08`) con evidencia de código verificada; **no** se modifica `contract/**`. La enmienda documental queda como `GOV-01-OPEN-01` (GAP-2) | **RESUELTA operativamente / ABIERTA documentalmente** |

**Ninguna de las tres se resolvió modificando un contrato, un plan o el código congelado.**

## 5. Hechos de GOV-00 consumidos

| Hecho | Uso en GOV-01 |
|---|---|
| Commit de rollback `f3df540` | Punto de reversión de este paquete. No se revierte ni se resetea |
| 384 archivos de autor / 6 782 988 B inventariados | Base del estado del destino. Ninguna ruta de código fue modificada |
| `D-1` — `Aplicacion/frontend/src` es un subconjunto de 184 archivos, no 559 | El shell de frontend (FND-06) parte de 184 archivos, no de una copia completa |
| `D-2` — `config/` con 2 variantes de destino; `Aplicacion/backend/modules/` vacío | `FR-07` registra `config/api.py` como archivo compartido de A0 y `contract_versions.py` como archivo nuevo de A0; el destino no tiene contraparte que ajustar |
| `D-3` — sin residuo CAM en `Aplicacion/` | Los fixtures provisionales no heredan rutas CAM |
| `D-4` — dos conjuntos de credenciales, no tres | No afecta a los freezes; los secretos siguen siendo NEVER-DELETE |
| `D-5` — `Aplicacion/**` versionado por `f3df540` | La evidencia de este paquete es revisable y reversible |
| `D-6` — **54** IDs de tarea definidos, no 96 | GOV-01 cierra `T-003`…`T-007`, los 5 IDs que le corresponden. No se inventaron tareas |

**Verificación de la afirmación de 54 IDs (recalculada en este paquete):** la matriz `00-matriz-tareas.md` mapea 54 IDs únicos. Los identificadores `GOV-01-OPEN-xx` de `FR-09` son **registro de gobierno**, no tareas: no crean filas en la matriz ni cambian el conteo.

## 6. Evidencia leída

### Contratos normativos (7 de 7)

`api-wrapper-presenter-contract.md` · `django-app-architecture-contract.md` · `next-app-architecture-contract.md` · `PLAN_REFACTORIZACION.md` · `SCHEMA_DRY_INTENTION.md` · `smart.md` · `TEST_ARCHITECTURE_CONTRACT.md`

### Plan (10 archivos)

`00-decisiones-y-alcance.md` · `funcional/01-modulos-y-responsabilidades.md` · `funcional/02-reglas-de-negocio.md` · `funcional/03-modelo-de-datos.md` · `funcional/04-flujos-end-to-end.md` · `contratos/01-api-wrappers-presenters.md` · `contratos/02-autenticacion-y-permisos.md` · `contratos/03-integraciones-y-eventos-internos.md` · `frontend/01-mapa-rutas-y-navegacion.md` · `implementacion/01-arquitectura-y-dependencias.md`

### Paquetes y documentos de ejecución

`Aplicacion/task/salesianos-fest-rebuild/00-contrato-global-de-apply.md` · `00-workflow-frontend-contract-first.md` · `00-matriz-tareas.md` · `STATE.md` · `wave-00-governance/GOV-01-contract-freeze.md` · `wave-00-governance/GOV-02-route-ux-baseline.md` · `evidence/checkpoint/GOV-00-checkpoint-summary.md` · `evidence/checkpoint/GOV-00-classification-and-rollback.md`

### Documentación de estado actual

`Aplicacion/documentacion/02a-inventario-de-endpoints.md` (completo) · `02b-proposito-y-consumidores-de-endpoints.md` (consulta dirigida: idempotencia, `estado_operativo`, pagos) · `05a-matriz-pagina-flujo-endpoint-datos.md` (consulta dirigida: idempotencia)

### Código congelado (solo lectura, verificación puntual)

`backend/core/responses.py` · `backend/core/pagination.py` · `backend/core/exceptions.py` · `backend/core/utils.py` · `backend/config/api.py` · `backend/config/settings/base.py` · `backend/config/urls.py` · `backend/modules/pagos/domain/constants.py` · `backend/modules/administracion/domain/services/core/admin_evento_activo_service.py` · `backend/modules/eventos/domain/selectors/evento_selector.py` · `backend/modules/salesianos_fest/domain/services/core/pase_service.py` · `backend/conftest.py` · `backend/modules/usuarios/tests/fixtures/usuarios_fixtures.py` · `frontend/src/utils/payload-builder.ts` · `frontend/src/lib/api.ts` · `frontend/src/types/api.types.ts`

### Skills

`.opencode/skills/salesianos-api-data/SKILL.md` · `.opencode/skills/salesianos-api-data/references/api-data-contract.md`

### Entorno verificado

`backend/.venv/Lib/site-packages/ninja/testing/client.py` · `backend/.venv/Lib/site-packages/ninja_extra/testing/client.py`

## 7. Archivos cambiados (este paquete — huella exacta)

Creados, todos bajo `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/`:

| Archivo | Bytes |
|---|---|
| `GOV-01-contract-freeze-summary.md` | este archivo |
| `FR-01-envelope-error-pagination.md` | 17 437 |
| `FR-02-edition-scope.md` | 10 172 |
| `FR-03-identity-titularidad.md` | 10 459 |
| `FR-04-commerce-payments-idempotency.md` | 10 220 |
| `FR-05-rights-lifecycle.md` | 9 398 |
| `FR-06-media.md` | 8 167 |
| `FR-07-presenter-schema-versions.md` | 12 440 |
| `FR-08-provisional-fixtures.md` | 13 620 |
| `FR-09-open-decisions-register.md` | registro de decisiones abiertas |
| `route-to-wrapper-ledger.csv` | 19 rutas propuestas |

Modificado: `Aplicacion/task/salesianos-fest-rebuild/STATE.md` (tablero de paquetes + bitácora).

Ningún archivo de código, contrato, plan, documentación, skill, agente, configuración, base de datos o secreto fue tocado. Ningún commit creado. `git stash` no invocado.

### 7.1 Dónde queda marcado el completado de `T-003`…`T-007`

| Artefacto de tareas | ¿Marcado? | Motivo |
|---|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/00-matriz-tareas.md` (filas `T-003`…`T-007`) | **No, no se editó** | La matriz está **fuera** de las raíces de edición permitidas de GOV-01 (solo `evidence/contracts/**`, `STATE.md` y los temas Engram). Sus filas siguen en `pending` y **deben** actualizarse en el siguiente paquete con permiso explícito, o por A0 |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | **Sí** | Fila `GOV-01` = `completed` + bitácora de transición que nombra `T-003`…`T-007` |
| Engram `sdd/salesianos-fest-rebuild/apply-progress` | **Sí** | §2 "Cumulative Task State" marca `T-003`…`T-007` como completados con su observación |
| Engram `sdd/salesianos-fest-rebuild/state` | **Sí** | Registro de transición de GOV-01 con los IDs de tarea de origen |

**No existe un artefacto Engram `sdd/salesianos-fest-rebuild/tasks`.** La matriz física es el único artefacto de tareas, y es de solo lectura para este paquete.

## 8. Comandos ejecutados y códigos de salida

Todos desde la raíz del repositorio.

| # | Comando | Exit | Resultado |
|---|---|---:|---|
| 1 | `git rev-parse --show-toplevel` | 0 | `C:/Users/Usuario/Desktop/Aplicaciones/CST/Salesianos` |
| 2 | `git rev-parse HEAD` | 0 | rollback point `f3df540…` |
| 3 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion .opencode/skills .opencode/agents` | 0 | **vacío** — ninguna raíz prohibida tocada |
| 4 | `git diff --name-only -- backend frontend worker proxy contract Aplicacion/plan Aplicacion/documentacion .opencode/skills .opencode/agents` | 0 | **vacío** — ninguna raíz de producto tocada |
| 5 | `git status --short` | 0 | solo rutas de `evidence/contracts/**` y `STATE.md` de este paquete, más actividad concurrente preexistente |
| 6 | búsqueda `EVENTO_ACTIVO_NOMBRE` en `backend/**.py` | 0 | **15 coincidencias** en 10 archivos (base de `FR-02` §1.1) |
| 7 | búsqueda `EVENTO_ACTIVO_NOMBRE` en `Aplicacion/backend`, `Aplicacion/frontend/src` | 0 | **1** coincidencia: `Aplicacion/backend/config/settings/base.py:132` |
| 8 | búsqueda `ImageField` / `upload_to` en `backend/**.py` | 0 | **0 coincidencias** — el almacenamiento en dominio no existe todavía |
| 9 | conteo de controllers con `async def` | 0 | **23 de 24** archivos; única excepción `usuarios/.../me_controller.py:53` |
| 10 | conteo de `register_controllers` en `backend/config/api.py` | 0 | **28** |
| 11 | clientes de prueba importados en `backend/**/tests/**` | 0 | `django.test.Client`, `ninja.testing.TestClient`, `ninja_extra.testing.TestAsyncClient` — **tres en uso** |
| 12 | lectura de `ninja/testing/client.py` y `ninja_extra/testing/client.py` | 0 | `TestClient._call` síncrono; `TestAsyncClient._call` asíncrono (confirmación del mecanismo de fallo) |
| 13 | `EstadoOperativoPago` en `backend/modules/pagos/domain/constants.py` | 0 | **8** valores, vocabulary sin renumerar |
| 14 | `git grep` de las 54 filas de la matriz de tareas | 0 | **54** IDs únicos (coincide con el conteo de GOV-00) |
| 15 | `git grep -n "PROVISIONAL_CONTRACT_FIXTURE\|field_errors\|page_size\|estado_operativo"` sobre `evidence/contracts` | 0 | coincidencia en todos los términos requeridos |
| 16 | `git grep -n "EVENTO_ACTIVO_NOMBRE"` sobre `evidence/contracts` | 0 | coincidencia en `FR-02` (como supuesto **reemplazado**) |

**Desviación de verificación:** los comandos del paquete están escritos con `rg`, que **no está instalado** en este entorno (`Get-Command rg` → vacío; `where.exe rg` → vacío). Se ejecutaron los equivalentes semánticos con `git grep` y `Select-String`, con los mismos patrones y sobre el mismo alcance, y se registra la desviación en §9.

## 9. Desviaciones

1. **Herramienta de verificación.** `rg` no disponible. Se usó `git grep` como equivalente (mismos patrones, mismo alcance, mismos códigos de salida: 0 con coincidencias, 1 sin ellas). Sin cambio de resultado.
2. **Alcance de lectura de evidencia.** `02b` (252 KB) y `05a` (121 KB) se consultaron de forma dirigida por los términos del contrato (idempotencia, `estado_operativo`, pagos, filtros) en lugar de una lectura lineal completa. `02a` (31 KB) se leyó completo. La extracción dirigida se apoya en el inventario de endpoints ya verificado por GOV-00.
3. **Enmienda del contrato de tests no ejecutada.** `contract/**` está en raíz prohibida para GOV-01. La contradicción del cliente de prueba queda resuelta **operativamente** y abierta **documentalmente** (`GOV-01-OPEN-01`), sin modificar el contrato.
4. **`PaginatedApiResponse` no eliminada.** La deprecación se registra como decisión; la eliminación del código es trabajo de FND-01 y está fuera del alcance de este paquete.
5. **Ledger parcial.** Contiene 19 rutas propuestas que cubren los 12 contratos de caso de uso del plan. Las rutas de lectura restantes se amplían en GOV-02 (`GOV-01-OPEN-12`).
6. **Identificadores `GOV-01-OPEN-xx`.** Son registro de gobierno, no tareas del plan. No alteran el conteo de 54 IDs.

## 10. Rollback

- **Punto de reversión:** commit `f3df5401c56b41c340f257e67d5a306904a9e670`.
- **Reversión de este paquete:** eliminar `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/**` y restaurar `Aplicacion/task/salesianos-fest-rebuild/STATE.md` a su contenido previo. En Engram: restaurar `sdd/salesianos-fest-rebuild/apply-progress` y `sdd/salesianos-fest-rebuild/state` a la observación de GOV-00 (#11227 / #11228).
- **No** revertir ni resetear `f3df540`: contiene el árbol previo que este paquete dejó de alterar.
- **Reversión de aplicación:** no aplica. No hubo cambios de código, contrato, plan ni configuración.

## 11. Consumidores desbloqueados

### Desbloqueados por el contrato (pueden empezar cuando su DAG lo permita)

| Consumidor | Freeze que lo habilita | Dependencia de DAG restante |
|---|---|---|
| GOV-02 (T-001, T-002) | todos | ninguna — **listo ahora** |
| FND-01 (T-016 media, T-018 permisos) | `FREEZE-MD`, `FREEZE-ID`, `FREEZE-ENV`, `FREEZE-PS` | GOV-02 |
| FND-02 (T-010 edición) | `FREEZE-ED` | FND-01 |
| FND-03 (T-011, T-012 identidad) | `FREEZE-ID` | FND-01 |
| FND-04 (T-013, T-014 commerce/pagos) | `FREEZE-CM`, `FREEZE-ENV` | FND-01 |
| FND-05 (T-015 activación) | `FREEZE-CM` | FND-04 |
| DOM-01…DOM-08 | `FREEZE-ED`, `FREEZE-ID`, `FREEZE-CM`, `FREEZE-RT`, `FREEZE-MD` | FND-02…FND-05 según DAG |
| UI-01…UI-05 | `FREEZE-FX`, `FREEZE-ED`, `FREEZE-ENV`, `FREEZE-RT` | GOV-02, FND-06 |
| API-01…API-05 | `FREEZE-PS` (ledger + espejo Zod 1:1 + test de drift) | UI-0x, DOM-0x, FND-08 |
| XCT-01…XCT-03 | todos | según DAG |
| VER-01…VER-03 | todos | según DAG |

### Regla de consumo

Un consumidor **solo** puede usar una interfaz cuando su entrada de freeze correspondiente está marcada FROZEN. Toda ruta del ledger marcada `provisional = sí` **no puede** consumir `PROVISIONAL_CONTRACT_FIXTURE` como si fuera real.

## 12. Criterios de aceptación del paquete

- [x] El registro de freeze nombra owners, identificadores, wrappers, errores y expectativas de versionado exactos.
- [x] El scope de edición y los contratos de presenter/schema preceden al trabajo paralelo de esqueletos y dominios.
- [x] Las contradicciones de cliente de prueba y de envelope tienen decisión rectora explícita o estado de bloqueo (`D-08`, `C-ENV-01`…`C-ENV-03`).
- [x] Las fixtures contienen **ejemplos** y están marcadas como provisionales.
- [x] Los `PD` quedan registrados con owner y ámbito de bloqueo; ninguna propuesta se convirtió en aprobación.
- [x] Se consumieron los hechos de GOV-00: `f3df540`, 384 archivos, `D-1`…`D-6` y los 54 IDs de tarea.

## 13. Siguiente paquete

**[GOV-02](GOV-02-route-ux-baseline.md)** — `T-001`, `T-002`. Fichas de ruta para los 40 page IDs del plan, baseline de checks del origen congelado y matriz de comandos del objetivo.
