# VER-03 — Informe de archivo, verificación final y estado de las compuertas

**Paquete:** `VER-03-signoff-archive-cutover-cleanup` · **Cambio:** `salesianos-fest-rebuild` · **Proyecto:** Salesianos
**Fecha:** 2026-11-20 · **Tarea de plan:** `T-095` · **Modo:** apply-only, artefactos en Engram + evidencia física
**Propietarios:** A0 (cableado/entorno/lint) + producto (decisiones)

---

## 1. Veredicto en una línea

**El rebuild NO está listo para firma ni para corte de producción.** El objetivo está **verde en código**
(backend `1011 passed / 2 skipped`, frontend `2288/2288`, `tsc` 0, compose válido) y **el archivo de
rollback ya existe y está probado** (compuerta G4 en verde), pero **tres salidas de F4 siguen abiertas**
—techo de Biome, lane PostgreSQL y pasada de navegador a cinco anchos— y **dos decisiones de gobernanza
siguen sin ratificar** (GAP-1 y GAP-3), lo que **bloquea la primera eliminación** por la regla de orden
`G1 → G2 → G3 → (objetivo verde) → G4 → primera eliminación`.

**Ninguna ruta fue eliminada en este paquete.** 0 borrados, 0 renombrados, 0 archivos de producto modificados.

---

## 2. Comandos finales ejecutados y códigos de salida

### 2.1 Backend — workdir `Aplicacion/backend`, **sólo** `uv run --group dev`

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| B1 | `uv run --group dev python -m pytest -q` | **0** | **1011 passed, 2 skipped**, 1095 warnings, 393.44 s |
| B2 | `uv run --group dev python manage.py check` | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **baseline ambiental B7**, idéntico a VER-01 §12.2 R10 |
| B3 | `uv run --group dev python manage.py check --settings=config.settings.test` | **0** | `System check identified no issues (0 silenced).` |
| B4 | `uv run --group dev python manage.py makemigrations --check --dry-run --settings=config.settings.test` | **0** | `No changes detected` |
| B5 | Introspección del registro vivo (`config.api.get_openapi_schema()`) | **0** | **79 operaciones** (26 públicas / 53 con JWT) |

### 2.2 Frontend — workdir `Aplicacion/frontend`

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| F1 | `npx tsc --noEmit` | **0** | 0 diagnósticos |
| F2 | `npx vitest run` | **0** | **53 ficheros · 2288 passed (2288)** · 0 fallos · 90.62 s |
| F3 | `npx biome check .` | **1** | `Checked 715 files` · **445 errors** · **110 warnings** |

### 2.3 Despliegue — workdir `Aplicacion`

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| D1 | `docker compose config --quiet` | **0** | compose válido |
| D2 | `docker compose up -d --build` | **1** | **BLOQUEADO**: el demonio Docker no está corriendo (`//./pipe/dockerDesktopLinuxEngine` no existe) |
| D3 | `docker compose ps --all` | **1** | Ídem (misma causa) |
| D4 | `docker compose down` | **1** | Ídem. **Nunca** se usó `-v` |

### 2.4 Repositorio — raíz

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| R1 | `git status --short` | **0** | **259 líneas** (línea base de este paquete: 247) |
| R2 | `git diff --check` | **0** | **verde tras la reparación de integridad** (§6). Antes: **2** (5 líneas con whitespace final) |
| R3 | `git diff --name-only -- backend frontend worker proxy contract` | **0** | **vacío** → raíces congeladas intactas |
| R4 | `git diff --name-only -- Aplicacion/plan Aplicacion/documentacion` | **0** | **vacío** → plan y documentación intactos |

---

## 3. Compuertas de reversibilidad G1–G5

Definición normativa: revisión del plan `#11211` → *Cleanup Classification And Reversibility Gates*.

| Compuerta | Requisito | Estado | Evidencia |
|---|---|---|---|
| **G1** Versionado / checkpoint | árbol limpio, HEAD registrado, rama registrada | 🔴 **ROJA** | `git status --short` = **259 líneas**; HEAD `2c411cdfc062714cfa7ff39765c4357ddf8267e2` ("betha 6"), rama `master`. **El trabajo del rebuild NO está commiteado** ⇒ el único punto de retorno del estado actual es el archivo G4, no un commit. |
| **G2** Manifiesto / hash | manifiesto por archivo, re-ejecución con hashes idénticos | 🟡 **ÁMBAR** | Re-ejecutado el comando de GOV-00 (#9 y #16) → **384 filas**: **253 idénticas · 63 distintas · 65 ausentes · 3 redactadas**. Las 65 ausentes son la **residencia CAM retirada** por el propio rebuild (23 `components/portada`, 14 `components/landing`, 7 `components/event`, 4 `components/paquetes`, 3 `components/confirmationDialog`, 2 `components/branding`, 2 `components/breadcrumbs`, 2 `components/emptyState`, 2 `components`, 1 `app/(app)`, 1 `app/(auth)/register`, 1 `app/informacion`, 1 `components/genericPagination`, 1 `hooks/cache`). Las 63 distintas son el rebuild. **0 filas sin clasificar**. |
| **G3** Decisión de propiedad | GAP-1/2/3/4 **registradas como decisiones** con dueño y fecha | 🔴 **ROJA** | `GAP-1` (fate de `Aplicacion/**`), `GAP-3` (objetivo del corte), `D-A` (destino de las 26 rutas en cuarentena), `D-D` (política de los 3 conjuntos de secretos) siguen **ABIERTOS** en `FR-09` §5 y en el tablero. **No son decisión de este paquete** (dueño A0 + producto). |
| **G4** Ruta de rollback | archivo externo sin `node_modules`/`.venv`/`.next` + **restore spot-check ≥ 5 ficheros** en las 3 raíces | 🟢 **VERDE** | §4 |
| **G5** Primera aplicación no destructiva | la primera eliminación ocurre sólo con G1–G4 verdes y objetivo verde | 🟢 **CUMPLIDA** | este paquete: **0 eliminaciones** |

**Consecuencia dura:** por la regla de orden `G1 → G2 → G3 → (objetivo verde) → G4 → primera eliminación`, y porque
**G1 y G3 están rojas**, **la primera eliminación está bloqueada**. De ahí que la lista de limpieza de §7 exista
como *allowlist preparado*, no como *allowlist aplicado*.

---

## 4. G4 — Archivo de rollback (VERDE)

### 4.1 Ubicación, tamaño y checksum

| Artefacto | Valor |
|---|---|
| **Payload (ZIP)** | `C:\Users\Usuario\AppData\Local\Temp\opencode\salesianos-fest-rebuild-archive-2026-11-20\salesianos-fest-rebuild-aplicacion-2026-11-20.zip` |
| **Tamaño** | **6 944 419 bytes** |
| **SHA-256 del payload** | `2668D0088E3704A452A34B66CE3342B50FF31B46CF8FF6F467919ABC89688E8A` |
| **Entradas** | **1731** |
| **Manifiesto por fichero (artefacto *trackeado*)** | `Aplicacion/task/salesianos-fest-rebuild/evidence/archive/ARCHIVE-MANIFEST.csv` (252 956 B · SHA-256 `EBA807BC0CEAB575E939B86A10F4811C79F50D24DEF62759291D9BA7502CBE73`) |
| **Bytes archivados** | **15 907 743** |
| **Fuera del repositorio** | por diseño: un blob binario de 6,9 MB no debe versionarse. El CSV del manifiesto **sí** es texto *trackeado* y basta para el spot-check y para re-construir el payload. |

### 4.2 Cobertura y exclusiones

| Categoría | Ficheros | Bytes | Nota |
|---|---:|---:|---|
| Incluidos en el payload | **1731** | 15 907 743 | todo `Aplicacion/**` authored |
| Excluidos — árboles generados | 61 867 | — | `node_modules`, `.venv`, `.next`, `__pycache__`, `.pytest_cache`, `.ruff_cache` |
| Excluidos — ficheros generados | 3 | — | `*.tsbuildinfo` (2), `next-env.d.ts` (1) |
| Excluidos — **secretos** | 3 | — | `Aplicacion/.env`, `Aplicacion/backend/.env`, `Aplicacion/frontend/.env.local` |
| Excluidos — `biome_baseline_tmp/**` | 41 | 220 260 | scratch **no trackeado** por el rollback; ver §7 |

**Reconciliación:** 1731 + 61 867 + 3 + 3 + 41 = **63 645** ficheros vistos bajo `Aplicacion/` ⇒ **cuadra exactamente**.

### 4.3 Integridad del archivo

| Prueba | Resultado |
|---|---|
| Entradas del ZIP vs. filas del manifiesto | **1731 = 1731**, **0 ausente**, **0 extra** |
| Entradas de secreto en el ZIP | **0** (sólo 1 plantilla `.env.example`) |
| Valores de secreto leídos/impresos/commiteados | **0** |

### 4.4 Restore spot-check — 6/6 PASS sobre las 3 raíces

| # | Raíz | Fichero | Bytes | Hash del archivo = manifiesto | Hash del disco = manifiesto |
|---:|---|---|---:|---|---|
| 1 | backend | `Aplicacion/backend/config/api.py` | 9 867 | ✅ | ✅ |
| 2 | backend | `Aplicacion/backend/core/exceptions.py` | 62 376 | ✅ | ✅ |
| 3 | backend | `Aplicacion/backend/modules/salesianos_fest/presentation/presenters/catalogo_presenter.py` | 7 842 | ✅ | ✅ |
| 4 | frontend | `Aplicacion/frontend/src/features/inscripciones/services/catalogo.service.ts` | 5 712 | ✅ | ✅ |
| 5 | frontend | `Aplicacion/frontend/src/shared/utils/query-keys.ts` | 2 794 | ✅ | ✅ |
| 6 | integración (`proxy`) | `Aplicacion/proxy/nginx.conf` | 5 419 | ✅ | ✅ |

### 4.5 Prueba de rollback (no sólo de lectura)

Se extrajo el fichero #1 del ZIP a un destino de restauración simulado
(`…/restore-spotcheck/ROLLBACK-TARGET/Aplicacion/backend/config/api.py`) y se volvió a hashear:
**hash restaurado = `0CAF82E681D6D6C492385F697FCEFFBC38F75542F079FAB52819B72FC8F0EFAD` = hash del manifiesto ⇒ PASS.**

**Instrucción de rollback probada y ejecutable** (§8.2).

---

## 5. Cero secretos y cero contaminación de referencia congelada

| Prueba | Método | Resultado |
|---|---|---|
| **Valores de `SECRET_KEY` / `IZIPAY_KEY` / `IZIPAY_SHOP_ID` en el árbol** | escaneo de 1731 ficheros de texto; los valores se cargaron **sólo en memoria** y **nunca se imprimieron** | **0 ficheros** ⇒ ✅ ningún secreto real en fichero versionable |
| **Literales de credencial en código** | `git grep -E "(IZIPAY_KEY\|SECRET_KEY\|IZIPAY_SHOP_ID\|api_key\|apikey\|DB_PASSWORD)\s*[:=]\s*<16+ chars>"` sobre backend/frontend/proxy/worker | **0** |
| **Entradas de secreto en el archivo** | nombres de entrada del ZIP | **0** |
| **Contaminación por raíz congelada** | `git grep -E "(\.\./)+(frontend\|backend\|worker\|proxy)/"` y rutas absolutas | **0** |
| **`BASE_DIR` del objetivo** | `config/settings/base.py` | `Path(__file__).resolve().parent.parent.parent` ⇒ resuelve a `Aplicacion/backend`, **no** a la raíz congelada |
| **Contextos de build del compose** | `Aplicacion/docker-compose.yml` | `.`, `frontend`, `worker/scraper` ⇒ **todos relativos a `Aplicacion/`** |
| **Rutas congeladas modificadas** | `git diff --name-only -- backend frontend worker proxy contract` | **vacío** |
| **Plan / documentación modificados** | `git diff --name-only -- Aplicacion/plan Aplicacion/documentacion` | **vacío** |

### 5.1 Hallazgo de seguridad residual (severidad **BAJA**, dueño A0)

El único valor sensible que sí aparece literal en ficheros versionables es la **contraseña por defecto de
desarrollo del compose** (`POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}`), presente en **7 ficheros**:

| Fichero | Papel |
|---|---|
| `Aplicacion/docker-compose.yml` | **origen** del valor por defecto |
| `Aplicacion/backend/config/settings/base.py` | valor por defecto del backend |
| `Aplicacion/backend/docker/entrypoint.sh` | valor por defecto del entrypoint |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | evidencia (cita el valor por defecto) |
| `…/evidence/cross-cutting/XCT-03-payment-media-notifications.md` | evidencia |
| `…/evidence/verification/VER-01-baseline-regression-payments.md` | evidencia |
| `…/evidence/verification/VER-02-e2e-ux-security.md` | evidencia |

**No es una credencial filtrada**: es el valor por defecto **público** del propio compose, y los 3 ficheros
de configuración lo declaran como *fallback* precisely para el arranque local. **El riesgo real es otro**: si
`DB_PASSWORD` no se define en el despliegue, el compose **arranca con esa contraseña por defecto**. Se registra
como **hallazgo BAJA con dueño A0**: *eliminar el fallback (`${DB_PASSWORD:?DB_PASSWORD es obligatorio}`)*
antes de cualquier despliegue real. **No se modificó** `docker-compose.yml` (raíz compartida propiedad de A0 y
fuera de las raíces de edición de este paquete).

**Los 4 ficheros de evidencia** que citan el valor por defecto se **conservan sin reescribir**: no son secretos,
y reescribir evidencia histórica de otros paquetes sin decisión del dueño es exactamente lo que `A0-VER01-01`
prohíbe (corrección con constancia, no borrado silencioso).

---

## 6. Corrección de metadatos de rollback con nota auditable

### 6.1 Qué estaba roto

`VER-01` §12.6 abrió la petición **`A0-VER01-01`**: los paquetes heredaban un SHA de rollback que **no existe
como objeto git**, y por tanto un punto de retorno **inejecutable**. `VER-01` no podía cerrarla (la evidencia
de otros paquetes está fuera de sus raíces). `VER-03` **es** el paquete dueño del tablero `STATE.md`.

Comprobación con `git cat-file -e`:

| SHA en las entradas históricas | ¿Objeto git? |
|---|---|
| `f3df5401c56b41c340f257e67d5a306904a9e670` (real, "betha 4") | ✅ **EXISTE** |
| `f3df5401c56b61c340f257e67a5a306904e9e670` (typo histórico) | ❌ **NO EXISTE** |
| `f3df5401c56b41c340f257e67a5a306904e9e670` (variante del typo) | ❌ **NO EXISTE** |

**5 punteros de rollback rotos** en `STATE.md` (3 con la forma `b61c340…`, 2 con `…a5a306904e9e670`), más
**12 caracteres de control** (5 × `U+0007`, 5 × `U+000C`, 2 × `U+001B`) y **5 cortes de línea** que habían
**comido la primera letra** de las líneas siguientes (`ast.parse`, `admin…`, `features…`, `evento`, `edicion`,
`npx tsc`, `npx vitest`, `npx biome`, `next build`, `reutilizada`).

### 6.2 Qué se corrigió (lista exhaustiva, 20 correcciones)

| # | Corrección | Cantidad | Efecto |
|---:|---|---:|---|
| 1 | `U+0007` → `a` | 5 | `admin_operacion_schemas.py`, `ast.parse`, `admin)`, `admin.E108` ×2 |
| 2 | `U+000C` → `f` | 5 | `f3df540…`, `features/admin/auditoria/**`, `features/admin/personas/**`, `features/inscripciones/**`, `features/competencias/**` |
| 3 | `U+001B` → `e` | 2 | `evento`, `edicion` |
| 4 | Rejoin de líneas partidas | 5 | `categoria nullable, reutilizada opcional).` · `· npx tsc --noEmit` · `· npx vitest run` · `· npx biome check` · `· next build` |
| 5 | SHA de rollback → SHA real | 5 | los 5 punteros de `**Rollback point:**` ahora resuelven a `f3df5401c56b41c340f257e67d5a306904a9e670` |
| 6 | Whitespace final eliminado | 5 líneas | `git diff --check` pasa de **exit 2** a **exit 0** |

**Constancia, no borrado silencioso:** cada corrección queda registrada en la transición de VER-03 (§9 de este
informe y en la transición correspondiente de `STATE.md`), con el SHA bueno y la fecha. La **cita** del typo
dentro de la evidencia de VER-01 (que *describe* el error) se dejó **intacta a propósito**: es una cita, no un
puntero.

**Antes / después:** `git diff --check` **exit 2 → exit 0**; `git grep -oE "f3df5401c56[0-9a-f]{27,41}"` sobre
todo `Aplicacion/task/salesianos-fest-rebuild/**` → **465 ocurrencias, todas del SHA real**, **0** variantes rotas.

---

## 7. Remitente a la lista de limpieza

La lista explícita de limpieza (con clase, condición, fuente de rollback y comando) está en
[`../cutover/VER-03-cleanup-allowlist.md`](../cutover/VER-03-cleanup-allowlist.md).
**Ninguna ruta de esa lista fue eliminada en este paquete** (G1 y G3 rojas, §3).

---

## 8. Procedimiento de rollback

### 8.1 Disparador

**Rollback si**: falla el smoke del corte de producción · falla un caso crítico de QA · se detecta una fuga
de datos o de permisos en el despliegue · o el PRODUCTO rechaza el corte (GAP-3) una vez la decisión esté tomada.

### 8.2 Procedimiento probado (orden de operaciones)

1. **No usar `git stash` ni variantes** (prohibido por norma de proyecto).
2. **Dejar la evidencia intacta**: `evidence/archive/**`, `evidence/cutover/**` y la transición de `STATE.md` **no**
   se borran al revertir (son el registro de lo que pasó).
3. **Restaurar el artefacto de producto** desde el archivo G4:
   ```powershell
   $zip = "C:\Users\Usuario\AppData\Local\Temp\opencode\salesianos-fest-rebuild-archive-2026-11-20\salesianos-fest-rebuild-aplicacion-2026-11-20.zip"
   # restaurar UN fichero
   Add-Type -AssemblyName System.IO.Compression.FileSystem
   $z = [System.IO.Compression.ZipFile]::OpenRead($zip)
   $e = $z.GetEntry("Aplicacion/backend/config/api.py")
   [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, "$repo\Aplicacion\backend\config\api.py", $true)
   $z.Dispose()
   ```
4. **Verificar el hash** contra `evidence/archive/ARCHIVE-MANIFEST.csv` antes y después de restaurar.
5. **Revertir el código committed** al punto de retorno `f3df5401c56b41c340f257e67d5a306904a9e670` ("betha 4")
   **con `git revert` o checkout explícito de rutas**, nunca con `reset` sobre ese commit.
6. **Revertir el despliegue**: `docker compose down` (nunca `-v`) y re-desplegar la referencia anterior.
7. **Detener la limpieza**: no borrar, no mover, no podar nada mientras el rollback esté en curso.
8. **Registrar** el rollback en `STATE.md` y en Engram (`sdd/salesianos-fest-rebuild/state`).

---

## 9. Decisiones reconciliadas (paso 1 del paquete)

| Elemento | Estado reconciliado | Dueño |
|---|---|---|
| `DEC-01`…`DEC-21` (plan `00-decisiones-y-alcance.md` §2) | **ACORDADAS** — ratificadas en el plan, sin cambios en VER-03 | A0 + producto |
| `PD-01`…`PD-10` (plan §4) | **ABIERTAS** — ninguna bloquea un freeze; bloquean reglas finales de negocio. Se **declaran** como pendientes (no se presentan como implementadas) | según `FR-09` §2 |
| `GAP-1` (fate de `Aplicacion/**`) | **ABIERTO** — bloquea toda operación de limpieza | A0 + producto |
| `GAP-2` (enmiendas a `contract/**`) | **ABIERTO** — afecta a `V-02-SEC-01` (código `INSCRIPCION_NO_AUTORIZADA` congelado en `FR-03` §2.1) | A0 + producto |
| `GAP-3` (objetivo del corte) | **ABIERTO** — **bloquea el corte y la limpieza** | A0 + producto |
| `GAP-4` (variantes de `config/api.py` / `settings/base.py`) | **RESUELTO de facto** — las divergencias eran el esqueleto destino; hoy el registro vivo es de 22 controllers y 79 rutas con DRIFT A = 0 | A0 |
| `D-A` (destino de las 26 rutas en cuarentena) | **ABIERTO** — 28 rutas siguen en cuarentena (§7) | A7 + A0 |
| `D-D` (política de los 3 conjuntos de secretos) | **ABIERTO** — **ningún secreto se archiva ni se borra**; los 3 conjuntos siguen `NEVER-DELETE` | A0 + responsable de credenciales |
| `D-B` / `D-C` / `D-E` | `D-C` **confirmado** (los módulos del destino ya no son un esqueleto); `D-B`/`D-E` siguen abiertos | A7 / responsable de datos |
| Aprobación del responsable de release (producto) | **PENDIENTE** — no hay firma de producto en el repositorio; los 3 hallazgos BAJA de seguridad tienen dueño pero no firma | Producto + A0 |
| Deuda conocida | techo de Biome, lane PostgreSQL, motor de navegador, `PD-08` (SMTP diferido), `RT-PG-05` sin dueño, `V-02-SEC-01/02/03` | A0 / A7 / A9 / Producto |

---

## 10. Ficheros cambiados por este paquete

| Fichero | Acción |
|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/evidence/archive/ARCHIVE-MANIFEST.csv` | **creado** (manifiesto por fichero del archivo, 1731 filas, 252 956 B) |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/archive/VER-03-archive-report.md` | **creado** (este documento) |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/cutover/VER-03-cutover-evidence.md` | **creado** |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/cutover/VER-03-cleanup-allowlist.md` | **creado** |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | **modificado** (fila VER-03 + transición + nota de corrección de integridad §6) |

**Fuera del repositorio (temporal, nada commiteado):**
`C:\Users\Usuario\AppData\Local\Temp\opencode\ver03\` (scripts de medición, salidas de inventario de rutas,
copia previa de `STATE.md`) y
`C:\Users\Usuario\AppData\Local\Temp\opencode\salesianos-fest-rebuild-archive-2026-11-20\` (**el archivo G4**).

**Cero** ficheros de producto modificados. **Cero** eliminaciones. **Cero** commits. `git stash` no invocado.

---

## 11. Criterios de aceptación del paquete

| Criterio | Estado |
|---|---|
| «Product/A0 sign-off, green verification, archive checksum, restore spot-check, cutover evidence, and rollback trigger all exist» | 🟡 **parcial** — verificación verde, checksum de archivo, spot-check 6/6, evidencia de corte y disparador de rollback **existen**; la **firma de producto/A0 falta** y el corte **no es reproducible en este entorno** (Docker) |
| «Cleanup touches only approved classified paths after cutover; secrets/data/source retirement require separate approval» | ✅ — **0 eliminaciones**; 0 secretos tocados; 0 datos tocados; 0 raíces congeladas tocadas |
| «Final status/manifest and archive report identify every retained, quarantined, and removed path» | ✅ — §7 + `VER-03-cleanup-allowlist.md` inventarían **retenidas**, **en cuarentena** y **0 eliminadas** |

---

## 12. Siguiente paso

**No hay siguiente paquete.** `VER-03` es el último del DAG
(`00-olas-paralelas.md`: *05 verification/cleanup → VER-01 → VER-02 → VER-03*, compuerta *Full suites, QA
evidence, archive, cutover approval*).

Cualquier defecto post-corte o **retirada de código fuente** exige un **paquete nuevo y aprobado por separado**
(`A0-VER03-01`: cierre de Biome · `A0-VER03-02`: lane PostgreSQL · `A0-VER03-03`: motor de navegador ·
`A0-VER03-04`: decisión GAP-3 + D-A + D-D · `A0-VER03-05`: eliminar el fallback de `DB_PASSWORD` ·
`A0-VER03-06`: registrar las 4 rutas sin contraparte o aceptar su retirada).
