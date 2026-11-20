import { z } from "zod";

/**
 * The client-side schema of the purchase recovery form.
 *
 * It is NOT a wire mirror and it will not become one in API-01: the route
 * `RT-RC-01` (`POST /recuperar-compra`) has NO registered controller in
 * `Aplicacion/backend/config/api.py` and NO frozen presenter to mirror. A
 * Zod mirror of a wrapper that does not exist would be an INVENTED contract.
 *
 * This schema validates what the person typed BEFORE the request leaves the
 * browser. When the backend owns the route, the wire mirror arrives next to
 * this file and the form keeps consuming this shape.
 *
 * The truth lives in Zod (`contract/smart.md` §5.1): the component never
 * decides on its own whether a value is acceptable.
 */
export const RecuperarCompraFormSchema = z.object({
  correo: z
    .string()
    .trim()
    .min(1, "Escribe el correo con el que hiciste la compra.")
    .email("Ese correo no tiene un formato válido."),
  numeroOrden: z
    .string()
    .trim()
    .min(1, "Escribe el número de orden de la compra.")
    .min(4, "El número de orden tiene al menos 4 caracteres."),
});

export type RecuperarCompraFormData = z.infer<typeof RecuperarCompraFormSchema>;
