"use client";

import { useEffect, useState } from "react";
import { FESTIVAL } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";
import { cn } from "@/lib/utils";

interface Restante {
  dias: number;
  horas: number;
  minutos: number;
  etiqueta: string;
}

function calcularRestante(): Restante {
  const inicio = new Date(FESTIVAL.inicio).getTime();
  const fin = new Date(FESTIVAL.fin).getTime();
  const ahora = Date.now();

  if (ahora >= fin) {
    return {
      dias: 0,
      horas: 0,
      minutos: 0,
      etiqueta: COPY.hero.pie.countdownDespues,
    };
  }
  if (ahora >= inicio) {
    return {
      dias: 0,
      horas: 0,
      minutos: 0,
      etiqueta: COPY.hero.pie.countdownDurante,
    };
  }

  const diferencia = inicio - ahora;
  return {
    dias: Math.floor(diferencia / 86_400_000),
    horas: Math.floor(diferencia / 3_600_000) % 24,
    minutos: Math.floor(diferencia / 60_000) % 60,
    etiqueta: COPY.hero.pie.countdownAntes,
  };
}

/**
 * Cuenta regresiva al festival.
 *
 * Tres bloques (días / horas / minutos) que se refrescan cada 30 segundos.
 * Con movimiento reducido el número sigue actualizando: solo se acota la
 * animación.
 */
export function Countdown({ className }: { className?: string }) {
  // El valor se calcula DESPUÉS de montar: si se calculara durante el render,
  // el servidor y el cliente podrían diferir en un minuto y romper la
  // hidratación.
  const [restante, setRestante] = useState<Restante | null>(null);

  useEffect(() => {
    const actualizar = () => setRestante(calcularRestante());
    actualizar();
    const intervalo = setInterval(actualizar, 30_000);
    return () => clearInterval(intervalo);
  }, []);

  const dias = restante?.dias;
  const horas = restante?.horas;
  const minutos = restante?.minutos;
  const etiquetaActual = restante?.etiqueta ?? COPY.hero.pie.countdownAntes;

  const bloques = [
    { valor: dias, etiqueta: "DÍAS" },
    { valor: horas, etiqueta: "HORAS" },
    { valor: minutos, etiqueta: "MIN" },
  ];

  return (
    <div
      className={cn("flex flex-col items-center gap-2", className)}
      role="timer"
      aria-live="off"
    >
      <span className="sr-only">
        {restante
          ? `${restante.etiqueta} ${restante.dias} días, ${restante.horas} horas y ${restante.minutos} minutos para el festival.`
          : "Cuenta regresiva para el festival."}
      </span>
      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#626195]">
        {etiquetaActual}
      </span>
      <div className="flex items-center gap-2">
        {bloques.map((bloque, index) => (
          <div key={bloque.etiqueta} className="flex items-center gap-2">
            {index > 0 && (
              <span
                className="text-xl font-black text-[#312e8e]/30"
                aria-hidden="true"
              >
                :
              </span>
            )}
            <div className="flex flex-col items-center">
              <span className="text-3xl font-black tabular-nums leading-none text-[#17214b] sm:text-4xl lg:text-5xl">
                {bloque.valor === undefined
                  ? "--"
                  : String(bloque.valor).padStart(2, "0")}
              </span>
              <span className="mt-1 text-[9px] font-black uppercase tracking-[0.15em] text-[#626195]">
                {bloque.etiqueta}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
