import { Suspense } from "react";
import { RegisterClientShell } from "@/features/auth/views";

export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <RegisterClientShell />
    </Suspense>
  );
}
