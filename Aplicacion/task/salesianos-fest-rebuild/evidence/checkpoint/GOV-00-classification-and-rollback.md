# GOV-00 — Registro de clasificación, fuentes de rollback y responsables de decisión

**Paquete:** `GOV-00-checkpoint-manifest` · **Cambio:** `salesianos-fest-rebuild` · **Proyecto:** Salesianos
**Fecha:** 2026-11-18 · **Complemento de:** `GOV-00-checkpoint-summary.md`

Fuente de verdad por ruta: `manifest-aplicacion.csv` (384 filas). Este documento es la vista legible y
regida; el CSV es el inventario exacto.

---

## 1. Vocabulario de clasificación

| Clase | Definición operativa | Regla de movimiento |
|---|---|---|
| `KEEP` | Contenido normativo o de estado que se conserva sin cambios. | No mover. Solo anotar. |
| `COPY/REBUILD` | Contenido que debe reconstruirse o copiarse hacia el destino final durante FND-0x. | Requiere un paquete que lo autorice explícitamente. |
| `QUARANTINE` | Contenido que se aparta del camino principal para que no contamine el destino. | Solo se retira en el corte, con las compuertas G1–G4 verdes y reemplazo verde. |
| `DELETE-LATER` | Contenido eliminable después de un reemplazo verificado y con archivo de respaldo. | Nunca antes del corte. |
| `GENERATED` | Artefacto que la cadena de herramientas regenera. | Se puede borrar en cualquier momento; no requiere archivo. |
| `NEVER-DELETE` | Secreto o material no recuperable por restauración de archivo. | Solo mediante reemisión de credenciales y decisión de rotación. |

---

## 2. Registro por área

`Origen` = raíz congelada de referencia (solo lectura). `Estado` = estado en `Aplicacion/`.

| # | Área | Archivos | Bytes | Clase | Estado | Fuente de rollback | Responsable |
|---|---|---:|---:|---|---|---|---|
| 1 | `Aplicacion/plan/**` | 18 | 115 291 | `KEEP` | spec y diseño, solo lectura | commit `f3df540` | A0 + producto |
| 2 | `Aplicacion/documentacion/**` | 15 | 985 208 | `KEEP` | evidencia del sistema actual | commit `f3df540` | A0 + producto |
| 3 | `Aplicacion/task/**` (sin `evidence/`) | 41 | 130 916 | `KEEP` | fuente ejecutable de paquetes | commit `f3df540` | A0 |
| 4 | `Aplicacion/backend/config/**` | 10 | 20 685 | `COPY/REBUILD` | 8 idénticos + **2 variantes de destino** | commit `f3df540`; variante reconstruible desde `backend/config/**` | A0 |
| 5 | `Aplicacion/backend/core/**` | 28 | 115 987 | `COPY/REBUILD` | 28/28 idénticos a `backend/core/**` | commit `f3df540`; original en `backend/core/**` | A0 |
| 6 | `Aplicacion/backend/modules/**` | 1 | 22 | `COPY/REBUILD` | **solo `__init__.py`** — esqueleto | commit `f3df540`; destino real = `backend/modules/**` | A0 |
| 7 | `Aplicacion/backend/{utils,static,docker}/**` | 4 | 904 669 | `COPY/REBUILD` | infraestructura | commit `f3df540`; original en `backend/**` | A0 |
| 8 | `Aplicacion/backend/` (raíz) | 9 | 337 297 | `COPY/REBUILD` | `Dockerfile`, `manage.py`, `pyproject.toml`, `pytest.ini`, `conftest.py`, `README.md`, `uv.lock`, `.python-version`, `.gitignore` | commit `f3df540`; original en `backend/` | A0 |
| 9 | `Aplicacion/frontend/src/**` (sin `components-app`) | 166 | 643 083 | `COPY/REBUILD` | subconjunto **idéntico** de `frontend/src` (184 de 559) | commit `f3df540`; original en `frontend/src/**` | A7 + A0 |
| 10 | `Aplicacion/frontend/src/components-app/**` | 18 | 105 515 | `QUARANTINE` | shell de la era CAM | commit `f3df540`; original en `frontend/src/components-app/**` | A7 + A0 |
| 11 | `Aplicacion/frontend/public/**` | 33 | 2 737 386 | `COPY/REBUILD` | recursos estáticos | commit `f3df540`; original en `frontend/public/**` | A7 + A0 |
| 12 | `Aplicacion/frontend/` (raíz, config) | 13 | 329 897 | `COPY/REBUILD` | `package.json`, lock, `biome.json`, `components.json`, `tsconfig.json`, `next.config.ts`, `postcss.config.mjs`, `vitest.*`, `Dockerfile`, `.dockerignore`, `.gitignore`, `README.md`, `.env.example` | commit `f3df540`; original en `frontend/` | A7 + A0 |
| 13 | `Aplicacion/frontend/doc_dev/**` | 6 | 26 559 | `QUARANTINE` | docs de la era CAM, superados por `Aplicacion/documentacion/**` | commit `f3df540` | A7 + A0 |
| 14 | `Aplicacion/frontend/explorer/**` | 2 | 19 768 | `QUARANTINE` | notas de exploración CAM | commit `f3df540` | A7 + A0 |
| 15 | `Aplicacion/proxy/**` | 3 | 7 052 | `COPY/REBUILD` | 3/3 idénticos | commit `f3df540`; original en `proxy/**` | A0 |
| 16 | `Aplicacion/worker/**` | 12 | 295 716 | `COPY/REBUILD` | 12/12 idénticos | commit `f3df540`; original en `worker/**` | A0 |
| 17 | `Aplicacion/docker-compose.yml` | 1 | 3 981 | `COPY/REBUILD` | compose del objetivo | commit `f3df540`; original en `docker-compose.yml` raíz | A0 |
| 18 | `Aplicacion/.env` | 1 | 3 369 | `NEVER-DELETE` | secreto, copia de `.env` raíz | **fuera del repositorio**: reemisión de credenciales | A0 + responsable de credenciales |
| 19 | `Aplicacion/backend/.env` | 1 | 335 | `NEVER-DELETE` | secreto, copia de `backend/.env` | **fuera del repositorio**: reemisión de credenciales | A0 + responsable de credenciales |
| 20 | `Aplicacion/frontend/.env.local` | 1 | 252 | `NEVER-DELETE` | secreto, copia de `frontend/.env.local` | **fuera del repositorio**: reemisión de credenciales | A0 + responsable de credenciales |
| — | `Aplicacion/**` (árbol generado excluido) | 70 080 | 2 424 434 696 | `GENERATED` | dependencias, build y cachés | **regenerable**; no requiere archivo | A0 |

Totales: **384** archivos inventariados + **70 080** generados excluidos = 384 authored + 70 080 generated.
Rastreados en el checkpoint: 380. No rastreados: 4 (3 secretos + `.env.example`, todos gitignorados).
Clases `REVIEW`: 0.

---

## 3. Candidatos futuros de limpieza y su fuente de rollback

Regla dura: **ninguna fila de esta sección puede moverse antes de que G1–G4 estén verdes y el reemplazo
destino pase sus pruebas.** Ninguna se movió en GOV-00.

| Candidato | Ruta | Fuente de rollback nombrada | Condición previa | Responsable |
|---|---|---|---|---|
| C-01 | `Aplicacion/frontend/src/components-app/**` (18) | commit `f3df540`; equivalente en `frontend/src/components-app/**` | Reconstrucción o reemplazo equivalente en verde | A7 + A0 |
| C-02 | `Aplicacion/frontend/doc_dev/**` (6) | commit `f3df540` | Confirmar cobertura por `Aplicacion/documentacion/**` | A7 + A0 |
| C-03 | `Aplicacion/frontend/explorer/**` (2) | commit `f3df540` | Confirmar cobertura documental | A7 + A0 |
| C-04 | `Aplicacion/frontend/node_modules/**` | **regenerable** (`npm ci`) | Ninguna | A0 |
| C-05 | `Aplicacion/frontend/.next/**` | **regenerable** (`next build`) | Ninguna | A0 |
| C-06 | `Aplicacion/backend/.venv/**`, `Aplicacion/worker/scraper/.venv/**` | **regenerable** (`uv sync`) | Ninguna | A0 |
| C-07 | `__pycache__/**`, `.pytest_cache/**` | **regenerable** | Ninguna | A0 |
| C-08 | `Aplicacion/frontend/*.tsbuildinfo`, `next-env.d.ts` | **regenerable** por el toolchain | Ninguna | A0 |

**Fuera de alcance de este cambio (no son candidatos de limpieza del objetivo):** la raíz congelada
`backend/` contiene `old_seed/*.dump|*.sql`, `diferencias_calculo.csv`, `reporte_ingesta_legacy.csv|.xlsx`,
`fix_tests.py`, `fix_migrations.py`, `check_*.py`, `main.py`, `verification_report_*.md`,
`db.sqlite3` y `db.sqlite3.bak-*`. Esas rutas **son la referencia de origen** y pertenecen a otro
dominio de decisión (la de la raíz fuente), no al ciclo de vida de `Aplicacion/`. Se dejan intactas.

---

## 4. Decisiones no resueltas — registro con dueño

| ID | Decisión | Ámbito bloqueante | Dueño | Criterio de cierre |
|---|---|---|---|---|
| GAP-1 | Destino permanente de `Aplicacion/**` | Toda limpieza | A0 + producto | Decisión escrita con fecha y firma |
| GAP-2 | Amendamientos a `contract/**` | GOV-01, FND-* | A0 + producto | Lista de cambios aprobada o ratificada |
| GAP-3 | Objetivo del corte | VER-03 | A0 + producto | Destino nombrado |
| GAP-4 | `config/api.py` y `settings/base.py`: ¿variante intencional o drift? | FND-01, FND-06 | A0 | Verificación contra `modules/` y el alcance por edición |
| D-A | Destino de las 26 rutas en cuarentena | FND-06, FND-07 | A7 + A0 | Decisión por ruta |
| D-B | Las 375 rutas de `frontend/src` no copiadas al destino | FND-06 | A7 + A0 | Lista de copia / reconstrucción / descarte |
| D-C | `Aplicacion/backend/modules/` con solo `__init__.py`: ¿intencionado? | FND-01 | A0 | Confirmación explícita |
| D-D | Los 3 conjuntos de secretos: rotación, reemisión o conservación | VER-03 | A0 + responsable de credenciales | Política de credenciales escrita |
| D-E | `backend/db.sqlite3` binario dentro de `f3df540` | fuera del alcance de GOV-00 | responsable de datos | Decisión de versionado de binarios |
| PD-01…PD-10 | Decisiones funcionales abiertas del plan | tareas específicas | A0 + producto | Cierre según `00-decisiones-y-alcance.md` §4 |

Ninguna de estas decisiones se toma en GOV-00. Los estados `[PROPUESTO]` y `[PENDIENTE]` del plan
permanecen sin ratificar.

---

## 5. Trazabilidad de la línea base de tareas

54 identificadores `T-xxx` definidos en `implementacion/02-plan-de-tareas-y-agentes.md`. GOV-00 cierra
`T-000` (validar decisiones y anotar asuntos PD). Ningún identificador nuevo fue inventado.

| Fase | IDs | Cantidad |
|---|---|---:|
| F0 | `T-000` … `T-007` | 8 |
| F1 | `T-010` … `T-018` | 9 |
| F2 dominios | `T-020`–`T-023`, `T-030`–`T-032`, `T-040`–`T-043`, `T-050`–`T-052`, `T-060` | 15 |
| F2 frontend | `T-070` … `T-078` | 9 |
| F3 | `T-080` … `T-086` | 7 |
| F4 | `T-090` … `T-095` | 6 |
| **Total** | | **54** |

Relación con el tablero de paquetes: `T-000` ↔ `GOV-00`; `T-003`–`T-007` ↔ `GOV-01`; el resto se
distribuye entre `FND-*`, `DOM-*`, `UI-*`, `API-*`, `XCT-*` y `VER-*`. Los 54 `T-xxx` son la línea base
de trazabilidad funcional; los identificadores de paquete son la unidad de ejecución y de propiedad de
archivos.
