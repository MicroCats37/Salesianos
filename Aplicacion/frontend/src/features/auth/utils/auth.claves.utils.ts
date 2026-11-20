/**
 * The query keys of the auth and identity datasets.
 *
 * They live HERE and nowhere else: a component never spells a key
 * (`salesianos-api-data`, "one dataset, one namespace").
 *
 * The namespace is `auth` because the session and the identity belong to the
 * SAME account: confirming an identity changes the facts of the session, and
 * the invalidation of one travels to the other.
 */
export const authClaves = {
  todas: ["auth"] as const,
  /** The facts of the session of the authenticated actor (`GET /auth/me`). */
  sesion: () => [...authClaves.todas, "sesion"] as const,
  /** The identity dataset (`/personas/**`). */
  identidad: () => [...authClaves.todas, "identidad"] as const,
  /** The consultation of a document in the external source (`RT-ID-01`). */
  documento: (documento: string) =>
    [...authClaves.identidad(), "documento", documento] as const,
  /** The resolution of a document (`RT-ID-02`). */
  personaResuelta: (tipoDocumento: string, numeroDocumento: string) =>
    [
      ...authClaves.identidad(),
      "resolver",
      tipoDocumento,
      numeroDocumento,
    ] as const,
  /** The confirmation of a document (`RT-ID-03`). */
  personaConfirmada: (tipoDocumento: string, numeroDocumento: string) =>
    [
      ...authClaves.identidad(),
      "confirmar",
      tipoDocumento,
      numeroDocumento,
    ] as const,
};
