import api from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";

export interface DocumentoConsultaData {
  tipo_documento: string;
  numero_documento: string;
  razon_social: string;
}

/**
 * Consulta los datos de un documento en el servicio externo.
 *
 * Endpoint CONGELADO por GOV-01 (`FREEZE-ID-1.0.0`, registro `RT-ID-01`):
 * `GET /personas/busqueda/{documento}`. No se inventa aqui ningun campo: el
 * espejo es el del wrapper `DocumentoConsultaOut`.
 */
export async function consultarDocumento(
  documento: string,
): Promise<ApiResponse<DocumentoConsultaData>> {
  const { data } = await api.get<ApiResponse<DocumentoConsultaData>>(
    `/personas/busqueda/${documento}`,
  );
  return data;
}
