import { describe, expect, it } from "vitest";
import { adminEstadoDesdeParametros } from "@/features/admin/utils/admin.lista.utils";
import {
  COMPETENCIAS_FILTROS_AGENDA,
  COMPETENCIAS_FILTROS_LISTA,
  competenciasFechaHoy,
  competenciasHora,
  competenciasMinutosDelDia,
  competenciasParametrosAgenda,
  competenciasParametrosLista,
} from "./competencias.url.utils";

/**
 * Focused test of the URL contract of the module.
 *
 * The URL OWNS the filters of every view and the client NEVER sends a
 * parameter the endpoint does not declare: the vocabulary of `estado` is the
 * state of the COMPETITION in the list and the state of the ENCOUNTER in the
 * agenda.
 */

describe("los filtros de la lista son los que declara su endpoint", () => {
  it("acepta los seis filtros de la lista", () => {
    const parametros = competenciasParametrosLista({
      evento_id: "ev1",
      disciplina_id: "di1",
      categoria_id: "ca1",
      estado: "PLANIFICADA",
      fecha_desde: "2026-11-01",
      fecha_hasta: "2026-11-30",
    });

    expect(parametros).toEqual({
      evento_id: "ev1",
      disciplina_id: "di1",
      categoria_id: "ca1",
      estado: "PLANIFICADA",
      fecha_desde: "2026-11-01",
      fecha_hasta: "2026-11-30",
    });
  });

  it("descarta un filtro que el endpoint no declara", () => {
    const parametros = competenciasParametrosLista({
      estado: "PLANIFICADA",
      pagina: "3",
      q: "ana",
    });

    expect(parametros).toEqual({ estado: "PLANIFICADA" });
  });

  it("descarta un filtro vacio", () => {
    const parametros = competenciasParametrosLista({
      estado: "   ",
      disciplina_id: "",
    });

    expect(parametros).toEqual({});
  });

  it("no envia el filtro de dia a la lista", () => {
    const parametros = competenciasParametrosLista({ fecha: "2026-11-16" });

    expect(parametros).toEqual({});
  });
});

describe("los filtros de la agenda son los que declara su endpoint", () => {
  it("acepta el dia y los filtros del alcance", () => {
    const parametros = competenciasParametrosAgenda({
      fecha: "2026-11-16",
      evento_id: "ev1",
      disciplina_id: "di1",
      categoria_id: "ca1",
      estado: "PROGRAMADO",
    });

    expect(parametros).toEqual({
      fecha: "2026-11-16",
      evento_id: "ev1",
      disciplina_id: "di1",
      categoria_id: "ca1",
      estado: "PROGRAMADO",
    });
  });

  it("descarta el rango de fechas de la lista", () => {
    const parametros = competenciasParametrosAgenda({
      fecha_desde: "2026-11-01",
      fecha_hasta: "2026-11-30",
    });

    expect(parametros).toEqual({});
  });

  it("declara dos listas de filtros distintas", () => {
    expect(COMPETENCIAS_FILTROS_LISTA).not.toContain("fecha");
    expect(COMPETENCIAS_FILTROS_AGENDA).toContain("fecha");
    expect(COMPETENCIAS_FILTROS_AGENDA).not.toContain("fecha_desde");
  });
});

describe("el estado de la URL alimenta los filtros de la consulta", () => {
  it("lee los filtros del recurso desde la query string", () => {
    const estado = adminEstadoDesdeParametros(
      new URLSearchParams("estado=EN_CURSO&disciplina_id=di1&page=2"),
      "",
      [],
    );

    expect(estado.filtros).toEqual({
      estado: "EN_CURSO",
      disciplina_id: "di1",
    });
  });

  it("recorre el camino completo de la URL a la consulta", () => {
    const parametros = new URLSearchParams("estado=EN_CURSO&q=ana");
    const estado = adminEstadoDesdeParametros(parametros, "", []);

    expect(competenciasParametrosLista(estado.filtros)).toEqual({
      estado: "EN_CURSO",
    });
  });
});

describe("el reloj del cliente es determinista y local", () => {
  it("devuelve el dia local en formato ISO", () => {
    const hoy = competenciasFechaHoy();

    expect(hoy).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("lee la hora de un instante ISO sin aplicar una zona horaria", () => {
    expect(competenciasHora("2026-11-16T14:30:00")).toBe("14:30");
    expect(competenciasHora(null)).toBe("");
  });

  it("lee los minutos del dia de un instante ISO", () => {
    expect(competenciasMinutosDelDia("2026-11-16T14:30:00")).toBe(870);
    expect(competenciasMinutosDelDia(undefined)).toBeNull();
  });
});
