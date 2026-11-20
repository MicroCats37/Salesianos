# VER-03 — Evidencia de corte (cutover): endpoints antiguos/nuevos, smoke y disparador de rollback

**Paquete:** `VER-03-signoff-archive-cutover-cleanup` · **Cambio:** `salesianos-fest-rebuild` · **Proyecto:** Salesianos
**Fecha:** 2026-11-20 · **Complemento de:** [`../archive/VER-03-archive-report.md`](../archive/VER-03-archive-report.md)

---

## 1. Veredicto del corte

**NO-GO para el corte de producción en este entorno.** El objetivo está verde en código y el compose es válido,
pero **el corte no es ejecutable ni verificable aquí**: el demonio Docker está apagado, la **lane PostgreSQL**
—que `VER-02` §10.2 exige *antes* del corte de producción— no se pudo ejecutar, y el **objetivo del corte
(GAP-3) sigue sin decidir**. Además, el corte **retira 89 operaciones y sólo añade 57**, y **4 de las retiradas
no tienen contraparte en el destino**: eso es una decisión de producto, no de ingeniería.

---

## 2. Qué es "corte" en este cambio

El cambio reconstruye la aplicación en `Aplicacion/**` y deja las raíces `backend/**`, `frontend/**`,
`worker/**`, `proxy/**` como **referencia congelada de solo lectura**. El corte es, por tanto, **cambiar el
sistema servido de la raíz congelada al objetivo**. Los contextos de build del compose lo confirman: son
**relativos a `Aplicacion/`** (`context: .`, `context: frontend`, `context: worker/scraper`), de modo que el
compose de `Aplicacion/` **ya sirve el objetivo**, no la referencia.

| | Antes (sistema que se sirve hoy) | Después (objetivo) |
|---|---|---|
| Raíz servida | `backend/**` + `frontend/**` (congeladas) | `Aplicacion/backend/**` + `Aplicacion/frontend/**` |
| Compose | `docker-compose.yml` de la raíz | `Aplicacion/docker-compose.yml` |
| Estado en git | `f3df5401c56b41c340f257e67d5a306904a9e670` ("betha 4") + `2c411cd…` ("betha 6") | **sin commit**: el trabajo del rebuild vive en el árbol de trabajo y en el archivo G4 |

---

## 3. Comandos de corte: ejecutados, con resultado real

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| 1 | `docker compose config --quiet` | `Aplicacion` | **0** | compose válido: **el objetivo es construible en principio** |
| 2 | `docker compose up -d --build` | `Aplicacion` | **1** | **BLOQUEADO**: `open //./pipe/dockerDesktopLinuxEngine: El sistema no puede encontrar el archivo especificado` — el demonio Docker **no está corriendo**. **Ningún contenedor se levantó** |
| 3 | `docker compose ps --all` | `Aplicacion` | **1** | Ídem (misma causa). **No hay estado de contenedores que registrar** |
| 4 | `docker compose down` | `Aplicacion` | **1** | Ídem. **Nunca se usó `-v`** (prohibido: nunca se borran volúmenes) |

**Consecuencia:** el **smoke del despliegue** (peticiones reales contra el servicio containerizado) **no es
ejecutable en este entorno**. No se marca como verde: se declara **BLOQUEADO DE ENTORNO**, con dueño A0 + A9.
Lo que sí se ejecutó es el **smoke de runtime contra el objetivo** (§5), que es el mismo código que el
contenedor serviría.

---

## 4. Endpoints antiguos vs. nuevos (registro vivo, ejecutado)

Ambos inventarios se obtuvieron **ejecutando** `config.api.get_openapi_schema()` en cada raíz, con su propio
entorno, y **sin mutar** la raíz congelada (verificado: `backend/uv.lock` y `backend/db.sqlite3` con **hash
idéntico antes y después**; `git status --short -- backend` = **0 líneas**).

| Magnitud | **ANTES** (raíz congelada `backend/`) | **DESPUÉS** (objetivo `Aplicacion/backend/`) | Δ |
|---|---:|---:|---:|
| Operaciones vivas | **111** | **79** | **−32** |
| Operaciones públicas | 20 | **26** | +6 |
| Operaciones con JWT | 91 | **53** | −38 |
| Controllers registrados | 28 llamadas a `register_controllers` | **22** | −6 |

| Diff | Operaciones |
|---|---:|
| **Retiradas en el corte** | **89** |
| **Añadidas en el corte** | **57** |

### 4.1 Retiradas agrupadas

| Prefijo retirado | Ops | Lectura |
|---|---:|---|
| `/api/administracion/**` | 41 | panel CAM de `liquidaciones` (competencias, catalogos, accesos, acreditaciones) |
| `/api/inscripciones/**` | 10 | superficie antigua de inscripciones (frozen) |
| `/api/participaciones/**` | 6 | — |
| `/api/pases/**` | 6 | — |
| `/api/catalogo/**` | 5 | sustituida por `/api/catalogo/**` (nuevo) |
| `/api/compras/**` | 5 | sustituida por `/api/pagos/**` + `/api/inscripciones/**/compras/**` |
| `/api/asignaciones/**` | 4 | — |
| `/api/acreditaciones/**` | 3 | **sin contraparte** |
| `/api/equipos/**` | 3 | — |
| `/api/pagos/**` | 2 | sustituida por `/api/pagos/ordenes/{id}/confirmar` |
| `/api/acceso/registrar` | 1 | **sin contraparte** |
| `/api/competencias/**` | 1 | sustituida por `/api/competencias/**` (nuevo) |
| `/api/cotizaciones/**` | 1 | sustituida por `/api/cotizaciones` |
| `/api/personas/**` | 1 | sustituida por `/api/personas/{confirmar,resolver}` |

### 4.2 Las 4 retiradas **sin contraparte** (hallazgo de corte)

| Retirada | Qué capability se pierde | Estado en el destino |
|---|---|---|
| `POST /api/acceso/registrar` | **alta de cuenta de usuario** | El destino **tiene el servicio** (`modules/usuarios/domain/services/{core/registro_core_service,flujos/registro_flujo}.py`, `domain/schemas/registro_schemas.py`, test `test_auth_alta_cuenta.py`) pero **NO tiene ruta registrada** ⇒ el alta de cuenta **no esCallable** tras el corte |
| `GET /api/acreditaciones/{evento_id}/{persona_id}` | consulta de acreditación | ninguna |
| `POST /api/acreditaciones/{evento_id}/{persona_id}/generar-qr` | **generación de QR** | ninguna (`modules/validaciones` valida tickets, **no genera** acreditaciones) |
| `PATCH /api/acreditaciones/{evento_id}/{persona_id}/override-fiesta` | override de FIESTA | ninguna |

**Esto es un NO-GO de producto, no un defecto de código.** Tres salidas: (a) registrar las 4 rutas en el
destino, (b) aceptarlas formalmente como retiradas (son parte de la nada de CAM que el rebuild descarta), o
(c) un paquete nuevo que las reconstruya. **Dueño: A0 + producto.** **Este paquete no inventa política, ni
rutas, ni credenciales.**

### 4.3 Añadidas en el corte (57) — muestra por dominio

`/api/catalogo/{categorias,disciplinas,paquetes,promociones}` · `/api/ediciones/actual` ·
`/api/personas/{confirmar,resolver}` · `/api/inscripciones/**` (alta, copos, equipos, participantes) ·
`/api/cotizaciones` · `/api/pagos/ordenes/{id}/confirmar` · `/api/pases/**` (compras, lotes, beneficiarios) ·
`/api/marketplace/**` (categorías, productos, pedidos, seguimiento por token) ·
`/api/competencias/**` (competición, rondas, encuentros, cuadro, equipos elegibles, avances, correcciones) ·
`/api/validaciones/{preview,confirmar}` · `/api/administracion/**` (auditoría, equipos, personas, pagos, pases,
cortesías, marketplace/entregas, marketplace/inventario) · `/api/patrocinadores` ·
`/api/token/{pair,refresh,verify}` · `/api/admin…`

---

## 5. Smoke de runtime contra el objetivo (ejecutado)

Cliente de pruebas de Django sobre el objetivo (`config.settings.test`), **sin** depender de Docker.

| # | Sonda | Esperado | Medido | Veredicto |
|---:|---|---|---|---|
| 1 | `GET /api/catalogos/paquetes` (público) | 200 ó 404 | **404** | ✅ (no hay edición publicada en la BD de prueba) |
| 2 | `GET /api/inscripciones/{uuid}` (con JWT) | **401** | **401** · `code=AUTHENTICATION_REQUIRED` | ✅ |
| 3 | `GET /api/administracion/auditoria` (con JWT) | **401** | **401** · `code=AUTHENTICATION_REQUIRED` | ✅ |
| 4 | Forma de la envoltura congelada (`FR-01` §4) en el cuerpo 401 | `success`/`data`/`error`/`message` | `success=False`, `data=None`, `error{code,message}`, `message` presente | ✅ |
| 5 | Fuga de internals en el cuerpo de denegación | 0 | **0** (`Traceback`, `/api/`, `SELECT `, `sqlite3`, `SECRET_KEY`) | ✅ |
| 6 | `POST /api/token/refresh` | 400/401 | **400** · claves `['code','detail','refresh']` | ⚠️ **envoltura de biblioteca, no la congelada** |
| 7 | `POST /api/token/pair` | 400/401 | **400** · claves `['code','detail','password','username']` | ⚠️ **envoltura de biblioteca** |
| 8 | `POST /api/token/verify` | 400/401 | **401** · claves `['data','error','message','success']` | ✅ (envoltura congelada) |

**Sondas 6 y 7 ⇒ `V-02-SEC-02` sigue ABIERTO y confirmado por medición**, no por cita: 2 de las 3 rutas de
`/api/token/**` (`ninja_jwt`) responden con `{"detail":…,"code":…}` en lugar de la envoltura congelada.
Severidad **BAJA** (inconsistencia de contrato, no de seguridad). Dueño **A0** (es un controller de terceros:
sustituirlo es una decisión de arquitectura). **No se cambió** — cambiar un controller de biblioteca es una
decisión de A0 fuera de las raíces de este paquete.

---

## 6. Condiciones previas al corte que NO están verdes

| # | Condición | Estado | Dueño | Efecto |
|---:|---|---|---|---|
| 1 | **Lane PostgreSQL** (`BL-05` §2) ejecutada con bloqueo de filas | 🔴 **NO EJECUTADA** | A0 + A9 | La serialización real (`QA-V02`, `QA-I05`, `RN-C02` precio-vs-cotización) **sigue sin probarse**; `VER-02` §4.3 la declara bloqueada por entorno (Docker apagado + `OperationalError` con las credenciales del compose) |
| 2 | **Techo de Biome** (105/93 congelado vs **445/110** actual) | 🔴 **ROJO** | A0 + A7 | Bloquea la **firma** (no el corte). Es **deuda heredada** de todo el frontend del rebuild: en los 29 ficheros tocados por las correcciones de VER-01 el recuento **bajó** de 45 a 38; el resto es trabajo concurrente |
| 3 | **Pasada de navegador a 5 anchos** (360/390/768/1024/1440) + barrido de axe + lector de pantalla | 🔴 **NO EJECUTADA** | A9 + A7 | Bloquea la **firma de UX**. `node_modules/@playwright`, `playwright`, `puppeteer`, `axe-core`, `jest-axe`, `vitest-axe` **no existen** y la instalación está prohibida |
| 4 | **Decisión del objetivo del corte (GAP-3)** | 🔴 **ABIERTA** | A0 + producto | Sin destino nombrado no hay "corte" que ejecutar ni rollback que declarar |
| 5 | **Rutas de producto retiradas sin contraparte** (§4.2) | 🔴 **SIN DECISIÓN** | A0 + producto | 4 capabilities (alta de cuenta, generación de QR, override de FIESTA, consulta de acreditación) |
| 6 | **Firma de producto / A0** | 🟡 **PENDIENTE** | Producto + A0 | Sin firma no hay corte |
| 7 | **Proveedor SMTP** (`PD-08`, diferido por el plan) | 🟡 **DIFERIDO** | A0 + producto | No bloquea el corte; **no puede presentarse como implementado** (`implementacion/03` §5) |

---

## 7. Disparador y procedimiento de rollback

**Disparadores:** fallo del smoke del despliegue · fallo de un caso crítico de QA · fuga de datos o de permisos
en el despliegue · rechazo del producto del corte (GAP-3) · o cualquier retreat de superficie no autorizada.

**Procedimiento (probado, salvo el paso 6 que requiere Docker):**

1. `docker compose down` — **nunca `-v`**.
2. Dejar **intacta** la evidencia (`evidence/archive/**`, `evidence/cutover/**`, la transición de `STATE.md`).
3. Restaurar el artefacto de producto desde el archivo G4 (comando literal en
   [`../archive/VER-03-archive-report.md`](../archive/VER-03-archive-report.md) §8.2) y **verificar el hash**
   contra `evidence/archive/ARCHIVE-MANIFEST.csv`.
4. Revertir a `f3df5401c56b41c340f257e67d5a306904a9e670` ("betha 4") por ruta explícita — **nunca `reset`**
   sobre ese commit, **nunca `git stash`**.
5. **Detener la limpieza** (no borrar, no mover, no podar) mientras el rollback esté en curso.
6. Re-desplegar la referencia anterior (`docker compose up -d --build` en la raíz anterior).
7. Registrar el rollback en `STATE.md` y en Engram (`sdd/salesianos-fest-rebuild/state`).

**Prueba de que el paso 3 funciona:** ejecutada en §4.5 del informe de archivo — fichero extraído del ZIP,
re-hasheado, **hash idéntico al manifiesto ⇒ PASS**.

---

## 8. Lo que este paquete NO hizo (declaración explícita)

| No hecho | Por qué |
|---|---|
| **No levantó contenedores** | el demonio Docker no está corriendo |
| **No ejecutó la lane PostgreSQL** | no hay PostgreSQL configurado ni Docker; es **bloqueo de entorno** |
| **No ejecutó la pasada de navegador a 5 anchos** | no hay motor de render y la instalación está prohibida |
| **No cambió `docker-compose.yml`** | raíz compartida propiedad de A0; además el hallazgo del `DB_PASSWORD` por defecto **exige** su decisión, no la suya |
| **No registró ni desregistró ninguna ruta** | A0 es dueño exclusivo de `config/api.py` |
| **No corrigió `V-02-SEC-01`** | el código `INSCRIPCION_NO_AUTORIZADA` está **congelado** en `FR-03` §2.1; neutralizarlo exige enmienda de contrato (GAP-2) |
| **No eliminó ninguna ruta** | G1 y G3 rojas (§3 del informe de archivo) |
