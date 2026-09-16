"use server";
import {
  DrizzleBaseRepository,
  DrizzleDisciplinaRepository,
  DrizzlePromocionRepository,
} from "@/infra/drizzle/repositories";

export async function getDisciplinasAction() {
  const repo = new DrizzleDisciplinaRepository();
  const list = await repo.listAll();
  return { success: true, data: list };
}

export async function getPromocionesAction() {
  const repo = new DrizzlePromocionRepository();
  const list = await repo.listAll(true);
  return { success: true, data: list };
}

export async function getBasesAction() {
  const repo = new DrizzleBaseRepository();
  const active = await repo.findActive();
  return { success: true, data: active };
}
