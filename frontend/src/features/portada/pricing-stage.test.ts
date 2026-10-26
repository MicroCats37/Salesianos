import { describe, expect, it } from "vitest";
import {
  estado,
  etiqueta,
  nota,
  precioDe,
  unidadPrecio,
} from "./pricing-stage";

/**
 * Las ventanas de venta se comparan contra instantes absolutos (Lima no
 * aplica horario de verano), por eso cada caso fija un instante explícito en
 * lugar de depender del reloj del runner.
 */
const INSTANTE = {
  antesDePreventa: "2026-10-20T10:00:00-05:00",
  preventa: "2026-10-25T19:59:00-05:00",
  finDePreventa: "2026-10-25T20:00:00-05:00",
  regular: "2026-10-26T00:00:00-05:00",
  finDeRegular: "2026-11-08T20:00:00-05:00",
  extemporanea: "2026-11-09T00:00:00-05:00",
  cierre: "2026-11-18T20:00:00-05:00",
} as const;

function instante(iso: string): number {
  return new Date(iso).getTime();
}

const PAQUETE = {
  precio_preventa: 400,
  precio_regular: 500,
  cantidad_minima_compra: 10,
};

describe("pricing-stage · ventanas de venta", () => {
  it("abre en preventa antes del 25 de octubre", () => {
    expect(estado(instante(INSTANTE.antesDePreventa)).key).toBe("preventa");
    expect(etiqueta(instante(INSTANTE.antesDePreventa))).toBe(
      "PREVENTA · HASTA EL 25 OCT, 8 P. M.",
    );
  });

  it("cierra la preventa exactamente a las 8:00 p. m. del 25 de octubre", () => {
    expect(estado(instante(INSTANTE.preventa)).key).toBe("preventa");
    expect(estado(instante(INSTANTE.finDePreventa)).key).toBe("gap");
    expect(etiqueta(instante(INSTANTE.finDePreventa))).toBe(
      "PREVENTA FINALIZADA",
    );
  });

  it("abre la tarifa regular el 26 de octubre", () => {
    expect(estado(instante(INSTANTE.regular)).key).toBe("regular");
    expect(etiqueta(instante(INSTANTE.regular))).toBe(
      "TARIFA REGULAR · HASTA EL 8 NOV, 8 P. M.",
    );
  });

  it("deja un intervalo de consulta entre regular y extemporánea", () => {
    expect(estado(instante(INSTANTE.finDeRegular)).key).toBe("gap");
    expect(etiqueta(instante(INSTANTE.finDeRegular))).toBe(
      "ETAPA REGULAR FINALIZADA",
    );
  });

  it("abre la inscripción extemporánea el 9 de noviembre", () => {
    expect(estado(instante(INSTANTE.extemporanea)).key).toBe("extemporanea");
    expect(etiqueta(instante(INSTANTE.extemporanea))).toBe(
      "INSCRIPCIÓN EXTEMPORÁNEA",
    );
  });

  it("cierra las inscripciones el 18 de noviembre", () => {
    expect(estado(instante(INSTANTE.cierre)).key).toBe("cerrada");
    expect(etiqueta(instante(INSTANTE.cierre))).toBe(
      "INSCRIPCIONES FINALIZADAS",
    );
    expect(nota(instante(INSTANTE.cierre))).toContain("18 de noviembre");
  });
});

describe("pricing-stage · precio por etapa", () => {
  it("devuelve el precio de preventa durante la preventa", () => {
    expect(precioDe(PAQUETE, instante(INSTANTE.preventa))).toBe(400);
  });

  it("devuelve el precio regular durante la etapa regular", () => {
    expect(precioDe(PAQUETE, instante(INSTANTE.regular))).toBe(500);
  });

  it("devuelve null —consultar— en las etapas sin tarifa publicada", () => {
    expect(precioDe(PAQUETE, instante(INSTANTE.antesDePreventa))).toBe(400);
    expect(precioDe(PAQUETE, instante(INSTANTE.finDePreventa))).toBeNull();
    expect(precioDe(PAQUETE, instante(INSTANTE.finDeRegular))).toBeNull();
    expect(precioDe(PAQUETE, instante(INSTANTE.extemporanea))).toBeNull();
    expect(precioDe(PAQUETE, instante(INSTANTE.cierre))).toBeNull();
  });

  it("respeta un precio de preventa ausente", () => {
    expect(
      precioDe(
        { ...PAQUETE, precio_preventa: null },
        instante(INSTANTE.preventa),
      ),
    ).toBeNull();
  });
});

describe("pricing-stage · unidad del precio", () => {
  it("usa x equipo cuando la compra mínima es de 10 o menos", () => {
    expect(unidadPrecio({ ...PAQUETE, cantidad_minima_compra: 7 })).toBe(
      "x equipo",
    );
    expect(unidadPrecio({ ...PAQUETE, cantidad_minima_compra: 10 })).toBe(
      "x equipo",
    );
  });

  it("usa x promoción cuando la compra mínima supera los 10", () => {
    expect(unidadPrecio({ ...PAQUETE, cantidad_minima_compra: 11 })).toBe(
      "x promoción",
    );
    expect(unidadPrecio({ ...PAQUETE, cantidad_minima_compra: 15 })).toBe(
      "x promoción",
    );
  });
});
