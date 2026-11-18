import { cn } from "@/lib/utils";
import {
  DEFAULT_DISCIPLINA_COLOR,
  DISCIPLINA_COLORS,
  getDisciplinaColor,
} from "./paquete-copy";

export { DEFAULT_DISCIPLINA_COLOR, DISCIPLINA_COLORS, getDisciplinaColor };

const GLYPH_PATHS = {
  F7M: "M8.39 21L3 15.61c0 1.09.04 2.1.2 3.02c.15.92.3 1.47.51 1.66c.19.21.73.36 1.64.52s1.92.19 3.04.19M15.5 9.89L9.89 15.5L8.5 14.11l5.61-5.61zM3.29 13.08l7.63 7.63c2.78-.5 4.98-1.56 6.61-3.18c1.62-1.63 2.68-3.83 3.18-6.61l-7.63-7.63c-2.78.5-4.98 1.56-6.61 3.18s-2.68 3.83-3.18 6.61M15.61 3L21 8.39c0-1.09-.04-2.1-.19-3.02c-.16-.92-.31-1.47-.52-1.66c-.19-.21-.73-.36-1.64-.51S16.73 3 15.61 3",
  F7F: "M8.39 21L3 15.61c0 1.09.04 2.1.2 3.02c.15.92.3 1.47.51 1.66c.19.21.73.36 1.64.52s1.92.19 3.04.19M15.5 9.89L9.89 15.5L8.5 14.11l5.61-5.61zM3.29 13.08l7.63 7.63c2.78-.5 4.98-1.56 6.61-3.18c1.62-1.63 2.68-3.83 3.18-6.61l-7.63-7.63c-2.78.5-4.98 1.56-6.61 3.18s-2.68 3.83-3.18 6.61M15.61 3L21 8.39c0-1.09-.04-2.1-.19-3.02c-.16-.92-.31-1.47-.52-1.66c-.19-.21-.73-.36-1.64-.51S16.73 3 15.61 3",
  VOL: "M19.04 4.85C17.34 3.2 15.33 2.25 13 2v3.62l9 5.18c-.28-2.3-1.27-4.3-2.96-5.95M12 22c3.44 0 6.16-1.38 8.17-4.14L17.06 16l-8.99 5.2c1.25.53 2.57.8 3.93.8m1-10.59l8.15 4.66c.44-.94.73-1.93.85-2.96l-9-5.18zm-9.12 6.4c.66.91 1.38 1.65 2.17 2.19l8.99-5.1L12 13.15zM11.04 2C10 2.09 9 2.36 8 2.8v10.35l3.04-1.74zM2 12c0 1.39.3 2.77.89 4.12L6 14.28V4c-2.67 2-4 4.65-4 8",
  BAS: "M2.34 14.63c.6-.22 1.22-.33 1.88-.33q2.01 0 3.51 1.26L4.59 18.7a10.6 10.6 0 0 1-2.25-4.07M15.56 9.8c1.97 1.47 4.1 1.83 6.38 1.08c.03.21.06.59.06 1.12c0 1.03-.25 2.18-.72 3.45c-.47 1.26-1.05 2.28-1.73 3.05l-6.33-6.31zm-6.79 6.84c1.06 1.53 1.28 3.2.65 5.02c-1.42-.41-2.69-1.05-3.75-1.93zm3.42-3.42l6.31 6.33c-2.17 1.9-4.72 2.7-7.62 2.39c.21-.66.32-1.38.32-2.16c0-.62-.14-1.35-.42-2.18s-.61-1.51-.98-2.04zM8.81 14.5a6.7 6.7 0 0 0-3.23-1.59c-1.22-.23-2.39-.16-3.52.22c-.03-.22-.06-.6-.06-1.13c0-1.03.25-2.18.72-3.45c.47-1.26 1.05-2.28 1.73-3.05l6.66 6.69zm6.75-6.77c-1.34-1.65-1.65-3.45-.93-5.39c.62.16 1.33.46 2.13.92c.79.45 1.44.9 1.94 1.33zm6.1 1.65c-.6.21-1.22.32-1.88.32c-1.09 0-2.14-.32-3.14-.98l3.09-3.05c.88 1.1 1.52 2.33 1.93 3.71m-9.47 1.73L5.5 4.45c2.17-1.9 4.72-2.7 7.63-2.39q-.33.99-.33 2.16c0 .72.16 1.53.49 2.44c.33.9.71 1.62 1.21 2.15z",
} as const;

type Glifo = keyof typeof GLYPH_PATHS;

interface DisciplinaIconProps {
  sigla: string;
  className?: string;
  iconClassName?: string;
  label?: string;
}

export function DisciplinaIcon({
  sigla,
  className,
  iconClassName,
  label,
}: DisciplinaIconProps) {
  const clave = sigla.trim().toUpperCase();
  const glifo: Glifo =
    clave === "F7F" || clave === "VOL" || clave === "BAS" ? clave : "F7M";

  return (
    <span
      className={cn(
        "inline-flex size-11 shrink-0 items-center justify-center rounded-full border-2 border-white text-white shadow-sm",
        className,
      )}
      style={{ backgroundColor: getDisciplinaColor(clave) }}
      role="img"
      aria-label={label ?? "Disciplina deportiva"}
    >
      <svg
        className={cn("size-6 fill-current", iconClassName)}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path d={GLYPH_PATHS[glifo]} />
      </svg>
    </span>
  );
}
