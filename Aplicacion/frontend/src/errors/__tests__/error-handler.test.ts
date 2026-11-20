// src/errors/__tests__/error-handler.test.ts
//
// The error handler has to attach the field errors to EVERY parsed error, so
// that a component never parses an API error on its own.
//
// The suites of this packet are WRITTEN but NOT EXECUTED.

import { describe, expect, it } from "vitest";

import { handleApiError } from "@/errors/error-handler";

function axiosError(status: number, data: unknown) {
  return { response: { status, data }, request: {}, isAxiosError: true };
}

describe("handleApiError — the field errors of the frozen envelope", () => {
  it("attaches the field errors of a 422 and keeps the public message", () => {
    const error = handleApiError(
      axiosError(422, {
        success: false,
        data: null,
        error: {
          code: "INVALID_REQUEST",
          message: "La solicitud no es válida.",
          details: null,
          field_errors: [
            { field: "titulo", code: "REQUIRED", message: "El título es obligatorio." },
          ],
        },
        message: null,
      }),
    );

    expect(error.message).toBe("La solicitud no es válida.");
    expect(error.status).toBe(422);
    expect(error.fieldErrors).toEqual({
      titulo: "El título es obligatorio.",
    });
  });

  it("attaches the field errors of the legacy detail[] shape", () => {
    const error = handleApiError(
      axiosError(422, {
        detail: [
          { loc: ["body", "titulo"], msg: "Este campo es requerido.", type: "value_error.missing" },
        ],
      }),
    );

    expect(error.fieldErrors).toEqual({ titulo: "Este campo es requerido." });
    expect(error.message).toContain("Este campo es requerido.");
  });

  it("does not invent field errors when the response carries none", () => {
    const error = handleApiError(
      axiosError(404, {
        success: false,
        data: null,
        error: { code: "NO_ENCONTRADO", message: "No se encontró.", details: null },
        message: null,
      }),
    );

    expect(error.message).toBe("No se encontró.");
    expect(error.fieldErrors).toBeUndefined();
  });

  it("reports a network failure without field errors", () => {
    const error = handleApiError({ request: {}, message: "Network Error" });

    expect(error.fieldErrors).toBeUndefined();
    expect(error.message.length).toBeGreaterThan(0);
  });
});
