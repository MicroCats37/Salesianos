# FR-08 — Fixtures provisionales tipadas para esqueletos de frontend

**Freeze:** `FREEZE-FX-1.0.0` · **Propietario:** A7 (frontend) + A0 (corte del contrato) · **Estado:** FROZEN (GOV-01)
**Trazabilidad:** `00-contrato-global-de-apply.md` §"Contract Freeze" · `00-workflow-frontend-contract-first.md` §"Stage 1" · `contract/api-wrapper-presenter-contract.md` §7

---

## 1. Cuándo existe una fixture provisional

Un esqueleto de frontend puede necesitar datos antes de que exista el presenter real. Para eso existe una **fixture provisional**, con reglas estrictas. **No** es un mock de producción, **no** es un fallback y **no** es un espejo de wire.

### 1.1 Las cinco condiciones (obligatorias)

Una fixture provisional **solo** existe si cumple **todas**:

1. Está marcada con el token literal **`PROVISIONAL_CONTRACT_FIXTURE`**.
2. Refleja un wrapper/presenter **con nombre** del plan o de este freeze (`FR-01`..`FR-07`).
3. Contiene **ejemplos**, no cálculos de negocio.
4. Vive **dentro del feature dueño**, no en archivos compartidos de API, schema ni query keys.
5. Su paquete de integración la **elimina o reemplaza** cuando el presenter/schema real queda congelado.

### 1.2 Forma obligatoria

```ts
/**
 * PROVISIONAL_CONTRACT_FIXTURE
 * Espeja: <NombreDelWrapper> (<módulo>, <ruta del plan>)
 * Versión de contrato referenciada: FREEZE-XX-1.0.0
 * NO PRODUCCIÓN. Sin reglas de negocio. Se elimina en <paquete de integración>.
 */
export const <nombre>Fixture = {
  ...
} as const satisfies <TipoDelWrapper>;
```

| Regla | Detalle |
|---|---|
| Marcador | El token `PROVISIONAL_CONTRACT_FIXTURE` aparece en el comentario de cabecera **y** en el nombre del símbolo (sufijo `Fixture`) |
| Tipo | `as const satisfies <Tipo>` sobre un **tipo TS**, no un schema Zod. Un Zod parecería un espejo de wire y podría confundirse con el real |
| Exports | **Prohibido** exportarlo desde un barrel de producción. Solo desde el módulo de fixtures del feature, y solo lo consumen tests y stories |
| Ubicación | `Aplicacion/frontend/src/features/<dominio>/fixtures/<nombre>.fixture.ts` |
| Prohibido | `src/lib/api.ts`, `src/lib/auth/**`, `src/providers/**`, `src/components/ui/**`, `features/*/schemas/**`, `features/*/utils/*.claves.utils.ts`, `features/*/services/**`, cualquier archivo de config o paquete |
| Determinismo | Valores literales fijos. **Prohibido** `Date.now()`, `Math.random()`, `crypto.randomUUID()` dentro del fixture |

### 1.3 Prohibición de reglas de negocio

**Prohibido** dentro de una fixture provisional:

| Prohibido | Ejemplo de lo que NO debe aparecer |
|---|---|
| Cálculo de precio o total | `total: items.reduce((s, i) => s + i.precio * i.cantidad, 0)` |
| Cálculo de elegibilidad | `esElegible: participante.categoria === discipline.categoria` |
| Cálculo de cupo o capacidad | `saldo: pagados - asignados` |
| Cálculo de estado de pago | `estado: orden.estado === "PAGADA" ? "CONFIRMADO" : "PENDIENTE"` |
| Cálculo de stock | `disponible: stock - reservado` |
| Cálculo de permiso o de acciones disponibles | `acciones: puedeEditar ? [...] : []` |
| Cálculo de transición de estado | `estado_operativo.codigo: derive(estado)` |
| Regla de negocio en el propio fixture | cualquier `if`/`switch` sobre datos de negocio |

Los valores de `plantilla.minimo`, `estado_operativo.codigo`, `precio` o `total` **pueden** aparecer como **literales**, porque el fixture los **declara**, no los **calcula**. La distinción es literal vs derivado.

### 1.4 Uso permitido

| Permitido | Prohibido |
|---|---|
| Renderizar un esqueleto de página con estados visibles | Servir datos a una ruta real |
| Test de componente / story | Exportar como servicio |
| Simular la forma de la respuesta para el layout | Usarse como **fallback** cuando la API falla |
| Mostrar estados loading/empty/error de una ruta skeleton | Convertirse en el camino de transporte real |

**Prohibido** que una fixture provisional se convierta en el camino de transporte por defecto: un `catch` que cae a la fixture es un mock en producción y está prohibido por el contrato global.

### 1.5 Ciclo de vida

```
UI-0x (esqueleto)          crea la fixture provisional marcada
   ↓
API-0x (integración)       reemplaza por el espejo Zod real + servicio + query keys
   ↓
T-082 (corte real)         prueba de que no queda importación, fallback ni ruta oculta
```

**Owner del corte:** A0 + A7. **Prueba de corte obligatoria:** ningún módulo fuera de tests/stories importa la fixture; el build y los tests de integración pasan sin ella.

## 2. Ejemplos tipados congelados

Los siguientes ejemplos son **la** forma canónica. Las fixtures de los esqueletos reales se derivan de aquí.

### 2.1 Edición activa — refleja `EdicionActualOut` (`FREEZE-ED-1.0.0`)

```ts
/**
 * PROVISIONAL_CONTRACT_FIXTURE
 * Espeja: EdicionActualOut (eventos, FR-02)
 * Contrato referenciado: FREEZE-ED-1.0.0
 * NO PRODUCCIÓN. Sin reglas de negocio. Se elimina en API-01.
 */
export type EdicionActualFixture = {
  id: string;
  evento_id: string;
  nombre: string;
  slug: string;
  anio: number;
  estado: "BORRADOR" | "PUBLICADA" | "CERRADA";
  modulos_habilitados: string[];
};

export const edicionActualFixture = {
  id: "00000000-0000-4000-8000-000000000001",
  evento_id: "00000000-0000-4000-8000-0000000000E1",
  nombre: "EDICION DE EJEMPLO",
  slug: "edicion-de-ejemplo",
  anio: 2026,
  estado: "PUBLICADA",
  modulos_habilitados: ["inscripciones", "pases"],
} as const satisfies EdicionActualFixture;
```

### 2.2 Veredicto operativo — refleja `EstadoOperativo` (`FREEZE-ENV-1.0.0`)

```ts
/**
 * PROVISIONAL_CONTRACT_FIXTURE
 * Espeja: EstadoOperativo (FR-01 §5) — codigo/etiqueta/descripcion
 * Contrato referenciado: FREEZE-ENV-1.0.0
 * NO PRODUCCIÓN. Sin reglas de negocio. Se elimina en API-04.
 */
export type EstadoOperativoFixture = {
  codigo: string;
  etiqueta: string;
  descripcion: string;
};

export const estadoOperativoPagoPendienteFixture = {
  codigo: "PENDIENTE",
  etiqueta: "Pago pendiente",
  descripcion: "El pago todavía no ha sido confirmado.",
} as const satisfies EstadoOperativoFixture;
```

### 2.3 Veredicto de equipo — refleja el presenter del plan `contratos/01` §3

```ts
/**
 * PROVISIONAL_CONTRACT_FIXTURE
 * Espeja: EquipoOperativoOut (plan contratos/01 §3, admin)
 * Contrato referenciado: FREEZE-ENV-1.0.0
 * NO PRODUCCIÓN. Sin reglas de negocio. Se elimina en API-04.
 */
export type EquipoOperativoFixture = {
  id: string;
  nombre: string;
  disciplina: { id: string; nombre: string };
  categoria: { id: string; nombre: string };
  plantilla: { registrados: number; minimo: number; maximo: number };
  estado_operativo: EstadoOperativoFixture;
  acciones_disponibles: string[];
};

export const equipoOperativoFixture = {
  id: "00000000-0000-4000-8000-0000000000A1",
  nombre: "EQUIPO DE EJEMPLO",
  disciplina: { id: "00000000-0000-4000-8000-0000000000D1", nombre: "DISCIPLINA DE EJEMPLO" },
  categoria: { id: "00000000-0000-4000-8000-0000000000C1", nombre: "CATEGORIA DE EJEMPLO" },
  plantilla: { registrados: 6, minimo: 7, maximo: 10 },
  estado_operativo: {
    codigo: "INCOMPLETO",
    etiqueta: "Falta 1 jugador",
    descripcion: "Se necesita al menos 7 jugadores para competir",
  },
  acciones_disponibles: ["VER_PARTICIPANTES", "AGREGAR_PARTICIPANTE"],
} as const satisfies EquipoOperativoFixture;
```

> `plantilla.minimo`, `plantilla.maximo` y `estado_operativo.codigo` son **literales declarados**, no valores derivados. La regla §1.3 prohíbe el *cálculo*, no la *declaración* de un ejemplo.

### 2.4 Veredicto de pago — refleja el presenter del plan `contratos/01` §4

```ts
/**
 * PROVISIONAL_CONTRACT_FIXTURE
 * Espeja: PagoOperativoOut (plan contratos/01 §4, admin)
 * Contrato referenciado: FREEZE-ENV-1.0.0
 * NO PRODUCCIÓN. Sin reglas de negocio. Se elimina en API-04.
 */
export type PagoOperativoFixture = {
  compra_id: string;
  orden_pago_id: string | null;
  tipo_compra: "INSCRIPCION" | "PASE" | "MARKETPLACE";
  resumen_concepto: string;
  comprador: { persona_id: string; nombre: string };
  monto: string;
  moneda: string;
  estado_operativo: EstadoOperativoFixture;
  entrega_derechos: { codigo: string; etiqueta: string };
  acciones_disponibles: string[];
};

export const pagoOperativoFixture = {
  compra_id: "00000000-0000-4000-8000-0000000000B1",
  orden_pago_id: "00000000-0000-4000-8000-0000000000F1",
  tipo_compra: "INSCRIPCION",
  resumen_concepto: "RESUMEN DE EJEMPLO",
  comprador: { persona_id: "00000000-0000-4000-8000-0000000000B2", nombre: "COMPRADOR DE EJEMPLO" },
  monto: "0.00",
  moneda: "PEN",
  estado_operativo: {
    codigo: "PENDIENTE",
    etiqueta: "Pago pendiente",
    descripcion: "El pago todavía no ha sido confirmado.",
  },
  entrega_derechos: {
    codigo: "SIN_ENTREGA",
    etiqueta: "Sin derechos habilitados",
  },
  acciones_disponibles: ["VER_INSCRIPCION", "VER_HISTORIAL"],
} as const satisfies PagoOperativoFixture;
```

> `monto` es `"0.00"` a propósito: un monto de ejemplo **no** puede parecer un precio real. El monto nunca se calcula en el frontend.

### 2.5 Paginación — refleja la forma única de `FR-01` §4.3

```ts
/**
 * PROVISIONAL_CONTRACT_FIXTURE
 * Espeja: PaginatedData (FR-01 §4.3) — items/total/page/page_size/total_pages
 * Contrato referenciado: FREEZE-ENV-1.0.0
 * NO PRODUCCIÓN. Sin reglas de negocio. Se elimina en API-04.
 */
export type PaginaFixture<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export const paginaVaciaFixture = {
  items: [],
  total: 0,
  page: 1,
  page_size: 25,
  total_pages: 0,
} as const satisfies PaginaFixture<never>;
```

### 2.6 Error con errores por campo — refleja `FR-01` §4.2

```ts
/**
 * PROVISIONAL_CONTRACT_FIXTURE
 * Espeja: ApiResponse de error con field_errors (FR-01 §4.2)
 * Contrato referenciado: FREEZE-ENV-1.0.0
 * NO PRODUCCIÓN. Sin reglas de negocio. Se elimina en API-04.
 */
export type ErrorFieldErrorsFixture = {
  success: false;
  data: null;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    field_errors?: { field: string; code: string; message: string }[];
  };
  message: null;
};

export const errorCamposFixture = {
  success: false,
  data: null,
  error: {
    code: "VALIDATION_ERROR",
    message: "Revisa los datos ingresados.",
    details: { non_field_errors: "Detalle de ejemplo." },
    field_errors: [
      { field: "email", code: "INVALID_FORMAT", message: "El correo no tiene un formato válido." },
    ],
  },
  message: null,
} as const satisfies ErrorFieldErrorsFixture;
```

### 2.7 Preview de ticket — refleja `FR-05` §3.1

```ts
/**
 * PROVISIONAL_CONTRACT_FIXTURE
 * Espeja: TicketPreviewOut (FR-05 §3.1)
 * Contrato referenciado: FREEZE-RT-1.0.0
 * NO PRODUCCIÓN. Sin reglas de negocio. Se elimina en API-05.
 */
export type TicketPreviewFixture = {
  tipo_derecho: "PASE" | "ENTRADA_CORTESIA" | "PRODUCTO" | "INSCRIPCION";
  codigo: string;
  titular: { persona_id: string; nombre: string };
  edicion_id: string;
  estado: string;
  cantidad_total: number;
  cantidad_disponible: number;
  cantidad_consumida: number;
  puede_canjear: boolean;
  motivo_codigo: string | null;
  motivo_mensaje: string | null;
};

export const ticketPreviewFixture = {
  tipo_derecho: "PASE",
  codigo: "PASE_FIESTA",
  titular: { persona_id: "00000000-0000-4000-8000-0000000000B2", nombre: "TITULAR DE EJEMPLO" },
  edicion_id: "00000000-0000-4000-8000-000000000001",
  estado: "HABILITADO",
  cantidad_total: 1,
  cantidad_disponible: 1,
  cantidad_consumida: 0,
  puede_canjear: true,
  motivo_codigo: null,
  motivo_mensaje: null,
} as const satisfies TicketPreviewFixture;
```

## 3. Registro de fixtures provisionales

El registro se mantiene en la evidencia del paquete que crea cada fixture. Formato:

| Fixture | Espeja | Contrato | Creado por | Se elimina en | Estado |
|---|---|---|---|---|---|
| `edicionActualFixture` | `EdicionActualOut` | `FREEZE-ED-1.0.0` | UI-01 | API-01 | pendiente |
| `estadoOperativoPagoPendienteFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | UI-04 | API-04 | pendiente |
| `equipoOperativoFixture` | `EquipoOperativoOut` | `FREEZE-ENV-1.0.0` | UI-04 | API-04 | pendiente |
| `pagoOperativoFixture` | `PagoOperativoOut` | `FREEZE-ENV-1.0.0` | UI-04 | API-04 | pendiente |
| `paginaVaciaFixture` | `PaginatedData` | `FREEZE-ENV-1.0.0` | UI-02..UI-05 | API-02..API-05 | pendiente |
| `errorCamposFixture` | `ApiResponse` de error | `FREEZE-ENV-1.0.0` | UI-02 | API-02 | pendiente |
| `ticketPreviewFixture` | `TicketPreviewOut` | `FREEZE-RT-1.0.0` | UI-05 | API-05 | pendiente |

**Estado:** ninguno creada todavía. Este freeze fija el **contrato** de la fixture; la creación ocurre en los paquetes UI-0x, cada uno registrando su entrada.

## 4. Criterios de aceptación de este freeze

- [x] Las cinco condiciones de existencia de una fixture provisional, verificables una por una.
- [x] Forma obligatoria (marcador, tipo TS con `satisfies`, ubicación, prohibiciones).
- [x] Prohibición explícita de reglas de negocio, con la distinción literal vs derivado.
- [x] Ciclo de vida con owner del corte y prueba de corte.
- [x] Siete ejemplos tipados canónicos, todos marcados `PROVISIONAL_CONTRACT_FIXTURE` y sin reglas de negocio.
- [x] Registro de fixtures con el paquete que la crea y el que la elimina.

## 5. Decisiones abiertas relacionadas

| ID | Pendiente | Owner |
|---|---|---|
| `GOV-01-OPEN-13` | Storybook o equivalente como consumidor formal de fixtures provisionales | A7 |
