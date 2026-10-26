"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import type { AdminAlertGroup } from "../utils/admin.resumen.utils";
import { toneClasses } from "../utils/admin.tone";

export interface AdminAlertListProps {
  group: AdminAlertGroup;
}

/**
 * An attention list of the operational overview.
 *
 * Only the items with a positive count reach this component: the mapping
 * layer drops the empty ones, so the panel never shows a zero as if it were
 * an incident.
 *
 * An item whose meaning IS a filter of the backend is a LINK to the list,
 * already filtered. An item without an expressible filter stays plain text:
 * a link that opens an unfiltered list would promise something it cannot
 * deliver.
 */
export function AdminAlertList({ group }: AdminAlertListProps) {
  return (
    <section className="card-elevated p-5 sm:p-6">
      <header className="mb-4">
        <h3 className="text-sm font-black uppercase tracking-wider text-slate-700">
          {group.title}
        </h3>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">
          {group.description}
        </p>
      </header>

      <ul className="flex flex-col gap-2">
        {group.items.map((item) => {
          const tones = toneClasses(item.tone);

          const cuerpo = (
            <>
              <div className="min-w-0">
                <p className="text-sm font-bold text-slate-800">{item.label}</p>
                <p className="mt-0.5 text-xs text-slate-500">{item.detail}</p>
              </div>
              <span
                className={cn(
                  "shrink-0 rounded-full border bg-white px-2.5 py-0.5 text-sm font-black",
                  tones.border,
                  tones.value,
                )}
              >
                {item.value}
              </span>
            </>
          );

          return (
            <li
              key={item.id}
              className={cn(
                "rounded-2xl border px-4 py-3",
                tones.soft,
                tones.border,
              )}
            >
              {item.ruta ? (
                <Link
                  href={item.ruta}
                  className="flex items-start justify-between gap-3 rounded-xl focus-visible:ring-2 focus-visible:ring-[#312e8e]/40 focus-visible:ring-offset-2 focus-visible:outline-none"
                >
                  {cuerpo}
                </Link>
              ) : (
                <div className="flex items-start justify-between gap-3">
                  {cuerpo}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
