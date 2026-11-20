# A0 · Validación del cableado global (apps, DI, controllers, versiones, catálogo, puertas)

**Artifact:** `evidence/foundations/A0-wiring-validation.md` · **Paquete:**
`sdd-apply` **A0 · validación y reconciliación** (sólo-verificación) ·
**Change:** `salesianos-fest-rebuild` · **Owner:** A0 (coordinador) · **Date:**
2026-11-19

> **ESTADO: `BLOCKED` — el cableado global de A0 NO está implementado en el
> objetivo.** La premisa «A0 global wiring is already implemented» **NO se
> sostiene** contra el árbol actual: la validación en runtime la contradice en
> los **siete** ejes exigidos. Este paquete **NO repara** nada: `Aplicacion/backend/**`
> es raíz **prohibida** para esta pasada. Lo que hace es **re-ejecutar** las
> pruebas, **cuantificar** el hueco y **documentar** la prueba fallida exacta.

**Paquetes cuya integración se reconcilia:** `DOM-03` (A4) · `DOM-05` (A5) ·
`DOM-06` (A5) · `DOM-07` (A6) · `DOM-08` (A8)

---

## 1. Entorno de verificación

| Elemento | Valor |
|---|---|
| Directorio de trabajo | `Aplicacion/backend` |
| Gestor | `uv 0.10.9` (f675560f3) |
| Intérprete | CPython 3.10.0 |
| Django | 5.2.11 |
| Comando base | `uv run --group dev python …` (obligatorio) |
| `pytest.ini` | `DJANGO_SETTINGS_MODULE = config.settings.test` · `addopts = --tb=short --nomigrations` · `asyncio_mode = auto` |
| HEAD | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit) |
| Overlays usados | **fuera del repositorio**: `%TEMP%\opencode\a0_all_apps_overlay.py` (verificación) — `config/**` **NO** se tocó |

**Por qué un overlay fuera del repositorio:** para responder «¿puedo registrar
`competencias` y `patrocinadores` sin romper nada?» hay que **probarlo** sin
escribir en `Aplicacion/backend/**`. El overlay replica el registro permanente
que A0 debe aplicar y vive en `%TEMP%`; **ningún fichero del repositorio fue
creado o modificado por esta pasada**.

---

## 2. Comandos / códigos de salida

| # | Comando (workdir `Aplicacion/backend`) | Exit | Resultado |
|---:|---|---:|---|
| R1 | `uv run --group dev python -m pytest --collect-only -q` (raíz, settings por defecto) | **2** | **725 collected, 6 errores de colección** — `RuntimeError: Model class modules.competencias… doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS` (y los 5 equivalentes de `patrocinadores`). **La raíz del backend NO se puede recolectar.** |
| R2 | `uv run --group dev python manage.py check` (settings por defecto = `config.settings.production`) | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **baseline ambiental idéntico** a FND-01…FND-05, DOM-06 y al cierre DOM-03/05/07/08. **NO** es regresión. |
| R3 | `uv run --group dev python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced).` |
| R4 | `uv run --group dev python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` — **pero CIEGA** para `competencias`/`patrocinadores`: Django no las conoce (§5, `A0-RTV-01`). |
| R5 | `uv run --group dev python -m pytest core/tests -q` | **0** | **244 passed** (1.78 s) — el guardián de registro está **verde HOY**, y sólo porque sus listas cerradas siguen reflejando el estado **sin cablear** (§6). |
| R6 | sonda de registro (`a0_wiring_probe.py`, fuera del repo) | **0** | 6 apps de dominio · 6 módulos de DI · 10 controllers · **34** rutas OpenAPI · **2** controllers **NO importables** (§4). |
| R7 | `uv run --group dev python -m pytest --collect-only -q` (**overlay de 8 apps**) | **0** | **833 collected** — la recolección de la raíz deja de estar interrumpida. |
| R8 | `uv run --group dev python -m pytest core/tests -q` (**overlay de 8 apps**) | **1** | **2 failed, 242 passed** — los 2 fallos son del guardián (`A0-RTV-04`, §6). |
| R9 | `uv run --group dev python -m pytest -q` (**overlay de 8 apps**, suite completa) | **1** | **2 failed, 831 passed** (833 collected), 597 warnings, 212.10 s — **reproduce exactamente** el V24 del cierre anterior. |
| R10 | inventario de códigos públicos (`a0_catalog_probe.py`, fuera del repo) | **0** | catálogo **120** · códigos lanzados en producción **78** · **33 sin catalogar** (§7). |
| G1 | `git rev-parse HEAD` | **0** | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` — sin commit |
| G2 | `git status --short -- Aplicacion/backend` | **0** | **122 líneas**, **idénticas** al estado de entrada: **ningún fichero del backend fue creado, modificado ni borrado** por esta pasada |
| G3 | SHA-256 de `Aplicacion/backend/db.sqlite3` antes / después de R2…R4 | **0** | **sin cambios** — las puertas de Django no abren la base de datos (`USE_SQLITE` no se fijó) |

**Not run:** `git stash` · `git reset` · `git checkout` · `git commit` ·
`git push` · Python global · `.venv\Scripts\python.exe` directo.

---

## 3. Eje 1 — `config/settings/base.py` registra las apps de DOM-03…DOM-08

**Resultado: FALLA.** Estado leído en runtime (R6):

```
APPS_MODULOS: ['modules.eventos', 'modules.usuarios', 'modules.pagos',
               'modules.commerce', 'modules.salesianos_fest', 'modules.marketplace']
DI_MODULOS:   ['modules.usuarios.di.UsuariosModule', 'modules.eventos.di.EventosModule',
               'modules.pagos.di.PagosModule', 'modules.commerce.di.CommerceModule',
               'modules.salesianos_fest.di.SalesianosFestModule',
               'modules.marketplace.di.MarketplaceModule']
```

| App de dominio | ¿Registrada? | Módulo de DI | ¿Registrado? |
|---|---|---|---|
| `modules.eventos` | **SÍ** | `EventosModule` | **SÍ** |
| `modules.usuarios` | **SÍ** | `UsuariosModule` | **SÍ** |
| `modules.pagos` | **SÍ** | `PagosModule` | **SÍ** |
| `modules.commerce` | **SÍ** | `CommerceModule` | **SÍ** |
| `modules.salesianos_fest` (DOM-01…03) | **SÍ** | `SalesianosFestModule` | **SÍ** |
| `modules.marketplace` (DOM-04…06) | **SÍ** | `MarketplaceModule` | **SÍ** |
| **`modules.competencias` (DOM-07)** | **NO** | **`CompetenciasModule`** | **NO** |
| **`modules.patrocinadores` (DOM-08)** | **NO** | **`PatrocinadoresModule`** | **NO** |

Ambos módulos de DI **existen en disco** (`modules/competencias/di.py` →
`class CompetenciasModule(Module)`, `modules/patrocinadores/di.py` →
`class PatrocinadoresModule(Module)`): lo que falta es **sólo** el registro.

El comentario de `base.py` §LOCAL_APPS sigue diciendo, textualmente,
«Ninguna app INACABADA (`pases`, `beneficios`, `validaciones`,
`patrocinadores`, `competencias`, `administracion`) se registra» — **las dos
últimas ya NO están inacabadas** (DOM-07 y DOM-08 están `completed` con suite
verde), pero el registro no se ha movido.

---

## 4. Eje 2 — `config/api.py` registra los cuatro controllers

**Resultado: FALLA.** Estado leído en runtime (R6):

```
CONTROLLERS_REGISTRADOS: ['NinjaJWTDefaultController', 'EdicionController',
  'PersonaController', 'AuthController', 'PagosController', 'CatalogoController',
  'InscripcionController', 'ProductoController', 'PaseController', 'AdminPaseController']
```

| Controller | Paquete | Prefijo `@api_controller` | ¿Registrado? | ¿Importable? |
|---|---|---|---|---|
| `PedidoController` | **DOM-05** | `/marketplace` (2 rutas) | **NO** | **SÍ** |
| `InventarioController` | **DOM-06** | `/administracion/marketplace` (5 rutas) | **NO** | **SÍ** |
| `CompetenciasController` | **DOM-07** | `/competencias` (16 rutas) | **NO** | **NO** |
| `PatrocinadorController` | **DOM-08** | `/patrocinadores` (1 ruta) | **NO** | **NO** |

**Las 24 rutas de los cuatro controllers NO existen en el API vivo.**

**Dependencia de orden (hallazgo NUEVO de esta pasada):** `PedidoController` e
`InventarioController` **importan** bien porque `modules.marketplace` **sí** está
registrada; `CompetenciasController` y `PatrocinadorController` **fallan al
importar**:

```
IMPORT_FAIL: CompetenciasController -> RuntimeError: Model class
  modules.competencias.domain.models.auditoria.AuditoriaOperacion doesn't
  declare an explicit app_label and isn't in an application in INSTALLED_APPS.
IMPORT_FAIL: PatrocinadorController -> RuntimeError: Model class
  modules.patrocinadores.domain.models.patrocinador.Patrocinador doesn't
  declare an explicit app_label and isn't in an application in INSTALLED_APPS.
```

⇒ **El registro de las apps (Eje 1) es un PRECONDICITO del registro de los
controllers (Eje 2)**, no un cambio paralelo: sin `modules.competencias` y
`modules.patrocinadores` en `INSTALLED_APPS`, **ni siquiera se pueden importar**
los dos controllers de esos dominios. Esto **no** estaba escrito en el
informe anterior y queda ahora probado en runtime.

### 4.1 Superficie OpenAPI viva (34 rutas)

Inventario completo de `api.get_openapi_schema()["paths"]` (R6). Las **24
rutas** que los cuatro controllersdominantes aportarían **no están**:

| Familia de rutas | Estado en el API vivo |
|---|---|
| `/api/token/{pair,refresh,verify}` | presente (`ninja_jwt`) |
| `/api/ediciones/actual` | presente (FND-02) |
| `/api/personas/**` (3) · `/api/auth/**` (4) | presentes (FND-03 / FND-03A) |
| `/api/pagos/**` (3) | presentes (FND-04) |
| `/api/catalogo/**` (2) · `/api/inscripciones/**` (7) | presentes (DOM-01 / DOM-02) |
| `/api/pases/**` (5) · `/api/administracion/pases/**` (2) | presentes (DOM-03) |
| `/api/marketplace/{productos,categorias}` (3) | presentes (DOM-04) |
| **`/api/marketplace/pedidos`** (2) | **AUSENTE** (DOM-05) |
| **`/api/administracion/marketplace/{inventario,entregas}/**` (5) | **AUSENTE** (DOM-06) |
| **`/api/competencias/**`** (16) | **AUSENTE** (DOM-07) |
| **`/api/patrocinadores`** (1) | **AUSENTE** (DOM-08) |

---

## 5. Eje 3 — Puertas de migración / `check`

**Resultado: PARCIAL — verdes, pero CIEGAS.**

| Puerta | Exit | Lectura |
|---|---:|---|
| `manage.py check` (settings por defecto) | **1** | `DB_NAME` — **baseline ambiental**, no regresión |
| `manage.py check --settings=config.settings.development` | **0** | `no issues` |
| `manage.py makemigrations --check --dry-run` (development) | **0** | `No changes detected` |

**La ceguera:** la puerta de migraciones es verde **precisamente porque
Django no conoce** `modules.competencias` ni `modules.patrocinadores`. Con las
ocho apps registradas (overlay, R7) la recolección de la raíz deja de estar
interrumpida (833 collected) — pero **la puerta de migraciones de esas dos apps
sigue sin poder evaluarse** hasta que estén registradas: hoy
`makemigrations --check --dry-run` **no ve** sus modelos.

---

## 6. Eje 4 — Guardián de registro y guardián OpenAPI

**Resultado: FALLA DE ALINEACIÓN.**

`core/tests/integration/test_registration_extension.py` fija **cinco** listas
**CERRADAS**:

| Lista | Entradas actuales | Le falta |
|---|---:|---|
| `CONTROLLERS_COMPLETADOS` | 10 | `PedidoController` · `InventarioController` · `CompetenciasController` · `PatrocinadorController` |
| `PREFIJOS_PERMITIDOS` | 10 | `/api/marketplace` (parcial) · `/api/administracion/marketplace` · `/api/competencias` · `/api/patrocinadores` |
| `RUTAS_DE_DOMINIO_CONGELADAS` | 31 | las 24 rutas de los cuatro controllers |
| `APPS_DE_DOMINIO_COMPLETADAS` | 6 | `modules.competencias` · `modules.patrocinadores` |
| `MODULOS_DE_DI_COMPLETADOS` | 6 | `modules.competencias.di.CompetenciasModule` · `modules.patrocinadores.di.PatrocinadoresModule` |

**Hoy el guardián está VERDE (R5: 244 passed)** — y ese es el punto: está verde
**porque** el registro no se ha movido. **Reproducido** con el overlay de ocho
apps (R8/R9):

```
FAILED core/tests/integration/test_registration_extension.py::test_no_hay_apps_de_dominio_inacabadas_registradas
    AssertionError: assert registradas == APPS_DE_DOMINIO_COMPLETADAS
    Left contains 2 more items, first extra item: 'modules.competencias'
FAILED core/tests/integration/test_registration_extension.py::test_solo_se_registran_los_modulos_de_di_completados
    AssertionError: assert modulos == MODULOS_DE_DI_COMPLETADOS
    Left contains 2 more items, first extra item: 'modules.competencias.di.CompetenciasModule'
```

**2 failed, 831 passed** sobre 833 collected (R9). Reproduce **exactamente**
el V24 del cierre anterior: registrar las dos apps **es seguro**, pero **exige
ampliar las listas en el MISMO cambio**. El guardián existe para que nadie
registre una app a medias; no es un defecto, es **su trabajo**.

---

## 7. Eje 5 — Registro de versiones del contrato

**Resultado: FALLA.** `core/contract_versions.py::SCHEMA_VERSIONS` (R6):

```
beneficios 1.0.0 · commerce 1.0.0 · envelope 1.0.0 · eventos 1.0.0 ·
marketplace 1.2.0 · pagos 1.0.0 · pases 1.0.0 · patrocinadores 1.0.0 ·
salesianos_fest 1.2.0 · usuarios 1.1.0 · validaciones 1.0.0
```

**Falta `"competencias"`.** El módulo `modules/competencias` declara
`SCHEMA_VERSION = "1.0.0"` en su `presentation/schemas/__init__.py` y **no
tiene test de drift** (a diferencia de `marketplace` y `patrocinadores`, que sí
lo tienen). Sin registro no hay mecanismo de **detección de drift** entre el
backend y el espejo Zod del frontend para DOM-07.

**Nota sobre las claves heredadas:** `pases`, `beneficios` y `validaciones` son
nombres de **dominio** heredados, no de **módulo físico** (`modules/<clave>`).
No se tocan en esta pasada: **no** es la raíz de este bloqueo y corregirlas
sería política de versionado de A0 (`FR-07`), no una prueba de runtime.

---

## 8. Eje 6 — Catálogo público de errores

**Resultado: FALLA.** Inventario por barrido de los literales `code = "<CÓDIGO>"`
del código de producción de los cuatro módulos (R10), contrastado con
`core/exceptions.py::PUBLIC_ERROR_MESSAGES`:

| Magnitud | Valor |
|---|---:|
| Entradas en `PUBLIC_ERROR_MESSAGES` | **120** |
| Códigos lanzados en producción (4 módulos) | **78** |
| **Códigos sin catalogar** | **33** |

Reparto: `marketplace` **13** · `competencias` **16** · `patrocinadores` **4** ·
`salesianos_fest` **0** (los 17 de DOM-03 **sí** están catalogados).

```
marketplace (13): MOVIMIENTO_INVENTARIO_INMUTABLE, MOVIMIENTO_INVENTARIO_INVALIDO,
  MOVIMIENTO_INVENTARIO_NO_ENCONTRADO, PEDIDO_CANTIDAD_INVALIDA, PEDIDO_ITEMS_MIXTOS,
  PEDIDO_ITEM_NO_PERMITIDO, PEDIDO_NO_AUTORIZADO, PEDIDO_NO_ENCONTRADO,
  PEDIDO_NO_ENTREGABLE, PEDIDO_NO_PAGADO, PEDIDO_SIN_RESERVA,
  RESERVA_NO_CONFIRMABLE, STOCK_INSUFICIENTE
competencias (16): BYE_INVALIDO, COMPETENCIA_EQUIPO_DUPLICADO,
  COMPETENCIA_EQUIPO_NO_ENCONTRADA, COMPETENCIA_NO_ENCONTRADA,
  DISCIPLINA_NO_ENCONTRADA, ENCUENTRO_NO_ENCONTRADO, ENLACE_INVALIDO,
  GANADOR_INVALIDO, HORARIO_INVALIDO, MOTIVO_REQUERIDO, ORDEN_DUPLICADO,
  PARTICIPANTE_INVALIDO, RONDA_DUPLICADA, RONDA_NO_ENCONTRADA,
  SOLAPAMIENTO_HORARIO, TRANSICION_INVALIDA
patrocinadores (4): GALERIA_PATROCINADOR_INVALIDA, PATROCINADOR_IMAGEN_NO_ENCONTRADA,
  PATROCINADOR_NO_ENCONTRADO, PATROCINADOR_SLUG_DUPLICADO
```

**Efecto real** (leído en `core/exceptions.py::on_http_error`): el
`error.code` estable **sí se conserva** (es el atributo `code` de la
excepción), pero la **prosa pública** cae al mensaje genérico del status HTTP y
el servidor registra un `WARNING "HttpError no catalogado (code=%s status=%s)"`
en **cada** ocurrencia.

---

## 9. Veredicto por eje

| # | Eje exigido | Veredicto |
|---:|---|---|
| 1 | `settings/base.py` registra globalmente las apps de DOM-03…DOM-08 (incl. `competencias` y `patrocinadores`) | **FALLA** — 6 de 8 apps y 6 de 8 módulos de DI |
| 2 | `config/api.py` registra `PedidoController`, `InventarioController`, `CompetenciasController`, `PatrocinadorController` | **FALLA** — 0 de 4 (y 2 de ellos ni siquiera importables) |
| 3 | Registro de versiones del contrato | **FALLA** — falta `"competencias"` |
| 4 | Catálogo público de errores | **FALLA** — 33 de 78 códigos sin catalogar |
| 5 | Recolección de la raíz | **FALLA** — exit **2**, 725 collected + **6 errores de colección** |
| 6 | Puertas de migración / `check` | **PARCIAL** — verdes por defecto, **ciegas** para las dos apps no registradas |
| 7 | Guardián de registro / guardián OpenAPI | **FALLA de alineación** — verde hoy, **rojo reproducible** en cuanto se cablea |

**Conclusión:** la evidencia de runtime **NO pasa**. El estado de integración
de A0 **se conserva como BLOQUEANTE** (`A0-RTV-01`…`A0-RTV-05`), **re-confirmado
con prueba de ejecución** y **no se promueve a `completed`**.

---

## 10. Lo que esta pasada NO hace (y por qué)

| Acción | Motivo |
|---|---|
| **No** registrar `modules.competencias` / `modules.patrocinadores` en `INSTALLED_APPS` | `Aplicacion/backend/**` es raíz **prohibida** para esta pasada. El encargo dice: *«si la validación revela un cambio de código ausente, DETENERSE y reportarlo; no repararlo en esta pasada»*. |
| **No** registrar los cuatro controllers en `config/api.py` | Ídem. |
| **No** ampliar las listas del guardián (`APPS_DE_DOMINIO_COMPLETADAS`, `MODULOS_DE_DI_COMPLETADOS`, `CONTROLLERS_COMPLETADOS`, `PREFIJOS_PERMITIDOS`, `RUTAS_DE_DOMINIO_CONGELADAS`) | Ídem — y **deben ampliarse en el MISMO cambio** que el registro (R8/R9). |
| **No** añadir `"competencias"` a `SCHEMA_VERSIONS` | Ídem. |
| **No** catalogar los 33 códigos | Ídem. |
| **No** añadir el test de drift de `competencias` | Un test rojo no es evidencia: fallaría mientras el registro no exista. |
| **No** tocar `Aplicacion/backend/db.sqlite3` | Byproducto preexistente, `M` en el árbol. **SHA-256 verificado idéntico** antes y después de las puertas (G3). |
| **No** bajar de `completed` a DOM-05/DOM-07/DOM-08 | Sus **paquetes** están verdes y ejecutados; el bloqueo es del **cableado de A0**, que es una fila de estado distinta. Re-litigar la decisión de la reconciliación anterior sin evidencia nueva sería inventar alcance. |

---

## 11. Ficheros cambiados (2, ambos dentro de las raíces permitidas)

| Fichero | Acción | Qué |
|---|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/A0-wiring-validation.md` | **creado** | Este documento. |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | **modificado** | La fila de DOM-05/DOM-06/DOM-07/DOM-08 y la transición de esta validación. |

**Fuera del repositorio** (temporal, no versionado, **nada commiteado**):
`%TEMP%\opencode\a0_wiring_probe.py` · `%TEMP%\opencode\a0_catalog_probe.py` ·
`%TEMP%\opencode\a0_all_apps_overlay.py`.

**Cero** ficheros de `Aplicacion/backend/**` creados, modificados o borrados (G2).

---

## 12. Concurrencia preservada

- `git rev-parse HEAD` → `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit).
- El árbol traía **122 líneas** de cambios de otros agentes
  (`Aplicacion/backend/config/**`, `core/**`, `modules/{usuarios,marketplace,salesianos_fest,competencias,patrocinadores}/**`,
  `Aplicacion/frontend/**`): **no se tocaron, no se revertieron y no se fusionaron**.
- **Concurrencia ACTIVA durante la pasada:** otros agentes escribieron en
  `Aplicacion/frontend/src/features/{auth,inscripciones,pases,public,marketplace}/**`
  (mtimes 17:32–18:15, **simultáneos** a esta pasada) y en
  `evidence/ui/{UI-02,UI-03}-*.md` (17:41 / 17:48). **Ninguno de esos ficheros
  lo escribió esta pasada**; su `LastWriteTime` cae fuera de las dos únicas
  escrituras de esta pasada (`STATE.md` y este informe). `contract/**` y
  `Aplicacion/plan/**`: **sin tocar**.
- `git stash` · `git reset` · `git checkout` · `git commit`: **nunca invocados**.

---

## 13. Rollback

1. Borrar `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/A0-wiring-validation.md`.
2. Revertir la fila de DOM-05/DOM-06/DOM-07/DOM-08 y la transición de esta
   validación en `STATE.md` y en los topics de Engram
   (`sdd/salesianos-fest-rebuild/state` · `…/apply-progress`).
3. Los tres scripts de `%TEMP%\opencode\` se pueden borrar sin efecto.

**Punto de rollback:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit).

---

## 14. Próximo paso

**Un único paquete, y NO es un paquete de funcionalidad:** el **cableado global
de A0** (A0-RTV-01 → A0-RTV-05) sobre `Aplicacion/backend/config/**` +
`Aplicacion/backend/core/**`, en **un solo cambio coordinado**:

1. `settings/base.py`: añadir `modules.competencias` y `modules.patrocinadores`
   a `LOCAL_APPS` (respetando el grafo de migraciones: después de
   `modules.marketplace`) y sus dos módulos de DI a `INJECTOR_MODULES`.
2. `config/api.py`: registrar `PedidoController`, `InventarioController`,
   `CompetenciasController` y `PatrocinadorController` (**en ese orden**: el
   registro de las apps es el precondicito, §4).
3. `core/contract_versions.py`: registrar `SCHEMA_VERSIONS["competencias"] = "1.0.0"`.
4. `core/tests/integration/test_registration_extension.py`: ampliar **las cinco**
   listas cerradas en el **mismo** cambio.
5. `core/exceptions.py`: catalogar los **33** códigos públicos.
6. `modules/competencias/tests/`: añadir el test de drift equivalente al de
   `marketplace` (**después** del punto 3).

**Puertas de aceptación de ese paquete:** raíz `pytest --collect-only` exit **0**
· suite completa **833 collected → 833 passed** (0 fallos) ·
`manage.py check` y `makemigrations --check --dry-run` verdes en **overlay de las
ocho apps** y **en el registro permanente** · **24** rutas nuevas presentes en
el esquema OpenAPI.

**Consumers desbloqueados por ese paquete:** **API-03** · **API-05** · **XCT-01**
· **XCT-03** · **VER-01…VER-03** (y los espejos Zod 1:1 de DOM-03/05/06/07/08).

**Decisiones ABIERTAS que este paquete NO toca:** `H-01` ·
`PD-01`/`PD-02`/`GOV-01-OPEN-08` · `OD-DOM05-01`…`03` · `OD-DOM06-01` ·
`OD-DOM07-01`…`05` · `OD-DOM08-01`…`06` · `R-RTV-04` (datetimes sin `tzinfo`
en las fixtures de `competencias` — warning de las **fixtures**, no de la
lógica de dominio) · `A0-RTV-06` (`core.media` deja directorios vacíos) ·
`A0-RTV-07` (`*.sqlite3` en `.gitignore`) · `A0-RTV-08`
(`00-matriz-tareas.md` sin sincronizar).
