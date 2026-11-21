"use client";

import { useApiCreate, useApiUpdate } from "@/hooks";
import {
  type ControlPartidoData,
  type GrupoTorneoUpdateData,
  type PartidoTorneoFormData,
  torneoAdminEnvelope,
} from "../schemas/torneo-admin.schema";
import { claveEncuentrosPublicos } from "../utils/encuentro-publico.claves.utils";

/** Tournament writes own their transport and invalidate the shared live snapshot. */
export function useGuardarGrupoTorneo() {
  return useApiUpdate({
    getUrl: ({ id }) => `/torneo-admin/groups/${id}`,
    schema: torneoAdminEnvelope,
    invalidateKeys: [claveEncuentrosPublicos],
  });
}

export function useGuardarLlaveTorneo() {
  return useApiUpdate({
    getUrl: ({ id }) => `/torneo-admin/knockout/${id}`,
    schema: torneoAdminEnvelope,
    invalidateKeys: [claveEncuentrosPublicos],
  });
}

export function useControlarPartidoTorneo() {
  return useApiCreate({
    getUrl: ({ id }) => `/torneo-admin/matches/${id}/control`,
    schema: torneoAdminEnvelope,
    invalidateKeys: [claveEncuentrosPublicos],
  });
}

export type {
  ControlPartidoData,
  GrupoTorneoUpdateData,
  PartidoTorneoFormData,
};
