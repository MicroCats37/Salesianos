import { describe, expect, it } from "vitest";

import {
  crearPatrocinadorSchema,
  patrocinadorEnvelope,
  patrocinadorSchema,
} from "../schemas/patrocinador.schema";
import { PATROCINADOR, PATROCINADOR_SIN_PIEZAS } from "./datos.contract";

/**
 * The mirror of the wire of the TARGET backend for the sponsors area.
 *
 * The examples are the JSON that the presenter of `DOM-08` publishes
 * (`Aplicacion/backend/modules/patrocinadores/presentation/schemas/patrocinadores_schemas.py`).
 * They are EXAMPLES of the wire, not a transport: no module of production
 * imports this file.
 *
 * **These suites have NEVER RUN.** They are written and the execution is
 * deferred to the verification phase. Nothing here may be read as a green
 * result.
 */
describe("API-05 — el espejo del backend objetivo (patrocinadores)", () => {
  it("acepta la forma exacta de PatrocinadorOut con sus tres bloques", () => {
    const resultado = patrocinadorSchema.parse(PATROCINADOR);

    expect(resultado.nombre).toBe("Colegio Norte");
    expect(resultado.slug).toBe("colegio-norte");
    expect(resultado.edicion_nombre).toBe("Salesianos FEST 2026");
  });

  it("acepta un patrocinador SIN logo y SIN galería", () => {
    const resultado = patrocinadorSchema.parse(PATROCINADOR_SIN_PIEZAS);

    expect(resultado.logo).toBeNull();
    expect(resultado.imagenes).toHaveLength(0);
    expect(resultado.visible).toBe(false);
  });

  it("el logo puede no tener URL: el hueco se dibuja, no la imagen rota", () => {
    const resultado = patrocinadorSchema.parse({
      ...PATROCINADOR,
      logo: { url: null, disponible: false },
    });

    expect(resultado.logo?.url).toBeNull();
    expect(resultado.logo?.disponible).toBe(false);
  });

  it("la galería conserva el ORDEN que declara el backend", () => {
    const resultado = patrocinadorSchema.parse(PATROCINADOR);

    expect(resultado.imagenes.map((imagen) => imagen.orden)).toEqual([0, 1]);
  });

  it("NO hay ninguna cifra en el patrocinador: ni un monto, ni una comisión", () => {
    const resultado = patrocinadorSchema.parse(PATROCINADOR);

    expect(Object.keys(resultado)).not.toContain("monto");
    expect(Object.keys(resultado)).not.toContain("aportacion");
    expect(Object.keys(resultado)).not.toContain("comision");
  });

  it("RECHAZA un identificador que no es un UUID", () => {
    expect(() =>
      patrocinadorSchema.parse({ ...PATROCINADOR, id: "colegio-norte" }),
    ).toThrow();
  });

  it("RECHAZA una galería que no es una lista de imágenes", () => {
    expect(() =>
      patrocinadorSchema.parse({ ...PATROCINADOR, imagenes: {} }),
    ).toThrow();
  });

  it("el envelope se abre con el mensaje del servidor", () => {
    const respuesta = patrocinadorEnvelope.parse({
      success: true,
      data: PATROCINADOR,
      error: null,
      message: null,
    });

    expect(respuesta.data?.nombre).toBe("Colegio Norte");
  });

  it("el alta exige el slug en kebab-case: el protocolo multipart no lo confunde", () => {
    expect(() =>
      crearPatrocinadorSchema.parse({
        nombre: "Colegio Norte",
        slug: "colegio_norte",
        descripcion: "",
        sitio_web: "",
        visible: true,
        logo: null,
        imagenes: [],
      }),
    ).toThrow();
  });

  it("el alta declara la galería ORDENADA y el token de cada imagen", () => {
    const alta = crearPatrocinadorSchema.parse({
      nombre: "Colegio Norte",
      slug: "colegio-norte",
      descripcion: "",
      sitio_web: "",
      visible: true,
      logo: "file_2f6a7b8c-9d0e-4f2a-8b4c-5d6e7f8091a2",
      imagenes: [
        {
          token: "file_3a7b8c9d-0e1f-4a3b-9c5d-6e7f8091a2b3",
          texto_alternativo: "El stand del patrocinador",
        },
      ],
    });

    expect(alta.imagenes[0].token.startsWith("file_")).toBe(true);
    expect(alta.logo?.startsWith("file_")).toBe(true);
  });
});
