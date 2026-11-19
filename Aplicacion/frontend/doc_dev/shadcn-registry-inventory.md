# shadcn registry @shadcn - inventario verificado (style: radix-nova)

Fuente: https://ui.shadcn.com/r/styles/radix-nova/registry.json  (219 items)
Consultado: 2026-11-18. Add command: `npx shadcn@latest add @shadcn/<name>`

## BLOCKS (30) - pagina completa, cada uno con su codigo fuente

| name | descripcion | registryDependencies |
|---|---|---|
| `@shadcn/dashboard-01` | A dashboard with sidebar, charts and data table. | sidebar, breadcrumb, separator, label, chart, card, select, tabs, table, toggle-group, badge, button, checkbox, dropdown-menu, drawer, input, avatar, sheet, sonner |
| `@shadcn/login-01` | A simple login form. | button, card, input, label, field |
| `@shadcn/login-02` | A two column login page with a cover image. | button, input, label, field |
| `@shadcn/login-03` | A login page with a muted background color. | button, card, input, label, field |
| `@shadcn/login-04` | A login page with form and image. | button, card, input, label, field |
| `@shadcn/login-05` | A simple email-only login page. | button, input, label, field |
| `@shadcn/preview` |  | alert-dialog, avatar, badge, button, button-group, card, checkbox, combobox, dropdown-menu, empty, field, input, input-group, item, label, popover, radio-group, select, separator, sheet, slider, spinner, switch, textarea, tooltip, example |
| `@shadcn/preview-02` |  | accordion, badge, breadcrumb, button, calendar, card, chart, checkbox, combobox, dropdown-menu, empty, field, input, input-group, item, label, native-select, progress, radio-group, select, separator, sidebar, skeleton, slider, spinner, switch, table, tabs, textarea, toggle-group |
| `@shadcn/preview-03` |  |  |
| `@shadcn/sidebar-01` | A simple sidebar with navigation grouped by section. | sidebar, breadcrumb, separator, label, dropdown-menu |
| `@shadcn/sidebar-02` | A sidebar with collapsible sections. | sidebar, breadcrumb, separator, label, dropdown-menu |
| `@shadcn/sidebar-03` | A sidebar with submenus. | sidebar, breadcrumb |
| `@shadcn/sidebar-04` | A floating sidebar with submenus. | sidebar, breadcrumb, separator |
| `@shadcn/sidebar-05` | A sidebar with collapsible submenus. | sidebar, breadcrumb, separator, label, collapsible |
| `@shadcn/sidebar-06` | A sidebar with submenus as dropdowns. | sidebar, breadcrumb, separator, card, dropdown-menu |
| `@shadcn/sidebar-07` | A sidebar that collapses to icons. | sidebar, breadcrumb, separator, collapsible, dropdown-menu, avatar |
| `@shadcn/sidebar-08` | An inset sidebar with secondary navigation. | sidebar, breadcrumb, separator, collapsible, dropdown-menu, avatar |
| `@shadcn/sidebar-09` | Collapsible nested sidebars. | sidebar, breadcrumb, separator, collapsible, dropdown-menu, avatar, switch, label |
| `@shadcn/sidebar-10` | A sidebar in a popover. | sidebar, breadcrumb, separator, popover, collapsible, dropdown-menu |
| `@shadcn/sidebar-11` | A sidebar with a collapsible file tree. | sidebar, breadcrumb, separator, collapsible |
| `@shadcn/sidebar-12` | A sidebar with a calendar. | sidebar, breadcrumb, separator, collapsible, calendar, dropdown-menu, avatar |
| `@shadcn/sidebar-13` | A sidebar in a dialog. | sidebar, breadcrumb, button, dialog |
| `@shadcn/sidebar-14` | A sidebar on the right. | sidebar, breadcrumb |
| `@shadcn/sidebar-15` | A left and right sidebar. | sidebar, breadcrumb, separator, popover, collapsible, dropdown-menu, calendar, avatar |
| `@shadcn/sidebar-16` | A sidebar with a sticky site header. | sidebar, breadcrumb, separator, collapsible, dropdown-menu, avatar, button, label |
| `@shadcn/signup-01` | A simple signup form. | button, card, input, label |
| `@shadcn/signup-02` | A two column signup page with a cover image. | button, input, label, field |
| `@shadcn/signup-03` | A signup page with a muted background color. | button, card, input, label, field |
| `@shadcn/signup-04` | A signup page with form and image. | button, card, input, label, field |
| `@shadcn/signup-05` | A simple signup form with social providers. | button, input, label |

## UI COMPONENTS (64) - primitivas

| name | registryDependencies |
|---|---|
| `accordion` |  |
| `alert` |  |
| `alert-dialog` | button |
| `aspect-ratio` |  |
| `attachment` | button |
| `avatar` |  |
| `badge` |  |
| `breadcrumb` |  |
| `bubble` |  |
| `button` |  |
| `button-group` | separator |
| `calendar` | button |
| `card` |  |
| `carousel` | button |
| `chart` |  |
| `checkbox` |  |
| `code-block` | button, use-highlighted-code |
| `collapsible` |  |
| `combobox` | button, input-group |
| `command` | dialog, input-group |
| `context-menu` |  |
| `dialog` | button |
| `direction` |  |
| `drawer` |  |
| `dropdown-menu` |  |
| `empty` |  |
| `field` | label, separator |
| `form` |  |
| `hover-card` |  |
| `input` |  |
| `input-group` | button, input, textarea |
| `input-otp` |  |
| `item` | separator |
| `kbd` |  |
| `label` |  |
| `marker` |  |
| `menubar` |  |
| `message` |  |
| `message-scroller` | button |
| `native-select` |  |
| `navigation-menu` |  |
| `pagination` | button |
| `popover` |  |
| `progress` |  |
| `questionnaire` | button |
| `radio-group` |  |
| `resizable` |  |
| `scroll-area` |  |
| `select` |  |
| `separator` |  |
| `sheet` | button |
| `sidebar` | button, separator, sheet, tooltip, input, use-mobile, skeleton |
| `skeleton` |  |
| `slider` |  |
| `sonner` |  |
| `spinner` |  |
| `switch` |  |
| `table` |  |
| `tabs` |  |
| `textarea` |  |
| `toggle` |  |
| `toggle-group` | toggle |
| `tooltip` |  |
| `trace` | collapsible |

## NOTAS
- `sidebar-01`..`sidebar-16`: 16 variantes (inset, floating, offcanvas, collapsible, con submenus, con secondary nav, rail).
- `login-01`..`login-05` y `signup-01`..`signup-05`: 5 layouts de auth (el 5 es split con imagen).
- `dashboard-01`: dashboard completo. `preview-01..03`: portadas / landing.
- Componentes con dependencia externa notable: `chart` (recharts), `command` (cmdk), `calendar` (react-day-picker), `carousel` (embla-carousel-react), `resizable` (react-resizable-panels), `table` (tanstack).
- `field` + `form`: primitivas de formulario (el proyecto usa GenericForm propio: revisar antes de adoptarlas).
- `empty`: estado vacio oficial. `item`: patron de fila. `input-group`: input con addon. `spinner`, `progress`, `switch`, `toggle-group`, `navigation-menu`, `menubar`, `breadcrumb`, `pagination`.

## INSTALADOS EN EL TARGET (Aplicacion/frontend/src/components/ui) - 27
avatar, badge, breadcrumb, button, calendar, carousel, checkbox, collapsible, dialog, dropdown-menu, input, label, popover, radio-group, scroll-area, searchable-select (custom), select, separator, sheet, sidebar, skeleton, sonner, table, tabs, textarea, tooltip

## FALTANTES en el target pero disponibles en el registry
accordion, alert, alert-dialog, aspect-ratio, chart, command, combobox, context-menu, drawer, empty, field, form, hover-card, input-group, item, menubar, native-select, navigation-menu, pagination, progress, resizable, slider, spinner, switch, toggle, toggle-group, attachment, bubble, message-scroller, questionnaire