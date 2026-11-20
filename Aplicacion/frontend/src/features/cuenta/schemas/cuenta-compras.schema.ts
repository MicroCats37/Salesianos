import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";
import type { CompraResumen, RolVeredicto } from "../types/cuenta.types";

const estadoCompraSchema = z.object({
  codigo: z.string().min(1),
  etiqueta: z.string(),
  descripcion: z.string(),
});

const compraCuentaSchema = z.object({
  id: z.string().min(1),
  origen: z.enum(["INSCRIPCION", "PASE", "MARKETPLACE"]),
  concepto: z.string(),
  monto: z.string(),
  moneda: z.string().length(3),
  fecha: z.string(),
  estado: estadoCompraSchema,
});

export const comprasCuentaEnvelopeSchema = apiResponseSchema(
  z.array(compraCuentaSchema),
);

function rolDesdeEstado(codigo: string): RolVeredicto {
  if (codigo === "PAGADA") return "confirmado";
  if (codigo === "PENDIENTE") return "pendiente";
  if (codigo === "CANCELADA") return "rechazado";
  return "desconocido";
}

export function compraCuentaDesdeWire(
  compra: z.infer<typeof compraCuentaSchema>,
): CompraResumen {
  return {
    id: compra.id,
    origen: compra.origen,
    concepto: compra.concepto,
    monto: compra.monto,
    moneda: compra.moneda,
    fecha: compra.fecha,
    veredicto: {
      estado: compra.estado,
      rol: rolDesdeEstado(compra.estado.codigo),
    },
  };
}
