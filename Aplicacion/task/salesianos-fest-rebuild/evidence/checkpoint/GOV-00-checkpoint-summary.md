# GOV-00 — Checkpoint no destructivo y manifiesto de `Aplicacion/`

**Paquete:** `GOV-00-checkpoint-manifest` · **Cambio:** `salesianos-fest-rebuild` · **Proyecto:** Salesianos
**Fecha:** 2026-11-18 · **Modo:** solo evidencia · **Propietario:** A0 + producto
**Tarea de plan:** `T-000` (validar decisiones y mantener pendientes explícitos)

> Este documento es evidencia. No es especificación ni producto. No se modificó código de producto.

---

## 1. Propósito y alcance ejecutado

Se levantó evidencia de partida antes de cualquier implementación objetivo: rama, HEAD, estado completo
del árbol, manifiesto `path/bytes/SHA-256/tracked/class` de `Aplicacion/`, clasificación por destino,
fuentes de rollback, responsables de decisiones no resueltas y línea base de identificadores de tarea.

**Resultado:** cero cambios de producto, cero borrados, cero movimientos, cero renombrados.

---

## 2. Conjunto normativo leído (orden de lectura obligatorio)

| # | Artefacto | Lectura |
|---|---|---|
| 1 | `AGENTS.md` (raíz) | completa |
| 2 | `contract/api-wrapper-presenter-contract.md` | completa |
| 3 | `contract/django-app-architecture-contract.md` | completa |
| 4 | `contract/next-app-architecture-contract.md` | completa |
| 5 | `contract/PLAN_REFACTORIZACION.md` | completa |
| 6 | `contract/SCHEMA_DRY_INTENTION.md` | completa |
| 7 | `contract/smart.md` | completa |
| 8 | `contract/TEST_ARCHITECTURE_CONTRACT.md` | completa |
| 9 | `Aplicacion/plan/salesianos-fest-rebuild/README.md` | completa |
| 10 | `Aplicacion/plan/salesianos-fest-rebuild/00-decisiones-y-alcance.md` | completa |
| 11 | `Aplicacion/plan/salesianos-fest-rebuild/implementacion/01-arquitectura-y-dependencias.md` | completa |
| 12 | `Aplicacion/plan/salesianos-fest-rebuild/implementacion/02-plan-de-tareas-y-agentes.md` | completa |
| 13 | `Aplicacion/task/salesianos-fest-rebuild/00-contrato-global-de-apply.md` | completa |
| 14 | `Aplicacion/task/salesianos-fest-rebuild/00-olas-paralelas.md` | completa |
| 15 | `Aplicacion/task/salesianos-fest-rebuild/wave-00-governance/GOV-00-checkpoint-manifest.md` | completa |
| 16 | `Aplicacion/task/salesianos-fest-rebuild/wave-00-governance/GOV-01-contract-freeze.md` | completa (próximo paquete) |
| 17 | `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | completa |
| 18 | Engram `sdd/explore/salesianos-fest-rebuild-plan-review` (#11211) + apéndice (#11213) | completa (no truncada) |
| 19 | `Aplicacion/documentacion/00-cobertura-y-trazabilidad.md` | referenciada como evidencia de estado actual, no como especificación |

**Precedencia aplicada:** `contract/` > plan objetivo > paquete ejecutable > documentación de estado actual > código actual.

---

## 3. Checkpoint: T0 (inicio de paquete) y T1 (checkpoint observado)

El estado del repositorio **cambió durante la ejecución de este paquete** por una acción concurrente ajena a
GOV-00. Se registran ambos puntos; ninguno fue provocar.

### 3.1 T0 — línea base al abrir el paquete

| Dato | Valor |
|---|---|
| Raíz del repositorio | `C:/Users/Usuario/Desktop/Aplicaciones/CST/Salesianos` |
| Rama | `master` |
| HEAD | `eb17e7bdc837130fe715c863cd968eca03be19ba` (`betha 2`) |
| `git status --short` | **74 líneas**: 49 `M` (modificados) + 25 `??` (entradas no rastreadas) |
| `git ls-files Aplicacion` | **0** (el árbol completo estaba fuera del índice) |

Detalle de las 74 líneas de T0 (capturadas antes de cualquier escritura de este paquete):

- `M` (49): `.atl/.skill-registry.cache.json`, `.atl/skill-registry.md`, `backend/db.sqlite3`,
  `backend/modules/administracion/**` (21 archivos: results, selectors, services, controller, presenters,
  schemas, tests), `backend/modules/commerce/**` (3), `backend/modules/pagos/**` (9),
  `backend/modules/salesianos_fest/domain/constants.py`,
  `frontend/src/features/admin/**` (10), `frontend/src/features/pagos/**` (3).
- `??` (25): `.agents/`, `.opencode/`, `AGENTS.md`, `Aplicacion/`, `opencode.json`, `skills-lock.json`,
  y 18 rutas de código nuevas bajo `backend/` y `frontend/`.

### 3.2 T1 — checkpoint observado a mitad de paquete

| Dato | Valor |
|---|---|
| Rama | `master` (sin cambio) |
| HEAD | `f3df5401c56b41c340f257e67d5a306904a9e670` (`betha 4`, padre `eb17e7b`) |
| Autor / fecha del commit | `MicroCats37 <microcat_73@outlook.com>` — 2026-11-18 18:47:07 -0500 |
| Archivos en el commit | 644 (390 bajo `Aplicacion/`) |
| `git status --short` | **2 líneas**, ambas de este paquete (los CSV de evidencia) |
| Índice (`git diff --cached`) | 0 entradas |
| `git stash` | no usado (prohibido por norma de proyecto) |

**El commit `f3df540` absorbió el árbol sucio completo preexistente**: las 49 modificaciones y las 25
entradas no rastreadas de T0, más las 390 rutas de `Aplicacion/` que hasta T0 no estaban en el índice.

### 3.3 Consecuencia para la compuerta G1 (versionado / checkpoint)

G1 queda **cumplida de hecho** por `f3df540`, no por GOV-00. Se acepta como punto de rollback
(because it exists, it is immutable, and it is a direct child of the T0 baseline), con dos salvedades
que GOV-01 debe tener presentes:

1. **El commit no es un checkpoint de gobernanza.** Su mensaje es `betha 4`; no identifica objetivo,
   compuerta ni alcance. No debe interpretarse como revisión aprobatoria de GOV-00.
2. **El commit arrastra evidencia de este paquete.** La primera generación de
   `manifest-aplicacion.csv` y `excluded-generated-trees.csv` quedó incluida por barrido (`git add -A`),
   junto con contenido ajeno a GOV-00 (`.agents/`, `.opencode/`, `AGENTS.md`, `opencode.json`,
   `skills-lock.json`, `backend/db.sqlite3` binario). La versión vigente de los manifiestos es la
   regenerada por este paquete, que difiere de la guardada en `f3df540`.

**Nota de riesgo (fuera del alcance de este paquete, sin acción):** `backend/db.sqlite3` (base de datos
binaria) quedó dentro de un commit. No es regresión de GOV-00 —el archivo ya estaba rastreado y modificado
en T0— pero conviene que el responsable de datos decida si ese binario debe seguir versionado.

### 3.4 Estado final tras aplicar GOV-00

`git status --short` al cierre: solo archivos creados por este paquete dentro de
`Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/**` y
`Aplicacion/task/salesianos-fest-rebuild/STATE.md`. Cero entradas `D`, `R`, `C` o `??`.

---

## 4. Manifiesto

| Artefacto | Ruta | Bytes | SHA-256 |
|---|---|---:|---|
| Manifiesto por archivo | `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/manifest-aplicacion.csv` | 138 071 | `1DF80E98E982E8F7AFD766E8579E0BAC3FF3D29A77166EB1F90056CCED0D8D8A` |
| Registro de generados excluidos | `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/excluded-generated-trees.csv` | 2 643 | `C603818C4F38703012E14C0193539C93AB605EC899AEB9B44E9C78ABED22180C` |

**Cobertura:** 384 archivos de contenido propio, 6 782 988 bytes, 100 % de `Aplicacion/` salvo lo excluido.

**Columnas:** `path`, `bytes`, `sha256`, `git_tracked`, `git_ignored`, `classification`,
`source_counterpart`, `content_match`, `rollback_source`, `decision_owner`.

**Exclusiones aplicadas** (con registro en `excluded-generated-trees.csv`, 17 entradas):

| Árbol / archivo excluido | Archivos | Bytes |
|---|---:|---:|
| `Aplicacion/frontend/node_modules` | 40 819 | 690 698 642 |
| `Aplicacion/frontend/.next` | 15 498 | 1 500 332 884 |
| `Aplicacion/backend/.venv` | 13 708 | 232 223 551 |
| `Aplicacion/worker/scraper/.venv` | 17 | 509 081 |
| `Aplicacion/frontend/tsconfig.tsbuildinfo` | 1 | 403 726 |
| `Aplicacion/frontend/tsconfig.phase4.tsbuildinfo` | 1 | 163 101 |
| `Aplicacion/frontend/next-env.d.ts` | 1 | 251 |
| `__pycache__` (7 dirs) / `.pytest_cache` (2 dirs) | 34 | 77 288 |
| **Total excluido** | **70 080** | **2 424 434 696** (≈ 2,42 GB) |

Todas las exclusiones son regenerables por la cadena de herramientas y están gitignoradas. El inventario
es una fotografía de un instante: el usuario podía instalar dependencias de frontend de forma concurrente,
por lo que el tamaño de `node_modules` puede haber variado durante la medición.

**Autorreferencia:** el manifiesto excluye `Aplicacion/task/salesianos-fest-rebuild/evidence/**` para no
inventariar su propia salida. La fila de `STATE.md` conserva el hash **previo** a este paquete, que
cambia por la actualización de estado exigida por el propio paquete.

---

## 5. Clasificación

| Clase | Archivos | Significado operativo |
|---|---:|---|
| `COPY/REBUILD` | 281 | Contenido a reconstruir o copiar hacia el objetivo; se decide en FND-0x. |
| `KEEP` | 74 | Se conserva tal cual: plan (18), documentación (15), paquetes de tarea (41). |
| `QUARANTINE` | 26 | Candidatos a cuarentena; se apartan en el corte, nunca antes. |
| `NEVER-DELETE` | 3 | Secretos: nunca se borran ni se archivan como contenido. |
| `GENERATED` | 17 (excluidos) | Artefactos de build/dependencias: se regeneran, no se archivan. |
| `REVIEW` | **0** | Sin rutas sin clasificar. |
| **Total inventariado** | **384** | + 70 080 archivos generados excluidos. |

Detalle por área, fuentes de rollback y responsables: `GOV-00-classification-and-rollback.md`.

### 5.1 Candidatos a cuarentena (26)

| Ruta | Archivos | Bytes |
|---|---:|---:|
| `Aplicacion/frontend/src/components-app/**` | 18 | 105 515 |
| `Aplicacion/frontend/doc_dev/**` | 6 | 26 559 |
| `Aplicacion/frontend/explorer/**` | 2 | 19 768 |

### 5.2 Candidatos a borrado posterior (DELETE-LATER)

**0 candidatos de contenido authored.** El único material con clase `DELETE-LATER` es el árbol generado
(70 080 archivos), que es regenerable y no requiere archivo externo. Las residencias CAM que la exploración
prevía borrar (`old_seed/*.dump`, `diferencias_calculo.csv`, `fix_*.py`, `db.sqlite3.bak-*`,
`verification_report_*.md`) **existen solo en la raíz fuente congelada `backend/`**, no en `Aplicacion/`;
por tanto no son candidatos de limpieza de este cambio y no se registran aquí.

### 5.3 Nunca borrar (3)

| Ruta | Bytes | Nota |
|---|---:|---|
| `Aplicacion/.env` | 3 369 | Copia de `.env` raíz (idéntica por hash). |
| `Aplicacion/backend/.env` | 335 | Copia de `backend/.env` (idéntica por hash). |
| `Aplicacion/frontend/.env.local` | 252 | Copia de `frontend/.env.local` (idéntica por hash). |

Los tres están gitignorados, **fuera del commit `f3df540`** y fuera del archivo externo. Se restauran
reemitiendo credenciales, nunca restaurando archivo.

---

## 6. Confirmación de redacción de secretos

- **Ningún valor de secreto fue leído, impreso, copiado, hasheado en el chat ni commiteado.**
- Se aplicó una redacción **más estricta** que la exploración: el hash SHA-256 de los 3 archivos de secreto
  se calculó en disco pero se **retiene** en la evidencia (`REDACTED-SECRET-HASH-WITHHELD`), por el veto de
  `00-contrato-global-de-apply.md` ("nunca hashear secretos en el chat"). La exploración (#11213) admitía
  hashear; el contrato global manda y se aplica la lectura más restrictiva.
- `Aplicacion/frontend/.env.example` **sí** registra hash: es plantilla sin credenciales, no archivo `.env`.
- Verificación de filtración en el commit concurrente: `git show --name-only --format= f3df540` filtrado por
  `\.env` → **0 coincidencias**. `git ls-files` filtrado por `\.env` → **1** coincidencia
  (`.env.example` de la raíz, plantilla preexistente y ajena a este paquete).
- Los archivos de entorno fuente se compararon **solo por hash**, sin mostrar valores.

---

## 7. Prueba de cero borrados y cero cambios de producto

| Prueba | Resultado |
|---|---|
| Entradas `D`/`R`/`C` en `git status --short` (T0 y cierre) | 0 |
| Archivos eliminados por este paquete | 0 |
| Archivos movidos o renombrados por este paquete | 0 |
| Archivos de código de producto modificados por este paquete | 0 |
| Rutas de escritura utilizadas | `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/**` y `Aplicacion/task/salesianos-fest-rebuild/STATE.md` |
| `git stash` / variantes | no invocado |
| Commits creados por este paquete | 0 (no se solicitó) |
| `git diff --name-only -- contract Aplicacion/plan .opencode/skills .opencode/agents` | vacío |
| Archivos de `contract/**`, `Aplicacion/plan/**`, `Aplicacion/documentacion/**`, `backend/**`, `frontend/**`, `worker/**`, `proxy/**` modificados | 0 |

---

## 8. Línea base de tareas: 54 identificadores de origen

El backlog de `implementacion/02-plan-de-tareas-y-agentes.md` define **54** identificadores `T-xxx`.
No son 96. Ninguna tarea nueva se ha inventado en este paquete.

| Fase | IDs | Cantidad |
|---|---|---:|
| F0 — Contratos y UX | `T-000` … `T-007` | 8 |
| F1 — Infraestructura fundacional | `T-010` … `T-018` | 9 |
| F2 — Dominios | `T-020`–`T-023`, `T-030`–`T-032`, `T-040`–`T-043`, `T-050`–`T-052`, `T-060` | 15 |
| F2 — Frontend | `T-070` … `T-078` | 9 |
| F3 — Integración y validaciones | `T-080` … `T-086` | 7 |
| F4 — Pruebas y entrega | `T-090` … `T-095` | 6 |
| **Total** | | **54** |

Relación con los paquetes: la matriz de paquetes usa identificadores de **paquete** (`GOV-00`, `FND-01`, …,
`VER-03`), no los `T-xxx` del plan. `T-000` es el único `T-xxx` asignado a GOV-00. Los 53 restantes se
distribuyen en GOV-01 (`T-003`–`T-007`), FND-* y los paquetes de dominio/UI/API/cross-cutting/verificación.
**Los 54 `T-xxx` son la línea base de trazabilidad; el tablero de paquetes es la unidad de ejecución.**

### 8.1 Prueba del 54 frente al 96

Conteo directo sobre `implementacion/02-plan-de-tareas-y-agentes.md`:

| Medida | Resultado |
|---|---:|
| Filas de tabla que definen una tarea | **54** |
| Identificadores únicos definidos | **54** |
| Tokens `T-xxx` distintos mencionados en todo el archivo | **54** |
| Rango numérico que abarca el espacio de IDs (`T-000`…`T-095`) | 96 números |
| IDs del rango **sin fila de tarea definida** | **42** |

Los 42 huecos son: `T-008`, `T-009`, `T-019`, `T-024`–`T-029`, `T-033`–`T-039`, `T-044`–`T-049`,
`T-053`–`T-059`, `T-061`–`T-068`, `T-069`, `T-079`, `T-087`–`T-089`.

**La cifra 96 proviene de contar el espacio numérico de IDs, no las tareas definidas.** El plan define 54
tareas. Inflar los huecos a tareas produciría 42 tareas inventadas. La línea base correcta es **54**.

---

## 9. Hallazgos que corrigen el registro de exploración

La exploración (`#11211`/`#11213`) contiene afirmaciones que **no coinciden con el disco**. El manifiesto
registra la realidad; estas discrepancias se declaran para que GOV-01 no herede premisas falsas.

| # | Afirmación de la exploración | Realidad verificada | Impacto |
|---|---|---|---|
| D-1 | `Aplicacion/frontend/src` tiene 559 archivos, byte-idénticos a `frontend/src` (559/559) | **184** archivos, **184/184 byte-idénticos** y **0 divergentes**; es un **subconjunto estricto**. Faltan 375 rutas de la fuente, incluidas las 69 de CAM `_legacy-app-routes/**` y `_legacy-features/**` | Alto: el destino está incompleto, no "copiado". El árbol CAM heredado **no está presente** en el destino. |
| D-2 | `config/` y `core/` están completos e idénticos | `core/` **28/28 idénticos**. `config/` **8/10 idénticos, 2 divergentes**: `api.py` (110 líneas menos) y `settings/base.py` (15 líneas menos) | Alto: el destino es un esqueleto deliberado; `config/api.py` y `settings/base.py` son **variantes de destino**, no drift. `Aplicacion/backend/modules/` contiene **solo `__init__.py` (22 B)** → el backend objetivo no puede arrancar todavía. |
| D-3 | Hay CAM residue en el destino: `core_application/`, `docs/`, `scripts/`, `old_seed/*.dump`, `.atl/`, `db.sqlite3` | **Ninguna de esas rutas existe bajo `Aplicacion/`.** Todo ese material está en la **raíz fuente congelada `backend/`**, que es referencia de solo lectura | Medio: los candidatos de limpieza son del árbol FUENTE, no del objetivo. Ninguno está en alcance de GOV-00. |
| D-4 | `Aplicacion/backend/.env` es un "conjunto de credenciales distinto" | `Aplicacion/backend/.env` es **idéntico por hash** a `backend/.env`; `Aplicacion/.env` es **idéntico** a `.env` raíz. Hay **dos** conjuntos distintos en el origen (raíz vs backend), no tres | Bajo-medio: sigue siendo `NEVER-DELETE`, pero la justification de "rotación" cambia a "copia de origen". |
| D-5 | `Aplicacion/**` "ni está rastreado ni gitignored" → invisible a `git status` | Cierto en T0 (`git ls-files Aplicacion` = 0). **Resuelto en T1** por el commit concurrente `f3df540` (390 rutas) | Alto: la compuerta G1 está satisfecha de hecho; el riesgo operativo principal del informe de exploración está cerrado, aunque por acción externa y no por GOV-00. |

### 9.1 Divergencias de contenido dentro del destino (4 rutas)

| Ruta | Match | Lectura |
|---|---|---|
| `Aplicacion/backend/config/api.py` | `target-variant` | Registro de controladores de dominio **retirado** (110 líneas): coherente con `modules/` vacío. |
| `Aplicacion/backend/config/settings/base.py` | `target-variant` | `LOCAL_APPS` sin `modules.*`, sin `core_application`, sin `AUTH_USER_MODEL`, sin `INJECTOR_MODULES` de dominio (15 líneas). |
| `Aplicacion/backend/.env` | `redacted-not-compared` | Secreto; identidad con la fuente verificada solo por hash. |
| `Aplicacion/frontend/.env.local` | `redacted-not-compared` | Secreto; identidad con la fuente verificada solo por hash. |

El plan (`implementacion/01` §5) lista `EVENTO_ACTIVO_NOMBRE` entre lo que **no** debe heredarse sin
revisión. GOV-01 debe verificar si `settings/base.py` del destino ya resuelve ese punto o si la variante
es solo un esqueleto por desajuste de módulos.

---

## 10. Decisiones no resueltas y responsables

| ID | Decisión abierta | Bloquea | Responsable |
|---|---|---|---|
| GAP-1 | Destino de `Aplicacion/**`: ¿se rastrea de forma permanente, se reconstruye en raíz o se archiva? | Toda operación de limpieza | A0 + producto |
| GAP-2 | Congelamiento de `contract/**`: ¿se amends, o los contratos rigen sin cambios? | GOV-01, FND-* | A0 + producto |
| GAP-3 | Objetivo del corte: ¿el corte es a `Aplicacion/` o a la raíz del producto? | VER-03 | A0 + producto |
| GAP-4 | Clasificación de divergencia: `config/api.py` y `settings/base.py` son variante intencional o drift por desajuste de módulos | FND-01, FND-06 | A0 |
| D-A | Destino de 26 rutas en cuarentena (`components-app`, `doc_dev`, `explorer`): ¿se reconstruyen, se archivan o se descartan? | FND-06, FND-07 | A7 + A0 |
| D-B | 375 rutas de `frontend/src` aún no copiadas al destino, incluidas las 69 de CAM: ¿copiar, reconstruir o descartar? | FND-06 | A7 + A0 |
| D-C | Confirmar que el esqueleto de `Aplicacion/backend/modules/` (solo `__init__.py`) es intencionado y no un borrado accidental | FND-01 | A0 |
| D-D | Los 3 conjuntos de secretos: ¿se rotan, se reemiten o se conservan para el corte? | VER-03 | A0 + responsable de credenciales |
| D-E | `backend/db.sqlite3` binario versionado en `f3df540`: ¿sigue versionado? | fuera del alcance | responsable de datos |
| PD-01…PD-10 | Decisiones funcionales abiertas del plan (asignación BOX, revocación de pases, tickets, acceso, stock, reembolso, invitado, SMTP, beneficios, acciones admin) | Tareas específicas | A0 + producto (según `00-decisiones-y-alcance.md` §4) |

Ninguna de estas se convierte en decisión aprobada en GOV-00. Los `[PROPUESTO]`/`[PENDIENTE]` del plan
siguen sin ratificarse.

---

## 11. Comandos ejecutados y códigos de salida

Ejecutados desde la raíz del repositorio.

| # | Comando | Exit | Resultado |
|---|---|---:|---|
| 1 | `git rev-parse --show-toplevel` | 0 | `C:/Users/Usuario/Desktop/Aplicaciones/CST/Salesianos` |
| 2 | `git rev-parse HEAD` | 0 | `f3df5401c56b41c340f257e67d5a306904a9e670` (T0: `eb17e7b…`) |
| 3 | `git status --short` | 0 | T0: 74 líneas · T1: 2 líneas (solo evidencia de este paquete) |
| 4 | `git ls-files Aplicacion` | 0 | T0: 0 · T1: 390 |
| 5 | `git diff --name-only -- contract Aplicacion/plan .opencode/skills .opencode/agents` | 0 | vacío |
| 6 | `git diff --no-index -- backend/config/api.py Aplicacion/backend/config/api.py` | 1 | 110 líneas menos en destino (divergencia esperada) |
| 7 | `git diff --no-index -- backend/config/settings/base.py Aplicacion/backend/config/settings/base.py` | 1 | 15 líneas menos en destino (divergencia esperada) |
| 8 | `Get-ChildItem -LiteralPath "Aplicacion" -File -Recurse -Force \| Where-Object { $_.FullName -notmatch '\\(node_modules\|\.venv\|\.next)\\' } \| Get-FileHash -Algorithm SHA256` | 0 | 422 archivos / 7 524 842 B (filtro del paquete) |
| 9 | Mismo comando con exclusión ampliada de cachés y `.tsbuildinfo` | 0 | 384 archivos / 6 782 988 B (manifiesto) |
| 10 | `git check-ignore -v` sobre rutas de secreto | 0 | `.gitignore:11:.env` y `frontend/.gitignore:34:.env*` |
| 11 | `git show --name-only --format= f3df540 \| Select-String '\.env'` | 0 | 0 coincidencias → sin filtración de secretos |
| 12 | `git diff --cached --name-only` | 0 | 0 entradas |

> El comando 8 es el comando de validación literal del paquete. Se ejecutó **completo** (incluye
> `Aplicacion/.env`); su salida no se volcó al chat ni a la evidencia para no exponer el hash de un
> secreto. La salida del chat de la herramienta se redirigió a un archivo temporal fuera del repositorio
> y se resumió solo en conteos.

### 11.1 Batería de verificación de cierre

| # | Comando | Exit | Resultado |
|---|---|---:|---|
| 13 | `git status --short` (cierre) | 0 | 10 líneas: **5 de este paquete** (3 `M` + 2 `??`) y **5 de actividad concurrente del usuario** (`skills-lock.json` modificado + 6 rutas `??` de `.agents/skills/gsap-*`, installation in progress). **0** `D`/`R`/`C` |
| 14 | `git diff --name-only -- backend frontend worker proxy contract Aplicacion/plan Aplicacion/documentacion` | 0 | vacío → raíces de producto y contratos intactos |
| 15 | `git diff --cached --name-only` | 0 | 0 entradas |
| 16 | Re-chequeo de reproducibilidad del manifiesto (re-hash de las 384 filas contra disco) | 0 | **380 idénticas · 1 distinta · 0 ausentes · 3 redactadas** |

**Única fila distinta:** `Aplicacion/task/salesianos-fest-rebuild/STATE.md`. Es el resultado **esperado**:
el manifiesto se capturó antes de que este paquete actualizara el tablero de estado, que es una
obligación del propio paquete. Las otras 383 filas reproducen su hash sin diferencia.

### 11.1.1 Actividad concurrente del usuario (fuera del alcance de GOV-00)

Dos eventos ajenos a este paquete ocurren durante su ejecución y quedan registrados como tales:

1. **Commit `f3df540`** — versionó el árbol preexistente completo (ver §3.2).
2. **Instalación de skills GSAP** — durante el cierre aparecieron `skills-lock.json` modificado y seis
   rutas `??` bajo `.agents/skills/gsap-*`. Son actividad del usuario, ajena a GOV-00: **no se tocaron, no
   se versionaron, no se incluyeron en el manifiesto y no se revirtieron**.

El huella de GOV-00 sobre el repositorio es exactamente **5 rutas**, todas dentro de las raíces permitidas:

| Ruta | Acción |
|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/manifest-aplicacion.csv` | creada y regenerada |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/excluded-generated-trees.csv` | creada y regenerada |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/GOV-00-checkpoint-summary.md` | creada |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/GOV-00-classification-and-rollback.md` | creada |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | modificada |

### 11.2 Comprobaciones de seguridad de la evidencia

| Comprobación | Resultado |
|---|---|
| Archivos `.env*` en el commit concurrente `f3df540` | **0** |
| Archivos `.env*` rastreados en el índice | 1 (`.env.example` de la raíz, plantilla preexistente y ajena al paquete) |
| Hashes de secreto en la evidencia | 0 (3 archivos con hash retenido) |
| Valores de secreto leídos/impresos/commiteados | 0 |
| Árboles generados dentro del commit | 0 |

### 11.3 Checksums finales de la evidencia

| Artefacto | Bytes | SHA-256 |
|---|---:|---|
| `manifest-aplicacion.csv` | 138 071 | `1DF80E98E982E8F7AFD766E8579E0BAC3FF3D29A77166EB1F90056CCED0D8D8A` |
| `excluded-generated-trees.csv` | 2 643 | `C603818C4F38703012E14C0193539C93AB605EC899AEB9B44E9C78ABED22180C` |
| `GOV-00-classification-and-rollback.md` | 9 740 | `016C99FBFD6665518B5D662CB59326C6C0448DA507921FE48F0E157F9C2D0C94` |

> El checksum de este propio documento se registra fuera del repositorio, en el artefacto de apply-progress
> (Engram #11227), para no auto-referenciarse.

---

## 12. Desviaciones respecto del paquete y de la exploración

1. **Hashes de secreto retenidos.** El paquete pide "nunca leer valores de secreto en la evidencia"; la
   exploración admitía hashear secretos. Se aplicó la regla más estricta del contrato global (no
   hashear en chat). Consecuencia: los 3 secretos no tienen hash comparable en la evidencia; su
   identidad con la fuente se verificó por comparación de hash **fuera** de la evidencia, sin mostrar
   valores. Documentado, no silencioso.
2. **Exclusión ampliada.** El paquete excluye `node_modules`, `.venv` y `.next`; se excluyó además
   `__pycache__`, `.pytest_cache`, `*.tsbuildinfo` y `next-env.d.ts`, por la instrucción de excluir
   cachés y árboles generados. Los excluidos quedan inventariados en el registro aparte.
3. **Manifiesto sin autorreferencia.** Se excluyó `evidence/**` del propio manifiesto para evitar que el
   hash del manifiesto describa una versión anterior de sí mismo.
4. **Rollback reforzado, no weakening.** Como `f3df540` ya versionó `Aplicacion/`, la fuente de rollback
   por ruta pasa de "archivo externo pendiente" a "commit `f3df540`", que es estrictamente más fuerte.
   La columna `rollback_source` refleja el estado real.

---

## 13. Rollback de este paquete

- **Alcance:** solo los artefactos de este paquete.
- **Retirar evidencia:** eliminar `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/**`.
- **Revertir estado:** `git checkout -- Aplicacion/task/salesianos-fest-rebuild/STATE.md`.
- **Precondición:** `f3df540` debe permanecer en la historia. No revertir, reescribir ni hacer `reset`
  sobre ese commit; contiene el árbol preexistente que este paquete dejó de alterar.
- **No aplica:** nada fuera de `Aplicacion/task/salesianos-fest-rebuild/**`.

---

## 14. Siguiente paquete

**`GOV-01` — `GOV-01-contract-freeze.md`** (`T-003` … `T-007`).

Requisitos que GOV-01 hereda de esta evidencia:

1. Consumir el manifiesto como línea base y las discrepancias D-1…D-5 como hechos, no como hipótesis.
2. Verificar si `config/api.py` y `settings/base.py` del destino resuelven el alcance por edición
   (GAP-4 / D-C) o si son solo esqueleto.
3. Registrar los pendientes PD con responsable y alcance bloqueante, sin convertirlos en decisiones.
4. Mantener la congelación de contratos antes de cualquier trabajo de esqueleto de dominio o frontend.

**Bloqueos heredados:** ninguno técnico. **Decisiones abiertas heredadas:** GAP-1…GAP-4, D-A…D-E,
PD-01…PD-10 (ver §10).
