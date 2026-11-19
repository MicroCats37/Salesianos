# RB-04 — Route Briefs: Admin Teams And Participants

**Artifact:** `evidence/routes/RB-04-admin-teams-participants.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — briefs only
**Date:** 2026-11-19
**Page IDs in this file (3 of 38):** `ADM-07`, `ADM-08`, `ADM-09`
**Shared references:** `SH-01` … `SH-06`

> **Redesign priority.** `frontend/04` §5: the current reference lists teams but **offers no clickable detail**, even though the participant data already exists. The rebuild **must** ship an operational team view.

---

## `ADM-07` — `/administracion/equipos` — find and manage teams

- **Actor:** administrador. **Priority:** **Alta** (redesign priority).
- **Objective:** find a team and understand whether it can compete.
- **Preconditions:** admin group; edition context.
- **Visible sections:** the table proposed by the plan — Team · discipline/category · responsible · current roster · minimum needed · maximum · **legible state** · the reason when it cannot compete · action "Ver equipo".
- **Key components (candidates):** `table` (≥1024) / card list (≤768) · `badge` (verdict chip) · `input`/`select` (filters) · `pagination` · `empty` · `command` (search).
- **Actions:** filter · open a team · act from the list.
- **Navigation:** `/administracion/equipos/[id]`.
- **Data / contract dependencies (provisional):** `RT-IN-09`.
- **States:** `S-01` · `S-02` (no teams for this edition) · `S-03` (filtered-empty, filters preserved) · `S-04` · `S-06`.
- **Responsive intent:** 360/390 card per team with roster `6 / 7–10`, the state sentence and "Ver equipo"; 768 a 3-priority-column table; 1024/1440 the full proposed column set.
- **Semantic-token intent:** `bg-surface-raised`, `bg-surface-recessed` table header, verdict chips (SH-01 §3.2), `text-foreground-muted` for the responsible line, `tabular-nums` for the roster figures, `bg-primary` for "Ver equipo".
- **Accessibility intent:** **cryptic badges are removed** — the state is the backend's sentence ("6 jugadores registrados; necesita al menos 7"), not a coloured dot; `<th scope="col">`; the roster figures are read as a sentence; the row is a link with an accessible name including the team and its discipline.
- **Acceptance:** from the list one opens the detail and understands **why** the team is not ready to compete (`frontend/04` §12.2) · the reason is never inferred client-side.
- **Open decisions:** `P-05` — whether this route becomes tabs of `ADM-05` (the plan allows conceptual destinations to merge).

---

## `ADM-08` — `/administracion/equipos/[id]` — operate one team

- **Actor:** administrador. **Priority:** **Alta**.
- **Objective:** operate an individual team — players, its registration, discipline, permitted actions.
- **Preconditions:** admin group; a team id.
- **Visible sections:** team identity · **state with its reason** · roster (participants with document and state) · the related registration · related cupos · eligibility · the authorised actions.
- **Key components (candidates):** `card` (identity + state) · `table`/card list (roster) · `badge` (per-participant state) · `drawer` (person resolution / add participant) · `alert-dialog` (withdraw) · `button`.
- **Actions:** add a participant · remove a participant · open the registration · act on an eligibility issue.
- **Navigation:** to the related registration (`/administracion/inscripciones/[id]`) and to the participant's record.
- **Data / contract dependencies (provisional):** `RT-IN-10`, `RT-IN-03` (cupos of the linked registration), `RT-ID-01`/`02` (person resolution), `RT-IN-09`.
- **States:** `S-01` · `S-02` (no participants yet — with a specific CTA to add one, **not** a generic empty screen) · `S-04` · `S-06` · `S-10` (removal confirmation naming the effect) · *not eligible for the competition* (with the backend's reason).
- **Responsive intent:** see `SH-06` §4.2. 360/390 single column, the state sentence above the roster, roster as cards; 768 single column; 1024/1440 two columns (roster + linked-registration summary).
- **Semantic-token intent:** `bg-surface-raised` for the state card, `--warning` for "falta 1 jugador", `--destructive` for a blocking ineligibility, `bg-primary` for "Agregar jugador", `text-foreground-muted` for the discipline line.
- **Accessibility intent:** the state is a sentence plus a chip, never a chip alone; the roster figure "6 / 7–10" is read as "6 jugadores registrados, necesita al menos 7"; the drawer traps and restores focus; the removal dialog names the consequence.
- **Acceptance:** the operator understands the team's readiness without opening a console or SQL (`frontend/06` §8) · the reasons come from the backend.
- **Open decisions:** none new.

---

## `ADM-09` — `/administracion/participantes` — find people and participations

- **Actor:** administrador. **Priority:** Media.
- **Objective:** find a person and their participations, locate conflicts, consult the history — **without duplicating a user panel**.
- **Preconditions:** admin group; edition context.
- **Visible sections:** search by person · participations grouped by event, team and discipline · the history · conflict indicators.
- **Key components (candidates):** `input` (search) · `table`/card list · `tabs` (by event / by team / by discipline) · `badge` (state) · `empty` · `dialog` (quick view).
- **Actions:** search · filter by event/team/discipline · open the person's record · inspect a conflict.
- **Navigation:** to the team (`ADM-08`) or the registration (`ADM-06`).
- **Data / contract dependencies (provisional):** `RT-IN-11`, `RT-ID-07`/`08`.
- **States:** `S-01` · `S-02` (no search performed → a prompt) · `S-03` (no results for the query) · `S-04` · `S-06`.
- **Responsive intent:** 360/390 search pinned at the top, participations as grouped cards; 768+ table with the grouped tabs.
- **Semantic-token intent:** `bg-surface-raised`, `bg-surface-recessed` for the group headers, verdict chips, `text-foreground-muted` for the document line, `border-border` group separators.
- **Accessibility intent:** each participation states the event, team and discipline in its accessible name; a conflict is stated in words (the backend's reason) and never only as a red highlight; the tab list is semantic.
- **Acceptance:** a duplicate participation for the same discipline is **detectable** from this page · no panel duplicates the user administration (`frontend/04` §5).
- **Open decisions:** none new.

---

## Cross-Route Obligations In This File

| ID | Obligation | Owner |
|---|---|---|
| `GOV-02-RB-04a` | **Roster maximum and paid-cupos balance are different numbers** and must never be presented as one (`contratos/01` §3). The team card shows roster; the registration shows cupos. | A7 |
| `GOV-02-RB-04b` | Every "why" on these pages is the backend's `estado_operativo.etiqueta` + `.descripcion`. No client-side inference of incompleteness (`contratos/01` §7). | A7 |
| `GOV-02-RB-04c` | Cryptic status badges are removed; every status is a sentence plus an icon (`frontend/04` §5). | A7 |
