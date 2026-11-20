import { describe, expect, it } from "vitest";

import {
  catalogoDisciplinasSchema,
  catalogoPaquetesSchema,
} from "../schemas/catalogo.schema";
import { compraCreadaSchema } from "../schemas/compra-cupos.schema";
import {
  inscripcionDetalleSchema,
  inscripcionInicialInSchema,
  inscripcionInicialSchema,
} from "../schemas/inscripcion.schema";
import { participanteAsignarInSchema, poolSchema } from "../schemas/pool.schema";
import { leerRespuesta } from "../services/respuesta.service";
import {
  construirPayloadAlta,
  construirPayloadCompraCupos,
  construirPayloadParticipante,
} from "../utils/inscripcion.payloads.utils";

/**
 * The mirrors of the wire of the TARGET backend.
 *
 * The examples below are the JSON that the target answers with: they were
 * read from the presenters of DOM-01 and DOM-02 and from the e2e suites of
 * the module (`Aplicacion/backend/modules/salesianos_fest/tests/e2e/`).
 *
 * They are EXAMPLES, not fixtures of production: no module of the feature
 * imports this file, and the file carries no provisional-fixture marker
 * because it is a test, not a transport.
 *
 * The money is a STRING on the wire: the chain that produces it is written
 * in `schemas/catalogo.schema.ts`.
 */

const PRECIO = {
  monto: "750.00",
  moneda: "PEN",
  vigente_desde: "2026-01-01",
  vigente_hasta: null,
};

const DISCIPLINA = {
  id: "3f0c1c1e-0000-4000-8000-0000000000d1",
  created_at: "2026-11-19T10:00:00+00:00",
  updated_at: "2026-11-19T10:00:00+00:00",
  edicion_id: "3f0c1c1e-0000-4000-8000-0000000000e1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  nombre: "FUTSAL",
  slug: "futsal",
  estado: "ACTIVA",
  modalidad: "MIXTO",
  minimo_por_equipo: 7,
  maximo_por_equipo: 10,
};

const PAQUETE = {
  id: "3f0c1c1e-0000-4000-8000-0000000000c1",
  created_at: "2026-11-19T10:00:00+00:00",
  updated_at: "2026-11-19T10:00:00+00:00",
  edicion_id: "3f0c1c1e-0000-4000-8000-0000000000e1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  nombre: "PAQUETE DE EJEMPLO",
  slug: "paquete-de-ejemplo",
  descripcion: "Paquete de ejemplo.",
  estado: "VIGENTE",
  cupos_incluidos: 10,
  precio: PRECIO,
  beneficios: [
    { codigo: "FIJO", nombre: "Beneficio fijo", tipo: "FIJO_INICIAL", cantidad: 1 },
  ],
  disciplinas: [DISCIPLINA],
};

const INSCRIPCION = {
  id: "3f0c1c1e-0000-4000-8000-0000000000a1",
  created_at: "2026-11-19T10:00:00+00:00",
  updated_at: "2026-11-19T10:00:00+00:00",
  edicion_id: "3f0c1c1e-0000-4000-8000-0000000000e1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  responsable_id: "3f0c1c1e-0000-4000-8000-0000000000b2",
  paquete_id: PAQUETE.id,
  paquete_nombre: PAQUETE.nombre,
  estado: "CREADA",
  referencia: "INSCRIPCION:3f0c1c1e-0000-4000-8000-0000000000a1:INICIAL",
  cupos_solicitados: 10,
  cupos_pagados: 0,
  cupos_asignados: 0,
  cupos_disponibles: 0,
  equipos: [
    {
      id: "3f0c1c1e-0000-4000-8000-0000000000f1",
      created_at: "2026-11-19T10:00:00+00:00",
      updated_at: "2026-11-19T10:00:00+00:00",
      disciplina_id: DISCIPLINA.id,
      disciplina_nombre: DISCIPLINA.nombre,
      nombre: "EQUIPO DE EJEMPLO",
      estado: "ACTIVO",
    },
  ],
};

const COMPRA = {
  compra_id: "3f0c1c1e-0000-4000-8000-0000000000b1",
  orden_pago_id: "3f0c1c1e-0000-4000-8000-0000000000b3",
  estado: "PENDIENTE",
  total: "750.00",
  moneda: "PEN",
  reutilizada: false,
};

const POOL = {
  inscripcion_id: INSCRIPCION.id,
  cupos_pagados: 10,
  cupos_asignados: 0,
  cupos_disponibles: 10,
  participaciones: [],
  impedimentos: [
    {
      codigo: "EQUIPO_MAXIMO",
      mensaje: "Este equipo alcanzó el máximo de participantes.",
      equipo_id: "3f0c1c1e-0000-4000-8000-0000000000f1",
    },
  ],
  causa_operativa: "POOL_CON_CUPOS_DISPONIBLES",
};

describe("API-02 — el espejo del catálogo del backend objetivo", () => {
  it("acepta la forma exacta de CatalogoPaquetesOut", () => {
    const resultado = catalogoPaquetesSchema.parse({
      edicion_id: "3f0c1c1e-0000-4000-8000-0000000000e1",
      edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
      paquetes: [PAQUETE],
    });

    expect(resultado.paquetes).toHaveLength(1);
    expect(resultado.paquetes[0].precio.monto).toBe("750.00");
    expect(resultado.paquetes[0].disciplinas[0].slug).toBe("futsal");
  });

  it("acepta la forma exacta de CatalogoDisciplinasOut", () => {
    const resultado = catalogoDisciplinasSchema.parse({
      edicion_id: "3f0c1c1e-0000-4000-8000-0000000000e1",
      edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
      disciplinas: [DISCIPLINA],
    });

    expect(resultado.disciplinas[0].minimo_por_equipo).toBe(7);
  });

  it("RECHAZA la forma del backend congelado (evento_id, sigla, precios[])", () => {
    const congelado = {
      id: PAQUETE.id,
      evento_id: "evento",
      nombre: PAQUETE.nombre,
      tipo: "PACK",
      precio_preventa: 750,
      tiene_fiesta: true,
      disciplinas_resumen: ["FUTSAL"],
      disciplinas: [{ disciplina_id: DISCIPLINA.id, disciplina_sigla: "FUT" }],
      beneficios: [],
      precios: [{ etapa: "REGULAR", precio_unitario: 750 }],
    };

    expect(() => catalogoPaquetesSchema.parse({ paquetes: [congelado] })).toThrow();
  });

  it("el importe es una cadena: el backend serializa el Decimal así", () => {
    expect(() =>
      catalogoPaquetesSchema.parse({
        edicion_id: "e",
        edicion_nombre: "E",
        paquetes: [{ ...PAQUETE, precio: { ...PRECIO, monto: 750 } }],
      }),
    ).toThrow();
  });
});

describe("API-02 — el espejo de la inscripción y del pool", () => {
  it("acepta la forma exacta de InscripcionDetalleOut", () => {
    const resultado = inscripcionDetalleSchema.parse(INSCRIPCION);

    expect(resultado.cupos_pagados).toBe(0);
    expect(resultado.equipos[0].nombre).toBe("EQUIPO DE EJEMPLO");
  });

  it("acepta la forma exacta de InscripcionInicialOut", () => {
    const resultado = inscripcionInicialSchema.parse({
      inscripcion: INSCRIPCION,
      compra: COMPRA,
      causa_operativa: "INSCRIPCION_CREADA",
    });

    expect(resultado.compra.total).toBe("750.00");
    expect(resultado.compra.reutilizada).toBe(false);
  });

  it("acepta la forma exacta de PoolOut", () => {
    const resultado = poolSchema.parse(POOL);

    expect(resultado.cupos_disponibles).toBe(10);
    expect(resultado.impedimentos[0].mensaje).toBe(
      "Este equipo alcanzó el máximo de participantes.",
    );
  });

  it("acepta la forma exacta de CompraCreadaOut", () => {
    const resultado = compraCreadaSchema.parse({
      inscripcion_id: INSCRIPCION.id,
      compra: { ...COMPRA, reutilizada: true },
      cupos_solicitados: 3,
      cupos_pagados: 10,
      cupos_asignados: 0,
      cupos_disponibles: 10,
      causa_operativa: "COMPRA_CUPOS_REUTILIZADA",
    });

    expect(resultado.compra.reutilizada).toBe(true);
    expect(resultado.cupos_solicitados).toBe(3);
  });

  it("el pool se lee con sus TRES números: el cliente no calcula ninguno", () => {
    const resultado = poolSchema.parse(POOL);

    // Los tres números vienen DECLARADOS. La suite no comprueba ninguna
    // resta: la aritmética es del servidor (RN-I03).
    expect(resultado.cupos_pagados).toBe(10);
    expect(resultado.cupos_asignados).toBe(0);
    expect(resultado.cupos_disponibles).toBe(10);
  });
});

describe("API-02 — el envelope se abre con ruido", () => {
  it("devuelve el dato y el mensaje del servidor", () => {
    const respuesta = leerRespuesta(
      catalogoPaquetesSchema,
      {
        success: true,
        data: {
          edicion_id: "e",
          edicion_nombre: "E",
          paquetes: [],
        },
        error: null,
        message: "Catálogo de paquetes consultado correctamente.",
      },
      "sin catálogo",
    );

    expect(respuesta.data.paquetes).toEqual([]);
    expect(respuesta.message).toBe(
      "Catálogo de paquetes consultado correctamente.",
    );
  });

  it("falla cuando el servidor dice que no tuvo éxito", () => {
    expect(() =>
      leerRespuesta(
        catalogoPaquetesSchema,
        { success: false, data: null, error: null, message: "No se pudo leer." },
        "sin catálogo",
      ),
    ).toThrow("No se pudo leer.");
  });

  it("falla cuando el cuerpo no es el envelope", () => {
    expect(() =>
      leerRespuesta(catalogoPaquetesSchema, { paquete: [] }, "sin catálogo"),
    ).toThrow();
  });
});

describe("API-02 — los payloads que viajan", () => {
  it("el alta viaja sin responsable, sin precio y sin cantidad", () => {
    const payload = construirPayloadAlta({
      edicion_id: "e",
      paquete_id: "p",
      equipos: [{ disciplina_id: "d", nombre: "Halcones" }],
    });

    expect(payload).toEqual({
      edicion_id: "e",
      paquete_id: "p",
      equipos: [{ disciplina_id: "d", nombre: "Halcones" }],
    });
    expect(Object.keys(payload)).not.toContain("responsable_id");
    expect(Object.keys(payload)).not.toContain("precio");
    expect(Object.keys(payload)).not.toContain("cantidad");
  });

  it("el alta acepta el payload del servidor", () => {
    const payload = inscripcionInicialInSchema.parse({
      edicion_id: "e",
      paquete_id: "p",
      equipos: [{ disciplina_id: "d", nombre: "Halcones" }],
    });

    expect(payload.equipos).toHaveLength(1);
  });

  it("el alta NO acota el número de equipos: el límite es del servidor", () => {
    const equipos = Array.from({ length: 21 }, (_v, i) => ({
      disciplina_id: "d" + i,
      nombre: "Equipo " + i,
    }));

    expect(() =>
      inscripcionInicialInSchema.parse({
        edicion_id: "e",
        paquete_id: "p",
        equipos,
      }),
    ).not.toThrow();
  });

  it("el participante viaja con el identificador o con el documento, nunca con ambos", () => {
    const porIdentificador = construirPayloadParticipante({
      persona_id: "p",
      equipo_id: "e",
    });

    expect(porIdentificador).toEqual({ equipo_id: "e", persona_id: "p" });

    const porDocumento = construirPayloadParticipante({
      tipo_documento: "DNI",
      numero_documento: "12345678",
      equipo_id: "e",
    });

    expect(porDocumento).toEqual({
      equipo_id: "e",
      tipo_documento: "DNI",
      numero_documento: "12345678",
    });
  });

  it("el participante acepta la forma del servidor", () => {
    const payload = participanteAsignarInSchema.parse({
      persona_id: "3f0c1c1e-0000-4000-8000-0000000000b2",
      equipo_id: "3f0c1c1e-0000-4000-8000-0000000000f1",
    });

    expect(payload.equipo_id).toBe("3f0c1c1e-0000-4000-8000-0000000000f1");
  });

  it("la compra de cupos viaja SOLO con la cantidad", () => {
    expect(construirPayloadCompraCupos(3)).toEqual({ cantidad: 3 });
  });
});
