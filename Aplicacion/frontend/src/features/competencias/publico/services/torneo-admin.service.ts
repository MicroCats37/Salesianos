import type { PartidoTorneo } from "../schemas/torneo-publico.schema";

export interface PartidoDraft {
  id: string;
  home_id: string | null;
  away_id: string | null;
  home_score: number | null;
  away_score: number | null;
  scheduled_at: string | null;
  court: string | null;
  duration_minutes: number;
  home_penalties: number | null;
  away_penalties: number | null;
}

export const partidoDraft = (partido: PartidoTorneo): PartidoDraft => ({
  id: partido.id,
  home_id: partido.home_id,
  away_id: partido.away_id,
  home_score: partido.home_score,
  away_score: partido.away_score,
  scheduled_at: partido.scheduled_at,
  court: partido.court,
  duration_minutes: partido.duration_minutes,
  home_penalties: partido.home_penalties,
  away_penalties: partido.away_penalties,
});
