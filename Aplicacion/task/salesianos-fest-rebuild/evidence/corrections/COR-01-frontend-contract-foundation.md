# COR-01 — Corrección de los bloqueos de contrato y de fundación del frontend probados por VER-01

**Artifact:** `evidence/corrections/COR-01-frontend-contract-foundation.md` ·
**Packet:** `COR-01` (apply correctivo, paralelo) · **Origen:** `VER-01` §6.2 (frontend) ·
**Change:** `salesianos-fest-rebuild` · **Owner:** A7 · **Store:** engram + evidencia física ·
**Fecha:** 2026-11-20 · **Tarea de origen:** las filas 11-21 y 34-36 de `evidence/verification/VER-01-baseline-regression-payments.md`

> **ESTADO: `implementation applied` — VER-02 NO queda desbloqueado.**
> Los **15 fallos de contrato/fundación** que VER-01 probó en las 7 suites de frontend están
> **corregidos y verificados** (`npx tsc --noEmit` exit **0**; 8 ficheros de test enfocados;
> **69/69** verdes). Los **25 fallos restantes** de VER-01 §6.2 son de **presentación**
> (copy del servidor, `scope` de columnas, acción «Reintentar», objetivos táctiles de 44 px,
> variables CSS, navbar) y los posee la **corrección paralela de presentación/UI**: **este
> packet no los toca**.
>
> **`STATE.md` NO se editó** (lo reconcilia el dueño de VER-01). Engram:
> `sdd/salesianos-fest-rebuild/cor-01-apply-progress` (#11483).

---

## 1. Alcance y raíces permitidas

| Permitido | Tocado |
|---|---|
| `Aplicacion/frontend/src/components/genericForm/**` | sólo el test del ciclo de vida |
| Raíces de query keys/caché de FND-08 | `src/shared/utils/query-keys.ts` (+ su test) |
| Esquemas/servicios/factorías de keys de los features implicados | `features/admin/auditoria/schemas/auditoria-admin.schema.ts`, `features/auth/schemas/identidad.schema.ts` |
| Tests enfocados de los features implicados | `validaciones`, `pases`, `marketplace` |

**NO tocado:** backend · `contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**` ·
shell compartido (`components/shell/**`) · globals (`globals.css`) · frontend de referencia
(`frontend/**`, raíz congelada) · `STATE.md`. **Cero** operaciones de git (`stash`/`commit`/`reset`/
`checkout`). **Cero** instalaciones. El trabajo concurrente de otros agentes en el árbol se dejó intacto.

---

## 2. Medición: el encargo nombraba 13; se midieron 15

El encargo nombraba «7 fallos de espejo Zod + 3 de query keys + 3 del `GenericForm` = 13». La corrida
enfocada de las 7 suites de VER-01 §6.2 mide **15** fallos: los 13 nombrados **más 2** de la misma
familia de contrato (cliente↔presenter en `pase`/`marketplace`), que **no** son de presentación.
Se corrigieron **los 15**: los 13 del encargo más los 2 restantes, en las mismas raíces permitidas.

| Familia | Medidos | Ficheros |
|---|---:|---|
| Espejo Zod | **7** | `validacion-contrato` (4) · `validacion-mirrors` (1) · `auditoria-admin-estados` (1) · `identidad-sesion-integration` (1) |
| Query keys (FND-08) | **2** | `pase.service` (1) · `marketplace.service` (1) |
| Contrato cliente↔presenter (API-03) | **3** | `pase.service` (2) · `marketplace.service` (1) |
| `GenericForm` (FND-07) | **3** | `generic-form.lifecycle` (3) |
| **Total** | **15** | |

---

## 3. Libro de fallos: causa raíz medida y dueño real

> Los diagnósticos de VER-01 §6.2 son hipótesis de una línea. **Cada uno se volvió a medir contra el
> presenter del backend** antes de tocar nada: seis de los quince BOMBAS de VER-01 eran en realidad
> **defectos de fixture**, y dos diagnósticos de VER-01 resultaron incorrectos.

| # | Suite / caso | Causa raíz MEDIDA | Dueño real | Tipo |
|---:|---|---|---|---|
| 1 | `validacion-contrato` · «acepta la forma congelada de la vista previa» | `UUID = "11111111-2222-3333-4444-555555555555"` **no es un UUID**: los bits de variante son `4` (reservados por RFC 4122). El espejo declara `z.string().uuid()` y el presenter publica `str(UUID)` canónico | dato de test | test |
| 2 | `validacion-contrato` · «acepta una vista previa que no se puede canjear» | ídem | dato de test | test |
| 3 | `validacion-contrato` · «acepta la forma congelada del canje» | ídem (`validacion_id`) | dato de test | test |
| 4 | `validacion-contrato` · «exige el envelope de éxito con sus cuatro claves» | ídem | dato de test | test |
| 5 | `validacion-mirrors` · «el derecho de entrada se REUSA del dueño del lote» | `persona_id = "7e1f2a3b-4c5d-6e7f-8091a2b3c4d5e6f"` tiene grupos `[8,4,4,15]`: **no es un UUID** (le falta un guion y un carácter). El espejo **sí** modela la referencia al dueño del lote: el diagnóstico de VER-01 (fila 15) es **incorrecto** | dato de test | test |
| 6 | `auditoria-admin-estados` · «el espejo RECHAZA un acta con el contexto crudo» | `auditoriaItemSchema` era `z.object()`: en Zod v4 una clave desconocida se **elimina en silencio**, así que un `contexto` crudo (una contraseña) pasaba. El acta publica una **LISTA BLANCA** y `AuditoriaItemOut` declara exactamente 8 campos | **XCT-02 (producción)** | **producción** |
| 7 | `identidad-sesion-integration` · «la entrada de la confirmación declara sus campos y sus límites» | `PersonaConfirmarInSchema.genero` era `z.string().max(1)`: acepta `"X"`. El vocabulario es del **DOMINIO** (`GeneroChoices` = `M`/`F`), no una longitud | **FND-03 (producción)** | **producción** |
| 8 | `pase.service` · «una edición ausente es la misma entrada que ninguna» | `buildQueryKey` emitía `["pase","catalogo",{}]`: la lectura sin edición y la lectura con `edicion_id: undefined` eran **DOS entradas de caché** para la MISMA petición. Contradice la regla escrita de FND-08 §3 regla 2 | **FND-08 (producción)** | **producción** |
| 9 | `marketplace.service` · «un filtro ausente es la misma entrada que ninguno» | ídem (`["marketplace","catalogo","productos",{}]`) | **FND-08 (producción)** | **producción** |
| 10 | `marketplace.service` · «el detalle se pide por el identificador del producto» | El mock devolvía `{id:"x"}`; el espejo del `ProductoDetalleOut` (19 campos) lo rechaza con ruido. El espejo **es** 1:1 con el presenter | dato de test | test |
| 11 | `pase.service` · «la lectura de la compra viaja con el token en la cabecera» | El mock devolvía el **catálogo** en la lectura de la **compra**; el espejo del `PaseCompraDetalleOut` lo rechaza (y con él, la credencial) | dato de test | test |
| 12 | `pase.service` · «el token nunca viaja en la query string» | ídem | dato de test | test |
| 13 | `generic-form.lifecycle` · «lets Zod own the coercion: a number travels as a number» | El schema del harness declaraba `titulo: z.string()` **obligatorio** y el caso no lo rellena ⇒ **Zod bloquea el envío** (`contract/smart.md` §1.A y §5.1) ⇒ `onSubmit` 0 llamadas. **La producción es correcta** | dato de test | test |
| 14 | `generic-form.lifecycle` · «hands the File over untouched» | ídem | dato de test | test |
| 15 | `generic-form.lifecycle` · «calls setError EXACTLY ONCE per field» | (a) el schema inválido impedía el envío y (b) el harness re-instalaba el espía en **cada render**, encadenando espías ⇒ la MISMA llamada se contaba 3 veces. `GenericForm` llama `setError` **una vez por campo** | dato de test | test |

---

## 4. Cambios de PRODUCCIÓN (3 ficheros)

| Fichero | Cambio | Por qué es el cambio correcto |
|---|---|---|
| `src/shared/utils/query-keys.ts` | `buildQueryKey`: si **todos** los parámetros están ausentes, la clave es la de la familia (**sin objeto de parámetros**) | Es la regla escrita del dueño (FND-08 §3 regla 2: «un parámetro `undefined` se descarta») y la que el docstring de las factorías de `pases`/`marketplace` ya prometía. Se corrige en el **dueño**, no en cada consumidor, y evita la reaparición |
| `src/features/admin/auditoria/schemas/auditoria-admin.schema.ts` | `auditoriaItemSchema` → **estricto** (`.strict()`) | El acta es una **lista blanca**: un campo que el servidor no publica es una violación del contrato. Un `contexto` **eliminado en silencio** escondería la fuga que el acta existe para impedir |
| `src/features/auth/schemas/identidad.schema.ts` | `PersonaConfirmarInSchema.genero` → `z.enum(["M","F"] as const).nullable()` | El **dueño del vocabulario** es el dominio (`GeneroChoices`), igual que el tipo de documento es `DNI`/`CE`/`PAS`. `register.schema.ts` ya declara `z.enum(["M","F"])`. Sin consumidores en producción (0 blast radius) |

## 5. Cambios de TEST (5 ficheros) — fixtures escritas y NUNCA ejecutadas

| Fichero | Cambio |
|---|---|
| `src/features/validaciones/__tests__/validacion-contrato.test.ts` | Identificadores de ejemplo → **UUID canónicos** (`11111111-2222-4333-8444-555555555555`) |
| `src/features/validaciones/__tests__/validacion-mirrors.test.ts` | `persona_id` → UUID canónico (`7e1f2a3b-4c5d-6e7f-8091-a2b3c4d5e6f7`) |
| `src/features/pases/__tests__/pase.service.test.ts` | La lectura de la compra se responde con la forma de `PaseCompraDetalleOut` (`COMPRA`) |
| `src/features/marketplace/__tests__/marketplace.service.test.ts` | El detalle se responde con la forma de `ProductoDetalleOut` (`PRODUCTO`) |
| `src/components/genericForm/__tests__/generic-form.lifecycle.test.tsx` | `titulo` **opcional** en el schema del harness (los tres casos envían un formulario sin título) y el espía de `setError` se instala **una sola vez** (`useRef`) |
| `src/shared/utils/__tests__/query-keys.test.ts` | **+1 caso** que fija la regla del dueño: una lectura sin parámetros es la de la familia |

---

## 6. Comandos / códigos de salida

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio (0 diagnósticos) |
| V2 | `npx vitest run` (8 ficheros enfocados: los 7 de VER-01 §6.2 + `shared/utils/__tests__/query-keys.test.ts`) | `Aplicacion/frontend` | **0** | **8 passed (8) · 69 passed (69)** — antes: 15 failed / 47 passed (62) |
| V3 | `npx vitest run` (radio de impacto: `src/shared`, `src/hooks/callsApi`, `src/hooks/cache`, `inscripcion-transporte`, `admin/operaciones`, `admin/auditoria`, `auth`, `pases/__tests__`, `marketplace/__tests__`, `validaciones/__tests__`, `genericForm`) | `Aplicacion/frontend` | **1** | **3 failed / 16 passed (19 ficheros) · 10 failed / 216 passed (226)** — los **10** son los **objetivos táctiles de 44 px** (VER-01 §6.2 filas 1-10; UI-03/UI-04/API-03): **preexistentes y fuera del alcance**. **0 regresiones** |
| V4 | `git status --short -- Aplicacion/frontend/src` | raíz | 0 | 9 ficheros de este packet; el resto del árbol con cambios de **agentes concurrentes**, intactos |

**NO ejecutado (por instrucción del encargo):** `vitest` completo · `next build` · `npm install` · `biome` ·
servidores · navegador · `git stash`/`commit`/`reset`/`checkout`.

---

## 7. Desviaciones

| # | Desviación | Motivo |
|---|---|---|
| D-COR-01-01 | Se corrigieron **15** fallos, no 13 | Los 2 restantes son de la **misma familia de contrato** (cliente↔presenter en `pase`/`marketplace`), en las raíces permitidas, y **no** son de presentación. Dejarlos abiertos mantendría bloqueado a VER-02 |
| D-COR-01-02 | 8 de las 15 correcciones son en **fixtures de test** | En 6 de ellas la **producción es correcta** y el defecto era el dato o el harness (un UUID inválido, un mock de otra forma, un schema que invalida el formulario, un espía re-instalado). Afirmar lo contrario sería untrue: cada caso se contrastó con el presenter del backend (`pase_schemas.py` → `PaseCompraDetalleOut`, `producto_schemas.py` → `ProductoDetalleOut`, `persona_schemas.py` → `PersonaConfirmarIn`, `admin_auditoria_schemas.py` → `AuditoriaItemOut`) |
| D-COR-01-03 | `genero` del mirror es **más estricto** que el wrapper HTTP (`str \| None`, `max_length=1`) | El **dueño del vocabulario** es el dominio (`GeneroChoices`); `register.schema.ts` ya declara `z.enum(["M","F"])`. Sin consumidores en producción |
| D-COR-01-04 | La regla de `salesianos-feature-architecture` («edita `frontend/src`, nunca `Aplicacion/frontend`») está **desfasada** | Igual que ya declaró FND-08 (D-FND08-07): en este rebuild `Aplicacion/frontend` es el **destino** y `frontend/**` es la raíz congelada de sólo lectura (`git ls-files`: 777 ficheros versionados en `Aplicacion/frontend`, 613 en `frontend/`) |

## 8. Bloqueos que quedan (con dueño)

| Bloqueo | Dueño | Estado |
|---|---|---|
| **25 fallos de presentación/UI** de VER-01 §6.2 (filas 1-10, 22-39) | **corrección paralela de presentación/UI** | **ABIERTO — fuera del alcance de COR-01** |
| `B-F1` · `catalogo_presenter.py:110` lee `result.paqueta_id` (el resultado expone `paquete_id`) ⇒ **HTTP 500** en `POST /cotizaciones` | DOM-01 / A0 | abierto (backend) |
| `A0-XCT02-01` · `modules.administracion` sin registrar ⇒ **7 endpoints** que el frontend ya consume no existen | A0 | abierto |
| `A0-API02-09` · `CotizacionController` sin registrar | A0 | abierto |
| Techo de Biome (441 errores / 110 avisos sobre 714 ficheros) | A0 + A7 | abierto |
| Lane PostgreSQL no ejecutada (`select_for_update` es NO-OP en SQLite ⇒ el riesgo de XCT-01 §7.1 sigue abierto) | A0 + A9 | abierto (entorno) |

**VER-02 sigue BLOQUEADO.** La contribución de COR-01 es que los **15 bloqueos de contrato/fundación
del frontend** que VER-01 probó quedan cerrados y verificados, y que los 25 de presentación quedan
explícitamente asignados a su dueño.

## 9. Rollback

1. Revertir los **9 ficheros** de §4 y §5: 8 versionados +
   `src/features/admin/auditoria/schemas/auditoria-admin.schema.ts` (que vive en un directorio
   **sin versionar** del árbol de XCT-02, así que su reversión es manual).
2. Borrar este fichero.
3. En Engram: retirar el topic `sdd/salesianos-fest-rebuild/cor-01-apply-progress` (#11483).
4. **NO** revertir ni resetear ningún commit: COR-01 **no creó ningún commit**. El punto de rollback es
   el HEAD real (`2c411cdfc062714cfa7ff39765c4357ddf8267e2`, "betha 6"), que ya existía y no cambió.
