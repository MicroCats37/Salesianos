import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * The static audit of the account area.
 *
 * The five widths and the a11y contract cannot be measured in this packet:
 * no browser is run. What CAN be frozen here is the RULE that the markup
 * has to obey, so a later packet that opens a browser checks a contract and
 * not an opinion.
 *
 * The files are read as SOURCE, the same way the portada audit does it.
 */
const RAIZ = join(process.cwd(), "src", "features", "cuenta");

const FUENTES = [
  "components/BarraFiltros.tsx",
  "components/EstadoIndeterminado.tsx",
  "components/ListaCompras.tsx",
  "components/ListaInscripciones.tsx",
  "components/SinResultadosConFiltros.tsx",
  "components/VeredictoEstado.tsx",
  "views/MiCuentaView.tsx",
  "views/MisCompraDetalleView.tsx",
  "views/MisComprasView.tsx",
  "views/MisInscripcionesView.tsx",
];

const FUENTE = Object.fromEntries(
  FUENTES.map((ruta) => [ruta, readFileSync(join(RAIZ, ruta), "utf8")]),
);

describe("UI-01 — la cuenta no inventa colores literales (T-01)", () => {
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

describe("UI-01 — la tabla declara sus cabeceras (SH-02 2.2)", () => {
  it.each(["components/ListaCompras.tsx", "components/ListaInscripciones.tsx"])(
    "%s marca cada columna con scope",
    (ruta) => {
      const fuente = FUENTE[ruta];
      const cabeceras = fuente.match(/<TableHead/g) ?? [];
      const conScope = fuente.match(/<TableHead scope="col"/g) ?? [];

      expect(cabeceras.length).toBeGreaterThan(0);
      expect(conScope.length).toBe(cabeceras.length);
    },
  );
});

describe("UI-01 — el ancho de trabajo no desborda", () => {
  it.each(FUENTES)(
    "%s no empuja la página con un scroll horizontal",
    (ruta) => {
      expect(FUENTE[ruta]).not.toMatch(/\boverflow-x-auto/);
    },
  );

  it.each(["components/ListaCompras.tsx", "components/ListaInscripciones.tsx"])(
    "%s ofrece la tabla desde 1024 y las tarjetas por debajo",
    (ruta) => {
      const fuente = FUENTE[ruta];

      expect(fuente).toContain("hidden lg:block");
      expect(fuente).toContain("lg:hidden");
    },
  );
});

describe("UI-01 — el área táctil y el foco", () => {
  it.each(["components/ListaCompras.tsx", "components/ListaInscripciones.tsx"])(
    "%s deja el siguiente paso con 44 px de alto",
    (ruta) => {
      expect(FUENTE[ruta]).toContain("min-h-11");
    },
  );
});

describe("UI-01 — el vocabulario del proveedor nunca aparece", () => {
  it.each(FUENTES)("%s no nombra un estado del proveedor", (ruta) => {
    const fuente = FUENTE[ruta];

    expect(fuente).not.toContain("settlement_status");
    expect(fuente).not.toContain("settlementStatus");
    expect(fuente).not.toContain("CAPTURED");
  });
});
