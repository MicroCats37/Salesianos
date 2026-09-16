"use client";

import { CreditCard, ShieldCheck, Trophy } from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { InscripcionPayload } from "../../schemas";

export function Step3Paquete({
  form,
}: {
  form: UseFormReturn<InscripcionPayload>;
}) {
  const deportistas = form.watch("deportistas") || [];

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Paquete */}
      <Card className="overflow-hidden border-0 shadow-2xl">
        <div className="bg-gradient-to-br from-[#312e8e] to-[#25236f] p-6 text-white">
          <div className="flex items-center gap-3">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
              <Trophy className="size-6 text-[#f4c64e]" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-white/70">
                Paquete Salesianos FEST
              </p>
              <p className="text-3xl font-black">S/ 1,350</p>
            </div>
          </div>
        </div>
        <CardContent className="space-y-4 p-6">
          <div className="flex items-center justify-between rounded-xl bg-[#f4f6fb] p-4">
            <span className="text-sm text-[#626195]">
              Deportistas en la nómina
            </span>
            <Badge className="bg-[#312e8e] text-white">
              {deportistas.length} deportista
              {deportistas.length === 1 ? "" : "s"}
            </Badge>
          </div>

          {/* izipay */}
          <div className="flex items-center gap-3 rounded-2xl border-2 border-[#312e8e]/15 bg-white p-4">
            <div className="flex size-11 items-center justify-center rounded-xl bg-[#312e8e]/10 text-[#312e8e]">
              <CreditCard className="size-5" />
            </div>
            <div className="flex-1">
              <p className="font-bold text-[#17214b]">Pasarela izipay</p>
              <p className="text-xs text-[#626195]">
                El cobro se habilitará después de la revisión del Comité.
              </p>
            </div>
            <Badge className="bg-[#f4c64e] text-[#17214b]">
              Próximo a habilitar
            </Badge>
          </div>

          <div className="flex items-start gap-3 rounded-xl bg-[#f4f6fb] p-4">
            <ShieldCheck className="size-5 shrink-0 text-[#312e8e]" />
            <p className="text-sm text-[#626195]">
              <strong className="text-[#17214b]">
                Monto sujeto a validación del Comité.
              </strong>{" "}
              La tarifa regular de las bases es S/ 1,350 por paquete. Anticipada
              y extemporánea pendientes de definición.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
