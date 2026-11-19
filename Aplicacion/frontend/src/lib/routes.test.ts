import { describe, expect, it } from "vitest";
import { DESTINOS_PUBLICOS, esRutaPublica, RUTAS } from "./routes";

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
