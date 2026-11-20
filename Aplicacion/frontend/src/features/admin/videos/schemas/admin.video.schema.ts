import { z } from "zod";
import {
  videoListItemSchema,
  videoSchema,
} from "@/features/videos/schemas/video.schema";
import { paginatedResultSchema } from "@/shared/schemas/pagination.schema";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirror of the administration wrappers of the videos.
 *
 * The administration surface and the public surface publish the SAME video:
 * the wrapper is not duplicated, it is REUSED from the public mirror. What
 * changes is the ENDPOINT (`/administracion/videos`) and the permission
 * (`RequireAdmin`), never the shape of the data.
 */

/** A video of the administration list (`VideoListOut`). */
export const adminVideoListItemSchema = videoListItemSchema;

/** The detail of a video (`VideoOut`). */
export const adminVideoSchema = videoSchema;

/** The administration list (`GET /api/administracion/videos`). */
export const adminVideosEnvelope = apiResponseSchema(
  paginatedResultSchema(adminVideoListItemSchema),
);

/** The administration detail of a video (`GET /api/administracion/videos/{id}`). */
export const adminVideoEnvelope = apiResponseSchema(adminVideoSchema);

/**
 * The form of the publication of a video (`CrearVideoIn`).
 *
 * It declares the SHAPE of the payload: the fields, whether they are
 * required and how long they can be. It does NOT declare the rules of the
 * domain: which schemes the address may use is the backend's decision
 * (`es_url_http_valida` in `modules/videos/domain/urls.py`), and the frontend
 * never duplicates it. A scheme that the server refuses comes back as a `422`
 * and reaches the control that owns the field.
 */
export const CrearVideoFormSchema = z.object({
  titulo: z
    .string()
    .trim()
    .min(1, "El video necesita un título.")
    .max(200, "El título admite hasta 200 caracteres."),
  descripcion: z
    .string()
    .trim()
    .max(5000, "La descripción admite hasta 5000 caracteres."),
  url: z
    .string()
    .trim()
    .min(1, "El video necesita una dirección.")
    .max(500, "La dirección admite hasta 500 caracteres."),
});

export type CrearVideoFormData = z.infer<typeof CrearVideoFormSchema>;

/**
 * The payload of the edition of a video (`ActualizarVideoIn`).
 *
 * The `PATCH` is PARTIAL: only the fields that the operator touched travel.
 * The diff is made by `GenericForm` in its `update` mode, against the values
 * that the video already had — not here.
 */
export type ActualizarVideoFormData = Partial<CrearVideoFormData>;
