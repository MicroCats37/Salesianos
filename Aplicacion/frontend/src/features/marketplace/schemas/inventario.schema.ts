import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";
import { pedidoLineaSchema } from "./pedido.schema";

const id = z.string().uuid();
const fecha = z.string().min(1);

export const movimientoInventarioSchema = z.object({
  id,
  producto_id: id,
  cantidad: z.number().int(),
  tipo: z.string().min(1),
  motivo: z.string(),
  referencia: z.string(),
  actor_id: id.nullable(),
  created_at: fecha,
});

export const inventarioProductoSchema = z.object({
  producto_id: id,
  nombre: z.string(),
  slug: z.string(),
  stock: z.number().int().min(0),
  reservado: z.number().int().min(0),
  disponible: z.number().int().min(0),
  movimientos: z.array(movimientoInventarioSchema),
});

export const inventarioEnvelope = apiResponseSchema(
  z.array(inventarioProductoSchema),
);
export const movimientoInventarioEnvelope = apiResponseSchema(
  movimientoInventarioSchema,
);

export const entregaPendienteSchema = z.object({
  pedido_id: id,
  comprador_nombres: z.string().min(1),
  comprador_apellidos: z.string().min(1),
  comprador_documento: z.string().min(1),
  estado: z.string().min(1),
  estado_entrega: z.string().min(1),
  total: z.coerce.number().min(0),
  moneda: z.string().min(1),
  lineas: z.array(pedidoLineaSchema),
  created_at: fecha,
});

export const entregaEntregadaSchema = z.object({
  pedido_id: id,
  comprador_nombres: z.string().min(1),
  comprador_apellidos: z.string().min(1),
  comprador_documento: z.string().min(1),
  total: z.coerce.number().min(0),
  moneda: z.string().min(1),
  lineas: z.array(pedidoLineaSchema),
  entregada_en: fecha,
});

export const entregaConfirmadaSchema = z.object({
  pedido_id: id,
  estado_entrega: z.string().min(1),
  cantidad_total: z.number().int().min(1),
  actor_id: id,
  entregada_en: fecha,
  lineas: z.array(pedidoLineaSchema),
});

export const entregasEnvelope = apiResponseSchema(
  z.object({
    pendientes: z.array(entregaPendienteSchema),
    entregadas: z.array(entregaEntregadaSchema),
  }),
);
export const entregaConfirmadaEnvelope = apiResponseSchema(
  entregaConfirmadaSchema,
);

export const movimientoInventarioFormSchema = z
  .object({
    producto_id: id,
    tipo: z.enum([
      "REPOSICION",
      "MERMA",
      "CONSUMO_INTERNO",
      "AJUSTE",
      "SALIDA_SIN_VENTA",
    ]),
    cantidad: z.coerce
      .number()
      .int()
      .refine((cantidad) => cantidad !== 0, {
        message: "La cantidad no puede ser cero.",
      }),
    motivo: z
      .string()
      .trim()
      .min(1, "Indica el motivo del movimiento.")
      .max(200),
  })
  .superRefine(({ tipo, cantidad }, contexto) => {
    const requiereEntrada = tipo === "REPOSICION";
    const requiereSalida = [
      "MERMA",
      "CONSUMO_INTERNO",
      "SALIDA_SIN_VENTA",
    ].includes(tipo);
    if (requiereEntrada && cantidad < 0) {
      contexto.addIssue({
        code: "custom",
        path: ["cantidad"],
        message: "Una reposición debe tener cantidad positiva.",
      });
    }
    if (requiereSalida && cantidad > 0) {
      contexto.addIssue({
        code: "custom",
        path: ["cantidad"],
        message: "Esta salida debe tener cantidad negativa.",
      });
    }
  });

export type InventarioProducto = z.infer<typeof inventarioProductoSchema>;
export type MovimientoInventario = z.infer<typeof movimientoInventarioSchema>;
export type MovimientoInventarioFormData = z.infer<
  typeof movimientoInventarioFormSchema
>;
export type EntregaPendiente = z.infer<typeof entregaPendienteSchema>;
export type EntregaEntregada = z.infer<typeof entregaEntregadaSchema>;
export type EntregaConfirmada = z.infer<typeof entregaConfirmadaSchema>;
