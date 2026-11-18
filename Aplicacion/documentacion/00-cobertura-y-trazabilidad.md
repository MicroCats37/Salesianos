# 00 — Cobertura y trazabilidad de la documentación

> **Ámbito:** auditoría de cobertura del conjunto documental de `Aplicacion/documentacion/` frente al código del repositorio.
> **Método:** verificación directa en el árbol de trabajo (`backend/`, `frontend/`, `worker/`, `proxy/`, `docker-compose.yml`) y relectura de los 13 documentos preexistentes.
> **Fecha de la auditoría:** 2026-11-18.
> **Naturaleza:** este documento **constata**. No modifica código, configuración ni base de datos.
> **Alcance de la corrección:** únicamente documentación (`Aplicacion/documentacion/`). Ningún archivo de aplicación, runtime, configuración o base de datos fue tocado.

---

## 1. Propósito

Responder tres preguntas de forma verificable:

1. **¿Está todo documentado?** — qué cantidad de cada cosa existe en el código y cuánto de eso está descrito.
2. **¿Coinciden los recuentos entre documentos?** — dónde dos documentos contaban la misma realidad de dos maneras.
3. **¿Qué falta?** — qué queda fuera por decisión de alcance, y cómo repetir la comprobación cuando el código cambie.

Este documento es el **contraste verificable** del resto de la carpeta. Si un número de cualquier otro documento no aparece aquí, o difiere, hay que resolverlo contra el código antes de fiarse de él.

---

## 2. Método

La auditoría combinó cinco técnicas. Ninguna escribe en el repositorio.

| # | Técnica | Qué produce | Limitación |
|---|---|---|---|
| 1 | **Recuento por análisis de decoradores** sobre `backend/modules/**/presentation/controllers/*.py`: `@route.get|post|put|patch|delete(...)` y `@api_controller(prefix, ...)` | Número de definiciones de ruta por controlador y por prefijo | No distingue lo registrado de lo no registrado |
| 2 | **Lectura del manifiesto** `backend/config/api.py` (28 llamadas a `api.register_controllers(...)`, en orden) | Qué controladores están montados y en qué orden (el orden resuelve prefijos compartidos) | No comprueba que el runtime acepte las rutas |
| 3 | **Recuento del árbol del frontend**: `frontend/src/app/**/page.tsx`, `layout.tsx`, `route.ts`, `frontend/src/features/**`, `frontend/src/components/**` | Pantallas, layouts, route handlers y tamaño de las carpetas | No dice qué endpoint consume cada pantalla |
| 4 | **Traza de consumidores** en `frontend/src/**` (excluyendo `_legacy*`): servicios → hooks → componentes → páginas | Qué rutas tiene un consumidor real y cuáles sólo tienen transporte preparado | Una función sin uso es indistinguible de un uso sin vista salvo por lectura del árbol de imports |
| 5 | **Recuento del dominio**: `backend/modules/*/migrations/`, `backend/modules/*/domain/models/`, `backend/core/management/commands/`, `backend/modules/*/management/commands/` | Migraciones, modelos, tablas y comandos de gestión | — |

**Regla de decisión aplicada:** una afirmación documental se corrige **solo** cuando el código la contradice de forma explícita. Cuando dos documentos discrepan pero ambos son defendibles, se corrige el que **no declara su criterio** y se documenta el criterio en ambos.

---

## 3. Cobertura por capa

### 3.1 Backend — superficie HTTP

| Elemento | Valor verificado | Documento que lo cubre |
|---|---|---|
| Rutas registradas en runtime | **111** | [02a](./02a-inventario-de-endpoints.md) § 4, [02b](./02b-proposito-y-consumidores-de-endpoints.md) § 4–§14 |
| Definiciones de ruta en código | **112** (111 + 1 no registrada) | [02a](./02a-inventario-de-endpoints.md) § 1 |
| Controladores registrados | 29 (28 del proyecto + `NinjaJWTDefaultController`) | [02](./02-backend-y-api.md) § 4.1 |
| Llamadas a `register_controllers` | **28** | [02](./02-backend-y-api.md) § 4.1, [01](./01-arquitectura-y-runtime.md) § 6.3 |
| Controlador escrito y no registrado | 1 (`IngenieroHabilitadoController`) | [02a](./02a-inventario-de-endpoints.md) § 5, [06 — H-8](./06-operacion-y-deuda-tecnica.md) |
| Rutas públicas (`auth=None`) | **20** (17 del proyecto + 3 de la librería) | [02a](./02a-inventario-de-endpoints.md) § 1 |
| Rutas con respuesta `204 No Content` | 2 | [02a](./02a-inventario-de-endpoints.md) § 1 |
| Fichas de endpoint escritas | **111 / 111 (100 %)** | [02b](./02b-proposito-y-consumidores-de-endpoints.md) |

### 3.2 Backend — autorización

| Elemento | Valor verificado | Documento |
|---|---|---|
| Códigos de capacidad | **11** | [02](./02-backend-y-api.md) § 6.2 |
| Niveles de actor | 3 (`usuario`, `staff`, `superusuario`) | [02](./02-backend-y-api.md) § 6.2 |
| Clases de permiso concretas | `RequireAdmin` + 10 subclases de `RequireCapability` | [02](./02-backend-y-api.md) § 6.2 |
| Propiedad (ownership) por recurso | 5 helpers en `salesianos_fest/presentation/ownership.py` | [02](./02-backend-y-api.md) § 6.2 |

### 3.3 Backend — dominio y datos

| Elemento | Valor verificado | Documento |
|---|---|---|
| Módulos de negocio | 7 (`usuarios`, `eventos`, `commerce`, `pagos`, `salesianos_fest`, `competencias`, `administracion`) | [04](./04-datos-y-dominio.md) § 2 |
| Modelos de negocio | **31** (+ 2 abstractos, 1 proxy sin tabla) | [04](./04-datos-y-dominio.md) § 3 |
| Tablas de negocio | **31** (+ 10 históricas de `simple_history` + 2 de unión M2M) | [04](./04-datos-y-dominio.md) § 1.3 |
| Tablas totales en `backend/db.sqlite3` | 56 (13 de framework + 43 de dominio) | [04](./04-datos-y-dominio.md) § 1.3 |
| Archivos de migración | **30** (29 aplicadas; `pagos.0006` pendiente) | [04](./04-datos-y-dominio.md) § 4 |
| Comandos de gestión del proyecto | **13** (11 en `modules/*` + 2 en `core/`) | [04a](./04a-seeds-y-datos-iniciales.md) § 1, [06](./06-operacion-y-deuda-tecnica.md) § 4.2, [02](./02-backend-y-api.md) § 8 |

### 3.4 Frontend — superficies

| Elemento | Valor verificado | Documento |
|---|---|---|
| Pantallas enrutables | **20** | [03](./03-frontend.md) § 3, [03a](./03a-paginas-publicas-y-compra.md) § 2.3, [03b](./03b-paginas-administrativas-y-operativas.md) § 2 |
| Route handlers de Next | 2 (`/api/auth/refresh`, `/api/auth/logout`) | [03](./03-frontend.md) § 3, [03a](./03a-paginas-publicas-y-compra.md) § 5.9–5.10 |
| Layouts | 11 (raíz, `(app)`, `(app)/dashboard`, área admin y 7 secciones) | [03](./03-frontend.md) § 2, [03b](./03b-paginas-administrativas-y-operativas.md) § 11 |
| Layouts de sección con `AdminSeccionGuard` | **7** | [03](./03-frontend.md) § 4, [03b](./03b-paginas-administrativas-y-operativas.md) § 3 |
| Fichas de pantalla escritas | 16 en [03b](./03b-paginas-administrativas-y-operativas.md) + 8 páginas y 2 handlers en [03a](./03a-paginas-publicas-y-compra.md) | — |
| Acciones de pantalla trazadas | 113 (72 con llamada al backend, 41 sin llamada) | [05a](./05a-matriz-pagina-flujo-endpoint-datos.md) § 6.1 |
| Clientes HTTP distintos para el catálogo | 4 en total; 3 sirven `GET /catalogo/paquetes/`, 2 sirven `GET /catalogo/disciplinas/` y `/categorias/` | [03](./03-frontend.md) § 7.4, [05](./05-flujos-end-to-end.md) nota del flujo 1 |
| Estilos de espejo de respuesta coexistentes | 2 (Zod estricto vs. genéricos de TypeScript) | [03](./03-frontend.md) § 7.3 |
| Clientes con `fetch` crudo sin pasar por `lib/api.ts` | 2 (`portada/hooks/useCatalogo.ts`, `landing/paquetes.service.ts`) | [03](./03-frontend.md) § 7.4, [06 — H-9](./06-operacion-y-deuda-tecnica.md) |
| Archivos de `frontend/src` | 559 | [03](./03-frontend.md) § 9 |

### 3.5 Cobertura de consumidores

**Criterio unificado:** una ruta tiene *consumidor en el frontend* cuando existe código de `frontend/src` que **emite la llamada** y ese código está **alcanzado por una vista renderizada** o por un route handler de Next. Una función de servicio o un hook exportado **sin ninguna vista que lo use** es *transporte preparado pero no conectado* y **no** cuenta como consumidor.

| Categoría | Rutas | Total |
|---|---|---|
| Con consumidor en el frontend | 68 | 111 |
| Con código de servicio/hook pero sin vista que lo invoque | 2 (`POST /api/inscripciones/`, `GET /api/catalogo/paquetes/{paquete_id}/`) | |
| Con consumidor externo, no frontend | 1 (`POST /api/pagos/izipay/notificacion` ← servidor de Izipay) | |
| Sin ninguna referencia en `frontend/src` | 40 | |

Cobertura documental de esa superficie: **111 / 111 rutas con ficha** en [02b](./02b-proposito-y-consumidores-de-endpoints.md), e inventario completo de las 43 sin consumidor frontend en [02b § 16](./02b-proposito-y-consumidores-de-endpoints.md) y [05a § 5](./05a-matriz-pagina-flujo-endpoint-datos.md).

### 3.6 Semillas y bootstrap

| Elemento | Valor verificado | Documento |
|---|---|---|
| Mecanismos de siembra / carga inicial / bootstrap | **15** (5 comandos activos, 2 comandos muertos, 3 residuos heredados de otro proyecto, 2 catálogos estáticos en el frontend, 1 juego de fixtures de test, 1 migración con puerta de datos, 1 microservicio sin siembra) | [04a](./04a-seeds-y-datos-iniciales.md) § 1 |
| Comandos activos | 5 (`create_admin`, `seed_admin`, `seed_catalogo_fest`, `seed_commerce`, `reset_dev`) | [04a](./04a-seeds-y-datos-iniciales.md) § 2 |
| Comandos inejecutables | 2 (`seed_colegiados`, `seed_perfiles_ingeniero_faltantes`) | [04a](./04a-seeds-y-datos-iniciales.md) § 2.6–2.7 |
| Comandos que no son seed | 6 (`reconciliar_pagos`, `reparar_cupos`, `verificar_pagos`, `verificar_intentos_pago`, `verificar_pases`, `auditar_genero_disciplinas`) | [04a](./04a-seeds-y-datos-iniciales.md) § 9 |
| Siembra automática en el arranque | **Ninguna**: `entrypoint.sh` sólo hace `migrate` + `collectstatic` + gunicorn | [01](./01-arquitectura-y-runtime.md) § 10.2, [06](./06-operacion-y-deuda-tecnica.md) § 3.3 |
| Planificador de tareas | **No existe** (`django_q` instalado y configurado, sin consumidor ni `schedule()`) | [06](./06-operacion-y-deuda-tecnica.md) § 4.1 |

### 3.7 Cobertura del conjunto documental

| Documento | Extensión | Cobertura declarada | Verificación de esta auditoría |
|---|---|---|---|
| 00 — Cobertura y trazabilidad | 8 secciones | Auditoría | Este documento |
| 01 — Arquitectura y runtime | 12 secciones | Runtime completo | Recuentos de archivos y grupos de ruta corregidos |
| 02 — Backend y API | 10 secciones | Servicio completo | § 8 ampliada a los 13 comandos de gestión |
| 02a — Inventario de endpoints | 7 secciones | 111 / 111 rutas | Cuadre de la columna «Rutas» corregido |
| 02b — Propósito y consumidores | 19 secciones | 111 / 111 rutas | 12 atribuciones de consumidor corregidas; § 1.3 y § 16 reencuadrados |
| 03 — Frontend | 12 secciones | Árbol, rutas, estado, calidad | Recuentos de `app/`, `features/` y `components/` corregidos |
| 03a — Páginas públicas y de compra | 10 secciones | 8 páginas + 2 handlers | Verificado contra `frontend/src/app` |
| 03b — Páginas administrativas | 11 secciones | 16 páginas + 2 handlers | Verificado contra `frontend/src/app` y los 7 guards |
| 04 — Datos y dominio | 13 secciones | Dominio y migraciones | Recuentos de migraciones y tablas revalidados |
| 04a — Seeds y datos iniciales | 9 secciones | 15 mecanismos + anexo de comandos | Recuento de 13 comandos revalidado |
| 05 — Flujos end-to-end | 6 secciones | 27 flujos | Recuentos de rutas por controlador corregidos |
| 05a — Matriz página → flujo → endpoint → datos | 6 secciones | 20 páginas + 2 handlers, 112 definiciones | Criterio de consumidor unificado con 02b |
| 06 — Operación y deuda técnica | 8 secciones | Operación + H-1…H-9 + D-1…D-16 | Recuento de comandos de gestión revalidado |
| 07 — Guía para el agente de UI/UX | 9 secciones | Intervención sobre el frontend | Sin cambios de contenido; enlaces reparados |

---

## 4. Contradicciones detectadas y corregidas

Cada fila es una discrepancia entre documentos o entre un documento y el código. La columna «corrección» indica qué se cambió y en qué archivo.

| # | Contradicción | Evidencia | Corrección |
|---|---|---|---|
| C-1 | [02a](./02a-inventario-de-endpoints.md) § 3 declaraba **16** rutas para `/api/administracion/competencias`, mientras su propio inventario detallado lista **17** y la suma de la columna daba 110 en lugar de 111 | Análisis de decoradores: `admin_competencias_controller.py` declara 17 `@route.*` | Corregido a **17** y añadida la fila de cuadre explícito |
| C-2 | [05](./05-flujos-end-to-end.md) § 3 decía «15 rutas» para `AdminCompetenciasController` y «11 rutas» para `AdminEncuentrosController`, listando 17 y 12 respectivamente | Análisis de decoradores: 17 y 12 | Corregido a **17** y **12** |
| C-3 | [05](./05-flujos-end-to-end.md) flujo 24 accounted «26 rutas» para la superficie de competencias | 17 + 12 = 29 | Corregido a **29** |
| C-4 | [05](./05-flujos-end-to-end.md) § 3 atribuía a `InscripcionSaldoController` el prefijo `/asignaciones` | `@api_controller("/inscripciones", …)` en `asignacion_controller.py:211` | Corregido a **`/inscripciones`** |
| C-5 | [01](./01-arquitectura-y-runtime.md) § 2.1 declaraba «618 archivos en ambos» para la copia de `frontend/src` | Recuento real: **559** archivos en `frontend/src` y en `Aplicacion/frontend/src` | Corregido a **559** |
| C-6 | [01](./01-arquitectura-y-runtime.md) § 2 y § 5.2 declaraban un grupo de ruta `(public)` en `app/` | No existe el directorio: sólo `(auth)` y `(app)`; `/` e `/informacion` cuelgan de la raíz | Corregido: se nombra la realidad (`(auth)`, `(app)` y raíz) |
| C-7 | [02](./02-backend-y-api.md) § 8 listaba **11** comandos de gestión; [06](./06-operacion-y-deuda-tecnica.md) § 4.2 listaba **13** | En disco hay 13: 11 en `modules/*/management/commands/` y 2 en `core/management/commands/` (`create_admin`, `reset_dev`) | Corregido [02](./02-backend-y-api.md) § 8 a **13**, alineado con [06](./06-operacion-y-deuda-tecnica.md) y [04a](./04a-seeds-y-datos-iniciales.md) |
| C-8 | [03](./03-frontend.md) § 1 declaraba «19 pantallas enrutables» | Recuento de `frontend/src/app/**/page.tsx`: **20** | Corregido a **20** |
| C-9 | [03](./03-frontend.md) § 2 declaraba «33 archivos .tsx» en `app/` | 20 `page.tsx` + 11 `layout.tsx` = **31** `.tsx`; los `route.ts` son 2 y van aparte | Corregido a **31 `.tsx` (20 páginas + 11 layouts) + 2 route handlers** |
| C-10 | [03](./03-frontend.md) § 2 declaraba «306 archivos» en `features/` | Recuento real: **281** (la suma de las subcarpetas que el propio documento lista da 281) | Corregido a **281** |
| C-11 | [03](./03-frontend.md) § 2 declaraba «14 carpetas» en `components/` | Recuento real: **13** | Corregido a **13** |
| C-12 | [02b](./02b-proposito-y-consumidores-de-endpoints.md) declaraba **79** rutas con consumidor frontend y **30** sin consumidor; [05a](./05a-matriz-pagina-flujo-endpoint-datos.md) declaraba **68** y **43** | Los dos recuentos son defendibles con criterios distintos: 02b contaba *servicio o hook*, 05a contaba *vista que consume* | Unificado el criterio en ambos documentos (§ 1.3 de 02b, nota de criterio) y **corregidas 12 atribuciones erróneas** en 02b (C-13) |
| C-13 | [02b](./02b-proposito-y-consumidores-de-endpoints.md) atribuía un consumidor de vista a 12 rutas que **no lo tienen** | (a) `competencias.comandos.service.ts` no expone alta/edición/borrado/estado de competencia, ni estado o borrado de ronda o encuentro; `competencias.service.ts` no expone lectura de equipos, rondas ni encuentros; `CompetenciaEditorModal.tsx` es sólo un marco de modal sin llamada HTTP. (b) `useCreateInscripcion` y `usePaqueteDetail` / `usePaqueteDisciplinas` están exportados y **ninguna vista los usa**. (c) `CompetenciasAccionesEncuentro.tsx` abre los editores de programación, bye y enlace, no de estado | 12 fichas de 02b corregidas (línea «Consumidor» y línea «Estado»), § 1.3 reencuadrado y § 16 ampliado de 30 a 43 rutas |
| C-14 | [03b](./03b-paginas-administrativas-y-operativas.md) enlazaba a `./02-backend-and-api.md`, fichero inexistente | Comprobación de todos los enlaces relativos de los 13 documentos | Enlace corregido a `./02-backend-y-api.md`. **No queda ningún enlace roto** en la carpeta |

### Contradicciones comprobadas y **resultado no ser** contradicciones

| # | Aparentemente contradictorio | Veredicto |
|---|---|---|
| N-1 | [03](./03-frontend.md) dice «tres clientes de catálogo» y [05](./05-flujos-end-to-end.md) dice «cuatro implementaciones de cliente» | No hay contradicción: 03 cuenta por *endpoint* (3 sirven `/catalogo/paquetes/`), 05 cuenta *clientes de catálogo en total* (4). El detalle se precisa en § 3.4 de este documento |
| N-2 | [03a](./03a-paginas-publicas-y-compra.md) dice «8 páginas + 2 handlers» y [03b](./03b-paginas-administrativas-y-operativas.md) dice «16 páginas» | No hay contradicción: el solapamiento es intencionado. 03b cubre las 12 páginas administrativas **más** `/dashboard`, `/dashboard/inscripcion/[id]`, `/inscripcion` y `/pases`, que 03a también documenta desde la perspectiva del usuario final |
| N-3 | [04](./04-datos-y-dominio.md) § 4 dice «30 migraciones, 29 aplicadas» y [04a](./04a-seeds-y-datos-iniciales.md) § 4 muestra `django_migrations` con 76 filas | No hay contradicción: 76 es el total de *todas* las apps (incluidas las de framework); 30/29 son las migraciones de **dominio** |
| N-4 | [04](./04-datos-y-dominio.md) da 31 modelos de negocio y [04a](./04a-seeds-y-datos-iniciales.md) § 4 recorre 31 tablas de negocio | Consistente |

---

## 5. Checklist reejecutable

Para repetir la auditoría tras un cambio de código. Cada punto indica **qué comprobar** y **dónde se compara**.

### 5.1 Superficie HTTP

| # | Comprobación | Cómo | Se compara con |
|---|---|---|---|
| 1 | Definiciones de ruta por controlador | Contar `@route.<verbo>(` en `backend/modules/**/presentation/controllers/*.py` | [02a](./02a-inventario-de-endpoints.md) § 4 · [02b](./02b-proposito-y-consumidores-de-endpoints.md) § 4–§14 |
| 2 | Controladores realmente montados | Contar `register_controllers(` en `backend/config/api.py` y leer el orden | [01](./01-arquitectura-y-runtime.md) § 6.3 · [02](./02-backend-y-api.md) § 4.1 |
| 3 | Rutas públicas | Contar `auth=None` en los controladores | [02a](./02a-inventario-de-endpoints.md) § 1 (20 tras descontar la ruta no registrada y añadir las 3 de la librería) |
| 4 | Superficie por prefijo | Sumar las rutas del § 4 de [02a](./02a-inventario-de-endpoints.md) | Debe dar **111** (+ 1 no registrada = 112) |
| 5 | Consumidores | Seguir servicio → hook → componente → página en `frontend/src` | [02b](./02b-proposito-y-consumidores-de-endpoints.md) § 2 y § 15 · [05a](./05a-matriz-pagina-flujo-endpoint-datos.md) § 5 y § 6.2 |

### 5.2 Frontend

| # | Comprobación | Cómo | Se compara con |
|---|---|---|---|
| 6 | Pantallas | Listar `frontend/src/app/**/page.tsx` | [03](./03-frontend.md) § 3 (20) · [03a](./03a-paginas-publicas-y-compra.md) § 2.3 · [03b](./03b-paginas-administrativas-y-operativas.md) § 2 · [05a](./05a-matriz-pagina-flujo-endpoint-datos.md) § 6.1 |
| 7 | Route handlers | Listar `frontend/src/app/**/route.ts` | [03](./03-frontend.md) § 3 (2) |
| 8 | Layouts y guards | Listar `frontend/src/app/**/layout.tsx` | [03](./03-frontend.md) § 4 (7 secciones con guard) · [03b](./03b-paginas-administrativas-y-operativas.md) § 3 |
| 9 | Tamaño del árbol | Contar archivos por carpeta de `frontend/src` | [03](./03-frontend.md) § 2 (559 en `src`, 281 en `features`, 13 carpetas en `components`) |
| 10 | Paridad `frontend/` ↔ `Aplicacion/frontend/` | SHA-256 archivo por archivo | [03](./03-frontend.md) § 9 (559/559, 18/18, 33/33) |
| 11 | Clientes HTTP duplicados | Buscar `await fetch(` fuera de `lib/api.ts` y de los route handlers | [03](./03-frontend.md) § 7.4 · [06 — H-9](./06-operacion-y-deuda-tecnica.md) |

### 5.3 Dominio, datos y operación

| # | Comprobación | Cómo | Se compara con |
|---|---|---|---|
| 12 | Migraciones | Contar `backend/modules/*/migrations/*.py` sin `__init__.py`; contrastar con `django_migrations` en modo sólo lectura | [04](./04-datos-y-dominio.md) § 4 (30 archivos, 29 aplicadas) |
| 13 | Tablas | `sqlite_master` sobre `backend/db.sqlite3` en `mode=ro` | [04](./04-datos-y-dominio.md) § 1.3 (56) |
| 14 | Comandos de gestión | Listar `backend/**/management/commands/*.py` sin `__init__.py` | [04a](./04a-seeds-y-datos-iniciales.md) § 1 · [06](./06-operacion-y-deuda-tecnica.md) § 4.2 · [02](./02-backend-y-api.md) § 8 (13) |
| 15 | Siembra automática | Leer `backend/docker/entrypoint.sh` y `docker-compose.yml` | [01](./01-arquitectura-y-runtime.md) § 10.2 (ninguna) |
| 16 | Planificador | Buscar `async_task`, `schedule(`, `crontab`, `qcluster` | [06](./06-operacion-y-deuda-tecnica.md) § 4.1 (ninguno) |
| 17 | Capacidades y gates | Listar las constantes de `backend/core/capacidades.py` y las clases de `backend/core/permissions.py` | [02](./02-backend-y-api.md) § 6.2 (11 códigos, 3 niveles) |
| 18 | Enrutamiento del borde | Leer `proxy/nginx.conf` | [01](./01-arquitectura-y-runtime.md) § 4 · [06](./06-operacion-y-deuda-tecnica.md) § 2 |

### 5.4 Enlazado interno de la documentación

| # | Comprobación | Cómo | Criterio de aceptación |
|---|---|---|---|
| 19 | Enlaces relativos | Resolver cada enlace Markdown de los 15 documentos contra el sistema de archivos | **0 enlaces rotos** |
| 20 | Recuentos cruzados | Comparar cada cifra repetida en dos documentos | Una sola cifra y un solo criterio |
| 21 | Cobertura de rutas | Contar las fichas `### N.M \`RUTA\`` de 02b y las filas del § 4 de 02a | Ambas = **111** |
| 22 | Cobertura de páginas | Contar las fichas `### N.M \`RUTA\`` de 03a y 03b | 03a = 8 páginas + 2 handlers; 03b = 16 páginas |

---

## 6. Exclusiones y huecos conocidos

Lo que **no** se verificó en esta auditoría y por qué. No son afirmaciones del sistema: son límites explícitos.

| # | Hueco | Motivo | Cómo cerrarlo |
|---|---|---|---|
| H-1 | **Paridad campo a campo** entre los *wrappers* del backend y los esquemas Zod del frontend | Exige un diff automático de ambos contratos; el volumen no permite una comprobación manual fiable | Generar el diff desde el esquema OpenAPI de Django contra los esquemas Zod |
| H-2 | **Cobertura de `ownership.py` ruta por ruta** | `ownership.py` expone 5 helpers y ~20 rutas dependen de ellos; la auditoría verificó **qué** helper usa cada ruta, no la corrección interna de cada helper | Auditar cada helper contra las reglas de propiedad del dominio |
| H-3 | **Línea base de pruebas** | No se ejecutó la suite de `backend/` ni la de `frontend/` en esta auditoría (sólo se leyó su código y la línea base registrada) | Ejecutar `pytest` y `npx vitest run` y registrar el resultado como línea base versionada |
| H-4 | **Comportamiento en PostgreSQL** | La base de desarrollo es SQLite; la portabilidad de las restricciones condicionales no se comprobó | Reproducir la cadena de migraciones sobre PostgreSQL |
| H-5 | **Contrato del worker en el límite** | El mapeo de 503/504 del scraper hacia `RealConsultaExternaClient` no se ejercitó | Prueba de contrato contra el scraper en ejecución |
| H-6 | **Parámetro `evento_id` de las rutas de acreditación** | No se comprobó si se contrasta con el evento activo | Lectura dirigida de `acreditacion_controller.py` y `registrar_acceso_flujo` |
| H-7 | **Campos de `MeOut`** | El flag `require_admin` que consume el frontend no se contrastó con la definición real del esquema | Lectura del esquema y del espejo frontend |
| H-8 | **Estado del árbol `Aplicacion/`** | `Aplicacion/` no está versionada; su contenido puede haber cambiado sin dejar rastro | Decidir la política de versionado antes de la siguiente auditoría |
| H-9 | **Líneas base de calidad del frontend** | Los valores «105 errores de Biome, 93 avisos» y «1 archivo rojo estable, 1 inestable» proceden de la medición de [03](./03-frontend.md) § 10, no de esta auditoría | Reejecutar `npx biome check .` y `npx vitest run` |

---

## 7. Trazabilidad de esta auditoría

| Elemento | Valor |
|---|---|
| Alcance | 15 documentos de `Aplicacion/documentacion/` contrastados con `backend/`, `frontend/`, `worker/`, `proxy/` y `docker-compose.yml` |
| Tipo de artefacto | Auditoría documental (solo lectura del código) |
| Artefacto SDD | `sdd/explore/documentation-coverage-audit` |
| Cambios en código | **Ninguno.** Sólo se modificaron documentos de `Aplicacion/documentacion/` |
| Cambios en la documentación | 13 documentos existentes corregidos o ampliados + 2 documentos creados (este y `README.md`) |
| Contradicciones corregidas | 14 (C-1 … C-14), de las cuales 2 eran enlaces rotos o recuentos de archivos y 12 atribuiciones de consumidor o recuentos de rutas |
| Contradicciones descartadas con justificación | 4 (N-1 … N-4) |
| Huecos declarados | 9 (H-1 … H-9) |

---

## 8. Documentos relacionados

- [README — Índice de la documentación](./README.md) — punto de entrada navegable.
- [01 — Arquitectura y runtime](./01-arquitectura-y-runtime.md) — topología, despliegue y variables de entorno.
- [02 — Backend y API](./02-backend-y-api.md) — arquitectura del servicio Django/Ninja.
- [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) — catálogo de las 111 rutas.
- [02b — Propósito y consumidores de endpoints](./02b-proposito-y-consumidores-de-endpoints.md) — ficha de negocio de cada ruta.
- [03 — Frontend](./03-frontend.md) — arquitectura del frontend.
- [03a — Páginas públicas y de compra](./03a-paginas-publicas-y-compra.md) — fichas de pantalla no administrativa.
- [03b — Páginas administrativas y operativas](./03b-paginas-administrativas-y-operativas.md) — fichas de pantalla administrativa.
- [04 — Datos y dominio](./04-datos-y-dominio.md) — modelos, tablas y migraciones.
- [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) — mecanismos de siembra.
- [05 — Flujos end-to-end](./05-flujos-end-to-end.md) — los 27 flujos de navegador.
- [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) — trazabilidad completa.
- [06 — Operación y deuda técnica](./06-operacion-y-deuda-tecnica.md) — operación, hallazgos y deuda.
- [07 — Guía para el agente de UI/UX](./07-guia-para-ui-ux.md) — alcance de la intervención sobre el frontend.
