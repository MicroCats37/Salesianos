# 05 — Flujos end-to-end

> **Ámbito:** inventario verificado de los **27 flujos** que el navegador (y sus servicios auxiliares) ejercen sobre el sistema, desde la pantalla de origen hasta la escritura en base de datos, incluyendo canal de transporte, ruta de recuperación y ruta de error.
> **Método:** extracción directa de controladores backend, servicios frontend y configuración nginx.
> **Documentos hermanos:** [01 — Arquitectura y runtime](./01-arquitectura-y-runtime.md) · [03 — Frontend](./03-frontend.md) · [04 — Datos y dominio](./04-datos-y-dominio.md) · [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) · [07 — Guía para el agente de UI/UX](./07-guia-para-ui-ux.md)

## Documentos de detalle asociados

Este documento describe los **27 flujos** que el navegador ejercita. Los documentos de detalle amplían cada flujo sin duplicarlo aquí:

| Documento de detalle | Qué añade a este documento |
|---|---|
| [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) | La trazabilidad completa de cada flujo: acción de pantalla → endpoint → modelo/tabla → diagrama, más el inventario de páginas sin llamada al backend y de endpoints sin consumidor frontend. |
| [03a — Páginas públicas y de compra](./03a-paginas-publicas-y-compra.md) | Ficha de cada pantalla de los flujos A–D (catálogo, autenticación, identidad, inscripción) con sus servicios, payloads y estados. |
| [03b — Páginas administrativas y operativas](./03b-paginas-administrativas-y-operativas.md) | Ficha de cada pantalla de los flujos G–H (competencias y administración) con sus capas de autorización y su matriz de acciones. |
| [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) | El catálogo completo de rutas, para cerrar el inventario de § 3 con permiso y wrapper. |
| [02b — Propósito y consumidores de endpoints](./02b-proposito-y-consumidores-de-endpoints.md) | Para cada ruta, su propósito de negocio, su consumidor real y sus efectos. |
| [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) | Cómo se pueblan las tablas que los flujos escriben. |

---

## 1. Convenciones

| Término | Significado |
|---|---|
| **Ruta de navegador** | La ruta Next.js desde la que se origina la interacción |
| **Endpoint (navegador)** | La ruta que el navegador pide al proxy: `/backend/...` (Django) o `/api/...` (handler de Next) |
| **Endpoint (Django)** | La ruta real en Django tras la reescritura `/backend → /api` |
| **Propietario** | El módulo `modules.<nombre>` que **posee el flujo**, no el que posee la tabla |
| **Wrapper** | `ApiResponse[T]` = sobre `{success, data, error, message}` de `backend/core/responses.py`. `PaginatedData[T]` = `{items, total, page, page_size, total_pages}` anidado en `ApiResponse` para listados de administración |
| **Recuperación** | Qué hace el sistema cuando el flujo no completa por la vía feliz |

---

## 2. Índice de flujos

| Grupo | Flujos | Tema |
|---|---|---|
| [A](#a-catálogo-público-y-cotización) | 1–2 | Catálogo público y cotización |
| [B](#b-autenticación-y-sesión) | 3–7 | Autenticación y sesión |
| [C](#c-identidad-y-personas) | 8–9 | Identidad y personas |
| [D](#d-inscripción-equipos-y-cupos) | 10–14 | Inscripción, equipos y cupos |
| [E](#e-pagos) | 15–20 | Pagos (Izipay) |
| [F](#f-pases-de-fiesta-y-acreditación) | 21–23 | Pases de fiesta y acreditación |
| [G](#g-competencias) | 24–25 | Competencias |
| [H](#h-administración) | 26 | Listas de administración |
| [I](#i-servicios-auxiliares) | 27 | Scraper externo |

---

## A. Catálogo público y cotización

| # | Pantalla | Transporte | Endpoint (navegador) | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 1 | `/`, `/informacion` | **4 clientes distintos** para el mismo endpoint (ver nota) | `GET /backend/catalogo/{disciplinas,promociones,categorias,paquetes}/` | `salesianos_fest` → `catalogo_controller` (todos `auth=None`) | Lee `Disciplina`, `Promocion`, `Categoria`, `Paquete`, `PasePrecio` | `ApiResponse[list[XOut]]` | `landing/paquetes.service` devuelve `null` si falla; `portada/useCatalogo` devuelve `null` y la portada renderiza respaldos estáticos; `catalog.service` relaja el contrato (tipo `Paquete` obsoleto) y devuelve el dato crudo; `paquete.service` registra el error y devuelve el elemento crudo |
| 2 | `/inscripcion` (paso 1) | `features/inscripciones/services/cotizacion.service` (axios) | `POST /backend/cotizaciones/` | `salesianos_fest` → `cotizacion_controller` (`auth=None`) → `cotizacion_flujo` | Lee `Paquete` y tablas de precios | `ApiResponse[CotizacionResponse]` | Público; los errores se propagan por `error.message` del sobre |

> **Nota — flujo 1.** El endpoint de catálogo público tiene **cuatro implementaciones de cliente**:
> 1. `features/portada/hooks/useCatalogo.ts` — `fetch` crudo + validación Zod, `BASE_URL` propio.
> 2. `features/landing/paquetes.service.ts` — `fetch` crudo, sin cabecera de autenticación, sin refresco, sin parser de errores; `BASE_URL` propio.
> 3. `features/inscripciones/services/catalog.service.ts` → `getPaquetes` — axios, tipo `Paquete` marcado `@deprecated`, con respaldo a campos heredados.
> 4. `features/inscripciones/services/paquete.service.ts` → `fetchPaqueteList` — axios + Zod, registra la discrepancia y continúa.
>
> Los clientes 1 y 2 evitan la instancia axios (`lib/api.ts`) y, por tanto, **no heredan** el interceptor de `Authorization`, el refresco proactivo, ni el reintento tras 401.

---

## B. Autenticación y sesión

| # | Pantalla | Transporte | Endpoint (navegador) | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 3 | `/login` | `features/auth/hooks/useLogin` → `lib/api.ts` (axios, sin servicio dedicado) | `POST /backend/auth/login/{username\|dni\|email}` | `usuarios` → `auth_controller` | Lee `Usuario`, `Persona` | `ApiResponse[LoginTokenOut]` | `success !== true` ⇒ `throw new Error(error.message)`. Tras el éxito, el **navegador** escribe las 4 cookies (`httpOnly: false`) |
| 4 | Implícito, en cualquier llamada axios | `lib/api.ts` → `refreshAccessToken()` → handler de Next | `POST /api/auth/refresh` → `POST {BACKEND_INTERNAL_URL}/token/refresh` | `ninja_jwt` (app `ninja_jwt.token_blacklist`) | Lee/escribe la tabla de blacklist | Sobre de Next: `{success, data:{expires_at}}` | Single-flight (`refreshPromise`); refresco proactivo si expira en < 5 min; 401 ⇒ refrescar y reintentar **una vez** (`_retry`); si el refresco falla, se propaga el 401 original |
| 5 | Logout | Handler de Next | `POST /api/auth/logout` | **Ninguna llamada al backend** | Elimina las 4 cookies | `{success:true}` | El refresh token **no se lista en la blacklist**. Ver [H-1](./06-operacion-y-deuda-tecnica.md) |
| 6 | `/administracion` (layout) y toda pantalla admin | `features/admin/services/admin.session.server.ts` → `getAdminSession()` (`cache()` de React, `cache:"no-store"`) | `GET {BACKEND_INTERNAL_URL}/auth/me` | `usuarios` → `me_controller` (`auth=JWTAuth()`) | Lee `Usuario`, `Persona` | `ApiResponse[MeOut]` | 4 resultados con **cierre por defecto**: `unauthenticated` → `/login`; `forbidden` → `AdminAccessDenied`; `unavailable` → `/dashboard`; `admin` → acceso |
| 7 | `/register` | `features/auth/services/register.service.registerUser` → `useRegister` | `POST /backend/auth/register` | `usuarios` → `registro_controller` (`auth=None`) → `registro_orchestrator` | **Escribe** `Persona`, `Usuario`, `Aceptacion` (BASES) | `ApiResponse[RegisterOut]` (incluye access/refresh/expires) | 409 por email o documento duplicado. El cliente escribe las 4 cookies (`maxAge` 7 d) y redirige a `/inscripcion` |

---

## C. Identidad y personas

| # | Pantalla | Transporte | Endpoint (navegador) | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 8 | `/inscripcion` (búsqueda DNI/RUC) | `components/genericForm/inputs/smart-fields/DocumentoLookupSmartField` | `GET /backend/personas/busqueda/{documento}` (8 u 11 dígitos) | `usuarios` → `persona_busqueda_controller` (`auth=None`) → `persona_busqueda_flujo` → `IConsultaExternaClient` | Sin modelo local: consulta externa | `ApiResponse[DocumentoConsultaOut]` | `RealConsultaExternaClient` traduce 404 → `ReniecNotFoundError`/`SunatNotFoundError`; 422 → `HttpError(422)`; 502/503/504 → `HttpError` homólogo; timeout de conexión → 503, de lectura → 504. En `DEBUG` responde `ConsultaExternaSimulator` |
| 9 | `/pases` (selector de beneficiario) | `features/pases/services/persona.resolucion.service` | `GET /backend/personas/resolver` | `usuarios` → `persona_resolucion_controller` (`auth=JWTAuth()`) | Lee `Persona` | `ApiResponse[PersonaResueltaOut]` | Requiere autenticación; un 401 dispara el refresco y reintento del interceptor de axios |

---

## D. Inscripción, equipos y cupos

| # | Pantalla | Transporte | Endpoint (navegador) | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 10 | `/inscripcion` (paso final) | `features/inscripciones/hooks/useCreateInscripcionCompleta` | `POST /backend/inscripciones/completa/` | `salesianos_fest` → `inscripcion_controller` → `inscripcion_orchestrator` → `CrearInscripcionCompletaFlujo` (**atómico**) | **Escribe** `Inscripcion`, `commerce.Compra` (PENDIENTE), `pagos.OrdenPago`, `CompraInscripcion`, `Equipo`, `AsignacionCupo` | `ApiResponse[InscripcionCompletaOut]` (201) | `CantidadInsuficienteError` si no se alcanza `minimo_compra_inicial`. El precio queda **congelado** en la creación. El `evento` se resuelve en el servidor desde `EVENTO_ACTIVO_NOMBRE` |
| 11 | `/dashboard`, `/dashboard/inscripcion/[id]` | `features/inscripciones/services/inscripcion.service` | `GET /backend/inscripciones/`, `GET /backend/inscripciones/{id}`, `GET /backend/inscripciones/{id}/detalle` | `salesianos_fest` → `inscripcion_controller` (con verificación de propiedad) | Lee `Inscripcion`, `Persona`, `Equipo`, `Participacion` | `ApiResponse[InscripcionOut]` / `ApiResponse[InscripcionDetailOut]` | La propiedad (`responsable` o admin de Django) se aplica en `presentation/ownership.py` → `ForbiddenError` (403) |
| 12 | Pool / capacidad | `features/inscripciones/services/pool.service` | `GET /backend/inscripciones/{id}/pool` · `POST /backend/inscripciones/{id}/pool/asignar` · `GET /backend/inscripciones/{id}/equipos/{equipo_id}/elegibles` | `salesianos_fest` → `asignacion_controller` / `inscripcion_controller` → `asignar_persona_flujo`, `crear_asignaciones_flujo` | Lee/escribe `AsignacionCupo`, `Participacion`, `Persona` | `ApiResponse[PoolOut]`, `ApiResponse[ElegiblesEquipoOut]`, y **`ApiResponse` sin tipar** para `pool/asignar` | Restricción R11 (una participación activa por evento/disciplina/persona) mediante índice único parcial; `select_for_update` en el servicio de asignación. El invariante "≤ cupos" es **solo de servicio**, no una restricción de base de datos |
| 13 | Equipos y participación | `features/inscripciones/services/inscripcion.service` | `POST /backend/equipos/`, `GET /backend/equipos/{id}`, `GET /backend/equipos/inscripcion/{id}`, `POST /backend/participaciones/`, `PATCH /backend/participaciones/{id}[/retirar,/mover]`, `GET /backend/participaciones/equipo/{equipo_id}` | `salesianos_fest` → `inscripcion_controller` (prefijos `equipos` y `participaciones`) → `crear_equipo_flujo`, `asignar_persona_flujo`, `retirar_persona_flujo` | **Escribe** `Equipo`, `Participacion` | `ApiResponse[EquipoOut]`, `ApiResponse[ParticipacionOut]` | Compatibilidad de género/modalidad validada en `domain/validators/participacion.py` y `Participacion.clean()`. `Evento.fecha_limite_modificacion` se aplica solo en código de aplicación |
| 14 | Liberación de cupo y saldo | `features/inscripciones/services/inscripcion.service` | `POST /backend/asignaciones/liberar` · `GET /backend/inscripciones/{id}/saldo` · `GET /backend/inscripciones/{id}/asignaciones` | `salesianos_fest` → `asignacion_controller` → `liberar_cupo_flujo` | **Escribe** `AsignacionCupo` (estado `LIBERADA`) | `ApiResponse[LiberarCupoOut]`, `ApiResponse[SaldoOut]` | Estas rutas **no aparecían** en el artefacto previo de inventario de rutas. Ver [H-5](./06-operacion-y-deuda-tecnica.md) |

---

## E. Pagos (Izipay)

El canal de pagos tiene **tres confirmaciones independientes** y **una sola autoridad comercial** (el backend).

| Canal | Quién lo dispara | Endpoint | Verificación |
|---|---|---|---|
| Relay del navegador | El usuario cierra el pop-up de Izipay | `POST /api/pagos/izipay/confirmar` | Autenticado + propiedad de la orden + coherencia de monto + idempotencia |
| Notificación del proveedor | Izipay, servidor a servidor | `POST /api/pagos/izipay/notificacion` (`auth=None`) | **Solo** si el HMAC del comercio verifica. Sin `IZIPAY_KEY_HASH` ⇒ falla cerrado |
| Lectura de retorno | El frontend, con sondeo acotado | `GET /api/pagos/transacciones/{id}` | Solo lectura del estado persistido |

| # | Pantalla | Transporte | Endpoint (navegador) | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 15 | Preparación de compra → pago | `features/pagos/services/pago.service.iniciarPagoIzipay` | `POST /backend/compras/{compra_id}/iniciar-pago` | `salesianos_fest` → `compra_controller` (`auth=JWTAuth()`) → `IniciarPagoFlujo` → `pagos.PagosOrchestrator.preparar_pago_izipay` → `IzipayCoreService` → `IzipayClient` | **Escribe** `pagos.OrdenPago` (reuso), `pagos.TransaccionPago` (PENDIENTE) | `ApiResponse[IniciarPagoOut]` (token, código de comercio, monto, comprador) | Comprador y monto se derivan del servidor desde la `Persona` del llamador. Un intento vivo por orden (índice único parcial `uniq_transpago_activo_orden`). La ruta **no aparecía** en el artefacto previo de rutas |
| 16 | Modal de checkout Izipay | `features/pagos/components/IzipayModal.tsx` → `pago.service.confirmarPagoIzipay` | `POST /backend/pagos/izipay/confirmar` | `pagos` → `pagos_controller` → `PagosOrchestrator.confirmar_pago_izipay` → `RegistrarPagoIzipayFlujo._confirmar_pago` → `IConfirmadorOrdenPagoService` → `ConfirmadorOrdenPagoAdapter` → `ConfirmarPagoFlujo` (fest) | **Escribe** `TransaccionPago` (EXITO), `Compra` (PAGADA), `AsignacionCupo`, `Acreditacion` | `ApiResponse[IzipayConfirmOut]` (`success`, `settlement_status`, `already_confirmed`) | Verificación de propiedad → `PagoNoAutorizadoError` (403); firma → `PagoFirmaInvalidaError`; monto/orden → `PagoDatosInconsistentesError`. **Idempotente**: reintentar converge. Si la liquidación comercial falla, el pago queda registrado y el mensaje pasa a "Pago confirmado. La activación comercial está pendiente." |
| 17 | — (servidor a servidor) | — | `POST /backend/pagos/izipay/notificacion` | `pagos` → `pagos_controller.recibir_notificacion` → `RegistrarPagoIzipayFlujo._confirmar_notificacion` | Igual que 16 | `ApiResponse[IzipayConfirmOut]` | Falla cerrado: sin `IZIPAY_KEY_HASH` → `PagoNotificacionNoVerificableError`; firma inválida → `PagoFirmaInvalidaError`. Los reintentos del proveedor convergen |
| 18 | Recuperación de pago | `features/pagos/utils/checkout.recuperacion.ts` → `pago.service.obtenerEstadoTransaccion` | `GET /backend/pagos/transacciones/{transaction_id}` | `pagos` → `pagos_controller.obtener_transaccion` | Lee `TransaccionPago` (+ `OrdenPago`) | `ApiResponse[TransaccionPagoOut]` | Sondeo acotado: `INTERVALO_SONDEO_MS = 2000`, `MAX_SONDEOS = 15` (30 s). **Una lectura fallida no es un pago fallido**: `EXITO` → éxito; `FALLIDO`/`CANCELADO` → rechazado; agotado el límite → "no se pudo verificar el pago" (no demostrado). Se cancela al cerrar el modal |
| 19 | Estado de la orden | `features/pagos/services/pago.service` | `GET /backend/pagos/ordenes/{orden_id}` | `pagos` → `pagos_controller.obtener_orden` | Lee `OrdenPago` | `ApiResponse[OrdenPagoOut]` | Solo el propietario o un administrador |
| 20 | Aprobación manual (admin) | `features/admin/services/admin.pago.service` | `POST /backend/administracion/pagos/{orden_pago_id}/aprobar-manual` · `.../anular-manual` | `administracion` → `admin_pago_controller` (permiso `RequirePagosAprobar` a nivel de ruta) → `pagos.aprobar_pago_manual_flujo` | **Escribe** `AprobacionPagoManual` (APROBADA/ANULADA) | `ApiResponse[AdminPagoAprobarManualOut]` | **Deshabilitado por defecto** (`PAGO_MANUAL_APROBACION_ENABLED=False`; en `.env` está en `true`). El índice único parcial `uniq_aprobmanual_activa_orden` mantiene ≤ 1 aprobación activa. La aprobación es **evidencia** para el predicado de liquidación, nunca una liquidación en sí misma |

---

## F. Pases de fiesta y acreditación

| # | Pantalla | Transporte | Endpoint (navegador) | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 21 | Compra y cancelación | `features/pases` / `features/admin/pases/services/admin.pase.service` | `POST /backend/compras/{id}/cancelar` · `POST /backend/administracion/pases/compras/{id}/cancelar` | `salesianos_fest` → `compra_controller` / `administracion` → `admin_pases_controller` (`RequirePagosVer` + `RequirePagosAprobar`) → `cancelar_compra_flujo` | **Escribe** `Compra` (CANCELADA), `AsignacionCupo` (REVOCADA) | `ApiResponse[CompraCanceladaOut]`, `ApiResponse[AdminPaseCanceladaOut]` | Contraste contra una orden pagada; los cupos se liberan |
| 22 | `/pases` | `features/pases/services/pase.service` + `pase.beneficiario.service` | `GET /backend/pases/` (público) · `POST /backend/pases/comprar` · `GET /backend/pases/compras/{id}` · `GET\|POST /backend/pases/compras/{id}/beneficiarios` · `DELETE /backend/pases/compras/{id}/beneficiarios/{persona_id}` | `salesianos_fest` → `pase_controller` → `crear_compra_pase_flujo`, `asignar_beneficiarios_pase_flujo`, `revocar_beneficiario_pase_flujo`, `listar_pases_flujo`, `obtener_compra_pase_flujo` | Lee/escribe `Pase`, `PasePrecio`, `CompraPase`, `PaseBeneficiario`, `commerce.Compra`, `OrdenPago` | `ApiResponse[PaseCompraCreadaOut]`, `[PaseCompraEstadoOut]`, `[PaseBeneficiariosListaOut]`, `[PaseBeneficiariosAsignadosOut]`, `[PaseBeneficiarioRevocadoOut]` | La asignación de beneficiarios solo es posible sobre una compra **PAGADA**; el cupo es inmutable y consumido; una persona no se reutiliza dentro de un lote ni siquiera tras la revocación. `1 ≤ slot ≤ CompraPase.cantidad`, el tope `Pase.cantidad_maxima` y `CANTIDAD_MAXIMA_POR_COMPRA=50` son **reglas de servicio**. **Bloqueado por `PASES_FIESTA_ENABLED` (por defecto `False`)** |
| 23 | Acreditación y acceso | `features/inscripciones` | `GET /backend/acreditaciones/{evento_id}/{persona_id}` · `PATCH /backend/acreditaciones/{evento_id}/{persona_id}/override-fiesta` · `POST /backend/acreditaciones/{evento_id}/{persona_id}/generar-qr` · `POST /backend/acceso/registrar` | `salesianos_fest` → `acreditacion_controller` (`/acreditaciones`) y `acceso_controller` (`/acceso`) → `override_fiesta_flujo`, `registrar_acceso_flujo` | Lee/escribe `Acreditacion`, `ControlAcceso`, `AceptacionInscripcion` | `ApiResponse[AcreditacionOut]`, `[OverrideFiestaOut]`, `[GenerarQROut]`, `[RegistrarAccesoOut]` | Precedencia `BLOQUEADA > AUTORIZADA > AUTOMATICA`. Un override administrativo **nunca** se limpia por una sincronización, compra o retiro posterior. `select_for_update` en `registrar_acceso_flujo`; lectura con propiedad o administración |

---

## G. Competencias

| # | Pantalla | Transporte | Endpoint (navegador) | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 24 | `/administracion/competencias/**` | `features/admin/competencias/services/{competencias,competencias.comandos}.service` | 29 rutas `GET\|POST\|PATCH\|DELETE /backend/administracion/competencias…` (17 de `AdminCompetenciasController` + 12 de `AdminEncuentrosController`): `/agenda`, `/cuadro`, `/{id}`, `/equipos`, `/rondas`, `/encuentros`, `.../estado`, `.../bye`, `.../enlace`, `.../desenlace`, `.../resultado`, `.../avance/preview\|confirm`, `.../correccion/preview\|confirm` | `competencias` → `admin_competencias_controller`, `admin_encuentros_controller` (`RequireCompetenciasEscribir`) → `core/*` + `flujos/*` (todos los flujos abren `transaction.atomic`) | Lee/escribe `Competencia`, `CompetenciaEquipo`, `Ronda`, `Encuentro` (+ `simple_history`) | `ApiResponse[CompetenciaListOut]`, `[RondaOut]`, `[EncuentroOut]`, `[AvanceOut]`, `[CorreccionOut]`, `[CuadroOut]`, `[AgendaOut]` | Bloqueo optimista con `version` + `expected_version` → `RESOURCE_CHANGED` (409). Índices únicos en base de datos y 4 `CheckConstraint`. **Es el agrupamiento más limpio del backend** |
| 25 | Cuadro público | Widget de cuadro | `GET /backend/competencias` · `/backend/competencias/encuentros` · `/backend/competencias/{id}` · `/backend/competencias/{id}/cuadro` | `competencias` → `public_competencias_controller` (`auth=None`) | Los mismos 4 modelos | `ApiResponse[...]` | Público por diseño, solo lectura |

---

## H. Administración

| # | Pantalla | Transporte | Endpoint (navegador) | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 26 | `/administracion/**` | `features/admin/services/admin.{inscripcion,operacion,pago,usuario,resumen}.service` → `admin.http.service.adminGet` (validación Zod estricta) | `GET /backend/administracion/{health,resumen,catalogos,inscripciones,inscripciones/{id},equipos,participantes,participaciones,acreditaciones,acreditaciones/{id},accesos,pagos,pagos/{id},usuarios,usuarios/{id}}` | `administracion` → `admin_*_controller` (`RequireAdminVer` / `RequirePagosVer` / `RequireUsuariosVer`) | Lee **a través de todos los módulos** (no tiene tablas propias) | `ApiResponse[PaginatedData[XListItemOut]]` en listados, `ApiResponse[XDetailOut]` en detalles | Filtros, página, orden y término viven en la **querystring** (`useAdminListaUrl`); una discrepancia con el esquema Zod **lanza** `ApiQueryError`. `GET /administracion/catalogos` es la fuente de los vocabularios de estado (incluye `estado_capacidad_equipo`) |

---

## I. Servicios auxiliares

| # | Pantalla | Transporte | Endpoint | Propietario → flujo | Modelos | Wrapper | Recuperación / error |
|---|---|---|---|---|---|---|---|
| 27 | Flujo 8 (búsqueda de documento) | `RealConsultaExternaClient` (httpx) | `GET {SCRAPER_URL}/consultar/{documento}` | `worker/scraper` (FastAPI) → `documento_scraper.consultar` | Ninguno (portal externo) | `{tipo_documento, numero_documento, razon_social}` | 200/404/422/500/502/503/504 con código de máquina y `retryable`. `GET /health` es el destino del healthcheck de compose. Un cambio en el HTML del portal produce 502 `FORMAT_ERROR` y exige actualizar el parser |

---

## 3. Inventario de rutas HTTP (extracción desde el código)

Extracción directa de los decoradores `@route.*` de todos los `*_controller.py` de `backend/modules/`, combinada con los prefijos `@api_controller(...)`. Este inventario es **la fuente de verdad**; cualquier tabla de rutas derivada de un artefacto previo debe reconciliarse contra él.

| Controlador | Prefijo | Rutas |
|---|---|---|
| `NinjaJWTDefaultController` | `/token` | `pair`, `refresh`, `verify` (controlados por la librería) |
| `AuthLoginController` | `/auth/login` | `POST /username` · `POST /dni` · `POST /email` (todos `auth=None`) |
| `RegistroController` | `/auth` | `POST /register` (`auth=None`) |
| `PersonaBusquedaController` | `/personas` | `GET /busqueda/{documento}` (`auth=None`) |
| `PersonaResolucionController` | `/personas` | `GET /resolver` (`auth=JWTAuth()`) |
| `AuthMeController` | `/auth` | `GET /me` (`auth=JWTAuth()`) |
| `PagosController` | `/pagos` | `POST /izipay/confirmar` · `POST /izipay/notificacion` (`auth=None`) · `GET /transacciones/{transaction_id}` · `GET /ordenes/{orden_id}` |
| `CatalogoController` | `/catalogo` | `GET /disciplinas/` · `GET /promociones/` · `GET /categorias/` · `GET /paquetes/` · `GET /paquetes/{paquete_id}/` (todos `auth=None`) |
| `PaseController` | `/pases` | `GET /` (`auth=None`) · `POST /comprar` · `GET /compras/{compra_id}` · `GET /compras/{compra_id}/beneficiarios` · `POST /compras/{compra_id}/beneficiarios` · `DELETE /compras/{compra_id}/beneficiarios/{persona_id}` |
| `InscripcionController` | `/inscripciones` | `POST /` · `POST /completa/` · `GET /` · `GET /{inscripcion_id}` · `GET /{inscripcion_id}/detalle` · `PATCH /{inscripcion_id}` · `POST /{inscripcion_id}/personas` (**sin tipar**) · `PATCH /{inscripcion_id}/personas/{persona_id}/retirar` · `GET /{inscripcion_id}/pool` · `GET /{inscripcion_id}/equipos/{equipo_id}/elegibles` · `POST /{inscripcion_id}/pool/asignar` (**sin tipar**) |
| `EquipoController` | `/equipos` | `POST /` · `GET /{equipo_id}` · `GET /inscripcion/{inscripcion_id}` |
| `ParticipacionController` | `/participaciones` | `POST /` · `GET /{participacion_id}` · `GET /equipo/{equipo_id}` · `PATCH /{participacion_id}/retirar` · `PATCH /{participacion_id}/mover` · `PATCH /{participacion_id}` |
| `CompraController` | `/compras` | `POST /` · `GET /{compra_id}` · `GET /inscripciones/{inscripcion_id}/compras` · `POST /{compra_id}/iniciar-pago` · `POST /{compra_id}/cancelar` |
| `AsignacionController` | `/asignaciones` | `POST /` · `POST /liberar` · `GET /{asignacion_id}` · `GET /inscripciones/{inscripcion_id}/asignaciones` |
| `InscripcionSaldoController` | `/inscripciones` | `GET /{inscripcion_id}/saldo` |
| `AcreditacionController` | `/acreditaciones` | `GET /{evento_id}/{persona_id}` · `PATCH /{evento_id}/{persona_id}/override-fiesta` · `POST /{evento_id}/{persona_id}/generar-qr` |
| `AccesoController` | `/acceso` | `POST /registrar` |
| `CotizacionController` | `/cotizaciones` | `POST /` (`auth=None`) |
| `AdminFundacionController` | `/administracion` | `GET /health` |
| `AdminResumenController` | `/administracion` | `GET /resumen` · `GET /catalogos` |
| `AdminInscripcionController` | `/administracion` | `GET /inscripciones` · `GET /inscripciones/{inscripcion_id}` |
| `AdminPagoController` | `/administracion` | `GET /pagos` · `GET /pagos/{orden_pago_id}` · `POST /pagos/{orden_pago_id}/aprobar-manual` · `POST /pagos/{orden_pago_id}/anular-manual` |
| `AdminOperacionController` | `/administracion` | `GET /equipos` · `GET /participantes` · `GET /participaciones` · `GET /acreditaciones` · `GET /acreditaciones/{acreditacion_id}` · `GET /accesos` |
| `AdminPasesController` | `/administracion/pases` | `POST /compras/{compra_id}/cancelar` |
| `AdminUsuarioController` | `/administracion` | `GET /usuarios` · `GET /usuarios/{usuario_id}` |
| `AdminCompetenciasController` | `/administracion/competencias` | 17 rutas (`GET /`, `GET /agenda`, `GET /{competencia_id}`, `GET /{competencia_id}/cuadro`, `GET /{competencia_id}/equipos`, `GET /{competencia_id}/rondas`, `GET /{competencia_id}/encuentros`, `POST /`, `PATCH /{competencia_id}`, `PATCH /{competencia_id}/estado`, `DELETE /{competencia_id}`, `POST /{competencia_id}/equipos`, `PATCH /{competencia_id}/equipos/{competencia_equipo_id}`, `POST /{competencia_id}/rondas`, `PATCH /{competencia_id}/rondas/{ronda_id}`, `PATCH /{competencia_id}/rondas/{ronda_id}/estado`, `POST /{competencia_id}/encuentros`) |
| `AdminEncuentrosController` | `/administracion/competencias/encuentros` | 12 rutas (`PATCH /{encuentro_id}/participantes`, `.../programacion`, `.../estado`, `POST .../bye`, `.../enlace`, `.../desenlace`, `.../resultado`, `.../avance/preview`, `.../avance/confirm`, `.../correccion/preview`, `.../correccion/confirm`, `DELETE /{encuentro_id}`) |
| `PublicCompetenciasController` | `/competencias` | `GET /` · `GET /encuentros` · `GET /{competencia_id}` · `GET /{competencia_id}/cuadro` (todos `auth=None`) |
| `IngenieroHabilitadoController` | `/ingenieros` | `GET /habilitados/{cip}` — **definida pero NO registrada**: la ruta no existe en la API |

---

## 4. Nota de completitud del artefacto de rutas

El artefacto previo de exploración de backend (`sdd/explore/rebuild-backend-api-map`) produjo una tabla de rutas que **omitía** controladores completos:

| Controlador omitido | Rutas que quedaban fuera |
|---|---|
| `CompraController` (`/compras`) | 5 rutas, entre ellas **`POST /compras/{compra_id}/iniciar-pago`** (la que el navegador llama para iniciar el pago) y `POST /compras/{compra_id}/cancelar` |
| `AsignacionController` + `InscripcionSaldoController` (`/asignaciones`) | 5 rutas, entre ellas **`POST /asignaciones/liberar`** (liberación de cupo) y `GET /inscripciones/{id}/saldo` |

**Impacto:** una lista de verificación de reconstrucción derivada exclusivamente de ese artefacto habría omitido el endpoint de inicio de pago y el de liberación de cupo, rompiendo los flujos 15 y 14 sin señal visible.

**Regla operativa derivada:** el inventario de rutas debe extraerse **del código** (decoradores `@route.*` + `@api_controller`), nunca de un artefacto de exploración. La tabla de § 3 es el punto de partida; debe regenerarse si cambia `backend/config/api.py`.

---

## 5. Límites de este mapa

- Los 27 flujos cubren **lo que el navegador ejercita**. La API expone además superficies administrativas (cubiertas por el flujo 26), superficies públicas de lectura (flujo 25), la superficie de `ninja_jwt` (`/token/*`) y comandos de gestión de Django que ningún flujo web cubre (ver [06 — Comandos manuales](./06-operacion-y-deuda-tecnica.md)).
- Dos respuestas del backend quedan **sin tipo de payload**: `POST /inscripciones/{id}/personas` y `POST /inscripciones/{id}/pool/asignar` declaran `ApiResponse` a secas. Esto abre un hueco en el contrato de paridad con el frontend.
- La paridad campo a campo entre frontend y backend no está resuelta en su totalidad (`nombre` vs `nombres`, `precio_preventa` vs `precio_promocional`, `cantidad_minima_compra` vs `cantidad_maxima_participantes`).
- No se verificó que el parámetro `evento_id` de las rutas de acreditación se valide contra el evento activo.

---

## 6. Referencias cruzadas

- [README — Índice de la documentación](./README.md) — punto de entrada navegable del conjunto documental.
- [00 — Cobertura y trazabilidad](./00-cobertura-y-trazabilidad.md) — metodología de auditoría, recuentos verificados y checklist reejecutable.
- [01 — Arquitectura y runtime](./01-arquitectura-y-runtime.md) — topología de cuatro niveles, tabla de enrutamiento nginx, las dos URLs base y la propiedad de las cookies.
- [02 — Backend y API](./02-backend-y-api.md) — arquitectura del servicio Django/Ninja.
- [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) — catálogo de rutas del backend.
- [02b — Propósito y consumidores de endpoints](./02b-proposito-y-consumidores-de-endpoints.md) — propósito, cadena de ejecución y efectos de cada ruta.
- [03 — Frontend](./03-frontend.md) — arquitectura del frontend, rutas, features y transporte HTTP.
- [03a — Páginas públicas y de compra](./03a-paginas-publicas-y-compra.md) — ficha de cada pantalla de los flujos A–D.
- [03b — Páginas administrativas y operativas](./03b-paginas-administrativas-y-operativas.md) — ficha de cada pantalla de los flujos G–H.
- [04 — Datos y dominio](./04-datos-y-dominio.md) — propiedad de datos, modelos, migraciones y fronteras de integración.
- [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) — quién puebla las tablas que los flujos escriben.
- [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) — trazabilidad completa de los 27 flujos.
- [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) — topología operativa, ausencia de planificador, y los hallazgos H-1 … H-9 (logout solo cliente, definiciones de cookie divergentes, ambigüedad de puerto, `doc/` obsoleto, artefacto de rutas incompleto).
