# API-05 — Integración de competencias, patrocinadores y validaciones

**Paquete:** `wave-03-api-integration/API-05-competition-admin-integration.md` · **Owner:** A0 + A7 · **Cambio:** `salesianos-fest-rebuild`
**Estado:** `implementation applied` — **NO cierra el paquete** (verificación en runtime diferida)
**Tareas de origen:** `T-077`, `T-078`, `T-082`
**Rollback:** revertir los ficheros de §6 (no hay commit creado; `git stash` nunca invocado)
**Fecha:** 2026-11-19 · **Objetivo:** `Aplicacion/frontend/**` (tres features) + evidencia + tablero

---

## 1. Veredicto de registro (la verdad que manda)

`Aplicacion/backend/config/api.py` es la puerta de registro (`FR-07` §3.1 regla 2): **una ruta no existe
hasta que su controller está registrado**. El estado fue **re-verificado en este paquete** contra el
**árbol de trabajo**, no contra el plan ni contra una evidencia anterior:

| Controller | ¿Registrado? | Rutas vivas | Evidencia de la lectura |
|---|---|---|---|
| `NinjaJWTDefaultController` | **SÍ** | `/token/{pair,refresh,verify}` | `config/api.py` |
| `EdicionController` | **SÍ** | `GET /ediciones/actual` | `config/api.py` |
| `PersonaController` | **SÍ** | `/personas/**` (3) | `config/api.py` |
| `AuthController` | **SÍ** | `/auth/**` (4) | `config/api.py` |
| `PagosController` | **SÍ** | `/pagos/**` (3) | `config/api.py` |
| `CatalogoController` | **SÍ** | `/catalogo/**` (2) | `config/api.py` |
| `InscripcionController` | **SÍ** | `/inscripciones/**` (7) | `config/api.py` |
| `ProductoController` | **SÍ** | `/marketplace/{categorias,productos}` (3) | `config/api.py` |
| `PaseController` | **SÍ** | `/pases/**` (7) | `config/api.py` |
| `AdminPaseController` | **SÍ** | `/administracion/pases/**` (3) | `config/api.py` |
| **`CompetenciasController`** | **NO** | sus **16 rutas NO EXISTEN** | `config/api.py` (no está en `registrar_controladores(...)`) |
| **`PatrocinadorController`** | **NO** | su **1 ruta NO EXISTE** | `config/api.py` (idem) |
| **`InventarioController`** | **NO** | sus **5 rutas NO EXISTEN** | `config/api.py` (idem) |
| **`PedidoController`** | **NO** | sus **2 rutas NO EXISTEN** | `config/api.py` (idem) |

**Precondición del registro (hallazgo vigente, no nuevo):** `modules.competencias` y
`modules.patrocinadores` **NO** están en `LOCAL_APPS` (`config/settings/base.py` los lista sólo hasta
`modules.marketplace`) y sus módulos de DI **NO** están en `INJECTOR_MODULES`. Sin el registro de las
apps, **ni siquiera se pueden importar** los dos controllers (`RuntimeError: … doesn't declare an
explicit app_label`). El registro de las apps es **precondición** del registro de los controllers, no
un cambio paralelo (`evidence/foundations/A0-wiring-validation.md` §4).

**El módulo `validaciones` NO EXISTE** en el objetivo: `Aplicacion/backend/modules/` contiene
`commerce`, `competencias`, `eventos`, `marketplace`, `pagos`, `patrocinadores`, `salesianos_fest` y
`usuarios`. **No hay** `modules/validaciones`, ni presenter, ni wrapper.

### 1.1 Consecuencia para este paquete

**De las TRES superficies del alcance de API-05, CERO rutas están registradas:**

| Superficie | Ruta del ledger | ¿Existe? | Dueño del bloqueo |
|---|---|---|---|
| `ADM-10…ADM-13` (competencias) | `GET /competencias`, `GET /competencias/agenda`, `GET /competencias/{id}`, `GET /competencias/{id}/cuadro`, `GET /competencias/{id}/equipos-elegibles` (+11 de escritura) | **NO** | A0 (`A0-RTV-01`/`A0-RTV-02`) |
| `ADM-21` (patrocinadores) | `POST /patrocinadores` (`RT-MD-02`) | **NO** | A0 (`A0-RTV-01`/`A0-RTV-02`) |
| `ADM-16` (entrada) | `POST /validaciones/preview` (`RT-RT-01`), `POST /validaciones/confirmar` (`RT-RT-02`) | **NO** | A0 + backend (el módulo no existe) |
| `ADM-20` (recogidas) | `GET /administracion/marketplace/entregas` (`RT-MK-10`), `POST …/confirmar` (`RT-MK-11`) | **NO** | A0 (`A0-RTV-02`) |
| `ADM-22` (auditoría) | `GET /administracion/validaciones` (`RT-VA-01`) | **NO** | A0 + backend (no está en el ledger) |

⇒ **API-05 liga CERO rutas.** Es el mismo veredicto que took `API-01` (para `RT-ID-04/05/06` y
`RT-RC-01`), `API-02` (para `RT-IN-01` y los beneficios) y `API-03` (para `PedidoController` e
`InventarioController`): un controller sin registrar es **código muerto por diseño** y un módulo
inexistente no tiene contrato. **Ligar una ruta que no existe sería inventar un contrato**, y el
packet lo prohíbe explícitamente.

---

## 2. Ledger endpoint → presenter → espejo Zod → consumidor

### 2.1 COMPETENCIAS (`features/competencias/**`) — ESPEJO, NO LIGADO

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Consumidor |
|---|---|---|---|---|---|---|
| — | GET | `/competencias` | `CompetenciasPresenter` | `list[CompetenciaListadoOut]` | `competenciaListadoSchema` | **NO LIGADO** |
| — | GET | `/competencias/agenda` | `CompetenciasPresenter` | `AgendaOut` | `agendaSchema` | **NO LIGADO** |
| — | GET | `/competencias/{competencia_id}` | `CompetenciasPresenter` | `CompetenciaDetalleOut` | `competenciaDetalleSchema` | **NO LIGADO** |
| — | GET | `/competencias/{competencia_id}/cuadro` | `CompetenciasPresenter` | `list[RondaOut]` | `rondaSchema` | **NO LIGADO** |
| — | GET | `/competencias/{competencia_id}/equipos-elegibles` | `CompetenciasPresenter` | `list[EquipoElegibleOut]` | `equipoElegibleSchema` | **NO LIGADO** |
| — | POST | `/competencias` | `CompetenciasPresenter` | `CompetenciaDetalleOut` | `competenciaCrearSchema` | **NO LIGADO** |
| — | POST | `/competencias/{id}/equipos` | `CompetenciasPresenter` | `CompetenciaEquipoOut` | `equipoIncorporarSchema` | **NO LIGADO** |
| — | PATCH | `/competencias/{id}/equipos/{participacion_id}` | `CompetenciasPresenter` | `CompetenciaEquipoOut` | `equipoEditarSchema` | **NO LIGADO** |
| — | POST | `/competencias/{id}/rondas` | `CompetenciasPresenter` | `RondaOut` | `rondaCrearSchema` | **NO LIGADO** |
| — | POST | `/competencias/{id}/encuentros` | `CompetenciasPresenter` | `EncuentroOut` | `encuentroCrearSchema` | **NO LIGADO** |
| — | PATCH | `/competencias/{id}/encuentros/{encuentro_id}` | `CompetenciasPresenter` | `EncuentroOut` | `encuentroActualizarSchema` | **NO LIGADO** |
| — | POST | `/competencias/{id}/encuentros/{encuentro_id}/resultado` | `CompetenciasPresenter` | `ResultadoRegistradoOut` | `resultadoRegistrarSchema` | **NO LIGADO** |
| — | POST | `…/avance/preview` (**NO ESCRIBE**) | `CompetenciasPresenter` | `AvancePreviewOut` | `avancePreviewSchema` | **NO LIGADO** |
| — | POST | `…/avance` | `CompetenciasPresenter` | `AvanceOut` | `avanceConfirmarSchema` | **NO LIGADO** |
| — | POST | `…/correccion/preview` (**NO ESCRIBE**) | `CompetenciasPresenter` | `CorreccionPreviewOut` | `correccionPrevisualizarSchema` | **NO LIGADO** |
| — | POST | `…/correccion` | `CompetenciasPresenter` | `CorreccionOut` | `correccionAplicarSchema` | **NO LIGADO** |

**Precedente, no invención:** los dieciséis wrappers y las diez entradas existen, están CONGELADOS y
versionados (`SCHEMA_VERSION = "1.0.0"` de `DOM-07`). El espejo es una transcripción 1:1 de un
contrato **existente**, no una forma inventada.

### 2.2 PATROCINADORES (`features/patrocinadores/**`) — ESPEJO, NO LIGADO

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Consumidor |
|---|---|---|---|---|---|---|
| `RT-MD-02` | POST | `/patrocinadores` | `PatrocinadorPresenter` | `PatrocinadorOut` | `patrocinadorSchema` | **NO LIGADO** |

**El ledger declara UNA ruta y es de ESCRITURA.** No existe ninguna ruta de lectura de los
patrocinadores: el listado y la consulta por `slug` son **capacidades de dominio** que `DOM-08`
entregó con sus tipos y sus pruebas, pero **no están expuestas por HTTP** (`D-DOM08-08`, petición
`A0-04` de `DOM-08`). ⇒ **`ADM-21` no tiene ruta de lectura**, y su tabla de patrocinadores queda
atendida por la ruta de alta, que devuelve **un solo** patrocinador (`PatrocinadorOut`).

### 2.3 VALIDACIONES (`features/validaciones/**`) — ESPEJO PARCIAL, NO LIGADO

| Ledger | Método | URL | Presenter | Wrapper | Espejo Zod | Consumidor |
|---|---|---|---|---|---|---|
| `RT-MK-10` | GET | `/administracion/marketplace/entregas` | `EntregaPresenter` | `list[EntregaPendienteOut]` | `entregaPendienteSchema` | **NO LIGADO** |
| `RT-MK-11` | POST | `…/entregas/{pedido_id}/confirmar` | `EntregaPresenter` | `EntregaConfirmadaOut` | `entregaConfirmadaSchema` | **NO LIGADO** |
| `RT-RT-01` | POST | `/validaciones/preview` | — | `TicketPreviewOut` | — | **NO EXISTE** (no hay módulo) |
| `RT-RT-02` | POST | `/validaciones/confirmar` | — | `TicketConfirmadoOut` | — | **NO EXISTE** (no hay módulo) |
| `RT-VA-01` | GET | `/administracion/validaciones` | — | `AdminValidacionListItemOut` | — | **NO EXISTE** (no está en el ledger) |

**Los tres wrappers de `validaciones` NO tienen presenter** ⇒ **no se espeja nada de ellos**: un
espejo de un wrapper inexistente sería un contrato inventado. Los tipos de vista que los dibujan
(`VistaPreviaValidacion`, `ResultadoValidacion`, `RegistroValidacion`) **siguen siendo PROVISIONALES**
y ahora lo dicen con la referencia exacta: `A0-UI05-02`, re-elevada como **`A0-API05-02`**.

### 2.4 Formas de wire REUTILIZADAS de su dueño (nunca duplicadas)

| Forma | Dueño canónico | Cómo la consume el área de validaciones |
|---|---|---|
| `PaseBeneficiarioOut` (`DOM-03`) | `features/pases` → `beneficiarioPaseSchema` | **REUTILIZADA** (`paseBeneficiarioSchema` es un alias) |
| `PedidoLineaOut` (`DOM-05`) | `features/marketplace` → `pedidoLineaSchema` | **REUTILIZADA** (importada) |

Es la regla de `salesianos-api-data`: *un dataset, un dueño*. El área de validaciones **no** publica
una segunda copia de la forma del lote de pases ni de la línea del pedido.

---

## 3. Lo que este paquete escribió (y por qué)

### 3.1 Los tres espejos Zod (1:1 con los presenters que EXISTEN)

| Fichero | Presenter espejado | Envelopes | Entradas |
|---|---|---|---|
| `features/competencias/schemas/competencia.schema.ts` | 13 wrappers de `DOM-07` | 9 | 10 `*In` |
| `features/patrocinadores/schemas/patrocinador.schema.ts` | `PatrocinadorOut` + sus 3 bloques + logo + imagen | 1 | 2 (`CrearPatrocinadorIn`, `ImagenPatrocinadorIn`) |
| `features/validaciones/schemas/validacion.schema.ts` | `EntregaPendienteOut`, `EntregaConfirmadaOut` | 2 | — |

**Las reglas del espejo (heredadas de `API-01`…`API-03`):**

- **Sin `z.any()` y sin campo genérico**: cada campo está declarado.
- El **envelope es el congelado** (`FREEZE-ENV-1.0.0`): la fábrica `apiResponseSchema` del proyecto
  lo construye, y la paginación vive DENTRO de `data` como
  `{ items, total, page, page_size, total_pages }`.
- **Los códigos de máquina son `string`, no enums**: el backend es dueño del vocabulario y un valor
  nuevo NO puede romper la lectura entera.
- **La versión del bloqueo optimista es un NÚMERO y viaja en cada escritura** (`expected_version`):
  el cliente nunca decide si una escritura es vigente.
- **Las previsualizaciones NUNCA escriben**: son esquemas SEPARADOS de las confirmaciones, y la
  separación se ve en los nombres.
- Los importes son **números**: el backend serializa `Decimal` como float
  (`core/responses.py::_decimal_to_float`).
- `DOM-07` declara sus identificadores como `str` (no `UUID`): el espejo respeta el tipo declarado y
  no se rompe si mañana se publica otro. `DOM-08`/`DOM-05`/`DOM-06` sí declaran `UUID`: ahí el espejo
  es estricto.

### 3.2 El `expected_version`, el impacto y las acciones

Los tres detalles que el packet exige mirrorar de forma explícita están en el espejo, no en la
interfaz:

- **`expected_version`** está en las **diez** entradas de escritura de `DOM-07`
  (`equipoEditarSchema`, `encuentroActualizarSchema`, `resultadoRegistrarSchema`,
  `avanceConfirmarSchema`, `correccionAplicarSchema`). Es **obligatorio**: `z.number().int()`, sin
  opcional.
- **El impacto de la corrección** (`correccionImpactoSchema`): `bloqueado`, `motivo_bloqueo`,
  `reemplaza`, `limpia_slot`, `limpia_resultado` y `afecta` son los seis campos que el backend
  publica, y `correccionPreviewSchema` declara `requiere_override` y `total_afectados`.
- **Las acciones** (`EncuentroOut.acciones`) son la lista **declarada** por el backend de lo que
  admite en el estado actual: la interfaz las imprime y no las deduce.

### 3.3 Las tres correcciones de honestidad del contrato

| # | Corrección | Por qué |
|---|---|---|
| `D-API05-01` | `LogoPatrocinador.url` y `ImagenPatrocinador.url` pasan de `string` a **`string \| null`** | El presenter declara `url: str \| None`. El tipo de vista mentía: un archivo no legible publicaba `url: null` y el componente lo dibujaba como `src`. `LogoPatrocinador` y `GaleriaPatrocinador` muestran ahora el **hueco** cuando falta la URL, no una imagen rota |
| `D-API05-02` | La unión `CodigoErrorMedio` tiene **un solo dueño**: el espejo (`schemas/patrocinador.schema.ts`). El tipo de vista **re-exporta** | `MEDIA_TOKEN_DUPLICADO` (400) lo declara el controller de `DOM-08` y **no** estaba en la unión. Ahora está, con su redacción en `FormularioPatrocinador` |
| `D-API05-03` | Los tres tipos de vista (`competencia.types.ts`, `patrocinador.types.ts`, `validacion.types.ts`) dejan de decir «NO son un espejo todavía» | El espejo **existe** y está al lado. La frase era cierta en `UI-05` y es falsa hoy |

---

## 4. Fixtures provisionales: ELIMINADOS

| Fichero | Acción |
|---|---|
| `src/features/competencias/fixtures/competencias.fixture.ts` | **ELIMINADO** (marcador `PROVISIONAL_CONTRACT_FIXTURE`) |
| `src/features/validaciones/fixtures/validaciones.fixture.ts` | **ELIMINADO** (marcador `PROVISIONAL_CONTRACT_FIXTURE`) |
| `src/features/patrocinadores/fixtures/patrocinadores.fixture.ts` | **ELIMINADO** (marcador `PROVISIONAL_CONTRACT_FIXTURE`) |

Los tres directorios `fixtures/` quedaron vacíos y se eliminaron.

**Los datos de las suites ya no son una copia del wire: son la RESPUESTA DEL CONTRATO parseada por el
mismo espejo que usaría el servicio.** Cada suite tiene ahora un módulo de datos **dentro de
`__tests__/`** (`datos.contract.ts`) que construye sus ejemplos con `schema.parse(...)`:

- una forma que el espejo rechaza rompe la suite **ANTES** de dibujar nada;
- los ejemplos son **EJEMPLOS del wire**, no un transporte: ningún módulo de producción los importa y
  no se exportan desde ningún barril (mismo precedente que
  `features/inscripciones/__tests__/inscripcion-mirrors.test.ts` de `API-02`).

### 4.1 Los datos PROVISIONALES se quedan en la suite, no en producción

El `preview`, la `confirmación` y la `fila de auditoría` **no tienen presenter** (§2.3). Sus literales
viven **en el fichero de datos de la suite**, marcados como PROVISIONALES, y **nunca** en código de
producción: un contrato provisional no es un contrato.

### 4.2 Escaneo de cierre

| Búsqueda | Alcance | Resultado |
|---|---|---|
| `PROVISIONAL_CONTRACT_FIXTURE` | `features/{competencias,validaciones,patrocinadores}/**` | **0** |
| `fixtures/` (imports) | las tres features | **0** |
| `fallback` / `mock[A-Z]` | las tres features (código de producción) | **0** (sólo `vi.mock("next/link")` y `vi.mock("next/navigation")` en las suites, que son shims del framework) |
| Rutas de `app/**` que apuntan a vistas sin dueño | las 8 rutas de `UI-05` | **0** — las 8 siguen apuntando a sus vistas |

**Pendiente FUERA del alcance de este paquete (deuda explícita, con dueño):** siguen existiendo
marcadores `PROVISIONAL_CONTRACT_FIXTURE` en `features/portada/fixtures/**` (raíz de `UI-01`, **no**
de este paquete) y en `features/admin/**` (raíz de `FND-06`, **no** de este paquete). Se registran en
§7 como `A0-API05-06`.

---

## 5. Ownership de `ADM-15` / `ADM-17` / `ADM-18` / `ADM-19`

La reconciliación de `UI-05` (`D-UI05-06` → `A0-UI05-08`, confirmada por la reconciliación
concurrente del tablero) establece que esas cuatro rutas:

- apuntan a `features/admin/views/**`, que es la **raíz de FND-06**;
- **UI-04 las desconoce** (§9 de su apply-progress) y **UI-05 no las tocó** (raíz prohibida);
- proceden del **agente `general` lanzado manualmente** de la sesión #11314, que trabaja **fuera** del
  sistema de paquetes: **no tienen fila, ni apply-progress, ni fichero de evidencia**.

**API-05 NO las reclamó y NO las tocó**: `features/admin/**` está **FUERA** de las raíces permitidas de
este packet, y el packet sólo era dueño de `features/{competencias,validaciones,patrocinadores}/**`.
**Reemplazarlas "si es seguro" NO era seguro**: habría exigido reescribir cuatro vistas de una raíz
ajena, con un árbol concurrente en vuelo, para entregar un cambio que **no** es del alcance de API-05 y
que el propio `UI-05` ya pidió que se atribuya.

⇒ La propiedad sigue **NO ATRIBUIDA** y se **re-eleva** como **`A0-API05-05`**, junto a
`A0-UI05-08`. La línea de las cuatro rutas **no se ha tocado**.

---

## 6. Ficheros

### 6.1 Creados (10)

**`features/competencias/`** (3): `schemas/competencia.schema.ts` ·
`__tests__/datos.contract.ts` · `__tests__/competencia-mirrors.test.ts`

**`features/validaciones/`** (3): `schemas/validacion.schema.ts` ·
`__tests__/datos.contract.ts` · `__tests__/validacion-mirrors.test.ts`

**`features/patrocinadores/`** (3): `schemas/patrocinador.schema.ts` ·
`__tests__/datos.contract.ts` · `__tests__/patrocinador-mirrors.test.ts`

**Evidencia** (1): `evidence/api/API-05-competition-admin-integration.md` (este fichero)

### 6.2 Modificados (11 + el tablero)

| Fichero | Cambio |
|---|---|
| `features/competencias/types/competencia.types.ts` | cabecera: el espejo existe (`D-API05-03`) |
| `features/competencias/__tests__/competencias-estados.test.tsx` | los datos salen del espejo, no de una fixture |
| `features/validaciones/types/validacion.types.ts` | cabecera: qué está congelado y qué es provisional; `A0-API05-02` |
| `features/validaciones/__tests__/validaciones-estados.test.tsx` | ídem |
| `features/validaciones/components/TablaAuditoriaValidaciones.tsx` | referencia de la petición ratificada |
| `features/validaciones/utils/validaciones.estados.utils.ts` | ídem |
| `features/patrocinadores/types/patrocinador.types.ts` | `url` nullable (`D-API05-01`) + `CodigoErrorMedio` re-exportado (`D-API05-02`) |
| `features/patrocinadores/__tests__/patrocinadores-estados.test.tsx` | los datos salen del espejo |
| `features/patrocinadores/components/FormularioPatrocinador.tsx` | redacción de `MEDIA_TOKEN_DUPLICADO` |
| `features/patrocinadores/components/LogoPatrocinador.tsx` | hueco cuando falta la URL |
| `features/patrocinadores/components/GaleriaPatrocinador.tsx` | ídem |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | fila de API-05 + esta transición |

### 6.3 Eliminados (3)

`features/competencias/fixtures/competencias.fixture.ts` ·
`features/validaciones/fixtures/validaciones.fixture.ts` ·
`features/patrocinadores/fixtures/patrocinadores.fixture.ts`

### 6.4 Raíces tocadas

`Aplicacion/frontend/src/features/competencias/**` ·
`Aplicacion/frontend/src/features/validaciones/**` ·
`Aplicacion/frontend/src/features/patrocinadores/**` ·
`Aplicacion/task/salesianos-fest-rebuild/evidence/api/**` ·
`Aplicacion/task/salesianos-fest-rebuild/STATE.md`.

### 6.5 Raíces PROHIBIDAS NO tocadas

`src/lib/**` · `src/shared/**` · `src/hooks/**` · `src/errors/**` · `src/components/**` ·
`src/providers/**` · `src/utils/**` · `src/types/**` · `src/app/**` · `src/features/admin/**` ·
`src/features/{auth,cuenta,inscripciones,marketplace,pases,portada,public,theme}/**` ·
`Aplicacion/backend/**` · `contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**`.

**Ninguna ruta de `src/app/**` necesitó cambio**: las ocho rutas de `UI-05` ya apuntan a sus vistas y
el estado honesto no cambia (§1.1).

---

## 7. BLOQUEOS reportados (nada se inventó)

| # | Bloqueo | Evidencia | Dueño |
|---|---|---|---|
| **B-05-01** | `CompetenciasController` **no registrado** y `modules.competencias` **no** en `LOCAL_APPS` → sus **16 rutas NO EXISTEN**: `ADM-10…ADM-13` no leen nada | `config/api.py`, `config/settings/base.py` · `A0-RTV-01`/`A0-RTV-02` | **A0** |
| **B-05-02** | `PatrocinadorController` **no registrado** y `modules.patrocinadores` **no** en `LOCAL_APPS` → su **1 ruta NO EXISTE**: `ADM-21` no puede dar de alta ningún patrocinador | ídem | **A0** |
| **B-05-03** | El módulo **`validaciones` NO EXISTE** → `RT-RT-01`, `RT-RT-02` y `RT-VA-01` no tienen ni ruta ni presenter: `ADM-16` y `ADM-22` no pueden leer ni auditar | `Aplicacion/backend/modules/` | **A0 + backend** |
| **B-05-04** | `InventarioController` **no registrado** → `RT-MK-10`/`RT-MK-11` no existen: `ADM-20` no puede listar ni confirmar recogidas | `config/api.py` · `A0-RTV-02` | **A0** |
| **B-05-05** | **No hay ninguna ruta de LECTURA de patrocinadores.** El ledger declara una sola fila (`RT-MD-02`, de escritura). `ADM-21` necesita listar y abrir: la lista no tiene de dónde salir | `D-DOM08-08` · `A0-04` de `DOM-08` | **A0** |
| **B-05-06** | La **paginación y los ocho filtros de la auditoría** (`RT-VA-01`) no tienen nombres de parámetro ratificados: la barra de filtros sólo ofrece el veredicto | `D-UI05-08` | **A0** |
| **B-05-07** | El **filtro `disciplina_id`** de la lista de competencias necesita el catálogo de disciplinas, que es otro dataset | `UI-05` §11 | **API-04 / A0** |
| **B-05-08** | El **confirm de la corrección** (`D-UI05-09`) y el **preview del avance** no están ligados: sus rutas no existen | `B-05-01` | **A0** |

### 7.1 Peticiones a A0

| # | Petición | Prioridad |
|---|---|---|
| **`A0-API05-01`** | **Registrar `modules.competencias` y `modules.patrocinadores`** en `LOCAL_APPS` (después de `modules.marketplace`, por el grafo de migraciones) **y** sus dos módulos de DI en `INJECTOR_MODULES`; **después**, registrar `CompetenciasController` y `PatrocinadorController` en `config/api.py`. El registro de las apps es **precondición**: sin él los controllers ni siquiera se importan | **BLOQUEANTE** |
| **`A0-API05-02`** | **Ratificar los tres wrappers de `validaciones`**: los campos de `TicketPreviewOut` y `TicketConfirmadoOut`, los nombres de parámetro de `RT-VA-01` y el código de una validación exitosa (`VALIDACION_PERMITIDA` es hoy PROVISIONAL). El módulo `validaciones` **tiene que existir**: hasta entonces `ADM-16` y `ADM-22` no tienen contrato | **BLOQUEANTE** |
| **`A0-API05-03`** | **Ratificar la ruta de LECTURA de los patrocinadores** (`GET /patrocinadores` o `GET /patrocinadores/{slug}`) o declarar explícitamente que `ADM-21` **no lista**: hoy el ledger sólo tiene el alta | **BLOQUEANTE para `ADM-21`** |
| **`A0-API05-04`** | **`SCHEMA_VERSIONS["competencias"] = "1.0.0"`** en `core/contract_versions.py` (+ su test de drift): sin registro no hay mecanismo de detección de drift entre el backend y el espejo Zod | ALTA (drift) |
| **`A0-API05-05`** | **Atribuir `ADM-15`, `ADM-17`, `ADM-18` y `ADM-19`** (ver §5). Siguen **NO ATRIBUIDAS**; `features/admin/**` no es raíz de este packet y sus vistas las produce una pasada **fuera** del sistema de paquetes (#11314) | MEDIA |
| **`A0-API05-06`** | **Deuda de fixtures provisionales FUERA del alcance de este packet**: `features/portada/fixtures/**` (raíz de `UI-01`) y `features/admin/**` (raíz de `FND-06`). Ninguna de las dos está en las raíces permitidas de API-05 | MEDIA |
| **`A0-API05-07`** | **`00-matriz-tareas.md`** no tiene fila de API-05 y la matriz es raíz prohibida | BAJA |

### 7.2 Decisiones tomadas (con su coste)

| # | Decisión | Motivo |
|---|---|---|
| **`D-API05-04`** | **API-05 liga CERO rutas** y no crea cliente, ni factoría de claves, ni hook, ni mutación | Una ruta que no existe no se puede ligar: hacerlo sería un cliente de código muerto y un `catch` que devuelve un fixture. El precedente es `API-01`, `API-02` y `API-03` |
| **`D-API05-05`** | **El espejo se escribe AUNQUE la ruta no exista** | El espejo transcribe un presenter **existente y congelado**: no inventa nada. Es la costura que hace que la liaison del futuro sea un cliente y **cero** reescrituras de vistas (mismo precedente: `pedido.schema.ts` de `API-03`) |
| **`D-API05-06`** | **Las formas de wire ya espejadas por su dueño se REUTILIZAN, no se duplican** (`PaseBeneficiarioOut`, `PedidoLineaOut`) | Un dataset, un dueño. El área de validaciones no publica una segunda copia de la forma del lote ni de la línea del pedido |
| **`D-API05-07`** | **Los datos de las suites se construyen con `schema.parse(...)`** y el módulo de datos vive en `__tests__/` | Una forma que el espejo rechaza rompe la suite antes de dibujar. Los datos dejan de ser una copia del wire y pasan a ser la respuesta del contrato |
| **`D-API05-08`** | **No se espeja nada de `TicketPreviewOut`, `TicketConfirmadoOut` ni `AdminValidacionListItemOut`** | No hay presenter: un espejo de un wrapper inexistente sería un contrato inventado |
| **`D-API05-09`** | **`ADM-15/17/18/19` no se tocan** | `features/admin/**` está fuera de las raíces permitidas y su árbol está en vuelo (§5) |

---

## 8. Comandos y verificación

**El ÚNICO comando de runtime de este packet fue el typecheck.** Todo lo demás estaba prohibido por el
contrato de lanzamiento.

| # | Comando | Workdir | Exit | Resultado |
|---|---|---|---|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 5 errores: **1 PROPIO** (`FormularioPatrocinador`: faltaba la redacción de `MEDIA_TOKEN_DUPLICADO` tras unificar la unión de códigos) — **corregido en este packet** — y **4 AJENOS**, en `features/admin/{equipos,inscripciones,pagos,participantes}/__tests__/**`: los ficheros `fixtures/*.fixture.ts` de ese árbol **habían desaparecido** mientras el otro agente lo reescribía. **No se tocaron, no se revirtieron ni se fusionaron** |
| V2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 8 errores, **TODOS ajenos** y **TODOS** en `features/admin/**` (el árbol concurrente, en vuelo). **Cero** en las raíces de este packet |
| V3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | **LIMPIO — el proyecto entero.** El agente concurrente reparó su propio árbol durante este packet |
| V4 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | **LIMPIO — verificación final** |

**Las raíces de este packet fueron limpias en todas las corridas** (V1 a V4): los errores ajenos
estaban **exclusivamente** en `features/admin/**`, el árbol **en vuelo** de otro agente, que este
packet **no tocó, no revirtió y no fusionó**.

**NOT RUN** (fuera del permiso de este packet): `vitest` · `biome check` · `next build` · `npm install`
· servidor · navegador · la auditoría de los cinco anchos (360 · 390 · 768 · 1024 · 1440) ·
`python manage.py check` · `pytest` · `git stash` · `git commit` · `git reset` · `git checkout`.

**Tests ESCRITOS, NO EJECUTADOS (6 suites):**

| Suite | Qué congela |
|---|---|
| `features/competencias/__tests__/competencias-estados.test.tsx` | los estados de `ADM-10…ADM-13` (reescrito: los datos salen del espejo) |
| `features/competencias/__tests__/competencia-mirrors.test.ts` | el espejo de `DOM-07`: acepta la forma exacta de cada wrapper, RECHAZA un encuentro sin versión, RECHAZA un ganador no textual, la vista previa NO lleva versión ni motivo, la corrección exige versión + motivo + las dos autorizaciones, y la edición distingue AUSENTE de `null` explícito |
| `features/validaciones/__tests__/validaciones-estados.test.tsx` | los estados de `ADM-16`, `ADM-20` y `ADM-22` (reescrito) |
| `features/validaciones/__tests__/validacion-mirrors.test.ts` | el espejo de `DOM-06`: acepta `EntregaPendienteOut`, RECHAZA un total como cadena (el `Decimal` es número), el estado del pedido y el de la entrega son dos hechos, y el derecho de entrada se REUSA del dueño del lote |
| `features/patrocinadores/__tests__/patrocinadores-estados.test.tsx` | los estados de `ADM-21` (reescrito) |
| `features/patrocinadores/__tests__/patrocinador-mirrors.test.ts` | el espejo de `DOM-08`: acepta la composición de los tres bloques, acepta un patrocinador sin logo ni galería, el logo puede no tener URL, la galería conserva el orden declarado, NO hay ninguna cifra, RECHAZA un identificador que no es UUID, y el alta exige el slug en kebab-case |

### 8.1 La auditoría de los cinco anchos

La matriz de `salesianos-responsive-a11y` exige 360 · 390 · 768 · 1024 · 1440 **con navegador**. Este
packet **no puede abrir un navegador**, así que la auditoría **sigue ABIERTA**. Lo que sí cambió en
el markup y hay que comprobar en el pase de navegador:

- el hueco del logo y de la pieza de la galería ahora se dibuja cuando **falta la URL**, no sólo
  cuando el archivo no es legible (`D-API05-01`): el `alt` y el texto alternativo siguen presentes.

**Riesgos residuales declarados, nunca asumidos verdes:** no hay ejecución de las suites, no hay
auditoría de navegador, no hay pase de tecnología asistiva, no hay reflow al 200 % de zoom y no hay
pasada de `axe` o `Lighthouse`.

---

## 9. Rollback

1. Borrar los 10 ficheros creados (§6.1) y restaurar los 11 modificados (§6.2) desde `HEAD` **o** desde
   el estado previo de `UI-05` (las tres features son de `UI-05`; para restaurarlas basta volver a
   la versión de `UI-05`).
2. `git stash` **nunca** fue invocado; no hay commit de este packet; el punto de rollback del árbol es
   el mismo que antes del packet.
3. **Nunca** restaurar las fixtures provisionales de producción: el rollback devuelve el área al
   estado **sin espejo**, que es el estado honesto de las rutas (no hay datos inventados en ningún
   caso).

---

## 10. Lo que este paquete NO ha hecho (y por qué)

- **No ha registrado ningún controller** ni ha tocado `Aplicacion/backend/**`: el registro es de A0.
- **No ha ligado ninguna ruta**: las dieciséis de `competencias`, la una de `patrocinadores`, las dos
  de `validaciones` y las dos de `entregas` **no existen** (§1.1).
- **No ha inventado** un presenter, un wrapper, un parámetro, un filtro, una paginación, un código de
  éxito ni un endpoint.
- **No ha espejado** `TicketPreviewOut`, `TicketConfirmadoOut` ni `AdminValidacionListItemOut`: no
  tienen presenter.
- **No ha duplicado** `PaseBeneficiarioOut` ni `PedidoLineaOut`: se reutilizan de su dueño.
- **No ha tocado** `features/admin/**` (§5), ni `src/lib/**`, `src/shared/**`, `src/hooks/**`,
  `src/errors/**`, `src/components/**`, `src/providers/**`, `src/app/**`, ni las features de otros
  paquetes, ni `contract/**`, ni `Aplicacion/backend/**`.
- **No ha ejecutado** `vitest`, `biome`, `next build`, servidores ni navegadores.
- **No ha hecho** ninguna operación de git.

---

## 11. Preparación de los consumidores

### 11.1 `XCT-01` (tickets y validación) — **PROVISIONAL**

- **Listo**: los tres espejos del área están escritos y son 1:1 con los presenters que existen. El día
  que exista el módulo `validaciones`, el espejo de sus tres wrappers es **un fichero** y las vistas
  no se reescriben.
- **Pendiente**: `RT-RT-01` y `RT-RT-02` no existen; `ADM-16` no puede comprobar ni confirmar.
- **Arranque**: `POST /validaciones/preview` con el código de la credencial y
  `POST /validaciones/confirmar` con la `idempotency_key` que declara el ledger.

### 11.2 `XCT-02` (transversal admin) — **PROVISIONAL**

- **Listo**: el espejo de `EntregaPendienteOut` y `EntregaConfirmadaOut` está escrito.
- **Pendiente**: `RT-MK-10`/`RT-MK-11` no existen; `ADM-20` no puede listar recogidas.
- **Arranque**: `GET /administracion/marketplace/entregas` y
  `POST /administracion/marketplace/entregas/{pedido_id}/confirmar` (idempotente).

### 11.3 `VER-01…VER-03` — **ABIERTO**

Dependen de la ejecución de las seis suites (no ejecutadas aquí) y de los bloqueos `B-05-01`…
`B-05-08`.

---

## 12. Criterios de aceptación del packet

- [x] **Espejo endpoint/presenter/schema**: completo para todo presenter que **existe** en las tres
      áreas (§2). Lo que **no** tiene presenter está **declarado como ausente**, no inventado.
- [x] **Propiedad de servicio/hook/clave**: **no hay** dataset ligado, luego **no hay** segundo dueño.
      El día que A0 registre los controllers, cada dataset tendrá **un** cliente, **una** factoría de
      claves y **un** hook; las áreas que hoy son dueñas (`features/pases` del lote y del derecho,
      `features/marketplace` del pedido) ya tienen **su** espejo y **este packet no lo duplicó**.
- [x] **Invalidación de caché**: **no aplica** — no hay mutación ligada. La política queda intacta
      (`FND-08`: sin escritura optimista; el servidor es el dueño).
- [x] **Envelope y error**: el espejo usa la fábrica `apiResponseSchema` del proyecto (envelope
      congelado) y `handleApiError` (rama por status) sigue siendo el único lector de errores.
- [x] **Eliminación de mocks**: las **tres** fixtures provisionales del alcance están **eliminadas** y
      el escaneo de cierre de las tres features da **0**.
- [ ] **La previsualización no muta y la confirmación/corrección gestiona el conflicto de versión y el
      impacto**: **BLOQUEADO** por `B-05-01`. Los esquemas están escritos y son correctos
      (`avancePreviewSchema` no lleva versión ni motivo; `correccionAplicarSchema` exige
      `expected_version`, el motivo, `override` **y** `acepta_impacto`), pero **no hay ruta contra la que
      probarlos** en este packet.
- [x] **Ninguna ruta completada usa un mock oculto ni un fallback inventado**: las ocho rutas del
      alcance conservan su **estado honesto** («el servicio todavía no está disponible en el backend»)
      y **ninguna** sale del dispositivo.
- [x] **La propiedad de `ADM-15/17/18/19` está resuelta como NO ATRIBUIDA y re-elevada**
      (`A0-API05-05`), **sin tocar** ninguna raíz ajena.

---

## 13. Siguiente paquete

**`XCT-01`** (tickets y validación), y después **`XCT-02`** y **`XCT-03`** por dependencia.
El **cableado global de A0** (`A0-API05-01`) es el camino crítico de las tres.
