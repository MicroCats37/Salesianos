# XCT-03 — Reconciliación de pagos, despliegue de media y notificación

**Paquete:** `XCT-03` (`wave-04-cross-cutting`) · **Tareas de origen:** `T-084`, `T-085`, `T-086`
**Propietarios:** A0 + A2 · **Fecha:** 2026-11-20
**Freezes respetados:** `FREEZE-CM-1.0.0` (FR-04) · `FREEZE-ENV-1.0.0` (FR-01) ·
`FREEZE-MD-1.0.0` (FR-06) · `FREEZE-PS-1.0.0` (FR-07) · `FREEZE-TC-1.0.0`
**Artefacto de apply (canónico):** `sdd/salesianos-fest-rebuild/xct-03-apply-progress` (Engram) ·
tema compartido `sdd/salesianos-fest-rebuild/apply-progress`

---

## 1. Resumen ejecutivo

Se implementaron las tres líneas de trabajo del paquete:

| Línea | Tarea | Estado | Qué se entregó |
|---|---|---|---|
| **WU-1** | `T-084` | **aplicada** | Un **segundo canal de veredicto** (`estado_activacion`), separado del veredicto operativo congelado; el servicio `ReconciliacionPagoService` y el comando `reconciliar_activaciones` (el disparador del reintento que `D-FND-05-07` dejó abierto) |
| **WU-2** | `T-085` | **aplicada** | Volumen de media **persistente** en el despliegue, exposición por el servidor de archivos en sólo-lectura, permisos del volumen, y *smoke checks* de despliegue + integración multipart |
| **WU-3** | `T-086` | **aplicada con BLOQUEO explícito** | El módulo `notificaciones` (trazabilidad del intento + puerto) y la garantía de que **el fallo de la notificación nunca revierte la compra**. El **proveedor SMTP NO se configuró**: `PD-08` sigue abierto |

**Los tres hechos que el paquete tenía que separar siguen siendo tres hechos.**
`Compra.estado`, `OrdenPago.estado` y `TransaccionPago.estado` no se tocan, y el
veredicto operativo conserva **exactamente sus ocho códigos congelados**. Lo que
se añadió es un **canal aditivo**: `estado_activacion`, que responde «¿está
habilitado el derecho?» sin contaminar el veredicto de «¿está pagado esto?».

**El vocabulario congelado NO se amplió ni se renumeró** (`D-07`, FR-01 §5.2). El
test `test_el_vocabulario_del_veredicto_operativo_no_se_amplia_ni_se_renumera`
lo fija.

---

## 2. Contexto leído (obligatorio)

| Fuente | Uso |
|---|---|
| `AGENTS.md` (raíz) · `contract/**` (7 ficheros) | Ownership, prohibiciones, arquitectura, tests |
| `00-contrato-global-de-apply.md` · `00-matriz-tareas.md` | Reglas globales · filas `T-084`/`T-085`/`T-086` |
| `STATE.md` | Tablero y baseline de fallos conocidos |
| `evidence/contracts/FR-04` · `FR-05` · `FR-06` · `FR-09` · `FR-01` §5 | Contratos de pago/activación, media, decisiones abiertas, veredicto |
| `evidence/foundations/FND-04` · `FND-05` | Digests del backend de pagos y del coordinador de activación |
| `evidence/domains/DOM-02` · `DOM-03` · `DOM-06` | Los tres orígenes de la activación (INSCRIPCION / PASE / MARKETPLACE) |
| `evidence/cross-cutting/XCT-01` · `XCT-02` | Patrón de apply veraz (`verification_required`) y módulo `administracion` ya existente |
| `evidence/api/API-03` · `API-04` · `API-05` | Estado de los presenters y de sus espejos Zod |
| `Aplicacion/plan/**` (`contratos/01`, `contratos/03`, `frontend/04`) | Reglas de veredicto, media y panel de pagos |
| `Aplicacion/documentacion/**` (dirigido) | Contradicción de `estado_operativo` en la UI, filtro no expuesto |

---

## 3. WU-1 · `T-084` — Conciliación de pagos

### 3.1 El problema que había

`FND-05` (`D-FND-05-01`) dejó escrito que el veredicto operativo **no refleja**
el estado de la activación: tras un fallo de activación seguía siendo `PAGADA`.
La incidencia existía y era reintentable (`ActivacionCompra.incidencia`,
`proxima_accion`), pero **nadie la encontraba**: no había ninguna superficie
que dijera «hay pagos cobrados sin derecho habilitado».

`D-FND-05-07` dejó abierto el **disparador** del reintento. `D-FND-05-08`
dejó abierto el número máximo de intentos. Este paquete cierra el primero.

### 3.2 La decisión de diseño: un SEGUNDO canal, no un código nuevo

La tentación era añadir un noveno código a `EstadoOperativoPago` (p. ej.
`PAGADA_SIN_ACTIVAR`). **No se hizo**, por tres razones:

1. `FR-01` §5.2 congela el vocabulario «sin renumerar» y `D-07` lo declara
   **intacto**; `FND-05` documentó que tocarlo **cambiaría la garantía de
   FND-04** (`PAGADA` tras una confirmación correcta), que tiene un test rojo
   si se toca.
2. El estado de la matriz `SH-03` («Necesita atención: cobrado pero el derecho
   todavía no está habilitado») es un estado de **presentación**, y la capa
   que lo resuelve es el adaptador, no el veredicto.
3. Un código nuevo obligaría a tocar los adaptadores de `features/admin/**`
   (owner de API-04/UI-04) y de `features/cuenta/**` (owner de API-01), que
   **no son raíces de este paquete**.

**Lo que se hizo:** `pagos` publica **dos** veredictos, y es el **único dueño
de los dos** (`EstadoOperativoPagoService`, FR-01 §5):

| Canal | Pregunta | Vocabulario | Dónde |
|---|---|---|---|
| `estado_operativo` | «¿está pagado esto?» | `EstadoOperativoPago` (8, **congelado**) | `modules/pagos/domain/constants.py` |
| `estado_activacion` | «¿está habilitado el derecho?» | `EstadoActivacionPago` (5, **nuevo**) | `modules/pagos/domain/constants.py` |

El segundo canal es **aditivo**: `estado_activacion` viaja **junto a**
`estado_operativo`, nunca dentro de él. El vocabulario de `commerce`
(`EstadoActivacionCompra`) **no se duplica**: el puerto expone **banderas**
(`activada`, `pendiente`, `fallida`, `en_curso`, `recuperable`) y `pagos`
publica el veredicto — igual que `EstadoCompraOrdenPago` expone banderas en
lugar del vocabulario de `commerce`.

### 3.3 Los tres estados y la incidencia, separados

```
Compra.estado      (PAGADA)      ── hecho COMERCIAL   ─┐
OrdenPago.estado   (CONFIRMADA)  ── hecho de ORDEN     ─┼─► estado_operativo  (8 códigos, congelado)
TransaccionPago    (EXITO)       ── hecho del PROVEEDOR┘
ActivacionCompra   (PENDIENTE |  ── hecho del DERECHO  ──► estado_activacion (5 códigos, nuevo)
                    FALLIDA | ACTIVADA)
```

La **incidencia de activación** viaja en `estado_activacion`
(`recuperable`, `proxima_accion`) y **no** se mezcla con el veredicto
operativo: un pago confirmado con la activación fallida sigue siendo
`PAGADA` en el canal congelado y `FALLIDA` en el canal nuevo.

### 3.4 La reconciliación

`modules/pagos/domain/services/core/reconciliacion_pago_service.py`

| Garantía | Cómo |
|---|---|
| **No se pierde un pago verificado** | Recorre las órdenes `CONFIRMADA` y detecta las que no tienen la activación resuelta |
| **No se activa dos veces** | Si la activación ya está `ACTIVADA`, la orden **no se toca**: el coordinador ni se invoca (FR-04 I-2) |
| **No revierte el cobro** | El servicio **no toca** `OrdenPago.estado` ni `Compra.estado`; sólo pide al coordinador que reintente |
| **El fallo es recuperable** | Un fallo del coordinador se registra como incidencia (`RECONCILIACION_FALLIDA`, `recuperable=True`) y la pasada continúa |
| **Es auditable** | Devuelve un informe por orden: estado antes, código del reintento, acción segura, si se aplicó |

El **disparador** (`D-FND-05-07`) es un **comando de operación**, no una cola
ni una tarea programada:

```
python manage.py reconciliar_activaciones             # informe, NO muta
python manage.py reconciliar_activaciones --aplicar    # reintenta
python manage.py reconciliar_activaciones --aplicar --limite 500
```

Por defecto **informa**: el comando nunca muta sin `--aplicar`.

### 3.5 Archivos (WU-1)

**Creados** (5)

| Archivo | Qué es |
|---|---|
| `modules/pagos/domain/services/core/reconciliacion_pago_service.py` | El servicio de conciliación |
| `modules/pagos/management/__init__.py` · `management/commands/__init__.py` | Paquetes del comando |
| `modules/pagos/management/commands/reconciliar_activaciones.py` | El disparador del reintento |
| `modules/pagos/tests/integration/test_reconciliacion_pago.py` | 9 tests de comportamiento (**ESCRITOS, NO EJECUTADOS**) |

**Modificados** (13)

`modules/pagos/domain/constants.py` (vocabulario `EstadoActivacionPago` +
`DESCRIPCIONES_ESTADO_ACTIVACION`) · `domain/schemas/pago_schemas.py`
(`EstadoActivacionCompraData`) · `domain/ports/__init__.py`
(`estado_activacion` en `IActivacionCompraService` + `INotificadorCompraService`) ·
`domain/results/pago_result.py` (`EstadoActivacionResult`, `ItemReconciliacion`,
`ResultadoReconciliacion`) · `domain/selectors/pago_selector.py`
(`listar_confirmadas`) · `domain/services/core/estado_operativo_pago_service.py`
(`calcular_activacion`, `calcular_activacion_para_orden`) ·
`domain/services/flujos/pago_confirmacion_flujo.py` (paso 9 de la secuencia +
`estado_activacion` en el resultado) ·
`domain/services/orchestrators/pagos_orchestrator.py` (canal en `RT-PG-03`) ·
`di.py` (bindings) · `presentation/schemas/pago_schemas.py` (`EstadoActivacionOut`) ·
`presentation/presenters/pago_presenter.py` (`present_estado_activacion`) ·
`modules/commerce/infrastructure/services/activacion_compra.py`
(`estado_activacion`, la lectura del puerto).

**El campo `estado_activacion` se publica en** `PagoConfirmadoOut` (RT-PG-01,
RT-PG-02) y en `OrdenPagoOut` (RT-PG-03).

---

## 4. WU-2 · `T-085` — Media, permisos y despliegue

### 4.1 Los tres huecos reales que había

| # | Hueco | Evidencia | Corrección |
|---|---|---|---|
| 1 | **El volumen de media no era persistente** | `Aplicacion/docker-compose.yml` montaba **sólo** `backend_static`; `MEDIA_ROOT = BASE_DIR/media` = `/app/media` **dentro** del contenedor ⇒ cada `docker compose up` perdía los logos y las imágenes | Volumen nombrado `backend_media` montado en `/app/media` |
| 2 | **El media no se servía en producción** | `config/urls.py` sólo sirve `MEDIA_URL` cuando `settings.DEBUG` es `True`, y `production.py` fija `DEBUG = False` ⇒ en el despliegue **no había servidor de media** | El **servidor de archivos del despliegue** (nginx) lo expone, con el volumen montado en sólo-lectura |
| 3 | **El proxy no conocía `/media/`** | `proxy/nginx.conf` no tenía `location /media/`: la URL absoluta `/media/…` caía en `location /` ⇒ Next.js, no el backend | `location /media/` con `alias`, `try_files`, `nosniff` y caché inmutable |

### 4.2 Las tres piezas del media, ahora coherentes

```
Django (escritor)          MEDIA_ROOT = /app/media   (config/settings/base.py)
     ▲                          │
     │ escribe                  │ volumen nombrado `backend_media`
     │                          ▼
docker-compose.yml      backend:  backend_media:/app/media
                        proxy:    backend_media:/var/www/media:ro
                                       ▲
                                       │ lee (sólo lectura)
                                       ▼
proxy/nginx.conf        location /media/ { alias /var/www/media/; … }
                                       │
                                       ▼
navegador               GET /media/productos/<id>/<uuid>.png
```

El test `test_las_tres_piezas_del_media_coinciden` **compara las tres** y falla
si deja de cuadrar.

### 4.3 Permisos del volumen

`docker/entrypoint.sh` prepara el volumen **antes** de que arranque gunicorn:

```bash
MEDIA_DIR="${MEDIA_ROOT:-/app/media}"
mkdir -p "$MEDIA_DIR"
chown -R appuser:appuser "$MEDIA_DIR"
chmod -R u+rwX,g+rX,o+rX "$MEDIA_DIR"
```

- El volumen puede haberlo creado `root` en una corrida anterior: se corrige
  el dueño.
- El grupo y los demás necesitan **leer** (nginx los monta en sólo-lectura):
  `0755` directorios, `0644` archivos.
- **Nunca** se borra, trunca ni vacía el volumen.

### 4.4 El respaldo: BLOQUEO EXPLÍCITO, nocompletion fingida

`GOV-01-OPEN-09` (política de copia de seguridad) sigue **ABIERTO**. Este
paquete **no inventa** rutas, credenciales, ventanas ni un planificador:

- `MEDIA_BACKUP_ENABLED` existe y vale **`False`**.
- `MEDIA_BACKUP_ROOT` existe y vale **`""`**.
- No hay ninguna tarea programada ni comando que active la copia.
- El comentario de `settings/base.py` lo dice con esas palabras: *«"Sin copia"
  es un hecho conocido y declarado, no un olvido»*.

El test `test_el_respaldo_del_media_no_esta_fingido` lo fija.

### 4.5 Sin secretos en el despliegue

- `MEDIA_ROOT` es **configurable por nombre de variable** (`MEDIA_ROOT`), nunca
  por valor. El valor por defecto es `BASE_DIR/media`.
- El test `test_la_configuracion_de_despliegue_no_publica_secretos` comprueba
  que el `docker-compose.yml` y el `nginx.conf` no contienen credenciales
  literales: sólo referencias `${VARIABLE}`.

### 4.6 Archivos (WU-2)

**Creados** (1) · `core/tests/integration/test_media_despliegue.py` — 5 *smoke
checks* de despliegue (**ESCRITOS, NO EJECUTADOS**).

**Modificados** (4) · `Aplicacion/backend/config/settings/base.py` (`MEDIA_ROOT`
configurable + bloqueador del respaldo) · `Aplicacion/docker-compose.yml`
(volumen `backend_media` en backend y proxy) · `Aplicacion/proxy/nginx.conf`
(`location /media/`) · `Aplicacion/backend/docker/entrypoint.sh` (permisos del
volumen).

**Integración multipart**: el protocolo (`data` + `files`, token
`<token>___<realname>`, rechazo de huérfanos, de token no resuelto y de token
duplicado) **ya estaba implementado y verificado** en `core/media.py`
(FND-01) y consumido por `marketplace` (DOM-04) y `patrocinadores` (DOM-08), con
sus tests en `core/tests/integration/test_media_validation.py`. Este paquete
**no lo reimplementa**: añade la comprobación de que el despliegue lo respeta
(volumen + servidor de archivos + permisos) y no duplica los tests de protocolo.

---

## 5. WU-3 · `T-086` — Notificación (proveedor BLOQUEADO)

### 5.1 `PD-08` sigue abierto ⇒ el proveedor NO se configura

`PD-08` (proveedor, plantillas, límites, reintentos y entrega) está **OPEN** y
diferido por `DEC-21` (`FR-09` §2.1). La regla del paquete es explícita:
*«configure provider only with explicit PD-08 approval and environment variable
names, never values»* y *«If PD-08 is unresolved, persist T-086 as
blocked/deferred without inventing SMTP settings»*.

**Lo que este paquete NO hizo:**

- No creó ningún cliente SMTP, ni destinatario, ni plantilla, ni credencial.
- No añadió ninguna variable de entorno de correo.
- No tocó `config/settings/production.py` (los `EMAIL_*` que ya existían
  vienen del código heredado; este paquete no ratifica ni ejecuta ese
  proveedor).
- No moduló Django's `EMAIL_BACKEND`: **ningún correo puede salir** por el
  módulo nuevo.

**Nombres de variable de entorno (sólo nombres, nunca valores).** Los nombres
que el despliegue necesitará cuando `PD-08` se ratifique son los estándar de
Django, y **ya existen** en `config/settings/production.py` del objetivo:

`EMAIL_HOST` · `EMAIL_PORT` · `EMAIL_USE_TLS` · `EMAIL_HOST_USER` ·
`EMAIL_HOST_PASSWORD`

Lo que `PD-08` tiene que decidir y este paquete **no** decide: el proveedor,
el remitente, las plantillas, los límites de envío, la política de reintentos
y la garantía de entrega.

### 5.2 Lo que sí se implementó (el contrato, no el proveedor)

El módulo `notificaciones` es una **hoja** del grafo: no depende de ningún
módulo de dominio.

| Pieza | Qué es |
|---|---|
| `modules/notificaciones/models.py` | `NotificacionEnvio`: la **trazabilidad** del intento (estado, código de máquina, intentos, incidencia con lista cerrada de claves) |
| `modules/notificaciones/domain/constants.py` | `EstadoNotificacion` (OMITIDA/PENDIENTE/ENVIADA/FALLIDA), `TipoNotificacion`, y `PROVEEDOR_NO_APROBADO` |
| `.../domain/services/core/notificacion_envio_core_service.py` | La escritura idempotente del registro (la restricción única es la guarda real) |
| `.../infrastructure/services/notificador_comprador.py` | La implementación del puerto: **omite** el envío y lo dice con un código |
| `modules/notificaciones/di.py` | El wiring de DI |
| `modules/notificaciones/migrations/0001_initial.py` | La migración (**escrita a mano**, sin generar) |

**La unicidad `(orden_pago_id, tipo)`** garantiza que un webhook duplicado **no**
crea un segundo registro de notificación: es I-1 aplicado a la notificación.

**El puerto** `INotificadorCompraService` lo declara `pagos` (el consumidor) y
lo implementa `notificaciones` (el proveedor): la dirección de dependencias
queda `notificaciones → pagos` y el grafo sigue acíclico. `pagos` nunca importa
`notificaciones` en tiempo de módulo: el enlace es una **fábrica perezosa** en
`modules/pagos/di.py`, igual que con `commerce`.

### 5.3 La garantía: el fallo de la notificación NO revierte la compra

`RN-C08`, FR-04 §4. En `pago_confirmacion_flujo.py`, el paso 9 de la secuencia
congelada:

```python
if confirmar and not ya_confirmado:
    await sync_to_async(self._notificar_comprador)(orden, activacion)
```

`_notificar_comprador` **captura cualquier excepción** del notificador y la
registra; el flujo continúa. El pago confirmado **y** el derecho habilitado se
conservan.

Además, **sólo se notifica cuando el derecho quedó habilitado**: avisar de una
compra cuyo derecho todavía no se ha concedido sería afirmar un hecho que no
ocurrió (decisión `D-XCT-03-03`, abierta a producto cuando `PD-08` se
ratifique).

**Tests** (`modules/pagos/tests/integration/test_notificacion_independencia.py`,
4 casos) y (`modules/notificaciones/tests/integration/test_notificacion.py`,
6 casos) — **ESCRITOS, NO EJECUTADOS**.

---

## 6. DI y orden de registro

| Elemento | Dónde | Nota |
|---|---|---|
| `modules.notificaciones` | `LOCAL_APPS` (`config/settings/base.py`) | **Al final**: no altera el grafo de migraciones de los demás nodos |
| `modules.notificaciones.di.NotificacionesModule` | `NINJA_EXTRA["INJECTOR_MODULES"]` | **Al final**: hoja del grafo, sin dependencias |
| `INotificadorCompraService` | `modules/pagos/di.py` → `_notificador_service_factory` | **Fábrica perezosa**: el import ocurre al resolver el puerto, nunca al importar el módulo |
| `IActivacionCompraService` | `modules/pagos/di.py` → `_activacion_service_factory` | Pre-existente (FND-05); ahora con el método de lectura |
| `ReconciliacionPagoService` | `modules/pagos/di.py` | Binding directo |
| `NotificacionEnvioCoreService` · `NotificadorCompradorAdapter` | `modules/notificaciones/di.py` | |
| **Endpoints** | `config/api.py` | **NO se registró ningún controller nuevo.** `notificaciones` no publica superficie HTTP: el ledger de FR-07 no tiene ruta de notificaciones y `PD-08` está abierto |

`manage.py check` (**0**, ver §7) carga la aplicación completa: los once
módulos de DI y los controllers registrados se importan sin error.

---

## 7. Comandos y códigos de salida

Standing restriction vigente (preferencia `workflow/salesianos-sdd-apply-verification-deferred`
#11299): durante **apply** las pruebas se **ESCRIBEN** pero **NO SE EJECUTAN**.
Lo único ejecutado en esta pasada:

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `uv run python manage.py check --settings=config.settings.test` | `Aplicacion/backend` | **0** | `System check identified no issues (0 silenced)` |
| V2 | `uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test` | `Aplicacion/backend` | **0** | `No changes detected` — la migración `notificaciones.0001_initial` escrita a mano coincide con el modelo |
| V3 | `ast.parse` sobre los 27 ficheros Python creados/modificados | `Aplicacion/backend` | **0** | `ast.parse OK: 27 ficheros, 0 fallos` |
| V4 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | **2 errores, ambos AJENOS**: `src/features/inscripciones/__tests__/inscripcion-transporte.test.ts` (líneas 446 y 487). **0 errores** en las raíces de este paquete |
| V5 | `docker compose config --quiet` | `Aplicacion` | **0** | La configuración del despliegue (volumen `backend_media` en backend y proxy) es válida |
| V6 | `git status --short` | raíz | **0** | Ver §9 |

**NO EJECUTADOS** (prohibidos por la restricción vigente): `pytest`,
`vitest`, `Biome`, `next build`, `docker compose build`, servidor, navegador,
auditoría de cinco anchos, `git diff --check` (requiere `git diff`, sin
operaciones de escritura: **no** se invocó por estar fuera de la lista
autorizada).

**NOTA sobre V1/V2**: el settings por defecto es `config.settings.production`
y falla con `ImproperlyConfigured: Set the DB_NAME environment variable` — el
**baseline ambiental** conocido e idéntico de FND-01…FND-05, DOM-* y XCT-01/02.
Se usó `--settings=config.settings.test` (SQLite en memoria, sin `debug_toolbar`)
por coherencia con `pytest.ini`.

**Fallos de baseline conocidos**: sin cambios. **Regresiones**: ninguna.

---

## 8. Los dos errores de `features/inscripciones/**` son AJENOS

`npx tsc --noEmit` sale **1** por dos errores en
`src/features/inscripciones/__tests__/inscripcion-transporte.test.ts`
(líneas 446 y 487): el literal de prueba no lleva `promocion_id` ni `cantidad`
que el tipo exige.

- **NO son de este paquete**: `features/inscripciones/**` no es raíz de
  edición de XCT-03 y no lo he tocado.
- **NO los he tocado, revertido ni fusionado**: son de un árbol **concurrente**
  (`git status` muestra 28 ficheros modificados y 5 nuevos en
  `features/inscripciones/**`, más `modules/salesianos_fest/**` y
  `modules/usuarios/**`, todos ajenos).
- Verificación de que son ajenos: `git diff` sobre
  `Aplicacion/frontend/src/features/inscripciones` **no** incluye ningún
  fichero mío; mis raíces son `features/pagos/**` (nuevo) y no aparecen.

---

## 9. Ficheros cambiados (este paquete)

**Backend — `Aplicacion/backend/`**

| Fichero | Acción |
|---|---|
| `modules/pagos/domain/constants.py` | modificado |
| `modules/pagos/domain/schemas/pago_schemas.py` | modificado |
| `modules/pagos/domain/ports/__init__.py` | modificado |
| `modules/pagos/domain/results/pago_result.py` | modificado |
| `modules/pagos/domain/selectors/pago_selector.py` | modificado |
| `modules/pagos/domain/services/core/estado_operativo_pago_service.py` | modificado |
| `modules/pagos/domain/services/core/reconciliacion_pago_service.py` | **creado** |
| `modules/pagos/domain/services/flujos/pago_confirmacion_flujo.py` | modificado |
| `modules/pagos/domain/services/orchestrators/pagos_orchestrator.py` | modificado |
| `modules/pagos/di.py` | modificado |
| `modules/pagos/management/__init__.py` · `management/commands/__init__.py` | **creado** |
| `modules/pagos/management/commands/reconciliar_activaciones.py` | **creado** |
| `modules/pagos/presentation/schemas/pago_schemas.py` | modificado |
| `modules/pagos/presentation/presenters/pago_presenter.py` | modificado |
| `modules/pagos/tests/integration/test_reconciliacion_pago.py` | **creado** |
| `modules/pagos/tests/integration/test_notificacion_independencia.py` | **creado** |
| `modules/commerce/infrastructure/services/activacion_compra.py` | modificado |
| `modules/notificaciones/**` (18 ficheros) | **creado** |
| `core/tests/integration/test_media_despliegue.py` | **creado** |
| `config/settings/base.py` | modificado |
| `docker/entrypoint.sh` | modificado |

**Despliegue — `Aplicacion/`** · `docker-compose.yml` (modificado) ·
`proxy/nginx.conf` (modificado)

**Frontend — `Aplicacion/frontend/src/features/pagos/`** (4 ficheros) ·
**creado**

**Evidencia y estado** · `evidence/cross-cutting/XCT-03-payment-media-notifications.md`
(creado) · `STATE.md` (modificado)

**CERO cambios** en: `contract/**`, `Aplicacion/plan/**`,
`Aplicacion/documentacion/**`, `backend/**`, `frontend/**`, `worker/**`,
`proxy/**` (raíces congeladas), `.env*`, bases de datos, y **ningún** módulo
ajeno (`modules/administracion/**`, `modules/salesianos_fest/**`,
`modules/usuarios/**`, `modules/validaciones/**`, `modules/competencias/**`,
`modules/marketplace/**`, `modules/patrocinadores/**`).

**Ningún commit. `git stash` nunca invocado. Ninguna operación de git de
escritura.**

---

## 10. Desviaciones y decisiones

| ID | Desviación / decisión | Por qué |
|---|---|---|
| `D-XCT-03-01` | El estado de la activación se publica como **canal aditivo** (`estado_activacion`), **no** como un noveno código de `EstadoOperativoPago` | `FR-01` §5.2 y `D-07` congelan el vocabulario «sin renumerar»; `FND-05` documentó que tocarlo rompe la garantía de FND-04. El paquete `T-084` («separar los tres estados y la incidencia») se cumple separando el canal, no el código |
| `D-XCT-03-02` | El disparador del reintento es un **comando de operación**, no una cola ni una tarea programada | Cierra `D-FND-05-07`. Es idempotente, auditable, no corre solo y no exige un planificador en el proceso del API |
| `D-XCT-03-03` | La notificación **sólo** se intenta cuando el derecho quedó habilitado | Avisar de una compra sin derecho concedido afirmaría un hecho que no ocurrió. Revisable por producto cuando `PD-08` se ratifique |
| `D-XCT-03-04` | `NotificacionEnvio` **no** lleva FK a `pagos` ni a `commerce` | `notificaciones` es una **hoja** del grafo. Una FK `PROTECT` haría que la trazabilidad bloquease el borrado de un pago (que está prohibido) y convertiría al auditor en participante del ciclo de vida del cobro |
| `D-XCT-03-05` | `NotificacionEnvio` **no** usa `simple_history` | La fila **es** la traza: acumula los intentos en sus propios campos. El histórico de modelos es opcional en este proyecto (`contract/django-app-architecture-contract.md`: «historic models *si el proyecto lo requiere*») |
| `D-XCT-03-06` | La migración `notificaciones/0001_initial.py` está **escrita a mano** | La restricción vigente prohíbe generar migraciones. Se verificó con `makemigrations --check --dry-run` → `No changes detected` (V2) |
| `D-XCT-03-07` | El media **no** se sirve por Django en producción | FR-06 §2.1: la exposición es «servicio/servidor de archivos del despliegue». Django sólo lo sirve en `DEBUG` (desarrollo) |
| `D-XCT-03-08` | El respaldo del media **no** se implementa | `GOV-01-OPEN-09` abierto. Se declara el bloqueo en vez de fingir una copia |
| `D-XCT-03-09` | No se registró ningún controller nuevo ni se amplió el ledger de rutas | `notificaciones` no publica superficie HTTP: `PD-08` está abierto y no hay ruta congelada para él |
| `D-XCT-03-10` | `estado_activacion` **no** se publica en `features/admin/pagos/**` ni en `features/cuenta/**` | Sus espejos Zod son de API-04 / API-01 (dueños: A7). Los presentadores que los alimentan (`modules/administracion/**`) **no** son raíces de este paquete. Se deja como petición a A0 (§12) |
| `D-XCT-03-11` | `D-FND-05-08` (número máximo de intentos) sigue **abierta** | El tope de intentos y el escalado al operador son una decisión de negocio/producto. El lease de 300 s de FND-05 sigue siendo la única red de seguridad |

---

## 11. Rollback

**Punto de rollback:** `f3df5401c56b61c340f257e67d5a306904a9e670` (sin cambios;
este paquete **no creó ningún commit** y **nunca** invocó `git stash`).

Orden de reversión:

1. `manage.py migrate notificaciones zero` (desaplica `0001_initial`).
2. Borrar `modules/notificaciones/**` y los ficheros nuevos listados en §9.
3. Revertir las modificaciones de `modules/pagos/**`, `modules/commerce/**`,
   `core/tests/**`, `config/settings/base.py` y `docker/entrypoint.sh` listadas
   en §9.
4. Revertir `Aplicacion/docker-compose.yml` y `Aplicacion/proxy/nginx.conf`.
5. Borrar `Aplicacion/frontend/src/features/pagos/**`.
6. Restaurar `STATE.md` y el artefacto de apply.

**Lo que el rollback NO deshace**: ningún cobro, ningún derecho ya habilitado,
ningún archivo de media ya subido. La política de reversión de derechos es
`PD-06` / `GOV-01-OPEN-06` y sigue **abierta**. **Nunca** `docker compose down -v`:
eso borraría el volumen de media, la base de datos y los hechos de pago.

---

## 12. Peticiones a A0

Ninguna **bloqueante** para el uso interno de lo entregado.

| ID | Petición | Owner natural |
|---|---|---|
| `A0-XCT03-01` | Publicar `estado_activacion` en el presenter administrativo (`modules/administracion/**`) y en sus espejos Zod (`features/admin/pagos/**`), para que el operador vea «cobrado pero el derecho no habilitado» en la lista de pagos | A8 + A7 (API-04) |
| `A0-XCT03-02` | Consumir `estado_activacion` en la cuenta del comprador (`features/cuenta/**`), con el mensaje de FR-04 §4 («Pago confirmado; estamos resolviendo la activación de tu compra») | A7 (API-01) |
| `A0-XCT03-03` | Ratificar `PD-08` (proveedor, plantillas, límites, reintentos, entrega) para poder configurar el proveedor de correo | A0 + producto |
| `A0-XCT03-04` | Ratificar `GOV-01-OPEN-09` (respaldo del volumen de media) y `GOV-01-OPEN-10` (límites de dimensión por tipo) | A0 + producto |
| `A0-XCT03-05` | Decidir `D-FND-05-08`: número máximo de intentos de activación y escalado al operador | A0 + producto |
| `A0-XCT03-06` | Sincronizar la matriz física `00-matriz-tareas.md`, filas `T-084`, `T-085` y `T-086` → `verification_required` | A0 |
| `A0-XCT03-07` | `*.sqlite3` en el `.gitignore` del objetivo (petición heredada de FND-01…FND-05) | A0 |
| `A0-XCT03-08` | El `docker-compose.yml` declara `POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}` — un valor por defecto **débil** y comiteado. No es un secreto filtrado (es un marcador conocido y sobrescribible por `.env`), pero conviene que el despliegue lo exija | A0 + producto |

---

## 13. Verificación pendiente (VER-01)

Este paquete queda en **`verification_required`**: la implementación está
aplicada y las pruebas **escritas**, pero **NO ejecutadas**.

| # | Prueba / comprobación | Escrita | Ejecutada |
|---:|---|---|---|
| 1 | `python -m pytest modules/commerce/tests modules/pagos/tests modules/notificaciones/tests -q` (workdir `Aplicacion/backend`) | 19 casos nuevos en 3 ficheros | **NO** |
| 2 | `python manage.py check` (workdir `Aplicacion/backend`) | — | **SÍ** (V1, exit 0) |
| 3 | `python manage.py makemigrations --check --dry-run` | — | **SÍ** (V2, exit 0) |
| 4 | `docker compose config --quiet` (workdir `Aplicacion`) | — | **SÍ** (V5, exit 0) |
| 5 | `docker compose build` (workdir `Aplicacion`) | — | **NO** |
| 6 | `npx vitest run src/features/pagos` (workdir `Aplicacion/frontend`) | 6 casos en 1 suite | **NO** |
| 7 | `npx biome check src/features/pagos` (workdir `Aplicacion/frontend`) | — | **NO** |
| 8 | `git diff --check` (raíz) | — | **NO** |

**Cobertura de comportamiento escrita** (19 casos de backend + 6 de frontend):

| Fichero | Casos | Garantía |
|---|---|---|
| `modules/pagos/tests/integration/test_reconciliacion_pago.py` | 9 | Separación de canales · recuperación · convergencia (no duplica) · no reversión del cobro · informe sin aplicación · orden no confirmada fuera · fallo del coordinador |
| `modules/pagos/tests/integration/test_notificacion_independencia.py` | 4 | El fallo de la notificación no revierte · sólo se notifica con derecho habilitado · un webhook duplicado no duplica la notificación · el veredicto de activación se publica |
| `modules/notificaciones/tests/integration/test_notificacion.py` | 6 | Trazabilidad · omisión con código explícito · idempotencia por orden y tipo · incidencia con datos seguros · no guarda el detalle comercial |
| `core/tests/integration/test_media_despliegue.py` | 5 | Volumen persistente · sólo-lectura · las tres piezas coinciden · el respaldo no está fingido · sin secretos |
| `frontend/src/features/pagos/__tests__/pagos-estados.test.ts` | 6 | El adaptador resuelve el cubo · el texto del backend se copia literal · un código desconocido es neutro |

**Riesgos que VER-01 debe atender primero**

1. Los **19 casos de backend** son nuevos y **nunca se han ejecutado**: pueden
   fallar por detalles de fixtures (`registro_activadores` es una fixture de
   `commerce`, importada en los tests de `pagos`).
2. La **resolución del inyector** (`IActivacionCompraService` →
   `ActivacionCompraAdapter`, `INotificadorCompraService` →
   `NotificadorCompradorAdapter`) sólo está verificada **estáticamente** en esta
   pasada: `manage.py check` carga los módulos de DI, pero no resuelve los
   puertos.
3. El **mensaje del proxy**: `/media/…` sólo existe si el proxy nginx del
   despliegue está en pie. En desarrollo, `DEBUG=True` y Django sirve el media.
4. La **migración `notificaciones.0001_initial`** está escrita a mano: verificada
   con `makemigrations --check --dry-run` (V2), pero el **replay** sobre una
   base real (`migrate` → `migrate notificaciones zero` → `migrate`) queda para
   VER-01.

---

## 14. Siguiente paquete

**VER-01** — `wave-05-verification-cleanup/VER-01-baseline-regression-payments.md`
(`T-090`, `T-091`). Es el que debe ejecutar lo que esta pasada escribió sin
ejecutar.

**Consumidores desbloqueados**: `API-03` / `API-04` (el canal
`estado_activacion` ya lo publica `pagos`; falta propagarlo a sus
presenters) · `API-05` (el comando de reconciliación es la operación de
mantenimiento que los lotes de pases necesitan) · `VER-01…VER-03` (la
evidencia de exactly-once, de fallo, de reintento y de independencia de la
notificación).

**Siguiente paquete:** `VER-01`.
