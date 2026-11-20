import { describe, expect, it } from "vitest";

import {
  agendaEnvelope,
  avancePreviewSchema,
  competenciaDetalleSchema,
  competenciaListadoSchema,
  correccionAplicarSchema,
  correccionPreviewSchema,
  encuentroActualizarSchema,
  encuentroSchema,
  equipoElegibleSchema,
} from "../schemas/competencia.schema";
import {
  AGENDA,
  COMPETENCIA,
  DETALLE,
  ENCUENTRO,
  EQUIPO_ELEGIBLE,
  EQUIPO_NO_ELEGIBLE,
  VISTA_PREVIA_AVANCE,
  VISTA_PREVIA_CORRECCION,
} from "./datos.contract";

/**
 * The mirror of the wire of the TARGET backend for the competitions area.
 *
 * The examples are the JSON that the presenters of `DOM-07` publish
 * (`Aplicacion/backend/modules/competencias/presentation/schemas/competencias_schemas.py`).
 * They are EXAMPLES of the wire, not a transport: no module of production
 * imports this file.
 *
 * **These suites have NEVER RUN.** They are written and the execution is
 * deferred to the verification phase. Nothing here may be read as a green
 * result.
 */
describe("API-05 — el espejo del backend objetivo (competencias)", () => {
  it("acepta la forma exacta de CompetenciaListadoOut", () => {
    const resultado = competenciaListadoSchema.parse(COMPETENCIA);

    expect(resultado.nombre).toBe("Copa Salesianos");
    expect(resultado.total_encuentros).toBe(7);
  });

  it("acepta la forma exacta de CompetenciaDetalleOut con sus rondas", () => {
    const resultado = competenciaDetalleSchema.parse(DETALLE);

    expect(resultado.equipos).toHaveLength(1);
    expect(resultado.rondas[0].encuentros[0].id).toBe(ENCUENTRO.id);
  });

  it("acepta la forma exacta de RondaOut y de su encuentro", () => {
    const resultado = encuentroSchema.parse(ENCUENTRO);

    expect(resultado.participantes).toHaveLength(2);
    expect(resultado.ganador_equipo_id).toBe(
      "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
    );
    expect(resultado.acciones).toEqual(["corregir", "avanzar"]);
  });

  it("acepta la forma exacta de AgendaOut", () => {
    const resultado = agendaEnvelope.parse({
      success: true,
      data: AGENDA,
      error: null,
      message: null,
    });

    expect(resultado.data?.total).toBe(1);
  });

  it("el veredicto de elegibilidad conserva el CÓDIGO del motivo", () => {
    const elegible = equipoElegibleSchema.parse(EQUIPO_ELEGIBLE);
    const inelegible = equipoElegibleSchema.parse(EQUIPO_NO_ELEGIBLE);

    expect(elegible.motivo).toBe("ELEGIBLE");
    expect(elegible.es_elegible).toBe(true);
    // El motivo lo publica el DUEÑO de la inscripción: el cliente no lo
    // deduce, lo imprime (QA-K01).
    expect(inelegible.motivo).toBe("PLANTILLA_INCOMPLETA");
    expect(inelegible.es_elegible).toBe(false);
  });

  it("RECHAZA un encuentro sin versión: el bloqueo optimista es obligatorio", () => {
    const { version: _version, ...sinVersion } = ENCUENTRO;

    expect(() => encuentroSchema.parse(sinVersion)).toThrow();
  });

  it("RECHAZA un ganador que no viaja como identificador", () => {
    expect(() =>
      encuentroSchema.parse({ ...ENCUENTRO, ganador_equipo_id: 42 }),
    ).toThrow();
  });

  it("la VISTA PREVIA no escribe: no lleva versión ni motivo", () => {
    const vista = avancePreviewSchema.parse(VISTA_PREVIA_AVANCE);

    expect(vista).not.toHaveProperty("expected_version");
    expect(vista).not.toHaveProperty("motivo");
    expect(vista.puede_confirmar).toBe(true);
  });

  it("la vista previa de la corrección declara su impacto", () => {
    const vista = correccionPreviewSchema.parse(VISTA_PREVIA_CORRECCION);

    expect(vista.total_afectados).toBe(1);
    expect(vista.descendientes[0].afecta).toBe(true);
    expect(vista.requiere_override).toBe(false);
  });

  it("la CONFIRMACIÓN de la corrección exige versión, motivo y las dos autorizaciones", () => {
    expect(() =>
      correccionAplicarSchema.parse({
        ganador_id: "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
        override: false,
        acepta_impacto: false,
        expected_version: 4,
      }),
    ).toThrow();
  });

  it("la edición de un encuentro distingue AUSENTE de NULL explícito", () => {
    const ausente = encuentroActualizarSchema.parse({
      expected_version: 4,
    });
    const limpieza = encuentroActualizarSchema.parse({
      participante_1_id: null,
      expected_version: 4,
    });

    expect("participante_1_id" in ausente).toBe(false);
    expect(limpieza.participante_1_id).toBeNull();
  });
});
