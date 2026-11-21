import { describe, expect, it } from "vitest";
import { ADMIN_CAPACIDADES } from "./admin.capacidades";
import {
  ADMIN_DESTINOS,
  ADMIN_GRUPOS,
  ADMIN_RESUMEN,
  adminEsAdministrador,
  adminGruposVisibles,
  adminSeccionActiva,
  adminSeccionesVisibles,
} from "./admin.secciones";

describe("admin.secciones — el modelo de navegación", () => {
  it("consolida las páginas en 13 destinos de navegación", () => {
    // El plan dice que las 22 entradas son DESTINOS CONCEPTUALES: "evitar
    // fragmentar navegación sin necesidad". Los detalles (ADM-06, ADM-08,
    // ADM-11, ADM-12, ADM-13, ADM-18, ADM-20) se alcanzan desde su destino
    // padre, no con una entrada propia. 13 destinos + el resumen = 14.
    expect(ADMIN_DESTINOS).toHaveLength(14);
    expect(ADMIN_DESTINOS.filter((d) => d.id !== "resumen")).toHaveLength(13);
  });

  it("agrupa los destinos en los cuatro grupos del plan", () => {
    expect(ADMIN_GRUPOS.map((grupo) => grupo.id)).toEqual([
      "deportivo",
      "ventas",
      "contenido",
      "personas",
    ]);
  });

  it("publica pases y control de ingreso en ventas", () => {
    const ventas = ADMIN_GRUPOS.find((grupo) => grupo.id === "ventas");

    expect(ventas?.destinos.map((destino) => destino.id)).toEqual(
      expect.arrayContaining(["pases", "control-ingreso"]),
    );
  });

  it("no repite un destino en dos grupos", () => {
    const ids = ADMIN_GRUPOS.flatMap((grupo) =>
      grupo.destinos.map((destino) => destino.id),
    );

    expect(new Set(ids).size).toBe(ids.length);
  });

  it("el resumen vive fuera de los grupos", () => {
    const ids = ADMIN_GRUPOS.flatMap((grupo) =>
      grupo.destinos.map((destino) => destino.id),
    );

    expect(ids).not.toContain(ADMIN_RESUMEN.id);
  });
});

describe("admin.secciones — filtrado por capacidad", () => {
  it("falla cerrado: sin capacidades sólo quedan los destinos sin capacidad", () => {
    const visibles = adminSeccionesVisibles([]);

    expect(visibles.length).toBeLessThan(ADMIN_DESTINOS.length);
    expect(visibles.every((destino) => !destino.capacidad)).toBe(true);
  });

  it("mantiene los destinos que el backend concedió", () => {
    const visibles = adminSeccionesVisibles([
      ADMIN_CAPACIDADES.ADMIN_VER,
      ADMIN_CAPACIDADES.USUARIOS_VER,
    ]);

    expect(visibles.some((destino) => destino.id === "usuarios")).toBe(true);
    expect(visibles.some((destino) => destino.id === "resumen")).toBe(true);
  });

  it("oculta pagos a quien no puede verlos", () => {
    const visibles = adminSeccionesVisibles([ADMIN_CAPACIDADES.ADMIN_VER]);

    expect(visibles.some((destino) => destino.id === "pagos")).toBe(false);
  });

  it("elimina los grupos que se quedan sin destinos", () => {
    const grupos = adminGruposVisibles([ADMIN_CAPACIDADES.PAGOS_VER]);

    expect(grupos.every((grupo) => grupo.destinos.length > 0)).toBe(true);
    expect(grupos.some((grupo) => grupo.id === "ventas")).toBe(true);
  });
});

describe("admin.secciones — destino activo", () => {
  it("marca el destino exacto", () => {
    expect(adminSeccionActiva("/administracion/pagos")?.id).toBe("pagos");
  });

  it("marca el destino padre de una ruta profunda", () => {
    expect(adminSeccionActiva("/administracion/inscripciones/abc")?.id).toBe(
      "inscripciones",
    );
  });

  it("gana el destino más específico cuando varios coinciden", () => {
    // El cuadro no es un destino propio: es una pestaña del detalle de la
    // competencia, así que sigue marcando "Competencias".
    expect(
      adminSeccionActiva("/administracion/competencias/7/cuadro")?.id,
    ).toBe("competencias");
  });

  it("marca el padre cuando la ruta baja a un detalle", () => {
    expect(adminSeccionActiva("/administracion/equipos/9")?.id).toBe("equipos");
  });

  it("no marca nada fuera del área", () => {
    expect(adminSeccionActiva("/mi-cuenta")).toBeNull();
  });
});

describe("admin.secciones — permiso de entrada", () => {
  it.each([
    [{ es_admin: true }, true],
    [{ is_staff: true }, true],
    [{ is_superuser: true }, true],
    [{ es_admin: false, is_staff: false, is_superuser: false }, false],
    [null, false],
  ])("lee el veredicto del backend %o", (sesion, esperado) => {
    expect(adminEsAdministrador(sesion)).toBe(esperado);
  });
});
