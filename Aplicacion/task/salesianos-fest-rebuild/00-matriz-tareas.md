# Original Task To Apply Packet Matrix

The source plan claims 96 tasks because its namespace ends at `T-095`, but the table physically defines 54 IDs. The unused numeric slots are not tasks and are not invented here. This matrix maps every source-defined task exactly once.

Unused number ranges: `008-009`, `019`, `024-029`, `033-039`, `044-049`, `053-059`, `061-069`, `079`, `087-089`.

| Task | Packet | Owner | Dependencies | Parallel wave | Status | Primary plan reference |
|---|---|---|---|---|---|---|
| T-000 | GOV-00 | A0 + product | none | W00 | pending | `implementacion/02` F0; decisions 00 |
| T-001 | GOV-02 | A7 | T-000 | W00 | pending | frontend route map |
| T-002 | GOV-02 | A7 | T-001 | W00 | pending | frontend 02-05 |
| T-003 | GOV-01 | A0 | T-000 | W00 | pending | contracts 01; API wrapper contract |
| T-004 | GOV-01 | A0 + A1 | T-000 | W00 | pending | decisions; functional 01-03 |
| T-005 | GOV-01 | A0 + A2 | T-003 | W00 | pending | contracts 01/03 |
| T-006 | GOV-01 | A0 + A4 + A8 | T-004 | W00 | pending | functional 02; contracts 03 |
| T-007 | GOV-01 | A0 | T-003,T-005,T-006 | W00 | pending | implementation 01; contract-first workflow |
| T-010 | FND-02 | A1 | T-004 | W01 | pending | RN-E01/E02; data model |
| T-011 | FND-03 | A1 | T-004 | W01 | pending | RN-U01/U02/U04; auth contract |
| T-012 | FND-03 | A1 | T-011 | W01 | pending | RN-U03; FL-02 |
| T-013 | FND-04 | A2 | T-005 | W01 | pending | RN-C01-C04; data model |
| T-014 | FND-04 | A2 | T-013 | W01 | pending | RN-C05-C08; integration contract |
| T-015 | FND-05 | A0 | T-013 | W01 | pending | activation interface |
| T-016 | FND-01 | A0 | T-003 | W01 | pending | media contract |
| T-017 | FND-06 | A7/A0 shared owner | T-001,T-003 | W01 | pending | frontend 01/06 |
| T-018 | FND-01 | A0 | T-003,T-011 | W01 | pending | auth/permissions contract |
| T-020 | DOM-01 | A3 | T-010,T-003 | W02 | pending | packages by edition |
| T-021 | DOM-01 | A3 | T-020,T-013 | W02 | pending | FL-03; QA-I01 |
| T-022 | DOM-02 | A3 | T-021,T-015 | W02 | pending | RN-I03-I05; FL-05 |
| T-023 | DOM-02 | A3 | T-022 | W02 | pending | RN-I06; FL-04 |
| T-030 | DOM-03 | A4 | T-010,T-013 | W02 | pending | FL-06; QA-P01 |
| T-031 | DOM-03 | A4 | T-030,T-015 | W02 | pending | RN-P04; QA-P02 |
| T-032 | DOM-03 | A4 | T-031,T-006 | W02 | pending | RN-P05; FL-07 |
| T-040 | DOM-04 | A5 | T-010,T-016 | W02 | pending | RN-M01-M03; media |
| T-041 | DOM-05 | A5 | T-040,T-013 | W02 | pending | FL-08; QA-M03 |
| T-042 | DOM-06 | A5 | T-040 | W02 | pending | RN-M04/M05; FL-09 |
| T-043 | DOM-06 | A5 | T-041,T-042,T-015 | W02 | pending | RN-M06/M07; QA-M01/M04 |
| T-050 | DOM-07 | A6 | T-010,T-022 | W02 | pending | RN-K01; QA-K01 |
| T-051 | DOM-07 | A6 | T-050 | W02 | pending | RN-K03; QA-K02 |
| T-052 | DOM-07 | A6 | T-051 | W02 | pending | RN-K02; QA-K03 |
| T-060 | DOM-08 | A8 | T-010,T-016 | W02 | pending | sponsors/media model |
| T-070 | API-01 | A7 | T-007,T-017,UI-01 | W03 | pending | PUB-01/PUB-02 |
| T-071 | API-01 | A7 | T-011,T-012,T-017,UI-01 | W03 | pending | AUTH/ACCOUNT/REC pages |
| T-072 | API-02 | A7 | T-007,T-017,UI-02,DOM-01/02 | W03 | pending | SPORT-01/ACCOUNT-03 |
| T-073 | API-03 | A7 | T-007,T-017,UI-03,DOM-03 | W03 | pending | PASS-01/PASS-02 |
| T-074 | API-03 | A7 | T-007,T-017,UI-03,DOM-04/05/06 | W03 | pending | SHOP-01/02/03 |
| T-075 | API-04 | A7 | T-007,T-017,UI-04,DOM-01/02 | W03 | pending | ADM-05-09 |
| T-076 | API-04 | A7 | T-007,T-017,UI-04,FND-04/05 | W03 | pending | ADM-14 |
| T-077 | API-05 | A7 | T-007,T-017,UI-05,DOM-07 | W03 | pending | ADM-10-13 |
| T-078 | API-05 | A7 | T-007,T-017,UI-05,domain packets | W03 | pending | ADM-15-22 |
| T-080 | XCT-01 | A8 + A4 | T-032,T-006 | W04 | pending | FL-10; QA-V01/V02 |
| T-081 | XCT-01 | A8 + A5 | T-043,T-006 | W04 | pending | marketplace delivery validation |
| T-082 | API-05 | A0 + A7 | relevant T-020..T-078 | W03 gate | pending | real contract cutover |
| T-083 | XCT-02 | A8 | relevant T-020..T-081 | W04 | pending | admin transversal |
| T-084 | XCT-03 | A2 + A0 | T-014,T-015,T-023,T-031,T-043 | W04 | pending | FL-12; QA-C03 |
| T-085 | XCT-03 | A0 | T-016,T-018 | W04 | pending | media/deployment/permissions |
| T-086 | XCT-03 | A0 | PD-08,T-015 | W04 conditional | pending | notification contract |
| T-090 | VER-01 | A9 | T-082..T-085 | W05 | pending | testing strategy |
| T-091 | VER-01 | A9 + A2 | T-084 | W05 | pending | QA-C01-C03 |
| T-092 | VER-02 | A9 + A3/A4/A5 | T-082 | W05 | pending | QA-I/P/M/V |
| T-093 | VER-02 | A9 + A6/A7 | T-082 | W05 | pending | QA-K/A UX |
| T-094 | VER-02 | A9 | T-082,T-085 | W05 | pending | permissions/a11y/secrets |
| T-095 | VER-03 | A0 + product | T-090..T-094 | W05 | pending | final sign-off |

## Supplemental Execution Packets

These packets close verified construction defects without inventing original plan IDs: `FND-07`, `FND-08`, and `UI-01` through `UI-05`. Their downstream original tasks remain mapped once above.
