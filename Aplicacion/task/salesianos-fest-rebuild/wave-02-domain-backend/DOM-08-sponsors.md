# DOM-08 - Implement Sponsors And Ordered Local Media

## Purpose

Provide edition-linked sponsor records, logo, ordered gallery, and visibility without monetary/vendor features.

## Original Plan Tasks

- `T-060`.

## Dependencies

- `FND-02`, `FND-01`; corrected media protocol from DOM-04 is reusable.

## Mandatory Context

- Relevant backend architecture/API/schema/test contracts.
- Plan: DEC-14/17, sponsor data model, media integration section, ADM-21, QA-MEDIA01.
- Documentation: current sponsor/media evidence if present.
- Skill: `salesianos-api-data` for endpoint/multipart work; no UI skills.

## Allowed Edit Roots

- Frozen sponsor module root under `Aplicacion/backend/modules/**`
- Its migrations/tests/media validators; packet evidence/state.

## Forbidden Edit Roots

- Marketplace internals except imported shared media utility; payment/vendor accounting; frontend/shared/frozen/normative roots; secrets/DB/user media.

## Implementation Steps

1. Implement sponsor, logo, ordered gallery, edition relation, and visibility.
2. Reuse corrected tokenized multipart and cleanup policy; do not fork protocol.
3. Exclude contributions, commissions, payouts, or unrequested financial modeling.
4. Add CRUD/order/visibility/file validation and cleanup tests.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/patrocinadores/tests -q`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Sponsor media is persistent, ordered, validated, and edition coherent.
- No financial/vendor domain is introduced.
- Presenter/schema is frozen for admin/public consumers.

## Parallelism And Conflicts

- Disjoint domain root; A0 media settings and registration remain serialized.

## Rollback

Revert code/migrations/tests; remove only packet-created test files, never user media or archive evidence.

## Apply Progress Output

Persist task, files/migrations, multipart reuse, tests/commands, media cleanup evidence, A0 requests, rollback, and API-05 readiness.

## Next Packet

- [API-05](../wave-03-api-integration/API-05-competition-admin-integration.md) after UI-05.
