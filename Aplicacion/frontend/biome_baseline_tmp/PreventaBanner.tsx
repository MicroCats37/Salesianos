import Image from "next/image";
import { cn } from "@/lib/utils";

interface PreventaBannerProps {
  titulo: string;
  palabraDestacada: string;
  variant: "PACKS" | "DISCIPLINA";
  className?: string;
}

export function PreventaBanner({
  titulo,
  palabraDestacada,
  variant,
  className,
}: PreventaBannerProps) {
  return (
    <div
      className={cn("relative isolate overflow-hidden bg-[#0b3b86]", className)}
    >
      <div className="absolute inset-0" aria-hidden="true">
        {variant === "PACKS" ? (
          <>
            <div
              className="absolute inset-y-0 left-0 w-[58%] overflow-hidden"
              style={{
                clipPath: "polygon(0 0, 88% 0, 72% 100%, 0 100%)",
              }}
            >
              <Image
                src="/images/fulbito-varones.webp"
                alt=""
                fill
                sizes="58vw"
                className="object-cover saturate-150"
              />
            </div>
            <div
              className="absolute inset-y-0 left-[37%] w-[48%] overflow-hidden"
              style={{
                clipPath: "polygon(20% 0, 100% 0, 88% 100%, 8% 100%)",
              }}
            >
              <Image
                src="/images/voley-mixto.webp"
                alt=""
                fill
                sizes="48vw"
                className="object-cover saturate-150"
              />
            </div>
            <div
              className="absolute inset-y-0 left-[64%] w-[42%] overflow-hidden"
              style={{
                clipPath: "polygon(26% 0, 100% 0, 100% 100%, 10% 100%)",
              }}
            >
              <Image
                src="/images/basket-varones.webp"
                alt=""
                fill
                sizes="42vw"
                className="object-cover saturate-150"
              />
            </div>
          </>
        ) : (
          <Image
            src="/images/fulbito-varones.webp"
            alt=""
            fill
            sizes="100vw"
            className="object-cover saturate-150"
          />
        )}
      </div>

      <div
        className="absolute inset-0 bg-gradient-to-r from-[#0b2f78]/45 via-[#0d63ad]/35 to-[#0aa6c9]/30"
        aria-hidden="true"
      />

      {/* Vignette: keeps the label plate legible without flattening the photos. */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-[#0a2f70]/75 via-[#0a2f70]/10 to-transparent"
        aria-hidden="true"
      />

      <div className="relative z-10 flex min-h-[18rem] items-center justify-center px-4 py-14 sm:min-h-[22rem] lg:min-h-[26rem]">
        <div className="rounded-xl border border-sky-300/60 bg-gradient-to-br from-[#1e5fa8] to-[#1557b8] px-6 py-4 text-center shadow-2xl shadow-[#06285d]/40 sm:px-8 sm:py-5">
          <h2 className="flex flex-wrap items-baseline justify-center gap-x-3 text-4xl font-black uppercase tracking-tight text-white sm:text-5xl lg:text-6xl">
            <span>{titulo}</span>
            <span className="text-sky-300/80">{palabraDestacada}</span>
          </h2>
        </div>
      </div>

      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 z-20 h-28 bg-gradient-to-t from-[#eef4fb] to-transparent"
        aria-hidden="true"
      />
    </div>
  );
}
