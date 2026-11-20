import { AlertTriangle, Lock, RefreshCw, ServerCrash } from "lucide-react";
import type { ReactNode } from "react";
import {
  Alert,
  AlertAction,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";

/**
 * The states every route must be able to show.
 *
 * They live here so the 38 routes of the plan cannot invent five different
 * grammars of "something went wrong". Each state offers the action that
 * resolves it - an error that cannot be acted on is a dead end.
 */

export interface ShellStateProps {
  title: string;
  description?: ReactNode;
  /** The action that resolves the state. */
  accion?: { label: string; onClick?: () => void; href?: string };
  className?: string;
}

/**
 * The recoverable error.
 *
 * The message comes from the backend and is shown verbatim: the interface
 * never rewrites, translates or patches it by code. What the interface owns is
 * the DIFFERENCE between the failures, because the next action differs.
 */
export function ShellErrorState({
  title = "No pudimos cargar esta información",
  description,
  accion,
  className,
}: ShellStateProps) {
  return (
    <Alert variant="destructive" className={className}>
      <ServerCrash className="size-5" aria-hidden="true" />
      <AlertTitle>{title}</AlertTitle>
      {description ? <AlertDescription>{description}</AlertDescription> : null}
      {accion ? (
        <AlertAction className="mt-3">
          <Button
            variant="outline"
            size="sm"
            className="min-h-11"
            onClick={accion.onClick}
          >
            <RefreshCw className="size-4" aria-hidden="true" />
            {accion.label}
          </Button>
        </AlertAction>
      ) : null}
    </Alert>
  );
}

/**
 * The empty state.
 *
 * It says what does not exist and offers the action that creates it. An empty
 * screen without an action is a dead end.
 */
export function ShellEmptyState({
  title,
  description,
  accion,
  className,
}: ShellStateProps) {
  return (
    <Empty className={className}>
      <EmptyHeader>
        <EmptyTitle>{title}</EmptyTitle>
        {description ? (
          <EmptyDescription>{description}</EmptyDescription>
        ) : null}
      </EmptyHeader>
      {accion ? (
        <EmptyContent>
          <Button size="sm" className="min-h-11" onClick={accion.onClick}>
            {accion.label}
          </Button>
        </EmptyContent>
      ) : null}
    </Empty>
  );
}

/**
 * The permission state.
 *
 * The 403 of the backend is the control. This component only explains that
 * the account lacks the permission - it never proposes a way around it.
 */
export function ShellPermissionDenied({
  title = "No tienes permiso para ver esto",
  description = "Tu cuenta no tiene la capacidad necesaria para abrir esta sección. Si crees que es un error, contacta con la organización del evento.",
  className,
}: ShellStateProps) {
  return (
    <Alert variant="destructive" className={className}>
      <Lock className="size-5" aria-hidden="true" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>{description}</AlertDescription>
    </Alert>
  );
}

/**
 * The "still working" state.
 *
 * It never invents a remaining time: the backend owns it.
 */
export function ShellPendingState({
  title = "Procesando…",
  description,
  className,
}: ShellStateProps) {
  return (
    <Alert className={className}>
      <AlertTriangle className="size-5" aria-hidden="true" />
      <AlertTitle>{title}</AlertTitle>
      {description ? <AlertDescription>{description}</AlertDescription> : null}
    </Alert>
  );
}
