import axios, { type AxiosError } from "axios";
import api from "@/lib/api";
import type { ApiResponse } from "@/shared/types/api.types";
import type { InscripcionPayload } from "../schemas";

export async function createInscripcion(payload: InscripcionPayload) {
  try {
    const { data } = await api.post<ApiResponse<unknown>>(
      "/api/inscripcion",
      payload,
    );
    return data;
  } catch (err) {
    // Axios rejects non-2xx responses as AxiosError.
    // When the server returns a structured ApiResponse (e.g. 409 duplicate),
    // extract it and return it as a normal response so the caller can
    // handle success=false without an unhandled rejection.
    if (axios.isAxiosError(err) && err.response?.data) {
      const data = err.response.data as ApiResponse<unknown>;
      if (typeof data.success === "boolean" && data.error !== undefined) {
        return data;
      }
    }
    throw err;
  }
}
