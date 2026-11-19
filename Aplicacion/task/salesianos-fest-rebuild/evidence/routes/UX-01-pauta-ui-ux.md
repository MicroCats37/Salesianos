# UX-01 — Pauta UI/UX de Salesianos FEST

**Artifact:** `evidence/routes/UX-01-pauta-ui-ux.md` · **Owner:** A7 (UI) · **Fecha:** 2026-11-19
**Alcance:** la pauta que gobierna las 38 rutas del plan. Complementa `SH-01` (tokens), `SH-02` (responsive), `SH-03` (estados) y `SH-04` (shadcn): aquí se fija **cómo se compone** una página.
**Referencia viva:** la portada (`/`, `src/features/portada/**`) es el ejemplo canónico. No se copia: se usa como medida.

---

## 0. Cómo se usa esta pauta

Cada página nueva se levanta con esta pauta encima. Si una pantalla contradice una regla de aquí, o cambia una regla, **la regla se actualiza aquí primero** y después en la pantalla. Una divergencia silenciosa es un bug de proceso, no un excepción de diseño.

Reglas de lectura:

- **[M]** = obligatorio. No se aplica en ninguna pantalla.
- **[R]** = recomendado. Se aplica salvo que la pantalla justifique lo contrario por escrito.
- **[D]** = decisión ya tomada. No se discute en la implementación.

---

## 1. El principio

> **Una página responde a UNA tarea principal.** Si necesitas dos verbos ("ver y editar", "buscar y comprar"), son dos páginas o una página con un drawer.

Se verifica así: **el título de la página es un verbo en imperativo** ("Ver tus inscripciones", "Editar un equipo", "Validar un pase"). Si el título admite dos verbos, la página está mal.

Consecuencia directa: el backend es la autoridad. La UI **presenta** el veredicto (precio, elegibilidad, cupo, estado de pago, permiso); nunca lo calcula ni lo anticipa (`07-guia-para-ui-ux.md` §1 y §5).

---

## 2. Los dos registros

La misma paleta, dos densidades. Esta es la decisión que gobierna todo lo demás.

| | **Placa institucional** | **Consola operativa** |
|---|---|---|
| Dónde | Portada, información, comercial público | Cuenta, administración |
| Superficie | Azul profundo, fotografía a tamaño real, oro | Blanca/tenue, densa, cero ornamento |
| Densidad | Amplia (secciones a pantalla completa) | Alta (fila de 36 px, padding 12–16) |
| Movimiento | 1 momento orquestado por superficie | Solo feedback de acción |
| Tarjetas | Contentidas, con acento de marca | Tablas y filas; **una** tarjeta por idea |
| Regla | Gastar la强度的 boldness en **un** lugar | Gastar la atención en los **datos** |

**[D]** La portada es el único lugar donde el movimiento decorativo es legítimo. En el resto del producto el movimiento **responde a una acción** (`frontend-design` §Restraint).

---

## 3. Color

Los roles y sus valores (claro/oscuro) están en `SH-01` §3.1 y viven en `Aplicacion/frontend/src/app/globals.css`. Aquí van las **reglas de consumo**.

### 3.1 Cómo se consume un color

- **[M]** Un componente pide un **rol**: `bg-primary`, `text-muted-foreground`, `border-border`. Nunca un literal.
- **[M]** Prohibido en componentes: `bg-[#…]`, `text-red-500`, `rgb()`, `hsl()`, `oklch()`. Lo vigila `src/components/__tests__/tokens.test.ts`.
- **[M]** Única excepción: un color **procedente de datos dinámicos** (p. ej. el color de una categoría que publica el backend). Se aplica con `style={{ backgroundColor: valor }}` sobre **un** elemento, acompañado siempre de texto, y se declara en la lista `EXCEPCIONES` del test.
- **[R]** Los gradientes se componen **desde tokens** (`from-primary via-brand-deep-blue to-brand-midnight`), nunca con hex.

### 3.2 Los dos pares que se confunden

Este es el error que ya costó una iteración: **texto sobre superficie clara** y **texto sobre banda oscura** necesitan roles distintos.

| Contexto | Rol correcto | Nunca |
|---|---|---|
| Texto sobre `bg-background` / `bg-card` | `text-foreground` / `text-muted-foreground` | — |
| Texto sobre `bg-surface-inverse` (banda de marca) | `text-surface-inverse-foreground` / `text-surface-inverse-muted` | `text-background` ← **se invisible en oscuro** |
| Texto sobre `bg-primary` | `text-primary-foreground` | `text-white` |

### 3.3 Color de estado = rol del veredicto

El backend publica el veredicto con su etiqueta. La UI solo decide el **color**, y lo decide por **rol**, nunca por el código del backend.

| Veredicto | Rol | Ejemplo de etiqueta (voz del plan 06 §2) |
|---|---|---|
| Verificado / habilitado | `success` | "Beneficio habilitado" |
| Pendiente / en verificación | `warning` | "Pago pendiente", "Pendiente de asignación" |
| Necesita atención | `info` | "Requiere atención" |
| No completado | `muted` + `foreground-muted` | "Pago no completado" |
| Rechazado / revocado | `destructive` | "Pase revocado" |
| Desconocido | `muted` + `foreground-muted` | se renderiza **neutral**, nunca revienta |

- **[M]** Todo estado lleva **color + icono + texto**. El color nunca es el único portador (`frontend/06` §6).
- **[M]** Un estado desconocido se renderiza neutral. Nunca se lanza una excepción por un código no previsto.

### 3.4 La firma de oro

La regla de 2 px en `--accent` acompaña al **eyebrow de sección** y al **ítem activo de navegación**. Es el gesto que hace reconocible el producto sin entrar en el kit de plantilla. Se usa en **las tres familias** (público, cuenta, administración) y **nada más**.

---

## 4. Tipografía

Una familia: **Plus Jakarta Sans**. **Geist Mono** solo para datos (importes, códigos, IDs, marcas de tiempo). **[D]**

| Rol | Tamaño | Peso | Tracking | Uso |
|---|---|---|---|---|
| `display` | `clamp(2.75rem, 6vw, 4.25rem)` | 800 | −0.03em | **Solo** el hero de la portada |
| `h1` | `2rem` (sm: `2.25rem`) | 700 | −0.02em | Título de página |
| `h2` | `1.5rem` | 700 | −0.02em | Título de sección |
| `h3` | `1.125rem` | 600 | −0.01em | Título de bloque/tarjeta |
| `h4` | `1rem` | 600 | 0 | Título de drawer/dialog/pestaña |
| `body` | `0.9375rem` | 400 | 0 | Lectura |
| `body-sm` | `0.875rem` | 400 | 0 | Texto secundario, celda de tabla |
| `eyebrow` | `0.6875rem` | 700 | 0.18em | **Uno** por sección, mayúsculas |
| `label` | `0.8125rem` | 600 | 0.01em | Etiqueta de campo, columna |
| `data` | `0.8125rem` mono | 500 | 0 | Importes, códigos, fechas técnicas |
| `caption` | `0.75rem` | 400 | 0.01em | Metadatos, pie de tabla |

Reglas:

- **[M]** El **eyebrow** identifica la SECCIÓN y aporta información real ("EDICIÓN 2026", "PAGOS", "EQUIPOS"). Máximo uno por sección. No decora cada título.
- **[M]** La **numeración `01 /`** solo donde el contenido **es** una secuencia (el proceso de inscripción: paquete → equipos → cupos → confirmación). En cualquier otro caso, fuera.
- **[M]** Los importes, contadores y columnas numéricas usan `tabular-nums`. Un valor que cambia **no debe reflujar** el layout.
- **[M]** La medida de la prosa: **≤ 72 caracteres** en público, **≤ 65** en consola. `max-w-prose` o equivalente.
- **[R]** Los títulos de página van en `h1` y describen la TAREA, no la entidad: "Tus inscripciones" > "Inscripciones".
- **[M]** Los pesos 900 no se usan: la familia carga 200–800.

---

## 5. Espacio, ritmo y densidad

### 5.1 Escala

| Token | Valor | Uso |
|---|---|---|
| 1 | `0.25rem` | Ajuste interno |
| 2 | `0.5rem` | Gap de icono y texto |
| 3 | `0.75rem` | Gap de controles en línea |
| 4 | `1rem` | Padding de tarjeta, gap de rejilla |
| 6 | `1.5rem` | Padding de panel, gap de bloque |
| 8 | `2rem` | Separación de bloques |
| 12 | `3rem` | Separación de secciones (público) |
| 16 | `4rem` | Separación de secciones (destacada) |

### 5.2 Densidad por registro

| | Contenedor | Fila de tabla | Padding de tarjeta | Gap de rejilla |
|---|---|---|---|---|
| Público | `max-w-[1200px]` | — | `p-6`–`p-8` | `gap-6`–`gap-8` |
| Cuenta | `max-w-[1100px]` | `h-9` (36 px) | `p-4`–`p-5` | `gap-4` |
| Administración | ancho del inset | `h-9` (36 px) | `p-4` | `gap-2`–`gap-3` |

- **[M]** Una columna de tabla nunca baja de 36 px ni sube de 44 px.
- **[M]** En ≤ 768 px, la tabla **no** hace scroll horizontal de página: se apila en filas `label`/`valor`.
- **[M]** El contenedor público **no** mide más de 1200 px: por encima, la línea de texto se vuelve ilegible.

### 5.3 La anatomía de una sección

Una sección de portada tiene **tres** elementos, en este orden y con esta jerarquía:

1. **Eyebrow** — una línea, 11 px, tracking amplio. Identifica la sección.
2. **Título** — `h2`, una o dos líneas. Una fraseaccentuada en el color de acento **solo si aporta información** (el resto del tiempo, ninguna: `frontend-design` advierte contra el "accented word" como tell).
3. **Cuerpo** — la prosa o la composición. Máximo 72 ch.

- **[R]** Las secciones de la portada ocupan `min-h-svh` con `snap-start`: el scroll-snap es lo que hace que la secuencia se sienta dirigida. **Nunca** es global: vive en `(portada)`.
- **[R]** La separación entre secciones de portada es `py-16 md:py-24`. En consola, `gap-4` y poco más: la densidad es la información.

---

## 6. Superficie y elevación

| Nivel | Uso | Tokens |
|---|---|---|
| 0 | Plano sobre el fondo | `bg-background` + `border-border` |
| 1 | Tarjeta, panel, celda destacada | `bg-card` + `border-border` + `shadow-sm` |
| 2 | Superficie flotante (dialog, sheet, popover, command) | `bg-popover` + `shadow-lg` |

- **[M]** Una tarjeta tiene **una** sombra. La jerarquía se construye con **borde + espacio**, no con sombras acumuladas.
- **[M]** El hover de una tarjeta cambia **borde y fondo**, nunca la sombra ni un `translateY`: el desplazamiento vertical en cada hover es un tell de plantilla (`frontend-design`).
- **[M]** No hay una tarjeta dentro de una tarjeta. Si un bloque necesita tres niveles de anidado, es un documento, no una interfaz.
- **[R]** La banda de marca (pie, hero, barra móvil) usa `bg-surface-inverse` con su par inverso de texto.

---

## 7. Componentes

### 7.1 La cabecera de página (todas las páginas)

```
[eyebrow]                       ← una sola vez, identifica la sección
Título de la tarea               ← h1, el verbo en imperativo
Descripción                      ← una línea, máximo 72 ch, responde "qué hago aquí"
                        [acciones] ← a la derecha; en ≤ 768 bajan a una fila propia
```

- **[M]** Máximo **dos** acciones primarias por página. La tercera es un `DropdownMenu`.
- **[M]** Las acciones destructivas o irreversibles van en `alert-dialog` y **no** son el botón principal.
- **[M]** El título va dentro del contenedor de la página, nunca pegado al borde de la ventana.

### 7.2 Botones

- **[M]** Un botón primario por pantalla. `bg-primary` (no gradiente) salvo el CTA de marca.
- **[M]** ÁREA táctil: **44×44 px** en ≤ 768 px (`size-11`), 36×36 (`size-9`) en escritorio.
- **[M]** El icono solo nunca lleva el significado: botón de icono → `aria-label` en español.
- **[M]** Durante el envío: `disabled` + `aria-busy` + texto de estado ("Guardando…"). Nunca doble submit.

### 7.3 Formularios

- **[M]** `GenericForm` en **modo 1 (manual, `children`)**. `contract/smart.md` es explícito.
- **[M]** La etiqueta es **visible**; el placeholder nunca es la etiqueta.
- **[M]** El error va **debajo del campo**, con `role="alert"`, `aria-invalid` y `aria-describedby` apuntando al mensaje.
- **[M]** El texto del error es el del backend o el de Zod. La UI no lo reescribe ni lo traduce.
- **[M]** El foco va al primer campo con error tras un envío fallido (patrón `ErrorSummary`).
- **[R]** Un campo por línea en ≤ 768 px. Dos campos juntos solo cuando el par es inseparable (DNI + tipo de documento).

### 7.4 Tabla operativa (todas las listas del admin)

Un **único** patrón, con la columna de identidad a la izquierda y el estado a la derecha:

```
[buscador] [filtros] [vista]              ← los filtros viven en la URL
┌──────────────────────────────────────────┐
│ IDENTIDAD │ ESTADO │ MÉTRICAS │ FECHA │ ⋯ │  ← ≤ 4 columnas en móvil
└──────────────────────────────────────────┘
Mostrando X a Y de Z · [paginación]         ← servidor, nunca corte local
```

- **[M]** El **veredicto va primero**: la fila se lee por su estado antes que por sus datos (`AdminListaOperativa` del congelado ya lo resolvía así).
- **[M]** La tabla tiene `role="region"` con nombre y `tabindex="0"`: la zona desplazable es alcanzable por teclado.
- **[M]** En ≤ 768 px la tabla se convierte en **tarjetas apiladas** con `label`/`valor`. No hay scroll horizontal de página.
- **[M]** La paginación la gobierna el servidor (`count`/`page`/`page_size`/`total_pages`). El frontend **no** deriva el total.
- **[M]** Cuatro estados obligatorios: carga (skeleton con la forma real), vacío inicial, vacío por filtro (conserva los filtros y ofrece limpiarlos), error recuperable (con "Reintentar", nunca solo un toast).

### 7.5 Detalle operativo

Un mismo patrón para inscripción, equipo, pago y participante:

```
Drawer (sheet) → veredicto primero: estado + causa + siguiente acción
              → luego los datos: hechos en tiles de 2 columnas
```

- **[M]** El drawer nunca es la única copia de la información crítica: la URL guarda el recurso, el drawer es la capa de detalle.
- **[M]** En ≤ 768 px el drawer ocupa el ancho completo y su contenido es desplazable.
- **[M]** La acción irreversible pide **motivo** cuando el motivo importa (`plan 04` §12.4).

---

## 8. Movimiento

| Registro | Dónde | Duración | Qué |
|---|---|---|---|
| **Funcional** | Todo | 120 ms (hover/press) · 200 ms (sheet, tab, toast) | Responde "qué cambió" |
| **Decorativo** | **Solo `(portada)`** | 400–700 ms, escalonado ≤ 3 por bloque | Un único momento orquestado |

- **[M]** En la consola (cuenta y administración) **no hay** animación de entrada. Ninguna.
- **[M]** El scroll-snap solo en `(portada)`.
- **[M]** `prefers-reduced-motion` desactiva **todo**, con una sola regla global en `globals.css` y un hook compartido (`useReducedMotion`) para lo que decide en vez de verse distinto.
- **[M]** Se anima `transform` y `opacity`. Nunca `width`, `height`, `top`/`left`.
- **[M]** Las transiciones declaran sus propiedades: `transition: all` está prohibido.

---

## 9. Iconografía y marcas

- **[M]** **Lucide** para la interfaz. Tamaños: 16 (en texto), 18 (navegación y botones), 20 (cabecera de bloque), 24 (estado vacío), 32+ (rasgo de marca en el hero).
- **[M]** **Nunca emoji como icono.** Un emoji es texto: se anuncia distinto y no se alinea.
- **[M]** Icono decorativo → `aria-hidden="true"` + `focusable="false"`. Icono accionable → `aria-label` en español.
- **[M]** Las marcas sociales (Facebook, Instagram, TikTok) vienen del MCP de iconos (`simple-icons`), no se dibujan a mano, y usan `currentColor` para funcionar en ambos temas.
- **[M]** El escudo y el wordmark son **imágenes** con `alt` real ("Salesianos FEST", "Escudo de los Salesianos"), nunca iconos.
- **[R]** `strokeWidth` 1.75 por defecto; 2.25 en el ítem activo de navegación (contraste de estado, no de color).

---

## 10. Los diez estados

Toda ruta los contempla. La diferencia entre pantallas no es qué estados tienen, sino **qué acción ofrecen** en cada uno.

| Estado | Qué ve | Qué ofrece | Componente |
|---|---|---|---|
| `initial` | La estructura de la página | — | — |
| `loading` | Skeleton **con la forma real** | — | `Skeleton` en `loading.tsx` |
| `empty` | Qué no existe | **La acción que lo crea** | `Empty` |
| `empty por filtro` | Los filtros siguen puestos | **Limpiar filtros** | `Empty` + `Button` |
| `error` | El mensaje del backend | **Reintentar** | `Alert variant="destructive"` |
| `validation` | El error **en el campo** | Corregir y reenviar | `FieldError` + `role="alert"` |
| `permission denied` | Que la cuenta no puede | A quién acudir | `Alert` + `Lock` |
| `success` | Qué cambió y qué sigue | La siguiente acción | `toast` vía `notify` |
| `timeout/retry` | "No responde" | **Reintentar**, sin perder la operación | `Alert` + `RefreshCw` |
| `móvil` | La misma tarea, en una columna | Todo alcanzable sin hover | — |

- **[M]** El mensaje de error **es el del backend**. Se muestra tal cual.
- **[M]** Un error sin acción es un callejón sin salida: todo estado ofrece una salida.

---

## 11. Responsive

Los cinco anchos son obligatorios: **360 · 390 · 768 · 1024 · 1440**.

| Ancho | Público | Cuenta | Administración |
|---|---|---|---|
| 360 / 390 | Menú en `Sheet`; CTA ≥ 44 px | Barra superior con menú de usuario | Sidebar **offcanvas**; tabla → tarjetas; filtros en `Sheet` |
| 768 | Nav horizontal | Contenedor `max-w-[720px]` | Sidebar en **rail de iconos** con tooltip |
| 1024 | Nav + CTA visibles | `max-w-[1100px]`, 2 columnas | Sidebar expandido + cabecera pegajosa |
| 1440 | `max-w-[1200px]` centrado | Ídem, más aire | Sidebar 272 px + tabla al ancho |

- **[M]** Ninguna ruta hace scroll horizontal de página. `overflow-x: clip` en el contenedor y `min-w-0` en los hijos flex.
- **[M]** Ninguna acción depende del `hover` para revelarse. En móvil, la acción de fila es un `DropdownMenu`.
- **[M]** El breakpoint de móvil es 768 (`useIsMobile`), el mismo en todo el producto.
- **[M]** Los diálogos a 360 px son a ancho completo; los formularios largos son **página**, no modal.

---

## 12. Accesibilidad

- **[M]** Contraste: texto normal ≥ **4.5:1**; texto grande y bordes de control ≥ **3:1**. Todos los pares de `SH-01` §3.1 están calculados para cumplirlo.
- **[M]** Foco visible en todos los interactivos: `ring-[3px] ring-ring/50 ring-offset-2`. El `outline` **nunca** se elimina.
- **[M]** Navegación por teclado completa. `Esc` cierra sheet/dialog/drawer/command. **El foco vuelve al disparador** al cerrar.
- **[M]** Skip-link al contenido en las tres familias con chrome.
- **[M]** Las tablas con scroll propio son `role="region"` con nombre accesible y `tabindex="0"`.
- **[M]** Los errores de campo están **asociados** al campo (`aria-describedby`) y anunciados (`role="alert"`).
- **[M]** Todo estado lleva texto, no solo color.
- **[M]** `prefers-reduced-motion` respetado (regla global + hook).
- **[R]** Los datos tabulares se leen en voz alta como tabla real, no como una lista de divs.

---

## 13. Los tells: lo que NO se hace

La lista más corta y la más importante. Cada punto es una razón por la que una pantalla se ve generada.

| ❌ No | ✅ Sí | Por qué |
|---|---|---|
| Rejilla de tarjetas idénticas | Una lista o una tabla con jerarquía | El "SaaS-card kit" |
| Sombra distinta en cada nivel | Una sombra, tres niveles | Ruido visual |
| `translateY(-4px)` en cada hover | Cambia borde y fondo | Movimiento grifo |
| Gradiente decorativo | Gradiente **desde tokens**, con propósito | `frontend-design` |
| Color literal | Rol semántico | Sin pareja en tema oscuro |
| `transition: all` | Propiedades declaradas | Coste de layout |
| Animación de entrada en cada bloque | Un momento orquestado | Fade-up por sección = tell de IA |
| Scroll-snap global | Solo en la portada | Secuestra el scroll de tablas |
| Emoji como icono | Lucide o marca del MCP | El emoji se anuncia distinto |
| `text-white` sobre azul | `text-primary-foreground` | Se rompe en oscuro |
| Texto de relleno | El copy de `frontend/06` §2 o el del backend | Se inventa la verdad |
| Botón deshabilitado sin explicación | Explica qué falta | Callejón sin salida |
| Scroller para un select | `Select` de shadcn | Accesibilidad |
| Icono sin etiqueta | `aria-label` en español | Nombre accesible |
| Fila de tabla que solo se expone en hover | Visible o en `DropdownMenu` | Táctil y teclado |
| `h1` + `h2` + `h3` idénticos | Escala de 4 niveles | Jerarquía |
| Tabla con scroll horizontal en móvil | Tarjetas apiladas | viewport |
| Un modal para una tarea larga | Página con URL recuperable | `frontend/06` §1 |
| Un dashboard con 12 KPIs | Las 5 métricas accionables | `frontend/04` §2 |

---

## 14. Shadcn por familia

Selección cerrada en `SH-04`. Lo que se usa, lo que no, y por qué:

| Familia | Se usa | No se usa | Por qué |
|---|---|---|---|
| Navegación | `sidebar` (ya instalada), `breadcrumb`, `dropdown-menu`, `sheet` | `navigation-menu`, `command` | Un header de 4 destinos no es un mega-menú; la paleta de comandos es una función nueva |
| Lista operativa | `table`, `pagination`, `toggle-group`, `input-group`, `empty`, `skeleton`, `dropdown-menu` | `data-table` (el ejemplo del registry usa la API **v9** de TanStack y el proyecto tiene **v8**) | `GOV-02-SH-04` |
| Detalle | `sheet`, `dialog`, `drawer` | — | Un panel, no dos |
| Formulario | `input`, `label`, `field`, `checkbox`, `radio-group`, `select`, `textarea`, `combobox` | `form` | `GenericForm` es el orquestador (`contract/smart.md`); `form` crearía dos fuentes de verdad |
| Estados | `alert`, `alert-dialog`, `sonner`, `empty`, `skeleton`, `spinner`, `progress` | — | — |
| Comercial | `card`, `carousel`, `badge`, `aspect-ratio`, `accordion`, `dialog` | `input-otp` | Los pases se escanean, no se teclean |
| Marca | `button`, `separator`, `tooltip`, `popover` | — | — |

- **[M]** shadcn es la **capa de primitivas**. La composición es de este proyecto. Un bloque del registry (`dashboard-01`, `login-01`, `preview-*`) **no se instala**: se usa como espécimen y se rehace con el modelo de rutas del plan.
- **[M]** Todo lo que se añade pasa por el MCP de shadcn (o el CLI con `-c Aplicacion/frontend`) y por la revisión de diff: `GOV-02-SH-02` y `GOV-02-SH-07`.

---

## 15. Checklist de entrega de una pantalla

- [ ] El título es un verbo en imperativo y describe **una** tarea.
- [ ] La cabecera sigue la anatomía de §7.1; máximo dos acciones primarias.
- [ ] Ningún color literal; el guard de tokens pasa.
- [ ] La escala tipográfica de §4, sin pesos 900, con `tabular-nums` en los números.
- [ ] La medida de la prosa ≤ 72 ch (público) / ≤ 65 (consola).
- [ ] La densidad corresponde al registro (placa o consola).
- [ ] Los diez estados de §10 están contemplados y cada uno ofrece una salida.
- [ ] Las cinco anchuras de §11: sin scroll horizontal, sin acción que dependa del hover.
- [ ] Teclado completo, foco visible, foco que vuelve al disparador, skip-link.
- [ ] Contraste ≥ 4.5:1 verificado sobre los roles usados.
- [ ] Cero movimiento decorativo fuera de `(portada)`.
- [ ] Los mensajes de error son los del backend, sin reescritura.
- [ ] La tabla (si la hay) tiene `role="region"` con nombre y se apila en ≤ 768 px.
- [ ] shadcn: todo componente nuevo pasó por el MCP y tiene diff revisado.
- [ ] `npx tsc --noEmit` · `npx vitest run` · `npx biome check` en verde respecto de la línea base.

---

## 16. Cómo se aplica: la ficha de cada ruta

Cada ruta que se construya declara, **antes de escribir código**:

| Campo | Contenido |
|---|---|
| Page ID | Del plan (`frontend/01` §2-§3) |
| Tarea | Verbo en imperativo (§1) |
| Registro | Placa institucional o consola operativa (§2) |
| Composición | Wireframe ASCII de escritorio y de móvil (§5.3, §7) |
| Estados | Los diez, con su acción (§10) |
| Componentes | Del catálogo shadcn de §14, con el componente propio si lo hay |
| Tokens | Los roles que usa, y solo esos |
| Responsive | Qué cambia en 360 / 768 / 1024 / 1440 (§11) |
| Accesibilidad | Foco, teclado, nombres, contraste (§12) |
| Copy | De `frontend/06` §2 o del backend. **Nada inventado** |
| Dependencia de datos | Fixture provisional o endpoint. Con su identificador |

Y la construcción sigue la ficha, no la improvisación.

---

## 17. Estado de la aplicación de esta pauta

| Superficie | Estado | Nota |
|---|---|---|
| Portada `/` | **Referencia canónica** | Composición, copy y ritmo del congelado, con el sistema de tokens aplicado |
| Login `/login` · Registro `/registro` | Pendiente | Casi idéntico al anterior: mejora de responsive, foco y contraste |
| Sidebar de administración | Pendiente | Mismo modelo de 3 grupos, con el activo en la firma de oro |
| Las 34 rutas restantes | Pendiente | Una ficha por ruta (§16) antes de escribir código |

**Pendiente de verificación:** la auditoría de las cinco anchuras en navegador, que la pauta exige y que ninguna pantalla puede dar por cerrada sin ella.
