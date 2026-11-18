# Salesianos FEST Rebuild Packet State

Initial state: all packets are `pending`. Apply agents update this board and persist the same transition to `sdd/salesianos-fest-rebuild/state`.

| Packet | Status | Dependencies | Owner | Last evidence |
|---|---|---|---|---|
| GOV-00 | pending | none | A0 + product | none |
| GOV-01 | pending | GOV-00 | A0 | none |
| GOV-02 | pending | GOV-01 | A0 + A7 + A9 | none |
| FND-01 | pending | GOV-01,GOV-02 | A0 | none |
| FND-02 | pending | GOV-01,FND-01 | A1 | none |
| FND-03 | pending | GOV-01,FND-01 | A1 | none |
| FND-04 | pending | GOV-01,FND-01 | A2 | none |
| FND-05 | pending | FND-04 | A0 | none |
| FND-06 | pending | GOV-02 | A0 + A7 | none |
| FND-07 | pending | FND-06 | A0 + A7 | none |
| FND-08 | pending | FND-06,FND-07 | A0 + A7 | none |
| DOM-01 | pending | FND-02,FND-03,FND-04 | A3 | none |
| DOM-02 | pending | DOM-01,FND-05 | A3 | none |
| DOM-03 | pending | FND-02,FND-03,FND-04,FND-05 | A4 | none |
| DOM-04 | pending | FND-02,FND-01 | A5 | none |
| DOM-05 | pending | DOM-04,FND-04 | A5 | none |
| DOM-06 | pending | DOM-04,DOM-05,FND-05 | A5 | none |
| DOM-07 | pending | FND-02,DOM-02 | A6 | none |
| DOM-08 | pending | FND-02,FND-01 | A8 | none |
| UI-01 | pending | GOV-02,FND-06 | A7 | none |
| UI-02 | pending | GOV-02,FND-06,FND-07 | A7 | none |
| UI-03 | pending | GOV-02,FND-06,FND-07 | A7 | none |
| UI-04 | pending | GOV-02,FND-06,FND-07 | A7 | none |
| UI-05 | pending | GOV-02,FND-06,FND-07 | A7 | none |
| API-01 | pending | UI-01,FND-02,FND-03,FND-08 | A7 | none |
| API-02 | pending | UI-02,DOM-01,DOM-02,FND-08 | A7 | none |
| API-03 | pending | UI-03,DOM-03..DOM-06,FND-08 | A7 | none |
| API-04 | pending | UI-04,DOM-01,DOM-02,FND-04,FND-08 | A7 | none |
| API-05 | pending | UI-05,DOM-03,DOM-07,DOM-08,FND-08 | A0 + A7 | none |
| XCT-01 | pending | DOM-03,DOM-06,API-03,API-05 | A8 + A4 + A5 | none |
| XCT-02 | pending | API-02..API-05,XCT-01 | A8 | none |
| XCT-03 | pending | FND-05,DOM-02,DOM-03,DOM-06,XCT-02 | A0 + A2 | none |
| VER-01 | pending | all implementation packets | A9 + A2 | none |
| VER-02 | pending | VER-01 | A9 + domain/UI owners | none |
| VER-03 | pending | VER-02 | A0 + product | none |

## Update Contract

For each transition record timestamp, apply-progress observation ID, changed-file list, commands/exit codes, known baseline failures, regressions, rollback point, and next packet. Never place secret values in this file.
