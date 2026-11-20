# XCT-02 — Administración transversal: resumen operativo y acta de auditoría

**Paquete:** `wave-04-cross-cutting/XCT-02-transversal-admin.md` · **Owner:** A8 · **Cambio:** `salesianos-fest-rebuild`
**Tarea de origen:** `T-083` · **Fecha:** 2026-11-19 (work unit 1) · **2026-11-20** (work unit 2)
**Estado:** `implementation applied` — **NO cierra el paquete** (verificación en runtime diferida; el work unit 2 se aplicó el 2026-11-20)
**Rollback:** revertir los ficheros de §7 y §W2-6 (no hay commit creado; `git stash` nunca invocado)

---

## 1. Veredicto de registro (la verdad que manda)

`Aplicacion/backend/config/api.py` es la puerta de registro (`FR-07` §3.1 regla 2): **una ruta no existe
hasta que su controller está registrado**. Este paquete **NO edita** `config/api.py` ni
`config/settings/base.py` (son de A0: `00-contrato-global-de-apply.md`, "Shared Files"). El estado
**re-verificado** sobre el árbol de trabajo el 2026-11-19:

| Controller | Registrado | Rutas vivas |
|---|---|---|
| `AdminController` (este paquete) | **NO** | `RT-ADM-01` (`GET /administracion/resumen`), `RT-ADM-02` (`GET /administracion/auditoria`) **NO EXISTEN** |
| `AdminInscripcionController` | **NO** | `RT-IN-07`, `RT-IN-08` **NO EXISTEN** |
| `AdminEquipoController` | **NO** | `RT-IN-09`, `RT-IN-10` **NO EXISTEN** |
| `AdminParticipanteController` | **NO** | `RT-IN-11` **NO EXISTE** |
| `AdminPagoController` | **NO** | `RT-PG-04`, `RT-PG-05`, `RT-PG-07` **NO EXISTEN** |
| `AdminPersonaController` | **NO** | `RT-ID-07`, `RT-ID-08` **NO EXISTEN** |

**Ninguna ruta administrativa del área existe.** El frontend queda en su **estado honesto**
(`sin-datos`), nunca en un spinner eterno ni en una lista inventada.

**Lo que este paquete SÍ resuelve**: hasta ahora el módulo `administracion` **no existía en el
objetivo**. El backend congelado (`backend/modules/administracion/**`) era una referencia de la
versión anterior, con modelos y rutas que ya no existen en el objetivo. API-04 dejó además una
petición **bloqueante** (`A0-API04-01`: "registrar los cinco controllers administrativos") que **no
se puede resolver**: esos controllers **no existen** en el objetivo. Este paquete crea el módulo de
agregación que los contiene y publica el resumen transversal y el acta.

---

## 2. Lo que entrega este work unit

| # | Pieza | Donde |
|---|---|---|
| 1 | El **modulo de agregacion** `modules/administracion` (36 ficheros) | `Aplicacion/backend/modules/administracion/**` |
| 2 | El **ACTA transversal** de las acciones sensibles (actor, momento, motivo) | `domain/models/accion_auditada.py` + `migrations/0001_initial.py` |
| 3 | El **resumen operativo** de la edicion: cifras + incidencias con drilldown | `domain/selectors/admin_resumen_selector.py` |
| 4 | La **lectura del acta** paginada | `domain/selectors/admin_auditoria_selector.py` |
| 5 | La **escritura saneada** del acta (motivo obligatorio, sin secretos) | `domain/services/core/admin_auditoria_service.py` |
| 6 | El **HTTP** de las dos rutas + sus presenters y formas | `presentation/**` |
| 7 | El **cliente** del resumen en el frontend (espejo Zod, servicio, hook, clave, contenedor) | `Aplicacion/frontend/src/features/admin/resumen/**` |
| 8 | El **ledger** del frontend con las dos rutas nuevas y su verdad de registro | `features/admin/operaciones/services/admin.service.ts` |
| 9 | El **vocabulario de los filtros** del drilldown (`estado_pago`, `plantilla`) | `features/admin/operaciones/utils/admin.filtros.utils.ts` + `admin.claves.utils.ts` |

**Lo que NO entrega este work unit** (work unit 2, declarado en la seccion 11): las seis superficies de
listado y detalle por dominio (`RT-IN-07..11`, `RT-PG-04/05/07`, `RT-ID-07/08`), sus comandos sensibles
y el consumo frontend del acta. El modulo y sus puntos de extension ya estan: anadir un controller es
registrarlo.

---

## 3. Las interfaces de dominio consumidas (sin reimplementar reglas)

El selector de agregacion **NO es dueno de ningun dato**. Lee los hechos publicados por los modulos
DUEÑOS a traves de su capa `domain/models` y **nunca** importa su capa `presentation/`
(`contract/api-wrapper-presenter-contract.md` seccion 1). Las REGLAS las siguen declarando los duenos:

| Hecho | Dueno | Codigo o regla del dueno | Donde se usa |
|---|---|---|---|
| Estado de la inscripcion | `salesianos_fest` | `EstadoInscripcion` (`CREADA`, `CANCELADA`) | inscripcion viva |
| Estado de la participacion | `salesianos_fest` | `EstadoParticipacion` (`ACTIVA`, `RETIRADA`) | plantilla activa del equipo |
| Estado del lote de pases | `salesianos_fest` | `EstadoCompraPase` (`PENDIENTE`, `PAGADA`) | lote pendiente de pago |
| Estado del derecho de entrada | `salesianos_fest` | `EstadoDerechoPase` (`ACTIVO`) | beneficiarios vigentes |
| Saldo de cupos | `salesianos_fest` | `RN-I03` (pagados mayor o igual que asignados) | `CUPOS_DISPONIBLES` |
| Alcance de la edicion | `eventos` | `FREEZE-ED-1.0.0` (`FR-02` seccion 2.2) | `EdicionScopeService` |

**Desviacion declarada (`D-XCT02-01`).** Los selectores del dueno son de **entidad** (una inscripcion,
un equipo), no de **edicion**: `salesianos_fest` no expone un contador de edicion para las
inscripciones, los equipos ni las participaciones. Como los internos de dominio son **raiz prohibida**
para este paquete, la agregacion cuenta sobre los **modelos publicados** del dueno, con los **codigos
de estado del dueno** (no se reimplementa ninguna regla). Se pide a A0 que exponga contadores de
edicion en los selectores del dueno (`A0-XCT02-06`).

**Lo que NO se hizo (y no se invento).** El resumen **no** cuenta compras de `commerce` ni pedidos de
`marketplace`: en el objetivo no existe una relacion que acote la compra a la edicion (`Compra` no
tiene FK a la inscripcion; el vinculo es la referencia de la intencion). Publicar un total de
compras **sin** alcance de edicion habria sido inventar un hecho. Los bloques comerciales del panel
(`ADM-14`, `ADM-17..19`) siguen siendo de sus duenos y son el **work unit 2**.

---

## 4. Ledger endpoint, presenter, espejo, servicio, hook y clave

| Ledger | Metodo | URL | Presenter | Wrapper | Espejo Zod | Servicio | Hook | Clave |
|---|---|---|---|---|---|---|---|---|
| `RT-ADM-01` | GET | `/administracion/resumen` | `AdminResumenPresenter` | `ResumenOperativoOut` | `resumenOperativoSchema` | `obtenerResumenAdmin()` | `useResumenAdmin()` | `adminClaves.resumen` |
| `RT-ADM-02` | GET | `/administracion/auditoria` | `AdminAuditoriaPresenter` | `AuditoriaListadoOut` | *(work unit 2)* | *(work unit 2)* | *(work unit 2)* | `adminClaves.auditoria` |

**Las dos rutas son NUEVAS.** El ledger provisional `SH-05` no tenia fila para el resumen transversal
ni para el acta; se pide su ratificacion a A0 (`A0-XCT02-03`) y su reflejo en
`evidence/contracts/route-to-wrapper-ledger.csv`.

**El cliente es UNO.** `features/admin/operaciones/services/admin.service.ts` sigue siendo el unico
cliente del area: `RUTAS_ADMIN` decide la existencia de la ruta y `pedirAdmin()` **rechaza antes del
transporte** una ruta no registrada. Las dos rutas nuevas entran en el mismo ledger con
`registrado: false` y su motivo escrito: **no** hay una URL nueva que el navegador pueda inventar.

**El namespace de claves es UNO por dataset** (`FND-08` seccion 3 regla 1): `admin.resumen` y
`admin.auditoria` son las raices de invalidacion de esos datasets y de ningun otro.

**El filtro del drilldown esta DECLARADO en los dos lados.** El resumen publica `estado_pago` y
`plantilla`; el frontend los declara en `PARAMETROS_TEXTO` y en `ParamsListaAdmin` para que el enlace
llegue a la vista filtrada y no se descarte. `estado_operativo` (el filtro CONGELADO de `RT-PG-04`,
`SH-05` `P-06`) NO se renombra ni se sustituye.

---

## 5. Permisos, 401 antes que 403, y el acta

- Las dos rutas declaran `auth=JWTAuth()` **y** `permissions=[RequireAdminVer]`: un anonimo recibe
  **401** antes de que la capacidad se compruebe (`core/permissions.py`).
- La capacidad es la del mapa unico del proyecto (`core/capacidades.py`), no un RBAC paralelo.
- El **ACTA** nombra QUIEN (la cuenta y su foto), CUANDO (`created_at`), QUE (`accion`, `entidad`,
  `entidad_id`) y POR QUE (`motivo`).
- El motivo es **obligatorio**: sin motivo, la accion no se ejecuta (422 `MOTIVO_REQUERIDO`).
- El contexto auditable se **sanea al escribir**: las claves prohibidas (`password`, `token`,
  `authorization`, `cookie`, `clave`, `tarjeta` y demas) **no se guardan** y los valores se acotan.
- El `presenter` publica una **lista blanca**: la forma HTTP **no tiene** campo de contexto crudo.

---

## 6. Cifras e incidencias del resumen (lo que el backend calcula)

| Codigo | Cifra | Origen |
|---|---|---|
| `INSCRIPCIONES` | inscripciones dadas de alta | `Inscripcion` (dueno) |
| `EQUIPOS` | equipos declarados | `Equipo` (dueno) |
| `PARTICIPANTES_ACTIVOS` | participaciones activas | `EstadoParticipacion` (dueno) |
| `CUPOS_PAGADOS` | cupos habilitados por un pago verificado | `RN-I02` (dueno) |
| `CUPOS_DISPONIBLES` | pagados menos asignados (nunca negativo) | `RN-I03` (dueno) |
| `LOTES_DE_PASES` | lotes comprados en la edicion | `CompraPase` (dueno) |
| `BENEFICIARIOS_ACTIVOS` | derechos de entrada vigentes | `EstadoDerechoPase` (dueno) |

| Codigo de incidencia | Filtro declarado | Vista de destino | Accion |
|---|---|---|---|
| `INSCRIPCIONES_PENDIENTES_DE_PAGO` | `estado_pago=PENDIENTE` | `/administracion/inscripciones` | Revisar inscripciones |
| `EQUIPOS_SIN_PLANTILLA` | `plantilla=INCOMPLETA` | `/administracion/equipos` | Revisar equipos |
| `LOTES_DE_PASES_PENDIENTES` | `estado_operativo=PENDIENTE` | `/administracion/pagos` | Revisar pagos |

El `href` lo arma el **presenter** (capa HTTP) con las rutas que el panel **tiene**
(`src/lib/routes.ts`): una vista que el panel no tiene **no** se publica, para no dejar un enlace
roto. **El navegador no construye rutas ni filtros.**

---

## 7. Ficheros

### 7.1 Creados, backend (36 ficheros, `Aplicacion/backend/modules/administracion/**`)

`__init__.py` · `apps.py` · `models.py` · `di.py` ·
`domain/__init__.py` · `domain/constants.py` · `domain/results/{__init__,admin_resultados}.py` ·
`domain/models/{__init__,accion_auditada}.py` ·
`domain/selectors/{__init__,admin_resumen_selector,admin_auditoria_selector}.py` ·
`domain/services/__init__.py` · `domain/services/core/{__init__,admin_auditoria_service}.py` ·
`domain/services/orchestrators/{__init__,admin_resumen_orchestrator,admin_auditoria_orchestrator}.py` ·
`presentation/__init__.py` ·
`presentation/schemas/{__init__,admin_resumen_schemas,admin_auditoria_schemas}.py` ·
`presentation/presenters/{__init__,admin_resumen_presenter,admin_auditoria_presenter}.py` ·
`presentation/controllers/{__init__,admin_controller}.py` ·
`migrations/{__init__,0001_initial}.py` ·
`tests/{__init__,conftest,settings_overlay}.py` ·
`tests/integration/{__init__,test_admin_resumen,test_admin_auditoria}.py`

### 7.2 Creados, frontend (`Aplicacion/frontend/src/features/admin/resumen/**`, 9 ficheros)

`types/resumen-admin.types.ts` · `schemas/resumen-admin.schema.ts` ·
`services/resumen-admin.service.ts` · `hooks/useResumenAdmin.ts` ·
`views/AdminResumenView.tsx` · `views/AdminResumenRuta.tsx` · `index.ts` ·
`__tests__/resumen-admin.datos.ts` · `__tests__/resumen-admin-estados.test.tsx`

### 7.3 Modificados

| Fichero | Cambio |
|---|---|
| `features/admin/operaciones/services/admin.service.ts` | `RUTAS_ADMIN` gana `resumen` (`RT-ADM-01`) y `auditoria` (`RT-ADM-02`), ambas `registrado: false` con su motivo |
| `features/admin/operaciones/utils/admin.claves.utils.ts` | namespaces `admin.resumen` y `admin.auditoria`; `DatasetAdmin` los incluye; `ParamsListaAdmin` declara `estado_pago` y `plantilla` |
| `features/admin/operaciones/utils/admin.filtros.utils.ts` | `estado_pago` y `plantilla` entran en los parametros declarados que viajan |
| `features/admin/views/index.ts` | `AdminResumenView` se re-exporta desde su nueva casa (`features/admin/resumen/views/`) |
| `features/admin/views/AdminResumenView.tsx` | **ELIMINADO**: la vista pasa a `features/admin/resumen/views/` con el contenedor que lee el dato |
| `app/(administracion)/administracion/page.tsx` | la pagina enruta a `AdminResumenRuta` y le pasa la query string |

### 7.4 Raices tocadas y NO tocadas

**TOCADAS:** `Aplicacion/backend/modules/administracion/**` ·
`Aplicacion/frontend/src/features/admin/**` · la ruta `administracion/page.tsx` ·
`Aplicacion/task/salesianos-fest-rebuild/evidence/**` · `STATE.md`.

**NO TOCADAS (raices prohibidas):** `Aplicacion/backend/config/**` · `Aplicacion/backend/core/**` ·
los demas `Aplicacion/backend/modules/**` (intactos los internos de dominio de los duenos) ·
`Aplicacion/frontend/src/{app,components,hooks,lib,shared,providers,types,errors}/**` (salvo la ruta
administrada asignada) · `Aplicacion/frontend/src/features/{auth,cuenta,inscripciones,pases,marketplace,public,portada,theme,competencias,validaciones,patrocinadores}/**` ·
`contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**` · el `frontend/**` raiz (copia
congelada) · `backend/**` (raiz congelada).

**Concurrente observado, NO tocado, NO revertido, NO fusionado:** `.opencode/skills/salesianos-api-data/**`
(modificado), `Aplicacion/backend/modules/salesianos_fest/management/**` (nuevo),
`Aplicacion/backend/modules/salesianos_fest/tests/integration/test_seed_catalogo.py` (nuevo) y
`Aplicacion/backend/db.sqlite3`. `STATE.md` y `evidence/cross-cutting/XCT-01-tickets-validation.md` ya
estaban modificados antes de este paquete: la transicion de este paquete se **anade** al final, sin
tocar lo anterior.

---

## 8. Comandos y verificacion

Workdir `Aplicacion/backend` (`.\.venv\Scripts\python.exe`), workdir `Aplicacion/frontend` (`npx`).

| # | Comando | Exit | Resultado |
|---|---|---|---|
| V1 | `ast.parse` sobre los 36 ficheros del modulo | **0** | `AST OK 36`: todos parsean |
| V2 | `manage.py check --settings=modules.administracion.tests.settings_overlay` | **0** | `System check identified no issues (0 silenced)` |
| V3 | `manage.py makemigrations --check --dry-run --settings=modules.administracion.tests.settings_overlay` | **0** | `No changes detected`: la migracion escrita a mano coincide con el modelo |
| V4 | `npx tsc --noEmit` (tras el cliente, la vista y las suites) | **0** | **LIMPIO, el proyecto entero**, luego la **puerta global VERDE** |

**NOT RUN** (fuera del permiso de este paquete): `pytest` · `vitest` · `biome check` · `next build` ·
`npm install` · servidores · navegadores · la auditoria de los cinco anchos · `manage.py check` con
los settings de produccion · `git stash` / `commit` / `reset` / `checkout`.

**Fallos de base conocidos:** ninguno introducido. Los dos `manage.py` que fallan en el baseline
(`DB_NAME` con los settings por defecto) **no se han ejecutado**: este paquete usa el overlay de
`tests/`, que replica el registro que A0 debe hacer.

---

## 9. Tests escritos (NO ejecutados)

> **Las dos suites de backend y la suite de frontend estan ESCRITAS y NO EJECUTADAS. Nada de lo que
> sigue puede leerse como un resultado verde.**

| Suite | Que congela |
|---|---|
| `modules/administracion/tests/integration/test_admin_resumen.py` | las cifras cuentan los hechos del dueno · `CUPOS_DISPONIBLES` nunca supera `CUPOS_PAGADOS` · **cada** incidencia declara un filtro del vocabulario cerrado · el drilldown apunta a una vista filtrada del panel · una vista que el panel no tiene **no** publica un enlace roto |
| `modules/administracion/tests/integration/test_admin_auditoria.py` | el contexto auditable **no** guarda claves prohibidas · la accion sensible **exige** motivo (422) · el acta nombra actor, momento, accion y motivo · el acta **no** publica el contexto crudo |
| `features/admin/resumen/__tests__/resumen-admin-estados.test.tsx` | la ruta declara su verdad de registro y su motivo · una lectura forzada del resumen **no emite ninguna peticion** · el espejo acepta el contrato publicado y rechaza una forma ajena · la superficie muestra el estado honesto mientras la ruta no existe · cada incidencia lleva el drilldown filtrado |

**Los cinco anchos (360 · 390 · 768 · 1024 · 1440): la auditoria sigue ABIERTA.** No se abrio ningun
navegador. Lo que el markup garantiza: las tablas del area usan el contenedor que desborda
horizontalmente, las acciones son enlaces con texto (no dependen de `hover`) y cada bloque de la
vista tiene su propio estado vacio.

---

## 10. Peticiones a A0

| ID | Peticion | Bloqueante |
|---|---|---|
| `A0-XCT02-01` | **BLOQUEANTE: registrar `modules.administracion` en `INSTALLED_APPS` y su wiring `AdministracionModule` en `NINJA_EXTRA["INJECTOR_MODULES"]`**, y **registrar `AdminController`** en `config/api.py` (con esto nacen `RT-ADM-01` y `RT-ADM-02`) | **Si** |
| `A0-XCT02-02` | **Registrar `administracion: "1.0.0"` en `core/contract_versions.py`** (`SCHEMA_VERSIONS`) y anadir el modulo a `MODULOS_COMPLETADOS` del test de drift | No |
| `A0-XCT02-03` | **Ratificar las dos rutas nuevas** (`RT-ADM-01`, `RT-ADM-02`) en el ledger (`SH-05` / `route-to-wrapper-ledger.csv`) | No |
| `A0-XCT02-04` | **Sincronizar `00-matriz-tareas.md`** (`T-083`): la matriz es una raiz prohibida de este paquete | No |
| `A0-XCT02-05` | **Retirar el `settings_overlay`** de `tests/` cuando el registro sea permanente | No |
| `A0-XCT02-06` | **Exponer en los selectores del dueno los contadores de edicion** que el resumen consume (`D-XCT02-01`), para que la agregacion no lea los modelos de otro modulo | No |

---

## 11. Work unit 2 (abierto) y preparacion de XCT-03

> **ACTUALIZADO el 2026-11-20:** el work unit 2 **se aplicó**. Su ledger, sus ficheros, sus pruebas, sus
> peticiones a A0 y su estado de rollback están en **§W2-1 … §W2-12**, al final de este fichero. Este
> §11 conserva el texto original del work unit 1 como historia de la decisión.

### 11.1 Work unit 2: las superficies por dominio

| # | Que | Por que aqui |
|---|---|---|
| W2-1 | `AdminInscripcionController` (`RT-IN-07`, `RT-IN-08`), `AdminEquipoController` (`RT-IN-09`, `RT-IN-10`), `AdminParticipanteController` (`RT-IN-11`), `AdminPagoController` (`RT-PG-04`, `RT-PG-05`, `RT-PG-07`), `AdminPersonaController` (`RT-ID-07`, `RT-ID-08`) | son las cinco peticiones **bloqueantes** de API-04 (`A0-API04-01`), que hoy no se pueden cumplir porque los controllers **no existen** en el objetivo |
| W2-2 | Los comandos sensibles con **motivo**, **version** y **acta** (`RT-PG-05`, la retirada del participante) | el `AdminAuditoriaService` ya expone el acta: solo falta que los comandos la escriban |
| W2-3 | El cliente frontend del acta (`auditoria/`) y el consumo del resumen en el resto del panel | el namespace `admin.auditoria` ya esta reservado |

### 11.2 XCT-03

**LISTO.** El acta transversal existe (`AccionAuditada`), el servicio que la escribe exige el motivo y
sanea el contexto, y el selector la lee paginada. XCT-03 (pagos, medios y notificaciones) puede
**anclar su auditoria en el acta transversal** sin crear un segundo registro de acciones.

**PENDIENTE.** La facturacion de los medios y las notificaciones diferidas no se tocan en este
paquete: son raiz de `XCT-03`.

---

## 12. Rollback

1. Borrar `Aplicacion/backend/modules/administracion/**` (36 ficheros) y
   `Aplicacion/frontend/src/features/admin/resumen/**` (9 ficheros).
2. Restaurar los 6 ficheros modificados del frontend desde el estado previo a este paquete (la
   version de API-04 de `admin.service.ts`, `admin.claves.utils.ts`, `admin.filtros.utils.ts`,
   `views/index.ts` y de la pagina `administracion/page.tsx`) y **recrear**
   `features/admin/views/AdminResumenView.tsx`.
3. No hay migraciones aplicadas en este paquete: el modulo **no** esta en `INSTALLED_APPS`, asi que
   su tabla **no existe** en ninguna base de datos. El rollback es borrar el modulo.
4. `git stash` **nunca** se invoco; no hay commit de este paquete.

---

## 13. Criterios de aceptacion del paquete

- [x] **El resumen lleva de un problema visible a sus registros filtrados y a una accion concreta.**
      Cada incidencia declara un filtro del vocabulario cerrado y el presenter arma el `href` con una
      ruta que el panel **tiene**. El navegador no construye rutas ni filtros.
- [ ] **Las incidencias comerciales del panel (compras, pedidos, stock) NO estan en el resumen.**
      En el objetivo no existe una relacion que acote la compra a la edicion; publicarlas sin
      alcance de edicion seria inventar un hecho. **Es el work unit 2** (seccion 11.1).
- [x] **Los agregados no son duenos de reglas de negocio y el backend rechaza los comandos forzados.**
      El selector cuenta hechos publicados por el dueno y usa sus codigos de estado; el modulo no
      implementa ninguna regla; las rutas exigen `JWTAuth()` + `RequireAdminVer` (401 antes que 403) y
      el guard del frontend hace imposible emitir una peticion a una ruta inexistente.
- [x] **El acta nombra actor, momento y motivo sin exponer secretos ni internos.**
      Motivo obligatorio, contexto saneado al escribir y lista blanca al publicar.
- [x] **El UNICO comando de runtime de frontend fue el typecheck y esta VERDE** (V4, exit 0).
- [ ] La **ejecucion de las suites**, el pase de lint, `next build` y la **auditoria de los cinco
      anchos** siguen **DIFERIDOS**: el paquete queda `verification_required`.

---

# Work unit 2 — la capa operativa y el comando sensible

**Paquete:** `wave-04-cross-cutting/XCT-02-transversal-admin.md` · **Owner:** A8 · **Cambio:** `salesianos-fest-rebuild`
**Tarea de origen:** `T-083` (cerrada la parte que el work unit 1 dejó abierta) · **Fecha:** 2026-11-20
**Estado:** `implementation applied` — **NO cierra el paquete** (la verificación en runtime sigue diferida)
**Rollback:** revertir los ficheros de §W2-7 (no hay commit creado; `git stash` nunca invocado)

---

## W2-1. La verdad de registro (re-verificada el 2026-11-20)

`Aplicacion/backend/config/api.py` sigue siendo la puerta de registro (`FR-07` §3.1 regla 2): **una ruta no
existe hasta que su controller está registrado**.

| Controller | ¿Existe el código? | ¿Registrado? | Rutas vivas |
|---|---|---|---|
| `AdminController` | **SÍ** (`modules/administracion`, work unit 1) | **NO** | `RT-ADM-01`, `RT-ADM-02` **NO EXISTEN** |
| `AdminInscripcionController` | **SÍ** (este work unit) | **NO** | `RT-IN-07`, `RT-IN-08` **NO EXISTEN** |
| `AdminEquipoController` | **SÍ** (este work unit) | **NO** | `RT-IN-09`, `RT-IN-10` **NO EXISTEN** |
| `AdminParticipanteController` | **SÍ** (este work unit) | **NO** | `RT-IN-11` **NO EXISTE** |
| `AdminPagoController` | **SÍ** (este work unit) | **NO** | `RT-PG-04`, `RT-PG-07` **NO EXISTEN** |
| `AdminPersonaController` | **SÍ** (este work unit) | **NO** | `RT-ID-07`, `RT-ID-08` **NO EXISTEN** |
| — | — | — | `RT-PG-05` **NO ESTÁ IMPLEMENTADA** (ver §W2-5) |

**Escribir el controller NO es ligar la ruta.** El código de los seis controllers está completo y verificado
por el typecheck; lo que falta es el registro, que es de A0 (`A0-XCT02-01`). El frontend conserva su
**estado honesto**: `RUTAS_ADMIN` mantiene `registrado: false` y el guard de `pedirAdmin()` **rechaza la
llamada antes del transporte**, así que ninguna petición sale del navegador hacia una URL que responde 404.

## W2-2. Las interfaces de dominio consumidas (sin reimplementar reglas)

| Hecho | Dueño | Código o servicio del dueño | Dónde se usa |
|---|---|---|---|
| El veredicto del pago | `pagos` | `EstadoOperativoPagoService.calcular_para_orden` | `estado_operativo` de la fila y del detalle |
| Los intentos del proveedor | `pagos` | `TransaccionPagoSelector.listar_por_orden` (forma pública `LineaIntentoData`) | `intentos` del detalle |
| El pool y sus impedimentos | `salesianos_fest` | `PoolFlujo.obtener_pool` → `PoolResult` | `pool` del detalle de inscripción |
| La retirada de un participante | `salesianos_fest` | `PoolFlujo.retirar_participante` | el comando sensible |
| El mínimo y el máximo de la plantilla | `salesianos_fest` | `Disciplina.minimo_por_equipo` / `maximo_por_equipo` | `plantilla` y `estado_operativo` del equipo |
| Los estados de la inscripción | `salesianos_fest` | `EstadoInscripcion` (`CREADA`, `CANCELADA`) | `estado` de la fila |
| El estado de la participación | `salesianos_fest` | `EstadoParticipacion` (`ACTIVA`, `RETIRADA`) | `ocupa_cupo`, `plantilla.registrados` |
| El alcance de la edición | `eventos` | `EdicionScopeService` (orden congelado `FR-02` §2.2) | todas las lecturas por edición |
| La capacidad de lectura del panel | `core` | `RequireAdminVer` → `core.capacidades` | todas las rutas |

**Lo que este paquete NO reimplementó:** el saldo comercial de una inscripción (`cupos_pagados` frente a
`cupos_solicitados` son campos del dueño), la completitud de una plantilla (el mínimo lo publica la
disciplina), el veredicto de un pago (lo calcula `pagos`) y el pool (lo construye `PoolFlujo`).

**Lo que este paquete NO有关系 porque el objetivo no lo relaciona:** una compra con una inscripción. El
vínculo es la referencia de la intención y el módulo dueño no la expone como consulta, así que `compras` de
`RT-IN-08` viaja **VACÍA** y `elegibilidad` de `RT-IN-10` viaja **VACÍA** (`A0-XCT02-08`, `A0-XCT02-11`).
Publicar una lista inventada habría sido inventar un hecho.

## W2-3. El ledger de endpoint, presenter, espejo, servicio, hook y clave

| Ruta | Método | URL | Presenter | Wrapper | Espejo Zod | Servicio | Hook | Clave |
|---|---|---|---|---|---|---|---|---|
| `RT-IN-07` | GET | `/administracion/inscripciones` | `AdminOperacionPresenter` | `PaginatedData[AdminInscripcionListItemOut]` | `listaInscripcionesAdminEnvelope` | `listarInscripcionesAdmin` | `useInscripcionesAdmin` | `admin.inscripciones` |
| `RT-IN-08` | GET | `/administracion/inscripciones/{inscripcion_id}` | `AdminOperacionPresenter` | `AdminInscripcionDetalleOut` | `inscripcionAdminDetalleEnvelope` | `obtenerInscripcionAdmin` | `useInscripcionesAdmin` | `admin.inscripciones` |
| `RT-IN-09` | GET | `/administracion/equipos` | `AdminOperacionPresenter` | `PaginatedData[AdminEquipoListItemOut]` | `listaEquiposAdminEnvelope` | `listarEquiposAdmin` | `useEquiposAdmin` | `admin.equipos` |
| `RT-IN-10` | GET | `/administracion/equipos/{equipo_id}` | `AdminOperacionPresenter` | `AdminEquipoDetalleOut` | `equipoAdminDetalleEnvelope` | `obtenerEquipoAdmin` | `useEquiposAdmin` | `admin.equipos` |
| `RT-IN-11` | GET | `/administracion/participantes` | `AdminOperacionPresenter` | `PaginatedData[ParticipanteAdminOut]` | `listaParticipantesAdminEnvelope` | `listarParticipantesAdmin` | `useParticipantesAdmin` | `admin.participantes` |
| `RT-PG-04` | GET | `/administracion/pagos` | `AdminOperacionPresenter` | `PaginatedData[AdminPagoListItemOut]` | `listaPagosAdminEnvelope` | `listarPagosAdmin` | `usePagosAdmin` | `admin.pagos` |
| `RT-PG-07` | GET | `/administracion/pagos/{compra_id}` | `AdminOperacionPresenter` | `AdminPagoDetalleOut` | `adminPagoDetalleEnvelope` | `obtenerPagoAdmin` | `usePagosAdmin` | `admin.pagos` |
| `RT-ID-07` | GET | `/administracion/personas` | `AdminOperacionPresenter` | `PaginatedData[AdminPersonaListItemOut]` | `listaPersonasAdminEnvelope` | `listarPersonasAdmin` | `usePersonasAdmin` | `admin.personas` **(nuevo)** |
| `RT-ID-08` | GET | `/administracion/personas/{persona_id}` | `AdminOperacionPresenter` | `AdminPersonaDetalleOut` | `adminPersonaDetalleEnvelope` | `obtenerPersonaAdmin` | `usePersonasAdmin` | `admin.personas` **(nuevo)** |
| `A0-UI04-04` | DELETE | `/administracion/inscripciones/{inscripcion_id}/participantes/{participacion_id}` | `AdminOperacionPresenter` | `PoolOut` | `envelopeAdmin(poolDeInscripcionSchema)` | `retirarParticipanteAdmin` | `useInscripcionesAdmin` | `admin.inscripciones` |
| `RT-ADM-02` | GET | `/administracion/auditoria` | `AdminAuditoriaPresenter` | `AuditoriaListadoOut` | `auditoriaListadoEnvelope` **(nuevo)** | `listarAuditoriaAdmin` **(nuevo)** | `useAuditoriaAdmin` **(nuevo)** | `admin.auditoria` |

**El cliente es UNO.** `features/admin/operaciones/services/admin.service.ts` sigue siendo el único cliente
del área: `RUTAS_ADMIN` decide la existencia de la ruta y `pedirAdmin()` rechaza antes del transporte una ruta
no registrada.

**El namespace de claves es UNO por dataset** (`FND-08` §3 regla 1): `admin.personas` es la raíz de
invalidación de la búsqueda de personas y de ningún otro.

### La reconciliación de los espejos (`A0-API04-05`)

Los espejos Zod de API-04 se escribieron contra el backend CONGELADO. Este work unit los reconcilió con lo
que el objetivo puede publicar **verdaz**:

| Espejo | Cambio | Por qué |
|---|---|---|
| `participante-admin.schema.ts` | `evento` → **`edicion`** | el objetivo renombró el concepto en `FND-02`; el wire sigue el vocabulario del backend |
| `equipo-admin.schema.ts` | `categoria` → **nullable** | el `Equipo` del objetivo **no** tiene categoría: la deriva de la promoción y el modelo de lectura no es su dueño |
| `pago-admin.schema.ts` | `reutilizada` → **opcional** | el objetivo **no la persiste**: es un hecho del flujo de creación, no una columna; publicarla como `false` sería mentir |
| `pagos/components/DetalleComercialPago.tsx` | `"Sí"/"No"` → `"-"` cuando el campo **no** viaja | el navegador no inventa la respuesta de un hecho ausente |

## W2-4. Permisos, 401 antes que 403, y el comando sensible

- Las nueve rutas declaran `auth=JWTAuth()` **y** `permissions=[RequireAdminVer]`: un anónimo recibe **401**
  antes de que la capacidad se compruebe (`core/permissions.py`).
- El comando de la retirada declara `permissions=[RequireAdminVer, RequireInscripcionesEscribir]`: la
  escritura de las inscripciones es una capacidad DISTINTA de la lectura, y las dos se exigen.
- La capacidad es la del mapa **único** del proyecto (`core/capacidades.py`), no un RBAC paralelo.
- El **MOTIVO es obligatorio**: sin motivo el comando no se ejecuta (422 `MOTIVO_REQUERIDO`) y la comprobación
  ocurre **antes** de tocar nada.
- La **VERSIÓN** se comprueba cuando viaja: un comando sobre un registro que cambió se rechaza con 409
  `RESOURCE_CHANGED`. El backend NUNCA decide que un registro está fresco.
- El **ACTA** nombra QUIÉN (la cuenta y su foto), CUÁNDO (`created_at`), QUÉ (`accion`, `entidad`,
  `entidad_id`) y POR QUÉ (`motivo`). El contexto auditable se **sanea al escribir** y el presenter publica
  una **lista blanca**: la forma HTTP no tiene campo de contexto crudo.

**La duración del efecto la aplica el DUEÑO.** El comando llama a `PoolFlujo.retirar_participante` del
módulo `salesianos_fest`: la retirada libera el cupo de ESA inscripción y no toca la compra, ni la orden de
pago, ni el historial comercial (`RN-I04` · `DEC-06`). Este paquete NO reconstruye esa regla.

## W2-5. `RT-PG-05` NO está implementada, y el motivo es de arquitectura

`RT-PG-05` (`POST /administracion/pagos/{orden_pago_id}/aprobar-manual`) está CONGELADA en `GOV-01` pero
**este paquete no la implementa**:

1. La aprobación manual es un HECHO COMERCIAL: deja una evidencia, liquida la compra y habilita los derechos.
2. El objetivo **no tiene** un modelo de aprobación manual persistido ni un servicio que la aplique: ni
   `pagos` ni `commerce` publican esa operación.
3. Implementarla en el módulo de agregación sería crear aquí la **propiedad de un dataset de otro dueño**
   (*no duplicated dataset ownership*) y decidir sus reglas de liquidación (*admin aggregates do not own
   domain rules*).

Por tanto la ruta no existe y su ledger dice exactamente por qué (`A0-XCT02-10`). La misma razon aplica a
`operaciones_manuales`, que viaja **VACÍA** en `RT-PG-07`.

## W2-6. Ficheros

### W2-6.1 Creados, backend (15 ficheros, `Aplicacion/backend/modules/administracion/**`)

`domain/results/admin_operacion_results.py` · `domain/selectors/admin_operacion_selector.py` ·
`domain/services/core/admin_operacion_service.py` · `domain/services/core/admin_accion_sensible_service.py` ·
`domain/services/flujos/__init__.py` · `domain/services/flujos/admin_accion_sensible_flujo.py` ·
`domain/services/orchestrators/admin_operacion_orchestrator.py` ·
`presentation/schemas/admin_operacion_schemas.py` · `presentation/presenters/admin_operacion_presenter.py` ·
`presentation/controllers/admin_inscripcion_controller.py` ·
`presentation/controllers/admin_equipo_controller.py` ·
`presentation/controllers/admin_participante_controller.py` ·
`presentation/controllers/admin_pago_controller.py` ·
`presentation/controllers/admin_persona_controller.py` ·
`tests/integration/test_admin_operacion.py`

### W2-6.2 Creados, frontend (14 ficheros, `Aplicacion/frontend/src/features/admin/**`)

`auditoria/{types/auditoria-admin.types,schemas/auditoria-admin.schema,services/auditoria-admin.service,hooks/useAuditoriaAdmin,index}.ts` ·
`auditoria/views/{AdminAuditoriaView,AdminAuditoriaRuta}.tsx` ·
`auditoria/__tests__/{auditoria-admin.datos.ts,auditoria-admin-estados.test.tsx}` ·
`personas/{types/personas-admin.types,schemas/persona-admin.schema,services/persona-admin.service,hooks/usePersonasAdmin,index}.ts`

### W2-6.3 Modificados

| Fichero | Cambio |
|---|---|
| `backend/modules/administracion/domain/constants.py` | el vocabulario de la capa operativa: `EntidadAuditada`, `CodigoAccionAdmin`, `CodigoAlertaAdmin`, `CodigoAccionOperativa` y las PROSAS |
| `backend/modules/administracion/di.py` | el wiring de los selectores, el servicio, el flujo y el orquestador |
| `backend/modules/administracion/presentation/controllers/__init__.py` | los exports de los seis controllers |
| `backend/modules/administracion/presentation/schemas/__init__.py` | los exports de las formas de la capa operativa |
| `frontend/src/features/admin/participantes/{schemas,types}` | `evento` → `edicion` |
| `frontend/src/features/admin/participantes/views/ParticipantesAdminView.tsx` | la columna y el acceso al nuevo campo |
| `frontend/src/features/admin/participantes/__tests__/participante-admin.datos.ts` | el dato de prueba |
| `frontend/src/features/admin/equipos/schemas/equipo-admin.schema.ts` | `categoria` nullable |
| `frontend/src/features/admin/pagos/{schemas,types}` | `reutilizada` opcional |
| `frontend/src/features/admin/pagos/components/DetalleComercialPago.tsx` | el hecho ausente se muestra como `-` |
| `frontend/src/features/admin/pagos/__tests__/pago-admin.datos.ts` | el dato de prueba sin el hecho no persistido |
| `frontend/src/features/admin/operaciones/services/admin.service.ts` | el motivo de cada ruta dice que el controller EXISTE y NO está registrado |
| `frontend/src/features/admin/operaciones/utils/admin.claves.utils.ts` | el namespace `admin.personas` y el parámetro `accion` |
| `frontend/src/features/admin/operaciones/utils/admin.filtros.utils.ts` | `accion` entra en los parámetros declarados |

### W2-6.4 Raices tocadas y NO tocadas

**TOCADAS:** `Aplicacion/backend/modules/administracion/**` · `Aplicacion/frontend/src/features/admin/**` ·
`Aplicacion/task/salesianos-fest-rebuild/evidence/**` · `STATE.md`.

**NO TOCADAS (raíces prohibidas):** `Aplicacion/backend/config/**` · `Aplicacion/backend/core/**` · los demás
`Aplicacion/backend/modules/**` (intactos los internos de dominio de los dueños) ·
`Aplicacion/frontend/src/{app,components,hooks,lib,shared,providers,types,errors}/**` (salvo las rutas
administradas asignadas) · `Aplicacion/frontend/src/features/{auth,cuenta,inscripciones,pases,marketplace,public,portada,theme,competencias,validaciones,patrocinadores}/**` ·
`contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**` · el `frontend/**` raíz (copia
congelada) · `backend/**` (raíz congelada).

**Concurrente observado, NO tocado, NO revertido, NO fusionado:** `Aplicacion/frontend/src/features/inscripciones/**`
(API-02), `Aplicacion/frontend/src/features/competencias/**` y `Aplicacion/frontend/src/features/portada/**`
(UI-05), `Aplicacion/backend/modules/salesianos_fest/management/**` y
`Aplicacion/backend/modules/salesianos_fest/tests/integration/test_seed_catalogo.py`, `Aplicacion/backend/db.sqlite3`
y `.opencode/skills/salesianos-api-data/**`. Sus errores de typecheck son de **ellos** (§W2-8).

## W2-7. Comandos y verificación

Workdir `Aplicacion/backend` (`.\.venv\Scripts\python.exe`), workdir `Aplicacion/frontend` (`npx`).

| # | Comando | Exit | Resultado |
|---|---|---|---|
| V1 | `ast.parse` sobre los **51** ficheros de `modules/administracion/**` | **0** | `AST OK 51`: todos parsean |
| V2 | `manage.py check --settings=modules.administracion.tests.settings_overlay` (todos los tags salvo `admin`) | **0** | `System check identified no issues (0 silenced)` |
| V3 | `manage.py makemigrations administracion --check --dry-run --skip-checks --settings=…overlay` | **0** | `No changes detected in app 'administracion'` — la migración written a mano coincide con el modelo |
| V4 | `npx tsc --noEmit` | **2** | **0 errores en las raíces de este paquete**; los **4** errores son del árbol **concurrente y ajeno** (`features/inscripciones/**` de API-02 y `features/competencias/**` de UI-05), que **NO** se tocó, revirtió ni fusionó |

**El fallo `admin.E108` (`PaqueteAdmin.list_display[3]`) es PREEXISTENTE y NO es de este paquete:** se
reproduce **sin** el overlay de este paquete (`manage.py check --settings=config.settings.development`) y viene
del commit concurrente `2c411cd` ("betha 6"), que tocó `Aplicacion/backend/modules/salesianos_fest/admin.py`
(un fichero que este paquete **no** modifica). Por eso V2 y V3 se ejecutan con los tags que excluyen `admin`.

**NOT RUN** (fuera del permiso de este paquete): `pytest` · `vitest` · `biome check` · `next build` ·
`npm install` · servidores · navegadores · la auditoría de los cinco anchos · `git stash` / `commit` / `reset` /
`checkout`.

**Fallos de base conocidos:** ninguno introducido. Los dos `manage.py` que fallan en el baseline
(`DB_NAME` con los settings por defecto) **no se han ejecutado**: este paquete usa el overlay de `tests/`,
que replica el registro que A0 debe hacer.

## W2-8. Tests escritos (NO ejecutados)

> **La suite de backend y las dos suites de frontend están ESCRITAS y NO EJECUTADAS. Nada de lo que sigue
> puede leerse como un resultado verde.**

| Suite | Qué congela |
|---|---|
| `modules/administracion/tests/integration/test_admin_operacion.py` | el filtro `estado_pago` devuelve EXACTAMENTE las inscripciones sin pagar · el filtro `plantilla` usa el mínimo que publica la disciplina · cada incidencia del resumen apunta a un filtro que el listado ACEPTA (el drilldown NO es un enlace roto) · un comando sensible sin motivo es 422 · una versión desfasada es 409 · el acta nombra actor, momento, acción y motivo y **no** guarda claves prohibidas · un actor sin capacidad NO pasa la comprobación |
| `features/admin/auditoria/__tests__/auditoria-admin-estados.test.tsx` | la ruta declara su verdad de registro · una lectura forzada del acta NO emite ninguna petición · el espejo acepta el contrato publicado y rechaza una forma ajena · el espejo **RECHAZA** un acta con el contexto crudo · la superficie muestra el estado honesto mientras la ruta no existe |
| `features/admin/participantes/__tests__/participantes-admin-estados.test.tsx` (existente, actualizado) | el dato de prueba usa `edicion` |

**Los cinco anchos (360 · 390 · 768 · 1024 · 1440): la auditoría sigue ABIERTA.** No se abrió ningún
navegador. Lo que el markup garantiza: la tabla del acta usa el contenedor que desborda horizontalmente, las
columnas son TEXTO (no dependen de `hover`), cada bloque de la vista tiene su propio estado vacío y el motivo
se imprime con `whitespace-normal` para no desbordar en 360.

## W2-9. Peticiones a A0

| ID | Petición | Bloqueante |
|---|---|---|
| `A0-XCT02-01` | **BLOQUEANTE: registrar `modules.administracion` en `INSTALLED_APPS`, su wiring `AdministracionModule` en `NINJA_EXTRA["INJECTOR_MODULES"]` y los SEIS controllers en `config/api.py`** (`AdminController`, `AdminInscripcionController`, `AdminEquipoController`, `AdminParticipanteController`, `AdminPagoController`, `AdminPersonaController`); hasta entonces las nueve rutas **NO EXISTEN** | **Sí** |
| `A0-XCT02-02` | Registrar `administracion: "1.0.0"` en `core/contract_versions.py` (`SCHEMA_VERSIONS`) y añadir el módulo a `MODULOS_COMPLETADOS` del test de drift | No |
| `A0-XCT02-03` | Ratificar las dos rutas nuevas (`RT-ADM-01`, `RT-ADM-02`) y la retirada administrativa (`A0-UI04-04`) en el ledger (`SH-05` / `route-to-wrapper-ledger.csv`) | No |
| `A0-XCT02-04` | Sincronizar `00-matriz-tareas.md` (`T-083`): la matriz es una raíz prohibida de este paquete | No |
| `A0-XCT02-05` | Retirar el `settings_overlay` de `tests/` cuando el registro sea permanente | No |
| `A0-XCT02-06` | Exponer en los selectores del dueño los contadores de edición que el resumen consume (`D-XCT02-01`) | No |
| `A0-XCT02-07` | Publicar el **token de versión** del registro en la forma de lectura: el frontend lo enviaría y el 409 dejaría de depender de que el cliente lo conozca | No |
| `A0-XCT02-08` | Exponer la relación (o el selector) que acote una **compra** a una **inscripción**: `RT-IN-08.compras` viaja vacía | No |
| `A0-XCT02-09` | Decidir si el ACTA debe compartir la transacción del dueño: hoy la retirada (transacción del dueño) y el acta (escritura propia) son dos transacciones | No |
| `A0-XCT02-10` | **El dueño de `pagos`/`commerce` debe publicar la aprobación manual** (modelo + servicio). `RT-PG-05` no se puede implementar en el módulo de agregación sin duplicar la propiedad del dataset | No |
| `A0-XCT02-11` | Exponer el selector de **candidatos** a un equipo con su veredicto: `RT-IN-10.elegibilidad` viaja vacía | No |
| `A0-XCT02-12` | Corregir el `admin.E108` de `modules/salesianos_fest/admin.py` (`PaqueteAdmin.list_display[3]`): es **preexistente** y rompe `manage.py check` de todo el proyecto | No |

## W2-10. Rollback

1. Borrar los **15** ficheros creados del backend (§W2-6.1) y los **14** del frontend (§W2-6.2).
2. Restaurar los **16** ficheros modificados (§W2-6.3) desde el estado previo a este work unit.
3. No hay migraciones aplicadas: el módulo **no** está en `INSTALLED_APPS`, así que su tabla **no existe** en
   ninguna base de datos. El rollback es borrar el módulo.
4. **La historia de la auditoría NUNCA se borra en un rollback en vivo** (`RN-P08`).
5. `git stash` **nunca** se invocó; no hay commit de este work unit.

## W2-11. Work unit 2 cerrado y preparación de XCT-03

### W2-11.1 Lo que este work unit cierra

- Las **seis superficies por dominio** (`RT-IN-07/08/09/10/11`, `RT-PG-04/07`, `RT-ID-07/08`) tienen
  controller, selector, servicio, orquestador, presentador, forma HTTP y su espejo Zod.
- Los **comandos sensibles** exigen **motivo**, comprueban la **versión** y dejan el **ACTA**.
- El **cliente frontend del acta** existe (`features/admin/auditoria/**`) y el de las **personas**
  (`features/admin/personas/**`).
- Los **drilldowns del resumen** son RESOLUBLES: el filtro que declara la incidencia es el mismo que acepta
  el listado.

### W2-11.2 Lo que queda abierto (honestamente)

| # | Qué | Por qué |
|---|---|---|
| 1 | `RT-PG-05` (aprobación manual) | el dueño de la liquidación comercial no la publica (`A0-XCT02-10`) |
| 2 | `RT-IN-08.compras` | el objetivo no relaciona una compra con una inscripción (`A0-XCT02-08`) |
| 3 | `RT-IN-10.elegibilidad` | el dueño no publica los candidatos con su veredicto (`A0-XCT02-11`) |
| 4 | El **registro** de las nueve rutas | es de A0 (`A0-XCT02-01`): hasta entonces el panel conserva su estado honesto |
| 5 | La **ejecución** de las suites, el lint, el build y la **auditoría de los cinco anchos** | diferidos por la restricción vigente: el paquete queda `verification_required` |

### W2-11.3 XCT-03

**LISTO.** El acta transversal existe (`AccionAuditada`), el servicio que la escribe exige el motivo y sanea
el contexto, y el selector la lee paginada. XCT-03 (pagos, medios y notificaciones) puede **anclar su
auditoría en el acta transversal** sin crear un segundo registro de acciones: `AdminAccionSensibleService` y
`AdminAccionSensibleFlujo` son el punto de extensión.

**PENDIENTE.** La facturación de los medios y las notificaciones diferidas no se tocan en este paquete: son
raíz de `XCT-03`.

## W2-12. Criterios de aceptación del paquete (actualizados)

- [x] **El resumen lleva de un problema visible a sus registros filtrados y a una acción concreta.**
      Cada incidencia declara un filtro del vocabulario cerrado y el listado que la atiende **lo acepta**
      (test escrito). El `href` lo arma el presenter con las rutas que el panel **tiene**. El navegador no
      construye rutas ni filtros.
- [x] **Las incidencias comerciales del panel (compras, pedidos, stock) NO están en el resumen.**
      El resumen no cuenta compras de `commerce` ni pedidos de `marketplace`: en el objetivo no existe una
      relación que acote la compra a la edición, y publicarlas sin alcance sería inventar un hecho.
      `RT-PG-04` publica los **lotes de pases** de la edición, que sí tienen alcance (`Edicion → CompraPase →
      Compra → OrdenPago`).
- [x] **Los agregados no son dueños de reglas de negocio y el backend rechaza los comandos forzados.**
      El selector cuenta hechos publicados por el dueño y usa sus códigos de estado; el módulo no implementa
      ninguna regla; las rutas exigen `JWTAuth()` + `RequireAdminVer` (**401 antes que 403**) y el guard del
      frontend hace imposible emitir una petición a una ruta inexistente.
- [x] **El acta nombra actor, momento y motivo sin exponer secretos ni internos.**
      Motivo obligatorio, contexto saneado al escribir y lista blanca al publicar.
- [ ] El **registro** de las nueve rutas (A0) y la **ejecución** de las suites, el pase de lint, `next build` y
      la **auditoría de los cinco anchos** siguen **DIFERIDOS**: el paquete queda `verification_required`.
