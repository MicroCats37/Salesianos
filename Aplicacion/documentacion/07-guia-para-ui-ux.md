# 07 — Guía para el agente de UI/UX

> **Estado:** vigente (guía operativa de intervención sobre el frontend)
> **Destinatario:** quien va a rediseñar o reconstruir las pantallas del frontend
> **Alcance:** qué se puede cambiar, qué no, y cómo se entrega un cambio
> **Fuente de verdad:** [`03-frontend.md`](./03-frontend.md) (arquitectura vigente) y [`../../contract/`](../../contract/) (obligaciones normativas)
> **Owner:** frontend

---

## 1. Principio rector

> **El backend posee el dominio. La UI posee la presentación.**

Todo el valor de una regla de negocio —elegibilidad, capacidad, cupo, roster, precio, estado de pago, transición de estados, autorización— vive en el backend, y se aplica dentro de una transacción. La UI **representa** ese veredicto; no lo recalcula, no lo anticipa y no lo interpreta.

Cuando una regla falta en la respuesta del backend, la pregunta correcta no es "¿qué regla aplico aquí?", sino: **"¿el backend debería haberla aplicado?"**. Si la respuesta es sí, es una solicitud de cambio de backend, no un ajuste de frontend.

---

## 2. Propiedad inmutable del backend

Lo siguiente **no se modifica desde el frontend**. No es una cuestión de estilo: alterarlo produce respuestas que el backend nunca devolvió, o ignora un control que el backend sí aplica.

| Activo del backend | Por qué es inmutable desde la UI | Cómo se consume |
|---|---|---|
| Sobre de respuesta `{success, data, error, message}` | Lo define `core.responses.ApiResponse` | Consumirlo; no reconstruirlo ni renombrarlo |
| Claves de paginación (`count`, `page`, `pageSize`, `totalPages`) | Mismo origen | Consumirlas; no derivar un total propio |
| Nombres de campo, nulabilidad y literales de enumeración de los *wrappers* | El espejo Zod 1:1 **es** el contrato (`contract/api-wrapper-presenter-contract.md` §7) | Consumir el espejo; cambiarlo exige cambio de backend en el mismo commit |
| Vocabularios de estado (`estado_capacidad_equipo`, estados de inscripción, de pago, de acreditación) | Los publica el backend (`GET /administracion/catalogos`) | Leer del catálogo; no hardcodear literales |
| Mapa de capacidades de administración (11 códigos) | Espejo 1:1 de `backend/core/capacidades.py`; el backend es la autoridad | `features/admin/utils/admin.capacidades.ts` solo **nombra** |
| Catálogo público de mensajes de error | Lo translate `core/exceptions.py` a partir de códigos estables | Mostrar el mensaje que llega; no traducirlo ni compilarlo |
| Códigos de error de negocio | Son estables y técnicos | Reaccionar al **estado HTTP** y al mensaje, no ramificar sobre el código |
| Reglas de transición de estado, cupos, precios y pagos | Se aplican en el backend, con transacción | Renderizar el estado devuelto |
| Forma del endpoint y sus parámetros | Contrato HTTP | Consumir el servicio; no llamar al backend desde un componente |

✅ Verificado: `features/admin/services/admin.resumen.service.ts` documenta y aplica exactamente este criterio — *"el servicio nunca recalcula una métrica"* — y `features/admin/utils/admin.capacidades.ts` declara que *ocultar un botón no es autorizar*.

---

## 3. Qué puede cambiar la UI

### 3.1 Liberty — se puede crear y editar libremente

| Ámbito | Qué se permite |
|---|---|
| `src/app/**` | Enrutado, grupos de ruta, `loading.tsx` / `error.tsx`, metadata, composición de layout. **Solo eso: nada de lógica de negocio ni de carga de datos** |
| `src/components/**` | Composición visual, layout, tokens de diseño, `components/ui` |
| `src/features/<f>/{components,views,hooks,utils}/**` | Presentación, interacción, estado de cliente |
| `src/providers/**`, `src/app/globals.css`, tema de Tailwind | Shell de la aplicación y tokens visuales |
| `src/lib/{forms,query-client}.ts`, `src/hooks/{cache,system}/**` | Infraestructura genérica de interacción |

### 3.2 Con cautela — se puede modificar, con restricciones

| Ámbito | Restricción |
|---|---|
| `features/<f>/schemas/**` | **Solo** para agregar campos de presentación (una etiqueta calculada, una variante visual). Cualquier campo que refleja un *wrapper* del backend exige un cambio de backend primero |
| `features/<f>/services/**` | Solo forma de la petición (parámetros de consulta, armado de `FormData`). No se altera el contrato del *payload* |
| `features/<f>/utils/**` | Mapeo y formato puros. No pueden replicar una regla del backend |
| `components/genericForm/inputs/registry.ts` | Solo para registrar un Smart Field **genérico**. Un campo de dominio va en `customFields`, no en el registro global |
| `features/<f>/hooks/**` | Se puede reorganizar la clave de caché **si no se parte** una clave ya usada en otro sitio. La invalidación es un contrato: los tests la verifican |

### 3.3 Prohibido — sin autoridad

| Prohibido | Por qué | Alternativa |
|---|---|---|
| `Aplicacion/backend/**` | El dominio es del backend | Solicitar el cambio |
| `src/proxy.ts`, `app/(app)/layout.tsx`, `app/(app)/administracion/layout.tsx`, `app/(app)/administracion/*/layout.tsx`, `AdminSeccionGuard`, `admin.session.server.ts` | Son la cadena de autoridad | No "simplificarlos": existen por una razón |
| `lib/api.ts`, `lib/auth/**` | Un transporte, un dueño de cookies | Reutilizarlos; nunca crear un segundo cliente |
| Confiar en `USER_SESSION`, en el store de Zustand o en `proxy.ts` para decidir acceso | Los tres son escribibles por el cliente | El 403 del backend es el control |
| Ramificar sobre un **código** de error en un componente | El mensaje público es el contrato | Reaccionar al mensaje y al estado HTTP |
| Reimplementar una regla de negocio | El backend la aplica con transacción | Renderizar lo devuelto |
| Agregar un `fetch` crudo junto a la instancia de `axios` | Crea una segunda política de base URL, autenticación y error | Usar `features/<f>/services/` + `lib/api.ts` |
| Introducir `z.any()` en un espejo de respuesta | Anula el contrato en ejecución | `z.unknown()` cuando la forma sea genuinamente abierta |
| Crear una carpeta de primer nivel bajo `src/` | Rompe el mapa que lee el siguiente agente | Actualizar [`03-frontend.md`](./03-frontend.md) en el mismo commit |
| Renombrar un archivo de prueba que pertenece al runner de Node | `vitest.config.ts` los excluye **por nombre** | No renombrar; convertirlo a suite de Vitest de forma explícita |
| Eliminar una guarda, un layout de sección o `AdminSeccionGuard` | No son redundantes | — |

---

## 4. Restricciones de la API

### 4.1 Un endpoint, un cliente

✅ El estado actual tiene **tres** clientes para `GET /catalogo/paquetes/` (ver [`03-frontend.md` §7.4](./03-frontend.md)). Mientras se normaliza, la regla para el trabajo nuevo es estricta:

- Toda llamada a un endpoint pasa por `features/<f>/services/**` y por la instancia compartida de `lib/api.ts`.
- Ningún `fetch` crudo fuera de `lib/api.ts`, `app/api/auth/*/route.ts` (route handlers del servidor) y `features/admin/services/admin.session.server.ts` (llamada servidor-a-servidor con `backendInternalUrl()`).
- Ningún `fetch` crudo en cliente. Si aparece, es una regresión.

### 4.2 Un conjunto de datos, una clave de caché

- El catálogo tiene **una** clave por conjunto de datos. La separación actual `["landing",…]` frente a `["inscripcion",…]` no se amplía.
- Las claves del panel administrativo siguen el patrón `["admin", <recurso>, params]`, con `adminParametrosConsulta(estado)` como contrato único de filtros.
- Toda mutación que cambie datos debe invalidar **exactamente** las claves afectadas. Los tests `*Comandos.test.tsx` verifican ese conjunto: alterarlo sin actualizar la suite es un error de entrega.

### 4.3 Todo sobre que se consume tiene espejo Zod

- Si se agrega una llamada a un endpoint, se agrega en el mismo commit el esquema Zod 1:1 del *wrapper* del backend, y el servicio valida con `.parse()`.
- Ante un desajuste de Zod, **el fallo debe ser ruidoso**. No se registra y se continúa: ese patrón es el que hoy hace que `features/inscripciones/services/paquete.service.ts` devuelva el payload crudo ante un desajuste y deje la deriva invisible.
- El patrón de referencia es `features/admin/services/admin.http.service.ts` y `admin.resumen.service.ts`: envoltura completa, `.parse()`, y error `ApiQueryError` que **conserva el estado HTTP** para que la UI distinga 403 de 503.

### 4.4 Los mensajes de error son del backend

- El mensaje público que llega en `error.message` se muestra tal cual. No se reescribe, no se traduce, no se parchea por código.
- Los mensajes de reserva del frontend (`errors/error-handler.ts`) están **en inglés**, mientras el backend responde en español. 🔴 Es una inconsistencia conocida (brecha FE-13): no se amplíe. Si se toca esa zona, es para unificar el idioma en el frontend, nunca para alterar el texto del backend.

### 4.5 Errores de campo

- 🔴 El parser de errores 422 de Django está **documentado pero no implementado**: `errors/error-handler.ts` describe el formato `detail: [{loc, msg}]`, pero la cadena de parsers solo contiene `genericRestParser`, que aplana los detalles en un único mensaje (brecha FE-12).
- Consecuencia práctica: hoy los errores de campo **no se aplican** a los campos del formulario. Si una pantalla necesita señalar el campo exacto, hay dos caminos válidos: implementar el parser (una llamada a `addErrorParser`, no una reescritura) o mostrar el mensaje agregado. No se debe simular el mapeo por campo a mano en el componente.

### 4.6 Autenticación y cookies

- El refresco de token pasa por el route handler `/api/auth/refresh`. El cliente no llama directamente a `POST /token/refresh`.
- 🔴 La cookie del token de acceso se emite con `httpOnly: false` (`lib/auth/cookies.ts`), y el comentario de `app/api/auth/refresh/route.ts` afirma lo contrario. Es una decisión de seguridad abierta (brecha FE-2): **no se "corrige" de paso** en un trabajo de UI. Si se cambia, es un cambio propio, revisado y con su propio plan, porque afecta al refresco proactivo en cliente y a la comprobación de credencial de `proxy.ts`.

---

## 5. No duplicar reglas de negocio

Esta es la sección que más veces se incumple, porque duplicar una regla "solo" en la UI parece inofensivo. No lo es: la UI duplicada se desincroniza del backend en silencio y empieza a mentirle al usuario.

| Regla | Dónde vive | Qué hace la UI |
|---|---|---|
| Elegibilidad de un participante | Backend | Muestra el veredicto |
| Capacidad y cupo de un equipo | Backend | Muestra el veredicto |
| Límites de roster | Backend | Muestra el veredicto |
| Cálculo de precio y precio promocional | Backend | Formatea el número devuelto |
| Estado de pago y transiciones de pago | Backend | Muestra el estado y las acciones habilitadas |
| Transiciones de estado de una inscripción | Backend | Muestra el estado; no decide el siguiente paso |
| Autorización por rol o capacidad | Backend (`RequireAdmin` / `RequireCapability`) | Oculta la acción como UX; el 403 es el control |

**Prueba rápida:** si una regla puede cambiar sin tocar el frontend, es del backend. Si el frontend la conoce, es una copia que envellecerá.

Casos concretos que hoy son copias parciales y no deben crecer:

- `features/portada/hooks/useCatalogo.ts` contiene **contenidos editoriales de respaldo** (disciplinas, categorías, orden de pestañas) con identificadores ficticios, que se renderizan cuando la API no responde. No se amplían ni se generalizan a otros conjuntos de datos.
- `features/inscripciones/services/catalog.service.ts` conserva un campo *legacy* (`cantidad_maxima_participantes`) además del vigente (`cantidad_minima_compra`) y normaliza precios por su cuenta. Es compatibilidad transitoria, no un patrón a extender.
- `features/landing/paquetes.service.ts` normaliza precios por su cuenta. Mismo criterio: es deuda transitoria, no plantilla.

---

## 6. Convenciones que se respetan al escribir código nuevo

✅ Derivadas de `contract/next-app-architecture-contract.md` y verificadas en el árbol.

| Tema | Regla |
|---|---|
| Ubicación de la lógica | `app/` enruta; `features/` contiene la lógica; `components/` contiene UI; `lib/` contiene infraestructura |
| `'use client'` | Lo más bajo posible en el árbol. Una página permanece Server Component salvo que necesite interactividad |
| Carga de datos | En Server Components o en hooks de TanStack Query. **Nunca** `useEffect` + `useState` para el dato inicial de una página |
| Formularios | `GenericForm` con **modo 1 (manual, `children`)** en producción. La validación vive en Zod; el componente Smart Field no valida |
| Payload | `buildApiPayload` se invoca **dentro del hook de mutación**, nunca en el `onSubmit` |
| Importaciones | Siempre con nombre; sin `import * as`. Alias `@/` para código compartido |
| *Barrels* | Re-export granulares y explícitos. Sin `export *`; sin barril global de features ni de componentes |
| Nombres | Esquema de formulario `{Acción}{Recurso}FormSchema`; respuesta `{Recurso}ResponseSchema`; servicio `{recurso}.service.ts`; hook `use{Recurso}` |
| Errores | Se propagan como `ApiQueryError` (con estado HTTP) o como el mensaje público; nunca se silencian con `console.error` |
| Pruebas | Cada archivo nuevo de feature llega con su prueba colocable. Vitest por defecto; `// @vitest-environment jsdom` solo en suites de componentes |

---

## 7. Checklist de entrega (handoff)

Una pantalla o un flujo se considera entregado cuando **todas** estas casillas están marcadas.

### 7.1 Alcance

- [ ] El cambio está dentro del ámbito permitido (§3.1) o cuenta con justificación explícita para tocar un ámbito «con cautela» (§3.2).
- [ ] No se tocó `Aplicacion/backend/**`, ni la cadena de guardas, ni `lib/api.ts` / `lib/auth/**`.
- [ ] No se introdujo una carpeta de primer nivel bajo `src/`; si fue inevitable, [`03-frontend.md`](./03-frontend.md) se actualizó en el mismo commit.

### 7.2 Contrato

- [ ] Ninguna regla de negocio se implementó ni se duplicó en el frontend (§5).
- [ ] Todo sobre consumido tiene espejo Zod 1:1 y el servicio valida antes de devolver (§4.3).
- [ ] Ningún mensaje de error fue reescrito, traducido ni parcheado por código (§4.4).
- [ ] No se modificaron las claves de los envelopes, los campos reflejados ni los vocabularios sin un cambio de backend correspondiente (§2).
- [ ] Si un vocabulario nuevo del backend no aparece en el espejo, se **solicitó** el ajuste en lugar de ampliar la copia local.

### 7.3 Transporte y estado

- [ ] Todas las llamadas HTTP pasan por `features/<f>/services/**` y la instancia compartida de `lib/api.ts` (§4.1).
- [ ] Cada conjunto de datos tiene una sola clave de caché; no se ha introducido una clave paralela (§4.2).
- [ ] Las mutaciones invalidan exactamente el conjunto de claves que invaliden antes.
- [ ] El estado de servidor es TanStack Query; el estado de interfaz, Zustand o URL; no hay estado duplicado en dos lugares.

### 7.4 Estructura y convenciones

- [ ] `app/` no contiene lógica de negocio ni carga de datos.
- [ ] `'use client'` está en el nivel más bajo posible.
- [ ] Los formularios usan `GenericForm` en modo 1 y `buildApiPayload` vive en el hook de mutación.
- [ ] Las importaciones son con nombre y los *barrels* son granulares.
- [ ] Los errores se propagan con estado HTTP y no se silencian.

### 7.5 Calidad

- [ ] `npx tsc --noEmit` pasa sin errores.
- [ ] `npx vitest run` no introduce fallos nuevos. 🔴 La línea base actual tiene **1 archivo rojo estable** (`admin.catalogos.schema.test.ts`, por la deriva `estado_capacidad_equipo`) y **1 archivo rojo inestable** (`CompetenciaEncuentroEditors.test.tsx`, dependiente del orden). Un cambio no puede añadir fallos; idealmente cierra alguno de los dos.
- [ ] `npx biome check .` no aumenta el número de errores por encima de la línea base actual (**105 errores, 93 avisos**).
- [ ] La prueba nueva está colocable junto al código y es determinista: pasa en ejecución aislada **y** en la carrera completa.

### 7.6 Documentación

- [ ] Si el cambio altera la arquitectura (rutas, carpetas, claves de caché, contratos), [`03-frontend.md`](./03-frontend.md) se actualizó en el mismo commit.
- [ ] Si el cambio reveló una brecha nueva o cerró una de las 17 listadas en [`03-frontend.md` §11.2](./03-frontend.md), la tabla de brechas se actualizó.
- [ ] El mensaje de entrega indica: rutas afectadas, endpoints usados, claves de caché tocadas, pruebas agregadas y estado de la línea base de calidad.

---

## 8. Errores frecuentes que conviene anticipar

| Error | Por qué ocurre | Qué hacer |
|---|---|---|
| "El backend no devuelve el campo que necesito" | Se asumió un nombre de campo en lugar de leer el espejo | Leer el esquema Zod vigente y el *wrapper* del backend; si el campo no existe, es solicitud de backend |
| "Necesito una llamada extra para el catálogo" | No se conoce el servicio existente | Buscar primero en `features/<f>/services/**`; el catálogo ya tiene clientes de sobra (§7.4 de 03) |
| "El botón debe aparecer solo con permiso X" | Se confunde UX con control | Ocultarlo es correcto como UX; el control es el 403 del backend |
| "La lista no trae los datos" | Se recreó el filtro en el estado local | Los filtros de la administración viven en la URL (`useAdminListaUrl`) |
| "El formulario no muestra el error en el campo" | El parser 422 no existe (FE-12) | Implementar el parser o mostrar el mensaje agregado; no parchear por componente |
| "El token caduca a mitad de la sesión" | Se perdió el interceptor de `lib/api.ts` | Reutilizar la instancia compartida; no reimplementar el refresco |
| "El test pasa solo en mi máquina" | Prueba dependiente del orden | Reproducir la carrera completa; aislar el estado compartido |

---

## 9. Referencias

- [`README.md`](./README.md) — índice navegable del conjunto documental.
- [`00-cobertura-y-trazabilidad.md`](./00-cobertura-y-trazabilidad.md) — auditoría de cobertura, recuentos verificados y checklist reejecutable.
- [`03-frontend.md`](./03-frontend.md) — arquitectura vigente del frontend: estructura, rutas, estado, transporte, calidad y brechas.
- [`03a-paginas-publicas-y-compra.md`](./03a-paginas-publicas-y-compra.md) — ficha de cada pantalla no administrativa que se puede rediseñar.
- [`03b-paginas-administrativas-y-operativas.md`](./03b-paginas-administrativas-y-operativas.md) — ficha de cada pantalla administrativa que se puede rediseñar.
- [`04-datos-y-dominio.md`](./04-datos-y-dominio.md) — *Datos y dominio* (documento hermano de la serie; su contenido no se anticipa aquí).
- [`01-arquitectura-y-runtime.md`](./01-arquitectura-y-runtime.md) — *Arquitectura y runtime* (documento hermano de la serie; su contenido no se anticipa aquí).
- [`05-flujos-end-to-end.md`](./05-flujos-end-to-end.md) — *Flujos end-to-end* (documento hermano de la serie; su contenido no se anticipa aquí).
- [`../../contract/next-app-architecture-contract.md`](../../contract/next-app-architecture-contract.md) — estructura, nombres, estado, formularios e importaciones.
- [`../../contract/api-wrapper-presenter-contract.md`](../../contract/api-wrapper-presenter-contract.md) — envoltorios por módulo, espejo 1:1 con el backend y propiedad de los mensajes públicos.
- [`../../contract/smart.md`](../../contract/smart.md) — Smart Fields, registro global frente a `customFields`, reglas duras del formulario.
- [`../../contract/django-app-architecture-contract.md`](../../contract/django-app-architecture-contract.md) — el lado del backend que este frontend consume.
- [`../../contract/PLAN_REFACTORIZACION.md`](../../contract/PLAN_REFACTORIZACION.md) — controladores, presentadores y construcción de mensajes públicos.

Los documentos hermanos de esta serie se publican en el mismo directorio (`Aplicacion/documentacion/`); este documento no resume ni anticipa su contenido, salvo el enlace explícito a [`04-datos-y-dominio.md`](./04-datos-y-dominio.md).
