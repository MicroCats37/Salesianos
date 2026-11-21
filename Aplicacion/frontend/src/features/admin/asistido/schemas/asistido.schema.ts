import { z } from "zod";
import { envelopeAdmin } from "@/features/admin/operaciones/schemas/operaciones.schema";
import { buildNumeroDocumentoValidator } from "@/features/auth/schemas/register.schema";

/**
 * The Zod mirrors of the ADMINISTRATIVE ASSISTED commands.
 *
 * They are the 1:1 mirror of the presenters of the target backend
 * (`Aplicacion/backend/modules/administracion/presentation/schemas/admin_asistido_schemas.py`):
 * `IdentidadCivilIn`, `ClienteCompraIn`, `EvidenciaPagoManualIn`,
 * `AgregarParticipanteEquipoIn`, `ItemPedidoClienteIn`, `ComprarPaseClienteIn`,
 * `ComprarPedidoClienteIn`, `ParticipanteAsistidoOut` and `CompraAsistidaOut`.
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
 * - **The identity is a BLOCK, not a loose field.** `nombres`, `apellidos`
 *   and `genero` travel ONLY when the person has to be REGISTERED: when
 *   the identity already exists, the padrón is the authority and the server
 *   never rewrites its names.
 */

/** The civil identity of the client of an assisted purchase. */
export const clienteCompraSchema = z.object({
  tipo_documento: z.string().min(1).max(3),
  numero_documento: z.string().min(1).max(20),
  nombres: z.string().max(255).nullable(),
  apellidos: z.string().max(255).nullable(),
  genero: z.enum(["M", "F"]).nullable(),
  contacto_email: z.string().max(255).nullable(),
});

/** The evidence of the external payment that the administrator registers. */
export const evidenciaPagoManualSchema = z.object({
  canal: z.string().min(1).max(32),
  referencia: z.string().min(1).max(100),
  motivo: z.string().min(1).max(1000),
});

/**
 * The evidence of the assisted purchase of a PASS.
 *
 * It is the general evidence PLUS two facts that belong to the path of the
 * passes and to NOTHING else (the Marketplace keeps the general evidence
 * untouched, `R6`):
 *
 * - `monto_declarado`: the amount the administrator DECLARES having received.
 *   It is INFORMATIVE and AUDITED: it never becomes the price, the total,
 *   the state of the payment or the state of the purchase (`R1`). Its absence
 *   means "not declared"; `"0"` is a valid declaration.
 * - `precio_version`: the token of the price that the quotation published. It
 *   is the CONCURRENCY control: when the server resolves a different price,
 *   it answers `409 PRECIO_CAMBIADO` and nothing is created.
 *
 * The CURRENCY is NEVER sent: the server derives it from the order (`R2`).
 */
export const evidenciaPagoCompraPaseSchema = evidenciaPagoManualSchema.extend({
  monto_declarado: z
    .string()
    .regex(
      /^\d+(\.\d{1,2})?$/,
      "El importe declarado lleva hasta dos decimales (por ejemplo, 35 o 35.50).",
    )
    .nullable()
    .optional(),
  precio_version: z.string().min(1).max(64).nullable().optional(),
});

/** The command that adds a participant to a team. */
export const agregarParticipanteEquipoSchema = z.object({
  tipo_documento: z.string().min(1).max(3),
  numero_documento: z.string().min(1).max(20),
  nombres: z.string().max(255).nullable(),
  apellidos: z.string().max(255).nullable(),
  genero: z.enum(["M", "F"]).nullable(),
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
  evidencia: evidenciaPagoCompraPaseSchema,
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
  /**
   * The amount the administrator DECLARED having received.
   *
   * It is the ECHO of the audited evidence: `null` means "not declared". It
   * is NOT the total of the purchase: the total is the one the server froze
   * (`total`).
   */
  monto_declarado: z.string().nullable(),
});

/**
 * The QUOTATION of a pass for the assisted purchase.
 *
 * It is the 1:1 mirror of `CotizacionPaseClienteOut`: the server resolves the
 * current price of the pass, derives the TOTAL and publishes the token of
 * that price (`version`).
 *
 * The AMOUNTS are STRINGS, exactly as the server sends them: the browser
 * prints them and NEVER multiplies a price by a quantity (`RN-C02`).
 */
export const cotizacionPaseClienteSchema = z.object({
  pase_id: z.string().min(1),
  edicion_id: z.string().min(1),
  pase_nombre: z.string(),
  cantidad: z.number().int().positive(),
  /** The unit price, as TEXT with two decimals. */
  precio_unitario: z.string(),
  /** The total of the quotation, as TEXT. The server derived it. */
  total: z.string(),
  /** The ISO-4217 currency of the price. */
  moneda: z.string(),
  /** The token of the price: the concurrency control of the quotation. */
  version: z.string().min(1),
  /** The state of the quotation (`ACTIVA`). */
  estado: z.string(),
  /** The moment the quotation stops being valid. */
  validez_hasta: z.string(),
});

// ── Envelopes ───────────────────────────────────────────────────────────────

/** The envelope of the assisted add of a participant. */
export const participanteAsistidoEnvelope = envelopeAdmin(
  participanteAsistidoSchema,
);

/** The envelope of the assisted purchases. */
export const compraAsistidaEnvelope = envelopeAdmin(compraAsistidaSchema);

/** The envelope of the quotation of a pass. */
export const cotizacionPaseClienteEnvelope = envelopeAdmin(
  cotizacionPaseClienteSchema,
);

// ── Inferred types ──────────────────────────────────────────────────────────

export type ClienteCompra = z.infer<typeof clienteCompraSchema>;
export type EvidenciaPagoManual = z.infer<typeof evidenciaPagoManualSchema>;
export type EvidenciaPagoCompraPase = z.infer<
  typeof evidenciaPagoCompraPaseSchema
>;
export type CotizacionPaseCliente = z.infer<typeof cotizacionPaseClienteSchema>;
export type CompraAsistida = z.infer<typeof compraAsistidaSchema>;
export type AgregarParticipanteEquipo = z.infer<
  typeof agregarParticipanteEquipoSchema
>;
export type ComprarPaseCliente = z.infer<typeof comprarPaseClienteSchema>;
export type ComprarPedidoCliente = z.infer<typeof comprarPedidoClienteSchema>;

// ── Los esquemas de FORMULARIO ──────────────────────────────────────────────
//
// Son la capa que el formulario valida. El COMANDO viaja al backend en el
// espejo de arriba: el formulario no es el contrato.

/**
 * The state of the ADMINISTRATIVE identity resolution.
 *
 * - `SIN_CONSULTAR`: the administrator has not searched the document yet.
 * - `ENCONTRADA`: the padrón already has that person: her canonical names
 *   are shown and the identity is REUSED.
 * - `NO_ENCONTRADA`: the padrón does not have that person: the names, the
 *   surnames and the gender have to be declared to REGISTER her.
 */
export const estadoIdentidadAdministrativaSchema = z.enum([
  "SIN_CONSULTAR",
  "ENCONTRADA",
  "NO_ENCONTRADA",
]);

export type EstadoIdentidadAdministrativa = z.infer<
  typeof estadoIdentidadAdministrativaSchema
>;

/**
 * The BLOCK of the administrative identity, shared by every form that asks
 * for a document.
 *
 * It is the same block for the participant and for the assisted purchases:
 * the resolution of the identity is ONE behaviour, not three.
 */
export const identidadAdministrativaCamposSchema = z.object({
  tipo_documento: z.enum(["DNI", "CE", "PAS"], {
    error: "Elige el tipo de documento.",
  }),
  numero_documento: z.string().min(1, "Escribe el número de documento."),
  nombres: z.string().max(255, "Máximo 255 caracteres."),
  apellidos: z.string().max(255, "Máximo 255 caracteres."),
  genero: z
    .string()
    .refine(
      (valor) => valor === "" || valor === "M" || valor === "F",
      "Elige el género.",
    ),
  estado_identidad: estadoIdentidadAdministrativaSchema,
});

/** The identity fields every administrative form shares. */
export type IdentidadAdministrativaCampos = z.infer<
  typeof identidadAdministrativaCamposSchema
>;

/**
 * The problems of an identity that has NOT been resolved yet.
 *
 * The list is EMPTY when the identity was found: the padrón brings the
 * canonical names and the administrator does not have to declare anything.
 */
export function problemasDeIdentidadAdministrativa(
  datos: IdentidadAdministrativaCampos,
): { campo: string; mensaje: string }[] {
  const documento = buildNumeroDocumentoValidator(
    datos.tipo_documento,
  ).safeParse(datos.numero_documento);

  if (!documento.success) {
    return [
      {
        campo: "numero_documento",
        mensaje:
          documento.error.issues[0]?.message ?? "Número de documento inválido.",
      },
    ];
  }

  if (datos.estado_identidad === "SIN_CONSULTAR") {
    return [
      {
        campo: "numero_documento",
        mensaje:
          "Busca la identidad del documento antes de continuar: el servidor decide si se reutiliza o se registra.",
      },
    ];
  }

  if (datos.estado_identidad === "ENCONTRADA") {
    return [];
  }

  const problemas: { campo: string; mensaje: string }[] = [];

  if (!datos.nombres.trim()) {
    problemas.push({
      campo: "nombres",
      mensaje: "Escribe los nombres: la persona se registrará en el padrón.",
    });
  }

  if (!datos.apellidos.trim()) {
    problemas.push({
      campo: "apellidos",
      mensaje: "Escribe los apellidos: la persona se registrará en el padrón.",
    });
  }

  if (!datos.genero) {
    problemas.push({
      campo: "genero",
      mensaje:
        "Elige el género: la disciplina lo exige para admitir a la persona.",
    });
  }

  return problemas;
}

/** The form of the administrative add of a participant. */
export const agregarParticipanteFormSchema = identidadAdministrativaCamposSchema
  .extend({
    rol: z.string().min(1, "Elige el rol."),
    motivo: z.string().min(1, "Escribe el motivo: queda en la auditoría."),
  })
  .superRefine((datos, ctx) => {
    for (const problema of problemasDeIdentidadAdministrativa(datos)) {
      ctx.addIssue({
        code: "custom",
        message: problema.mensaje,
        path: [problema.campo],
      });
    }
  });

/**
 * The form of an assisted purchase.
 *
 * The quantity is COERCED because the input is a number and the form reads
 * a string. The price NEVER travels: the server freezes it against the
 * catalogue (`RN-C02`).
 *
 * `monto_declarado` is the ONLY amount the administrator writes, and it is
 * INFORMATIVE: it travels as audited evidence and it NEVER becomes the price
 * nor the total. An EMPTY string means "not declared"; `"0"` is a valid
 * declaration (the administrator declares that nothing was charged).
 *
 * The field has a DEFAULT of an empty string so that a form that does not
 * draw it (the store, which keeps the general evidence) still validates.
 */
export const compraParaClienteFormSchema = identidadAdministrativaCamposSchema
  .extend({
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
    monto_declarado: z
      .string()
      .max(20, "Máximo 20 caracteres.")
      .refine(
        (valor) =>
          valor.trim() === "" || /^\d+(\.\d{1,2})?$/.test(valor.trim()),
        "El importe declarado lleva hasta dos decimales (por ejemplo, 35 o 35.50).",
      )
      .default(""),
  })
  .superRefine((datos, ctx) => {
    for (const problema of problemasDeIdentidadAdministrativa(datos)) {
      ctx.addIssue({
        code: "custom",
        message: problema.mensaje,
        path: [problema.campo],
      });
    }
  });

export type AgregarParticipanteFormData = z.infer<
  typeof agregarParticipanteFormSchema
>;
export type CompraParaClienteFormData = z.infer<
  typeof compraParaClienteFormSchema
>;
