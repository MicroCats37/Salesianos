import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * The guard of the token system.
 *
 * Rule T-01 of `evidence/routes/SH-01`: no component carries a literal colour.
 * A component asks for a ROLE (`bg-primary`, `text-muted-foreground`) and the
 * role resolves the colour in both themes. A literal breaks that: it has no
 * counterpart in the dark theme and it drags the palette of the default
 * Tailwind into a product whose identity is institutional blue and gold.
 *
 * The ONLY exception is a colour that comes from runtime data (for example the
 * colour of a category published by the backend). It must be declared here,
 * in `EXCEPCIONES`, with the file and the reason.
 */
const EXCEPCIONES: { archivo: string; motivo: string }[] = [];

const RAIZ = join(process.cwd(), "src");
const CARPETAS = ["components", "features"];

/** The guard itself carries the patterns it searches for. */
const EL_GUARD = "__tests__/tokens.test.ts";

/** Arbitrary values: `bg-[#312e8e]`, `text-[rgb(0,0,0)]`. */
const ARBITRARIO = /-\[(?:#[0-9a-f]{3,8}|rgba?\(|hsla?\(|oklch\()/i;

/** Palette utilities of the default Tailwind: `text-red-500`. */
const PALETA =
  /-(?:red|blue|green|yellow|purple|pink|indigo|teal|cyan|orange|slate|gray|zinc|neutral|stone|amber|lime|emerald|sky|violet|fuchsia|rose)-(?:[1-9]50|[1-9]00)\b/;

/** Functional colour notations. */
const FUNCIONAL = /\b(?:rgba?|hsla?|oklch)\(/i;

function recorrer(dir: string): string[] {
  const salida: string[] = [];

  for (const entrada of readdirSync(dir)) {
    const completo = join(dir, entrada);

    if (statSync(completo).isDirectory()) {
      salida.push(...recorrer(completo));
      continue;
    }

    if (/\.(tsx?|css)$/.test(entrada)) {
      salida.push(completo);
    }
  }

  return salida;
}

describe("tokens — ningun componente lleva un color literal", () => {
  const archivos = CARPETAS.flatMap((carpeta) => {
    const dir = join(RAIZ, carpeta);
    return recorrer(dir).filter(
      (archivo) =>
        !relative(RAIZ, archivo).replace(/\\/g, "/").includes(EL_GUARD),
    );
  });

  it("encuentra los archivos que debe vigilar", () => {
    expect(archivos.length).toBeGreaterThan(20);
  });

  it.each(archivos.map((archivo) => [relative(RAIZ, archivo), archivo]))(
    "%s no declara colores literales",
    (_nombre, archivo) => {
      const fuente = readFileSync(archivo, "utf8");
      const permitidos = EXCEPCIONES.filter((excepcion) =>
        relative(RAIZ, archivo).endsWith(excepcion.archivo),
      );

      // Los colores literales permitidos se ocultan del análisis para que la
      // excepción sea real y no una excusa del analizador.
      let analizable = fuente;
      for (const excepcion of permitidos) {
        analizable = analizable.replaceAll(excepcion.motivo, "");
      }

      const literales = analizable
        .split("\n")
        .map((linea, indice) => ({ linea: linea + 1, indice }))
        .filter(({ linea }) => {
          if (ARBITRARIO.test(linea)) return true;
          if (PALETA.test(linea)) return true;
          return FUNCIONAL.test(linea);
        });

      expect(
        literales.map(({ indice }) => `${archivo}:${indice + 1}`).join("\n"),
      ).toBe("");
    },
  );
});

describe("tokens — el sistema global declara los roles", () => {
  const globals = readFileSync(join(RAIZ, "app", "globals.css"), "utf8");

  it.each([
    "--primary",
    "--secondary",
    "--accent",
    "--surface",
    "--border",
    "--muted",
    "--success",
    "--warning",
    "--destructive",
    "--chart-1",
    "--chart-5",
  ])("declara el rol %s", (rol) => {
    expect(globals).toContain(`${rol}:`);
  });

  it("define cada rol también en el tema oscuro", () => {
    const oscuro = globals.slice(globals.indexOf(".dark {"));

    for (const rol of [
      "--secondary",
      "--success",
      "--warning",
      "--destructive",
      "--popover",
      "--info",
    ]) {
      expect(oscuro).toContain(`${rol}:`);
    }
  });

  it("no arrastra el scroll-snap ni el scroll forzado a todas las rutas", () => {
    expect(globals).not.toContain("scroll-snap-type");
    expect(globals).not.toContain("overflow-y: scroll");
  });
});
