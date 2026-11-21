import { permanentRedirect } from "next/navigation";

/**
 * Legacy public route retained for existing shared links.
 */
export default function Page() {
  permanentRedirect("/en-vivo");
}
