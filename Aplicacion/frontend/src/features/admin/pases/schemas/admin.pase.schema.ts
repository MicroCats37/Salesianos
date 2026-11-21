import { z } from "zod";
import {
  type IdentidadAdministrativaCampos,
  identidadAdministrativaCamposSchema,
  problemasDeIdentidadAdministrativa,
} from "@/features/admin/asistido/schemas/asistido.schema";
import {
  envelopeAdmin,
  envelopeAdminPaginado,
} from "@/features/admin/operaciones/schemas/operaciones.schema";

/**
 * The Zod mirrors of the ADMINISTRATIVE PASSES (the courtesies and the
 * one-shot credential of the door).
 *
 * They are the 1:1 mirror of the frozen ledger
 * (`plan/administracion-pases-alta-directa/contracts` §1.2, §1.3, §3.3, §3.4):
 *
 * | Wire | Backend | Success |
 * |---|---|---|
 * | the list of the courtesies | `GET /administracion/pases/cortesias` | `PaginatedData[AdminCortesiaListItemOut]` |
 * | the grant of a courtesy | `POST /administracion/pases/cortesias` | `AdminCortesiaOut` (201) |
 * | the revocation of a courtesy | `POST /administracion/pases/cortesias/{id}/revocar` | `AdminCortesiaRevocadaOut` (200) |
 * | the credential of the door | `POST /validaciones/tickets` | `TicketEmitidoOut` (201) |
 *
 * ## What the browser NEVER does
 *
 * - It NEVER computes an amount: a courtesy has NO financial facts, so there
 *   is no price, no total and no currency anywhere in this file (`R4`).
 * - It NEVER declares the type of the right nor the operation of the ticket:
 *   the server derives both from the right (`F6`).
 * - It NEVER invents a state: the state is the one the presenter published.
 */

/** The identifier published by the backend. */
const id = z.string().min(1);

/** An instant published by the presenter. */
const marcaTiempo = z.string().min(1);

// ── The wire shapes ──────────────────────────────────────────────────────────

/**
 * A row of the administrative list of the courtesies
 * (`AdminCortesiaListItemOut`).
 *
 * The list NEVER publishes the token of the management of a purchase nor the
 * detail of a payment.
 */
export const adminCortesiaListaItemSchema = z.object({
  /** The acta of the courtesy. */
  id,
  /** The name of the pass that was granted. */
  pase_nombre: z.string(),
  /** The name of the edition. */
  edicion_nombre: z.string(),
  /** The names of the beneficiary. */
  persona_nombres: z.string(),
  /** The type of document of the beneficiary. */
  persona_tipo_documento: z.string().max(3),
  /** The number of document of the beneficiary. */
  persona_numero_documento: z.string().max(20),
  /** The state of the courtesy (`ACTIVA` | `REVOCADA`). */
  estado: z.string().min(1),
  /** The reason of the grant. */
  motivo: z.string(),
  /** The names of who granted it. */
  actor_nombres: z.string(),
  /** The instant of the grant. */
  concedido_en: marcaTiempo,
  /**
   * The identifier of the RIGHT that the courtesy created.
   *
   * The credential of the door is issued against the RIGHT
   * (`PaseBeneficiario`), not against the acta: without this identifier the
   * action does not exist.
   *
   * It is NULLABLE and NOT optional: the backend ALWAYS publishes the key,
   * and its value is `null` only when the acta has no right — a corrupted
   * historical record. The absent identifier is published as absent and is
   * NEVER invented.
   */
  derecho_id: id.nullable(),
});

/** The grant of a courtesy (`AdminCortesiaOut`). */
export const adminCortesiaSchema = z.object({
  /** The acta of the courtesy. */
  id,
  /** The edition of the scope. */
  edicion_id: id,
  /** The name of the edition. */
  edicion_nombre: z.string(),
  /** The pass that was granted. */
  pase_id: id,
  /** The name of the pass. */
  pase_nombre: z.string(),
  /** The person who receives the courtesy. */
  persona_id: id,
  /** The names of the person. */
  persona_nombres: z.string(),
  /** The type of document of the person. */
  persona_tipo_documento: z.string().max(3),
  /** The number of document of the person. */
  persona_numero_documento: z.string().max(20),
  /** The state of the courtesy. */
  estado: z.string().min(1),
  /** The reason of the grant. */
  motivo: z.string(),
  /** The account that granted the courtesy. */
  actor_usuario_id: id.nullable(),
  /** The names of who granted it. */
  actor_nombres: z.string(),
  /** The instant of the grant. */
  concedido_en: marcaTiempo,
  /** The instant of the revocation, when it happened. */
  revocado_en: marcaTiempo.nullable(),
  /**
   * The identifier of the RIGHT that the courtesy created.
   *
   * It is NOT nullable: the acta and its right are created in the SAME
   * transaction, so a granted courtesy ALWAYS has one. The browser uses it
   * to issue the credential of the door without another round trip.
   */
  derecho_id: id,
});

/**
 * The revocation of a courtesy (`AdminCortesiaRevocadaOut`).
 *
 * The revocation is IDEMPOTENT: a second revocation answers `200` with
 * `ya_revoked = true` and never an error.
 */
export const adminCortesiaRevocadaSchema = z.object({
  /** The acta of the courtesy. */
  id,
  /** The edition of the scope. */
  edicion_id: id,
  /** The name of the edition. */
  edicion_nombre: z.string(),
  /** The pass that was granted. */
  pase_id: id,
  /** The name of the pass. */
  pase_nombre: z.string(),
  /** The person who received the courtesy. */
  persona_id: id,
  /** The names of the person. */
  persona_nombres: z.string(),
  /** The type of document of the person. */
  persona_tipo_documento: z.string().max(3),
  /** The number of document of the person. */
  persona_numero_documento: z.string().max(20),
  /** The state of the courtesy (`REVOCADA`). */
  estado: z.string().min(1),
  /** The reason of the GRANT. */
  motivo: z.string(),
  /** The reason of the REVOCATION. */
  motivo_revocacion: z.string(),
  /** The account that granted the courtesy. */
  actor_usuario_id: id.nullable(),
  /** The names of who granted it. */
  actor_nombres: z.string(),
  /** The instant of the grant. */
  concedido_en: marcaTiempo,
  /** The instant of the revocation. */
  revocado_en: marcaTiempo,
  /** Whether the courtesy was ALREADY revoked when the command arrived. */
  ya_revocado: z.boolean(),
});

/**
 * The credential of the door (`TicketEmitidoOut`).
 *
 * `codigo` is the SECRET: it travels ONLY in this answer, it is never listed,
 * never audited and never cached.
 */
export const ticketEmitidoSchema = z.object({
  /** The ticket. */
  ticket_id: id,
  /** The secret of the ticket: it is shown ONCE. */
  codigo: z.string().min(1),
  /** The type of the right (`PASE` | `ENTRADA_CORTESIA`). */
  tipo_derecho: z.string().min(1),
  /** The operation of the ticket (`INGRESO`). */
  operacion: z.string().min(1),
  /** The edition of the ticket. */
  edicion_id: id,
  /** The instant of the issue. */
  emitido_en: marcaTiempo,
});

// ── The commands (the bodies that travel) ────────────────────────────────────

/**
 * The grant of a courtesy (`OtorgarCortesiaIn`).
 *
 * The MOTIVE is mandatory: without it there is no audit. The ACTOR is the
 * authenticated account: the browser NEVER declares it.
 */
export const otorgarCortesiaSchema = z.object({
  /** The edition of the scope. */
  edicion_id: id,
  /** The pass that is granted. */
  pase_id: id,
  /** The type of document of the person. */
  tipo_documento: z.string().max(3).nullable(),
  /** The number of document of the person. */
  numero_documento: z.string().max(20).nullable(),
  /** The names of the person, when she has to be registered. */
  nombres: z.string().max(255),
  /** The surnames of the person, when she has to be registered. */
  apellidos: z.string().max(255),
  /** The reason of the grant. It is mandatory. */
  motivo: z.string().min(1).max(500),
});

/**
 * The revocation of a courtesy (`RevocarCortesiaIn`).
 *
 * Without a reason there is no audit: the domain demands five characters.
 */
export const revocarCortesiaSchema = z.object({
  /** The reason of the revocation. */
  motivo: z.string().min(5).max(500),
});

/**
 * The issue of the credential of the door (`EmitirTicketIn`).
 *
 * The browser declares ONLY the right: the type and the operation are
 * DERIVED by the server from the right itself.
 */
export const emitirTicketSchema = z.object({
  /** The right that receives the credential. */
  derecho_id: id,
});

// ── The envelopes ────────────────────────────────────────────────────────────

/** The envelope of the list of the courtesies. */
export const adminCortesiasListaEnvelope = envelopeAdminPaginado(
  adminCortesiaListaItemSchema,
);

/** The envelope of the grant of a courtesy. */
export const adminCortesiaEnvelope = envelopeAdmin(adminCortesiaSchema);

/** The envelope of the revocation of a courtesy. */
export const adminCortesiaRevocadaEnvelope = envelopeAdmin(
  adminCortesiaRevocadaSchema,
);

/** The envelope of the issue of the credential. */
export const ticketEmitidoEnvelope = envelopeAdmin(ticketEmitidoSchema);

// ── The forms ────────────────────────────────────────────────────────────────

/**
 * The problems of an identity that a COURTESY declares.
 *
 * They are the problems of the SHARED administrative identity, WITHOUT the
 * gender: the wire contract of the courtesy has no `genero` field, so the
 * form never demands a value that the server would discard.
 */
export function problemasDeIdentidadCortesia(
  datos: IdentidadAdministrativaCampos,
): { campo: string; mensaje: string }[] {
  return problemasDeIdentidadAdministrativa(datos).filter(
    (problema) => problema.campo !== "genero",
  );
}

/**
 * The form of the grant of a courtesy.
 *
 * It is the Mode 1 (`children`): the identity lives in the SHARED block, the
 * pass is a SELECT of the catalogue, the reason is a mandatory text and the
 * CONFIRMATION of the absence of a charge is an explicit checkbox: a
 * courtesy has no financial facts, and the operator says so.
 */
export const cortesiaPaseFormSchema = identidadAdministrativaCamposSchema
  .extend({
    /** The pass that is granted. */
    pase_id: z.string().min(1, "Elige el pase que se otorga."),
    /** The reason of the grant. */
    motivo: z
      .string()
      .min(5, "El motivo necesita al menos 5 caracteres: queda en el acta.")
      .max(500, "Máximo 500 caracteres."),
    /** The explicit confirmation that the courtesy does not charge anything. */
    confirma_sin_cobro: z
      .boolean()
      .refine(
        (confirmado) => confirmado,
        "Confirma que la cortesía no genera cobro, orden ni transacción.",
      ),
  })
  .superRefine((datos, ctx) => {
    for (const problema of problemasDeIdentidadCortesia(datos)) {
      ctx.addIssue({
        code: "custom",
        message: problema.mensaje,
        path: [problema.campo],
      });
    }
  });

/** The form of the revocation of a courtesy. */
export const revocarCortesiaFormSchema = z.object({
  /** The reason of the revocation: without it there is no audit. */
  motivo: z
    .string()
    .min(5, "El motivo necesita al menos 5 caracteres: queda en el acta.")
    .max(500, "Máximo 500 caracteres."),
});

// ── The inferred types ───────────────────────────────────────────────────────

export type AdminCortesiaListaItem = z.infer<
  typeof adminCortesiaListaItemSchema
>;
export type AdminCortesia = z.infer<typeof adminCortesiaSchema>;
export type AdminCortesiaRevocada = z.infer<typeof adminCortesiaRevocadaSchema>;
export type TicketEmitido = z.infer<typeof ticketEmitidoSchema>;

export type OtorgarCortesia = z.infer<typeof otorgarCortesiaSchema>;
export type RevocarCortesia = z.infer<typeof revocarCortesiaSchema>;
export type EmitirTicket = z.infer<typeof emitirTicketSchema>;

/** The page of the list of the courtesies. */
export interface PaginaCortesias {
  /** The rows of the page. */
  items: AdminCortesiaListaItem[];
  /** The total of the rows. */
  total: number;
  /** The page, 1-based. */
  page: number;
  /** The size of the page. */
  page_size: number;
  /** The total of the pages. */
  total_pages: number;
}

/** The form of the grant of a courtesy. */
export type CortesiaPaseFormData = z.infer<typeof cortesiaPaseFormSchema>;

/** The form of the revocation of a courtesy. */
export type RevocarCortesiaFormData = z.infer<typeof revocarCortesiaFormSchema>;
