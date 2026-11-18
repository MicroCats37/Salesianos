# VER-02 - Execute Business E2E, UX, Accessibility, Permission, And Secret QA

## Purpose

Run the full business QA matrix, responsive/accessibility review, permission attacks, concurrency, and sensitive-data checks.

## Original Plan Tasks

- `T-092`, `T-093`, `T-094`.

## Dependencies

- `VER-01` has no unresolved regression that invalidates E2E evidence.

## Mandatory Context

- All contracts and final plan requirements/flows/pages/test matrix.
- Every route brief, endpoint/presenter/schema ledger, and current STATE/apply/verify evidence.
- Skills: `salesianos-responsive-a11y`, `salesianos-ui-ux`, `salesianos-api-data`; forms skill for form/server-error checks.
- UI reviewer definition for findings format; do not modify code during review.

## Allowed Edit Roots

- `Aplicacion/task/salesianos-fest-rebuild/evidence/verification/**`
- Test/QA automation files only when they encode already-approved behavior
- STATE and Engram verify/apply topics.

## Forbidden Edit Roots

- Production implementation, contracts/plan/docs, frozen roots, runtime config, DB/secrets, cleanup. Defects return to owner/fix packet.

## Implementation Steps

1. Execute all 29 plan QA cases with preconditions, steps, expected/actual, version, evidence, status, and incident.
2. Exercise concurrency for capacity, stock, callbacks, and validation.
3. Test 401/403/titularity/forced commands/token scope and scan responses/log evidence for sensitive leakage without recording secrets.
4. Audit all shipped routes at five widths, keyboard, focus, labels/errors/live regions, touch, overflow, reduced motion, and responsive tables/dialogs/brackets.
5. Record findings first by severity; rerun only after separate fixes.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules -q -m "e2e or integration"`
- Workdir `Aplicacion/frontend`: `npx vitest run`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check .`
- Browser/assistive audit widths: `360`, `390`, `768`, `1024`, `1440`.
- Repository root: `git grep -n -I -E "(SECRET_KEY|IZIPAY_KEY|SMTP_PASSWORD)=" -- Aplicacion` with output redacted and secrets never copied.

## Acceptance Criteria

- Each QA ID has real evidence or an explicit blocker; no invented success.
- No critical accessibility, permission, ownership, concurrency, or secret-exposure finding remains.
- Residual browser/device/assistive-technology gaps are listed.

## Parallelism And Conflicts

- QA domains may execute in parallel after stable environment snapshot; A9 owns merged verdict.
- UI reviewer is read-only; fixes are separate packets.

## Rollback

Revert only test/evidence artifacts. Preserve incident records and do not mutate product state to hide failures.

## Apply Progress Output

Persist tasks, QA matrix results, security/concurrency evidence, accessibility findings by route/viewport, command outputs/exit codes, incidents/owners, files, rollback, and sign-off readiness in apply and verify topics.

## Next Packet

- [VER-03](VER-03-signoff-archive-cutover-cleanup.md) only after required gates are green.
