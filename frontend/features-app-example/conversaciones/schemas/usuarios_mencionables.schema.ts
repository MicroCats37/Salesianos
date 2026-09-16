// features/conversaciones/schemas/usuarios_mencionables.schema.ts
// Schema for usuarios mencionables endpoint — non-paginated list response.

import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

// ── Schema ─────────────────────────────────────────────────────────────────────

/**
 * Usuario mencionable in a chat context.
 *
 * Context fields (area_id, area_nombre, rol, periodo_id, numero_ciclo,
 * tipo_participacion) are present when the query uses solicitud_id and
 * the backend returns participants from open periods.
 */
export const UsuarioMencionableSchema = z.object({
  id: z.string().uuid(),
  username: z.string(),
  nombres: z.string().nullable().optional(),
  apellidos: z.string().nullable().optional(),
  dni: z.string().nullable().optional(),
  // ── Contexto de participación (solo con solicitud_id) ──
  area_id: z.string().uuid().nullable().optional(),
  area_nombre: z.string().nullable().optional(),
  rol: z.string().nullable().optional(),
  periodo_id: z.string().uuid().nullable().optional(),
  numero_ciclo: z.number().int().nullable().optional(),
  tipo_participacion: z.string().nullable().optional(),
});

export type UsuarioMencionable = z.infer<typeof UsuarioMencionableSchema>;

// ── API Response ────────────────────────────────────────────────────────────────

/**
 * Non-paginated list response — ApiResponse[list[UsuarioMencionable]].
 */
export const UsuariosMencionablesResponseSchema = apiResponseSchema(
  z.array(UsuarioMencionableSchema),
);

export type UsuariosMencionablesResponse = z.infer<
  typeof UsuariosMencionablesResponseSchema
>;
