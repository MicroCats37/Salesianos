import type { PaqueteListContract } from "@/features/inscripciones/schemas/paquete.schema";
import type { ApiResponse } from "@/types/api.types";

export type Paquete = PaqueteListContract;

type PaqueteApi = Omit<
  Paquete,
  "precio_preventa" | "precio_regular" | "precio_promocional"
> & {
  precio_preventa: number | string | null;
  precio_regular: number | string | null;
  precio_promocional: number | string | null;
};

function normalizarPrecio(precio: number | string | null): number | null {
  if (precio === null) return null;

  const valor = Number(precio);
  return Number.isFinite(valor) ? valor : null;
}

const configuredBaseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

const BASE_URL =
  typeof window === "undefined" && configuredBaseUrl.startsWith("/")
    ? "http://backend:8000/api"
    : configuredBaseUrl;

export async function fetchPaquetes(): Promise<Paquete[] | null> {
  try {
    const res = await fetch(`${BASE_URL}/catalogo/paquetes/`, {
      cache: "no-store",
    });

    if (!res.ok) return null;

    const json = (await res.json()) as ApiResponse<PaqueteApi[]>;

    if (!json.success || json.data === null) return null;

    return json.data.map((paquete) => ({
      ...paquete,
      precio_preventa: normalizarPrecio(paquete.precio_preventa),
      precio_regular: normalizarPrecio(paquete.precio_regular),
      precio_promocional: normalizarPrecio(paquete.precio_promocional),
    }));
  } catch {
    return null;
  }
}
