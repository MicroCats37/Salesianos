"use client";

import { useApiCreate, useApiDelete, useApiQuery, useApiUpdate } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import type { Patrocinador } from "../schemas/patrocinador.schema";
import {
  listaPatrocinadoresEnvelope,
  patrocinadorEnvelope,
} from "../schemas/patrocinador.schema";
import {
  rutaImagenPatrocinador,
  rutaLogoPatrocinador,
  rutaOrdenPatrocinadores,
  rutaPatrocinadores,
  rutaPatrocinadoresAdmin,
} from "../services/patrocinadores.service";

const keys = {
  all: ["patrocinadores"] as const,
  public: ["patrocinadores", "public"] as const,
  admin: ["patrocinadores", "admin"] as const,
};

/**
 * The payload of the alta.
 *
 * The FILES travel as they are: the generic hook builds the multipart of the
 * protocol (`file_<uuid>` + `token___name`) with `buildApiPayload`.
 */
export interface PayloadAltaPatrocinador {
  nombre: string;
  slug: string;
  descripcion: string;
  sitio_web: string;
  visible: boolean;
  logo: File | null;
  imagenes: { token: File; texto_alternativo: string }[];
}

/** The data of the record of a sponsor, without the media. */
export interface PayloadActualizacionPatrocinador {
  nombre: string;
  descripcion: string;
  sitio_web: string;
  visible: boolean;
}

export function usePatrocinadoresPublicos() {
  return useApiQuery({
    queryKey: keys.public,
    url: rutaPatrocinadores(),
    schema: datosDelEnvelope(listaPatrocinadoresEnvelope),
    queryOptions: {
      staleTime: STALE_TIME.catalogo,
      gcTime: gcTimeFor(STALE_TIME.catalogo),
    },
  });
}

export function usePatrocinadoresAdmin() {
  return useApiQuery({
    queryKey: keys.admin,
    url: rutaPatrocinadoresAdmin(),
    schema: datosDelEnvelope(listaPatrocinadoresEnvelope),
    queryOptions: {
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
    },
  });
}

export function usePatrocinadorMutaciones() {
  const crear = useApiCreate<Patrocinador, PayloadAltaPatrocinador>({
    url: rutaPatrocinadoresAdmin(),
    schema: datosDelEnvelope(patrocinadorEnvelope),
    invalidateKeys: [keys.all],
  });

  const actualizar = useApiUpdate<
    Patrocinador,
    PayloadActualizacionPatrocinador
  >({
    baseUrl: rutaPatrocinadoresAdmin(),
    method: "PATCH",
    schema: datosDelEnvelope(patrocinadorEnvelope),
    invalidateKeys: [keys.all],
  });

  const eliminar = useApiDelete<void>({
    baseUrl: rutaPatrocinadoresAdmin(),
    invalidateKeys: [keys.all],
  });

  const reordenar = useApiUpdate<
    Patrocinador[],
    { patrocinador_ids: string[] }
  >({
    url: rutaOrdenPatrocinadores(),
    method: "PATCH",
    schema: datosDelEnvelope(listaPatrocinadoresEnvelope),
    invalidateKeys: [keys.all],
  });

  const reemplazarLogo = useApiUpdate<Patrocinador, { archivo: File }>({
    getUrl: ({ id }) => rutaLogoPatrocinador(String(id)),
    method: "PATCH",
    schema: datosDelEnvelope(patrocinadorEnvelope),
    invalidateKeys: [keys.all],
  });

  const eliminarImagen = useApiDelete<void, { id: string; imagenId: string }>({
    getUrl: (variables) =>
      rutaImagenPatrocinador(variables.id, variables.imagenId),
    invalidateKeys: [keys.all],
  });

  return {
    crear,
    actualizar,
    eliminar,
    reordenar,
    reemplazarLogo,
    eliminarImagen,
  };
}

export type { Patrocinador };
