"use client";

import { Hash, Mail, User as UserIcon, Users } from "lucide-react";
import { useEffect, useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuthStore } from "@/features/auth/store/auth.store";
import type { InscripcionPayload } from "../../schemas";
import { getPromociones } from "../../services/catalog.service";

export function Step1Responsable({
  form,
}: {
  form: UseFormReturn<InscripcionPayload>;
}) {
  const user = useAuthStore((s) => s.user);
  const {
    watch,
    setValue,
    formState: { errors },
  } = form;
  const [promociones, setPromociones] = useState<any[]>([]);

  useEffect(() => {
    getPromociones().then((res) => {
      if (res.success && res.data) setPromociones(res.data);
    });
  }, []);

  // Use empty string consistently to avoid Select uncontrolled/controlled warning
  const promocionId = watch("promocionId") ?? "";
  const fusionPromocionId = watch("fusionPromocionId");

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Responsable = usuario logueado (read-only summary) */}
      <Card className="border border-[#312e8e]/15 bg-[#f4f6fb] shadow-sm">
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-xl bg-[#312e8e] text-white">
              <UserIcon className="size-5" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-[#626195]">
                Responsable
              </p>
              <p className="font-black text-[#17214b]">
                {user?.nombres} {user?.apellidos}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-xl bg-[#312e8e] text-white">
              <Hash className="size-5" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-[#626195]">
                Documento
              </p>
              <p className="font-black text-[#17214b]">
                {user?.tipoDocumento}: {user?.numeroDocumento}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-xl bg-[#312e8e] text-white">
              <Mail className="size-5" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-[#626195]">
                Email
              </p>
              <p className="font-black text-[#17214b]">{user?.email}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Promoción */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label
            htmlFor="promocionId"
            className="flex items-center gap-2 text-sm font-semibold"
          >
            <Users className="size-4 text-[#312e8e]" /> Promoción
          </label>
          <Select
            value={promocionId || ""}
            onValueChange={(v) => setValue("promocionId", v)}
          >
            <SelectTrigger className="input-brand bg-white">
              <SelectValue placeholder="Selecciona tu promoción" />
            </SelectTrigger>
            <SelectContent>
              {promociones.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  {p.nombre || `Promoción ${p.anio}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.promocionId && (
            <p className="text-sm text-destructive">
              {errors.promocionId.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label
            htmlFor="fusionPromocionId"
            className="flex items-center gap-2 text-sm font-semibold"
          >
            <Users className="size-4 text-[#312e8e]" /> Fusión (opcional)
          </label>
          <Select
            value={fusionPromocionId ?? "none"}
            onValueChange={(v) =>
              setValue("fusionPromocionId", v === "none" ? null : v)
            }
          >
            <SelectTrigger className="input-brand bg-white">
              <SelectValue placeholder="Sin fusión" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Sin fusión</SelectItem>
              {promociones.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  {p.nombre || `Promoción ${p.anio}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}
