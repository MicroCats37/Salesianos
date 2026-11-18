# Salesianos FEST — Documentación técnica

> **Ámbito:** documentación de referencia del sistema **Salesianos FEST** (backend Django + `django-ninja-extra`, frontend Next.js 16, worker FastAPI, proxy nginx).
> **Estado:** vigente. Describe **el estado actual del código**, no el deseado.
> **Fecha de la última auditoría:** 2026-11-18 sobre el árbol de trabajo local (`backend/`, `frontend/`, `worker/`, `proxy/`, `docker-compose.yml`).
> **Contratos normativos:** [`../../contract/`](../../contract/) — el código describe la realidad, el contrato describe la obligación.

---

## 1. Para qué sirve esta carpeta

Esta carpeta contiene **15 documentos** que, en conjunto, describen cómo está construido, cómo se ejecuta y cómo se comporta hoy el sistema. No es un manual de uso ni un plan de trabajo: es el mapa que permite reconstruir, auditar o modificar el sistema sin adivinar.

El punto de partida es este índice. A partir de aquí, cada documento responde a una pregunta concreta y remite a sus hermanos para el detalle.

### Orden de lectura recomendado

| Si tu pregunta es… | Lee primero | Después |
|---|---|---|
| ¿Cómo funciona el sistema por dentro? | [01 — Arquitectura y runtime](./01-arquitectura-y-runtime.md) | [02 — Backend y API](./02-backend-y-api.md), [03 — Frontend](./03-frontend.md) |
| ¿Qué rutas expone la API? | [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) | [02b — Propósito y consumidores](./02b-proposito-y-consumidores-de-endpoints.md) |
| ¿Qué hace cada endpoint y quién lo llama? | [02b — Propósito y consumidores](./02b-proposito-y-consumidores-de-endpoints.md) | [02a](./02a-inventario-de-endpoints.md), [05a](./05a-matriz-pagina-flujo-endpoint-datos.md) |
| ¿Qué hace esta pantalla? | [03a — Páginas públicas y de compra](./03a-paginas-publicas-y-compra.md) · [03b — Páginas administrativas y operativas](./03b-paginas-administrativas-y-operativas.md) | [03 — Frontend](./03-frontend.md) |
| ¿Cómo se escriben los datos? | [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) | [04 — Datos y dominio](./04-datos-y-dominio.md) |
| ¿Qué tablas existen y quién las puebla? | [04 — Datos y dominio](./04-datos-y-dominio.md) | [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) |
| ¿Cómo se siembran los datos? | [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) | [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) |
| ¿Qué hace el usuario de punta a punta? | [05 — Flujos end-to-end](./05-flujos-end-to-end.md) | [05a](./05a-matriz-pagina-flujo-endpoint-datos.md) |
| ¿Cómo se opera y qué está roto? | [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) | [02 — Backend y API](./02-backend-y-api.md) |
| ¿Qué puedo cambiar en el frontend? | [07 — Guía para el agente de UI/UX](./07-guia-para-ui-ux.md) | [03 — Frontend](./03-frontend.md) |
| ¿Está todo documentado? | [00 — Cobertura y trazabilidad](./00-cobertura-y-trazabilidad.md) | — |

---

## 2. Dónde mirar

| Necesitas… | Documento | Sección de entrada |
|---|---|---|
| La topología de servicios, los puertos y el proxy nginx | [01 — Arquitectura y runtime](./01-arquitectura-y-runtime.md) | §3 Topología general · §4 Tabla de enrutamiento nginx |
| Las reglas de capas del backend (controller → orchestrator → flujo → core → selector → presenter) | [02 — Backend y API](./02-backend-y-api.md) | §4 Arquitectura Django + `django-ninja-extra` |
| El sobre de respuesta, la paginación y el catálogo de errores | [02 — Backend y API](./02-backend-y-api.md) | §5 Contratos de request, response y error |
| Quién puede hacer qué (capacidades y gates) | [02 — Backend y API](./02-backend-y-api.md) | §6 Política de autenticación y autorización |
| El catálogo completo de rutas con su permiso efectivo | [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) | §4 Inventario detallado |
| El propósito de negocio y el consumidor real de una ruta | [02b — Propósito y consumidores](./02b-proposito-y-consumidores-de-endpoints.md) | §4–§14 Fichas por endpoint |
| Las rutas que nadie consume | [02b](./02b-proposito-y-consumidores-de-endpoints.md) · [05a](./05a-matriz-pagina-flujo-endpoint-datos.md) | 02b §16 · 05a §5 |
| La estructura del frontend y el mapa ruta → feature → endpoint | [03 — Frontend](./03-frontend.md) | §2 Árbol real · §3 Mapa ruta → guard → feature → servicio → endpoint |
| La cadena de guardas y la política de sesión | [03 — Frontend](./03-frontend.md) | §4 Cadena de guardas y sesión |
| La ficha de una pantalla pública o de compra | [03a — Páginas públicas y de compra](./03a-paginas-publicas-y-compra.md) | §5 Fichas por página |
| La ficha de una pantalla administrativa u operativa | [03b — Páginas administrativas y operativas](./03b-paginas-administrativas-y-operativas.md) | §4 Catálogo de páginas |
| Quién es dueño de qué tabla | [04 — Datos y dominio](./04-datos-y-dominio.md) | §2 Propiedad por módulo |
| El grafo de migraciones y sus reglas | [04 — Datos y dominio](./04-datos-y-dominio.md) | §4 Migraciones Django |
| Qué comando siembra qué tabla y con qué riesgo | [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) | §4 Matriz seed → tabla |
| En qué orden se ejecutan las semillas | [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) | §3 Orden de ejecución recomendado |
| Un recorrido completo de un usuario | [05 — Flujos end-to-end](./05-flujos-end-to-end.md) | §A–§I Los 27 flujos |
| La trazabilidad pantalla → endpoint → tabla | [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) | §2 Matriz por ruta de frontend |
| Los comandos de gestión y su secuencia | [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) | §4 Trabajos programados y comandos manuales |
| Los hallazgos y la deuda técnica registrados | [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) | §6 Hallazgos (H-1 … H-9) · §7 Deuda técnica (D-1 … D-16) |
| Qué está prohibido cambiar en el frontend | [07 — Guía para el agente de UI/UX](./07-guia-para-ui-ux.md) | §3 Qué puede cambiar la UI |
| La auditoría de cobertura y el checklist | [00 — Cobertura y trazabilidad](./00-cobertura-y-trazabilidad.md) | §5 Checklist reejecutable |

---

## 3. Catálogo de documentos

| # | Documento | Qué cubre | Alcance |
|---|---|---|---|
| — | **[00 — Cobertura y trazabilidad](./00-cobertura-y-trazabilidad.md)** | Metodología de auditoría, recuentos exactos de cobertura, exclusiones y checklist reejecutable. | Todo el sistema |
| 01 | [Arquitectura y runtime](./01-arquitectura-y-runtime.md) | Topología de ejecución, raíces de código, capa de borde, URLs base, cookies, despliegue, variables de entorno. | Todo el sistema |
| 02 | [Backend y API](./02-backend-y-api.md) | Arquitectura del servicio Django/Ninja, capas, DI, contratos de request/response/error, autenticación y autorización. | `backend/` |
| 02a | [Inventario de endpoints](./02a-inventario-de-endpoints.md) | Catálogo de las 111 rutas registradas: método, ruta, `auth`, permiso efectivo, wrapper y estado. | `backend/` |
| 02b | [Propósito y consumidores de endpoints](./02b-proposito-y-consumidores-de-endpoints.md) | Para cada ruta: propósito, consumidor real, cadena de ejecución, tablas, invariantes e implicaciones de error. | `backend/` + `frontend/` |
| 03 | [Frontend](./03-frontend.md) | Árbol real, mapa ruta → guard → feature → servicio → endpoint, guardas, estado, transporte HTTP, calidad y brechas. | `frontend/` |
| 03a | [Páginas públicas y de compra](./03a-paginas-publicas-y-compra.md) | Fichas de las 8 páginas públicas, de cuenta y de compra, y de los 2 route handlers de sesión. | `frontend/` |
| 03b | [Páginas administrativas y operativas](./03b-paginas-administrativas-y-operativas.md) | Fichas de las 16 páginas administrativas y operativas, con su modelo de capacidades. | `frontend/` |
| 04 | [Datos y dominio](./04-datos-y-dominio.md) | Propiedad de tablas, modelos, migraciones y fronteras de integración. | `backend/` |
| 04a | [Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) | Los 15 mecanismos de siembra, carga inicial y bootstrap; matriz seed → tabla; brechas de la documentación operativa. | Todo el repositorio |
| 05 | [Flujos end-to-end](./05-flujos-end-to-end.md) | Los 27 flujos que el navegador ejercita, con transporte, endpoint, modelo y recuperación. | `frontend/` + `backend/` |
| 05a | [Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) | Trazabilidad completa, con diagramas de flujo y los endpoints sin consumidor. | `frontend/` + `backend/` |
| 06 | [Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) | Topología operativa, base de datos, ausencia de planificador, hallazgos H-1 … H-9 y deuda D-1 … D-16. | Todo el sistema |
| 07 | [Guía para el agente de UI/UX](./07-guia-para-ui-ux.md) | Qué puede y qué no puede cambiarse en el frontend, y cómo se entrega un cambio. | `frontend/` |

---

## 4. Recuentos verificados

Cifras comprobadas contra el código el 2026-11-18. El detalle y el método están en [00 — Cobertura y trazabilidad](./00-cobertura-y-trazabilidad.md).

| Ámbito | Recuento |
|---|---|
| Rutas HTTP registradas en el backend | **111** (112 definiciones en código; 1 no registrada) |
| Controladores registrados / escritos | 28 del proyecto + 1 de la librería = **29**; 1 controlador escrito y no registrado |
| Rutas públicas (`auth=None`) | **20** |
| Rutas con consumidor en el frontend | **68** (2 con código de servicio sin vista, 1 con consumidor externo, 40 sin ninguna referencia) |
| Pantallas enrutables del frontend | **20** (+ 2 route handlers) |
| Layouts de sección con guard de administración | **7** |
| Comandos de gestión del proyecto | **13** (11 en `modules/*`, 2 en `core/`) |
| Mecanismos de siembra / bootstrap documentados | **15** |
| Modelos de negocio / tablas de negocio | **31** modelos · **31** tablas de negocio (+ 10 históricas, + 2 de unión) |
| Migraciones Django | **30** archivos (29 aplicadas; `pagos.0006` pendiente) |
| Capacidades de administración | **11** códigos, 3 niveles de actor |
| Flujos de navegador documentados | **27** |
| Hallazgos / deuda técnica registrados | **9** hallazgos (H-1 … H-9) · **16** deudas (D-1 … D-16) |

---

## 5. Política de fuente de verdad

Hay cuatro fuentes con alcances distintos. Confundirlas es la causa más común de documentación incorrecta.

| Fuente | Autoridad sobre | **No** decide |
|---|---|---|
| [`contract/`](../../contract/) (7 documentos normativos) | Cómo **debe** ser el código: estructura de módulos, capas, wrappers, mensajes públicos, permisos, estrategia de pruebas | Qué rutas existen hoy |
| `backend/` y `frontend/` (código) | Qué **existe** hoy: rutas, esquemas, permisos efectivos, comportamiento | Cómo debería ser |
| `frontend/src/features/**/services/*.ts` | Qué forma consume el cliente final: fija el contrato de respuesta en la práctica | Nada del backend |
| `Aplicacion/documentacion/` (esta carpeta) | Explicación navegable del estado actual | Nada. Es **derivada y regenerable** |

Reglas que se aplican en toda la carpeta:

- **El contrato manda sobre el código** cuando discrepan: se documenta el comportamiento real y se marca la desviación; no se documenta como si cumpliera el contrato.
- **El runtime manda sobre la lectura estática** para decidir la existencia de una ruta. Un controlador escrito y no registrado no es una ruta.
- **La documentación es derivada.** Los inventarios no se mantienen a mano: se reconstruyen desde el código. Si cambia `backend/config/api.py` o `frontend/src/app/**`, hay que regenerarlos.
- **Un artefacto de exploración no es una fuente de verdad.** El inventario de rutas se extrae siempre de los decoradores `@route.*` y `@api_controller(...)` del código. Ver [06 — H-5](./06-operacion-y-deuda-tecnica.md) y [02b §16](./02b-proposito-y-consumidores-de-endpoints.md).
- **`Aplicacion/` no está versionada** (`git ls-files Aplicacion` → 0 archivos). Lo que se escriba en esta carpeta no tiene revisión ni reversión mientras siga fuera de Git. Ver [06 — H-7](./06-operacion-y-deuda-tecnica.md).

---

## 6. Convenciones de lectura

| Marcador | Significado |
|---|---|
| ✅ | Verificado en esta pasada contra el código |
| 🟡 | Verificado parcialmente o deducido del código con alta confianza |
| 🔴 | Brecha, conflicto o incumplimiento verificado, sin resolver |
| 🔍 | Supuesto o inferido; plausible pero no comprobado contra una fuente primaria |

Otras convenciones:

- **Rutas de la API.** Se expresan como las ve Django (`/api/...`). El navegador las pide con el prefijo `/backend`, que nginx reescribe a `/api`.
- **Rutas de pantalla.** Se expresan como las ve el usuario (`/administracion/competencias/[id]`).
- **Archivos.** Las rutas de código se expresan desde la raíz del repositorio (`backend/modules/...`, `frontend/src/...`).
- **Idioma.** Documentación en español neutro. Los identificadores, rutas y literales de código se citan literalmente, en su idioma original.

---

## 7. Mantenimiento de esta carpeta

Cuando cambie el código, la documentación se actualiza en el **mismo cambio**. La lista mínima es:

1. ¿Se añadió o quitó una ruta? → regenerar [02a](./02a-inventario-de-endpoints.md) y [02b](./02b-proposito-y-consumidores-de-endpoints.md); ajustar el inventario de [05](./05-flujos-end-to-end.md) § 3.
2. ¿Se añadió o quitó una pantalla? → actualizar [03](./03-frontend.md) § 3, la ficha correspondiente en [03a](./03a-paginas-publicas-y-compra.md) o [03b](./03b-paginas-administrativas-y-operativas.md), y la matriz de [05a](./05a-matriz-pagina-flujo-endpoint-datos.md).
3. ¿Cambió el modelo de datos? → actualizar [04](./04-datos-y-dominio.md) y, si cambia la siembra, [04a](./04a-seeds-y-datos-iniciales.md).
4. ¿Se añadió un comando de gestión? → actualizar [04a](./04a-seeds-y-datos-iniciales.md), [06](./06-operacion-y-deuda-tecnica.md) § 4.2 y [02](./02-backend-y-api.md) § 8.
5. ¿Apareció un defecto nuevo? → registrarlo en [06](./06-operacion-y-deuda-tecnica.md) § 6 con evidencia e impacto.
6. ¿Cambió la cobertura? → reejecutar el checklist de [00](./00-cobertura-y-trazabilidad.md) § 5 y actualizar sus recuentos.

---

## 8. Documentos que **no** son referencia

Las carpetas `doc/`, `doc_dev/`, `doc-dev/`, `docs/`, `docs-dev/` y `salesianos-fest-2026-main/` contienen material de épocas distintas del proyecto. **No deben usarse como referencia de comportamiento actual** ni copiarse a esta carpeta. El detalle está en [02 § 9.4](./02-backend-y-api.md) y en [06 — H-4](./06-operacion-y-deuda-tecnica.md).

Dos excepciones, ambas verificadas contra el código: `doc/ADMINISTRACION_OPERATIVA_FEST.md` sigue describiendo con exactitud el módulo `administracion`, y `backend/README.md` documenta un comando **inexistente** (`seed_inscripciones`), por lo que requiere corrección antes de usarse como guía operativa — ver [04a § 8, B-1](./04a-seeds-y-datos-iniciales.md).
