"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { updateInscripcionStatus } from "@/core/use-cases/inscripcion";
import { DrizzleInscripcionRepository } from "@/infra/drizzle/repositories";

const UpdateStatusSchema = z.object({
  inscripcionId: z.string().uuid(),
  status: z.enum(["en_revision", "validada", "observada", "rechazada"]),
  observacion: z.string().optional().nullable(),
});

export async function updateInscripcionStatusAction(
  input: z.infer<typeof UpdateStatusSchema>,
) {
  const parsed = UpdateStatusSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false as const,
      data: null,
      error: {
        code: "VALIDATION_ERROR",
        message: "Datos inválidos",
        details: parsed.error.flatten(),
      },
      meta: null,
    };
  }

  const inscripcionRepository = new DrizzleInscripcionRepository();
  const result = await updateInscripcionStatus(
    { inscripcionRepository },
    parsed.data,
  );

  revalidatePath("/admin/comite/inscripciones");
  revalidatePath(`/dashboard`);
  return { success: true as const, data: result, error: null, meta: null };
}
