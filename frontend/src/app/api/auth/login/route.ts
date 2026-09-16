import type { NextRequest } from "next/server";
import { z } from "zod";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { ValidationError } from "@/core/errors";
import { loginUser } from "@/core/use-cases/auth";
import { setAuthCookie } from "@/infra/auth/cookies";
import {
  DrizzleSesionRepository,
  DrizzleUserRepository,
} from "@/infra/drizzle/repositories";

const LoginRequestSchema = z.object({
  identifier: z.string().min(1, "Email o DNI requerido"),
  password: z.string().min(1, "Contraseña requerida"),
});

export async function POST(request: NextRequest) {
  try {
    const raw = await request.json();
    const parsed = LoginRequestSchema.safeParse(raw);
    if (!parsed.success) {
      const fieldErrors: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(
        parsed.error.flatten().fieldErrors,
      )) {
        if (value) fieldErrors[key] = value;
      }
      throw new ValidationError("Datos inválidos", fieldErrors);
    }

    const userRepository = new DrizzleUserRepository();
    const sesionRepository = new DrizzleSesionRepository();
    const result = await loginUser(
      { userRepository, sesionRepository },
      parsed.data,
    );

    await setAuthCookie(result._accessToken);
    const { _accessToken, ...payload } = result;

    return jsonSuccess(payload.user, 200);
  } catch (error) {
    return jsonFromUnknownError(error, "POST /api/auth/login");
  }
}

export const dynamic = "force-dynamic";
