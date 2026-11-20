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
const EXCEPCIONES: { archivo: string; motivos: string[] }[] = [
  {
    archivo: "features/auth/hooks/useLogin.ts",
    motivos: ["/auth/login/username", "/auth/login/dni", "/auth/login/email"],
  },
  {
    archivo: "features/auth/services/register.service.ts",
    motivos: ["/auth/register"],
  },
  {
    archivo: "features/auth/services/sesion.service.ts",
    motivos: ["/auth/me"],
  },
  {
    archivo: "features/auth/services/identidad.service.ts",
    motivos: [
      "/personas/busqueda",
      "/personas/resolver",
      "/personas/confirmar",
    ],
  },
  {
    archivo: "features/public/services/edicion.service.ts",
    motivos: ["/ediciones/actual"],
  },
  {
    archivo: "features/inscripciones/services/catalogo.service.ts",
    motivos: [
      "/catalogo/paquetes",
      "/catalogo/disciplinas",
      "/catalogo/categorias",
      "/catalogo/promociones",
    ],
  },
  {
    archivo: "features/inscripciones/services/cotizacion.service.ts",
    motivos: ["/cotizaciones"],
  },
  {
    archivo: "features/inscripciones/services/inscripcion.service.ts",
    motivos: ["/inscripciones"],
  },
  {
    archivo: "features/competencias/services/competencia.service.ts",
    motivos: ["/competencias"],
  },
  {
    archivo: "features/marketplace/services/marketplace.service.ts",
    motivos: ["/marketplace"],
  },
  {
    archivo: "features/validaciones/services/validacion.service.ts",
    motivos: ["/validaciones"],
  },
  {
    archivo: "features/admin/operaciones/services/admin.service.ts",
    motivos: [
      "/administracion/resumen",
      "/administracion/auditoria",
      "/administracion/inscripciones",
      "/administracion/equipos",
      "/administracion/pagos",
      "/administracion/participantes",
      "/administracion/personas",
    ],
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
      if (nombre.includes("/__tests__/")) {
        // The same rationale, extended to the DATA files of a test: they hold
        // the literal paths the server publishes (a drilldown `href`, an
        // example id) and they are not components.
        return false;
      }

      return !EXCLUIDAS.some((excluida) => nombre.startsWith(excluida));
    }),
  );

  it("encuentra los archivos que debe vigilar", () => {
    expect(archivos.length).toBeGreaterThan(20);
  });

  it.each(
    archivos.map((archivo) => [
      relative(RAIZ, archivo).replace(/\\/g, "/"),
      archivo,
    ]),
  )("%s no escribe una ruta de página", (nombre, archivo) => {
    const fuente = readFileSync(archivo, "utf8");

    // The allowed paths are hidden from the analysis so that the exception
    // is real and not an excuse of the analyser.
    //
    // `nombre` is the NORMALISED relative path (forward slashes on every
    // platform): the raw `relative()` returns backslashes on Windows and
    // the declared exceptions would never match there.
    let analizable = fuente;
    for (const excepcion of EXCEPCIONES) {
      if (!nombre.endsWith(excepcion.archivo)) continue;
      for (const motivo of excepcion.motivos) {
        analizable = analizable.replaceAll(motivo, "");
      }
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
  });

  it("no vuelve a publicar las rutas que el mapa retiró", () => {
    // `/register`, `/dashboard` and `/admin/dashboard` belonged to the
    // previous application: the router does not serve them.
    for (const retirada of ["/register", "/dashboard", "/admin/dashboard"]) {
      expect(DECLARADAS.has(retirada)).toBe(false);
    }
  });
});
