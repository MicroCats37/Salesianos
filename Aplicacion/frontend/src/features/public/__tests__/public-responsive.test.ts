import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * The static audit of the public area of the packet.
 *
 * Same purpose as the account audit: the browser pass is deferred, so the
 * RULE the markup obeys is frozen here instead of an opinion about it.
 */
const RAIZ = join(process.cwd(), "src", "features", "public");

const FUENTES = [
  "components/IndiceInformacion.tsx",
  "components/RecuperarCompraForm.tsx",
  "views/InformacionView.tsx",
  "views/RecuperarCompraView.tsx",
];

const FUENTE = Object.fromEntries(
  FUENTES.map((ruta) => [ruta, readFileSync(join(RAIZ, ruta), "utf8")]),
);

describe("UI-01 — el índice de anclas es real", () => {
  it("cada sección que el índice anuncia tiene su ancla en la página", () => {
    const vista = FUENTE["views/InformacionView.tsx"];
    const indice = FUENTE["components/IndiceInformacion.tsx"];

    // El índice y la página leen la MISMA lista de secciones.
    expect(indice).toContain("aria-current");
    expect(vista).toContain("scroll-mt-24");
    expect(indice).toContain("lg:hidden");
    expect(indice).toContain("hidden lg:block");
  });

  it("el índice expone un nombre accesible", () => {
    expect(FUENTE["components/IndiceInformacion.tsx"]).toContain(
      'aria-label="Contenido de esta página"',
    );
  });
});

describe("UI-01 — la zona pública no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = FUENTE[ruta];

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(/\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/);
  });
});

describe("UI-01 — el formulario de recuperación", () => {
  it("asocia el error a su campo y declara el tipo del correo", () => {
    const fuente = FUENTE["components/RecuperarCompraForm.tsx"];

    expect(fuente).toContain('aria-invalid={Boolean(error)}');
    expect(fuente).toContain('aria-describedby={error ? "correo-error" : undefined}');
    expect(fuente).toContain('type="email"');
    expect(fuente).toContain('autoComplete="email"');
  });

  it("el error tiene un resumen que se anuncia", () => {
    const fuente = FUENTE["components/RecuperarCompraForm.tsx"];

    expect(fuente).toContain('role="alert"');
    expect(fuente).toContain("tabIndex={-1}");
  });

  it("los campos y el botón tienen 44 px de alto", () => {
    const fuente = FUENTE["components/RecuperarCompraForm.tsx"];

    expect(fuente).toContain("min-h-11");
  });

  it("la respuesta nunca depende de que exista una compra", () => {
    const fuente = FUENTE["components/RecuperarCompraForm.tsx"];

    expect(fuente).toContain("exista o no");
    expect(fuente).not.toMatch(/encontramos tu compra/i);
  });
});
