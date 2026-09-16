import type { NextRequest } from "next/server";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { getCurrentUser } from "@/core/use-cases/auth";
import {
  DrizzleSesionRepository,
  DrizzleUserRepository,
} from "@/infra/drizzle/repositories";

export async function GET(_request: NextRequest) {
  try {
    const userRepository = new DrizzleUserRepository();
    const sesionRepository = new DrizzleSesionRepository();
    const result = await getCurrentUser({ userRepository, sesionRepository });

    return jsonSuccess(result.user, 200);
  } catch (error) {
    return jsonFromUnknownError(error, "GET /api/auth/me");
  }
}

export const dynamic = "force-dynamic";
