"use client";

import {
  ArrowRight,
  CalendarDays,
  Clock3,
  Radio,
  Trophy,
  Users,
  Zap,
} from "lucide-react";
import { useState } from "react";
import {
  ShellErrorState,
  ShellPendingState,
} from "@/components/shell/ShellState";
import type {
  GrupoTorneo,
  PartidoTorneo,
  TorneoPublico,
} from "../schemas/torneo-publico.schema";

export type EstadoVistaEncuentrosPublicos =
  | "sin-datos"
  | "cargando"
  | "listo"
  | "error";
type Section = "overview" | "groups" | "schedule" | "bracket";

export interface EncuentrosPublicosViewProps {
  estado?: EstadoVistaEncuentrosPublicos;
  encuentros?: TorneoPublico;
  mensajeError?: string;
  actualizacionEnVivo?: Date | null;
  estadoRealtime?: "conectando" | "conectado" | "reconectando";
  seleccionarCompetencia?: (competitionId: string) => void;
  reintentar?: () => void;
}

const statusLabels: Record<PartidoTorneo["status"], string> = {
  scheduled: "Programado",
  live: "En juego",
  halftime: "Medio tiempo",
  extra: "Tiempo extra",
  penalties: "Penales",
  final: "Finalizado",
};

const stageLabels: Record<PartidoTorneo["stage"], string> = {
  group: "Fase de grupos",
  round16: "Octavos de final",
  quarter: "Cuartos de final",
  semi: "Semifinales",
  cross: "Cruces",
  final: "Final",
  third_place: "Tercer puesto",
};
const stageOrder: PartidoTorneo["stage"][] = [
  "round16",
  "quarter",
  "semi",
  "cross",
  "final",
  "third_place",
];

const isLive = (match: PartidoTorneo) =>
  ["live", "halftime", "extra", "penalties"].includes(match.status);
const scheduledSort = (a: PartidoTorneo, b: PartidoTorneo) =>
  (a.scheduled_at
    ? new Date(a.scheduled_at).getTime()
    : Number.POSITIVE_INFINITY) -
  (b.scheduled_at
    ? new Date(b.scheduled_at).getTime()
    : Number.POSITIVE_INFINITY);
const score = (value: number | null) => value ?? "—";
const timeLabel = (value: string | null) =>
  value
    ? new Intl.DateTimeFormat("es-PE", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "America/Lima",
      }).format(new Date(value))
    : "Por definir";
const dateLabel = (value?: string) =>
  value
    ? new Intl.DateTimeFormat("es-PE", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        timeZone: "America/Lima",
      }).format(new Date(`${value}T00:00:00-05:00`))
    : "Fecha por confirmar";

export function EncuentrosPublicosView({
  estado = "sin-datos",
  encuentros,
  mensajeError,
  actualizacionEnVivo,
  estadoRealtime,
  seleccionarCompetencia,
  reintentar,
}: EncuentrosPublicosViewProps) {
  if (estado === "cargando")
    return (
      <ShellPendingState
        title="Cargando el campeonato"
        description="Estamos leyendo el fixture oficial."
      />
    );
  if (estado === "error")
    return (
      <ShellErrorState
        title="No pudimos cargar el campeonato"
        description={mensajeError ?? "Inténtalo nuevamente."}
        accion={
          reintentar ? { label: "Reintentar", onClick: reintentar } : undefined
        }
      />
    );
  if (!encuentros?.ready)
    return (
      <ShellPendingState
        title="El campeonato se está preparando"
        description="El fixture aparecerá cuando quede publicado."
      />
    );
  return (
    <>
      <p className="sr-only" aria-live="polite">
        {actualizacionEnVivo
          ? "El marcador se actualizó con la información oficial."
          : ""}
      </p>
      <TorneoView
        data={encuentros}
        actualizacionEnVivo={actualizacionEnVivo}
        estadoRealtime={estadoRealtime}
        seleccionarCompetencia={seleccionarCompetencia}
      />
    </>
  );
}

function TorneoView({
  data,
  actualizacionEnVivo,
  estadoRealtime = "conectando",
  seleccionarCompetencia,
}: {
  data: TorneoPublico;
  actualizacionEnVivo?: Date | null;
  estadoRealtime?: "conectando" | "conectado" | "reconectando";
  seleccionarCompetencia?: (competitionId: string) => void;
}) {
  const [section, setSection] = useState<Section>("overview");
  const [selectedGroup, setSelectedGroup] = useState("A");
  const [scheduleFilter, setScheduleFilter] = useState("Todos");
  const all = [
    ...data.groups.flatMap((group) => group.matches),
    ...data.knockout,
  ];
  const live = all.filter(isLive).sort(scheduledSort);
  const upcoming = all
    .filter((match) => match.status === "scheduled")
    .sort(scheduledSort);
  const finished = all
    .filter((match) => match.status === "final")
    .sort((a, b) => scheduledSort(b, a));
  const group =
    data.groups.find((item) => item.id === selectedGroup) ?? data.groups[0];
  const champion = data.knockout.find(
    (match) => match.stage === "final" && match.winner_id,
  );
  const winnerName =
    champion?.winner_id === champion?.home_id
      ? champion?.home_name
      : champion?.away_name;

  return (
    <main className="relative left-1/2 min-h-svh w-screen -translate-x-1/2 bg-brand-deep-navy text-brand-on-gradient">
      <section className="border-b border-brand-on-gradient-border bg-brand-deep-blue">
        <div className="grid w-full gap-8 px-4 py-10 sm:px-8 lg:grid-cols-[1fr_auto] lg:px-14 lg:py-12 2xl:px-20">
          <div>
            <p className="text-xs font-black tracking-[.18em] text-brand-cyan">
              RESULTADOS OFICIALES
            </p>
            <h1 className="mt-3 font-heading text-5xl font-black uppercase leading-none sm:text-6xl">
              {data.competition_name ?? data.tournament ?? "Campeonato"}
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-brand-on-gradient-muted">
              {data.discipline ?? "Disciplina por confirmar"}
              {data.category ? ` · ${data.category}` : ""} ·{" "}
              {dateLabel(data.date)}
            </p>
            {data.competitions.length > 1 ? (
              <label className="mt-6 block max-w-xl text-[11px] font-black tracking-[.14em] text-brand-cyan">
                DISCIPLINA Y COMPETENCIA
                <select
                  value={data.competition_id ?? ""}
                  onChange={(event) =>
                    seleccionarCompetencia?.(event.target.value)
                  }
                  className="mt-2 min-h-12 w-full rounded-lg border border-brand-on-gradient-border bg-brand-deep-navy px-4 text-sm font-bold tracking-normal text-brand-on-gradient outline-none focus:border-brand-cyan"
                >
                  {data.competitions.map((competition) => (
                    <option key={competition.id} value={competition.id}>
                      {competition.discipline} · {competition.category}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <Stat label="En juego" value={live.length} tone="active" />
            <Stat label="Por jugar" value={upcoming.length} />
            <Stat label="Finalizados" value={finished.length} />
          </div>
        </div>
      </section>

      <div className="w-full px-4 sm:px-8 lg:px-14 2xl:px-20">
        <div className="grid gap-3 border-b border-brand-on-gradient-border py-4 text-xs sm:grid-cols-[auto_1fr] sm:items-center">
          <div
            className={`flex w-fit items-center gap-2 rounded-full px-3 py-2 font-black ${estadoRealtime === "conectado" ? "bg-brand-cyan text-brand-deep-navy" : "bg-brand-deep-blue text-brand-on-gradient-muted"}`}
          >
            <Zap className="size-4" />
            {estadoRealtime === "conectado"
              ? "Conexión en vivo activa"
              : estadoRealtime === "reconectando"
                ? "Reconectando resultados"
                : "Conectando resultados"}
          </div>
          <p className="text-brand-on-gradient-muted">
            {actualizacionEnVivo
              ? `Marcador oficial actualizado a las ${timeLabel(actualizacionEnVivo.toISOString())}.`
              : "Cuando la organización inicia o actualiza un partido, esta página recarga el marcador oficial automáticamente."}
          </p>
        </div>
        <nav
          aria-label="Secciones de resultados"
          className="flex overflow-x-auto border-b border-brand-on-gradient-border"
        >
          {(
            [
              ["overview", "Resumen", Radio],
              ["groups", "Grupos", Users],
              ["schedule", "Partidos", CalendarDays],
              ...(data.knockout.length > 0
                ? ([["bracket", "Llaves", Trophy]] as const)
                : []),
            ] as const
          ).map(([key, label, Icon]) => (
            <button
              key={key}
              type="button"
              onClick={() => setSection(key)}
              className={`flex min-h-14 items-center gap-2 border-b-2 px-5 text-sm font-black ${section === key ? "border-brand-cyan text-brand-cyan" : "border-transparent text-brand-on-gradient-muted"}`}
            >
              <Icon className="size-4" />
              {label}
            </button>
          ))}
        </nav>

        {section === "overview" ? (
          <div className="space-y-12 py-10">
            <SectionHeader
              kicker="AHORA"
              title="Partidos en juego"
              count={live.length}
            />
            {live.length ? (
              <div className="grid gap-5 lg:grid-cols-2">
                {live.map((match) => (
                  <LiveCard
                    key={match.id}
                    match={match}
                    group={data.groups.find(
                      (item) => item.id === match.group_id,
                    )}
                  />
                ))}
              </div>
            ) : (
              <div className="flex min-h-36 items-center gap-5 rounded-xl border border-dashed border-brand-on-gradient-border bg-brand-deep-blue-mid p-7">
                <Radio className="size-12 rounded-xl bg-brand-deep-blue p-3 text-brand-cyan" />
                <div>
                  <strong className="font-heading text-2xl uppercase">
                    No hay partidos en juego
                  </strong>
                  <p className="mt-1 text-sm text-brand-on-gradient-muted">
                    Cuando la organización lo inicie, aparecerá aquí. La
                    conexión en vivo actualizará su estado y marcador oficial.
                  </p>
                </div>
              </div>
            )}
            <div className="grid gap-8 lg:grid-cols-2">
              <MatchColumn
                title="Próximos partidos"
                matches={upcoming.slice(0, 5)}
              />
              <MatchColumn
                title="Últimos finales"
                matches={finished.slice(0, 5)}
              />
            </div>
            <button
              type="button"
              onClick={() => setSection("groups")}
              className="flex w-full items-center justify-between rounded-xl bg-brand-cyan p-7 text-left text-brand-deep-navy"
            >
              <span>
                <small className="font-black tracking-[.18em]">
                  FASE DE GRUPOS
                </small>
                <strong className="mt-1 block font-heading text-4xl uppercase">
                  Cada resultado mueve la tabla.
                </strong>
              </span>
              <ArrowRight />
            </button>
          </div>
        ) : null}

        {section === "groups" && group ? (
          <div className="space-y-6 py-10">
            <SectionHeader
              kicker="CAMPEONATO INTERPROMOCIONES"
              title="Fase de grupos"
              count={data.groups.length}
            />
            <p className="text-sm text-brand-on-gradient-muted">
              Los puntos oficiales se actualizan al finalizar cada partido.
            </p>
            <Pills
              values={data.groups.map((item) => item.label)}
              selected={group.label}
              onSelect={(value) =>
                setSelectedGroup(
                  data.groups.find((item) => item.label === value)?.id ?? value,
                )
              }
            />
            <div className="grid items-start gap-6 lg:grid-cols-2">
              <StandingCard group={group} />
              <div className="space-y-3 rounded-xl border border-brand-on-gradient-border bg-brand-deep-blue p-4">
                <div className="flex justify-between text-xs font-black text-brand-on-gradient-muted">
                  <span>ENCUENTROS DEL GRUPO</span>
                  <span>{group.matches.length} partidos</span>
                </div>
                {group.matches.map((match) => (
                  <CompactMatch key={match.id} match={match} />
                ))}
              </div>
            </div>
          </div>
        ) : null}

        {section === "schedule" ? (
          <div className="space-y-6 py-10">
            <SectionHeader
              kicker="LA JORNADA"
              title="Todos los partidos"
              count={all.length}
            />
            <p className="text-sm text-brand-on-gradient-muted">
              Horarios en hora de Perú.
            </p>
            <Pills
              values={[
                "Todos",
                "En juego",
                "Programados",
                "Finalizados",
                ...data.groups.map((item) => `Grupo ${item.id}`),
              ]}
              selected={scheduleFilter}
              onSelect={setScheduleFilter}
            />
            <div className="space-y-3">
              {all
                .filter(
                  (match) =>
                    scheduleFilter === "Todos" ||
                    (scheduleFilter === "En juego" && isLive(match)) ||
                    (scheduleFilter === "Programados" &&
                      match.status === "scheduled") ||
                    (scheduleFilter === "Finalizados" &&
                      match.status === "final") ||
                    scheduleFilter === `Grupo ${match.group_id}`,
                )
                .sort(scheduledSort)
                .map((match) => (
                  <CompactMatch key={match.id} match={match} expanded />
                ))}
            </div>
          </div>
        ) : null}

        {section === "bracket" ? (
          <div className="space-y-6 py-10">
            <SectionHeader kicker="CAMINO AL CAMPEÓN" title="Llaves finales" />
            <p className="text-sm text-brand-on-gradient-muted">
              Los participantes se mostrarán con la clasificación oficial hasta
              que cada equipo quede resuelto.
            </p>
            <div className="overflow-x-auto pb-4">
              <div className="grid min-w-[760px] grid-flow-col auto-cols-[minmax(240px,1fr)] gap-5">
                {stageOrder
                  .filter((stage) =>
                    data.knockout.some((match) => match.stage === stage),
                  )
                  .map((stage, index) => (
                    <div key={stage} className="space-y-4">
                      <div className="flex items-center gap-3 border-b border-brand-on-gradient-border pb-3">
                        <span className="font-heading text-3xl text-brand-cyan">
                          0{index + 1}
                        </span>
                        <strong className="text-sm uppercase">
                          {stageLabels[stage]}
                        </strong>
                      </div>
                      {data.knockout
                        .filter((match) => match.stage === stage)
                        .map((match) => (
                          <BracketMatch key={match.id} match={match} />
                        ))}
                    </div>
                  ))}
              </div>
            </div>
            <div className="flex items-center gap-5 rounded-xl bg-brand-cyan p-6 text-brand-deep-navy">
              <Trophy className="size-9" />
              <div>
                <span className="text-xs font-black tracking-[.15em]">
                  CAMPEÓN SALESIANOS FEST 2026
                </span>
                <strong className="block font-heading text-3xl uppercase">
                  {winnerName || "La historia se está escribiendo"}
                </strong>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </main>
  );
}

function SectionHeader({
  kicker,
  title,
  count,
}: {
  kicker: string;
  title: string;
  count?: number;
}) {
  return (
    <header>
      <span className="text-[11px] font-black tracking-[.18em] text-brand-cyan">{`/// ${kicker}`}</span>
      <h2 className="mt-2 font-heading text-5xl font-black uppercase">
        {title}
        {count !== undefined ? (
          <span className="ml-3 align-top text-lg text-brand-cyan">
            {count}
          </span>
        ) : null}
      </h2>
    </header>
  );
}
function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "active";
}) {
  return (
    <div
      className={`min-w-24 border p-4 ${tone === "active" ? "border-brand-cyan bg-brand-cyan text-brand-deep-navy" : "border-brand-on-gradient-border bg-brand-deep-blue"}`}
    >
      <span className="block text-[10px] font-black tracking-[.12em]">
        {label}
      </span>
      <strong className="mt-1 block font-heading text-4xl leading-none">
        {String(value).padStart(2, "0")}
      </strong>
    </div>
  );
}
function Pills({
  values,
  selected,
  onSelect,
}: {
  values: string[];
  selected: string;
  onSelect: (value: string) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 sm:flex-wrap sm:overflow-visible">
      {values.map((value) => (
        <button
          key={value}
          type="button"
          onClick={() => onSelect(value)}
          className={`min-h-11 whitespace-nowrap rounded-lg border px-4 text-xs font-black ${selected === value ? "border-brand-cyan bg-brand-cyan text-brand-deep-navy" : "border-brand-on-gradient-border bg-brand-deep-blue text-brand-on-gradient-muted"}`}
        >
          {value}
        </button>
      ))}
    </div>
  );
}
function MatchColumn({
  title,
  matches,
}: {
  title: string;
  matches: PartidoTorneo[];
}) {
  return (
    <section>
      <h3 className="mb-4 font-heading text-3xl font-black uppercase">
        {title}
      </h3>
      <div className="space-y-3">
        {matches.length ? (
          matches.map((match) => <CompactMatch key={match.id} match={match} />)
        ) : (
          <p className="text-sm text-brand-on-gradient-muted">
            No hay partidos para mostrar.
          </p>
        )}
      </div>
    </section>
  );
}
function CompactMatch({
  match,
  expanded = false,
}: {
  match: PartidoTorneo;
  expanded?: boolean;
}) {
  const active = isLive(match);
  return (
    <article
      className={`grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-3 border p-4 sm:grid-cols-[120px_minmax(0,1fr)_auto] sm:p-5 ${active ? "border-accent bg-brand-deep-blue-mid" : "border-brand-on-gradient-border bg-brand-deep-blue"}`}
    >
      <div>
        <strong className="text-sm">{timeLabel(match.scheduled_at)}</strong>
        <small className="block text-[10px] text-brand-on-gradient-muted">
          {match.court ? `Cancha ${match.court}` : "Cancha pendiente"}
        </small>
      </div>
      <div className="order-3 col-span-full flex min-w-0 items-center gap-3 text-left text-sm font-black sm:order-none sm:col-span-1 sm:justify-center sm:text-center">
        <span className="min-w-0 flex-1 truncate sm:flex-none">
          {match.home_name}
        </span>
        <span className="shrink-0 text-brand-cyan">
          {match.status === "scheduled"
            ? "VS"
            : `${score(match.home_score)} : ${score(match.away_score)}`}
        </span>
        <span className="min-w-0 flex-1 truncate sm:flex-none">
          {match.away_name}
        </span>
      </div>
      <span
        className={`text-[10px] font-black uppercase ${active ? "text-accent" : "text-brand-on-gradient-muted"}`}
      >
        {statusLabels[match.status]}
      </span>
      {expanded ? (
        <div className="col-span-full flex flex-wrap gap-4 border-t border-brand-on-gradient-border pt-3 text-[10px] text-brand-on-gradient-muted">
          <span>
            {match.group_id
              ? match.category
              : `${stageLabels[match.stage]} · ${match.category}`}
          </span>
          <span>{match.duration_minutes} minutos</span>
        </div>
      ) : null}
    </article>
  );
}
function LiveCard({
  match,
  group,
}: {
  match: PartidoTorneo;
  group?: GrupoTorneo;
}) {
  const homeBase =
    group?.table.find((team) => team.id === match.home_id)?.pts ?? 0;
  const awayBase =
    group?.table.find((team) => team.id === match.away_id)?.pts ?? 0;
  return (
    <article className="overflow-hidden rounded-xl border border-brand-on-gradient-border border-t-4 border-t-accent bg-brand-deep-blue-mid">
      <div className="flex justify-between px-5 py-4 text-[10px] font-black uppercase text-brand-on-gradient-muted">
        <span className="text-accent">● {statusLabels[match.status]}</span>
        <span>
          GRUPO {match.group_id} · CANCHA {match.court}
        </span>
      </div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-5 py-7">
        <div>
          <small className="text-brand-cyan">PROMOCIÓN</small>
          <strong className="block font-heading text-4xl uppercase">
            {match.home_name}
          </strong>
          <span className="text-[10px] text-brand-on-gradient-muted">
            +{match.live_points.home} pts · total{" "}
            {homeBase + match.live_points.home}
          </span>
        </div>
        <div className="font-heading text-6xl font-black">
          {score(match.home_score)}
          <span className="px-2 text-brand-cyan">:</span>
          {score(match.away_score)}
        </div>
        <div className="text-right">
          <small className="text-brand-cyan">PROMOCIÓN</small>
          <strong className="block font-heading text-4xl uppercase">
            {match.away_name}
          </strong>
          <span className="text-[10px] text-brand-on-gradient-muted">
            +{match.live_points.away} pts · total{" "}
            {awayBase + match.live_points.away}
          </span>
        </div>
      </div>
      <div className="border-t border-brand-on-gradient-border px-5 py-3 text-xs text-brand-on-gradient-muted">
        Duración prevista: {match.duration_minutes} min
      </div>
    </article>
  );
}
function StandingCard({ group }: { group: GrupoTorneo }) {
  return (
    <article className="overflow-hidden rounded-xl border border-brand-on-gradient-border bg-brand-deep-blue">
      <div className="flex justify-between border-b border-brand-on-gradient-border p-5">
        <div>
          <span className="text-[10px] font-black tracking-[.15em] text-brand-cyan">
            FASE DE GRUPOS
          </span>
          <h3 className="font-heading text-3xl font-black uppercase">
            {group.label}
          </h3>
        </div>
        <span className="text-xs text-brand-on-gradient-muted">
          {group.teams.length} promociones · {group.matches.length} partidos
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] text-center text-xs">
          <thead className="bg-brand-deep-blue-mid text-brand-cyan">
            <tr>
              {["#", "Promoción", "PJ", "G", "E", "P", "DG", "Pts"].map(
                (label) => (
                  <th key={label} className="p-3">
                    {label}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {group.table.map((team, index) => (
              <tr
                key={team.id}
                className="border-t border-brand-on-gradient-border"
              >
                <td className="p-3 text-brand-cyan">{index + 1}</td>
                <td className="p-3 text-left font-black">{team.name}</td>
                <td>{team.pj}</td>
                <td>{team.g}</td>
                <td>{team.e}</td>
                <td>{team.p}</td>
                <td>{team.dg > 0 ? `+${team.dg}` : team.dg}</td>
                <td className="text-lg font-black">{team.pts}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center gap-2 p-4 text-[11px] text-brand-on-gradient-muted">
        <Clock3 className="size-4 text-brand-cyan" />
        Solo se cuentan los partidos finalizados.
      </div>
    </article>
  );
}
function BracketMatch({ match }: { match: PartidoTorneo }) {
  return (
    <article className="rounded-lg border border-brand-on-gradient-border bg-brand-deep-blue p-3">
      <div className="mb-2 flex justify-between text-[9px] font-black text-brand-on-gradient-muted">
        <span>{match.title || `PARTIDO ${match.position + 1}`}</span>
        <span>{statusLabels[match.status]}</span>
      </div>
      {(
        [
          ["home", match.home_id, match.home_name, match.home_score],
          ["away", match.away_id, match.away_name, match.away_score],
        ] as const
      ).map(([slot, id, name, value]) => (
        <div
          key={`${match.id}-${slot}`}
          className={`flex justify-between border-t border-brand-on-gradient-border py-3 text-sm font-bold ${match.winner_id && match.winner_id === id ? "text-brand-cyan" : ""}`}
        >
          <span>{name}</span>
          <b>{score(value)}</b>
        </div>
      ))}
    </article>
  );
}
