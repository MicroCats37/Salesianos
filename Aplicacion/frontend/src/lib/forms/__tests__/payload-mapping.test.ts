// src/lib/forms/__tests__/payload-mapping.test.ts
//
// The EXACT wire shape of a create payload and of an update payload.
//
// The suites of this packet are WRITTEN but NOT EXECUTED: the runtime
// verification of FND-07 is deferred (the only command allowed in this packet
// is `npx tsc --noEmit`).

import { describe, expect, it } from "vitest";
import { z } from "zod";

import { buildCreatePayload } from "@/lib/forms/buildCreatePayload";
import { buildUpdatePayload } from "@/lib/forms/buildUpdatePayload";
import { imageField } from "@/lib/forms/imageField";

const fileSchema = imageField().schema;

const schema = z.object({
  titulo: z.string(),
  descripcion: z.string().nullable().optional(),
  cantidad: z.coerce.number().optional(),
  imagen: fileSchema,
  etiqueta: z.string().optional(),
});

type SchemaShape = z.infer<typeof schema>;

const file = new File(["contenido"], "logo.png", { type: "image/png" });

/**
 * The values of a form are a SUBSET of the declared fields: the mapping is
 * exercised with the values that were actually filled.
 */
const createPayload = (values: Record<string, unknown>) =>
  buildCreatePayload(values as unknown as SchemaShape, schema);

const updatePayload = (
  values: Record<string, unknown>,
  initialData: Record<string, unknown>,
) =>
  buildUpdatePayload(
    values as unknown as SchemaShape,
    initialData as unknown as Partial<SchemaShape>,
    schema,
    { strict: true },
  );

describe("buildCreatePayload — the full validated mapping", () => {
  it("sends every declared field that carries a value", () => {
    const payload = createPayload({
      titulo: "Inscripción",
      descripcion: "La inscripción de prueba",
      cantidad: 3,
      imagen: file,
    });

    expect(payload).toEqual({
      titulo: "Inscripción",
      descripcion: "La inscripción de prueba",
      cantidad: 3,
      imagen: file,
    });
  });

  it("omits a field that was never filled", () => {
    const payload = createPayload({
      titulo: "Inscripción",
      descripcion: undefined,
    });

    expect(payload).toEqual({ titulo: "Inscripción" });
    expect("descripcion" in payload).toBe(false);
  });

  it("keeps an explicit null: it is a value, not an absence", () => {
    const payload = createPayload({ titulo: "Inscripción", descripcion: null });

    expect(payload).toEqual({ titulo: "Inscripción", descripcion: null });
  });

  it("keeps the File: the transport owns the multipart construction", () => {
    const payload = createPayload({ titulo: "Inscripción", imagen: file });

    expect(payload.imagen).toBe(file);
  });

  it("omits the URL of a file that is already stored: there is nothing to upload", () => {
    const payload = createPayload({
      titulo: "Inscripción",
      imagen: "/media/logo.png",
    });

    expect("imagen" in payload).toBe(false);
  });

  it("never sends a field the schema does not declare", () => {
    const payload = createPayload({
      titulo: "Inscripción",
      campoInventado: "valor",
    });

    expect("campoInventado" in payload).toBe(false);
  });
});

describe("buildUpdatePayload — the strict update mapping", () => {
  const initialData = {
    titulo: "Inscripción",
    descripcion: "La inscripción de prueba",
    cantidad: 3,
    etiqueta: "sin etiqueta",
  };

  it("omits the values the user did not touch", () => {
    const payload = updatePayload(
      {
        titulo: "Inscripción",
        descripcion: "La inscripción de prueba",
        cantidad: 3,
        etiqueta: "sin etiqueta",
      },
      initialData,
    );

    expect(payload).toEqual({});
  });

  it("sends the value that changed", () => {
    const payload = updatePayload(
      { titulo: "Inscripción nueva", descripcion: "La inscripción de prueba" },
      initialData,
    );

    expect(payload).toEqual({ titulo: "Inscripción nueva" });
  });

  it("keeps an explicit null: it clears a nullable field", () => {
    const payload = updatePayload(
      { titulo: "Inscripción", descripcion: null },
      initialData,
    );

    expect(payload).toEqual({ descripcion: null });
  });

  it("sends the File that replaces the stored one", () => {
    const payload = updatePayload(
      { titulo: "Inscripción", imagen: file },
      initialData,
    );

    expect(payload).toEqual({ imagen: file });
  });

  it("omits the URL of a file that did not change", () => {
    const payload = updatePayload(
      { titulo: "Inscripción", imagen: "/media/logo.png" },
      initialData,
    );

    expect("imagen" in payload).toBe(false);
  });

  it("omits an absent field", () => {
    const payload = updatePayload(
      { titulo: "Inscripción", descripcion: undefined },
      initialData,
    );

    expect("descripcion" in payload).toBe(false);
  });

  it("sends every defined value when the mapping is not strict", () => {
    const payload = buildUpdatePayload(
      { titulo: "Inscripción", descripcion: "La inscripción de prueba" } as unknown as SchemaShape,
      initialData as unknown as Partial<SchemaShape>,
      schema,
      { strict: false },
    );

    expect(payload).toEqual({
      titulo: "Inscripción",
      descripcion: "La inscripción de prueba",
    });
  });
});
