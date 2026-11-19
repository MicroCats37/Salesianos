<task id="ses_e0ed5c18effeGn7f7IOILkxcis" state="completed">
<task_result>
# Salesianos FEST — Brief GOV-02 · Parte A: Sistema visual global y shell

> **Alcance:** sistema de tokens, gramática visual y esqueleto de aplicación para `Aplicacion/frontend/**`.
> **Estado:** brief de diseño (read-only). No se ha modificado ningún archivo.
> **Fuentes normativas:** `contract/next-app-architecture-contract.md`, `contract/smart.md`, `contract/api-wrapper-presenter-contract.md`, `Aplicacion/documentacion/07-guia-para-ui-ux.md`.
> **Fuentes de plan:** `Aplicacion/plan/salesianos-fest-rebuild/frontend/01..06`.
> **Catálogo shadcn:** `Aplicacion/frontend/doc_dev/shadcn-registry-inventory.md` (registry oficial `@shadcn`, style `radix-nova`, 219 ítems, consultado 2026-11-18). Verificado en vivo contra `https://ui.shadcn.com/r/styles/radix-nova/{name}.json`.
> **Nota de método:** el MCP de shadcn no estuvo disponible en esta sesión; la comparación de candidatos se hizo contra el inventario verificado del proyecto y se contrastó por fetch directo contra el registry oficial (`empty.json` y `field.json` descargados y leídos). Toda URL de registry citada es verificable.

---

## A. Diagnóstico de la situación actual

### A.1 Hallazgo raíz: el target no tiene sistema visual propio

`Aplicacion/frontend/src/app/globals.css` y `frontend/src/app/globals.css` son **el mismo archivo** (841 líneas, contenido idéntico línea a línea). El "objetivo editable" no se reconstruyó desde cero: se sembró una copia literal del frontend congelado. En consecuencia, **todo lo que sigueCritica "no copiar" aplica al target también**, no solo al congelado: el target arrastra el `.dark` muerto, los hex hardcodeados, el scroll-snap global y los dos sistemas de radio.

### A.2 Tokens actuales del target — qué está bien

| Elemento | Estado | Veredicto |
|---|---|---|
| Paleta de marca (`#312e8e`, `#25236f`, `#17214b`, `#0c0c1f`, `#f4c64e`, `#22d3ee`, `#6976ff`) | Íntegra en `:root` | **Conservar exacta** |
| `@theme inline` mapeando `--color-*` → variables semánticas | Correcto y compatible con Tailwind v4 | **Conservar el patrón** |
| `@custom-variant dark (&:is(.dark *))` | Correcto | **Conservar** |
| `--radius: 0.75rem` | Presente | **Poblar `@theme`** (hoy es inerte) |
| Plus Jakarta Sans (`--font-sans` + `--font-heading`) y Geist Mono | Cargadas por `next/font` en `app/layout.tsx` | **Conservar**; falta el peso 900 (§A.6) |
| `--sidebar-*` (13 vars) | Presentes y con marca | **Conservar**, cambiar valores (§B.1) |

### A.3 Tokens actuales del target — qué está roto

| # | Defecto | Evidencia | Impacto |
|---|---|---|---|
| D1 | **Bloque `.dark` incompleto.** Le faltan `--secondary`, `--secondary-foreground`, `--popover`, `--popover-foreground`, `--success`, `--success-foreground`, `--warning`, `--warning-foreground`, `--destructive`, `--destructive-foreground`, `--sidebar-accent` sí está, pero `--brand-*`, `--surface-form-amber*`, `--shadow-gold*` heredan valores **de tema claro** | `globals.css:145-171` vs `:root:72-143` | En oscuro, un `<Badge variant="success">` renderiza con前景 de tema claro sobre fondo oscuro |
| D2 | **`ThemeProvider` no montado.** `next-themes` está en `package.json`; el único uso es `useTheme()` dentro de `components/ui/sonner.tsx`, sin proveedor ⇒ devuelve `undefined` ⇒ `theme = "system"` por defecto ⇒ la clase `.dark` **nunca se aplica** | `grep next-themes\|ThemeProvider` → 2 coincidencias, ambas en `sonner.tsx` | Todo el tema oscuro es código muerto |
| D3 | **Definiciones duplicadas.** `--color-gold` se declara dos veces: en `@theme inline` (línea 37, como token) y en un segundo `:root` (línea 675, como var cruda) ⇒ el valor crudo pisa al token. `--radius` sólo existe en `:root` y **nunca entra en `@theme`** ⇒ `rounded-md` usa `--radius-md`, no `--radius` | `globals.css:37`, `:655-695`, `:142` | Dos sistemas de radio conviviendo; el `--radius` "de marca" es decorativo |
| D4 | **`@layer utilities` legacy (v4) junto a `@utility` (v4).** El bloque legacy `:697-841` define `.login-bg`, `.vp-panel`, `.vp-vignette`, `.auth-card`, `.input-pill`, `.label-brand-xs`, `.text-gold`, `.text-gold-light`, `.bg-gold-dim`, `.badge-dot`, `.btn-login`, `.tab-active`, `.feature-pill`, `.carousel-dot*` como CSS plano, fuera del sistema de utilidades | `globals.css:697-841` | Sobreviven sin variantes responsive, sin `data-slot`, con especificidad impredecible y sin tokenización |
| D5 | **Hex literales dentro de `@utility` y `@layer utilities`.** `#1557b8`, `#00bde7`, `#ec4899`, `#6366f1`, `#ffd700`, `#f6f4ee`, `#1f2357`, `#1a1857`, `#211e70` + `rgba(...)` en `hero-gradient`, `hero-gradient-overlay`, `section-gradient-warm`, `card-elevated`, `text-gradient-brand`, `text-gradient-gold`, `text-gradient-festival`, `btn-brand-gradient`, `discipline-card`, `surface-page-gradient`, `input-brand`, `btn-login` | `globals.css:207-214, 255-360, 467-479, 573-594, 697-800` | Los colores de marca se **desvían**: `#00bde7` ≠ `#22d3ee` (cyan), y `text-gradient-festival` introduce magenta `#ec4899` e índigo `#6366f1`, ajenos a la paleta |
| D6 | **`html { scroll-snap-type: y proximity }` + `.event-snap` global.** Es un recurso de landing aplicado a *todas* las rutas | `globals.css:228-243` | El scroll-snap secuestra el scroll de tablas largas, wizards y formularios; además interfiere con el foco por teclado al navegar |
| D7 | **`body { overflow-y: scroll }` global.** Fuerza barra de scroll permanente en todas las rutas | `globals.css:238` | Reserva de canal muerto en móvil y desalineación del `100vh` en contenedores |
| D8 | **`html { scroll-behavior: smooth }` declarado dos veces** (`:231` dentro de `@layer base` y `:535` fuera de capa) | `globals.css:231, 535` | Doble declaración, sin guard de `prefers-reduced-motion` |
| D9 | **Guard de `prefers-reduced-motion` ad-hoc**: dos bloques `@media` distintos con listas de selectores (`597-609` y `644-649`) que enumeran animation-names uno a uno | `globals.css:597-609, 644-649` | Cada animación nueva exige editar CSS global; es el defecto a corregir (§B.6) |
| D10 | **Animaciones infinitas decorativas en el scope global**: `orb-float`, `orb-float-slow`, `festival-ribbon-marquee`, `pulse-slow`, `shine-sweep`, `goldPulse`, `cyanPulse` | `globals.css:362-464, 506-532, 611-649` | Heredadas al shell admin, donde deben ser sobrias |
| D11 | **`transition: all`** en `card-elevated` y `discipline-card` | `globals.css:302, 583` | Transiciona propiedades no animables; coste de layout |
| D12 | **`--brand-cyan-soft` con valor dorado**: `--brand-cyan-soft: #c98a1f` | `globals.css:90` | Bug de paleta: la variante "suave del cyan" es un ocre |
| D13 | **`--input` = `--border`** (mismo valor) | `globals.css:127-128` | El borde de campo y el separador son indistinguibles |
| D14 | **Sin escala tipográfica**: sólo 3 pesos cargados de familia (`--font-sans`/`--font-heading` idénticos) y sin escala de roles | `app/layout.tsx:21-30` | Cada pantalla inventa su propio `text-[13px]` |
| D15 | **Scrollbar y `::selection` con rgba literal** | `globals.css:550-569` |细节 de cromo fuera del sistema de tokens |
| D16 | **`text-eyebrow-brand` con `font-weight: 900`** pero `next/font` sólo carga hasta `800` | `globals.css:216-222` vs `app/layout.tsx:24` | El navegador sintetiza el peso o recae: el eyebrow pierde su carácter |

### A.4 Gap de roles semánticos exigidos

| Rol | ¿Existe en `:root`? | ¿Existe en `.dark`? | Acción |
|---|---|---|---|
| `background` / `foreground` | Sí / Sí | Sí / Sí | Ajustar valor de foreground oscuro (§B.1) |
| `card` / `card-foreground` | Sí / Sí | Sí / Sí | Mantener |
| `popover` / `popover-foreground` | Sí / Sí | **No** | Añadir ambos |
| `secondary` / `secondary-foreground` | Sí / Sí | **No** | Añadir ambos |
| `muted` / `muted-foreground` | Sí / Sí | Sí / Sí | Mantener |
| `accent` / `accent-foreground` | Sí / Sí | Sí / Sí | Mantener |
| `destructive` (+fg) | Sí / Sí | **No** | Añadir ambos |
| `success` (+fg) | Sí / Sí | **No** | Añadir ambos |
| `warning` (+fg) | Sí / Sí | **No** | Añadir ambos |
| `border` | Sí | Sí | Separar de `input` |
| `input` | Sí (idéntico a `border`) | Sí | Dar valor propio |
| `ring` | Sí | Sí | Mantener |
| `chart-1..5` | **No** | **No** | Crear 5 roles con significado de negocio |
| `surface` / `surface-raised` | **No** | **No** | Crear para densidad admin |
| `sidebar-*` (13) | Sí | Sí (parcial) | Re-valorar |
| `--brand-*` | Sí (7, uno corrupto) | Heredado | Separar de semánticos (§B.2) |

### A.5 Estado real del target

| Hallazgo | Evidencia | Consecuencia |
|---|---|---|
| **`src/features/` está VACÍO** | `glob Aplicacion/frontend/src/features/**` → sin resultados | Todo import de `@/features/*` no resuelve |
| **63 imports de `@/features/*` en 34 archivos** (la cifra "24 archivos" del encargo está subestimada; además 1 archivo cae en `src/components-app/**`, excluido por `tsconfig`) | `grep` sobre `Aplicacion/frontend/src` | **`npx tsc --noEmit` falla**; el target no compila. 33 archivos fuera de `components-app` rompen el build: 23 en `components/portada/`, 5 en `components/landing/`, 2 en `components/paquetes/`, 1 en `components/event/`, 2 en `app/` |
| **`tsconfig.json` excluye `src/components-app/**`** (12 archivos: `tables/`, `sidebar/`, `pdf/`, `pages/`, `forms/`) | `tsconfig.json:34-38` | Código muerto heredado del congelado, invisible al typecheck **y** a `biome check src/app src/components` |
| **`src/app/` sólo tiene 6 archivos de ruta** | `glob src/app/**` → `page.tsx`, `layout.tsx`, `informacion/page.tsx`, `(auth)/login/page.tsx`, `(auth)/register/page.tsx`, `(app)/layout.tsx`, + 2 route handlers | Las 36 page IDs del plan no tienen hogar |
| **No existe `loading.tsx`, `error.tsx` ni `not-found.tsx`** en ningún nivel | `glob src/app/**` | El plan 06 §3 exige carga, vacío, error recuperable, 403, 404 |
| **Grupo `(app)` sin ninguna página** — sólo un layout de guarda que redirige a `"/"` | `app/(app)/layout.tsx` | Un grupo huérfano que además confunde la arquitectura de rutas |
| **`ThemeProvider` ausente** | ver D2 | Sin tema oscuro |
| **`GenericForm` sí existe** en el target | `src/components/genericForm/GenericForm.tsx`, `GenericInput.tsx`, `inputs/registry.ts` + 18 inputs, `ui/CardFieldWrapper.tsx` | El sistema Smart Fields **ya está**: no se reconstruye, no se duplica |
| **Infraestructura lista** | `lib/api.ts`, `lib/query-client.ts`, `lib/auth/{index,cookies,actions}.ts`, `lib/server/{jwt,backend-url}.ts`, `hooks/use-mobile.ts` (breakpoint 768), `hooks/callsApi/*`, `hooks/cache/*`, `providers/ReactQueryProvider.tsx` | FND-06 debe cablear, no inventar |
| **Primitivas shadcn instaladas** | 27 en `src/components/ui/`, incl. `sidebar`, `sheet`, `table`, `tabs`, `skeleton`, `sonner`, `tooltip`, `searchable-select` (custom) | No reinstalar; auditar antes de componer |
| **Bug de peso de fuente** | `next/font` carga `["200".."800"]`; `text-eyebrow-brand` usa `font-weight: 900` | El eyebrow no se ve como se diseñó |

### A.6 Invariantes funcionales que el shell NO puede romper

1. El backend es la autoridad de rol y capacidad (§5 de `07-guia-para-ui-ux.md`): ocultar un ítem de navegación es cortesía, el 403 es el control.
2. La redirección de ruta no reemplaza la autorización: un layout de guarda es cortesía, `RequireCapability` decide.
3. Un conjunto de datos ⇒ una clave de caché; una ruta ⇒ un `loading.tsx` por nivel, no spinners por componente (§4.2).
4. Todo mensaje de error visible proviene del backend; la UI no reescribe ni ramifica por código (§4.4).
5. Un endpoint ⇒ un cliente: `lib/api.ts` es el único transporte (§4.1).
6. `app/` sólo enruta y compone; la lógica vive en `features/` (contrato de arquitectura §1).
7. La navegación **no inventa módulos habilitados**: los destinos del plan son conceptuales; la habilitación real la publica el backend.
8. El token de enlace invitado no se persiste en el cliente más de lo necesario; su expiración la aplica el servidor.

---

## B. Sistema visual global

### B.0 Dirección visual (decisión, no menú)

**Concepto: "Institucional nocturno".** La identidad de Salesianos es institucional y nocturna (azul profundo, oro, fiesta). La traducción: la **página pública es una placa institucional** (azul profundo, oro como firma, fotografía de disciplina a tamaño real); el **área operativa es una consola sobria** (blanco/navy, densidad alta, cero ornamento). La misma paleta, dos densidades.

**El gesto único y reconocible: la "firma de oro".** Una regla de 2 px en `--brand-gold` que acompaña (a) al eyebrow de sección y (b) al ítem activo del menú lateral. Un solo elemento, presente en las tres familias (público, cuenta, administración). Es lo que hace el producto reconocible sin entrar en el kits de plantilla.

**Lo que se elimina deliberadamente:** el grid de 3 tarjetas del dashboard congelado; `rounded-[40px]`/`rounded-3xl` como norma; el crema cálido `#f6f4ee` de `surface-page-gradient` (contrasta con el azul institucional y es el tell más obvio de plantilla); el magenta `#ec4899` de `text-gradient-festival`; los orbes flotantes como recurso de portada.

**Regla de Eyebrow:** máximo **uno** por sección, portando información real (categoría del contenido: "EDICIÓN 2026", "PAGOS", "EQUIPOS"), nunca sobre cada tarjeta.
**Regla de Numeración `01 /`:** sólo en contenido que **es** una secuencia (el proceso de inscripción: paquete → equipos → cupos → confirmación, plan 02 SPORT-01). En cualquier otro caso, fuera.

---

### B.1 Mapa de roles semánticos

> Convenciones: `light` = tema claro, `dark` = tema oscuro (`.dark`). Todos los pares están chosen para cumplir **WCAG AA**: texto normal ≥ 4.5:1, texto grande y componentes de UI ≥ 3:1.

#### Roles base y superficies

| Rol (Tailwind) | Significado | Light | Dark | Consumo previsto |
|---|---|---|---|---|
| `--background` → `bg-background` | Superficie raíz de la aplicación | `#f4f6fb` | `#0c0c1f` | `<body>`, fondo de página admin/cuenta |
| `--foreground` → `text-foreground` | Texto principal sobre `background` | `#17214b` | `#f4f6fb` | Títulos, texto de párrafo |
| `--card` → `bg-card` | Superficie elevada de contenido | `#ffffff` | `#16162e` | Tarjetas de contenido, paneles de detalle |
| `--card-foreground` | Texto sobre `card` | `#17214b` | `#f4f6fb` | — |
| `--popover` / `--popover-foreground` | Superficie flotante (menú, popover, combobox) | `#ffffff` / `#17214b` | `#1e1e3c` / `#f4f6fb` | `Popover`, `DropdownMenu`, `Select`, `Tooltip` |
| `--surface` | Superficie de nivel medio (tabla, barra de filtro) | `#eef1f8` | `#12122a` | Cabecera de tabla, `FilterBar`, stripes |
| `--surface-raised` | Superficie de nivel alto (inset del admin, barra superior) | `#ffffff` | `#12122a` | `SidebarInset`, `SiteHeader` |
| `--muted` / `--muted-foreground` | Superficie y texto atenuados | `#f1f5fb` / `#626195` | `#1a1a36` / `#a0a3c4` | Texto secundario, placeholders, filas inactivas |
| `--border` | Separador y borde decorativo | `#dde1ec` | `#2a2a4a` | `border-border`, separadores, `--color-border` |
| `--input` | **Borde de campo** (distinto de `--border`) | `#c9cfdf` | `#3a3a5e` | `border-input` |
| `--field-bg` | Fondo de campo de formulario | `#ffffff` | `#14142b` | `Input`, `Textarea`, `Select` |
| `--field-bg-muted` | Campo deshabilitado / sólo lectura | `#f1f5fb` | `#1a1a36` | `disabled`, `readOnly` |
| `--ring` | Anillo de foco | `#312e8e` | `#8f99ff` | `ring-ring`, `focus-visible:ring-[3px] ring-ring/50` |

#### Roles de marca / acción

| Rol | Significado | Light | Dark | Consumo previsto |
|---|---|---|---|---|
| `--primary` / `--primary-foreground` | Acción principal de marca (inscribirse, guardar, confirmar) | `#312e8e` / `#ffffff` | `#7d88ff` / `#0c0c1f` | `bg-primary text-primary-foreground`, botón primario |
| `--secondary` / `--secondary-foreground` | Acción secundaria marcada (píldora, tag de estado) | `#6976ff` / `#ffffff` | `#5a67e8` / `#ffffff` | `bg-secondary`, chips de filtro activos |
| `--accent` / `--accent-foreground` | Acento de marca: oro | `#f4c64e` / `#17214b` | `#f4c64e` / `#17214b` | `bg-accent`, texto de "firma de oro", `Badge variant="accent"` |

> **Por qué el primario oscuro cambia a `#7d88ff`:** con `#6976ff` sobre `#0c0c1f` la relación es ≈4.4:1, por debajo de 4.5:1. `#7d88ff` da ≈6.3:1 y mantiene el registro "azul institucional claro" del congelado.

#### Roles de estado

| Rol | Significado de negocio | Light | Dark | Consumo previsto |
|---|---|---|---|---|
| `--success` / `--success-foreground` | Confirmado / pagado / habilitado | `#047857` / `#ffffff` | `#34d399` / `#022c22` | `bg-success`, badge "Pago confirmado", "Beneficio habilitado" |
| `--warning` / `--warning-foreground` | Pendiente / requiere atención / por asignar | `#b45309` / `#ffffff` | `#fbbf24` / `#422006` | "Pago pendiente", "Pendiente de asignación", "Incompleto" |
| `--destructive` / `--destructive-foreground` | Error recuperable / acción irreversible | `#dc2626` / `#ffffff` | `#f87171` / `#450a0a` | `bg-destructive`, `Alert variant="destructive"`, `ConfirmActionDialog` |

> El congelado usaba `#ef4444` (rojo Tailwind 500): blanco sobre `#ef4444` da **3.76:1** ⇒ falla AA. Se baja a `#dc2626` (4.83:1).

#### Roles de chart (significado real, no decorativo)

| Rol | Significado | Light | Dark | Dónde se usa |
|---|---|---|---|---|
| `--chart-1` | **Ocupación / volumen principal** (inscripciones, unidades vendidas) | `#312e8e` | `#7d88ff` | Serie principal de cualquier serie temporal |
| `--chart-2` | **Deporte / disciplina** (segunda serie) | `#0e7490` | `#22d3ee` | Distribución por disciplina |
| `--chart-3` | **Inserción / ampliación** (tercera serie) | `#b45309` | `#fbbf24` | Compras de ampliación de cupos |
| `--chart-4` | **Completado / confirmado** | `#047857` | `#34d399` | Estadoscwerts de resolución positiva |
| `--chart-5` | **Atención / pendiente** | `#b91c1c` | `#f87171` | Alertas e incidencias |

> These colors are also the ones used by the status chips, so a chart and a badge never tell different stories. `chart` (recharts) **no se instala** en el MVP (ver §D-8).

#### Roles de navegación lateral

| Rol | Light | Dark |
|---|---|---|
| `--sidebar-background` | `#ffffff` | `#12122a` |
| `--sidebar-foreground` | `#17214b` | `#f4f6fb` |
| `--sidebar-primary` | `#312e8e` | `#7d88ff` |
| `--sidebar-primary-foreground` | `#ffffff` | `#0c0c1f` |
| `--sidebar-accent` | `#eef1f8` (hover/activo suave) | `#1d1d3a` |
| `--sidebar-accent-foreground` | `#17214b` | `#f4f6fb` |
| `--sidebar-border` | `#e4e7f0` | `#282845` |
| `--sidebar-ring` | `#312e8e` | `#7d88ff` |

> **Decisión de elevación:** el sidebar congelado era un gradiente duro `from-[#1f2357] via-[#1a1857] to-[#0c0c1f]` con texto forzado a blanco por selectores `!important`. En el nuevo sistema **el lateral es claro en tema claro** y el azul queda reservado para el ítem activo y la "firma de oro". El producto gana legibilidad operativa y deja de depender de hex en el markup.

#### Tokens de superficie de página

| Token | Light | Dark |
|---|---|---|
| `--surface-page-gradient` | `linear-gradient(180deg, #f4f6fb 0%, #ffffff 38%)` | `linear-gradient(180deg, #0c0c1f 0%, #10102a 38%)` |
| `--brand-gradient-cta` | `linear-gradient(135deg, #312e8e 0%, #25236f 100%)` | mismo |
| `--brand-gradient-cta-hover` | `linear-gradient(135deg, #25236f 0%, #1a1857 100%)` | mismo |

---

### B.2 Tokens de marca vs tokens semánticos

**Dos capas, una regla de consumo.**

| Capa | Prefijo | Naturaleza | ¿Cambia con el tema? | Consumido por |
|---|---|---|---|---|
| **Identidad** | `--brand-*` | Constantes de la marca. No expresan intención de UI | No (salvo variantes oscuras explícitas) | Wordmark, escudo, hero público, "firma de oro", gradiente de CTA |
| **Semántica** | `--primary`, `--surface`, `--muted-foreground`, `--destructive`, `--chart-*`… | Intención de UI. Un componente pregunta "qué rol necesito" | Sí | **Todo componente de shadcn y todo componente propio** |

#### Inventario `--brand-*` definitivo

| Token | Valor | Uso único |
|---|---|---|
| `--brand-gold` | `#f4c64e` | Regla de 2 px, eyebrow, detalle de CTA |
| `--brand-gold-soft` | `#c98a1f` | Texto de oro sobre fondo claro (legible) — **corregir el bug `--brand-cyan-soft`** |
| `--brand-cyan` | `#22d3ee` | Detalle en fondo oscuro: live badge, borde de la "firma" |
| `--brand-navy` | `#17214b` | Texto institucional sobre claro |
| `--brand-blue` | `#312e8e` | Azul institucional (mismo valor que `primary` light) |
| `--brand-blue-dark` | `#25236f` | Estado hover del CTA |
| `--brand-midnight` | `#0c0c1f` | Fondo oscuro de marca (hero, panel de auth) |
| `--brand-indigo` | `#6976ff` | Azul secundario de marca |
| `--brand-gradient-cta` | ver §B.1 | Fondo del CTA píldora |

#### Colapsos del congelado (se eliminan)

| Token heredado | Motivo | Sustituto |
|---|---|---|
| `--institutional` | Duplica `--primary` | `--primary` |
| `--institutional-dark` | Duplica `--brand-blue-dark` | `--brand-blue-dark` |
| `--gold` | Duplica `--brand-gold` | `--brand-gold` |
| `--brand-deep-blue`, `--brand-deep-blue-mid`, `--brand-deep-night` | Nombres no expresivos | `--brand-midnight`, `--brand-blue-dark` |
| `--brand-cyan-soft` | Valor corrupto (dorado) | `--brand-gold-soft` |
| `--surface-form-amber`, `--surface-form-amber-border`, `--shadow-gold`, `--shadow-gold-strong` | Vidrio ámbar del login congelado; el login nuevo usa el panel de marca | `--surface`, `--brand-gold` |
| `--color-gold`, `--color-gold-light`, `--color-gold-dim`, `--color-gold-glow` (2º `:root`) | Duplicados | `--brand-gold`, `--brand-gold-soft` |
| `--color-orb-blue`, `--color-orb-cyan` | Orbes decorativos | — (se eliminan) |
| `--login-bg-*`, `--vp-*`, `--auth-card-*`, `--input-pill-*`, `--btn-login-*` | Tokens de una sola página, en el scope global | tokens del layout `(auth)` (§B.7) |

#### Prohibición de literales y excepción única

**Prohibido en cualquier componente** (`src/components/**`, `src/features/**`):
`bg-[#...]` · `text-[#...]` · `border-[#...]` · `bg-red-500` / cualquier `*-500`/`*-400` de la paleta Tailwind · `rgb(...)` · `hsl(...)` · `rgba(...)` · `oklch(...)` en literales de color.

**Motivo, no gusto:** la paleta Tailwind por defecto introduce colores que no existen en la identidad (verde esmeralda ≠ verde institucional, rojo 500 ≠ rojo de marca, gris 500 ≠ navy atenủado). Y un hex literal no tiene contraparte en tema oscuro: el componente queda atado a un tema.

**Excepción única y documentada.** Se admite color **procedente de datos dinámicos** (p. ej. el color de una categoría devuelto por el backend). Condiciones:
1. Se aplica con `style={{ backgroundColor: valor }}` sobre **un solo elemento** (un swatch), nunca como clase Tailwind.
2. Se acompaña **siempre** de texto o icono: el color nunca es el único portador del significado (plan 06 §6).
3. El elemento va marcado con `// TODO(datos): color dinámico del backend — no tokenizable` y una prueba lo verifica.
4. Si el backend devuelve algo que *parece* un color de marca, se normaliza al token, no al revés.

**Mecanismo de enforcement (FND-06):**
- Prueba Vitest `src/components/__tests__/tokens.test.ts` que recorre `src/components/**` y `src/features/**` y falla si encuentra literales de color fuera de la excepción documentada.
- Revisión con `npx biome check src/app src/components src/lib` (ya en el comando de FND-06).
- Auditoría manual del checklist shadcn (`get_audit_checklist`) en la entrega de FND-06.

---

### B.3 Escala de espaciado, radio, densidad y elevación

#### Radio — UNA escala

| Token | Valor | Uso |
|---|---|---|
| `--radius-sm` | `0.5rem` | Badges, chips, celdas compactas, botones `size="sm"` |
| `--radius-md` | `0.75rem` | **Base**: inputs, botones, selects, menús |
| `--radius-lg` | `1rem` | Tarjetas, paneles, `SidebarInset` |
| `--radius-xl` | `1.5rem` | Exclusivo de superficies de marca (hero, panel de auth, `card-glass`) |
| píldora | `9999px` (`rounded-full`) | **Excepción declarada**: CTA de marca, tags de estado, chips de filtro |
| `--radius` | `0.75rem` | Se mantiene **y se declara en `@theme`** como alias de `--radius-md` |

**Prohibido:** `--radius-2xl`, `--radius-3xl`, `rounded-3xl`, `rounded-[40px]`, radios ad-hoc por componente. El congelado usaba `rounded-[40px]` y `rounded-3xl` como norma: es exactamente el tell de plantilla que se elimina.

#### Espaciado y densidad

| Contexto | Escala | Notas |
|---|---|---|
| Contenedor público | `max-w-[1200px]`, `px-4 sm:px-6 lg:px-10` | El congelado usaba `max-w-[1480px]`: excede la longitud de línea legible (objetivo ≤ 72 ch) |
| Sección pública | `py-16 md:py-24` | |
| Grid público | `gap-4 md:gap-6` | Nunca `gap-10` (aire excessive) |
| Consola admin (densidad alta) | `gap-2`, `gap-3`, `p-3`, `p-4` | Tabla: `px-3 py-2` por celda; fila `h-9` (36 px) |
| Consola admin (densidad media) | `p-5`, `gap-5` | Tarjetas de detalle, paneles |
| Tarea focal (wizard, checkout) | `max-w-[640px]` + `gap-8` | Una columna, sin distracción |
| Móvil / táctil | Altura mínima de control `h-11` (44 px) | `h-11` en ≤ 768 px; `h-10`/`h-9` en escritorio |

**Densidad como token de layout, no de CSS:** dos presets documentados (admin denso, público espacioso) aplicados con utilities locales al componente. No se introduce un `--density-*` global: Tailwind ya es la escala.

#### Elevación — tres niveles

| Nivel | Token | Sombra | Uso |
|---|---|---|---|
| 0 | — | ninguna | Tarjetas planas sobre `bg-background`, separadores |
| 1 | `--shadow-card` | `0 1px 2px rgba(23,33,75,.06), 0 8px 24px -12px rgba(23,33,75,.18)` | `card-elevated` (tarjetas de contenido, panel de detalle) |
| 2 | `--shadow-overlay` | `0 24px 64px -24px rgba(12,12,31,.45)` | `Sheet`, `Dialog`, `Drawer`, `Command`, menús |
| (fuera de escala) | `--shadow-gold` | `0 0 0 1px rgba(244,197,74,.35)` | **Sólo** la "firma de oro" |

> Se elimina la pila de 3 sombras con tinte azul de `card-elevated` y la sombra `0 32px 64px` de `card-elevated-hover` (radios inflados de hover). El hover de tarjeta cambia **borde + fondo**, no sombra ni `translateY(-4px)`: el desplazamiento vertical es el otro tell de plantilla.

---

### B.4 Escala tipográfica

**Una familia: Plus Jakarta Sans.** Ya cargada, ya con 7 pesos, con carácter geométrico-humanista que sostiene "institucional pero cercano". **No se añade una segunda familia de texto**: dos familias en un producto con una sola voz verbal restan carácter y suman una petición de fuente. **Geist Mono es la única excepción y ya existe**: sólo para datos (códigos, importes, identificadores, marcas de tiempo, SKU) — nunca para texto corrido.

| Rol | Tamaño | Peso | Tracking | Line-height | Uso |
|---|---|---|---|---|---|
| `display` | `clamp(2.75rem, 6vw, 4.25rem)` | 800 | `-0.03em` | 1.05 | Título del hero (sólo público) |
| `h1` | `2rem` | 700 | `-0.02em` | 1.2 | Título de página (`/mi-cuenta`, `/administracion`) |
| `h2` | `1.5rem` | 700 | `-0.02em` | 1.25 | Título de sección |
| `h3` | `1.125rem` | 600 | `-0.01em` | 1.35 | Título de tarjeta / bloque |
| `h4` | `1rem` | 600 | `0` | 1.4 | Título de drawer / diálogo / pestaña |
| `body` | `0.9375rem` (15) | 400 | `0` | 1.6 | Texto de lectura |
| `body-sm` | `0.875rem` (14) | 400 | `0` | 1.55 | Texto secundario, celda de tabla |
| `eyebrow` | `0.6875rem` (11) | **700** | `0.18em` | 1.2 | `text-eyebrow-brand` — mayúsculas, **uno por sección** |
| `label` | `0.8125rem` (13) | 600 | `0.01em` | 1.4 | Etiqueta de campo, columna de tabla |
| `data` | `0.8125rem` (13) | 500 | `0` | 1.4 | Geist Mono: importes, códigos, IDs, fechas técnicas |
| `caption` | `0.75rem` (12) | 400 | `0.01em` | 1.45 | Metadatos, notas al pie, pie de tabla |

**Correcciones al congelado:**
- `text-eyebrow-brand` pasa de `0.625rem / 900 / 0.3em` a `0.6875rem / 700 / 0.18em`. El tracking de 0.3 em a 10 px es ilegible y es el tell de "label sobre todo"; 11 px / 0.18 em sigue siendo inequívocamente un eyebrow y cumple contraste. **El peso 900 además no está cargado** (D16).
- `label-brand` del congelado (`0.875rem / 600`) pasa al rol `label` de 13 px para que etiqueta y campo compartan altura optical.
- `tabular-nums` en todo importe, contador y columna numérica (`font-variant-numeric: tabular-nums`).

**Longitud de línea:** ≤ 72 ch en prosa pública; ≤ 65 ch en cuerpo de consola.

---

### B.5 Escala de iconografía

- **Estándar:** `lucide-react` (ya instalado; `iconLibrary: "lucide"` en `components.json`). Sin excepciones.
- **Tamaños:** `16` (dentro de texto y celdas) · `18` (ítems de navegación, botones) · `20` (cabeceras de bloque) · `24` (estados vacíos) · `32+` (rasgo de marca en hero).
- **Grosor:** `strokeWidth` 1.75 por defecto; 2.25 en el ítem activo de navegación (contraste de estado, no color).
- **Reglas duras:**
  1. **Sin emoji como icono.** Los emoji son texto: seAnnouncean de forma distinta y no se alinean.
  2. **Icono decorativo** → `aria-hidden="true"` y `focusable="false"`. Nunca `aria-label` en un icono que no significa nada.
  3. **Icono accionable** (botón sólo-icono) → `aria-label` en español en el `<Button>` (`aria-label="Cerrar sesión"`), `type="button"`, y área táctil ≥ 44 px en móvil (`size-11`) / ≥ 36 px en escritorio (`size-9`).
  4. **Icono + texto** → el texto es el nombre accesible; el icono es `aria-hidden`.
  5. **El icono nunca es el único portador de estado**: todo estado lleva texto (plan 06 §6).
  6. **Marca ≠ icono:** el wordmark (`/images/brand.png`, `/images/brand2.png`) y el escudo (`/images/logo.jpeg`, `/images/logo-oficial-salesianos-2002.jpeg`) son `<Image>` con `alt` real ("Salesianos FEST" / "Escudo de los Salesianos"); no se sustituyen por lucide ni se repiten como badge decorativo.
  7. Los iconos de disciplina (`fulbito-varones.webp`, `fulbito-dam.webp`, `voley-mixto.webp`, `basket-varones.webp`) son **fotografías**, no iconos.

---

### B.6 Política de movimiento

**Dos_REGISTROS, con reglas distintas.**

| Registro | Dónde | Duración | Easing | Qué se anima |
|---|---|---|---|---|
| **Funcional** (feedback de la acción) | Todo el producto | `120 ms` (hover/press) · `200 ms` (apertura de sheet/dialog/drawer, indicador de pestaña, expansión de fila, toast) | `cubic-bezier(0.2, 0, 0.2, 1)` | Sólo `transform` y `opacity`. Responde "qué cambió" |
| **Decorativo** (revelado de contenido) | **Sólo `(public)`** | `400–700 ms`, entrada escalonada ≤ 3 elementos por bloque | `cubic-bezier(0.16, 1, 0.3, 1)` | Una sola secuencia orquestada por sección. **Nunca** un fade-up en cada tarjeta |

**Prohibiciones:**
- Animación infinita en `(cuenta)` y `(administracion)`. Se eliminan del scope global `orb-float`, `orb-float-slow`, `festival-ribbon-marquee`, `pulse-slow`, `shine-sweep` y `goldPulse`/`cyanPulse` (D10).
- `transition: all` (D11) → se declaran propiedades explícitas.
- Animar `width`/`height`; se usa `grid-template-rows` o `transform`.
- Animación que bloquea la lectura: el contenido crítico aparece sin animación tras 300 ms.

**Guard compartido (reemplaza D9):** una única regla global en `globals.css`, al final del archivo:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

**Hook compartido para animación por JS:** `src/hooks/system/useReducedMotion.ts` (a crear en FND-06) devuelve `boolean` y se consume desde los componentes que animan con JS/GSAP. **No se escribe un `matchMedia` ad-hoc por componente** — ése es el defecto del frontend congelado (dos listas de selectores que enumeran animation-names).

**Smooth scroll:** `scroll-behavior: smooth` se acota a la navegación por anclas de `(public)` (clase `.anchor-scroll` en el layout público) y no es global (D8); bajo `prefers-reduced-motion` se desactiva por la regla anterior.

**Foco (parte del movimiento):** el `ring` aparece con transición de `120 ms` en `opacity`, nunca un `outline` que "salte".

---

### B.7 Superficies de formulario

**Superficies:**

| Contexto | Fondo | Borde | Texto |
|---|---|---|---|
| Campo normal | `--field-bg` (`#ffffff` / `#14142b`) | `--input` (`#c9cfdf` / `#3a3a5e`) | `--foreground` |
| Campo en superficie elevada | `--card` | `--input` | `--card-foreground` |
| Campo deshabilitado / sólo lectura | `--field-bg-muted` | `--border` | `--muted-foreground` |
| Campo inválido | `--field-bg` | `--destructive` | etiqueta en `--destructive` |
| Campo con foco | `--field-bg` | `--ring` + anillo exterior | `--foreground` |

**Foco visible (una sola especificación global):**
- `ring-[3px] ring-ring/50 ring-offset-2 ring-offset-background`, aplicado por `focus-visible:`.
- `outline` **nunca** se elimina; para elementos que no soportan `ring` (enlaces dentro de prosa, `summary`), se usa `outline-2 outline-offset-2 outline-ring`.
- Contraste del anillo sobre `background` ≥ 3:1 (medido: `#312e8e` sobre `#f4f6fb` ≈ 8.6:1; `#8f99ff` sobre `#0c0c1f` ≈ 6.4:1).

**Estado de error:**
1. El campo recibe `aria-invalid="true"` y `aria-describedby="<id>-error"`.
2. El mensaje se renderiza **inmediatamente debajo del campo**, con `role="alert"`, en `--destructive`, 13 px (rol `label`).
3. **El texto del error viene de Zod o del backend.** La UI no reescribe, no traduce, no ramifica por código (07 §4.4). Si el parser 422 de Django sigue sin existir (brecha FE-12 documentada), se muestra el mensaje agregado y **no** se simula el mapeo por campo en el componente (07 §4.5).
4. Regla del proyecto (04 §12): el mensaje explica la causa y la siguiente acción ("Ya participa en fútbol de esta edición", "6 jugadores registrados; necesita al menos 7").
5. Existe un patrón `ErrorSummary` (resumen de errores al inicio del formulario) que además lleva el foco al primer campo con error — **sólo** cuando hay envío, no en cada tecleo.

**Altura y área táctil:** campo ≥ 40 px en escritorio, ≥ 44 px en ≤ 768 px. Etiqueta siempre visible (nunca placeholder como etiqueta).

**Botón de envío:** deshabilitado durante el envío (`disabled` + `aria-busy`), con texto de estado ("Guardando…") y sin doble submit (plan 06 §3.5).

---

## C. Arquitectura del shell (para FND-06)

### C.1 Route groups propuestos

Raíz: `Aplicacion/frontend/src/app/**`. `app/` es **sólo routing** (contrato §1). Los grupos de ruta no alteran la URL.

```
src/app/
├── layout.tsx                          # raíz: fuentes, <html lang="es">, AppProviders
├── globals.css                         # tokens (B)
├── not-found.tsx                       # 404 global
├── error.tsx                           # error boundary global (client)
│
├── (public)/                           # ── VISITANTE ──────────────────────────
│   ├── layout.tsx                      # header público + <main id="contenido"> + footer
│   ├── loading.tsx  error.tsx  not-found.tsx
│   ├── page.tsx                        # PUB-01  /
│   ├── informacion/page.tsx            # PUB-02  /informacion
│   ├── pases/
│   │   ├── page.tsx                    # PASS-01 /pases
│   │   └── gestionar/
│   │       ├── layout.tsx              # chrome mínimo (enlace privado)
│   │       └── [token]/page.tsx        # PASS-02 /pases/gestionar/[token]
│   ├── tienda/
│   │   ├── page.tsx                    # SHOP-01 /tienda
│   │   ├── [slug]/page.tsx             # SHOP-02 /tienda/[slug]
│   │   └── pedidos/
│   │       ├── layout.tsx              # chrome mínimo
│   │       └── [token]/page.tsx        # SHOP-03 /tienda/pedidos/[token]
│   └── recuperar-compra/page.tsx        # REC-01 /recuperar-compra
│
├── (auth)/                             # ── ANÓNIMO AUTENTICÁNDOSE ────────────
│   ├── layout.tsx                      # split brand panel + panel de formulario
│   ├── loading.tsx  error.tsx
│   ├── login/page.tsx                  # AUTH-01 /login
│   └── registro/page.tsx               # AUTH-02 /registro
│
├── (cuenta)/                           # ── RESPONSABLE ───────────────────────
│   ├── layout.tsx                      # top bar esbelta + contenedor de tarea
│   ├── loading.tsx  error.tsx  not-found.tsx
│   ├── mi-cuenta/page.tsx              # ACCOUNT-01 /mi-cuenta
│   ├── mis-inscripciones/
│   │   ├── page.tsx                    # ACCOUNT-02 /mis-inscripciones
│   │   └── [id]/page.tsx               # ACCOUNT-03 /mis-inscripciones/[id]
│   ├── mis-compras/
│   │   ├── page.tsx                    # ACCOUNT-04 /mis-compras
│   │   └── [id]/page.tsx               # ACCOUNT-05 /mis-compras/[id]
│   └── inscripcion/
│       ├── layout.tsx                  # layout de tarea: una columna + progreso
│       └── page.tsx                    # SPORT-01 /inscripcion
│
└── (administracion)/                   # ── ADMINISTRADOR ──────────────────────
    ├── layout.tsx                      # SidebarProvider + Sidebar inset + SidebarInset
    ├── loading.tsx  error.tsx  not-found.tsx
    └── administracion/
        ├── page.tsx                    # ADM-01 /administracion
        ├── ediciones/page.tsx          # ADM-02
        ├── personas/page.tsx           # ADM-03
        ├── usuarios/page.tsx           # ADM-04
        ├── inscripciones/
        │   ├── page.tsx                # ADM-05
        │   └── [id]/page.tsx           # ADM-06
        ├── equipos/
        │   ├── page.tsx                # ADM-07
        │   └── [id]/page.tsx           # ADM-08
        ├── participantes/page.tsx       # ADM-09
        ├── competencias/
        │   ├── page.tsx                # ADM-10
        │   ├── agenda/page.tsx         # ADM-13
        │   └── [id]/
        │       ├── page.tsx            # ADM-11
        │       └── cuadro/page.tsx     # ADM-12
        ├── pagos/page.tsx              # ADM-14
        ├── pases/
        │   ├── page.tsx                # ADM-15
        │   └── validar/page.tsx        # ADM-16
        ├── marketplace/
        │   ├── page.tsx                # ADM-17
        │   ├── inventario/page.tsx     # ADM-19
        │   ├── entregas/page.tsx       # ADM-20
        │   └── productos/[id]/page.tsx # ADM-18
        ├── patrocinadores/page.tsx     # ADM-21
        └── validaciones/page.tsx       # ADM-22
```

**Cobertura de los 36 page IDs:** PUB-01/02 ✔ · AUTH-01/02 ✔ · ACCOUNT-01..05 ✔ · SPORT-01 ✔ · PASS-01/02 ✔ · SHOP-01/02/03 ✔ · REC-01 ✔ · ADM-01..22 ✔ (22/22 enumerados arriba).

**Decisiones de agrupación y su porqué:**
- **`(public)`** incluye las rutas de enlace privado (`/pases/gestionar/[token]`, `/tienda/pedidos/[token]`): son de **visitante invitado**, no de cuenta. Un `layout.tsx` anidado en `gestionar/` y `pedidos/` les da chrome mínimo (logo + salida) sin barra de sesión.
- **`(auth)`** separado de `(public)`: el login no debe heredar el header público con CTA de inscripción (bucle de navegación) ni el pie.
- **`(cuenta)`**: cuenta del responsable. La barra superior es esbelta; **no** hay sidebar. Motivo: el responsable tiene 5 destinos y una tarea dominante; un sidebar de 22 ítems sería ruido. La navegación de cuenta va en el menú de usuario + accesos en la propia página (`/mi-cuenta` es el hub).
- **`(cuenta)/inscripcion/`**: sub-layout de tarea con **una columna** y barra de progreso del wizard (plan 02 SPORT-01, 4 etapas). Es una pantalla de foco, no un dashboard.
- **`(administracion)`**: único lugar con sidebar. Contenido en `SidebarInset` con `header` pegajoso.
- **Se elimina `(app)/`**: el grupo actual no tiene ninguna página y su layout de guarda (redirige a `"/"`) es un esqueleto provisional. Se renombra a `(cuenta)` + `(administracion)` con guardas propias. **PROVISIONAL**: mientras el backend no congele la política de redirección, ambos grupos con sesión ausente redirigen a `/login?next=<ruta>` (respeta `lib/post-auth-redirect.ts`, ya presente).

**Contrato de nombres de ruta:** todas las rutas se declaran en **una** constante compartida `src/lib/routes.ts` (objeto por familia + helper `href`). Motivo: el plan 01 declara las rutas como *propuestas*; renombrar 36 rutas de otro modo es una búsqueda-reemplazo en el markup.

### C.2 Layouts

| Layout | Estructura (slots) | `loading.tsx` | `error.tsx` | `not-found.tsx` |
|---|---|---|---|---|
| **`(public)/layout.tsx`** | `<a class="skip-link" href="#contenido">Saltar al contenido</a>` → `SiteHeader` (wordmark + nav + CTA marca) → `<main id="contenido">{children}</main>` → `SiteFooter` (wordmark, escudo, enlaces legales) | Skeleton del armazón público: header + 3 bloques de contenido con la altura del bloque real | `ErrorState` con mensaje del backend + botón "Reintentar" (client component con `reset()`) | Enlace privado inválido/expirado: copy neutro, sin revelar existencia |
| **`(auth)/layout.tsx`** | ≥ 1024: dos columnas — panel de marca (fondo `--brand-midnight`, wordmark + escudo + copy de la edición) y panel de formulario (`max-w-[440px]`). < 1024: una columna con wordmark arriba | Skeleton del formulario (marca + 2 campos + botón) | Formulario con estado de error en línea | — |
| **`(cuenta)/layout.tsx`** | Barra superior esbelta (wordmark · contexto de edición · menú de usuario) → `<main class="max-w-[1100px]">{children}</main>`. Sin sidebar | Skeleton de cabecera + 2–3 tarjetas de tarea | Error con "Reintentar" y enlace a `/mi-cuenta` | Registro no encontrado: "No encontramos esta inscripción" + volver a la lista |
| **`(cuenta)/inscripcion/layout.tsx`** | Cabecera de tarea: "← Volver" + nombre de la edición + barra de progreso del wizard → `<main class="max-w-[640px]">` | Skeleton de la etapa actual | Error de etapa con "Volver al paso anterior" | — |
| **`(administracion)/layout.tsx`** | `SidebarProvider` → `Sidebar` (inset, colapsable a iconos) con grupos → `SidebarInset` → `header` pegajoso (breadcrumb + contexto de edición + menú de usuario) → `<main class="p-4 lg:p-6">{children}</main>` | Skeleton: barra lateral + cabecera + 6 filas de tabla | Error con "Reintentar" + enlace a `/administracion` | Registro admin no encontrado: mensaje + volver al listado |
| **`app/not-found.tsx`** | 404 global: marca + "Página no encontrada" + 3 enlaces útiles (Portada / Mi cuenta / Administración si hay sesión) | — | — | ✔ |
| **`app/error.tsx`** | Boundary global de error (client) con `reset()` y `digest` visible en modo desarrollo | — | ✔ | — |

**Reglas:**
1. `loading.tsx` **existe en cada grupo** y refleja la forma real del contenido (alto de fila, número de columnas), no un spinner genérico (plan 06 §3.1).
2. `error.tsx` es un **Client Component** (necesita `reset()`); distingue 401/403/404/409/422/5xx por el estado HTTP que propaga `ApiQueryError` (07 §6, patrón `admin.http.service.ts`).
3. `not-found.tsx` de grupo se usa para `notFound()` dentro de ese grupo; el 404 global vive en `app/`.
4. **Ninguna página implementa su propio spinner de carga**: la carga la cubre `loading.tsx` + `QueryClient` (evita el anti-patrón `useState`+`useEffect` del contrato §8).

### C.3 Navegación

#### Modelo por actor

| Actor | Grupo | Destinos visibles | treatment |
|---|---|---|---|
| **Visitante** | `(public)` | Inicio `/`, Información `/informacion`, Pases `/pases`, Tienda `/tienda` (sólo si el módulo está habilitado), "Iniciar sesión" | Header horizontal en ≥ 1024; en < 1024, `Sheet` con el mismo contenido. CTA primario = "Inscribirse" (`btn-brand-gradient` + `btn-shine`, píldora) |
| **Responsable** | `(cuenta)` | Mi cuenta, Mis inscripciones, Mis compras, Nueva inscripción; + "Administración" sólo si el backend confirma `es_admin` | Barra superior esbelta + `DropdownMenu` de usuario. Sin sidebar |
| **Administrador** | `(administracion)` | 22 destinos conceptuales agrupados en 3 secciones desplegables: **Deportivo** (Resumen, Ediciones, Inscripciones, Equipos, Participantes, Competencias), **Ventas y entradas** (Pagos, Pases, Ingreso, Tienda, Patrocinadores), **Configuración y personas** (Personas, Usuarios, Validaciones) | Sidebar inset, colapsable a iconos, grupos plegables |

#### Reglas de la navegación

1. **Ubicación actual:** `SidebarMenuButton isActive` con la regla del congelado: una entrada está activa si la ruta actual es la entrada **o un descendiente**, y cuando varias coinciden gana **la más específica** (`adminSeccionActiva`). Se reutiliza el mismo helper, no una reimplementación.
2. **Indicador de activo = "firma de oro"**: regla de 2 px `--brand-gold` a la izquierda del ítem activo + `text-sidebar-accent-foreground`. Un único lenguaje visual para los tres grupos.
3. **Indicador de ruta actual en el subárbol:** `breadcrumb` (padrón shadcn, ya instalado) en el `header` del admin y de la cuenta; en móvil se reduce al último segmento.
4. **La navegación no inventa módulos habilitados.** Los 22 destinos son *conceptuales* (plan 04 §1). El filtro real lo publica el backend; hasta que el catálogo esté congelado, el shell renderiza la lista del plan **sin** flags inventados y con las capacidades ya conocidas como único filtro. Ver §F-Q2/Q3.
5. **Ocultar ≠ autorizar.** El filtro por capacidad es cortesía; el 403 del backend es el control (07 §5).
6. **Responsive:** `Sidebar` con `collapsible="offcanvas"` por debajo de `md` (768) → se abre como `Sheet` con foco atrapado y cierre por `Esc`; `collapsible="icon"` en `md`–`lg`; expandido en `≥ lg` (1024). El patrón de `sidebar` shadcn ya resuelve offcanvas ↔ desktop; **no** se construye un drawer propio.
7. **Foco y teclado:** skip-link al inicio del contenido; `Tab` recorre los destinos en orden de lectura; `Esc` cierra sheet/dialog/drawer/command; el foco **vuelve al disparador** al cerrar; `SidebarRail` es un botón con `aria-label`.
8. **Sin hover-dependencia:** ningún destino depende de `hover` para revelarse (04 §12.6). En móvil, el menú se abre con un botón ≥ 44 px.

### C.4 Proveedores

#### Estado real

| Provider | ¿Existe? | Ubicación | Nota |
|---|---|---|---|
| Query client | ✔ | `src/providers/ReactQueryProvider.tsx` | `QueryClientProvider` + `HydrationBoundary` + `configureToast(toast.error, toast.success)` |
| Tooltip | ✔ | montado **inline** en `app/layout.tsx:67` | Falta moverlo al árbol de providers (§C.4.2) |
| Toast (sonner) | ✔ | `app/layout.tsx:68`, `components/ui/sonner.tsx` | `sonner.tsx` llama `useTheme()` **sin** ThemeProvider → el tema del toast es incorrecto |
| **Tema** | ✘ | — | `next-themes` instalado, sin montar → **`.dark` nunca se aplica** (D2) |

#### Árbol de providers (orden y porqué)

```
<html lang="es" class="<fuentes>" suppressHydrationWarning>
  <body>
    <AppProviders>                                   // 'use client' — src/providers/AppProviders.tsx
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <QueryClientProvider client={queryClient}>   // src/providers/ReactQueryProvider.tsx (existente)
          <TooltipProvider delayDuration={200} skipDelayDuration={300}>
            <Toaster position="bottom-right" richColors closeButton />
            {children}
          </TooltipProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </AppProviders>
  </body>
</html>
```

**Orden justificado:**
1. `ThemeProvider` **por fuera**: aplica `class="dark"` en `<html>` antes del pintado; `Toaster`/`sonner` lee `useTheme()` y necesita estar dentro.
2. `QueryClientProvider` antes de todo lo que consume hooks de datos; mantiene el estado de servidor durante la navegación.
3. `TooltipProvider` innermost: los tooltips son de nivel de hoja; `delayDuration={200}` evita el parpadeo al pasar el puntero.
4. `Toaster` como hermano de `{children}`, no ancestro: las notificaciones no deben envolver el árbol.

**Responsabilidades de FND-06 (permitido)**
- Crear `src/providers/AppProviders.tsx` con el árbol anterior.
- Montar `ThemeProvider` con `attribute="class"`, `defaultTheme="system"`, `enableSystem`, `disableTransitionOnChange`.
- Mover `TooltipProvider` y `Toaster` al árbol.
- Crear `src/hooks/system/useReducedMotion.ts`.
- Crear `src/lib/routes.ts` (constante única de rutas).
- Crear `src/app/**` (grupos, layouts, `loading/error/not-found`).
- Reescribir `src/app/globals.css` con los tokens de §B.
- Instalar las primitivas de §C.5 y componer el shell (`SiteHeader`, `SiteFooter`, `AdminSidebar`, `AccountTopbar`).
- Crear `src/components/__tests__/tokens.test.ts` (guard de literales) y pruebas del shell.

**Responsabilidades que FND-06 NO puede tocar**
- `lib/api.ts` (transporte real: URL base, interceptores, refresco de token) — sólo puede consumirlo.
- `lib/auth/**` (cookies, `getUserSession`) — la cadena de autoridad; puede *llamarla*, no reescribirla.
- Cualquier esquema Zod de respuesta (espejo 1:1 del backend) o payload de mutación.
- Endpoints de dominio, catalogueo de módulos, reglas de elegibilidad/capacidad/precio/pago.
- `Aplicacion/backend/**`, `contract/**`, `plan/**`, `Aplicacion/documentacion/**`, `Aplicacion/task/**`.

**Límite de la navegación admin:** FND-06 puede leer la sesión y *ocultar* destinos; no puede crear un endpoint de "módulos habilitados" ni un proxy de autorización.

### C.5 Inventario de primitivas shadcn a instalar

**Ya instaladas (27) — no reinstalar:** avatar, badge, breadcrumb, button, calendar, carousel, checkbox, collapsible, dialog, dropdown-menu, input, label, popover, radio-group, scroll-area, searchable-select (custom), select, separator, sheet, sidebar, skeleton, sonner, table, tabs, textarea, tooltip.

**Faltantes del inventory oficial que hacen falta** — de las 64 primitivas verificadas:

#### Instalar en FND-06 (compartidas por todas las familias de ruta)

| Comando | Primitiva | Justificación en una frase |
|---|---|---|
| `npx shadcn@latest add @shadcn/empty -c Aplicacion/frontend` | `empty` | Estado vacío oficial exigido por plan 06 §3.2; bloque compuesto (`Empty`/`EmptyTitle`/`EmptyDescription`/`EmptyContent`) que cubre "vacío inicial" y "sin resultados de filtros" con un solo patrón. Verificado en el registry (`empty.json`) |
| `npx shadcn@latest add @shadcn/item -c Aplicacion/frontend` | `item` | Patrón de fila para listados (`Item`/`ItemMedia`/`ItemContent`/`ItemTitle`/`ItemDescription`); base de las tablas de administración y de las listas de cuenta, donde el patrón "fila" es transversal |
| `npx shadcn@latest add @shadcn/spinner -c Aplicacion/frontend` | `spinner` | Feedback de proceso en curso con indicador no bloqueante; plan 06 §3.5 "progreso verídico sin inventar tiempos" |
| `npx shadcn@latest add @shadcn/progress -c Aplicacion/frontend` | `progress` | Barra de progreso del wizard de inscripción (SPORT-01, 4 etapas) y de tareas multipaso en admin |
| `npx shadcn@latest add @shadcn/alert -c Aplicacion/frontend` | `alert` | Mensaje contextual en línea (módulo no habilitado, error recuperable, aviso de cierre de modificación); `variant="destructive"` para el estado de error |
| `npx shadcn@latest add @shadcn/alert-dialog -c Aplicacion/frontend` | `alert-dialog` | Confirmación de operaciones irreversibles/sensibles (retirar participante, anular compra, revocar pase); plan 04 §12.4 exige confirmar con efecto y motivo |
| `npx shadcn@latest add @shadcn/pagination -c Aplicacion/frontend` | `pagination` | Paginación de todas las listas operativas (admin, tienda, compras); plan 06 §1 exige **un único patrón** de tabla con paginación |
| `npx shadcn@latest add @shadcn/toggle-group -c Aplicacion/frontend` | `toggle-group` (+ `toggle`) | Filtros segmentados por estado (PENDIENTE/CONFIRMADO…) y selector de vista; es el patrón natural para los vocabularios de estado del backend |
| `npx shadcn@latest add @shadcn/field -c Aplicacion/frontend` | `field` (+ `label`, `separator` ya instalados) | Primitiva **presentacional** de campo; se adopta como capa de render del `DefaultFieldWrapper` de `GenericForm` (label + descripción + `FieldError` con `role="alert"`), sin sustituir la lógica de Smart Fields (ver §D-3) |
| `npx shadcn@latest add @shadcn/drawer -c Aplicacion/frontend` | `drawer` | Panel lateral móvil para el "detalle de encuentro" (plan 05 §3) y el detalle de inscripción/compra; el `sheet` ya instalado cubre escritorio, `drawer` cubre móvil con un gesto coherente |
| `npx shadcn@latest add @shadcn/command -c Aplicacion/frontend` | `command` (+ `dialog`, `input-group`) | Paleta de comandos: navegación global del admin y búsqueda de personas/equipos/competencias por teclado; depend de `input-group` |
| `npx shadcn@latest add @shadcn/input-group -c Aplicacion/frontend` | `input-group` | Input con addon/prefijo (buscador con icono, campo con sufijo); dependencia de `command` |

#### Instalar por familia de ruta (UI-01..05), NO en FND-06

| Comando | Primitiva | Familia | Justificación |
|---|---|---|---|
| `npx shadcn@latest add @shadcn/accordion -c Aplicacion/frontend` | `accordion` | UI-01 (público) / UI-05 | PUB-02 organiza reglamento, cronograma y categorías por temas con anclas reales (plan 02 PUB-02) |
| `npx shadcn@latest add @shadcn/aspect-ratio -c Aplicacion/frontend` | `aspect-ratio` | UI-02 / UI-03 | Galería de imágenes de producto (SHOP-02) y de disciplinas, sin salto de layout |
| `npx shadcn@latest add @shadcn/switch -c Aplicacion/frontend` | `switch` | UI-04 (admin) | Habilitar/deshabilitar un módulo de la edición (ADM-02) y activar/desactivar cuentas (ADM-04) |
| `npx shadcn@latest add @shadcn/combobox -c Aplicacion/frontend` | `combobox` | UI-04 (a decidir) | Ya existe `searchable-select` local; sólo si el filtro administrativo necesita multi-selección con búsqueda |
| `npx shadcn@latest add @shadcn/chart -c Aplicacion/frontend` | `chart` | UI-04 (a decidir) | `recharts`. **No en el MVP**: plan 04 §2 prohíbe "decenas de KPIs"; sólo si aparece una serie temporal real |

#### NO instalar (decisión)

| Item | Motivo |
|---|---|
| `form` | `Form` de shadcn es un binding de `react-hook-form` (`FormProvider` + `useFormContext`). `GenericForm` **ya es** el orquestador de RHF del proyecto (`contract/smart.md`). Instalar `form` crea dos fuentes de verdad del estado del formulario. Ver §D-3 |
| `navigation-menu` | Mega-menú innecesario: el plan 01 exige llegar a la tarea principal en ≤ 2 navegaciones desde la portada; un header horizontal de 4 destinos cumple. Evitar `navigation-menu` reduce peso y complejidad |
| `combobox` | Duplica el `searchable-select` local ya instalado y usado |
| `chart` | Ver arriba (decidido por familia, no en FND-06) |
| `resizable`, `hover-card`, `context-menu`, `menubar`, `slider`, `native-select`, `aspect-ratio` (en shell), `toggle` (suelto), `message-scroller`, `bubble`, `questionnaire`, `attachment`, `code-block`, `input-otp`, `kbd`, `marker`, `direction`, `trace`, `code-block` | Sin caso de uso en el plan 01–06. No se instala lo que no tiene tarea |

> **Todos los comandos se ejecutan con `-c Aplicacion/frontend`** (config del target) y **previa revisión de diff** contra la customization local (regla de `salesianos-shadcn`: no sobrescribir a ciegas). `searchable-select` es local y **no** se toca.

### C.6 Criterios de aceptación verificables para FND-06

| # | Criterio | Cómo se verifica |
|---|---|---|
| S1 | `npx tsc --noEmit` sin errores en `Aplicacion/frontend` | Comando de FND-06. Requiere que `src/features/**` deje de tener imports rotos (§F: **S1 es bloqueante y preexistente**) |
| S2 | Los 4 grupos de ruta existen con sus 36 page IDs mapeados y sus `loading/error/not-found` | `glob src/app/**` + checklist de rutas |
| S3 | `src/app/globals.css` declara los roles de §B.1 en **claro y oscuro**, sin literales de color dentro de `@utility`/`@layer utilities` | Inspección + prueba `tokens.test.ts` |
| S4 | `ThemeProvider` montado: `<html>` recibe `class="dark"` con `defaultTheme="system"` | Prueba de render + verificación manual |
| S5 | La navegación admin **no inventa módulos**: destinos = plan 04 §1, filtrados por capacidad conocida | Inspección del árbol de navegación + comparación con la lista del plan |
| S6 | Sin scroll-snap ni `overflow-y: scroll` globales; el scroll-snap sólo en la portada | `grep "scroll-snap\|overflow-y: scroll" src/app/globals.css` → 0 coincidencias fuera del scope de portada |
| S7 | `prefers-reduced-motion` resuelto por **una** regla global + un hook compartido | `grep "@media (prefers-reduced-motion"` → 1 bloque |
| S8 | 0 literales de color en `src/components/**` y `src/features/**` salvo la excepción documentada | `npx vitest run src/components` (prueba de tokens) |
| S9 | Foco visible en todos los interactivos; anillo de 3 px con offset 2 px | Auditoría manual de teclado en los 5 anchos |
| S10 | El sidebar colapsa a `offcanvas` (Sheet) en < 768, a iconos en 768–1023, expandido en ≥ 1024 | Captura manual en 360/390/768/1024/1440 |
| S11 | Skip-link al contenido en los 3 layouts con chrome | Auditoría de teclado |
| S12 | `npx biome check src/app src/components src/lib` sin errores nuevos | Comando de FND-06 |
| S13 | `npx vitest run src/app src/components` verde en las pruebas nuevas | Comando de FND-06 |
| S14 | Radio único: sin `--radius-2xl/3xl`, sin `rounded-3xl`, sin `rounded-[40px]` | `grep` |
| S15 | El peso 900 existe en la familia o ningún token lo usa | `next/font` `weight` incluye `"900"` **o** `text-eyebrow-brand` usa `700` |

---

## D. Tablas de candidatos shadcn

> **Columnas:** `item` · `registry` · `fit` · `role support` · `mobile behavior` · `customization cost` · `risks` · `recommendation`.
> Todas las filas provienen del inventario verificado (`Aplicacion/frontend/doc_dev/shhadcn-registry-inventory.md`, 219 ítems) o del fetch directo al registry oficial `https://ui.shadcn.com/r/styles/radix-nova/{name}.json`.

### D-1. Navegación / shell (16 variantes `sidebar-01..16`)

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `sidebar-08` — inset con navegación secundaria | `@shadcn/sidebar-08` · deps: sidebar, breadcrumb, separator, collapsible, dropdown-menu, avatar | **Alto.** Es la única variante con *inset* + *secondary nav*: el admin necesita un nivel secundario (módulo actual → secciones) y el `SidebarInset` resuelve el marco de contenido | **Alto.** Avatar + `DropdownMenu` de usuario en el pie; secciones plegables con `collapsible` | El `sidebar` base resuelve `collapsible="offcanvas"` → `Sheet` en < 768 sin código extra | **Media.** Hay que reescribir el modelo de menús (los blocks hardcodean rutas y etiquetas en inglés) y arrancar el color del lateral (`from-[#1f2357]` → tokens) | **El block trae un dashboard de ejemplo**: si se copia el archivo tal cual, aparecen rutas y textos de otro producto | **ADOPTAR como referencia estructural**, no instalar el block: se compone sobre el `sidebar` ya instalado, con el modelo de menús del proyecto |
| `sidebar-07` — colapsable a iconos | `@shadcn/sidebar-07` · deps: sidebar, breadcrumb, separator, collapsible, dropdown-menu, avatar | **Alto** para el modo "raíl" en 768–1023: el bloque ya resuelve el tooltip al colapse y el rail | **Alto** (avatar + menú de usuario) | Colapsable a iconos con `tooltip` en el rail; el offcanvas lo da la primitiva | **Media.** El tooltip del rail debe reescribirse en español y con `aria-label` | Riesgo de perder legibilidad si el estado activo se marca sólo por color | **ADOPTAR el patrón de colapse + tooltip**; el bloque se usa como espécimen, no como archivo a copiar |
| `sidebar-01` — simple, agrupado por sección | `@shadcn/sidebar-01` · deps: sidebar, breadcrumb, separator, label, dropdown-menu | **Alto** para `(cuenta)` (sin sidebar) y como base mínima del admin: agrupación por sección = los 3 grupos de plan 04 §1 | **Medio** (sin avatar en deps) | Offcanvas vía `Sheet` | **Baja.** Es el closer a lo que ya hay | groups hardcodeados; `label` en inglés | **Base de referencia** para el menú: copiar la estructura de grupos, no el contenido |
| `sidebar-02` — secciones colapsables | `@shadcn/sidebar-02` · deps: + label, dropdown-menu | **Alto.** Plan 04 §1 pide explícitamente "secciones desplegables: Deportivo / Ventas y entradas / Configuración y personas" | **Medio** | Los grupos plegables sobreviven bien en offcanvas | **Baja** | Que un grupo quede plegado oculte destinos que el admin no recuerda que existen | **ADOPTAR** como comportamiento de los 3 grupos del admin (estado de pliegue persistido en `localStorage`, no en servidor) |
| `sidebar-05` — submenús colapsables | `@shadcn/sidebar-05` · deps: + collapsible | **Medio.** Útil si un módulo (p. ej. Marketplace) tiene sub-rutas | **Medio** | Submenú anidado en offcanvas es frágil (scroll anidado) | **Media** | Scroll anidado + foco atrapado | **NO** en el MVP: los destinos del plan son conceptuales y planos. Se reserva para cuando un módulo tenga jerarquía propia |
| `sidebar-04` — flotante con submenús | `@shadcn/sidebar-04` · deps: sidebar, breadcrumb, separator | **Bajo.** El lateral flotante con sombraSeparada es un recurso de producto SaaS genérico | **Bajo** | Puede flotar sobre el contenido en móvil | **Media** | El marco flotante + el contenido produce un segundo plano visual; menos legible para una consola operativa densa | **NO**: la consola admin debe Maximizar el área de tabla, no flotar |
| `sidebar-10` — en popover / `sidebar-13` — en diálogo | `@shadcn/sidebar-10`, `@shadcn/sidebar-13` | **Medio** sólo como alternativa al offcanvas cuando el menú debe ir *encima* del contenido sin empujarlo | **Bajo** | Popover no es patrón móvil; diálogo sí, pero es peor que `Sheet` para navegación | **Media** | Un menú en popover en móvil se sale de pantalla; las hojas modal con `Sidebar` duplican primitivas | **NO**: `Sheet` (ya instalado) cubre el offcanvas con menos piezas |
| `sidebar-14` (derecha) · `sidebar-15` (doble) · `sidebar-16` (header pegajoso) · `sidebar-09` (anidadas) · `sidebar-11` (árbol) · `sidebar-12` (calendario) · `sidebar-03` (submenús) · `sidebar-06` (submenús como dropdown) | `@shadcn/sidebar-14..16`, `09`, `11`, `12`, `03`, `06` | **Bajo.** Un panel derecho duplicaría el peso de la interfaz en un admin de 3 secciones; un sidebar anidado o con calendario no corresponde a ninguna tarea del plan | **Bajo** | — | **Alta** si se instalan | Cada variante añade superficie y rutas no contempladas | **NO**: documentadas aquí para dejar constancia de que las 16 se revisaron y 10 se descartaron por falta de tarea |

**Conclusión de la familia:** el target ya tiene la primitiva `sidebar` instalada (soporta `variant: "sidebar" | "floating" | "inset"` y `collapsible: "offcanvas" | "icon" | "none"`). **No se instala ningún block `sidebar-*`**: se usa `sidebar-08` + `sidebar-02` + `sidebar-07` como **especimen de estructura** y se compone sobre la primitiva, con el modelo de menús del plan y los tokens de §B.

### D-2. Tabla de datos operativa (admin)

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `table` | `@shadcn/table` (ya instalada) | **Alto.** Es la única primitiva de tabla del registro | **Medio** (sin manage) | Con `overflow-x` controlado y `min-w-0`; en ≤ 768 se apila en filas label/valor | **Media** | Los headers sticky + `overflow-x` en móvil producen scroll horizontal (prohibido) | **CONSERVAR** y componer: `OperationalDataTable` (proyecto) sobre `table` + `@tanstack/react-table` (ya instalado) |
| `table-example` / `data-table` | bloque `preview-02` incluye `table`; **`data-table` NO existe en el inventory `radix-nova`** | **N/A** | — | — | — | Referenciar un `data-table` inexistente rompe la instalación | **NO instalar `data-table`**: no está en las 64 primitivas verificadas. Construir `OperationalDataTable` propio sobre `table` + TanStack Table |
| Toolbar + filtros | sin item oficial (`input-group`, `toggle-group`, `pagination`, `searchable-select`, `sheet`) | **Alto.** Es el patrón transversal del admin (plan 06 §1: "un único patrón visual de tablas con paginación, filtros, estados vacíos y detalles") | **Alto** (todo admin opera) | En ≤ 768 la barra de filtros colapsa en `Sheet`; la búsqueda queda siempre visible | **Media** | Que cada pantalla invente su toolbar produce 12 variantes | **COMPONER** `FilterBar` (proyecto) con `input-group` + `toggle-group` + `searchable-select` + `sheet`; los filtros viven en la URL (`useAdminListaUrl`), no en estado local |
| `empty` | `@shadcn/empty` | **Alto** | **Alto** | Se apila; `EmptyContent` con la acción relevante | **Baja** | Empty con más de una acción compite | **INSTALAR** (FND-06) |
| `pagination` | `@shadcn/pagination` | **Alto** | **Alto** | En ≤ 768: botones + "ir a página" | **Baja** | Paginación client-side sobre datos ya paginados por el backend | **INSTALAR** (FND-06); consume `count/page/pageSize/totalPages` del envelope, no deriva el total |
| `spinner` / `skeleton` | `@shadcn/spinner` / `skeleton` (instalada) | **Alto** | **Alto** | — | **Baja** | Spinner dentro de la celda da salto de layout | **INSTALAR** `spinner`; `skeleton` ya instalada |

### D-3. Formulario y wizard — `field`/`form` vs `GenericForm`

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `field` | `@shadcn/field` · deps: label, separator (ambos instalados) | **Alto como capa de render**, **nulo como orquestador**: es puramente presentacional (`Field`, `FieldLabel`, `FieldDescription`, `FieldError` con `role="alert"` y `data-invalid` → `text-destructive`) | **Alto** | `orientation="responsive"` apila label/valor en móvil | **Baja** | Que alguien intente usarlo como reemplazo del `GenericForm` y rompa el contrato `smart.md` | **ADOPTAR Y ADAPTAR**: `Field`/`FieldLabel`/`FieldDescription`/`FieldError` sustituyen la maquetación del `DefaultFieldWrapper` de `GenericForm`; el estado, la validación y los Smart Fields **no cambian** |
| `form` | `@shadcn/form` | **Nulo.** Es un binding de `react-hook-form` (`FormProvider`/`useFormContext`) que **reemplaza** al orquestador | — | — | **Alta** | Dos fuentes de verdad del estado del formulario; `useFormContext` no existiría en el árbol del proyecto; los Smart Fields (`useController`) dejarían de encajar | **NO instalar.** `contract/smart.md` es explícito: "`GenericForm` posee la validación y el estado. Las features poseen el layout y la transformación". `GenericForm` ya está en el target (`src/components/genericForm/`) |
| `input-group` | `@shadcn/input-group` · deps: button, input, textarea | **Alto**: campo con addon (icono de búsqueda, prefijo, sufijo) | **Alto** | Se apila en ≤ 768 | **Baja** | — | **INSTALAR** (FND-06) |
| `input-otp` | `@shadcn/input-otp` | **Nulo**: no hay OTP en el plan | — | — | — | Añadir un flujo de autenticación noBackend | **NO instalar** |
| Wizard (4 etapas) | sin item oficial | **Alto**: `progress` + `tabs` (no navegables) | **Alto** | Barra de progreso + "volver" fijo | **Media** | Un wizard con `Tabs` navegables rompe el flujo | **COMPONER**: `progress` (FND-06) + barra de pasos propia en `(cuenta)/inscripcion/layout.tsx`; los pasos son de lectura, no navegación libre |

### D-4. Estados y retroalimentación

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `empty` | `@shadcn/empty` | **Alto** | **Alto** | Se apila, sin `EmptyMedia` grande | **Baja** | "No hay datos" sin acción | **INSTALAR** (FND-06) |
| `alert` | `@shadcn/alert` | **Alto** | **Alto** | Se apila; icono arriba | **Baja** | Alerta genérica que contradice el mensaje del backend | **INSTALAR** (FND-06); el texto es el del backend |
| `alert-dialog` | `@shadcn/alert-dialog` · deps: button | **Alto** para acciones irreversibles (plan 04 §12.4) | **Alto** | A ancho completo en móvil | **Baja** | Confirmación sin el motivo o el efecto | **INSTALAR** (FND-06) |
| `sonner` | `@shadcn/sonner` (ya instalada) | **Alto** | **Alto** | Se re-posiciona abajo-centro | **Baja** | `sonner.tsx` usa `useTheme()` sin ThemeProvider → el toast no cambia de tema | **CONSERVAR**; queda resuelta al montar `ThemeProvider`. Usar siempre `notify` del adaptador (`src/errors/toast-adapter.ts`), nunca `toast()` directo (contrato §8) |
| `skeleton` | `@shadcn/skeleton` (ya instalada) | **Alto** | **Alto** | Respeta la forma real | **Baja** | Skeleton que no coincide con el layout final produce salto | **CONSERVAR**; los `loading.tsx` de grupo lo usan |
| `spinner` | `@shadcn/spinner` | **Alto** | **Alto** | Inline en celda y botón | **Baja** | — | **INSTALAR** (FND-06) |
| `progress` | `@shadcn/progress` | **Alto** | **Alto** | Barra completa | **Baja** | Barra que "inventa" un progreso no verificable | **INSTALAR** (FND-06); el valor refleja pasos completados reales |

### D-5. Drawer / modal / sheet / command / navigation-menu

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `sheet` | `@shadcn/sheet` (ya instalada) | **Alto**: offcanvas del sidebar y paneles de detalle en escritorio | **Alto** | Panel lateral, foco atrapado, cierre por `Esc` | **Baja** | Sheet con contenido largo ⇒ scroll interno + foco | **CONSERVAR**; es el offcanvas del shell |
| `dialog` | `@shadcn/dialog` (ya instalada) | **Alto**: acciones cortas y confirmaciones (plan 06 §1: "modales/drawers sólo para acciones cortas") | **Alto** | A ancho completo en ≤ 768 | **Baja** | Diálogo usado para tareas largas | **CONSERVAR** |
| `drawer` | `@shadcn/drawer` | **Alto** en móvil: detalle de encuentro (plan 05 §3), detalle de inscripción y de compra | **Alto** | Panel inferior con arrastre | **Media** (comportamiento de arrastre ≠ comportamiento de `Sheet`) | Que coexistan drawer y sheet con la misma tarea ⇒ dos interacciones para el mismo gesto | **INSTALAR** (FND-06); regla: `drawer` en ≤ 768, `sheet`/`dialog` en ≥ 1024, para el detalle largo |
| `command` | `@shadcn/command` · deps: dialog, input-group | **Alto**: navegación global del admin + búsqueda de personas/equipos/competencias por teclado (ADM-03/07/09/10) | **Alto** | Se abre como diálogo a ancho completo | **Media** | Paleta de comandos que ejecuta acciones destructivas sin confirmación | **INSTALAR** (FND-06); acciones-destructive pasan por `alert-dialog` |
| `navigation-menu` | `@shadcn/navigation-menu` | **Bajo**: el header público tiene 4 destinos | **Bajo** | Menú vertical en móvil, con submenús anidados | **Alta** | Mega-menú añade peso, foco complejo y rutas anidadas | **NO instalar**: header horizontal simple + `Sheet` en móvil |

### D-6. Navegación por pestañas / breadcrumb / paginación

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `tabs` | `@shadcn/tabs` (ya instalada) | **Alto**: pestañas del detalle de inscripción (Resumen / Equipos / Pool / Compras / Historial — plan 04 §4) y del detalle de competencia | **Alto** | Scroll horizontal con indicadores de borde; `aria-label` en la lista | **Baja** | Tabs navegables que pierden el estado al recargar | **CONSERVAR**; las pestañas son de **lectura de un mismo registro**, con URL propia por pestaña (`?tab=`) para que sea recuperable (plan 06 §1) |
| `toggle-group` | `@shadcn/toggle-group` (+ `toggle`) | **Alto**: filtros por estado y selector de vista (lista vs cuadro) | **Alto** | Se comprime; en ≤ 768 pasa a `Select` | **Baja** | `toggle-group` con 5+ opciones se vuelve un menú de estados | **INSTALAR** (FND-06) |
| `breadcrumb` | `@shadcn/breadcrumb` (ya instalada) | **Alto**: `header` del admin y de la cuenta | **Alto** | Se reduce al último segmento | **Baja** | Migas con nombres técnicos de base de datos (plan 06 §2: navegar por intención) | **CONSERVAR**; los labels son de negocio ("Inscripciones", "Pago"), nunca `settlement_status` |
| `pagination` | `@shadcn/pagination` | **Alto** | **Alto** | Ver D-2 | **Baja** | — | **INSTALAR** (FND-06) |

### D-7. Auth — `login-01..05` / `signup-01..05`

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `login-04` — formulario + imagen | `@shadcn/login-04` · deps: button, card, input, label, field | **Alto**: AUTH-01 necesita panel de marca + formulario, y el panel de marca ya tiene foto de disciplina (`fulbito-varones.webp`, `voley-mixto.webp`) | **Alto** | En < 1024 la imagen colapsa a cabecera; el formulario manda | **Media** | La imagen puede competir con el formulario si es muy saturada | **ADOPTAR como composición de referencia** (2 columnas, panel de marca + formulario), con la foto de disciplina real y el gradiente `--brand-midnight` |
| `login-01` — formulario simple con card | `@shadcn/login-01` · deps: button, card, input, label, field | **Medio** | **Alto** | Un columna, funciona | **Baja** | Card flotante genérico = look de plantilla | **NO** como layout; útil como referencia del formulario en sí |
| `login-03` — fondo atenuado | `@shadcn/login-03` | **Medio** | **Alto** | Bien | **Baja** | Fondo plano sin identidad | **NO**: la identidad institucional necesita el panel de marca, no un `muted` |
| `login-02` / `login-05` | `@shadcn/login-02`, `login-05` | **Bajo**: 02 duplica el layout de 04; 05 es "email only" (el plan no define auth por email exclusivamente) | **Bajo** | — | — | Asumir un mecanismo de autenticación que el backend no congeló | **NO** |
| `signup-04` — formulario + imagen | `@shadcn/signup-04` · deps: button, input, label, field | **Alto**: AUTH-02 (`/registro`) tiene la misma identidad de marca que el login | **Alto** | Igual que login-04 | **Media** | El registro pide tipo/documento + RENIEC + contacto + credenciales: es **más largo** que un signup de shadcn | **ADOPTAR la composición**, no el formulario: el bloque es un signup de 2 campos; el ours tiene 4 bloques y wizard de confirmación de datos |
| `signup-01` / `signup-03` / `signup-05` | `@shadcn/signup-01`, `signup-03`, `signup-05` | **Bajo** | — | — | **Baja** | `signup-05` con proveedores sociales no existen en el plan | **NO** |

**Conclusión:** el layout de auth se construye como **composición** (panel de marca + panel de formulario) tomando `login-04`/`signup-04` como espécimen de estructura, con el formulario propio sobre `GenericForm` + `field`. No se instala ningún block de auth: son páginas completas con copy y navegación fijas que el producto debe redefinir.

### D-8. Dashboard admin — `dashboard-01`

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `dashboard-01` | `@shadcn/dashboard-01` · deps: sidebar, breadcrumb, separator, label, chart, card, select, tabs, table, toggle-group, badge, button, checkbox, dropdown-menu, drawer, input, avatar, sheet, sonner | **Bajo como bloque; ALTO como catálogo de piezas.** El bloque es el dashboard genérico de SaaS: rejilla de KPIs, charts, tabla de ejemplo | **Alto** | Responsive, pero por construcción | **Muy alta** si se adapta; **baja** si se usa de catálogo | **Alto.** Es exactamente el "look de plantilla" que el encargo prohíbe: KPIs de relleno, `chart` con datos inventados, tabla de ejemplo con datos ficticios. Y arrastra `chart` (recharts) al bundle | **NO adoptar el bloque.** Adoptar **su patrón de KPI** —fila de métricas accionables (inscripciones pendientes, equipos incompletos, compras por revisar, entradas por validar, pedidos por entregar— plan 04 §2) y **su patrón de tabla**—, construidos con `card`, `badge`, `table` y `toggle-group`, sin `chart` en el MVP. **Cero datos de relleno**: si el backend no devuelve la métrica, no se muestra la métrica |

### D-9. Landing / promo — `preview-01..03`

| item | registry | fit | role support | mobile behavior | customization cost | risks | recommendation |
|---|---|---|---|---|---|---|---|
| `preview-01` | `@shadcn/preview` · deps: alert-dialog, avatar, badge, button, button-group, card, checkbox, combobox, dropdown-menu, empty, field, input, input-group, item, label, popover, radio-group, select, separator, sheet, slider, spinner, switch, textarea, tooltip, example | **Nulo como página**: es una galería de componentes, no una landing | **Bajo** | — | — | Copiar la galería a la portada produce un catálogo de widgets | **NO instalar ni usar** |
| `preview-02` | `@shadcn/preview-02` · deps: accordion, badge, breadcrumb, button, calendar, card, chart, checkbox, combobox, dropdown-menu, empty, field, input, input-group, item, label, native-select, progress, radio-group, select, separator, sidebar, skeleton, slider, spinner, switch, table, tabs, textarea, toggle-group | **Nulo como landing**: es la galería de componentes con `sidebar` | **Bajo** | — | — | Instalar 27 dependencias para ver una galería | **NO** (además arrastra `chart`) |
| `preview-03` | `@shadcn/preview-03` (sin `registryDependencies`) | **Bajo** | — | — | **Baja** | Bloque sin dependencias declaradas: comportamiento incierto | **NO** |

**Conclusión de landing:** la portada (PUB-01) no se construye con un block de shadcn. Se compone con `carousel` (ya instalada) para los frames del hero (`public/images/portada/`), `accordion` para el bloque de información, `card`/`badge` para los paquetes y `btn-brand-gradient` + `btn-shine` para el CTA. **Los bloques `preview-*` son catálogos de componentes, no páginas de marketing**: no aportan a esta pantalla.

---

## E. Responsive y accesibilidad (global)

### E.1 Matriz de cinco anchos

| Ancho | Público `(public)` | Cuenta `(cuenta)` | Administración `(administracion)` |
|---|---|---|---|
| **360** | Header reducido: wordmark + CTA icono (≥ 44 px) + botón de menú (≥ 44 px). Navegación en `Sheet`. Sin scroll horizontal en ninguna sección. CTA sticky en el wizard, sin tapar contenido | Top bar con wordmark + avatar; navegación como `DropdownMenu`/chips con scroll horizontal **indicado**. Wizard a una columna, pasos con barra de progreso y scroll de etapas | Sidebar **offcanvas** (`Sheet`). Tabla → **filas apiladas** con `label`/`valor` (no scroll horizontal). Barra de filtros en `Sheet`; búsqueda siempre visible. Acciones en `DropdownMenu` |
| **390** | Igual que 360, con 30 px de aire extra; carrusel con miniaturas táctiles de 44 px | Igual | Igual |
| **768** | Nav horizontal visible (`md`); contenido en 2 columnas donde la tarea lo permita | Contenedor `max-w-[720px]`; wizard 1 columna con barra lateral de pasos opcional | Sidebar colapsado a **rail de iconos** (`collapsible="icon"`, tooltips) o offcanvas según densidad; tabla con scroll-x **sólo** dentro del contenedor de tabla (con `aria-label` de la zona desplazable) |
| **1024** | Layout completo: nav + CTA; secciones a 2 columnas | Contenedor `max-w-[1100px]`, rejillas de 2 columnas | Sidebar **expandido** (`inset`, 272 px) + `SidebarInset` con `header` pegajoso; tablas con paginación y filtro en línea |
| **1440** | Contenedor `max-w-[1200px]` centrado (nunca `1480px`: longitud de línea) | Ídem, con más aire entre bloques | Sidebar 272 px + contenido `max-w-[1200px]`; sin stretching del texto; la tabla ocupa el ancho disponible |

**Política de breakpoints:** se usan los breakpoints por defecto de Tailwind (`sm 640`, `md 768`, `lg 1024`, `xl 1280`). El `useIsMobile` ya instalado usa **768**, coherente con esta matriz → no hay dos sistemas de "móvil".

### E.2 Reglas globales

| Regla | Especificación |
|---|---|
| **Área táctil** | ≥ 44 × 44 px en ≤ 768 px (`size-11`, `h-11`); ≥ 36 × 36 px en escritorio (`size-9`). Separación ≥ 8 px entre controles |
| **Foco visible** | `ring-[3px] ring-ring/50 ring-offset-2 ring-offset-background`; `outline` nunca eliminado (enlaces en prosa: `outline-2 outline-offset-2 outline-ring`) |
| **Contraste** | Texto normal ≥ 4.5:1; texto grande (≥ 24 px o ≥ 18.66 px bold) y componentes de UI (bordes de campo, anillo, foco) ≥ 3:1. Todos los pares de §B.1 están calculados para cumplir AA |
| **Movimiento reducido** | Regla global única (§B.6) + `useReducedMotion()`; sin `scroll-behavior: smooth` global |
| **Sin overflow horizontal** | `overflow-x: clip` en contenedores de página; `min-w-0` en hijos flex; las tablas con scroll propio llevan `tabindex="0"` y `role="region"` con nombre accesible |
| **Teclado en el shell** | Skip-link → `Tab` en orden de lectura → `Esc` cierra sheet/dialog/drawer/command → el foco **vuelve al disparador** al cerrar → `SidebarRail` es `<button>` con `aria-label` → el `Command` filtra por teclado |
| **Estado no sólo por color** | Todo estado lleva texto (y, si aplica, icono). En tablas, la celda de estado lleva texto, no una mancha de color |
| **Semántica** | Iconos decorativos `aria-hidden="true"`; botones sólo-icono con `aria-label` en español; `<Image>` de marca con `alt` real; `alt` descriptivo en fotos de producto y patrocinador |
| **Reader QR** | Ingreso manual alternativo siempre disponible (plan 06 §6); el `drawer`/panel de validación es operable por teclado |
| **Errores** | `role="alert"` en el mensaje de campo; `ErrorSummary` con foco al primer campo con error tras un envío |
| **Cargando** | `loading.tsx` con skeleton de la forma real; nunca un spinner a pantalla completa en navegación interna |

### E.3 Lo que queda como regla por ruta (Partes B/C del brief)

- Contenido y copy de cada page ID, jerarquía de secciones, microcopy de estados.
- Composición de la tabla operativa por familia (inscripciones, equipos, pagos, marketplace).
- Comportamiento del wizard de inscripción (4 etapas, validaciones por etapa).
- Flujos de checkout (pases, tienda) y sus modales de pasarela.
- Panel de detalle de encuentro (bracket, agenda, cuadro) y su navegación móvil.
- Reglas de la "firma de oro" y del eyebrow **dentro** de cada página.
- Validación por campo y asociación error↔campo **por formulario**.

---

## F. Supuestos y preguntas de contrato abiertas

### F.1 Supuestos provisionales (a corregir cuando el backend esté congelado)

| # | Supuesto | Base | Cómo se absorbe el cambio |
|---|---|---|---|
| P1 | Las rutas del plan 01 (`/mi-cuenta`, `/mis-inscripciones`, `/administracion/**`) son las finales | Plan 01 §2, §3 ("rutas propuestas") | Una única constante `src/lib/routes.ts`; renombrar = un archivo |
| P2 | El backend expone `es_admin` y un vector de capacidades en la sesión (`GET /auth/me`) | 03b §3.1, 03b §3.2 | La navegación lee ese veredicto; si cambia el nombre, se toca el lector, no las páginas |
| P3 | Envelope `{success, data, message}` y paginación `{count, page, pageSize, totalPages}` | `Aplicacion/documentacion/02-backend-y-api.md` §5 | Se consume; no se construye ni se renombra |
| P4 | El token del enlace invitado puede viajar en la ruta o ser sesión temporal | Plan 01 nota y `PD-07` | La ruta se declara; la resolución del token es del servidor |
| P5 | Se soportan tema claro y oscuro, con `defaultTheme="system"` | El congelado tiene un `.dark` (muerto) que demuestra la intención | Si el producto decide sólo claro, se cambia una prop; los tokens oscuros quedan como red de seguridad sin coste |
| P6 | `next-themes` es la librería de tema (ya instalada) | `package.json` | No se añade otra |
| P7 | La navegación admin lista los 22 destinos **conceptuales** del plan, sin flags de "módulo habilitado" inventados | Plan 04 §1, FND-06 AC | Cuando el backend publique el catálogo por módulo, el filtro se añade en un solo sitio |
| P8 | Las fuentes se cargan con pesos `200–800`; el eyebrow usa 700 | `app/layout.tsx:24`, D16 | Si se quiere 900, se añade el peso a `next/font` (un token) |
| P9 | Los estados de negocio (pago, inscripción, pase) los publica el backend como código+etiqueta+acción recomendada | Plan 04 §6 ("`estado_operativo.codigo`, `etiqueta`, `descripcion`, `accion_recomendada`") | La UI pinta lo que llega; los colores de estado se asignan por rol semántico, no por código |
| P10 | `chart` no entra en el MVP | Plan 04 §2 ("no mostrar decenas de KPIs irrelevantes") | Si aparece una serie real, se instala en UI-04 |
| P11 | `src/features/**` está vacío y sus 63 imports rotos son un **bloqueo preexistente** que FND-06 debe resolver | Medición sobre `Aplicacion/frontend/src` | FND-06 no implementa features de dominio: o se crean las rutas con placeholders sin imports a `features`, o seRestore el alcance |

### F.2 Preguntas de contrato abiertas (sólo bloqueantes para el esqueleto)

> Criterio: si la duda se resuelve con el plan o la documentación vigente, **no se pregunta** — se decide y se documenta como supuesto.

| # | Pregunta | Por qué bloquea el esqueleto | Qué se hace mientras tanto | Impacto si cambia |
|---|---|---|---|---|
| **Q1** | **Forma del veredicto de sesión que el shell consume**: ¿el layout de administración lee `es_admin` + `capacidades` desde `GET /auth/me` en servidor, o existe un endpoint de sesión distinto? | Determina si `(administracion)/layout.tsx` es un Server Component (lee la sesión) o un Client Component (recibe la sesión por props), y si la navegación se filtra en servidor o en cliente | Se asume lectura en servidor desde `getUserSession()` (ya presente en `src/lib/auth/`), con `capacidades` como array de códigos | Cambia la firma del layout y el punto de filtrado de la navegación. No cambia las rutas |
| **Q2** | **Vocabulario de capacidades**: ¿se mantiene el espejo de 11 códigos de `backend/core/capacidades.py` (`admin.ver`, `admin.pagos.ver`, `admin.competencias.escribir`, …) o el rebuild lo renombra? | El shell **debe** filtrar secciones por capacidad para no mostrar destinos prohibidos. Sin el vocabulario congelado, el shell tendría que mostrarlos todos (o inventar el filtro) | Se asume el vocabulario de 03b §3.2, leído como **datos** (no hardcodeado en el componente): el componente consume una lista de secciones con su capacidad requerida | Si cambian los códigos, se toca el archivo de datos, no los componentes |
| **Q3** | **Catálogo de módulos habilitados por edición**: ¿el backend publica, para la edición seleccionada, qué módulos están activos (inscripciones / pases / marketplace /Lbanchetas / fizz)? | Sin ese dato, la navegación puede ofrecer un destino que en esa edición no existe (violando el AC de FND-06 "no inventa módulos habilitados") | Se asume que **no** hay filtro por módulo en el MVP del shell: se muestran los destinos conceptuales del plan y se documenta la limitación | Si el backend lo publica, el filtro entra en un único punto (la construcción de la lista de navegación) |

**No bloqueantes, pero se registran para el backend:** (a) forma exacta del envelope y de la paginación; (b) nombres de los campos de `GET /auth/me`; (c) expiración y revocación del enlace invitado; (d) si el token de compra invitada puede viajar en la ruta o debe ir por sesión (PD-07).

### F.3 Trazabilidad de este brief

- **Contratos leídos:** `next-app-architecture-contract.md`, `smart.md`, `api-wrapper-presenter-contract.md`.
- **Plan leído:** `frontend/01..06` (mapa de rutas, sistema UX/UI, fichas públicas/comerciales/admin/competencias).
- **Documentación leída:** `07-guia-para-ui-ux.md` (ley operativa), `03b-paginas-administrativas-y-operativas.md`, `05a-matriz-pagina-flujo-endpoint-datos.md`, `03a-paginas-publicas-y-compra.md`.
- **Evidencia de código:** `Aplicacion/frontend/src/app/globals.css` (target), `frontend/src/app/globals.css` (congelado), `Aplicacion/frontend/components.json`, `Aplicacion/frontend/doc_dev/shadcn-registry-inventory.md`, `Aplicacion/frontend/src/components/ui/**` (27), `Aplicacion/frontend/src/app/**` (estado real), `Aplicacion/frontend/src/providers/ReactQueryProvider.tsx`, `Aplicacion/frontend/src/lib/{api,query-client,auth,post-auth-redirect}`, `Aplicacion/frontend/src/hooks/use-mobile.ts`, `Aplicacion/frontend/tsconfig.json`, `Aplicacion/frontend/package.json`, `frontend/src/components/AppSidebar.tsx` (congelado, sólo evidencia).
- **Skills aplicados:** `salesianos-ui-ux`, `salesianos-shadcn`, `ui-ux-pro-max`, `frontend-design`.
- **No modificado:** ningún archivo. Ningún endpoint, payload, presenter, regla de elegibilidad, capacidad, precio o pago ha sido inventado en este brief.
