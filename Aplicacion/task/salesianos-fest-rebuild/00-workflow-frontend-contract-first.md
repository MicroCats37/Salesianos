# Frontend Contract-First Workflow

Frontend presentation may progress in parallel with backend domain work without touching shared API ownership.

## Stage 1: UI Skeleton And Provisional Adapter

The skeleton packet may create route shells, feature views, layout, responsive composition, visible states, and colocated UI tests. It may also create a feature-local typed fixture adapter marked `PROVISIONAL_CONTRACT_FIXTURE`.

Required states: initial/loading, empty, filtered-empty, recoverable error, validation, permission, success, in-progress, partial/indeterminate, and irreversible confirmation where relevant.

Skeleton packets must:

- Name plan page IDs and exact proposed routes.
- Trace actors, primary/recovery actions, and plan wrapper/presenter references.
- Compare shadcn candidates through MCP before selection.
- Audit 360, 390, 768, 1024, and 1440 widths.
- Keep fixtures deterministic and free of price, eligibility, capacity, payment, stock, or permission calculations.
- Avoid `src/lib/api.ts`, auth, providers, services, network hooks, Zod wire mirrors, query-key factories, shared UI primitives, and package/config files.

The fixture contract is provisional until the backend presenter/schema is frozen. It cannot be exported as a production service or used as fallback data.

## Stage 2: Real API Integration

The integration packet starts only after the relevant endpoint, presenter, schema, error envelope, and edition scope are frozen.

It must:

1. Verify live target endpoint registration in `Aplicacion/backend/config/api.py`.
2. Add or reuse the owning feature service through `Aplicacion/frontend/src/lib/api.ts`.
3. Add exact Zod mirrors for success, pagination, errors, and 204 behavior; no `z.any()`.
4. Own one domain query-key factory and exported `queryOptions` per read dataset.
5. Define targeted invalidation and shape-safe optimistic policy with snapshot, rollback, and settle invalidation.
6. Separate create and update payload mappings; preserve `undefined` versus nullable `null`.
7. Map Django 422 details to `fieldErrors` and React Hook Form `setError`.
8. Use the corrected multipart protocol for images: `data` JSON contains `file_<uuid>` tokens and file parts use `<token>___<realname>`; reject missing/orphan files and test cleanup.
9. Delete/replace every provisional fixture and prove no mock import, fallback, or hidden route remains.
10. Run focused typecheck, Vitest, Biome, endpoint/envelope checks, and all five viewport audits.

## Construction Skill Order

Frontend route/page work loads these project-local skills in order as relevant:

1. `.opencode/skills/salesianos-ui-ux/SKILL.md`
2. `.opencode/skills/salesianos-feature-architecture/SKILL.md`
3. `.opencode/skills/salesianos-api-data/SKILL.md` when data/endpoints are involved
4. `.opencode/skills/salesianos-forms-smart-fields/SKILL.md` when forms/files are involved
5. `.opencode/skills/salesianos-shadcn/SKILL.md`
6. `.opencode/skills/salesianos-responsive-a11y/SKILL.md`

The current skill text points at frozen source roots. For this rebuild, the packet's explicit `Aplicacion/frontend/**` allowed roots govern target edits; the frozen `frontend/**` root remains read-only evidence.

## Handoff Record

Each skeleton-to-integration handoff records page IDs/routes, selected shadcn items, provisional fixture paths, real endpoint/presenter/schema owner, expected envelope, permission states, fixture deletion checklist, and unresolved backend-owned decisions.
