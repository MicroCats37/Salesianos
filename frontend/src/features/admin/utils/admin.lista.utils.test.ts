/**
 * Focused tests for the URL / filter / pagination / ordering mapping of the
 * administration area.
 *
 * The module under test is dependency-free on purpose, so it can be exercised
 * without the React/axios runtime.
 *
 * Run with:
 *   node --experimental-strip-types --test \
 *     src/features/admin/utils/admin.lista.utils.test.ts
 *
 * NOTE: the module is imported through a computed specifier on purpose — Node
 * requires the explicit `.ts` extension to strip the types, while the project
 * `tsconfig` forbids `.ts` extensions in import paths. A computed specifier
 * keeps `tsc --noEmit` clean and still loads the REAL module under test.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./admin.lista.utils.ts";
const utils = (await import(specifier)) as {
  ADMIN_PAGE_POR_DEFECTO: number;
  ADMIN_PAGE_SIZE_MAXIMO: number;
  ADMIN_PAGE_SIZE_POR_DEFECTO: number;
  adminAlternarOrdering: (actual: string, campo: string) => string;
  adminCampoOrdenActual: (ordering: string) => {
    campo: string;
    descendente: boolean;
  };
  adminClavesReservadas: (prefijo?: string) => Set<string>;
  adminEsClavePropia: (
    clave: string,
    prefijo?: string,
    otros?: string[],
  ) => boolean;
  adminEstadoDesdeParametros: (
    parametros: URLSearchParams | Record<string, string> | null | undefined,
    prefijo?: string,
    otros?: string[],
  ) => {
    page: number;
    pageSize: number;
    q: string;
    ordering: string;
    filtros: Record<string, string>;
  };
  adminHayFiltrosActivos: (estado: {
    q: string;
    filtros: Record<string, string>;
  }) => boolean;
  adminNormalizarOrdering: (valor: unknown) => string;
  adminNormalizarPage: (valor: unknown) => number;
  adminNormalizarPageSize: (valor: unknown) => number;
  adminNormalizarQ: (valor: unknown) => string;
  adminOpcionesOrdering: (
    campos: Array<{ campo: string; etiqueta: string }>,
  ) => Array<{ valor: string; etiqueta: string }>;
  adminParametrosConsulta: (estado: unknown) => Record<string, string | number>;
  adminParametrosUrl: (estado: unknown, prefijo?: string) => URLSearchParams;
  adminParametrosUrlActualizados: (
    parametros: URLSearchParams,
    estado: unknown,
    prefijo?: string,
    otros?: string[],
  ) => URLSearchParams;
};

// ── The pagination rules mirror the backend contract ────────────────────────

test("la pagina es de base 1 y nunca baja de 1", () => {
  assert.equal(utils.adminNormalizarPage(undefined), 1);
  assert.equal(utils.adminNormalizarPage(""), 1);
  assert.equal(utils.adminNormalizarPage("abc"), 1);
  assert.equal(utils.adminNormalizarPage(0), 1);
  assert.equal(utils.adminNormalizarPage(-7), 1);
  assert.equal(utils.adminNormalizarPage("3"), 3);
});

test("el tamano de pagina se recorta en el maximo, no se rechaza", () => {
  assert.equal(utils.adminNormalizarPageSize(undefined), 25);
  assert.equal(utils.adminNormalizarPageSize(0), 1);
  assert.equal(utils.adminNormalizarPageSize(1000), 100);
  assert.equal(utils.adminNormalizarPageSize(50), 50);
});

test("el termino de busqueda se normaliza y se acota a 120 caracteres", () => {
  assert.equal(utils.adminNormalizarQ("  ana   lopez  "), "ana lopez");
  assert.equal(utils.adminNormalizarQ(null), "");
  assert.equal(utils.adminNormalizarQ("x".repeat(200)).length, 120);
});

// ── The state is read out of the URL ───────────────────────────────────────

test("la URL aporta pagina, tamano, termino y orden", () => {
  const estado = utils.adminEstadoDesdeParametros(
    new URLSearchParams("page=2&page_size=50&q=ana&ordering=-created_at"),
  );

  assert.equal(estado.page, 2);
  assert.equal(estado.pageSize, 50);
  assert.equal(estado.q, "ana");
  assert.equal(estado.ordering, "-created_at");
});

test("los parametros que no son reservados son filtros del recurso", () => {
  const estado = utils.adminEstadoDesdeParametros(
    new URLSearchParams("estado=CONFIRMADA&paquete_id=abc"),
  );

  assert.deepEqual(estado.filtros, {
    estado: "CONFIRMADA",
    paquete_id: "abc",
  });
});

test("el identificador del detalle NO es un filtro del backend", () => {
  const estado = utils.adminEstadoDesdeParametros(
    new URLSearchParams("detalle=orden-1&estado=PAGADA"),
  );

  assert.deepEqual(estado.filtros, { estado: "PAGADA" });
});

test("una URL vacia devuelve los valores por defecto", () => {
  const estado = utils.adminEstadoDesdeParametros(new URLSearchParams(""));

  assert.equal(estado.page, 1);
  assert.equal(estado.pageSize, 25);
  assert.equal(estado.q, "");
  assert.equal(estado.ordering, "");
  assert.deepEqual(estado.filtros, {});
});

// ── Two tabs of the same page own two namespaces ───────────────────────────

test("cada namespace lee sus propios parametros", () => {
  const parametros = new URLSearchParams(
    "participantes_page=2&participantes_q=ana&participaciones_page=3&participaciones_q=lucas",
  );

  const participantes = utils.adminEstadoDesdeParametros(
    parametros,
    "participantes_",
  );
  const participaciones = utils.adminEstadoDesdeParametros(
    parametros,
    "participaciones_",
  );

  assert.equal(participantes.page, 2);
  assert.equal(participantes.q, "ana");
  assert.equal(participaciones.page, 3);
  assert.equal(participaciones.q, "lucas");
});

test("los filtros de una tab nunca invaden la otra", () => {
  const parametros = new URLSearchParams(
    "participantes_estado_pool=LISTO&participaciones_rol=J",
  );

  const participantes = utils.adminEstadoDesdeParametros(
    parametros,
    "participantes_",
    ["participaciones_"],
  );
  const participaciones = utils.adminEstadoDesdeParametros(
    parametros,
    "participaciones_",
    ["participantes_"],
  );

  assert.deepEqual(participantes.filtros, { estado_pool: "LISTO" });
  assert.deepEqual(participaciones.filtros, { rol: "J" });
});

test("actualizar una tab conserva el estado de la otra", () => {
  const parametros = new URLSearchParams(
    "participantes_q=ana&participaciones_q=lucas&participaciones_rol=J",
  );

  const estado = utils.adminEstadoDesdeParametros(
    parametros,
    "participantes_",
    ["participaciones_"],
  );
  estado.q = "maria";

  const resultado = utils.adminParametrosUrlActualizados(
    parametros,
    estado,
    "participantes_",
    ["participaciones_"],
  );

  assert.equal(resultado.get("participantes_q"), "maria");
  assert.equal(resultado.get("participaciones_q"), "lucas");
  assert.equal(resultado.get("participaciones_rol"), "J");
});

test("el namespace principal ignora los prefijos de sus hermanos", () => {
  assert.equal(
    utils.adminEsClavePropia("participaciones_rol", "", ["participaciones_"]),
    false,
  );
  assert.equal(
    utils.adminEsClavePropia("estado", "", ["participaciones_"]),
    true,
  );
  assert.equal(
    utils.adminEsClavePropia("participaciones_rol", "participaciones_"),
    true,
  );
});

test("los parametros reservados de un namespace son suyos", () => {
  const reservadas = utils.adminClavesReservadas("accesos_");

  assert.ok(reservadas.has("accesos_page"));
  assert.ok(reservadas.has("accesos_page_size"));
  assert.ok(reservadas.has("accesos_q"));
  assert.ok(reservadas.has("accesos_ordering"));
  assert.ok(reservadas.has("accesos_detalle"));
});

// ── The query sent to the backend ──────────────────────────────────────────

test("la consulta siempre lleva pagina y tamano, y omite lo vacio", () => {
  const parametros = utils.adminParametrosConsulta({
    page: 3,
    pageSize: 25,
    q: "",
    ordering: "",
    filtros: { estado: "PAGADA", disciplina_id: "" },
  });

  assert.deepEqual(parametros, {
    page: 3,
    page_size: 25,
    estado: "PAGADA",
  });
});

test("la URL omite los valores por defecto", () => {
  const parametros = utils.adminParametrosUrl({
    page: 1,
    pageSize: 25,
    q: "",
    ordering: "",
    filtros: {},
  });

  assert.equal(parametros.toString(), "");
});

test("la URL escribe el namespace en los parametros", () => {
  const parametros = utils.adminParametrosUrl(
    {
      page: 2,
      pageSize: 50,
      q: "ana",
      ordering: "-created_at",
      filtros: { estado_pool: "LISTO" },
    },
    "participantes_",
  );

  assert.equal(parametros.get("participantes_page"), "2");
  assert.equal(parametros.get("participantes_page_size"), "50");
  assert.equal(parametros.get("participantes_q"), "ana");
  assert.equal(parametros.get("participantes_ordering"), "-created_at");
  assert.equal(parametros.get("participantes_estado_pool"), "LISTO");
});

test("el detalle abierto sobrevive a un cambio de la lista", () => {
  const parametros = new URLSearchParams("detalle=orden-1");

  const resultado = utils.adminParametrosUrlActualizados(parametros, {
    page: 2,
    pageSize: 25,
    q: "",
    ordering: "",
    filtros: {},
  });

  assert.equal(resultado.get("detalle"), "orden-1");
  assert.equal(resultado.get("page"), "2");
});

test("limpiar los filtros conserva el tamano de pagina elegido", () => {
  const parametros = new URLSearchParams("page_size=10&q=ana&estado=PAGADA");

  const resultado = utils.adminParametrosUrlActualizados(parametros, {
    page: 1,
    pageSize: 10,
    q: "",
    ordering: "",
    filtros: {},
  });

  assert.equal(resultado.get("page_size"), "10");
  assert.equal(resultado.get("q"), null);
  assert.equal(resultado.get("estado"), null);
});

// ── The empty state knows whether a filter is narrowing the list ───────────

test("sin filtros la lista esta vacia de verdad", () => {
  assert.equal(utils.adminHayFiltrosActivos({ q: "", filtros: {} }), false);
});

test("con termino o con filtros la lista esta filtrada", () => {
  assert.equal(utils.adminHayFiltrosActivos({ q: "ana", filtros: {} }), true);
  assert.equal(
    utils.adminHayFiltrosActivos({ q: "", filtros: { estado: "PAGADA" } }),
    true,
  );
  assert.equal(
    utils.adminHayFiltrosActivos({ q: "", filtros: { estado: "" } }),
    false,
  );
});

// ── The ordering only offers whitelisted public fields ─────────────────────

test("el orden se lee como campo y direccion", () => {
  assert.deepEqual(utils.adminCampoOrdenActual("created_at"), {
    campo: "created_at",
    descendente: false,
  });
  assert.deepEqual(utils.adminCampoOrdenActual("-created_at"), {
    campo: "created_at",
    descendente: true,
  });
  assert.deepEqual(utils.adminCampoOrdenActual(""), {
    campo: "",
    descendente: false,
  });
});

test("alternar el orden invierte la direccion del mismo campo", () => {
  assert.equal(
    utils.adminAlternarOrdering("created_at", "created_at"),
    "-created_at",
  );
  assert.equal(
    utils.adminAlternarOrdering("-created_at", "created_at"),
    "created_at",
  );
});

test("un campo distinto arranca en orden ascendente", () => {
  assert.equal(utils.adminAlternarOrdering("-created_at", "estado"), "estado");
});

test("las opciones de orden ofrecen las dos direcciones", () => {
  const opciones = utils.adminOpcionesOrdering([
    { campo: "created_at", etiqueta: "Creación" },
    { campo: "estado", etiqueta: "Estado" },
  ]);

  assert.deepEqual(
    opciones.map((opcion) => opcion.valor),
    ["created_at", "-created_at", "estado", "-estado"],
  );
});

test("un orden vacio se normaliza a cadena vacia", () => {
  assert.equal(utils.adminNormalizarOrdering("-"), "");
  assert.equal(utils.adminNormalizarOrdering("  -created_at  "), "-created_at");
});
