import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  AdminCatalogosResponseSchema,
  AdminEstadosCatalogosSchema,
} from "./admin.catalogos.schema";

/**
 * Contract tests of the mirror of the filter catalogs (A2).
 *
 * The catalog publishes the vocabularies the client used to INVENT: the
 * completeness of a roster, the state of a participation, the commercial kind
 * of a purchase row and the operator verdict of a payment.
 *
 * The mirror is 1:1 with the backend wrapper
 * (`backend/modules/administracion/presentation/schemas/admin_catalogos_schemas.py`):
 * a catalog that does not carry the published vocabularies is REJECTED, never
 * silently accepted.
 */

const ESTADOS = {
  inscripcion: ["BORRADOR", "RECIBIDA"],
  compra: ["PENDIENTE", "PAGADA", "CANCELADA"],
  orden_pago: ["PENDIENTE", "PAGADA", "CANCELADA", "VENCIDA"],
  asignacion_cupo: ["ACTIVA", "LIBERADA", "REVOCADA"],
  equipo: ["EQUIPO_ACTIVO", "EQUIPO_CANCELADO"],
  acreditacion: ["PENDIENTE", "ACTIVA"],
  autorizacion_fiesta: ["AUTOMATICA", "AUTORIZADA", "BLOQUEADA"],
  acceso: ["PERMITIDO", "DENEGADO"],
  pool: ["LISTO", "ESPERANDO_PAGO"],
  rol_participante: ["J", "C", "D"],
  roster: ["COMPLETO", "INCOMPLETO"],
  estado_participacion: ["A", "R"],
  tipo_compra: ["INICIAL", "AMPLIACION", "PASE"],
  estado_operativo_pago: [
    "SIN_ORDEN",
    "PAGADA",
    "PAGADA_SIN_LIQUIDAR",
    "PAGADA_SIN_EVIDENCIA",
    "PAGADA_SIN_FECHA",
    "PENDIENTE",
    "CANCELADA",
    "VENCIDA",
  ],
};

const CATALOGO = {
  evento_id: "11111111-2222-3333-4444-555555555555",
  evento_nombre: "FEST 2026",
  disciplinas: [],
  paquetes: [],
  promociones: [],
  categorias: [],
  puntos_acceso: ["Puerta 1"],
  estados: ESTADOS,
};

/** The filters that used to carry their own copy of the options. */
const FILTROS = [
  {
    archivo: "../components/AdminPagosLista.tsx",
    vocabulario: "estados.tipo_compra",
  },
  {
    archivo: "../components/AdminEquiposLista.tsx",
    vocabulario: "estados.roster",
  },
  {
    archivo: "../components/AdminParticipantesLista.tsx",
    vocabulario: "estados.estado_participacion",
  },
];

/** The option literals no filter may hardcode anymore. */
const LITERALES_PROHIBIDOS = [
  "COMPLETO",
  "INCOMPLETO",
  "INICIAL",
  "AMPLIACION",
  "PASE",
];

describe("admin.catalogos.schema — el espejo del catálogo", () => {
  it("acepta el catálogo con los vocabularios publicados", () => {
    const parsed = AdminCatalogosResponseSchema.parse(CATALOGO);

    expect(parsed.estados.roster).toEqual(["COMPLETO", "INCOMPLETO"]);
    expect(parsed.estados.estado_participacion).toEqual(["A", "R"]);
    expect(parsed.estados.tipo_compra).toEqual([
      "INICIAL",
      "AMPLIACION",
      "PASE",
    ]);
    expect(parsed.estados.estado_operativo_pago).toContain(
      "PAGADA_SIN_LIQUIDAR",
    );
  });

  it("rechaza un catálogo sin uno de los vocabularios publicados", () => {
    const { roster: _roster, ...estadosIncompletos } = ESTADOS;

    const resultado = AdminEstadosCatalogosSchema.safeParse(estadosIncompletos);

    expect(resultado.success).toBe(false);
  });

  it("acepta un veredicto desconocido para poder renderizarlo neutro", () => {
    const resultado = AdminEstadosCatalogosSchema.safeParse({
      ...ESTADOS,
      estado_operativo_pago: [...ESTADOS.estado_operativo_pago, "INVENTADO"],
    });

    // El vocabulario se publica como LISTA de valores: un código nuevo
    // atraviesa el espejo y la interfaz lo renderiza de forma neutra, sin
    // romper la página entera.
    expect(resultado.success).toBe(true);
  });
});

describe("los filtros leen sus opciones del catálogo", () => {
  for (const { archivo, vocabulario } of FILTROS) {
    it(`${archivo} lee ${vocabulario} y no inventa sus opciones`, () => {
      const fuente = readFileSync(new URL(archivo, import.meta.url), "utf8");

      expect(fuente).toContain(vocabulario);

      for (const literal of LITERALES_PROHIBIDOS) {
        expect(fuente).not.toContain(`{ valor: "${literal}"`);
      }
    });
  }
});
