import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

export const partidoTorneoFormSchema = z.object({
  id: z.string().min(1),
  home_id: z.string().nullable(),
  away_id: z.string().nullable(),
  home_score: z.number().int().min(0).nullable(),
  away_score: z.number().int().min(0).nullable(),
  scheduled_at: z.string().nullable(),
  court: z.string().trim().max(30).nullable(),
  duration_minutes: z.number().int().min(1).max(240),
  home_penalties: z.number().int().min(0).nullable(),
  away_penalties: z.number().int().min(0).nullable(),
});

export const grupoTorneoUpdateSchema = z.object({
  revision: z.number().int().min(0),
  matches: z.array(partidoTorneoFormSchema).min(1),
});

export const controlPartidoSchema = z.object({
  action: z.enum([
    "start",
    "halftime",
    "resume",
    "extra",
    "penalties",
    "reopen",
    "finish",
  ]),
  winner_id: z.string().nullable().optional(),
  decision: z.enum(["manual", "penalties"]).nullable().optional(),
});

const torneoAdminResultSchema = z.object({
  saved: z.boolean(),
  revision: z.number().int().optional(),
  status: z.string().optional(),
});

export const torneoAdminEnvelope = apiResponseSchema(torneoAdminResultSchema);

export type PartidoTorneoFormData = z.infer<typeof partidoTorneoFormSchema>;
export type GrupoTorneoUpdateData = z.infer<typeof grupoTorneoUpdateSchema>;
export type ControlPartidoData = z.infer<typeof controlPartidoSchema>;
