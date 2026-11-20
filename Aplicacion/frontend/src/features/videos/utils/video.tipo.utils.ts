/**
 * The classification of a published video address.
 *
 * It is a PRESENTATION concern and NOT a domain rule: the backend already
 * refuses every scheme that is not `http` or `https` (`CrearVideoIn` and
 * `ActualizarVideoIn` validate the address at the HTTP edge, and the model
 * carries NO provider column). The browser decides HOW to show the address,
 * never WHETHER the address is valid.
 *
 * The functions here are PURE: no network, no state, no side effects. A
 * browser that cannot classify an address falls back to an external link,
 * and an address whose scheme is not http/https is shown as plain text — a
 * `javascript:` link is never rendered as a link.
 */

/** The three ways a published address can be shown. */
export type TipoVideo = "hls" | "archivo" | "embebible" | "externo";

/**
 * The extensions that the browser plays with its own `<video>` control.
 *
 * The check ignores the query and the fragment: the path decides.
 */
const EXTENSIONES_ARCHIVO: readonly string[] = [
  ".mp4",
  ".webm",
  ".ogv",
  ".ogg",
  ".mov",
  ".m4v",
];

const EXTENSION_HLS = ".m3u8";

/**
 * Parses an address, and accepts ONLY `http` and `https`.
 *
 * A scheme that the browser could execute (`javascript:`, `data:`) never
 * leaves this function: it is not an address, it is not even text.
 */
function analizar(url: string): URL | null {
  const recortada = url.trim();
  if (recortada === "") return null;

  try {
    const analizada = new URL(recortada);

    if (analizada.protocol !== "http:" && analizada.protocol !== "https:") {
      return null;
    }

    return analizada;
  } catch {
    return null;
  }
}

/**
 * Whether the address can be linked safely.
 *
 * A link is only rendered when the address is `http` or `https`: an anchor
 * with a `javascript:` address is an execution, not a navigation.
 */
export function esUrlHttpSeguro(url: string): boolean {
  return analizar(url) !== null;
}

/** Whether the address points at a file the browser plays natively. */
function esArchivo(analizada: URL): boolean {
  const camino = analizada.pathname.toLowerCase();

  return EXTENSIONES_ARCHIVO.some((extension) => camino.endsWith(extension));
}

function esHls(analizada: URL): boolean {
  return analizada.pathname.toLowerCase().endsWith(EXTENSION_HLS);
}

/** The first segment of the path, without the empty ones. */
function segmentos(analizada: URL): string[] {
  return analizada.pathname.split("/").filter((segmento) => segmento !== "");
}

/** The identifier of a YouTube video, whatever the shape of the address. */
function embebibleYouTube(analizada: URL): string | null {
  const host = analizada.hostname.toLowerCase().replace(/^www\./, "");
  const partes = segmentos(analizada);

  if (host === "youtu.be") {
    return partes[0] ? `https://www.youtube.com/embed/${partes[0]}` : null;
  }

  if (host !== "youtube.com" && host !== "m.youtube.com") return null;

  if (partes[0] === "watch") {
    const identificador = analizada.searchParams.get("v");
    return identificador
      ? `https://www.youtube.com/embed/${identificador}`
      : null;
  }

  if (partes[0] === "embed" || partes[0] === "shorts" || partes[0] === "live") {
    return partes[1] ? `https://www.youtube.com/embed/${partes[1]}` : null;
  }

  return null;
}

/** The identifier of a Vimeo video. */
function embebibleVimeo(analizada: URL): string | null {
  const host = analizada.hostname.toLowerCase();
  const partes = segmentos(analizada);

  if (host === "player.vimeo.com") {
    if (partes[0] === "video" && partes[1]) {
      return `https://player.vimeo.com/video/${partes[1]}`;
    }
    return null;
  }

  if (host === "vimeo.com" || host === "www.vimeo.com") {
    if (partes.length === 1 && /^\d+$/.test(partes[0])) {
      return `https://player.vimeo.com/video/${partes[0]}`;
    }
  }

  return null;
}

/** The identifier of a Dailymotion video. */
function embebibleDailymotion(analizada: URL): string | null {
  const host = analizada.hostname.toLowerCase();
  const partes = segmentos(analizada);

  if (host === "dai.ly") {
    return partes[0]
      ? `https://www.dailymotion.com/embed/video/${partes[0]}`
      : null;
  }

  if (host === "dailymotion.com" || host === "www.dailymotion.com") {
    if (partes[0] === "video" && partes[1]) {
      return `https://www.dailymotion.com/embed/video/${partes[1]}`;
    }
  }

  return null;
}

/** The identifier of a Streamable video. */
function embebibleStreamable(analizada: URL): string | null {
  const host = analizada.hostname.toLowerCase();
  const partes = segmentos(analizada);

  if (host !== "streamable.com" && host !== "www.streamable.com") return null;
  if (!partes[0]) return null;

  if (partes[0] === "e") {
    return partes[1] ? `https://streamable.com/e/${partes[1]}` : null;
  }

  return `https://streamable.com/e/${partes[0]}`;
}

/** The channel or the video of a Twitch stream. */
function embebibleTwitch(analizada: URL): string | null {
  const host = analizada.hostname.toLowerCase();
  const partes = segmentos(analizada);

  if (host !== "twitch.tv" && host !== "www.twitch.tv") return null;
  if (!partes[0]) return null;

  if (partes[0] === "videos") {
    return partes[1] ? `https://player.twitch.tv/?video=${partes[1]}` : null;
  }

  return `https://player.twitch.tv/?channel=${partes[0]}`;
}

/** A Facebook video published under the official page of the organisation. */
function embebibleFacebook(analizada: URL): string | null {
  const host = analizada.hostname.toLowerCase();
  const partes = segmentos(analizada);

  if (host !== "facebook.com" && host !== "www.facebook.com") return null;

  const esVideo = partes.includes("videos") || partes[0] === "watch";
  if (!esVideo) return null;

  return `https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(
    analizada.toString(),
  )}`;
}

/**
 * The address of the frame, when the address belongs to a known provider.
 *
 * The list of providers is HARDCODED here and it is never fed by the data:
 * an address that arrives from the server cannot widen it.
 */
function embebibleDe(analizada: URL): string | null {
  return (
    embebibleYouTube(analizada) ??
    embebibleVimeo(analizada) ??
    embebibleDailymotion(analizada) ??
    embebibleStreamable(analizada) ??
    embebibleTwitch(analizada) ??
    embebibleFacebook(analizada)
  );
}

/**
 * The address of the frame that reproduces the video, or `null` when the
 * address does not belong to a known provider.
 */
export function urlEmbebibleVideo(url: string): string | null {
  const analizada = analizar(url);
  if (!analizada) return null;

  return embebibleDe(analizada);
}

/**
 * How the address has to be shown.
 *
 * - `hls`: a live HLS stream (`.m3u8`) rendered in the native player.
 * - `archivo`: the browser plays a media file with its own control.
 * - `embebible`: a known provider: the address becomes a frame.
 * - `externo`: anything else: a real external link, never a frame.
 */
export function clasificarVideo(url: string): TipoVideo {
  const analizada = analizar(url);
  if (!analizada) return "externo";

  if (esHls(analizada)) return "hls";
  if (esArchivo(analizada)) return "archivo";
  if (embebibleDe(analizada) !== null) return "embebible";

  return "externo";
}
