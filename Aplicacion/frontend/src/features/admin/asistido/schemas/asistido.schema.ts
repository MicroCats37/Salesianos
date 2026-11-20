import { z } from "zod";
import { envelopeAdmin } from "@/features/admin/operaciones/schemas/operaciones.schema";

/**
 * The Zod mirrors of the ADMINISTRATIVE ASSISTED commands.
 *
 * They are the 1:1 mirror of the presenters of the target backend
 * (`Aplicacion/backend/modules/administracion/presentation/schemas/admin_asistido_schemas.py`):
 * `ClienteCompraIn`, `EvidenciaPagoManualIn`, `AgregarParticipanteEquipoIn`,
 * `ItemPedidoClienteIn`, `ComprarPaseClienteIn`, `ComprarPedidoClienteIn`,
 * `ParticipanteAsistidoOut` and `CompraAsistidaOut`.
 *
 * The rules of the mirror:
 *
 * - **No `z.any()` and no generic field.** Every field is declared.
 * - **The envelope is the FROZEN one**: the factory `envelopeAdmin` of the
 *   administration area builds it, so the shape is not replicated.
 * - **The machine codes are `string`, not enums.** The backend owns the
 *   vocabulary and a new value must NOT break the whole read.
 * - **The amounts are STRINGS.** The backend serialises `Decimal` as a
 *   string in this wrapper, and the browser never recalculates a total.
 */

/** The civil identity of the client of an assisted purchase. */
export const clienteCompraSchema = z.object({
  tipo_documento: z.string().min(1).max(3),
  numero_documento: z.string().min(1).max(20),
  nombres: z.string().min(1).max(255),
  apellidos: z.string().max(255),
  contacto_email: z.string().max(255),
});

/** The evidence of the external payment that the administrator registers. */
export const evidenciaPagoManualSchema = z.object({
  canal: z.string().min(1).max(32),
  referencia: z.string().min(1).max(100),
  motivo: z.string().min(1).max(1000),
});

/** The command that adds an existing participant to a team. */
export const agregarParticipanteEquipoSchema = z.object({
  tipo_documento: z.string().min(1).max(3),
  numero_documento: z.string().min(1).max(20),
  rol: z.string().min(1).max(16),
  motivo: z.string().min(1).max(1000),
});

/** One article of the assisted order of the store. */
export const itemPedidoClienteSchema = z.object({
  tipo: z.string().min(1).max(16),
  producto_id: z.string().min(1),
  cantidad: z.number().int().positive(),
});

/** The command that buys passes for a client. */
export const comprarPaseClienteSchema = z.object({
  pase_id: z.string().min(1),
  cantidad: z.number().int().positive(),
  cliente: clienteCompraSchema,
  evidencia: evidenciaPagoManualSchema,
});

/** The command that orders the store for a client. */
export const comprarPedidoClienteSchema = z.object({
  items: z.array(itemPedidoClienteSchema).min(1),
  cliente: clienteCompraSchema,
  evidencia: evidenciaPagoManualSchema,
});

/** The participation that the administration just created. */
export const participanteAsistidoSchema = z.object({
  participacion_id: z.string().min(1),
  persona_id: z.string().min(1),
  nombre: z.string(),
  documento: z.string(),
  equipo_id: z.string().min(1),
  inscripcion_id: z.string().min(1),
  rol: z.string(),
  estado: z.string(),
});

/** The assisted purchase. */
export const compraAsistidaSchema = z.object({
  compra_id: z.string().min(1),
  recurso_id: z.string().min(1),
  orden_pago_id: z.string().min(1),
  tipo: z.string().min(1),
  concepto: z.string(),
  total: z.string(),
  moneda: z.string(),
  estado: z.string(),
  estado_pago: z.string(),
  comprador_persona_id: z.string().min(1),
  comprador_nombre: z.string(),
  cantidad: z.number().int().positive(),
});

// ── Envelopes ───────────────────────────────────────────────────────────────

/** The envelope of the assisted add of a participant. */
export const participanteAsistidoEnvelope = envelopeAdmin(
  participanteAsistidoSchema,
);

/** The envelope of the assisted purchases. */
export const compraAsistidaEnvelope = envelopeAdmin(compraAsistidaSchema);

// ── Inferred types ──────────────────────────────────────────────────────────

export type ClienteCompra = z.infer<typeof clienteCompraSchema>;
export type EvidenciaPagoManual = z.infer<typeof evidenciaPagoManualSchema>;
export type AgregarParticipanteEquipo = z.infer<
  typeof agregarParticipanteEquipoSchema
>;
export type ComprarPaseCliente = z.infer<typeof comprarPaseClienteSchema>;
export type ComprarPedidoCliente = z.infer<typeof comprarPedidoClienteSchema>;

// ── Los esquemas de FORMULARIO ──────────────────────────────────────────────
//
// Son la capa que el formulario valida. El COMANDO viaja al backend en el
// espejo de arriba: el formulario no es el contrato.

/** The form of the administrative add of a participant. */
export const agregarParticipanteFormSchema = z.object({
  tipo_documento: z.string().min(1, "Elige el tipo de documento."),
  numero_documento: z.string().min(1, "Escribe el número de documento."),
  rol: z.string().min(1, "Elige el rol."),
  motivo: z.string().min(1, "Escribe el motivo: queda en la auditoría."),
});

/**
 * The form of an assisted purchase.
 *
 * The quantity is COERCED because the input is a number and the form reads
 * a string. The price NEVER travels: the server freezes it against the
 * catalogue (`RN-C02`).
 */
export const compraParaClienteFormSchema = z.object({
  tipo_documento: z.string().min(1, "Elige el tipo de documento."),
  numero_documento: z.string().min(1, "Escribe el número de documento."),
  nombres: z.string().min(1, "Escribe los nombres del cliente."),
  apellidos: z.string(),
  contacto_email: z
    .string()
    .refine(
      (correo) => correo === "" || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo),
      "Escribe un correo válido.",
    ),
  cantidad: z.coerce
    .number({ message: "Escribe la cantidad." })
    .int("La cantidad es un número entero.")
    .min(1, "La cantidad es al menos una unidad."),
  canal: z.string().min(1, "Elige el canal del pago."),
  referencia: z.string().min(1, "Escribe la referencia del pago."),
  motivo: z.string().min(1, "Escribe el motivo: queda en la auditoría."),
});

export type AgregarParticipanteFormData = z.infer<
  typeof agregarParticipanteFormSchema
>;
export type CompraParaClienteFormData = z.infer<
  typeof compraParaClienteFormSchema
>;
