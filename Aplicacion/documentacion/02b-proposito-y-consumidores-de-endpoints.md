# Propósito funcional y consumidores de cada endpoint — API Salesianos FEST

> **Servicio:** backend Django 5 + `django-ninja-extra`, montado en `/api/` por `backend/config/urls.py`.
> **Prefijo público en el navegador:** `/backend` — el proxy nginx (`proxy/nginx.conf`) reescribe `/backend/*` → `/api/*` y reserva `/api/auth/{refresh,logout}` para el frontend Next.js. Las rutas de este documento son las que ve Django; el navegador las consume con el prefijo `/backend`.
> **Documento par:** [02a-inventario-de-endpoints.md](02a-inventario-de-endpoints.md) (inventario método/ruta/auth/permiso/wrapper). Este documento **no repite ese inventario**: añade, endpoint por endpoint, el propósito de negocio, el consumidor real del frontend, la cadena de ejecución, los datos tocados, las invariantes y las implicaciones de error.
> **Contratos aplicados:** `contract/django-app-architecture-contract.md`, `contract/api-wrapper-presenter-contract.md`, `contract/next-app-architecture-contract.md`, `contract/TEST_ARCHITECTURE_CONTRACT.md`.

---

## 1. Método de verificación y alcance

### 1.1 Qué se leyó

1. **Registro runtime.** Se arrancó Django con `backend/.venv` y se recorrió `config.api.api._routers` (29 routers) leyendo `path_operations → PathView.operations` para extraer método, ruta completa, función de vista y `auth_callbacks` reales. **111 rutas registradas**, verificadas de primera mano en esta revisión.
2. **Código de aplicación.** Los 23 archivos bajo `backend/modules/**/presentation/controllers/`, los orquestadores/flujos/servicios core/selectores/presenters/esquemas de cada módulo, `core/{responses,pagination,exceptions,capacidades,permissions,security}.py`, `modules/salesianos_fest/presentation/ownership.py` y la lista real de tablas (`sqlite_master` sobre `backend/db.sqlite3`, sólo lectura).
3. **Consumidores frontend.** Barrido de `frontend/src` (excluyendo `_legacy*`, que es material heredado sin router) buscando literales de ruta y llamadas `api.get/post/patch/delete`; después se resuelve la cadena *servicio → hook → componente → página Next.js*.
4. **Artefactos Engram** `sdd/explore/rebuild-backend-api-map`, `sdd/explore/rebuild-flows-infrastructure-map` (+ apéndice) y `sdd/explore/application-rebuild-architecture-documentation`, usados como contexto; **la fuente de verdad es el código de runtime**.

### 1.2 Reglas de lectura

| Etiqueta | Significado |
|---|---|
| **Auth** | `JWT` = exige `Authorization: Bearer <token>` válido. `público` = la ruta declara `auth=None` y anula el `JWTAuth()` global de la API. |
| **Permiso efectivo** | Permiso realmente evaluado. La lista de permisos de la **ruta reemplaza** la del controlador (`ninja_extra/operation.py`: `route.permissions or controller.permission_classes`). Se indica entre paréntesis el permiso del controlador que queda anulado. |
| **Consumidor** | Archivo y función del frontend que emite la llamada. Si no existe, se marca **«sin consumidor conocido»** y se justifica. |
| **Cadena** | `Controller → Orchestrator → Flujo → Core/Selector → Presenter → Schema Out`. Los controllers de `salesianos_fest` que saltan la capa de orquestador están marcados como **acceso directo a selector**. |
| **Tablas** | Nombres reales de tabla (`db_table` / `<app_label>_<model>`). `lectura` / `escritura`. |
| **Efectos** | Efectos externos: envío de correo, pago al proveedor, emisión de credencial, auditoría. |

### 1.3 Conteo de cobertura

| Métrica | Valor |
|---|---|
| Rutas registradas en runtime (verificadas en esta revisión) | **111** |
| Routers registrados | 29 (28 del proyecto + `NinjaJWTDefaultController` de `django-ninja-jwt`) |
| Controladores escritos y **no** registrados | 1 (`IngenieroHabilitadoController` → `GET /api/ingenieros/habilitados/{cip}`) |
| Rutas públicas (`auth=None`) | 20 |
| Rutas con **consumidor en el frontend** (servicio → hook → componente renderizado, o route handler de Next) | **68** |
| Rutas con **código de servicio/hook en el frontend pero sin vista que las invoque** | 2 (`POST /api/inscripciones/`, `GET /api/catalogo/paquetes/{paquete_id}/`) |
| Rutas con **consumidor no-frontend** (proveedor externo) | 1 (`POST /api/pagos/izipay/notificacion` ← servidor de Izipay) |
| Rutas **sin ninguna referencia** en `frontend/src` | **40** |
| Documentadas en este archivo | **111 / 111 (100 %)** |

**Cuadre:** 68 + 2 + 1 + 40 = **111** rutas registradas. Sumando la ruta escrita y no registrada (`GET /api/ingenieros/habilitados/{cip}`) hay **112 definiciones de ruta en código**.

> **Criterio de «consumidor».** Una ruta cuenta como *con consumidor en el frontend* cuando existe código de `frontend/src` que **emite la llamada** y ese código está **alcanzado por una vista renderizada** (o por un route handler de Next). Una función de servicio o un hook exportado **sin ninguna vista que lo use** no cuenta: es código de transporte preparado pero no conectado. Este criterio es el mismo que aplica [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) § 6.2; ambos documentos deben leerse con esta definición para que sus recuentos coincidan.

**Verificación de cobertura:** el número de fichas de endpoint de §4 a §10 (111) coincide con el número de operaciones registradas en runtime (111) y con el total declarado en [02a](02a-inventario-de-endpoints.md). No hay rutas registradas sin ficha ni fichas sin ruta registrada. La única ruta *escrita en código* y no registrada se documenta aparte en §17.1, porque no forma parte del contrato HTTP vigente.

### 1.4 Mapa de dominios

| # | Dominio | Rutas | Prefijo |
|---|---|---|---|
| 1 | Autenticación y sesión | 8 | `/api/auth`, `/api/token` |
| 2 | Personas | 2 | `/api/personas` |
| 3 | Catálogo y cotización | 6 | `/api/catalogo`, `/api/cotizaciones` |
| 4 | Pases de fiesta | 6 | `/api/pases` |
| 5 | Inscripción deportiva | 12 | `/api/inscripciones` |
| 6 | Equipos y participaciones | 9 | `/api/equipos`, `/api/participaciones` |
| 7 | Compras y asignaciones de cupo | 9 | `/api/compras`, `/api/asignaciones` |
| 8 | Pagos Izipay | 4 | `/api/pagos` |
| 9 | Acreditación y acceso | 4 | `/api/acreditaciones`, `/api/acceso` |
| 10 | Administración operativa | 18 | `/api/administracion` (+ `/administracion/pases`) |
| 11 | Competencias | 33 | `/api/administracion/competencias`, `/api/competencias` |
| | **Total** | **111** | |

---

## 2. Índice inverso: endpoint → consumidor frontend

Ordenado por ruta. `—` significa **sin consumidor conocido**.

| # | Método | Ruta | Consumidor frontend |
|---|---|---|---|
| 1 | POST | `/api/token/pair` | — |
| 2 | POST | `/api/token/refresh` | `app/api/auth/refresh/route.ts` (route handler de Next.js, no navegador) |
| 3 | POST | `/api/token/verify` | — |
| 4 | POST | `/api/auth/login/username` | `features/auth/hooks/useLogin.ts` → `app/(auth)/login/page.tsx` |
| 5 | POST | `/api/auth/login/dni` | `features/auth/hooks/useLogin.ts` → `app/(auth)/login/page.tsx` |
| 6 | POST | `/api/auth/login/email` | `features/auth/hooks/useLogin.ts` → `app/(auth)/login/page.tsx` |
| 7 | POST | `/api/auth/register` | `features/auth/services/register.service.ts` → `features/auth/hooks/useRegister.ts` → `app/(auth)/register/page.tsx` |
| 8 | GET | `/api/auth/me` | `features/admin/services/admin.me.service.ts` → `useAdminSession`, `features/auth/utils/resolver-destino.ts`, `features/admin/services/admin.session.server.ts` (guard servidor) |
| 9 | GET | `/api/personas/busqueda/{documento}` | `features/inscripciones/services/inscripcion.service.ts` (`consultarDocumento`) → `useDocumentoLookup` → `components/forms/DocumentoLookupSmartField.tsx` |
| 10 | GET | `/api/personas/resolver` | `features/pases/services/persona.resolucion.service.ts` → `useResolverPersona` → `components/PaseLookupPersonaField.tsx` |
| 11 | GET | `/api/catalogo/disciplinas/` | `features/inscripciones/services/catalog.service.ts` → `useInscripcionCatalogs`; además `features/portada/hooks/useCatalogo.ts` → `components/portada/{ChampionshipSection,ScheduleSection}.tsx` |
| 12 | GET | `/api/catalogo/categorias/` | `features/inscripciones/services/catalog.service.ts` → `useInscripcionCatalogs`; además `features/portada/hooks/useCatalogo.ts` |
| 13 | GET | `/api/catalogo/paquetes/` | `features/inscripciones/services/{catalog,paquete}.service.ts` → `useInscripcionCatalogs`; `features/landing/paquetes.service.ts` → `useLandingPaquetes` → `components/landing/Paquetes*.tsx` |
| 14 | GET | `/api/catalogo/paquetes/{paquete_id}/` | — (código de transporte sin vista: `features/inscripciones/services/{catalog,paquete}.service.ts` → `usePaqueteDetail` / `usePaqueteDisciplinas`, hooks exportados y **sin uso** en ninguna vista) |
| 15 | GET | `/api/catalogo/promociones/` | `features/inscripciones/services/catalog.service.ts` → `useInscripcionCatalogs` |
| 16 | POST | `/api/cotizaciones/` | `features/inscripciones/services/cotizacion.service.ts` → `useCotizacion` → `components/InscripcionWizard.tsx` |
| 17 | GET | `/api/pases/` | `features/pases/services/pase.service.ts` → `usePasesCatalogo` → `app/(app)/pases/page.tsx` |
| 18 | POST | `/api/pases/comprar` | `features/pases/services/pase.service.ts` → `useCompraPase` → `views/PaseCompraView.tsx` |
| 19 | GET | `/api/pases/compras/{compra_id}` | `features/pases/services/pase.service.ts` → `useCompraPaseEstado` → `views/PaseCompraView.tsx` |
| 20 | GET | `/api/pases/compras/{compra_id}/beneficiarios` | `features/pases/services/pase.beneficiario.service.ts` → `useBeneficiariosCompra` → `components/PaseBeneficiariosPanel.tsx` |
| 21 | POST | `/api/pases/compras/{compra_id}/beneficiarios` | `features/pases/services/pase.beneficiario.service.ts` → `useAsignarBeneficiarios` |
| 22 | DELETE | `/api/pases/compras/{compra_id}/beneficiarios/{persona_id}` | `features/pases/services/pase.beneficiario.service.ts` → `useRevocarBeneficiario` → `components/PaseRevocarDialog.tsx` |
| 23 | POST | `/api/acceso/registrar` | — |
| 24 | GET | `/api/acreditaciones/{evento_id}/{persona_id}` | — |
| 25 | POST | `/api/acreditaciones/{evento_id}/{persona_id}/generar-qr` | — |
| 26 | PATCH | `/api/acreditaciones/{evento_id}/{persona_id}/override-fiesta` | — |
| 27 | GET | `/api/inscripciones/` | `features/inscripciones/services/inscripcion.service.ts` (`getMisInscripciones`) → `app/(app)/dashboard/page.tsx` |
| 28 | POST | `/api/inscripciones/` | — (código de transporte sin vista: `features/inscripciones/services/inscripcion.service.ts` (`createInscripcion`) → `useCreateInscripcion`, hook exportado y **sin uso**; el asistente usa `/inscripciones/completa/`) |
| 29 | POST | `/api/inscripciones/completa/` | `features/inscripciones/services/inscripcion.service.ts` (`createInscripcionCompleta`) → `useCreateInscripcionCompleta` → `components/InscripcionWizard.tsx` |
| 30 | GET | `/api/inscripciones/{inscripcion_id}` | — |
| 31 | PATCH | `/api/inscripciones/{inscripcion_id}` | — |
| 32 | GET | `/api/inscripciones/{inscripcion_id}/detalle` | `features/inscripciones/services/inscripcion.service.ts` → `useInscripcionDetalle` → `views/InscripcionDetailView.tsx` → `app/(app)/dashboard/inscripcion/[id]/page.tsx` |
| 33 | GET | `/api/inscripciones/{inscripcion_id}/pool` | `features/inscripciones/services/pool.service.ts` (`getPool`) → `useInscripcionPool` → `components/PoolParticipantesSeccion.tsx` |
| 34 | POST | `/api/inscripciones/{inscripcion_id}/pool/asignar` | `features/inscripciones/services/pool.service.ts` (`asignarPoolAEquipo`) → `useAsignarParticipanteAEquipo` → `components/SelectorParticipanteModal.tsx` |
| 35 | GET | `/api/inscripciones/{inscripcion_id}/equipos/{equipo_id}/elegibles` | `features/inscripciones/services/elegibles.service.ts` → `useElegiblesEquipo` → `components/SelectorParticipanteModal.tsx` |
| 36 | POST | `/api/inscripciones/{inscripcion_id}/personas` | `features/inscripciones/services/pool.service.ts` (`preregistrarEnPool`) → `usePreregistrarEnPool` → `components/AddParticipanteModal.tsx` |
| 37 | PATCH | `/api/inscripciones/{inscripcion_id}/personas/{persona_id}/retirar` | — |
| 38 | GET | `/api/inscripciones/{inscripcion_id}/saldo` | `features/inscripciones/services/pool.service.ts` (`getSaldoInscripcion`) → `useAsignarParticipanteAEquipo`, `components/PoolParticipantesSeccion.tsx` |
| 39 | POST | `/api/equipos/` | — |
| 40 | GET | `/api/equipos/{equipo_id}` | — |
| 41 | GET | `/api/equipos/inscripcion/{inscripcion_id}` | — |
| 42 | POST | `/api/participaciones/` | — |
| 43 | GET | `/api/participaciones/{participacion_id}` | — |
| 44 | GET | `/api/participaciones/equipo/{equipo_id}` | — |
| 45 | PATCH | `/api/participaciones/{participacion_id}` | `features/inscripciones/services/inscripcion.service.ts` (`editarParticipante`) → `useEditarParticipante` → `components/EditParticipanteModal.tsx` |
| 46 | PATCH | `/api/participaciones/{participacion_id}/mover` | — |
| 47 | PATCH | `/api/participaciones/{participacion_id}/retirar` | `features/inscripciones/services/inscripcion.service.ts` (`eliminarParticipante`) → `useEditarParticipante` → `components/EditParticipanteModal.tsx` |
| 48 | POST | `/api/compras/` | — |
| 49 | GET | `/api/compras/{compra_id}` | — |
| 50 | GET | `/api/compras/inscripciones/{inscripcion_id}/compras` | — |
| 51 | POST | `/api/compras/{compra_id}/iniciar-pago` | `features/pagos/services/pago.service.ts` (`iniciarPagoIzipay`) → `components/IzipayModal.tsx` |
| 52 | POST | `/api/compras/{compra_id}/cancelar` | — |
| 53 | POST | `/api/asignaciones/` | — |
| 54 | GET | `/api/asignaciones/{asignacion_id}` | — |
| 55 | POST | `/api/asignaciones/liberar` | — |
| 56 | GET | `/api/asignaciones/inscripciones/{inscripcion_id}/asignaciones` | — |
| 57 | POST | `/api/pagos/izipay/confirmar` | `features/pagos/services/pago.service.ts` (`confirmarPagoIzipay`) → `components/IzipayModal.tsx` |
| 58 | POST | `/api/pagos/izipay/notificacion` | **Proveedor Izipay (servidor a servidor)** — no es consumidor de navegador |
| 59 | GET | `/api/pagos/transacciones/{transaction_id}` | `features/pagos/services/pago.service.ts` (`obtenerEstadoTransaccion`) → `components/IzipayModal.tsx`, `utils/checkout.recuperacion.ts` |
| 60 | GET | `/api/pagos/ordenes/{orden_id}` | — |
| 61 | GET | `/api/administracion/health` | — |
| 62 | GET | `/api/administracion/resumen` | `features/admin/services/admin.resumen.service.ts` → `useAdminResumen` → `components/AdminOverview.tsx` → `app/(app)/administracion/page.tsx` |
| 63 | GET | `/api/administracion/catalogos` | `features/admin/services/admin.resumen.service.ts` → `useAdminCatalogos` → `Admin*Lista.tsx` (filtros de todas las tablas) |
| 64 | GET | `/api/administracion/inscripciones` | `features/admin/services/admin.inscripcion.service.ts` → `useAdminInscripciones` → `components/AdminInscripcionesLista.tsx` → `app/(app)/administracion/inscripciones/page.tsx` |
| 65 | GET | `/api/administracion/inscripciones/{inscripcion_id}` | `features/admin/services/admin.inscripcion.service.ts` → `useAdminInscripciones` (detalle) → `components/AdminInscripcionDetalle.tsx` → `app/(app)/administracion/inscripciones/[id]/page.tsx` |
| 66 | GET | `/api/administracion/pagos` | `features/admin/services/admin.pago.service.ts` → `useAdminPagos` → `components/AdminPagosLista.tsx` → `app/(app)/administracion/pagos/page.tsx` |
| 67 | GET | `/api/administracion/pagos/{orden_pago_id}` | `features/admin/services/admin.pago.service.ts` → `useAdminPagos` (detalle) → `components/AdminPagosLista.tsx` |
| 68 | POST | `/api/administracion/pagos/{orden_pago_id}/aprobar-manual` | `features/admin/services/admin.pago.service.ts` → `useAdminPagosComandos` → `components/AdminPagoManualDialog.tsx` |
| 69 | POST | `/api/administracion/pagos/{orden_pago_id}/anular-manual` | `features/admin/services/admin.pago.service.ts` → `useAdminPagosComandos` → `components/AdminPagoManualDialog.tsx` |
| 70 | GET | `/api/administracion/equipos` | `features/admin/services/admin.operacion.service.ts` → `useAdminEquipos` → `components/AdminEquiposLista.tsx` → `app/(app)/administracion/equipos/page.tsx` |
| 71 | GET | `/api/administracion/participantes` | `features/admin/services/admin.operacion.service.ts` → `useAdminParticipantes` → `components/AdminParticipantesLista.tsx` → `app/(app)/administracion/participantes/page.tsx` |
| 72 | GET | `/api/administracion/participaciones` | `features/admin/services/admin.operacion.service.ts` → `useAdminParticipantes` (sección roster) → `components/AdminParticipantesLista.tsx` |
| 73 | GET | `/api/administracion/acreditaciones` | `features/admin/services/admin.operacion.service.ts` → `useAdminAcreditaciones` → `components/AdminAcreditacionesLista.tsx` → `app/(app)/administracion/acreditaciones/page.tsx` |
| 74 | GET | `/api/administracion/acreditaciones/{acreditacion_id}` | `features/admin/services/admin.operacion.service.ts` → `useAdminAcreditacionDetalle` → `components/AdminAcreditacionesLista.tsx` |
| 75 | GET | `/api/administracion/accesos` | `features/admin/services/admin.operacion.service.ts` → `useAdminAccesos` → `components/AdminAcreditacionesLista.tsx` (sección accesos) |
| 76 | GET | `/api/administracion/usuarios` | `features/admin/services/admin.usuario.service.ts` → `useAdminUsuarios` → `components/AdminUsuariosLista.tsx` → `app/(app)/administracion/usuarios/page.tsx` |
| 77 | GET | `/api/administracion/usuarios/{usuario_id}` | `features/admin/services/admin.usuario.service.ts` → `useAdminUsuarios` (detalle) → `components/AdminUsuariosLista.tsx` |
| 78 | POST | `/api/administracion/pases/compras/{compra_id}/cancelar` | `features/admin/pases/services/admin.pase.service.ts` → `features/admin/pases/hooks/useAdminPaseComandos.ts` → `components/AdminPaseCancelarDialog.tsx` → `app/(app)/administracion/pagos/page.tsx` |
| 79 | GET | `/api/administracion/competencias` | `features/admin/competencias/services/competencias.service.ts` → `useCompetencias` → `components/CompetenciasLista.tsx` → `app/(app)/administracion/competencias/page.tsx` |
| 80 | POST | `/api/administracion/competencias` | — (sin código de transporte en el frontend: `competencias.comandos.service.ts` **no expone** alta de competencia y `components/editors/CompetenciaEditorModal.tsx` es sólo un marco de modal) |
| 81 | GET | `/api/administracion/competencias/agenda` | `features/admin/competencias/services/competencias.service.ts` → `useCompetencias` → `components/CompetenciasAgenda.tsx` → `app/(app)/administracion/competencias/agenda/page.tsx` |
| 82 | GET | `/api/administracion/competencias/{competencia_id}` | `features/admin/competencias/services/competencias.service.ts` → `useCompetencias` → `components/CompetenciasDetalle.tsx` → `app/(app)/administracion/competencias/[id]/page.tsx` |
| 83 | PATCH | `/api/administracion/competencias/{competencia_id}` | — (sin código de transporte en el frontend: `competencias.comandos.service.ts` **no expone** edición de competencia) |
| 84 | PATCH | `/api/administracion/competencias/{competencia_id}/estado` | — (sin código de transporte en el frontend: `competencias.comandos.service.ts` **no expone** cambio de estado de competencia) |
| 85 | DELETE | `/api/administracion/competencias/{competencia_id}` | — (sin código de transporte en el frontend: `competencias.comandos.service.ts` **no expone** borrado de competencia) |
| 86 | GET | `/api/administracion/competencias/{competencia_id}/cuadro` | `features/admin/competencias/services/competencias.service.ts` → `useCompetencias` → `components/CompetenciasCuadro.tsx` → `app/(app)/administracion/competencias/cuadro/page.tsx` |
| 87 | GET | `/api/administracion/competencias/{competencia_id}/equipos` | — (sin código de transporte en el frontend: `competencias.service.ts` sólo expone lista, detalle, agenda y cuadro; el detalle ya trae los equipos) |
| 88 | POST | `/api/administracion/competencias/{competencia_id}/equipos` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEquipoEditor.tsx` |
| 89 | PATCH | `/api/administracion/competencias/{competencia_id}/equipos/{competencia_equipo_id}` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEquipoEditor.tsx` |
| 90 | GET | `/api/administracion/competencias/{competencia_id}/rondas` | — (sin código de transporte en el frontend: `competencias.service.ts` **no expone** lectura de rondas) |
| 91 | POST | `/api/administracion/competencias/{competencia_id}/rondas` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaRondaEditor.tsx` |
| 92 | PATCH | `/api/administracion/competencias/{competencia_id}/rondas/{ronda_id}` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaRondaEditor.tsx` |
| 93 | PATCH | `/api/administracion/competencias/{competencia_id}/rondas/{ronda_id}/estado` | — (sin código de transporte en el frontend: `competencias.comandos.service.ts` **no expone** invalidación de ronda) |
| 94 | GET | `/api/administracion/competencias/{competencia_id}/encuentros` | — (sin código de transporte en el frontend: `competencias.service.ts` **no expone** lectura de encuentros; el detalle ya los trae) |
| 95 | POST | `/api/administracion/competencias/{competencia_id}/encuentros` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEncuentroEditor.tsx` |
| 96 | PATCH | `/api/administracion/competencias/encuentros/{encuentro_id}/participantes` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEncuentroEditor.tsx` |
| 97 | PATCH | `/api/administracion/competencias/encuentros/{encuentro_id}/programacion` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaProgramacionEditor.tsx` |
| 98 | PATCH | `/api/administracion/competencias/encuentros/{encuentro_id}/estado` | — (sin código de transporte en el frontend: `CompetenciasAccionesEncuentro.tsx` abre los editores de *programación*, *bye* y *enlace*, no de estado) |
| 99 | POST | `/api/administracion/competencias/encuentros/{encuentro_id}/bye` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaByeEditor.tsx` |
| 100 | POST | `/api/administracion/competencias/encuentros/{encuentro_id}/enlace` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEnlaceEditor.tsx` |
| 101 | POST | `/api/administracion/competencias/encuentros/{encuentro_id}/desenlace` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEnlaceEditor.tsx` |
| 102 | POST | `/api/administracion/competencias/encuentros/{encuentro_id}/resultado` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaResultadoDialog.tsx` |
| 103 | POST | `/api/administracion/competencias/encuentros/{encuentro_id}/avance/preview` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaAvanceDialog.tsx` |
| 104 | POST | `/api/administracion/competencias/encuentros/{encuentro_id}/avance/confirm` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaAvanceDialog.tsx` |
| 105 | POST | `/api/administracion/competencias/encuentros/{encuentro_id}/correccion/preview` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaCorreccionDialog.tsx` |
| 106 | POST | `/api/administracion/competencias/encuentros/{encuentro_id}/correccion/confirm` | `features/admin/competencias/services/competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaCorreccionDialog.tsx` |
| 107 | DELETE | `/api/administracion/competencias/encuentros/{encuentro_id}` | — (sin código de transporte en el frontend: `competencias.comandos.service.ts` **no expone** borrado de encuentro) |
| 108 | GET | `/api/competencias` | — |
| 109 | GET | `/api/competencias/encuentros` | — |
| 110 | GET | `/api/competencias/{competencia_id}` | — |
| 111 | GET | `/api/competencias/{competencia_id}/cuadro` | — |

> Nota de exactitud: las rutas de la tabla son las que emite el runtime, sin abreviaturas; los identificadores de path (`{encuentro_id}`, `{competencia_id}`, …) son los literales de la URL pública.

---

## 3. Contrato transversal de respuesta y error

### 3.1 Envoltura de éxito

Todo endpoint responde con `ApiResponse[T]` (`backend/core/responses.py`):

```json
{ "success": true, "data": { ... }, "error": null, "message": "…" }
```

- `data`: el payload tipado del esquema `*Out` del módulo. Los `Decimal` se serializan como número JSON.
- `message`: texto fijo, en español, definido por el controller. Los endpoints de lectura suelen devolver `null`.
- Los listados paginados usan `ApiResponse[PaginatedData[X]]`: `data = { items[], total, page, page_size, total_pages }` (`backend/core/pagination.py`). El tipo `PaginatedApiResponse` existe pero **no lo usa ninguna ruta**.

### 3.2 Envoltura de error

```json
{ "success": false, "data": null, "error": { "code": "…", "message": "…", "details": { … } } }
```

Traducción única en `backend/core/exceptions.py` (`register_exception_handlers`):

| Excepción / situación | HTTP | `code` |
|---|---|---|
| Token ausente, inválido, expirado o revocado | 401 | `AUTHENTICATION_REQUIRED` |
| Permiso insuficiente (incluye `ForbiddenError`) | 403 | `ACTION_NOT_ALLOWED` |
| `NotFoundError` con código propio | 404 | código del dominio (p. ej. `COMPETENCIA_NOT_FOUND`) |
| `ObjectDoesNotExist` sin código | 404 | `NOT_FOUND` |
| `PermissionDenied` de Django | 403 | `PERMISSION_DENIED` |
| Validación Pydantic / Ninja | 422 | `VALIDATION_ERROR` |
| `DjangoValidationError` | 400 | `VALIDATION_ERROR` |
| `BusinessError` | 400 | código del dominio o `BUSINESS_ERROR` |
| `ConflictError` | 409 | código del dominio o `CONFLICT` |
| `ValueError` (credenciales inválidas) | 401 | `AUTH_ERROR` |
| `IntegrityError` no controlada | 409 | `CONFLICT` |
| Excepción inesperada | 500 | `INTERNAL_ERROR` |

El mensaje público **nunca** lo decide la excepción: sale del catálogo `PUBLIC_ERROR_MESSAGES` de `core/exceptions.py`. Consecuencia práctica para el consumidor: un 409 de negocio y un 409 de concurrencia se distinguen por `error.code`, no por el texto.

### 3.3 Recuperación desde el frontend

`frontend/src/lib/api.ts` centraliza el transporte: inyecta `Authorization: Bearer` desde la cookie `httpOnly`, refresca proactivamente cuando el token caduca en < 5 min y, ante un 401, intenta **un** refresco y reintenta la petición original (`_retry`). Si el refresco falla, el 401 se propaga y la UI debe redirigir al login. `handleApiError` (`frontend/src/errors/error-handler.ts`) traduce el envelope de error a un mensaje mostrable.

---

## 4. Dominio 1 — Autenticación y sesión (8 rutas)

Contexto común: `AUTH_USER_MODEL = "usuarios.Usuario"`; `NINJA_JWT` con `ACCESS_TOKEN_LIFETIME = 1 h`, `REFRESH_TOKEN_LIFETIME = 7 d`, `ROTATE_REFRESH_TOKENS = True`, `BLACKLIST_AFTER_ROTATION = True`, cabecera `Bearer`. El backend **no** usa el login built-in de `django-ninja-jwt`: expone su propio login modular y sólo deja las tres rutas `/api/token/*` de la librería.

### 4.1 `POST /api/token/pair`

- **Propósito:** emitir un par access/refresh token validando credenciales contra `usuarios.Usuario`. Es la superficie built-in de la librería, disponible pero **no usada por el frontend** (el login propio la suplanta).
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidor:** **sin consumidor conocido**. Ningún archivo de `frontend/src` invoca `/token/pair`.
- **Entrada:** body `{ username, password }` (esquema nativo `TokenObtainPairRequest`).
- **Validación:** la de `django-ninja-jwt` (credenciales y usuario activo).
- **Controller:** `django-ninja-jwt` — `NinjaJWTDefaultController.obtain_token` (registrado en `backend/config/api.py`).
- **Cadena:** Controller → `ninja_jwt` (vista de la librería) → ORM `usuarios_usuario` → esquema nativo `TokenObtainPairOut` (**no** envuelto en `ApiResponse`).
- **Modelos/tablas:** lectura `usuarios_usuario`; escritura `token_blacklist_outstandingtoken` / `token_blacklist_blacklistedtoken` al rotar.
- **Efectos:** emisión de tokens; bloqueo del refresh anterior en la lista negra.
- **Invariantes:** nunca devuelve credenciales; el token no lleva datos sensibles.
- **Respuesta:** `{ access, refresh }` (esquema nativo, **fuera** del wrapper `ApiResponse`).
- **Errores:** 401 `HTTP_ERROR` por credenciales inválidas; 422 por payload malformado.
- **Estado:** registrada (runtime) · **superficie duplicada sin consumidor**.

### 4.2 `POST /api/token/refresh`

- **Propósito:** rotar el par de tokens a partir del refresh token vigente; el refresh anterior queda en lista negra.
- **Llamador / rol / permiso:** público (`auth=None`).
- **Consumidor:** **`frontend/src/app/api/auth/refresh/route.ts`** (route handler de Next.js). El navegador nunca llama directamente: `lib/api.ts` hace `fetch("/api/auth/refresh")` y el handler de servidor reenvía a `${backendInternalUrl()}/token/refresh` con `body = { refresh }`. Es el único consumidor no-navegador del backend fuera del proveedor de pagos.
- **Entrada:** body `{ refresh }`.
- **Validación:** el refresh debe existir, no estar bloqueado y no haber expirado.
- **Controller:** `NinjaJWTDefaultController.refresh_token`.
- **Cadena:** Next.js route handler → `fetch` server-side → Controller `ninja_jwt` → lista negra + `usuarios_usuario` → esquema nativo.
- **Modelos/tablas:** escritura `token_blacklist_blacklistedtoken`, `token_blacklist_outstandingtoken`.
- **Efectos:** rotación; el handler reescribe las cookies `access_token`, `refresh_token` y `expires_at` (esta última legible por JS para el refresco proactivo).
- **Invariantes:** el cliente no puede leer la cookie httpOnly del refresh; la rotación es del servidor.
- **Respuesta:** `{ access, refresh? }` nativo; el handler lo reexpone como `{ success: true, data: { expires_at } }`.
- **Errores:** 401 del backend → el handler responde 401 `{ success:false, error:{ message:"Refresh fallido" } }`; ausencia de cookie → 401 "Refresh token no encontrado"; token sin `access` → 500.
- **Estado:** registrada · **consumida por el frontend (vía route handler)**.

### 4.3 `POST /api/token/verify`

- **Propósito:** comprobar si un token dado es válido (expiración y revocación) sin emitir nada.
- **Llamador / rol / permiso:** público (`auth=None`).
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** body `{ token }`.
- **Validación:** la de la librería.
- **Controller:** `NinjaJWTDefaultController.verify_token`.
- **Cadena:** Controller → `ninja_jwt` → lista negra → `{ detail }` nativo.
- **Modelos/tablas:** lectura `token_blacklist_blacklistedtoken`.
- **Efectos:** ninguno.
- **Invariantes:** no muta estado.
- **Respuesta:** `{ detail }` nativo (**fuera** de `ApiResponse`).
- **Errores:** 401 si el token es inválido.
- **Estado:** registrada · **superficie sin consumidor**.

### 4.4 `POST /api/auth/login/username`

- **Propósito:** autenticar por **username** y emitir el par JWT. Punto de entrada del proceso de sesión del frontend (el hook decide el endpoint según el identificador entregado).
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`); devuelve tokens, no datos de negocio.
- **Consumidor:** `frontend/src/features/auth/hooks/useLogin.ts` (`resolveLogin` → rama `username`) → `app/(auth)/login/page.tsx` → `features/auth/views/LoginClientShell.tsx`. El hook persiste `access_token`, `refresh_token`, `expires_at` y `user_session` en cookies del navegador.
- **Entrada:** body `{ username: string (min 1), password: string (min 1) }`.
- **Validación:** `LoginUsernameIn`; credenciales verificadas por `AuthCoreService.autenticar`; usuario inactivo rechazado.
- **Controller:** `backend/modules/usuarios/presentation/controllers/auth_controller.py` → `AuthLoginController.login_username`.
- **Cadena:** Controller → `AuthOrchestrator.login_username` → `AuthFlujo._proceso_login_username` → `AuthCoreService` (buscar/autenticar/crear tokens) → ORM `usuarios_usuario` → `AuthPresenter.present_login` → `ApiResponse[LoginTokenOut]`.
- **Modelos/tablas:** lectura/escritura `usuarios_usuario`; escritura `token_blacklist_outstandingtoken`.
- **Efectos:** emisión de tokens y registro del outstanding token.
- **Invariantes:** mensaje de éxito fijo «Inicio de sesión exitoso.»; el token no viaja con datos del usuario más allá de `user`.
- **Respuesta:** `data = { access_token, refresh_token, expires_at, user: { id, username, email, is_staff, is_superuser, persona_id, dni_legacy } }`.
- **Errores:** 401 (`HTTP_ERROR`, mensaje «Credenciales inválidas») por credenciales incorrectas; 403 (`HTTP_ERROR`, «Usuario inactivo») por cuenta desactivada; 422 por payload inválido.
- **Estado:** registrada · **consumida**.

### 4.5 `POST /api/auth/login/dni`

- **Propósito:** autenticar por **DNI** (8 dígitos) y emitir el par JWT. Variante de identidad civil del mismo caso de uso que 4.4.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidor:** `features/auth/hooks/useLogin.ts` (rama `dni`) → `app/(auth)/login/page.tsx`.
- **Entrada:** body `{ dni: string (exactamente 8 caracteres), password: string (min 1) }`.
- **Validación:** `LoginDniIn` con `min_length=8, max_length=8` sobre `dni`; autenticación por `persona_fk` + hash de contraseña.
- **Controller:** `auth_controller.py` → `AuthLoginController.login_dni`.
- **Cadena:** Controller → `AuthOrchestrator.login_dni` → `AuthFlujo._proceso_login_dni` → `AuthCoreService` (búsqueda por DNI en `usuarios_persona`/`usuarios_usuario` + `autenticar`) → `AuthPresenter.present_login` → `ApiResponse[LoginTokenOut]`.
- **Modelos/tablas:** lectura `usuarios_usuario`, `usuarios_persona`; escritura `token_blacklist_outstandingtoken`.
- **Efectos:** emisión de tokens.
- **Invariantes:** el DNI identifica a una persona ya registrada; no se crea nada en este endpoint.
- **Respuesta:** idéntica a 4.4.
- **Errores:** 401 «Credenciales inválidas»; 403 «Usuario inactivo»; 422 si el DNI no tiene 8 caracteres.
- **Estado:** registrada · **consumida**.

### 4.6 `POST /api/auth/login/email`

- **Propósito:** autenticar por **correo** y emitir el par JWT.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidor:** `features/auth/hooks/useLogin.ts` (rama `email`, por defecto) → `app/(auth)/login/page.tsx`.
- **Entrada:** body `{ email: string, password: string (min 1) }`.
- **Validación:** `LoginEmailIn`; no se exige formato de correo en el esquema (la comprobación real es la autenticación).
- **Controller:** `auth_controller.py` → `AuthLoginController.login_email`.
- **Cadena:** Controller → `AuthOrchestrator.login_email` → `AuthFlujo._proceso_login_email` → `AuthCoreService` → `AuthPresenter.present_login` → `ApiResponse[LoginTokenOut]`.
- **Modelos/tablas:** lectura/escritura `usuarios_usuario`; escritura `token_blacklist_outstandingtoken`.
- **Efectos:** emisión de tokens.
- **Invariantes:** el email es único por `Usuario` (garantía de la capa de datos).
- **Respuesta:** idéntica a 4.4.
- **Errores:** 401 «Credenciales inválidas»; 403 «Usuario inactivo»; 422.
- **Estado:** registrada · **consumida**.

### 4.7 `POST /api/auth/register`

- **Propósito:** **alta de usuario responsable**: crea o reutiliza la `Persona` del documento, crea el `Usuario` con su `Persona` vinculada, registra la aceptación de BASES y devuelve el par JWT para que el usuario quede con sesión iniciada.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidor:** `features/auth/services/register.service.ts` → `features/auth/hooks/useRegister.ts` → `features/auth/components/RegisterForm.tsx` → `app/(auth)/register/page.tsx`.
- **Entrada (body `RegisterIn`):** `email` (≤120), `password` (8–120), `confirmPassword` (debe coincidir con `password`), `tipoDocumento` ∈ {DNI, CE, PAS}, `numeroDocumento` (1–20), `nombres` (≤120), `apellidos` (≤120), `genero` ∈ {M, F}, `telefono` (9), `whatsapp` (9), `contactoEmergenciaNombre` (≤120), `contactoEmergenciaTelefono` (≤120), `acceptedBases: bool` (debe ser `true`).
- **Validación:** esquema Pydantic de presentación + validación cruzada `password == confirmPassword` + `acceptedBases` obligatorio.
- **Controller:** `backend/modules/usuarios/presentation/controllers/registro_controller.py` → `RegistroController.register`.
- **Cadena:** Controller (extrae IP de `X-Forwarded-For` o `REMOTE_ADDR` y `User-Agent`) → `RegistroOrchestrator.registrar` → `RegistroFlujo._proceso_registro` (transaction.atomic) → `PersonaCoreService` + `AuthCoreService` → ORM `usuarios_persona`, `usuarios_usuario`, `aceptaciones_inscripcion` → `RegistroPresenter.present_registro` → `ApiResponse[RegisterOut]`.
- **Modelos/tablas:** escritura `usuarios_persona`, `usuarios_usuario`, `aceptaciones_inscripcion`; lectura para detectar duplicados.
- **Efectos:** email ya existente → error; el usuario queda **autenticado** (tokens emitidos) sin pasar por el login.
- **Invariantes:** `username` generado como `{tipo_documento_lower}_{numero_documento}`; si la `Persona` ya existe sin usuario, se reutiliza (no se duplica); si ya existe con usuario → 409; el registro de la aceptación guarda IP y user-agent (evidencia de consentimiento).
- **Respuesta:** `data = { access_token, refresh_token, expires_at, user: { id, username, email, is_staff, is_superuser, persona_id } }`; mensaje «Registro exitoso. Ya puedes iniciar sesión.»
- **Errores:** 409 por email/documento ya registrados; 422 por confirmación de contraseña distinta, `acceptedBases = false` o campos malformados; 500 en fallos inesperados.
- **Estado:** registrada · **consumida**.

### 4.8 `GET /api/auth/me`

- **Propósito:** **revalidación de sesión**. Devuelve la identidad del llamador y su **nivel y capacidades** para que la UI sepa qué mostrar, sin que el cliente sea la autoridad.
- **Llamador / rol / permiso:** requiere token válido (`auth=JWTAuth()`); **no** exige permiso adicional (no declara `permissions`, por lo que no hereda `AllowAny` ni una lista de negocio). Es la única ruta que publica el `nivel` del propio actor.
- **Consumidores:**
  - `features/admin/services/admin.me.service.ts` (`getAdminMe`) → `features/admin/hooks/useAdminSession.ts` y `features/auth/utils/resolver-destino.ts` (redirección post-login: decide `/administracion` vs `/dashboard`).
  - `features/admin/services/admin.session.server.ts` / `admin.guard.service.ts` (**guard de servidor** de `app/(app)/administracion/layout.tsx`): revalida con `cache: "no-store"` para observar revocaciones.
- **Entrada:** sin parámetros.
- **Validación:** la firma y expiración del token; `request.user` debe estar autenticado.
- **Controller:** `backend/modules/usuarios/presentation/controllers/me_controller.py` → `AuthMeController.me` (**controller síncrono**, sin orquestador: lee `request.user` y delega en `core/capacidades.py`).
- **Cadena:** Controller → `core.capacidades.{es_admin, es_staff, es_superusuario, nivel_de, capacidades_de}` → `request.user.persona_fk` → `success_response(dict)` → `ApiResponse[MeOut]`.
- **Modelos/tablas:** lectura `usuarios_usuario`, `usuarios_persona` (relación `persona_fk`).
- **Efectos:** ninguno (escritura).
- **Invariantes:** `admin = is_staff OR is_superuser`; `rol` se deriva de la **misma** regla (`"admin"`/`"user"`), para que el vocabulario del cliente no pueda divergir; `nivel` distingue `usuario`/`staff`/`superusuario`; `capacidades` es **advisory** — el backend vuelve a evaluarlas en cada petición.
- **Respuesta:** `data = { id, username, email, nombres, apellidos, rol, es_admin, is_staff, is_superuser, nivel, capacidades[], persona_id }`.
- **Errores:** si el usuario no está autenticado devuelve `data = null` con `success = true` (no lanza); con token inválido, 401 `AUTHENTICATION_REQUIRED` por el interceptor global.
- **Estado:** registrada · **consumida** (UI + guard de servidor).

---

## 5. Dominio 2 — Personas (2 rutas)

### 5.1 `GET /api/personas/busqueda/{documento}`

- **Propósito:** **consulta externa de identidad**: devuelve el tipo de documento y la razón social / nombre completo de un DNI (RENIEC) o RUC (SUNAT). Es el autocompletado del formulario de inscripción; **no** devuelve el id interno de la aplicación.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`). Se publica porque la consulta es a una fuente oficial de identidad, no a datos de negocio.
- **Consumidor:** `features/inscripciones/services/inscripcion.service.ts` (`consultarDocumento`) → `features/inscripciones/hooks/useDocumentoLookup.ts` → `features/inscripciones/components/forms/DocumentoLookupSmartField.tsx` (wizard de inscripción).
- **Entrada:** path `documento` (8–11 caracteres); query params: ninguno.
- **Validación:** `Path(..., min_length=8, max_length=11)`; la longitud determina el tipo (8 → DNI, 11 → RUC).
- **Controller:** `backend/modules/usuarios/presentation/controllers/persona_busqueda_controller.py` → `PersonaBusquedaController.buscar_documento`.
- **Cadena:** Controller → `PersonaBusquedaOrchestrator.buscar_documento` → `PersonaBusquedaFlujo._proceso_busqueda` → puerto `IConsultaExternaClient` (implementación HTTP contra el microservicio `worker/scraper/main.py`, `GET /consultar/{documento}`) → `PersonaBusquedaPresenter.present_documento` → `ApiResponse[DocumentoConsultaOut]`.
- **Modelos/tablas:** **no toca la base de datos** — sólo llama al worker externo.
- **Efectos:** llamada de red al microservicio de consulta; ese worker consulta la fuente oficial externa.
- **Invariantes:** sólo lectura; nunca crea ni modifica una `Persona` en la aplicación.
- **Respuesta:** `data = { tipo_documento, numero_documento, razon_social }`.
- **Errores:** 404 `RENIEC_NOT_FOUND` / `SUNAT_NOT_FOUND` (códigos del catálogo) si el documento no existe; 422 si la longitud es inválida; 500/503 si el worker no responde.
- **Estado:** registrada · **consumida**.

### 5.2 `GET /api/personas/resolver`

- **Propósito:** **resolver el id interno** de una `Persona` ya registrada a partir de su identidad civil exacta. Es el complemento *interno* de 5.1: 5.1 pregunta «¿qué dice la fuente oficial?», esta pregunta «¿qué id tiene esta persona en el sistema?». Se usa para asignar beneficiarios de pases sin escribir texto libre.
- **Llamador / rol / permiso:** **requiere sesión** (`auth=JWTAuth()` + `permissions=[IsAuthenticated]`, que **sustituye** al `AllowAny` del controlador). Un visitante anónimo recibe 401 y nunca llega a la consulta.
- **Consumidor:** `features/pases/services/persona.resolucion.service.ts` (`resolverPersona`) → `features/pases/hooks/useResolverPersona.ts` → `features/pases/components/PaseLookupPersonaField.tsx` (asignación de beneficiarios de un pase).
- **Entrada:** query `tipo_documento` (≤3 caracteres) y `numero_documento` (1–20). Ambos obligatorios.
- **Validación:** coincidencia **exacta** sobre `(tipo_documento, numero_documento)`; el tipo se normaliza a mayúsculas sin espacios; el número sólo se recorta. No hay búsqueda difusa ni listado.
- **Controller:** `backend/modules/usuarios/presentation/controllers/persona_resolucion_controller.py` → `PersonaResolucionController.resolver_persona`.
- **Cadena:** Controller → `PersonaResolucionOrchestrator.resolver_persona` → `PersonaResolucionFlujo._proceso_resolver` → `PersonaSelector` (ORM) → `PersonaResolucionPresenter.present_persona` → `ApiResponse[PersonaResueltaOut]`.
- **Modelos/tablas:** lectura `usuarios_persona`.
- **Efectos:** ninguno.
- **Invariantes:** **sólo lectura**: la consulta nunca crea ni modifica una `Persona`; la ausencia es un error tipado (404), no una lista vacía; el resultado sólo expone id, nombre y documento ya consultado.
- **Respuesta:** `data = { persona_id, nombre_completo, tipo_documento, numero_documento }`; mensaje «Persona encontrada correctamente.»
- **Errores:** 404 `PERSONA_NO_ENCONTRADA`; 422 `TIPO_DOCUMENTO_INVALIDO` si el tipo no es válido; 401 si no hay sesión.
- **Estado:** registrada · **consumida**.

---

## 6. Dominio 3 — Catálogo público y cotización (6 rutas)

### 6.1 `GET /api/catalogo/disciplinas/`

- **Propósito:** listar las **disciplinas activas** del evento con su modalidad y el mínimo/máximo de jugadores por equipo. Alimenta el selector de disciplina del wizard y las secciones de campeonato de la portada.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidores:** `features/inscripciones/services/catalog.service.ts` (`getDisciplinas`) → `features/inscripciones/hooks/useInscripcionCatalogs.ts` → `components/smart-fields/SmartEquipoField.tsx`; además `features/portada/hooks/useCatalogo.ts` (`useDisciplinas`, `fetch` con `cache: "no-store"` y validación Zod) → `components/portada/ChampionshipSection.tsx` y `components/portada/ScheduleSection.tsx`.
- **Entrada:** sin parámetros.
- **Validación:** ninguna en el servidor; el consumidor de portada valida el payload contra `DisciplinaOutSchema` y, si no encaja, usa un respaldo estático (`DISCIPLINAS_FALLBACK`).
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/catalogo_controller.py` → `CatalogoController.listar_disciplinas`.
- **Cadena:** Controller → **acceso directo al selector** (`sync_to_async(DisciplinaSelector.get_activas)`) → `CatalogoPresenter.present_disciplinas` → `ApiResponse[list[DisciplinaOut]]`. *(Este controller no usa orquestador: desviación respecto de `django-app-architecture-contract.md` §4.8.)*
- **Modelos/tablas:** lectura `disciplinas`.
- **Efectos:** ninguno.
- **Invariantes:** sólo se devuelven las disciplinas activas; el padrón no lo elige el cliente.
- **Respuesta:** `data = [{ id, nombre, sigla, modalidad, min_jugadores, max_jugadores }]`.
- **Errores:** 500 `INTERNAL_ERROR` en fallo inesperado; sin errores de negocio previstos.
- **Estado:** registrada · **consumida** (dos superficies distintas).

### 6.2 `GET /api/catalogo/promociones/`

- **Propósito:** listar las **promociones activas** (rangos etarios) del evento, para el filtro de promoción del wizard y de la administración.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidor:** `features/inscripciones/services/catalog.service.ts` (`getPromociones`) → `useInscripcionCatalogs`.
- **Entrada:** sin parámetros.
- **Validación:** ninguna en el servidor.
- **Controller:** `catalogo_controller.py` → `CatalogoController.listar_promociones`.
- **Cadena:** Controller → `sync_to_async(PromocionSelector.get_activas)` → `CatalogoPresenter.present_promociones` → `ApiResponse[list[PromocionOut]]`.
- **Modelos/tablas:** lectura `promociones`.
- **Efectos:** ninguno.
- **Invariantes:** sólo promociones activas.
- **Respuesta:** `data = [{ id, anio, nombre }]`.
- **Errores:** 500 en fallo inesperado.
- **Estado:** registrada · **consumida**.

### 6.3 `GET /api/catalogo/categorias/`

- **Propósito:** listar las **categorías activas** del evento con su rango etario (`promocion_desde` / `promocion_hasta`). Determina en qué promoción juega cada equipo.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidores:** `features/inscripciones/services/catalog.service.ts` (`getCategorias`) → `useInscripcionCatalogs`; además `features/portada/hooks/useCatalogo.ts` (`useCategorias`) → `components/portada/{ChampionshipSection,ScheduleSection}.tsx`.
- **Entrada:** sin parámetros.
- **Validación:** ninguna en el servidor; la portada valida con `CategoriaOutSchema` y cae en `CATEGORIAS_FALLBACK` si falla.
- **Controller:** `catalogo_controller.py` → `CatalogoController.listar_categorias`.
- **Cadena:** Controller → `sync_to_async(CategoriaSelector.get_activas)` → `CatalogoPresenter.present_categorias` → `ApiResponse[list[CategoriaOut]]`.
- **Modelos/tablas:** lectura `categorias` (+ `eventos` para `evento_nombre`).
- **Efectos:** ninguno.
- **Invariantes:** sólo categorías activas del evento vigente.
- **Respuesta:** `data = [{ id, evento_id, evento_nombre, nombre, promocion_desde, promocion_hasta }]`.
- **Errores:** 500 en fallo inesperado.
- **Estado:** registrada · **consumida** (dos superficies).

### 6.4 `GET /api/catalogo/paquetes/`

- **Propósito:** listar los **paquetes comerciales** del evento con precios vigentes, beneficios y resumen de disciplinas. Es la tabla de precios que el visitante ve antes de contracting.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidores:** `features/inscripciones/services/catalog.service.ts` (`getPaquetes`, normaliza precios y `cantidad_minima_compra`) y `features/inscripciones/services/paquete.service.ts` → ambos en `useInscripcionCatalogs`; además `features/landing/paquetes.service.ts` (`fetchPaquetes`, `fetch` con `cache: "no-store"`) → `features/landing/hooks/useLandingPaquetes.ts` → `components/landing/Paquetes.tsx`, `PaquetesCards.tsx`, `PaquetesCardsClient.tsx`.
- **Entrada:** sin parámetros.
- **Validación:** ninguna en el servidor; los dos consumidores normalizan `precio_*` (número o string → número) y aplican fallback de `cantidad_minima_compra` desde el nombre histórico `cantidad_maxima_participantes`.
- **Controller:** `catalogo_controller.py` → `CatalogoController.listar_paquetes`.
- **Cadena:** Controller → `sync_to_async(PaqueteSelector.get_activos)` → `CatalogoPresenter.present_paquetes` → `ApiResponse[list[PaqueteListOut]]`.
- **Modelos/tablas:** lectura `paquetes`, `paquetes_precios`, `paquetes_beneficios`, `paquetes_disciplinas`, `disciplinas`.
- **Efectos:** ninguno.
- **Invariantes:** sólo paquetes activos; el precio publicado es el vigente en la fecha del servidor.
- **Respuesta:** `data = [{ id, evento_id, nombre, descripcion, tipo, modo_disciplinas, cantidad_disciplinas, cantidad_minima_compra, cantidad_maxima_equipos, precio_preventa, precio_regular, precio_promocional, tiene_fiesta, tiene_box, tiene_cerveza, disciplinas_resumen[], disciplinas[], beneficios[], precios[] }]`.
- **Errores:** 500 en fallo inesperado.
- **Estado:** registrada · **consumida** (wizard + landing).

### 6.5 `GET /api/catalogo/paquetes/{paquete_id}/`

- **Propósito:** **detalle** de un paquete con la línea completa de precios, beneficios y disciplinas (incluye `minimo_compra_inicial`, que la vista de lista expone con otro nombre).
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidores:** **sin consumidor en vista**. El transporte existe (`features/inscripciones/services/catalog.service.ts` → `getPaqueteDisciplinas`; `features/inscripciones/services/paquete.service.ts` → `fetchPaqueteDetail`) y los hooks `usePaqueteDisciplinas` / `usePaqueteDetail` están exportados, pero **ninguna vista los invoca**: el `SmartEquipoField` deriva el paquete del listado canónico. El tipo `PaqueteDisciplina` sí se usa en `components/smart-fields/SmartEquipoField.tsx`, alimentado por el listado.
- **Entrada:** path `paquete_id`.
- **Validación:** si el paquete no existe se lanza `PaqueteNotFoundError` (404) en el propio controller.
- **Controller:** `catalogo_controller.py` → `CatalogoController.detalle_paquete`.
- **Cadena:** Controller → `sync_to_async(PaqueteSelector.get_by_id)` → (404 si `None`) → `CatalogoPresenter.present_paquete_detail` → `ApiResponse[PaqueteDetailOut]`.
- **Modelos/tablas:** lectura `paquetes`, `paquetes_precios`, `paquetes_beneficios`, `paquetes_disciplinas`, `disciplinas`.
- **Efectos:** ninguno.
- **Invariantes:** la respuesta incluye la línea temporal de precios, que es la base de la cotización.
- **Respuesta:** `data = { id, evento_id, nombre, descripcion, tipo, modo_disciplinas, cantidad_disciplinas, minimo_compra_inicial, precios[], beneficios[], disciplinas[] }`.
- **Errores:** 404 `PAQUETE_NOT_FOUND`; 500 en fallo inesperado.
- **Estado:** registrada - **consumidor no conectado a ninguna vista**.

### 6.6 `POST /api/cotizaciones/`

- **Propósito:** **cotización sin persistencia**. Calcula precio unitario, total, mínimo comercial y ventana de validez para un paquete y una cantidad. No escribe nada: el cliente guarda el resultado en el estado del formulario y lo reenvía en la confirmación para que el servidor lo revalide.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`): es información de precios.
- **Consumidor:** `features/inscripciones/services/cotizacion.service.ts` (`cotizarPaquete`) → `features/inscripciones/hooks/useCotizacion.ts` → `components/InscripcionWizard.tsx` (tarjeta de cotización del wizard).
- **Entrada (body `CotizacionRequest`):** `paquete_id: str`, `cantidad: int`.
- **Validación:** `cantidad >= Paquete.minimo_compra_inicial` (si no, `CantidadInsuficienteError`); el paquete debe existir (`PaqueteNotFoundError`); el precio unitario sale del `PaquetePrecio` vigente (preventa o regular).
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/cotizacion_controller.py` → `CotizacionController.cotizar`.
- **Cadena:** Controller → instancia directa `CotizacionFlujo()` → `sync_to_async(flujo.cotizar)` → `CotizacionFlujo` (consulta `Paquete`/`PaquetePrecio`) → devuelve el esquema de presentación `CotizacionResponse` → `success_response(...)` → `ApiResponse[CotizacionResponse]`. *(Sin orquestador: desviación respecto del contrato de arquitectura.)*
- **Modelos/tablas:** lectura `paquetes`, `paquetes_precios`.
- **Efectos:** ninguno (**no persiste** la cotización).
- **Invariantes:** `precio_promocional` se deriva del precio activo si es menor que el regular; ventana de validez de **24 h** (`COTIZACION_VALIDIDAD_HOURS`); el `version` es un contador de versión de precio para trazabilidad.
- **Respuesta:** `data = { paquete_id, paquete_nombre, modo_disciplinas, minimo_cantidad, cantidad_cotizada, precio_unitario, precio_regular, precio_preventa, total, validez_hasta, version, estado }`; mensaje «Cotización generada correctamente.»
- **Errores:** 400 `CANTIDAD_INSUFICIENTE` (cantidad bajo el mínimo); 404 `PAQUETE_NOT_FOUND`; 422 por body inválido.
- **Estado:** registrada · **consumida**.

---

## 7. Dominio 4 — Pases de fiesta (6 rutas)

Contexto común: el módulo de pases es un **lote comercial independiente** de la inscripción deportiva. Una compra de pases crea `commerce.Compra` + `pagos_ordenpago` + `salesianos_fest_compra_pase`, y **nunca** crea `Inscripcion`, `AsignacionCupo`, `Participacion` ni `Equipo`. Toda la superficie está detrás del interruptor `settings.PASES_FIESTA_ENABLED`.

### 7.1 `GET /api/pases/`

- **Propósito:** **catálogo público** de los pases que pueden comprarse ahora: precio vigente, precio de preventa, precio regular, tope de cantidad y línea de precios.
- **Llamador / rol / permiso:** público (`auth=None`, `AllowAny`).
- **Consumidor:** `features/pases/services/pase.service.ts` (`listarPases`) → `features/pases/hooks/usePasesCatalogo.ts` → `features/pases/components/PaseCatalogoCard.tsx` → `app/(app)/pases/page.tsx` (y `components/portada/PartyPassSection.tsx` referencia la sección de pases, aunque la lista vive en la página de pases).
- **Entrada:** sin parámetros.
- **Validación:** ninguna en el servidor.
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/pase_controller.py` → `PaseController.listar_pases`.
- **Cadena:** Controller → `PaseOrchestrator.listar_catalogo` → `ListarPasesFlujo._listar_pases` → selectores de `pases` / `pases_precios` → `PasePresenter.present_pases` → `ApiResponse[list[PaseListOut]]`.
- **Modelos/tablas:** lectura `pases`, `pases_precios`.
- **Efectos:** ninguno.
- **Invariantes:** sólo los pases **activos** del **evento activo**; si el interruptor de despliegue está apagado o no hay pase activo, la respuesta es una **lista vacía** — nunca se filtra un catálogo no publicado.
- **Respuesta:** `data = [{ id, evento_id, nombre, descripcion, activo, precio_preventa, precio_regular, precio_vigente, cantidad_maxima, precios[] }]`.
- **Errores:** 500 en fallo inesperado.
- **Estado:** registrada · **consumida**.

### 7.2 `POST /api/pases/comprar`

- **Propósito:** **comprar un lote de pases**. Crea atómicamente la compra (`PENDIENTE`), su orden de pago (`PENDIENTE`) y la línea comercial del lote con el **precio congelado**.
- **Llamador / rol / permiso:** requiere sesión (`auth=JWTAuth()` + `permissions=[IsAuthenticated]`, que sustituye al `AllowAny` del controlador). El comprador es `request.user.persona_fk`.
- **Consumidor:** `features/pases/services/pase.service.ts` (`comprarPases`) → `features/pases/hooks/useCompraPase.ts` → `features/pases/views/PaseCompraView.tsx` → `app/(app)/pases/page.tsx`.
- **Entrada (body `PaseComprarIn`):** `pase_id: str` (1–64), `cantidad: int` (> 0).
- **Validación:** el comprador debe tener `Persona` (`BusinessError`); el interruptor `PASES_FIESTA_ENABLED` debe estar activo (`ConflictError`); el pase debe existir, estar activo y pertenecer a la edición vigente (`PASE_NO_DISPONIBLE`); debe existir un `PasePrecio` vigente (`PASE_PRECIO_NO_VIGENTE`); el inventario no puede estar agotado (`PASE_INVENTARIO_AGOTADO`); la cantidad debe ser un entero positivo dentro del tope comercial (`PASE_CANTIDAD_INVALIDA`).
- **Controller:** `pase_controller.py` → `PaseController.comprar_pases`.
- **Cadena:** Controller (extrae `responsable_id` de `request.user.persona_fk_id`) → `PaseOrchestrator.comprar_pases` → `CrearCompraPaseFlujo._crear_compra_pase` (un `transaction.atomic`) → `IzipayCoreService` (snapshot sanitizado de metadata) → ORM `commerce_compra`, `pagos_ordenpago`, `salesianos_fest_compra_pase` → `PasePresenter.present_compra_creada` → `ApiResponse[PaseCompraCreadaOut]`.
- **Modelos/tablas:** escritura `commerce_compra`, `pagos_ordenpago`, `salesianos_fest_compra_pase`; lectura `pases`, `pases_precios`.
- **Efectos:** crea la orden de pago; el pago real ocurre después contra Izipay (ver §9.3).
- **Invariantes:** **el cliente nunca controla el precio ni el total**: el precio unitario sale del `PasePrecio` vigente y el total se calcula en el servidor; la edición se resuelve en el servidor (el cliente no manda `evento_id`); el tope de inventario (`Pase.cantidad_maxima`, 0 = sin límite) se recalcula **dentro** de la transacción contra las compras no canceladas; no se crea ningún objeto deportivo.
- **Respuesta:** `data = { compra_id, orden_pago_id, numero_orden, pase_id, pase_nombre, cantidad, precio_unitario, total, estado_compra, estado_orden }`; mensaje «Compra de pases registrada correctamente. Proceda al pago.»
- **Errores:** 400 `PASE_CANTIDAD_INVALIDA` / `PASE_COMPRADOR_SIN_PERSONA`; 409 `PASES_FIESTA_DESHABILITADO`, `PASE_NO_DISPONIBLE`, `PASE_PRECIO_NO_VIGENTE`, `PASE_INVENTARIO_AGOTADO`; 404 `PASE_NO_ENCONTRADO`; 422 por body inválido.
- **Estado:** registrada · **consumida**.

### 7.3 `GET /api/pases/compras/{compra_id}`

- **Propósito:** **estado de la compra de pases**: estados comercial y de la orden, importes congelados, moneda, origen del pago y contadores de beneficiarios asignados/pendientes.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth` + `IsAuthenticated`). Sólo el **comprador** (`Compra.responsable`) puede leer la compra.
- **Consumidor:** `features/pases/services/pase.service.ts` (`obtenerCompraPase`) → `features/pases/hooks/useCompraPaseEstado.ts` → `features/pases/views/PaseCompraView.tsx`.
- **Entrada:** path `compra_id`.
- **Validación:** la compra debe existir y su `responsable_id` debe coincidir con el llamador.
- **Controller:** `pase_controller.py` → `PaseController.obtener_compra_pase`.
- **Cadena:** Controller → `PaseOrchestrator.obtener_compra` → `ObtenerCompraPaseFlujo._obtener_compra_pase` → selector de compra/orden → `PasePresenter.present_compra_estado` → `ApiResponse[PaseCompraEstadoOut]`.
- **Modelos/tablas:** lectura `commerce_compra`, `pagos_ordenpago`, `salesianos_fest_compra_pase`, `pases_beneficiarios`.
- **Efectos:** ninguno.
- **Invariantes:** la propiedad es la autorización; no hay atajo de administrador en esta ruta.
- **Respuesta:** `data = { compra_id, orden_pago_id, numero_orden, pase_id, pase_nombre, cantidad, precio_unitario, total, estado_compra, estado_orden, moneda, origen_pago, created_at, beneficiarios_asignados, beneficiarios_pendientes }`.
- **Errores:** 404 `PASE_COMPRA_NO_ENCONTRADA`; 403 `PASE_COMPRA_NO_AUTORIZADA` si el llamador no es el comprador; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 7.4 `GET /api/pases/compras/{compra_id}/beneficiarios`

- **Propósito:** listar las **personas titulares** de los pases de una compra, con su *slot*, estado y traza de auditoría (asignación/revocación), más los contadores de uso del lote.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth` + `IsAuthenticated`); sólo el comprador.
- **Consumidor:** `features/pases/services/pase.beneficiario.service.ts` (`listarBeneficiarios`) → `features/pases/hooks/useBeneficiariosCompra.ts` → `features/pases/components/PaseBeneficiariosPanel.tsx`.
- **Entrada:** path `compra_id`.
- **Validación:** propiedad de la compra; la compra debe existir.
- **Controller:** `pase_controller.py` → `PaseController.listar_beneficiarios`.
- **Cadena:** Controller → `PaseOrchestrator.listar_beneficiarios` → `ListarBeneficiariosPaseFlujo._listar_beneficiarios` → `PaseBeneficiarioSelector` (ORM) → `PasePresenter.present_beneficiarios_lista` → `ApiResponse[PaseBeneficiariosListaOut]`.
- **Modelos/tablas:** lectura `pases_beneficiarios`, `usuarios_persona`, `commerce_compra`.
- **Efectos:** ninguno.
- **Invariantes:** **la contabilidad de slots es inmutable**: un slot revocado sigue consumido y `slots_disponibles` nunca vuelve a crecer tras una revocación.
- **Respuesta:** `data = { compra_id, cantidad_pases, activos, revocados, slots_usados, slots_disponibles, beneficiarios[] }`; cada beneficiario: `{ persona_id, nombre_completo, tipo_documento, numero_documento, slot, estado, asignado_en, revocado_en, motivo_revocacion }`.
- **Errores:** 404 `PASE_COMPRA_NO_ENCONTRADA`; 403 `PASE_COMPRA_NO_AUTORIZADA`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 7.5 `POST /api/pases/compras/{compra_id}/beneficiarios`

- **Propósito:** **materializar los derechos nominativos** de una compra de pases ya pagada: una persona por slot inmutable.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth` + `IsAuthenticated`); sólo el comprador. `actor_id` (usuario autenticado) queda registrado para auditoría.
- **Consumidor:** `features/pases/services/pase.beneficiario.service.ts` (`asignarBeneficiarios`) → `features/pases/hooks/useAsignarBeneficiarios.ts` → `components/PaseBeneficiariosPanel.tsx`.
- **Entrada (body `PaseBeneficiariosAsignarIn`):** `beneficiario_ids: list[str]` (1–50 UUIDs de personas **existentes**).
- **Validación:** la compra debe estar **PAGADA** (`PASE_COMPRA_NO_PAGADA`); los ids deben corresponder a personas existentes (`PASE_BENEFICIARIO_NO_ENCONTRADO`); no puede haber más beneficiarios que slots libres (`PASE_BENEFICIARIOS_EXCEDIDOS`); una persona ya titular activa en el lote es **no-op idempotente**; una persona con derecho **revocado** en ese lote se rechaza (`PASE_NO_TRANSFERIBLE`); una persona con pase activo en el evento (en otra compra) se rechaza (`PASE_BENEFICIARIO_DUPLICADO`).
- **Controller:** `pase_controller.py` → `PaseController.asignar_beneficiarios`.
- **Cadena:** Controller → `PaseOrchestrator.asignar_beneficiarios` → `AsignarBeneficiariosPaseFlujo._asignar_beneficiarios` (un `transaction.atomic`) → `PaseBeneficiarioCoreService` + selectores → ORM `pases_beneficiarios` → `PasePresenter.present_beneficiarios_asignados` → `ApiResponse[PaseBeneficiariosAsignadosOut]`.
- **Modelos/tablas:** escritura `pases_beneficiarios`; lectura `commerce_compra`, `usuarios_persona`, `pases_beneficiarios`.
- **Efectos:** materializa derechos; recalcula la acreditación de las personas afectadas.
- **Invariantes:** la API **nunca crea una persona a partir de texto libre**; se asignan los slots libres **más bajos**; un slot revocado nunca se restituye; sólo se concede derecho sobre una compra pagada.
- **Respuesta:** `data = { compra_id, cantidad_pases, activos, revocados, slots_usados, slots_disponibles, asignados, ya_asignados, beneficiarios[] }`; mensaje «Beneficiarios del pase asignados correctamente.»
- **Errores:** 404 `PASE_COMPRA_NO_ENCONTRADA` / `PASE_BENEFICIARIO_NO_ENCONTRADO`; 403 `PASE_COMPRA_NO_AUTORIZADA`; 409 `PASE_COMPRA_NO_PAGADA`, `PASE_BENEFICIARIOS_EXCEDIDOS`, `PASE_BENEFICIARIO_DUPLICADO`, `PASE_NO_TRANSFERIBLE`; 422 por body inválido.
- **Estado:** registrada · **consumida**.

### 7.6 `DELETE /api/pases/compras/{compra_id}/beneficiarios/{persona_id}`

- **Propósito:** **revocar permanentemente** el pase de una persona. El slot queda consumido para siempre y el derecho no se transfiere a nadie.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth` + `IsAuthenticated`); sólo el comprador.
- **Consumidor:** `features/pases/services/pase.beneficiario.service.ts` (`revocarBeneficiario`) → `features/pases/hooks/useRevocarBeneficiario.ts` → `features/pases/components/PaseRevocarDialog.tsx`.
- **Entrada:** path `compra_id`, `persona_id`; body `PaseBeneficiarioRevocarIn` = `{ motivo: str (1–1000) }`.
- **Validación:** el motivo es **obligatorio**; la persona debe tener derecho en ese lote (`PASE_BENEFICIARIO_NO_ENCONTRADO`); la compra debe pertenecer al llamador.
- **Controller:** `pase_controller.py` → `PaseController.revocar_beneficiario`.
- **Cadena:** Controller → `PaseOrchestrator.revocar_beneficiario` → `RevocarBeneficiarioPaseFlujo._revocar_beneficiario` (un `transaction.atomic`) → `PaseBeneficiarioCoreService` + `AcreditacionCoreService` → ORM `pases_beneficiarios`, `acreditaciones_evento` → `PasePresenter.present_beneficiario_revocado` → `ApiResponse[PaseBeneficiarioRevocadoOut]`.
- **Modelos/tablas:** escritura `pases_beneficiarios`, `acreditaciones_evento`.
- **Efectos:** revocación auditada (actor, fecha, motivo) y recálculo del acceso efectivo de la persona.
- **Invariantes:** la revocación es **permanente** e **idempotente** (revocar dos veces no falla: informa `ya_revocado = true`); el slot no se devuelve nunca.
- **Respuesta:** `data = { compra_id, persona_id, estado, revocado_en, ya_revocado, cantidad_pases, activos, revocados, slots_usados, slots_disponibles }`; mensaje «El pase fue revocado correctamente.»
- **Errores:** 404 `PASE_COMPRA_NO_ENCONTRADA` / `PASE_BENEFICIARIO_NO_ENCONTRADO`; 403 `PASE_COMPRA_NO_AUTORIZADA`; 422 por motivo vacío.
- **Estado:** registrada · **consumida**.

---

## 8. Dominio 5 — Inscripción deportiva (12 rutas)

Contexto común: la inscripción es el agregado raíz del 영역 deportiva (`inscripciones`). Los derechos de cupo viven en `asignaciones_cupo`; el roster en `inscripciones_personas` + `participaciones`. La autorización de estas rutas es **por propiedad**: responsable de la inscripción (`inscripcion.responsable_id`) o admin Django (`is_staff`/`is_superuser`), verificado por `modules/salesianos_fest/presentation/ownership.py`.

### 8.1 `POST /api/inscripciones/`

- **Propósito:** **crear la inscripción deportiva** (estado inicial `BORRADOR`) linked a un paquete y una promoción, sin compra ni roster. El `responsable_id` **nunca** lo envía el cliente: lo deriva el servidor del usuario autenticado.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); el usuario debe tener `Persona` vinculada, si no `BusinessError` («Usuario sin persona vinculada. Complete su registro.»).
- **Consumidor:** **sin consumidor en vista**. El servicio `createInscripcion` y el hook `useCreateInscripcion` existen y están exportados, pero **ninguna vista los usa**: el asistente crea la inscripción por `POST /api/inscripciones/completa/` (8.2).
- **Entrada (body `CrearInscripcionIn`):** `evento_id`, `paquete_id`, `promocion_id`, `fusion_promocion_id` (opcional), `delegado_id` (opcional), `estado` (default `BORRADOR`), `observacion` (default `""`). El esquema **rechaza** `responsable_id` desde el cliente.
- **Validación:** paquete y promoción deben existir; la fecha límite del evento (`evento.puede_modificar()`) se evalúa en el flujo.
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py` → `InscripcionController.crear_inscripcion`.
- **Cadena:** Controller (`_get_authenticated_persona_id`) → `InscripcionOrchestrator.crear_inscripcion_proceso` → `CrearInscripcionFlujo.ejecutar` → `InscripcionCoreService` → ORM `inscripciones` (+ lectura `eventos`, `paquetes`, `promociones`) → `InscripcionPresenter.present_inscripcion` → `ApiResponse[InscripcionOut]`.
- **Modelos/tablas:** escritura `inscripciones`; lectura `eventos`, `paquetes`, `promociones`, `usuarios_persona`.
- **Efectos:** ninguno fuera de la base de datos.
- **Invariantes:** el `responsable_id` es server-side; la inscripción nace sin compra, sin orden de pago y sin roster; los cupos **no** se consumen en la creación (sólo tras el pago confirmado).
- **Respuesta:** `data = { id, evento_id, evento_nombre, responsable_id, responsable_nombre, paquete_id, paquete_nombre, promocion_id, promocion_nombre, fusion_promocion_id, delegado_id, estado, observacion, created_at }`; mensaje «La inscripción se registró correctamente.»
- **Errores:** 400 `BUSINESS_ERROR` si el usuario no tiene `Persona`; 404 `INSCRIPCION_NOT_FOUND` / `PAQUETE_NOT_FOUND` según el caso; 409 `INSCRIPCION_UNIQUE_CONSTRAINT` por duplicidad; 422 por body inválido.
- **Estado:** registrada - **consumidor no conectado a ninguna vista**.

### 8.2 `POST /api/inscripciones/completa/`

- **Propósito:** **alta atómica completa**: inscripción (`BORRADOR`) + compra inicial (`PENDIENTE`) + orden de pago (`PENDIENTE`) + línea `CompraInscripcion` + equipos, en una sola transacción. Es la vía que usa el wizard para dejar al usuario a un paso del pago.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); `responsable_id` server-side.
- **Consumidor:** `features/inscripciones/services/inscripcion.service.ts` (`createInscripcionCompleta`) → `features/inscripciones/hooks/useCreateInscripcionCompleta.ts` → `components/InscripcionWizard.tsx` → `app/(app)/inscripcion/page.tsx`.
- **Entrada (body `CrearInscripcionCompletaIn`):** `evento_id`, `paquete_id`, `promocion_id`, `fusion_promocion_id?`, `delegado_id?`, `cantidad: int`, `equipos: [{ disciplina_id, categoria_id?, nombre, estado? }]`, `estado` (default `BORRADOR`), `observacion`, `precio_unitario_cotizado?` (float), `cotizacion_version?` (int, metadata).
- **Validación:** `cantidad >= paquete.minimo_compra_inicial` (`CANTIDAD_INSUFICIENTE`); el precio cotizado por el cliente **se revalida** contra el catálogo con tolerancia 0,01 (`PRECIO_CAMBIADO`) — si coincide, se usa el precio cotizado (contrato de confianza con el usuario); `cotizacion_version` es sólo trazabilidad; fecha límite del evento.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.crear_inscripcion_completa`.
- **Cadena:** Controller → `InscripcionOrchestrator.crear_inscripcion_completa_proceso` → `CrearInscripcionCompletaFlujo.ejecutar` (transaction.atomic) → `InscripcionCoreService` + `EquipoCoreService` + `IzipayCoreService` → ORM `inscripciones`, `commerce_compra`, `salesianos_fest_compra_inscripcion`, `pagos_ordenpago`, `equipos` → `InscripcionPresenter.present_equipo` por equipo → `ApiResponse[InscripcionCompletaOut]`.
- **Modelos/tablas:** escritura `inscripciones`, `commerce_compra`, `salesianos_fest_compra_inscripcion`, `pagos_ordenpago`, `equipos`; lectura `paquetes`, `paquetes_precios`, `disciplinas`, `categorias`.
- **Efectos:** crea la orden de pago; el cobro ocurre después contra Izipay.
- **Invariantes:** todo o nada (una sola transacción); el **precio queda congelado** en la compra; los cupos no se consumen hasta la confirmación del pago; **no se crea el roster de participantes** en este paso.
- **Respuesta:** `data = { inscripcion_id, inscripcion_estado, compra_id, orden_pago_id, compra_estado, cantidad, precio_unitario, total, equipos[] }`; mensaje «La inscripción con compra inicial se registró correctamente.»
- **Errores:** 400 `CANTIDAD_INSUFICIENTE`; 404 `PAQUETE_NOT_FOUND` / `INSCRIPCION_NOT_FOUND`; 409 `PRECIO_CAMBIADO`, `INSCRIPCION_UNIQUE_CONSTRAINT`; 422 por body inválido.
- **Estado:** registrada · **consumida**.

### 8.3 `GET /api/inscripciones/`

- **Propósito:** listar las **inscripciones del responsable autenticado**. Es el índice del dashboard del usuario.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); el filtro por responsable es implícito (derivado del usuario), no un parámetro.
- **Consumidor:** `features/inscripciones/services/inscripcion.service.ts` (`getMisInscripciones`) → `app/(app)/dashboard/page.tsx`.
- **Entrada:** sin parámetros.
- **Validación:** el usuario debe tener `Persona` vinculada.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.listar_mis_inscripciones`.
- **Cadena:** Controller → `InscripcionOrchestrator.listar_por_responsable_proceso` → selector de inscripciones → `InscripcionPresenter.present_inscripcion` por elemento → `ApiResponse[list[InscripcionOut]]`.
- **Modelos/tablas:** lectura `inscripciones`, `eventos`, `paquetes`, `promociones`.
- **Efectos:** ninguno.
- **Invariantes:** nunca devuelve inscripciones de otro responsable.
- **Respuesta:** `data = [InscripcionOut]` (misma forma que 8.1).
- **Errores:** 400 `BUSINESS_ERROR` si no hay `Persona`; 500 en fallo inesperado.
- **Estado:** registrada · **consumida**.

### 8.4 `GET /api/inscripciones/{inscripcion_id}`

- **Propósito:** **detalle mínimo** de una inscripción (sin equipos ni roster).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y **propiedad**: `check_ownership_or_admin(request, inscripcion_id)` — responsable de la inscripción o admin Django.
- **Consumidor:** **sin consumidor conocido**. El frontend usa la variante enriquecida `GET .../detalle` (8.5) en todas partes; esta ruta queda expuesta pero no invocada.
- **Entrada:** path `inscripcion_id`.
- **Validación:** propiedad verificada antes de leer; `InscripcionNotFoundError` (404) si no existe.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.obtener_inscripcion`.
- **Cadena:** Controller → `check_ownership_or_admin` → `InscripcionOrchestrator.obtener_inscripcion_proceso` → selector → `InscripcionPresenter.present_inscripcion` → `ApiResponse[InscripcionOut]`.
- **Modelos/tablas:** lectura `inscripciones`, `eventos`, `paquetes`, `promociones`.
- **Efectos:** ninguno.
- **Invariantes:** la denegación no muta nada y no revela la existencia del recurso a un tercero.
- **Respuesta:** `data = InscripcionOut`.
- **Errores:** 403 `ACTION_NOT_ALLOWED` si no es propietario ni admin; 404 `INSCRIPCION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 8.5 `GET /api/inscripciones/{inscripcion_id}/detalle`

- **Propósito:** **detalle operativo completo** de la inscripción: equipos con su estado de plantilla derivado, roster (`personas`), resumen de pagos (compras + ordenes), resumen de equipos y resumen de participantes.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad (`check_ownership_or_admin`).
- **Consumidor:** `features/inscripciones/services/inscripcion.service.ts` (`getInscripcionDetalle`) → `features/inscripciones/hooks/useInscripcionDetalle.ts` → `features/inscripciones/views/InscripcionDetailView.tsx` → `app/(app)/dashboard/inscripcion/[id]/page.tsx`. Componentes que consumen el payload: `DatosInscripcionCard`, `EquipoCard`, `EstadoProgresoCard`, `InscripcionHero`, `PaymentCallout`, `ResumenPagoCard`, `PoolParticipantesSeccion`, `SelectorParticipanteModal`.
- **Entrada:** path `inscripcion_id`.
- **Validación:** propiedad; la inscripción debe existir.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.obtener_inscripcion_detalle`.
- **Cadena:** Controller → `check_ownership_or_admin` → `InscripcionOrchestrator.obtener_inscripcion_detalle_proceso` → selectores de inscripción/equipos/personas/compras → `InscripcionPresenter.present_inscripcion_detail` → `ApiResponse[InscripcionDetailOut]`.
- **Modelos/tablas:** lectura `inscripciones`, `equipos`, `participaciones`, `inscripciones_personas`, `commerce_compra`, `pagos_ordenpago`, `disciplinas`, `categorias`, `paquetes`, `promociones`, `usuarios_persona`.
- **Efectos:** ninguno.
- **Invariantes:** `estado_roster` es **derivado** (`COMPLETO`/`INCOMPLETO`) a partir de `Disciplina.min_jugadores` y de las participaciones activas; `jugadores_registrados` cuenta sólo participaciones `ACTIVA`; `resumen_participantes` distingue **personas distintas** de **filas de roster** (un cupo pagado autoriza a una persona en todas las disciplinas contratadas); `resumen_pago.estado_mensaje` es el veredicto de UI; los importes vienen del snapshot congelado de la compra.
- **Respuesta:** `data = { …campos de InscripcionOut, delegado_nombre, equipos[], personas[], resumen_equipos, resumen_pago, resumen_participantes }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida** (es la lectura central del flujo de inscripción).

### 8.6 `PATCH /api/inscripciones/{inscripcion_id}`

- **Propósito:** **actualizar** estado, observación o delegado de una inscripción.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad (`check_ownership_or_admin`); la denegación **no** muta nada.
- **Consumidor:** **sin consumidor conocido**. Ninguna vista del frontend edita la cabecera de la inscripción (el wizard sólo crea; el detalle sólo lee).
- **Entrada:** path `inscripcion_id`; body `ActualizarInscripcionIn` = `{ estado?, observacion?, delegado_id? }`.
- **Validación:** la propiedad se verifica **antes** de construir el DTO; la transición de estado la valida el dominio.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.actualizar_inscripcion`.
- **Cadena:** Controller → `check_ownership_or_admin` → `InscripcionOrchestrator.actualizar_inscripcion_proceso` → `InscripcionCoreService` → ORM `inscripciones` → `InscripcionPresenter.present_inscripcion` → `ApiResponse[InscripcionOut]`.
- **Modelos/tablas:** escritura `inscripciones`.
- **Efectos:** ninguno fuera de la base de datos.
- **Invariantes:** el cliente no puede cambiar el `responsable_id`; el estado se mueve por las transiciones permitidas por el dominio.
- **Respuesta:** `data = InscripcionOut`; mensaje «Inscripción actualizada correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 409 `INVALID_STATE_TRANSITION` si la transición no es legal; 422 por body inválido.
- **Estado:** registrada · **superficie sin consumidor**.

### 8.7 `GET /api/inscripciones/{inscripcion_id}/pool`

- **Propósito:** **pool de participantes** de la inscripción: las personas pre-registradas sin participación activa, con su **elegibilidad de cupo** y un motivo bloqueante apto para UI. Es la única fuente de elegibilidad: el frontend no la recalcula.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad.
- **Consumidor:** `features/inscripciones/services/pool.service.ts` (`getPool`) → `features/inscripciones/hooks/useInscripcionPool.ts` → `features/inscripciones/components/PoolParticipantesSeccion.tsx` (tipos en `PoolParticipanteCard.tsx`).
- **Entrada:** path `inscripcion_id`.
- **Validación:** propiedad; `estado_pool` es un discriminador tipado (`LISTO` | `ESPERANDO_PAGO` | `SIN_CAPACIDAD` | `CUPO_POR_ASIGNAR`) y `motivo_bloqueo` es null cuando la persona es elegible.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.obtener_pool`.
- **Cadena:** Controller → `check_ownership_or_admin` → `InscripcionOrchestrator.obtener_pool_proceso` → selectores + `AsignacionCoreService` (saldo) → `InscripcionPresenter.present_pool` → `ApiResponse[PoolOut]`.
- **Modelos/tablas:** lectura `inscripciones_personas`, `usuarios_persona`, `asignaciones_cupo`, `commerce_compra`.
- **Efectos:** ninguno.
- **Invariantes:** la elegibilidad la decide el servidor; el `id` de cada entrada es el `InscripcionPersona.id` que espera la mutación de asignación.
- **Respuesta:** `data = { inscripcion_id, pool: [{ id, persona, estado, created_at, tiene_cupo_activo, estado_pool, motivo_bloqueo }] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 8.8 `POST /api/inscripciones/{inscripcion_id}/pool/asignar`

- **Propósito:** **asignación atómica** de un participante del pool a un equipo. Es la **única autoridad** de asignación de un participante a un equipo: el backend crea la `Participacion` y aplica todas las compuertas (cupo, R11, roster, fecha límite) dentro de una transacción.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad (`check_ownership_or_admin`).
- **Consumidor:** `features/inscripciones/services/pool.service.ts` (`asignarPoolAEquipo`) → `features/inscripciones/hooks/useAsignarParticipanteAEquipo.ts` → `features/inscripciones/components/SelectorParticipanteModal.tsx`.
- **Entrada:** path `inscripcion_id`; body `AsignarAEquipoIn` = `{ inscripcion_persona_id, equipo_id, rol (default "J"), talla_camiseta (default ""), notas (default "") }`.
- **Validación:** **R11** (una persona no juega dos veces en la **misma** disciplina); el cupo pagado debe existir y estar activo; el roster no puede exceder `Disciplina.max_jugadores`; la fecha límite del evento; la persona debe estar en el pool.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.asignar_a_equipo`.
- **Cadena:** Controller → `check_ownership_or_admin` → `InscripcionOrchestrator.asignar_a_equipo_proceso` → asignación atómica (flujo + `AsignacionCoreService`/`ParticipacionCoreService`) → ORM `participaciones`, `inscripciones_personas`, `asignaciones_cupo`, `acreditaciones_evento` → `InscripcionPresenter.present_participacion` → `ApiResponse` (sin tipo de payload) con `data = { participante: ParticipacionOut }`.
- **Modelos/tablas:** escritura `participaciones`, `inscripciones_personas` (estado), `asignaciones_cupo`, `acreditaciones_evento`; lectura `equipos`, `disciplinas`.
- **Efectos:** consume cupo pagado; recalcula la acreditación de la persona; una participación por (persona, disciplina).
- **Invariantes:** un cupo pagado autoriza a la persona en **todas** las disciplinas contratadas: se crea una `Participacion` por disciplina y R11 sólo prohíbe repetir en la misma disciplina; la asignación es atómica (nunca queda participación sin cupo).
- **Respuesta:** `data = { participante: ParticipacionOut }`; mensaje «La persona se agregó al equipo correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND` / `EQUIPO_NOT_FOUND`; 409 `CUPO_NO_ASIGNADO`, `CUPO_AGOTADO`, `PARTICIPANTE_DEBE_PREREGISTRARSE`, `R11_DUPLICADO`, `ROSTER_COMPLETO`, `FECHA_LIMITE_EXCEDIDA`; 422 por body inválido.
- **Estado:** registrada · **consumida**.
- **Nota de contrato:** la respuesta declara `ApiResponse` **sin tipo de payload**, lo que rompe el espejo de esquemas con el frontend (`contract/api-wrapper-presenter-contract.md` §7).

### 8.9 `GET /api/inscripciones/{inscripcion_id}/equipos/{equipo_id}/elegibles`

- **Propósito:** **candidatos** de un equipo concreto: para cada participante activo de la inscripción informa si tiene cupo pagado, en qué disciplinas ya juega y si es asignable **a este equipo**, con el motivo cuando no lo es.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad.
- **Consumidor:** `features/inscripciones/services/elegibles.service.ts` → `features/inscripciones/hooks/useElegiblesEquipo.ts` → `components/SelectorParticipanteModal.tsx` (tipos en el propio servicio).
- **Entrada:** path `inscripcion_id`, `equipo_id`.
- **Validación:** propiedad; la inscripción y el equipo deben existir y ser coherentes entre sí.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.obtener_elegibles_equipo`.
- **Cadena:** Controller → `check_ownership_or_admin` → `InscripcionOrchestrator.obtener_elegibles_equipo_proceso` → selectores + `AsignacionCoreService` → `InscripcionPresenter.present_elegibles_equipo` → `ApiResponse[ElegiblesEquipoOut]`.
- **Modelos/tablas:** lectura `participaciones`, `inscripciones_personas`, `asignaciones_cupo`, `equipos`, `disciplinas`.
- **Efectos:** ninguno.
- **Invariantes:** una persona que ya juega en **otra** disciplina sigue siendo candidata (el cupo paga todas las disciplinas); R11 sólo impide repetir en la **misma** disciplina; `asignable` + `motivo_no_asignable` son la autoridad de UI.
- **Respuesta:** `data = { inscripcion_id, equipo_id, equipo_nombre, disciplina, elegibles: [{ id, persona, estado, created_at, tiene_cupo_activo, estado_pool, motivo_bloqueo, disciplinas_asignadas[], ya_en_disciplina, asignable, motivo_no_asignable }] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND` / `EQUIPO_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 8.10 `POST /api/inscripciones/{inscripcion_id}/personas`

- **Propósito:** **preregistrar** una persona en la inscripción (alta en el *pool*) o, si se envía `equipo_id`, **colocar** en el equipo a un participante ya registrado. Es el único punto de entrada del ciclo de vida del participante.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad (`check_ownership_or_admin`).
- **Consumidor:** `features/inscripciones/services/pool.service.ts` (`preregistrarEnPool`, **sin** `equipo_id`) → `features/inscripciones/hooks/usePreregistrarEnPool.ts` → `features/inscripciones/components/AddParticipanteModal.tsx`.
- **Entrada (body `AgregarPersonaIn`):** exactamente uno de `persona_id` (persona existente) o `persona_data` (`{ tipo_documento ∈ {DNI,CE,PAS}, numero_documento ≤20, nombres ≤255, apellidos ≤255, genero ∈ {M,F}, telefono ≤9, whatsapp ≤9 }`); `equipo_id` opcional; `aceptaciones` opcional (lista de `BASES` | `APTITUD_FISICA` | `IMAGEN`).
- **Validación:** XOR `persona_id` ⊻ `persona_data` obligatorio (si no, `PersonaDataRequiredError` → 422 `PERSONA_REQUIRED`); `persona_data` hace **upsert** por documento (reutiliza la `Persona` existente si el documento coincide); una persona **nueva** (`persona_data`) **junto con** `equipo_id` se rechaza con 422 `PARTICIPANTE_DEBE_PREREGISTRARSE`; compuerta de capacidad contratada (`CupoContratadoExcedidoError`, con máximo en el mensaje técnico); la fecha límite del evento; la aceptación de BASES se registra con la versión de documento `BASES-SF26-2026-09-06`.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.agregar_persona`.
- **Cadena:** Controller (traduce `PersonaInlineIn` → `PersonaInlineData`) → `check_ownership_or_admin` → `InscripcionOrchestrator.agregar_persona_proceso` → `AgregarPersonaFlujo.ejecutar` → `AsignacionCoreService` (saldo) + `AcreditacionCoreService` → ORM `inscripciones_personas`, `asignacion_cupo`, `aceptaciones_inscripcion`, `participaciones`, `acreditaciones_evento`, `usuarios_persona` → `InscripcionPresenter.present_inscripcion_persona` o `present_participacion` → `ApiResponse` (sin tipo) con `data = { participante: … }`.
- **Modelos/tablas:** escritura `inscripciones_personas`, `aceptaciones_inscripcion`, `asignaciones_cupo` (reclamo automático del cupo pagado si queda capacidad libre), `participaciones` (si viene `equipo_id`), `acreditaciones_evento`, `usuarios_persona` (upsert).
- **Efectos:** puede **reclamar automáticamente** el cupo pagado de la inscripción; sincroniza la acreditación de la persona; registra las aceptaciones legales.
- **Invariantes:** sin `equipo_id` la persona **espera en el pool** y el cupo se reclama automáticamente sólo si queda capacidad pagada libre; el conteo de capacidad se compara con `>` (no `>=`) para no rechazar el último slot libre; si la inscripción no tiene capacidad pagada (`pagados == 0`) la compuerta se omite (permite preregistrar antes de comprar); el roster **no** se crea en la etapa de compra.
- **Respuesta:** `data = { participante: InscripcionPersonaOut | ParticipacionOut }`; mensaje «La persona se agregó correctamente.» o «La persona se agregó al equipo correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND` / `PERSONA_NOT_FOUND`; 409 `CUPO_CONTRATADO_EXCEDIDO`, `FECHA_LIMITE_EXCEDIDA`; 422 `PERSONA_REQUIRED`, `PARTICIPANTE_DEBE_PREREGISTRARSE`, `GENERO_NO_PERMITIDO`; 500 en fallos inesperados.
- **Estado:** registrada · **consumida**.
- **Nota de contrato:** la respuesta declara `ApiResponse` **sin tipo de payload** (misma desviación que 8.8).

### 8.11 `PATCH /api/inscripciones/{inscripcion_id}/personas/{persona_id}/retirar`

- **Propósito:** **retirar** a una persona del roster de la inscripción y desactivar sus participaciones.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad (`check_ownership_or_admin`).
- **Consumidor:** **sin consumidor conocido**. El frontend retira participantes por la vía de participación (`PATCH /api/participaciones/{id}/retirar`, ver 9.6), no por esta ruta.
- **Entrada:** path `inscripcion_id`, `persona_id`. Sin body.
- **Validación:** propiedad; la persona debe pertenecer a la inscripción; fecha límite del evento.
- **Controller:** `inscripcion_controller.py` → `InscripcionController.retirar_persona`.
- **Cadena:** Controller → `check_ownership_or_admin` → `InscripcionOrchestrator.retirar_persona_proceso` → `RetirarPersonaFlujo.ejecutar` → ORM `inscripciones_personas`, `participaciones`, `asignaciones_cupo`, `acreditaciones_evento` → `InscripcionPresenter.present_inscripcion_persona` → `ApiResponse[InscripcionPersonaOut]`.
- **Modelos/tablas:** escritura `inscripciones_personas`, `participaciones`, `asignaciones_cupo`, `acreditaciones_evento`.
- **Efectos:** libera el roster y recalcula la acreditación.
- **Invariantes:** la retirada no borra filas: cambia el estado (`R`); el cupo pagado puede liberarse según la misma regla multi-disciplina que 9.2.
- **Respuesta:** `data = InscripcionPersonaOut`; mensaje «La persona se retiró correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND` / `PERSONA_NOT_FOUND`; 409 `FECHA_LIMITE_EXCEDIDA`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 8.12 `GET /api/inscripciones/{inscripcion_id}/saldo`

- **Propósito:** **saldo de cupos** de la inscripción: contratados, pagados, asignados (consumidos) y disponibles. Es la respuesta de "¿todavía puedo asignar un cupo pagado?".
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad (`check_ownership_or_admin`).
- **Consumidor:** `features/inscripciones/services/pool.service.ts` (`getSaldoInscripcion`) → `features/inscripciones/hooks/useAsignarParticipanteAEquipo.ts` y `components/PoolParticipantesSeccion.tsx`.
- **Entrada:** path `inscripcion_id`.
- **Validación:** propiedad verificada antes del cálculo.
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/asignacion_controller.py` → `InscripcionSaldoController.obtener_saldo` (controlador con prefijo `/inscripciones`, registrado después de `AsignacionController`).
- **Cadena:** Controller → `check_ownership_or_admin` → `AsignacionOrchestrator.obtener_saldo` → `AsignacionCoreService.calcular_saldo_inscripcion` → ORM `commerce_compra`, `salesianos_fest_compra_inscripcion`, `asignaciones_cupo` → `AsignacionPresenter.present_saldo` → `ApiResponse[SaldoOut]`.
- **Modelos/tablas:** lectura `commerce_compra`, `salesianos_fest_compra_inscripcion`, `asignaciones_cupo`.
- **Efectos:** ninguno.
- **Invariantes:** `disponibles_pagados = 0` significa que nadie puede entrar a un equipo todavía; las compras canceladas no contratan; sólo cuentan los derechos `ACTIVA`.
- **Respuesta:** `data = { inscripcion_id, contratados, pagados, asignados_pagados, disponibles_pagados }`; mensaje «Saldo calculado.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

---

## 9. Dominio 6 — Equipos y participaciones (9 rutas)

### 9.1 `POST /api/equipos/`

- **Propósito:** **crear un equipo** dentro de una inscripción, en una disciplina (y categoría) concreta.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y **propiedad** de la inscripción (`check_ownership_or_admin(request, payload.inscripcion_id)`). La denegación no crea ningún equipo.
- **Consumidor:** **sin consumidor conocido**. Los equipos del usuario se crean en bloque dentro de `POST /api/inscripciones/completa/` (8.2); el frontend nunca llama a esta ruta.
- **Entrada (body `CrearEquipoIn`):** `inscripcion_id`, `disciplina_id`, `categoria_id?`, `nombre`, `estado` (default `EQUIPO_ACTIVO`).
- **Validación:** la inscripción debe existir y ser del llamador; la disciplina y la categoría deben existir; la fecha límite del evento (`evento.puede_modificar()`) bloquea la creación; el equipo se crea dentro de una transacción.
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py` → `EquipoController.crear_equipo` (mismo archivo, prefijo `/equipos`).
- **Cadena:** Controller → `check_ownership_or_admin` → `EquipoOrchestrator.crear_equipo_proceso` → `CrearEquipoFlujo.ejecutar` (transaction.atomic) → `EquipoCoreService` → ORM `equipos` → `InscripcionPresenter.present_equipo` → `ApiResponse[EquipoOut]`.
- **Modelos/tablas:** escritura `equipos`; lectura `inscripciones`, `disciplinas`, `categorias`.
- **Efectos:** ninguno fuera de la base de datos.
- **Invariantes:** el equipo nace sin participantes; la capacidad de jugadores por disciplina la define `Disciplina.min_jugadores`/`max_jugadores`.
- **Respuesta:** `data = { id, inscripcion_id, disciplina, categoria, nombre, estado, created_at }`; mensaje «Equipo creado correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 409 `FECHA_LIMITE_EXCEDIDA`; 422 por body inválido.
- **Estado:** registrada · **superficie sin consumidor**.

### 9.2 `GET /api/equipos/{equipo_id}`

- **Propósito:** **detalle de un equipo** por su id.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad **vía equipo**: `check_ownership_or_admin_for_equipo(request, equipo_id)`.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** path `equipo_id`.
- **Validación:** el equipo debe existir y pertenecer a una inscripción del llamador (o el llamador es admin).
- **Controller:** `inscripcion_controller.py` → `EquipoController.obtener_equipo`.
- **Cadena:** Controller → `check_ownership_or_admin_for_equipo` → `EquipoOrchestrator.obtener_equipo_proceso` → selector → `InscripcionPresenter.present_equipo` → `ApiResponse[EquipoOut]`.
- **Modelos/tablas:** lectura `equipos`, `disciplinas`, `categorias`.
- **Efectos:** ninguno.
- **Invariantes:** la autorización se resuelve a través de la inscripción del equipo.
- **Respuesta:** `data = EquipoOut`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EQUIPO_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 9.3 `GET /api/equipos/inscripcion/{inscripcion_id}`

- **Propósito:** **listar los equipos** de una inscripción.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad de la inscripción.
- **Consumidor:** **sin consumidor conocido**. El frontend obtiene los equipos dentro de `GET /api/inscripciones/{id}/detalle` (8.5), que ya los incluye.
- **Entrada:** path `inscripcion_id`.
- **Validación:** propiedad.
- **Controller:** `inscripcion_controller.py` → `EquipoController.listar_por_inscripcion`.
- **Cadena:** Controller → `check_ownership_or_admin` → `EquipoOrchestrator.listar_por_inscripcion_proceso` → selector → `InscripcionPresenter.present_equipos` → `ApiResponse[list[EquipoOut]]`.
- **Modelos/tablas:** lectura `equipos`, `disciplinas`, `categorias`.
- **Efectos:** ninguno.
- **Invariantes:** sólo los equipos de esa inscripción.
- **Respuesta:** `data = [EquipoOut]`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 9.4 `POST /api/participaciones/`

- **Propósito:** **crear una participación** (alta directa de una persona en un equipo), aplicando R11 y la validación de roster máximo.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`). La inscripción se deduce del `inscripcion_persona_id` y se verifica la propiedad sobre ella (`check_ownership_or_admin`).
- **Consumidor:** **sin consumidor conocido**. El frontend asigna desde el pool (8.8), que es la vía vigente y con respuesta tipada.
- **Entrada (body `CrearParticipacionIn`):** `inscripcion_persona_id`, `equipo_id`, `rol` (default `J`), `talla_camiseta` (default `""`), `notas` (default `""`).
- **Validación:** la `InscripcionPersona` debe existir (si no, `InscripcionNotFoundError`); R11 (no jugar dos veces en la misma disciplina); roster máximo de la disciplina; la persona debe tener cupo pagado activo.
- **Controller:** `inscripcion_controller.py` → `ParticipacionController.crear_participacion` (prefijo `/participaciones`).
- **Cadena:** Controller (resuelve `inscripcion_id` con `sync_to_async`) → `check_ownership_or_admin` → `ParticipacionOrchestrator.crear_participacion_proceso` → creación atómica → ORM `participaciones`, `acreditaciones_evento` → `InscripcionPresenter.present_participacion` → `ApiResponse[ParticipacionOut]`.
- **Modelos/tablas:** escritura `participaciones`, `acreditaciones_evento`; lectura `inscripciones_personas`, `equipos`, `disciplinas`.
- **Efectos:** consume cupo; sincroniza acreditación.
- **Invariantes:** la creación es atómica; una participación sin cupo pagado no puede existir.
- **Respuesta:** `data = ParticipacionOut`; mensaje «Participación registrada correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 409 `R11_DUPLICADO`, `CUPO_NO_ASIGNADO`, `ROSTER_COMPLETO`; 422 por body inválido.
- **Estado:** registrada · **superficie sin consumidor**.

### 9.5 `GET /api/participaciones/{participacion_id}`

- **Propósito:** **detalle de una participación** (persona, equipo, disciplina, rol, talla, estado).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad **vía participación**: `check_ownership_or_admin_for_participacion`.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** path `participacion_id`.
- **Validación:** la participación debe existir y pertenecer a una inscripción del llamador.
- **Controller:** `inscripcion_controller.py` → `ParticipacionController.obtener_participacion`.
- **Cadena:** Controller → `check_ownership_or_admin_for_participacion` → `ParticipacionOrchestrator.obter_participacion_proceso` → selector → `InscripcionPresenter.present_participacion` → `ApiResponse[ParticipacionOut]`.
- **Modelos/tablas:** lectura `participaciones`, `inscripciones_personas`, `usuarios_persona`, `equipos`, `disciplinas`.
- **Efectos:** ninguno.
- **Invariantes:** la autorización se resuelve a través de la inscripción de la participación.
- **Respuesta:** `data = ParticipacionOut`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `PARTICIPACION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 9.6 `GET /api/participaciones/equipo/{equipo_id}`

- **Propósito:** **roster de un equipo**: las participaciones de sus participantes.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad **vía equipo**.
- **Consumidor:** **sin consumidor conocido**. El roster llega dentro del detalle de inscripción (8.5).
- **Entrada:** path `equipo_id`.
- **Validación:** el equipo debe existir y ser del llamador.
- **Controller:** `inscripcion_controller.py` → `ParticipacionController.listar_por_equipo`.
- **Cadena:** Controller → `check_ownership_or_admin_for_equipo` → `ParticipacionOrchestrator.listar_por_equipo_proceso` → selector → `InscripcionPresenter.present_participaciones` → `ApiResponse[list[ParticipacionOut]]`.
- **Modelos/tablas:** lectura `participaciones`, `usuarios_persona`, `equipos`, `disciplinas`.
- **Efectos:** ninguno.
- **Invariantes:** una persona con participaciones retiradas sigue apareciendo con su estado (`R`); el filtro de estado no lo decide el cliente.
- **Respuesta:** `data = [ParticipacionOut]`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EQUIPO_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 9.7 `PATCH /api/participaciones/{participacion_id}`

- **Propósito:** **editar** los datos de una participación: rol, talla de camiseta, notas y estado.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad resuelta con `_check_participacion_ownership` (responsable de la inscripción padre o admin Django). Si el usuario no tiene `Persona`, la comprobación lanza `ForbiddenError`.
- **Consumidor:** `features/inscripciones/services/inscripcion.service.ts` (`editarParticipante`) → `features/inscripciones/hooks/useEditarParticipante.ts` → `features/inscripciones/components/EditParticipanteModal.tsx`.
- **Entrada:** path `participacion_id`; body `ActualizarParticipacionIn` = `{ rol?, talla_camiseta?, notas?, estado? }`. El frontend añade además `aseguradora_nombre` y `aseguradora_numero_poliza`, que **no** forman parte del esquema HTTP declarado (`ActualizarParticipacionIn` no los contempla).
- **Validación:** propiedad; actualización atómica del registro.
- **Controller:** `inscripcion_controller.py` → `ParticipacionController.actualizar_participacion`.
- **Cadena:** Controller → `_check_participacion_ownership` → `ParticipacionOrchestrator.actualizar_participacion_proceso` → `ParticipacionCoreService` → ORM `participaciones` → `InscripcionPresenter.present_participacion` → `ApiResponse[ParticipacionOut]`.
- **Modelos/tablas:** escritura `participaciones`.
- **Efectos:** ninguno fuera de la base de datos.
- **Invariantes:** el estado de la participación se mueve por los valores permitidos por el dominio (`A`/`R`).
- **Respuesta:** `data = ParticipacionOut`; mensaje «Participación actualizada correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `PARTICIPACION_NOT_FOUND`; 422 por body inválido.
- **Estado:** registrada · **consumida**.
- **Desviación detectada:** el frontend envía campos (`aseguradora_*`) que el esquema `ActualizarParticipacionIn` no declara; con el modelo actual se descartan silenciosamente (no hay `extra="allow"` ni campos de aseguradora en ese esquema).

### 9.8 `PATCH /api/participaciones/{participacion_id}/mover`

- **Propósito:** **mover** una participación a otro equipo.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad de la participación.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** path `participacion_id`; body `MoverParticipacionIn` = `{ equipo_destino_id: str }`.
- **Validación:** el equipo destino debe existir y ser coherente con la disciplina; R11 se reevalúa en el destino; la propiedad se verifica antes de mutar.
- **Controller:** `inscripcion_controller.py` → `ParticipacionController.mover_participacion`.
- **Cadena:** Controller → `_check_participacion_ownership` → `ParticipacionOrchestrator.mover_participacion_proceso` → movimiento atómico → ORM `participaciones` → `InscripcionPresenter.present_participacion` → `ApiResponse[ParticipacionOut]`.
- **Modelos/tablas:** escritura `participaciones`; lectura `equipos`, `disciplinas`.
- **Efectos:** recalcula la acreditación si la disciplina cambia.
- **Invariantes:** el cupo pagado sobrevive al movimiento (una persona puede jugar en varias disciplinas con un solo cupo).
- **Respuesta:** `data = ParticipacionOut`; mensaje «Participación movida correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `PARTICIPACION_NOT_FOUND` / `EQUIPO_NOT_FOUND`; 409 `R11_DUPLICADO`; 422 por body inválido.
- **Estado:** registrada · **superficie sin consumidor**.

### 9.9 `PATCH /api/participaciones/{participacion_id}/retirar`

- **Propósito:** **retirar** una participación (estado → `R`). No es un borrado: conserva la historia del roster.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad de la participación.
- **Consumidor:** `features/inscripciones/services/inscripcion.service.ts` (`eliminarParticipante`, que **no** borra: el propio frontend lo documenta como «retiro sets estado to R») → `features/inscripciones/hooks/useEditarParticipante.ts` → `components/EditParticipanteModal.tsx`.
- **Entrada:** path `participacion_id`. Sin body.
- **Validación:** propiedad; la retirada puede liberar el cupo si la persona ya no tiene participación activa en la inscripción.
- **Controller:** `inscripcion_controller.py` → `ParticipacionController.retirar_participacion`.
- **Cadena:** Controller → `_check_participacion_ownership` → `ParticipacionOrchestrator.retirer_participacion_proceso` → retirada atómica → ORM `participaciones`, `asignaciones_cupo`, `acreditaciones_evento` → `InscripcionPresenter.present_participacion` → `ApiResponse[ParticipacionOut]`.
- **Modelos/tablas:** escritura `participaciones`, `asignaciones_cupo`, `acreditaciones_evento`.
- **Efectos:** recalcula el acceso efectivo de la persona (R10: puede conservar acceso por otra inscripción).
- **Invariantes:** nunca se borra la fila; la capacidad comprada no se devuelve al evento, queda reasignable en la misma inscripción.
- **Respuesta:** `data = ParticipacionOut`; mensaje «Participación retirada correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `PARTICIPACION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

---

## 10. Dominio 7 — Compras y asignaciones de cupo (9 rutas)

### 10.1 `POST /api/compras/`

- **Propósito:** **crear una compra** de cupos (inicial o ampliación) para una inscripción: genera `commerce.Compra` + `pagos_ordenpago` + `salesianos_fest_compra_inscripcion` con el precio congelado del catálogo vigente.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); el usuario debe tener `Persona` y ser **responsable de la inscripción** (verificación explícita en el controller, que lanza `PermissionDenied` de Django).
- **Consumidor:** **sin consumidor conocido**. El alta del usuario se hace por `POST /api/inscripciones/completa/` (8.2), que ya incluye la compra inicial; las ampliaciones no tienen UI.
- **Entrada (body `CompraCreateIn`):** `inscripcion_id` (UUID), `tipo` (`INICIAL` | `AMPLIACION`), `cantidad` (> 0).
- **Validación:** la inscripción debe existir (`INSCRIPCION_NOT_FOUND`) y ser del llamador; el tipo `INICIAL` exige `cantidad >= Paquete.minimo_compra_inicial` (`CANTIDAD_INSUFICIENTE`); debe existir un `PaquetePrecio` vigente (`PRECIO_NO_ENCONTRADO`); la fecha límite del evento.
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/compra_controller.py` → `CompraController.crear_compra`.
- **Cadena:** Controller (crea `InscripcionSelector()` **a mano** y valida propiedad — desviación del contrato §4.8) → `CompraOrchestrator.crear_compra` → `CrearCompraFlujo._crear_compra` (transaction.atomic) → `IzipayCoreService` → ORM `commerce_compra`, `pagos_ordenpago`, `salesianos_fest_compra_inscripcion` → `CompraPresenter.present_created` → `ApiResponse[CompraCreateOut]`.
- **Modelos/tablas:** escritura `commerce_compra`, `pagos_ordenpago`, `salesianos_fest_compra_inscripcion`; lectura `inscripciones`, `paquetes_precios`.
- **Efectos:** crea la orden de pago asociada.
- **Invariantes:** el precio se **congela** en el momento de la compra (decisión D2); los cupos no se consumen hasta la confirmación del pago; la compra pertenece a la inscripción (responsable) y su línea `CompraInscripcion` es la composición que la liga al agregado deportivo.
- **Respuesta:** `data = { compra_id, compra_inscripcion_id, orden_pago_id, tipo, cantidad, precio_unitario, total, estado, message }`; mensaje «Compra creada correctamente. Proceda al pago.»
- **Errores:** 400 `BUSINESS_ERROR` (usuario sin `Persona` o cantidad insuficiente); 403 `PERMISSION_DENIED` (no es responsable); 404 `INSCRIPCION_NOT_FOUND`; 409 `PRECIO_NO_ENCONTRADO` / `CANTIDAD_INSUFICIENTE`; 422 por body inválido.
- **Estado:** registrada · **superficie sin consumidor**.

### 10.2 `GET /api/compras/{compra_id}`

- **Propósito:** **detalle de una compra**: tipo, cantidad, precio unitario y total congelados, estado comercial y orden de pago asociada.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); la propiedad se valida con `_validate_compra_ownership`: una compra **deportiva** pertenece al responsable de su inscripción; cualquier otra (lote de pases) al `Compra.responsable`.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** path `compra_id`.
- **Validación:** existencia + propiedad (la denegación es `PermissionDenied` de Django → 403 `PERMISSION_DENIED`).
- **Controller:** `compra_controller.py` → `CompraController.obtener_compra`.
- **Cadena:** Controller (`CompraSelector` inyectado → `sync_to_async(obtener_por_id)`) → `_validate_compra_ownership` → `CompraPresenter.present_detail` → `ApiResponse[CompraDetailOut]`.
- **Modelos/tablas:** lectura `commerce_compra`, `salesianos_fest_compra_inscripcion`, `pagos_ordenpago`.
- **Efectos:** ninguno.
- **Invariantes:** la regla deportiva **no** se debilita: una compra con inscripción siempre se contrasta contra el responsable de esa inscripción.
- **Respuesta:** `data = { id, inscripcion_id, orden_pago_id, tipo, cantidad, precio_unitario, total, estado, created_at }`.
- **Errores:** 403 `PERMISSION_DENIED`; 404 `COMPRA_NOT_FOUND`; 400 `BUSINESS_ERROR` si el usuario no tiene `Persona`.
- **Estado:** registrada · **superficie sin consumidor**.

### 10.3 `GET /api/compras/inscripciones/{inscripcion_id}/compras`

- **Propósito:** **listar las compras** de una inscripción (historial de compras iniciales y ampliaciones con sus importes congelados).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y responsabilidad de la inscripción.
- **Consumidor:** **sin consumidor conocido**. El resumen de pagos del detalle de inscripción (8.5) ya incluye las compras.
- **Entrada:** path `inscripcion_id`.
- **Validación:** existencia de la inscripción + propiedad.
- **Controller:** `compra_controller.py` → `CompraController.listar_compras_inscripcion`.
- **Cadena:** Controller (`InscripcionSelector` a mano) → comprobación de propiedad → `CompraSelector.listar_por_inscripcion` → `CompraPresenter.present_list` → `ApiResponse[CompraListOut]`.
- **Modelos/tablas:** lectura `commerce_compra`, `salesianos_fest_compra_inscripcion`, `inscripciones`.
- **Efectos:** ninguno.
- **Invariantes:** sólo compras de esa inscripción.
- **Respuesta:** `data = { compras: [CompraDetailOut] }`.
- **Errores:** 403 `PERMISSION_DENIED`; 404 `INSCRIPCION_NOT_FOUND`; 400 `BUSINESS_ERROR`.
- **Estado:** registrada · **superficie sin consumidor**.

### 10.4 `POST /api/compras/{compra_id}/iniciar-pago`

- **Propósito:** **abrir el checkout** del proveedor: genera el token de sesión de Izipay y devuelve la configuración del SDK. El backend deriva los datos del comprador y el importe desde el `Persona` del responsable y desde el snapshot congelado de la compra.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad de la compra (`_validate_compra_ownership`).
- **Consumidor:** `features/pagos/services/pago.service.ts` (`iniciarPagoIzipay`) → `features/pagos/components/IzipayModal.tsx` (y `features/pagos/utils/checkout.observador.ts`).
- **Entrada:** path `compra_id`. Sin body.
- **Validación:** la compra debe existir (`COMPRA_NOT_FOUND`) y ser del llamador; debe estar en estado `PENDIENTE` (`COMPRA_NO_COBRABLE`); debe tener comprador (`COMPRA_SIN_COMPRADOR`); el intento de pago anterior se **retira** y se crea uno nuevo con identidad propia (`transaction_id`, `order_number`) — nunca se reproduce una sesión de proveedor.
- **Controller:** `compra_controller.py` → `CompraController.iniciar_pago`.
- **Cadena:** Controller → `CompraOrchestrator.iniciar_pago` → `IniciarPagoFlujo._iniciar_pago` → `PagosOrchestrator.preparar_pago_izipay` → `RegistrarPagoIzipayFlujo._preparar_pago` (transaction.atomic; bloqueo de la fila de la orden) → `IzipayCoreService` (**llamada externa** a Izipay Token/Generate) → ORM `pagos_ordenpago`, `pagos_transaccionpago` → `CompraPresenter.present_iniciar_pago` → `ApiResponse[IniciarPagoOut]`.
- **Modelos/tablas:** escritura `pagos_transaccionpago` (nuevo intento), `pagos_ordenpago` (estado); lectura `commerce_compra`, `usuarios_persona`.
- **Efectos:** **llamada externa al proveedor de pagos**; persiste la sesión del proveedor en el intento vivo.
- **Invariantes:** el navegador **nunca** envía ni controla el importe, la moneda ni los datos del comprador; cada apertura de checkout produce un intento nuevo con identidad propia; si el intento fue superado mientras se abría la sesión, se rechaza con un conflicto reintentable en vez de entregar una sesión muerta.
- **Respuesta:** `data = { compra_id, orden_pago_id, transaction_id, order_number, token, merchant_code, amount, currency, buyer_email, buyer_name, buyer_surname }`; mensaje «Sesion de pago preparada.»
- **Errores:** 400 `COMPRA_SIN_COMPRADOR`; 403 `PERMISSION_DENIED`; 404 `COMPRA_NOT_FOUND`; 409 `COMPRA_NO_COBRABLE`; 422/500 si el proveedor no responde.
- **Estado:** registrada · **consumida**.

### 10.5 `POST /api/compras/{compra_id}/cancelar`

- **Propósito:** **cancelar una compra** (reembolso o pago abandonado) y **revocar los derechos** que financió.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); autorización = responsable de la inscripción **o** admin Django. Si el llamador es admin, se salta la comprobación de propiedad (`responsable_id = None`).
- **Consumidor:** **sin consumidor conocido**. La cancelación administrativa de compras de pases tiene su propia ruta (§11.x).
- **Entrada:** path `compra_id`. Sin body.
- **Validación:** la compra debe existir (`COMPRA_NOT_FOUND`); la propiedad se comprueba antes de mutar; una compra financiada por una **aprobación manual activa** **no** puede cancelarla su propietario (`COMPRA_CON_APROBACION_MANUAL`); una compra de **pases** no puede cancelarse por el comprador (`PASE_CANCELACION_REQUIERE_ADMINISTRACION`).
- **Controller:** `compra_controller.py` → `CompraController.cancelar_compra`.
- **Cadena:** Controller → `CompraOrchestrator.cancelar_compra` → `CancelarCompraFlujo._cancelar_compra` (transaction.atomic con `SELECT FOR UPDATE` sobre la compra) → ORM `commerce_compra`, `pagos_ordenpago`, `asignaciones_cupo`, `pases_beneficiarios`, `participaciones`, `acreditaciones_evento` → `CompraPresenter.present_cancelar` → `ApiResponse[CompraCanceladaOut]`.
- **Modelos/tablas:** escritura `commerce_compra`, `pagos_ordenpago`, `asignaciones_cupo`, `pases_beneficiarios`, `participaciones`, `acreditaciones_evento`.
- **Efectos:** revoca **sólo** los derechos financiados por esa compra; recalcula el acceso efectivo de todas las personas afectadas (R10: pueden conservar acceso por otra inscripción).
- **Invariantes:** la cancelación es **idempotente** (`ya_cancelada`); una asignación pagada por otra compra conserva su derecho; una participación respaldada por un derecho revocado se retira; los derechos de pase revocados se consumen para siempre.
- **Respuesta:** `data = { compra_id, inscripcion_id, estado, ya_cancelada, asignaciones_revocadas, personas_afectadas }`; mensaje «La compra se canceló correctamente.»
- **Errores:** 403 `PERMISSION_DENIED`; 404 `COMPRA_NOT_FOUND`; 409 `COMPRA_CON_APROBACION_MANUAL`, `PASE_CANCELACION_REQUIERE_ADMINISTRACION`, `COMPRA_YA_CANCELADA`.
- **Estado:** registrada · **superficie sin consumidor**.

### 10.6 `POST /api/asignaciones/`

- **Propósito:** **asignar un cupo pagado** a una persona ya registrada dentro de la inscripción. Crea la `InscripcionPersona` + `AsignacionCupo` (`ACTIVA`) y sincroniza su acreditación.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y **propiedad** (`check_ownership_or_admin(request, inscripcion_id)`): responsable de la inscripción o admin Django. Nunca se puede consumir la capacidad pagada de otra inscripción.
- **Consumidor:** **sin consumidor conocido**. El flujo vigente del frontend es el *pool* (8.10 + 8.8), que reutiliza la misma capacidad pagada.
- **Entrada (body `AsignarPersonaIn`):** `inscripcion_id` (UUID), `persona_id` (UUID).
- **Validación:** la inscripción debe existir; la persona no puede tener ya una asignación activa (`PERSONA_YA_ASIGNADA`); debe haber saldo disponible (`CUPO_AGOTADO` — el responsable debe comprar ampliación); la fecha límite del evento (`FECHA_LIMITE_EXCEDIDA`); una asignación `LIBERADA` previa se **reactiva** (idempotencia).
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/asignacion_controller.py` → `AsignacionController.asignar_persona`.
- **Cadena:** Controller → `check_ownership_or_admin` → `AsignacionOrchestrator.asignar_persona` → `AsignarPersonaFlujo._asignar_persona` (transaction.atomic) → `AsignacionCoreService` + `AcreditacionCoreService` → ORM `inscripciones_personas`, `asignaciones_cupo`, `acreditaciones_evento` → `AsignacionPresenter.present_asignar_persona` → `ApiResponse[AsignarPersonaOut]`.
- **Modelos/tablas:** escritura `inscripciones_personas`, `asignaciones_cupo`, `acreditaciones_evento`; lectura `inscripciones`, `commerce_compra`.
- **Efectos:** consume cupo pagado; crea la acreditación de la persona.
- **Invariantes:** el cupo sólo se asigna contra capacidad **pagada**; la asignación es transaccional; la operación es idempotente frente a una asignación liberada previa.
- **Respuesta:** `data = { asignacion_id, inscripcion_id, persona_id, estado, compra_origen_id }`; mensaje «Persona asignada correctamente.»
- **Errores:** 400 `BUSINESS_ERROR` (usuario sin `Persona`); 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 409 `CUPO_AGOTADO`, `PERSONA_YA_ASIGNADA`, `FECHA_LIMITE_EXCEDIDA`.
- **Estado:** registrada · **superficie sin consumidor**.

### 10.7 `GET /api/asignaciones/{asignacion_id}`

- **Propósito:** **detalle de una asignación de cupo**: inscripción, persona, compra de origen, estado, motivo y fecha de liberación.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad **vía asignación**: `check_ownership_or_admin_for_asignacion`.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** path `asignacion_id`.
- **Validación:** la asignación debe existir y pertenecer al llamador.
- **Controller:** `asignacion_controller.py` → `AsignacionController.obtener_asignacion`.
- **Cadena:** Controller → `check_ownership_or_admin_for_asignacion` → `AsignacionSelector.obtener_por_id` (vía `sync_to_async`) → `AsignacionPresenter.present_detail` → `ApiResponse[AsignacionDetailOut]`.
- **Modelos/tablas:** lectura `asignaciones_cupo`, `usuarios_persona`, `inscripciones`.
- **Efectos:** ninguno.
- **Invariantes:** la asignación nunca sale del ámbito del propietario de su inscripción.
- **Respuesta:** `data = { id, inscripcion_id, compra_id, persona_id, persona_nombre, estado, motivo, liberada_en, created_at }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ASIGNACION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 10.8 `POST /api/asignaciones/liberar`

- **Propósito:** **liberar el cupo** de un jugador, retirando sus participaciones y liberando el derecho pagado si ya no juega en ninguna disciplina de esa inscripción.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad (`check_ownership_or_admin`).
- **Consumidor:** **sin consumidor conocido**.
- **Entrada (body `LiberarCupoIn`):** `inscripcion_id`, `persona_id`, `motivo?`, `disciplina_id?`.
- **Validación:** `disciplina_id` **acota** la liberación a una disciplina; el cupo **sobrevive** si la persona mantiene una participación activa en otra disciplina de la misma inscripción; la fecha límite del evento.
- **Controller:** `asignacion_controller.py` → `AsignacionController.liberar_cupo`.
- **Cadena:** Controller → `check_ownership_or_admin` → `AsignacionOrchestrator.liberar_cupo` → `LiberarCupoFlujo._liberar_cupo` (transaction.atomic) → `AsignacionCoreService` + `AcreditacionCoreService` → ORM `participaciones`, `asignaciones_cupo`, `acreditaciones_evento` → `AsignacionPresenter.present_liberar_cupo` → `ApiResponse[LiberarCupoOut]`.
- **Modelos/tablas:** escritura `participaciones`, `asignaciones_cupo`, `acreditaciones_evento`.
- **Efectos:** retira participaciones; recalcula la acreditación considerando **todas** las inscripciones de la persona (R10); la capacidad comprada **no** se devuelve al evento, queda reasignable en la misma inscripción.
- **Invariantes:** un cupo paga varias disciplinas; la comprobación «¿sigue jugando en otra disciplina?» se evalúa **antes** de retirar las filas (después siempre sería falsa y la regla no podría expresarse).
- **Respuesta:** `data = { inscripcion_id, persona_id, asignacion_id, estado, cupo_liberado }`; el mensaje es condicional: «Cupo liberado correctamente.» o «Participaciones retiradas. El cupo se mantiene mientras la persona juegue en otra disciplina.»
- **Errores:** 400 `BUSINESS_ERROR`; 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 409 `FECHA_LIMITE_EXCEDIDA`.
- **Estado:** registrada · **superficie sin consumidor**.

### 10.9 `GET /api/asignaciones/inscripciones/{inscripcion_id}/asignaciones`

- **Propósito:** **listar las asignaciones de cupo** de una inscripción (quién tiene derecho pagado y en qué estado).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y propiedad de la inscripción.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** path `inscripcion_id`.
- **Validación:** propiedad.
- **Controller:** `asignacion_controller.py` → `AsignacionController.listar_asignaciones_inscripcion`.
- **Cadena:** Controller → `check_ownership_or_admin` → `AsignacionSelector.listar_por_inscripcion` → `AsignacionPresenter.present_list` → `ApiResponse[AsignacionListOut]`.
- **Modelos/tablas:** lectura `asignaciones_cupo`, `usuarios_persona`.
- **Efectos:** ninguno.
- **Invariantes:** nunca lista asignaciones de otra inscripción.
- **Respuesta:** `data = { asignaciones: [AsignacionDetailOut] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `INSCRIPCION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

---

## 11. Dominio 8 — Pagos Izipay (4 rutas)

Contexto común: modelo de dos canales. El **navegador** retransmite el `kr_answer` del SDK y debe estar autenticado y ser dueño de la orden; el **proveedor** notifica servidor a servidor y se autentica por la firma del comercio. En ambos casos la liquidación comercial la ejecuta el backend, nunca el navegador.

### 11.1 `POST /api/pagos/izipay/confirmar`

- **Propósito:** **retransmitir la respuesta del proveedor** (`kr_answer`) y confirmar el pago. Es idempotente: si la transacción ya estaba confirmada, se vuelve a conducir la liquidación (también idempotente) y la respuesta informa `already_confirmed = true`.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`). `_actor(request)` resuelve el actor: si es `is_staff`/`is_superuser` → `(None, es_admin=True)`; si no, exige `persona_fk_id` y devuelve `(persona_id, False)`; sin `Persona` ⇒ `PagoNoAutorizadoError`.
- **Consumidor:** `features/pagos/services/pago.service.ts` (`confirmarPagoIzipay`) → `features/pagos/components/IzipayModal.tsx` → `features/pagos/utils/checkout.observador.ts` / `checkout.recuperacion.ts`.
- **Entrada (body `IzipayConfirmIn`):** `kr_answer`: `{ code (obligatorio), message?, transactionId?, orderNumber?, amount?, signature?, payloadHttp?, response?: { payMethod?, paymentMethodType?, transactionId?, order[] } }`. El controller envía `payload.kr_answer.model_dump()` al orquestador.
- **Validación:** la **firma del proveedor** se verifica cuando la clave de comercio está configurada (una firma inválida siempre se rechaza); el payload se **contrasta con la transacción persistida** (monto, orden, transacción); la propiedad de la orden se exige en el flujo.
- **Controller:** `backend/modules/pagos/presentation/controllers/pagos_controller.py` → `PagosController.confirmar_pago`.
- **Cadena:** Controller (`_actor`) → `PagosOrchestrator.confirmar_pago_izipay` → `RegistrarPagoIzipayFlujo._confirmar_pago` (verifica canal, monto/orden, `transaction.atomic` para actualizar la transacción y pasar la orden a `PAGADA`) → `ConfirmarPagoFlujo._confirmar_compra` (liquidación comercial: `Compra` → `PAGADA` + reparto determinista de cupos + sincronización de acreditaciones) → ORM `pagos_transaccionpago`, `pagos_ordenpago`, `commerce_compra`, `asignaciones_cupo`, `acreditaciones_evento` → `IzipayPresenter.present_confirm` → `ApiResponse[IzipayConfirmOut]`.
- **Modelos/tablas:** escritura `pagos_transaccionpago`, `pagos_ordenpago`, `commerce_compra`, `asignaciones_cupo`, `acreditaciones_evento`.
- **Efectos:** **llamada externa** al proveedor para verificar la firma; liquidación comercial y reparto de cupos.
- **Invariantes:** un payload falsado, obsoleto o ajeno **no cambia nada**; la liquidación sólo ocurre cuando la orden **prueba** el pago (`PAGO_NO_VERIFICADO` si no hay evidencia); el navegador nunca envía una confirmación comercial.
- **Respuesta:** `data = { transaction_id, success, status, orden_pago_id, response_code, response_message, metodo_pago, already_confirmed, settlement_status }`. El **mensaje** es fijo y refleja el estado autoritativo: «Pago confirmado correctamente.» / «Pago confirmado. La activación comercial está pendiente.» / «El pago no se completó.»
- **Errores:** 404 `TRANSACCION_PAGO_NO_ENCONTRADA`; 403 `PAGO_NO_AUTORIZADO` (no es dueño de la orden); 409 `PAGO_DATOS_INCONSISTENTES` (el payload contradice la orden); 409 `PAGO_NO_VERIFICADO` (sin evidencia); 400 `PAGO_FIRMA_INVALIDA`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 11.2 `POST /api/pagos/izipay/notificacion`

- **Propósito:** **notificación servidor a servidor** del proveedor. Es el canal que no depende del navegador: si el usuario cierra el popup, la notificación sigue informing el pago.
- **Llamador / rol / permiso:** **público** (`auth=None`, `permissions=[AllowAny]`, que **sustituye** al `IsAuthenticated` del controlador). La autenticidad no la da la sesión sino la **firma del comercio**.
- **Consumidor:** **el proveedor Izipay** (llamada externa servidor a servidor). **No** hay consumidor en el navegador.
- **Entrada (body `IzipayNotificacionIn`):** `payloadHttp: str` (obligatorio), `signature: str` (obligatorio), `transactionId?`.
- **Validación:** la clave de comercio (`keyHash`) **debe** estar configurada y la firma **debe** verificarse: **no hay ruta de repliegue**; una notificación no verificable se rechaza.
- **Controller:** `pagos_controller.py` → `PagosController.recibir_notificacion`.
- **Cadena:** Controller → `PagosOrchestrator.confirmar_pago_por_notificacion` → `RegistrarPagoIzipayFlujo._confirmar_notificacion` (verificación de firma → `transaction.atomic` → transacción `EXITO` + orden `PAGADA`) → `ConfirmarPagoFlujo._confirmar_compra` (liquidación) → ORM `pagos_transaccionpago`, `pagos_ordenpago`, `commerce_compra`, `asignaciones_cupo` → `IzipayPresenter.present_confirm` → `ApiResponse[IzipayConfirmOut]`.
- **Modelos/tablas:** escritura `pagos_transaccionpago`, `pagos_ordenpago`, `commerce_compra`, `asignaciones_cupo`, `acreditaciones_evento`.
- **Efectos:** llamada externa al proveedor para verificar la firma; liquidación comercial.
- **Invariantes:** la confirmación es **idempotente**: un reintento del proveedor converge en lugar de duplicar; la firma se verifica **antes** de mutar nada.
- **Respuesta:** `data = IzipayConfirmOut` (misma forma que 11.1) con el mensaje condicional correspondiente.
- **Errores:** 400 `PAGO_NOTIFICACION_NO_VERIFICABLE` (falta la clave de comercio); 400 `PAGO_FIRMA_INVALIDA`; 404 `TRANSACCION_PAGO_NO_ENCONTRADA`; 409 `PAGO_DATOS_INCONSISTENTES`.
- **Estado:** registrada · **consumida por el proveedor externo**.

### 11.3 `GET /api/pagos/transacciones/{transaction_id}`

- **Propósito:** **estado de un intento de pago**. Es el canal de recuperación del checkout: cuando la retransmisión del navegador es incierta, el cliente lee el estado de la transacción que preparó en lugar de confiar en un relay que puede no llegar nunca.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); el acceso se restringe al **dueño** de la orden o a un administrador (`_actor`).
- **Consumidor:** `features/pagos/services/pago.service.ts` (`obtenerEstadoTransaccion`) → `features/pagos/components/IzipayModal.tsx` y `features/pagos/utils/checkout.recuperacion.ts`.
- **Entrada:** path `transaction_id`.
- **Validación:** la transacción debe existir y pertenecer a una orden del llamador (o el llamador es admin).
- **Controller:** `pagos_controller.py` → `PagosController.obtener_transaccion`.
- **Cadena:** Controller (`_actor`) → `PagosOrchestrator.obtener_transaccion` → `RegistrarPagoIzipayFlujo._obtener_transaccion` → ORM `pagos_transaccionpago`, `pagos_ordenpago` → `IzipayPresenter.present_transaccion` → `ApiResponse[TransaccionPagoOut]`.
- **Modelos/tablas:** lectura `pagos_transaccionpago`, `pagos_ordenpago`.
- **Efectos:** ninguno.
- **Invariantes:** sólo lectura; no se hace ninguna llamada al proveedor desde el navegador.
- **Respuesta:** `data = { id, orden_pago_id, transaction_id, order_number, amount, currency, status, response_code, response_message, metodo_pago, created_at, updated_at }`.
- **Errores:** 404 `TRANSACCION_PAGO_NO_ENCONTRADA`; 403 `PAGO_NO_AUTORIZADO`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 11.4 `GET /api/pagos/ordenes/{orden_id}`

- **Propósito:** **estado de una orden de pago**: importe, moneda, estado, fecha de pago, caducidad y snapshots descriptivos.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); dueño de la orden o administrador (`_actor`).
- **Consumidor:** **sin consumidor conocido**. El frontend usa la ruta de transacción (11.3) como canal de recuperación y no consulta la orden directamente.
- **Entrada:** path `orden_id`.
- **Validación:** la orden debe existir y pertenecer al llamador (o el llamador es admin).
- **Controller:** `pagos_controller.py` → `PagosController.obtener_orden`.
- **Cadena:** Controller (`_actor`) → `PagosOrchestrator.obtener_orden` → `RegistrarPagoIzipayFlujo._obtener_orden` → ORM `pagos_ordenpago` → `IzipayPresenter.present_orden_pago` → `ApiResponse[OrdenPagoOut]`.
- **Modelos/tablas:** lectura `pagos_ordenpago`.
- **Efectos:** ninguno.
- **Invariantes:** el `metadata` interno de la orden nunca se expone (sólo `descripcion` y `referencia_externa`, que son snapshots de negocio).
- **Respuesta:** `data = { id, numero, monto_total, moneda, estado, pagada_en, expires_at, descripcion, referencia_externa, created_at }`.
- **Errores:** 404 `ORDEN_PAGO_NO_ENCONTRADA`; 403 `PAGO_NO_AUTORIZADO`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

---

## 12. Dominio 9 — Acreditación y acceso (4 rutas)

Contexto común: la acreditación es la credencial de una persona en el evento. El **QR es una credencial portadora viva**: nunca viaja en las respuestas de lectura; sólo lo entrega la acción explícita de regeneración.

### 12.1 `GET /api/acreditaciones/{evento_id}/{persona_id}`

- **Propósito:** **estado de acreditación** de una persona en un evento: estado, acceso a fiesta/box, autorización administrativa y observación. No entrega el QR.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); `check_acreditacion_access_or_admin(request, persona_id)` — la persona acreditada o un admin Django.
- **Consumidor:** **sin consumidor conocido**. La vista de administración usa su propia superficie (`GET /api/administracion/acreditaciones`, §13.13), que además nunca incluye `codigo_qr`.
- **Entrada:** path `evento_id`, `persona_id`.
- **Validación:** la acreditación debe existir para ese par evento/persona (`ACREDITACION_NOT_FOUND`).
- **Controller:** `backend/modules/salesianos_fest/presentation/controllers/acreditacion_controller.py` → `AcreditacionController.obtener_acreditacion`.
- **Cadena:** Controller → `check_acreditacion_access_or_admin` → `AcreditacionSelector.obtener_por_evento_persona` (vía `sync_to_async`) → `AcreditacionPresenter.present_acreditacion` → `ApiResponse[AcreditacionOut]`.
- **Modelos/tablas:** lectura `acreditaciones_evento`, `usuarios_persona`.
- **Efectos:** ninguno.
- **Invariantes:** `codigo_qr` **no** forma parte del payload: es una credencial portadora y sólo la entrega la acción admin de generación; `acceso_fiesta` es el acceso **efectivo** (resultado de aplicar la precedencia de autorización).
- **Respuesta:** `data = { acreditacion_id, evento_id, persona_id, estado, acceso_fiesta, acceso_box, autorizacion_fiesta, habilitado, observacion }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ACREDITACION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 12.2 `POST /api/acreditaciones/{evento_id}/{persona_id}/generar-qr`

- **Propósito:** **regenerar el código QR** de una acreditación. Es la **única** acción que entrega la credencial viva; al rotarla, la credencial anterior deja de funcionar.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y la capacidad `admin.acreditaciones.escribir` (`permissions=[RequireAcreditacionesEscribir]`, que **sustituye** al `IsAuthenticated` del controlador) — la tienen el staff operativo y el nivel de ruptura. Anónimo → 401; autenticado no admin → 403 y **no se muta nada**.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** path `evento_id`, `persona_id`. Sin body.
- **Validación:** la acreditación debe existir (`ACREDITACION_NOT_FOUND`).
- **Controller:** `acreditacion_controller.py` → `AcreditacionController.generar_qr`.
- **Cadena:** Controller → `AcreditacionOrchestrator.regenerar_qr` → servicio de acreditación (rotación del `codigo_qr`) → ORM `acreditaciones_evento` → `AcreditacionPresenter.present_generar_qr` → `ApiResponse[GenerarQROut]`.
- **Modelos/tablas:** escritura `acreditaciones_evento`.
- **Efectos:** emite una credencial nueva e invalida la anterior.
- **Invariantes:** rotación efectiva e inmediata; la credencial antigua deja de servir en el mismo instante.
- **Respuesta:** `data = { acreditacion_id, codigo_qr }`; mensaje «Codigo QR regenerado.»
- **Errores:** 403 `ACTION_NOT_ALLOWED` (sin la capacidad); 404 `ACREDITACION_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 12.3 `PATCH /api/acreditaciones/{evento_id}/{persona_id}/override-fiesta`

- **Propósito:** **override administrativo del acceso a fiesta**: fija `autorizacion_fiesta` en `AUTORIZADA` o `BLOQUEADA`, recalcula el acceso efectivo y guarda el motivo en la observación.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y la capacidad `admin.acreditaciones.escribir`.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** path `evento_id`, `persona_id`; body `OverrideFiestaIn` = `{ autorizacion: str, motivo: str }` (motivo obligatorio).
- **Validación:** `autorizacion` debe ser válida (`AUTORIZADA` / `BLOQUEADA`); el motivo es obligatorio; la acreditación debe existir.
- **Controller:** `acreditacion_controller.py` → `AcreditacionController.override_fiesta`.
- **Cadena:** Controller → `AcreditacionOrchestrator.aplicar_override_fiesta` → `OverrideFiestaFlujo._aplicar_override` (transaction.atomic) → `AcreditacionCoreService` → ORM `acreditaciones_evento` → `AcreditacionPresenter.present_override` → `ApiResponse[OverrideFiestaOut]`.
- **Modelos/tablas:** escritura `acreditaciones_evento`.
- **Efectos:** auditoría del override (autor, motivo y marca de tiempo en `observacion`).
- **Invariantes:** precedencia `BLOQUEADA > AUTORIZADA > AUTOMATICA`; `AUTOMATICA` se deriva de las compras pagadas con beneficio FIESTA; **el override no se borra** en la siguiente sincronización.
- **Respuesta:** `data = { persona_id, evento_id, autorizacion_fiesta, acceso_fiesta, observacion }`; mensaje «Override de fiesta aplicado.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ACREDITACION_NOT_FOUND`; 400 por `autorizacion` inválida; 422 por motivo vacío.
- **Estado:** registrada · **superficie sin consumidor**.

### 12.4 `POST /api/acceso/registrar`

- **Propósito:** **registrar el intento de acceso** por lectura de QR en un punto de control. Devuelve el veredicto (`PERMITIDO` / `DENEGADO`) y lo deja auditado.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`); el `operador_id` es el usuario autenticado (queda registrado como responsable del escaneo).
- **Consumidor:** **sin consumidor conocido**. No existe lector de QR en el frontend; el registro de accesos que sí ve la administración (`GET /api/administracion/accesos`) se alimenta de esta ruta.
- **Entrada (body `RegistrarAccesoIn`):** `qr_token: str` (UUID del QR), `punto_acceso: str?`.
- **Validación:** el QR debe existir (`ACREDITACION_NOT_FOUND`); el evento debe estar activo; la acreditación debe estar `ACTIVA` y `habilitado != False`; el acceso a fiesta se evalúa por precedencia de `autorizacion_fiesta`; **uso único por día y evento**: un `PERMITIDO` ya registrado ese día ⇒ `CONFLICT` (`ACCESO_DUPLICADO`).
- **Controller:** `acreditacion_controller.py` → `AccesoController.registrar_acceso` (prefijo `/acceso`).
- **Cadena:** Controller → `AcreditacionOrchestrator.registrar_acceso` → `RegistrarAccesoFlujo._registrar_acceso` (transaction.atomic: comprueba uso único, crea el `ControlAcceso`) → `AcreditacionCoreService` → ORM `controles_acceso`, `acreditaciones_evento` → `AcreditacionPresenter.present_registrar_acceso` → `ApiResponse[RegistrarAccesoOut]`.
- **Modelos/tablas:** escritura `controles_acceso`; lectura `acreditaciones_evento`.
- **Efectos:** registra el intento de acceso (auditoría de puerta).
- **Invariantes:** el QR es **no adivinable** (UUID); un mismo QR **no** puede usarse dos veces el mismo día; tanto el caso permitido como el denegado quedan registrados.
- **Respuesta:** `data = { resultado, persona, acceso_fiesta, timestamp }`; el mensaje es condicional: «Acceso registrado.» o «Acceso denegado.»
- **Errores:** 404 `ACREDITACION_NOT_FOUND` (QR desconocido); 409 `ACCESO_DUPLICADO` (ya usado hoy); 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

---

## 13. Dominio 10 — Administración operativa (18 rutas)

Contexto común:
- **Evento activo** se resuelve **en el servidor** desde `settings.EVENTO_ACTIVO_NOMBRE`; el cliente nunca manda `evento_id`.
- **Permisos**: `RequireAdminVer` (`admin.ver`), `RequirePagosVer` (`admin.pagos.ver`), `RequireUsuariosVer` (`admin.usuarios.ver`), `RequirePagosAprobar` (`admin.pagos.aprobar`). El nivel `staff` **no** aprueba ni anula pagos; sólo `superusuario` lo hace.
- **Todas son de sólo lectura** salvo cuatro: las dos de aprobación/anulación manual de pagos y la cancelación administrativa de una compra de pases.
- **Paginación**: `ApiResponse[PaginatedData[X]]` con `items/total/page/page_size/total_pages`; los filtros se combinan con AND; `ordering` es una lista blanca y un valor o filtro inválido se rechaza con 422 `INVALID_REQUEST`.

### 13.1 `GET /api/administracion/health`

- **Propósito:** **sonda de la fundación** del módulo de administración: prueba el registro de la app, el cableado de inyección de dependencias y el permiso de administración sin exponer datos de negocio.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** **sin consumidor conocido**.
- **Entrada:** sin parámetros.
- **Validación:** ninguna adicional.
- **Controller:** `backend/modules/administracion/presentation/controllers/admin_fundacion_controller.py` → `AdminFundacionController.health`.
- **Cadena:** Controller → `AdminFundacionOrchestrator.obtener_fundacion` → `EventoSelector` (evento activo por nombre, con fallback) → `AdminFundacionPresenter.present_fundacion` → `ApiResponse[AdminHealthOut]`.
- **Modelos/tablas:** lectura `eventos`.
- **Efectos:** ninguno.
- **Invariantes:** sólo lectura; no expone datos de negocio.
- **Respuesta:** `data = { modulo, estado, evento_activo_id?, evento_activo_nombre? }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 401 sin sesión.
- **Estado:** registrada · **superficie sin consumidor**.

### 13.2 `GET /api/administracion/resumen`

- **Propósito:** **panorama operativo** del evento activo: ocho bloques de métricas (evento, inscripciones, pagos, cupos, pases, equipos, participantes, acreditaciones, accesos). Todos los números se calculan en el servidor.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.resumen.service.ts` (`getAdminResumen`) → `features/admin/hooks/useAdminResumen.ts` → `features/admin/components/AdminOverview.tsx` → `app/(app)/administracion/page.tsx`.
- **Entrada:** sin parámetros.
- **Validación:** el evento activo se resuelve en el servidor; sin evento activo ⇒ 404 `EVENTO_ACTIVO_NO_ENCONTRADO`.
- **Controller:** `backend/modules/administracion/presentation/controllers/admin_resumen_controller.py` → `AdminResumenController.resumen`.
- **Cadena:** Controller → `AdminResumenOrchestrator.obtener_resumen` → `AdminResumenSelector` + servicios de consulta → ORM `eventos`, `inscripciones`, `commerce_compra`, `pagos_ordenpago`, `asignaciones_cupo`, `equipos`, `participaciones`, `acreditaciones_evento`, `controles_acceso`, `pases_beneficiarios` → `AdminResumenPresenter.present_resumen` → `ApiResponse[AdminResumenOut]`.
- **Modelos/tablas:** lectura (múltiple, sólo lectura) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** las cifras de personas y de filas de roster **no** se mezclan (`participantes.personas_distintas` vs `participaciones_activas`); `compras_pagadas_sin_liquidar` delata pagos cobrados sin activación comercial.
- **Respuesta:** `data = { evento, inscripciones, pagos, cupos, pases, equipos, participantes, acreditaciones, accesos }` (cada bloque con sus contadores y desgloses).
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 13.3 `GET /api/administracion/catalogos`

- **Propósito:** **listas de opciones de filtro** de la administración: disciplinas, paquetes, promociones, categorías, puntos de acceso y los vocabularios de estado del dominio. Reutiliza las fuentes de los módulos propietarios (sin duplicar reglas de negocio).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.resumen.service.ts` (`getAdminCatalogos`) → `features/admin/hooks/useAdminCatalogos.ts` → todas las listas de administración (`AdminInscripcionesLista`, `AdminEquiposLista`, `AdminPagosLista`, `AdminParticipantesLista`, `AdminAcreditacionesLista`, `AdminUsuariosLista`) para poblar sus filtros.
- **Entrada:** sin parámetros.
- **Validación:** ninguna adicional.
- **Controller:** `admin_resumen_controller.py` → `AdminResumenController.catalogos`.
- **Cadena:** Controller → `AdminResumenOrchestrator.obtener_catalogos` → selectores de los módulos propietarios → ORM `disciplinas`, `paquetes`, `promociones`, `categorias`, `eventos` (+ vocabularios de `core/domain/constants.py`) → `AdminCatalogosPresenter.present_catalogos` → `ApiResponse[AdminCatalogosOut]`.
- **Modelos/tablas:** lectura `disciplinas`, `paquetes`, `promociones`, `categorias`, `eventos`.
- **Efectos:** ninguno.
- **Invariantes:** los vocabularios de estado salen del backend; el frontend no los inventa.
- **Respuesta:** `data = { evento_id, evento_nombre, disciplinas[], paquetes[], promociones[], categorias[], puntos_acceso[], estados: { inscripcion[], compra[], orden_pago[], asignacion_cupo[], equipo[], acreditacion[], autorizacion_fiesta[], acceso[], pool[], rol_participante[], roster[], estado_participacion[], tipo_compra[], estado_operativo_pago[], estado_capacidad_equipo[] } }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 401 sin sesión.
- **Estado:** registrada · **consumida** (dependencia común de todas las listas).

### 13.4 `GET /api/administracion/inscripciones`

- **Propósito:** **tabla de inscripciones** del evento activo: responsable, paquete, promoción, estado, conteos de equipos/personas/participaciones, cupos y monto pagado.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.inscripcion.service.ts` → `features/admin/hooks/useAdminInscripciones.ts` → `features/admin/components/AdminInscripcionesLista.tsx` → `app/(app)/administracion/inscripciones/page.tsx`.
- **Entrada (query):** `page?`, `page_size?` (máx. 100), `q?` (búsqueda sobre responsable y paquete), `ordering?` (lista blanca: `created_at`, `estado`, `responsable`, `paquete`), `estado?`, `paquete_id?`, `promocion_id?`, `responsable_persona_id?`.
- **Validación:** filtros combinados con AND; `ordering` fuera de la lista blanca o filtro inválido ⇒ 422 `INVALID_REQUEST`.
- **Controller:** `backend/modules/administracion/presentation/controllers/admin_inscripcion_controller.py` → `AdminInscripcionController.listar_inscripciones`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.listar_inscripciones` (resuelve evento activo) → `AdminInscripcionSelector` + `AdminPaginacionService` + `AdminConsultaService` → ORM `inscripciones`, `equipos`, `participaciones`, `inscripciones_personas`, `commerce_compra`, `asignaciones_cupo`, `usuarios_persona` → `AdminInscripcionPresenter.present_listado` → `ApiResponse[PaginatedData[AdminInscripcionListItemOut]]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** el ámbito es el evento activo; los importes vienen del snapshot congelado de la compra; los conteos de personas y participaciones son números distintos por diseño.
- **Respuesta:** `data = { items: [{ id, evento_nombre, responsable_nombre, responsable_documento, paquete_nombre, promocion_nombre, estado, equipos_total, equipos_completos, personas, participaciones, cupos_contratados, cupos_pagados, cupos_disponibles, monto_pagado, created_at }], total, page, page_size, total_pages }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 422 `INVALID_REQUEST`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 13.5 `GET /api/administracion/inscripciones/{inscripcion_id}`

- **Propósito:** **drilldown** de una inscripción: equipos (con su roster), participantes, compras, asignaciones de cupo, aceptaciones legales y saldo de cupos.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.inscripcion.service.ts` (`getAdminInscripcionDetalle`) → `useAdminInscripciones` → `features/admin/components/AdminInscripcionDetalle.tsx` → `app/(app)/administracion/inscripciones/[id]/page.tsx`.
- **Entrada:** path `inscripcion_id`.
- **Validación:** un id desconocido y un id de otra edición se responden **igual**: 404 `RESOURCE_NOT_FOUND` — la superficie no confirma la existencia de recursos fuera de su ámbito.
- **Controller:** `admin_inscripcion_controller.py` → `AdminInscripcionController.obtener_inscripcion`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.obtener_inscripcion_detalle` → selectores de administración → ORM `inscripciones`, `equipos`, `participaciones`, `inscripciones_personas`, `commerce_compra`, `asignaciones_cupo`, `aceptaciones_inscripcion` → `AdminInscripcionPresenter.present_detalle` → `ApiResponse[AdminInscripcionDetailOut]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** alcance restringido al evento activo; no se exponen UUIDs técnicos de otros dominios más allá de los identificadores necesarios.
- **Respuesta:** `data = { …campos de la lista, delegado_nombre, observacion, fecha_limite_modificacion, equipos[], participantes[], compras[], asignaciones[], aceptaciones[], saldo: { contratados, pagados, asignados_pagados, disponibles_pagados } }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `RESOURCE_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 13.6 `GET /api/administracion/pagos`

- **Propósito:** **tabla de pagos** del evento activo con el **veredicto operativo** de cada uno (`estado_operativo`): la única respuesta a «¿está este pago hecho?».
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequirePagosVer` (`admin.pagos.ver`).
- **Consumidor:** `features/admin/services/admin.pago.service.ts` (`getAdminPagos`) → `features/admin/hooks/useAdminPagos.ts` → `features/admin/components/AdminPagosLista.tsx` → `app/(app)/administracion/pagos/page.tsx`.
- **Entrada (query):** `page?`, `page_size?`, `q?` (número de orden y responsable), `ordering?` (lista blanca: `created_at`, `total`, `cantidad`, `estado_compra`, `estado_orden`, `pagada_en`), `estado_compra?`, `estado_orden?`, `estado_operativo?` (`SIN_ORDEN`, `PAGADA`, `PAGADA_SIN_LIQUIDAR`, `PAGADA_SIN_EVIDENCIA`, `PAGADA_SIN_FECHA`, `PENDIENTE`, `CANCELADA`, `VENCIDA`), `tipo?` (`INICIAL`/`AMPLIACION`), `desde?`, `hasta?` (ISO).
- **Validación:** los importes salen del snapshot congelado; `ordering` y filtros fuera de la lista blanca ⇒ 422 `INVALID_REQUEST`.
- **Controller:** `backend/modules/administracion/presentation/controllers/admin_pago_controller.py` → `AdminPagoController.listar_pagos`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.listar_pagos` → `AdminPagoSelector` + `EstadoOperativoPagoService` (veredicto) → ORM `pagos_ordenpago`, `pagos_transaccionpago`, `commerce_compra`, `salesianos_fest_compra_inscripcion`, `salesianos_fest_compra_pase`, `usuarios_persona` → `AdminPagoPresenter.present_listado` → `ApiResponse[PaginatedData[AdminPagoListItemOut]]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** la respuesta **nunca** lleva `metadata`, `token_sesion`, `response_message` ni `transaction_id`: sólo campos explícitos y seguros; los hechos que alimentan el veredicto siguen viajando como traza de auditoría.
- **Respuesta:** `data = { items: [{ compra_id, orden_pago_id?, numero_orden?, inscripcion_id?, pase_id?, responsable_nombre, tipo, producto_nombre, cantidad, precio_unitario, total, estado_compra, estado_orden?, pagada_en?, origen_pago, estado_operativo, monto_orden?, moneda_orden?, beneficiarios_activos, beneficiarios_revocados, created_at }], total, page, page_size, total_pages }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 422 `INVALID_REQUEST`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 13.7 `GET /api/administracion/pagos/{orden_pago_id}`

- **Propósito:** **drilldown** de una orden de pago: la orden, sus intentos de pago y sus aprobaciones manuales.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequirePagosVer`.
- **Consumidor:** `features/admin/services/admin.pago.service.ts` (`getAdminPagoDetalle`) → `useAdminPagos` (detalle por URL) → `components/AdminPagosLista.tsx` (panel lateral de detalle).
- **Entrada:** path `orden_pago_id`.
- **Validación:** una orden desconocida y una orden de otra edición se responden igual: 404 `RESOURCE_NOT_FOUND`.
- **Controller:** `admin_pago_controller.py` → `AdminPagoController.obtener_pago`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.obtener_pago_detalle` → `AdminPagoSelector` → ORM `pagos_ordenpago`, `pagos_transaccionpago`, `pagos_aprobacion_pago_manual`, `pases_beneficiarios`, `usuarios_persona` → `AdminPagoPresenter.present_detalle` → `ApiResponse[AdminPagoDetailOut]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** los intentos llevan campos explícitos: sin `metadata`, sin `token_sesion`, sin `response_message`, sin `transaction_id`; los beneficiarios de un pase aparecen sin nombres ni documentos.
- **Respuesta:** `data = { …campos de la lista, transacciones[], aprobaciones[], beneficiarios[] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `RESOURCE_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 13.8 `POST /api/administracion/pagos/{orden_pago_id}/aprobar-manual`

- **Propósito:** **aprobar un pago recibido fuera del proveedor** (transferencia, efectivo, Yape, Plin) y liquidar la compra que financia. La evidencia se registra **antes** de la liquidación comercial: si la liquidación falla, la prueba del pago queda durable y la activación pendiente.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) y la capacidad `admin.pagos.aprobar` (`permissions=[RequirePagosAprobar]`, que **sustituye** a `RequirePagosVer`). El staff operativo recibe 403.
- **Consumidor:** `features/admin/services/admin.pago.service.ts` (`aprobarPagoManual`) → `features/admin/hooks/useAdminPagosComandos.ts` → `features/admin/components/AdminPagoManualDialog.tsx` → `app/(app)/administracion/pagos/page.tsx`.
- **Entrada (body `AdminPagoAprobarManualIn`):** `canal` (Literal del dominio), `referencia: str`, `monto: Decimal`, `moneda: str`, `motivo: str`. Todos obligatorios: una aprobación sin evidencia no es una aprobación.
- **Validación:** el interruptor `PAGO_MANUAL_APROBACION_ENABLED` debe estar activo; si ya existe una aprobación activa ⇒ operación idempotente (`YA_APROBADA`, sin escribir); si la orden ya tiene una transacción exitosa del proveedor ⇒ `ORDEN_YA_PAGADA_CON_IZIPAY`; si la compra ya está cancelada ⇒ `COMPRA_YA_CANCELADA`; **importe y moneda deben coincidir exactamente** con la orden ⇒ `MONTO_NO_COINCIDE`.
- **Controller:** `admin_pago_controller.py` → `AdminPagoController.aprobar_pago_manual` (el actor se toma de `request.auth.id`).
- **Cadena:** Controller → `AdminOperacionOrchestrator.aprobar_pago_manual` → `AprobarPagoManualFlujo._aprobar_pago_manual` (bloquea la orden; `transaction.atomic` escribe la aprobación y pasa la orden a `PAGADA`; **después** del commit se conduce la liquidación por el puerto `IConfirmadorOrdenPagoService`) → ORM `pagos_aprobacion_pago_manual`, `pagos_ordenpago`, `commerce_compra`, `asignaciones_cupo`, `acreditaciones_evento` → `AdminPagoPresenter.present_aprobar_manual` → `ApiResponse[AdminPagoAprobarManualOut]`.
- **Modelos/tablas:** escritura `pagos_aprobacion_pago_manual`, `pagos_ordenpago`, `commerce_compra`, `asignaciones_cupo`, `acreditaciones_evento`.
- **Efectos:** **nunca** crea una `TransaccionPago`: un pago manual no pasó por el proveedor y fabricar una transacción corrompería la conciliación y la traza de auditoría.
- **Invariantes:** el importe y la moneda deben ser **exactos**; la operación es idempotente; la prueba del pago es durable antes de la liquidación; la liquidación nunca contradice al proveedor.
- **Respuesta:** `data = { resultado ("APROBADA"|"YA_APROBADA"), settlement_status, orden_pago_id, numero_orden, estado_orden, aprobacion_id, estado_aprobacion, canal, referencia, monto, moneda, motivo, actor, approved_at }`; mensaje «El pago manual se registró correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `APROBACION_PAGO_MANUAL_NO_ENCONTRADA` / `RESOURCE_NOT_FOUND`; 409 `ORDEN_YA_PAGADA_CON_IZIPAY`, `COMPRA_YA_CANCELADA`, `MONTO_NO_COINCIDE`, `PAGO_MANUAL_APROBACION_DESHABILITADA`; 422 por body inválido.
- **Estado:** registrada · **consumida**.

### 13.9 `POST /api/administracion/pagos/{orden_pago_id}/anular-manual`

- **Propósito:** **anular la aprobación manual** de una orden: marca la aprobación `ANULADA` (actor, fecha, motivo), cancela la orden y la compra, y revoca **sólo** los derechos que financió esa compra.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.pagos.aprobar` (sustituye a `RequirePagosVer`).
- **Consumidor:** `features/admin/services/admin.pago.service.ts` (`anularPagoManual`) → `useAdminPagosComandos` → `components/AdminPagoManualDialog.tsx`.
- **Entrada:** path `orden_pago_id`; body `AdminPagoAnularManualIn` = `{ motivo: str }` (obligatorio).
- **Validación:** la anulación es **idempotente** (repetirla responde `YA_ANULADA` sin revocar dos veces); sólo se revoca lo que financió esa compra; las aprobacionesmanuales de otras órdenes no se tocan.
- **Controller:** `admin_pago_controller.py` → `AdminPagoController.anular_pago_manual`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.anular_pago_manual` → `CancelarCompraFlujo._anular_pago_manual` (actualiza de forma atómica aprobación, orden y compra con actor, fecha y motivo; luego revoca por la vía canónica) → ORM `pagos_aprobacion_pago_manual`, `pagos_ordenpago`, `commerce_compra`, `asignaciones_cupo`, `pases_beneficiarios`, `participaciones`, `acreditaciones_evento` → `AdminPagoPresenter.present_anular_manual` → `ApiResponse[AdminPagoAnularManualOut]`.
- **Modelos/tablas:** escritura (múltiple) — ver arriba.
- **Efectos:** recalcula el acceso efectivo de todas las personas afectadas.
- **Invariantes:** **no es un reembolso monetario**: es la revocación de la activación y de los derechos; la anulación de la aprobación es la **decisión auditada**, y por eso una compra con aprobación activa no puede cancelarla su propietario (10.5).
- **Respuesta:** `data = { resultado, orden_pago_id, compra_id, estado_compra, estado_orden, estado_aprobacion, asignaciones_revocadas, beneficiarios_revocados, personas_afectadas, anulada_por, anulada_en, motivo_anulacion }`; mensaje «La aprobación manual del pago se anuló correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `APROBACION_PAGO_MANUAL_NO_ENCONTRADA`; 409 `COMPRA_YA_CANCELADA`; 422 por motivo vacío.
- **Estado:** registrada · **consumida**.

### 13.10 `GET /api/administracion/equipos`

- **Propósito:** **tabla de equipos** del evento activo con su estado de plantilla **derivado** en el servidor.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.operacion.service.ts` (`getAdminEquipos`) → `features/admin/hooks/useAdminEquipos.ts` → `features/admin/components/AdminEquiposLista.tsx` → `app/(app)/administracion/equipos/page.tsx`.
- **Entrada (query):** `page?`, `page_size?`, `q?` (nombre del equipo), `ordering?` (lista blanca: `created_at`, `nombre`, `disciplina`, `estado`), `inscripcion_id?`, `disciplina_id?`, `estado?`, `roster?` (`COMPLETO`/`INCOMPLETO`).
- **Validación:** un equipo es `COMPLETO` cuando sus participaciones **activas** alcanzan el `min_jugadores` de su disciplina; filtros combinados con AND; `ordering` inválido ⇒ 422.
- **Controller:** `backend/modules/administracion/presentation/controllers/admin_operacion_controller.py` → `AdminOperacionController.listar_equipos`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.listar_equipos` → `AdminEquipoSelector` + `AdminPaginacionService` → ORM `equipos`, `participaciones`, `disciplinas`, `categorias`, `inscripciones` → `AdminInscripcionPresenter.present_equipo_listado` → `ApiResponse[PaginatedData[AdminEquipoListItemOut]]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** el estado de plantilla se deriva, no se persiste ni lo recalcula el cliente; `estado_capacidad` distingue la capacidad comercial de la inscribed.
- **Respuesta:** `data = { items: [{ id, nombre, disciplina_sigla, disciplina_nombre, categoria_nombre?, inscripcion_id, inscripcion_ref, inscripcion_estado, estado, jugadores_registrados, minimo_deportivo, maximo_deportivo, estado_capacidad, estado_roster, created_at }], total, page, page_size, total_pages }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 422 `INVALID_REQUEST`.
- **Estado:** registrada · **consumida**.

### 13.11 `GET /api/administracion/participantes`

- **Propósito:** **superficie de personas** (pool) del evento: la gente registrada en una inscripción, con su estado de pool derivado y el motivo de bloqueo.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.operacion.service.ts` (`getAdminParticipantes`) → `features/admin/hooks/useAdminParticipantes.ts` → `features/admin/components/AdminParticipantesLista.tsx` → `app/(app)/administracion/participantes/page.tsx`.
- **Entrada (query):** `page?`, `page_size?`, `q?` (persona), `ordering?` (lista blanca: `created_at`, `persona`, `estado`), `estado_pool?` (`LISTO`, `ESPERANDO_PAGO`, `SIN_CAPACIDAD`, `CUPO_POR_ASIGNAR`), `disciplina_id?`, `con_cupo?` (`true`/`false`).
- **Validación:** el estado de pool es **derivado** de la capacidad pagada de la inscripción y de la asignación de cupo de la persona: nunca se persiste ni lo recalcula el cliente.
- **Controller:** `admin_operacion_controller.py` → `AdminOperacionController.listar_participantes`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.listar_participantes` → `AdminParticipanteSelector` + servicios de consulta → ORM `inscripciones_personas`, `usuarios_persona`, `asignaciones_cupo`, `inscripciones`, `participaciones` → `AdminInscripcionPresenter.present_participante_listado` → `ApiResponse[PaginatedData[AdminParticipanteListItemOut]]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** personas y filas de roster son **dos números distintos**; un cupo pagado autoriza a una persona en **todas** las disciplinas contratadas.
- **Respuesta:** `data = { items: [{ inscripcion_persona_id, persona_id, persona_nombre, persona_documento, inscripcion_id, estado, estado_pool, motivo_bloqueo?, disciplinas[], created_at }], total, page, page_size, total_pages }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 422 `INVALID_REQUEST`.
- **Estado:** registrada · **consumida**.

### 13.12 `GET /api/administracion/participaciones`

- **Propósito:** **superficie de roster**: una persona colocada en un equipo de una disciplina. No es la lista de personas.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.operacion.service.ts` (`getAdminParticipaciones`) → `useAdminParticipantes` (sección «participaciones») → `components/AdminParticipantesLista.tsx`.
- **Entrada (query):** `page?`, `page_size?`, `q?` (persona y equipo), `ordering?` (lista blanca: `created_at`, `persona`, `equipo`, `disciplina`, `rol`, `estado`), `disciplina_id?`, `rol?` (`J`/`C`/`D`), `estado?` (`A`/`R`), `inscripcion_id?`.
- **Validación:** los filtros se combinan con AND; `ordering` inválido ⇒ 422.
- **Controller:** `admin_operacion_controller.py` → `AdminOperacionController.listar_participaciones`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.listar_participaciones` → `AdminParticipanteSelector`/selector de participaciones → ORM `participaciones`, `inscripciones_personas`, `usuarios_persona`, `equipos`, `disciplinas` → `AdminInscripcionPresenter.present_participacion_listado` → `ApiResponse[PaginatedData[AdminParticipacionListItemOut]]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** los estados `A`/`R` se muestran tal cual (retiradas incluidos).
- **Respuesta:** `data = { items: [{ id, inscripcion_persona_id, persona_nombre, persona_documento, equipo_nombre, disciplina_sigla, inscripcion_id, rol, talla_camiseta, estado, created_at }], total, page, page_size, total_pages }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 422 `INVALID_REQUEST`.
- **Estado:** registrada · **consumida**.

### 13.13 `GET /api/administracion/acreditaciones`

- **Propósito:** **tabla de acreditaciones** del evento activo con el estado de fiesta, la autorización administrativa y los conteos de accesos. **Nunca** incluye el QR.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.operacion.service.ts` (`getAdminAcreditaciones`) → `features/admin/hooks/useAdminAcreditaciones.ts` → `features/admin/components/AdminAcreditacionesLista.tsx` → `app/(app)/administracion/acreditaciones/page.tsx`.
- **Entrada (query):** `page?`, `page_size?`, `q?` (persona), `ordering?` (lista blanca: `persona`, `estado`, `autorizacion_fiesta`), `estado?`, `autorizacion_fiesta?` (`AUTOMATICA`/`AUTORIZADA`/`BLOQUEADA`), `acceso_fiesta?` (`true`/`false`).
- **Validación:** la respuesta **nunca** lleva `codigo_qr`; el QR es una credencial portadora viva y sólo lo entrega la acción de generación del módulo propietario.
- **Controller:** `admin_operacion_controller.py` → `AdminOperacionController.listar_acreditaciones`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.listar_acreditaciones` → `AdminAcreditacionSelector` → ORM `acreditaciones_evento`, `usuarios_persona`, `controles_acceso` → `AdminAcreditacionPresenter.present_listado` → `ApiResponse[PaginatedData[AdminAcreditacionListItemOut]]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** `accesos_permitidos` y `ultimo_acceso` se derivan del log de accesos.
- **Respuesta:** `data = { items: [{ id, persona_id, persona_nombre, persona_documento, estado, acceso_fiesta, acceso_box?, autorizacion_fiesta, habilitado?, observacion, accesos_permitidos, ultimo_acceso?, created_at }], total, page, page_size, total_pages }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 422 `INVALID_REQUEST`.
- **Estado:** registrada · **consumida**.

### 13.14 `GET /api/administracion/acreditaciones/{acreditacion_id}`

- **Propósito:** **drilldown** de una acreditación con su registro de accesos.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.operacion.service.ts` (`getAdminAcreditacionDetalle`) → `useAdminAcreditacionDetalle` → `components/AdminAcreditacionesLista.tsx` (panel de detalle).
- **Entrada:** path `acreditacion_id`.
- **Validación:** id desconocido e id de otra edición ⇒ 404 `RESOURCE_NOT_FOUND` idéntico.
- **Controller:** `admin_operacion_controller.py` → `AdminOperacionController.obtener_acreditacion`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.obtener_acreditacion_detalle` → `AdminAcreditacionSelector` → ORM `acreditaciones_evento`, `controles_acceso`, `usuarios_persona` → `AdminAcreditacionPresenter.present_detalle` → `ApiResponse[AdminAcreditacionDetailOut]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** la respuesta **nunca** lleva `codigo_qr`.
- **Respuesta:** `data = { …campos de la lista, accesos: [{ id, acreditacion_id, persona_nombre, persona_documento, resultado, punto_acceso?, operador_nombre?, fecha_hora }] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `RESOURCE_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 13.15 `GET /api/administracion/accesos`

- **Propósito:** **bitácora de accesos** del evento activo: los intentos registrados por los escáneres, del más reciente al más antiguo por defecto.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireAdminVer`.
- **Consumidor:** `features/admin/services/admin.operacion.service.ts` (`getAdminAccesos`) → `useAdminAccesos` → `components/AdminAcreditacionesLista.tsx` (sección «accesos»).
- **Entrada (query):** `page?`, `page_size?`, `q?` (persona), `ordering?` (lista blanca: `fecha_hora`, `resultado`, `punto_acceso`), `resultado?` (`PERMITIDO`/`DENEGADO`), `punto_acceso?`, `desde?`, `hasta?` (ISO).
- **Validación:** rango de fechas en ISO; filtros combinados con AND.
- **Controller:** `admin_operacion_controller.py` → `AdminOperacionController.listar_accesos`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.listar_accesos` → `AdminAcreditacionSelector`/selector de accesos → ORM `controles_acceso`, `acreditaciones_evento`, `usuarios_persona` → `AdminAcreditacionPresenter.present_listado_accesos` → `ApiResponse[PaginatedData[AdminAccesoListItemOut]]`.
- **Modelos/tablas:** lectura (múltiple) — ver arriba.
- **Efectos:** ninguno.
- **Invariantes:** se registran tanto los accesos permitidos como los denegados (no se filtran los fallidos).
- **Respuesta:** `data = { items: [{ id, acreditacion_id, persona_nombre, persona_documento, resultado, punto_acceso?, operador_nombre?, fecha_hora }], total, page, page_size, total_pages }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `EVENTO_ACTIVO_NO_ENCONTRADO`; 422 `INVALID_REQUEST`.
- **Estado:** registrada · **consumida**.

### 13.16 `GET /api/administracion/usuarios`

- **Propósito:** **tabla de cuentas**. Las cuentas son identidades **globales**: no están acotadas al evento.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireUsuariosVer` (`admin.usuarios.ver`).
- **Consumidor:** `features/admin/services/admin.usuario.service.ts` (`getAdminUsuarios`) → `features/admin/hooks/useAdminUsuarios.ts` → `features/admin/components/AdminUsuariosLista.tsx` → `app/(app)/administracion/usuarios/page.tsx`.
- **Entrada (query):** `page?`, `page_size?`, `q?` (usuario, correo, documento y nombre), `ordering?` (lista blanca: `created_at`, `username`, `nombres`, `last_login`), `estado?` (`activo`/`inactivo`), `es_admin?` (`true`/`false`).
- **Validación:** la respuesta **nunca** lleva la contraseña, su hash ni ningún token; **sí** publica el nivel de la cuenta (`is_staff`, `is_superuser`, `nivel`) para que un administrador de cuentas vea quién tiene el nivel de ruptura.
- **Controller:** `backend/modules/administracion/presentation/controllers/admin_usuario_controller.py` → `AdminUsuarioController.listar_usuarios`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.listar_usuarios` → `AdminUsuarioSelector` + paginación → ORM `usuarios_usuario`, `usuarios_persona` → `AdminUsuarioPresenter.present_listado` → `ApiResponse[PaginatedData[AdminUsuarioListItemOut]]`.
- **Modelos/tablas:** lectura `usuarios_usuario`, `usuarios_persona`.
- **Efectos:** ninguno.
- **Invariantes:** sólo lectura; la superficie **no** gestiona contraseñas.
- **Respuesta:** `data = { items: [{ id, username, email?, nombres, apellidos, persona_id, persona_documento, es_admin, is_staff, is_superuser, nivel, is_active, last_login?, created_at }], total, page, page_size, total_pages }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 422 `INVALID_REQUEST`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 13.17 `GET /api/administracion/usuarios/{usuario_id}`

- **Propósito:** **drilldown** de una cuenta: sus datos y las inscripciones que posee **dentro del evento activo**.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `RequireUsuariosVer`.
- **Consumidor:** `features/admin/services/admin.usuario.service.ts` (`getAdminUsuarioDetalle`) → `useAdminUsuarios` (detalle) → `components/AdminUsuariosLista.tsx`.
- **Entrada:** path `usuario_id`.
- **Validación:** id desconocido ⇒ 404 `RESOURCE_NOT_FOUND`; la contraseña y su hash nunca se exponen; las inscripciones mostradas **sí** están acotadas al evento activo.
- **Controller:** `admin_usuario_controller.py` → `AdminUsuarioController.obtener_usuario`.
- **Cadena:** Controller → `AdminOperacionOrchestrator.obtener_usuario_detalle` → `AdminUsuarioSelector` → ORM `usuarios_usuario`, `usuarios_persona`, `inscripciones` → `AdminUsuarioPresenter.present_detalle` → `ApiResponse[AdminUsuarioDetailOut]`.
- **Modelos/tablas:** lectura `usuarios_usuario`, `usuarios_persona`, `inscripciones`.
- **Efectos:** ninguno.
- **Invariantes:** sólo lectura; publica el nivel de la cuenta.
- **Respuesta:** `data = { …campos de la lista, personas: [{ inscripcion_id, estado, created_at }] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `RESOURCE_NOT_FOUND`; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 13.18 `POST /api/administracion/pases/compras/{compra_id}/cancelar`

- **Propósito:** **cancelación administrativa** de una compra de pases: cancela la compra y su orden, revoca permanentemente los derechos nominativos que financió y recalcula el acceso efectivo de cada persona afectada.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.pagos.aprobar` (`permissions=[RequirePagosAprobar]`, que **sustituye** a `RequirePagosVer` del controlador). El staff operativo recibe 403.
- **Consumidor:** `features/admin/pases/services/admin.pase.service.ts` (`cancelarCompraPase`) → `features/admin/pases/hooks/useAdminPaseComandos.ts` → `features/admin/pases/components/AdminPaseCancelarDialog.tsx` → `app/(app)/administracion/pagos/page.tsx`.
- **Entrada:** path `compra_id`; body `AdminPaseCancelarIn` = `{ motivo: str }` (obligatorio).
- **Validación:** la compra debe existir y **ser una compra de pases** (si no, `COMPRA_NOT_FOUND`); el motivo es obligatorio; la decisión queda auditada.
- **Controller:** `backend/modules/administracion/presentation/controllers/admin_pases_controller.py` → `AdminPasesController.cancelar_compra_pase` (prefijo `/administracion/pases`).
- **Cadena:** Controller → `AdminOperacionOrchestrator.cancelar_compra_pase` → `CancelarCompraFlujo._cancelar_compra_pase` (misma vía canónica de revocación que 10.5) → ORM `commerce_compra`, `pagos_ordenpago`, `pases_beneficiarios`, `acreditaciones_evento` → `AdminPasesPresenter.present_cancelar_compra_pase` → `ApiResponse[AdminPaseCanceladaOut]`.
- **Modelos/tablas:** escritura `commerce_compra`, `pagos_ordenpago`, `pases_beneficiarios`, `acreditaciones_evento`.
- **Efectos:** revocación permanente de los derechos y recálculo de accesos.
- **Invariantes:** **no es un reembolso monetario**: cancela la compra y revoca lo entregado; los slots de los pases revocados se consumen para siempre.
- **Respuesta:** `data = { compra_id, estado_compra, estado_orden, ya_cancelada, beneficiarios_revocados, personas_afectadas, motivo }`; mensaje «La compra de pases fue cancelada correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPRA_NOT_FOUND`; 422 por motivo vacío.
- **Estado:** registrada · **consumida**.

---

## 14. Dominio 11 — Competencias (33 rutas)

Contexto común:
- **Permiso único** de todo el dominio: `RequireCompetenciasEscribir` (`admin.competencias.escribir`). Cubre **lectura y escritura**: las lecturas administrativas de competencias exigen la misma capacidad de escritura, porque hoy la sostienen el mismo nivel (staff + ruptura). El nombre de la capacidad es de escritura, pero gobierna toda la superficie administrativa del cuadro.
- **Lock optimista**: casi todas las mutaciones exigen `expected_version` (`Field(ge=1)`). Una versión obsoleta falla con 409 `RESOURCE_CHANGED` y **no se escribe nada**.
- **Motivo auditado**: las mutaciones sensibles exigen `motivo`; sin él, 422 `REASON_REQUIRED`.
- **Tablas**: `competencias`, `rondas`, `encuentros`, `competencia_equipos` (+ sus tablas de historia `competencias_historical*` vía `simple_history`).
- **Consumers**: el módulo `features/admin/competencias/` (servicios → hooks → componentes → páginas `app/(app)/administracion/competencias/**`).

### 14.1 `GET /api/administracion/competencias`

- **Propósito:** listar las **competencias** del ámbito administrativo con sus contadores (equipos, encuentros, encuentros finalizados).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `features/admin/competencias/services/competencias.service.ts` (`getCompetencias`) → `features/admin/competencias/hooks/useCompetencias.ts` → `components/CompetenciasLista.tsx` → `app/(app)/administracion/competencias/page.tsx`.
- **Entrada (query):** `evento_id?`, `disciplina_id?`, `categoria_id?`, `estado?`, `fecha_desde?`, `fecha_hasta?` (fechas ISO).
- **Validación:** los filtros se combinan con AND; los contadores se calculan en el servidor.
- **Controller:** `backend/modules/competencias/presentation/controllers/admin_competencias_controller.py` → `AdminCompetenciasController.listar_competencias`.
- **Cadena:** Controller → `CompetenciaLecturaOrchestrator.listar_competencias` → `CompetenciaSelector` + `AlcanceSelector` → ORM `competencias`, `competencia_equipos`, `encuentros` → `CompetenciasPresenter.present_listado` → `ApiResponse[list[CompetenciaListOut]]`.
- **Modelos/tablas:** lectura `competencias`, `competencia_equipos`, `encuentros`.
- **Efectos:** ninguno.
- **Invariantes:** el ámbito de eventos lo resuelve el servidor (`_eventos_permitidos`).
- **Respuesta:** `data = [{ id, evento_id, disciplina_id, categoria_id, nombre, fecha, estado, version, total_equipos, total_encuentros, total_encuentros_finalizados }]`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 422 por query inválida; 401 sin sesión.
- **Estado:** registrada · **consumida**.

### 14.2 `POST /api/administracion/competencias`

- **Propósito:** **crear una competencia** (evento + disciplina + categoría + nombre + fecha).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`; el actor se toma de `request.auth` para la auditoría.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Entrada (body `CompetenciaCreateIn`):** `evento_id: UUID`, `disciplina_id: UUID`, `categoria_id: UUID`, `nombre: str` (1–150), `fecha: date`.
- **Validación:** la identidad (evento + disciplina + categoría + nombre) es **única** ⇒ duplicado 409 `COMPETENCIA_DUPLICADA`; la fecha debe caer **dentro del evento** ⇒ 422 `INVALID_SCHEDULE`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.crear_competencia`.
- **Cadena:** Controller → `CompetenciaOrchestrator.crear_competencia_proceso` → `CompetenciaFlujo.crear` (transaction.atomic) → `CompetenciaService` → ORM `competencias` → `CompetenciasPresenter.present_competencia` → `ApiResponse[CompetenciaListOut]` (**201**).
- **Modelos/tablas:** escritura `competencias`.
- **Efectos:** auditoría del actor en la fila histórica.
- **Invariantes:** el nombre y la fecha los elige el administrador; la unicidad la impone el dominio, no el cliente.
- **Respuesta:** `data = CompetenciaListOut`; mensaje «La competencia se registró correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 409 `COMPETENCIA_DUPLICADA`; 422 `INVALID_SCHEDULE`; 401 sin sesión.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.3 `GET /api/administracion/competencias/agenda`

- **Propósito:** **agenda de un día**: los encuentros cuya programación empieza ese día (hoy si el cliente no lo dice).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.service.ts` (`getAgendaCompetencias`) → `useCompetencias` → `components/CompetenciasAgenda.tsx` → `app/(app)/administracion/competencias/agenda/page.tsx`.
- **Entrada (query):** `fecha?` (día), `evento_id?`, `disciplina_id?`, `categoria_id?`, `estado?`.
- **Validación:** un día sin encuentros es una **agenda vacía**, nunca un error.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.obtener_agenda`.
- **Cadena:** Controller → `CompetenciaLecturaOrchestrator.obtener_agenda` → `EncuentroSelector` → ORM `encuentros`, `rondas`, `competencias` → `CompetenciasPresenter.present_agenda` → `ApiResponse[AgendaOut]`.
- **Modelos/tablas:** lectura `encuentros`, `rondas`, `competencias`.
- **Efectos:** ninguno.
- **Invariantes:** la agenda es **temporal**: sólo encuentros con programación en ese día; un cuadro parcial sigue siendo una agenda legible.
- **Respuesta:** `data = { fecha, total, encuentros: [EncuentroOut] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 422 por query inválida.
- **Estado:** registrada · **consumida**.

### 14.4 `GET /api/administracion/competencias/{competencia_id}`

- **Propósito:** **detalle** de una competencia con sus equipos y sus rondas.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.service.ts` (`getCompetenciaDetalle`) → `useCompetencias` → `components/CompetenciasDetalle.tsx` → `app/(app)/administracion/competencias/[id]/page.tsx`.
- **Entrada:** path `competencia_id`.
- **Validación:** id desconocido ⇒ 404 `COMPETENCIA_NOT_FOUND`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.obtener_competencia`.
- **Cadena:** Controller → `CompetenciaLecturaOrchestrator.obtener_competencia` → `CompetenciaSelector` → ORM `competencias`, `competencia_equipos`, `rondas` → `CompetenciasPresenter.present_detalle` → `ApiResponse[CompetenciaDetalleOut]`.
- **Modelos/tablas:** lectura `competencias`, `competencia_equipos`, `rondas`.
- **Efectos:** ninguno.
- **Invariantes:** nada se inventa: sólo lo que existe.
- **Respuesta:** `data = { …campos de la lista, created_at, equipos: [CompetenciaEquipoOut], rondas: [RondaOut] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`.
- **Estado:** registrada · **consumida**.

### 14.5 `PATCH /api/administracion/competencias/{competencia_id}`

- **Propósito:** **actualizar** nombre o fecha de una competencia (edición optimista).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Entrada:** path `competencia_id`; body `CompetenciaUpdateIn` = `{ nombre? (1–150), fecha?, expected_version: int (≥1) }`.
- **Validación:** `expected_version` obligatorio; versión obsoleta ⇒ 409 `RESOURCE_CHANGED` sin escribir nada; la fecha debe seguir dentro del evento ⇒ 422 `INVALID_SCHEDULE`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.actualizar_competencia`.
- **Cadena:** Controller → `CompetenciaOrchestrator.actualizar_competencia_proceso` → `CompetenciaFlujo.actualizar` (transaction.atomic, lock por versión) → ORM `competencias` → `CompetenciasPresenter.present_competencia` → `ApiResponse[CompetenciaListOut]`.
- **Modelos/tablas:** escritura `competencias`.
- **Efectos:** auditoría.
- **Invariantes:** control de concurrencia por versión; la edición no pisa cambios ajenos.
- **Respuesta:** `data = CompetenciaListOut`; mensaje «La competencia se actualizó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`; 409 `RESOURCE_CHANGED`; 422 `INVALID_SCHEDULE`.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.6 `PATCH /api/administracion/competencias/{competencia_id}/estado`

- **Propósito:** **mover la competencia** por su ciclo de vida.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Estado:** registrada - **superficie sin consumidor**.
- **Validación:** transición ilegal ⇒ 409 `INVALID_STATE_TRANSITION`; versión obsoleta ⇒ 409 `RESOURCE_CHANGED`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.cambiar_estado_competencia`.
- **Cadena:** Controller → `CompetenciaOrchestrator.cambiar_estado_competencia_proceso` → `CompetenciaFlujo.cambiar_estado` → ORM `competencias` → `CompetenciasPresenter.present_competencia` → `ApiResponse[CompetenciaListOut]`.
- **Modelos/tablas:** escritura `competencias`.
- **Efectos:** auditoría con motivo.
- **Invariantes:** la máquina de estados del dominio es la autoridad; no hay saltos libres.
- **Respuesta:** `data = CompetenciaListOut`; mensaje «El estado de la competencia se actualizó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`; 409 `INVALID_STATE_TRANSITION`, `RESOURCE_CHANGED`.
- **Estado:** registrada · **consumida**.

### 14.7 `DELETE /api/administracion/competencias/{competencia_id}`

- **Propósito:** **eliminar** una competencia nunca usada (borrador).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Entrada:** path `competencia_id`.
- **Validación:** sólo una competencia **planificada, sin equipos, sin rondas y sin historia** posterior a su creación puede borrarse; cualquier otro caso se **cancela** conservando su historia ⇒ 409 `DELETE_NOT_ALLOWED`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.eliminar_competencia`.
- **Cadena:** Controller → `CompetenciaOrchestrator.eliminar_competencia_proceso` → `CompetenciaFlujo.eliminar` → ORM `competencias` (+ `simple_history`) → `None`.
- **Modelos/tablas:** escritura `competencias`, `competencias_historicalcompetencia`.
- **Efectos:** ninguno.
- **Invariantes:** la historia nunca se borra cuando el recurso ya se usó.
- **Respuesta:** **204 No Content**, cuerpo vacío.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`; 409 `DELETE_NOT_ALLOWED`.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.8 `GET /api/administracion/competencias/{competencia_id}/cuadro`

- **Propósito:** **cuadro (bracket)** de una competencia: rondas con sus encuentros.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.service.ts` (`getCompetenciaCuadro`) → `useCompetencias` → `components/CompetenciasCuadro.tsx` → `app/(app)/administracion/competencias/cuadro/page.tsx`.
- **Entrada:** path `competencia_id`.
- **Validación:** un cuadro **vacío o parcial** es una respuesta válida: se devuelven las rondas y encuentros que existen y **no se inventa nada**.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.obtener_cuadro`.
- **Cadena:** Controller → `CompetenciaLecturaOrchestrator.obtener_cuadro` → `RondaSelector` + `EncuentroSelector` → ORM `rondas`, `encuentros` → `CompetenciasPresenter.present_cuadro` → `ApiResponse[CuadroOut]`.
- **Modelos/tablas:** lectura `rondas`, `encuentros`.
- **Efectos:** ninguno.
- **Invariantes:** nada se completa automáticamente (ni participantes, ni resultados, ni horarios).
- **Respuesta:** `data = { competencia_id, nombre, fecha, estado, total_equipos, rondas: [{ id, etiqueta, orden, estado, encuentros: [EncuentroOut] }] }`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`.
- **Estado:** registrada · **consumida**.

### 14.9 `GET /api/administracion/competencias/{competencia_id}/equipos`

- **Propósito:** **equipos inscritos** en el cuadro, con su **orden manual**.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Entrada:** path `competencia_id`.
- **Validación:** el orden es **manual** (del administrador), nunca una semilla automática.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.listar_equipos`.
- **Cadena:** Controller → `CompetenciaLecturaOrchestrator.listar_equipos` → `CompetenciaSelector` → ORM `competencia_equipos`, `equipos` → `CompetenciasPresenter.present_equipos` → `ApiResponse[list[CompetenciaEquipoOut]]`.
- **Modelos/tablas:** lectura `competencia_equipos`, `equipos`.
- **Efectos:** ninguno.
- **Invariantes:** el orden lo fija el humano.
- **Respuesta:** `data = [{ id, competencia_id, equipo_id, equipo_nombre, orden, estado, version }]`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.10 `POST /api/administracion/competencias/{competencia_id}/equipos`

- **Propósito:** **inscribir un equipo** en el cuadro con su orden manual.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEquipoEditor.tsx`.
- **Entrada:** path `competencia_id`; body `CompetenciaEquipoCreateIn` = `{ equipo_id: UUID, orden: int (≥1) }`.
- **Validación:** el equipo debe estar **activo** y compartir **evento, disciplina y categoría** con la competencia ⇒ si no, 409 `EQUIPO_NO_ELEGIBLE`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.incorporar_equipo`.
- **Cadena:** Controller → `CompetenciaEquipoOrchestrator.incorporar_equipo_proceso` → `CompetenciaEquipoFlujo.incorporar` → ORM `competencia_equipos` → `CompetenciasPresenter.present_equipos` → `ApiResponse[CompetenciaEquipoOut]` (**201**).
- **Modelos/tablas:** escritura `competencia_equipos`, `competencias_historicalcompetenciaequipo`.
- **Efectos:** auditoría del actor.
- **Invariantes:** el orden lo elige el administrador, nunca el sistema.
- **Respuesta:** `data = CompetenciaEquipoOut`; mensaje «El equipo se incorporó a la competencia correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND` / `EQUIPO_NOT_FOUND`; 409 `EQUIPO_NO_ELEGIBLE`.
- **Estado:** registrada · **consumida**.

### 14.11 `PATCH /api/administracion/competencias/{competencia_id}/equipos/{competencia_equipo_id}`

- **Propósito:** **actualizar** el orden manual o el estado de la participación de un equipo en el cuadro.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEquipoEditor.tsx`.
- **Entrada:** path `competencia_id`, `competencia_equipo_id`; body `CompetenciaEquipoUpdateIn` = `{ orden? (≥1), estado? (1–20), motivo?, expected_version: int (≥1) }`.
- **Validación:** `expected_version` obligatorio; versión obsoleta ⇒ 409 `RESOURCE_CHANGED`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.actualizar_equipo`.
- **Cadena:** Controller → `CompetenciaEquipoOrchestrator.actualizar_equipo_proceso` → `CompetenciaEquipoFlujo.actualizar` → ORM `competencia_equipos` → `CompetenciasPresenter.present_equipos` → `ApiResponse[CompetenciaEquipoOut]`.
- **Modelos/tablas:** escritura `competencia_equipos`.
- **Efectos:** auditoría.
- **Invariantes:** control de concurrencia por versión.
- **Respuesta:** `data = CompetenciaEquipoOut`; mensaje «La participación del equipo se actualizó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_EQUIPO_NOT_FOUND`; 409 `RESOURCE_CHANGED`.
- **Estado:** registrada · **consumida**.

### 14.12 `GET /api/administracion/competencias/{competencia_id}/rondas`

- **Propósito:** **rondas** del cuadro con su etiqueta, orden, estado y número de encuentros.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Entrada:** path `competencia_id`.
- **Validación:** ninguna adicional.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.listar_rondas`.
- **Cadena:** Controller → `CompetenciaLecturaOrchestrator.listar_rondas` → `RondaSelector` → ORM `rondas` → `CompetenciasPresenter.present_rondas` → `ApiResponse[list[RondaOut]]`.
- **Modelos/tablas:** lectura `rondas`.
- **Efectos:** ninguno.
- **Respuesta:** `data = [{ id, competencia_id, etiqueta, orden, estado, version, total_encuentros }]`.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.13 `POST /api/administracion/competencias/{competencia_id}/rondas`

- **Propósito:** **crear una ronda** del cuadro.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaRondaEditor.tsx`.
- **Entrada:** path `competencia_id`; body `RondaCreateIn` = `{ etiqueta: str (1–100), orden: int (≥1) }`.
- **Validación:** etiqueta y orden son **únicos dentro del cuadro** ⇒ duplicado 409 `COMPETENCIA_DUPLICADA`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.crear_ronda`.
- **Cadena:** Controller → `RondaOrchestrator.crear_ronda_proceso` → `RondaFlujo.crear` → ORM `rondas` → `CompetenciasPresenter.present_rondas` → `ApiResponse[RondaOut]` (**201**).
- **Modelos/tablas:** escritura `rondas`, `competencias_historicalronda`.
- **Efectos:** auditoría.
- **Invariantes:** unicidad de etiqueta y orden dentro de la competencia.
- **Respuesta:** `data = RondaOut`; mensaje «La ronda se registró correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`; 409 `COMPETENCIA_DUPLICADA`.
- **Estado:** registrada · **consumida**.

### 14.14 `PATCH /api/administracion/competencias/{competencia_id}/rondas/{ronda_id}`

- **Propósito:** **actualizar** etiqueta u orden de una ronda.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaRondaEditor.tsx`.
- **Entrada:** path `competencia_id`, `ronda_id`; body `RondaUpdateIn` = `{ etiqueta? (1–100), orden? (≥1), motivo?, expected_version: int (≥1) }`.
- **Validación:** versión obsoleta ⇒ 409 `RESOURCE_CHANGED`; duplicado ⇒ 409 `COMPETENCIA_DUPLICADA`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.actualizar_ronda`.
- **Cadena:** Controller → `RondaOrchestrator.actualizar_ronda_proceso` → `RondaFlujo.actualizar` → ORM `rondas` → `CompetenciasPresenter.present_rondas` → `ApiResponse[RondaOut]`.
- **Modelos/tablas:** escritura `rondas`.
- **Efectos:** auditoría.
- **Respuesta:** `data = RondaOut`; mensaje «La ronda se actualizó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `RONDA_NOT_FOUND`; 409 `RESOURCE_CHANGED`, `COMPETENCIA_DUPLICADA`.
- **Estado:** registrada · **consumida**.

### 14.15 `PATCH /api/administracion/competencias/{competencia_id}/rondas/{ronda_id}/estado`

- **Propósito:** **invalidar** una ronda. Nunca se borra: conserva su historia.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Estado:** registrada - **superficie sin consumidor**.
- **Validación:** `expected_version` obligatorio; versión obsoleta ⇒ 409 `RESOURCE_CHANGED`.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.invalidar_ronda`.
- **Cadena:** Controller → `RondaOrchestrator.invalidar_ronda_proceso` → `RondaFlujo.invalidar` → ORM `rondas` → `CompetenciasPresenter.present_rondas` → `ApiResponse[RondaOut]`.
- **Modelos/tablas:** escritura `rondas`.
- **Efectos:** auditoría.
- **Invariantes:** la invalidación conserva la historia; nunca hay borrado físico.
- **Respuesta:** `data = RondaOut`; mensaje «La ronda se invalidó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `RONDA_NOT_FOUND`; 409 `RESOURCE_CHANGED`, `INVALID_STATE_TRANSITION`.
- **Estado:** registrada · **consumida**.

### 14.16 `GET /api/administracion/competencias/{competencia_id}/encuentros`

- **Propósito:** **encuentros** del cuadro, incluidos los sin programación y los parciales.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Entrada:** path `competencia_id`; query `ronda_id?`, `estado?`, `fecha?`.
- **Validación:** los encuentros incompletos **forman parte** de la respuesta: el cuadro debe permanecer legible.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.listar_encuentros`.
- **Cadena:** Controller → `CompetenciaLecturaOrchestrator.listar_encuentros` → `EncuentroSelector` → ORM `encuentros`, `rondas` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[list[EncuentroOut]]`.
- **Modelos/tablas:** lectura `encuentros`, `rondas`.
- **Efectos:** ninguno.
- **Respuesta:** `data = [EncuentroOut]` (estado del encuentro, participantes con nombre, programación, resultado, enlace al siguiente, versión).
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `COMPETENCIA_NOT_FOUND`.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.17 `POST /api/administracion/competencias/{competencia_id}/encuentros`

- **Propósito:** **crear un encuentro** en una ronda del cuadro.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEncuentroEditor.tsx`.
- **Entrada:** path `competencia_id`; body `EncuentroCreateIn` = `{ ronda_id: UUID, orden: int (≥1), participante_1_id?: UUID, participante_2_id?: UUID }`.
- **Validación:** **ambos participantes son opcionales a propósito**: un cuadro vacío o parcial debe poder editarse sin inventar participantes.
- **Controller:** `admin_competencias_controller.py` → `AdminCompetenciasController.crear_encuentro`.
- **Cadena:** Controller → `EncuentroOrchestrator.crear_encuentro_proceso` → `EncuentroFlujo.crear` → ORM `encuentros` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[EncuentroOut]` (**201**).
- **Modelos/tablas:** escritura `encuentros`, `competencias_historicalencuentro`.
- **Efectos:** auditoría del actor.
- **Invariantes:** el sistema nunca completa un cuadro por su cuenta.
- **Respuesta:** `data = EncuentroOut`; mensaje «El encuentro se registró correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `RONDA_NOT_FOUND`; 422 por body inválido.
- **Estado:** registrada · **consumida**.

### 14.18 `PATCH /api/administracion/competencias/encuentros/{encuentro_id}/participantes`

- **Propósito:** **mover los equipos** de los dos slots de un encuentro.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEncuentroEditor.tsx`.
- **Entrada:** path `encuentro_id`; body `EncuentroParticipantesIn` = `{ participante_1_id?: UUID, participante_2_id?: UUID, motivo?, expected_version: int (≥1) }`.
- **Validación:** mover un slot **siempre** exige motivo auditado (sin él, 422 `REASON_REQUIRED`); un comando repetido con la misma intención **no escribe nada** (idempotente); versión obsoleta ⇒ 409 `RESOURCE_CHANGED`.
- **Controller:** `backend/modules/competencias/presentation/controllers/admin_encuentros_controller.py` → `AdminEncuentrosController.asignar_participantes`.
- **Cadena:** Controller → `EncuentroOrchestrator.asignar_participantes_proceso` → `EncuentroFlujo.asignar_participantes` (transaction.atomic) → ORM `encuentros` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[EncuentroOut]`.
- **Modelos/tablas:** escritura `encuentros`.
- **Efectos:** auditoría con motivo.
- **Invariantes:** idempotencia de la orden repetida; el motivo es parte del contrato, no un adorno.
- **Respuesta:** `data = EncuentroOut`; mensaje «Los participantes del encuentro se actualizaron correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `RESOURCE_CHANGED`, `INVALID_STATE_TRANSITION`; 422 `REASON_REQUIRED`.
- **Estado:** registrada · **consumida**.

### 14.19 `PATCH /api/administracion/competencias/encuentros/{encuentro_id}/programacion`

- **Propósito:** **programar** un encuentro (inicio y fin).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaProgramacionEditor.tsx`.
- **Entrada:** path `encuentro_id`; body `EncuentroProgramacionIn` = `{ inicio_programado: datetime, fin_programado: datetime, motivo?, expected_version: int (≥1) }`.
- **Validación:** la programación debe ser un **intervalo positivo del día de la competencia** ⇒ 422 `INVALID_SCHEDULE`; un equipo **no puede disputar dos encuentros a la vez** ⇒ 409 `EQUIPO_SOLAPADO` (la comprobación es **portable**: abarca todas las competencias del evento); versión obsoleta ⇒ 409 `RESOURCE_CHANGED`.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.programar_encuentro`.
- **Cadena:** Controller → `EncuentroOrchestrator.programar_encuentro_proceso` → `EncuentroFlujo.programar` → `ProgramacionService` → ORM `encuentros`, `rondas`, `competencias` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[EncuentroOut]`.
- **Modelos/tablas:** escritura `encuentros`; lectura `rondas`, `competencias`.
- **Efectos:** auditoría con motivo.
- **Invariantes:** no hay solapamiento de equipos; la comprobación cruza las competitions del evento.
- **Respuesta:** `data = EncuentroOut`; mensaje «El encuentro se programó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `EQUIPO_SOLAPADO`, `RESOURCE_CHANGED`; 422 `INVALID_SCHEDULE`.
- **Estado:** registrada · **consumida**.

### 14.20 `PATCH /api/administracion/competencias/encuentros/{encuentro_id}/estado`

- **Propósito:** **mover el encuentro** por su ciclo de vida.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Estado:** registrada - **superficie sin consumidor**.
- **Validación:** transición ilegal ⇒ 409 `INVALID_STATE_TRANSITION`; versión obsoleta ⇒ 409 `RESOURCE_CHANGED`.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.cambiar_estado_encuentro`.
- **Cadena:** Controller → `EncuentroOrchestrator.cambiar_estado_encuentro_proceso` → `EncuentroFlujo.cambiar_estado` → ORM `encuentros` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[EncuentroOut]`.
- **Modelos/tablas:** escritura `encuentros`.
- **Efectos:** auditoría.
- **Respuesta:** `data = EncuentroOut`; mensaje «El estado del encuentro se actualizó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `INVALID_STATE_TRANSITION`, `RESOURCE_CHANGED`.
- **Estado:** registrada · **consumida**.

### 14.21 `POST /api/administracion/competencias/encuentros/{encuentro_id}/bye`

- **Propósito:** **configurar un bye manual**: un encuentro con exactamente un participante, sin programación y sin marcador, y de estado final.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaByeEditor.tsx`.
- **Entrada:** path `encuentro_id`; body `EncuentroParticipantesIn` (se reutiliza el esquema: `motivo`, `expected_version`).
- **Validación:** **el sistema nunca elige un bye por sí mismo** (decisión de especificación): lo decide el administrador; `expected_version` obligatorio.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.configurar_bye`.
- **Cadena:** Controller → `EncuentroOrchestrator.configurar_bye_proceso` → `EncuentroFlujo.configurar_bye` → ORM `encuentros` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[EncuentroOut]`.
- **Modelos/tablas:** escritura `encuentros`.
- **Efectos:** auditoría con motivo.
- **Invariantes:** un bye tiene un solo participante, sin horario y sin puntuación, y es definitivo.
- **Respuesta:** `data = EncuentroOut`; mensaje «El bye se configuró correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `RESOURCE_CHANGED`, `INVALID_STATE_TRANSITION`.
- **Estado:** registrada · **consumida**.

### 14.22 `POST /api/administracion/competencias/encuentros/{encuentro_id}/enlace`

- **Propósito:** **enlazar** un encuentro con el siguiente del cuadro (definición manual del avance).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEnlaceEditor.tsx`.
- **Entrada:** path `encuentro_id`; body `EncuentroEnlaceIn` = `{ siguiente_encuentro_id: UUID, slot_destino: str (1–20), motivo?, expected_version: int (≥1) }`.
- **Validación:** el enlace y su slot destino se escriben **juntos**; el enlace **siempre apunta hacia adelante** (a una ronda **posterior** de la misma competencia), por lo que no se puede construir un ciclo ⇒ enlace inválido 422 `INVALID_LINK`.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.enlazar_siguiente`.
- **Cadena:** Controller → `EncuentroOrchestrator.enlazar_siguiente_encuentro_proceso` → `EncuentroFlujo.enlazar_siguiente` (transaction.atomic) → ORM `encuentros` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[EncuentroOut]`.
- **Modelos/tablas:** escritura `encuentros`.
- **Efectos:** auditoría con motivo.
- **Invariantes:** aciclicidad garantizada por el orden de las rondas.
- **Respuesta:** `data = EncuentroOut`; mensaje «El encuentro se enlazó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `RESOURCE_CHANGED`; 422 `INVALID_LINK`.
- **Estado:** registrada · **consumida**.

### 14.23 `POST /api/administracion/competencias/encuentros/{encuentro_id}/desenlace`

- **Propósito:** **eliminar el enlace** de un encuentro (ambos campos viajan juntos).
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/editors/CompetenciaEnlaceEditor.tsx`.
- **Entrada:** path `encuentro_id`; body `EncuentroDesenlaceIn` = `{ motivo?, expected_version: int (≥1) }`.
- **Validación:** una propagación ya aplicada **no puede quedar huérfana**: la corrección es quien reescribe ese estado ⇒ 409 `INVALID_STATE_TRANSITION`.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.desenlazar_siguiente`.
- **Cadena:** Controller → `EncuentroOrchestrator.desenlazar_siguiente_encuentro_proceso` → `EncuentroFlujo.desenlazar_siguiente` → ORM `encuentros` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[EncuentroOut]`.
- **Modelos/tablas:** escritura `encuentros`.
- **Efectos:** auditoría con motivo.
- **Respuesta:** `data = EncuentroOut`; mensaje «El enlace del encuentro se eliminó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `RESOURCE_CHANGED`, `INVALID_STATE_TRANSITION`.
- **Estado:** registrada · **consumida**.

### 14.24 `POST /api/administracion/competencias/encuentros/{encuentro_id}/resultado`

- **Propósito:** **registrar el resultado autoritativo** de un encuentro: el ganador y, opcionalmente, el marcador informativo.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaResultadoDialog.tsx`.
- **Entrada:** path `encuentro_id`; body `ResultadoEncuentroIn` = `{ ganador_id: UUID, puntaje_1? (≥0), puntaje_2? (≥0), marcador_detalle? (≤500), motivo?, expected_version: int (≥1) }`.
- **Validación:** el ganador es **autoritativo** y **debe ocupar uno de los dos slots** ⇒ si no, 422 `INVALID_WINNER`; los puntajes son opcionales y **puramente informativos**: nunca determinan ni contradicen al ganador; un comando repetido con la misma intención **no escribe nada**.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.registrar_resultado`.
- **Cadena:** Controller → `ResultadoOrchestrator.registrar_resultado_proceso` → `ResultadoFlujo.registrar_resultado` (transaction.atomic) → `ResultadoService` → ORM `encuentros` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[EncuentroOut]`.
- **Modelos/tablas:** escritura `encuentros`.
- **Efectos:** auditoría con motivo; habilita el avance (14.26).
- **Invariantes:** el ganador siempre es uno de los participantes; el marcador no decide.
- **Respuesta:** `data = EncuentroOut`; mensaje «El resultado del encuentro se registró correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `RESOURCE_CHANGED`, `INVALID_STATE_TRANSITION`; 422 `INVALID_WINNER`.
- **Estado:** registrada · **consumida**.

### 14.25 `POST /api/administracion/competencias/encuentros/{encuentro_id}/avance/preview`

- **Propósito:** **previsualizar el avance** del ganador al siguiente encuentro. **Nunca escribe**: es la propuesta que el administrador confirma.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaAvanceDialog.tsx`.
- **Entrada:** path `encuentro_id`. Sin body.
- **Validación:** un destino bloqueado **se informa en la respuesta**; no es un error de la petición.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.previsualizar_avance`.
- **Cadena:** Controller → `AvanceOrchestrator.previsualizar_avance_proceso` → `AvanceFlujo.previsualizar` → `AvanceService` → ORM `encuentros` (sólo lectura) → `CompetenciasPresenter.present_avance_preview` → `ApiResponse[AvancePreviewOut]`.
- **Modelos/tablas:** lectura `encuentros`.
- **Efectos:** **ninguno** (es una previsualización).
- **Invariantes:** no muta nada; informa `ya_propagado`, `bloqueado` y `motivo_bloqueo`.
- **Respuesta:** `data = { encuentro_id, siguiente_encuentro_id, slot_destino, ganador_id, ocupante_actual_id?, ya_propagado, bloqueado, motivo_bloqueo? }`; mensaje «La propuesta de avance se generó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`.
- **Estado:** registrada · **consumida**.

### 14.26 `POST /api/administracion/competencias/encuentros/{encuentro_id}/avance/confirm`

- **Propósito:** **colocar al ganador** en el slot enlazado del siguiente encuentro y registrar la propagación.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaAvanceDialog.tsx`.
- **Entrada:** path `encuentro_id`; body `AvanceConfirmarIn` = `{ motivo?, expected_version: int (≥1) }`.
- **Validación:** el ganador se coloca **una sola vez**; destino bloqueado ⇒ 409 `DESTINO_BLOQUEADO`; slot ocupado ⇒ 409 `SLOT_OCUPADO`; un comando repetido **no escribe nada**; versión obsoleta ⇒ 409 `RESOURCE_CHANGED`.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.confirmar_avance`.
- **Cadena:** Controller → `AvanceOrchestrator.confirmar_avance_proceso` → `AvanceFlujo.confirmar` (transaction.atomic) → ORM `encuentros` → `CompetenciasPresenter.present_avance` → `ApiResponse[AvanceOut]`.
- **Modelos/tablas:** escritura `encuentros`.
- **Efectos:** propaga el ganador y registra la operación.
- **Invariantes:** la propagación es idempotente y nunca duplica al ganador.
- **Respuesta:** `data = { encuentro_origen_id, siguiente_encuentro_id, slot_destino, ganador_id, ya_aplicado, destino: EncuentroOut }`; mensaje «El avance del cuadro se aplicó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `DESTINO_BLOQUEADO`, `SLOT_OCUPADO`, `RESOURCE_CHANGED`.
- **Estado:** registrada · **consumida**.

### 14.27 `POST /api/administracion/competencias/encuentros/{encuentro_id}/correccion/preview`

- **Propósito:** **analizar el impacto** de corregir al ganador de un encuentro, sobre todos sus descendientes.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaCorreccionDialog.tsx`.
- **Entrada:** path `encuentro_id`; body `CorreccionPreviewIn` = `{ ganador_id: UUID }`.
- **Validación:** **nunca escribe**: informa `requiere_override` y el detalle por descendiente (`bloqueado`, `motivo_bloqueo`, `se_reemplaza`, `se_limpia_resultado`).
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.previsualizar_correccion`.
- **Cadena:** Controller → `CorreccionOrchestrator.previsualizar_correccion_proceso` → `CorreccionFlujo.previsualizar` → `CorreccionService` → ORM `encuentros` (sólo lectura) → `CompetenciasPresenter.present_correccion_preview` → `ApiResponse[CorreccionPreviewOut]`.
- **Modelos/tablas:** lectura `encuentros`.
- **Efectos:** **ninguno**.
- **Invariantes:** toda corrección pasa primero por una previsualización; el impacto se calcula antes de tocar nada.
- **Respuesta:** `data = { encuentro_id, ganador_actual_id?, ganador_nuevo_id, requiere_override, descendientes: [{ encuentro_id, slot, estado, ocupante_actual_id?, ganador_propagado_id?, bloqueado, motivo_bloqueo?, se_reemplaza, se_limpia_resultado }] }`; mensaje «El impacto de la corrección se calculó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 422 por body inválido.
- **Estado:** registrada · **consumida**.

### 14.28 `POST /api/administracion/competencias/encuentros/{encuentro_id}/correccion/confirm`

- **Propósito:** **corregir el ganador autoritativo** de un encuentro.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** `competencias.comandos.service.ts` → `useCompetenciasComandos` → `components/dialogs/CompetenciaCorreccionDialog.tsx`.
- **Entrada:** path `encuentro_id`; body `CorreccionConfirmarIn` = `{ ganador_id: UUID, motivo?, override: bool = false, acepta_impacto: bool = false, expected_version: int (≥1) }`.
- **Validación:** si un descendiente del enlace ya **empezó, terminó o fue cancelado**, la corrección **no cambia nada** salvo que el administrador envíe `override = true` **y** `acepta_impacto = true` **y** un motivo: **nunca hay cascada silenciosa** ⇒ 409 `DESTINO_BLOQUEADO`; versión obsoleta ⇒ 409 `RESOURCE_CHANGED`.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.corregir_ganador`.
- **Cadena:** Controller → `CorreccionOrchestrator.corregir_ganador_proceso` → `CorreccionFlujo.corregir` (transaction.atomic) → `CorreccionService` → ORM `encuentros` → `CompetenciasPresenter.present_correccion` → `ApiResponse[CorreccionOut]`.
- **Modelos/tablas:** escritura `encuentros`.
- **Efectos:** reescribe el resultado y, si se acepta el impacto, los descendientes afectados.
- **Invariantes:** la corrección exige consentimiento explícito del impacto; la traza de auditoría es obligatoria para una cascada.
- **Respuesta:** `data = { encuentro_id, ganador_id, requirio_override, descendientes_afectados, encuentro: EncuentroOut, descendientes: [...] }`; mensaje «La corrección del ganador se aplicó correctamente.»
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `DESTINO_BLOQUEADO`, `RESOURCE_CHANGED`, `INVALID_STATE_TRANSITION`; 422 `INVALID_WINNER`.
- **Estado:** registrada · **consumida**.

### 14.29 `DELETE /api/administracion/competencias/encuentros/{encuentro_id}`

- **Propósito:** **eliminar un borrador** de encuentro nunca usado.
- **Llamador / rol / permiso:** requiere sesión (`JWTAuth`) + `admin.competencias.escribir`.
- **Consumidor:** **sin consumidor conocido**. `frontend/src` **no contiene ninguna función de transporte** para esta operación: `competencias.comandos.service.ts` expone equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, y `competencias.service.ts` expone lista, detalle, agenda y cuadro; ninguna cubre esta ruta.
- **Entrada:** path `encuentro_id`.
- **Validación:** sólo un borrador **sin participantes, sin programación, sin enlaces o dependencias y sin historia** posterior a su creación puede borrarse; cualquier otro caso se cancela conservando su historia ⇒ 409 `DELETE_NOT_ALLOWED`.
- **Controller:** `admin_encuentros_controller.py` → `AdminEncuentrosController.eliminar_encuentro`.
- **Cadena:** Controller → `EncuentroOrchestrator.eliminar_encuentro_proceso` → `EncuentroFlujo.eliminar` → ORM `encuentros` (+ historia) → `None`.
- **Modelos/tablas:** escritura `encuentros`, `competencias_historicalencuentro`.
- **Efectos:** ninguno.
- **Invariantes:** la historia nunca se borra cuando el recurso ya se usó.
- **Respuesta:** **204 No Content**, cuerpo vacío.
- **Errores:** 403 `ACTION_NOT_ALLOWED`; 404 `ENCUENTRO_NOT_FOUND`; 409 `DELETE_NOT_ALLOWED`.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.30 `GET /api/competencias` (público)

- **Propósito:** **catálogo público** de las competencias del ámbito autorizado por el lector.
- **Llamador / rol / permiso:** **público** (`auth=None`, `AllowAny`).
- **Consumidor:** **sin consumidor conocido**. La superficie pública de competencias no tiene vista en el frontend: no existe página pública que muestre el cuadro (la portada consume el catálogo de disciplinas y categorías).
- **Entrada (query):** `disciplina_id?`, `categoria_id?`, `estado?`, `fecha_desde?`, `fecha_hasta?`.
- **Validación:** el **ámbito se resuelve en el servidor** (`CompetenciaPublicaLecturaOrchestrator._eventos_permitidos` → ediciones activas): el cliente nunca elige el ámbito, sólo pide una competencia.
- **Controller:** `backend/modules/competencias/presentation/controllers/public_competencias_controller.py` → `PublicCompetenciasController.listar_competencias`.
- **Cadena:** Controller → `CompetenciaPublicaLecturaOrchestrator.listar_competencias` → `CompetenciaSelector` + `AlcanceSelector` → ORM `competencias`, `competencia_equipos`, `encuentros` → `CompetenciasPresenter.present_listado` → `ApiResponse[list[CompetenciaListOut]]`.
- **Modelos/tablas:** lectura `competencias`, `competencia_equipos`, `encuentros`.
- **Efectos:** ninguno.
- **Invariantes:** un cuadro vacío o parcial es una respuesta válida; no se completa ningún participante ni resultado automáticamente.
- **Respuesta:** `data = [CompetenciaListOut]`.
- **Errores:** 422 por query inválida; 500 en fallo inesperado.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.31 `GET /api/competencias/encuentros` (público)

- **Propósito:** **encuentros públicos** del ámbito autorizado, incluidos los sin programación y los parciales.
- **Llamador / rol / permiso:** **público** (`auth=None`).
- **Consumidor:** **sin consumidor conocido**. La superficie pública de competencias no tiene vista en el frontend: no existe página pública que muestre los encuentros.
- **Entrada (query):** `competencia_id?`, `ronda_id?`, `disciplina_id?`, `categoria_id?`, `estado?`, `fecha?`.
- **Validación:** el ámbito lo resuelve el servidor; los encuentros incompletos forman parte de la respuesta.
- **Controller:** `public_competencias_controller.py` → `PublicCompetenciasController.listar_encuentros`.
- **Cadena:** Controller → `CompetenciaPublicaLecturaOrchestrator.listar_encuentros` → `EncuentroSelector` → ORM `encuentros`, `rondas` → `CompetenciasPresenter.present_encuentros` → `ApiResponse[list[EncuentroOut]]`.
- **Modelos/tablas:** lectura `encuentros`, `rondas`.
- **Efectos:** ninguno.
- **Respuesta:** `data = [EncuentroOut]`.
- **Errores:** 422 por query inválida.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.32 `GET /api/competencias/{competencia_id}` (público)

- **Propósito:** **detalle público** de una competencia del ámbito autorizado.
- **Llamador / rol / permiso:** **público** (`auth=None`).
- **Consumidor:** **sin consumidor conocido**. La superficie pública de competencias no tiene vista en el frontend: no existe página pública que muestre el detalle de una competencia.
- **Entrada:** path `competencia_id`.
- **Validación:** una competencia **fuera del ámbito autorizado** se responde **exactamente igual que un id desconocido**: 404 `COMPETENCIA_NOT_FOUND`. La superficie nunca confirma la existencia de un recurso que el lector no puede ver.
- **Controller:** `public_competencias_controller.py` → `PublicCompetenciasController.obtener_competencia`.
- **Cadena:** Controller → `CompetenciaPublicaLecturaOrchestrator.obtener_competencia` → `CompetenciaSelector` (con filtro de alcance) → ORM `competencias`, `competencia_equipos`, `rondas` → `CompetenciasPresenter.present_detalle` → `ApiResponse[CompetenciaDetalleOut]`.
- **Modelos/tablas:** lectura `competencias`, `competencia_equipos`, `rondas`.
- **Efectos:** ninguno.
- **Invariantes:** no se filtra la existencia de recursos fuera del ámbito.
- **Respuesta:** `data = CompetenciaDetalleOut`.
- **Errores:** 404 `COMPETENCIA_NOT_FOUND` (id desconocido o fuera de ámbito); 422 por query inválida.
- **Estado:** registrada - **superficie sin consumidor**.

### 14.33 `GET /api/competencias/{competencia_id}/cuadro` (público)

- **Propósito:** **cuadro público** de una competencia del ámbito autorizado.
- **Llamador / rol / permiso:** **público** (`auth=None`).
- **Consumidor:** **sin consumidor conocido**. La superficie pública de competencias no tiene vista en el frontend: no existe página pública que muestre el cuadro.
- **Entrada:** path `competencia_id`.
- **Validación:** un cuadro vacío o parcial es una respuesta válida: se devuelve lo que existe y **no se inventa nada**; fuera de ámbito ⇒ 404 `COMPETENCIA_NOT_FOUND`.
- **Controller:** `public_competencias_controller.py` → `PublicCompetenciasController.obtener_cuadro`.
- **Cadena:** Controller → `CompetenciaPublicaLecturaOrchestrator.obtener_cuadro` → `RondaSelector` + `EncuentroSelector` → ORM `rondas`, `encuentros` → `CompetenciasPresenter.present_cuadro` → `ApiResponse[CuadroOut]`.
- **Modelos/tablas:** lectura `rondas`, `encuentros`.
- **Efectos:** ninguno.
- **Respuesta:** `data = CuadroOut`.
- **Errores:** 404 `COMPETENCIA_NOT_FOUND`; 422 por query inválida.
- **Estado:** registrada - **superficie sin consumidor**.

---

## 15. Índice inverso: consumidor → endpoints

Ordenado por artefacto del frontend. Sólo se listan los consumidores **conectados**; la superficie huérfana se trata en §16.

| Consumidor (archivo) | Endpoints consumidos |
|---|---|
| `features/auth/hooks/useLogin.ts` | `POST /api/auth/login/username`, `POST /api/auth/login/dni`, `POST /api/auth/login/email` |
| `features/auth/services/register.service.ts` | `POST /api/auth/register` |
| `features/auth/utils/resolver-destino.ts` | `GET /api/auth/me` |
| `features/admin/services/admin.me.service.ts` | `GET /api/auth/me` |
| `features/admin/services/admin.session.server.ts` (guard servidor) | `GET /api/auth/me` |
| `features/admin/services/admin.resumen.service.ts` | `GET /api/administracion/resumen`, `GET /api/administracion/catalogos` |
| `features/admin/services/admin.inscripcion.service.ts` | `GET /api/administracion/inscripciones`, `GET /api/administracion/inscripciones/{inscripcion_id}` |
| `features/admin/services/admin.pago.service.ts` | `GET /api/administracion/pagos`, `GET /api/administracion/pagos/{orden_pago_id}`, `POST /api/administracion/pagos/{orden_pago_id}/aprobar-manual`, `POST /api/administracion/pagos/{orden_pago_id}/anular-manual` |
| `features/admin/services/admin.operacion.service.ts` | `GET /api/administracion/equipos`, `GET /api/administracion/participantes`, `GET /api/administracion/participaciones`, `GET /api/administracion/acreditaciones`, `GET /api/administracion/acreditaciones/{acreditacion_id}`, `GET /api/administracion/accesos` |
| `features/admin/services/admin.usuario.service.ts` | `GET /api/administracion/usuarios`, `GET /api/administracion/usuarios/{usuario_id}` |
| `features/admin/pases/services/admin.pase.service.ts` | `POST /api/administracion/pases/compras/{compra_id}/cancelar` |
| `features/admin/competencias/services/competencias.service.ts` | `GET /api/administracion/competencias`, `GET /api/administracion/competencias/agenda`, `GET /api/administracion/competencias/{competencia_id}`, `GET /api/administracion/competencias/{competencia_id}/cuadro` |
| `features/admin/competencias/services/competencias.comandos.service.ts` | `POST|PATCH /api/administracion/competencias/{id}/equipos[/{ceid}]`, `POST|PATCH /api/administracion/competencias/{id}/rondas[/{rid}]`, `POST /api/administracion/competencias/{id}/encuentros`, y 10 de los 12 comandos de `/administracion/competencias/encuentros/{id}/…` (participantes, programacion, bye, enlace, desenlace, resultado, avance/preview, avance/confirm, correccion/preview, correccion/confirm). **No cubre** el CRUD de la competencia, el cambio de estado de ronda ni el de encuentro, ni el borrado de encuentro |
| `features/inscripciones/services/inscripcion.service.ts` | `POST /api/inscripciones/`, `POST /api/inscripciones/completa/`, `GET /api/inscripciones/`, `GET /api/inscripciones/{id}/detalle`, `PATCH /api/participaciones/{id}`, `PATCH /api/participaciones/{id}/retirar`, `GET /api/personas/busqueda/{documento}` |
| `features/inscripciones/services/catalog.service.ts` | `GET /api/catalogo/paquetes/`, `GET /api/catalogo/paquetes/{id}/`, `GET /api/catalogo/disciplinas/`, `GET /api/catalogo/categorias/`, `GET /api/catalogo/promociones/` |
| `features/inscripciones/services/paquete.service.ts` | `GET /api/catalogo/paquetes/`, `GET /api/catalogo/paquetes/{id}/` |
| `features/inscripciones/services/cotizacion.service.ts` | `POST /api/cotizaciones/` |
| `features/inscripciones/services/elegibles.service.ts` | `GET /api/inscripciones/{id}/equipos/{equipo_id}/elegibles` |
| `features/inscripciones/services/pool.service.ts` | `GET /api/inscripciones/{id}/pool`, `POST /api/inscripciones/{id}/pool/asignar`, `GET /api/inscripciones/{id}/saldo`, `POST /api/inscripciones/{id}/personas` |
| `features/pagos/services/pago.service.ts` | `POST /api/compras/{compra_id}/iniciar-pago`, `POST /api/pagos/izipay/confirmar`, `GET /api/pagos/transacciones/{transaction_id}` |
| `features/pases/services/pase.service.ts` | `GET /api/pases/`, `POST /api/pases/comprar`, `GET /api/pases/compras/{compra_id}` |
| `features/pases/services/pase.beneficiario.service.ts` | `GET /api/pases/compras/{compra_id}/beneficiarios`, `POST /api/pases/compras/{compra_id}/beneficiarios`, `DELETE /api/pases/compras/{compra_id}/beneficiarios/{persona_id}` |
| `features/pases/services/persona.resolucion.service.ts` | `GET /api/personas/resolver` |
| `features/landing/paquetes.service.ts` | `GET /api/catalogo/paquetes/` |
| `features/portada/hooks/useCatalogo.ts` | `GET /api/catalogo/disciplinas/`, `GET /api/catalogo/categorias/` |
| `app/api/auth/refresh/route.ts` (route handler) | `POST /api/token/refresh` |
| **Proveedor Izipay** (servidor a servidor) | `POST /api/pagos/izipay/notificacion` |

### 15.1 Páginas Next.js → endpoint principal

| Página | Endpoint principal |
|---|---|
| `app/(auth)/login/page.tsx` | `POST /api/auth/login/{username,dni,email}` |
| `app/(auth)/register/page.tsx` | `POST /api/auth/register` |
| `app/(app)/inscripcion/page.tsx` | `POST /api/inscripciones/completa/`, `POST /api/cotizaciones/`, catálogo |
| `app/(app)/dashboard/page.tsx` | `GET /api/inscripciones/` |
| `app/(app)/dashboard/inscripcion/[id]/page.tsx` | `GET /api/inscripciones/{id}/detalle`, pool, saldo, elegibles, asignar |
| `app/(app)/pases/page.tsx` | `GET /api/pases/`, `POST /api/pases/comprar`, beneficiarios |
| `app/(app)/administracion/page.tsx` | `GET /api/administracion/resumen`, `GET /api/administracion/catalogos` |
| `app/(app)/administracion/inscripciones/page.tsx` · `[id]/page.tsx` | `GET /api/administracion/inscripciones[/{id}]` |
| `app/(app)/administracion/pagos/page.tsx` | `GET /api/administracion/pagos[/{id}]`, `aprobar-manual`, `anular-manual`, `pases/compras/{id}/cancelar` |
| `app/(app)/administracion/equipos/page.tsx` | `GET /api/administracion/equipos` |
| `app/(app)/administracion/participantes/page.tsx` | `GET /api/administracion/participantes`, `GET /api/administracion/participaciones` |
| `app/(app)/administracion/acreditaciones/page.tsx` | `GET /api/administracion/acreditaciones[/{id}]`, `GET /api/administracion/accesos` |
| `app/(app)/administracion/usuarios/page.tsx` | `GET /api/administracion/usuarios[/{id}]` |
| `app/(app)/administracion/competencias/page.tsx` · `[id]` · `agenda` · `cuadro` | superficie `/api/administracion/competencias/**` (17 + 12 rutas) |
| `app/page.tsx`, `app/informacion/page.tsx` (portada pública) | `GET /api/catalogo/{disciplinas,categorias}/` (el resto es contenido editorial estático) |

---

## 16. Superficie sin consumidor en el frontend (43 rutas)

Estas rutas **existen, están registradas y responden** en runtime, pero **ninguna vista de `frontend/src` las invoca**. No es un error por sí mismo: una parte es superficie deliberadamente reservada (operación física, integraciones) y otra parte es deuda de diseño (API duplicada o no migrada).

> **Criterio y recuento.** Aplicando el criterio de § 1.3 (una función de servicio o un hook exportado **sin vista que lo use** no cuenta como consumidor), la superficie sin consumidor es de **43 rutas registradas**, no de 30. El detalle:
>
> | Subconjunto | Rutas | Lectura |
> |---|---|---|
> | Sin ninguna referencia en `frontend/src` | 40 | 30 de la tabla siguiente + 10 rutas de competencias enumeradas al final |
> | Con código de servicio/hook pero sin vista que lo invoque | 2 | `POST /api/inscripciones/`, `GET /api/catalogo/paquetes/{paquete_id}/` |
> | Con consumidor externo (no frontend) | 1 | `POST /api/pagos/izipay/notificacion` ← servidor de Izipay |
> | **Total sin consumidor frontend** | **43** | De las 111 registradas |
>
> Esta tabla y el recuento son los mismos que aplica [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) § 5 y § 6.2.

| Grupo | Rutas | Lectura |
|---|---|---|
| **Token de la librería** (2) | `POST /api/token/pair`, `POST /api/token/verify` | El login propio (`/api/auth/login/*`) suplanta a `pair`. `verify` no se usa: la revalidación se hace con `GET /api/auth/me`. |
| **Superficie escrita y no registrada** (fuera de las 111) | `GET /api/ingenieros/habilitados/{cip}` | **No registrada** (ver §17.1); el lookup de documentos va por RENIEC/SUNAT. No cuenta en el total de 43 porque no forma parte del contrato HTTP vigente. |
| **Compras** (4) | `POST /api/compras/`, `GET /api/compras/{id}`, `GET /api/compras/inscripciones/{id}/compras`, `POST /api/compras/{id}/cancelar` | El alta del usuario va por `/inscripciones/completa/`; el historial de compras llega dentro del detalle de inscripción; la cancelación de pases tiene su ruta administrativa. |
| **Asignaciones** (4) | `POST /api/asignaciones/`, `GET /api/asignaciones/{id}`, `POST /api/asignaciones/liberar`, `GET /api/asignaciones/inscripciones/{id}/asignaciones` | El flujo vigente es el **pool** (`/inscripciones/{id}/personas` + `/pool/asignar`), que produce el mismo efecto con mejor contrato de respuesta. |
| **Equipos** (3) | `POST /api/equipos/`, `GET /api/equipos/{id}`, `GET /api/equipos/inscripcion/{id}` | Los equipos se crean en bloque en `/inscripciones/completa/` y se leen en `/inscripciones/{id}/detalle`. |
| **Participaciones** (4) | `POST /api/participaciones/`, `GET /api/participaciones/{id}`, `GET /api/participaciones/equipo/{id}`, `PATCH /api/participaciones/{id}/mover` | El alta pasa por `/pool/asignar`; el resto se lee en el detalle de inscripción. |
| **Inscripciones** (3) | `GET /api/inscripciones/{id}`, `PATCH /api/inscripciones/{id}`, `PATCH /api/inscripciones/{id}/personas/{persona_id}/retirar` | El frontend usa la variante enriquecida `/detalle` y retira participantes por `/participaciones/{id}/retirar`. |
| **Acreditación y acceso** (4) | `GET /api/acreditaciones/{evento_id}/{persona_id}`, `POST /api/acreditaciones/{evento_id}/{persona_id}/generar-qr`, `PATCH /api/acreditaciones/{evento_id}/{persona_id}/override-fiesta`, `POST /api/acceso/registrar` | Superficie de **operación física** (portería, control de acceso, emisión de credenciales). El frontend actual no la ejercita. |
| **Pagos** (1) | `GET /api/pagos/ordenes/{orden_id}` | El canal de recuperación del checkout es `/pagos/transacciones/{id}`. |
| **Administración** (1) | `GET /api/administracion/health` | Sonda de fundación; no la invoca ninguna vista. |
| **Competencias públicas** (4) | `GET /api/competencias`, `GET /api/competencias/encuentros`, `GET /api/competencias/{id}`, `GET /api/competencias/{id}/cuadro` | Superficie pública **sin ninguna página pública que la consuma**: la portada usa el catálogo de disciplinas/categorías, no el cuadro. |
| **Alta simple de inscripción** (1) | `POST /api/inscripciones/` | El servicio y el hook (`useCreateInscripcion`) existen y están exportados, pero **ninguna vista los usa**: el asistente va por `/inscripciones/completa/`. |
| **Detalle de paquete** (1) | `GET /api/catalogo/paquetes/{paquete_id}/` | El servicio (`getPaqueteDisciplinas`, `fetchPaqueteDetail`) y los hooks (`usePaqueteDisciplinas`, `usePaqueteDetail`) existen, pero **ninguna vista los usa**: el `SmartEquipoField` deriva el paquete del listado canónico. |
| **Ciclo de vida y lecturas de competencia** (10) | `POST /api/administracion/competencias`, `PATCH /api/administracion/competencias/{id}`, `PATCH /api/administracion/competencias/{id}/estado`, `DELETE /api/administracion/competencias/{id}`, `GET /api/administracion/competencias/{id}/equipos`, `GET /api/administracion/competencias/{id}/rondas`, `GET /api/administracion/competencias/{id}/encuentros`, `PATCH /api/administracion/competencias/{id}/rondas/{rid}/estado`, `PATCH /api/administracion/competencias/encuentros/{eid}/estado`, `DELETE /api/administracion/competencias/encuentros/{eid}` | **Sin ninguna función de transporte en el frontend**: `competencias.comandos.service.ts` cubre equipos, rondas, encuentros y 10 de los 12 comandos de encuentro, pero no el CRUD de la competencia, ni el estado de ronda o encuentro, ni el borrado de encuentro; `competencias.service.ts` cubre sólo lista, detalle, agenda y cuadro. |
| **Notificación del proveedor** (1) | `POST /api/pagos/izipay/notificacion` | **Consumidor externo**: el servidor de Izipay, servidor a servidor. No es una ruta huérfana; es una integración. |

### 16.1 Lecturas sobre la superficie huérfana

1. **No son «código muerto» en sentido estricto**: casi todas están registradas, tipadas, con permiso, mensajes y contrato de error. Son **superficie reservada** o **API no migrada al frontend**.
2. **El bloque de equipos/participaciones/asignaciones es API duplicada por diseño evolutivo**: el modelo del *pool* (`inscripciones_personas` + `participaciones`) sustituyó al modelo anterior (`asignaciones` como vía de alta). Mantener ambas es una deuda, no una decisión.
3. **Las 4 rutas públicas de competencias son el hueco más visible**: el sitio público no muestra el cuadro, y la superficie pública ya está implementada y auditada por versión. Es trabajo de frontend pendiente, no de backend.
4. **Las 10 rutas de ciclo de vida de competencia son un hueco de *pantalla*, no de API**: el backend expone el CRUD completo y auditado, pero el frontend no tiene comando para él. Es trabajo de frontend pendiente.
5. **`GET /api/administracion/health`** y **`GET /api/token/verify`** son candidatas naturales a **eliminación** si la política es «lo que no se consume no se mantiene».
6. **`POST /api/token/pair`** duplica el login propio; eliminarlo reduce superficie sin perder función (el frontend ya no lo usa).

---

## 17. Brechas, desviaciones y riesgos detectados

Todo lo que sigue se comprobó en el código de runtime; nada es suposición.

### 17.1 Superficie escrita y NO registrada

`IngenieroHabilitadoController` (`backend/modules/usuarios/presentation/controllers/ingeniero_habilitado_controller.py`) declara `@api_controller("/ingenieros", …)` con `GET /habilitados/{cip}`, pero **no aparece** en `api.register_controllers(...)` de `backend/config/api.py`. Verificado en runtime: los 29 routers registrados **no** lo incluyen. La ruta `GET /api/ingenieros/habilitados/{cip}` **no es alcanzable** y no tiene consumidor. Decisión pendiente: registrar o eliminar.

### 17.2 Controllers que saltan la capa de orquestador

`contract/django-app-architecture-contract.md` §4.8 exige que los controllers deleguen en un orquestador. En `modules/salesianos_fest` hay controllers que llaman a selectores o flujos directamente:

| Controller | Acceso directo |
|---|---|
| `catalogo_controller.py` | `sync_to_async(DisciplinaSelector.get_activas)`, `PromocionSelector`, `CategoriaSelector`, `PaqueteSelector` |
| `cotizacion_controller.py` | instancia `CotizacionFlujo()` directamente |
| `compra_controller.py` | instancia `InscripcionSelector()` a mano (líneas ~124 y ~201) |
| `asignacion_controller.py` | `AsignacionSelector` inyectado y usado con `sync_to_async` |
| `acreditacion_controller.py` | `AcreditacionSelector` con `sync_to_async` |
| `inscripcion_controller.py` | `_check_participacion_ownership` consulta `Participacion`/`InscripcionPersona` desde el controller |

Impacto: la lógica de negocio y el acceso a datos quedan en la capa HTTP, lo que rompe el espejo de contrato y dificulta las pruebas unitarias de la capa de presentación.

### 17.3 Respuestas sin tipar (rompen el espejo con el frontend)

Dos rutas declaran `ApiResponse` **sin tipo de payload**:

- `POST /api/inscripciones/{inscripcion_id}/personas`
- `POST /api/inscripciones/{inscripcion_id}/pool/asignar`

Ambas son consumidas por el frontend. El cliente adivina la forma (`{ participante: … }`), lo que contraviene `contract/api-wrapper-presenter-contract.md` §7 (espejo 1:1 backend ↔ frontend sin `any`).

### 17.4 Campos enviados por el frontend que el backend no declara

`PATCH /api/participaciones/{participacion_id}`: `useEditarParticipante` envía `aseguradora_nombre` y `aseguradora_numero_poliza`, pero `ActualizarParticipacionIn` **no** los declara. Con el esquema actual esos campos se descartan silenciosamente.

### 17.5 Doble transporte HTTP en el frontend

Conviven dos clientes con bases de URL distintas:

| Cliente | Base | Resuelve |
|---|---|---|
| `frontend/src/lib/api.ts` (axios) | `backendPublicUrl()` en el navegador, `backendInternalUrl()` en el servidor |.login, registro, administración, inscripciones, pases, pagos |
| `fetch` directo (`features/portada/hooks/useCatalogo.ts`, `features/landing/paquetes.service.ts`) | `NEXT_PUBLIC_API_URL` con un *fallback* propio (`http://backend:8000/api` / `http://localhost:8000/api`) | catálogo de la portada |

El segundo cliente **no** reusa `backend-url.ts` y no aplica el interceptor de token/refresh. Es una divergencia latente: `NEXT_PUBLIC_API_URL` relativo + `fetch` en servidor produce la URL relativa que ya rompió producción antes (documentado en `lib/server/backend-url.ts`).

### 17.6 Códigos de error ausentes del catálogo público

`core/exceptions.py` traduce mediante `PUBLIC_ERROR_MESSAGES`; cuando el código no está en el catálogo, el mensaje público se construye a partir del texto de la excepción. Códigos referenciados en los flujos pero **ausentes** del catálogo: `CONFLICT`, `PERMISSION_DENIED`, `VALIDATION_ERROR`, `NOT_FOUND`, `AUTH_ERROR`, `CIP_NOT_FOUND`, `BUSINESS_ERROR`. Además, el manejador de `ValueError` devuelve `str(exc)` en la respuesta pública, contra `contract/api-wrapper-presenter-contract.md` §8.

### 17.7 `modules.pagos` sin módulo de inyección

`backend/config/settings/base.py` deja **comentado** `modules.pagos.di.PagosModule` en `NINJA_EXTRA["INJECTOR_MODULES"]`, pese a que `modules.pagos` **sí** está en `LOCAL_APPS` y `PagosController` **sí** está registrado. El módulo funciona por auto-construcción implícita de `injector`, no por el cableado declarado.

### 17.8 Prefijos compartidos: el orden de registro es significativo

Seis controladores usan el prefijo `/administracion` y dos usan `/administracion/competencias` (+ `/administracion/competencias/encuentros`). El desempate lo hace el **orden** de `api.register_controllers(...)` en `backend/config/api.py`. Reordenar el registro cambia silenciosamente la resolución de rutas.

### 17.9 Autorización de competencias por capacidad de escritura

Toda la superficie de `/api/administracion/competencias/**` (29 rutas: 17 de `AdminCompetenciasController` + 12 de `AdminEncuentrosController`, incluidas las de **lectura**) exige `admin.competencias.escribir`. Las 4 rutas públicas de `/api/competencias/**` son `auth=None` y no dependen de capacidades. El nombre de la capacidad no refleja lo que protege; hoy funciona porque lectura y escritura las sostiene el mismo nivel.

### 17.10 Cobertura de ownership no auditada ruta por ruta

~20 rutas del área FEST delegan la propiedad en `modules/salesianos_fest/presentation/ownership.py` (`check_ownership_or_admin`, `…_for_equipo`, `…_for_participacion`, `…_for_asignacion`, `check_acreditacion_access_or_admin`). Esta revisión verificó **qué** helper usa cada ruta (fichas §8–§12), pero **no** re-auditó la corrección interna de cada helper frente al dominio.

### 17.11 Divergencia entre docstring y ejecución en el login

Los docstrings de `AuthLoginController` anuncian «ValueError con código AUTH_ERROR si credenciales inválidas (401)», pero `AuthFlujo` lanza `HttpError(401, "Credenciales inválidas")`, que el manejador global traduce como `code = "HTTP_ERROR"` (no existe entrada `AUTH_ERROR` en el catálogo). El cliente debe distinguir por **status**, no por `error.code`.

---

## 18. Trazabilidad de esta revisión

| Aspecto | Valor |
|---|---|
| Alcance | 111 rutas registradas (runtime) + 1 ruta escrita no registrada |
| Fuentes primarias | `backend/config/api.py`, 23 controllers, orquestadores/flujos/servicios core/selectores/presenters/esquemas, `core/{responses,pagination,exceptions,capacidades,permissions,security}.py`, `backend/config/settings/base.py`, `frontend/src/**` (excluido `_legacy*`), `backend/db.sqlite3` (sólo lectura de `sqlite_master`) |
| Artefactos Engram usados como contexto | `sdd/explore/rebuild-backend-api-map`, `sdd/explore/rebuild-flows-infrastructure-map` (+ apéndice), `sdd/explore/application-rebuild-architecture-documentation` |
| Verificación de cobertura | fichas de §4–§14 = **111**; rutas registradas en runtime = **111**; routers = **29** (28 del proyecto + `NinjaJWTDefaultController`) |
| Modificaciones al código | **ninguna**: sólo se creó este documento |
| Topic key del artefacto | `sdd/explore/backend-endpoint-functional-catalog` |

---

## 19. Documentos relacionados

- [README.md](README.md) — índice navegable del conjunto documental.
- [00-cobertura-y-trazabilidad.md](00-cobertura-y-trazabilidad.md) — metodología de auditoría, recuentos de cobertura y checklist reejecutable.
- [01-arquitectura-y-runtime.md](01-arquitectura-y-runtime.md) — runtime, despliegue y proxy.
- [02-backend-y-api.md](02-backend-y-api.md) — arquitectura del servicio, wrappers y política de errores.
- [02a-inventario-de-endpoints.md](02a-inventario-de-endpoints.md) — inventario método/ruta/auth/permiso/wrapper (base de este documento).
- [03-frontend.md](03-frontend.md) — capa de frontend, sus servicios, hooks y páginas.
- [04-datos-y-dominio.md](04-datos-y-dominio.md) — modelo de datos y agregados.
- [05-flujos-end-to-end.md](05-flujos-end-to-end.md) — recorridos de extremo a extremo.
- [06-operacion-y-deuda-tecnica.md](06-operacion-y-deuda-tecnica.md) — operación y deuda técnica.
- [07-guia-para-ui-ux.md](07-guia-para-ui-ux.md) — guía de UI/UX.

