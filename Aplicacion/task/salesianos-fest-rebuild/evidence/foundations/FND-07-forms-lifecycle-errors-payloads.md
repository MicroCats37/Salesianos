# FND-07 — Ciclo de vida del formulario, errores de campo 422 y semántica de payload

**Paquete:** `wave-01-foundations/FND-07-forms-lifecycle-errors-payloads.md` · **Owner:** A0 + A7
**Estado:** `implementation applied` — **NO cierra el paquete** (verificación en runtime diferida)
**Tarea de origen:** ninguna (paquete de divergencia de construcción required para los paquetes de frontend posteriores)
**Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit creado; `git stash` nunca invocado)
**Fecha:** 2026-11-19

---

## 1. Contexto obligatorio leído

| Fuente | Qué aporta a este paquete |
|---|---|
| `contract/smart.md` | §1 el GenericForm es el orquestador; §2 el Smart Field es un adaptador bidireccional; §5.2 **prohibido** el `watch()` indiscriminado; §5.4 la limpieza del `handleFormSubmit` no puede destruir el `File` |
| `contract/next-app-architecture-contract.md` | §5 Forms: `GenericForm` posee validación y estado, las features poseen el layout; §5 el `buildApiPayload` vive en el hook de mutación, **nunca** en el formulario; §6 imports nombrados; §7 barrels granulares sin comodín; §8 `buildApiPayload` dentro de `onSubmit` es ANTIPATRÓN; §11 la forma del error de API (`fieldErrors?: Record<string, string>`) |
| `contract/api-wrapper-presenter-contract.md` | §8 el texto de error vive en `error.message`; la validación es 422 y **debe** traer errores de campo |
| `contract/SCHEMA_DRY_INTENTION.md` | composición de schemas por bloques (sin mirror de frontend: no gobierna este paquete) |
| `contract/TEST_ARCHITECTURE_CONTRACT.md` | reglas de test del backend; el frontend se gobierna por `vitest.config.ts` |
| `evidence/contracts/FR-01-envelope-error-pagination.md` | **FREEZE-ENV-1.0.0**: `error.field_errors[]` es el **ÚNICO** canal de error por campo, cada entrada `{field, code, message}` con ruta punteada; `error.details` = contexto NO-campo |
| `Aplicacion/backend/core/responses.py` | la forma REAL del envelope (`FieldError`, `ErrorDetail`, `ApiResponse`) que consume el parser |
| `Aplicacion/backend/core/media.py` | allowlist MIME `image/jpeg`/`image/png`/`image/webp` (SVG prohibido) y tope de **5 MiB** por archivo → los valores que la UI ofrece y acepta |
| `.opencode/skills/salesianos-forms-smart-fields/` + `references/form-smart-field-matrix.md` | la matriz que declara las CUATRO divergencias que este paquete cierra y la receta del Smart Field |
| `.opencode/skills/salesianos-api-data/` | §"Build payloads in mutation hooks": create y update usan mapeos DISTINTOS; `undefined` = intacto; `null` = limpieza; nunca enviar un campo no declarado |
| `.opencode/skills/salesianos-feature-architecture/` | capas y tests colocadores; `app/**` sólo routing |
| `.opencode/skills/salesianos-responsive-a11y/` | errores asociados programáticamente, foco visible, objetivos táctiles alcanzables |
| `frontend/src/**` (raíz congelada) | **evidencia de sólo lectura**: los cuatro ficheros de este paquete eran copias byte a byte de la raíz congelada (`SHA-256` idéntico) — las divergencias eran heredadas, no nuevas |

---

## 2. Divergencias cerradas (las cuatro de la matriz)

| Divergencia (matriz) | Antes | Después |
|---|---|---|
| `GenericForm` inicializa con `initialData` una vez y no resetea | el formulario de edición se quedaba con los valores del primer render | `reset(initialData)` DETERMINISTA cuando **cambia el CONTENIDO** de `initialData` (`stableSerialize`), nunca por su referencia; una envío en vuelo no se interrumpe; un padre que devuelve los valores vivos no resetea |
| el manejo de errores no tiene un parser 422 con `fieldErrors` | `handleApiError` NUNCA devolvía `fieldErrors`: el comentario del fichero describía el formato 422 pero no había implementación | `src/errors/field-errors.ts` lee las CUATRO formas de canal de campo y las normaliza a `Record<string, string>`; `handleApiError` adjunta `fieldErrors` a **todo** error parseado; `GenericForm` llama `setError` **exactamente una vez por campo** |
| la coerción por `FieldConfig` sólo corre en los modos automáticos | el bucle de coerción (`Number()`, `Boolean()`) re-coercía el valor YA validado por Zod y destruía el `null` explícito de un campo numérico | Zod es el dueño de la coerción en TODOS los modos; la única transformación que queda es la IDENTIDAD de la opción de un `select`/`radio` (`"3"` ES la opción `3`), que no es coerción; `undefined`, `null` y `File` se preservan |
| `buildUpdatePayload` ignora `initialData`/`strict` y `GenericForm` lo aplica a las creaciones | una sola función para crear y actualizar; el diff no existía | DOS mapeos exactos y separados: `buildCreatePayload` (mapeo completo validado) y `buildUpdatePayload` (mapeo estricto, consciente de `initialData`); `GenericForm` elige con `submitMode` y una creación NUNCA usa semántica de diff |

---

## 3. Lo entregado

### 3.1 Errores de campo del backend (`src/errors/**`)

- `src/errors/field-errors.ts` (nuevo) — parser PURO, sin dependencias de React:
  - **`error.field_errors[]`** (el canal congelado): `{field, code, message}` → `{field: message}`; la ruta punteada (`beneficiarios.0.documento`) se preserva tal cual, que es la forma que espera `setError` de RHF.
  - **`detail[]`** (Django Ninja / Pydantic): `loc: ["body", "beneficiarios", 0, "documento"]` → `beneficiarios.0.documento` (se descarta el origen `body`/`query`/`path`/`form`).
  - **`errors{}`** (DRF) y **`details{}`** (mapa plano heredado de `format_errors()`).
  - `non_field_errors` **nunca** es un campo: pertenece al mensaje de formulario.
  - Un campo con DOS mensajes conserva ambos, unidos por ` • ` (el mismo separador que usa el backend en sus agregados).
- `src/errors/error-handler.ts` — `handleApiError` adjunta `fieldErrors` a **todo** resultado del parser (no sólo al 422) y construye el mensaje del `detail[]` legacy, que antes caía en el mensaje genérico. Un 422 con errores de campo y sin mensaje propio usa `"Please correct the highlighted fields."`.
- `src/errors/index.ts` — exporta el parser para que NINGÚN componente tenga que parsear un error de API por su cuenta.

### 3.2 Mapeo de payload (`src/lib/forms/**`, `src/utils/payload-builder.ts`)

| Regla | Create | Update (estricto) |
|---|---|---|
| `undefined` | omitido | omitido |
| `null` | incluido (valor explícito) | incluido (limpia un campo nullable) |
| valor igual al de `initialData` | — (no hay estado previo) | **omitido**: el usuario no lo tocó |
| `File` | incluido | incluido (reemplaza) |
| URL de un campo de archivo | omitida (no hay nada que subir) | omitida (no cambió) |
| campo NO declarado por el schema | omitido | omitido |

- `src/lib/forms/schemaShape.ts` (nuevo) — lee el shape de primer nivel del schema Zod **sin evaluarlo** y sin lanzar: `getTopLevelShape`, `isDeclaredField`, `getFieldSchema`, `isFileKindSchema`.
- `src/lib/forms/valueEquality.ts` (nuevo) — `isSameFormValue`: primitivos por valor, `Date` por instante, `File` por IDENTIDAD (dos archivos con el mismo nombre son dos subidas), objetos y arrays estructuralmente.
- `src/lib/forms/buildCreatePayload.ts` (nuevo) — el mapeo completo validado.
- `src/lib/forms/buildUpdatePayload.ts` (reescrito) — el mapeo estricto; `strict` ahora **significa** lo que el nombre dice (omitir lo intacto) y su `default` es `true`. Antes la opción existía, no hacía nada y su docstring describía la semántica INVERTIDA.
- `src/lib/forms/stableSerialize.ts` (nuevo) — serialización determinista (claves ordenadas) para detectar un cambio real de datos.
- `src/lib/forms/index.ts` (nuevo) — barrel **granular** (sin comodín), como exige el contrato.
- `src/utils/payload-builder.ts` — el hand-off de archivos: el token de la parte multipart se genera con `crypto.getRandomValues` cuando existe (disponible también en contexto no seguro, donde `crypto.randomUUID` no lo está) en lugar de `Math.random`; la detección de `File` está protegida (`typeof File !== "undefined"`), porque el transporte también corre en el servidor; el payload de entrada **nunca** se muta. El protocolo (`data` + `files` con `<token>___<realname>`) NO se tocó: es `PROTO-MD-1.0.0`.

### 3.3 Ciclo de vida e hidratación (`src/components/genericForm/**`)

- **`submitMode`** (prop nueva, `"create"` por defecto): el mapeo del submit. `"create"` = mapeo completo validado; `"update"` = mapeo estricto contra `initialData`. El valor por defecto preserva la forma del cable de HOY (que, al no diferir nunca, era de hecho un mapeo completo), de modo que **ningún consumidor existente cambia de forma de payload** por sorpresa.
- **`resetOnInitialDataChange`** (prop nueva, `true` por defecto): la re-hidratación determinista. Se puede desactivar para conservar lo que el usuario escribió.
- La re-hidratación:
  1. se dispara cuando cambia el **CONTENIDO** de `initialData` (`stableSerialize`), no su referencia → un padre que reconstruye el objeto en cada render no resetea nunca;
  2. no interrumpe un envío en vuelo;
  3. no resetea cuando los valores que el formulario ya tiene SON los nuevos datos (protege al padre que devuelve los valores vivos);
  4. usa el MISMO constructor de defaults que la hidratación inicial (`buildFormDefaults`), así que ambos no pueden discrepar.
- **Dependencias**: `FormField.dependsOn` (nuevo). Un campo que declara sus dependencias lee SOLO esos campos con `useWatch`; un campo sin `dependsOn` conserva el comportamiento heredado; un campo con `hidden` booleano no lee nada. `GenericForm` ya NO llama a `watch()` sobre el formulario entero (prohibido por `contract/smart.md` §5.2): la visibilidad de cada campo y de cada sección se resuelve en `src/components/genericForm/visibility.tsx` con tres componentes distintos (estático / con nombre / formulario entero), de modo que el número de hooks de un componente nunca depende de una condición de runtime.
- **Errores de campo**: el `catch` del submit limpia los errores de servidor de la tentativa anterior, llama `setError` **una vez por campo** (el mapa tiene una entrada por campo) y registra los campos para la siguiente tentativa.
- El bloque que "aseguraba los campos de archivo de los renderizadores personalizados" era **código muerto** (`processedData` ya tenía todas las claves de `data`): se eliminó.

### 3.4 UX del campo de archivo (`src/components/genericForm/inputs/InputImage.tsx`)

- **La previsualización sigue el VALOR del formulario**, no `field.defaultValue`: antes, el formulario de edición no mostraba la imagen ya almacenada (el `defaultValue` de la configuración no es el dato del registro) y la imagen se perdía en la previsualización.
- Las acciones ("Subir imagen" / "Cambiar" / "Ver" / "Quitar") son **siempre visibles**: antes sólo aparecían al pasar el ratón (`opacity-0 group-hover:opacity-100`), lo que las volvía inalcanzables con teclado y en pantallas táctiles.
- El control real es un `<input type="file">` con `sr-only` y **alcanzable con el teclado**, con `focus-within:ring` en el contenedor (foco visible), `aria-label`, `aria-invalid` y `aria-describedby` hacia el error.
- El `accept` y el texto del límite salen del **contrato de media del backend** (`image/jpeg`, `image/png`, `image/webp`; 5 MiB), no de un número inventado en la UI.
- `alt` = la etiqueta del campo; el `FileReader` se cancela al desmontar; `Quitar` escribe `null` (limpieza explícita) y vacía el input.

### 3.5 Higiene del contrato

- `src/components/genericForm/inputs/index.ts` — el barrel tenía `export * from "./types"`, prohibido por `contract/next-app-architecture-contract.md` §7: ahora exporta los tipos de forma granular.
- `GenericInput` — el mensaje de error lleva un `id` estable (`<campo>-error`) para que el control pueda apuntar a él con `aria-describedby`.

---

## 4. Ficheros cambiados

### Creados (10)

| Fichero | Papel |
|---|---|
| `Aplicacion/frontend/src/errors/field-errors.ts` | parser del canal de error por campo |
| `Aplicacion/frontend/src/errors/__tests__/field-errors.test.ts` | suite del parser |
| `Aplicacion/frontend/src/errors/__tests__/error-handler.test.ts` | suite del handler |
| `Aplicacion/frontend/src/lib/forms/schemaShape.ts` | lectura del shape del schema |
| `Aplicacion/frontend/src/lib/forms/valueEquality.ts` | igualdad de valores de formulario |
| `Aplicacion/frontend/src/lib/forms/stableSerialize.ts` | serialización determinista |
| `Aplicacion/frontend/src/lib/forms/buildCreatePayload.ts` | mapeo de creación |
| `Aplicacion/frontend/src/lib/forms/index.ts` | barrel granular |
| `Aplicacion/frontend/src/lib/forms/__tests__/payload-mapping.test.ts` | suite de la forma exacta del payload |
| `Aplicacion/frontend/src/components/genericForm/formDefaults.ts` | defaults de hidratación y de reset |
| `Aplicacion/frontend/src/components/genericForm/visibility.tsx` | visibilidad con dependencias declaradas |
| `Aplicacion/frontend/src/components/genericForm/__tests__/generic-form.lifecycle.test.tsx` | suite del ciclo de vida |

### Modificados (9)

| Fichero | Qué cambió |
|---|---|
| `Aplicacion/frontend/src/errors/error-handler.ts` | `fieldErrors` en todo error parseado + mensaje del `detail[]` legacy |
| `Aplicacion/frontend/src/errors/index.ts` | export del parser |
| `Aplicacion/frontend/src/lib/forms/buildUpdatePayload.ts` | `initialData`/`strict` **ahora funcionan**; shape de primer nivel |
| `Aplicacion/frontend/src/utils/payload-builder.ts` | token del multipart con `getRandomValues`; `File` protegido; entrada no mutada |
| `Aplicacion/frontend/src/components/genericForm/GenericForm.tsx` | reset determinista, `submitMode`, Zod como dueño de la coerción, `setError` una vez por campo, sin `watch()` global |
| `Aplicacion/frontend/src/components/genericForm/GenericInput.tsx` | `dependsOn`, `id` del error |
| `Aplicacion/frontend/src/components/genericForm/inputs/types.ts` | `dependsOn`, `errorId` |
| `Aplicacion/frontend/src/components/genericForm/inputs/InputImage.tsx` | UX del campo de archivo |
| `Aplicacion/frontend/src/components/genericForm/inputs/index.ts` | barrel sin comodín |

**Ninguna raíz prohibida fue tocada.** Verificado con `git diff --name-only` sobre `src/lib/api.ts`, `src/lib/query-client.ts`, `src/hooks/**`, `src/shared/**`, `src/features/**`, `src/components-app/**`, `src/app/**`, `Aplicacion/backend/**`, `contract/**` y `frontend/**`: **vacío para los cambios de ESTE paquete** (el árbol de trabajo ya traía modificaciones de otros agentes en esas raíces, que **no** se tocaron, no se revirtieron y no se fusionaron).

---

## 5. Comandos / códigos de salida

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio (2 passes: tras la primera tanda de cambios y tras el refinamiento del reset) |
| V2 | `git diff --name-only -- <raíces prohibidas>` | raíz del repo | **0** | vacío para los cambios de este paquete |
| V3 | `git diff --stat -- <raíces permitidas>` | raíz del repo | **0** | 449 inserciones / 304 borrados sobre ficheros versionados + ~1 250 líneas nuevas sin versionar |
| V4 | `git rev-parse HEAD` | raíz del repo | **0** | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` — sin commit creado |

**Comandos NO ejecutados (por instrucción del paquete y del usuario):** `vitest`, `biome`, `next build`, `npm install`, servidores, navegadores, sondas HTTP. `git stash` nunca invocado. `git reset`/`checkout` nunca invocados.

**Pruebas ESCRITAS, NO EJECUTADAS:** 4 suites — `src/errors/__tests__/field-errors.test.ts`, `src/errors/__tests__/error-handler.test.ts`, `src/lib/forms/__tests__/payload-mapping.test.ts`, `src/components/genericForm/__tests__/generic-form.lifecycle.test.tsx` (jsdom). Cubren: hidratación y reset (incluido el "no reset si el contenido no cambió"), forma exacta create/update (ausente / `null` / create / update / archivo), 422 (`field_errors`, `detail[]`, `errors{}`, `details{}`, `non_field_errors`), coerción de Zod, hand-off del `File` y `setError` una vez por campo.

---

## 6. Divergencias declaradas

| Id | Divergencia | Por qué |
|---|---|---|
| `D-FND07-01` | `submitMode` tiene `"create"` por defecto | preserva la forma del cable de HOY para TODOS los consumidores existentes (`RegisterForm`, `InscripcionWizardView`, `AppFormModal`, `AppStepperFormModal`), que en la práctica ya enviaban un mapeo completo porque `buildUpdatePayload` nunca diferenció. El mapeo estricto es **opt-in** explícito |
| `D-FND07-02` | la sección puede quedar vacía (con su título) cuando sus campos se ocultan por una función | el salto de sección ("todos los campos ocultos → no renderizar la sección") exigía leer el formulario entero. Se conserva para las secciones con `hidden` booleano; con `hidden` por función la sección se renderiza y sus campos se ocultan dentro. Con `dependsOn` declarado, el salto vuelve a ser exacto |
| `D-FND07-03` | la identidad de la opción de un `select`/`radio` se sigue aplicando en el submit | NO es coerción: el DOM sólo lleva cadenas y `"3"` ES la opción `3`. La coerción de TIPO es de Zod. Sin este mapeo, un schema `z.string()` con opciones numéricas viajaría con el tipo del schema y no con el de la opción |
| `D-FND07-04` | se eliminó la coerción `Number()`/`Boolean()` por `FieldConfig.type` | Zod es el dueño de la coerción. La coerción anterior **ya no podía rescuing** una validación fallida (el resolver de Zod corre antes) y sí podía corromper el valor validado |
| `D-FND07-05` | `buildUpdatePayload.strict` ahora significa "omitir lo intacto" y vale `true` por defecto | el parámetro existía, no hacía nada y su docstring describía la semántica INVERTIDA. La semántica corregida es la que exige la matriz ("strict update mapper using initial data") |
| `D-FND07-06` | NO se creó `src/components/smartField/**` | la raíz no existe en el objetivo y **las raíces permitidas del propio paquete no la incluyen**. El ecosistema Smart Field del contrato vive en `components/genericForm/**` (`contract/smart.md` §3). Los Smart Fields de dominio del árbol congelado (`features/inscripciones/components/smart-fields/**`) son raíces de feature prohibidas |
| `D-FND07-07` | `imageField()` y su convención (Symbol) NO se tocaron | `imageField().schema.optional()` perdería el Symbol y rompería la detección de campos de archivo. Es una trampa real que se documenta, no se cambia: cambiar la convención rompería los schemas ya escritos |
| `D-FND07-08` | `src/components-app/**` está EXCLUIDO de `tsconfig.json` | sus consumidores (`AppFormModal`, `AppStepperFormModal`) **no** los cubre el `tsc --noEmit` de este paquete. Se verificó a mano que ambos siguen siendo compatibles (`children` presente ⇒ modo manual; `formMethods` ⇒ modo 4) |

---

## 7. Hechos nuevos (relevantes para los paquetes siguientes)

- **F-71** — El envelope del backend entrega `error.field_errors[]` con la ruta del campo YA punteada (`beneficiarios.0.documento`): el frontend NO tiene que construirla a partir de `loc` cuando el backend es el del objetivo. La conversión desde `loc` sólo hace falta para el backend congelado heredado.
- **F-72** — `zodResolver` entrega el **salida parseada** de Zod: por eso la coerción del lado del formulario era redundante cuando el schema coerciona y corruptora cuando no.
- **F-73** — El `watch()` global del `GenericForm` re-renderizaba el formulario entero en cada tecla (`contract/smart.md` §5.2 lo prohíbe). `useWatch` con un array de nombres devuelve un array **en el mismo orden** (documentación de RHF), lo que permite construir el mapa de dependencias sin ambigüedad.
- **F-74** — `src/components-app/**` está excluido de `tsconfig.json`: el typecheck del frontend NO cubre esos consumidores.
- **F-75** — El allowlist de media del backend (`image/jpeg`, `image/png`, `image/webp`, SVG prohibido, 5 MiB) es la fuente de verdad del `accept` y del texto del límite del campo de archivo.

---

## 8. Riesgo / trabajo pendiente

| Id | Riesgo | Estado |
|---|---|---|
| `R-FND07-01` | Las 4 suites están ESCRITAS y NO EJECUTADAS | abierto — la verificación en runtime está diferida (preferencia vigente del proyecto). `tsc` es la única puerta ejecutada |
| `R-FND07-02` | El comportamiento del `reset` con un padre que devuelve los valores vivos se protege por la comparación de valores, no por una prueba | abierto — la suite lo cubre en el caso "mismo contenido"; el caso "valores vivos" queda para la verificación en runtime |
| `R-FND07-03` | La sección puede quedar vacía con su título (D-FND07-02) | abierto — cosmético; se cierra cuando las features declaren `dependsOn` |
| `R-FND07-04` | Los consumidores de `components-app/**` no los cubre `tsc` | abierto — revisión manual hecha (D-FND07-08) |
| `R-FND07-05` | El tamaño real del paquete (~1 700 líneas cambiadas) excede el presupuesto de revisión de 400 líneas por ≈ 4× | **reportado a A0** — el artefacto del paquete NO lleva `Review Workload Forecast`, así que NO exigía una decisión de cadena/tamaño (mismo precedente que DOM-06). Se declaran 4 rodadas autónomas (WU-1…WU-4) con orden de rollback WU-4 → WU-1 |

---

## 9. Rodadas de revisión (autónomas)

| Rodada | Alcance | Ficheros |
|---|---|---|
| **WU-1** | Errores de campo 422 | `src/errors/field-errors.ts`, `src/errors/error-handler.ts`, `src/errors/index.ts`, `src/errors/__tests__/**` |
| **WU-2** | Mapeo de payload y hand-off de archivos | `src/lib/forms/**`, `src/utils/payload-builder.ts` |
| **WU-3** | Ciclo de vida, hidratación y dependencias | `GenericForm.tsx`, `formDefaults.ts`, `visibility.tsx`, `GenericInput.tsx`, `inputs/types.ts` |
| **WU-4** | UX del campo de archivo + suite del ciclo de vida | `inputs/InputImage.tsx`, `inputs/index.ts`, `genericForm/__tests__/**` |

**Orden de rollback:** WU-4 → WU-3 → WU-2 → WU-1. Cada rodada es autónoma: se puede revertir sin tocar las demás. El rollback completo = revertir los 9 ficheros modificados y borrar los 12 creados, y revertir la fila de FND-07 del `STATE.md` y de los topics. **NO** revertir ni resetear `fd1c4c12`.

---

## 10. Consumidores desbloqueados

- **UI-02 / UI-03 / UI-04 / UI-05** — los formularios de ruta ya tienen re-hidratación determinista, errores de campo que llegan al control, y dos mapeos de payload separados.
- **API-01…API-05** — el espejo del envelope y el canal de errores de campo están cerrados para el frontend; los hooks de mutación (raíz de FND-08) reciben un payload con la forma exacta.
- **XCT-01…XCT-03 / VER-01…VER-03** — existe una base verificable para el comportamiento de los formularios (con la salvedad de R-FND07-01).

**Siguiente paquete:** `FND-08` ya está aplicado (`verification_required`); el siguiente pendiente de la ola es **UI-01** (briefs de ruta, candidatos shadcn, `PROVISIONAL_CONTRACT_FIXTURE`, los diez estados por ruta, los page IDs y la auditoría de navegador de cinco anchos).
