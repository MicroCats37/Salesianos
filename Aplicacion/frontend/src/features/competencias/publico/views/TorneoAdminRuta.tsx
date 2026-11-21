"use client";

import { Check, Clock3, Flag, MapPin, Save, Trophy, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { useEncuentrosPublicos } from "../hooks/useEncuentrosPublicos";
import { useEncuentrosPublicosRealtime } from "../hooks/useEncuentrosPublicosRealtime";
import {
  useControlarPartidoTorneo,
  useGuardarGrupoTorneo,
  useGuardarLlaveTorneo,
} from "../hooks/useTorneoAdmin";
import {
  type PartidoTorneoFormData,
  partidoTorneoFormSchema,
} from "../schemas/torneo-admin.schema";
import type { PartidoTorneo } from "../schemas/torneo-publico.schema";
import {
  type PartidoDraft,
  partidoDraft,
} from "../services/torneo-admin.service";

type Tab = "groups" | "bracket" | "courts";

const ALL_COURTS = "__all__";
const UNASSIGNED_COURT = "__unassigned__";
const courtCollator = new Intl.Collator("es-PE", {
  numeric: true,
  sensitivity: "base",
});

function courtValue(match: PartidoTorneo) {
  return match.court?.trim() || UNASSIGNED_COURT;
}

function courtLabel(court: string) {
  if (court === UNASSIGNED_COURT) return "Sin cancha asignada";
  return /^cancha\b/i.test(court) ? court : `Cancha ${court}`;
}

export function TorneoAdminRuta() {
  const [competitionId, setCompetitionId] = useState<string>();
  const query = useEncuentrosPublicos(competitionId);
  const realtime = useEncuentrosPublicosRealtime();
  const guardarGrupo = useGuardarGrupoTorneo();
  const guardarLlave = useGuardarLlaveTorneo();
  const controlarPartido = useControlarPartidoTorneo();
  const [tab, setTab] = useState<Tab>("groups");
  const [groupId, setGroupId] = useState("A");
  const [matchId, setMatchId] = useState("round16-1");
  const [courtFilter, setCourtFilter] = useState(ALL_COURTS);
  const [drafts, setDrafts] = useState<PartidoDraft[]>([]);
  const data = query.data;
  const group =
    data?.groups.find((item) => item.id === groupId) ?? data?.groups[0];
  const knockout =
    data?.knockout.find((item) => item.id === matchId) ?? data?.knockout[0];
  const all: PartidoTorneo[] = data
    ? [...data.groups.flatMap((item) => item.matches), ...data.knockout]
    : [];

  useEffect(() => {
    setDrafts(
      data
        ? [
            ...data.groups.flatMap((item) => item.matches),
            ...data.knockout,
          ].map(partidoDraft)
        : [],
    );
  }, [data]);

  if (query.isPending) return <p className="p-8">Cargando mesa de control…</p>;
  if (!data || !group)
    return <p className="p-8 text-destructive">No se pudo cargar el torneo.</p>;

  const busy =
    guardarGrupo.isPending ||
    guardarLlave.isPending ||
    controlarPartido.isPending;
  const updateDraft = (
    id: string,
    field: keyof PartidoDraft,
    value: string | number | null,
  ) =>
    setDrafts((current) =>
      current.map((draft) =>
        draft.id === id ? { ...draft, [field]: value } : draft,
      ),
    );
  const draftFor = (match: PartidoTorneo) =>
    drafts.find((item) => item.id === match.id) ?? partidoDraft(match);
  const groupDrafts = group.matches.map(draftFor);
  const knockoutDraft = knockout ? draftFor(knockout) : null;
  const courtOptions = Array.from(new Set(all.map(courtValue))).sort(
    (left, right) => {
      if (left === UNASSIGNED_COURT) return 1;
      if (right === UNASSIGNED_COURT) return -1;
      return courtCollator.compare(left, right);
    },
  );
  const visibleCourtGroups = courtOptions
    .filter((court) => courtFilter === ALL_COURTS || court === courtFilter)
    .map((court) => ({
      court,
      matches: all.filter((match) => courtValue(match) === court),
    }));
  const competitionContext = [
    data.discipline,
    data.category,
    data.date
      ? new Intl.DateTimeFormat("es-PE", {
          day: "2-digit",
          month: "long",
          year: "numeric",
          timeZone: "America/Lima",
        }).format(new Date(`${data.date}T00:00:00-05:00`))
      : undefined,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <main className="min-h-screen bg-surface px-4 py-8 text-foreground sm:px-6">
      <div className="mx-auto max-w-container-admin">
        <header className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <span className="text-xs font-black tracking-[.18em] text-primary">
              MESA DE CONTROL · {data.tournament}
            </span>
            <h1 className="mt-1 font-heading text-4xl font-black uppercase sm:text-5xl">
              Jornada en vivo
            </h1>
            <p className="mt-2 text-sm text-foreground-muted">
              {competitionContext || "Contexto de competencia por confirmar"}
            </p>
            <p
              aria-live="polite"
              className="mt-2 text-xs font-bold text-success"
            >
              {realtime.estado === "conectado"
                ? "En vivo conectado: los cambios publicados se actualizan automáticamente."
                : "Reconectando actualizaciones en vivo..."}
            </p>
          </div>
          <a
            href="/partidos"
            className="rounded-lg border border-border bg-surface-raised px-5 py-3 text-sm font-black shadow-sm transition-colors hover:bg-muted"
          >
            Vista pública
          </a>
        </header>
        {data.competitions.length > 1 ? (
          <label className="mt-6 block max-w-md text-xs font-black text-foreground-muted">
            COMPETENCIA
            <select
              value={data.competition_id ?? ""}
              onChange={(event) => {
                setCourtFilter(ALL_COURTS);
                setCompetitionId(event.target.value);
              }}
              className="mt-2 min-h-11 w-full rounded-lg border border-input bg-surface-raised px-3 text-sm font-bold text-foreground"
            >
              {data.competitions.map((competition) => (
                <option key={competition.id} value={competition.id}>
                  {competition.discipline} · {competition.category} ·{" "}
                  {competition.name}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Stat icon={Users} label="GRUPOS" value={data.groups.length} />
          <Stat
            icon={Clock3}
            label="EN JUEGO"
            value={
              all.filter((item) =>
                ["live", "halftime", "extra", "penalties"].includes(
                  item.status,
                ),
              ).length
            }
          />
          <Stat
            icon={Flag}
            label="FINALIZADOS"
            value={all.filter((item) => item.status === "final").length}
          />
          <Stat icon={Trophy} label="PARTIDOS TOTALES" value={all.length} />
        </div>
        <div className="mt-8 flex overflow-x-auto border-b border-border">
          <button
            type="button"
            onClick={() => setTab("groups")}
            className={`min-h-12 shrink-0 border-b-2 px-5 font-black ${tab === "groups" ? "border-primary text-primary" : "border-transparent text-foreground-muted"}`}
          >
            Fase de grupos
          </button>
          {data.knockout.length > 0 ? (
            <button
              type="button"
              onClick={() => setTab("bracket")}
              className={`min-h-12 shrink-0 border-b-2 px-5 font-black ${tab === "bracket" ? "border-primary text-primary" : "border-transparent text-foreground-muted"}`}
            >
              Llaves finales
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => setTab("courts")}
            className={`min-h-12 shrink-0 border-b-2 px-5 font-black ${tab === "courts" ? "border-primary text-primary" : "border-transparent text-foreground-muted"}`}
          >
            Por canchas
          </button>
        </div>
        {tab === "groups" ? (
          <div className="mt-6 grid gap-6 lg:grid-cols-[220px_1fr]">
            <aside className="flex gap-2 overflow-x-auto rounded-xl border border-border bg-surface-recessed p-3 lg:flex-col">
              {data.groups.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setGroupId(item.id)}
                  className={`min-w-24 rounded-lg p-3 text-left font-black transition-colors ${group.id === item.id ? "bg-primary text-primary-foreground" : "bg-surface-raised hover:bg-muted"}`}
                >
                  {item.label}
                  <small className="block font-normal">
                    {item.matches.length} partidos
                  </small>
                </button>
              ))}
            </aside>
            <section>
              <div className="mb-5 flex items-end justify-between">
                <div>
                  <span className="text-xs font-black text-primary">
                    EDITANDO FASE DE GRUPOS
                  </span>
                  <h2 className="font-heading text-5xl font-black uppercase">
                    {group.label}
                  </h2>
                </div>
                <span className="text-xs text-foreground-muted">
                  VERSIÓN {group.revision + 1}
                </span>
              </div>
              <div className="space-y-4">
                {group.matches.map((match, index) => (
                  <MatchEditor
                    key={match.id}
                    match={match}
                    draft={draftFor(match)}
                    teams={group.teams}
                    number={index + 1}
                    busy={busy}
                    onChange={(field, value) =>
                      updateDraft(match.id, field, value)
                    }
                    onSave={(nextDraft) =>
                      guardarGrupo.mutateAsync({
                        id: group.id,
                        data: {
                          revision: group.revision,
                          matches: groupDrafts.map((item) =>
                            item.id === nextDraft.id ? nextDraft : item,
                          ),
                        },
                      })
                    }
                    onAction={(action, winner, decision) =>
                      controlarPartido.mutateAsync({
                        id: match.id,
                        data: {
                          action,
                          winner_id: winner,
                          decision,
                        },
                      })
                    }
                  />
                ))}
              </div>
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void guardarGrupo.mutate({
                    id: group.id,
                    data: { revision: group.revision, matches: groupDrafts },
                  })
                }
                className="mt-5 flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-primary font-black text-primary-foreground transition-colors hover:bg-primary-hover disabled:opacity-50"
              >
                <Save className="size-4" />
                Actualizar grupo
              </button>
            </section>
          </div>
        ) : tab === "bracket" && knockout ? (
          <div className="mt-6 grid gap-6 lg:grid-cols-[240px_1fr]">
            <aside className="flex gap-2 overflow-x-auto rounded-xl border border-border bg-surface-recessed p-3 lg:flex-col">
              {data.knockout.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setMatchId(item.id)}
                  className={`min-w-36 rounded-lg p-3 text-left text-xs font-black transition-colors ${knockout.id === item.id ? "bg-primary text-primary-foreground" : "bg-surface-raised hover:bg-muted"}`}
                >
                  {item.title || `${item.stage} · ${item.position + 1}`}
                  <small className="block truncate font-normal">
                    {item.home_name} vs {item.away_name}
                  </small>
                </button>
              ))}
            </aside>
            <section>
              <h2 className="mb-5 font-heading text-5xl font-black uppercase">
                {knockout.title || `Llave · Partido ${knockout.position + 1}`}
              </h2>
              {knockoutDraft ? (
                <MatchEditor
                  match={knockout}
                  draft={knockoutDraft}
                  teams={data.teams ?? []}
                  number={knockout.position + 1}
                  busy={busy}
                  onChange={(field, value) =>
                    updateDraft(knockout.id, field, value)
                  }
                  onSave={(nextDraft) =>
                    guardarLlave.mutateAsync({
                      id: nextDraft.id,
                      data: nextDraft,
                    })
                  }
                  onAction={(action, winner, decision) =>
                    controlarPartido.mutateAsync({
                      id: knockout.id,
                      data: {
                        action,
                        winner_id: winner,
                        decision,
                      },
                    })
                  }
                />
              ) : null}
              <button
                type="button"
                disabled={busy || !knockoutDraft}
                onClick={() =>
                  knockoutDraft &&
                  void guardarLlave.mutate({
                    id: knockoutDraft.id,
                    data: knockoutDraft,
                  })
                }
                className="mt-5 flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-primary font-black text-primary-foreground transition-colors hover:bg-primary-hover disabled:opacity-50"
              >
                <Save className="size-4" />
                Actualizar partido
              </button>
            </section>
          </div>
        ) : tab === "bracket" ? (
          <div className="mt-6 rounded-xl border border-dashed border-border bg-surface-recessed p-8 text-center">
            <Trophy className="mx-auto size-8 text-foreground-muted" />
            <h2 className="mt-3 font-heading text-2xl font-black uppercase">
              Esta competencia no tiene llaves finales
            </h2>
            <p className="mt-2 text-sm text-foreground-muted">
              Administra sus encuentros desde la fase de grupos.
            </p>
          </div>
        ) : (
          <section className="mt-6 space-y-6" aria-labelledby="courts-title">
            <div className="flex flex-col gap-4 rounded-xl border border-border bg-surface-recessed p-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <span className="text-xs font-black text-primary">
                  AGENDA OPERATIVA
                </span>
                <h2
                  id="courts-title"
                  className="font-heading text-4xl font-black uppercase sm:text-5xl"
                >
                  Partidos por cancha
                </h2>
                <p className="mt-1 text-sm text-foreground-muted">
                  Reúne fase de grupos y llaves para operar cada espacio sin
                  cambiar de grupo.
                </p>
              </div>
              <label className="block min-w-56 text-xs font-black text-foreground-muted">
                FILTRAR POR CANCHA
                <select
                  aria-label="Filtrar por cancha"
                  value={courtFilter}
                  onChange={(event) => setCourtFilter(event.target.value)}
                  className="mt-2 min-h-11 w-full rounded-lg border border-input bg-surface-raised px-3 text-sm font-bold text-foreground"
                >
                  <option value={ALL_COURTS}>Todas las canchas</option>
                  {courtOptions.map((court) => (
                    <option key={court} value={court}>
                      {courtLabel(court)}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {visibleCourtGroups.length > 0 ? (
              visibleCourtGroups.map(({ court, matches }) => (
                <section key={court} className="space-y-4">
                  <header className="flex flex-wrap items-end justify-between gap-2 border-b border-border pb-3">
                    <div className="flex items-center gap-3">
                      <span className="grid size-10 place-items-center rounded-full bg-primary text-primary-foreground">
                        <MapPin className="size-5" aria-hidden="true" />
                      </span>
                      <div>
                        <h3 className="font-heading text-3xl font-black uppercase">
                          {courtLabel(court)}
                        </h3>
                        <p className="text-xs text-foreground-muted">
                          {matches.length}{" "}
                          {matches.length === 1 ? "partido" : "partidos"}
                        </p>
                      </div>
                    </div>
                  </header>
                  <div className="space-y-4">
                    {matches.map((match) => {
                      const ownerGroup = data.groups.find((item) =>
                        item.matches.some(
                          (candidate) => candidate.id === match.id,
                        ),
                      );
                      const number = ownerGroup
                        ? ownerGroup.matches.findIndex(
                            (candidate) => candidate.id === match.id,
                          ) + 1
                        : match.position + 1;

                      return (
                        <MatchEditor
                          key={match.id}
                          match={match}
                          draft={draftFor(match)}
                          teams={ownerGroup?.teams ?? data.teams ?? []}
                          number={number}
                          context={
                            ownerGroup?.label ??
                            match.title ??
                            `Llave · ${match.stage}`
                          }
                          busy={busy}
                          onChange={(field, value) =>
                            updateDraft(match.id, field, value)
                          }
                          onSave={(nextDraft) =>
                            ownerGroup
                              ? guardarGrupo.mutateAsync({
                                  id: ownerGroup.id,
                                  data: {
                                    revision: ownerGroup.revision,
                                    matches: ownerGroup.matches.map(
                                      (candidate) =>
                                        candidate.id === nextDraft.id
                                          ? nextDraft
                                          : draftFor(candidate),
                                    ),
                                  },
                                })
                              : guardarLlave.mutateAsync({
                                  id: nextDraft.id,
                                  data: nextDraft,
                                })
                          }
                          onAction={(action, winner, decision) =>
                            controlarPartido.mutateAsync({
                              id: match.id,
                              data: {
                                action,
                                winner_id: winner,
                                decision,
                              },
                            })
                          }
                        />
                      );
                    })}
                  </div>
                </section>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-border bg-surface-recessed p-8 text-center">
                <MapPin className="mx-auto size-8 text-foreground-muted" />
                <h3 className="mt-3 font-heading text-2xl font-black uppercase">
                  No hay partidos en esta cancha
                </h3>
                <p className="mt-2 text-sm text-foreground-muted">
                  Elige otra cancha o vuelve a mostrar todas.
                </p>
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Users;
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface-raised p-5 shadow-sm">
      <div className="flex items-center gap-2 text-primary">
        <Icon className="size-5" />
        <span className="text-[10px] font-black tracking-[.12em]">{label}</span>
      </div>
      <strong className="mt-3 block font-heading text-5xl">
        {String(value).padStart(2, "0")}
      </strong>
    </div>
  );
}
function MatchEditor({
  match,
  draft,
  teams,
  number,
  context,
  busy,
  onChange,
  onSave,
  onAction,
}: {
  match: PartidoTorneo;
  draft: PartidoDraft;
  teams: { id: string; name: string }[];
  number: number;
  context?: string;
  busy: boolean;
  onChange: (field: keyof PartidoDraft, value: string | number | null) => void;
  onSave: (draft: PartidoTorneoFormData) => Promise<unknown>;
  onAction: (
    action: string,
    winner?: string | null,
    decision?: string | null,
  ) => Promise<unknown>;
}) {
  const form = useForm<PartidoTorneoFormData>({ defaultValues: draft });
  const [decision, setDecision] = useState("");
  const [winner, setWinner] = useState("");
  const change = (field: keyof PartidoDraft, value: string | number | null) => {
    form.setValue(field, value as never, { shouldDirty: true });
    onChange(field, value);
  };
  const canFinish =
    draft.home_score !== null &&
    draft.away_score !== null &&
    draft.home_id !== null &&
    draft.away_id !== null &&
    (decision !== "manual" || winner !== "");

  return (
    <GenericForm<PartidoTorneoFormData>
      formMethods={form}
      schema={partidoTorneoFormSchema}
      initialData={draft}
      onSubmit={onSave}
      isLoading={busy}
      skipFooter
      formClassName="space-y-0"
    >
      {({ isSubmitting, submissionMessage }) => (
        <article className="overflow-hidden rounded-xl border border-border bg-surface-raised shadow-sm">
          <div className="flex justify-between gap-4 border-b border-border bg-surface-recessed p-4">
            <div>
              <strong>PARTIDO {number}</strong>
              {context ? (
                <small className="mt-0.5 block text-xs font-medium text-foreground-muted">
                  {context}
                </small>
              ) : null}
            </div>
            <span className="text-xs font-black uppercase text-primary">
              {match.status}
            </span>
          </div>
          <div className="grid items-center gap-4 p-4 md:grid-cols-[1fr_auto_1fr]">
            <select
              aria-label="Equipo local"
              value={draft.home_id ?? ""}
              onChange={(event) =>
                change("home_id", event.target.value || null)
              }
              className="min-h-11 rounded-lg border border-input bg-background px-3"
            >
              <option value="">{match.home_name}</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
            <div className="flex items-center gap-2">
              <input
                aria-label="Marcador local"
                type="number"
                min="0"
                value={draft.home_score ?? ""}
                onChange={(event) =>
                  change(
                    "home_score",
                    event.target.value === ""
                      ? null
                      : Number(event.target.value),
                  )
                }
                className="h-12 w-16 rounded-lg border border-input bg-background text-center text-xl font-black"
              />
              <span>:</span>
              <input
                aria-label="Marcador visitante"
                type="number"
                min="0"
                value={draft.away_score ?? ""}
                onChange={(event) =>
                  change(
                    "away_score",
                    event.target.value === ""
                      ? null
                      : Number(event.target.value),
                  )
                }
                className="h-12 w-16 rounded-lg border border-input bg-background text-center text-xl font-black"
              />
            </div>
            <select
              aria-label="Equipo visitante"
              value={draft.away_id ?? ""}
              onChange={(event) =>
                change("away_id", event.target.value || null)
              }
              className="min-h-11 rounded-lg border border-input bg-background px-3"
            >
              <option value="">{match.away_name}</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-3 border-t border-border p-4 sm:grid-cols-3">
            <label className="text-[10px] font-black text-foreground-muted">
              HORA
              <input
                type="time"
                value={localTime(draft.scheduled_at)}
                onChange={(event) =>
                  change(
                    "scheduled_at",
                    withLocalTime(draft.scheduled_at, event.target.value),
                  )
                }
                className="mt-1 min-h-11 w-full rounded-lg border border-input bg-background px-3 text-sm"
              />
            </label>
            <label className="text-[10px] font-black text-foreground-muted">
              CANCHA
              <input
                value={draft.court ?? ""}
                onChange={(event) =>
                  change("court", event.target.value || null)
                }
                className="mt-1 min-h-11 w-full rounded-lg border border-input bg-background px-3 text-sm"
              />
            </label>
            <label className="text-[10px] font-black text-foreground-muted">
              DURACIÓN (MIN)
              <input
                type="number"
                min="1"
                value={draft.duration_minutes}
                onChange={(event) =>
                  change("duration_minutes", Number(event.target.value))
                }
                className="mt-1 min-h-11 w-full rounded-lg border border-input bg-background px-3 text-sm"
              />
            </label>
          </div>
          <div className="flex flex-wrap gap-2 border-t border-border p-4">
            {match.status === "scheduled" ? (
              <ControlButton disabled={busy} onClick={() => onAction("start")}>
                Iniciar
              </ControlButton>
            ) : null}
            {["live", "extra"].includes(match.status) ? (
              <ControlButton
                disabled={busy}
                onClick={() => onAction("halftime")}
              >
                Pausar
              </ControlButton>
            ) : null}
            {["halftime", "penalties"].includes(match.status) ? (
              <ControlButton disabled={busy} onClick={() => onAction("resume")}>
                Reanudar
              </ControlButton>
            ) : null}
            {["live", "halftime", "penalties"].includes(match.status) ? (
              <ControlButton disabled={busy} onClick={() => onAction("extra")}>
                Tiempo extra
              </ControlButton>
            ) : null}
            {["live", "halftime", "extra"].includes(match.status) ? (
              <ControlButton
                disabled={busy}
                onClick={() => onAction("penalties")}
              >
                Ir a penales
              </ControlButton>
            ) : null}
            {match.status !== "final" ? (
              <div className="flex w-full flex-wrap items-end gap-2 border-t border-border pt-4">
                <label className="text-[10px] font-black text-foreground-muted">
                  DEFINICIÓN
                  <select
                    value={decision}
                    onChange={(event) => setDecision(event.target.value)}
                    className="mt-1 block min-h-11 rounded-lg border border-input bg-background px-3 text-sm"
                  >
                    <option value="">Según marcador / empate</option>
                    <option value="penalties">Penales</option>
                    <option value="manual">Ganador elegido</option>
                  </select>
                </label>
                {decision === "penalties" ? (
                  <div className="flex items-center gap-2">
                    <input
                      aria-label="Penales local"
                      type="number"
                      min="0"
                      value={draft.home_penalties ?? ""}
                      onChange={(event) =>
                        change(
                          "home_penalties",
                          event.target.value === ""
                            ? null
                            : Number(event.target.value),
                        )
                      }
                      className="h-11 w-16 rounded-lg border border-input bg-background text-center"
                    />
                    <span>:</span>
                    <input
                      aria-label="Penales visitante"
                      type="number"
                      min="0"
                      value={draft.away_penalties ?? ""}
                      onChange={(event) =>
                        change(
                          "away_penalties",
                          event.target.value === ""
                            ? null
                            : Number(event.target.value),
                        )
                      }
                      className="h-11 w-16 rounded-lg border border-input bg-background text-center"
                    />
                  </div>
                ) : null}
                {decision === "manual" ? (
                  <select
                    aria-label="Ganador"
                    value={winner}
                    onChange={(event) => setWinner(event.target.value)}
                    className="min-h-11 rounded-lg border border-input bg-background px-3 text-sm"
                  >
                    <option value="">Elegir ganador</option>
                    <option value={draft.home_id ?? ""}>
                      {teams.find((team) => team.id === draft.home_id)?.name ??
                        "Equipo A"}
                    </option>
                    <option value={draft.away_id ?? ""}>
                      {teams.find((team) => team.id === draft.away_id)?.name ??
                        "Equipo B"}
                    </option>
                  </select>
                ) : null}
                <ControlButton
                  disabled={busy || !canFinish}
                  onClick={() =>
                    onAction("finish", winner || null, decision || null)
                  }
                >
                  <Check className="size-4" />
                  Finalizar
                </ControlButton>
              </div>
            ) : (
              <ControlButton disabled={busy} onClick={() => onAction("reopen")}>
                Reabrir
              </ControlButton>
            )}
          </div>
          <div className="flex items-center justify-between gap-3 border-t border-border p-4">
            <output
              aria-live="polite"
              className="text-sm text-foreground-muted"
            >
              {submissionMessage?.message ??
                "Los cambios se publicarán al guardar."}
            </output>
            <button
              type="submit"
              disabled={busy || isSubmitting}
              className="min-h-11 rounded-lg bg-primary px-4 text-sm font-black text-primary-foreground disabled:opacity-50"
            >
              {isSubmitting ? "Guardando..." : "Guardar partido"}
            </button>
          </div>
        </article>
      )}
    </GenericForm>
  );
}
function localTime(value: string | null) {
  if (!value) return "";
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "America/Lima",
  }).format(new Date(value));
}
function withLocalTime(existing: string | null, time: string) {
  if (!time) return null;
  const source = existing
    ? new Date(existing)
    : new Date("2026-11-21T00:00:00-05:00");
  const parts = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "America/Lima",
  }).formatToParts(source);
  const part = (key: string) =>
    parts.find((item) => item.type === key)?.value ?? "";
  return new Date(
    `${part("year")}-${part("month")}-${part("day")}T${time}:00-05:00`,
  ).toISOString();
}
function ControlButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      {...props}
      className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-border bg-surface-raised px-4 text-xs font-black transition-colors hover:bg-muted disabled:opacity-50"
    >
      {children}
    </button>
  );
}
