"use client";

import {
  Activity,
  AlertCircle,
  CheckCircle2,
  FileCheck,
  Image as ImageIcon,
} from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import type { InscripcionPayload } from "../../schemas";

export function Step4Declaraciones({
  form,
}: {
  form: UseFormReturn<InscripcionPayload>;
}) {
  const {
    watch,
    setValue,
    formState: { errors },
  } = form;

  const declarations = [
    {
      field: "fitnessDeclaration" as const,
      icon: Activity,
      title: "Declaración de aptitud física",
      desc: "Confirmo que todos los deportistas registrados se encuentran en condiciones físicas adecuadas para participar.",
    },
    {
      field: "imageConsent" as const,
      icon: ImageIcon,
      title: "Consentimiento de uso de imagen",
      desc: "Autorizo el uso de imágenes y videos de los participantes para fines promocionales del Salesianos FEST 2026.",
    },
    {
      field: "acceptedBases" as const,
      icon: FileCheck,
      title: "Aceptación de las bases oficiales",
      desc: "He leído y acepto los términos del documento BASES-SF26-2026-09-06.",
    },
  ];

  return (
    <div className="space-y-5 animate-fade-up">
      <div className="flex items-start gap-3 rounded-xl border-2 border-[#f4c64e]/40 bg-[#fff9df] p-4">
        <AlertCircle className="size-5 shrink-0 mt-0.5 text-[#f4c64e]" />
        <p className="text-sm font-bold text-[#17214b]">
          Último paso — debes confirmar las siguientes condiciones para enviar
          tu solicitud. Las bases deportivas finales podrán requerir una nueva
          aceptación si cambian las categorías o condiciones aplicables.
        </p>
      </div>

      {declarations.map(({ field, icon: Icon, title, desc }) => (
        <div
          key={field}
          className="flex items-start gap-3 rounded-xl border-2 border-[#312e8e]/15 bg-white p-4 shadow-sm"
        >
          <Checkbox
            id={field}
            checked={watch(field)}
            onCheckedChange={(checked) => setValue(field, !!checked)}
            aria-invalid={!!errors[field]}
            className="mt-0.5"
          />
          <div className="flex-1">
            <Label
              htmlFor={field}
              className="flex items-center gap-2 cursor-pointer font-bold leading-tight text-[#17214b]"
            >
              <Icon className="size-4 text-[#312e8e]" /> {title}
            </Label>
            <p className="mt-1 text-xs text-muted-foreground">{desc}</p>
          </div>
          {watch(field) && (
            <CheckCircle2 className="size-5 shrink-0 text-[#10b981]" />
          )}
        </div>
      ))}

      {errors.fitnessDeclaration && (
        <p className="text-sm text-destructive">
          {errors.fitnessDeclaration.message}
        </p>
      )}
      {errors.imageConsent && (
        <p className="text-sm text-destructive">
          {errors.imageConsent.message}
        </p>
      )}
      {errors.acceptedBases && (
        <p className="text-sm text-destructive">
          {errors.acceptedBases.message}
        </p>
      )}
    </div>
  );
}
