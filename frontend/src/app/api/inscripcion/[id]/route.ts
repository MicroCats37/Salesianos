import type { NextRequest } from "next/server";
import { z } from "zod";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import {
  NotFoundError,
  PermissionDeniedError,
  ValidationError,
} from "@/core/errors";
import { updateInscripcion } from "@/core/use-cases/inscripcion";
import {
  DrizzleCategoriaRepository,
  DrizzleDisciplinaRepository,
  DrizzleInscripcionRepository,
  DrizzlePromocionRepository,
} from "@/infra/drizzle/repositories";
import { getSession } from "@/lib/auth/get-session";

const DeportistaSchema = z.object({
  tipoDocumento: z.enum(["DNI", "CE", "PAS"]),
  numeroDocumento: z.string().min(1),
  nombres: z.string().min(1).max(120),
  apellidos: z.string().min(1).max(120),
  genero: z.enum(["V", "M"]).optional().nullable(),
  telefono: z.string().optional().nullable(),
  rolDisciplina: z.enum(["Capitán", "Delegado", "Jugador"]).default("Jugador"),
  acreditacion: z
    .enum(["Verificación en padrón", "Excepción aprobada"])
    .default("Verificación en padrón"),
  disciplinaIds: z.array(z.string().uuid()).min(1),
  shirtSize: z.enum(["XS", "S", "M", "L", "XL", "XXL"]).optional().nullable(),
});

const UpdateInscripcionSchema = z.object({
  teamName: z
    .string()
    .min(1, "El nombre del equipo es requerido")
    .max(120)
    .optional(),
  deportistas: z
    .array(DeportistaSchema)
    .min(1, "Debe haber al menos un deportista")
    .optional(),
  equiposConfig: z
    .array(
      z.object({
        disciplinaId: z.string().uuid(),
        categoriaId: z.string().uuid(),
      }),
    )
    .optional(),
});

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const session = await getSession();
    if (!session || session.rol !== "responsable") {
      throw new PermissionDeniedError(
        "No autorizado para actualizar inscripciones",
      );
    }

    const { id } = await params;

    // Verify the inscription belongs to this user
    const inscripcionRepository = new DrizzleInscripcionRepository();
    const existing = await inscripcionRepository.findById(id);
    if (!existing) {
      throw new NotFoundError(`Inscripción no encontrada: ${id}`);
    }
    if (existing.inscripcion.userId !== session.sub) {
      throw new PermissionDeniedError(
        "No autorizado para editar esta inscripción",
      );
    }

    const raw = await request.json();
    const parsed = UpdateInscripcionSchema.safeParse(raw);
    if (!parsed.success) {
      const fieldErrors: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(
        parsed.error.flatten().fieldErrors,
      )) {
        if (value) fieldErrors[key] = value;
      }
      throw new ValidationError("Datos inválidos", fieldErrors);
    }

    const result = await updateInscripcion({ inscripcionRepository }, id, {
      teamName: parsed.data.teamName,
      deportistas: parsed.data.deportistas,
      equiposConfig: parsed.data.equiposConfig,
    });

    return jsonSuccess(result, 200);
  } catch (error) {
    return jsonFromUnknownError(error, "PATCH /api/inscripcion/[id]");
  }
}

export const dynamic = "force-dynamic";
