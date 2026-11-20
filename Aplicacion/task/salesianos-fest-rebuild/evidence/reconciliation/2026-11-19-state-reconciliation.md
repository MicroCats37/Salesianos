# Reconciliación formal del estado — salesianos-fest-rebuild

**Reconciliación:** A0 (coordinador) · **Change:** `salesianos-fest-rebuild` · **Fecha:** 2026-11-19
**Naturaleza:** reconciliación de **estado y evidencia** sobre paquetes YA ENTREGADOS. **NO** es un paquete
nuevo, **NO** implementa comportamiento, **NO** toca código, contratos ni planes.
**Alcance:** FND-01…FND-06 · DOM-01…DOM-08 (+ la fila ausente de UI-01A).
**Tablero:** `Aplicacion/task/salesianos-fest-rebuild/STATE.md` · **Topics:** `sdd/salesianos-fest-rebuild/state`
(#11228) · `sdd/salesianos-fest-rebuild/apply-progress` (#11227).
**Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (`betha 5`) — sin commit, `git stash` nunca invocado.

---

## 1. Regla aplicada

El estado de cada paquete se determina **exclusivamente** por la evidencia de runtime **ya registrada** por ese
paquete. **Ninguna fila se promovió a `completed` sin una suite verde ejecutada.** Los paquetes con evidencia
de runtime ausente o diferida se mantienen en `verification_required` y se listan explícitamente en §4.

**Comandos de verificación ejecutados en esta reconciliación: NINGUNO.** No se ejecutó `pytest`,
`manage.py check`, `makemigrations`, `migrate`, `showmigrations`, typecheck, lint, `vitest`, `biome` ni
`next build` (la verificación en ejecución está diferida por instrucción del usuario; esta reconciliación no
pide autorización para ejecutarla).

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| C1 | `git rev-parse --show-toplevel` | 0 | raíz del workspace |
| C2 | `git rev-parse HEAD` | 0 | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` — sin commit |
| C3 | `git status --short` | 0 | 251 líneas (árbol sucio preexistente de los paquetes concurrentes) |
| C4 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion .opencode backend frontend worker proxy` | 0 | **vacío** — raíces prohibidas intactas |
| C5 | `git stash` / `git reset` / `git checkout` | — | **nunca invocados** |

---

## 2. Transiciones (estado exacto)

| Packet | Antes | Después | Base de la decisión |
|---|---|---|---|
| FND-06 | `pending` (evidencia `none`) | **`verification_required`** | #11303 — pasada de implementación aplicada (26 ficheros en `Aplicacion/frontend/**`). Único runtime: `npx tsc --noEmit` exit 0. Vitest / Biome / `next build` / sonda HTTP / navegador de cinco anchos **NOT RUN**; 4 pruebas ESCRITAS, NO EXECUTADAS. |
| DOM-08 | `pending` (evidencia `none`) | **`verification_required`** | #11347 — `Aplicacion/backend/modules/patrocinadores/**` (57 ficheros, 3 363 líneas). 53 pruebas ESCRITAS, NO EJECUTADAS; comandos NINGUNO (revisión estática: 22 comprobaciones + 5 correcciones). |
| DOM-06 | `completed` | **`completed` (confirmado)** | #11361 — `modules/marketplace/tests` **97 passed** (69 + 28) con `uv run`; `makemigrations --check` 0; `check` 0; migrate/showmigrations/rollback/replay 0; esquema SQLite real inspeccionado. |
| DOM-03 | `verification_required` | **`verification_required` (confirmado)** | 41 pruebas ESCRITAS, NO EJECUTADAS + reconciliación de cableado de A0 (`A0-reconciliation-dom03.md`, comandos NINGUNO): 2 controllers registrados, `salesianos_fest` → `1.2.0`, 17 códigos públicos nuevos, 31 paths vivos, 86 casos parametrizados ESCRITOS y NO ejecutados. |
| DOM-05 | `verification_required` | **`verification_required` (confirmado)** | 32 pruebas ESCRITAS, NO EJECUTADAS (34 casos colectados, una parametrizada ×3). |
| DOM-07 | `verification_required` | **`verification_required` (confirmado)** | 43 pruebas ESCRITAS, NO EXECUTADAS; migración `0001_initial` escrita A MANO, **sin verificar en runtime** (`pytest.ini` usa `--nomigrations`). |
| FND-01…FND-05 · DOM-01 · DOM-02 · DOM-04 | `completed` | **`completed` (confirmado)** | Suites verdes en su propia ventana (ver §3). |
| UI-01A | fila **ausente** | **`completed` (fila añadida)** | #11256 + bugfix #11257. **UI-01 sigue `pending`.** |

**Divergencia #11283 cerrada:** FND-06 nunca se promovió a `completed`; el índice acumulado y el topic de estado
dejaban de afirmarlo y el paquete queda en `verification_required` con la evidencia que lo sostiene.

---

## 3. Test totals (los de cada paquete, en SU propia ventana)

| Suite | Resultado | Evidencia |
|---|---|---|
| `core/tests` | 156 passed | verde |
| `modules/eventos/tests` | 63 passed | verde |
| `modules/usuarios/tests` | 35 passed | verde |
| `modules/commerce/tests` + `modules/pagos/tests` | 96 passed | verde |
| `modules/salesianos_fest/tests` | 102 passed (45 DOM-01 + 57 DOM-02) | verde · **+41 de DOM-03 SIN ejecutar** → 143 funciones escritas |
| `modules/marketplace/tests` | 97 passed (69 DOM-04/05 + 28 DOM-06) | verde — **última medición en runtime: DOM-06** |
| `modules/competencias/tests` | 43 funciones ESCRITAS | **NO ejecutadas** |
| `modules/patrocinadores/tests` | 53 funciones ESCRITAS | **NO ejecutadas** |
| `core/tests` (reconciliación A0 de DOM-03) | 86 casos parametrizados ESCRITOS + 7 modificados | **NO ejecutados** |
| Frontend `Aplicacion/frontend` | UI-01A: `vitest` 248 passed / **5 failed** (token-guard preexistentes, corregidos después por FND-06 y **nunca re-ejecutados**) · `tsc` 0 · `biome` 0 · `next build` 0 · sonda HTTP todas 200 | auditoría de navegador de cinco anchos **ABIERTA** |

**Balance en `Aplicacion/backend`:** **549** funciones ejecutadas y verdes en su ventana · **137** ESCRITAS y NO
ejecutadas (41 DOM-03 + 43 DOM-07 + 53 DOM-08) · **86** casos parametrizados compartidos ESCRITOS y NO
ejecutados · **686** funciones escritas en total. **La suite de la raíz completa NO se midió** en la ventana de
DOM-06 (sólo la del módulo): la última cifra global conocida es **432 passed** (2ª reconciliación A0 de FND-01)
y **487 passed · 2 failed** (DOM-02, ambos de A0) — **ninguna es una medición actual**.

---

## 4. Outstanding warnings (open)

1. `modules/salesianos_fest` tiene un cambio de modelo pendiente (`0004_alter_comprapase_token_revocado_en`) →
   la puerta global `makemigrations --check --dry-run` **falla** (DOM-06 A0-07).
2. Controllers **no registrados** (BLOQUEANTES): `InventarioController` + `PedidoController` (DOM-06) ·
   `CompetenciasController` (DOM-07) · `PatrocinadorController` (DOM-08). Hasta entonces esas rutas **no existen**.
3. Versiones de contrato sin registrar: `competencias` `1.0.0` · `patrocinadores` `1.0.0`.
4. Códigos públicos sin catalogar: 8 (DOM-06) · 21 (DOM-07) · 4 (DOM-08).
5. Ledger (`FR-07` §3.3) y `SH-05` sin ratificar: `RT-PS-01`…`RT-PS-08` · `RT-MK-08`…`RT-MK-12` · las 16 de
   DOM-07 · `RT-MD-02` (`OD-A0R3-01`, `OD-A0R2-02`).
6. Decisiones abiertas sin inventar: `OD-A0R3-02` (canal `X-Pase-Token`) · `OD-A0R3-03` (ruta de revocación de
   CORTESÍA) · `OD-A0R3-04` (las DOS definiciones de "administrador") · `OD-A0R3-05` (prosa de
   `PASE_NO_TRANSFERIBLE`) · `OD-DOM06-01` (expiración de la reserva) · `PD-01`/`PD-02`/`PD-03`.
7. **H-01** (`A0-reconciliation-dom03.md` §8): `PaseNoTransferibleError` está DEFINIDA y **no se lanza** — hallazgo
   de DOMINIO, no tocado.
8. `core.media.limpiar_archivos_media` deja directorios vacíos (DOM-08 A0-08) — raíz de A0.
9. `*.sqlite3` en el `.gitignore` del objetivo — pendiente desde FND-01.
10. `00-matriz-tareas.md` sin sincronizar (`T-010`…`T-060`) — **A0 debe sincronizarla explícitamente**.
11. FND-06 sin cerrar: 5 puertas de verificación sin ejecutar · `FND-06-IMP-R-02` (panel de auth nunca visto en
    un navegador) · `FND-06-IMP-R-03` (el `GET` de logout muta estado).

---

## 5. Reported, NOT changed

- **`FND-03A`** (autenticación: `AuthController` registrado en `config/api.py`, 4 paths vivos en el inventario de
  A0, módulo en `modules/usuarios/**`): existe en el árbol y en la evidencia de la reconciliación de DOM-03, pero
  **NO tiene fila en el tablero ni artefacto de apply-progress**. **No se le asigna estado** (sería inventarlo).
  **A0 debe abrir su fila y su artefacto.**
- `00-matriz-tareas.md` y `route-to-wrapper-ledger.csv`: raíces prohibidas.
- Árboles congelados `backend/**`, `frontend/**`, `worker/**`, `proxy/**`, `.opencode/**`, `contract/**`,
  `Aplicacion/plan/**`: **no tocados** (C4 vacío).

---

## 6. Rollback

1. Borrar `evidence/reconciliation/2026-11-19-state-reconciliation.md`.
2. Revertir las filas del tablero de la transición de este informe en `STATE.md`.
3. Restaurar los topics #11228 y #11227 a su contenido anterior.

Punto de rollback `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit; **no revertir ni resetear**).
**El historial comercial, de pagos y de inventario se preserva**: esta reconciliación no borra ninguna compra,
orden, transacción, acta ni movimiento de bitácora.

---

## 7. Next dependency

**API-03** y **XCT-01** — tras la ratificación de las rutas provisionales (A0-01, A0-04) y el congelamiento del
presenter de entrega. En paralelo, y **sólo con autorización explícita del usuario**: la verificación diferida con
`uv run` de **DOM-03**, **DOM-05**, **DOM-07** y **DOM-08**, y el apply **sólo-verificación** de **FND-06** (lo
que cierra formalmente ese paquete).
