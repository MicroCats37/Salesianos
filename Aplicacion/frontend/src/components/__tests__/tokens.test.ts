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

/**
 * The roles that the global system DECLARES.
 *
 * A role lives in `globals.css`, at whatever level: `@theme inline`, `:root`
 * or `.dark`. The scanner reads every custom property declaration of that
 * file, so the guard does not have to know where each role is declared.
 */
function rolesDeclarados(): Set<string> {
  const globals = readFileSync(join(RAIZ, "app", "globals.css"), "utf8");
  const declarados = new Set<string>();

  for (const coincidencia of globals.matchAll(/--([a-zA-Z0-9-]+)\s*:/g)) {
    declarados.add(coincidencia[1]);
  }

  return declarados;
}

/**
 * The roles that the CODE publishes, not the stylesheet.
 *
 * A component can publish a custom property through an inline style
 * (`style={{ "--sidebar-width": … }}`) and `next/font` publishes the family
 * of the text through `variable: "--font-plus-jakarta-sans"`. Those are
 * legitimate OWNERS of a variable: the guard only forbids a CONSUMER that
 * reads a variable nobody declares.
 */
function rolesPublicadosPorElCodigo(): Set<string> {
  const publicados = new Set<string>();

  for (const archivo of recorrer(RAIZ)) {
    const nombre = relative(RAIZ, archivo).replace(/\\/g, "/");

    // The frozen legacy tree is not part of the target.
    if (nombre.startsWith("components-app")) continue;

    const fuente = readFileSync(archivo, "utf8");

    for (const coincidencia of fuente.matchAll(/"--([a-zA-Z0-9-]+)"/g)) {
      publicados.add(coincidencia[1]);
    }
  }

  return publicados;
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

/**
 * The second half of the token contract: not only does a component ask for a
 * ROLE, the role must EXIST.
 *
 * A consumer that reads a variable nobody declares is invisible in the
 * editor and in the review: the property simply falls back to `inherit` (or
 * to nothing) and the defect only shows on screen. The rebuild proved it:
 * the auth feature still read `--gold` and `--color-gold`, two variables that
 * the rewrite of the token system had removed.
 */
describe("tokens — ninguna regla lee una variable que nadie declara", () => {
  const declarados = rolesDeclarados();
  const publicados = rolesPublicadosPorElCodigo();

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
    "%s no lee variables inexistentes",
    (_nombre, archivo) => {
      const fuente = readFileSync(archivo, "utf8");
      const inexistentes: string[] = [];

      for (const coincidencia of fuente.matchAll(
        /var\(\s*--([a-zA-Z0-9-]+)\s*([,)])/g,
      )) {
        const nombre = coincidencia[1];

        // A variable with a fallback declares its own default.
        if (coincidencia[2] === ",") continue;
        if (declarados.has(nombre)) continue;
        if (publicados.has(nombre)) continue;

        inexistentes.push(nombre);
      }

      expect([...new Set(inexistentes)].join(", ")).toBe("");
    },
  );
});
