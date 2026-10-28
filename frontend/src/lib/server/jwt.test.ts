import { describe, expect, it } from "vitest";
import { expiracionDeToken } from "./jwt";

/**
 * Focused tests of the reader of the `exp` claim.
 *
 * The value is a UX hint for the proactive refresh of the client, never an
 * authority: the backend validates the signature of every token.
 */

function construirToken(payload: Record<string, unknown>): string {
  const codificar = (valor: string) =>
    Buffer.from(valor, "utf8")
      .toString("base64")
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

  return `${codificar(JSON.stringify({ alg: "HS256", typ: "JWT" }))}.${codificar(
    JSON.stringify(payload),
  )}.firma`;
}

describe("expiracionDeToken", () => {
  it("devuelve la expiración real del token", () => {
    const exp = 1_700_000_000;
    const expiracion = expiracionDeToken(construirToken({ exp }));

    expect(expiracion).not.toBeNull();
    expect(expiracion?.toISOString()).toBe(new Date(exp * 1000).toISOString());
  });

  it("devuelve null cuando el token no trae `exp`", () => {
    expect(expiracionDeToken(construirToken({ sub: "1" }))).toBeNull();
  });

  it("devuelve null cuando `exp` no es un número", () => {
    expect(expiracionDeToken(construirToken({ exp: "mañana" }))).toBeNull();
  });

  it("devuelve null con un token malformado", () => {
    expect(expiracionDeToken("no-es-un-jwt")).toBeNull();
  });

  it("devuelve null sin token", () => {
    expect(expiracionDeToken(null)).toBeNull();
    expect(expiracionDeToken(undefined)).toBeNull();
    expect(expiracionDeToken("")).toBeNull();
  });
});
