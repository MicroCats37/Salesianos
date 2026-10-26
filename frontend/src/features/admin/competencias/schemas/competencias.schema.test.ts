import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  type Agenda,
  AgendaEnvelopeSchema,
  AgendaSchema,
  type CompetenciaDetalle,
  CompetenciaDetalleEnvelopeSchema,
  CompetenciaDetalleSchema,
  type CompetenciaEquipo,
  CompetenciaEquipoSchema,
  type CompetenciaListaItem,
  CompetenciaListaItemSchema,
  CompetenciasListaEnvelopeSchema,
  type Cuadro,
  CuadroSchema,
  type Encuentro,
  EncuentroSchema,
  type Ronda,
  type RondaCuadro,
  RondaCuadroSchema,
  RondaSchema,
} from "./competencias.schema";

/**
 * Focused contract test of the Zod mirrors of the `competencias` module.
 *
 * The mirrors are the CLIENT half of the wrapper contract: they must declare
 * EXACTLY the fields of the backend wrapper and NEVER invent a field
 * (`contract/api-wrapper-presenter-contract.md` §7).
 *
 * The drift is verified against the SOURCE of the backend schema, so a field
 * added there and forgotten here fails the test instead of being silently
 * dropped by the parser.
 */

// ── Payloads ─────────────────────────────────────────────────────────────────

function encuentroPayload(overrides: Partial<Encuentro> = {}): Encuentro {
  return {
    id: "e1",
    ronda_id: "r1",
    ronda_etiqueta: "Cuartos de final",
    ronda_orden: 1,
    competencia_id: "c1",
    competencia_nombre: "Eliminatoria F7 B",
    orden: 1,
    participante_1_id: "eq1",
    participante_1_nombre: "Los Andes",
    participante_2_id: "eq2",
    participante_2_nombre: "San Francisco",
    inicio_programado: "2026-11-16T14:30:00",
    fin_programado: "2026-11-16T15:10:00",
    estado: "PROGRAMADO",
    estado_pre_suspension: null,
    iniciado_en: null,
    finalizado_en: null,
    es_bye: false,
    ganador_id: null,
    puntaje_1: null,
    puntaje_2: null,
    marcador_detalle: "",
    siguiente_encuentro_id: null,
    slot_destino: null,
    ganador_propagado_id: null,
    version: 1,
    ...overrides,
  };
}

function listaItemPayload(
  overrides: Partial<CompetenciaListaItem> = {},
): CompetenciaListaItem {
  return {
    id: "c1",
    evento_id: "ev1",
    disciplina_id: "di1",
    categoria_id: "ca1",
    nombre: "Eliminatoria F7 B",
    fecha: "2026-11-16",
    estado: "PLANIFICADA",
    version: 1,
    total_equipos: 6,
    total_encuentros: 4,
    total_encuentros_finalizados: 0,
    ...overrides,
  };
}

function equipoPayload(
  overrides: Partial<CompetenciaEquipo> = {},
): CompetenciaEquipo {
  return {
    id: "ce1",
    competencia_id: "c1",
    equipo_id: "eq1",
    equipo_nombre: "Los Andes",
    orden: 1,
    estado: "ACTIVO",
    version: 1,
    ...overrides,
  };
}

function rondaPayload(overrides: Partial<Ronda> = {}): Ronda {
  return {
    id: "r1",
    competencia_id: "c1",
    etiqueta: "Cuartos de final",
    orden: 1,
    estado: "ACTIVA",
    version: 1,
    total_encuentros: 2,
    ...overrides,
  };
}

// ── The source of the backend contract ───────────────────────────────────────

const RUTA_FUENTE_BACKEND =
  "../../../../../../backend/modules/competencias/presentation/schemas/competencias_schemas.py";

const FUENTE_BACKEND = readFileSync(
  new URL(RUTA_FUENTE_BACKEND, import.meta.url),
  "utf8",
).replace(/"""[\s\S]*?"""/g, "");

/** The direct bases of a class of the backend schema. */
function basesDe(clase: string): string[] {
  const coincidencia = new RegExp(`class ${clase}\\(([^)]*)\\)`).exec(
    FUENTE_BACKEND,
  );
  if (!coincidencia) return [];
  return coincidencia[1]
    .split(",")
    .map((base) => base.trim())
    .filter(Boolean);
}

/** The fields a class declares, INCLUDING the ones it inherits. */
function camposDe(clase: string): string[] {
  const inicio = FUENTE_BACKEND.indexOf(`class ${clase}(`);
  expect(inicio, `la clase ${clase} no existe en el backend`).toBeGreaterThan(
    -1,
  );

  const fin = FUENTE_BACKEND.indexOf("\nclass ", inicio + 1);
  const bloque = FUENTE_BACKEND.slice(
    inicio,
    fin === -1 ? FUENTE_BACKEND.length : fin,
  );

  const propios = Array.from(bloque.matchAll(/^ {4}([a-z_][a-z0-9_]*)\s*:/gm))
    .map((coincidencia) => coincidencia[1])
    .filter((campo) => !campo.startsWith("model_"));

  // `BaseSchema` is the shared base of the project, not a payload class: the
  // recursion stops there.
  const heredados = basesDe(clase)
    .filter((base) => base !== "BaseSchema")
    .flatMap((base) => camposDe(base));

  return [...new Set([...propios, ...heredados])];
}

// ── The mirrors declare EXACTLY the fields of the backend ───────────────────

describe("los mirrors declaran exactamente los campos del backend", () => {
  const PARES: Array<[string, { shape: object }]> = [
    ["CompetenciaListOut", CompetenciaListaItemSchema],
    ["CompetenciaEquipoOut", CompetenciaEquipoSchema],
    ["RondaOut", RondaSchema],
    ["EncuentroOut", EncuentroSchema],
    ["CompetenciaDetalleOut", CompetenciaDetalleSchema],
    ["RondaCuadroOut", RondaCuadroSchema],
    ["CuadroOut", CuadroSchema],
    ["AgendaOut", AgendaSchema],
  ];

  for (const [clase, esquema] of PARES) {
    it(`el mirror de ${clase} tiene los mismos campos`, () => {
      const delCliente = Object.keys(esquema.shape).sort();
      const delBackend = camposDe(clase).sort();

      expect(delCliente).toEqual(delBackend);
    });
  }
});

// ── The mirrors accept the payloads of the backend ──────────────────────────

describe("los mirrors aceptan los payloads del backend", () => {
  it("acepta una fila de la lista", () => {
    const fila = listaItemPayload();
    expect(CompetenciaListaItemSchema.parse(fila)).toEqual(fila);
  });

  it("acepta un encuentro con sus campos nulos", () => {
    const encuentro = encuentroPayload({
      participante_1_id: null,
      participante_1_nombre: null,
      participante_2_id: null,
      participante_2_nombre: null,
      inicio_programado: null,
      fin_programado: null,
      ganador_id: null,
      marcador_detalle: null,
    });

    expect(EncuentroSchema.parse(encuentro)).toEqual(encuentro);
  });

  it("acepta un detalle con sus equipos y sus rondas", () => {
    const detalle: CompetenciaDetalle = {
      ...listaItemPayload(),
      created_at: "2026-11-01T10:00:00",
      equipos: [equipoPayload()],
      rondas: [rondaPayload()],
    };

    expect(CompetenciaDetalleSchema.parse(detalle)).toEqual(detalle);
  });

  it("acepta un cuadro con sus rondas y sus encuentros", () => {
    const ronda: RondaCuadro = {
      id: "r1",
      etiqueta: "Cuartos de final",
      orden: 1,
      estado: "ACTIVA",
      encuentros: [encuentroPayload()],
    };

    const cuadro: Cuadro = {
      competencia_id: "c1",
      nombre: "Eliminatoria F7 B",
      fecha: "2026-11-16",
      estado: "PLANIFICADA",
      total_equipos: 6,
      rondas: [ronda],
    };

    expect(CuadroSchema.parse(cuadro)).toEqual(cuadro);
  });

  it("acepta una agenda vacía", () => {
    const agenda: Agenda = {
      fecha: "2026-11-16",
      total: 0,
      encuentros: [],
    };

    expect(AgendaSchema.parse(agenda)).toEqual(agenda);
  });
});

// ── The drift fails loudly ──────────────────────────────────────────────────

describe("el desvío del contrato falla de forma ruidosa", () => {
  it("rechaza una fila sin su nombre", () => {
    const { nombre: _nombre, ...sinNombre } = listaItemPayload();

    expect(CompetenciaListaItemSchema.safeParse(sinNombre).success).toBe(false);
  });

  it("rechaza una fila con un contador que no es un número", () => {
    const fila = { ...listaItemPayload(), total_equipos: "seis" };

    expect(CompetenciaListaItemSchema.safeParse(fila).success).toBe(false);
  });

  it("rechaza un encuentro sin su marca de bye", () => {
    const { es_bye: _esBye, ...sinBye } = encuentroPayload();

    expect(EncuentroSchema.safeParse(sinBye).success).toBe(false);
  });
});

// ── The envelopes ───────────────────────────────────────────────────────────

describe("los envelopes comparten la forma de la API", () => {
  it("acepta el envelope de la lista", () => {
    const envelope = {
      success: true,
      data: [listaItemPayload()],
      error: null,
      message: null,
    };

    expect(CompetenciasListaEnvelopeSchema.parse(envelope)).toEqual(envelope);
  });

  it("acepta el envelope de la agenda", () => {
    const envelope = {
      success: true,
      data: { fecha: "2026-11-16", total: 0, encuentros: [] },
      error: null,
      message: null,
    };

    expect(AgendaEnvelopeSchema.parse(envelope)).toEqual(envelope);
  });

  it("acepta un envelope de error con su codigo estable", () => {
    const envelope = {
      success: false,
      data: null,
      error: { code: "COMPETENCIA_NOT_FOUND", message: "No encontrado." },
      message: null,
    };

    expect(AgendaEnvelopeSchema.parse(envelope)).toEqual(envelope);
  });

  it("rechaza una lista donde se espera un detalle", () => {
    const envelope = {
      success: true,
      data: [listaItemPayload()],
      error: null,
      message: null,
    };

    expect(CompetenciaDetalleEnvelopeSchema.safeParse(envelope).success).toBe(
      false,
    );
  });
});
