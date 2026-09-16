import type { NextRequest } from "next/server";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { PermissionDeniedError } from "@/core/errors";
import { getMyInscripcion } from "@/core/use-cases/inscripcion";
import { DrizzleInscripcionRepository } from "@/infra/drizzle/repositories";
import { getSession } from "@/lib/auth/get-session";

export async function GET(_request: NextRequest) {
  try {
    const session = await getSession();
    if (!session || session.rol !== "responsable") {
      throw new PermissionDeniedError("No autorizado");
    }

    const inscripcionRepository = new DrizzleInscripcionRepository();
    const result = await getMyInscripcion(
      { inscripcionRepository },
      session.sub,
    );
    return jsonSuccess(result, 200);
  } catch (error) {
    return jsonFromUnknownError(error, "GET /api/inscripcion/mine");
  }
}

export const dynamic = "force-dynamic";
