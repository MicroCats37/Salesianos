import { afterEach, describe, expect, it } from "vitest";
import { backendInternalUrl, backendPublicUrl } from "./backend-url";

/**
 * Focused tests of the two backend URLs.
 *
 * The browser and the Next.js server reach the backend by DIFFERENT urls: the
 * browser uses the relative path the nginx proxy rewrites, the server uses the
 * internal name of the backend. Mixing them is what broke the administration
 * area and the token refresh in production.
 */

const ORIGINAL = { ...process.env };

afterEach(() => {
  process.env = { ...ORIGINAL };
});

describe("backendPublicUrl", () => {
  it("usa la ruta relativa del proxy cuando no hay configuración", () => {
    delete process.env.NEXT_PUBLIC_API_URL;

    expect(backendPublicUrl()).toBe("/backend");
  });

  it("respeta la URL pública configurada", () => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api";

    expect(backendPublicUrl()).toBe("http://localhost:8000/api");
  });

  it("elimina la barra final", () => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api/";

    expect(backendPublicUrl()).toBe("http://localhost:8000/api");
  });
});

describe("backendInternalUrl", () => {
  it("usa BACKEND_INTERNAL_URL cuando está configurada", () => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000/api";
    process.env.NEXT_PUBLIC_API_URL = "/backend";

    expect(backendInternalUrl()).toBe("http://backend:8000/api");
  });

  it("nunca resuelve la ruta relativa del navegador", () => {
    delete process.env.BACKEND_INTERNAL_URL;
    process.env.NEXT_PUBLIC_API_URL = "/backend";

    const url = backendInternalUrl();

    expect(url.startsWith("/")).toBe(false);
    expect(url).toBe("http://backend:8000/api");
  });

  it("reutiliza la URL pública cuando es absoluta", () => {
    delete process.env.BACKEND_INTERNAL_URL;
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api";

    expect(backendInternalUrl()).toBe("http://localhost:8000/api");
  });

  it("cae en el backend local cuando no hay nada configurado", () => {
    delete process.env.BACKEND_INTERNAL_URL;
    delete process.env.NEXT_PUBLIC_API_URL;

    expect(backendInternalUrl()).toBe("http://localhost:8000/api");
  });

  it("elimina la barra final de la URL configurada", () => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000/api/";

    expect(backendInternalUrl()).toBe("http://backend:8000/api");
  });
});
