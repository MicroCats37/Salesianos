# Feature Pattern Catalogue

## Authority And Scope

- Tracked frontend source: `frontend/src`.
- Route behavior: `Aplicacion/documentacion/03a-paginas-publicas-y-compra.md` and `03b-paginas-administrativas-y-operativas.md`.
- Action-to-endpoint trace: `Aplicacion/documentacion/05a-matriz-pagina-flujo-endpoint-datos.md`.
- Visual guidance: `Aplicacion/documentacion/07-guia-para-ui-ux.md`.
- Folder and naming contract: `contract/next-app-architecture-contract.md` sections 1, 2, 6-8, and 10.

## Canonical Dependency Direction

| Layer | Owns | Must not own |
| --- | --- | --- |
| `app/**/page.tsx` | Route entry and thin composition | Fetching, state machines, business rules |
| `features/<domain>/views/` | Route-level feature composition | Transport implementation |
| `features/<domain>/components/` | Feature-only presentation | URLs, payloads, domain calculations |
| `features/<domain>/hooks/` | Query/mutation orchestration and UI-facing state | Raw transport duplication |
| `features/<domain>/services/` | Calls through `frontend/src/lib/api.ts` | JSX or cache ownership |
| `features/<domain>/schemas/` | Zod form and wire mirrors | Network calls |
| Colocated `*.test.*` | Observable contract of its layer | Cross-layer implementation details |

Use `components/ui/` for generic shadcn primitives and `components/<domain>/` only for genuinely cross-feature domain presentation. Add a `utils/` file only for pure mappings or a domain key factory.

## Reuse Decision

Extend an existing feature when it already owns the domain and the new route shares endpoint, permissions, schemas, and most behavior. Add an admin/public namespace when endpoint, permissions, or schemas differ. Create a new feature only for a cohesive use case without an owner. Do not create a second client or feature merely to avoid understanding an existing one.

## Anti-Patterns

- Logic-heavy `app/**/page.tsx`, page-level `useEffect` fetching, or inline feature components.
- Raw `fetch`, hardcoded URLs, transport in components, or browser-side business calculations.
- New work under `_legacy-*`, `components-app/**`, or the wrong `Aplicacion/frontend` tree.
- References to deleted `frontend/features-app-example` or `frontend/src/features-example-app`.
- Global barrels, `export *`, or a new top-level `src/` folder without updating architecture documentation.
- Treating `.agent/skills/app-builder/` as authoritative. It is a legacy generic greenfield scaffolder and is not a Salesianos construction skill.

## Known Divergence

**CURRENT BEHAVIOR:** `Aplicacion/frontend/src` is an untracked byte-identical copy observed during exploration, and some live code imports excluded or legacy paths.

**TARGET RULE:** New work uses tracked `frontend/src` and current non-legacy feature anatomy.

**REQUIRED AGENT ACTION:** Do not normalize unrelated legacy code opportunistically. If the requested path depends on it, either include a tested migration in scope or stop and report the boundary.
