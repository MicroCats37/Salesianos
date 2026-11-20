import { describe, expect, it } from "vitest";
import type { EstadoActivacion } from "../types/pagos.types";
import {
  CODIGOS_ESTADO_ACTIVACION_PAGO,
  rolActivacionDesdeCodigo,
  veredictoActivacionDesdeEstado,
} from "../utils/pagos.adaptador.utils";

/**
 * The activation verdict of a paid purchase (`XCT-03`).
 *
 * The suite proves the rules the interface depends on:
 *
 * 1. the bucket is resolved by the ADAPTER, never by a component;
 * 2. the wording of the backend is copied VERBATIM;
 * 3. an unknown code renders NEUTRALLY: the browser never invents a meaning.
 */

const ESTADO: EstadoActivacion = {
  codigo: "FALLIDA",
  etiqueta: "Fallida",
  descripcion:
    "El pago está confirmado y estamos resolviendo la activación de tu compra.",
  recuperable: true,
  proxima_accion: "REINTENTAR_ACTIVACION",
};

describe("el veredicto de la activación de derechos", () => {
  it("copia el estado del backend sin reescribirlo", () => {
    const veredicto = veredictoActivacionDesdeEstado(ESTADO);

    expect(veredicto.estado).toEqual(ESTADO);
    expect(veredicto.estado.etiqueta).toBe(ESTADO.etiqueta);
    expect(veredicto.estado.descripcion).toBe(ESTADO.descripcion);
    expect(veredicto.estado.proxima_accion).toBe("REINTENTAR_ACTIVACION");
  });

  it("resuelve el cubo visual en el adaptador, no en el componente", () => {
    const veredicto = veredictoActivacionDesdeEstado(ESTADO);

    expect(veredicto.rol).toBe("atencion");
  });

  it("conoce los cinco codigos del backend", () => {
    expect(CODIGOS_ESTADO_ACTIVACION_PAGO).toEqual([
      "SIN_ACTIVACION",
      "ACTIVADA",
      "PENDIENTE",
      "EN_CURSO",
      "FALLIDA",
    ]);
  });

  it("mapea cada codigo a su cubo presentacional", () => {
    expect(rolActivacionDesdeCodigo("ACTIVADA")).toBe("confirmado");
    expect(rolActivacionDesdeCodigo("PENDIENTE")).toBe("pendiente");
    expect(rolActivacionDesdeCodigo("EN_CURSO")).toBe("verificando");
    expect(rolActivacionDesdeCodigo("FALLIDA")).toBe("atencion");
    expect(rolActivacionDesdeCodigo("SIN_ACTIVACION")).toBe("sin-confirmar");
  });

  it("un codigo desconocido se dibuja de forma neutra", () => {
    expect(rolActivacionDesdeCodigo("CODIGO_DEL_FUTURO")).toBe("desconocido");
    expect(rolActivacionDesdeCodigo("")).toBe("desconocido");
  });

  it("el archivo del adaptador no ramifica sobre el codigo fuera del mapa", () => {
    // La regla de `SH-03` §6 vive en el ADAPTADOR: el mapa es el único sitio
    // que conoce los codigos.
    const veredicto = veredictoActivacionDesdeEstado({
      ...ESTADO,
      codigo: "CODIGO_DEL_FUTURO",
    });

    expect(veredicto.estado.codigo).toBe("CODIGO_DEL_FUTURO");
    expect(veredicto.rol).toBe("desconocido");
  });
});
