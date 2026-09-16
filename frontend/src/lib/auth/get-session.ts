import { cookies } from "next/headers";
import { AUTH_COOKIE_NAME } from "@/infra/auth/cookies";
import { verifyAccessToken } from "@/infra/auth/jwt";

export async function getSession() {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  if (!token) return null;
  return await verifyAccessToken(token);
}
