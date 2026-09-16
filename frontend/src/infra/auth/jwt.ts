import { jwtVerify, SignJWT } from "jose";

export interface JwtPayload {
  sub: string;
  email: string;
  rol: "responsable" | "admin_comite" | "admin_finanzas";
}

const ALG = "HS256";

function getSecret(): Uint8Array {
  const secret = process.env.JWT_SECRET;
  if (!secret || secret.length < 32) {
    throw new Error("JWT_SECRET env var is required and must be >= 32 chars");
  }
  return new TextEncoder().encode(secret);
}

export async function signAccessToken(payload: JwtPayload): Promise<string> {
  const ttlSeconds = Number(
    process.env.JWT_ACCESS_TOKEN_TTL_SECONDS ?? 60 * 60 * 24 * 7,
  );
  return await new SignJWT({ ...payload })
    .setProtectedHeader({ alg: ALG })
    .setIssuedAt()
    .setExpirationTime(`${ttlSeconds}s`)
    .setSubject(payload.sub)
    .sign(getSecret());
}

export async function verifyAccessToken(
  token: string,
): Promise<JwtPayload | null> {
  try {
    const { payload } = await jwtVerify(token, getSecret(), {
      algorithms: [ALG],
    });
    if (typeof payload.sub !== "string" || typeof payload.email !== "string") {
      return null;
    }
    return {
      sub: payload.sub,
      email: payload.email,
      rol: payload.rol as JwtPayload["rol"],
    };
  } catch {
    return null;
  }
}

export async function hashToken(token: string): Promise<string> {
  const data = new TextEncoder().encode(token);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}
