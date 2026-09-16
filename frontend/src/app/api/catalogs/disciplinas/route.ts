import type { NextRequest } from "next/server";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { DrizzleDisciplinaRepository } from "@/infra/drizzle/repositories";

export async function GET(_request: NextRequest) {
  try {
    const repo = new DrizzleDisciplinaRepository();
    const list = await repo.listAll();
    return jsonSuccess(list, 200);
  } catch (error) {
    return jsonFromUnknownError(error, "GET /api/catalogs/disciplinas");
  }
}

export const dynamic = "force-dynamic";
