# FR-01 — Envelope único de respuesta, error y paginación

**Freeze:** `FREEZE-ENV-1.0.0` · **Propietario:** A0 · **Estado:** FROZEN (GOV-01) · **Fecha:** 2026-11-18
**Alcance:** toda ruta HTTP del objetivo (`Aplicacion/backend`) y su espejo en `Aplicacion/frontend`.

---

## 1. Fuentes leídas

| Fuente | Aporte |
|---|---|
| `contract/api-wrapper-presenter-contract.md` §2, §5, §6, §7, §8 | wrapper tipado por módulo; sin `data`/`contexto` genérico; espejo 1:1 con Zod; catálogo público de errores; categorías HTTP |
| `contract/SCHEMA_DRY_INTENTION.md` | composición de schemas en 3 bloques (general / específico / identidad); prohibición de schemas monolíticos por endpoint |
| `contract/django-app-architecture-contract.md` §7 | `success_response()` de `core.responses`; el controller nunca construye respuestas de error |
| `Aplicacion/plan/salesianos-fest-rebuild/contratos/01-api-wrappers-presenters.md` §1–§8 | envelope propuesto `[PROPUESTO]`, `error.field_errors`, presenters de ejemplo, `acciones_disponibles`, contratos de estado, validación runtime |
| `.opencode/skills/salesianos-api-data/references/api-data-contract.md` | forma del envelope, forma paginada, 204, política de caché y query keys |
| `Aplicacion/documentacion/02a-inventario-de-endpoints.md` | inventario de 111 rutas registradas y sus wrappers declarados |

## 2. Estado actual verificado (código congelado, solo lectura)

Verificado por lectura directa del código en `backend/`:

| Artefacto | Ubicación | Forma real |
|---|---|---|
| `ApiResponse[T]` | `backend/core/responses.py:34-43` | `{ success: bool, data: T \| null, error: ErrorDetail \| null, message: str \| null }` |
| `ErrorDetail` | `backend/core/responses.py:26-31` | `{ code: str, message: str, details: dict \| null }` |
| `PaginationMeta` | `backend/core/responses.py:46-52` | `{ page, page_size, total, total_pages }` |
| `PaginatedApiResponse[T]` | `backend/core/responses.py:55-65` | `{ success, data: list[T], error, message, meta }` — **paginación fuera de `data`** |
| `PaginatedData[T]` | `backend/core/pagination.py:13-37` | `{ items: list[T], total, page, page_size, total_pages }` — **paginación dentro de `data`** |
| `success_response()` | `backend/core/responses.py:68-86` | `{ success: True, data, error: None, message }` |
| `error_response()` | `backend/core/responses.py:89-101` | `{ success: False, data: None, error: { code, message, details } }` |
| `format_errors()` | `backend/core/utils.py:96-111` | `dict[str, str]` plano `campo → mensaje`; `non_field_errors` para errores de formulario |
| `humanize_validation_errors()` | `backend/core/utils.py:122-174` | une el dict plano en un único mensaje legible |

Uso real de las dos formas de paginación (inventario 02a):

- `ApiResponse[PaginatedData[X]]` — 13 rutas de administración (`GET /api/administracion/inscripciones`, `/accesos`, `/acreditaciones`, `/equipos`, `/participaciones`, `/participantes`, `/pagos`, `/usuarios`, …).
- `ApiResponse[list[X]]` — 20+ rutas de dominio sin paginación (catálogo, pases, competencias, equipos,…).
- `PaginatedApiResponse[T]` — declarado en `core/responses.py` pero **no usado por ninguna ruta registrada**.

## 3. Contradicciones detectadas y su resolución

| ID | Contradicción | Origen A | Origen B | Resolución GOV-01 |
|---|---|---|---|---|
| `C-ENV-01` | Forma de la paginación | `PaginatedData` (dentro de `data`) — `core/pagination.py` | `PaginatedApiResponse` + `meta` (fuera de `data`) — `core/responses.py` | **Resuelta** — se congela una sola forma: `data: { items, total, page, page_size, total_pages }`. `PaginatedApiResponse` queda **deprecada** en el objetivo. |
| `C-ENV-02` | Canal de error de campo | `error.details` = `dict[str, str]` plano — `core/responses.py` | `error.field_errors` = lista — plan `contratos/01` §2 | **Resuelta** — conviven dos canales **ortogonales y sin solapamiento**: `details` solo contexto no-campo; `field_errors` lista tipada es el **único** canal de error por campo. |
| `C-ENV-03` | Cliente de prueba HTTP | `TEST_ARCHITECTURE_CONTRACT.md` §2/§10.5 → `ninja.testing.TestClient` | `django-app-architecture-contract.md` §2.1 → `ninja_extra.testing.TestAsyncClient` o `django.test.Client` | **Resuelta operativamente / abierta documentalmente** — ver §7 de este documento y `GOV-01-OPEN-01` en `FR-09`. |

## 4. Decisión congelada — UN envelope

### 4.1 Éxito

```json
{
  "success": true,
  "data": { },
  "error": null,
  "message": "La operación se completó correctamente."
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `success` | `boolean` | siempre `true` |
| `data` | `T \| null` | payload del caso de uso. `null` solo si el caso de uso no tiene payload |
| `error` | `null` | siempre `null` en éxito |
| `message` | `string \| null` | mensaje fijo y contextual declarado por el controller. **Prohibido** interpolar ids, UUIDs, montos o texto técnico (`api-wrapper-presenter-contract.md` §8) |

### 4.2 Error

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Revisa los datos ingresados.",
    "details": { "non_field_errors": "La edición indicada no admite amendments." },
    "field_errors": [
      { "field": "email", "code": "INVALID_FORMAT", "message": "El correo no tiene un formato válido." }
    ]
  },
  "message": null
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `error.code` | `string` | **obligatorio**, estable y legible por máquina. Vive en `core/exceptions.py` (`PUBLIC_ERROR_MESSAGES`). Único origen: la excepción de dominio. Nunca se construye en el controller |
| `error.message` | `string` | **obligatorio**, prosa pública en español, sourced del catálogo. Nunca contiene UUIDs, ids internos, texto crudo de excepción, SQL, trazas, rutas, payloads del proveedor ni secretos |
| `error.details` | `object \| null` | contexto **no-campo** y opcional. Ej.: `{ "non_field_errors": "…" }`. **Prohibido** usarlo como canal de errores por campo |
| `error.field_errors` | `array \| null` | **único** canal de error por campo. Cada entrada: `{ field, code, message }` |
| `error.field_errors[].field` | `string` | ruta del campo. Anidado con punto: `beneficiarios.0.documento`. `non_field_errors` para error de formulario |
| `error.field_errors[].code` | `string` | código estable del error de campo. Por defecto `INVALID_VALUE`; el dominio puede fijar uno propio |
| `error.field_errors[].message` | `string` | prosa pública segura del error de campo |
| `message` (raíz) | `null` | siempre `null` en error |

**Regla de conversión desde el código congelado.** El `details` plano `campo → mensaje` que produce hoy `format_errors()` se convierte en la frontera de error: cada clave se transforma en una entrada de `field_errors`; `non_field_errors` permanece en `details`. Esta conversión es responsabilidad de `core/exceptions.py` (A0), no de cada controller.

### 4.3 Paginación (forma única)

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 25,
    "total_pages": 0
  },
  "error": null,
  "message": null
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `data.items` | `T[]` | puede estar vacío; nunca `null` |
| `data.total` | `integer` | total de filas **antes** de paginar |
| `data.page` | `integer` | **base 1**. Por defecto `1` |
| `data.page_size` | `integer` | por defecto `25`, máximo `100` |
| `data.total_pages` | `integer` | `ceil(total / page_size)`; `0` cuando `total == 0` |

**Reglas de transición (obligatorias, owners indicados):**

1. `PaginatedApiResponse[T]` + `meta` queda **deprecada** en el objetivo. Ninguna ruta nueva la usa. — Owner A0 (`core/responses.py`).
2. Las 13 rutas `ApiResponse[PaginatedData[X]]` de administración **ya cumplen** la forma congelada. No se tocan. — Owner A0.
3. Las rutas de dominio que hoy devuelven `ApiResponse[list[X]]` sin paginación **deben** adoptar `PaginatedData` cuando expongan listados navegables. La conversión de los listados que no son paginados (catálogo público) se decide en FND-01 y no bloquea este freeze. — Owner A0 + A7.
4. El frontend **no** debe mantener un segundo tipo de paginación. El `meta` queda fuera del espejo Zod del objetivo. — Owner A7 (FND-08).

### 4.4 204 y códigos de estado

| Resultado | Comportamiento congelado |
|---|---|
| `204 No Content` | cuerpo vacío. **Prohibido** parsear `data` o `message`. El cliente no debe intentar leer el cuerpo |
| `200` | éxito con payload |
| `201` | creación con payload |
| `400` | petición malformada no atribuible a validación de campo |
| `401` | `AUTHENTICATION_REQUIRED` |
| `403` | `ACTION_NOT_ALLOWED` / `ADMIN_REQUIRED` |
| `404` | `RESOURCE_NOT_FOUND` / código específico del dominio |
| `409` | conflicto de negocio o de versión (`RESOURCE_CHANGED`) |
| `422` | validación; **debe** traer `field_errors` |
| `500` | `INTERNAL_ERROR` con mensaje genérico; el detalle técnico solo va al log |

`code` es para diagnóstico y mapeo. **Prohibido** ramificar la UI únicamente por `code`: se ramifica por status HTTP y, cuando el mensaje deba ser específico, por `code` **junto con** el status.

## 5. `estado_operativo` — veredicto operativo legible

El plan (`contratos/01` §3, §4, §7) exige un estado comprensible, y la auditoría (`03b` líneas 308–320, 966) documenta que el backend **ya** calcula `estado_operativo` y que la UI **no expone el filtro**, que es el más útil para el operador.

### 5.1 Forma congelada

```json
{
  "codigo": "PAGADA_SIN_EVIDENCIA",
  "etiqueta": "Pagada sin evidencia",
  "descripcion": "El pago figura como pagado pero no hay evidencia verificable asociada."
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `codigo` | `string` | código estable de máquina, propiedad del módulo dueño del veredicto. **No se renumera** el vocabulario existente |
| `etiqueta` | `string` | etiqueta corta en español. **Prohibido** usar el código como etiqueta primaria de UI |
| `descripcion` | `string` | una línea con la causa y el siguiente paso seguro |

### 5.2 Vocabulario congelado para pagos

Se conserva el vocabulario vivo `EstadoOperativoPago` (`backend/modules/pagos/domain/constants.py:23-52`), **sin renumerar**:

`SIN_ORDEN` · `PAGADA` · `PAGADA_SIN_LIQUIDAR` · `PAGADA_SIN_EVIDENCIA` · `PAGADA_SIN_FECHA` · `PENDIENTE` · `CANCELADA` · `VENCIDA`

Propietario del veredicto: `pagos` (`EstadoOperativoPagoService` es el **único** dueño). Ninguna otra superficie recalcula el veredicto comparando hechos hermanos.

### 5.3 Reglas de uso

1. El frontend **nunca** deriva el veredicto cruzando `Compra.estado`, `OrdenPago.estado` y banderas locales (`contratos/01` §1.4, `RN-C07`).
2. `acciones_disponibles` es una **proyección UX** del estado de lectura. No es una frontera de seguridad: toda mutación revalida en backend (`contratos/01` §6, `RN-A01`).
3. El filtro `estado_operativo` debe quedar **expuesto** en la UI de pagos administrativos. La capacidad de filtrado ya existe en backend (`02b` línea 1340); la brecha es de UI. — Owner A7 (API-04), criterio de aceptación derivado de `03b` línea 966.
4. "Liquidación", `settlement`, `captured` y UUIDs del proveedor **no** son etiquetas de UI (DEC-20, `RN-C07`).

## 6. Composición de schemas (`SCHEMA_DRY_INTENTION`)

Todo schema HTTP del objetivo se compone de los tres bloques del contrato, sin excepción:

| Bloque | Contenido | Nombre de convención en el objetivo |
|---|---|---|
| General | campos compartidos por la entidad | `XxxBase` |
| Específico | lo que varía por caso de uso | `XxxDetalle`, `XxxCreate`, `XxxListado` |
| Identidad | ids, timestamps, uuid de auditoría | `XxxIdentity` o bloque `identidad` dentro del schema final |

**Prohibido** schemas monolíticos independientes por endpoint. **Prohibido** `z.any()` en el espejo frontend. **Prohibido** el envelope genérico `data: Any` / `contexto: dict` dentro de un wrapper (`api-wrapper-presenter-contract.md` §5).

## 7. Cliente de prueba HTTP — resolución

### 7.1 Evidencia verificada

| Hecho | Ubicación verificada |
|---|---|
| `config.api.api` es un `NinjaExtraAPI` | `backend/config/api.py:6,75,84,94` — 28 llamadas `register_controllers` |
| 23 de 24 archivos de controller usan `async def` | `backend/modules/*/presentation/controllers/*.py` — única excepción `usuarios/.../me_controller.py:53` |
| `ninja.testing.TestClient._call` es **síncrona**: `NinjaResponse(func(request, **kwargs))` | `backend/.venv/.../ninja/testing/client.py:189-191` |
| `ninja.testing.TestAsyncClient._call` **espera** la corrutina | `ninja/testing/client.py:194-198` |
| `ninja_extra.testing.TestClient._call` es **síncrona** | `ninja_extra/testing/client.py:69-71` |
| `ninja_extra.testing.TestAsyncClient._call` **espera** la corrutina | `ninja_extra/testing/client.py:74-76` |
| La fixture compartida `usuarios_fixtures.api_client` usa `ninja.testing.TestClient(api)` | `backend/modules/usuarios/tests/fixtures/usuarios_fixtures.py:14,25` |
| `TEST_ARCHITECTURE_CONTRACT.md` §10.2 obliga a **copiar verbatim** esa fixture | `contract/TEST_ARCHITECTURE_CONTRACT.md:308` |
| Clientes en uso real hoy: `django.test.Client`, `ninja.testing.TestClient`, `ninja_extra.testing.TestAsyncClient` | `backend/conftest.py:40,69,86`; `backend/modules/competencias/tests/**` |

Consecuencia verificada: con controllers `async def`, el cliente síncrono `ninja.testing.TestClient` recibe una corrutina y `NinjaResponse.__init__` lee `http_response.status_code` sobre esa corrutina → `AttributeError: 'coroutine' object has no attribute 'status_code'`. Es exactamente el fallo que documenta `django-app-architecture-contract.md` §2.1.

### 7.2 Decisión congelada — `FREEZE-TC-1.0.0`

**Cliente de prueba obligatorio para el objetivo, por tipo de controller:**

| Tipo de controller | Cliente | Test |
|---|---|---|
| `async def` (regla por defecto del proyecto) | `ninja_extra.testing.TestAsyncClient(api)` | `async def` + `asyncio_mode="auto"` |
| `async def` (alternativa permitida) | `django.test.Client` | `def` normal |
| `def` síncrono | `ninja_extra.testing.TestClient(api)` o `ninja.testing.TestClient(api)` | `def` normal |

**Prohibido**, sin excepción: `ninja.testing.TestClient` y `ninja_extra.testing.TestClient` contra un controller `async def`.

**Precedencia aplicada.** `django-app-architecture-contract.md` §2.1 registra una decisión de usuario explícita y fechada (2026-08-27) que describe la arquitectura async verificada en el código; `TEST_ARCHITECTURE_CONTRACT.md` §2/§10.5 data de antes y no contempla `NinjaExtraAPI` con controllers async. Ante contratos del **mismo** nivel normativo, el global apply contract ordena registrar la decisión rectora antes de la implementación con tests, y la evidencia del código respalda la regla async. Por eso la decisión operativa es la de §7.2.

**Lo que esta decisión NO hace.** No modifica ningún archivo de `contract/`. La contradicción documental permanece abierta como `GOV-01-OPEN-01` (`FR-09`): una enmienda explícita a `TEST_ARCHITECTURE_CONTRACT.md` §2 y §10.5 que reconozca `NinjaExtraAPI` y `TestAsyncClient` sigue siendo necesaria y pertenece a GAP-2 (A0 + producto). La decisión de §7.2 **desbloquea** la implementación con tests; no ratifica el texto del contrato.

**Deuda que la decisión expone.** `backend/modules/usuarios/tests/fixtures/usuarios_fixtures.py:25` es la fixture que `TEST_ARCHITECTURE_CONTRACT.md` §10.2 manda a copiar verbatim, y usa un cliente síncrono sobre una API con controllers async. En el objetivo esa fixture debe reescribirse con `TestAsyncClient` y su copia por módulo (`FND-01`, owner A0 + A1). El texto del contrato que obliga a copiarla verbatim debe alinearse en `GOV-01-OPEN-01`.

## 8. Reglas para el espejo Zod (frontend)

1. Cada wrapper consumido tiene un **espejo Zod exacto** en el feature dueño. Sin `z.any()`, sin `z.unknown()` como sustituto, sinIgnorar campos.
2. El espejo declara la versión del schema del backend: `export const SCHEMA_VERSION = "1.0.0"`. La coincidencia con el registro de versiones del backend se verifica en un test de contrato (ver `FR-07`).
3. `success` se lee de la raíz; `message` de `response.message`; el texto de error de `error.message`; el detalle de campo de `error.field_errors[]`.
4. `204` → no parsear cuerpo.
5. La **forma** del envelope no se replica por módulo: existe un solo `apiResponseSchema` / `paginatedResponseSchema` compartido, parametrizado por el schema del payload.
6. Ningún schema del frontend calcula precio, elegibilidad, cupo, capacidad, estado de pago, stock ni permiso (`00-contrato-global-de-apply.md`, prohibiciones).

## 9. Criterios de aceptación de este freeze

- [x] Una sola forma de éxito, una sola forma de error, una sola forma de paginación, con reglas de deprecación explícitas.
- [x] `field_errors` definido como canal único de error por campo, sin romper `details`.
- [x] `estado_operativo` congelado con `codigo` / `etiqueta` / `descripcion` y vocabulario de pagos sin renumerar.
- [x] `EVENTO_ACTIVO_NOMBRE` **no** aparece como supuesto de scope (ver `FR-02`).
- [x] La contradicción del cliente de prueba tiene decisión rectora **y** estado documental abierto, sin tocar `contract/`.
- [x] La composición de schemas conforme a `SCHEMA_DRY_INTENTION` queda obligatoria.
