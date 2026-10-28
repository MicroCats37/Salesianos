import { describe, expect, it } from "vitest";
import { ADMIN_CAPACIDADES } from "./admin.capacidades";
import {
  ADMIN_SECCIONES,
  adminSeccionActiva,
  adminSeccionesVisibles,
} from "./admin.secciones";

/**
 * Focused tests of the section catalogue of the administration area.
 *
 * The catalogue is the DERIVED view of the matrix "sección → ruta →
 * capability": it is NOT persisted per user and it does NOT need a table.
 * The backend owns the real decision; this module only decides what the
 * navigation SHOWS.
 */

const TODAS = Object.values(ADMIN_CAPACIDADES);

describe("admin.secciones — catálogo", () => {
  it("declara una capacidad en cada sección del área", () => {
    for (const seccion of ADMIN_SECCIONES) {
      expect(seccion.capacidad).toBeDefined();
    }
  });

  it("mapea las secciones a sus capacidades", () => {
    const por_id = new Map(
      ADMIN_SECCIONES.map((seccion) => [seccion.id, seccion.capacidad]),
    );

    expect(por_id.get("resumen")).toBe(ADMIN_CAPACIDADES.ADMIN_VER);
    expect(por_id.get("pagos")).toBe(ADMIN_CAPACIDADES.PAGOS_VER);
    expect(por_id.get("usuarios")).toBe(ADMIN_CAPACIDADES.USUARIOS_VER);
  });

  it("la sección de pagos NO exige la capability sensible", () => {
    const pagos = ADMIN_SECCIONES.find((seccion) => seccion.id === "pagos");

    expect(pagos?.capacidad).not.toBe(ADMIN_CAPACIDADES.PAGOS_APROBAR);
  });
});

describe("admin.secciones — filtro por capacidades", () => {
  it("un usuario sin capacidades no ve ninguna sección del área", () => {
    expect(adminSeccionesVisibles([])).toHaveLength(0);
    expect(adminSeccionesVisibles(undefined)).toHaveLength(0);
  });

  it("el staff operativo ve las secciones de lectura", () => {
    const visibles = adminSeccionesVisibles([
      ADMIN_CAPACIDADES.ADMIN_VER,
      ADMIN_CAPACIDADES.PAGOS_VER,
      ADMIN_CAPACIDADES.USUARIOS_VER,
    ]);

    expect(visibles.map((seccion) => seccion.id)).toEqual([
      "resumen",
      "inscripciones",
      "pagos",
      "equipos",
      "competencias",
      "participantes",
      "acreditaciones",
      "usuarios",
    ]);
  });

  it("sin `admin.usuarios.ver` la sección de usuarios desaparece", () => {
    const visibles = adminSeccionesVisibles([
      ADMIN_CAPACIDADES.ADMIN_VER,
      ADMIN_CAPACIDADES.PAGOS_VER,
    ]);

    expect(visibles.map((seccion) => seccion.id)).not.toContain("usuarios");
  });

  it("sin `admin.pagos.ver` la sección de pagos desaparece", () => {
    const visibles = adminSeccionesVisibles([ADMIN_CAPACIDADES.ADMIN_VER]);

    expect(visibles.map((seccion) => seccion.id)).not.toContain("pagos");
  });

  it("el superusuario ve todas las secciones", () => {
    expect(adminSeccionesVisibles(TODAS)).toHaveLength(ADMIN_SECCIONES.length);
  });

  it("una sección sin capacidad declarada siempre se ve", () => {
    const sinCapacidad = [
      {
        id: "panel",
        title: "Panel",
        icon: ADMIN_SECCIONES[0].icon,
        href: "/dashboard",
        description: "Panel del equipo",
      },
    ];

    expect(adminSeccionesVisibles([], sinCapacidad)).toHaveLength(1);
  });
});

describe("admin.secciones — sección activa", () => {
  it("marca la sección de la ruta", () => {
    expect(adminSeccionActiva("/administracion/usuarios")?.id).toBe("usuarios");
    expect(adminSeccionActiva("/administracion")?.id).toBe("resumen");
  });

  it("marca la sección más específica de una ruta profunda", () => {
    expect(adminSeccionActiva("/administracion/competencias/agenda")?.id).toBe(
      "competencias",
    );
  });
});
