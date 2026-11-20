import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { DESTINOS_PUBLICOS, esRutaPublica, RUTAS } from "./routes";

/**
 * The pages the application router really serves.
 *
 * A route group — `(public)`, `(auth)`, `(cuenta)`, `(administracion)`,
 * `(portada)` — does NOT alter the URL: it is a way of organising the code.
 * The path of `(cuenta)/mi-cuenta` is `/mi-cuenta`.
 */
function paginasDeLaApp(): string[] {
  const salida: string[] = [];

  const recorrer = (dir: string, segmentos: string[]) => {
    for (const entrada of readdirSync(dir).sort()) {
      const completo = join(dir, entrada);

      if (statSync(completo).isDirectory()) {
        const esGrupo = entrada.startsWith("(") && entrada.endsWith(")");
        recorrer(completo, esGrupo ? segmentos : [...segmentos, entrada]);
        continue;
      }

      if (entrada !== "page.tsx") continue;

      const ruta = `/${segmentos.join("/")}`.replace(/\/+$/, "");
      salida.push(ruta === "" ? "/" : ruta);
    }
  };

  recorrer(join(process.cwd(), "src", "app"), []);

  return salida;
}

describe("routes — el mapa de rutas", () => {
  it("expone las 38 rutas del plan en una sola constante", () => {
    const plan = [
      RUTAS.publico.inicio,
      RUTAS.publico.informacion,
      RUTAS.publico.pases,
      RUTAS.publico.tienda,
      RUTAS.publico.recuperarCompra,
      RUTAS.auth.login,
      RUTAS.auth.registro,
      RUTAS.cuenta.miCuenta,
      RUTAS.cuenta.misInscripciones,
      RUTAS.cuenta.misCompras,
      RUTAS.cuenta.inscripcion,
      RUTAS.administracion.resumen,
      RUTAS.administracion.ediciones,
      RUTAS.administracion.personas,
      RUTAS.administracion.usuarios,
      RUTAS.administracion.inscripciones,
      RUTAS.administracion.equipos,
      RUTAS.administracion.participantes,
      RUTAS.administracion.competencias,
      RUTAS.administracion.competenciaAgenda,
      RUTAS.administracion.pagos,
      RUTAS.administracion.pases,
      RUTAS.administracion.pasesValidar,
      RUTAS.administracion.marketplace,
      RUTAS.administracion.marketplaceInventario,
      RUTAS.administracion.marketplaceEntregas,
      RUTAS.administracion.patrocinadores,
      RUTAS.administracion.validaciones,
    ];

    // 28 rutas fijas + 6 parametrizadas = 34; las 4 restantes son las que
    // llevan un identificador en la ruta (inscripción, compra, equipo,
    // competencia y producto) y se prueban abajo.
    expect(new Set(plan).size).toBe(plan.length);
    expect(plan).toHaveLength(28);
  });

  it("construye las rutas parametrizadas con el identificador dentro", () => {
    expect(RUTAS.cuenta.misInscripcionesDetalle("abc")).toBe(
      "/mis-inscripciones/abc",
    );
    expect(RUTAS.administracion.competenciaCuadro("7")).toBe(
      "/administracion/competencias/7/cuadro",
    );
    expect(RUTAS.publico.paseGestionar("tok")).toBe("/pases/gestionar/tok");
  });

  it("publica el registro como /registro y no como /register", () => {
    // La ruta congelada del plan es `/registro`: `/register` fue el nombre
    // del frontend anterior y hoy no lo sirve nadie. Un enlace a `/register`
    // terminaba en un 404.
    expect(RUTAS.auth.registro).toBe("/registro");
    expect(RUTAS.auth.registro).not.toBe("/register");
  });
});

describe("routes — el mapa y el router de la aplicación coinciden", () => {
  const paginas = paginasDeLaApp();

  const fijas = paginas.filter((ruta) => !ruta.includes("["));
  const dinamicas = paginas.filter((ruta) => ruta.includes("["));

  it("el router sirve las 38 rutas del plan", () => {
    expect(paginas).toHaveLength(38);
    expect(fijas).toHaveLength(28);
    expect(dinamicas).toHaveLength(10);
  });

  it("cada ruta fija del mapa tiene su página", () => {
    const declaradas = [
      RUTAS.publico.inicio,
      RUTAS.publico.informacion,
      RUTAS.publico.pases,
      RUTAS.publico.tienda,
      RUTAS.publico.recuperarCompra,
      RUTAS.auth.login,
      RUTAS.auth.registro,
      RUTAS.cuenta.miCuenta,
      RUTAS.cuenta.misInscripciones,
      RUTAS.cuenta.misCompras,
      RUTAS.cuenta.inscripcion,
      RUTAS.administracion.resumen,
      RUTAS.administracion.ediciones,
      RUTAS.administracion.personas,
      RUTAS.administracion.usuarios,
      RUTAS.administracion.inscripciones,
      RUTAS.administracion.equipos,
      RUTAS.administracion.participantes,
      RUTAS.administracion.competencias,
      RUTAS.administracion.competenciaAgenda,
      RUTAS.administracion.pagos,
      RUTAS.administracion.pases,
      RUTAS.administracion.pasesValidar,
      RUTAS.administracion.marketplace,
      RUTAS.administracion.marketplaceInventario,
      RUTAS.administracion.marketplaceEntregas,
      RUTAS.administracion.patrocinadores,
      RUTAS.administracion.validaciones,
    ];

    for (const ruta of declaradas) {
      expect(fijas).toContain(ruta);
    }
  });

  it("cada página fija está declarada en el mapa", () => {
    const declaradas = new Set<string>([
      RUTAS.publico.inicio,
      RUTAS.publico.informacion,
      RUTAS.publico.pases,
      RUTAS.publico.tienda,
      RUTAS.publico.recuperarCompra,
      RUTAS.auth.login,
      RUTAS.auth.registro,
      RUTAS.cuenta.miCuenta,
      RUTAS.cuenta.misInscripciones,
      RUTAS.cuenta.misCompras,
      RUTAS.cuenta.inscripcion,
      RUTAS.administracion.resumen,
      RUTAS.administracion.ediciones,
      RUTAS.administracion.personas,
      RUTAS.administracion.usuarios,
      RUTAS.administracion.inscripciones,
      RUTAS.administracion.equipos,
      RUTAS.administracion.participantes,
      RUTAS.administracion.competencias,
      RUTAS.administracion.competenciaAgenda,
      RUTAS.administracion.pagos,
      RUTAS.administracion.pases,
      RUTAS.administracion.pasesValidar,
      RUTAS.administracion.marketplace,
      RUTAS.administracion.marketplaceInventario,
      RUTAS.administracion.marketplaceEntregas,
      RUTAS.administracion.patrocinadores,
      RUTAS.administracion.validaciones,
    ]);

    for (const pagina of fijas) {
      expect(declaradas.has(pagina)).toBe(true);
    }
  });

  it("cada página dinámica tiene su fábrica en el mapa", () => {
    const patrones = [
      RUTAS.publico.paseGestionar("__id__"),
      RUTAS.publico.tiendaProducto("__id__"),
      RUTAS.publico.tiendaPedido("__id__"),
      RUTAS.cuenta.misInscripcionesDetalle("__id__"),
      RUTAS.cuenta.misComprasDetalle("__id__"),
      RUTAS.administracion.inscripcionesDetalle("__id__"),
      RUTAS.administracion.equiposDetalle("__id__"),
      RUTAS.administracion.competenciaDetalle("__id__"),
      RUTAS.administracion.competenciaCuadro("__id__"),
      RUTAS.administracion.marketplaceProducto("__id__"),
    ];

    for (const pagina of dinamicas) {
      const conMarcador = pagina.replace(/\[[^\]]+\]/g, "__id__");
      expect(patrones).toContain(conMarcador);
    }
  });
});

describe("routes — las rutas públicas", () => {
  it.each([
    "/",
    "/informacion",
    "/pases",
    "/tienda",
    "/recuperar-compra",
    "/login",
    "/registro",
  ])("es pública %s", (ruta) => {
    expect(esRutaPublica(ruta)).toBe(true);
  });

  it.each([
    "/mi-cuenta",
    "/mis-inscripciones",
    "/administracion",
    "/administracion/pagos",
  ])("NO es pública %s", (ruta) => {
    expect(esRutaPublica(ruta)).toBe(false);
  });

  it("trata los enlaces de invitado como públicos", () => {
    expect(esRutaPublica("/pases/gestionar/tok")).toBe(true);
    expect(esRutaPublica("/tienda/pedidos/tok")).toBe(true);
  });
});

describe("routes — la navegación pública", () => {
  it("ofrece los destinos del plan sin inventar módulos", () => {
    expect(DESTINOS_PUBLICOS.map((destino) => destino.href)).toEqual([
      "/informacion",
      "/pases",
      "/tienda",
    ]);
  });
});
