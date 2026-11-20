import type { AxiosError } from "axios";

/**
 * The adaptation of the ERRORS of the server for the forms of the feature.
 *
 * The wire speaks `snake_case` (`numero_documento`) and the forms speak
 * `camelCase` (`numeroDocumento`). The `field_errors` of a 422 travel to the
 * control they belong to through `setError`, so the names must match the
 * fields of the form.
 *
 * The adaptation happens HERE, in the layer of the feature, and NOT in the
 * component: a component never parses an API error on its own
 * (`contract/smart.md` §5.4).
 */

interface ErrorDeCampo {
  field: string;
  code?: string;
  message: string;
}

interface CuerpoDeError {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown> | null;
    field_errors?: ErrorDeCampo[] | null;
  };
  [clave: string]: unknown;
}

/**
 * The name of a control of the form, from the name of the field of the wire.
 *
 * `numero_documento` becomes `numeroDocumento`. A name that is not in
 * `snake_case` travels untouched: the server may address a field this
 * feature does not know, and dropping it would hide a real problem.
 */
export function aCampoDeFormulario(campo: string): string {
  return campo.replace(/_([a-z0-9])/g, (_, letra: string) =>
    letra.toUpperCase(),
  );
}

/**
 * Rewrites the field names of a 422 so that they reach the control they
 * belong to.
 *
 * The error keeps its status, its code and its message: only the NAME of the
 * field changes, and only when the answer carries field errors. Any other
 * error travels untouched.
 */
export function adaptarErrorDeCampos(error: unknown): unknown {
  const axiosError = error as AxiosError<CuerpoDeError>;

  const cuerpo = axiosError?.response?.data;
  const errores = cuerpo?.error?.field_errors;

  if (!Array.isArray(errores) || errores.length === 0) return error;

  const adaptados = errores.map((campo) => ({
    ...campo,
    field: aCampoDeFormulario(campo.field),
  }));

  return {
    ...axiosError,
    response: {
      ...axiosError.response,
      data: {
        ...cuerpo,
        error: {
          ...cuerpo?.error,
          field_errors: adaptados,
        },
      },
    },
  };
}
