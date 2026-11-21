import { z } from "zod";

/** The invalidation event emitted by the public encounter WebSocket. */
export const encuentroActualizadoEventSchema = z.object({
  type: z.literal("encuentro.actualizado"),
  schema_version: z.literal(1),
  encuentro_id: z.string().min(1),
  occurred_at: z.string().datetime(),
});
