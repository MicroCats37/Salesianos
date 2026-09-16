import type { NextRequest } from "next/server";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { clearAuthCookie, getAuthCookie } from "@/infra/auth/cookies";
import { hashToken } from "@/infra/auth/jwt";
import { DrizzleSesionRepository } from "@/infra/drizzle/repositories";

export async function POST(_request: NextRequest) {
  try {
    const token = await getAuthCookie();
    if (token) {
      try {
        const tokenHash = await hashToken(token);
        const sesionRepo = new DrizzleSesionRepository();
        const sesion = await sesionRepo.findByTokenHash(tokenHash);
        if (sesion) {
          await sesionRepo.revoke(sesion.id);
        }
      } catch (dbError) {
        console.error("[POST /api/auth/logout] DB revoke failed:", dbError);
      }
    }

    await clearAuthCookie();
    return jsonSuccess(null, 200);
  } catch (error) {
    return jsonFromUnknownError(error, "POST /api/auth/logout");
  }
}

export const dynamic = "force-dynamic";
