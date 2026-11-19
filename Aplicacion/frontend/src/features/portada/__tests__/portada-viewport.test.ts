import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * El contrato vertical de la portada.
 *
 * La portada tiene su propio chrome (un navbar sticky) y una serie de
 * secciones pensadas para ocupar "una pantalla". El defecto que corrigió
 * este paquete era que esas secciones se medían contra el viewport ENTERO
 * (100svh) POR ENCIMA de ese chrome: el navbar se comía la parte superior de
 * la primera pantalla y el titular quedaba por debajo del pliegue.
 *
 * Aquí se fija la regla, no la maquetación:
 *
 * 1. La altura del chrome persistente es UN token, y el navbar lo consume: el
 *    número no puede desincronizarse del layout.
 * 2. Una sección "de una pantalla" mide el espacio DISPONIBLE (viewport menos
 *    chrome) y es un `min-height`: si el contenido no cabe, la sección crece
 *    y nunca recorta.
 * 3. En móvil no se fuerza la composición de una pantalla: la sección fluye.
 * 4. El scroll-snap es `proximity`: con `mandatory`, una sección más alta que
 *    la pantalla deja el scroll secuestrado.
 */
const RAIZ = join(process.cwd(), "src");

const globals = readFileSync(join(RAIZ, "app", "globals.css"), "utf8");
const navbar = readFileSync(
  join(RAIZ, "features", "portada", "components", "Navbar.tsx"),
  "utf8",
);
const hero = readFileSync(
  join(RAIZ, "features", "portada", "components", "HeroPortada.tsx"),
  "utf8",
);
const seccion = readFileSync(
  join(RAIZ, "features", "portada", "components", "PortadaSection.tsx"),
  "utf8",
);
const momentos = readFileSync(
  join(RAIZ, "features", "portada", "components", "MomentosSection.tsx"),
  "utf8",
);
const snap = readFileSync(
  join(RAIZ, "features", "portada", "components", "ScrollSnapScope.tsx"),
  "utf8",
);
const marca = readFileSync(
  join(RAIZ, "components", "brand", "FestBrandHeader.tsx"),
  "utf8",
);

/** Las secciones que se“Allanan” con el viewport. */
const SECCIONES: [string, string][] = [
  ["HeroPortada", hero],
  ["PortadaSection", seccion],
  ["MomentosSection", momentos],
];

describe("portada — el chrome persistente es la única fuente de verdad", () => {
  it("declara el token del chrome de la portada", () => {
    expect(globals).toContain("--portada-chrome-height:");
  });

  it("el navbar consume el token y no un alto suelto", () => {
    expect(navbar).toContain("h-[var(--portada-chrome-height)]");
    expect(navbar).not.toContain("h-[74px]");
  });

  it("la altura disponible descuenta el chrome", () => {
    expect(globals).toContain("@utility portada-altura-disponible");
    expect(globals).toContain(
      "min-height: calc(100svh - var(--portada-chrome-height))",
    );
  });
});

describe("portada — una sección de una pantalla mide el espacio disponible", () => {
  it.each(SECCIONES)("%s no reclama el viewport entero", (_n, fuente) => {
    expect(fuente).toContain("portada-altura-disponible");
    expect(fuente).not.toMatch(/min-h-svh|min-h-screen|h-svh|h-screen/);
  });

  it.each(SECCIONES)(
    "%s ancla el scroll por debajo del chrome",
    (_n, fuente) => {
      expect(fuente).toContain("scroll-mt-[var(--portada-chrome-height)]");
    },
  );

  it("la composición de una pantalla es de escritorio: el móvil fluye", () => {
    for (const [, fuente] of SECCIONES) {
      expect(fuente).toContain("lg:portada-altura-disponible");
    }
  });
});

describe("portada — el hero se adapta a la altura disponible", () => {
  it("el lockup de marca escala con la altura de la pantalla", () => {
    // El escudo y el wordmark son los bloques más altos del hero: a un alto
    // fijo empujaban el titular fuera de la pantalla.
    expect(hero).toContain("size-[clamp(");
    expect(hero).toContain("wordmarkHeight=");
    expect(marca).toContain("wordmarkHeight?: number | string");
  });

  it("el titular se encoge cuando la pantalla es baja", () => {
    expect(hero).toContain("lg:text-[clamp(");
  });

  it("el relleno vertical de la sección también es fluido", () => {
    expect(hero).toContain("py-[clamp(");
  });
});

describe("portada — el scroll-snap no secuestra el scroll", () => {
  it("usa proximity, no mandatory", () => {
    expect(snap).toContain("snap-proximity");
    expect(snap).not.toContain("snap-mandatory");
  });
});
