import type { NextRequest } from "next/server";
import { z } from "zod";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { ValidationError } from "@/core/errors";
import { registerUser } from "@/core/use-cases/auth";
import { setAuthCookie } from "@/infra/auth/cookies";
import {
  DrizzleSesionRepository,
  DrizzleUserRepository,
} from "@/infra/drizzle/repositories";

const RegisterRequestSchema = z
  .object({
    email: z.string().email("Email inválido"),
    password: z.string().min(8, "Mínimo 8 caracteres"),
    /** Required — DB is NOT NULL. Frontend always sends via defaultValues "DNI". No .default() (zodResolver type mismatch). */
    tipoDocumento: z.enum(["DNI", "CE", "PAS"]),
    /** Required when tipoDocumento is set — validated in superRefine */
    numeroDocumento: z.string(),
    nombres: z.string().min(1, "Requerido").max(120),
    apellidos: z.string().min(1, "Requerido").max(120),
    genero: z.enum(["V", "M"]).optional().nullable(),
    telefono: z.string().optional().nullable(),
    whatsapp: z.string().optional().nullable(),
    emergencyName: z.string().max(120).optional().nullable(),
    emergencyPhone: z.string().optional().nullable(),
  })
  .superRefine((data, ctx) => {
    const { tipoDocumento, numeroDocumento } = data;

    if (!numeroDocumento || numeroDocumento.trim() === "") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "El número de documento es requerido",
        path: ["numeroDocumento"],
      });
      return;
    }

    if (tipoDocumento === "DNI" && !/^\d{8}$/.test(numeroDocumento)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "El DNI debe tener 8 dígitos",
        path: ["numeroDocumento"],
      });
    } else if (tipoDocumento === "CE" && !/^\d{9}$/.test(numeroDocumento)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "El CE debe tener 9 dígitos",
        path: ["numeroDocumento"],
      });
    } else if (tipoDocumento === "PAS" && numeroDocumento.trim().length < 4) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "El PAS debe tener al menos 4 caracteres alfanuméricos",
        path: ["numeroDocumento"],
      });
    }
  });

export async function POST(request: NextRequest) {
  try {
    const raw = await request.json();
    const parsed = RegisterRequestSchema.safeParse(raw);
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
    const result = await registerUser(
      { userRepository, sesionRepository },
      parsed.data,
    );

    await setAuthCookie(result._accessToken);
    const { _accessToken, ...payload } = result;

    return jsonSuccess(payload.user, 201);
  } catch (error) {
    return jsonFromUnknownError(error, "POST /api/auth/register");
  }
}

export const dynamic = "force-dynamic";
