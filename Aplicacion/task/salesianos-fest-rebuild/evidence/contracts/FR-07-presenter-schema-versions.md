# FR-07 — Versiones de presenters/schemas y ledger ruta → wrapper

**Freeze:** `FREEZE-PS-1.0.0` · **Propietario:** A0 (registro) + A7 (espejo frontend) · **Estado:** FROZEN (GOV-01)
**Trazabilidad:** `contract/api-wrapper-presenter-contract.md` §7, §9 · `contract/django-app-architecture-contract.md` §4.7, §4.9, §5 · plan `contratos/01` §5, §8

---

## 1. Reglas de versionado congeladas

### 1.1 Dónde vive la versión

La versión **no** es un campo del wire. Es un **registro** que A0 mantiene y que ambos lados declaran.

| Elemento | Ubicación en el objetivo | Owner |
|---|---|---|
| Registro global de versiones | `Aplicacion/backend/core/contract_versions.py` | A0 |
| Versión del envelope | `ENVELOPE_VERSION` en el mismo archivo | A0 |
| Versión por módulo | `modules/<modulo>/presentation/schemas/__init__.py` → `SCHEMA_VERSION` | Dueño del módulo |
| Presenter asociado | `modules/<modulo>/presentation/presenters/<modulo>_presenter.py` | Dueño del módulo |
| Espejo frontend | `features/<dominio>/schemas/<dominio>.schema.ts` → `export const SCHEMA_VERSION` | A7 |

### 1.2 Semántica

| Cambio | Versión | Ejemplo |
|---|---|---|
| Se **elimina** o **renombra** un campo, se cambia su tipo, se elimina un endpoint o un wrapper | **MAJOR** | `1.0.0` → `2.0.0` |
| Se **agrega** un campo opcional, un endpoint nuevo, un wrapper nuevo | **MINOR** | `1.0.0` → `1.1.0` |
| Corrección editorial, mensaje público, documentación | **PATCH** | `1.0.0` → `1.0.1` |

**Prohibido** subir de versión sin que el cambio corresponda a la categoría. **Prohibido** un cambio MAJOR sin actualizar **todos** los espejos Zod en el mismo trabajo.

### 1.3 Detección de drift (obligatoria)

| Regla | Detalle |
|---|---|
| Visibilidad | Un drift de contrato debe ser **visible y testeable** (`contratos/01` §8) |
| Test | Un test de contrato compara la versión declarada en el espejo Zod con la del registro del backend y falla si difieren |
| Efecto | Un fallo de este test **bloquea** el merge del módulo afectado |
| 1:1 | Todo wrapper consumido tiene un espejo Zod exacto. **Prohibido** `z.any()` |

## 2. Versiones congeladas en GOV-01

| Artefacto | Versión | Estado |
|---|---|---|
| Envelope (éxito / error / paginación) | `ENVELOPE_VERSION = "1.0.0"` | FROZEN — `FR-01` |
| `eventos` (ediciones) | `SCHEMA_VERSION = "1.0.0"` | FROZEN — `FR-02` |
| `usuarios` (personas, cuentas, titularidad) | `SCHEMA_VERSION = "1.0.0"` | FROZEN — `FR-03` |
| `commerce` (compras) | `SCHEMA_VERSION = "1.0.0"` | FROZEN — `FR-04` |
| `pagos` (órdenes, transacciones, veredicto) | `SCHEMA_VERSION = "1.0.0"` | FROZEN — `FR-04`, `FR-01` §5.2 |
| `pases` / `beneficios` (derechos) | `SCHEMA_VERSION = "1.0.0"` | FROZEN — `FR-05` |
| `validaciones` (preview / confirm) | `SCHEMA_VERSION = "1.0.0"` | FROZEN — `FR-05` |
| `marketplace` / `patrocinadores` (media) | `SCHEMA_VERSION = "1.0.0"` | FROZEN — `FR-06` |

## 3. Ledger ruta → wrapper

### 3.1 Reglas de lectura del ledger

1. El ledger describe **rutas propuestas del objetivo**, no las 111 rutas actuales. Esas se leen en `Aplicacion/documentacion/02a-inventario-de-endpoints.md`.
2. Una ruta del ledger **no existe** hasta que su controller está registrado en `Aplicacion/backend/config/api.py`. El registro es decisivo: código escrito y no registrado es código muerto (`02a` §5, `api-data-contract` "Endpoint Authority").
3. Cada fila declara `provisional = sí|no`. Una ruta provisional **no** puede consumir `PROVISIONAL_CONTRACT_FIXTURE` como si fuera real.
4. El ledger **no** autoriza rutas fuera de las owners nombradas en la columna `owner`.
5. Copia legible: `route-to-wrapper-ledger.csv` (mismo contenido, ordenable).

### 3.2 Columnas

`id_ruta` · `metodo` · `ruta_propuesta` · `modulo_dueno` · `presenter` · `wrapper_respuesta` · `schema_entrada` · `errores` · `status` · `scope_edicion` · `permiso` · `freeze` · `provisional` · `owner`

### 3.3 Ledger

| id_ruta | método | ruta propuesta | módulo | presenter | wrapper respuesta | schema entrada | errores (código → status) | scope edición | permiso | freeze | provisional | owner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `RT-ED-01` | GET | `/ediciones/actual` | `eventos` | `EdicionPresenter` | `EdicionActualOut` | — | `EDICION_NO_PUBLICADA` → 404 · `EDICION_AMBIGUA` → 409 · `EDICION_NO_RESUELTA` → 404 | implícito (resolución) | público | `FREEZE-ED` | sí | A1 |
| `RT-ED-02` | GET | `/ediciones/{edicion_id}/catalogo` | `eventos` | `CatalogoEdicionPresenter` | `CatalogoEdicionOut` | — | `EDICION_NO_ENCONTRADA` → 404 | path | público | `FREEZE-ED` | sí | A1 |
| `RT-ID-01` | GET | `/personas/busqueda/{documento}` | `usuarios` | `PersonaBusquedaPresenter` | `DocumentoConsultaOut` | — | `PERSONA_NO_ENCONTRADA` → 404 | no | público | `FREEZE-ID` | sí | A1 |
| `RT-ID-02` | POST | `/personas/resolver` | `usuarios` | `PersonaResolverPresenter` | `PersonaResueltaOut` | `PersonaResolverIn` | `PERSONA_NO_ENCONTRADA` → 404 · `FUENTE_EXTERNA_NO_DISPONIBLE` → 503 | no | autenticado | `FREEZE-ID` | sí | A1 |
| `RT-ID-03` | POST | `/personas/confirmar` | `usuarios` | `PersonaConfirmarPresenter` | `PersonaOut` | `PersonaConfirmarIn` | `PERSONA_DUPLICADA` → 409 · `TIPO_DOCUMENTO_INVALIDO` → 422 | no | autenticado | `FREEZE-ID` | sí | A1 |
| `RT-CM-01` | POST | `/inscripciones/{inscripcion_id}/compras/cupos` | `inscripciones` | `CompraCuposPresenter` | `CompraCreadaOut` | `ComprarCuposIn` | `COMPRA_NO_AUTORIZADA` → 403 · `PAQUETE_NO_VIGENTE` → 409 · `CUPO_INVALIDO` → 422 | path | `TITULARIDAD_RESPONSABLE` | `FREEZE-CM` | sí | A3 |
| `RT-CM-02` | POST | `/pases/compras` | `pases` | `CompraPasePresenter` | `CompraPaseCreadaOut` | `ComprarPaseIn` | `PASE_NO_DISPONIBLE` → 409 · `CANTIDAD_INVALIDA` → 422 | implícito | autenticado o invitado | `FREEZE-CM` | sí | A4 |
| `RT-CM-03` | POST | `/marketplace/pedidos` | `marketplace` | `PedidoPresenter` | `PedidoCreadoOut` | `CrearPedidoIn` | `PRODUCTO_NO_DISPONIBLE` → 409 · `STOCK_INSUFICIENTE` → 409 | implícito | autenticado o invitado | `FREEZE-CM` | sí | A5 |
| `RT-PG-01` | POST | `/pagos/ordenes/{orden_id}/confirmar` | `pagos` | `PagoConfirmadoPresenter` | `PagoConfirmadoOut` | `ConfirmarPagoIn` | `PAGO_FIRMA_INVALIDA` → 400 · `PAGO_DATOS_INCONSISTENTES` → 409 · `MONTO_NO_COINCIDE` → 409 · `ORDEN_YA_PAGADA_CON_IZIPAY` → 409 | implícito | `TITULARIDAD_COMPRADOR` | `FREEZE-CM` | sí | A2 |
| `RT-PG-02` | POST | `/pagos/izipay/notificacion` | `pagos` | `PagoNotificacionPresenter` | `PagoConfirmadoOut` | — | `PAGO_FIRMA_INVALIDA` → 400 · `PAGO_NOTIFICACION_NO_VERIFICABLE` → 400 | no | servidor-a-servidor (firma) | `FREEZE-CM` | sí | A2 |
| `RT-PG-03` | GET | `/pagos/ordenes/{orden_id}` | `pagos` | `OrdenPagoPresenter` | `OrdenPagoOut` | — | `ORDEN_PAGO_NO_ENCONTRADA` → 404 | implícito | `TITULARIDAD_COMPRADOR` | `FREEZE-CM` | sí | A2 |
| `RT-PG-04` | GET | `/administracion/pagos` | `administracion` | `AdminPagoPresenter` | `PaginatedData[AdminPagoListItemOut]` | query: `page`, `page_size`, `q`, `ordering`, `estado_operativo`, `estado_compra`, `estado_orden`, `tipo`, `desde`, `hasta` | `ACTION_NOT_ALLOWED` → 403 | path o `edicion_id` | `Administrador` | `FREEZE-ENV` | sí | A0 + A7 |
| `RT-PG-05` | POST | `/administracion/pagos/{orden_pago_id}/aprobar-manual` | `administracion` | `AdminPagoManualPresenter` | `AdminPagoAprobarManualOut` | `AprobarPagoManualIn` | `PAGO_MANUAL_APROBACION_DESHABILITADA` → 409 · `MONTO_NO_COINCIDE` → 409 · `ORDEN_YA_PAGADA_CON_IZIPAY` → 409 · `COMPRA_YA_CANCELADA` → 409 | implícito | `Administrador` + capacidad de aprobación | `FREEZE-CM` | sí | A0 |
| `RT-RT-01` | POST | `/validaciones/preview` | `validaciones` | `TicketPreviewPresenter` | `TicketPreviewOut` | `PreviewTicketIn` | `TICKET_NO_ENCONTRADO` → 404 · `ACTION_NOT_ALLOWED` → 403 | implícito | operador autenticado | `FREEZE-RT` | sí | A8 |
| `RT-RT-02` | POST | `/validaciones/confirmar` | `validaciones` | `TicketConfirmPresenter` | `TicketConfirmadoOut` | `ConfirmarTicketIn` (incluye `idempotency_key`) | `TICKET_YA_CONSUMIDO` → 409 · `CANTIDAD_EXCEDIDA` → 409 · `DERECHO_REVOCADO` → 409 · `IDEMPOTENCY_KEY_REUTILIZADA` → 409 | implícito | operador autenticado | `FREEZE-RT` | sí | A8 |
| `RT-RT-03` | DELETE | `/pases/compras/{compra_id}/beneficiarios/{persona_id}` | `pases` | `PaseBeneficiarioPresenter` | `PaseBeneficiarioRevocadoOut` | — | `PASE_NO_TRANSFERIBLE` → 409 · `PASE_BENEFICIARIO_NO_ENCONTRADO` → 404 | implícito | `TITULARIDAD_COMPRADOR` o `Administrador` | `FREEZE-RT` | sí | A4 |
| `RT-MD-01` | POST | `/marketplace/productos` | `marketplace` | `ProductoPresenter` | `ProductoOut` | `CrearProductoIn` (multipart `data` + `files`) | `MEDIA_TIPO_NO_PERMITIDO` → 400 · `MEDIA_ARCHIVO_HUERFANO` → 400 · `MEDIA_TOKEN_NO_RESUELTO` → 400 · `MEDIA_TAMANO_EXCEDIDO` → 413 | implícito | `Administrador` | `FREEZE-MD` | sí | A5 |
| `RT-MD-02` | POST | `/patrocinadores` | `patrocinadores` | `PatrocinadorPresenter` | `PatrocinadorOut` | `CrearPatrocinadorIn` (multipart `data` + `files`) | idem `RT-MD-01` | implícito | `Administrador` | `FREEZE-MD` | sí | A8 |

### 3.4 Notas de lectura

- El ledger **no** incluye las rutas de lectura del catálogo público de la edición actual (`RT-ED-02` las cubre) ni las de administración no relacionadas con pagos. Se amplía en GOV-02 (T-001/T-002) cuando se aproximen las fichas de ruta.
- `RT-PG-04` conserva el filtro `estado_operativo` que la auditoría documenta como **existente en backend y ausente en la UI** (`03b` líneas 314, 966). El ledger lo deja explícito como parámetro de query: exponerlo es parte del contrato, no una mejora opcional.
- Todas las rutas marcadas `provisional = sí` **deben** permanecer sin registrar hasta que su módulo y su presenter estén implementados y versionados.

## 4. Contrato de nombre de wrapper (congelado)

| Elemento | Convención | Origen |
|---|---|---|
| Schema HTTP | `<Entidad><Operación>In` / `<Entidad><Operación>Out` | `django-app-architecture-contract.md` §5 |
| Presenter | `<Entidad>Presenter` con un método público por endpoint | `django-app-architecture-contract.md` §4.9 |
| Schema interno | `<Entidad><Operación>Data` / `<Entidad><Operación>Result` / `<Entidad>PaginatedResult` | `django-app-architecture-contract.md` §4.6 |
| Composición | Bloques `General` + `Específico` + `Identidad` | `SCHEMA_DRY_INTENTION.md` |

**Prohibido** un presenter que consulte la base de datos. **Prohibido** que un controller de un módulo importe presenters o schemas de otro módulo.

## 5. Consumo del freeze

| Consumidor | Depende de | Acción |
|---|---|---|
| FND-01 (`T-018`) | este freeze | Crear `core/contract_versions.py`, registrar `ENVELOPE_VERSION` y la versión de cada módulo |
| FND-06 (`T-017`) | `T-001`, `T-003` | Espejo Zod con `SCHEMA_VERSION` por dominio |
| FND-08 (consolidación de query keys y caché) | `T-017` + este freeze | Una clave por dataset, `queryOptions` por lectura, invalidación dirigida; el espejo Zod único de `FR-01` §8 |
| DOM-01..DOM-08 | `T-003` | Presenter y schema por módulo, con su `SCHEMA_VERSION` |
| API-01..API-05 | `T-082` | Verificar registro en `config/api.py`, espejo Zod 1:1, test de drift de versión |
| GOV-02 | este freeze | Ampliar el ledger con las rutas de lectura de las fichas |

## 6. Criterios de aceptación de este freeze

- [x] Esquema de versionado semver con MAJOR/MINOR/PATCH y su ubicación exacta.
- [x] Mecanismo de detección de drift por test de contrato.
- [x] Ledger ruta → wrapper con método, ruta, módulo, presenter, wrapper, schema de entrada, errores, status, scope, permiso, versión, carácter provisional y owner.
- [x] Regla de registro en `config/api.py` como condición de existencia de la ruta.
- [x] Convenciones de nombre de schema y presenter.

## 7. Decisiones abiertas relacionadas

| ID | Pendiente | Owner |
|---|---|---|
| `GOV-01-OPEN-11` | Versionado de **path** de API (`/v1`) — `django-app-architecture-contract.md` §16.4 lo pospone ("por ahora no es necesario"). Este freeze **no** introduce versionado de path: se usa el versionado de schema | A0 |
| `GOV-01-OPEN-12` | Rutas de lectura restantes del ledger (catálogos, cuentas, equipos, competencias) | A7 (GOV-02) |
