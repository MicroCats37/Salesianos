import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";
import { RUTAS } from "../routes";

/**
 * The guard of the route map.
 *
 * The route map (`src/lib/routes.ts`) is the ONE owner of the paths of the
 * product: a rename is a change in one file, never a search-and-replace
 * across the markup.
 *
 * A second owner is a second truth. The rebuild proved it: the map published
 * the registration as `/registro` while four components still pointed at
 * `/register`, and the gate of the proxy kept its own copy of the public
 * paths. Both are 404 waiting to happen.
 *
 * The rule of this guard: NO COMPONENT MAY WRITE A PAGE PATH. A path that
 * appears in a component must come from the map.
 *
 * The exceptions are declared here, with the file and the reason. The only
 * legitimate exception is a path that is NOT a page of this application: the
 * endpoints of the backend, which the transport prefixes with its base URL.
 */
const EXCEPCIONES: { archivo: string; motivo: string }[] = [
  {
    archivo: "features/auth/hooks/useLogin.ts",
    motivo: "/auth/login/username",
  },
  {
    archivo: "features/auth/hooks/useLogin.ts",
    motivo: "/auth/login/dni",
  },
  {
    archivo: "features/auth/hooks/useLogin.ts",
    motivo: "/auth/login/email",
  },
  {
    archivo: "features/auth/services/register.service.ts",
    motivo: "/auth/register",
  },
];

const RAIZ = join(process.cwd(), "src");

/** The folders that may navigate: the shell, the features and the routes. */
const CARPETAS = ["app", "components", "features"];

/**
 * The frozen legacy tree. It is not part of the target (`tsconfig.json`
 * excludes it) and it keeps the paths of the previous application.
 */
const EXCLUIDAS = ["components-app"];

/** The guard carries the paths it searches for. */
const EL_GUARD = "route-map.guard.test.ts";

/** A literal path: it starts with `/` and it is not a template. */
const RUTA = /"(\/[^"{]*)"/g;

function recorrer(dir: string): string[] {
  const salida: string[] = [];

  for (const entrada of readdirSync(dir)) {
    const completo = join(dir, entrada);

    if (statSync(completo).isDirectory()) {
      salida.push(...recorrer(completo));
      continue;
    }

    if (/\.tsx?$/.test(entrada)) {
      salida.push(completo);
    }
  }

  return salida;
}

/** Every fixed path of the map. The factories build their own path. */
function rutasFijas(valor: unknown): string[] {
  if (typeof valor === "string") return [valor];
  if (typeof valor === "function") return [];
  if (valor && typeof valor === "object") {
    return Object.values(valor).flatMap(rutasFijas);
  }

  return [];
}

const DECLARADAS = new Set(rutasFijas(RUTAS));

describe("routes — el mapa es el único dueño de las rutas", () => {
  const archivos = CARPETAS.flatMap((carpeta) =>
    recorrer(join(RAIZ, carpeta)).filter((archivo) => {
      const nombre = relative(RAIZ, archivo).replace(/\\/g, "/");

      if (nombre.includes(EL_GUARD)) return false;
      if (nombre.endsWith(".test.ts") || nombre.endsWith(".test.tsx")) {
        // A test may assert a literal path: that is the point of a test.
        return false;
      }

      return !EXCLUIDAS.some((excluida) => nombre.startsWith(excluida));
    }),
  );

  it("encuentra los archivos que debe vigilar", () => {
    expect(archivos.length).toBeGreaterThan(20);
  });

  it.each(archivos.map((archivo) => [relative(RAIZ, archivo), archivo]))(
    "%s no escribe una ruta de página",
    (_nombre, archivo) => {
      const fuente = readFileSync(archivo, "utf8");

      // The allowed paths are hidden from the analysis so that the exception
      // is real and not an excuse of the analyser.
      let analizable = fuente;
      for (const excepcion of EXCEPCIONES) {
        if (!relative(RAIZ, archivo).endsWith(excepcion.archivo)) continue;
        analizable = analizable.replaceAll(excepcion.motivo, "");
      }

      const sospechosas: string[] = [];

      for (const coincidencia of analizable.matchAll(RUTA)) {
        const ruta = coincidencia[1];

        // A file name: an image, a font, a calendar.
        if (ruta.includes(".")) continue;
        // A route handler of the product (`/api/...`).
        if (ruta.startsWith("/api/")) continue;

        if (!DECLARADAS.has(ruta)) sospechosas.push(ruta);
      }

      expect([...new Set(sospechosas)].join(", ")).toBe("");
    },
  );

  it("no vuelve a publicar las rutas que el mapa retiró", () => {
    // `/register`, `/dashboard` and `/admin/dashboard` belonged to the
    // previous application: the router does not serve them.
    for (const retirada of ["/register", "/dashboard", "/admin/dashboard"]) {
      expect(DECLARADAS.has(retirada)).toBe(false);
    }
  });
});
