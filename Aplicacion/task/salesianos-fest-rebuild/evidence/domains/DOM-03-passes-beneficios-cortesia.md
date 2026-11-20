# DOM-03 — Pases: catálogo, compra, beneficiarios y cortesía

**Packet:** `DOM-03` · **Change:** `salesianos-fest-rebuild` · **Owner:** A4
**Tareas de origen:** `T-030`, `T-031`, `T-032` · **Fecha:** 2026-11-19
**ESTADO: `verification_required`** — la verificación en runtime está
**DIFERIDA por instrucción explícita del usuario**: las pruebas se ESCRIBEN
pero **NO se ejecutan**. Ver §6.

---

## 1. Qué se entregó

### 1.1 La raíz física

El dominio de pases vive en **`Aplicacion/backend/modules/salesianos_fest/`**,
la MISMA app que `DOM-01` (inscripciones) y `DOM-02` (pool). Su código se
CONSERVÓ íntegro: este paquete sólo AÑADIÓ capas nuevas y extendió los
vocabularios.

**Por qué esta raíz y no una app nueva `modules/pases/`:**

- El plan lo autoriza explícitamente: *"La existencia de un módulo **lógico**
  no obliga a crear una aplicación Django separada. La separación física se
  decidirá por cohesión, volumen y dependencia real."*
  (`funcional/01` §1).
- Los pases necesitan el alcance de edición (`eventos`), el padrón de
  identidades (`usuarios`) y la compra congelada (`commerce`), que son
  EXACTAMENTE los tres puertos que `salesianos_fest` ya declara. Una app
  nueva los duplicaría.
- La evidencia congelada de la ola de dominio (`STATE.md`, apply-progress
  índice) sitúa la raíz del dominio en `modules/salesianos_fest/**`.

**La ruta HTTP NO cambia**: el ledger congelado declara `/pases/...`, y esas
rutas existen tal cual. El "módulo dueño" del ledger (`pases`) es la
responsabilidad de A4, no la carpeta Django.

### 1.2 El modelo — seis modelos nuevos

| Modelo | Tabla | Qué es |
|---|---|---|
| `Pase` | `fest_pase` | El TIPO de entrada del catálogo, con alcance de EDICIÓN |
| `PasePrecio` | `fest_pase_precio` | El precio de catálogo, con su ventana de vigencia |
| `CompraPase` | `fest_compra_pase` | El LOTE comprado: unidades, importe congelado y token privado |
| `PaseBeneficiario` | `fest_pase_beneficiario` | El DERECHO efectivo de una persona (origen `COMPRA` o `CORTESIA`) |
| `CortesiaPase` | `fest_cortesia_pase` | El ACTA auditada de una cortesía |
| `ActivacionPase` | `fest_activacion_pase` | El acta de idempotencia de la activación (`FND-05`) |

**El diseño central: UN DERECHO, DOS ORÍGENES.** `PaseBeneficiario` es la
tabla de derechos efectivos y su columna `origen` discrimina `COMPRA` /
`CORTESIA` (`RN-P02`). Así la regla de **no duplicación** es UNA sola
restricción parcial única y vale para los dos orígenes:

```
fest_pase_beneficiario_activo_unico_por_persona
    UNIQUE (edicion, pase, persona) WHERE estado = 'ACTIVO'
```

Una cortesía NO puede duplicar una compra, ni al revés: es la MISMA
restricción.

### 1.3 Las reglas congeladas y cómo se cumplen

| Regla | Cómo se cumple | Dónde |
|---|---|---|
| `RN-E01` (alcance de edición) | `Pase`, `PasePrecio`, `CompraPase`, `PaseBeneficiario` y `CortesiaPase` cuelgan de `eventos.Edicion` | `domain/models/` |
| `RN-C02` (el servidor congela el precio) | el payload NO admite importe; el precio lo resuelve el servidor contra el catálogo vigente y el total se DERIVA con `calcular_total` de `commerce` (la MISMA expresión) | `CompraPaseFlujo` |
| `RN-P02` (origen y estado de cada derecho) | `CompraPase.estado` + `PaseBeneficiario.origen` | `domain/models/derecho_pase.py` |
| `RN-P02` (una compra pendiente NO habilita) | `CompraPase.estado = PENDIENTE` hasta la ACTIVACIÓN; la asignación lo rechaza con `COMPRA_PASE_NO_PAGADA` | `BeneficiarioFlujo._verificar_pagada` |
| `RN-P03` / `PD-01` (BOX) | **NO se modela BOX.** No hay ninguna marca de BOX en el catálogo: la titularidad del beneficio grupal sigue ABIERTA | §7 · `OD-DOM03-02` |
| `RN-P04` (comprador ≠ asistente) | `CompraPase.comprador` es el titular; `PaseBeneficiario.persona` es quien asiste. Son columnas y personas distintas | `domain/models/derecho_pase.py` |
| `RN-P05` (cortesía con actor, fecha y motivo; NO un cobro de S/ 0) | `CortesiaPase` NO tiene ninguna columna que lo enlace con `commerce.Compra`, `pagos.OrdenPago` ni `pagos.TransaccionPago`. La AUSENCIA del enlace es la garantía | `domain/models/derecho_pase.py` · §1.5 |
| `RN-P06` (escanear no es usar) | el módulo NO implementa el canje: sólo concede el derecho. `cantidad_consumida` nace en cero y la escribe el módulo de validación (`XCT-01`) | `PaseBeneficiario.cantidad_consumida` |
| `RN-P07` (consumo auditado, sin duplicar) | la restricción parcial única es la autoridad; la excepción `PaseDuplicadoError` es su traducción legible | `BeneficiarioCoreService` |
| `RN-P08` (revocar invalida el futuro, el pasado permanece) | el derecho pasa a `REVOCADO` con instante, motivo y actor; los consumos ya ocurridos no se tocan | `BeneficiarioCoreService.revocar` |
| `RN-U04` (el documento NO es credencial) | el acceso al lote es por TITULAR autenticado, ADMINISTRADOR o TOKEN; el DNI no abre nada | `PaseAccesoService` |
| `QA-P01` (compra sin cuenta → habilitación tras pago) | la compra invitada NO crea `Usuario`; los pases se habilitan sólo tras la activación | §1.4 · §1.6 |
| `QA-P02` (asignación limitada y sin derecho duplicado) | capacidad pagada + unicidad parcial | §1.4 |
| `QA-P03` (cortesía con motivo y sin transacción ficticia) | actor + motivo obligatorios; cero hechos financieros | §1.5 |

### 1.4 La compra y la asignación

**La compra (`RT-CM-02`, CONGELADA en el ledger).** `POST /pases/compras`:

- **Sin cuenta obligatoria**: el comprador es una identidad CIVIL. Si la
  petición va autenticada, el comprador es el ACTOR y el documento del
  payload se **IGNORA**; si es un invitado, la identidad se resuelve o se
  REGISTRA en el padrón por el puerto `IObtensionPersonaService`. **Nunca**
  se crea un `Usuario`.
- El precio lo congela el servidor; el total se deriva con la expresión de
  `commerce`.
- El lote nace `PENDIENTE` con un **token privado** (`secrets.token_urlsafe`,
  con vencimiento y revocabilidad). El token es la credencial del enlace de
  gestión y es de **ÁMBITO POR COMPRA**.
- Un reintento con la misma intención **RECUPERA** la misma compra y el
  mismo lote (`FR-04` I-4).

**La asignación (`RT-PS-05`).** `POST /pases/compras/{id}/beneficiarios`:

- Sólo se asigna **capacidad pagada**: la comprobación y la reserva ocurren
  DENTRO de la misma transacción.
- La reserva de la unidad es un `UPDATE` **CONDICIONAL**
  (`WHERE asignados < cantidad`): dos asignaciones simultáneas no pueden
  sobre-asignar el lote. Es el mismo patrón que `CapacidadCoreService` de
  `DOM-02`: la base de datos decide quién entra.
- La no duplicación la impone la base de datos; la excepción se traduce
  FUERA de la transacción, para que la unidad reservada se libere con el
  rollback.

**La revocación y su alcance.** `RT-RT-03` (CONGELADA) es
`DELETE /pases/compras/{compra_id}/beneficiarios/{persona_id}`:

- **Permanente**: el derecho deja de ser canjeable para validaciones
  futuras; los consumos yagulpACParecen.
- **Auditada**: actor, instante y motivo.
- **Idempotente**: la segunda revocación informa del estado final con
  `ya_revocado=True`; no es un error.
- El ledger congelado declara esta ruta **SIN schema de entrada**: el motivo
  viaja como parámetro de consulta.

### 1.5 La cortesía (`RT-PS-08`)

`POST /administracion/pases/cortesias` (Administrador):

- Registra un **ACTA** (`CortesiaPase`) con actor, motivo y fecha, y el
  **DERECHO** correspondiente (`PaseBeneficiario` con origen `CORTESIA`), en
  la misma transacción.
- El motivo es **obligatorio** (`CORTESIA_MOTIVO_INVALIDO`, 422).
- **No crea** compra, orden de pago ni transacción: el modelo no tiene
  ninguna columna que lo permita. El test lo comprueba contando los hechos
  financieros antes y después, y otro test comprueba el ESQUEMA del acta.
- Un administrador sin cuenta no puede: `ACTOR_REQUERIDO` (401).

### 1.6 La activación de derechos (FND-05)

`ActivadorPase` implementa el puerto `IActivadorDominioCompra` de `commerce`
para el origen `PASE` y se registra en `apps.py::ready()`, junto al
`ActivadorInscripcion` de `DOM-02`.

**El coordinador de `commerce` NO se tocó**: ni `CoordinadorActivacionCompra`,
ni `ActivacionCompra`, ni `RegistroActivadoresCompra`. El paquete sólo
consume el puerto congelado (`contexto.clave`, `contexto.compra_id`,
`contexto.referencia`, `contexto.lineas_snapshot`).

La activación:

1. resuelve el lote por `compra_id` (la clave: un lote por compra);
2. **comprueba** que la referencia de intención es de este módulo y describe
   ESA compra — una referencia ajena se rechaza con
   `REFERENCIA_PASE_NO_RECONOCIDA`, sin adivinar;
3. registra el ACTA con la `clave` ÚNICA del coordinador → la idempotencia
   la garantiza la base de datos (`FR-04` I-2);
4. marca el lote `PAGADA` → a partir de ahí se puede asignar.

### 1.7 El acceso y el token

`PaseAccesoService` decide quién abre un lote. TRES credenciales, una basta:

| Credencial | Condición | Autoridad |
|---|---|---|
| Administrador | siempre | `core.capacidades.es_admin` — la ÚNICA mapa de permisos del proyecto (FND-01) |
| Titular autenticado | con cuenta | el actor es la persona COMPRADORA (`FR-03` §2.1) |
| Token privado | sin cuenta | el enlace, de ÁMBITO POR COMPRA (`contratos/02` §5) |

- El token viaja en la cabecera **`X-Pase-Token`** (nunca en la query
  string: la query string queda en los logs). La comparación es en TIEMPO
  CONSTANTE (`secrets.compare_digest`).
- Token ausente, inválido, expirado o revocado → **401**
  `TOKEN_PASE_INVALIDO` (es un fallo de AUTENTICACIÓN de la credencial).
- Credencial válida pero insuficiente → **403**
  `COMPRA_PASE_NO_AUTORIZADA`.
- **401 antes que 403**, como manda la autoridad de permisos.

### 1.8 La superficie HTTP

| Ruta | Método | Presenter | Wrapper |
|---|---|---|---|
| `RT-PS-01` | GET `/pases` | `PaseCatalogoPresenter` | `PaseCatalogoOut` |
| `RT-PS-02` | GET `/pases/{pase_id}` | `PaseDetallePresenter` | `PaseDetalleOut` |
| `RT-CM-02` | POST `/pases/compras` | `CompraPasePresenter` | `CompraPaseCreadaOut` |
| `RT-PS-03` | GET `/pases/compras/{compra_pase_id}` | `PaseCompraDetallePresenter` | `PaseCompraDetalleOut` |
| `RT-PS-04` | GET `/pases/compras/{compra_pase_id}/beneficiarios` | `PaseBeneficiariosPresenter` | `PaseBeneficiariosOut` |
| `RT-PS-05` | POST `/pases/compras/{compra_pase_id}/beneficiarios` | `PaseBeneficiarioAsignarPresenter` | `PaseBeneficiariosOut` |
| `RT-RT-03` | DELETE `/pases/compras/{compra_pase_id}/beneficiarios/{persona_id}` | `PaseBeneficiarioPresenter` | `PaseBeneficiarioRevocadoOut` |
| `RT-PS-06` | GET `/administracion/pases` | `AdminPaseListaPresenter` | `PaginatedData[AdminPaseListItemOut]` |
| `RT-PS-07` | GET `/administracion/pases/cortesias` | `AdminCortesiaListaPresenter` | `PaginatedData[AdminCortesiaListItemOut]` |
| `RT-PS-08` | POST `/administracion/pases/cortesias` | `AdminCortesiaCrearPresenter` | `AdminCortesiaOut` |

Los nombres de presenter y wrapper son los del ledger congelado
(`FR-07` §3.3 para `RT-CM-02` y `RT-RT-03`; `SH-05` §1.4 para las ocho
provisionales).

**`SCHEMA_VERSION` de `salesianos_fest`: `1.1.0` → `1.2.0` (MINOR).** El
cambio es ADITIVO: no se modifica ni se elimina ninguna forma de respuesta
existente.

---

## 2. Los controladores no contienen reglas de negocio

| Decisión | Dónde vive |
|---|---|
| Qué pase está a la venta | `PaseFlujo` / `PaseSelector` |
| Cuál es el precio vigente | `PaseSelector.obtener_precio_vigente` |
| Si la compra habilita | `BeneficiarioFlujo._verificar_pagada` |
| Si el derecho se duplica | la base de datos + `BeneficiarioCoreService` |
| Quién abre el lote | `PaseAccesoService` |
| La aritmética de capacidad | `PaseCoreService.reservar_pase` (UPDATE condicional) |
| La causa operativa | el dominio (`CausaOperativaCompraPase`), la publica el presenter |
| El mensaje de éxito | el controller (texto FIJO, sin identificadores) |
| El mensaje de error | `core/exceptions.py` (el controller NO construye errores) |

El controller sólo: parsea el payload, extrae la cabecera del token, delega
en el orquestador y devuelve `success_response(presenter.present_x(...))`.

---

## 3. Ficheros cambiados (todos dentro de las raíces permitidas)

### 3.1 Creados (26)

```
Aplicacion/backend/modules/salesianos_fest/domain/models/pase.py
Aplicacion/backend/modules/salesianos_fest/domain/models/derecho_pase.py
Aplicacion/backend/modules/salesianos_fest/domain/referencia_pase.py
Aplicacion/backend/modules/salesianos_fest/domain/constants.py            (extendido)
Aplicacion/backend/modules/salesianos_fest/domain/exceptions.py           (extendido)
Aplicacion/backend/modules/salesianos_fest/domain/ports/__init__.py        (extendido)
Aplicacion/backend/modules/salesianos_fest/domain/results/pase_result.py
Aplicacion/backend/modules/salesianos_fest/domain/schemas/pase_schemas.py
Aplicacion/backend/modules/salesianos_fest/domain/selectors/pase_selector.py
Aplicacion/backend/modules/salesianos_fest/domain/services/core/activador_pase.py
Aplicacion/backend/modules/salesianos_fest/domain/services/core/beneficiario_core_service.py
Aplicacion/backend/modules/salesianos_fest/domain/services/core/cortesia_core_service.py
Aplicacion/backend/modules/salesianos_fest/domain/services/core/pase_acceso_service.py
Aplicacion/backend/modules/salesianos_fest/domain/services/core/pase_core_service.py
Aplicacion/backend/modules/salesianos_fest/domain/services/flujos/beneficiario_flujo.py
Aplicacion/backend/modules/salesianos_fest/domain/services/flujos/compra_pase_flujo.py
Aplicacion/backend/modules/salesianos_fest/domain/services/flujos/cortesia_flujo.py
Aplicacion/backend/modules/salesianos_fest/domain/services/flujos/pase_flujo.py
Aplicacion/backend/modules/salesianos_fest/domain/services/orchestrators/beneficiario_orchestrator.py
Aplicacion/backend/modules/salesianos_fest/domain/services/orchestrators/cortesia_orchestrator.py
Aplicacion/backend/modules/salesianos_fest/domain/services/orchestrators/pase_orchestrator.py
Aplicacion/backend/modules/salesianos_fest/infrastructure/services/obtencion_persona.py
Aplicacion/backend/modules/salesianos_fest/migrations/0003_pases_derechos.py
Aplicacion/backend/modules/salesianos_fest/presentation/controllers/pase_controller.py
Aplicacion/backend/modules/salesianos_fest/presentation/presenters/admin_pase_presenter.py
Aplicacion/backend/modules/salesianos_fest/presentation/presenters/beneficiario_presenter.py
Aplicacion/backend/modules/salesianos_fest/presentation/presenters/compra_pase_presenter.py
Aplicacion/backend/modules/salesianos_fest/presentation/presenters/pase_presenter.py
Aplicacion/backend/modules/salesianos_fest/presentation/schemas/pase_schemas.py
Aplicacion/backend/modules/salesianos_fest/tests/fixtures/pase_fixtures.py
Aplicacion/backend/modules/salesianos_fest/tests/integration/test_activador_pase.py
Aplicacion/backend/modules/salesianos_fest/tests/integration/test_beneficiario_pase.py
Aplicacion/backend/modules/salesianos_fest/tests/integration/test_compra_pase.py
Aplicacion/backend/modules/salesianos_fest/tests/integration/test_cortesia_pase.py
Aplicacion/backend/modules/salesianos_fest/tests/e2e/test_pase_controller.py
```

### 3.2 Modificados (13)

`admin.py` · `apps.py` · `di.py` · `domain/constants.py` ·
`domain/exceptions.py` · `domain/models/__init__.py` · `domain/ports/__init__.py` ·
`infrastructure/services/__init__.py` · `models.py` ·
`presentation/schemas/__init__.py` · `tests/conftest.py` ·
`tests/urls_salesianos_fest.py` · `STATE.md`.

**El código de `DOM-01` y `DOM-02` NO se reescribió**: las modificaciones son
ADITIVAS (vocabularios, puertos, bindings, `SCHEMA_VERSION`, admin y
registro de activadores). Ninguna clase, función ni test de `DOM-01`/`DOM-02`
cambió de comportamiento.

---

## 4. Las pruebas (ESCRITAS, NO EJECUTADAS)

**41 funciones de prueba nuevas**, en cinco ficheros:

| Fichero | Tests | Qué cubren |
|---|---|---|
| `tests/integration/test_compra_pase.py` | 10 | compra invitada sin cuenta, comprador autenticado, precio congelado, reintento idempotente, token, límites, pase sin precio, pase retirado |
| `tests/integration/test_beneficiario_pase.py` | 14 | capacidad pagada, duplicado, cortesía vs compra, comprador ≠ asistente, resolución por documento, acceso (401/403/token/titular), revocación idempotente, la unidad NO se devuelve |
| `tests/integration/test_cortesia_pase.py` | 8 | acta con actor y motivo, sin motivo, sin cuenta, **cero hechos financieros**, esquema sin columnas financieras, duplicado, pase inexistente |
| `tests/integration/test_activador_pase.py` | 5 | activación, idempotencia, referencia ajena, compra desconocida, lote pendiente |
| `tests/e2e/test_pase_controller.py` | 14 | catálogo, precio, módulo no habilitado, compra (201/409/422), acceso (401/403), asignación, duplicado, lote pendiente, revocación idempotente, cortesía (201/401/422), listado sin token, administración, envelope |

**Sin dobles**: los servicios son los de producción, resueltos por el
inyector real (`injector` con `UsuariosModule`, `EventosModule`,
`PagosModule`, `CommerceModule`, `SalesianosFestModule`).

**Secuenciales a propósito**: la carrera de la capacidad la decide el índice
condicional del modelo; verificarla con hilos reintroduciría el bloqueo de
SQLite observado en la ronda interrumpida de `DOM-05` (F-59).

---

## 5. Revisión estática de la fuente (33 comprobaciones)

| # | Comprobación | Resultado |
|---|---|---|
| S-01 | Los controllers no contienen reglas de negocio | OK |
| S-02 | Los presenters no consultan la base de datos | OK — son transformadores puros |
| S-03 | Los core services son sync y NO abren `transaction.atomic()` | OK — la abre el flujo |
| S-04 | Los flujos son async y abren la transacción donde corresponde | OK |
| S-05 | Los orquestadores son delgados | OK |
| S-06 | El total del lote y el de la compra usan la MISMA expresión | OK — `calcular_total` de `commerce` |
| S-07 | El payload de compra NO admite importe | OK |
| S-08 | La cantidad NO lleva rango en el schema HTTP | OK — el límite lo declara el dominio (`CANTIDAD_INVALIDA`) |
| S-09 | Los mensajes públicos salen del catálogo, no del controller | OK |
| S-10 | Los códigos de máquina del activador cumplen `^[A-Z0-9_]{1,64}$` | OK |
| S-11 | El `detalle` del activador sólo usa claves de la lista cerrada | OK — `cantidad`, `estado` |
| S-12 | La reserva de capacidad es un `UPDATE` condicional | OK — `WHERE asignados < cantidad` |
| S-13 | El `IntegrityError` de duplicado se captura FUERA de la transacción | OK — así la unidad reservada se libera con el rollback |
| S-14 | El `IntegrityError` que NO es de duplicado no se disfraza | OK — se comprueba el nombre de la restricción |
| S-15 | El token se genera con `secrets`, no con `uuid4` | OK |
| S-16 | El token se compara en tiempo constante | OK — `secrets.compare_digest` |
| S-17 | El token NO aparece en ningún listado | OK — sólo en `CompraPaseCreadaOut` |
| S-18 | El token NO viaja en la query string | OK — cabecera `X-Pase-Token` |
| S-19 | La cortesía NO tiene columna hacia compra/orden/transacción | OK — la garantía es estructural |
| S-20 | La cortesía exige actor (CHECK en base de datos) | OK |
| S-21 | La cortesía exige motivo (dominio) | OK |
| S-22 | La no duplicación cubre los DOS orígenes | OK — una sola restricción parcial |
| S-23 | El origen y su soporte van juntos (CHECK) | OK |
| S-24 | La revocación no libera la unidad | OK — el contador `asignados` no se decrementa |
| S-25 | La revocación es idempotente | OK |
| S-26 | El comprador autenticado IGNORA el documento del payload | OK — `RN-U04` |
| S-27 | El comprador invitado NO toca `usuarios.Usuario` | OK — el puerto sólo registra `Persona` |
| S-28 | `SCHEMA_VERSION` `1.1.0` → `1.2.0` es MINOR (aditivo) | OK |
| S-29 | La capa HTTP compone los tres bloques (Identidad + General + Específico) | OK — `SCHEMA_DRY_INTENTION` |
| S-30 | No hay `z.any()` ni campos genéricos | OK |
| S-31 | El catálogo no expone un pase sin precio vigente | OK |
| S-32 | La edición sin el módulo `pases` habilitado NO expone catálogo | OK — `MODULO_NO_HABILITADO` (409) |
| S-33 | El coordinador de `commerce` NO fue modificado | OK — sólo se consume el puerto |

**Correcciones aplicadas en esta ronda (5):**

| # | Corrección |
|---|---|
| C-01 | `orden_pago_id` se serializaba como `"None"` cuando no había orden de pago → ahora es `""` y el presenter lo traduce a `None` |
| C-02 | `PaseCompraDetalleOut.compra_id` era obligatorio y el dominio puede no tener compra → ahora es opcional |
| C-03 | `PrecioPaseOut.vigente_desde` era `datetime` y el modelo es `DateField` → ahora es `date` (igual que `DOM-01`) |
| C-04 | `PaseAccesoService` construía su adaptador de titularidad a mano → ahora es `@inject` y lo liga el DI |
| C-05 | La migración `0003` y una `0004` autogenerada se contradecían (índices y `Q` con distinto orden) → reconciliadas en una sola migración canónica (F-60) |

---

## 6. Verificación — DIFERIDA POR INSTRUCCIÓN DEL USUARIO

**Comandos ejecutados durante este apply: NINGUNO.** No se ejecutó
`pytest`, `manage.py check`, `makemigrations`, `migrate`, `showmigrations`,
typecheck ni lint. No se invocó el Python global ni el de `.venv`.

La instrucción vigente del proyecto (`workflow/salesianos-sdd-apply-verification-deferred`)
prohíbe ejecutar cualquier comando de verificación durante el apply, exige
`uv run` para toda verificación posterior y obliga a marcar el paquete
`verification_required`.

**En su lugar se hizo una REVISIÓN ESTÁTICA de la fuente** (§5), que es el
sustituto del runtime mientras la ejecución está diferida.

### 6.1 Comandos FUTUROS (NO ejecutados — requieren autorización explícita)

Workdir `Aplicacion/backend`:

```bash
# 1. Migraciones: ¿el modelo y la migración coinciden?
uv run python manage.py makemigrations salesianos_fest --check --dry-run

# 2. Puertas de Django
uv run python manage.py check --settings=config.settings.development
uv run python manage.py makemigrations --check --dry-run --settings=config.settings.development

# 3. Suite focalizada del paquete
uv run python -m pytest modules/salesianos_fest/tests/integration/test_compra_pase.py \
  modules/salesianos_fest/tests/integration/test_beneficiario_pase.py \
  modules/salesianos_fest/tests/integration/test_cortesia_pase.py \
  modules/salesianos_fest/tests/integration/test_activador_pase.py -q

# 4. E2E del controller
uv run python -m pytest modules/salesianos_fest/tests/e2e/test_pase_controller.py -q

# 5. Suite completa del módulo (DOM-01 + DOM-02 + DOM-03)
uv run python -m pytest modules/salesianos_fest/tests -q

# 6. Migración reversible y reproducible
uv run python manage.py migrate --settings=modules.salesianos_fest.tests.settings_overlay
uv run python manage.py migrate salesianos_fest zero --settings=modules.salesianos_fest.tests.settings_overlay
uv run python manage.py migrate --settings=modules.salesianos_fest.tests.settings_overlay

# 7. Regresión de los paquetes vecinos (no editados por este paquete)
uv run python -m pytest modules/eventos/tests modules/usuarios/tests \
  modules/commerce/tests modules/pagos/tests modules/marketplace/tests -q
```

> **La base de datos del ensayo debe vivir FUERA del repositorio** (los
> `*.sqlite3` son un artefacto prohibido). Ningún fichero `.sqlite3` fue
> creado por este paquete.

### 6.2 Lo que la verificación debe comprobar Y NO se ha comprobado

1. Que `0003` reproduce EXACTAMENTE el estado del modelo (`makemigrations
   --check` debe salir 0). La reconciliación de F-60 es un razonamiento
   estático: **no está verificada en runtime**.
2. Que las 41 pruebas nuevas pasan.
3. Que las 102 pruebas previas de `DOM-01`/`DOM-02` siguen verdes.
4. Que la restricción parcial única y el `UPDATE` condicional se comportan
   como se espera en SQLite.
5. Que el `drift` de `SCHEMA_VERSION` (`1.2.0` declarado, `1.1.0` en el
   registro global) se detecta: es un fallo esperado hasta que A0 actualice
   `core/contract_versions.py` (A0-02).

---

## 7. Decisiones abiertas y BLOQUEOS explícitos (nunca adivinados)

| ID | Bloqueo | Owner | Efecto |
|---|---|---|---|
| `PD-01` | **BOX**: la titularidad y el uso del beneficio grupal siguen ABIERTOS | A4 + producto | El paquete **NO modela BOX**: no hay ninguna marca de BOX en `Pase` ni en `PaqueteBeneficio`. La Open Decision es la que queda declarada: `OD-DOM03-02` |
| `PD-02` / `GOV-01-OPEN-08` | **Revocación**: ¿libera la asignación? ¿permite reemplazar titular? | A4 + producto | El paquete congela la **INTERFAZ** de la revocación (permanente, auditada, idempotente, `ya_revocado`) y **NO inventa la política**: la revocación **NO** devuelve la unidad ni permite reasignarla. Es la lectura más conservadora de `FR-05` §2.3. `OD-DOM03-01` |
| `PD-03` | Ticket por unidad vs cantidad y consumo parcial | A4 + A8 + producto | El derecho lleva `cantidad` y `cantidad_consumida` (nace en cero) para que la forma congelada de `FR-05` §3.1 no cambie. `OD-DOM03-03` |
| `PD-04` | Alcance de validez de una entrada | A8 + producto | **No bloquea** este paquete: el módulo concede el derecho y no implementa el canje |
| `GOV-01-OPEN-05` | Política exacta de expiración, rotación y verificación del enlace | A1 + A0 + producto | El MECANISMO está congelado (vencimiento, ámbito por compra, revocabilidad) y se declara un valor conservador (`VIGENCIA_TOKEN_PASE_DIAS = 30`). La cabecera `X-Pase-Token` es una decisión PROVISIONAL: `OD-DOM03-04` |
| `GOV-01-OPEN-04` | Grupo de los operadores de validación | A0 + producto | **No bloquea**: este paquete no implementa el canje |
| — | **Qué tipos de pase admiten cortesía** (`FL-07` paso 1 dice "entrada permitida") | A4 + producto | El paquete **NO inventa** la lista: cualquier pase existente en la edición puede recibir cortesía, y la garantía es el motivo obligatorio + la auditoría. `OD-DOM03-05` |
| — | **Revocación de una CORTESÍA** (`FL-07` paso 4) | A4 + A0 | El ledger **no tiene ruta** para revocarla (`RT-RT-03` es de beneficiarios de una COMPRA). El servicio de dominio expone la operación; la ruta se PIDE a A0: `A0-09` |

**Lo que este paquete NO hizo por no adivinar:**

- No inventó la lista de pases que admiten cortesía.
- No inventó la política de reasignación tras una revocación.
- No modeló BOX.
- No inventó el parámetro exacto de expiración del enlace.
- No creó una ruta que el ledger no declara.

---

## 8. Peticiones a A0 (registradas, NO aplicadas)

| ID | Petición | ¿Bloqueante? |
|---|---|---|
| A0-01 | Registrar `PaseController` y `AdminPaseController` en `config/api.py` (`registrar_controladores(...)`) | **SÍ** — sin esto las rutas no existen |
| A0-02 | `SCHEMA_VERSIONS["salesianos_fest"] = "1.2.0"` en `core/contract_versions.py` | **SÍ** — el test de drift falla mientras tanto |
| A0-03 | Catalogar 9 códigos públicos nuevos: `PASE_NO_DISPONIBLE` (409), `CANTIDAD_INVALIDA` (422), `PASE_NO_ENCONTRADO` (404), `COMPRA_PASE_NO_ENCONTRADA` (404), `PASE_BENEFICIARIO_NO_ENCONTRADO` (404), `PASE_NO_TRANSFERIBLE` (409), `PASE_DUPLICADO` (409), `SIN_PASES_DISPONIBLES` (409), `COMPRA_PASE_NO_PAGADA` (409) | **SÍ** — sin prosa pública el mensaje cae al genérico |
| A0-04 | Catalogar 4 códigos de autenticación/autorización: `TOKEN_PASE_INVALIDO` (401), `ACTOR_REQUERIDO` (401), `COMPRA_PASE_NO_AUTORIZADA` (403), `CORTESIA_MOTIVO_INVALIDO` (422), `CORTESIA_NO_ENCONTRADA` (404) | **SÍ** |
| A0-05 | Ratificar `RT-PS-01`…`RT-PS-08` en el ledger + `SH-05` (son provisionales) | NO |
| A0-06 | Ratificar la cabecera `X-Pase-Token` como canal del token de gestión (`P-01` sigue provisional) | NO — pero A7 necesita el canal para el espejo |
| A0-07 | Inventario de rutas: **+10** (o **+8** si A0 decide no registrar las provisionales) | NO |
| A0-08 | `*.sqlite3` en `.gitignore` (arrastrado de FND-01…DOM-05) | NO |
| A0-09 | Añadir al ledger una ruta de revocación de CORTESÍA (`FL-07` paso 4) | NO |
| A0-10 | Sincronizar la matriz física de tareas (`T-030`, `T-031`, `T-032`) | NO |
| A0-11 | Unificar las DOS definiciones de administrador que hay en el proyecto (`core.capacidades.es_admin` = `is_staff OR is_superuser` vs `usuarios.GrupoFuncionalService.es_administrador` = grupo `Administrador`) | NO — este paquete usa la del proyecto (`core.capacidades`), pero la divergencia es real |

---

## 9. Desviaciones

| ID | Desviación | Motivo |
|---|---|---|
| `D-DOM03-01` | El dominio de pases vive en la app `salesianos_fest`, no en una app `pases` nueva | El plan lo permite (`funcional/01` §1) y evita duplicar los tres puertos que el dominio ya tenía |
| `D-DOM03-02` | La revocación NO devuelve la unidad ni permite reasignarla | `PD-02` sigue ABIERTA: se congela la interfaz, no la política |
| `D-DOM03-03` | El motivo de la revocación viaja como parámetro de consulta | El ledger congelado declara `RT-RT-03` SIN schema de entrada |
| `D-DOM03-04` | El token de gestión viaja en la cabecera `X-Pase-Token` | `P-01` deja el canal abierto; la query string filtraría la credencial en los logs |
| `D-DOM03-05` | La cortesía no exige que el pase esté `VIGENTE` | Una cortesía puede otorgar un pase retirado del catálogo; lo que no puede es un pase que no existe |
| `D-DOM03-06` | Se añadió el puerto `IObtensionPersonaService` al módulo | `FL-06` paso 2 exige comprar SIN cuenta: hace falta obtener (o registrar) una identidad civil sin crear un `Usuario` |
| `D-DOM03-07` | `PaseBeneficiario.cantidad_consumida` existe desde el principio, en cero | `FR-05` §3.1 exige la cantidad en la forma congelada; `XCT-01` la escribirá |
| `D-DOM03-08` | La migración `0004` autogenerada se eliminó y su contenido se reconcilió en `0003` | F-60: `0004` duplicaba las restricciones de `0003` y renombraba índices que `0003` crea con otro nombre. La cadena queda `0001 → 0002 → 0003` |

---

## 10. Hechos nuevos (para `sdd/salesianos-fest-rebuild/facts`)

| ID | Hecho |
|---|---|
| **F-60** | **`Q.__init__` ORDENA los `kwargs` y NO ordena los argumentos posicionales.** Un `Q` escrito en una migración con `models.Q(("origen", "COMPRA"), ("compra_pase__isnull", False), ...)` tiene los hijos en otro orden que el `Q` del modelo (`models.Q(origen=..., compra_pase__isnull=..., ...)`), y el autodetector lo lee como una restricción **ALTERADA**: emite `RemoveConstraint` + `AddConstraint` y el drift no se estabiliza. **La forma correcta en una migración es escribir el `Q` con ARGUMENTOS DE PALABRA.** |
| **F-61** | **Un token de gestión es una CREDENCIAL, y una credencial no es un identificador.** Generado con `secrets`, comparado en tiempo constante, viajando en una CABECERA (nunca en la query string, que queda en los logs) y ausente de TODOS los listados. |
| **F-62** | **La no duplicación de un derecho puede ser UNA sola regla para dos orígenes.** Si la compra y la cortesía convergieran en la MISMA tabla de derechos, la restricción parcial única los cubre a los dos y una cortesía no puede duplicar una compra por construcción. |
| **F-63** | **La ausencia de una columna es una garantía más fuerte que una convención.** `CortesiaPase` no tiene ninguna columna hacia `commerce.Compra`, `pagos.OrdenPago` ni `pagos.TransaccionPago`: el test puede comprobar el ESQUEMA y la de "no simular un cobro de S/ 0" deja de depender de la disciplina del código. |
| **F-64** | **Un `UPDATE` condicional, el mismo patrón del pool de `DOM-02`, resuelve la concurrencia de la asignación con UNA sola sentencia y sin `select_for_update`** (que no funciona en SQLite). La condición viaja DENTRO de la sentencia y la base de datos decide quién entra. |

---

## 11. Slices de revisión (presupuesto ≈ 400 líneas)

El paquete **supera** el presupuesto de revisión. Se declara la misma
frontera que usaron `DOM-01`…`DOM-05`: un paquete, un rollback, sin mixing de
dominios ajenos.

| Slice | Contenido | Líneas aprox. |
|---|---|---|
| WU-A · dominio | modelos, constantes, excepciones, puerto, referencia, selector, DTOs | ≈ 2 100 |
| WU-B · servicios | core services, flujo de activator, flujos, orquestadores | ≈ 1 500 |
| WU-C · superficie | schemas HTTP, presenters, controllers, `di.py`, `apps.py`, admin | ≈ 1 300 |
| WU-D · persistencia | migración `0003` | ≈ 900 |
| WU-E · pruebas | fixtures + 4 de integración + 1 e2e | ≈ 1 500 |

**Frontera de rollback: TODO el slice de `DOM-03`.** Ningún slice mezcla
dominios ajenos.

---

## 12. Rollback

1. `uv run python manage.py migrate salesianos_fest 0002_pool_capacidad --settings=…`
   (si A0 lo autoriza; la migración es reversible: `CreateModel` +
   `AddConstraint`/`AddIndex` se deshacen).
2. Borrar los ficheros de `DOM-03` (los 26 creados + las 13 modificaciones
   revertidas) y la migración `0003`.
3. Restaurar `STATE.md` y los topics de Engram.
4. **El historial comercial y de pagos se preserva**: la reversión con datos
   vivos es un asiento compensatorio, no un borrado. `ActivacionPase` y
   `CortesiaPase` son ACTAS: no se borran.

**Punto de rollback:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (HEAD del
usuario; este paquete **no** creó ningún commit). `git stash` **nunca**
invocado.

---

## 13. Concurrencia y trabajo preservado

| Ruta | Estado |
|---|---|
| `Aplicacion/backend/modules/marketplace/**` (`DOM-05`, A5) | **NO tocada.** Ni revertida ni fusionada. Sus filas del tablero NO se editaron |
| `Aplicacion/frontend/**` (`FND-06` / `UI-01A` / trabajo concurrente) | **NO tocada.** Sus filas NO se editaron |
| `Aplicacion/backend/modules/commerce/**` · `pagos/**` | **NO editados**: el coordinador de activación es un INTERFAZ, no un interior. El paquete lo CONSUME por el puerto |
| `Aplicacion/backend/modules/eventos/**` · `usuarios/**` | **NO editados**: se cruzan por PUERTO |
| `Aplicacion/backend/modules/salesianos_fest/**` (`DOM-01` / `DOM-02`) | **CONSERVADO**: sólo adiciones. Ninguna clase ni test de `DOM-01`/`DOM-02` cambió de comportamiento |
| `Aplicacion/backend/core/**` · `config/**` | **NO editados** (raíz compartida de A0): se piden los cambios en §8 |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/**` | Sólo se AÑADE este fichero |

**Una observación de concurrencia registrada:** durante el apply, un proceso
en segundo plano ejecutó `makemigrations` y generó una migración `0004`
autogenerada a partir de los modelos de este paquete. Se reconcilió con
`0003` (F-60, `D-DOM03-08`) en vez de dejarla: dos migraciones que se
contradicen habrían roto el `migrate`. **La reconciliación es un
razonamiento estático y NO está verificada en runtime** (§6.2, punto 1).

---

## 14. Consumidores desbloqueados

| Consumidor | Qué recibe | Estado |
|---|---|---|
| **API-03** | las ocho rutas de `pases` + `RT-CM-02` + `RT-RT-03`, con sus wrappers y presenters nombrados | **PROVISIONAL** — pendiente de la verificación diferida |
| **XCT-01** | `PaseBeneficiario` como el DERECHO que `validaciones` consulta: `tipo_derecho`, `titular`, `estado`, `cantidad_total`, `cantidad_disponible`, `cantidad_consumida` | **PROVISIONAL** |
| **XCT-03** | la separación pago (`CompraPase.estado`) / entrega (asignación) / consumo (`cantidad_consumida`) | **PROVISIONAL** |
| **UI-02 / UI-03 / UI-04** | el catálogo, el enlace de gestión por token y el panel de cortesías | **PROVISIONAL** |
| **API-05** | el catálogo de pases de la edición | **PROVISIONAL** |
| **DOM-06 / DOM-07** | sin impacto: el paquete no toca stock ni competencias | — |

---

## 15. Siguiente paquete

**API-03** (espejo comercial) y **XCT-01** (tickets y validación) — ambos
**DESPUÉS** de la verificación diferida de este paquete con `uv run`, que
hoy exige autorización explícita del usuario.
