import { apiSend } from "@/lib/api";
import type { Patrocinador } from "../schemas/patrocinador.schema";
import {
  listaPatrocinadoresEnvelope,
  patrocinadorEnvelope,
} from "../schemas/patrocinador.schema";

const BASE = "/patrocinadores";
const ADMIN_BASE = "/administracion/patrocinadores";

/** The route of the public catalogue of sponsors. */
export function rutaPatrocinadores(): string {
  return BASE;
}

/** The route of the administration of the sponsors. */
export function rutaPatrocinadoresAdmin(): string {
  return ADMIN_BASE;
}

/** The route of ONE sponsor of the administration. */
export function rutaPatrocinadorAdmin(id: string): string {
  return `${ADMIN_BASE}/${encodeURIComponent(id)}`;
}

/** The route of the logo of ONE sponsor. */
export function rutaLogoPatrocinador(id: string): string {
  return `${ADMIN_BASE}/${encodeURIComponent(id)}/logo`;
}

/** The route of ONE piece of the gallery of ONE sponsor. */
export function rutaImagenPatrocinador(id: string, imagenId: string): string {
  return `${ADMIN_BASE}/${encodeURIComponent(id)}/imagenes/${encodeURIComponent(imagenId)}`;
}

/** The route of the order of the gallery of the edition. */
export function rutaOrdenPatrocinadores(): string {
  return `${ADMIN_BASE}/orden`;
}

export async function listarPatrocinadores(): Promise<Patrocinador[]> {
  const { data } = await apiSend<unknown>("get", rutaPatrocinadores());
  return listaPatrocinadoresEnvelope.parse(data).data ?? [];
}

export async function listarPatrocinadoresAdmin(): Promise<Patrocinador[]> {
  const { data } = await apiSend<unknown>("get", rutaPatrocinadoresAdmin());
  return listaPatrocinadoresEnvelope.parse(data).data ?? [];
}

export async function crearPatrocinador(
  payload: FormData,
): Promise<Patrocinador> {
  const { data } = await apiSend<unknown>(
    "post",
    rutaPatrocinadoresAdmin(),
    payload,
  );
  return patrocinadorEnvelope.parse(data).data!;
}

export async function actualizarPatrocinador(
  id: string,
  payload: object,
): Promise<Patrocinador> {
  const { data } = await apiSend<unknown>(
    "patch",
    rutaPatrocinadorAdmin(id),
    payload,
  );
  return patrocinadorEnvelope.parse(data).data!;
}

export async function eliminarPatrocinador(id: string): Promise<void> {
  await apiSend<unknown>("delete", rutaPatrocinadorAdmin(id));
}

export async function reemplazarLogoPatrocinador(
  id: string,
  payload: FormData,
): Promise<Patrocinador> {
  const { data } = await apiSend<unknown>(
    "patch",
    rutaLogoPatrocinador(id),
    payload,
  );
  return patrocinadorEnvelope.parse(data).data!;
}

export async function reemplazarImagenPatrocinador(
  id: string,
  imagenId: string,
  payload: FormData,
): Promise<Patrocinador> {
  const { data } = await apiSend<unknown>(
    "patch",
    rutaImagenPatrocinador(id, imagenId),
    payload,
  );
  return patrocinadorEnvelope.parse(data).data!;
}

export async function eliminarImagenPatrocinador(
  id: string,
  imagenId: string,
): Promise<Patrocinador> {
  const { data } = await apiSend<unknown>(
    "delete",
    rutaImagenPatrocinador(id, imagenId),
  );
  return patrocinadorEnvelope.parse(data).data!;
}

export async function reordenarPatrocinadores(
  patrocinador_ids: string[],
): Promise<Patrocinador[]> {
  const { data } = await apiSend<unknown>("patch", rutaOrdenPatrocinadores(), {
    patrocinador_ids,
  });
  return listaPatrocinadoresEnvelope.parse(data).data ?? [];
}
