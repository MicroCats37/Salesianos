import type { NextRequest } from "next/server";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { DrizzleBaseRepository } from "@/infra/drizzle/repositories";

export async function GET(_request: NextRequest) {
  try {
    const repo = new DrizzleBaseRepository();
    const active = await repo.findActive();
    return jsonSuccess(active, 200);
  } catch (error) {
    return jsonFromUnknownError(error, "GET /api/catalogs/bases");
  }
}

export const dynamic = "force-dynamic";
