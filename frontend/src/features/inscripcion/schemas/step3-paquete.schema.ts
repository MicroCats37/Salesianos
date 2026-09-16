import { z } from "zod";

/**
 * Step 3 — Paquete y pago.
 * No tiene inputs: es una pantalla de revisión (S/ 1,350 + izipay próximo a habilitar).
 * Se mantiene el schema para que el wizard tenga un paso validable.
 */
export const Step3PaqueteSchema = z.object({}).passthrough();

export type Step3PaqueteData = z.infer<typeof Step3PaqueteSchema>;
