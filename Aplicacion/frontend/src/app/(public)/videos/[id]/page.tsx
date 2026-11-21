import { permanentRedirect } from "next/navigation";

/**
 * Legacy public route retained for existing shared links.
 */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  permanentRedirect(`/en-vivo/${encodeURIComponent(id)}`);
}
