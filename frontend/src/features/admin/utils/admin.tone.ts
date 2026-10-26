import type { AdminTone } from "./admin.estado.utils";

/**
 * Tailwind classes of every admin tone.
 *
 * The palette is the one already established by the panel of the team
 * (brand indigo `#312e8e`, amber accents, slate surfaces), so the
 * administration area looks like a part of the same product and not like a
 * foreign dashboard.
 */
export interface AdminToneClasses {
  /** Background and text of the icon container. */
  icon: string;
  /** Text colour of the value. */
  value: string;
  /** Soft surface used by the chips and the decorative blob. */
  soft: string;
  /** Border colour of the chips. */
  border: string;
}

const TONE_CLASSES: Record<AdminTone, AdminToneClasses> = {
  brand: {
    icon: "bg-[#312e8e]/10 text-[#312e8e]",
    value: "text-[#17214b]",
    soft: "bg-[#312e8e]/10",
    border: "border-[#312e8e]/20",
  },
  emerald: {
    icon: "bg-emerald-500/10 text-emerald-600",
    value: "text-emerald-700",
    soft: "bg-emerald-500/10",
    border: "border-emerald-200",
  },
  cyan: {
    icon: "bg-cyan-500/10 text-cyan-600",
    value: "text-cyan-700",
    soft: "bg-cyan-500/10",
    border: "border-cyan-200",
  },
  violet: {
    icon: "bg-violet-500/10 text-violet-600",
    value: "text-violet-700",
    soft: "bg-violet-500/10",
    border: "border-violet-200",
  },
  orange: {
    icon: "bg-orange-500/10 text-orange-600",
    value: "text-orange-700",
    soft: "bg-orange-500/10",
    border: "border-orange-200",
  },
  amber: {
    icon: "bg-amber-500/10 text-amber-600",
    value: "text-amber-700",
    soft: "bg-amber-500/10",
    border: "border-amber-200",
  },
  rose: {
    icon: "bg-rose-500/10 text-rose-600",
    value: "text-rose-700",
    soft: "bg-rose-500/10",
    border: "border-rose-200",
  },
  red: {
    icon: "bg-red-500/10 text-red-600",
    value: "text-red-700",
    soft: "bg-red-500/10",
    border: "border-red-200",
  },
  blue: {
    icon: "bg-blue-500/10 text-blue-600",
    value: "text-blue-700",
    soft: "bg-blue-500/10",
    border: "border-blue-200",
  },
  slate: {
    icon: "bg-slate-500/10 text-slate-600",
    value: "text-slate-700",
    soft: "bg-slate-500/10",
    border: "border-slate-200",
  },
};

/** Classes of a tone. Unknown tones fall back to the neutral slate. */
export function toneClasses(tone: AdminTone): AdminToneClasses {
  return TONE_CLASSES[tone] ?? TONE_CLASSES.slate;
}
