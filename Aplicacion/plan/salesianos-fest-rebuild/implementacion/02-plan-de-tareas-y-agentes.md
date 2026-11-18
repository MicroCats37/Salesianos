# Implementación 02 — Backlog, etapas y agentes paralelos

**Estado:** **plan de trabajo preliminar** para ejecutar reconstrucción desde cero. No se ha escrito código del producto. **Tareas** = unidades entregables, no órdenes de alterar una arquitectura particular. Identificadores sirven para trazabilidad con [las reglas](../funcional/02-reglas-de-negocio.md), [flujos](../funcional/04-flujos-end-to-end.md) y [mapa de páginas](../frontend/01-mapa-rutas-y-navegacion.md).

## 1. Estrategia y fases

| Fase | Entregable | Dependencia | Paralelo posible |
|---|---|---|---|
| **F0 — Contratos y UX** | Decisiones validadas, mapa de páginas, entidades/contratos comunes, mocks | Ninguna | UX y arquitectura colaboran |
| **F1 — Fundaciones** | Ediciones, identidad, auth/grupos, commerce/pagos, API base, multimedia | F0 | Subfundaciones coordinadas |
| **F2 — Dominios** | Inscripciones, pases, marketplace, patrocinios y competencias | Contratos F1 estables | **Sí, varios agentes** |
| **F3 — Integración** | Checkout E2E, derechos, validaciones, panel admin y datos | F2 suficiente | Sí, con integrador único de interfaces |
| **F4 — Validación final** | Suite de pruebas, E2E, revisión UX, seguridad, datos y regresiones | F3 | QA/UX/seguridad coordinados |

**Regla acordada:** durante cada tarea se **escriben** los tests, pero se **ejecutan** en F4 al integrar y estabilizar el sistema. Realizar análisis estático, revisión de contrato o chequeos de estructura antes de F4 no equivale a ejecutar la suite funcional.

## 2. Agentes sugeridos y propiedad

| Código | Agente | Propiedad principal | Evitar escribir en |
|---|---|---|---|
| A0 | Integrador / arquitectura local | Contratos transversales, API base, cambios compartidos y revisión | Reglas internas de otros dominios sin acuerdo |
| A1 | Identidad y ediciones | Persona/Usuario, Django Groups, RENIEC, edición/flags | Compra específica de otros módulos |
| A2 | Commerce/pagos | Compra, orden, intentos, Izipay, coordinación idempotente | Cupos/pases/inventario directamente |
| A3 | Inscripciones | Paquetes, inscripción, equipos, participantes, cupos | Transacción proveedor y tienda |
| A4 | Pases/beneficios | Pase, CompraPase, PaseBeneficiario, cortesías, acceso efectivo | Pool deportivo/stock tienda |
| A5 | Marketplace | Productos, imágenes, pedido, inventario, entregas | Compra de deportes/pases |
| A6 | Competencias | Competición, rondas, partidos, cuadro, resultados | Cambios al pool o a commerce |
| A7 | Frontend UX | Mapa rutas, diseño, pantallas y servicios según contratos | Reglas de negocio en cliente |
| A8 | Admin/validación/patrocinadores | Panel admin, lectores, patrocinios, auditoría | Mutar servicios ajenos sin contrato |
| A9 | QA/integración final | E2E, pruebas, criterios, regresiones | Confirmar requisitos no aprobados por su cuenta |

No significa necesitar diez agentes simultáneos. Para menor infraestructura, combinar A8/A5 o A1/A0 manteniendo las fronteras. Si se usan agentes distintos en frontend, A7 mantiene propiedad de componentes globales; cada agente de página trabaja sobre carpeta feature y contrato acordado.

## 3. F0 — Definición antes de programar

| ID | Responsable | Tarea / entregable | Depende | Aceptación |
|---|---|---|---|---|
| T-000 | A0 + producto | Validar decisiones 00 y anotar asuntos PD | — | No hay propuestas marcadas por error como aprobadas |
| T-001 | A7 | Aprobar mapa de rutas y navegación por actor | T-000 | Cada ruta responde a tarea y módulo; evitar páginas duplicadas |
| T-002 | A7 | Wireframes mobile/desktop de inscripción, equipos, pagos y encuentros | T-001 | Pueden recorrerse flujos completos y errores sin backend |
| T-003 | A0 | Definir contrato API común: wrapper, errores, paginación, vocabularios, autorización | T-000 | Ejemplos + schemas + reglas de versionado |
| T-004 | A0 + A1 | Congelar identidad, edición, scope de consultas y titularidad | T-000 | Interfaz estable para todos los módulos |
| T-005 | A0 + A2 | Congelar contrato comercio/pagos, reintentos, activación idempotente | T-003 | Dominios consumen interfaz sin modificar proveedor |
| T-006 | A0 + A4 + A8 | Definir contrato de derecho/canje, sin duplicar pases/cupos | T-004 | Lectura/preview/confirmación de ticket coherentes |
| T-007 | A0 | Definir ejemplos/mocks por caso de uso | T-003,T-005,T-006 | Frontend trabaja contra fixtures verificables |

## 4. F1 — Infraestructura fundacional

| ID | Responsable | Tarea / entregable | Depende | Aceptación |
|---|---|---|---|---|
| T-010 | A1 | Evento/Edicion y alcance entre años | T-004 | Operaciones quedan vinculadas a edición correcta |
| T-011 | A1 | Persona/Usuario y roles Django Normal/Admin | T-004 | Persona sin cuenta válida; administración controlada |
| T-012 | A1 | Resolver local→RENIEC y confirmar persistencia | T-011 | Sin duplicados; fuente externa falla de forma recuperable |
| T-013 | A2 | Compra/orden/intentó pago comunes | T-005 | Historial consistente por compra |
| T-014 | A2 | Izipay, callbacks/firmas, estado real y reintentos | T-013 | Cierre de modal no cancela; webhook repetido idempotente |
| T-015 | A0 | Coordinación activar derechos por dominio, reintento de errores | T-013 | Cobro probado y derecho aplicado exactamente una vez |
| T-016 | A0 | Contrato de `ImageField` + persistencia/validación de media | T-003 | Imágenes servidas y persistentes sin CDN |
| T-017 | A7 | Shell público/admin, cliente API, auth UI, esquema UX y estados | T-001,T-003 | Layout y navegación coherentes en móvil/escritorio |
| T-018 | A0 | Registro de endpoints y autoridad de permisos Django Ninja | T-003,T-011 | Backend responde 401/403 correctamente |

## 5. F2 — Dominios desarrollables en paralelo

| ID | Agente | Tarea / entregable | Depende | Aceptación |
|---|---|---|---|---|
| T-020 | A3 | Catálogo de paquetes, disciplinas, beneficios por edición | T-010,T-003 | Backend devuelve catálogo verdadero y elegibilidad |
| T-021 | A3 | Crear inscripción + equipo + compra inicial | T-020,T-013 | No habilita cupos antes de pago |
| T-022 | A3 | Pool de cupos y asignación/retiro/movimiento | T-021,T-015 | Saldo correcto; concurrencia y duplicidad protegidas |
| T-023 | A3 | Ampliación de cupos y beneficios ligados a cupos | T-022 | Compra nueva en misma inscripción; beneficio fijo no se duplica |
| T-030 | A4 | Catálogo y compra de pase independiente | T-010,T-013 | Invitado puede iniciar compra sin crear Usuario |
| T-031 | A4 | Asignación `PaseBeneficiario`, consulta, auditoría | T-030,T-015 | Solo derechos pagados; reglas pendientes visibles |
| T-032 | A4 | Cortesía gratuita y derecho de acceso efectivo | T-031,T-006 | No genera OrdenPago ficticia; origen trazable |
| T-040 | A5 | Categorías, productos, precios/ofertas, imágenes | T-010,T-016 | Galería múltiple, precio validado servidor |
| T-041 | A5 | Pedido/detalle/compra de tienda | T-040,T-013 | Snapshot de importe; sin mezcla con pases/cupos |
| T-042 | A5 | Movimiento de inventario y salidas sin pago | T-040 | Historial con actor/motivo; stock consistente |
| T-043 | A5 | Venta, reserva anti-sobreventa, estado de entrega | T-041,T-042,T-015 | No doble descuento ni venta sin stock |
| T-050 | A6 | Competencia y elegibilidad de equipos | T-010,T-022 | Equipos solo del torneo/edición correctos |
| T-051 | A6 | Rondas/encuentros/agenda y programación | T-050 | Sin horarios imposibles o duplicados |
| T-052 | A6 | Resultado/ganador, avance y correcciones | T-051 | Preview sin escritura y conflictos controlados |
| T-060 | A8 | Patrocinadores, logo y galerías por edición | T-010,T-016 | CRUD y orden de imágenes |

## 6. F2 — Frontend en paralelo a dominios

| ID | Agente | Tarea / entregable | Depende de contrato | Criterios |
|---|---|---|---|---|
| T-070 | A7 | Portada/información coherentes, sin fallback inventado | T-007,T-017 | CTA a cada función habilitada |
| T-071 | A7 | Login, registro, cuenta, recuperación conceptual | T-011,T-012,T-017 | No crear cuenta para beneficiarios ajenos |
| T-072 | A7 | Wizard inscripción + detalle/pool/plantillas | T-007,T-017 | Estados guiados, compra recuperable |
| T-073 | A7 | Pase público + checkout + enlace invitado | T-007,T-017 | Beneficiarios y estados comprensibles |
| T-074 | A7 | Tienda + ficha/carrusel + pedido | T-007,T-017 | Sin carrito mixto, responsive |
| T-075 | A7 | Admin equipos/participantes e inscripción | T-007,T-017 | Drilldown y razones explícitas |
| T-076 | A7 | Admin pagos con filtro operativo y diagnóstico separado | T-007,T-017 | Pago/compra/entrega se distinguen |
| T-077 | A7 | Admin competencias + agenda/bracket/encuentro | T-007,T-017 | Acciones coherentes desde las 3 vistas |
| T-078 | A7 | Panel tienda, pases, tickets y patrocinadores | T-007,T-017 | CRUD/validación usable en móvil |

**Nota de coordinación:** T-072 a T-078 pueden usar mocks del contrato T-007 antes de disponer de endpoints reales; A7 no debe depender de datos inventados diferentes a los documentados.

## 7. F3 — Integración y validaciones

| ID | Agente | Tarea | Depende | Aceptación |
|---|---|---|---|---|
| T-080 | A8 + A4 | Credencial/ticket y control de ingreso | T-032,T-006 | Preview vs confirmar; no doble ingreso indebido |
| T-081 | A8 + A5 | Ticket y entrega de productos | T-043,T-006 | Consumo atómico y bitácora |
| T-082 | A0 + A7 | Conectar frontends contra contratos reales | T-020..T-078 relevantes | Ninguna ruta sin consumidor funcional ni mock oculto |
| T-083 | A8 | Administración transversal, filtros/detalles y auditoría | T-020..T-081 relevantes | Operaciones reales, no solo listados |
| T-084 | A2 + A0 | Reconciliación y recuperación de pago con derechos | T-014,T-015,T-023,T-031,T-043 | No pagos cobrados «perdidos» ni dobles efectos |
| T-085 | A0 | Configuración media, permisos operativos y despliegue | T-016,T-018 | Persistencia, control backend, trazabilidad |
| T-086 | A0 | Configurar notificaciones cuando se apruebe SMTP | PD-08, T-015 | No acoplar éxito de compra con correo |

## 8. F4 — Ejecutar pruebas y aprobar entrega

| ID | Responsable | Entregable | Depende | Aceptación |
|---|---|---|---|---|
| T-090 | A9 | Ejecutar tests escritos en F1–F3 y corregir regresiones | T-082..T-085 | Casos requeridos pasan o se documentan bloqueos |
| T-091 | A9 + A2 | Prueba Izipay/duplicados/reintentos | T-084 | Efectos idempotentes y confirmación fiable |
| T-092 | A9 + A3/A4/A5 | E2E inscripción, pase invitado, tienda y stock | T-082 | Activa/consume derechos correctos |
| T-093 | A9 + A6/A7 | E2E de equipos/competencias y UX admin | T-082 | Encuentros/resultado/impactos coherentes |
| T-094 | A9 | Accesibilidad, permisos y datos sensibles | T-082,T-085 | Sin rutas admin abiertas ni exposición de tokens |
| T-095 | A0 + producto | Revisión y firma de decisiones abiertas; documentación final | T-090..T-094 | Versión estable de plan, modelos y pantallas |

## 9. Orden de ejecución sugerido para múltiples agentes

**Ronda de acuerdos:** A0, A1, A2, A7 cierran T-000..T-007. **Ronda de construcción paralela:** A3 (inscripción), A4 (pases), A5 (tienda), A6 (competencias), A8 (patrocinios); A7 implementa pantallas según mocks. **Ronda de coordinación:** A0 integra registrar rutas compartidas y cambios cruzados; A8 valida tickets y admin, A2 reconcilia pagos. **Última ronda:** A9 ejecuta y revisa pruebas.

**Importante:** la necesidad de T-050 respecto a T-022 depende de usar el contrato de elegibilidad deportiva; A6 puede construir rondas/bracket de manera autónoma mientras A3 implementa cupos. Similarmente A4 puede implementar catálogo/beneficiarios con stub de pago hasta que A2 estabilice Izipay.

## 10. Gestión de conflictos y bloqueos

- Cada agente entrega: cambios, contratos usados, pruebas escritas, decisiones faltantes, archivos modificados.
- Un cambio a `Persona`, `Compra`, `OrdenPago`, `Edicion`, respuesta base o permisos exige aprobación del integrador A0.
- No usar migraciones paralelas sobre el mismo app/modelo sin coordinación.
- Un pendiente PD bloquea **solo** su subtarea afectada; los demás agentes continúan.
- Si un endpoint no existe, frontend usa mock marcado como mock, nunca falsea «confirmado» o inventa datos comerciales en producción.

## 11. Definición de tarea terminada (sin ejecución anticipada de pruebas)

Criterio: regla de negocio cubierta, contrato y presenter documentados, endpoints/servicios integrados según fase, UI en estados relevantes, pruebas **escritas** y listas para F4, seguridad revisada, decisiones abiertas declaradas, sin modificaciones silenciosas a otros módulos.
