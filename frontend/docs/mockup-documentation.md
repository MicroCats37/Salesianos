# Documentación del Mockup — Salesianos FEST 2026

> **Origen:** `mokup/` (exportación estática compilada desde el sitio original `salesianos-fest-2026-registro.ciplimai.chatgpt.site`)
> **Fecha de documentación:** 2026-09-13
> **Alcance:** Inventario funcional y de UX para reproducir el flujo en una app fullstack real (Next.js + Drizzle + JWT).

---

## 1. Identidad del Producto

| Atributo | Valor |
|----------|-------|
| Nombre comercial | **Salesianos FEST 2026** |
| Tagline | "Rumbo a la Mayordomía 2027" |
| Subtítulo | "Tu promoción vuelve a la cancha" |
| Eslogan secundario | "Deporte · Familia · Diversión" |
| Organización | Asociación Okinawense del Perú — Promoción 2002 (Bodas de Plata) |
| Sede | Av. Asturias 588 — Ate |
| Fecha del evento | Sábado 21 de noviembre de 2026 |
| Documento normativo | `BASES-SF26-2026-09-06` (aprobado 2026-09-05) |

---

## 2. Inventario de Pantallas / Secciones

El sitio es una **single-page estática** con anchors. Estructura:

| # | Sección | ID | Propósito |
|---|---------|----|-----------|
| 1 | Hero | `#inicio` | Portada con datos clave (fecha, sede, disciplinas, estado) |
| 2 | Galería | (sin id) | 4 cards de imágenes: Vóley jóvenes, Fulbito senior, Básquet máster, Súper máster confraternidad |
| 3 | Paquetes | `#paquetes` | Pricing (S/ 1,350 regular) + aviso de izipay bloqueado |
| 4 | Proceso | `#proceso` | Línea de tiempo 01→04: Registra → Validamos → Paga → Compite |
| 5 | Disciplinas | (sin id) | Cobertura deportiva con detalle de categorías por edad |
| 6 | **Formulario de inscripción** | `#inscripcion` | Núcleo de la app — preinscripción del equipo |
| 7 | Reglamento | `#reglamento` | Accordion con criterios de inscripción |
| 8 | Footer | — | Marca + tagline |

---

## 3. Formulario de Inscripción (`#inscripcion`)

El formulario está implementado en el bundle compilado `assets/registration-form-B3a-dJqM.js` (53 KB). Por el contexto del sitio y las reglas visibles, los campos mínimos esperados son:

### 3.1 Bloque: Datos del Responsable

| Campo | Tipo | Validación mockup |
|-------|------|-------------------|
| Nombres y apellidos | text | requerido |
| Documento (DNI/CE/Pasaporte) | text | requerido, formato según tipo |
| Email | email | requerido, válido |
| Teléfono (WhatsApp) | tel | requerido, 9 dígitos (PE) |
| Relación con la promoción | select | responsable / delegado / capitán |

### 3.2 Bloque: Datos de la Promoción

| Campo | Tipo | Validación |
|-------|------|-----------|
| Promoción (año de egreso) | select | requerido, lista cerrada de promociones válidas |
| Colegio de procedencia | select | San Juan Bosco / María Auxiliadora de Ayacucho |
| Nombre del equipo | text | opcional (autogenerado si vacío) |
| Cantidad de disciplinas a inscribir | counter | 1–4 (fulbito var, fulbito dam, vóley mix, básquet var) |

### 3.3 Bloque: Disciplinas + Nóminas

Por cada disciplina seleccionada:

| Campo | Tipo | Validación |
|-------|------|-----------|
| Disciplina | radio | una de las 4 disponibles |
| Categoría | select | según disciplina y rango etario |
| Nómina de jugadores | repeater (mín 5, máx según disciplina) | DNI, nombres, apellidos, fecha nacimiento, categoría |

Reglas duras (de las bases):

- **Fulbito varones:** máx 12 jugadores, categorías Junior / Senior / Máster / Súper Máster.
- **Fulbito mujeres:** máx 12 jugadoras, Junior / Máster.
- **Vóley mixto:** máx 12 jugadores, en cancha mín 2 / máx 3 varones.
- **Básquet varones:** máx 10 jugadores, Junior / Senior / Máster.
- **No duplicados** de DNI dentro de la misma nómina.
- **Cruce entre equipos:** cada jugador no puede integrar otro equipo de la misma disciplina.

### 3.4 Bloque: Aceptación y Envío

| Campo | Tipo |
|-------|------|
| Aceptación de bases (checkbox) | requerido |
| Declaración jurada de exalumno (checkbox) | requerido |
| Botón "Enviar preinscripción" | submit |

---

## 4. Reglas de Negocio Visibles

| # | Regla | Estado en mockup | Implicación técnica |
|---|-------|------------------|---------------------|
| R1 | Una promoción puede inscribir **un equipo por disciplina** | descrito | constraint único `(promocion_id, disciplina_id)` |
| R2 | Pago se habilita solo **después de validar nómina** | banner "Pago con izipay" bloqueado | flujo de estados `pendiente → validado → pagado → confirmado` |
| R3 | Duplicados de DNI bloqueados | FAQ regla 3 | validación server-side y UNIQUE constraint |
| R4 | Observaciones notifican por email/WhatsApp | FAQ regla 4 | canal notificación configurable |
| R5 | Suplantación → descalificación del equipo | banner "Bases aprobadas" | flag `acreditado` por jugador + log |
| R6 | Tarifa regular S/ 1,350 | card paquete | campo `paquete_id` referenciando catálogo |
| R7 | Bases vigentes al 2026-09-05 | card | snapshot de `bases_aceptadas_id` con timestamp |

---

## 5. Flujo de Estados de la Inscripción

```
[REGISTRA] → [RECIBIDA] → [EN REVISIÓN] → [VALIDADA] → [PAGO PENDIENTE] → [PAGADA] → [CONFIRMADA]
                  ↓                ↓
            [OBSERVADA]      [RECHAZADA]
                  ↓
            [SUBSANADA] → vuelve a EN REVISIÓN
```

Estados inferidos del texto del proceso y de las FAQ:
- `RECIBIDA` — form enviado con éxito
- `EN REVISION` — Comité está validando elegibilidad/cupo/duplicados
- `OBSERVADA` — hay objeciones; responsable debe subsanar
- `VALIDADA` — nómina aprobada, habilita pago
- `PAGO_PENDIENTE` — esperando orden izipay
- `PAGADA` — pago conciliado
- `CONFIRMADA` — equipo listo para competir
- `RECHAZADA` — terminada sin confirmación

---

## 6. Stack Técnico del Mockup

| Capa | Tecnología detectada |
|------|----------------------|
| Framework | Next.js (compilado a estático — `__VINEXT_RSC_CHUNKS__`) |
| UI | Radix UI (accordion primitives), Tailwind, lucide-react |
| Build output | HTML + JS + CSS estáticos, sin backend |
| Hosting | GitHub Pages (`pages.yml`) |
| Pago | izipay — **no implementado**, banner de aviso |

---

## 7. Diferencias: Mockup ↔ Producto Final

| Capacidad | Mockup | Producto final (este proyecto) |
|-----------|--------|--------------------------------|
| Persistencia | ninguna | DB con Drizzle (Postgres o SQLite) |
| Autenticación | ninguna | JWT (registro + login) |
| Roles | ninguno | responsable + admin_comite + finanzas (a confirmar) |
| Validación de nómina | no existe | backend valida duplicados + cupo + categoría |
| Pago izipay | banner "bloqueado" | integración diferida (módulo aparte) |
| Observaciones | FAQ estática | flujo real con notificación email/WhatsApp |
| Admin | no existe | dashboard aparte para Comité |

---

## 8. Riesgos y Supuestos Detectados

| # | Riesgo / Supuesto | Acción sugerida |
|---|--------------------|-----------------|
| S1 | El bundle JS del mockup está minificado — los nombres exactos de campos no son visibles | Levantar el mockup en navegador y abrir DevTools para confirmar campos reales |
| S2 | El documento de bases menciona artículos 14, 20, 26 con reglas detalladas que no están copiadas en el sitio | Solicitar el PDF de bases `BASES-SF26-2026-09-06` |
| S3 | El rango etario "Máster 1987-1997" de vóley mixto está marcado "pendiente de precisión" | Confirmar con Comité antes de cerrar reglas |
| R1 | Si izipay queda fuera de alcance, el flujo de pago queda pendiente — UX debe mostrar estado explícito | Diseñar `PAGO_PENDIENTE` como estado terminal visible, no como error |
| R2 | Validación de exalumno no es trivial: carnet, padrón, o declaración jurada | Decidir método de validación en explore |

---

## 9. Artefactos a Generar en el Explore

Antes de proponer arquitectura técnica, necesito resolver:

1. **DB target**: SQLite (dev rápido) vs Postgres (producción).
2. **Estrategia API**: Next.js Route Handlers (`app/api/...`) vs Server Actions puras.
3. **JWT storage**: cookies httpOnly (server-set) vs localStorage (client-set).
4. **Estilo del formulario**: single-page largo vs wizard multi-step.
5. **Roles iniciales** y matriz de permisos mínima.
6. **Alcance del MVP**: ¿incluye admin del Comité o solo el flujo del responsable?
7. **Validación de exalumno**: carnet, padrón, o declaración jurada.

> Las respuestas a estos puntos se incorporarán a `sdd/{change}/explore` antes del `propose`.
