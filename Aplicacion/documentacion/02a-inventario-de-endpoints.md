# Inventario de endpoints — Salesianos FEST API

> **Servicio:** backend Django + `django-ninja-extra`, montado en `/api/`.
> **Base de la ruta pública:** el proxy nginx reescribe `/backend/*` → `/api/*` (`proxy/nginx.conf`). Las rutas que se listan abajo son las que ve el backend; el navegador las consume con el prefijo `/backend`.
> **Documento par:** [02-backend-y-api.md](02-backend-y-api.md).

---

## 1. Método de verificación

Este inventario no es una transcripción manual. Se construyó combinando dos fuentes y contrastándolas:

1. **Análisis del AST** de todos los controladores bajo `backend/modules/**/presentation/controllers/`, leyendo el decorador `@api_controller(prefix, tags, permissions)` y, por cada método, el decorador `@route.<verbo>(ruta, response=…, auth=…, permissions=…)`.
2. **Introspección del runtime**: arranque de Django y recorrido de `config.api.api._routers`, que devuelve las rutas **efectivamente registradas**, con sus métodos HTTP y sus *auth callbacks* reales.

Cada fila del inventario se etiquetó según ambas fuentes. La columna **Estado** distingue lo que está registrado de lo que sólo está escrito en disco.

**Recuento verificado:**

| Métrica | Valor |
|---|---|
| Rutas registradas en el runtime | **111** |
| Controladores registrados | 29 (28 del proyecto + `NinjaJWTDefaultController` de `django-ninja-jwt`) |
| Rutas declaradas en código | 112 |
| Controladores escritos y **no** registrados | 1 (`IngenieroHabilitadoController`) |
| Rutas públicas (`auth=None`) | 20 |
| Rutas con respuesta `204 No Content` | 2 |

---

## 2. Convenciones de lectura

| Columna | Significado |
|---|---|
| **Auth** | `JWT` = exige `Authorization: Bearer <token>` válido. `público` = la ruta declara `auth=None`; el `auth` global de la API queda anulado |
| **Permiso efectivo** | Permiso que realmente se evalúa. Cuando la ruta declara `permissions=[...]`, esa lista **reemplaza** la del controlador (verificado en `ninja_extra/operation.py`: `route.permissions or controller.permission_classes`). La coletilla «(sustituye a …)» indica el permiso del controlador que queda anulado |
| **Wrapper de respuesta** | Esquema declarado en `response={…}`. `ApiResponse` sin tipo significa carga útil no tipada |
| **Estado** | `registrada` = alcanzable en runtime. `NO registrada` = código muerto |

Observaciones sobre las rutas:

- **Barra final.** Se conserva exactamente como la emite el runtime. Django sirve estas rutas con `APPEND_SLASH` activo, pero la URL canónica es la que figura en la tabla. El comportamiento del proxy y del cliente ante la barra final no se auditó en esta revisión.
- **Prefijos compartidos.** Seis controladores usan `/administracion` y dos usan `/administracion/competencias`. El desempate lo hace el **orden** de `api.register_controllers(...)` en `backend/config/api.py`, no la unicidad del prefijo.
- **Rutas fuera del backend.** `/api/auth/refresh` y `/api/auth/logout` **no** las sirve Django: las atiende el frontend Next.js, y el proxy nginx las reserva de forma explícita. No aparecen en el inventario porque no son rutas de este servicio.

---

## 3. Superficies por prefijo (resumen)

| Prefijo | Controlador(s) | Rutas | Naturaleza |
|---|---|---|---|
| `/api/auth` | `AuthLoginController`, `AuthMeController`, `RegistroController` | 5 | Login, registro y sesión |
| `/api/token` | `NinjaJWTDefaultController` | 3 | Built-in de `django-ninja-jwt` |
| `/api/personas` | `PersonaBusquedaController`, `PersonaResolucionController` | 2 | Consulta de documentos y resolución de persona existente |
| `/api/catalogo` | `CatalogoController` | 5 | Catálogo público de paquetes, disciplinas, categorías y promociones |
| `/api/cotizaciones` | `CotizacionController` | 1 | Cotización pública |
| `/api/pases` | `PaseController` | 6 | Catálogo público de pases y compra con derechos nominativos |
| `/api/inscripciones` | `InscripcionController`, `InscripcionSaldoController` | 12 | Inscripción deportiva, roster, pool y saldo |
| `/api/equipos` | `EquipoController` | 3 | Equipos |
| `/api/participaciones` | `ParticipacionController` | 6 | Participaciones en competencias |
| `/api/compras` | `CompraController` | 5 | Compras de cupos e inicio de pago |
| `/api/asignaciones` | `AsignacionController` | 4 | Asignación y liberación de cupos |
| `/api/acreditaciones` | `AcreditacionController` | 3 | Acreditación y override de fiesta |
| `/api/acceso` | `AccesoController` | 1 | Registro de acceso |
| `/api/pagos` | `PagosController` | 4 | Confirmación y notificación Izipay, consulta de órdenes y transacciones |
| `/api/administracion` | 6 controladores | 17 | Superficie operativa de administración |
| `/api/administracion/pases` | `AdminPasesController` | 1 | Cancelación administrativa de compras de pases |
| `/api/administracion/competencias` | `AdminCompetenciasController` | 17 | Gestión de competencias, rondas y cuadro |
| `/api/administracion/competencias/encuentros` | `AdminEncuentrosController` | 12 | Gestión de encuentros y resultados |
| `/api/competencias` | `PublicCompetenciasController` | 4 | Cuadro público de competencias |
| `/api/ingenieros` | `IngenieroHabilitadoController` | 1 | **No registrada** |

> **Cuadre de la columna «Rutas»:** 5 + 3 + 2 + 5 + 1 + 6 + 12 + 3 + 6 + 5 + 4 + 3 + 1 + 4 + 17 + 1 + 17 + 12 + 4 = **111 rutas registradas**; más la fila `/api/ingenieros` (no registrada) = **112 definiciones de ruta en código**, de las cuales **1 no se monta** en la API.

---

## 4. Inventario detallado

### `AccesoController`

Archivo: `salesianos_fest/presentation/controllers/acreditacion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/acceso/registrar` | JWT | IsAuthenticated | `{200: ApiResponse[RegistrarAccesoOut]}` | registrada |

### `AcreditacionController`

Archivo: `salesianos_fest/presentation/controllers/acreditacion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/acreditaciones/{evento_id}/{persona_id}` | JWT | IsAuthenticated | `{200: ApiResponse[AcreditacionOut]}` | registrada |
| POST | `/api/acreditaciones/{evento_id}/{persona_id}/generar-qr` | JWT | RequireAcreditacionesEscribir, (sustituye a IsAuthenticated) | `{200: ApiResponse[GenerarQROut]}` | registrada |
| PATCH | `/api/acreditaciones/{evento_id}/{persona_id}/override-fiesta` | JWT | RequireAcreditacionesEscribir, (sustituye a IsAuthenticated) | `{200: ApiResponse[OverrideFiestaOut]}` | registrada |

### `AdminCompetenciasController`

Archivo: `competencias/presentation/controllers/admin_competencias_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/administracion/competencias/` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[list[CompetenciaListOut]]}` | registrada |
| POST | `/api/administracion/competencias/` | JWT | RequireCompetenciasEscribir | `{201: ApiResponse[CompetenciaListOut]}` | registrada |
| GET | `/api/administracion/competencias/agenda` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[AgendaOut]}` | registrada |
| DELETE | `/api/administracion/competencias/{competencia_id}` | JWT | RequireCompetenciasEscribir | `{204: None}` | registrada |
| GET | `/api/administracion/competencias/{competencia_id}` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[CompetenciaDetalleOut]}` | registrada |
| PATCH | `/api/administracion/competencias/{competencia_id}` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[CompetenciaListOut]}` | registrada |
| GET | `/api/administracion/competencias/{competencia_id}/cuadro` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[CuadroOut]}` | registrada |
| GET | `/api/administracion/competencias/{competencia_id}/encuentros` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[list[EncuentroOut]]}` | registrada |
| POST | `/api/administracion/competencias/{competencia_id}/encuentros` | JWT | RequireCompetenciasEscribir | `{201: ApiResponse[EncuentroOut]}` | registrada |
| GET | `/api/administracion/competencias/{competencia_id}/equipos` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[list[CompetenciaEquipoOut]]}` | registrada |
| POST | `/api/administracion/competencias/{competencia_id}/equipos` | JWT | RequireCompetenciasEscribir | `{201: ApiResponse[CompetenciaEquipoOut]}` | registrada |
| PATCH | `/api/administracion/competencias/{competencia_id}/equipos/{competencia_equipo_id}` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[CompetenciaEquipoOut]}` | registrada |
| PATCH | `/api/administracion/competencias/{competencia_id}/estado` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[CompetenciaListOut]}` | registrada |
| GET | `/api/administracion/competencias/{competencia_id}/rondas` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[list[RondaOut]]}` | registrada |
| POST | `/api/administracion/competencias/{competencia_id}/rondas` | JWT | RequireCompetenciasEscribir | `{201: ApiResponse[RondaOut]}` | registrada |
| PATCH | `/api/administracion/competencias/{competencia_id}/rondas/{ronda_id}` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[RondaOut]}` | registrada |
| PATCH | `/api/administracion/competencias/{competencia_id}/rondas/{ronda_id}/estado` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[RondaOut]}` | registrada |

### `AdminEncuentrosController`

Archivo: `competencias/presentation/controllers/admin_encuentros_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| DELETE | `/api/administracion/competencias/encuentros/{encuentro_id}` | JWT | RequireCompetenciasEscribir | `{204: None}` | registrada |
| POST | `/api/administracion/competencias/encuentros/{encuentro_id}/avance/confirm` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[AvanceOut]}` | registrada |
| POST | `/api/administracion/competencias/encuentros/{encuentro_id}/avance/preview` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[AvancePreviewOut]}` | registrada |
| POST | `/api/administracion/competencias/encuentros/{encuentro_id}/bye` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[EncuentroOut]}` | registrada |
| POST | `/api/administracion/competencias/encuentros/{encuentro_id}/correccion/confirm` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[CorreccionOut]}` | registrada |
| POST | `/api/administracion/competencias/encuentros/{encuentro_id}/correccion/preview` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[CorreccionPreviewOut]}` | registrada |
| POST | `/api/administracion/competencias/encuentros/{encuentro_id}/desenlace` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[EncuentroOut]}` | registrada |
| POST | `/api/administracion/competencias/encuentros/{encuentro_id}/enlace` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[EncuentroOut]}` | registrada |
| PATCH | `/api/administracion/competencias/encuentros/{encuentro_id}/estado` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[EncuentroOut]}` | registrada |
| PATCH | `/api/administracion/competencias/encuentros/{encuentro_id}/participantes` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[EncuentroOut]}` | registrada |
| PATCH | `/api/administracion/competencias/encuentros/{encuentro_id}/programacion` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[EncuentroOut]}` | registrada |
| POST | `/api/administracion/competencias/encuentros/{encuentro_id}/resultado` | JWT | RequireCompetenciasEscribir | `{200: ApiResponse[EncuentroOut]}` | registrada |

### `AdminFundacionController`

Archivo: `administracion/presentation/controllers/admin_fundacion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/administracion/health` | JWT | RequireAdminVer | `{200: ApiResponse[AdminHealthOut]}` | registrada |

### `AdminInscripcionController`

Archivo: `administracion/presentation/controllers/admin_inscripcion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/administracion/inscripciones` | JWT | RequireAdminVer | `{200: ApiResponse[PaginatedData[AdminInscripcionListItemOut]]}` | registrada |
| GET | `/api/administracion/inscripciones/{inscripcion_id}` | JWT | RequireAdminVer | `{200: ApiResponse[AdminInscripcionDetailOut]}` | registrada |

### `AdminOperacionController`

Archivo: `administracion/presentation/controllers/admin_operacion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/administracion/accesos` | JWT | RequireAdminVer | `{200: ApiResponse[PaginatedData[AdminAccesoListItemOut]]}` | registrada |
| GET | `/api/administracion/acreditaciones` | JWT | RequireAdminVer | `{200: ApiResponse[PaginatedData[AdminAcreditacionListItemOut]]}` | registrada |
| GET | `/api/administracion/acreditaciones/{acreditacion_id}` | JWT | RequireAdminVer | `{200: ApiResponse[AdminAcreditacionDetailOut]}` | registrada |
| GET | `/api/administracion/equipos` | JWT | RequireAdminVer | `{200: ApiResponse[PaginatedData[AdminEquipoListItemOut]]}` | registrada |
| GET | `/api/administracion/participaciones` | JWT | RequireAdminVer | `{200: ApiResponse[PaginatedData[AdminParticipacionListItemOut]]}` | registrada |
| GET | `/api/administracion/participantes` | JWT | RequireAdminVer | `{200: ApiResponse[PaginatedData[AdminParticipanteListItemOut]]}` | registrada |

### `AdminPagoController`

Archivo: `administracion/presentation/controllers/admin_pago_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/administracion/pagos` | JWT | RequirePagosVer | `{200: ApiResponse[PaginatedData[AdminPagoListItemOut]]}` | registrada |
| GET | `/api/administracion/pagos/{orden_pago_id}` | JWT | RequirePagosVer | `{200: ApiResponse[AdminPagoDetailOut]}` | registrada |
| POST | `/api/administracion/pagos/{orden_pago_id}/anular-manual` | JWT | RequirePagosAprobar, (sustituye a RequirePagosVer) | `{200: ApiResponse[AdminPagoAnularManualOut]}` | registrada |
| POST | `/api/administracion/pagos/{orden_pago_id}/aprobar-manual` | JWT | RequirePagosAprobar, (sustituye a RequirePagosVer) | `{200: ApiResponse[AdminPagoAprobarManualOut]}` | registrada |

### `AdminPasesController`

Archivo: `administracion/presentation/controllers/admin_pases_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/administracion/pases/compras/{compra_id}/cancelar` | JWT | RequirePagosAprobar, (sustituye a RequirePagosVer) | `{200: ApiResponse[AdminPaseCanceladaOut]}` | registrada |

### `AdminResumenController`

Archivo: `administracion/presentation/controllers/admin_resumen_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/administracion/catalogos` | JWT | RequireAdminVer | `{200: ApiResponse[AdminCatalogosOut]}` | registrada |
| GET | `/api/administracion/resumen` | JWT | RequireAdminVer | `{200: ApiResponse[AdminResumenOut]}` | registrada |

### `AdminUsuarioController`

Archivo: `administracion/presentation/controllers/admin_usuario_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/administracion/usuarios` | JWT | RequireUsuariosVer | `{200: ApiResponse[PaginatedData[AdminUsuarioListItemOut]]}` | registrada |
| GET | `/api/administracion/usuarios/{usuario_id}` | JWT | RequireUsuariosVer | `{200: ApiResponse[AdminUsuarioDetailOut]}` | registrada |

### `AsignacionController`

Archivo: `salesianos_fest/presentation/controllers/asignacion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/asignaciones/` | JWT | IsAuthenticated | `{200: ApiResponse[AsignarPersonaOut]}` | registrada |
| GET | `/api/asignaciones/inscripciones/{inscripcion_id}/asignaciones` | JWT | IsAuthenticated | `{200: ApiResponse[AsignacionListOut]}` | registrada |
| POST | `/api/asignaciones/liberar` | JWT | IsAuthenticated | `{200: ApiResponse[LiberarCupoOut]}` | registrada |
| GET | `/api/asignaciones/{asignacion_id}` | JWT | IsAuthenticated | `{200: ApiResponse[AsignacionDetailOut]}` | registrada |

### `AuthLoginController`

Archivo: `usuarios/presentation/controllers/auth_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/auth/login/dni` | público | AllowAny | `{200: ApiResponse[LoginTokenOut]}` | registrada |
| POST | `/api/auth/login/email` | público | AllowAny | `{200: ApiResponse[LoginTokenOut]}` | registrada |
| POST | `/api/auth/login/username` | público | AllowAny | `{200: ApiResponse[LoginTokenOut]}` | registrada |

### `AuthMeController`

Archivo: `usuarios/presentation/controllers/me_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/auth/me` | JWT | AllowAny (sin permiso explícito) | `{200: ApiResponse[MeOut]}` | registrada |

### `CatalogoController`

Archivo: `salesianos_fest/presentation/controllers/catalogo_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/catalogo/categorias/` | público | AllowAny | `{200: ApiResponse[list[CategoriaOut]]}` | registrada |
| GET | `/api/catalogo/disciplinas/` | público | AllowAny | `{200: ApiResponse[list[DisciplinaOut]]}` | registrada |
| GET | `/api/catalogo/paquetes/` | público | AllowAny | `{200: ApiResponse[list[PaqueteListOut]]}` | registrada |
| GET | `/api/catalogo/paquetes/{paquete_id}/` | público | AllowAny | `{200: ApiResponse[PaqueteDetailOut]}` | registrada |
| GET | `/api/catalogo/promociones/` | público | AllowAny | `{200: ApiResponse[list[PromocionOut]]}` | registrada |

### `CompraController`

Archivo: `salesianos_fest/presentation/controllers/compra_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/compras/` | JWT | IsAuthenticated | `{200: ApiResponse[CompraCreateOut]}` | registrada |
| GET | `/api/compras/inscripciones/{inscripcion_id}/compras` | JWT | IsAuthenticated | `{200: ApiResponse[CompraListOut]}` | registrada |
| GET | `/api/compras/{compra_id}` | JWT | IsAuthenticated | `{200: ApiResponse[CompraDetailOut]}` | registrada |
| POST | `/api/compras/{compra_id}/cancelar` | JWT | IsAuthenticated | `{200: ApiResponse[CompraCanceladaOut]}` | registrada |
| POST | `/api/compras/{compra_id}/iniciar-pago` | JWT | IsAuthenticated | `{200: ApiResponse[IniciarPagoOut]}` | registrada |

### `CotizacionController`

Archivo: `salesianos_fest/presentation/controllers/cotizacion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/cotizaciones/` | público | AllowAny | `{200: ApiResponse[CotizacionResponse]}` | registrada |

### `EquipoController`

Archivo: `salesianos_fest/presentation/controllers/inscripcion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/equipos/` | JWT | IsAuthenticated | `{201: ApiResponse[EquipoOut]}` | registrada |
| GET | `/api/equipos/inscripcion/{inscripcion_id}` | JWT | IsAuthenticated | `{200: ApiResponse[list[EquipoOut]]}` | registrada |
| GET | `/api/equipos/{equipo_id}` | JWT | IsAuthenticated | `{200: ApiResponse[EquipoOut]}` | registrada |

### `IngenieroHabilitadoController`

Archivo: `usuarios/presentation/controllers/ingeniero_habilitado_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/ingenieros/habilitados/{cip}` | público | AllowAny | `{200: ApiResponse[IngenieroHabilitadoOut]}` | **NO registrada (código muerto)** |

### `InscripcionController`

Archivo: `salesianos_fest/presentation/controllers/inscripcion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/inscripciones/` | JWT | IsAuthenticated | `{200: ApiResponse[list[InscripcionOut]]}` | registrada |
| POST | `/api/inscripciones/` | JWT | IsAuthenticated | `{201: ApiResponse[InscripcionOut]}` | registrada |
| POST | `/api/inscripciones/completa/` | JWT | IsAuthenticated | `{201: ApiResponse[InscripcionCompletaOut]}` | registrada |
| GET | `/api/inscripciones/{inscripcion_id}` | JWT | IsAuthenticated | `{200: ApiResponse[InscripcionOut]}` | registrada |
| PATCH | `/api/inscripciones/{inscripcion_id}` | JWT | IsAuthenticated | `{200: ApiResponse[InscripcionOut]}` | registrada |
| GET | `/api/inscripciones/{inscripcion_id}/detalle` | JWT | IsAuthenticated | `{200: ApiResponse[InscripcionDetailOut]}` | registrada |
| GET | `/api/inscripciones/{inscripcion_id}/equipos/{equipo_id}/elegibles` | JWT | IsAuthenticated | `{200: ApiResponse[ElegiblesEquipoOut]}` | registrada |
| POST | `/api/inscripciones/{inscripcion_id}/personas` | JWT | IsAuthenticated | `{201: ApiResponse}` | registrada |
| PATCH | `/api/inscripciones/{inscripcion_id}/personas/{persona_id}/retirar` | JWT | IsAuthenticated | `{200: ApiResponse[InscripcionPersonaOut]}` | registrada |
| GET | `/api/inscripciones/{inscripcion_id}/pool` | JWT | IsAuthenticated | `{200: ApiResponse[PoolOut]}` | registrada |
| POST | `/api/inscripciones/{inscripcion_id}/pool/asignar` | JWT | IsAuthenticated | `{200: ApiResponse}` | registrada |

### `InscripcionSaldoController`

Archivo: `salesianos_fest/presentation/controllers/asignacion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/inscripciones/{inscripcion_id}/saldo` | JWT | IsAuthenticated | `{200: ApiResponse[SaldoOut]}` | registrada |

### `NinjaJWTDefaultController`

Archivo: `django-ninja-jwt (NinjaJWTDefaultController)`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/token/pair` | público | AllowAny (controller de la librería) | `esquema nativo de django-ninja-jwt` | registrada |
| POST | `/api/token/refresh` | público | AllowAny (controller de la librería) | `esquema nativo de django-ninja-jwt` | registrada |
| POST | `/api/token/verify` | público | AllowAny (controller de la librería) | `esquema nativo de django-ninja-jwt` | registrada |

### `PagosController`

Archivo: `pagos/presentation/controllers/pagos_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/pagos/izipay/confirmar` | JWT | IsAuthenticated | `{200: ApiResponse[IzipayConfirmOut]}` | registrada |
| POST | `/api/pagos/izipay/notificacion` | público | AllowAny, (sustituye a IsAuthenticated) | `{200: ApiResponse[IzipayConfirmOut]}` | registrada |
| GET | `/api/pagos/ordenes/{orden_id}` | JWT | IsAuthenticated | `{200: ApiResponse[OrdenPagoOut]}` | registrada |
| GET | `/api/pagos/transacciones/{transaction_id}` | JWT | IsAuthenticated | `{200: ApiResponse[TransaccionPagoOut]}` | registrada |

### `ParticipacionController`

Archivo: `salesianos_fest/presentation/controllers/inscripcion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/participaciones/` | JWT | IsAuthenticated | `{201: ApiResponse[ParticipacionOut]}` | registrada |
| GET | `/api/participaciones/equipo/{equipo_id}` | JWT | IsAuthenticated | `{200: ApiResponse[list[ParticipacionOut]]}` | registrada |
| GET | `/api/participaciones/{participacion_id}` | JWT | IsAuthenticated | `{200: ApiResponse[ParticipacionOut]}` | registrada |
| PATCH | `/api/participaciones/{participacion_id}` | JWT | IsAuthenticated | `{200: ApiResponse[ParticipacionOut]}` | registrada |
| PATCH | `/api/participaciones/{participacion_id}/mover` | JWT | IsAuthenticated | `{200: ApiResponse[ParticipacionOut]}` | registrada |
| PATCH | `/api/participaciones/{participacion_id}/retirar` | JWT | IsAuthenticated | `{200: ApiResponse[ParticipacionOut]}` | registrada |

### `PaseController`

Archivo: `salesianos_fest/presentation/controllers/pase_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/pases/` | público | AllowAny | `{200: ApiResponse[list[PaseListOut]]}` | registrada |
| POST | `/api/pases/comprar` | JWT | IsAuthenticated, (sustituye a AllowAny) | `{200: ApiResponse[PaseCompraCreadaOut]}` | registrada |
| GET | `/api/pases/compras/{compra_id}` | JWT | IsAuthenticated, (sustituye a AllowAny) | `{200: ApiResponse[PaseCompraEstadoOut]}` | registrada |
| GET | `/api/pases/compras/{compra_id}/beneficiarios` | JWT | IsAuthenticated, (sustituye a AllowAny) | `{200: ApiResponse[PaseBeneficiariosListaOut]}` | registrada |
| POST | `/api/pases/compras/{compra_id}/beneficiarios` | JWT | IsAuthenticated, (sustituye a AllowAny) | `{200: ApiResponse[PaseBeneficiariosAsignadosOut]}` | registrada |
| DELETE | `/api/pases/compras/{compra_id}/beneficiarios/{persona_id}` | JWT | IsAuthenticated, (sustituye a AllowAny) | `{200: ApiResponse[PaseBeneficiarioRevocadoOut]}` | registrada |

### `PersonaBusquedaController`

Archivo: `usuarios/presentation/controllers/persona_busqueda_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/personas/busqueda/{documento}` | público | AllowAny | `{200: ApiResponse[DocumentoConsultaOut]}` | registrada |

### `PersonaResolucionController`

Archivo: `usuarios/presentation/controllers/persona_resolucion_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/personas/resolver` | JWT | IsAuthenticated, (sustituye a AllowAny) | `{200: ApiResponse[PersonaResueltaOut]}` | registrada |

### `PublicCompetenciasController`

Archivo: `competencias/presentation/controllers/public_competencias_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| GET | `/api/competencias/` | público | AllowAny | `{200: ApiResponse[list[CompetenciaListOut]]}` | registrada |
| GET | `/api/competencias/encuentros` | público | AllowAny | `{200: ApiResponse[list[EncuentroOut]]}` | registrada |
| GET | `/api/competencias/{competencia_id}` | público | AllowAny | `{200: ApiResponse[CompetenciaDetalleOut]}` | registrada |
| GET | `/api/competencias/{competencia_id}/cuadro` | público | AllowAny | `{200: ApiResponse[CuadroOut]}` | registrada |

### `RegistroController`

Archivo: `usuarios/presentation/controllers/registro_controller.py`

| Método | Ruta | Auth | Permiso efectivo | Wrapper de respuesta | Estado |
|---|---|---|---|---|---|
| POST | `/api/auth/register` | público | AllowAny | `{200: ApiResponse[RegisterOut]}` | registrada |

---

## 5. Superficie escrita pero no registrada

| Controlador | Archivo | Ruta declarada | Situación |
|---|---|---|---|
| `IngenieroHabilitadoController` | `usuarios/presentation/controllers/ingeniero_habilitado_controller.py` | `GET /api/ingenieros/habilitados/{cip}` | El controlador existe con su decorador `@api_controller("/ingenieros", …)`, pero **no** aparece en `api.register_controllers(...)` dentro de `backend/config/api.py`. La ruta no es alcanzable. No se localizó un consumidor en el frontend |

Decisión pendiente: registrar el controlador o eliminarlo. Mientras exista, es superficie de API documentada en el código y ausente del contrato HTTP.

---

## 6. Observaciones de política

- **Las rutas públicas** (20) son: los tres logins, el registro, la búsqueda de documento por código, las cinco del catálogo, la cotización, el catálogo de pases, la notificación Izipay del servidor a servidor, las tres de `django-ninja-jwt` y las cuatro públicas de competencias.
- **`POST /api/pagos/izipay/notificacion`** es pública por necesidad del proveedor: la firma del comercio se verifica dentro del flujo, no en la capa HTTP. La ruta declara `permissions=[AllowAny]`, lo que **reemplaza** el `IsAuthenticated` del controlador `PagosController`.
- **`GET /api/auth/me`** no declara permisos en ningún nivel: la única exigência es el token válido. Es coherente con que la respuesta incluye el nivel de permisos del actor.
- **Las rutas de aprobación y anulación manual de pagos** (3) declaran `RequirePagosAprobar`, que **sustituye** a `RequirePagosVer` del controlador. Ningún rol salvo `superusuario` las puede ejecutar: la capacidad `admin.pagos.aprobar` está fuera del conjunto de `staff`.
- **Las rutas de lectura de administración** (13) declaran `RequireAdminVer`, `RequirePagosVer` o `RequireUsuariosVer` a nivel de controlador, sin sobrescritura por ruta.
- **Las rutas de competencias** exigen `RequireCompetenciasEscribir` incluso para **lectura** (`GET /administracion/competencias`, `agenda`, `cuadro`, listados de rondas y encuentros). El nombre de la capacidad es de escritura, pero cubre el acceso completo a la superficie administrativa de competencias.
- **Las rutas de propiedad** (inscripciones, equipos, participaciones, compras, asignaciones, saldo) declaran sólo `IsAuthenticated` y añaden la verificación de titularidad en código, mediante los helpers de `modules/salesianos_fest/presentation/ownership.py`. El permiso por rol no basta: el responsable de la inscripción y un admin Django son los únicos actores admitidos. La cobertura exacta de estos helpers por ruta no fue auditada en esta revisión.
- **Las dos respuestas sin tipar** (`POST /api/inscripciones/{inscripcion_id}/personas` y `POST /api/inscripciones/{inscripcion_id}/pool/asignar`) rompen el espejo de esquemas con el frontend y no permiten validación de la carga útil en el cliente.

---

## 7. Documentos relacionados

- [README.md](README.md) — índice navegable del conjunto documental.
- [00-cobertura-y-trazabilidad.md](00-cobertura-y-trazabilidad.md) — metodología de auditoría y recuentos de cobertura verificados.
- [02-backend-y-api.md](02-backend-y-api.md) — arquitectura del servicio, contratos de request/response/error y política de autenticación y autorización.
- [02b-proposito-y-consumidores-de-endpoints.md](02b-proposito-y-consumidores-de-endpoints.md) — para cada ruta de este inventario: propósito de negocio, consumidor real, cadena de ejecución y efectos.
- [03-frontend.md](03-frontend.md) — capa de frontend, consumidores de estas rutas.
- [04-datos-y-dominio.md](04-datos-y-dominio.md) — modelo de datos y dominio.
- [05-flujos-end-to-end.md](05-flujos-end-to-end.md) — recorridos de extremo a extremo.
