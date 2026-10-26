import { z } from "zod";

/**
 * AdminErrorSchema — mirror 1:1 of the backend `core.responses.ErrorDetail`.
 *
 * The admin area never renders a raw exception: it only surfaces the stable
 * machine-readable code and the public Spanish message owned by the backend
 * error catalog (`contract/api-wrapper-presenter-contract.md` §8).
 *
 * `details` is the only free-form field of the contract and it is optional;
 * it never carries credentials, SQL or stack traces.
 */
export const AdminErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.record(z.string(), z.unknown()).nullish(),
});

export type AdminError = z.infer<typeof AdminErrorSchema>;
