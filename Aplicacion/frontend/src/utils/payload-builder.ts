import { v4 as uuidv4 } from "uuid";

/**
 * Robust boolean parser for environment variables.
 * Handles strings like 'true', '1', 'on', 'yes'.
 */
const toBoolean = (val: string | undefined): boolean => {
  if (!val) return false;
  const s = val.trim().toLowerCase();
  return s === "true" || s === "1" || s === "on" || s === "yes";
};

/**
 * Manual UUID generator fallback for non-secure contexts (HTTP)
 * where the native crypto or library might have issues.
 *
 * `crypto.getRandomValues` is available even in an insecure context, so it is
 * preferred over `Math.random`: the token of a multipart part is a
 * correlation id and two parts must never share it.
 */
const manualGenerateUUID = (): string => {
  const cryptoApi =
    typeof globalThis !== "undefined" ? globalThis.crypto : undefined;

  if (cryptoApi && typeof cryptoApi.getRandomValues === "function") {
    const bytes = new Uint8Array(16);
    cryptoApi.getRandomValues(bytes);
    // RFC 4122 version 4 layout.
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (byte) =>
      byte.toString(16).padStart(2, "0"),
    ).join("");
    return [
      hex.slice(0, 8),
      hex.slice(8, 12),
      hex.slice(12, 16),
      hex.slice(16, 20),
      hex.slice(20, 32),
    ].join("-");
  }

  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

/**
 * Decides which UUID generator to use.
 * Priority:
 * 1. Force manual generation if NEXT_PUBLIC_IS_TEST_UUID is truthy.
 * 2. Fallback to manual if in a non-secure context (HTTP) in the browser.
 * 3. Default to standard uuid library.
 */
const getUUID = (): string => {
  const isTestMode = toBoolean(process.env.NEXT_PUBLIC_IS_TEST_UUID);
  const isNotSecure =
    typeof window !== "undefined" && window.isSecureContext === false;

  if (isTestMode || isNotSecure) {
    return manualGenerateUUID();
  }

  try {
    return uuidv4();
  } catch (error) {
    console.warn("[PayloadBuilder] v4 library failed, falling back", error);
    return manualGenerateUUID();
  }
};

const FILE_PREFIX = "file_";

export type PayloadResult<T> = FormData | T;

/**
 * Tells whether a value is a `File`.
 *
 * The guard on the global keeps the module usable in a runtime where `File`
 * does not exist: the transport also runs on the server, where the payload of
 * a request is never a `File`.
 */
const isFile = (value: unknown): value is File =>
  typeof File !== "undefined" && value instanceof File;

/**
 * Automatically detects File objects in the payload and converts to FormData.
 * If no files are found, returns the original object (sent as JSON by Axios).
 *
 * The protocol is the one of the backend media contract (`PROTO-MD-1.0.0`):
 * the part `data` carries the JSON of the payload and the part `files`
 * carries one part per file, named `<token>___<realname>`, where the token is
 * the identifier that replaces the file inside the JSON.
 *
 * The input is NEVER mutated: the tokenized copy is a new object.
 */
export function buildApiPayload<T>(inputData: T): PayloadResult<T> {
  const fileList: Array<{ token: string; file: File }> = [];

  const scanAndTokenize = (node: unknown): unknown => {
    if (node === null || node === undefined) return node;

    if (isFile(node)) {
      const uuid = getUUID();
      const token = `${FILE_PREFIX}${uuid}`;
      fileList.push({ token, file: node });
      return token;
    }

    if (node instanceof Date) return node;
    if (Array.isArray(node)) return node.map(scanAndTokenize);

    if (typeof node === "object") {
      const result: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(
        node as Record<string, unknown>,
      )) {
        result[key] = scanAndTokenize(value);
      }
      return result;
    }

    return node;
  };

  const tokenizedData = scanAndTokenize(inputData);

  if (fileList.length === 0) return inputData;

  const formData = new FormData();
  formData.append("data", JSON.stringify(tokenizedData));

  // The backend uses token___realname to identify the link in the JSON payload natively
  // without losing the original file name formatting.
  for (const item of fileList) {
    const overloadedName = `${item.token}___${item.file.name}`;
    formData.append("files", item.file, overloadedName);
  }

  return formData;
}
