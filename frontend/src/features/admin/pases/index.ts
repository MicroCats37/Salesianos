/**
 * Administrative operations over the party passes.
 *
 * The area owns the CANCELLATION of a pass purchase: the payments table, its
 * drilldown and the overview live in the shared administration area.
 */

export {
  AdminPaseCancelarDialog,
  type AdminPaseCancelarDialogProps,
} from "./components";
export {
  construirPayloadCancelarCompraPase,
  invalidarLecturasPase,
  useCancelarCompraPase,
  type VariablesCancelarCompraPase,
} from "./hooks";
export {
  type AdminPaseCancelada,
  type AdminPaseCanceladaEnvelope,
  AdminPaseCanceladaEnvelopeSchema,
  AdminPaseCanceladaSchema,
  type AdminPaseCancelarFormData,
  AdminPaseCancelarFormSchema,
  type AdminPaseCancelarPayload,
  AdminPaseCancelarPayloadSchema,
} from "./schemas";
export { cancelarCompraPase } from "./services";
export {
  ADMIN_BENEFICIARIO_ACTIVA,
  ADMIN_BENEFICIARIO_REVOCADA,
  adminBeneficiarioEstadoLabel,
  adminBeneficiarioEstadoTone,
  adminPaseCancelable,
  adminPaseCancelacionAviso,
  adminPaseConteosTexto,
} from "./utils";
