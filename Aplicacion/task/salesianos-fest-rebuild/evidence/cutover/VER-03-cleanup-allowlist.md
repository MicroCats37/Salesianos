# VER-03 — Allowlist de limpieza (preparada, **no aplicada**)

**Paquete:** `VER-03-signoff-archive-cutover-cleanup` · **Cambio:** `salesianos-fest-rebuild` · **Proyecto:** Salesianos
**Fecha:** 2026-11-20 · **Complemento de:** [`../archive/VER-03-archive-report.md`](../archive/VER-03-archive-report.md)

---

## 1. Decisión en una línea

**Cero eliminaciones.** El allowlist queda **preparado y verificado** (cada ítem con su condición, su fuente de
rollback y su comando), pero **no se aplica**: las compuertas **G1** (árbol sin commitear) y **G3** (decisiones de
propiedad sin ratificar) están **rojas**, y la regla de orden del plan es explícita:
`G1 → G2 → G3 → (objetivo verde) → G4 → primera eliminación → siguientes eliminaciones`.

---

## 2. Por qué no se aplica (cadena de bloqueo, verificable)

| # | Compuerta | Estado | Evidencia | Dueño |
|---:|---|---|---|---|
| 1 | **G1** versionado / checkpoint | 🔴 | `git status --short` = **259 líneas**; el rebuild **no está commiteado** | A0 + producto |
| 2 | **G3** decisiones de propiedad | 🔴 | `GAP-1`, `GAP-3`, `D-A`, `D-D` **abiertas** en `FR-09` §5 y en el tablero | A0 + producto |
| 3 | **Corte verde** (paso 5 del paquete: *"sólo tras un corte verde"*) | 🔴 | Docker apagado · lane PostgreSQL no ejecutada · 4 rutas retiradas sin contraparte | A0 + A9 + producto |
| 4 | **Techo de Biome** | 🔴 | 445/110 vs techo congelado 105/93 | A0 + A7 |
| 5 | **Firma de producto** | 🟡 | no existe firma en el repositorio | Producto |

**Ninguno de estos cinco bloqueos es imputable a este paquete** (A0 es dueño exclusivo de `config/api.py`, los
settings y el compose; el producto es dueño de las decisiones; A7 es dueño de la deuda de lint y de la
superficie frontend).

---

## 3. Allowlist de limpieza: ítem por ítem

Cada ítem lleva **clase** (GOV-00), **condición previa**, **fuente de rollback** y **comando exacto**.
`GOV-00` §3 es el registro que nombra las fuentes de rollback; `FR-08` §1.5 es el corte de fixtures provisionales.

### 3.1 Ítems en cuarentena (residencia CAM-era en el destino)

| # | Ruta | Ficheros | Bytes | Clase | Condición previa | Fuente de rollback | Estado |
|---:|---|---:|---:|---|---|---|---|
| C-01 | `Aplicacion/frontend/src/components-app/**` | 18 | 105 515 | `QUARANTINE` | **reemplazo equivalente en verde** ✅ (`src/components/shell/**`; `tsconfig.json` lo excluye; **0 imports** de producción — sólo dos tests que lo *excluyen*) | commit `f3df540` **y** equivalente en la raíz congelada `frontend/src/components-app/**` (18 ficheros) ⇒ **doble fuente** | 🔒 **BLOQUEADO** (G1/G3) |
| C-02 | `Aplicacion/frontend/doc_dev/**` | 8 | 124 364 | `QUARANTINE` | cobertura documental por `Aplicacion/documentacion/**` | 6 de los 8 ficheros tienen equivalente en `frontend/doc_dev/**` (raíz congelada) + commit; **2 son trabajo concurrente sin equivalente** (`brief-gov02-parte-a-sistema-visual-y-shell.md`, `shadcn-registry-inventory.md`) ⇒ esos 2 **sólo** son recuperables desde el archivo G4 | 🔒 **BLOQUEADO** (G1/G3) y **dividido**: 6 ficheros con doble rollback, 2 con rollback único (archivo G4) |
| C-03 | `Aplicacion/frontend/explorer/**` | 2 | 19 768 | `QUARANTINE` | cobertura documental | commit `f3df540` + `frontend/explorer/**` (2 ficheros) ⇒ doble fuente | 🔒 **BLOQUEADO** (G1/G3) |

**Nota sobre C-02:** `GOV-02` registró un **conflicto sin resolver** entre `doc_dev/brief-gov02-parte-a…md` y la
evidencia `evidence/routes/SH-04` (la brief reporta **219** ítems del registro shadcn; SH-04 midió **471**), y
dejó constancia de que **A0 debe decidir el orden de fusión y qué fuente gana** antes de que FND-06 consuma
cualquiera de las dos. **Retirar ese fichero sin esa decisión destruiría un material que A0 tiene pendiente.**
Se **retain** por ese motivo, con independencia de la compuerta.

### 3.2 Scratch y duplicados no clasificados (hallazgo de este paquete)

| # | Ruta | Ficheros | Bytes | Clase propuesta | Condición | Rollback | Estado |
|---:|---|---:|---:|---|---|---|---|
| C-04 | `Aplicacion/frontend/biome_baseline_tmp/**` | 41 | 220 260 | `GENERATED`/duplicado | **41 copias scratch** de los componentes de portada; **no trackeadas** por git, excluidas de `tsconfig` (`biome_baseline_tmp/**`) y **excluidas del payload del archivo** | **ninguno por commit** (no versionadas) ⇒ **sólo el contenido original** en `src/features/portada/components/**` | 🔒 **BLOQUEADO** (G1/G3) + **sin rollback propio**: si se borran, no se pierde contenido, pero la operación necesita una compuerta verde y una nota |
| C-05 | `Aplicacion/frontend/.biome-baseline/**` | 41 | 220 260 | `GENERATED`/duplicado | **idéntica** a C-04 (mismo tamaño) pero **trackeada** en git ⇒ rollback por commit + archivo G4 (41 filas en el manifiesto) | commit + archivo G4 | 🔒 **BLOQUEADO** (G1/G3) |

**Contribución a la deuda de Biome:** estas dos carpetas y `src/components-app/**` están **dentro** de las 715
ficheras que Biome revisa (`src/components-app/forms/MultiPartFormStepper.tsx` 7 diagnósticos,
`src/components-app/tables/AppDataTable.tsx` 6, `.biome-baseline/Hero.tsx` 6). **No son la causa** del techo
(la deuda es de todo el frontend del rebuild), pero su retirada **reduce** el recuento. **No se cuenta como
justificación**: la justificación es que son duplicados sin valor de producto.

### 3.3 Fixtures provisionales (corte `FR-08` §1.5)

| # | Ruta | Ficheros | Bytes | Condición del corte | Estado |
|---:|---|---:|---:|---|---|
| C-06 | `Aplicacion/frontend/src/features/portada/fixtures/**` | 8 | 40 650 | `FR-08` §1.5: *"ningún módulo fuera de tests/stories importa la fixture"* | 🔴 **CUT TEST NOT SATISFIED** |

**Medición real:** el token `PROVISIONAL_CONTRACT_FIXTURE` sigue en **3** ficheros del árbol
(`paquetes.fixture.ts`, `useCatalogo.ts`, `useLandingPaquetes.ts`) y **3 módulos de producción los importan**:

| Fichero de producción | Importa |
|---|---|
| `features/portada/components/ChampionshipSection.tsx` | `@/features/portada/fixtures/useCatalogo` |
| `features/portada/components/Paquetes.tsx` | `@/features/portada/fixtures/useLandingPaquetes` + `paquetes.fixture` |
| `features/portada/components/TicketsSection.tsx` | `@/features/portada/fixtures/useLandingPaquetes` |

**Consecuencia:** **borrarlos ahora rompe la portada**. Y el motivo de fondo está documentado en el propio
fichero: `useCatalogo.ts` replica la forma del backend **congelado** (`sigla`, `min_jugadores`) y **no** la del
backend **objetivo** (`slug`, `minimo_por_equipo`); migrarlo exige un espejo Zod y un cliente propios
⇒ es trabajo de **API** (dueño A7 + A0), **no** de limpieza. Los otros 5 tokens del rebuild ya se cortaron
correctamente en API-01…API-05 (0 coincidencias en `features/{pases,marketplace,competencias,validaciones,
patrocinadores,admin,inscripciones,public,cuenta,auth}`). **Este es el residuo #1 que bloquea el criterio de
salida de F4 "no mocks de datos reales en producción".**

### 3.4 Ítems explícitamente **fuera** del alcance (nunca se tocan)

| Ruta | Clase | Motivo |
|---|---|---|
| `Aplicacion/.env`, `Aplicacion/backend/.env`, `Aplicacion/frontend/.env.local` | `NEVER-DELETE` | secretos: se restauran **reeemitiendo credenciales**, nunca desde un archivo. `D-D` (política) sigue **abierta** |
| `Aplicacion/backend/db.sqlite3` | dato | base de datos: requiere aprobación aparte. **No** se archiva como contenido, **no** se borra |
| `Aplicacion/frontend/.env.example` | `KEEP` | plantilla sin credenciales |
| `backend/**`, `frontend/**`, `worker/**`, `proxy/**` (raíces congeladas) | referencia | **prohibido** retirarlas sin aprobación expresa del usuario |
| `contract/**`, `Aplicacion/plan/**`, `Aplicacion/documentacion/**` | normativo / spec / evidencia | **prohibido** |
| `node_modules`, `.venv`, `.next`, `__pycache__`, `.pytest_cache`, `*.tsbuildinfo` | `GENERATED` | regenerables; **prohibido** limpiarlos *antes* de la compuerta explícita de limpieza; y borrarlos **rompería** las puertas finales |

---

## 4. Inventario final: **retenidas**, **en cuarentena**, **eliminadas**

| Categoría | Rutas | Ficheros | Bytes |
|---|---|---:|---:|
| **Eliminadas por este paquete** | **ninguna** | **0** | **0** |
| **Movidas / renombradas** | ninguna | 0 | 0 |
| **En cuarentena (pendientes de la compuerta)** | C-01, C-02, C-03, C-04, C-05 | **110** | **691 927** |
| **Residuo de fixture provisional (corte pendiente)** | C-06 | **8** | **40 650** |
| **Retenidas por regla dura (nunca eliminar sin aprobación aparte)** | secretos (3) + `db.sqlite3` (1) + `.env.example` (1) + raíces congeladas + contratos/plan/documentación | — | — |
| **Totales bajo `Aplicacion/**`** | — | **1731 archivados + 3 secretos + 41 scratch** | **15 907 743** |

### 4.1 Ruta por ruta (las 6 que la allowlist toca)

| Ruta | Estado | Acción pendiente |
|---|---|---|
| `Aplicacion/frontend/src/components-app/**` | 🟡 **retenida en cuarentena** | borrar tras G1+G3 (doble rollback) |
| `Aplicacion/frontend/doc_dev/**` | 🟡 **retenida en cuarentena** | borrar los **6** ficheros CAM (doble rollback); **retener 2** hasta que A0 resuelva el conflicto 219-vs-471 |
| `Aplicacion/frontend/explorer/**` | 🟡 **retenida en cuarentena** | borrar tras G1+G3 (doble rollback) |
| `Aplicacion/frontend/biome_baseline_tmp/**` | 🟡 **retenida** | borrar tras G1+G3; sin rollback propio (no versionada) |
| `Aplicacion/frontend/.biome-baseline/**` | 🟡 **retenida** | borrar tras G1+G3 (rollback por commit + archivo G4) |
| `Aplicacion/frontend/src/features/portada/fixtures/**` | 🔴 **retenida — corte no satisfecho** | **no** es limpieza: requiere el espejo Zod + cliente del backend objetivo (API, dueño A7 + A0) |

---

## 5. Procedimiento de aplicación (para cuando las compuertas estén verdes)

**Precondiciones, TODAS necesarias:** G1 verde (árbol commiteado) · G2 re-verificado · **G3 verde** (GAP-1, GAP-3,
D-A, D-D **ratificados por escrito**) · corte de producción verde · techo de Biome cerrado o **expresamente
aceptado por el responsable de release** · firma de producto.

### 5.1 Orden (quarantine-before-delete)

1. **Congelar** (quarantine) antes de borrar: mover cada ruta candidata a
   `Aplicacion/task/salesianos-fest-rebuild/evidence/cleanup/quarantine-<fecha>/<ruta-original>`,
   **conservando la estructura**, y generar su manifiesto SHA-256.
2. **Re-verificar el objetivo** con las puertas focales: `uv run --group dev python -m pytest -q` ·
   `npx tsc --noEmit` · `npx vitest run` · `npx biome check .` · `docker compose config --quiet`.
3. **Borrar** la cuarentena **sólo** si las puertas focales siguen verdes.
4. **Re-ejecutar** el smoke completo y el **spot-check del archivo** (§4.5 del informe de archivo).
5. **Publicar** el informe final con la lista de **retenidas / en cuarentena / eliminadas**.

### 5.2 Comando por ítem (una vez verde la compuerta)

```powershell
# C-01
Remove-Item -Recurse -Force "Aplicacion\frontend\src\components-app"
# C-03
Remove-Item -Recurse -Force "Aplicacion\frontend\explorer"
# C-02 (sólo los 6 ficheros CAM; los 2 de GOV-02 se RETIENEN)
Remove-Item -Force "Aplicacion\frontend\doc_dev\CARDS_ARCHITECTURE_STRATEGY.md",
                        "Aplicacion\frontend\doc_dev\EDIFICACIONES_SMART_FIELDS_REFACTOR.md",
                        "Aplicacion\frontend\doc_dev\FRONTEND_REBUILD_STRATEGY.md",
                        "Aplicacion\frontend\doc_dev\PAGE_HEADER_ABSTRACTION.md",
                        "Aplicacion\frontend\doc_dev\REBUILD_ROADMAP.md",
                        "Aplicacion\frontend\doc_dev\SMART_FIELD_ARCHITECTURE.md"
# C-04 / C-05 (duplicados scratch, 41 + 41)
Remove-Item -Recurse -Force "Aplicacion\frontend\biome_baseline_tmp",
                             "Aplicacion\frontend\.biome-baseline"
```

**Nunca**: `git stash` · `git reset` sobre `f3df540` · `docker compose down -v` · borrar secretos · borrar
`db.sqlite3` · tocar las raíces congeladas.

### 5.3 Rollback de la limpieza

Cada ruta eliminada se recupera desde el **archivo G4** (§8.2 del informe de archivo) y se verifica con
`evidence/archive/ARCHIVE-MANIFEST.csv`. Las 41 rutas de C-04 (`biome_baseline_tmp`) **no** están versionadas:
su contenido original está en `src/features/portada/components/**`, así que la recuperación es por *reconstrucción*,
no por *restauración* — y por eso C-04 exige la compuerta verde **antes** de tocarse.

---

## 6. Prueba de «cero limpieza»

| Prueba | Resultado |
|---|---|
| Entradas `D` / `R` / `C` creadas por este paquete | **0** |
| Ficheros de producto eliminados | **0** |
| Ficheros de producto movidos o renombrados | **0** |
| Ficheros de producto modificados | **0** (sólo `STATE.md` y la evidencia nueva) |
| Rutas de secreto tocadas | **0** |
| Bases de datos / dumps / media tocadas | **0** |
| Raíces congeladas tocadas | **0** (`git diff --name-only -- backend frontend worker proxy contract` ⇒ vacío) |
| Plan / documentación tocados | **0** |
| Contratos tocados | **0** |
| `git stash` invocado | **no** |
| Commits creados | **0** |
| `docker compose down -v` invocado | **no** |
