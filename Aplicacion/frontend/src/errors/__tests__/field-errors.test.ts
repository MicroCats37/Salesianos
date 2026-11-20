// src/errors/__tests__/field-errors.test.ts
//
// The field-error channel of the frozen error envelope.
//
// The suites of this packet are WRITTEN but NOT EXECUTED: the runtime
// verification of FND-07 is deferred (the only command allowed in this packet
// is `npx tsc --noEmit`).

import { describe, expect, it } from "vitest";

import {
  fieldPathFromLocation,
  parseFieldErrorEntries,
  parseFieldErrors,
} from "@/errors/field-errors";

describe("fieldPathFromLocation", () => {
  it("drops the source of the error", () => {
    expect(fieldPathFromLocation(["body", "titulo"])).toBe("titulo");
    expect(fieldPathFromLocation(["query", "documento"])).toBe("documento");
  });

  it("keeps the nested path with its indexes", () => {
    expect(
      fieldPathFromLocation(["body", "beneficiarios", 0, "documento"]),
    ).toBe("beneficiarios.0.documento");
  });

  it("returns undefined when there is no field", () => {
    expect(fieldPathFromLocation(["body"])).toBeUndefined();
    expect(fieldPathFromLocation("titulo")).toBeUndefined();
    expect(fieldPathFromLocation(undefined)).toBeUndefined();
  });
});

describe("parseFieldErrors — the frozen channel", () => {
  it("reads error.field_errors[]", () => {
    const body = {
      success: false,
      data: null,
      error: {
        code: "INVALID_REQUEST",
        message: "La solicitud no es válida.",
        details: null,
        field_errors: [
          {
            field: "titulo",
            code: "REQUIRED",
            message: "El título es obligatorio.",
          },
          {
            field: "beneficiarios.0.documento",
            code: "INVALID_VALUE",
            message: "El documento no es válido.",
          },
        ],
      },
      message: null,
    };

    expect(parseFieldErrors(body)).toEqual({
      titulo: "El título es obligatorio.",
      "beneficiarios.0.documento": "El documento no es válido.",
    });
  });

  it("ignores a field error without a message", () => {
    const body = {
      error: {
        code: "INVALID_REQUEST",
        message: "La solicitud no es válida.",
        field_errors: [{ field: "titulo", code: "REQUIRED" }],
      },
    };

    expect(parseFieldErrors(body)).toBeUndefined();
  });

  it("keeps every message of a field that fails twice", () => {
    const body = {
      error: {
        field_errors: [
          { field: "titulo", message: "El título es obligatorio." },
          { field: "titulo", message: "El título es demasiado corto." },
        ],
      },
    };

    expect(parseFieldErrors(body)).toEqual({
      titulo: "El título es obligatorio. • El título es demasiado corto.",
    });
  });
});

describe("parseFieldErrors — the legacy wire shapes", () => {
  it("reads the Django Ninja / Pydantic detail[]", () => {
    const body = {
      detail: [
        {
          loc: ["body", "titulo"],
          msg: "Este campo es requerido.",
          type: "value_error.missing",
        },
        {
          loc: ["body", "precio"],
          msg: "Un número es requerido.",
          type: "type_error.number",
        },
      ],
    };

    expect(parseFieldErrors(body)).toEqual({
      titulo: "Este campo es requerido.",
      precio: "Un número es requerido.",
    });
  });

  it("reads a flat DRF style errors{}", () => {
    const body = { errors: { titulo: ["Este campo es requerido."] } };

    expect(parseFieldErrors(body)).toEqual({
      titulo: "Este campo es requerido.",
    });
  });

  it("reads the legacy flat details{} and never treats non_field_errors as a field", () => {
    const body = {
      error: {
        message: "La solicitud no es válida.",
        details: {
          non_field_errors: "No se puede crear la inscripción.",
          titulo: "Este campo es requerido.",
        },
      },
    };

    expect(parseFieldErrors(body)).toEqual({
      titulo: "Este campo es requerido.",
    });
  });
});

describe("parseFieldErrorEntries", () => {
  it("keeps the stable code of the error", () => {
    const body = {
      error: {
        field_errors: [
          {
            field: "cantidad",
            code: "CANTIDAD_INVALIDA",
            message: "La cantidad no es válida.",
          },
        ],
      },
    };

    expect(parseFieldErrorEntries(body)).toEqual([
      {
        field: "cantidad",
        code: "CANTIDAD_INVALIDA",
        message: "La cantidad no es válida.",
      },
    ]);
  });

  it("returns an empty list when the body carries no field error", () => {
    expect(parseFieldErrorEntries({ error: { message: "Fallo." } })).toEqual(
      [],
    );
    expect(parseFieldErrorEntries(undefined)).toEqual([]);
    expect(parseFieldErrorEntries("texto")).toEqual([]);
  });
});
