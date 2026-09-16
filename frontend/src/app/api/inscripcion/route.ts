import type { NextRequest } from "next/server";
import { z } from "zod";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { PermissionDeniedError, ValidationError } from "@/core/errors";
import { createInscripcion } from "@/core/use-cases/inscripcion";
import {
  DrizzleBaseRepository,
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

const CreateInscripcionSchema = z.object({
  userId: z.string().uuid(),
  promocionId: z.string().uuid(),
  fusionPromocionId: z.string().uuid().optional().nullable(),
  basesId: z.string().uuid(),
  paqueteMonto: z.number().positive(),
  teamName: z.string().min(1, "Ingresa el nombre del equipo").max(120),
  acceptedBases: z.boolean().refine((val) => val === true),
  fitnessDeclaration: z.boolean().refine((val) => val === true),
  imageConsent: z.boolean().refine((val) => val === true),
  deportistas: z.array(DeportistaSchema).min(1),
});

export async function POST(request: NextRequest) {
  try {
    const session = await getSession();
    if (!session || session.rol !== "responsable") {
      throw new PermissionDeniedError("No autorizado para crear inscripciones");
    }

    const raw = await request.json();
    const parsed = CreateInscripcionSchema.safeParse(raw);
    if (!parsed.success) {
      const fieldErrors: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(
        parsed.error.flatten().fieldErrors,
      )) {
        if (value) fieldErrors[key] = value;
      }
      throw new ValidationError("Datos inválidos", fieldErrors);
    }

    // Override userId from session to prevent spoofing
    parsed.data.userId = session.sub;

    const inscripcionRepository = new DrizzleInscripcionRepository();
    const promocionRepository = new DrizzlePromocionRepository();
    const disciplinaRepository = new DrizzleDisciplinaRepository();
    const categoriaRepository = new DrizzleCategoriaRepository();
    const baseRepository = new DrizzleBaseRepository();

    const result = await createInscripcion(
      {
        inscripcionRepository,
        promocionRepository,
        disciplinaRepository,
        categoriaRepository,
        baseRepository,
      },
      parsed.data,
    );

    return jsonSuccess(result, 201);
  } catch (error) {
    return jsonFromUnknownError(error, "POST /api/inscripcion");
  }
}

export const dynamic = "force-dynamic";
