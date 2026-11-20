# CORR-VER01 · Corrección de los bloqueadores de backend probados por VER-01

**Artifact:** `evidence/corrections/CORR-VER01-backend-blockers.md` ·
**Change:** `salesianos-fest-rebuild` · **Owner:** A0 (cableado) + DOM-01/A3
(presenter) · **Modo:** apply correctivo · **Store:** engram + evidencia
física · **Fecha:** 2026-11-20

> **ESTADO: `applied` — los TRES bloqueadores de backend probados por VER-01
> §6.1 y §7.1 están corregidos y VERDE en runtime.**
>
> **NO se editó `STATE.md`**: esta corrección corre en PARALELO con otra
> corrección del mismo VER-01; el dueño de VER-01 reconcilia el tablero
> compartido cuando las dos terminen.

---

## 1. Qué se corrigió (y por qué)

| # | Bloqueador probado | Corrección | Dueño |
|---:|---|---|---|
| **B-F1** | `catalogo_presenter.py:110` leía `result.paqueta_id`; el resultado expone `paquete_id` ⇒ **HTTP 500** en `POST /cotizaciones` | Una línea: `result.paqueta_id` → `result.paquete_id` | DOM-01 / A3 |
| **A0-XCT02-01** | `modules.administracion` NO registrada en `INSTALLED_APPS` ni en `INJECTOR_MODULES`, y sus **seis** controllers NO registrados ⇒ **7 endpoints que el frontend YA consume NO existían** (404) y **2 ficheros de test NO se podían recolectar** | App + wiring de DI + los seis controllers, en el registro permanente | A0 |
| **A0-API02-09** | `CotizacionController` implementado y **NO registrado** ⇒ `POST /cotizaciones` no existía | Controller registrado en `config/api.py` | A0 |
| **admin.E108** | XCT-02 lo declaró preexistente (`PaqueteAdmin.list_display[3] → cupos_incluidos`) | **NO SE CORRIGIÓ: la condición no se cumple.** El `list_display` actual de `PaqueteAdmin` es `("nombre", "edicion", "estado", "tipo", "minimo_compra_inicial")`: el índice 3 es `tipo`, NO `cupos_incluidos`, y `cupos_incluidos` sigue siendo un campo real del modelo. El `check` de Django está **verde** (VER-01 §6.3 ya lo declaraba RESUELTO). Se deja un **guardián** (§5) para que no vuelva | A0 (guardián) |

### 1.1 Corrección del allowlist del guardián de registro

`core/tests/integration/test_registration_extension.py` fija **cinco** listas
CERRADAS. El registro nuevo las obliga a moverse **en el MISMO cambio**
(lo exige `evidence/foundations/A0-wiring-validation.md` §6):

| Lista | Cambio |
|---|---|
| `CONTROLLERS_COMPLETADOS` | + `CotizacionController` (tras `CatalogoController`) · + los seis de `administracion` (al final) |
| `PREFIJOS_PERMITIDOS` | + `/api/cotizaciones` · + `/api/administracion` |
| `RUTAS_DE_DOMINIO_CONGELADAS` | + `POST /api/cotizaciones` · + las **12** rutas de `administracion` · + `/api/catalogo/categorias` y `/api/catalogo/promociones` (deriva preexistente del árbol concurrente, forzada por la aserción de **igualdad exacta**) |
| `APPS_DE_DOMINIO_COMPLETADAS` | + `modules.notificaciones` (deriva preexistente) · + `modules.administracion` |
| `MODULOS_DE_DI_COMPLETADOS` | + `modules.notificaciones.di.NotificacionesModule` (deriva preexistente) · + `modules.administracion.di.AdministracionModule` |

**Medido antes del cambio** (corrida sobre el árbol ya cableado, con las
listas viejas): **8 failed, 3 passed**. Los ocho fallos eran exactamente el
desalineamiento de las cinco listas. **Después:** **11 passed**.

---

## 2. Ficheros cambiados (4 modificados + 2 creados)

| Fichero | Acción | Qué |
|---|---|---|
| `Aplicacion/backend/modules/salesianos_fest/presentation/presenters/catalogo_presenter.py` | modificado (1 línea) | `result.paqueta_id` → `result.paquete_id` |
| `Aplicacion/backend/config/settings/base.py` | modificado | `LOCAL_APPS` += `modules.administracion` · `INJECTOR_MODULES` += `modules.administracion.di.AdministracionModule` (al FINAL: su migración `0001_initial` sólo depende de `eventos.0001_initial` y de `AUTH_USER_MODEL`, y su wiring va detrás del de los módulos que consume) |
| `Aplicacion/backend/config/api.py` | modificado | Import + registro de `CotizacionController` y de los seis controllers de `administracion` · comentarios del registro actualizados |
| `Aplicacion/backend/core/tests/integration/test_registration_extension.py` | modificado | Las cinco listas cerradas, alineadas con el registro real |
| `Aplicacion/backend/core/tests/integration/test_a0_cableado_administracion_cotizacion.py` | **creado** | 8 pruebas de A0 (§5) |
| `Aplicacion/backend/modules/salesianos_fest/tests/e2e/test_cotizacion_controller.py` | **creado** | 3 pruebas de DOM-01 (§5) |

**Fuera de las raíces permitidas: NADA.** Cero cambios en `contract/**`,
`Aplicacion/plan/**`, `Aplicacion/documentacion/**`, frontend, módulos
ajenos ni los **raíces congelados** (`backend/**`, `frontend/**`,
`worker/**`, `proxy/**`). Cero `git stash` / `reset` / `checkout` / `commit` /
`push`. Cero instalaciones: `uv run --group dev` exclusivamente.

---

## 3. Comandos / códigos de salida (workdir `Aplicacion/backend`)

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| C1 | `python -m pytest core/tests/integration/test_registration_extension.py -q` (allowlist viejo, registro nuevo) | **1** | **8 failed, 3 passed** — el desalineamiento medido |
| C2 | `python -m pytest core/tests/integration/test_registration_extension.py -q` (allowlist nuevo) | **0** | **11 passed** |
| C3 | `python -m pytest modules/administracion/tests -q` | **0** | **15 passed** — antes NO se podían recolectar (VER-01 §6.1 B-F2/B-F3) |
| C4 | `python -m pytest modules/salesianos_fest/tests/e2e -q` | **0** | **46 passed** (43 previos + 3 nuevos) |
| C5 | `python -m pytest modules/salesianos_fest/tests/e2e/test_cotizacion_controller.py -q` | **1** | **2 failed, 1 passed** — **RED PROBADO** con el typo reintroducido a propósito (§4) |
| C6 | `python -m pytest modules/salesianos_fest/tests/e2e/test_cotizacion_controller.py -q` (restaurado) | **0** | **3 passed** |
| C7 | `python -m pytest core/tests/integration/test_a0_cableado_administracion_cotizacion.py -q` | **0** | **8 passed** |
| C8 | `python -m pytest modules/administracion/tests modules/salesianos_fest/tests/e2e core/tests/integration/test_registration_extension.py core/tests/integration/test_a0_cableado_administracion_cotizacion.py -q` | **0** | **83 passed** — el objetivo combinado más pequeño |
| C9 | `python manage.py check --settings=config.settings.test` | **0** | `System check identified no issues (0 silenced).` |
| C10 | `python manage.py makemigrations --check --dry-run --settings=config.settings.test` | **0** | `No changes detected` |
| C11 | `python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced).` |
| C12 | `python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| C13 | `python -m pytest --collect-only -q` (raíz) | **0** | **971 tests collected** — **0 errores de recolección** (VER-01 B1 medía *exit 2 · 690 collected + 2 errores*) |
| C14 | `python -m pytest modules core -q` (backend completo) | **1** | **2 failed, 969 passed** en 212.27 s — los 2 fallos son de otro dueño (§6) |
| C15 | `python manage.py check` (settings por defecto = producción) | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **baseline ambiental B7**, idéntico a VER-01 B7 · GOV-02 · FND-01…05 · DOM-* · XCT-* |

**Comandos NO ejecutados (y por qué):** `next build` · `npm install` ·
navegador · auditoría de cinco anchos · **lane PostgreSQL** de `BL-05` §2 (no
hay PostgreSQL en este entorno: los casos de concurrencia `QA-V02` / `QA-I05`
corren sobre SQLite, donde `select_for_update` es un **NO-OP** — el riesgo que
XCT-01 §7.1 declaró **sigue ABIERTO**) · suite de frontend · suite de raíz
completa · `git stash` / `commit` / `reset` / `checkout` · `uv sync` ·
Python global.

---

## 4. Prueba RED (el defecto estaba ahí y la prueba lo caza)

La corrección del presenter se **reintrodujo a propósito** (`paqueta_id`) y se
ejecutó el objetivo nuevo:

```
F modules/salesianos_fest/tests/e2e/test_cotizacion_controller.py::test_la_cotizacion_responde_200_y_trae_el_identificador_del_paquete
    assert respuesta.status_code == 200
E   assert 500 == 200
E   AttributeError: 'CotizacionResult' object has no attribute 'paqueta_id'. Did you mean: 'paquete_id'?
    core\...\catalogo_presenter.py:110 in present_cotizacion
E       paquete_id=UUID(result.paqueta_id),

F modules/salesianos_fest/tests/e2e/test_cotizacion_controller.py::test_la_cotizacion_no_devuelve_500_ni_traza
E   assert 500 == 200
2 failed, 1 passed
```

Es **exactamente** el defecto `B-F1` de VER-01 §6.1 (mismo `AttributeError`,
misma línea, mismo HTTP 500). El typo se restauró inmediatamente después y la
corrida volvió a **3 passed**.

---

## 5. Pruebas nuevas (focales por dueño)

### 5.1 `core/tests/integration/test_a0_cableado_administracion_cotizacion.py` (A0 — 8)

1. `test_la_app_administracion_esta_registrada_de_forma_permanente`
2. `test_el_wiring_de_di_de_administracion_esta_registrado`
3. `test_el_wiring_de_di_de_administracion_va_tras_el_de_los_modulos_que_consume`
4. `test_las_rutas_de_administracion_existen_en_el_api_vivo` (las 12)
5. `test_las_seis_superficies_de_administracion_responden_y_no_404` — **`GET
   /api/administracion/resumen` sin sesión responde 401, NO 404**: la ruta
   existe y su autenticación está cableada
6. `test_la_ruta_de_cotizacion_existe_en_el_api_vivo`
7. `test_el_check_de_django_no_reporta_el_error_de_admin_e108`
8. `test_el_admin_de_paquetes_no_declara_una_entrada_invalida_en_list_display`
   — la regla de `admin.E108` comprobada sobre el modelo

### 5.2 `modules/salesianos_fest/tests/e2e/test_cotizacion_controller.py` (DOM-01 — 3)

1. `test_la_ruta_de_cotizacion_esta_registrada_en_el_api_permanente`
2. `test_la_cotizacion_responde_200_y_trae_el_identificador_del_paquete` —
   comprueba `paquete_id` (el campo que rompía)
3. `test_la_cotizacion_no_devuelve_500_ni_traza`

Ambas suites usan el **URLconf real de la aplicación** (`config.urls`), no un
URLconf de pruebas: si el controller no estuviera registrado en
`config/api.py`, el cliente respondería **404** y la prueba caería.

---

## 6. Verdad de rutas y de migraciones (medida)

| Magnitud | Antes (VER-01, 2026-11-20) | **Ahora** |
|---|---:|---:|
| Controllers registrados | 15 | **22** |
| Rutas vivas (`api.get_openapi_schema()["paths"]`) | 62 | **75** (+13) |
| Rutas consumidas por el frontend SIN ruta registrada (DRIFT A) | **8** | **0** |
| Apps de dominio en `INSTALLED_APPS` | 9 | **11** (`+notificaciones`, `+administracion`) |
| Módulos de DI en `INJECTOR_MODULES` | 9 | **11** |
| Errores de recolección de la raíz | **2** | **0** |
| `manage.py check` (`config.settings.test`) | 0 | **0** |
| `makemigrations --check --dry-run` (`config.settings.test`) | 0 | **0** (`No changes detected`) |

### 6.1 Las trece rutas nuevas

| Ruta | Dueño |
|---|---|
| `POST /api/cotizaciones` | DOM-01 (`A0-API02-09`) |
| `GET /api/administracion/resumen` | XCT-02 (`RT-ADM-01`) |
| `GET /api/administracion/auditoria` | XCT-02 (`RT-ADM-02`) |
| `GET /api/administracion/inscripciones` | XCT-02 |
| `GET /api/administracion/inscripciones/{inscripcion_id}` | XCT-02 |
| `GET /api/administracion/inscripciones/{inscripcion_id}/participantes/{participacion_id}` | XCT-02 |
| `GET /api/administracion/equipos` | XCT-02 |
| `GET /api/administracion/equipos/{equipo_id}` | XCT-02 |
| `GET /api/administracion/participantes` | XCT-02 |
| `GET /api/administracion/pagos` | XCT-02 |
| `GET /api/administracion/pagos/{compra_id}` | XCT-02 |
| `GET /api/administracion/personas` | XCT-02 |
| `GET /api/administracion/personas/{persona_id}` | XCT-02 |

### 6.2 Verdad de migraciones

`modules.administracion` se registra y su migración `0001_initial` está
escrita a mano: `makemigrations --check --dry-run` dice **"No changes
detected"** ⇒ la migración coincide EXACTAMENTE con el modelo
`AccionAuditada`. El grafo no se altera: `administracion.0001_initial`
depende sólo de `eventos.0001_initial` y de `AUTH_USER_MODEL`, y no declara
FK a ningún otro módulo de dominio.

---

## 7. Residuales (NO bloqueadores de este packet)

### 7.1 Dos fallos de la suite del backend, de OTRO dueño

`C14` → **2 failed, 969 passed**. Los dos fallos **NO** son de este packet:
las pruebas y el código que los producen son del cambio concurrente
`restore-registration-promotion-catalog-flow` (2026-11-20), y ese cambio
**no estaba** cuando VER-01 midió (VER-01 §2.1 B3: `1 failed, 700 passed`).

| # | Test | Causa | Archivo a tocar | Fuera de las raíces permitidas |
|---:|---|---|---|---|
| R-1 | `core/tests/integration/test_contract_versions.py::test_no_hay_drift_entre_el_registro_y_el_modulo[salesianos_fest]` | El módulo `salesianos_fest` subió `SCHEMA_VERSION` a `2.0.0` (MAJOR) pero el registro global de A0 sigue en `"1.2.0"`: `hay_drift('2.0.0', '1.2.0')` | `core/contract_versions.py` → `SCHEMA_VERSIONS["salesianos_fest"] = "2.0.0"` | **SÍ** — `core/contract_versions.py` no está en las raíces de este packet |
| R-2 | `core/tests/integration/test_exceptions_public_catalog.py::test_todo_codigo_de_dominio_esta_en_el_catalogo_publico` | El módulo declara `PrecioCambiadoError` (`PRECIO_CAMBIADO`, 409) y **pide** su prosa a A0; el catálogo público tiene ya los otros cinco códigos nuevos, pero **no** éste | `core/exceptions.py` → `PUBLIC_ERROR_MESSAGES["PRECIO_CAMBIADO"]` | **SÍ** — `core/exceptions.py` no está en las raíces de este packet |

**No se corrigieron**: (a) no son bloqueadores **probados por VER-01**;
(b) sus archivos están **fuera** de las raíces de edición permitidas;
(c) `core/contract_versions.py` y `core/exceptions.py` los acaba de tocar un
agente **concurrente**: tocarlos aquí sería competir con su árbol en vuelo.
**Dueño: A0**, en el paquete que cierre `restore-registration-promotion-catalog-flow`.

> Nota: la ruta `POST /api/cotizaciones` que este packet registra es una de
> las tres que el propio cambio concurrente declara en su *changelog* de
> versión (`1.2.0` → `2.0.0`). Con el registro aplicado, la superficie y la
> versión declarada **coinciden**; sólo queda actualizar el registro global.

### 7.2 Limpiezas opcionales (no bloquean)

- `modules/administracion/tests/settings_overlay.py`: su propio docstring pide
  a A0 que lo elimine una vez aplicado el registro permanente. Es **idempotente**
  (`if "modules.administracion" not in INSTALLED_APPS`) y **no molesta**: la
  suite del módulo pasa **sin** overlay. No se borra en este packet para no
  tocar más raíces del dueño XCT-02 (`apps.py`, `di.py` lo citan).
- `modules/salesianos_fest/tests/urls_salesianos_fest.py`: monta su propia
  `NinjaExtraAPI` con los controllers de `salesianos_fest`. Su docstring pide
  a A0 que lo elimine al registrar los controllers. **Se conserva**: el
  registro permanente es `config/api.py`, y este URLconf es el que aísla la
  suite e2e del módulo del resto de la superficie. La prueba de que la ruta
  existe en el registro **permanente** vive en el fichero nuevo (§5.2), que
  usa `config.urls`.

---

## 8. Concurrencia preservada

- El árbol traía **178 líneas** de cambios de otros agentes al empezar este
  packet: **no se tocaron, no se revertieron y no se fusionaron**. Los seis
  ficheros de este packet se editan **sólo** en sus puntos de_packet.
- `git stash` · `git reset` · `git checkout` · `git commit` · `git push`:
  **nunca invocados**. `uv sync` / instalación: **nunca**.
- `STATE.md` **no** se editó (corrección paralela): el dueño de VER-01
  reconcilia el tablero compartido cuando las dos correcciones terminen.
- Engram: observación **packet-específica**
  `sdd/salesianos-fest-rebuild/corr-ver01-backend-blockers` (el topic
  compartido `…/apply-progress` y `…/state` **no** se tocaron).
- **Fuera del repositorio (temporal, no versionado, nada commiteado):**
  `%TEMP%\opencode\ver01b_routes_probe.py` (sonda que vuelca los controllers
  vivos y las 75 rutas del esquema OpenAPI). Se puede borrar sin efecto.

---

## 9. Rollback

1. `modules/salesianos_fest/presentation/presenters/catalogo_presenter.py`:
   revertir **una** línea (`result.paquete_id` → `result.paqueta_id`).
2. `config/api.py`: quitar los siete imports y las trece entradas de
   `registrar_controladores`, y devolver el comentario al texto anterior.
3. `config/settings/base.py`: quitar `"modules.administracion"` de
   `LOCAL_APPS` y `"modules.administracion.di.AdministracionModule"` de
   `INJECTOR_MODULES`.
4. `core/tests/integration/test_registration_extension.py`: devolver las cinco
   listas a su contenido anterior.
5. Borrar los dos ficheros de prueba nuevos.
6. En Engram: borrar el topic
   `sdd/salesianos-fest-rebuild/corr-ver01-backend-blockers`.
7. **Punto de rollback:** `2c411cdfc062714cfa7ff39765c4357ddf8267e2` ("betha 6")
   — el HEAD real, que ya existía cuando empezó VER-01. **No revertir ni
   resetear ese commit.**

> **La historia de los pagos NUNCA se borra en un rollback:** un cobro, un
> derecho habilitado y una activación registrada son hechos (`RN-C08`,
> `RN-P08`).

---

## 10. Estado para VER-02

**DESBLOQUEADO en su parte de backend**, salvo los residuales §7.1 (que son
de otro dueño) y la lane PostgreSQL (§3).

| Bloqueador de VER-01 §11 | Estado |
|---|---|
| B-F1 (`catalogo_presenter.py:110`) | **CORREGIDO** (RED→GREEN probado, §4) |
| A0-XCT02-01 (`modules.administracion` sin registrar) | **CORREGIDO** (12 rutas vivas · 401 y no 404 · suite 15/15 sin overlay) |
| A0-API02-09 (`CotizacionController` sin registrar) | **CORREGIDO** (`POST /api/cotizaciones` viva · 200 con `paquete_id`) |
| admin.E108 | **NO APLICA**: el `list_display` actual no lo produce; `check` verde; guardián añadido |
| 40 fallos de frontend | **FUERA DE ALCANCE** (dueños UI-01/UI-03/UI-04/UI-05/API-01…API-05/FND-06/FND-07/FND-08) |
| Lane PostgreSQL | **ENTORNO**: no disponible en este entorno |
| R-1 / R-2 (§7.1) | **ABIERTOS**, dueño A0, cambio concurrente `restore-registration-promotion-catalog-flow` |
