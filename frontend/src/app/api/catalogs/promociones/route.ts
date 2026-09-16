import type { NextRequest } from "next/server";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { DrizzlePromocionRepository } from "@/infra/drizzle/repositories";

export async function GET(_request: NextRequest) {
  try {
    const repo = new DrizzlePromocionRepository();
    const list = await repo.listAll(true);
    return jsonSuccess(list, 200);
  } catch (error) {
    return jsonFromUnknownError(error, "GET /api/catalogs/promociones");
  }
}

export const dynamic = "force-dynamic";
