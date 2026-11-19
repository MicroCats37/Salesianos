# FND-05 — Coordinate Exactly-Once Rights Activation

**Freeze:** `FREEZE-CM-1.0.0` (FR-04 §2.1 I-2, §2.3, §4) · **Trazabilidad:** `RN-C06`, `RN-C08` · **Plan:** `T-015`
**Paquete:** `FND-05` (`wave-01-foundations`) · **Propietario:** A0 · **Fecha:** 2026-11-19
**Artefacto de apply (canónico):** `sdd/salesianos-fest-rebuild/fnd-05-apply-progress` (Engram)
**Contexto heredado:** `FND-04` (#11252) · reconciliación A0 de FND-01/02/03/04 (#11259)

---

## 1. Resumen ejecutivo

Se implementó el **coordinador de la activación de derechos**: el servicio de aplicación que
convierte un pago verificado en **una** activación de dominio, **idempotente**, **recuperable** y
**visible** cuando falla.

- **El pago y el derecho siguen siendo hechos separados** (`RN-C08`). `pagos` confirma el pago y
  pide la activación; **no habilita ningún derecho** por su cuenta.
- **Una activación efectiva por `(compra_id, origen)`** (`FR-04` I-2), con **cuatro** capas de
  guarda: restricción única en base de datos, `estado = ACTIVADA` terminal, reserva condicional
  del intento (compare-and-swap) y **clave de activación estable** que el dominio usa para
  deduplicar.
- **El coordinador conoce interfaces, no reglas de dominio**: no sabe qué es un cupo, un pase ni
  una salida de stock. Despacha por origen a un puerto tipado, `IActivadorDominioCompra`.
- **El fallo no revierte el cobro**: la compra queda `PAGADA`, la orden `CONFIRMADA`, y la
  activación queda `FALLIDA` con una incidencia de **datos seguros** y una acción segura
  (`REINTENTAR_ACTIVACION`).
- **17 tests de comportamiento nuevos** (12 en `commerce`, 5 en `pagos`), todos verdes. Suite
  completa del objetivo: **294 passed** (277 antes de este paquete).

---

## 2. La secuencia congelada §2.3, implementada

```
CompraCreada(origen, compra_id, orden_id)     # commerce · FND-04
PagoVerificado(orden_id, evidencia)            # pagos · FND-04 (firma verificada)
CompraMarcadaPagada(compra_id)                 # pagos · FND-04 (idempotente)
ActivarDominio(compra_id, origen)              # commerce · FND-05 (este paquete)
  origen=INSCRIPCION -> habilitar cupos         # lo implementa DOM-02
  origen=PASE        -> habilitar lote de entradas   # lo implementa DOM-03
  origen=MARKETPLACE -> confirmar pedido y stock    # lo implementa DOM-06
NotificarComprador(compra_id)                   # opcional y reintentable (no implementado)
```

El paso `ActivarDominio` se ejecuta **al final del flujo de confirmación de `pagos`**:
`PagoConfirmacionFlujo._confirmar` → `_marcar_compra_pagada` → `_activar_compra`. Es el orden
congelado, no un atajo.

`pagos` habla con el coordinador por un **puerto declarado por el consumidor**
(`IActivacionCompraService`, en `modules/pagos/domain/ports/`), implementado en `commerce`
(`modules/commerce/infrastructure/services/activacion_compra.py`). El módulo de pago **nunca
importa** `commerce`: la dirección de dependencias queda `commerce → pagos` y el grafo de módulos
sigue acíclico.

---

## 3. Las cuatro guardas de "exactamente una vez"

| # | Guarda | Dónde | Qué evita |
|---|---|---|---|
| 1 | Restricción única `(compra_id, origen)` | `commerce_activacion_compra` | Dos registros de activación para la misma compra y origen |
| 2 | `clave` UNIQUE y **estable** | `commerce_activacion_compra.clave` | Dos activaciones con claves distintas para la misma compra |
| 3 | `estado = ACTIVADA` es **terminal** | `CoordinadorActivacionCompra.activar_por_compra` | Invocar al dominio una segunda vez tras el éxito |
| 4 | **Reserva condicional** del intento (compare-and-swap) | `ActivacionCompraCoreService.reclamar` | Que dos reintentos concurrentes despachen a la vez |

Las guardas 1 y 2 son de base de datos: son la única defensa real bajo concurrencia (aprendizaje
#6 de FND-04). La guarda 4 es **una sola sentencia `UPDATE` condicional**, que es atómica en
SQLite y en PostgreSQL:

```sql
UPDATE commerce_activacion_compra
   SET en_curso = 1, intentos = intentos + 1, ultimo_intento_en = <ahora>
 WHERE id = <id>
   AND estado IN ('PENDIENTE', 'FALLIDA')
   AND (en_curso = 0 OR ultimo_intento_en <= <ahora - 300s>)
```

El `lease` de 300 s (`LEGA_ACTIVACION_SEGUNDOS`) es la red de seguridad del caso "el proceso
murió con el intento reservado": sin él, un fallo de proceso dejaría la activación bloqueada
para siempre.

**La clave de activación** es `activacion:{origen}:{compra_id}`. Es **estable** entre reintentos:
es lo que permite que el dominio deduplique por ella y que el reintento **converja** en vez de
duplicar el derecho. El coordinador entrega la clave al dominio; **no decide** qué hacer con ella.

---

## 4. Lo que se entregó

### 4.1 El modelo `ActivacionCompra` (dueño: `commerce`)

`Aplicacion/backend/modules/commerce/domain/models/activacion_compra.py` ·
migración `commerce.0002_activacioncompra`.

| Atributo | Regla |
|---|---|
| `compra` | FK → `commerce.Compra` (`CASCADE`, `related_name="activaciones"`) |
| `origen` | `INSCRIPCION` \| `PASE` \| `MARKETPLACE` — el vocabulario cerrado de `commerce` |
| `clave` | Clave de idempotencia **estable** (`UNIQUE`, ≤ 128) |
| `estado` | `PENDIENTE` \| `ACTIVADA` \| `FALLIDA` — `ACTIVADA` es terminal |
| `intentos` | Nº de intentos (reintentables) |
| `en_curso` | Hay un intento **reservado** |
| `ultimo_intento_en` | Instante de la reserva (recuperación por lease) |
| `activada_en` | Instante en que el derecho quedó habilitado |
| `incidencia` | Datos **seguros** del último fallo: `codigo`, `origen`, `intento`, `fecha` |
| `detalle` | Resumen informativo del dominio, con **lista cerrada** de claves |

Restricciones reales verificadas en el esquema SQLite:

```
UNIQUE ("compra_id", "origen")   -- activacion_unica_por_compra_y_origen
"clave" varchar(128) NOT NULL UNIQUE
```

### 4.2 El coordinador

`Aplicacion/backend/modules/commerce/domain/services/core/coordinador_activacion_compra.py`

Es un servicio **sync** que **no abre `transaction.atomic()`**: cada escritura es una sola
sentencia (un `INSERT`, un `UPDATE` condicional) y por eso ya es atómica
(`contract/django-app-architecture-contract.md` §4.3).

| Método | Qué hace |
|---|---|
| `activar_por_orden(orden_pago_id)` | Entrada que usa `pagos`. Resuelve la compra por su orden |
| `activar_por_compra(compra_id)` | Dispatch por origen, con las cuatro guardas |

### 4.3 El puerto de dominio (el dispatch por origen)

`Aplicacion/backend/modules/commerce/domain/ports/__init__.py` → `IActivadorDominioCompra`.

```python
class IActivadorDominioCompra(ABC):
    @abstractmethod
    def activar(self, contexto: ContextoActivacionCompra) -> ResultadoActivacionDominio: ...
```

`ContextoActivacionCompra` lleva **hechos congelados**, no reglas: `compra_id`, `origen`,
`clave`, `persona_id`, `referencia`, `total`, `moneda`, `lineas_snapshot`. El coordinador no
resuelve catálogos, ni elegibilidad, ni stock.

`ResultadoActivacionDominio` lleva `exito`, un `codigo` de máquina (`[A-Z0-9_]{1,64}`) y un
`detalle` con **claves de lista cerrada** (`cantidad`, `codigo`, `estado`). **No hay texto libre**:
el texto de una excepción nunca se persiste ni se devuelve.

### 4.4 El registro de activadores

`Aplicacion/backend/modules/commerce/domain/services/core/registro_activadores_compra.py`

Cada dominio de origen registra SU activador **sin tocar el código de `commerce`** (DOM-02,
DOM-03, DOM-06). Mientras un dominio no lo registre, la activación de ese origen queda
`PENDIENTE` y **reintentable**, y el cobro confirmado se conserva.

```python
obtener_registro().registrar(OrigenCompra.INSCRIPCION, MiActivadorDeInscripcion())
```

### 4.5 Los dobles de prueba reutilizables

`Aplicacion/backend/modules/commerce/tests/fixtures/activacion_fakes.py` → `ActivadorDominioFake`.

Modela el **contrato** del puerto, no las reglas de ningún dominio: aplica el derecho **una sola
vez por clave**, puede fallar, puede rechazar y devuelve un código y un detalle con claves
permitidas. Es importable por los tests de los dominios:

```python
from modules.commerce.tests.fixtures.activacion_fakes import (
    ActivadorDominioFake,
    registro_activadores,
)
```

---

## 5. Evidencia de fallo, reintento y recuperación

### 5.1 El fallo del dominio NO revierte el pago

`test_el_fallo_de_la_activacion_no_revierte_el_pago_confirmado` (`pagos`):

| Hecho | Valor tras el fallo |
|---|---|
| `OrdenPago.estado` | `CONFIRMADA` (con `pagada_en`) |
| `Compra.estado` | `PAGADA` |
| `TransaccionPago.estado` | `EXITO` |
| `ActivacionCompra.estado` | `FALLIDA` |
| `ActivacionCompra.incidencia` | `{"codigo": "ACTIVACION_FALLIDA", "origen": …, "intento": 1, "fecha": …}` |
| `ActivacionCompra.es_reintentable` | `True` |

**Nunca** hay una reversión silenciosa del cobro (`RN-C08`, FR-04 §4).

### 5.2 La acción segura que sigue

El resultado del coordinador expone `proxima_accion`, que es una **acción pública y segura**:

| Situación | `codigo` | `proxima_accion` |
|---|---|---|
| Derecho habilitado | `ACTIVACION_COMPLETADA` | `NINGUNA` |
| Ya estaba habilitado (repetición) | `ACTIVACION_YA_COMPLETADA` | `NINGUNA` |
| Hay un intento reservado | `ACTIVACION_EN_CURSO` | `ESPERAR_ACTIVACION` |
| El dominio no tiene activador todavía | `ACTIVADOR_NO_DISPONIBLE` | `REINTENTAR_ACTIVACION` |
| El dominio falló | `ACTIVACION_FALLIDA` | `REINTENTAR_ACTIVACION` |
| El dominio rechazó | `ACTIVACION_RECHAZADA` | `REINTENTAR_ACTIVACION` |
| No hay compra para la orden | `SIN_COMPRA` | `NINGUNA` |
| La compra no está pagada | `COMPRA_NO_PAGADA` | `NINGUNA` |

### 5.3 El reintento converge

`test_el_reintento_tras_un_fallo_habilita_el_derecho`: tras un fallo, el reintento deja la
activación `ACTIVADA` con `intentos = 2` y **una sola** aplicación efectiva del derecho (el doble
deduplica por la clave estable).

### 5.4 La concurrencia

`test_un_reintento_concurrente_no_habilita_el_derecho_dos_veces`: un reintento que llega
**mientras** el primer intento tiene la activación reservada recibe
`ACTIVACION_EN_CURSO` / `ESPERAR_ACTIVACION` y **no despacha**. El dominio se invoca **una vez** y
el derecho se habilita **una vez**.

### 5.5 La confirmación tardía

`test_la_confirmacion_tardia_no_habilita_el_derecho_dos_veces` (`pagos`): una notificación que
llega tarde, o un webhook duplicado, converge en **una sola** activación efectiva. El cobro se
confirma una vez (`pagada_en` no cambia) y el derecho se habilita una vez.

---

## 6. Seguridad de los envelopes y de los logs

- La **incidencia** persistida tiene **exactamente** cuatro claves: `codigo`, `origen`, `intento`,
  `fecha`. Nunca el texto de una excepción, ni un payload de proveedor, ni un secreto, ni un
  identificador interno (`test_la_incidencia_no_expone_el_texto_del_fallo_ni_el_detalle_crudo`).
- El **detalle** del dominio se reduce a la lista cerrada `("cantidad", "codigo", "estado")` con
  valores escalares; cualquier clave o valor que no encaje **se descarta**.
- El **código** del dominio se valida contra `^[A-Z0-9_]{1,64}$`; si no encaja, se sustituye por
  `DOMINIO_NO_CATALOGADO`.
- El coordinador **nunca** recibe un payload de proveedor: recibe el `orden_pago_id` y el snapshot
  congelado de la compra. La firma del proveedor y el payload firmado viven en `pagos` y no
  cruzan esta frontera.
- El puerto expone **banderas y códigos**, nunca identificadores ni mensajes de excepción.

---

## 7. Archivos

### 7.1 Creados — `Aplicacion/backend/modules/commerce/**` (8)

| Archivo | Qué es |
|---|---|
| `domain/models/activacion_compra.py` | El modelo `ActivacionCompra` |
| `domain/services/core/activacion_compra_core_service.py` | Persistencia y reserva condicional del intento |
| `domain/services/core/coordinador_activacion_compra.py` | El coordinador |
| `domain/services/core/registro_activadores_compra.py` | El registro por origen |
| `infrastructure/services/activacion_compra.py` | El adaptador del puerto de `pagos` |
| `migrations/0002_activacioncompra.py` | La migración |
| `tests/fixtures/activacion_fakes.py` | Los dobles reutilizables |
| `tests/integration/test_activacion_compra.py` | Los 12 tests de comportamiento |

### 7.2 Modificados — `Aplicacion/backend/modules/commerce/**` (9)

`domain/constants.py` (vocabulario `EstadoActivacionCompra` + `LEGA_ACTIVACION_SEGUNDOS` +
`CLAVES_DETALLE_PERMITIDAS`) · `domain/models/__init__.py` · `models.py` · `domain/ports/__init__.py`
(el puerto de dominio) · `domain/schemas/compra_schemas.py` (`ContextoActivacionCompra`,
`ResultadoActivacionDominio`, `ResultadoActivacionCompra`) · `infrastructure/services/__init__.py` ·
`di.py` (bindings) · `admin.py` (superficie de operación de sólo lectura) ·
`tests/conftest.py` (registro de fixtures).

### 7.3 Modificados — `Aplicacion/backend/modules/pagos/**` (4)

`domain/ports/__init__.py` (el puerto `IActivacionCompraService`) ·
`domain/schemas/pago_schemas.py` (`ResultadoActivacionCompra`) ·
`domain/services/flujos/pago_confirmacion_flujo.py` (el paso `ActivarDominio`) ·
`di.py` (binding del puerto).

### 7.4 Creados — `Aplicacion/backend/modules/pagos/tests/**` (1)

`integration/test_pago_activacion.py` — los 5 tests de comportamiento del lado del pago.

### 7.5 Fuera de las raíces de los módulos

`Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/FND-05-rights-activation.md` (este
archivo) · `Aplicacion/task/salesianos-fest-rebuild/STATE.md` (la fila y la transición de FND-05).

**Ningún archivo compartido de A0 fue editado**: ni `config/settings/base.py`, ni `config/api.py`,
ni `core/exceptions.py`. **Ningún archivo de `frontend/**` fue tocado.**

---

## 8. Migraciones

| Migración | Qué hace | Reversible |
|---|---|---|
| `commerce.0002_activacioncompra` | Crea `commerce_activacion_compra` con la restricción única `(compra_id, origen)`, la `clave` UNIQUE y los índices de `estado` y `origen` | Sí |

- Depende de `commerce.0001_initial`; **no** depende de `pagos` (la FK es a `commerce.Compra`).
- `makemigrations --check --dry-run` → `No changes detected`: el modelo y la migración coinciden.
- **No se editó ninguna migración de FND-04.** `pagos.0001_initial` y `commerce.0001_initial`
  siguen intactas.

---

## 9. Verificación

### 9.1 Entorno exacto

- Workdir: `Aplicacion/backend`
- Intérprete: `.\.venv\Scripts\python.exe` — Python 3.10.0, Django 5.2.11, pytest-django 4.9.0,
  injector 0.24.0
- `pytest.ini`: `DJANGO_SETTINGS_MODULE = config.settings.test` (SQLite **en memoria**),
  `addopts = --tb=short --nomigrations`
- Entorno de la **rehearsal de migraciones**: `USE_SQLITE=true` +
  `--settings=config.settings.development` (SQLite **de archivo**, `Aplicacion/backend/db.sqlite3`)
- `DJANGO_SETTINGS_MODULE` **no** se fijó: el registro permanente de A0 ya está hecho, así que la
  suite corre con los settings del proyecto (no hace falta el overlay de FND-04).

### 9.2 Comandos y códigos de salida

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V1 | `python -m pytest modules/commerce/tests modules/pagos/tests -q -k "activ or idempot"` | **0** | **29 passed**, 67 deselected |
| V2 | `python -m pytest modules/commerce/tests modules/pagos/tests -q` | **0** | **96 passed** (27 commerce + 69 pagos) |
| V3 | `python -m pytest -q` (raíz completa del objetivo) | **0** | **294 passed** (277 antes de este paquete) |
| V4 | `python -m pytest core/tests -q` | **0** | **100 passed** — baseline de FND-01 intacto |
| V5 | `python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| V6 | `python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced)` |
| V7 | `python manage.py check` (settings por defecto = producción) | **1** | `DB_NAME` — **baseline conocido, idéntico a FND-01/02/03/04** |
| V8 | `python manage.py makemigrations --check --dry-run` (por defecto) | **1** | mismo `DB_NAME` — baseline conocido |
| V9 | `manage.py migrate` (base vacía, SQLite de archivo) | **0** | `Applying commerce.0001_initial... OK` → `Applying commerce.0002_activacioncompra... OK` |
| V10 | `manage.py showmigrations commerce` | **0** | `[X] 0001_initial` · `[X] 0002_activacioncompra` |
| V11 | `manage.py migrate commerce zero` | **0** | `Unapplying commerce.0002_activacioncompra... OK` → `Unapplying commerce.0001_initial... OK` |
| V12 | `manage.py migrate` (replay) | **0** | `Applying commerce.0001_initial... OK` → `Applying commerce.0002_activacioncompra... OK` |
| V13 | inspección del esquema SQLite de `commerce_activacion_compra` | **0** | `UNIQUE ("compra_id","origen")` + `clave UNIQUE` presentes |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **vacío** |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **vacío** — raíces congeladas intactas |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — **sin commit creado** |
| R4 | `git stash` | — | **nunca invocado** |

**Byproduct eliminado:** la rehearsal de migraciones creó `Aplicacion/backend/db.sqlite3` (471 040 B);
se **borró** al terminar (las bases de datos son un artefacto prohibido).

### 9.3 Cobertura de comportamiento (behavior-first)

`modules/commerce/tests/integration/test_activacion_compra.py` (12):

| Test | Garantía |
|---|---|
| `test_la_activacion_habilita_el_derecho_una_sola_vez` | I-2 |
| `test_el_duplicado_no_vuelve_a_invocar_al_dominio` | I-2 — la repetición converge |
| `test_la_confirmacion_tardia_converge_en_una_sola_activacion` | RN-C06 — retraso |
| `test_el_fallo_del_dominio_conserva_el_pago_y_registra_la_incidencia` | RN-C08 — fallo parcial |
| `test_el_reintento_tras_un_fallo_habilita_el_derecho` | RN-C08 — reintento |
| `test_un_reintento_concurrente_no_habilita_el_derecho_dos_veces` | I-2 — reintento concurrente |
| `test_la_clave_de_activacion_es_estable_entre_reintentos` | I-2 — clave |
| `test_el_coordinador_despacha_al_origen_correspondiente` | `funcional/01` §5 — dispatch por origen |
| `test_sin_activador_de_dominio_la_activacion_queda_pendiente` | RN-C08 — recuperable |
| `test_una_compra_no_pagada_no_se_activa` | RN-C08 — separación de hechos |
| `test_la_incidencia_no_expone_el_texto_del_fallo_ni_el_detalle_crudo` | FR-04 §4 — seguridad |
| `test_el_coordinador_no_depende_de_capas_de_presentacion` | arquitectura — sin presentación |

`modules/pagos/tests/integration/test_pago_activacion.py` (5):

| Test | Garantía |
|---|---|
| `test_la_confirmacion_del_pago_pide_la_activacion_del_derecho` | §2.3 — orden de la secuencia |
| `test_un_webhook_duplicado_no_habilita_el_derecho_dos_veces` | I-2 — duplicado |
| `test_la_confirmacion_tardia_no_habilita_el_derecho_dos_veces` | RN-C06 — retraso |
| `test_el_fallo_de_la_activacion_no_revierte_el_pago_confirmado` | RN-C08 — fallo parcial |
| `test_un_pago_no_confirmado_no_pide_la_activacion` | RN-C05 — sin evidencia confiable |

### 9.4 Clasificación de regresiones

**0 regresiones.** V3 mantiene verdes las 277 pruebas que había antes de este paquete (277 →
294 = +17). V4 mantiene el baseline de FND-01. Las 79 pruebas de FND-04 (15 commerce + 64 pagos)
siguen verdes **sin modification**: el único cambio en un test de FND-04 es una aclaración del
docstring de `test_la_compra_se_marca_pagada_sin_activar_derechos` (sus aserciones NO se tocaron),
que ahora explica que un REGISTRO de activación no es un DERECHO.

**Fallos de baseline conocidos:** sin cambios. V7 y V8 siguen siendo el fallo **ambiental** de
`DB_NAME` con los settings de producción, **idéntico** a FND-01/FND-02/FND-03/FND-04.

---

## 10. Desviaciones

| ID | Desviación | Por qué |
|---|---|---|
| `D-FND-05-01` | El **veredicto operativo** (`estado_operativo`) **no** refleja el estado de la activación. Tras un fallo de activación sigue siendo `PAGADA`, no `PAGADA_SIN_LIQUIDAR`. | Publicarlo exigiría un puerto nuevo en `pagos` (`IEstadoActivacionCompraService`) que **cambiaría la garantía de FND-04** (`PAGADA` tras una confirmación correcta), y ese texto congelado es de FND-04. XCT-03 es el dueño de "separar los tres estados y la incidencia de activación" (`FR-04` §6). La incidencia y la acción segura **sí** están expuestas: en `ActivacionCompra.incidencia` y en el `proxima_accion` del resultado. |
| `D-FND-05-02` | La clave de activación es **derivada** (`activacion:{origen}:{compra_id}`), no un UUID v4 del cliente. | `FR-04` §2.2 habla de claves de cliente para el borde HTTP. La activación es una operación interna cuya identidad **es** `(compra, origen)`: una clave derivada es la única que puede ser estable entre reintentos y la que permite converger. |
| `D-FND-05-03` | El coordinador **es sync** y vive en `domain/services/core/`, con laatomicidad de `transaction.atomic()` repartida en sentencias individuales. | El puerto de `pagos` es sync (como `IEstadoCompraOrdenPagoService`), y llamar a un flujo async desde un puerto sync dentro de `sync_to_async` es la trampa de `async`/`sync` que FND-04 ya documentó. Cada escritura es una sola sentencia y por eso ya es atómica. |
| `D-FND-05-04` | El registro de activadores es un objeto **único del proceso**, no un binding de DI. | Los dominios de origen (DOM-02/03/06) registran SU activador **sin tocar el código de `commerce`**. Un binding de DI obligaría a `commerce` a conocer clases de dominios que todavía no existen. |
| `D-FND-05-05` | Se añadió una fila de `ActivacionCompra` por cada pago confirmado, aunque ningún dominio haya registrado su activador. | Es el **registro de la intención de activación** con su clave estable: sin él no habría dónde persistir el estado ni la incidencia, y el reintento no sería ni idempotente ni auditable. El **derecho** sigue sin concederse: un registro no es un derecho. |
| `D-FND-05-06` | Se tocó el docstring (no las aserciones) de un test de FND-04. | `test_la_compra_se_marca_pagada_sin_activar_derechos` seguía siendo cierto pero podía leerse como falso. Sus aserciones (`apps.is_installed`) NO se modificaron. |

---

## 11. Peticiones a A0 (ficheros compartidos NO editados por este paquete)

Ninguna es **bloqueante** para el uso interno del coordinador.

- **A0-FND05-01** · `*.sqlite3` en el `.gitignore` del objetivo (ya pedido por FND-01/02/03/04; el
  byproduct de la rehearsal de migraciones lo borra el paquete, pero la regla debe existir).
- **A0-FND05-02** · Sincronizar la matriz física `00-matriz-tareas.md`, fila `T-015`
  (`FND-05 | A0 | T-013 | W01 | pending | activation interface`) → `completed`.
- **A0-FND05-03** · Decidir **dónde se publica** el estado de la activación al operador
  (`D-FND-05-01`): un puerto nuevo en `pagos` que extienda `estado_operativo`, o una superficie de
  lectura propia. XCT-03 / API-03 son los dueños naturales.

---

## 12. Decisiones abiertas

- **`D-FND-05-01`** (nueva) · dónde se publica el estado de la activación al operador — A0 +
  XCT-03 + API-03.
- **`D-FND-05-07`** (nueva) · **política de reintento**: este paquete NO implementa un comando de
  reintento ni una cola. El reintento es **seguro** (la clave es estable y el dominio deduplica),
  pero su **disparador** —un comando de operación, una tarea programada o el propio flujo de
  pago— está sin decidir. A0 + A2.
- **`D-FND-05-08`** (nueva) · **número máximo de intentos**: el lease de 300 s permite reintentar
  indefinidamente. Si el negocio exige un tope o un escalado al operador, hay que fijarlo.
  A0 + producto.
- Se heredan sin cambio: `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · GAP-1…GAP-4 · D-A…D-E ·
  `GOV-02-UX-01`…`05` · `GOV-02-SH-01`…`08` · `GOV-02-BL-01`…`12` · `GOV-02-CM-01`…`05` ·
  `P-01`…`P-12` · `GOV-01-OPEN-09` · `GOV-01-OPEN-10` · `NEW-FND03-01`…`04` · `D-FND-02-01`…`09` ·
  `D-FND-04-01`…`06`.

---

## 13. Rollback

**Punto de rollback:** `f3df5401c56b41c340f257e67d5a306904a9e670` (sin cambios; este paquete **no
creó ningún commit** y **nunca** invocó `git stash`).

Orden de reversión:

1. `manage.py migrate commerce zero` (desaplica `0002_activacioncompra` y `0001_initial`).
2. Borrar los ficheros nuevos de `modules/commerce/**` y `modules/pagos/**` listados en §7.
3. Revertir las modificaciones de `modules/pagos/**` listadas en §7.3 y de
   `modules/commerce/**` listadas en §7.2 (los ficheros de FND-04 **no** se tocan: este paquete no
   reescribió ninguno, salvo las modificaciones listadas, que son nuevas o aditivas).
4. Restaurar `STATE.md` y el artefacto de apply.

**El historial de pagos se conserva**: el rollback no deshace ni un cobro. Si el rollback ocurre
después de que un dominio haya aplicado un derecho, ese derecho **no se revierte** (la política de
reversión es `PD-06` / `GOV-01-OPEN-06`, sigue abierta).

---

## 14. Consumidores desbloqueados

- **DOM-02** (`inscripciones`, pool y ampliación de cupos) · **DOM-03** (`pases`, lotes y
  beneficiarios) · **DOM-06** (`marketplace`, pedido y stock): implementan
  `IActivadorDominioCompra` y registran su activador. **Ya no tienen que inventar el contrato de
  la activación**: la clave, el contexto, el resultado y el doble de prueba están hechos.
- **DOM-01 / DOM-04 / DOM-05** · **DOM-07 / DOM-08**: pueden seguir creando compras y órdenes
  igual que hasta ahora; el coordinador no exige cambios en ellos.
- **XCT-03** (conciliación de pagos: los tres estados y la incidencia de activación): la
  incidencia ya existe, es legible y es reintentable (`D-FND-05-01`).
- **API-03 / API-04**: pueden publicar `estado_operativo` sin cambios; la activación se publica
  según `D-FND-05-01`.
- **VER-01…VER-03**: tienen la evidencia de exactly-once, de fallo y de reintento.
- **A7 / UI-01…UI-05**: la UI del comprador puede seguir mostrando "Pago confirmado; estamos
  resolviendo la activación de tu compra" en cuanto `D-FND-05-01` decida el canal.

---

## 15. Nota de concurrencia

`Aplicacion/frontend/**` (FND-06 / UI-01A) siguió avanzando durante este paquete: **no se tocó,
no se revirtió y no se fusionó**. `Aplicacion/backend/modules/eventos/**` y
`Aplicacion/backend/modules/usuarios/**` tampoco se tocaron; sus suites se re-ejecutaron verdes
dentro de V3. La fila `FND-06` del tablero **no** se editó (A0/A7 es su dueño).

---

## 16. Siguiente paquete

**DOM-02**, **DOM-03** y **DOM-06**, después de sus prerrequisitos de dominio. Cada uno implementa
`IActivadorDominioCompra` y registra su activador: con eso, un pago confirmado habilita el
derecho **una sola vez** en el dominio que le corresponde.

El contrato que tienen delante, en una línea:

```python
class MiActivadorDeDominio(IActivadorDominioCompra):
    def activar(self, contexto: ContextoActivacionCompra) -> ResultadoActivacionDominio:
        # 1. Si ya aplicaste `contexto.clave`, no lo apliques otra vez.
        # 2. Aplica TU derecho (cupos, entradas, stock) con TUS reglas.
        # 3. Devuelve exito=True y un código de máquina. Nada de texto libre.
        ...
```

