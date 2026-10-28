import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";
import { AUTH_COOKIES } from "./lib/auth";
import proxy, { config } from "./proxy";

/**
 * Focused tests of the authentication gate of `proxy.ts`.
 *
 * The file is the AUTHENTICATION gate of the UX and nothing more: it decides
 * whether a CREDENTIAL exists, never whether the caller holds a role. These
 * tests freeze that behaviour so a future change cannot quietly turn the
 * proxy into a second (and forgeable) authority.
 *
 * There is NO `nextUrl` behaviour here on purpose: the round-trip of the
 * deep links is outside the scope of this change.
 */

const ORIGEN = "https://salesianosfest.test";

function construirRequest(ruta: string, token?: string): NextRequest {
  const headers = new Headers();

  if (token) {
    headers.set("cookie", `${AUTH_COOKIES.ACCESS_TOKEN}=${token}`);
  }

  return new NextRequest(new URL(ruta, ORIGEN), { headers });
}

function destino(respuesta: Response): string | null {
  return respuesta.headers.get("location");
}

async function leerProxy(): Promise<string> {
  return readFile(
    fileURLToPath(new URL("./proxy.ts", import.meta.url)),
    "utf8",
  );
}

describe("proxy — rutas públicas", () => {
  it("deja pasar la portada sin credencial", () => {
    const respuesta = proxy(construirRequest("/"));

    expect(respuesta.status).toBe(200);
    expect(destino(respuesta)).toBeNull();
  });

  it("deja pasar /login sin credencial", () => {
    const respuesta = proxy(construirRequest("/login"));

    expect(respuesta.status).toBe(200);
    expect(destino(respuesta)).toBeNull();
  });
});

describe("proxy — assets", () => {
  it("deja pasar las rutas con extensión (imágenes, css, fuentes)", () => {
    const respuesta = proxy(construirRequest("/images/brand.png"));

    expect(respuesta.status).toBe(200);
    expect(destino(respuesta)).toBeNull();
  });
});

describe("proxy — /administracion/**", () => {
  it("rechaza al visitante anónimo y lo devuelve a la portada", () => {
    const respuesta = proxy(construirRequest("/administracion"));

    expect(respuesta.status).toBe(307);
    expect(destino(respuesta)).toBe(`${ORIGEN}/`);
  });

  it("rechaza al visitante anónimo en una sección profunda", () => {
    const respuesta = proxy(construirRequest("/administracion/usuarios"));

    expect(respuesta.status).toBe(307);
    expect(destino(respuesta)).toBe(`${ORIGEN}/`);
  });

  it("deja pasar al visitante autenticado", () => {
    const respuesta = proxy(
      construirRequest("/administracion", "token-de-prueba"),
    );

    expect(respuesta.status).toBe(200);
    expect(destino(respuesta)).toBeNull();
  });

  it("no excluye la sección administrativa del matcher", () => {
    const LOOKAHEAD = /\(\?!\s*([^)]*)\)/;
    const excluidos = (LOOKAHEAD.exec(config.matcher[0])?.[1] ?? "")
      .split("|")
      .map((valor) => valor.trim());

    expect(excluidos).not.toContain("administracion");
    expect(excluidos).not.toContain("admin");
  });
});

describe("proxy — /login con credencial", () => {
  it("deja pasar al visitante autenticado (ruta pública)", () => {
    const respuesta = proxy(construirRequest("/login", "token-de-prueba"));

    // `/login` está en `PUBLIC_PATHS`, así que la comprobación de las rutas
    // públicas ocurre ANTES que la del token: la rama que redirigía a
    // `/dashboard` es inalcanzable. Este test congela el comportamiento REAL
    // en curso, no el que se supone en el código.
    expect(respuesta.status).toBe(200);
    expect(destino(respuesta)).toBeNull();
  });
});

describe("proxy — alcance", () => {
  it("no contiene lógica nextUrl", async () => {
    const fuente = await leerProxy();

    // `request.nextUrl` es la API de Next.js (la URL de la petición); el
    // parámetro `nextUrl` de la aplicación es otra cosa y no debe existir.
    const sinApiDeNext = fuente.replaceAll("request.nextUrl", "");

    expect(sinApiDeNext).not.toContain("nextUrl");
  });

  it("no decide roles ni permisos", async () => {
    const fuente = await leerProxy();

    expect(fuente).not.toContain("is_staff");
    expect(fuente).not.toContain("is_superuser");
    expect(fuente).not.toContain("es_admin");
    expect(fuente).not.toContain("capacidades");
  });
});
