import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * The static audit of the registration area.
 *
 * The five widths and the a11y contract cannot be measured in this packet:
 * no browser is run. What CAN be frozen here is the RULE that the markup
 * has to obey, so a later packet that opens a browser checks a contract and
 * not an opinion.
 *
 * The files are read as SOURCE, the same way the account audit does it.
 */
const RAIZ = join(process.cwd(), "src", "features", "inscripciones");

const FUENTES = [
  "components/FormularioParticipante.tsx",
  "components/PanelBeneficios.tsx",
  "components/PanelCompras.tsx",
  "components/PanelEquipos.tsx",
  "components/PanelParticipantes.tsx",
  "components/PanelPool.tsx",
  "components/PasoConfirmacion.tsx",
  "components/PasoEquipos.tsx",
  "components/PasoPaquete.tsx",
  "components/PasoPromocion.tsx",
  "components/PasoResumen.tsx",
  "components/PaqueteCard.tsx",
  "components/SeccionParticipantes.tsx",
  "components/WizardStepper.tsx",
  "views/InscripcionWizardView.tsx",
  "views/MisInscripcionDetalleView.tsx",
];

const FUENTE = Object.fromEntries(
  FUENTES.map((ruta) => [ruta, readFileSync(join(RAIZ, ruta), "utf8")]),
);

/**
 * The layers that talk to the server.
 *
 * The rule of the business belongs to them as much as to the presentation:
 * a hook that subtracted cupos or multiplied a price would resolve in the
 * browser what the server owns (`RN-C02`, `RN-I03`).
 */
const FUENTES_NEGOCIO = [
  "hooks/useCatalogo.ts",
  "hooks/useCotizacion.ts",
  "hooks/useInscripcion.ts",
  "hooks/useInscripcionMutaciones.ts",
  "services/catalogo.service.ts",
  "services/cotizacion.service.ts",
  "services/inscripcion.service.ts",
  "services/respuesta.service.ts",
  "utils/inscripcion.claves.utils.ts",
  "utils/inscripcion.errores.utils.ts",
  "utils/inscripcion.payloads.utils.ts",
];

const FUENTE_NEGOCIO = Object.fromEntries(
  FUENTES_NEGOCIO.map((ruta) => [ruta, readFileSync(join(RAIZ, ruta), "utf8")]),
);

describe("UI-02 — la inscripción no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = FUENTE[ruta];

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
    expect(fuente).not.toMatch(/\b(text|bg|border)-\[#[0-9a-fA-F]/);
  });

  it.each(FUENTES)("%s no lleva un ancho fijo en píxeles", (ruta) => {
    expect(FUENTE[ruta]).not.toMatch(/\bw-\[\d{3,}px\]/);
  });
});

describe("UI-02 — la tabla declara sus cabeceras (SH-02 2.2)", () => {
  it("PanelParticipantes marca cada columna con scope", () => {
    const fuente = FUENTE["components/PanelParticipantes.tsx"];
    const cabeceras = fuente.match(/<TableHead/g) ?? [];
    const conScope = fuente.match(/<TableHead scope="col"/g) ?? [];

    expect(cabeceras.length).toBeGreaterThan(0);
    expect(conScope.length).toBe(cabeceras.length);
  });

  it("PanelParticipantes ofrece la tabla desde 1024 y las tarjetas por debajo", () => {
    const fuente = FUENTE["components/PanelParticipantes.tsx"];

    expect(fuente).toContain("hidden lg:block");
    expect(fuente).toContain("lg:hidden");
  });
});

describe("UI-02 — el ancho de trabajo no desborda", () => {
  it.each(FUENTES)(
    "%s no empuja la página con un scroll horizontal",
    (ruta) => {
      expect(FUENTE[ruta]).not.toMatch(/\boverflow-x-auto/);
    },
  );
});

describe("UI-02 — el área táctil y el foco", () => {
  it("las acciones del asistente dejan 44 px de alto", () => {
    expect(FUENTE["views/InscripcionWizardView.tsx"]).toContain("min-h-11");
    expect(FUENTE["components/PasoEquipos.tsx"]).toContain("min-h-11");
  });
});

describe("UI-02 — el vocabulario del proveedor nunca aparece", () => {
  it.each(FUENTES)("%s no nombra un estado del proveedor", (ruta) => {
    const fuente = FUENTE[ruta];

    expect(fuente).not.toContain("settlement_status");
    expect(fuente).not.toContain("settlementStatus");
    expect(fuente).not.toContain("CAPTURED");
  });
});

describe("UI-02 — el navegador no calcula el negocio", () => {
  it.each(FUENTES)("%s no multiplica cupos ni precios", (ruta) => {
    const fuente = FUENTE[ruta];

    // Una resta o una multiplicación de cupos o de dinero en el navegador
    // sería el dominio resuelto en el cliente (RN-C02, RN-I03).
    expect(fuente).not.toMatch(/cupos_pagados\s*-\s*/);
    expect(fuente).not.toMatch(/cupos_incluidos\s*\*/);
    expect(fuente).not.toMatch(/precio\.[a-z]+\s*\*/);
    expect(fuente).not.toMatch(/monto\s*\*/);
  });

  it.each(FUENTES_NEGOCIO)("%s no calcula ni un cupo", (ruta) => {
    const fuente = FUENTE_NEGOCIO[ruta];

    expect(fuente).not.toMatch(/cupos_pagados\s*-\s*/);
    expect(fuente).not.toMatch(/cupos_asignados\s*-\s*/);
    expect(fuente).not.toMatch(/cupos_disponibles\s*-\s*/);
    expect(fuente).not.toMatch(/cupos_incluidos\s*\*/);
    expect(fuente).not.toMatch(/total\s*\*/);
    expect(fuente).not.toMatch(/monto\s*\*/);
  });

  it.each(FUENTES_NEGOCIO)(
    "%s no inventa una ruta del backend congelado",
    (ruta) => {
      const fuente = FUENTE_NEGOCIO[ruta];

      // La inscripción atómica del backend congelado no existe en el objetivo.
      expect(fuente).not.toContain("/inscripciones/completa");

      // Las rutas RESTAURADAS existen, pero SIN la barra final del árbol
      // congelado: el estilo del backend objetivo es sin barra.
      expect(fuente).not.toContain("/cotizaciones/");
      expect(fuente).not.toContain("/catalogo/promociones/");
      expect(fuente).not.toContain("/catalogo/categorias/");
    },
  );

  it.each(FUENTES)("%s no deriva la categoría de la promoción", (ruta) => {
    const fuente = FUENTE[ruta];

    // Comparar el año de una promoción con el rango de una categoría en el
    // navegador sería resolver en el cliente una regla del servidor
    // (`RN-C02`, `QA-K01`).
    expect(fuente).not.toMatch(/promocion_desde\s*[<>]=?\s*/);
    expect(fuente).not.toMatch(/promocion_hasta\s*[<>]=?\s*/);
    expect(fuente).not.toMatch(/anio\s*[<>]=?\s*.*promocion/);
  });

  it("el asistente NO envía la categoría de los equipos", () => {
    const fuente = FUENTE_NEGOCIO["utils/inscripcion.payloads.utils.ts"];

    expect(fuente).not.toContain("categoria_id");
  });
});
