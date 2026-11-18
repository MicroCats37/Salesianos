/**
 * Minimal reader of the `exp` claim of a JWT.
 *
 * The value is NOT a cryptographic authority: it is read from a token the
 * backend just issued and it is used ONLY to tell the client when to refresh
 * proactively. The real authority is always the signature, and it is the
 * backend who validates it on every request.
 *
 * The reader never throws: a malformed token yields `null` and the caller
 * applies its own fallback.
 */

interface ClaimsJwt {
  exp?: unknown;
}

function decodificarBase64Url(valor: string): string | null {
  try {
    // `atob` works in the browser and in Node 18+; the base64url alphabet is
    // translated to the standard one before decoding.
    const normalizado = valor.replace(/-/g, "+").replace(/_/g, "/");
    const relleno = normalizado.padEnd(
      normalizado.length + ((4 - (normalizado.length % 4)) % 4),
      "=",
    );
    const binario = atob(relleno);

    // Rebuild the UTF-8 string: `atob` yields latin1 bytes.
    const bytes = Uint8Array.from(binario, (caracter) =>
      caracter.charCodeAt(0),
    );

    return new TextDecoder().decode(bytes);
  } catch {
    return null;
  }
}

/**
 * The expiry of an access token, read from its `exp` claim.
 *
 * Returns `null` when the token is malformed or carries no usable `exp`.
 */
export function expiracionDeToken(
  accessToken: string | null | undefined,
): Date | null {
  if (!accessToken) {
    return null;
  }

  const segmentos = accessToken.split(".");
  if (segmentos.length < 2) {
    return null;
  }

  const payload = decodificarBase64Url(segmentos[1]);
  if (!payload) {
    return null;
  }

  let claims: ClaimsJwt;
  try {
    claims = JSON.parse(payload) as ClaimsJwt;
  } catch {
    return null;
  }

  const exp = claims.exp;
  if (typeof exp !== "number" || !Number.isFinite(exp)) {
    return null;
  }

  const expiracion = new Date(exp * 1000);
  return Number.isNaN(expiracion.getTime()) ? null : expiracion;
}
