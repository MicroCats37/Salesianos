# Flujo de referencia del `frontend-mokup`

> **ÚLTIMA ACTUALIZACIÓN**: Validado contra código fuente real del mockup.
> Este documento resume el flujo visual y funcional existente en `frontend-mokup`. Debe usarse como **referencia de UX, copy, pantallas, estados y reglas visibles**, no como arquitectura objetivo ni como fuente para copiar código directamente.

---

## Regla Principal

| Punto | Decisión |
|-------|----------|
| Rol del mockup | Referencia visual/funcional para entender el producto. No es la arquitectura final. |
| Arquitectura objetivo | No se define desde `frontend-mokup`; debe seguir el contrato y la arquitectura acordada del proyecto real (`backend/`, `frontend/`, `contract/`). |
| Uso permitido | Extraer flujos, campos, validaciones visibles, estados, textos y conceptos de negocio. |
| Uso no permitido | Copiar carpetas, Drizzle, API routes, Server Actions, stores, schemas o layouts como arquitectura final. |

---

## Ruta Feliz (Happy Path)

1. El visitante entra a `/` y revisa disciplinas, paquetes, proceso y reglamento.
2. Si no tiene cuenta, usa `/register` para crear usuario responsable.
3. Si ya tiene cuenta, usa `/login` con DNI o email (NO username).
4. El responsable entra a `/dashboard`.
5. Si no tiene inscripción, el dashboard lo envía a `/inscripcion`.
6. Completa el wizard: responsable/promoción, equipo/nómina, paquete/pago y declaraciones.
7. Al enviar, vuelve a `/dashboard` para ver estado, observaciones, integrantes y equipos.
8. El Comité revisa en `/admin/comite/inscripciones` y cambia estados.

**Nota sobre login**: La UI real solo tiene tabs **DNI** y **Email**. Existe un schema `LoginUsernameFormSchema` en el código que **NO se utiliza** en la interfaz actual. Esto puede ser遗留 (legacy) o para futuro.

---

## Mapa de Rutas

| Ruta | Público/Rol | Propósito | Fuente principal |
|------|-------------|-----------|-----------------|
| `/` | Público | Landing con hero, galería, paquetes, disciplinas, proceso, reglamento y CTAs. | `src/app/page.tsx`, `src/components/landing/*` |
| `/register` | Público | Registro de responsable. | `src/app/(auth)/register/page.tsx`, `src/features/auth/components/RegisterForm.tsx` |
| `/login` | Público | Login por DNI o email (tabs). No username en UI real. | `src/app/(auth)/login/page.tsx`, `src/features/auth/components/LoginForm.tsx` |
| `/dashboard` | `responsable` | Panel del responsable: estado de inscripción o CTA para preinscribir. | `src/app/(protected)/dashboard/page.tsx`, `src/features/inscripcion/views/ResponsableDashboardView.tsx` |
| `/inscripcion` | `responsable` | Wizard de preinscripción (4 pasos). | `src/app/(protected)/inscripcion/page.tsx`, `src/features/inscripcion/components/InscripcionWizard.tsx` |
| `/admin/dashboard` | `admin_comite`, `admin_finanzas` | Resumen administrativo con estadísticas. | `src/app/(protected)/admin/dashboard/page.tsx`, `src/features/admin/inscripciones/components/AdminDashboardStats.tsx` |
| `/admin/comite/inscripciones` | `admin_comite`, `admin_finanzas` | Lista de inscripciones, jugadores y cambio de estado. | `src/app/(protected)/admin/comite/inscripciones/page.tsx`, `src/features/admin/inscripciones/components/InscripcionListTable.tsx` |

**Ruta de redirect al login**: `src/lib/auth/require-role.ts` — admins van a `/admin/comite/inscripciones`; responsables van a `/dashboard`; no autenticados van a `/login`.

---

## Landing/Home

La landing comunica el evento antes de pedir datos. Sus referencias útiles son la narrativa, la jerarquía visual y el orden de decisión del usuario.

| Sección | Qué comunica |
|---------|--------------|
| Hero | Salesianos FEST 2026, promoción 2002, fecha, sede, disciplinas y CTA a registro/login. |
| Paquetes | Paquete regular de S/ 1,350 y pago pendiente de habilitación por izipay. |
| Disciplinas | Fulbito varones, fulbito mujeres, vóley mixto y básquet varones. |
| Proceso | "Registra → Validamos → Paga → Compite". |
| Reglamento | Reglas frecuentes, observaciones y validación por Comité. |
| Footer | Marca, Asociación Okinawense del Perú, redes sociales (Facebook, Instagram, TikTok). |

---

## Registro de Usuario

El registro crea al responsable que luego manejará la inscripción. El formulario usa validación con Zod y confirma aceptación de bases.

| Campo | Regla visible/en schema |
|-------|------------------------|
| `email` | Requerido, formato email (regex `^[^@\s]+@[^@\s]+\.[^@\s]+$`), máximo 120 caracteres. |
| `password` | Requerida, mínimo 8 caracteres, máximo 120. |
| `confirmPassword` | Requerida y debe coincidir con `password`. |
| `tipoDocumento` | `DNI`, `CE` o `PAS`; opcional en schema (default `'DNI'` en BD). La UI siempre lo envía con `defaultValues: "DNI"`. |
| `numeroDocumento` | **Condicional**: requerido SI `tipoDocumento` está presente. DNI: exactamente 8 dígitos; CE: exactamente 9 dígitos; PAS: mínimo 4 caracteres alfanuméricos. |
| `nombres` | Requerido, máximo 120 caracteres. |
| `apellidos` | Requerido, máximo 120 caracteres. |
| `genero` | Opcional: valores técnicos `V`/`M`; la UI muestra labels "Masculino"/"Femenino" (Select con valores `V`/`M`). |
| `telefono` | Opcional; si se informa, exactamente 9 dígitos. |
| `whatsapp` | Opcional; si se informa, exactamente 9 dígitos. |
| `emergencyName` (`contactoEmergenciaNombre` en BD) | Opcional, máximo 120 caracteres. |
| `emergencyPhone` (`contactoEmergenciaTelefono` en BD) | Opcional; si se informa, exactamente 9 dígitos. |
| `acceptedBases` | Debe ser `true`. Mostrado con texto "BASES-SF26-2026-09-06". |

**Camino tras registro exitoso**: `router.push("/inscripcion")` — va directo al wizard, no al dashboard.

---

## Login

El mockup muestra login por **tabs de DNI y email** (NO username).

| Modo | Campos | Validación |
|------|--------|------------|
| DNI | `dni`, `password` | DNI requerido con exactamente 8 dígitos; contraseña requerida. |
| Email | `email`, `password` | Email requerido válido; contraseña requerida. |

**Existe además** `LoginUsernameFormSchema` en el código (`src/features/auth/schemas/login.schema.ts`) que soporta login con username (mín 3 chars, alphanumeric + underscore), pero **NO se utiliza en la UI actual**.

### Redirect tras autenticación exitosa

Según `LoginForm.tsx` (líneas 248-263):
- Si hay `redirect` param, ir a ese valor.
- Si rol es `admin_comite` o `admin_finanzas`, ir a `/admin/dashboard`.
- De lo contrario (responsable), ir a `/dashboard`.

---

## Dashboard del Responsable

| Estado | Comportamiento |
|--------|----------------|
| Sin inscripción | Muestra bienvenida y botón `Preinscribir mi equipo` hacia `/inscripcion`. |
| Con inscripción | Muestra estado, equipo, monto, fecha, integrantes y cantidad de disciplinas. |
| Con observación | Muestra bloque `Observación del Comité`. |
| Con inscripción editable | Permite editar si el estado no es `validada`, `pagada`, `confirmada` ni `rechazada`. |

**Estados visibles**: `recibida`, `en_revision`, `observada`, `validada`, `pago_pendiente`, `pagada`, `confirmada`, `rechazada`.

**Componente**: `ResponsableDashboardView.tsx` — usa `InscripcionEditModal` para edición.

---

## Wizard de Inscripción

El wizard está en `/inscripcion` y requiere rol `responsable`. El mockup carga `basesId` desde catálogo y usa monto por defecto `1350`.

| Paso | Nombre | Qué captura/valida |
|------|--------|---------------------|
| 1 | Responsable | Muestra datos del usuario logueado (read-only) y solicita `promocionId`; permite `fusionPromocionId` opcional. |
| 2 | Equipo y nómina | Solicita `teamName` y al menos un deportista. Cada deportista puede asociarse a una o varias disciplinas. |
| 3 | Paquete y pago | **Solo informativo**: paquete S/ 1,350, deportistas registrados e izipay "Próximo a habilitar". No tiene inputs. |
| 4 | Declaraciones | Requiere aptitud física (`fitnessDeclaration`), consentimiento de imagen (`imageConsent`) y aceptación de bases (`acceptedBases`). Los tres en `false` por defecto. |

### Payload del Wizard

| Campo | Regla |
|-------|-------|
| `userId` | UUID del usuario logueado. |
| `promocionId` | UUID requerido. |
| `fusionPromocionId` | UUID opcional o `null`. |
| `basesId` | UUID requerido, cargado desde `/api/catalogs/bases`. |
| `paqueteMonto` | Número positivo; default visual `1350`. |
| `teamName` | Requerido, máximo 120 caracteres. |
| `deportistas` | Array con mínimo 1 deportista. |
| `acceptedBases` | Debe ser `true` (default `false` en el form). |
| `fitnessDeclaration` | Debe ser `true` (default `false`). |
| `imageConsent` | Debe ser `true` (default `false`). |

### Deportista en Nómina

| Campo | Regla |
|-------|-------|
| `tipoDocumento` | `DNI`, `CE` o `PAS`. Default UI: `"DNI"`. |
| `numeroDocumento` | Requerido; DNI 8 dígitos, CE 9 dígitos, PAS mínimo 4 caracteres. |
| `nombres` | Requerido, máximo 120 caracteres. |
| `apellidos` | Requerido, máximo 120 caracteres. |
| `genero` | Opcional, valores técnicos `V`/`M`. |
| `telefono` | Opcional; si se informa, 9 dígitos. |
| `rolDisciplina` | `Jugador`, `Capitán` o `Delegado`. **Default: `"Jugador"`** (schema línea 19: `.default('Jugador')`). |
| `acreditacion` | `Verificación en padrón` o `Excepción aprobada`. **Default en UI: `"Verificación en padrón"`** (hardcodeado en `handleAddPlayer`). |
| `disciplinaIds` | Mínimo una disciplina (array de UUID). |
| `shirtSize` | Opcional: `XS`, `S`, `M`, `L`, `XL`, `XXL`. |

**Botón "Usar mis datos"** en Step2Equipo: pre-popula el form con los datos del responsable logueado y pone `rolDisciplina: "Delegado"`.

---

## Roles y Permisos Visibles

| Rol | Acceso visible | Nota |
|-----|----------------|------|
| `responsable` | `/dashboard`, `/inscripcion`. | Gestiona una preinscripción propia. |
| `admin_comite` | `/admin/dashboard`, `/admin/comite/inscripciones`. | Revisa inscripciones y cambia estados. |
| `admin_finanzas` | `/admin/dashboard`, `/admin/comite/inscripciones`. | Mismas rutas que Comité. El mockup no separa claramente permisos financieros. |

**Redirect de rutas protegidas** (`require-role.ts`):
- `admin_comite` → `/admin/comite/inscripciones`
- `admin_finanzas` → `/admin/comite/inscripciones`
- `responsable` → `/dashboard`
- No autenticado → `/login`

---

## Catálogos y Datos de Referencia

| Concepto | Valores visibles/inferidos |
|----------|----------------------------|
| Bases | `BASES-SF26-2026-09-06`, aprobadas el 2026-09-05, activas. |
| Promociones | Años desde 1970 hasta el año actual (`new Date().getFullYear()`), colegio `ma`, nombre `Promoción {año}`, todas activas. |
| Colegios | `sjb` (no aparece en seed, solo `ma`). |
| Disciplinas | `fulbito_var` (max 12), `fulbito_dam` (max 12), `voley_mix` (max 12), `basket_var` (max 10). |
| Categorías | Junior, Senior, Master, Super Master (solo fulbito_var tiene Super Master). |

### Categorías Sembradas en el Mockup (del seed)

| Disciplina | Categorías/años |
|------------|-----------------|
| Fulbito varones | Junior 2012-2025; Senior 1998-2011; Master 1987-1997; **Super Master 1970-1986**. |
| Fulbito mujeres | Junior 2001-2024; Master 1975-2000. |
| Vóley mixto | Junior 2012-2025; Senior 1998-2011; **Master 1975-1986**. |
| Básquet varones | Junior 2012-2025; Senior 1998-2011; Master 1970-1997. |

**Nota**: La documentación anterior decía "Vóley mixto Master pendiente para 1987-1997". El seed real no indica estado pendiente — el rango es 1975-1986. Esto puede ser una decisión de negocio por confirmar.

---

## Conceptos de Datos Inferidos (candidatos a tablas)

| Concepto | Para qué sirve en el flujo |
|----------|----------------------------|
| Persona | Datos civiles/contacto compartidos por usuarios y deportistas. |
| Usuario | Cuenta autenticable con email, passwordHash y rol. |
| Sesión | Cookie/token de sesión (gestión de auth). |
| Promoción | Año/colegio del equipo responsable; permite fusión opcional. |
| Bases | Versión aceptada para la inscripción con fecha de aprobación. |
| Disciplina | Deporte disponible con máximo operativo de jugadores. |
| Categoría | Rango de años por disciplina. |
| Inscripción | Solicitud principal, estado, monto, declaraciones y observación. |
| Equipo | Combinación de inscripción, disciplina y categoría. |
| Deportista | Participante asociado a una persona y una inscripción. |
| Deportista-equipo | Relación muchos-a-muchos (tabla pivote) para que un deportista participe en varias disciplinas. |

---

## Qué Reutilizar Como Referencia

- La ruta mental del usuario: landing → registro/login → dashboard → inscripción → seguimiento.
- La división progresiva del wizard en 4 pasos (Step 3 es informativo).
- Los campos y validaciones visibles, especialmente documento por tipo, teléfonos de 9 dígitos y declaraciones obligatorias (3 checkboxes).
- Los estados de inscripción y cómo se comunican al responsable.
- El área del Comité para revisión, observación y cambio de estado (admin/comite/inscripciones).
- El redirect diferenciando admins vs responsables.
- Catálogos deportivos (4 disciplinas), rangos de categorías y monto base (S/ 1,350) como insumos.
- Copy útil de producto: validación por Comité, pago posterior, bases vigentes, izipay "Próximo a habilitar".

---

## Qué No Copiar Ciegamente

- La estructura Next.js/Drizzle del mockup como arquitectura final.
- Los nombres internos de carpetas, hooks, stores y Server Actions.
- El modelo de autorización sin revisar separación real entre Comité y Finanzas.
- Los valores técnicos `V`/`M` en UI sin labels humanos (la UI sí los traduce, pero la BD los almacena como `V`/`M`).
- Los rangos de categorías del seed como definitivos — especialmente vóley mixto Master.
- El seed de promociones solo con colegio `ma` si el producto final requiere ambos (`sjb` y `ma`).
- El flujo de pago izipay, que está marcado como "Próximo a habilitar" y no implementado.
- El schema `LoginUsernameFormSchema` que existe en el código pero **no se usa en la UI actual**.

---

## Preguntas Abiertas para Futuro `sdd-explore` / `sdd-apply`

| Tema | Pregunta |
|------|----------|
| Arquitectura | ¿Cómo se mapea este flujo al backend Django/contrato real sin heredar Drizzle ni Server Actions? |
| Login username | ¿El schema `LoginUsernameFormSchema` es遗留 (legacy) o está planeado para uso futuro? ¿Soportar username o no? |
| Responsables | ¿Una cuenta responsable puede tener una sola inscripción o varias por promoción/equipo? |
| Promociones | ¿Deben existir `sjb` y `ma` para todos los años o solo ciertos catálogos aprobados? |
| Fusión | ¿Qué reglas de negocio aplican cuando una promoción se fusiona con otra? |
| Categorías | ¿Cuál es la regla final para vóley mixto Master y los rangos 1987-1997? ¿El seed está correcto o falta actualizar? |
| Deportistas | ¿Un deportista puede participar en múltiples disciplinas sin límite? ¿Hay reglas de incompatibilidad? |
| Género | ¿Cómo se validan deportes por género usando labels humanos y datos normalizados (`V`/`M`)? |
| Comité/Finanzas | ¿Qué acciones son del Comité y cuáles son exclusivas de Finanzas? El mockup comparte rutas. |
| Pago | ¿Izipay entra al MVP o queda como estado/manualidad administrativa? |
| Bases | ¿Se debe guardar snapshot/versionado de aceptación por inscripción? |
| Mount minimums | ¿Cuál es el número mínimo y máximo de jogadores por equipo/disciplina? (El seed tiene `maxJugadores` pero no `minJugadores`). |
| Editabilidad | ¿Hasta qué estado permite el sistema editar inscripción? ¿Qué campos son editables post-envío? |

---

## Correcciones Respecto a Versión Anterior

1. **Login UI real**: Solo tabs DNI y Email. Se eliminó referencia incorrecta a tabs de "DNI" y "email" como "username".
2. **`acceptedBases` default**: En wizard el default es `false`, no `true`.
3. **Roles admin visibles**: Ahora se documentan `admin_comite` y `admin_finanzas` como ambos con acceso a admin.
4. **Redirect login**: Admins van a `/admin/dashboard` (no solo `/admin/comite/inscripciones`).
5. **Deportista rol default**: `Jugador` (no `Capitán`).
6. **Categorías vóley mixto**: Rango Master es 1975-1986, sin注明 de "pendiente" en el seed.
7. **`LoginUsernameFormSchema`**: Documentado como existente pero no usado en UI.
8. **Camino post-registro**: `router.push("/inscripcion")` (va directo al wizard, no al dashboard).
