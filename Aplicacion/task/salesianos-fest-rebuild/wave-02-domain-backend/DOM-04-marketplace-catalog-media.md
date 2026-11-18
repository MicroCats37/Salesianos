# DOM-04 - Implement Marketplace Catalog And Correct Multipart Media

## Purpose

Build edition-scoped categories/products/offers and ordered local images using the corrected multipart protocol.

## Original Plan Tasks

- `T-040`.

## Dependencies

- `FND-02`, `FND-01` media foundation and frozen edition/media contracts.

## Mandatory Context

- Relevant Django architecture, controller pattern, API wrapper/schema DRY/test contracts.
- Plan: RN-M01-M03, marketplace data model, media integration section, SHOP-01/02, QA-MEDIA01.
- Documentation: current endpoint/media/deployment evidence.
- Skill: `salesianos-api-data` plus `references/api-data-contract.md`; no UI skills.

## Allowed Edit Roots

- Frozen target marketplace module root under `Aplicacion/backend/modules/**`
- Its migrations/tests/media validators; packet evidence/state.

## Forbidden Edit Roots

- Shared media settings directly; frontend; other domains; frozen/normative roots; secrets/DB/media user data.

## Implementation Steps

1. Implement categories/products/prices/offers and ordered image relations scoped by edition policy.
2. Implement multipart hydration: JSON `data` tokens `file_<uuid>`, file names `<token>___<realname>`, exactly-once matching.
3. Reject missing/orphan files, invalid signature/MIME/size; define rollback/replacement/deletion cleanup.
4. Keep typed dates and one file representation through controller/DTO/orchestrator/flow.
5. Add JSON/multipart success and all failure/cleanup integration tests.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/marketplace/tests -q -k "producto or imagen or multipart"`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Catalog/price/image order is server-authoritative and edition coherent.
- Multipart tokens hydrate exactly once; invalid/orphan files leave no residue.
- No raw ValueError/public file internals or secret paths leak.

## Parallelism And Conflicts

- Disjoint from passes/competitions; A0 owns media settings.
- Product migrations serialize with later marketplace packets.

## Rollback

Revert module/migrations/tests and remove only packet-created test media; preserve user media and checkpoint evidence.

## Apply Progress Output

Record task, multipart protocol/version, file/migration list, media cleanup evidence, tests/commands, A0 requests, rollback, and `DOM-05` readiness.

## Next Packet

- [DOM-05](DOM-05-marketplace-order.md)
