// lib/forms/index.ts
// Barrel exports for the form helpers.
//
// Granular named exports only: the frontend contract forbids wildcard
// re-exports (they break tree-shaking and hide the public surface).

export { buildCreatePayload } from "./buildCreatePayload";
export {
  buildUpdatePayload,
  type BuildUpdatePayloadOptions,
} from "./buildUpdatePayload";
export { imageField, type ImageFieldResult } from "./imageField";
export {
  getFieldSchema,
  getTopLevelShape,
  isDeclaredField,
  isFileKindSchema,
} from "./schemaShape";
export { isSameFormValue } from "./valueEquality";
