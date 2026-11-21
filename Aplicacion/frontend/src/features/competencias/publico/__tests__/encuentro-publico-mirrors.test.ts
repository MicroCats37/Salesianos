import { describe, expect, it } from "vitest";

import {
  encuentroPublicoSchema,
  encuentrosPublicosEnvelope,
  encuentrosPublicosSchema,
} from "../schemas/encuentro-publico.schema";
import {
  ENCUENTRO_EN_VIVO,
  ENCUENTRO_FINALIZADO,
  ENCUENTRO_PROGRAMADO,
  ENCUENTROS_PUBLICOS,
} from "./datos.contract";

/**
 * The mirror of the wire of the PUBLIC surface of the encounters.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * The examples are the JSON that the presenters of the target backend publish
 * for `GET /publico/competencias/encuentros`. A body that does not comply is
 * a LOUD failure: the mirror never trusts a partial answer.
 */
describe("el espejo de la superficie pública de los encuentros", () => {
  it("acepta la forma exacta de EncuentroPublicoOut", () => {
    const resultado = encuentroPublicoSchema.parse(ENCUENTRO_FINALIZADO);

    expect(resultado.ronda_etiqueta).toBe("Cuartos de final");
    expect(resultado.participantes).toHaveLength(2);
    expect(resultado.estado_publico).toBe("FINALIZADO");
  });

  it("acepta la forma exacta de EncuentrosPublicosOut con sus tres cubos", () => {
    const resultado = encuentrosPublicosSchema.parse(ENCUENTROS_PUBLICOS);

    expect(resultado.edicion_nombre).toBe("Salesianos Fest 2027");
    expect(resultado.total).toBe(3);
    expect(resultado.en_vivo).toHaveLength(1);
    expect(resultado.proximos).toHaveLength(1);
    expect(resultado.finalizados).toHaveLength(1);
  });

  it("acepta el envelope congelado de la ruta pública", () => {
    const envelope = encuentrosPublicosEnvelope.parse({
      success: true,
      data: ENCUENTROS_PUBLICOS,
      error: null,
      message: null,
    });

    expect(envelope.data?.total).toBe(3);
  });

  it("rechaza un cuerpo sin los tres cubos", () => {
    const { finalizados: _finalizados, ...sinCubos } = ENCUENTROS_PUBLICOS;

    expect(() => encuentrosPublicosSchema.parse(sinCubos)).toThrow();
  });

  it("rechaza un encuentro sin versión", () => {
    const { version: _version, ...sinVersion } = ENCUENTRO_EN_VIVO;

    expect(() => encuentroPublicoSchema.parse(sinVersion)).toThrow();
  });

  it("CONSERVA la versión: el futuro canal la necesita para descartar un evento viejo", () => {
    const resultado = encuentroPublicoSchema.parse(ENCUENTRO_FINALIZADO);

    expect(resultado.version).toBe(7);
  });

  it("el ganador viaja como lo que es: la autoridad, no el que va ganando", () => {
    const resultado = encuentroPublicoSchema.parse(ENCUENTRO_FINALIZADO);

    // El marcador es 9 a 4 y el ganador es el SEGUNDO slot: el espejo no
    // deduce nada, travels lo que el backend publicó.
    expect(resultado.puntaje_1).toBe(9);
    expect(resultado.puntaje_2).toBe(4);
    expect(resultado.ganador_equipo_id).toBe(
      "77777777-7777-4777-8777-777777777777",
    );
    expect(resultado.ganador_equipo_nombre).toBe("Salesianos B");
  });

  it("un encuentro sin ganador NO inventa uno", () => {
    const resultado = encuentroPublicoSchema.parse(ENCUENTRO_EN_VIVO);

    expect(resultado.ganador_equipo_id).toBeNull();
    expect(resultado.ganador_equipo_nombre).toBeNull();
  });

  it("un slot libre viaja con sus identificadores vacíos", () => {
    const resultado = encuentroPublicoSchema.parse({
      ...ENCUENTRO_PROGRAMADO,
      participantes: [
        {
          slot: "PARTICIPANTE_1",
          competencia_equipo_id: null,
          equipo_id: null,
          equipo_nombre: null,
          orden: null,
        },
      ],
    });

    expect(resultado.participantes[0].equipo_nombre).toBeNull();
  });

  it("rechaza un cuerpo que no es un objeto de encuentros", () => {
    expect(() => encuentrosPublicosSchema.parse({ total: "muchos" })).toThrow();
  });
});
