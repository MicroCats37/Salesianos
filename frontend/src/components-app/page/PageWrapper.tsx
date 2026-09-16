"use client";

import { ArrowLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface BreadcrumbItem {
  /** Etiqueta visible del paso */
  label: string;
  /** Si se omite, el item se renderiza como página actual (no link) */
  href?: string;
}

export interface PageWrapperProps {
  /** Page title displayed in the header */
  title: string;
  /** Optional description below the title */
  description?: string;
  /** Optional icon node (e.g., `<FileText className="h-6 w-6 text-primary" />`) rendered inside the wine icon container */
  icon?: React.ReactNode;
  /** Optional action nodes rendered on the right side of the header (e.g., "Nueva Solicitud" button) */
  actions?: React.ReactNode;
  /** Page content */
  children: React.ReactNode;
  /** Additional CSS classes for the `.app-page` container */
  className?: string;
  /** Optional href for the back button. When provided, a back arrow button appears left of the icon. Uses `router.push()` internally. */
  backHref?: string;
  /**
   * Optional breadcrumb trail that shows the current location inside the app.
   * Renders above the page header. Last item is rendered as the current page
   * (non-clickable). Earlier items become clickable links.
   */
  breadcrumbs?: BreadcrumbItem[];
}

/**
 * Corporate page shell component.
 *
 * Renders:
 * - `.app-page` container (`p-6 lg:p-8 space-y-6`)
 * - `.app-page-header` header block with:
 *   - Back button (if `backHref` is provided) → left of icon
 *   - Icon container + title + description → left side
 *   - `actions` → right side
 * - Content area (children)
 */
export function PageWrapper({
  title,
  description,
  icon,
  actions,
  children,
  className,
  backHref,
  breadcrumbs,
}: PageWrapperProps) {
  const router = useRouter();

  return (
    <div className={cn("app-page", className)}>
      {/* Breadcrumb trail */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav
          aria-label="Ruta de navegación"
          className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground"
        >
          {breadcrumbs.map((item, idx) => {
            const isLast = idx === breadcrumbs.length - 1;
            return (
              <span
                key={`${item.label}-${idx}`}
                className="inline-flex items-center gap-1.5"
              >
                {item.href && !isLast ? (
                  <Link
                    href={item.href}
                    className="hover:text-foreground transition-colors"
                  >
                    {item.label}
                  </Link>
                ) : (
                  <span
                    aria-current={isLast ? "page" : undefined}
                    className={cn(isLast && "font-semibold text-foreground")}
                  >
                    {item.label}
                  </span>
                )}
                {!isLast && (
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60" />
                )}
              </span>
            );
          })}
        </nav>
      )}

      {/* Header */}
      <div className="app-page-header">
        {/* Left side: back button + icon + title + description */}
        <div className="relative z-10 flex items-center gap-4">
          {backHref && (
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 p-2 h-9 w-9 shrink-0"
              onClick={() => router.push(backHref)}
              aria-label="Volver"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
          )}
          {icon && <div className="page-header-icon">{icon}</div>}
          <div className="min-w-0">
            <p className="page-header-eyebrow">Trámite Documentario</p>
            <h1 className="app-page-title">{title}</h1>
            {description && (
              <p className="text-sm font-medium text-muted-foreground">
                {description}
              </p>
            )}
          </div>
        </div>

        {/* Right side: actions */}
        {actions && (
          <div className="relative z-10 flex items-center gap-2 shrink-0">
            {actions}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="app-page-body">{children}</div>
    </div>
  );
}
