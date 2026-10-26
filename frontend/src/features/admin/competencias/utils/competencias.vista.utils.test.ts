import { describe, expect, it } from "vitest";
import {
  resolverEstadoVista,
  resolverVistaVacio,
} from "./competencias.vista.utils";

/**
 * Focused test of the states of the views of the module.
 *
 * The four states are a CONTRACT: a running query is a loading view, a
 * failed query is an error view and only a successful answer with no rows is
 * an empty view.
 */

describe("el estado de una vista se resuelve con una prioridad fija", () => {
  it("es una vista cargando mientras la consulta corre", () => {
    expect(resolverEstadoVista({ cargando: true, error: null, total: 0 })).toBe(
      "cargando",
    );
  });

  it("es una vista cargando aunque la consulta falle", () => {
    expect(
      resolverEstadoVista({ cargando: true, error: "boom", total: 0 }),
    ).toBe("cargando");
  });

  it("es una vista de error cuando la consulta falla", () => {
    expect(
      resolverEstadoVista({ cargando: false, error: "boom", total: 0 }),
    ).toBe("error");
  });

  it("es una vista vacia cuando la respuesta no tiene filas", () => {
    expect(
      resolverEstadoVista({ cargando: false, error: null, total: 0 }),
    ).toBe("vacio");
  });

  it("es una vista con datos cuando la respuesta trae filas", () => {
    expect(
      resolverEstadoVista({ cargando: false, error: null, total: 3 }),
    ).toBe("listo");
  });
});

describe("el texto de la vista vacia distingue el motivo", () => {
  it("ofrece la copia de la lista sin filtros", () => {
    const vacio = resolverVistaVacio(
      false,
      "Todavía no hay competencias",
      "No hay competencias registradas en el evento activo.",
    );

    expect(vacio).toEqual({
      titulo: "Todavía no hay competencias",
      descripcion: "No hay competencias registradas en el evento activo.",
      accion: null,
    });
  });

  it("ofrece la accion de limpiar cuando el filtro es el motivo", () => {
    const vacio = resolverVistaVacio(
      true,
      "Todavía no hay competencias",
      "No hay competencias registradas en el evento activo.",
    );

    expect(vacio.titulo).toBe("Sin resultados");
    expect(vacio.accion).toBe("Limpiar filtros");
  });
});
