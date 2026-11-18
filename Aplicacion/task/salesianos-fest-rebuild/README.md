# Salesianos FEST Rebuild Apply Packets

This directory is the executable task source for the target rebuild under `Aplicacion/`. It does not replace the existing plan; every future apply uses the plan as specification and design.

## Quick Path

1. Read [the global apply contract](00-contrato-global-de-apply.md).
2. Confirm dependencies and ownership in [the task matrix](00-matriz-tareas.md) and [wave DAG](00-olas-paralelas.md).
3. Run packets in the order below, updating [STATE.md](STATE.md) after each apply.
4. Do not begin cleanup until `VER-03` and all rollback/archive gates are green.

## Source Hierarchy

1. [`contract/`](../../../contract/) is normative fallback and mandatory read-only context.
2. [`Aplicacion/plan/salesianos-fest-rebuild/`](../../plan/salesianos-fest-rebuild/) is the target specification and design source.
3. This directory is the executable task source.
4. [`Aplicacion/documentacion/`](../../documentacion/) is current-state evidence only.
5. Current `backend/`, `frontend/`, `worker/`, and `proxy/` are frozen source references, not edit targets.

When sources conflict, stop and record the conflict. Do not silently alter contracts, plan files, or business behavior.

## Status Legend

| Status | Meaning |
|---|---|
| `pending` | Dependencies or execution not started |
| `ready` | Dependencies and contract freeze are satisfied |
| `in_progress` | One apply owns the packet and has persisted its start evidence |
| `blocked` | A named decision, dependency, or failed check prevents completion |
| `verification_required` | Implementation exists; aggregate gate remains |
| `complete` | Acceptance criteria and required checks have recorded evidence |

No packet may be marked `complete` merely because code was written. Test results are future evidence, never assumptions.

## Future SDD Apply Invocation

Launch one formal `sdd-apply` per packet with this contract:

```text
change_name: salesianos-fest-rebuild
tasks_artifact: <exact packet path from the index below>
spec_design_references:
  - Aplicacion/plan/salesianos-fest-rebuild/00-decisiones-y-alcance.md
  - every exact plan path listed by the packet under Mandatory Context
mandatory_context: contract/
allowed_edit_roots: copy exactly from the packet
verification_commands: copy exactly from the packet
progress_topic: sdd/salesianos-fest-rebuild/apply-progress
state_topic: sdd/salesianos-fest-rebuild/state
instruction: Read contract/ before editing code. Treat backend/, frontend/, worker/, and proxy/ as frozen references. Do not use git stash.
```

The apply orchestrator must pass the packet path as the tasks artifact and the listed plan files as existing spec/design references. Do not create new proposal/spec/design phases for this change.

## Exact Execution Order

Packets inside the same parallel wave may run concurrently only when [the wave rules](00-olas-paralelas.md) say their roots are disjoint. A0-owned shared files are always serialized.

| Order | Packet | Outcome |
|---|---|---|
| 1 | [GOV-00](wave-00-governance/GOV-00-checkpoint-manifest.md) | Non-destructive checkpoint and manifest |
| 2 | [GOV-01](wave-00-governance/GOV-01-contract-freeze.md) | Freeze cross-module contracts and provisional fixtures |
| 3 | [GOV-02](wave-00-governance/GOV-02-route-ux-baseline.md) | Freeze route briefs and record baseline checks |
| 4 | [FND-01](wave-01-foundations/FND-01-backend-shared-api-media.md) | A0 backend shared API/media surface |
| 5 | [FND-02](wave-01-foundations/FND-02-event-edition-scope.md) | Event/edition scoping |
| 6 | [FND-03](wave-01-foundations/FND-03-identity-reniec.md) | Identity and RENIEC resolution |
| 7 | [FND-04](wave-01-foundations/FND-04-commerce-payments.md) | Commerce/payment foundation |
| 8 | [FND-05](wave-01-foundations/FND-05-rights-activation.md) | Exactly-once rights activation |
| 9 | [FND-06](wave-01-foundations/FND-06-frontend-shell.md) | A0 frontend shell and shared providers |
| 10 | [FND-07](wave-01-foundations/FND-07-forms-lifecycle-errors-payloads.md) | Form hydration, 422, and payload corrections |
| 11 | [FND-08](wave-01-foundations/FND-08-query-cache-consolidation.md) | Query-key/client/cache corrections |
| 12 | [DOM-01](wave-02-domain-backend/DOM-01-inscription-catalog-purchase.md) | Registration catalog and initial purchase |
| 13 | [DOM-02](wave-02-domain-backend/DOM-02-inscription-pool-expansion.md) | Pool, assignment, and expansion |
| 14 | [DOM-03](wave-02-domain-backend/DOM-03-passes-benefits-courtesy.md) | Passes, beneficiaries, and courtesy |
| 15 | [DOM-04](wave-02-domain-backend/DOM-04-marketplace-catalog-media.md) | Marketplace catalog/media |
| 16 | [DOM-05](wave-02-domain-backend/DOM-05-marketplace-order.md) | Marketplace order and snapshots |
| 17 | [DOM-06](wave-02-domain-backend/DOM-06-inventory-reservation-delivery.md) | Inventory and anti-oversell |
| 18 | [DOM-07](wave-02-domain-backend/DOM-07-competitions.md) | Competitions and match progression |
| 19 | [DOM-08](wave-02-domain-backend/DOM-08-sponsors.md) | Sponsors and ordered media |
| 20 | [UI-01](wave-02-frontend-skeletons/UI-01-public-account-shells.md) | Public/account provisional shells |
| 21 | [UI-02](wave-02-frontend-skeletons/UI-02-inscription-shells.md) | Registration provisional shells |
| 22 | [UI-03](wave-02-frontend-skeletons/UI-03-commerce-shells.md) | Pass/shop provisional shells |
| 23 | [UI-04](wave-02-frontend-skeletons/UI-04-admin-operations-shells.md) | Admin operations provisional shells |
| 24 | [UI-05](wave-02-frontend-skeletons/UI-05-competition-validation-shells.md) | Competition/validation provisional shells |
| 25 | [API-01](wave-03-api-integration/API-01-public-account-integration.md) | Public/account real API integration |
| 26 | [API-02](wave-03-api-integration/API-02-inscription-integration.md) | Registration real API integration |
| 27 | [API-03](wave-03-api-integration/API-03-commercial-integration.md) | Pass/shop real API integration |
| 28 | [API-04](wave-03-api-integration/API-04-admin-operations-integration.md) | Admin sports/payment API integration |
| 29 | [API-05](wave-03-api-integration/API-05-competition-admin-integration.md) | Competition/admin integration and mock gate |
| 30 | [XCT-01](wave-04-cross-cutting/XCT-01-tickets-validation.md) | Shared ticket validation |
| 31 | [XCT-02](wave-04-cross-cutting/XCT-02-transversal-admin.md) | Transversal administration |
| 32 | [XCT-03](wave-04-cross-cutting/XCT-03-payment-media-notifications.md) | Recovery, deployment, and deferred notifications |
| 33 | [VER-01](wave-05-verification-cleanup/VER-01-baseline-regression-payments.md) | Regression and payment verification |
| 34 | [VER-02](wave-05-verification-cleanup/VER-02-e2e-ux-security.md) | E2E, UX, accessibility, and security |
| 35 | [VER-03](wave-05-verification-cleanup/VER-03-signoff-archive-cutover-cleanup.md) | Sign-off, archive, cutover, then cleanup |

## Topic Keys

| Purpose | Engram topic key |
|---|---|
| Plan review | `sdd/explore/salesianos-fest-rebuild-plan-review` |
| Apply progress | `sdd/salesianos-fest-rebuild/apply-progress` |
| State/DAG | `sdd/salesianos-fest-rebuild/state` |
| Verification | `sdd/salesianos-fest-rebuild/verify-report` |
| Archive | `sdd/salesianos-fest-rebuild/archive-report` |

## Review Budget

Each packet is a review unit. Keep implementation changes at or below roughly 400 changed lines where feasible, with behavior and its tests together. If a packet forecasts more, persist a safe boundary in apply progress and resume the same packet in another work-unit commit; never mix unrelated domains to reduce the packet count.
