import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

const teamSchema = z.object({
  id: z.string(),
  name: z.string(),
  group_id: z.string(),
});

const standingSchema = z.object({
  id: z.string(),
  name: z.string(),
  pj: z.number().int(),
  g: z.number().int(),
  e: z.number().int(),
  p: z.number().int(),
  gf: z.number().int(),
  gc: z.number().int(),
  dg: z.number().int(),
  pts: z.number().int(),
});

export const partidoTorneoSchema = z.object({
  id: z.string(),
  group_id: z.string().nullable(),
  stage: z.enum([
    "group",
    "round16",
    "quarter",
    "semi",
    "cross",
    "final",
    "third_place",
  ]),
  category: z.string(),
  title: z.string(),
  position: z.number().int(),
  home_id: z.string().nullable(),
  away_id: z.string().nullable(),
  home_name: z.string(),
  away_name: z.string(),
  scheduled_at: z.string().nullable(),
  court: z.string().nullable(),
  duration_minutes: z.number().int(),
  status: z.enum([
    "scheduled",
    "live",
    "halftime",
    "extra",
    "penalties",
    "final",
  ]),
  home_score: z.number().int().nullable(),
  away_score: z.number().int().nullable(),
  home_penalties: z.number().int().nullable(),
  away_penalties: z.number().int().nullable(),
  winner_id: z.string().nullable(),
  decision: z.string().nullable(),
  elapsed_seconds: z.number().int(),
  running: z.boolean(),
  segment: z.string(),
  live_points: z.object({ home: z.number().int(), away: z.number().int() }),
});

const grupoTorneoSchema = z.object({
  id: z.string(),
  label: z.string(),
  revision: z.number().int(),
  teams: z.array(teamSchema),
  table: z.array(standingSchema),
  matches: z.array(partidoTorneoSchema),
});

const competenciaTorneoSchema = z.object({
  id: z.string(),
  name: z.string(),
  discipline: z.string(),
  category: z.string(),
  date: z.string(),
});

export const torneoPublicoSchema = z.object({
  ready: z.boolean(),
  competition_id: z.string().optional(),
  competition_name: z.string().optional(),
  competitions: z.array(competenciaTorneoSchema).default([]),
  tournament: z.string().optional(),
  discipline: z.string().optional(),
  category: z.string().optional(),
  date: z.string().optional(),
  server_time: z.string(),
  groups: z.array(grupoTorneoSchema),
  knockout: z.array(partidoTorneoSchema),
  teams: z.array(teamSchema).optional(),
});

export const torneoPublicoEnvelope = apiResponseSchema(torneoPublicoSchema);

export type PartidoTorneo = z.infer<typeof partidoTorneoSchema>;
export type GrupoTorneo = z.infer<typeof grupoTorneoSchema>;
export type TorneoPublico = z.infer<typeof torneoPublicoSchema>;
